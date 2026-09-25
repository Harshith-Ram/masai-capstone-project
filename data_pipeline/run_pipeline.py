# Author: harshith kumar | Date: 2026-09-23
import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "books.db"
RAW_CSV_PATH = DATA_DIR / "books_raw.csv"
CLEAN_CSV_PATH = DATA_DIR / "books_clean.csv"
QUERY_OUTPUT_PATH = DATA_DIR / "sql_query_outputs.md"
GBP_TO_INR_RATE = 105.50
MIN_BOOKS = 60

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    response.encoding = 'utf-8'
    return BeautifulSoup(response.text, "html.parser")


def parse_price(raw_price: str):
    if raw_price is None:
        return None
    match = re.search(r"[\d.]+", raw_price)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def parse_availability(raw_availability: str):
    if raw_availability is None:
        return None
    text = " ".join(raw_availability.split()).lower()
    if "in stock" in text:
        return True
    if "out of stock" in text:
        return False
    return None


def discover_categories(limit: int = 3) -> List[Dict[str, str]]:
    soup = get_soup(BASE_URL)
    category_links = soup.select("ul.nav-list ul li a")

    categories: List[Dict[str, str]] = []
    for link in category_links[:limit]:
        category_name = link.get_text(strip=True)
        href = link.get("href")
        categories.append(
            {
                "category": category_name,
                "url": requests.compat.urljoin(BASE_URL, href),
            }
        )
    return categories


