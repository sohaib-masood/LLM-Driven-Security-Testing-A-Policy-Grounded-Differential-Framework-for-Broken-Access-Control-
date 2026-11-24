import pymysql
from config import DB

conn = pymysql.connect(**DB)
cur = conn.cursor()
cur.execute("SELECT appointment_id, doctor_id, patient_id FROM appointment ORDER BY appointment_id")
for row in cur.fetchall():
    print(row)
conn.close()