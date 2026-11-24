"""
Condition C0: direct prompting.
The LLM gets only the misuse case + Authorization Context (no PATM, no permission matrix)
and must write the test script itself. Uses the same Groq key/model as C2 (config.py).
"""
import os
import re
import requests
from config import GROQ_API_KEY, GROQ_MODEL, BASE_URL, ACCOUNTS
from db_check import resolve_dynamic_accounts

INSTANCES_C0 = [
    dict(
        name="appointment",
        attacker="doctor4",
        own_id=31, victim_id=47,
        victim_marker="MARK_D06_X",
        misuse_case=(
            "A malicious doctor is logged in under their own account. They attempt to VIEW another "
            "doctor's appointment (by GET doctor/manage_appointment/edit/{id}) and to DELETE another "
            "doctor's appointment (by GET doctor/manage_appointment/delete/{id}), in both cases by "
            "replacing the appointment ID in the URL with an appointment ID that belongs to a different "
            "doctor. The system must deny both attempts."
        ),
        endpoint="doctor/manage_appointment/edit/{id} and doctor/manage_appointment/delete/{id}",
    ),
    dict(
        name="prescription",
        attacker="patient3",
        own_id=3, victim_id=5,
        victim_marker="MARK_RX05_X",
        misuse_case=(
            "A malicious patient is logged in under their own account. They attempt to view another "
            "patient's prescription (GET patient/view_prescription/edit/{id}) by replacing the "
            "prescription ID in the URL. The system must deny this access."
        ),
        endpoint="patient/view_prescription/edit/{id}",
    ),
    dict(
        name="doctor_account",
        attacker="patient3",
        own_id=None, victim_id=None,
        victim_marker="MARK_D04_X",
        misuse_case=(
            "A malicious patient attempts to access the admin page that manages doctor accounts "
            "(GET admin/manage_doctor). Two attempts must be tested: first while logged in as a "
            "patient, then with no active session at all. The system must deny both attempts."
        ),
        endpoint="admin/manage_doctor",
    ),
    dict(
        name="invoice",
        attacker="doctor4",
        own_id=None, victim_id=None,
        victim_marker="MARK_INV03_X",
        misuse_case=(
            "A malicious doctor attempts to access the patient invoice page (GET patient/view_invoice). "
            "Two attempts must be tested: first while logged in as a doctor, then with no active "
            "session at all. The system must deny both attempts."
        ),
        endpoint="patient/view_invoice",
    ),
]


