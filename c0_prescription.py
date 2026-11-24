import requests, re, sys
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
VIEW_URL_TEMPLATE = BASE_URL + "index.php?/patient/view_prescription/edit/{}"

ATTACKER = {
    "login_type": "patient",
    "email": "bilal@gmail.com",
    "password": "bilal123"
}

VICTIM_MARKER = "MARK_RX05_X"
OWN_ID = 3
VICTIM_ID = 5

def get_auth_token(session):
    resp = session.get(LOGIN_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if not token_tag or not token_tag.has_attr("value"):
        sys.exit("Failed to locate authenticity_token on login page")
    return token_tag["value"]

def login(session):
    token = get_auth_token(session)
    payload = {
        "login_type": ATTACKER["login_type"],
        "email": ATTACKER["email"],
        "password": ATTACKER["password"],
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    resp.raise_for_status()
    # login fails if the login page is rendered again (contains the login_type field)
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed for attacker account")
    return True

def fetch_page(session, presc_id):
    url = VIEW_URL_TEMPLATE.format(presc_id)
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text

def main():
    sess = requests.Session()
    login(sess)

    # Baseline request (own prescription)
    own_page = fetch_page(sess, OWN_ID)
    if VICTIM_MARKER in own_page:
        print("FAIL Baseline request unexpectedly contains victim marker")
    else:
        # we only need to ensure the request succeeded; no marker expected
        print("PASS Baseline request succeeded without victim data")

    # Attack request (victim prescription)
    victim_page = fetch_page(sess, VICTIM_ID)
    if VICTIM_MARKER in victim_page:
        print("FAIL Attack allowed – victim marker found")
    else:
        print("PASS Attack denied – victim marker absent")

if __name__ == "__main__":
    main()