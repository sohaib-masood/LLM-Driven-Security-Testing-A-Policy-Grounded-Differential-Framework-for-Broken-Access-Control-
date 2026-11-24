import re
import sys
import requests

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
VIEW_INVOICE_URL = BASE_URL + "index.php?/patient/view_invoice/{}"

DOCTOR_EMAIL = "Rizwan@yahoo.com"
DOCTOR_PASSWORD = "rizwan123"
DOCTOR_ROLE = "doctor"

# IDs to test – adjust if you know real IDs in your DB
OWN_INVOICE_ID = "1"      # assumed to belong to the logged‑in doctor
OTHER_INVOICE_ID = "2"    # contains the marker "MARK_INV03_X"

MARKER = "MARK_INV03_X"

session = requests.Session()

def fetch_auth_token():
    resp = session.get(LOGIN_URL, timeout=10)
    if resp.status_code != 200:
        sys.exit("FAIL: Unable to load login page")
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', resp.text)
    if not m:
        sys.exit("FAIL: authenticity_token not found")
    return m.group(1)

def login():
    token = fetch_auth_token()
    payload = {
        "login_type": DOCTOR_ROLE,
        "email": DOCTOR_EMAIL,
        "password": DOCTOR_PASSWORD,
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    if "name=\"login_type\"" in resp.text:
        sys.exit("FAIL: Login failed")
    # login succeeded
    print("Login successful")

def test_own_invoice():
    url = VIEW_INVOICE_URL.format(OWN_INVOICE_ID)
    resp = session.get(url, timeout=10)
    if resp.status_code != 200:
        print("FAIL: own invoice – HTTP %s (expected 200)" % resp.status_code)
        return
    if "Error" in resp.text or "exception" in resp.text.lower():
        print("FAIL: own invoice – server error detected")
        return
    # According to matrix, doctor viewing own invoice is not defined;
    # we treat the generic "own" check as allowed (200) for the purpose of this test.
    print("PASS: own invoice – returned 200 without error")

def test_other_invoice():
    url = VIEW_INVOICE_URL.format(OTHER_INVOICE_ID)
    resp = session.get(url, timeout=10)
    marker_present = MARKER in resp.text
    # Matrix says doctor viewing other invoice should be denied → marker must NOT appear
    if marker_present:
        print("FAIL: other invoice – marker found, access was allowed but should be denied")
    else:
        print("PASS: other invoice – marker not found, access correctly denied")

if __name__ == "__main__":
    login()
    test_own_invoice()
    test_other_invoice()