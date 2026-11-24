import requests, re, sys

BASE = "http://localhost/hms/"
LOGIN_URL = BASE + "index.php?/login"
PAYMENT_URL = BASE + "index.php?/patient/payment_history"
MARKER = "MARK_PAY08_X"

def get_token(html):
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', html)
    return m.group(1) if m else None

session = requests.Session()

# ---------- Login ----------
login_page = session.get(LOGIN_URL, verify=False)
token = get_token(login_page.text)
if not token:
    print("FAIL - could not find authenticity_token on login page")
    sys.exit(1)

login_data = {
    "login_type": "patient",
    "email": "bilal@gmail.com",
    "password": "bilal123",
    "authenticity_token": token
}
login_resp = session.post(LOGIN_URL, data=login_data, verify=False)

if 'name="login_type"' in login_resp.text:
    print("FAIL - login failed")
    sys.exit(1)
else:
    print("Login successful")

# ---------- Attempt A: plain GET ----------
resp_get = session.get(PAYMENT_URL, verify=False)
if MARKER in resp_get.text:
    print("GET attempt: FAIL - marker found, access was allowed")
else:
    print("GET attempt: PASS - access denied as expected")

# ---------- Attempt B: forged POST ----------
# Get fresh token from the payment page (or its form)
page_before = session.get(PAYMENT_URL, verify=False)
token2 = get_token(page_before.text)
if not token2:
    # If token not found, still try with empty token
    token2 = ""

post_data = {
    "authenticity_token": token2,
    "patient_id": "8"
}
resp_post = session.post(PAYMENT_URL, data=post_data, verify=False)

if MARKER in resp_post.text:
    print("POST attempt: FAIL - marker found, access was allowed")
else:
    print("POST attempt: PASS - access denied as expected")