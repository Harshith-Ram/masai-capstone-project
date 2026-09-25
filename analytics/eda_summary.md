# EDA Summary

## Missing Values

`deck` is missing about 77.2 percent of its values, `age` is missing about 19.9 percent of its values, `embarked` is missing about 0.2 percent of its values, `embark_town` is missing about 0.2 percent of its values.

|             |   missing_percent |
|:------------|------------------:|
| deck        |         77.2166   |
| age         |         19.8653   |
| embarked    |          0.224467 |
| embark_town |          0.224467 |

Following the threshold rule from the brief, columns missing under five percent have those rows dropped, columns missing between five and thirty percent are imputed, and any column missing far more than that is encoded as its own category instead of being guessed, since a missing value there is itself meaningful information rather than noise to fill in.

## Outlier Counts Using the IQR Rule

`age` has 65 outliers and `fare` has 114 outliers, using the standard rule of flagging anything outside 1.5 times the interquartile range beyond the first and third quartiles.

## Fare Distribution

The mean fare is 32.10, the median fare is 14.45, and the mode is 8.05. The ordering of mean, median, and mode places this distribution as right skewed. This makes sense for ticket pricing, where a large majority of passengers paid modest fares while a smaller group paid very high fares, pulling the mean upward.

## Survival Rates

### By Sex

| sex    |   survived |
|:-------|-----------:|
| female |   0.740385 |
| male   |   0.188908 |

### By Passenger Class

|   pclass |   survived |
|---------:|-----------:|
|        1 |   0.626168 |
|        2 |   0.472826 |
|        3 |   0.242363 |

### By Sex and Passenger Class

| sex    |   pclass |   survived |
|:-------|---------:|-----------:|
| female |        1 |   0.967391 |
| female |        2 |   0.921053 |
| female |        3 |   0.5      |
| male   |        1 |   0.368852 |
| male   |        2 |   0.157407 |
| male   |        3 |   0.135447 |

## Two Strongest Correlations

The strongest absolute correlation is between `pclass` and `fare` at -0.5482, followed by `sibsp` and `parch` at 0.4145. These two relationships are the ones worth reading into, since every other pair among the six numeric columns has a noticeably weaker linear relationship.

## Multivariate Data Story

### Survival by Sex and Passenger Class

See `charts/survival_sex_class.png`. Survival was shaped heavily by sex and then reinforced by class, with women in the higher classes surviving at far higher rates than men in any class. Sex was the dominant factor in who lived, and class amplified that effect, especially for women in the higher classes.

### Fare by Survival and Class

See `charts/fare_survival_class.png`. Within every passenger class, survivors tended to have paid a noticeably higher fare than non survivors. This suggests that fare, which likely reflects cabin location and how close a passenger was to the lifeboats, added a survival advantage even among passengers in the same class.

### Age Against Fare by Survival

See `charts/age_fare_survival.png`. Survivors are spread fairly evenly across ages but cluster more toward higher fares, while non survivors are concentrated in the low fare and low to middle age range. There is no clean age cutoff that predicts survival on its own, which suggests that fare and class carried more predictive weight than age by itself.

### Survival by Embarkation Port

See `charts/survival_embarked.png`. Passengers boarding at different ports show noticeably different survival rates, and this difference is unlikely to be a direct effect of the port itself, since it more likely reflects the mix of ticket classes that boarded there.

### Correlation Heatmap

See `charts/corr_heatmap.png`. The heatmap confirms the two strongest relationships already reported above, while the rest of the numeric features show much weaker linear relationships with each other.

## Standardization Check

### Before Z Score

|      |    mean |     std |
|:-----|--------:|--------:|
| age  | 29.3152 | 12.9849 |
| fare | 32.0967 | 49.6975 |

### After Z Score

|        |        mean |     std |
|:-------|------------:|--------:|
| age_z  | 2.71749e-16 | 1.00056 |
| fare_z | 1.39871e-16 | 1.00056 |

Both transformed columns land at approximately zero mean and a standard deviation of one, confirming the standardization worked as expected. This check is exploratory only and does not feed into the modeling pipeline, which fits its own scaler on the training split.
