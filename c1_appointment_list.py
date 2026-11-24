import requests, re, sys, html
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
MANAGE_APPT_URL = BASE_URL + "index.php?/doctor/manage_appointment"
USERNAME = "Rizwan@yahoo.com"
PASSWORD = "rizwan123"
ROLE = "doctor"
MARKER = "MARK_D06_X"

def extract_token(text):
    soup = BeautifulSoup(text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    return token_tag["value"] if token_tag and token_tag.has_attr("value") else None

def is_transport_denied(resp):
    # classic 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # meta refresh tag
    if b'<meta http-equiv="refresh"' in resp.content.lower():
        return True
    return False

def check_response(resp, expect_allowed):
    # If marker present => other data rendered => allowed
    marker_present = MARKER in resp.text
    if marker_present:
        observed_allowed = True
    else:
        # No marker, treat transport denial as decision
        observed_allowed = not is_transport_denied(resp)
    return observed_allowed == expect_allowed, marker_present, is_transport_denied(resp)

def login(session):
    # GET login page
    r = session.get(LOGIN_URL)
    token = extract_token(r.text)
    if not token:
        print("FAIL: Could not find authenticity_token on login page")
        sys.exit(1)

    payload = {
        "login_type": ROLE,
        "email": USERNAME,
        "password": PASSWORD,
        "authenticity_token": token
    }
    r = session.post(LOGIN_URL, data=payload)
    if 'name="login_type"' in r.text:
        print("FAIL: Login failed")
        sys.exit(1)
    # login succeeded
    return True

def test_get(session):
    r = session.get(MANAGE_APPT_URL)
    ok, marker_present, transport_denied = check_response(r, expect_allowed=False)
    if ok:
        print("PASS: GET request correctly denied")
    else:
        reason = []
        if marker_present:
            reason.append("other data rendered (marker found)")
        if transport_denied:
            reason.append("transport denial detected")
        else:
            reason.append("unexpected allow")
        print(f"FAIL: GET request denied incorrectly – {'; '.join(reason)}")

def test_post(session):
    # First GET to obtain fresh token
    r_get = session.get(MANAGE_APPT_URL)
    token = extract_token(r_get.text)
    if not token:
        print("FAIL: Could not obtain authenticity_token for POST")
        return

    payload = {
        "authenticity_token": token,
        "appointment_id": "9999"   # forged identifier, assumed field name
    }
    r = session.post(MANAGE_APPT_URL, data=payload)
    ok, marker_present, transport_denied = check_response(r, expect_allowed=False)
    if ok:
        print("PASS: POST request correctly denied")
    else:
        reason = []
        if marker_present:
            reason.append("other data rendered (marker found)")
        if transport_denied:
            reason.append("transport denial detected")
        else:
            reason.append("unexpected allow")
        print(f"FAIL: POST request denied incorrectly – {'; '.join(reason)}")

def main():
    sess = requests.Session()
    login(sess)
    test_get(sess)
    test_post(sess)

if __name__ == "__main__":
    main()