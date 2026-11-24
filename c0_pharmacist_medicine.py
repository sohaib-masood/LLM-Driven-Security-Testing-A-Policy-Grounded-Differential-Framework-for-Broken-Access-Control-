import requests, re, sys
from bs4 import BeautifulSoup

BASE_URL = "http://localhost/hms/"
LOGIN_URL = BASE_URL + "index.php?/login"
MANAGE_MED_URL = BASE_URL + "index.php?/pharmacist/manage_medicine"

ATTACKER = {
    "login_type": "pharmacist",
    "email": "hassan@yahoo.com",
    "password": "hassan123"
}

def get_auth_token(session, url):
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if not token_tag or not token_tag.has_attr("value"):
        raise RuntimeError("authenticity_token not found")
    return token_tag["value"]

def login(session):
    token = get_auth_token(session, LOGIN_URL)
    payload = {
        "login_type": ATTACKER["login_type"],
        "email": ATTACKER["email"],
        "password": ATTACKER["password"],
        "authenticity_token": token
    }
    resp = session.post(LOGIN_URL, data=payload, timeout=10)
    resp.raise_for_status()
    # login fails if the login page marker is still present
    if 'name="login_type"' in resp.text:
        raise RuntimeError("Login failed")
    return resp

def is_transport_denied(resp):
    # 3xx redirect
    if resp.is_redirect or (300 <= resp.status_code < 400):
        return True
    # Refresh header
    if resp.headers.get("Refresh"):
        return True
    # Meta refresh tag
    soup = BeautifulSoup(resp.text, "html.parser")
    meta = soup.find("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)})
    if meta:
        return True
    return False

def main():
    session = requests.Session()
    try:
        login(session)
    except Exception as e:
        print(f"FAIL: login error – {e}")
        sys.exit(1)

    try:
        resp = session.get(MANAGE_MED_URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"FAIL: request error – {e}")
        sys.exit(1)

    denied = is_transport_denied(resp)
    if denied:
        print("FAIL: access was denied (transport redirect) but expected ALLOW")
    else:
        print("PASS: access allowed as expected")

if __name__ == "__main__":
    main()