import requests, re, sys, urllib.parse

BASE = "http://localhost/hms/"
LOGIN_URL = urllib.parse.urljoin(BASE, "index.php?/login")
VIEW_URL = urllib.parse.urljoin(BASE, "index.php?/patient/view_invoice")
TOKEN_NAME = "authenticity_token"
MARKER = "MARK_INV08_X"

def get_token(text):
    m = re.search(r'<input[^>]+name=["\']{}["\'][^>]+value=["\']([^"\']+)["\']'.format(TOKEN_NAME), text)
    return m.group(1) if m else None

def is_transport_denied(resp):
    # classic 3xx
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # meta refresh tag
    if re.search(r'<meta[^>]+http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def login(session):
    # get login page
    r = session.get(LOGIN_URL, timeout=10)
    token = get_token(r.text)
    if not token:
        print("FAIL login: cannot find authenticity_token")
        sys.exit(1)
    payload = {
        "login_type": "patient",
        "email": "bilal@gmail.com",
        "password": "bilal123",
        TOKEN_NAME: token
    }
    r = session.post(LOGIN_URL, data=payload, timeout=10)
    if 'name="login_type"' in r.text:
        print("FAIL login: login failed")
        sys.exit(1)
    # login succeeded
    return True

def test_get(session, ownership, expect_allowed):
    params = {}
    if ownership == "other":
        # forge an invoice id that likely belongs to another patient
        params["invoice_id"] = "9999"
    url = VIEW_URL
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    r = session.get(url, timeout=10)
    denied = is_transport_denied(r)
    marker_present = MARKER in r.text
    if expect_allowed:
        if denied:
            return False, "unexpected transport denial"
        # own case: just need 200 and no denial
        return True, "allowed as expected"
    else:
        # expect denial
        if denied:
            return True, "denied by transport"
        if marker_present:
            return False, "marker found, data leaked"
        # no transport denial and no marker -> treat as denial (no data shown)
        return True, "denied (no marker, no redirect)"
    
def test_post(session, ownership, expect_allowed):
    # first get fresh token
    r = session.get(VIEW_URL, timeout=10)
    token = get_token(r.text)
    if not token:
        return False, "cannot obtain authenticity_token for POST"
    payload = {TOKEN_NAME: token}
    if ownership == "other":
        payload["invoice_id"] = "9999"
    r = session.post(VIEW_URL, data=payload, timeout=10)
    denied = is_transport_denied(r)
    marker_present = MARKER in r.text
    if expect_allowed:
        if denied:
            return False, "unexpected transport denial"
        return True, "allowed as expected"
    else:
        if denied:
            return True, "denied by transport"
        if marker_present:
            return False, "marker found, data leaked"
        return True, "denied (no marker, no redirect)"

def main():
    s = requests.Session()
    login(s)

    tests = [
        ("own", "GET", True),
        ("own", "POST", True),
        ("other", "GET", False),
        ("other", "POST", False),
    ]

    for ownership, method, expect_allowed in tests:
        if method == "GET":
            ok, reason = test_get(s, ownership, expect_allowed)
        else:
            ok, reason = test_post(s, ownership, expect_allowed)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {ownership} {method}: {reason}")

if __name__ == "__main__":
    main()