"""Logs into the HMS and sends requests, using a real browser-like session (cookies kept).
Handles two things this HMS does that a plain HTTP client would miss:
 1. CSRF protection is on, so every POST needs the one-time token from the login page first.
 2. A "denied" redirect here is sent as a 200 response with a Refresh header (CodeIgniter's
    redirect(..., 'refresh')), not a classic 300-399 redirect, so it must be checked for too.
"""
import re
import requests
from config import BASE_URL

def new_session():
    return requests.Session()

def _csrf_token(html):
    m = re.search(r'name=["\']authenticity_token["\'][^>]*value=["\']([^"\']+)["\']', html, re.I)
    if not m:
        m = re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']authenticity_token["\']', html, re.I)
    return m.group(1) if m else None

def _is_refresh(resp):
    """True if this response is CodeIgniter's redirect(..., 'refresh') style: 200 OK + a Refresh header/meta tag."""
    if 300 <= resp.status_code < 400:
        return True
    if any(k.lower() == "refresh" for k in resp.headers.keys()):
        return True
    if re.search(r'<meta[^>]+http-equiv=["\']refresh["\']', resp.text, re.I):
        return True
    return False

def _refresh_target(resp):
    h = resp.headers.get("Refresh") or resp.headers.get("refresh")
    if h:
        m = re.search(r'url=(.+)$', h, re.I)
        if m: return m.group(1).strip()
    m = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][^;]*;\s*url=([^"\']+)', resp.text, re.I)
    return m.group(1).strip() if m else None

def login(session, email, password, login_type):
    """Returns True if the login succeeded (lands on that role's dashboard)."""
    page = session.get(BASE_URL + "index.php?login", timeout=10)
    token = _csrf_token(page.text)
    data = {"login_type": login_type, "email": email, "password": password}
    if token:
        data["authenticity_token"] = token
    r = session.post(BASE_URL + "index.php?login", data=data, allow_redirects=True, timeout=10)
    if _is_refresh(r):
        target = _refresh_target(r)
        if target:
            if not target.startswith("http"):
                target = BASE_URL.rstrip("/") + "/" + target.lstrip("/")
            r = session.get(target, allow_redirects=True, timeout=10)
    return (login_type + " panel") in r.text.lower() or "logout" in r.text.lower()

def get(session, path, allow_redirects=False):
    """GET one endpoint. allow_redirects=False so we can see a classic redirect too (both count as denied)."""
    return session.get(BASE_URL + "index.php?" + path, allow_redirects=allow_redirects, timeout=10)

def post(session, path, data, allow_redirects=False, token_path=None):
    """POST to one endpoint with a CSRF token fetched first, merged with the extra form fields
    in `data` (e.g. a forged patient_id/doctor_id for the identifier-source-replacement mutants
    M26-M29). Added for the remaining-mutant extension.
    By default the token is fetched from `path` itself (safe for GET-only display pages like
    view_appointment/payment_history). Some endpoints (e.g. manage_profile/update_profile_info)
    run their write logic on ANY request to that URL, GET included, since the PHP controller
    only checks the URL segment, not the HTTP method -- for those, pass `token_path` pointing
    at a safe page instead (e.g. "patient/manage_profile") so fetching the token doesn't itself
    trigger the write with empty data."""
    page = session.get(BASE_URL + "index.php?" + (token_path or path), timeout=10)
    token = _csrf_token(page.text)
    body = dict(data)
    if token:
        body["authenticity_token"] = token
    return session.post(BASE_URL + "index.php?" + path, data=body, allow_redirects=allow_redirects, timeout=10)

def is_denied(resp):
    """A classic redirect, or this app's 200+Refresh redirect, both mean the HMS sent the user away -> denied."""
    return _is_refresh(resp)
