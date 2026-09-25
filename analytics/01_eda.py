# Author: harshith kumar | Date: 2026-09-20
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent
CHART_DIR = BASE_DIR / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

RAW_CSV = BASE_DIR / "titanic.csv"
CLEAN_CSV = BASE_DIR / "titanic_clean.csv"
SUMMARY_MD = BASE_DIR / "eda_summary.md"


def iqr_outlier_count(series: pd.Series) -> int:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((series < lower) | (series > upper)).sum())


def top_two_correlations(corr: pd.DataFrame):
    pairs = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], corr.iloc[i, j], abs(corr.iloc[i, j])))
    pairs = sorted(pairs, key=lambda x: x[3], reverse=True)
    return pairs[:2]


def main() -> None:
    sns.set_theme(style="whitegrid")

    # Single source-of-truth raw load for this module.
    df = sns.load_dataset("titanic")
    df.to_csv(RAW_CSV, index=False)

    print("=== INFO ===")
    print(df.info())
    print("=== DESCRIBE ===")
    print(df.describe(include="all"))
    print("=== SHAPE ===")
    print(df.shape)

    missing_pct = (df.isnull().mean() * 100).sort_values(ascending=False)
    missing_pct = missing_pct[missing_pct > 0]

    work = df.copy()

    # <5% missing: drop rows for embarked and embark_town.
    work = work.dropna(subset=["embarked", "embark_town"])

    # 5-30% missing: impute age with median.
    work["age"] = work["age"].fillna(work["age"].median())

    # Very high missing: deck is mostly missing, encode as category level.
    work["deck"] = work["deck"].astype("object").fillna("Missing")

    # Small numeric missingness: impute fare.
    work["fare"] = work["fare"].fillna(work["fare"].median())

    # Any remaining rows missing target are dropped.
    work = work.dropna(subset=["survived"]).copy()

    work.to_csv(CLEAN_CSV, index=False)

    # Univariate charts.
    plt.figure(figsize=(8, 5))
    sns.histplot(work["age"], bins=30, kde=True)
    plt.title("Age Distribution")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "age_hist.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.boxplot(x=work["age"])
    plt.title("Age Box Plot")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "age_box.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.histplot(work["fare"], bins=30, kde=True)
    plt.title("Fare Distribution")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "fare_hist.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.boxplot(x=work["fare"])
    plt.title("Fare Box Plot")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "fare_box.png", dpi=150)
    plt.close()

    age_outliers = iqr_outlier_count(work["age"])
    fare_outliers = iqr_outlier_count(work["fare"])

    fare_mean = float(work["fare"].mean())
    fare_median = float(work["fare"].median())
    fare_mode = float(work["fare"].mode().iloc[0])

    # Bivariate analysis.
    survival_by_sex = work.groupby("sex", as_index=False)["survived"].mean()
    survival_by_pclass = work.groupby("pclass", as_index=False)["survived"].mean()
    survival_by_sex_pclass = work.groupby(["sex", "pclass"], as_index=False)["survived"].mean()

    corr_cols = ["survived", "pclass", "age", "sibsp", "parch", "fare"]
    corr = work[corr_cols].corr()

    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Heatmap (Specified 6 Columns)")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "corr_heatmap.png", dpi=150)
    plt.close()

    top2 = top_two_correlations(corr)

    # Multivariate story charts.
    plt.figure(figsize=(8, 5))
    sns.barplot(data=work, x="sex", y="survived", hue="pclass")
    plt.title("Survival by Sex and Class")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "survival_sex_class.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.boxplot(data=work, x="survived", y="fare", hue="pclass")
    plt.title("Fare by Survival and Class")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "fare_survival_class.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=work, x="age", y="fare", hue="survived", alpha=0.7)
    plt.title("Age vs Fare by Survival")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "age_fare_survival.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.barplot(data=work, x="embarked", y="survived")
    plt.title("Survival by Embarkation Port")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "survival_embarked.png", dpi=150)
    plt.close()

    # Exploratory standardization check.
    scaler = StandardScaler()
    z_cols = pd.DataFrame(scaler.fit_transform(work[["age", "fare"]]), columns=["age_z", "fare_z"])

    std_before = work[["age", "fare"]].agg(["mean", "std"]).T
    std_after = z_cols[["age_z", "fare_z"]].agg(["mean", "std"]).T

    with SUMMARY_MD.open("w", encoding="utf-8") as f:
        f.write("# EDA Summary\n\n")
        f.write("## Missing Values\n\n")
        missing_desc = ", ".join(
            f"`{col}` is missing about {pct:.1f} percent of its values"
            for col, pct in missing_pct.items()
        )
        f.write(f"{missing_desc}.\n\n")
        f.write(missing_pct.to_frame("missing_percent").to_markdown())
        f.write("\n\n")
        f.write(
            "Following the threshold rule from the brief, columns missing under five percent have those "
            "rows dropped, columns missing between five and thirty percent are imputed, and any column "
            "missing far more than that is encoded as its own category instead of being guessed, since a "
            "missing value there is itself meaningful information rather than noise to fill in.\n\n"
        )

        f.write("## Outlier Counts Using the IQR Rule\n\n")
        f.write(
            f"`age` has {age_outliers} outliers and `fare` has {fare_outliers} outliers, using the "
            "standard rule of flagging anything outside 1.5 times the interquartile range beyond the "
            "first and third quartiles.\n\n"
        )

        f.write("## Fare Distribution\n\n")
        if fare_mean > fare_median > fare_mode:
            skew = "right skewed"
            skew_reason = (
                "This makes sense for ticket pricing, where a large majority of passengers paid modest "
                "fares while a smaller group paid very high fares, pulling the mean upward."
            )
        elif fare_mean < fare_median < fare_mode:
            skew = "left skewed"
            skew_reason = (
                "This means a smaller group of unusually low fares is pulling the mean below the median."
            )
        else:
            skew = "approximately symmetric or mixed"
            skew_reason = "The mean, median, and mode do not follow a clean ordering in either direction."
        f.write(
            f"The mean fare is {fare_mean:.2f}, the median fare is {fare_median:.2f}, and the mode is "
            f"{fare_mode:.2f}. The ordering of mean, median, and mode places this distribution as "
            f"{skew}. {skew_reason}\n\n"
        )

        f.write("## Survival Rates\n\n")
        f.write("### By Sex\n\n")
        f.write(survival_by_sex.to_markdown(index=False))
        f.write("\n\n### By Passenger Class\n\n")
        f.write(survival_by_pclass.to_markdown(index=False))
        f.write("\n\n### By Sex and Passenger Class\n\n")
        f.write(survival_by_sex_pclass.to_markdown(index=False))
        f.write("\n\n")

        f.write("## Two Strongest Correlations\n\n")
        (c1a, c2a, va, absa), (c1b, c2b, vb, absb) = top2[0], top2[1]
        f.write(
            f"The strongest absolute correlation is between `{c1a}` and `{c2a}` at {va:.4f}, followed by "
            f"`{c1b}` and `{c2b}` at {vb:.4f}. These two relationships are the ones worth reading into, "
            "since every other pair among the six numeric columns has a noticeably weaker linear "
            "relationship.\n\n"
        )

        f.write("## Multivariate Data Story\n\n")
        f.write("### Survival by Sex and Passenger Class\n\n")
        f.write(
            "See `charts/survival_sex_class.png`. Survival was shaped heavily by sex and then reinforced "
            "by class, with women in the higher classes surviving at far higher rates than men in any "
            "class. Sex was the dominant factor in who lived, and class amplified that effect, especially "
            "for women in the higher classes.\n\n"
        )
        f.write("### Fare by Survival and Class\n\n")
        f.write(
            "See `charts/fare_survival_class.png`. Within every passenger class, survivors tended to have "
            "paid a noticeably higher fare than non survivors. This suggests that fare, which likely "
            "reflects cabin location and how close a passenger was to the lifeboats, added a survival "
            "advantage even among passengers in the same class.\n\n"
        )
        f.write("### Age Against Fare by Survival\n\n")
        f.write(
            "See `charts/age_fare_survival.png`. Survivors are spread fairly evenly across ages but "
            "cluster more toward higher fares, while non survivors are concentrated in the low fare and "
            "low to middle age range. There is no clean age cutoff that predicts survival on its own, "
            "which suggests that fare and class carried more predictive weight than age by itself.\n\n"
        )
        f.write("### Survival by Embarkation Port\n\n")
        f.write(
            "See `charts/survival_embarked.png`. Passengers boarding at different ports show noticeably "
            "different survival rates, and this difference is unlikely to be a direct effect of the port "
            "itself, since it more likely reflects the mix of ticket classes that boarded there.\n\n"
        )
        f.write("### Correlation Heatmap\n\n")
        f.write(
            "See `charts/corr_heatmap.png`. The heatmap confirms the two strongest relationships already "
            "reported above, while the rest of the numeric features show much weaker linear relationships "
            "with each other.\n\n"
        )

        f.write("## Standardization Check\n\n")
        f.write("### Before Z Score\n\n")
        f.write(std_before.to_markdown())
        f.write("\n\n### After Z Score\n\n")
        f.write(std_after.to_markdown())
        f.write(
            "\n\nBoth transformed columns land at approximately zero mean and a standard deviation of "
            "one, confirming the standardization worked as expected. This check is exploratory only and "
            "does not feed into the modeling pipeline, which fits its own scaler on the training split.\n"
        )


if __name__ == "__main__":
    main()

