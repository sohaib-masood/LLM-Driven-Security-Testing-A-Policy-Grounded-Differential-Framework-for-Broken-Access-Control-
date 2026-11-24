import requests, re, sys, urllib.parse

BASE = "http://localhost/hms/"
LOGIN_URL = urllib.parse.urljoin(BASE, "index.php?/login")
VIEW_URL = urllib.parse.urljoin(BASE, "index.php?/patient/view_admit_history")
OTHER_PATIENT_ID = "8"          # assumed other patient
MARKER = "None"                # marker that would indicate other data was rendered

def get_token(text):
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', text)
    return m.group(1) if m else None

def is_transport_denied(resp):
    # classic 3xx
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # meta refresh tag
    if re.search(r'<meta[^>]*http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def check_allowed(resp):
    # allowed if not transport denied and no server error
    if is_transport_denied(resp):
        return False
    if resp.status_code >= 500:
        return False
    return True

def check_denied_other(resp):
    # denied if transport denied OR marker not present
    if is_transport_denied(resp):
        return True
    if MARKER not in resp.text:
        return True
    return False

session = requests.Session()

# ---------- login ----------
login_page = session.get(LOGIN_URL, verify=False)
token = get_token(login_page.text)
if not token:
    print("FAIL: Could not find authenticity_token on login page")
    sys.exit(1)

login_data = {
    "login_type": "patient",
    "email": "bilal@gmail.com",
    "password": "bilal123",
    "authenticity_token": token
}
login_resp = session.post(LOGIN_URL, data=login_data, verify=False)
if 'name="login_type"' in login_resp.text:
    print("FAIL: Login failed")
    sys.exit(1)
# ---------- end login ----------

def test_own_get():
    resp = session.get(VIEW_URL, verify=False)
    allowed = check_allowed(resp)
    if allowed:
        print("P301 GET PASS: own view allowed")
    else:
        print("P301 GET FAIL: own view denied unexpectedly")

def test_own_post():
    # get fresh token from the view page
    page = session.get(VIEW_URL, verify=False)
    token = get_token(page.text) or ""
    data = {"authenticity_token": token}
    resp = session.post(VIEW_URL, data=data, verify=False)
    allowed = check_allowed(resp)
    if allowed:
        print("P301 POST PASS: own view allowed")
    else:
        print("P301 POST FAIL: own view denied unexpectedly")

def test_other_get():
    url = VIEW_URL + "?patient_id=" + OTHER_PATIENT_ID
    resp = session.get(url, verify=False)
    denied = check_denied_other(resp)
    if denied:
        print("P302 GET PASS: other view correctly denied")
    else:
        print("P302 GET FAIL: other view was allowed")

def test_other_post():
    # get fresh token
    page = session.get(VIEW_URL, verify=False)
    token = get_token(page.text) or ""
    data = {
        "authenticity_token": token,
        "patient_id": OTHER_PATIENT_ID
    }
    resp = session.post(VIEW_URL, data=data, verify=False)
    denied = check_denied_other(resp)
    if denied:
        print("P302 POST PASS: other view correctly denied")
    else:
        print("P302 POST FAIL: other view was allowed")

# Run tests
test_own_get()
test_own_post()
test_other_get()
test_other_post()