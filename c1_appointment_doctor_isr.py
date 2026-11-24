import requests, re, sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
TOKEN_REGEX = re.compile(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', re.I)

MARKER = "MARK_D06_X"

def get_token(session, url):
    r = session.get(url, timeout=10)
    m = TOKEN_REGEX.search(r.text)
    return m.group(1) if m else None

def is_denied_by_transport(resp):
    # classic 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # meta refresh tag
    if re.search(r'<meta\s+http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def login(session):
    # get login page
    r = session.get(LOGIN_URL, timeout=10)
    token = get_token(session, LOGIN_URL)
    if not token:
        print("FAIL login - could not find authenticity_token")
        sys.exit(1)
    payload = {
        "login_type": "doctor",
        "email": "Rizwan@yahoo.com",
        "password": "rizwan123",
        "authenticity_token": token
    }
    r = session.post(LOGIN_URL, data=payload, timeout=10)
    if 'name="login_type"' in r.text:
        print("FAIL login - login page still present")
        sys.exit(1)
    # login succeeded
    return True

def evaluate_response(row_id, case_desc, resp, expect_allowed, is_other):
    # own case: just need 200 and not denied by transport
    if not is_other:
        if resp.status_code == 200 and not is_denied_by_transport(resp):
            return "PASS", "own resource returned 200 as expected"
        else:
            return "FAIL", f"own resource unexpected status {resp.status_code} or transport denial"
    # other case: look for marker
    if MARKER in resp.text:
        observed_allowed = True
    else:
        observed_allowed = not is_denied_by_transport(resp)
    if observed_allowed == expect_allowed:
        return "PASS", f"marker {'found' if MARKER in resp.text else 'absent'}, transport {'denied' if is_denied_by_transport(resp) else 'allowed'}"
    else:
        return "FAIL", f"marker {'found' if MARKER in resp.text else 'absent'}, transport {'denied' if is_denied_by_transport(resp) else 'allowed'}"

def test_case(session, row_id, resource_id, expect_allowed, method):
    url = BASE_URL + f"doctor/manage_appointment/edit/{resource_id}"
    case_desc = f"{row_id} {method} id={resource_id}"
    is_other = (resource_id != 32)  # own id is 32, other is 35
    if method == "GET":
        resp = session.get(url, timeout=10)
        result, reason = evaluate_response(row_id, case_desc, resp, expect_allowed, is_other)
        print(f"{row_id} GET id={resource_id}: {result} - {reason}")
    else:  # POST
        # get fresh token
        token = get_token(session, url)
        if not token:
            print(f"{row_id} POST id={resource_id}: FAIL - could not obtain authenticity_token")
            return
        payload = {
            "authenticity_token": token,
            "doctor_id": "6"          # forged field as required
        }
        resp = session.post(url, data=payload, timeout=10)
        result, reason = evaluate_response(row_id, case_desc, resp, expect_allowed, is_other)
        print(f"{row_id} POST id={resource_id}: {result} - {reason}")

def main():
    sess = requests.Session()
    login(sess)

    # Row P158: doctor edit appointment own allowed
    test_case(sess, "P158", 32, True, "GET")
    test_case(sess, "P158", 32, True, "POST")

    # Row P159: doctor edit appointment other denied
    test_case(sess, "P159", 35, False, "GET")
    test_case(sess, "P159", 35, False, "POST")

if __name__ == "__main__":
    main()