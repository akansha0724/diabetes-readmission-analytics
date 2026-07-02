-- =============================================================================
-- Healthcare Readmission Analytics — MySQL schema
-- Source: UCI "Diabetes 130-US hospitals for years 1999-2008" (101,766 encounters)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS healthcare_analytics
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE healthcare_analytics;

-- One row per hospital encounter
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id             BIGINT UNSIGNED NOT NULL,
    patient_nbr              BIGINT UNSIGNED NOT NULL,
    race                     VARCHAR(30)  NULL,
    gender                   VARCHAR(20)  NOT NULL,
    age                      VARCHAR(10)  NOT NULL COMMENT 'Decade band, e.g. [70-80)',
    admission_type_id        TINYINT      NOT NULL,
    discharge_disposition_id TINYINT      NOT NULL,
    admission_source_id      TINYINT      NOT NULL,
    time_in_hospital         TINYINT      NOT NULL COMMENT 'Length of stay, days (1-14)',
    num_lab_procedures       SMALLINT     NOT NULL,
    num_procedures           TINYINT      NOT NULL,
    num_medications          SMALLINT     NOT NULL,
    number_outpatient        SMALLINT     NOT NULL COMMENT 'Outpatient visits, prior 12 months',
    number_emergency         SMALLINT     NOT NULL COMMENT 'ER visits, prior 12 months',
    number_inpatient         SMALLINT     NOT NULL COMMENT 'Inpatient visits, prior 12 months',
    diag_1                   VARCHAR(10)  NULL COMMENT 'Primary diagnosis (ICD-9)',
    diag_2                   VARCHAR(10)  NULL,
    diag_3                   VARCHAR(10)  NULL,
    number_diagnoses         TINYINT      NOT NULL,
    max_glu_serum            VARCHAR(10)  NULL,
    a1c_result               VARCHAR(10)  NULL,
    insulin                  VARCHAR(10)  NOT NULL,
    med_change               VARCHAR(5)   NOT NULL COMMENT 'Ch = diabetes meds changed during stay',
    diabetes_med             VARCHAR(5)   NOT NULL,
    readmitted               VARCHAR(5)   NOT NULL COMMENT '<30 / >30 / NO',
    PRIMARY KEY (encounter_id),
    KEY ix_enc_patient   (patient_nbr),
    KEY ix_enc_readmit   (readmitted),
    KEY ix_enc_age       (age),
    KEY ix_enc_disp      (discharge_disposition_id),
    KEY ix_enc_inpatient (number_inpatient)
) ENGINE=InnoDB;

-- Lookup: admission type / discharge disposition / admission source
CREATE TABLE IF NOT EXISTS id_mapping (
    id_type     VARCHAR(40) NOT NULL COMMENT 'admission_type_id / discharge_disposition_id / admission_source_id',
    id_value    TINYINT     NOT NULL,
    description VARCHAR(120) NULL,
    PRIMARY KEY (id_type, id_value)
) ENGINE=InnoDB;
