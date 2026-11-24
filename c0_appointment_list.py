import requests, re, sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
MANAGE_APPT_URL = BASE_URL + "index.php?/doctor/manage_appointment"
ATTACKER_EMAIL = "Rizwan@yahoo.com"
ATTACKER_PASS = "rizwan123"
ATTACKER_ROLE = "doctor"
MARKER = "MARK_D06_X"

def get_token(session, url):
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', resp.text)
    if not m:
        sys.exit("Failed to find authenticity_token")
    return m.group(1)

def login(session):
    token = get_token(session, LOGIN_URL)
    payload = {
        "login_type": ATTACKER_ROLE,
        "email": ATTACKER_EMAIL,
        "password": ATTACKER_PASS,
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    resp.raise_for_status()
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed")
    # login succeeded
    return resp

def check_access(resp_text):
    return MARKER in resp_text

def main():
    sess = requests.Session()
    # Step 1: login as attacker
    login(sess)

    # Step 2: baseline / attack request (GET doctor/manage_appointment)
    resp = sess.get(MANAGE_APPT_URL, timeout=10)
    resp.raise_for_status()
    allowed = check_access(resp.text)

    # Expected decision: deny (i.e., marker should NOT be present)
    if not allowed:
        print("PASS: access correctly denied")
    else:
        print("FAIL: victim data was exposed (marker found)")

if __name__ == "__main__":
    main()