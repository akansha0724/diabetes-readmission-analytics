"""
model.py — 30-day readmission risk models.

Two models, deliberately simple and defensible:
- Logistic regression (interpretable baseline; coefficients = risk story)
- Random forest (non-linear benchmark)

Design choices that matter:
- One encounter per patient (prep.py) so the same patient never appears in
  both train and test.
- class_weight='balanced' — positives are ~9% of the cohort.
- Headline metric is ROC-AUC + PR-AUC, not accuracy (a model that says
  "never readmitted" is 91% accurate and useless).

Writes reports/model_results.md and two figures.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from prep import load_clean, model_frame, ROOT

FIG = ROOT / "reports" / "figures"
RANDOM_STATE = 42


def main():
    df = load_clean()
    X, y = model_frame(df)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE)

    out = ["# Model results — 30-day readmission risk", ""]
    out.append(f"- Cohort: {len(df):,} patients (first encounter each), "
               f"positives: {y.mean()*100:.2f}%")
    out.append(f"- Features: {X.shape[1]} after one-hot encoding · train/test 75/25 stratified")
    out.append("")

    # ── Logistic regression ───────────────────────────────────────────────────
    logreg = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced"),
    )
    logreg.fit(X_tr, y_tr)
    p_lr = logreg.predict_proba(X_te)[:, 1]
    auc_lr = roc_auc_score(y_te, p_lr)
    ap_lr = average_precision_score(y_te, p_lr)

    coefs = pd.Series(logreg[-1].coef_[0], index=X.columns).sort_values()
    out.append("## Logistic regression (balanced)")
    out.append(f"- ROC-AUC: **{auc_lr:.3f}** · PR-AUC: {ap_lr:.3f} (baseline = {y_te.mean():.3f})")
    out.append("- Top risk-increasing coefficients (standardised):")
    for name, v in coefs.tail(5)[::-1].items():
        out.append(f"    - `{name}`: +{v:.3f}")
    out.append("- Top protective coefficients:")
    for name, v in coefs.head(3).items():
        out.append(f"    - `{name}`: {v:.3f}")
    out.append("")

    # ── Random forest ─────────────────────────────────────────────────────────
    rf = RandomForestClassifier(
        n_estimators=400, min_samples_leaf=25, class_weight="balanced",
        n_jobs=-1, random_state=RANDOM_STATE)
    rf.fit(X_tr, y_tr)
    p_rf = rf.predict_proba(X_te)[:, 1]
    auc_rf = roc_auc_score(y_te, p_rf)
    ap_rf = average_precision_score(y_te, p_rf)

    imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    out.append("## Random forest (400 trees, min_leaf=25)")
    out.append(f"- ROC-AUC: **{auc_rf:.3f}** · PR-AUC: {ap_rf:.3f}")
    out.append("- Top feature importances: " +
               ", ".join(f"`{k}` {v:.3f}" for k, v in imp.head(6).items()))
    out.append("")

    # ── ROC curves ────────────────────────────────────────────────────────────
    plt.figure(figsize=(7, 6))
    for label, p in [(f"LogReg AUC={auc_lr:.3f}", p_lr), (f"RF AUC={auc_rf:.3f}", p_rf)]:
        fpr, tpr, _ = roc_curve(y_te, p)
        plt.plot(fpr, tpr, label=label)
    plt.plot([0, 1], [0, 1], "k--", lw=0.8)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("30-day readmission — ROC")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "roc_curves.png", dpi=150)
    plt.close()

    # feature importance figure
    plt.figure(figsize=(8, 6))
    imp.head(12)[::-1].plot(kind="barh", color="#2a9d8f")
    plt.title("Random forest — top 12 feature importances")
    plt.tight_layout()
    plt.savefig(FIG / "feature_importance.png", dpi=150)
    plt.close()

    # ── Decile lift: what a discharge-planning team would actually use ────────
    deciles = pd.qcut(pd.Series(p_rf, index=y_te.index), 10, labels=False, duplicates="drop")
    lift = y_te.groupby(deciles).mean() * 100
    capture = y_te.groupby(deciles).sum().iloc[::-1].cumsum() / y_te.sum() * 100
    out.append("## Operational view (risk deciles, random forest)")
    out.append(f"- Top decile readmission rate: **{lift.iloc[-1]:.1f}%** vs bottom decile {lift.iloc[0]:.1f}%")
    out.append(f"- Targeting the top 30% highest-risk patients captures "
               f"**{capture.iloc[2]:.0f}%** of all 30-day readmissions.")
    out.append("")
    out.append("**Recommendation:** run the model at discharge; route the top-3-decile "
               "patients to transitional-care follow-up (48-72h call, medication "
               "reconciliation, PCP appointment before day 7). Prior utilisation and "
               "discharge destination dominate the risk — both are known before discharge.")

    text = "\n".join(out)
    (ROOT / "reports" / "model_results.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
