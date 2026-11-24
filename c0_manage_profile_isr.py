import requests, re, sys, pymysql, traceback

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
UPDATE_URL = BASE_URL + "index.php?/patient/manage_profile/update_profile_info"

ATTACKER = {
    "login_type": "patient",
    "email": "bilal@gmail.com",
    "password": "bilal123"
}

# ---------- helper ----------
def get_token(html):
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', html)
    return m.group(1) if m else None

def db_connect():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="binaryte_hms",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def get_phone(conn, patient_id):
    with conn.cursor() as cur:
        cur.execute("SELECT phone FROM patient WHERE patient_id=%s", (patient_id,))
        row = cur.fetchone()
        return row["phone"] if row else None

# ---------- login ----------
session = requests.Session()
try:
    resp = session.get(LOGIN_URL, timeout=10)
    token = get_token(resp.text)
    if not token:
        print("FAIL: Could not find authenticity_token on login page")
        sys.exit(1)

    login_data = {
        "login_type": ATTACKER["login_type"],
        "email": ATTACKER["email"],
        "password": ATTACKER["password"],
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=login_data, timeout=10)
    if 'name="login_type"' in resp.text:
        print("FAIL: Login failed for attacker")
        sys.exit(1)
except Exception as e:
    print(f"FAIL: Exception during login - {e}")
    sys.exit(1)

# ---------- pre‑attack DB state ----------
try:
    conn = db_connect()
    original_phone = get_phone(conn, 8)
except Exception as e:
    print(f"FAIL: Could not read DB before attack - {e}")
    sys.exit(1)

# ---------- craft attack ----------
try:
    resp = session.get(UPDATE_URL, timeout=10)
    token = get_token(resp.text)
    if not token:
        print("FAIL: Could not find authenticity_token on update page")
        sys.exit(1)

    attack_data = {
        "authenticity_token": token,
        "patient_id": "8",                     # forged
        "name": "Test User",
        "email": "testuser@example.com",
        "address": "123 Test St",
        "sex": "Male",
        "birth_date": "1990-01-01",
        "age": "30",
        "blood_group": "A+",
        "phone": "0000000008"
    }

    resp = session.post(UPDATE_URL, data=attack_data, timeout=10)
except Exception as e:
    print(f"FAIL: Exception during attack request - {e}")
    sys.exit(1)

# ---------- post‑attack DB state ----------
try:
    new_phone = get_phone(conn, 8)
    conn.close()
except Exception as e:
    print(f"FAIL: Could not read DB after attack - {e}")
    sys.exit(1)

# ---------- decision ----------
if original_phone == new_phone:
    print("PASS: Attack denied, victim phone unchanged")
else:
    print(f"FAIL: Attack succeeded, victim phone changed from {original_phone} to {new_phone}")
