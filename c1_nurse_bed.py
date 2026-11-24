import requests, re, sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
TARGET_PATH = "nurse/manage_bed"
TARGET_URL = BASE_URL + f"index.php?/{TARGET_PATH}"

# credentials
LOGIN_DATA = {
    "login_type": "admin",
    "email": "admin@admin.com",
    "password": "admin123",
}

TOKEN_REGEX = re.compile(r'<input[^>]+name=["\']authenticity_token["\'][^>]+value=["\']([^"\']+)["\']', re.I)

def fetch_token(session, url):
    resp = session.get(url, timeout=10)
    m = TOKEN_REGEX.search(resp.text)
    if not m:
        print(f"ERROR: authenticity_token not found at {url}")
        sys.exit(1)
    return m.group(1)

def is_denied(resp):
    # classic 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if "Refresh" in resp.headers:
        return True
    # meta refresh tag
    if re.search(r'<meta\s+http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def login(session):
    # get login page to obtain token
    token = fetch_token(session, LOGIN_URL)
    data = LOGIN_DATA.copy()
    data["authenticity_token"] = token
    resp = session.post(LOGIN_URL, data=data, timeout=10)
    # login failed if the login form is still present
    if 'name="login_type"' in resp.text:
        print("ERROR: Login failed")
        sys.exit(1)

def test_get(session):
    resp = session.get(TARGET_URL, timeout=10)
    denied = is_denied(resp)
    expected = True  # admin should be denied
    if denied == expected:
        print("GET /nurse/manage_bed: PASS")
    else:
        print(f"GET /nurse/manage_bed: FAIL (expected denied={expected}, got denied={denied})")

def test_post(session):
    # first GET to obtain fresh token
    token = fetch_token(session, TARGET_URL)
    # forged field – name unknown, using a generic placeholder
    forged_field_name = "bed_id"
    forged_field_value = "999"
    data = {
        "authenticity_token": token,
        forged_field_name: forged_field_value,
    }
    resp = session.post(TARGET_URL, data=data, timeout=10)
    denied = is_denied(resp)
    expected = True  # admin should be denied
    if denied == expected:
        print("POST /nurse/manage_bed: PASS")
    else:
        print(f"POST /nurse/manage_bed: FAIL (expected denied={expected}, got denied={denied})")

def main():
    session = requests.Session()
    login(session)
    test_get(session)
    test_post(session)

if __name__ == "__main__":
    main()