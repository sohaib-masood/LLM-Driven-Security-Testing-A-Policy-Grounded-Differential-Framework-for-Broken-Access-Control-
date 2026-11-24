import requests, re, sys, html
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
VIEW_APPT_URL = BASE_URL + "index.php?/patient/view_appointment"
MARKER = "MARK_D08_APPT_X"

def get_token(text):
    soup = BeautifulSoup(text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    return token_tag["value"] if token_tag and token_tag.has_attr("value") else None

def login(session):
    # GET login page
    resp = session.get(LOGIN_URL, verify=False)
    token = get_token(resp.text)
    if not token:
        print("FAIL - could not find authenticity_token on login page")
        sys.exit(1)

    payload = {
        "login_type": "patient",
        "email": "bilal@gmail.com",
        "password": "bilal123",
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, verify=False)
    if 'name="login_type"' in resp.text:
        print("FAIL - login failed")
        sys.exit(1)
    # login succeeded
    return True

def check_marker(resp_text):
    return MARKER in resp_text

def attempt_get(session):
    resp = session.get(VIEW_APPT_URL, verify=False)
    allowed = check_marker(resp.text)
    expected = False  # deny
    if allowed == expected:
        print("GET attempt: PASS - access denied as expected")
    else:
        print("GET attempt: FAIL - victim marker was present")

def attempt_post(session):
    # GET page first to obtain fresh token
    resp = session.get(VIEW_APPT_URL, verify=False)
    token = get_token(resp.text)
    if not token:
        print("FAIL - could not find authenticity_token on view_appointment page")
        return

    payload = {
        "authenticity_token": token,
        "patient_id": "8"   # forged victim id
    }
    resp = session.post(VIEW_APPT_URL, data=payload, verify=False)
    allowed = check_marker(resp.text)
    expected = False  # deny
    if allowed == expected:
        print("POST attempt: PASS - access denied as expected")
    else:
        print("POST attempt: FAIL - victim marker was present")

def main():
    sess = requests.Session()
    # suppress insecure warnings if HTTPS with self‑signed certs
    requests.packages.urllib3.disable_warnings()
    login(sess)

    attempt_get(sess)
    attempt_post(sess)

if __name__ == "__main__":
    main()