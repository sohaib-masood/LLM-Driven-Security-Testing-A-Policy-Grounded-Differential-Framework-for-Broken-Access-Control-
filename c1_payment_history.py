import requests, re, sys
from bs4 import BeautifulSoup

BASE = "http://localhost/hms/index.php?/"
LOGIN_URL = BASE + "login"
ENDPOINT = "patient/payment_history"
FULL_URL = BASE + ENDPOINT
MARKER = "MARK_PAY08_X"

def get_token(html):
    soup = BeautifulSoup(html, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    return token_tag["value"] if token_tag and token_tag.has_attr("value") else None

def is_transport_denied(resp):
    if resp.is_redirect:
        return True
    if resp.headers.get("Refresh"):
        return True
    if re.search(r'<meta\s+http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def check_allowed(resp):
    # allowed if not transport denied and (for other) marker not required
    return not is_transport_denied(resp)

def main():
    s = requests.Session()

    # ----- login -----
    try:
        r = s.get(LOGIN_URL, timeout=10)
    except Exception as e:
        print(f"FAIL login GET error: {e}")
        sys.exit(1)

    token = get_token(r.text)
    if not token:
        print("FAIL login: could not find authenticity_token")
        sys.exit(1)

    login_data = {
        "login_type": "patient",
        "email": "bilal@gmail.com",
        "password": "bilal123",
        "authenticity_token": token,
    }
    try:
        r = s.post(LOGIN_URL, data=login_data, timeout=10)
    except Exception as e:
        print(f"FAIL login POST error: {e}")
        sys.exit(1)

    if 'name="login_type"' in r.text:
        print("FAIL login: login failed (login_type field still present)")
        sys.exit(1)
    # login succeeded

    # ----- test own view (P293) -----
    try:
        r = s.get(FULL_URL, timeout=10)
    except Exception as e:
        print(f"FAIL P293 own GET error: {e}")
    else:
        if r.status_code == 200 and not is_transport_denied(r):
            print("PASS P293 own view allowed")
        else:
            reason = "status_code={!r}".format(r.status_code)
            if is_transport_denied(r):
                reason = "transport denied"
            print(f"FAIL P293 own view allowed ({reason})")

    # ----- test other view via GET (P294 a) -----
    other_id = 8
    url_other = FULL_URL + f"?patient_id={other_id}"
    try:
        r = s.get(url_other, timeout=10)
    except Exception as e:
        print(f"FAIL P294 GET error: {e}")
    else:
        denied = is_transport_denied(r) or (MARKER not in r.text)
        if denied:
            print("PASS P294 other view GET denied")
        else:
            print("FAIL P294 other view GET denied (marker found)")

    # ----- test other view via POST (P294 b) -----
    # get fresh token from the page (without forged id)
    try:
        r_get = s.get(FULL_URL, timeout=10)
    except Exception as e:
        print(f"FAIL P294 POST token fetch error: {e}")
        sys.exit(1)

    token = get_token(r_get.text)
    if not token:
        print("FAIL P294 POST: could not obtain authenticity_token")
        sys.exit(1)

    post_data = {
        "authenticity_token": token,
        "patient_id": other_id,
    }
    try:
        r = s.post(FULL_URL, data=post_data, timeout=10)
    except Exception as e:
        print(f"FAIL P294 POST error: {e}")
    else:
        denied = is_transport_denied(r) or (MARKER not in r.text)
        if denied:
            print("PASS P294 other view POST denied")
        else:
            print("FAIL P294 other view POST denied (marker found)")

if __name__ == "__main__":
    main()