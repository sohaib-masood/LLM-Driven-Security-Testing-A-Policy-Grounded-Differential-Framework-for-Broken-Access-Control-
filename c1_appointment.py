import requests
import re
import sys

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"

session = requests.Session()

# ---------- Login ----------
login_page = session.get(LOGIN_URL)
token_match = re.search(
    r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']',
    login_page.text,
)
if not token_match:
    print("FAIL: could not find authenticity_token on login page")
    sys.exit(1)

auth_token = token_match.group(1)

login_payload = {
    "login_type": "doctor",
    "email": "Rizwan@yahoo.com",
    "password": "rizwan123",
    "authenticity_token": auth_token,
}
login_resp = session.post(LOGIN_URL, data=login_payload)

if 'name="login_type"' in login_resp.text:
    print("FAIL: login failed")
    sys.exit(1)
else:
    print("PASS: login successful")

# ---------- Test helpers ----------
MARKER = "MARK_D06_X"


def check_allowed(resp):
    """Allowed means HTTP 200 (no server error)."""
    return resp.status_code == 200


def check_denied(resp):
    """Denied means the marker string is NOT present in the response."""
    return MARKER not in resp.text


def run_test(description, url, expect_allowed):
    try:
        resp = session.get(url)
    except Exception as e:
        print(f"FAIL: {description} – request error: {e}")
        return

    if expect_allowed:
        if check_allowed(resp):
            print(f"PASS: {description}")
        else:
            print(
                f"FAIL: {description} – expected allowed (200) but got {resp.status_code}"
            )
    else:
        if check_denied(resp):
            print(f"PASS: {description}")
        else:
            print(
                f"FAIL: {description} – expected denied (no marker) but marker found"
            )


# ---------- Tests ----------
# 1. doctor | view appointment | appointment | own | allowed
own_view_url = BASE_URL + "index.php?/doctor/manage_appointment/edit/32"
run_test(
    "doctor view appointment own",
    own_view_url,
    expect_allowed=True,
)

# 2. doctor | view appointment | appointment | other | denied
other_view_url = BASE_URL + "index.php?/doctor/manage_appointment/edit/35"
run_test(
    "doctor view appointment other",
    other_view_url,
    expect_allowed=False,
)

# 3. doctor | delete appointment | appointment | other | denied
other_delete_url = BASE_URL + "index.php?/doctor/manage_appointment/delete/35"
run_test(
    "doctor delete appointment other",
    other_delete_url,
    expect_allowed=False,
)