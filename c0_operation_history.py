import requests, re, sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
VIEW_URL = BASE_URL + "index.php?/patient/view_operation_history"
MARKER = "MARK_OP08_X"

def get_auth_token(session, url):
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    m = re.search(r'<input[^>]*name=["\']authenticity_token["\'][^>]*value=["\']([^"\']+)["\']', resp.text)
    if not m:
        sys.exit("Failed to find authenticity_token")
    return m.group(1)

def login(session, email, password):
    token = get_auth_token(session, LOGIN_URL)
    data = {
        "login_type": "patient",
        "email": email,
        "password": password,
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=data, timeout=10)
    resp.raise_for_status()
    # login fails if the login page is still present (contains the login_type field)
    if 'name="login_type"' in resp.text:
        sys.exit("Login failed")
    return resp

def check_access(resp_text):
    return MARKER in resp_text

def main():
    sess = requests.Session()

    # Step 1: login as attacker
    login(sess, "bilal@gmail.com", "bilal123")

    # Step 2: perform the attack request
    resp = sess.get(VIEW_URL, timeout=10)
    resp.raise_for_status()
    allowed = check_access(resp.text)

    # Expected decision: deny (i.e., marker must NOT appear)
    if not allowed:
        print("PASS: Access denied as expected")
    else:
        print("FAIL: Access allowed, marker found in response")

if __name__ == "__main__":
    main()