import re
import sys
import requests

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
MANAGE_DOCTOR_URL = BASE_URL + "index.php?/admin/manage_doctor"
MARKER = "MARK_D04_X"

def get_authenticity_token(session):
    resp = session.get(LOGIN_URL, timeout=10)
    if resp.status_code != 200:
        sys.exit("Failed to load login page")
    m = re.search(r'<input[^>]*name=["\']authenticity_token["\'][^>]*value=["\']([^"\']+)["\']', resp.text)
    if not m:
        sys.exit("authenticity_token not found")
    return m.group(1)

def login_as_patient(session):
    token = get_authenticity_token(session)
    payload = {
        "login_type": "patient",
        "email": "bilal@gmail.com",
        "password": "bilal123",
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed for patient")
    return resp

def test_manage_doctor(session, expected_allowed):
    resp = session.get(MANAGE_DOCTOR_URL, timeout=10)
    marker_present = MARKER in resp.text
    observed_allowed = marker_present
    if observed_allowed == expected_allowed:
        print("PASS: patient manage doctors - expected {}, observed {}".format(
            "allowed" if expected_allowed else "denied",
            "allowed" if observed_allowed else "denied"))
    else:
        print("FAIL: patient manage doctors - expected {}, observed {} (marker {}found)".format(
            "allowed" if expected_allowed else "denied",
            "allowed" if observed_allowed else "denied",
            "" if marker_present else "not "))

def main():
    session = requests.Session()
    login_as_patient(session)
    # Matrix row: patient | manage doctors | doctor account | none | denied
    test_manage_doctor(session, expected_allowed=False)

if __name__ == "__main__":
    main()