import requests, re, sys

BASE_URL = "http://localhost/hms/"
ENDPOINT = "accountant/manage_invoice"
FULL_URL = f"{BASE_URL}index.php?/{ENDPOINT}"
MARKER = "None"

def is_denied(resp: requests.Response) -> bool:
    # Classic 3xx redirect
    if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # Meta refresh tag
    if '<meta http-equiv="refresh"' in resp.text.lower():
        return True
    return False

def has_marker(resp: requests.Response) -> bool:
    return MARKER in resp.text

def test_get(session: requests.Session):
    try:
        resp = session.get(FULL_URL, timeout=10)
    except Exception as e:
        print(f"GET: FAIL - request error: {e}")
        return
    denied = is_denied(resp)
    marker = has_marker(resp)
    if denied and not marker:
        print("GET: PASS")
    else:
        reason = []
        if not denied:
            reason.append("no transport denial")
        if marker:
            reason.append("marker found (data rendered)")
        print(f"GET: FAIL - {'; '.join(reason)}")

def scrape_token(html: str) -> str:
    m = re.search(r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']', html)
    if m:
        return m.group(1)
    return ""

def test_post(session: requests.Session):
    # First GET to obtain authenticity_token
    try:
        get_resp = session.get(FULL_URL, timeout=10)
    except Exception as e:
        print(f"POST: FAIL - token fetch error: {e}")
        return
    token = scrape_token(get_resp.text)
    if not token:
        print("POST: FAIL - authenticity_token not found")
        return
    # Prepare forged field (assumed name 'invoice_id')
    payload = {
        "authenticity_token": token,
        "invoice_id": "123"
    }
    try:
        resp = session.post(FULL_URL, data=payload, timeout=10)
    except Exception as e:
        print(f"POST: FAIL - request error: {e}")
        return
    denied = is_denied(resp)
    marker = has_marker(resp)
    if denied and not marker:
        print("POST: PASS")
    else:
        reason = []
        if not denied:
            reason.append("no transport denial")
        if marker:
            reason.append("marker found (data rendered)")
        print(f"POST: FAIL - {'; '.join(reason)}")

def main():
    # No login – use a fresh session with no authentication
    session = requests.Session()
    test_get(session)
    test_post(session)

if __name__ == "__main__":
    main()