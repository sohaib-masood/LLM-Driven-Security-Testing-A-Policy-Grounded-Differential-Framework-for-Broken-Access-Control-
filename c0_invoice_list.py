import requests, re, sys
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
VIEW_INVOICE_URL = BASE_URL + "index.php?/patient/view_invoice"
MARKER = "MARK_INV08_X"

def get_auth_token(session, url):
    resp = session.get(url, verify=False)
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if not token_tag or not token_tag.has_attr("value"):
        print("FAIL: Could not find authenticity_token")
        sys.exit(1)
    return token_tag["value"]

def login_as_patient(session, email, password):
    # Get login page to fetch token
    token = get_auth_token(session, LOGIN_URL)

    payload = {
        "login_type": "patient",
        "email": email,
        "password": password,
        "authenticity_token": token
    }

    resp = session.post(LOGIN_URL, data=payload, verify=False)
    # login fails if the response still contains the login form field name
    if 'name="login_type"' in resp.text:
        print("FAIL: Login failed for attacker account")
        sys.exit(1)
    # otherwise login succeeded
    return True

def check_access(session):
    resp = session.get(VIEW_INVOICE_URL, verify=False)
    if MARKER in resp.text:
        return "ALLOW"
    else:
        return "DENY"

def main():
    sess = requests.Session()
    # Disable warnings for self‑signed certs if any
    requests.packages.urllib3.disable_warnings()

    # Step 1: login as attacker (patient)
    login_as_patient(sess, "bilal@gmail.com", "bilal123")

    # Step 2: perform the attack attempt (GET patient/view_invoice)
    decision = check_access(sess)

    # Expected decision is DENY
    if decision == "DENY":
        print("PASS: Access correctly denied")
    else:
        print("FAIL: Access was allowed (marker found)")

if __name__ == "__main__":
    main()