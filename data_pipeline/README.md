# Data Pipeline

## Objective

This module builds a full scrape, clean, and store workflow on top of books.toscrape.com and converts every price into INR using a fixed rate of 1 GBP equal to 105.50 INR.

## How to Run

Install the dependencies from the repository root, then run the pipeline script from inside this folder.

```bash
pip install -r requirements.txt
python data_pipeline/run_pipeline.py
```

## What Gets Produced

- `books_raw.csv` holds the raw scraped records before any cleaning.
- `books_clean.csv` holds the cleaned dataset with typed columns.
- `books.db` is the normalized SQLite database with a primary key and foreign key relationship between books and categories.
- `sql_query_outputs.md` holds every required SQL query along with its printed output.

## Schema

Two tables share a primary key and foreign key relationship. The `categories` table stores `category_id` as its primary key and a unique `category_name`. The `books` table stores `book_id` as its primary key along with `title`, `price_gbp`, `price_inr`, `rating`, `in_stock`, and a `category_id` that references the categories table.

## Cleaning Decisions

When `price_gbp` or `rating` fail to parse for a row, the pipeline fills that value with the column's median rather than dropping the row, since price and rating are numeric fields where a reasonable estimate keeps the row usable. When `in_stock` cannot be parsed, the row is dropped instead of guessed, because a wrong stock status is more misleading than a missing row. The scraper also normalizes the page encoding to UTF 8 before parsing, since the source site would otherwise render the currency symbol incorrectly and break every price value.

## SQL Clause Coverage

The queries in `sql_query_outputs.md` together cover `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT`, `BETWEEN`, `IN`, and a join across both tables.

## Pandas Equivalence

The join query result is produced twice, once through `pd.read_sql` against the SQLite database and once through `pd.merge` on the in memory DataFrames with no SQL involved. Both results are compared row by row, and the equivalence check prints as True.