def scrape_category(category_name: str, category_url: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    next_url = category_url

    while next_url:
        soup = get_soup(next_url)
        for article in soup.select("article.product_pod"):
            title = article.h3.a.get("title", "").strip()
            price = article.select_one("p.price_color").get_text(strip=True)
            rating_classes = article.select_one("p.star-rating").get("class", [])
            star_text = next((c for c in rating_classes if c in RATING_MAP), None)
            availability = article.select_one("p.instock.availability").get_text(" ", strip=True)
            records.append(
                {
                    "title": title,
                    "price": price,
                    "star_rating": star_text,
                    "availability": availability,
                    "category": category_name,
                }
            )

        next_link = soup.select_one("li.next a")
        if next_link:
            next_url = requests.compat.urljoin(next_url, next_link.get("href"))
        else:
            next_url = None

    return records


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    clean["price_gbp"] = clean["price"].apply(parse_price)
    clean["rating"] = clean["star_rating"].map(RATING_MAP)
    clean["in_stock"] = clean["availability"].apply(parse_availability)

    # Median-impute numeric fields when parsing fails to keep pipeline robust.
    for col in ["price_gbp", "rating"]:
        median_val = clean[col].median()
        if pd.isna(median_val):
            raise ValueError(f"Cannot compute median for column {col}")
        clean[col] = clean[col].fillna(median_val)

    # If stock status cannot be parsed, drop row because boolean imputation can be misleading.
    clean = clean.dropna(subset=["in_stock"]).copy()

    clean["rating"] = clean["rating"].round().astype(int)
    clean["in_stock"] = clean["in_stock"].astype(bool)
    clean["price_inr"] = (clean["price_gbp"] * GBP_TO_INR_RATE).round(2)

    clean = clean[["title", "category", "price_gbp", "price_inr", "rating", "in_stock"]]
    return clean


def build_database(df: pd.DataFrame, db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute(
        """
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            price_inr REAL NOT NULL,
            rating INTEGER NOT NULL,
            in_stock INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
        """
    )

    categories = sorted(df["category"].unique().tolist())
    cursor.executemany(
        "INSERT INTO categories (category_name) VALUES (?)",
        [(cat,) for cat in categories],
    )

    cat_map = pd.read_sql("SELECT category_id, category_name FROM categories", conn).set_index("category_name")[
        "category_id"
    ].to_dict()

    books_df = df.copy()
    books_df["category_id"] = books_df["category"].map(cat_map)
    books_df["in_stock"] = books_df["in_stock"].astype(int)

    cursor.executemany(
        """
        INSERT INTO books (title, price_gbp, price_inr, rating, in_stock, category_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        books_df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category_id"]].itertuples(index=False, name=None),
    )

    conn.commit()
    conn.close()


def run_queries(db_path: Path) -> Dict[str, pd.DataFrame]:
    conn = sqlite3.connect(db_path)

    queries = {
        "q1_select_where": """
            SELECT title, price_gbp, rating
            FROM books
            WHERE rating >= 4
            ORDER BY rating DESC, price_gbp DESC
            LIMIT 10
        """,
        "q2_distinct": """
            SELECT DISTINCT c.category_name
            FROM categories c
            ORDER BY c.category_name
        """,
        "q3_between": """
            SELECT title, price_gbp
            FROM books
            WHERE price_gbp BETWEEN 20 AND 40
            ORDER BY price_gbp ASC
            LIMIT 10
        """,
        "q4_in_clause": """
            SELECT title, rating, price_gbp
            FROM books
            WHERE rating IN (4, 5)
            ORDER BY price_gbp DESC
            LIMIT 10
        """,
        "q5_join": """
            SELECT b.title, b.rating, b.price_gbp, c.category_name
            FROM books b
            JOIN categories c ON b.category_id = c.category_id
            ORDER BY b.rating DESC, b.price_gbp DESC
            LIMIT 15
        """,
    }

    results = {name: pd.read_sql(query, conn) for name, query in queries.items()}

    read_sql_df_1 = pd.read_sql(queries["q1_select_where"], conn)
    read_sql_df_2 = pd.read_sql(queries["q5_join"], conn)

    books_df = pd.read_sql("SELECT * FROM books", conn)
    categories_df = pd.read_sql("SELECT * FROM categories", conn)

    merged_df = books_df.merge(categories_df, on="category_id", how="inner")
    merged_df = merged_df[["title", "rating", "price_gbp", "category_name"]]
    merged_df = merged_df.sort_values(["rating", "price_gbp"], ascending=[False, False]).head(15).reset_index(drop=True)

    join_match = read_sql_df_2.reset_index(drop=True).equals(merged_df)

    results["read_sql_df_1"] = read_sql_df_1
    results["read_sql_df_2"] = read_sql_df_2
    results["merge_equivalent_df"] = merged_df
    results["join_equivalence"] = pd.DataFrame({"join_equivalent": [join_match]})

    with QUERY_OUTPUT_PATH.open("w", encoding="utf-8") as f:
        f.write("# SQL Query Outputs\n\n")
        for name, query in queries.items():
            f.write(f"## {name}\n\n")
            f.write("```sql\n")
            f.write(query.strip() + "\n")
            f.write("```\n\n")
            f.write(results[name].to_markdown(index=False))
            f.write("\n\n")

        f.write("## Pandas read_sql Demonstration\n\n")
        f.write("read_sql result (Query 1):\n\n")
        f.write(read_sql_df_1.to_markdown(index=False) + "\n\n")
        f.write("read_sql result (JOIN query):\n\n")
        f.write(read_sql_df_2.to_markdown(index=False) + "\n\n")

        f.write("## Pandas merge Demonstration (No SQL)\n\n")
        f.write(merged_df.to_markdown(index=False) + "\n\n")
        f.write(f"Join-equivalence check: **{join_match}**\n")

    conn.close()
    return results


def main() -> None:
    categories = discover_categories(limit=3)

    scraped_rows: List[Dict[str, str]] = []
    for cat in categories:
        scraped_rows.extend(scrape_category(cat["category"], cat["url"]))

    if len(scraped_rows) < MIN_BOOKS:
        raise ValueError(f"Scraped only {len(scraped_rows)} rows, expected at least {MIN_BOOKS}")

    raw_df = pd.DataFrame(scraped_rows)
    raw_df.to_csv(RAW_CSV_PATH, index=False)

    clean_df = clean_data(raw_df)
    clean_df.to_csv(CLEAN_CSV_PATH, index=False)

    build_database(clean_df, DB_PATH)
    results = run_queries(DB_PATH)

    summary = {
        "rows_raw": len(raw_df),
        "rows_clean": len(clean_df),
        "categories": sorted(clean_df["category"].unique().tolist()),
        "price_gbp_dtype": str(clean_df["price_gbp"].dtype),
        "rating_dtype": str(clean_df["rating"].dtype),
        "in_stock_dtype": str(clean_df["in_stock"].dtype),
        "price_inr_dtype": str(clean_df["price_inr"].dtype),
        "join_equivalent": bool(results["join_equivalence"].iloc[0, 0]),
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
