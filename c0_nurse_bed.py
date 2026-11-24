import requests, re, sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
TARGET_URL = BASE_URL + "index.php?/nurse/manage_bed"

def get_auth_token(session, url):
    resp = session.get(url, timeout=10)
    if resp.status_code != 200:
        sys.exit(f"Failed to load page for token: {url}")
    m = re.search(r'<input[^>]+name=["\']authenticity_token["\'][^>]+value=["\']([^"\']+)["\']', resp.text)
    return m.group(1) if m else None

def login_as_admin():
    sess = requests.Session()
    token = get_auth_token(sess, LOGIN_URL)
    if not token:
        sys.exit("Could not find authenticity_token on login page")
    payload = {
        "login_type": "admin",
        "email": "admin@admin.com",
        "password": "admin123",
        "authenticity_token": token
    }
    resp = sess.post(LOGIN_URL, data=payload, timeout=10)
    # login fails if the login page is still present (contains the login_type field)
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed for admin")
    return sess

def is_denied_by_transport(resp):
    # classic 3xx redirect
    if 300 <= resp.status_code < 400 and resp.headers.get('Location'):
        return True
    # Refresh header
    if resp.status_code == 200 and resp.headers.get('Refresh'):
        return True
    # meta refresh tag
    if resp.status_code == 200 and re.search(r'<meta\s+http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def main():
    session = login_as_admin()
    # Attempt to access nurse/manage_bed as admin (GET)
    resp = session.get(TARGET_URL, timeout=10)
    denied = is_denied_by_transport(resp)

    expected = "deny"
    observed = "deny" if denied else "allow"

    if observed == expected:
        print("PASS: admin access to nurse/manage_bed correctly denied")
    else:
        reason = "request was not denied by transport" if not denied else "unexpected denial"
        print(f"FAIL: admin access to nurse/manage_bed {observed.upper()}, expected DENY – {reason}")

if __name__ == "__main__":
    main()