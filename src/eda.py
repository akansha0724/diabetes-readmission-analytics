"""
eda.py — Exploratory analysis: cohort profile + readmission-rate figures.
Writes PNGs to reports/figures and a summary to reports/eda_summary.md.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from prep import load_clean, ROOT

FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid", palette="crest")


def rate_plot(df, by, title, fname, order=None, min_n=200):
    g = (df.groupby(by)
           .agg(n=("readmit_30d", "size"), rate=("readmit_30d", "mean"))
           .query("n >= @min_n"))
    if order is not None:
        g = g.reindex([o for o in order if o in g.index])
    ax = (g["rate"] * 100).plot(kind="bar", figsize=(9, 5), color="#2a9d8f")
    ax.axhline((df["readmit_30d"].mean()) * 100, color="#e76f51", ls="--",
               label=f"cohort avg {(df['readmit_30d'].mean()) * 100:.1f}%")
    ax.set_ylabel("30-day readmission %")
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG / fname, dpi=150)
    plt.close()
    return g


def main():
    df = load_clean()
    lines = ["# EDA summary — 30-day readmission cohort", ""]
    lines.append(f"- Encounters after cleaning (first per patient, non-hospice/expired): **{len(df):,}**")
    lines.append(f"- 30-day readmission rate: **{df['readmit_30d'].mean() * 100:.2f}%**")
    lines.append(f"- Median length of stay: **{df['time_in_hospital'].median():.0f} days**; "
                 f"median medications: **{df['num_medications'].median():.0f}**")
    lines.append("")

    # 1. age
    rate_plot(df, "age", "Readmission rate by age band", "readmit_by_age.png",
              order=sorted(df["age"].dropna().unique()))

    # 2. prior inpatient visits
    df["prior_inpatient"] = df["number_inpatient"].clip(upper=5)
    g = rate_plot(df, "prior_inpatient",
                  "Prior inpatient visits (12m) vs readmission — the strongest signal",
                  "readmit_by_prior_inpatient.png", min_n=50)
    lines.append(f"- **Frequent-flyer gradient:** {g['rate'].iloc[0]*100:.1f}% (0 prior stays) → "
                 f"{g['rate'].iloc[-1]*100:.1f}% (5+ prior stays)")

    # 3. primary diagnosis
    g = rate_plot(df, "primary_diag", "Readmission rate by primary diagnosis chapter",
                  "readmit_by_diagnosis.png")
    top = (g["rate"] * 100).idxmax()
    lines.append(f"- Highest-risk primary diagnosis chapter: **{top}** ({g['rate'].max()*100:.1f}%)")

    # 4. length of stay distribution split by outcome
    plt.figure(figsize=(9, 5))
    sns.kdeplot(data=df, x="time_in_hospital", hue="readmit_30d",
                common_norm=False, fill=True)
    plt.title("Length of stay distribution: readmitted vs not")
    plt.xlabel("days in hospital")
    plt.tight_layout()
    plt.savefig(FIG / "los_distribution.png", dpi=150)
    plt.close()

    # 5. numeric feature correlation with target
    from prep import NUMERIC_FEATURES
    corr = (df[NUMERIC_FEATURES + ["readmit_30d"]]
            .corr(numeric_only=True)["readmit_30d"]
            .drop("readmit_30d").sort_values())
    plt.figure(figsize=(8, 5))
    corr.plot(kind="barh", color="#264653")
    plt.title("Correlation with 30-day readmission")
    plt.tight_layout()
    plt.savefig(FIG / "feature_correlation.png", dpi=150)
    plt.close()
    lines.append(f"- Strongest numeric correlate: **{corr.abs().idxmax()}** (r={corr[corr.abs().idxmax()]:.3f})")

    (ROOT / "reports" / "eda_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nfigures -> {FIG}")


if __name__ == "__main__":
    main()
