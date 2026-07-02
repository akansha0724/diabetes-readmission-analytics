-- =============================================================================
-- Healthcare Readmission Analytics — analytical query set
-- Business question: which patients bounce back within 30 days, and why?
-- Run: mysql healthcare_analytics < sql/02_analysis_queries.sql
-- =============================================================================
USE healthcare_analytics;

-- Q1. Overall 30-day readmission rate
SELECT
    COUNT(*)                                             AS encounters,
    SUM(readmitted = '<30')                              AS readmit_30d,
    ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2)   AS readmit_30d_pct
FROM encounters;

-- Q2. Readmission rate by age band (does risk climb with age?)
SELECT
    age,
    COUNT(*)                                             AS encounters,
    ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2)   AS readmit_30d_pct
FROM encounters
GROUP BY age
ORDER BY age;

-- Q3. Prior inpatient visits — the "frequent flyer" effect
SELECT
    LEAST(number_inpatient, 5)                           AS prior_inpatient_visits,
    COUNT(*)                                             AS encounters,
    ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2)   AS readmit_30d_pct
FROM encounters
GROUP BY LEAST(number_inpatient, 5)
ORDER BY prior_inpatient_visits;

-- Q4. Length of stay vs readmission (window function: decile analysis)
WITH los AS (
    SELECT
        time_in_hospital,
        readmitted,
        NTILE(4) OVER (ORDER BY time_in_hospital) AS los_quartile
    FROM encounters
)
SELECT
    los_quartile,
    MIN(time_in_hospital) AS min_days,
    MAX(time_in_hospital) AS max_days,
    COUNT(*)              AS encounters,
    ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2) AS readmit_30d_pct
FROM los
GROUP BY los_quartile
ORDER BY los_quartile;

-- Q5. Discharge disposition — where patients go matters
SELECT
    m.description                                        AS discharge_to,
    COUNT(*)                                             AS encounters,
    ROUND(100 * SUM(e.readmitted = '<30') / COUNT(*), 2) AS readmit_30d_pct
FROM encounters e
JOIN id_mapping m
  ON m.id_type = 'discharge_disposition_id' AND m.id_value = e.discharge_disposition_id
GROUP BY m.description
HAVING COUNT(*) >= 500
ORDER BY readmit_30d_pct DESC
LIMIT 10;

-- Q6. Does an HbA1c test (and acting on it) reduce readmission?
--     (the original research question of the Strack et al. paper)
SELECT
    CASE
        WHEN a1c_result IS NULL              THEN '1. Not measured'
        WHEN a1c_result IN ('>7','>8')
         AND med_change = 'Ch'               THEN '3. High + meds changed'
        WHEN a1c_result IN ('>7','>8')       THEN '2. High + no change'
        ELSE                                      '4. Normal'
    END                                              AS a1c_group,
    COUNT(*)                                         AS encounters,
    ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2) AS readmit_30d_pct
FROM encounters
GROUP BY a1c_group
ORDER BY a1c_group;

-- Q7. Medication burden deciles (polypharmacy signal), window function
WITH meds AS (
    SELECT num_medications, readmitted,
           NTILE(10) OVER (ORDER BY num_medications) AS med_decile
    FROM encounters
)
SELECT med_decile,
       MIN(num_medications) AS min_meds,
       MAX(num_medications) AS max_meds,
       ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2) AS readmit_30d_pct
FROM meds
GROUP BY med_decile
ORDER BY med_decile;

-- Q8. Primary diagnosis chapter (ICD-9 grouped) ranked by readmission risk
SELECT
    CASE
        WHEN diag_1 LIKE 'V%' OR diag_1 LIKE 'E%' THEN 'Other (V/E codes)'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 390 AND 459 THEN 'Circulatory'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 460 AND 519 THEN 'Respiratory'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 520 AND 579 THEN 'Digestive'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 250 AND 251 THEN 'Diabetes'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 800 AND 999 THEN 'Injury'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 710 AND 739 THEN 'Musculoskeletal'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 580 AND 629 THEN 'Genitourinary'
        WHEN CAST(diag_1 AS DECIMAL(6,2)) BETWEEN 140 AND 239 THEN 'Neoplasms'
        ELSE 'Other'
    END AS diagnosis_chapter,
    COUNT(*) AS encounters,
    ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2) AS readmit_30d_pct
FROM encounters
WHERE diag_1 IS NOT NULL
GROUP BY diagnosis_chapter
ORDER BY readmit_30d_pct DESC;

-- Q9. Repeat encounters: patients ranked by admission count (top of the cost curve)
WITH per_patient AS (
    SELECT patient_nbr,
           COUNT(*)                            AS admissions,
           SUM(readmitted = '<30')             AS readmits_30d,
           SUM(time_in_hospital)               AS total_bed_days
    FROM encounters
    GROUP BY patient_nbr
)
SELECT
    CASE WHEN admissions >= 5 THEN '5+' ELSE CAST(admissions AS CHAR) END AS admission_bucket,
    COUNT(*)                       AS patients,
    ROUND(AVG(total_bed_days), 1)  AS avg_bed_days,
    ROUND(100 * SUM(readmits_30d > 0) / COUNT(*), 2) AS pct_with_30d_readmit
FROM per_patient
GROUP BY admission_bucket
ORDER BY MIN(admissions);

-- Q10. Insulin regime vs outcome for diabetes-medicated patients
SELECT
    insulin,
    med_change AS meds_changed,
    COUNT(*)   AS encounters,
    ROUND(100 * SUM(readmitted = '<30') / COUNT(*), 2) AS readmit_30d_pct
FROM encounters
WHERE diabetes_med = 'Yes'
GROUP BY insulin, med_change
ORDER BY readmit_30d_pct DESC;
