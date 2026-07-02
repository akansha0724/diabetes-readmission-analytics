# Model results — 30-day readmission risk

- Cohort: 69,990 patients (first encounter each), positives: 8.98%
- Features: 31 after one-hot encoding · train/test 75/25 stratified

## Logistic regression (balanced)
- ROC-AUC: **0.631** · PR-AUC: 0.147 (baseline = 0.090)
- Top risk-increasing coefficients (standardised):
    - `number_inpatient`: +0.217
    - `on_diabetes_med`: +0.083
    - `time_in_hospital`: +0.082
    - `number_emergency`: +0.074
    - `age_mid`: +0.068
- Top protective coefficients:
    - `discharged_home`: -0.267
    - `primary_diag_Respiratory`: -0.120
    - `primary_diag_Other`: -0.084

## Random forest (400 trees, min_leaf=25)
- ROC-AUC: **0.638** · PR-AUC: 0.145
- Top feature importances: `num_lab_procedures` 0.154, `num_medications` 0.131, `time_in_hospital` 0.095, `discharged_home` 0.093, `age_mid` 0.075, `number_diagnoses` 0.069

## Operational view (risk deciles, random forest)
- Top decile readmission rate: **17.1%** vs bottom decile 3.5%
- Targeting the top 30% highest-risk patients captures **48%** of all 30-day readmissions.

**Recommendation:** run the model at discharge; route the top-3-decile patients to transitional-care follow-up (48-72h call, medication reconciliation, PCP appointment before day 7). Prior utilisation and discharge destination dominate the risk — both are known before discharge.