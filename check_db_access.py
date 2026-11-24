# Checks that the test program can read the HMS database (state evidence) and see the markers.
import pymysql

DB = dict(host="localhost", user="hms_ro", password="furqan123", database="binaryte_hms")

conn = pymysql.connect(**DB)

def rows(sql, args=()):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()

print("Markers found (expect 8 rows):")
for r in rows("SELECT 'patient', patient_id, name FROM patient WHERE name LIKE %s "
              "UNION ALL SELECT 'doctor', doctor_id, name FROM doctor WHERE name LIKE %s "
              "UNION ALL SELECT 'prescription', prescription_id, case_history FROM prescription WHERE case_history LIKE %s "
              "UNION ALL SELECT 'invoice', invoice_id, title FROM invoice WHERE title LIKE %s",
              ("%MARK_%",) * 4):
    print(" ", r)

def appointment_state():
    return rows("SELECT COUNT(*), MAX(appointment_id) FROM appointment")

before = appointment_state()
print("Appointments before (count, max id):", before)
input("Now, in the browser, log in as doctor 4, add ONE new appointment, then press Enter... ")
conn.commit()          # refresh the read view
after = appointment_state()
print("Appointments after (count, max id): ", after)
print("State changed:", before != after)
conn.close()