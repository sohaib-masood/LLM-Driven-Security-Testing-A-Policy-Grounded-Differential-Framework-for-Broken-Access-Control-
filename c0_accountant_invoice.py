import requests
import re

BASE_URL = "http://localhost/hms/"

def is_denied(resp: requests.Response) -> bool:
    # Classic 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header (CodeIgniter's refresh method)
    if resp.headers.get("Refresh"):
        return True
    # Meta refresh tag in HTML body
    if resp.headers.get("Content-Type", "").lower().startswith("text"):
        if re.search(r'<meta\s+http-equiv=["\']?refresh["\']?', resp.text, re.IGNORECASE):
            return True
    return False

def main():
    session = requests.Session()
    target = BASE_URL + "index.php?/accountant/manage_invoice"
    try:
        resp = session.get(target, timeout=10)
    except Exception as e:
        print(f"FAIL - request error: {e}")
        return

    denied = is_denied(resp)
    expected_denied = True  # the misuse case expects a denial

    if denied == expected_denied:
        print("PASS")
    else:
        reason = "allowed when denial expected" if not denied else "denied when allowance expected"
        print(f"FAIL - {reason}")

if __name__ == "__main__":
    main()