# --- remaining mutants: M13, M14, M16, M17, M19-M24, M26-M29 ---
INSTANCES_C0_NEW = [
    dict(
        name="nurse_bed", attacker="admin1", own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny",
        misuse_case=(
            "An admin, logged in under their own admin account, attempts to GET nurse/manage_bed, "
            "a page reserved for the nurse role. The system must deny this (an admin session is not "
            "a nurse session)."
        ),
        endpoint="nurse/manage_bed",
    ),
    dict(
        name="admin_patient", attacker=None, own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny",
        misuse_case=(
            "A visitor with no active session at all attempts to GET admin/manage_patient, a page "
            "reserved for the admin role. The system must deny this."
        ),
        endpoint="admin/manage_patient",
    ),
    dict(
        name="pharmacist_medicine", attacker="pharmacist1", own_id=None, victim_id=None, victim_marker=None,
        expected_decision="allow",
        misuse_case=(
            "A LEGITIMATE pharmacist, logged in under their own correct pharmacist account, attempts "
            "to GET pharmacist/manage_medicine, which is exactly the page their role is supposed to be "
            "able to use. The system must ALLOW this (this is not an attack -- it is checking that a "
            "legitimate, properly-authorized user is not wrongly denied access to their own role's page)."
        ),
        endpoint="pharmacist/manage_medicine",
    ),
    dict(
        name="accountant_invoice", attacker=None, own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny",
        misuse_case=(
            "A visitor with no active session at all attempts to GET accountant/manage_invoice, a page "
            "reserved for the accountant role. The system must deny this."
        ),
        endpoint="accountant/manage_invoice",
    ),
    dict(
        name="appointment_list", attacker="doctor4", own_id=None, victim_id=None, victim_marker="MARK_D06_X",
        expected_decision="deny",
        misuse_case=(
            "A malicious doctor, logged in under their own account, GETs doctor/manage_appointment "
            "(the plain list page, no id in the URL -- this lists the doctor's OWN appointments). "
            "The system must show only the attacker's own appointments: a different doctor's "
            "appointment, identifiable by the marker string below, must not appear in the list."
        ),
        endpoint="doctor/manage_appointment",
    ),
    dict(
        name="patient_appointment", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_D08_APPT_X", expected_decision="deny",
        misuse_case=(
            "A malicious patient, logged in under their own account, attacks patient/view_appointment "
            "(which normally lists only the logged-in patient's own appointments) two ways: "
            "(a) a plain GET with no tampering, hoping the list simply includes other patients' rows; "
            "(b) a POST to the same URL with an extra forged form field patient_id=8, hoping the server "
            "trusts that POSTed id instead of the session's own patient id. Both attempts must be denied: "
            "a different patient's appointment, identifiable by the doctor-name marker string below, "
            "must not appear in either response."
        ),
        endpoint="patient/view_appointment",
    ),
    dict(
        name="payment_history", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_PAY08_X", expected_decision="deny",
        misuse_case=(
            "A malicious patient, logged in under their own account, attacks patient/payment_history "
            "two ways: (a) a plain GET with no tampering; (b) a POST to the same URL with an extra "
            "forged form field patient_id=8. Both attempts must be denied: a different patient's "
            "payment, identifiable by the marker string below in its description field, must not "
            "appear in either response."
        ),
        endpoint="patient/payment_history",
    ),
    dict(
        name="admit_history", attacker="patient3", own_id=None, victim_id=None,
        victim_marker=None, expected_decision="deny",
        misuse_case=(
            "A malicious patient, logged in under their own account, GETs patient/view_admit_history "
            "(which normally lists only the logged-in patient's own bed allotments). Patient id 8 has a "
            "bed allotment of their own; that other patient's name (looked up from the `patient` table, "
            "patient_id=8, column `name`) must not appear in the attacker's response."
        ),
        endpoint="patient/view_admit_history",
    ),
    dict(
        name="operation_history", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_OP08_X", expected_decision="deny",
        misuse_case=(
            "A malicious patient, logged in under their own account, GETs "
            "patient/view_operation_history (which normally lists only the logged-in patient's own "
            "operation reports). A different patient's operation report, identifiable by the marker "
            "string below in its description field, must not appear in the response."
        ),
        endpoint="patient/view_operation_history",
    ),
    dict(
        name="invoice_list", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_INV08_X", expected_decision="deny",
        misuse_case=(
            "A malicious patient, logged in under their own account, GETs patient/view_invoice "
            "(which normally lists only the logged-in patient's own invoices). A different patient's "
            "invoice, identifiable by the marker string below in its description field, must not "
            "appear in the response."
        ),
        endpoint="patient/view_invoice",
    ),
    dict(
        name="appointment_doctor_isr", attacker="doctor4", own_id=31, victim_id=47,
        victim_marker="MARK_D06_X", expected_decision="deny",
        misuse_case=(
            "A malicious doctor, logged in under their own account, POSTs to "
            "doctor/manage_appointment/edit/{victim_id} with an extra forged form field doctor_id=6 "
            "(the real owner's id), hoping the server trusts that POSTed doctor_id instead of the "
            "session's own doctor id when deciding ownership. The attempt must be denied."
        ),
        endpoint="doctor/manage_appointment/edit/{id} (POST, forged doctor_id)",
    ),
    dict(
        name="manage_profile_isr", attacker="patient3", own_id=None, victim_id=None,
        victim_marker=None, expected_decision="deny",
        misuse_case=(
            "A malicious patient, logged in under their own account, POSTs to "
            "patient/manage_profile/update_profile_info with an extra forged form field patient_id=8 "
            "and phone=0000000008 (plus plausible values for the other required fields: name, email, "
            "address, sex, birth_date, age, blood_group), hoping the server updates patient 8's record "
            "instead of the session's own patient's record. There is no content marker for this one: "
            "the oracle is whether patient 8's phone number in the `patient` table actually changed to "
            "0000000008 after the request (query the database directly to check -- a direct, read-only "
            "MySQL SELECT is fine here). The attempt must be denied, i.e. patient 8's phone must be "
            "unchanged."
        ),
        endpoint="patient/manage_profile/update_profile_info (POST, forged patient_id)",
    ),
]


