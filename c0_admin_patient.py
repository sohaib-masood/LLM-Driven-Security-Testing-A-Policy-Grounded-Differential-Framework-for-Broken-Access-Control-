import requests
import re

BASE_URL = "http://localhost/hms/"
TARGET = "admin/manage_patient"
FULL_URL = f"{BASE_URL}index.php?/{TARGET}"

def is_denied_by_transport(resp: requests.Response) -> bool:
    # Classic 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header (CodeIgniter's refresh method)
    if "Refresh" in resp.headers:
        return True
    # Meta refresh tag in HTML body
    if resp.headers.get("Content-Type", "").startswith("text"):
        if re.search(r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]*>', resp.text, re.IGNORECASE):
            return True
    return False

def main():
    session = requests.Session()
    try:
        resp = session.get(FULL_URL, allow_redirects=False, timeout=10)
    except Exception as e:
        print(f"FAIL - request error: {e}")
        return

    denied = is_denied_by_transport(resp)
    expected_denied = True  # the test expects the request to be denied

    if denied == expected_denied:
        print("PASS")
    else:
        reason = "allowed when it should be denied" if not denied else "denied when it should be allowed"
        print(f"FAIL - {reason}")

if __name__ == "__main__":
    main()