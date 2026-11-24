import requests
import re

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
ADMIN_MANAGE_DOCTOR = BASE_URL + "index.php?/admin/manage_doctor"
MARKER = "MARK_D04_X"

def get_auth_token(session):
    resp = session.get(LOGIN_URL, timeout=10)
    resp.raise_for_status()
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', resp.text)
    if not m:
        raise ValueError("authenticity_token not found on login page")
    return m.group(1)

def login_as_patient():
    sess = requests.Session()
    token = get_auth_token(sess)
    payload = {
        "login_type": "patient",
        "email": "bilal@gmail.com",
        "password": "bilal123",
        "authenticity_token": token
    }
    resp = sess.post(LOGIN_URL, data=payload, timeout=10)
    resp.raise_for_status()
    # login fails if the login page marker is still present
    if 'name="login_type"' in resp.text:
        raise RuntimeError("Login failed for patient account")
    return sess

def check_marker(resp_text):
    return MARKER in resp_text

def attempt(session, description):
    resp = session.get(ADMIN_MANAGE_DOCTOR, timeout=10)
    resp.raise_for_status()
    allowed = check_marker(resp.text)
    if allowed:
        print(f"FAIL {description}: Marker found - access allowed")
    else:
        print(f"PASS {description}: Marker not found - access denied")

def main():
    # 1. Login as patient
    patient_session = login_as_patient()

    # 2. Attempt while logged in as patient (should be denied)
    attempt(patient_session, "Logged‑in patient attempt")

    # 3. Attempt with no active session (should be denied)
    anon_session = requests.Session()  # fresh session, not logged in
    attempt(anon_session, "Unauthenticated attempt")

if __name__ == "__main__":
    main()