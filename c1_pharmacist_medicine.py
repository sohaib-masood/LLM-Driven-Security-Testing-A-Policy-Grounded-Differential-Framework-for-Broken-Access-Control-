import requests, re, sys, html
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
TARGET_PATH = "pharmacist/manage_medicine"
TARGET_URL = BASE_URL + f"index.php?/{TARGET_PATH}"

# ---------- helpers ----------
def get_auth_token(session, url):
    """Fetch a page and extract the hidden authenticity_token value."""
    resp = session.get(url, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to load page for token: {url}")
    # look for <input type="hidden" name="authenticity_token" value="...">
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if not token_tag or not token_tag.get("value"):
        raise RuntimeError("authenticity_token not found")
    return token_tag["value"]

def is_transport_denied(resp):
    """Detect denial via redirects, Refresh header or meta‑refresh tag."""
    # classic 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # meta‑refresh tag
    if re.search(r'<meta[^>]+http-equiv=["\']?refresh["\']?', resp.text, re.I):
        return True
    return False

def login_pharmacist():
    sess = requests.Session()
    # get login page
    try:
        token = get_auth_token(sess, LOGIN_URL)
    except Exception as e:
        sys.exit(f"Login page error: {e}")

    payload = {
        "login_type": "pharmacist",
        "email": "hassan@yahoo.com",
        "password": "hassan123",
        "authenticity_token": token
    }
    resp = sess.post(LOGIN_URL, data=payload, timeout=10)
    # login failed if the response still contains the login form field
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed – login form still present.")
    return sess

def test_get(session):
    resp = session.get(TARGET_URL, timeout=10)
    denied = is_transport_denied(resp)
    # Decision for this row is ALLOWED
    if denied:
        return False, "GET was denied (redirect/Refresh detected)"
    if resp.status_code != 200:
        return False, f"GET returned unexpected status {resp.status_code}"
    return True, "GET allowed"

def test_post(session):
    # obtain fresh token from the target page
    try:
        token = get_auth_token(session, TARGET_URL)
    except Exception as e:
        return False, f"Failed to obtain token for POST: {e}"

    # forged field – name guessed as medicine_id (value arbitrary)
    payload = {
        "authenticity_token": token,
        "medicine_id": "999"   # forged identifier
    }
    resp = session.post(TARGET_URL, data=payload, timeout=10)
    denied = is_transport_denied(resp)
    if denied:
        return False, "POST was denied (redirect/Refresh detected)"
    if resp.status_code != 200:
        return False, f"POST returned unexpected status {resp.status_code}"
    return True, "POST allowed"

# ---------- main ----------
if __name__ == "__main__":
    sess = login_pharmacist()

    ok, msg = test_get(sess)
    print("GET pharmacist/manage_medicine :", "PASS" if ok else "FAIL", "-", msg)

    ok, msg = test_post(sess)
    print("POST pharmacist/manage_medicine :", "PASS" if ok else "FAIL", "-", msg)