"""
load_to_mysql.py — Load the UCI diabetes encounters CSV into MySQL.

Usage:
    python src/load_to_mysql.py
Env (optional): DB_HOST, DB_PORT, DB_USER, DB_PASSWORD (defaults: localhost root)
"""

from pathlib import Path
import os
import sys
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "diabetic_data.csv"
IDS = ROOT / "data" / "IDS_mapping.csv"

KEEP_COLS = {
    "encounter_id": "encounter_id",
    "patient_nbr": "patient_nbr",
    "race": "race",
    "gender": "gender",
    "age": "age",
    "admission_type_id": "admission_type_id",
    "discharge_disposition_id": "discharge_disposition_id",
    "admission_source_id": "admission_source_id",
    "time_in_hospital": "time_in_hospital",
    "num_lab_procedures": "num_lab_procedures",
    "num_procedures": "num_procedures",
    "num_medications": "num_medications",
    "number_outpatient": "number_outpatient",
    "number_emergency": "number_emergency",
    "number_inpatient": "number_inpatient",
    "diag_1": "diag_1",
    "diag_2": "diag_2",
    "diag_3": "diag_3",
    "number_diagnoses": "number_diagnoses",
    "max_glu_serum": "max_glu_serum",
    "A1Cresult": "a1c_result",
    "insulin": "insulin",
    "change": "med_change",
    "diabetesMed": "diabetes_med",
    "readmitted": "readmitted",
}


def get_engine():
    user = os.environ.get("DB_USER", "root")
    pwd = os.environ.get("DB_PASSWORD", "")
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "3306")
    url = (f"mysql+pymysql://{quote_plus(user)}:{quote_plus(pwd)}@{host}:{port}"
           f"/healthcare_analytics?charset=utf8mb4")
    return create_engine(url)


def parse_id_mapping(path: Path) -> pd.DataFrame:
    """IDS_mapping.csv stacks three lookup tables separated by blank lines."""
    rows, current_type = [], None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line == ",":
            current_type = None
            continue
        key, _, desc = line.partition(",")
        if key in ("admission_type_id", "discharge_disposition_id", "admission_source_id"):
            current_type = key
            continue  # header row of the next block
        if current_type:
            rows.append({"id_type": current_type, "id_value": int(key),
                         "description": desc.strip() or None})
    return pd.DataFrame(rows)


def main() -> int:
    df = pd.read_csv(DATA, na_values=["?", "None"])
    df = df[list(KEEP_COLS)].rename(columns=KEEP_COLS)
    ids = parse_id_mapping(IDS)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE encounters"))
        conn.execute(text("TRUNCATE TABLE id_mapping"))
    df.to_sql("encounters", engine, if_exists="append", index=False, chunksize=5000)
    ids.to_sql("id_mapping", engine, if_exists="append", index=False)

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM encounters")).scalar()
        m = conn.execute(text("SELECT COUNT(*) FROM id_mapping")).scalar()
    print(f"loaded encounters={n:,} id_mapping={m}")
    return 0 if n == len(df) else 1


if __name__ == "__main__":
    sys.exit(main())
