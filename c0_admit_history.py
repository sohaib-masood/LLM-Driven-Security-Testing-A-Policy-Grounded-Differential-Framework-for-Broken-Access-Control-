import requests, re, sys, html
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
VIEW_URL = BASE_URL + "index.php?/patient/view_admit_history"

ATTACKER = {
    "login_type": "patient",
    "email": "bilal@gmail.com",
    "password": "bilal123"
}

# victim identifier we will look for in the response
VICTIM_ID = "8"          # patient_id of the victim
# optional: a known part of the victim's name if you have it
VICTIM_NAME = None       # e.g. "John Doe"


def get_auth_token(session, url):
    """Fetch a page and extract the hidden authenticity_token value."""
    resp = session.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if not token_tag or not token_tag.has_attr("value"):
        return None
    return token_tag["value"]


def login(session):
    token = get_auth_token(session, LOGIN_URL)
    if not token:
        print("FAIL: Could not obtain authenticity_token for login")
        sys.exit(1)

    payload = {
        "login_type": ATTACKER["login_type"],
        "email": ATTACKER["email"],
        "password": ATTACKER["password"],
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)

    # login failed if the login page marker is still present
    if 'name="login_type"' in resp.text:
        print("FAIL: Login failed for attacker")
        sys.exit(1)
    # otherwise login succeeded
    return resp


def is_transport_denied(resp):
    """Detect CodeIgniter 'refresh' redirects or classic 3xx redirects."""
    # classic 3xx
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # meta refresh tag
    if '<meta http-equiv="refresh"' in resp.text.lower():
        return True
    return False


def check_victim_exposed(resp_text):
    """Return True if victim information appears in the response."""
    # If we have a known victim name, check that first
    if VICTIM_NAME and VICTIM_NAME.lower() in resp_text.lower():
        return True
    # Fallback: look for the victim id (e.g., as a link or plain number)
    # Use a simple regex to avoid matching the id inside other numbers
    pattern = r"\b" + re.escape(VICTIM_ID) + r"\b"
    if re.search(pattern, resp_text):
        return True
    return False


def main():
    session = requests.Session()

    # 1. Login as attacker
    login(session)

    # 2. Baseline / attack request (same request in this case)
    resp = session.get(VIEW_URL, timeout=10)

    # 3. Decide outcome
    denied_by_transport = is_transport_denied(resp)
    victim_exposed = check_victim_exposed(resp.text)

    # Expected decision: deny
    if denied_by_transport or not victim_exposed:
        print("PASS: deny (no victim data visible or transport denial)")
    else:
        print("FAIL: allow (victim data leaked)")

if __name__ == "__main__":
    main()