def build_prompt(inst):
    attacker = ACCOUNTS[inst["attacker"]] if inst.get("attacker") else None
    expected = inst.get("expected_decision", "deny")
    marker = inst.get("victim_marker")

    if attacker is not None:
        account_line = f"- Attacker account: role={attacker['role']}, email={attacker['email']}, password={attacker['password']}"
    else:
        account_line = "- Attacker has NO session at all: do not log in, just send the request with a fresh requests.Session()."

    if marker:
        oracle = (f"- Reliable detection method (use this and only this to decide ALLOW vs DENY): the victim's "
                  f"record in the database has a unique marker string planted in it: \"{marker}\". This marker "
                  f"string appears in the HTML response if and only if the victim's actual data was rendered to "
                  f"the attacker. So: if \"{marker}\" appears anywhere in resp.text, access was ALLOWED. If it "
                  f"does NOT appear in resp.text, access was DENIED, regardless of status code, URL, or redirect "
                  f"mechanism.")
    else:
        oracle = ("- There is no content marker for this case: read the specific oracle described in the misuse "
                  "case above (it tells you exactly what to check -- a database query, or simply whether the "
                  "request was denied by transport, i.e. redirected via CodeIgniter's refresh mechanism, "
                  "described below).")

    return f"""You are testing a Hospital Management System (HMS) built in PHP/CodeIgniter for a Broken Access Control vulnerability.

Misuse case: {inst['misuse_case']}

Authorization Context:
- Base URL: {BASE_URL}
{account_line}
- Attacker's own resource ID (if applicable): {inst.get('own_id')}
- Victim's resource ID (if applicable): {inst.get('victim_id')}
- Endpoint(s): {inst['endpoint']}
- Expected decision for the attack attempt(s) described above: {expected}
- Login mechanism (skip this step entirely if the attacker has no session): GET {BASE_URL}index.php?/login
  first to obtain the page, then parse the hidden input named "authenticity_token" from its HTML (its value
  changes per page load). POST to {BASE_URL}index.php?/login with form fields: login_type (one of admin,
  doctor, patient, nurse, pharmacist, laboratorist, accountant), email, password, and authenticity_token
  (the scraped value). Use a requests.Session() so the resulting session cookie is kept for subsequent
  requests. Login failed if resp.text still contains 'name="login_type"' after the POST.
- For any request described as a POST with a forged field: first GET the target page to scrape a fresh
  "authenticity_token" the same way as login, then POST to the same URL with that token plus the forged
  field(s) named in the misuse case (and, where the misuse case says so, plausible values for any other
  fields the real HTML form on that page would normally submit).
- Important application quirk: this application's redirects use CodeIgniter's 'refresh' method,
  which returns HTTP 200 with a Refresh header or a meta-refresh tag instead of a real 3xx redirect.
  The requests library does NOT follow these automatically. Because of this, do NOT try to detect
  denial by checking resp.url, resp.status_code, for "access denied"/"unauthorized" phrases, or for
  the login-page marker — none of these reliably indicate denial for every endpoint in this app, since
  some denials redirect to the attacker's own dashboard rather than to the login page or an error page.
  A response counts as "denied by transport" if it is a classic 3xx redirect, OR a 200 response carrying
  a Refresh header, OR a 200 response whose HTML contains a <meta http-equiv="refresh"> tag.
{oracle}

Task: Write a complete, runnable Python script using the `requests` library that:
1. Logs in as the attacker if one is specified, confirming success by checking resp.text as described (not resp.url). If the misuse case says the attacker has no session, skip login entirely.
2. Sends the baseline request (if any is described) and the attack attempt(s) described in the misuse case, using GET or POST exactly as the misuse case specifies.
3. Decides ALLOW vs DENY for the attack attempt(s) using ONLY the oracle described above (content marker, direct database check, or transport-denial check as applicable) — never resp.url, status code alone, or generic denial phrases.
4. Prints one line per attempt: PASS if the observed decision matches the expected decision ({expected}) above, FAIL otherwise, with a short reason.

Return only the Python script. No explanation, no markdown fences.
"""


def call_groq(prompt):
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": GROQ_MODEL,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    usage = data.get("usage", {})
    return data["choices"][0]["message"]["content"], usage


def extract_code(text):
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


def run(instances):
    resolve_dynamic_accounts(ACCOUNTS)  # fills in nurse1/pharmacist1/accountant1 from the live DB
    for inst in instances:
        fname = f"c0_{inst['name']}.py"
        if os.path.exists(fname):
            print(f"=== C0: {inst['name']} === already done, skipping ({fname} exists)")
            continue
        print(f"=== C0: {inst['name']} ===")
        prompt = build_prompt(inst)
        reply, usage = call_groq(prompt)
        code = extract_code(reply)
        fname = f"c0_{inst['name']}.py"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Saved {fname}  (tokens used: {usage})")


if __name__ == "__main__":
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "new":
        run(INSTANCES_C0_NEW)          # only the 14 added for the remaining mutants
    elif arg == "original":
        run(INSTANCES_C0)              # only the original 4 (already run once -- no need to re-spend tokens)
    else:
        run(INSTANCES_C0 + INSTANCES_C0_NEW)
