import requests, re, sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
TOKEN_REGEX = re.compile(r'<input[^>]+name=["\']authenticity_token["\'][^>]+value=["\']([^"\']+)["\']', re.I)

def get_token(session):
    resp = session.get(LOGIN_URL, timeout=10)
    m = TOKEN_REGEX.search(resp.text)
    if not m:
        sys.exit("Failed to find authenticity_token on login page")
    return m.group(1)

def login(session, email, password):
    token = get_token(session)
    payload = {
        "login_type": "patient",
        "email": email,
        "password": password,
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    # login fails if the login form is still present
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed")
    return resp

def test_view_prescription(session, resource_id, expected_allowed, label):
    url = f"{BASE_URL}index.php?/patient/view_prescription/edit/{resource_id}"
    resp = session.get(url, timeout=10)
    # own resource: just need HTTP 200
    if label == "own":
        if resp.status_code == 200:
            result = "PASS"
            reason = ""
        else:
            result = "FAIL"
            reason = f"expected HTTP 200, got {resp.status_code}"
    else:  # other resource: check marker
        marker_present = "MARK_RX05_X" in resp.text
        allowed = marker_present
        if allowed == expected_allowed:
            result = "PASS"
            reason = ""
        else:
            result = "FAIL"
            reason = ("marker found" if marker_present else "marker not found")
    print(f"{label}: {result}" + (f" ({reason})" if reason else ""))

def main():
    sess = requests.Session()
    login(sess, "bilal@gmail.com", "bilal123")

    # Row: patient | view prescription | prescription | own | allowed
    test_view_prescription(sess, resource_id=3, expected_allowed=True, label="own")

    # Row: patient | view prescription | prescription | other | denied
    test_view_prescription(sess, resource_id=5, expected_allowed=False, label="other")

if __name__ == "__main__":
    main()