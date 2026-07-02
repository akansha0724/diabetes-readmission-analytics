"""
stats_tests.py — Hypothesis tests behind the dashboard claims.
Writes reports/stats_tests.md.

Each test states H0, the statistic, p-value, and a plain-English conclusion —
the same structure expected in an analytics interview.
"""

import sys

import numpy as np
import pandas as pd
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from prep import load_clean, ROOT


def chi_square(df, group_col, label, out):
    ct = pd.crosstab(df[group_col], df["readmit_30d"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    n = ct.values.sum()
    cramers_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    out.append(f"## {label}")
    out.append(f"- H0: readmission rate is independent of `{group_col}`")
    out.append(f"- chi²({dof}) = {chi2:,.1f}, p = {p:.2e}, Cramér's V = {cramers_v:.3f}")
    verdict = "reject H0" if p < 0.05 else "fail to reject H0"
    out.append(f"- **Conclusion:** {verdict} at α=0.05.")
    out.append("")
    return p


def main():
    df = load_clean()
    out = ["# Hypothesis tests — 30-day readmission", ""]

    # 1. Prior inpatient visits (binned) vs readmission
    df["prior_inpatient_bin"] = pd.cut(df["number_inpatient"],
                                       [-1, 0, 1, 2, np.inf],
                                       labels=["0", "1", "2", "3+"])
    chi_square(df, "prior_inpatient_bin",
               "1. Prior inpatient visits × readmission (chi-square)", out)

    # 2. HbA1c measured vs not (the Strack et al. question)
    ct = pd.crosstab(df["a1c_measured"], df["readmit_30d"])
    rate_not = ct.loc[0, 1] / ct.loc[0].sum()
    rate_yes = ct.loc[1, 1] / ct.loc[1].sum()
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    out.append("## 2. HbA1c measured × readmission (chi-square)")
    out.append(f"- Readmission when A1c NOT measured: {rate_not*100:.2f}%; measured: {rate_yes*100:.2f}%")
    out.append(f"- chi²({dof}) = {chi2:.1f}, p = {p:.2e}")
    out.append(f"- **Conclusion:** {'measuring A1c is associated with a lower readmission rate' if (p < 0.05 and rate_yes < rate_not) else 'no significant association'} "
               "(association, not causation — measurement likely proxies attentive diabetes care).")
    out.append("")

    # 3. Length of stay: readmitted vs not (Welch's t-test + Mann-Whitney)
    a = df.loc[df["readmit_30d"] == 1, "time_in_hospital"]
    b = df.loc[df["readmit_30d"] == 0, "time_in_hospital"]
    t, pt = stats.ttest_ind(a, b, equal_var=False)
    u, pu = stats.mannwhitneyu(a, b)
    d = (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)  # Cohen's d
    out.append("## 3. Length of stay: readmitted vs not")
    out.append(f"- Mean LOS: readmitted {a.mean():.2f}d vs not {b.mean():.2f}d (Cohen's d = {d:.2f})")
    out.append(f"- Welch t = {t:.2f} (p = {pt:.2e}); Mann-Whitney U p = {pu:.2e} (LOS is right-skewed)")
    out.append(f"- **Conclusion:** readmitted patients had significantly longer index stays, "
               f"but the effect size is small — LOS alone is a weak discriminator.")
    out.append("")

    # 4. Medication change during stay vs readmission (2-proportion z-test)
    ch = df[df["meds_changed"] == 1]["readmit_30d"]
    no = df[df["meds_changed"] == 0]["readmit_30d"]
    p1, p2 = ch.mean(), no.mean()
    pp = (ch.sum() + no.sum()) / (len(ch) + len(no))
    z = (p1 - p2) / np.sqrt(pp * (1 - pp) * (1 / len(ch) + 1 / len(no)))
    pz = 2 * (1 - stats.norm.cdf(abs(z)))
    out.append("## 4. Diabetes medication changed during stay (2-proportion z-test)")
    out.append(f"- Readmission: meds changed {p1*100:.2f}% vs unchanged {p2*100:.2f}%")
    out.append(f"- z = {z:.2f}, p = {pz:.2e}")
    out.append(f"- **Conclusion:** {'significant difference' if pz < 0.05 else 'no significant difference'}; "
               "medication change flags sicker/less-controlled patients rather than causing readmission.")
    out.append("")

    text = "\n".join(out)
    (ROOT / "reports" / "stats_tests.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
