"""
prep.py — Shared cleaning / feature engineering for the readmission analysis.

Cleaning decisions (documented because they change the answer):
- '?' and 'None' are read as missing.
- Target: readmitted == '<30' (binary). '>30' and 'NO' are both negative —
  the CMS penalty window is 30 days.
- Encounters that CANNOT be readmitted are dropped: discharge disposition
  11 (expired), 13/14 (hospice), 19/20/21 (expired variants).
- One encounter per patient (the first) to stop the same frequent-flyer
  patient appearing in both train and test folds (leakage).
- weight (97% missing), payer_code (~40% missing) and medical_specialty
  (~49% missing) are excluded from modelling.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "diabetic_data.csv"

EXPIRED_OR_HOSPICE = {11, 13, 14, 19, 20, 21}

AGE_MIDPOINT = {f"[{lo}-{lo+10})": lo + 5 for lo in range(0, 100, 10)}


def icd9_chapter(code) -> str:
    """Group raw ICD-9 codes into coarse clinical chapters."""
    if pd.isna(code):
        return "Missing"
    s = str(code)
    if s.startswith(("V", "E")):
        return "Other"
    try:
        v = float(s)
    except ValueError:
        return "Other"
    if 390 <= v <= 459 or v == 785:
        return "Circulatory"
    if 460 <= v <= 519 or v == 786:
        return "Respiratory"
    if 520 <= v <= 579 or v == 787:
        return "Digestive"
    if 250 <= v < 251:
        return "Diabetes"
    if 800 <= v <= 999:
        return "Injury"
    if 710 <= v <= 739:
        return "Musculoskeletal"
    if 580 <= v <= 629 or v == 788:
        return "Genitourinary"
    if 140 <= v <= 239:
        return "Neoplasms"
    return "Other"


def load_clean(dedupe_patients: bool = True) -> pd.DataFrame:
    df = pd.read_csv(RAW, na_values=["?", "None"], low_memory=False)

    df = df[~df["discharge_disposition_id"].isin(EXPIRED_OR_HOSPICE)]
    if dedupe_patients:
        df = df.sort_values("encounter_id").drop_duplicates("patient_nbr", keep="first")

    df["readmit_30d"] = (df["readmitted"] == "<30").astype(int)
    df["age_mid"] = df["age"].map(AGE_MIDPOINT)
    df["primary_diag"] = df["diag_1"].apply(icd9_chapter)
    df["a1c_measured"] = df["A1Cresult"].notna().astype(int)
    df["glu_measured"] = df["max_glu_serum"].notna().astype(int)
    df["meds_changed"] = (df["change"] == "Ch").astype(int)
    df["on_diabetes_med"] = (df["diabetesMed"] == "Yes").astype(int)
    df["on_insulin"] = (df["insulin"] != "No").astype(int)
    df["discharged_home"] = (df["discharge_disposition_id"] == 1).astype(int)
    df["emergency_admission"] = (df["admission_type_id"] == 1).astype(int)
    return df


NUMERIC_FEATURES = [
    "age_mid", "time_in_hospital", "num_lab_procedures", "num_procedures",
    "num_medications", "number_outpatient", "number_emergency",
    "number_inpatient", "number_diagnoses",
]
BINARY_FEATURES = [
    "a1c_measured", "glu_measured", "meds_changed", "on_diabetes_med",
    "on_insulin", "discharged_home", "emergency_admission",
]
CATEGORICAL_FEATURES = ["race", "gender", "primary_diag"]


def model_frame(df: pd.DataFrame):
    """Return X (one-hot encoded) and y for modelling."""
    X = pd.get_dummies(
        df[NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES],
        columns=CATEGORICAL_FEATURES, drop_first=True,
    )
    X["age_mid"] = X["age_mid"].fillna(X["age_mid"].median())
    y = df["readmit_30d"]
    return X, y
