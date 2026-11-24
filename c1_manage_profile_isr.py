import requests, re, sys

BASE = "http://localhost/hms/"
LOGIN_URL = BASE + "index.php?/login"
PROFILE_URL = BASE + "index.php?/patient/manage_profile/update_profile_info"

def get_token(text):
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', text)
    return m.group(1) if m else None

def is_denied(resp):
    # transport denial: 3xx redirect, Refresh header, or meta refresh tag
    if 300 <= resp.status_code < 400:
        return True
    if 'Refresh' in resp.headers:
        return True
    if '<meta http-equiv="refresh"' in resp.text.lower():
        return True
    return False

def login(sess):
    # get login page
    r = sess.get(LOGIN_URL, timeout=10)
    token = get_token(r.text)
    if not token:
        print("FAIL login: could not find authenticity_token")
        sys.exit(1)
    payload = {
        "login_type": "patient",
        "email": "bilal@gmail.com",
        "password": "bilal123",
        "authenticity_token": token
    }
    r = sess.post(LOGIN_URL, data=payload, timeout=10)
    if 'name="login_type"' in r.text:
        print("FAIL login: login failed")
        sys.exit(1)
    # login succeeded
    return True

def test_own_get(sess):
    r = sess.get(PROFILE_URL, timeout=10)
    denied = is_denied(r)
    if denied:
        return False, "own GET denied"
    return True, "own GET allowed"

def test_own_post(sess):
    # fetch fresh token
    r = sess.get(PROFILE_URL, timeout=10)
    token = get_token(r.text)
    if not token:
        return False, "own POST: no token"
    payload = {
        "authenticity_token": token,
        "phone": "1111111111"
    }
    r = sess.post(PROFILE_URL, data=payload, timeout=10)
    denied = is_denied(r)
    if denied:
        return False, "own POST denied"
    return True, "own POST allowed"

def test_other_get(sess):
    # attempt to access other user's profile via query param
    r = sess.get(PROFILE_URL, params={"patient_id": "8"}, timeout=10)
    denied = is_denied(r)
    if denied:
        return True, "other GET correctly denied"
    return False, "other GET not denied"

def test_other_post(sess):
    # fetch fresh token
    r = sess.get(PROFILE_URL, timeout=10)
    token = get_token(r.text)
    if not token:
        return False, "other POST: no token"
    payload = {
        "authenticity_token": token,
        "patient_id": "8",
        "phone": "0000000008"
    }
    r = sess.post(PROFILE_URL, data=payload, timeout=10)
    denied = is_denied(r)
    if denied:
        return True, "other POST correctly denied"
    return False, "other POST not denied"

def main():
    sess = requests.Session()
    login(sess)

    # Row P285: patient manage profile own -> allowed
    ok, msg = test_own_get(sess)
    print("PASS" if ok else "FAIL", "- own GET:", msg)
    ok, msg = test_own_post(sess)
    print("PASS" if ok else "FAIL", "- own POST:", msg)

    # Row P286: patient manage profile other -> denied
    ok, msg = test_other_get(sess)
    print("PASS" if ok else "FAIL", "- other GET:", msg)
    ok, msg = test_other_post(sess)
    print("PASS" if ok else "FAIL", "- other POST:", msg)

if __name__ == "__main__":
    main()