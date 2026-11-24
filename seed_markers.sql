-- HMS test data for the BAC experiment. Database: binaryte_hms
-- Run in phpMyAdmin: select the database, open the SQL tab, paste, click Go.
-- Safe to run more than once.

-- 1. Markers (fixed length, no overlap)
UPDATE patient SET name = CONCAT(REPLACE(name, ' MARK_P03_X', ''), ' MARK_P03_X') WHERE patient_id = 3;
UPDATE patient SET name = CONCAT(REPLACE(name, ' MARK_P08_X', ''), ' MARK_P08_X') WHERE patient_id = 8;
UPDATE doctor  SET name = CONCAT(REPLACE(name, ' MARK_D04_X', ''), ' MARK_D04_X') WHERE doctor_id  = 4;
UPDATE doctor  SET name = CONCAT(REPLACE(name, ' MARK_D06_X', ''), ' MARK_D06_X') WHERE doctor_id  = 6;
UPDATE prescription SET case_history = CONCAT(REPLACE(case_history, ' MARK_RX03_X', ''), ' MARK_RX03_X') WHERE prescription_id = 3;

-- 2. One prescription for a second existing patient (patient 8)
DELETE FROM prescription WHERE prescription_id = 5;
INSERT INTO prescription
  (prescription_id, creation_timestamp, doctor_id, patient_id, case_history, medication, medication_from_pharmacist, description)
VALUES
  (5, 1785500000, 6, 8, 'Fever MARK_RX05_X', 'Paracetamol', '', 'Seed record for access-control tests');

-- 3. One invoice for each of two existing patients
DELETE FROM invoice WHERE invoice_id IN (3, 4);
INSERT INTO invoice
  (invoice_id, patient_id, title, description, amount, creation_timestamp, status)
VALUES
  (3, 3, 'Consultation MARK_INV03_X', 'Seed invoice', 500, 1785500000, 'unpaid'),
  (4, 8, 'Consultation MARK_INV08_X', 'Seed invoice', 700, 1785500000, 'unpaid');

-- 4. Check: you should see 8 rows
SELECT 'patient' AS tbl, patient_id AS id, name AS text FROM patient WHERE name LIKE '%MARK_%'
UNION ALL SELECT 'doctor', doctor_id, name FROM doctor WHERE name LIKE '%MARK_%'
UNION ALL SELECT 'prescription', prescription_id, case_history FROM prescription WHERE case_history LIKE '%MARK_%'
UNION ALL SELECT 'invoice', invoice_id, title FROM invoice WHERE title LIKE '%MARK_%';

-- 5. Read-only account for the test program (run once; change the password)
-- CREATE USER 'hms_ro'@'localhost' IDENTIFIED BY 'CHOOSE_A_PASSWORD';
-- GRANT SELECT ON binaryte_hms.* TO 'hms_ro'@'localhost';
-- FLUSH PRIVILEGES;
