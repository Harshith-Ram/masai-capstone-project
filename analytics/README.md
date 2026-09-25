# Analytics Pipeline

## Objective

This module runs one cohesive Titanic pipeline that starts at profiling and cleaning and continues straight into predictive modeling, without ever reloading the raw dataset a second time.

## How to Run

Install the dependencies from the repository root, then run both scripts in order from inside this folder.

```bash
pip install -r requirements.txt
python analytics/01_eda.py
python analytics/02_modeling.py
```

## What Gets Produced

- `titanic.csv` is the offline fallback saved right after the one and only raw data load.
- `titanic_clean.csv` is the cleaned dataset that the modeling script continues from.
- `eda_summary.md` holds the missingness report, outlier counts, survival breakdowns, correlation findings, chart interpretations, and the standardization check.
- `modeling_summary.md` holds the classifier comparison, the imbalance handling comparison, the grid search and out of bag results, the regression metrics, and the final recommendation.
- `best_classifier_pipeline.joblib` is the complete fitted pipeline, covering preprocessing and the final estimator together, ready to run on raw new data.
- `charts` holds every required figure as a PNG file.

## Missing Value Strategy

Columns missing under five percent of their values have those rows dropped. Columns missing between five and thirty percent are imputed. The `deck` column is missing far more than that, so instead of imputing an unreliable guess it is encoded as its own "Missing" category, since a passenger having no recorded deck is itself meaningful information.

## Modeling Notes

The train and test split is stratified on the target before any preprocessing happens. Every preprocessing step, meaning the imputer, the encoder, and the scaler, is wrapped in a `ColumnTransformer` and fit only on the training split, then applied to the test split without ever being refit on it. Three classifiers are trained on that same split, Logistic Regression, Decision Tree, and Random Forest, and each is evaluated with a confusion matrix, accuracy, precision, recall, F1, and an ROC curve with its AUC. Class imbalance is compared three ways, using the raw baseline, using `class_weight='balanced'`, and using SMOTE applied only to the training fold. The Random Forest is tuned with `GridSearchCV` over its estimator count, depth, and feature sampling, and it is built with `oob_score=True` so its out of bag score can be reported alongside the best parameters. A parallel linear regression predicts fare from the other features and reports MAE, RMSE, R squared, and adjusted R squared, together with a residual plot.
