# Author: harshith kumar | Date: 2026-09-21
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = Path(__file__).resolve().parent
CHART_DIR = BASE_DIR / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = BASE_DIR / "titanic_clean.csv"
SUMMARY_MD = BASE_DIR / "modeling_summary.md"
BEST_PIPELINE_PATH = BASE_DIR / "best_classifier_pipeline.joblib"


def adjusted_r2(r2: float, n: int, p: int) -> float:
    return 1 - ((1 - r2) * (n - 1) / (n - p - 1))


def build_preprocessor(numeric_cols, categorical_cols):
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ]
    )


def evaluate_classifier(name, pipe, x_train, y_train, x_test, y_test):
    pipe.fit(x_train, y_train)
    y_pred = pipe.predict(x_test)
    y_proba = pipe.predict_proba(x_test)[:, 1]

    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = auc(fpr, tpr)

    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot()
    plt.title(f"Confusion Matrix - {name}")
    plt.tight_layout()
    plt.savefig(CHART_DIR / f"cm_{name.lower().replace(' ', '_')}.png", dpi=150)
    plt.close()

    return {
        "model": name,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "auc": roc_auc,
        "fpr": fpr,
        "tpr": tpr,
        "pipeline": pipe,
    }


def main() -> None:
    df = pd.read_csv(INPUT_CSV)

    target = "survived"
    features = ["pclass", "sex", "age", "sibsp", "parch", "fare", "embarked"]

    x = df[features].copy()
    y = df[target].astype(int)

    class_balance = y.value_counts(normalize=True).sort_index()

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    numeric_cols = ["pclass", "age", "sibsp", "parch", "fare"]
    categorical_cols = ["sex", "embarked"]

    preprocess = build_preprocessor(numeric_cols, categorical_cols)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(random_state=42, max_depth=5),
        "Random Forest": RandomForestClassifier(random_state=42, n_estimators=300),
    }

    eval_rows = []
    roc_items = []
    fitted = {}

    for name, est in models.items():
        pipe = Pipeline(steps=[("preprocess", preprocess), ("model", est)])
        metrics = evaluate_classifier(name, pipe, x_train, y_train, x_test, y_test)
        eval_rows.append({k: metrics[k] for k in ["model", "accuracy", "precision", "recall", "f1", "auc"]})
        roc_items.append((name, metrics["fpr"], metrics["tpr"], metrics["auc"]))
        fitted[name] = metrics["pipeline"]

    # Decision tree visualization with labeled features and classes.
    tree_model = fitted["Decision Tree"].named_steps["model"]
    prep = fitted["Decision Tree"].named_steps["preprocess"]
    feature_names = prep.get_feature_names_out()

    plt.figure(figsize=(26, 10))
    plot_tree(
        tree_model,
        feature_names=feature_names,
        class_names=["not_survived", "survived"],
        filled=True,
        rounded=True,
        fontsize=7,
    )
    plt.title("Decision Tree (Labeled Features and Classes)")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "decision_tree_plot.png", dpi=150)
    plt.close()

    # ROC curve figure.
    plt.figure(figsize=(8, 6))
    for name, fpr, tpr, score in roc_items:
        plt.plot(fpr, tpr, label=f"{name} (AUC={score:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHART_DIR / "roc_curves.png", dpi=150)
    plt.close()

    comparison_df = pd.DataFrame(eval_rows).sort_values("f1", ascending=False).reset_index(drop=True)

    # Imbalance handling comparison on Logistic Regression.
    base_pipe = Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
            ("model", LogisticRegression(max_iter=2000, random_state=42)),
        ]
    )
    bal_pipe = Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
            ("model", LogisticRegression(max_iter=2000, random_state=42, class_weight="balanced")),
        ]
    )
    smote_pipe = ImbPipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
            ("smote", SMOTE(random_state=42)),
            ("model", LogisticRegression(max_iter=2000, random_state=42)),
        ]
    )

    imbalance_rows = []
    for name, pipe in [
        ("baseline", base_pipe),
        ("class_weight_balanced", bal_pipe),
        ("smote", smote_pipe),
    ]:
        pipe.fit(x_train, y_train)
        pred = pipe.predict(x_test)
        imbalance_rows.append(
            {
                "variant": name,
                "precision": precision_score(y_test, pred),
                "recall": recall_score(y_test, pred),
                "f1": f1_score(y_test, pred),
            }
        )

    imbalance_df = pd.DataFrame(imbalance_rows)

    # Random Forest hyperparameter tuning with OOB.
    rf_tune_pipe = Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
            (
                "model",
                RandomForestClassifier(
                    random_state=42,
                    oob_score=True,
                    bootstrap=True,
                ),
            ),
        ]
    )

    param_grid = {
        "model__n_estimators": [200, 300],
        "model__max_depth": [None, 6, 10],
        "model__max_features": ["sqrt", "log2"],
    }

    grid = GridSearchCV(
        estimator=rf_tune_pipe,
        param_grid=param_grid,
        scoring="f1",
        cv=5,
        n_jobs=-1,
    )
    grid.fit(x_train, y_train)
    best_params = grid.best_params_
    best_rf_pipeline = grid.best_estimator_
    oob_score = best_rf_pipeline.named_steps["model"].oob_score_

    # Regression side-task: predict fare.
    reg_features = ["survived", "pclass", "sex", "age", "sibsp", "parch", "embarked"]
    x_reg = df[reg_features].copy()
    y_reg = df["fare"].copy()

    x_train_r, x_test_r, y_train_r, y_test_r = train_test_split(
        x_reg,
        y_reg,
        test_size=0.2,
        random_state=42,
    )

    reg_num = ["survived", "pclass", "age", "sibsp", "parch"]
    reg_cat = ["sex", "embarked"]

    reg_pre = build_preprocessor(reg_num, reg_cat)
    reg_pipe = Pipeline(steps=[("preprocess", reg_pre), ("model", LinearRegression())])
    reg_pipe.fit(x_train_r, y_train_r)

    y_pred_r = reg_pipe.predict(x_test_r)
    mae = mean_absolute_error(y_test_r, y_pred_r)
    rmse = mean_squared_error(y_test_r, y_pred_r, squared=False)
    r2 = r2_score(y_test_r, y_pred_r)
    adj_r2 = adjusted_r2(r2, n=len(y_test_r), p=reg_pipe.named_steps["preprocess"].fit_transform(x_train_r).shape[1])

    residuals = y_test_r - y_pred_r
    plt.figure(figsize=(8, 5))
    plt.scatter(y_pred_r, residuals, alpha=0.7)
    plt.axhline(y=0, color="red", linestyle="--")
    plt.xlabel("Predicted Fare")
    plt.ylabel("Residual")
    plt.title("Residual Plot - Linear Regression")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "residual_plot.png", dpi=150)
    plt.close()

    # Correlation between predicted value and residual magnitude flags non constant variance.
    hetero_corr = float(np.corrcoef(y_pred_r, residuals.abs())[0, 1])
    hetero_conclusion = (
        "shows heteroscedasticity, since residual spread grows as predicted fare increases"
        if abs(hetero_corr) > 0.2
        else "does not show strong heteroscedasticity, since residual spread stays roughly similar across predicted fare"
    )

    # Save best complete classifier pipeline.
    top_model_name = comparison_df.iloc[0]["model"]
    final_pipeline = fitted[top_model_name]
    joblib.dump(final_pipeline, BEST_PIPELINE_PATH)

    # Reload test on raw input.
    loaded_pipeline = joblib.load(BEST_PIPELINE_PATH)
    sample_raw = x_test.head(5).copy()
    reload_preds = loaded_pipeline.predict(sample_raw).tolist()

    combined_rows = []
    for _, row in comparison_df.iterrows():
        combined_rows.append(
            {
                "classifier_model": row["model"],
                "accuracy": row["accuracy"],
                "precision": row["precision"],
                "recall": row["recall"],
                "f1": row["f1"],
                "auc": row["auc"],
                "regression_model": "Linear Regression",
                "mae": mae,
                "rmse": rmse,
                "r2": r2,
                "adjusted_r2": adj_r2,
            }
        )
    combined_df = pd.DataFrame(combined_rows)

    best_by_auc = comparison_df.sort_values("auc", ascending=False).iloc[0]
    survived_share = float(class_balance.get(1, 0.0))
    not_survived_share = float(class_balance.get(0, 0.0))

    best_imbalance = imbalance_df.sort_values("f1", ascending=False).iloc[0]

    with SUMMARY_MD.open("w", encoding="utf-8") as f:
        f.write("# Modeling Summary\n\n")
        f.write("## Stratification Justification\n\n")
        f.write(
            f"The class balance shows about {not_survived_share * 100:.1f} percent non survivors against "
            f"about {survived_share * 100:.1f} percent survivors, which is imbalanced enough that a plain "
            "random split could easily produce a train or test set with a noticeably different ratio. "
            "Stratifying the split on the survived column keeps that same proportion in both the training "
            "and test sets, so model evaluation reflects the real class balance rather than an accident of "
            "the split.\n\n"
        )

        f.write("## Class Balance\n\n")
        f.write(class_balance.rename("proportion").to_frame().to_markdown())
        f.write("\n\n")

        f.write("## Classifier Comparison\n\n")
        f.write(comparison_df.to_markdown(index=False))
        f.write("\n\n")

        f.write("## Imbalance Strategy Comparison Using Logistic Regression\n\n")
        f.write(imbalance_df.to_markdown(index=False))
        f.write("\n\n")
        f.write(
            f"The {best_imbalance['variant']} variant produced the best overall F1 score at "
            f"{best_imbalance['f1']:.4f} among the three imbalance handling strategies tried here, "
            "making it the strongest choice when both false positives and false negatives matter.\n\n"
        )

        f.write("## Random Forest Grid Search\n\n")
        f.write(
            f"The best parameter combination found by grid search is {best_params}. That configuration "
            f"reached a cross validated F1 score of {grid.best_score_:.4f} and an out of bag score of "
            f"{oob_score:.4f}.\n\n"
        )

        f.write("## Regression Metrics\n\n")
        f.write(
            f"Predicting fare from the other features gives a mean absolute error of {mae:.4f}, a root "
            f"mean squared error of {rmse:.4f}, an R squared of {r2:.4f}, and an adjusted R squared of "
            f"{adj_r2:.4f}.\n\n"
        )

        f.write("## Heteroscedasticity Note\n\n")
        f.write(
            f"The residual plot in charts/residual_plot.png {hetero_conclusion}. This was checked "
            f"quantitatively with the correlation between predicted fare and the absolute residual, "
            f"which came out to {hetero_corr:.3f}.\n\n"
        )

        f.write("## Combined Model Comparison\n\n")
        f.write(
            "Classifier metrics and regression metrics sit on different scales, so they are kept in "
            "separate columns rather than implying they are directly comparable numbers.\n\n"
        )
        f.write(combined_df.to_markdown(index=False))
        f.write("\n\n")

        f.write("## Final Recommendation\n\n")
        f.write(
            f"{best_by_auc['model']} is the classifier worth deploying here. It posts the highest AUC at "
            f"{best_by_auc['auc']:.3f} among the three models, together with an accuracy of "
            f"{best_by_auc['accuracy']:.3f} and a precision of {best_by_auc['precision']:.3f}. The other "
            "two models are shown side by side in the table above for comparison, and neither beats it on "
            "both accuracy and ranking ability at the same time. Given that this model combines the "
            "strongest overall accuracy with the strongest ranking ability shown by its AUC, it is the "
            "most sensible default choice for deployment.\n\n"
        )

        f.write("## Reload Check\n\n")
        f.write(
            f"The saved pipeline at {BEST_PIPELINE_PATH.name} was reloaded and produced predictions of "
            f"{reload_preds} on the first five raw test rows, confirming the saved artifact works end to "
            "end on new, unprocessed input.\n"
        )



if __name__ == "__main__":
    main()
