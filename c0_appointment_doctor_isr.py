import requests, re, sys

BASE = "http://localhost/hms/"
LOGIN_URL = BASE + "index.php?/login"
ATTACKER = {
    "login_type": "doctor",
    "email": "Rizwan@yahoo.com",
    "password": "rizwan123",
}
TARGET_ID = 47          # victim's resource id
FORGED_DOCTOR_ID = "6"  # real owner's id
MARKER = "MARK_D06_X"

session = requests.Session()

def get_token(html):
    m = re.search(r'<input[^>]*name=["\']authenticity_token["\'][^>]*value=["\']([^"\']+)["\']', html)
    return m.group(1) if m else None

# ---------- Login ----------
resp = session.get(LOGIN_URL)
token = get_token(resp.text)
if not token:
    print("FAIL: Could not find authenticity_token on login page")
    sys.exit(1)

login_data = {
    "login_type": ATTACKER["login_type"],
    "email": ATTACKER["email"],
    "password": ATTACKER["password"],
    "authenticity_token": token,
}
resp = session.post(LOGIN_URL, data=login_data)
if 'name="login_type"' in resp.text:
    print("FAIL: Login failed for attacker")
    sys.exit(1)

# ---------- Attack attempt ----------
edit_url = f"{BASE}index.php?/doctor/manage_appointment/edit/{TARGET_ID}"
# GET the edit page to obtain fresh token
resp = session.get(edit_url)
token = get_token(resp.text)
if not token:
    print("FAIL: Could not retrieve authenticity_token from edit page")
    sys.exit(1)

# Build forged POST payload (include any other plausible fields if needed)
payload = {
    "authenticity_token": token,
    "doctor_id": FORGED_DOCTOR_ID,
    # add placeholder fields that the real form might expect
    "appointment_date": "2025-01-01",
    "appointment_time": "09:00",
    "patient_id": "1",
}
resp = session.post(edit_url, data=payload)

allowed = MARKER in resp.text
expected_allowed = False  # we expect the attempt to be denied

if allowed == expected_allowed:
    print("PASS: access denied as expected")
else:
    reason = "access allowed unexpectedly" if allowed else "access denied unexpectedly"
    print(f"FAIL: {reason}")