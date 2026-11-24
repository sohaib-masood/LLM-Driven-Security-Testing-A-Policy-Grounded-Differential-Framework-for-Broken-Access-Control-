import requests, re, sys, html
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
VIEW_URL = BASE_URL + "index.php?/patient/view_operation_history"
MARKER = "MARK_OP08_X"

def get_auth_token(session, url):
    resp = session.get(url, timeout=10)
    if resp.status_code != 200:
        return None, resp
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if token_tag and token_tag.has_attr("value"):
        return token_tag["value"], resp
    return None, resp

def is_denied_by_transport(resp):
    # 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # Meta refresh tag
    if re.search(r'<meta[^>]+http-equiv=["\']?refresh["\']?', resp.text, re.I):
        return True
    return False

def login(session):
    token, resp = get_auth_token(session, LOGIN_URL)
    if not token:
        print("FAIL login: could not obtain authenticity_token")
        sys.exit(1)
    payload = {
        "login_type": "patient",
        "email": "bilal@gmail.com",
        "password": "bilal123",
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    if 'name="login_type"' in resp.text:
        print("FAIL login: login failed, login_type field still present")
        sys.exit(1)
    # login succeeded
    return True

def test_own_get(session):
    resp = session.get(VIEW_URL, timeout=10)
    if resp.status_code != 200:
        return False, f"expected 200, got {resp.status_code}"
    if is_denied_by_transport(resp):
        return False, "unexpected transport denial"
    return True, "own GET returned 200 without denial"

def test_other_get(session, other_id):
    params = {"patient_id": other_id}
    resp = session.get(VIEW_URL, params=params, timeout=10)
    # check marker
    if MARKER in resp.text:
        return False, "marker found, other data was rendered (should be denied)"
    # otherwise rely on transport denial
    if is_denied_by_transport(resp):
        return True, "denied by transport as expected"
    return False, "no marker and no transport denial (unexpected allow)"

def test_other_post(session, other_id):
    # fetch fresh token from the view page
    token, _ = get_auth_token(session, VIEW_URL)
    if not token:
        return False, "could not obtain authenticity_token for POST"
    payload = {
        "authenticity_token": token,
        "patient_id": other_id
    }
    resp = session.post(VIEW_URL, data=payload, timeout=10)
    if MARKER in resp.text:
        return False, "marker found in POST response (should be denied)"
    if is_denied_by_transport(resp):
        return True, "POST denied by transport as expected"
    return False, "POST neither marker nor transport denial (unexpected allow)"

def main():
    sess = requests.Session()
    login(sess)

    # Row P339: patient view operation history own allowed
    ok, reason = test_own_get(sess)
    print("PASS" if ok else "FAIL", f"P339 own GET: {reason}")

    # Row P340: patient view operation history other denied (GET)
    other_id = "9999"  # arbitrary ID that does not belong to the logged‑in patient
    ok, reason = test_other_get(sess, other_id)
    print("PASS" if ok else "FAIL", f"P340 other GET: {reason}")

    # Row P340: patient view operation history other denied (POST)
    ok, reason = test_other_post(sess, other_id)
    print("PASS" if ok else "FAIL", f"P340 other POST: {reason}")

if __name__ == "__main__":
    main()