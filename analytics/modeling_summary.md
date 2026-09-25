# Modeling Summary

## Stratification Justification

The class balance shows about 61.8 percent non survivors against about 38.2 percent survivors, which is imbalanced enough that a plain random split could easily produce a train or test set with a noticeably different ratio. Stratifying the split on the survived column keeps that same proportion in both the training and test sets, so model evaluation reflects the real class balance rather than an accident of the split.

## Class Balance

|   survived |   proportion |
|-----------:|-------------:|
|          0 |     0.617548 |
|          1 |     0.382452 |

## Classifier Comparison

| model               |   accuracy |   precision |   recall |       f1 |      auc |
|:--------------------|-----------:|------------:|---------:|---------:|---------:|
| Logistic Regression |   0.808989 |    0.783333 | 0.691176 | 0.734375 | 0.860963 |
| Random Forest       |   0.803371 |    0.761905 | 0.705882 | 0.732824 | 0.824131 |
| Decision Tree       |   0.764045 |    0.76     | 0.558824 | 0.644068 | 0.837366 |

## Imbalance Strategy Comparison Using Logistic Regression

| variant               |   precision |   recall |       f1 |
|:----------------------|------------:|---------:|---------:|
| baseline              |    0.783333 | 0.691176 | 0.734375 |
| class_weight_balanced |    0.71831  | 0.75     | 0.733813 |
| smote                 |    0.735294 | 0.735294 | 0.735294 |

The smote variant produced the best overall F1 score at 0.7353 among the three imbalance handling strategies tried here, making it the strongest choice when both false positives and false negatives matter.

## Random Forest Grid Search

The best parameter combination found by grid search is {'model__max_depth': None, 'model__max_features': 'sqrt', 'model__n_estimators': 200}. That configuration reached a cross validated F1 score of 0.7434 and an out of bag score of 0.8073.

## Regression Metrics

Predicting fare from the other features gives a mean absolute error of 21.0986, a root mean squared error of 41.7021, an R squared of 0.3482, and an adjusted R squared of 0.3091.

## Heteroscedasticity Note

The residual plot in charts/residual_plot.png shows heteroscedasticity, since residual spread grows as predicted fare increases. This was checked quantitatively with the correlation between predicted fare and the absolute residual, which came out to 0.337.

## Combined Model Comparison

Classifier metrics and regression metrics sit on different scales, so they are kept in separate columns rather than implying they are directly comparable numbers.

| classifier_model    |   accuracy |   precision |   recall |       f1 |      auc | regression_model   |     mae |    rmse |       r2 |   adjusted_r2 |
|:--------------------|-----------:|------------:|---------:|---------:|---------:|:-------------------|--------:|--------:|---------:|--------------:|
| Logistic Regression |   0.808989 |    0.783333 | 0.691176 | 0.734375 | 0.860963 | Linear Regression  | 21.0986 | 41.7021 | 0.348163 |       0.30913 |
| Random Forest       |   0.803371 |    0.761905 | 0.705882 | 0.732824 | 0.824131 | Linear Regression  | 21.0986 | 41.7021 | 0.348163 |       0.30913 |
| Decision Tree       |   0.764045 |    0.76     | 0.558824 | 0.644068 | 0.837366 | Linear Regression  | 21.0986 | 41.7021 | 0.348163 |       0.30913 |

## Final Recommendation

Logistic Regression is the classifier worth deploying here. It posts the highest AUC at 0.861 among the three models, together with an accuracy of 0.809 and a precision of 0.783. The other two models are shown side by side in the table above for comparison, and neither beats it on both accuracy and ranking ability at the same time. Given that this model combines the strongest overall accuracy with the strongest ranking ability shown by its AUC, it is the most sensible default choice for deployment.

## Reload Check

The saved pipeline at best_classifier_pipeline.joblib was reloaded and produced predictions of [0, 0, 0, 0, 0] on the first five raw test rows, confirming the saved artifact works end to end on new, unprocessed input.
