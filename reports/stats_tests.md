# Hypothesis tests — 30-day readmission

## 1. Prior inpatient visits × readmission (chi-square)
- H0: readmission rate is independent of `prior_inpatient_bin`
- chi²(3) = 664.7, p = 9.48e-144, Cramér's V = 0.097
- **Conclusion:** reject H0 at α=0.05.

## 2. HbA1c measured × readmission (chi-square)
- Readmission when A1c NOT measured: 9.11%; measured: 8.40%
- chi²(1) = 6.4, p = 1.14e-02
- **Conclusion:** measuring A1c is associated with a lower readmission rate (association, not causation — measurement likely proxies attentive diabetes care).

## 3. Length of stay: readmitted vs not
- Mean LOS: readmitted 4.79d vs not 4.22d (Cohen's d = 0.19)
- Welch t = 14.23 (p = 2.29e-45); Mann-Whitney U p = 3.87e-56 (LOS is right-skewed)
- **Conclusion:** readmitted patients had significantly longer index stays, but the effect size is small — LOS alone is a weak discriminator.

## 4. Diabetes medication changed during stay (2-proportion z-test)
- Readmission: meds changed 9.44% vs unchanged 8.60%
- z = 3.84, p = 1.21e-04
- **Conclusion:** significant difference; medication change flags sicker/less-controlled patients rather than causing readmission.
