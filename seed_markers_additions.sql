-- Additional seed data for the 14 new mutants (M13,M14,M16,M17,M19-M24,M26-M29).
-- Appends to seed_markers.sql; run this once after your existing seed_markers.sql, as one script
-- (so the @new_doctor_id and @any_bed_id variables below carry over between statements).
-- Nothing here touches the 12 original mutants' data, or any existing row.

-- payment: patient 8 (victim) gets a payment with a unique marker in description. (M21, M27)
INSERT INTO `payment` (`payment_type`, `transaction_id`, `invoice_id`, `patient_id`, `method`, `description`, `amount`, `timestamp`)
VALUES ('Consultation', 900008, 1, 8, 'cash', 'MARK_PAY08_X', 800, UNIX_TIMESTAMP());

-- report: patient 8 (victim) gets an operation-type report with a unique marker. (M23)
INSERT INTO `report` (`type`, `description`, `timestamp`, `doctor_id`, `patient_id`)
VALUES ('operation', 'MARK_OP08_X', UNIX_TIMESTAMP(), 6, 8);

-- a dedicated fake doctor whose name IS the marker, since the patient-side appointment list
-- shows doctor name + department but no patient-identifying text. (M20, M26)
INSERT INTO `doctor` (`name`, `email`, `password`, `address`, `phone`, `department_id`, `profile`)
VALUES ('MARK_D08_APPT_X', 'mark.d08.appt.x@example.invalid', 'unused123', 'n/a', '0000000000', 1, '');
SET @new_doctor_id = LAST_INSERT_ID();

-- appointment: patient 8 (victim) with the fake marker-doctor above. (M20, M26)
INSERT INTO `appointment` (`appointment_timestamp`, `doctor_id`, `patient_id`)
VALUES (UNIX_TIMESTAMP(), @new_doctor_id, 8);

-- bed_allotment: patient 8 (victim) gets a bed allotment row, on whichever bed happens to
-- exist first. (M22) -- the oracle looks up patient 8's own name from the DB at test time and
-- checks for it in the attacker's response, so no marker text is needed here, just the row.
SET @any_bed_id = (SELECT bed_id FROM bed ORDER BY bed_id LIMIT 1);
INSERT INTO `bed_allotment` (`bed_id`, `patient_id`, `allotment_timestamp`, `discharge_timestamp`)
VALUES (@any_bed_id, 8, UNIX_TIMESTAMP(), UNIX_TIMESTAMP() + 86400);

-- invoice: patient 8 (victim) gets an invoice with a unique marker in description. (M24)
INSERT INTO `invoice` (`patient_id`, `title`, `description`, `amount`, `creation_timestamp`, `status`)
VALUES (8, 'MARK_INV08_X_TITLE', 'MARK_INV08_X', 500, UNIX_TIMESTAMP(), 'unpaid');

-- Print the new doctor_id so you can confirm it matches what config.py expects
-- (config.py below queries it back itself at run time, so this is just for your own check).
SELECT @new_doctor_id AS new_doctor_id_for_M20_M26, @any_bed_id AS bed_id_used_for_M22;
