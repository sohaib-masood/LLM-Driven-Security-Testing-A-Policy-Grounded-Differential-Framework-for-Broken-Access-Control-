import requests, re, sys, urllib.parse

BASE = "http://localhost/hms/"
LOGIN_URL = urllib.parse.urljoin(BASE, "index.php?/login")
VIEW_APPT_URL = urllib.parse.urljoin(BASE, "index.php?/patient/view_appointment")
MARKER = "MARK_D08_APPT_X"

def get_token(session, url):
    """Fetch a page and return the value of the hidden input named authenticity_token."""
    resp = session.get(url, timeout=10)
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', resp.text)
    return m.group(1) if m else None

def is_transport_denied(resp):
    """Return True if response indicates a redirect/refresh (i.e., denied by transport)."""
    if 300 <= resp.status_code < 400:
        return True
    if resp.headers.get('Refresh'):
        return True
    if re.search(r'<meta\s+http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def login(session):
    # get login page for token
    token = get_token(session, LOGIN_URL)
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
        print("FAIL login: login page still present")
        sys.exit(1)
    # login succeeded
    return True

def test_own_view(session):
    # P309: patient view own appointment – allowed
    resp = session.get(VIEW_APPT_URL, timeout=10)
    denied = is_transport_denied(resp)
    if denied:
        print("FAIL P309 own GET: transport denied (expected allowed)")
        return
    if resp.status_code >= 500:
        print(f"FAIL P309 own GET: server error {resp.status_code}")
        return
    # No marker check needed for own; just ensure not denied
    print("PASS P309 own GET")

def test_other_view_get(session):
    # P310: patient view other appointment via GET – denied
    params = {"patient_id": "8"}
    resp = session.get(VIEW_APPT_URL, params=params, timeout=10)
    denied = is_transport_denied(resp)
    marker_present = MARKER in resp.text
    if marker_present:
        print("FAIL P310 other GET: marker found (other data leaked)")
    else:
        # either transport denial or simply no marker = correct denial
        print("PASS P310 other GET")

def test_other_view_post(session):
    # P310: patient view other appointment via POST – denied
    # first fetch token from the view page
    token = get_token(session, VIEW_APPT_URL)
    if not token:
        print("FAIL P310 other POST: could not obtain authenticity_token")
        return
    payload = {
        "authenticity_token": token,
        "patient_id": "8"
    }
    resp = session.post(VIEW_APPT_URL, data=payload, timeout=10)
    denied = is_transport_denied(resp)
    marker_present = MARKER in resp.text
    if marker_present:
        print("FAIL P310 other POST: marker found (other data leaked)")
    else:
        print("PASS P310 other POST")

def main():
    sess = requests.Session()
    login(sess)
    test_own_view(sess)
    test_other_view_get(sess)
    test_other_view_post(sess)

if __name__ == "__main__":
    main()