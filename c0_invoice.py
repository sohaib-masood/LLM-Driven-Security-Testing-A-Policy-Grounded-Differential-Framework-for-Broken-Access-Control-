import requests, re, sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
INVOICE_URL = BASE_URL + "index.php?/patient/view_invoice"
MARKER = "MARK_INV03_X"

def get_auth_token(session):
    resp = session.get(LOGIN_URL, timeout=10)
    if resp.status_code != 200:
        sys.exit("Failed to load login page")
    m = re.search(r'<input[^>]*name=["\']authenticity_token["\'][^>]*value=["\']([^"\']+)["\']', resp.text)
    if not m:
        sys.exit("authenticity_token not found")
    return m.group(1)

def login_as_doctor():
    sess = requests.Session()
    token = get_auth_token(sess)
    payload = {
        "login_type": "doctor",
        "email": "Rizwan@yahoo.com",
        "password": "rizwan123",
        "authenticity_token": token
    }
    resp = sess.post(LOGIN_URL, data=payload, timeout=10)
    if "name=\"login_type\"" in resp.text:
        sys.exit("Login failed")
    return sess

def contains_marker(text):
    return MARKER in text

def attempt(session, description):
    # Baseline request (should not contain marker)
    baseline_resp = session.get(INVOICE_URL, timeout=10)
    # Attack request (same endpoint; marker presence decides outcome)
    attack_resp = session.get(INVOICE_URL, timeout=10)
    allowed = contains_marker(attack_resp.text)
    if allowed:
        print(f"{description}: FAIL - access allowed (marker found)")
    else:
        print(f"{description}: PASS - access denied (marker not found)")

def main():
    # Attempt 1: logged‑in doctor
    doctor_session = login_as_doctor()
    attempt(doctor_session, "Attempt 1 (logged‑in doctor)")

    # Attempt 2: no active session
    anon_session = requests.Session()  # no login performed
    attempt(anon_session, "Attempt 2 (no session)")

if __name__ == "__main__":
    main()