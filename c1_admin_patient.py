import requests, re, sys, urllib.parse

BASE = "http://localhost/hms/"
ENDPOINT = "admin/manage_patient"
FULL_URL = urllib.parse.urljoin(BASE, f"index.php?/{ENDPOINT}")

def is_denied(resp: requests.Response) -> bool:
    # classic 3xx redirect
    if 300 <= resp.status_code < 400:
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # meta refresh tag
    if re.search(r'<meta[^>]+http-equiv=["\']?refresh["\']?', resp.text, re.I):
        return True
    return False

def get_token(session: requests.Session, url: str) -> str:
    r = session.get(url, timeout=10)
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', r.text)
    return m.group(1) if m else ""

def test_get(session: requests.Session):
    resp = session.get(FULL_URL, timeout=10)
    denied = is_denied(resp)
    if denied:
        print("GET unauthenticated: PASS - request denied as expected")
    else:
        print("GET unauthenticated: FAIL - request was allowed")

def test_post(session: requests.Session):
    token = get_token(session, FULL_URL)
    data = {
        "authenticity_token": token,
        "patient_id": "9999"   # forged identifier field
    }
    resp = session.post(FULL_URL, data=data, timeout=10)
    denied = is_denied(resp)
    if denied:
        print("POST unauthenticated: PASS - request denied as expected")
    else:
        print("POST unauthenticated: FAIL - request was allowed")

def main():
    sess = requests.Session()
    # No login – test unauthenticated access
    test_get(sess)
    test_post(sess)

if __name__ == "__main__":
    main()