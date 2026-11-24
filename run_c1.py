"""
Condition C1: permission matrix only.
The LLM gets the permission matrix and application description (no misuse case, no PATM)
and must write the test script itself. Uses the same Groq key/model as C0/C2 (config.py).
"""
import os
import re
import requests
from config import GROQ_API_KEY, GROQ_MODEL, BASE_URL, ACCOUNTS
from db_check import resolve_dynamic_accounts

PERMISSION_MATRIX_EXCERPT = """\
Role    | Operation        | Resource      | Ownership | Decision
doctor  | view appointment | appointment   | own       | allowed
doctor  | view appointment | appointment   | other     | denied
doctor  | delete appointment | appointment | other     | denied
patient | view prescription | prescription | other     | denied
patient | manage doctors   | doctor account| none      | denied
admin   | manage doctors   | doctor account| none      | allowed
patient | view prescription | prescription | own       | allowed
patient | view invoice     | invoice       | own       | allowed
doctor  | view invoice     | invoice       | other     | denied
"""

APP_DESCRIPTION = (
    "The subject is an open-source Hospital Management System (HMS) written in PHP with the "
    "CodeIgniter framework and a MySQL database. It is a role-based application with seven roles "
    "(admin, doctor, nurse, patient, pharmacist, laboratorist, accountant) and 70 controller actions, "
    "most of them protected by a session and role guard. Many actions also filter records by the "
    "identifier of the logged-in doctor or patient."
)

INSTANCES_C1 = [
    dict(
        name="appointment",
        attacker="doctor4",
        own_id=32, victim_id=35,
        victim_marker="MARK_D06_X",
        relevant_rows=(
            "doctor | view appointment | appointment | own | allowed\n"
            "doctor | view appointment | appointment | other | denied\n"
            "doctor | delete appointment | appointment | other | denied"
        ),
        endpoint="doctor/manage_appointment/edit/{id} and doctor/manage_appointment/delete/{id}",
    ),
    dict(
        name="prescription",
        attacker="patient3",
        own_id=3, victim_id=5,
        victim_marker="MARK_RX05_X",
        relevant_rows=(
            "patient | view prescription | prescription | own | allowed\n"
            "patient | view prescription | prescription | other | denied"
        ),
        endpoint="patient/view_prescription/edit/{id}",
    ),
    dict(
        name="doctor_account",
        attacker="patient3",
        own_id=None, victim_id=None,
        victim_marker="MARK_D04_X",
        relevant_rows=(
            "patient | manage doctors | doctor account | none | denied\n"
            "admin | manage doctors | doctor account | none | allowed"
        ),
        endpoint="admin/manage_doctor",
    ),
    dict(
        name="invoice",
        attacker="doctor4",
        own_id=None, victim_id=None,
        victim_marker="MARK_INV03_X",
        relevant_rows=(
            "patient | view invoice | invoice | own | allowed\n"
            "doctor | view invoice | invoice | other | denied"
        ),
        endpoint="patient/view_invoice",
    ),
]


# --- remaining mutants: M13, M14, M16, M17, M19-M24, M26-M29 ---
INSTANCES_C1_NEW = [
    dict(
        name="nurse_bed", attacker="admin1", own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny", method="GET",
        relevant_rows=(
            "admin | manage | bed | none | denied    (P225)\n"
            "nurse | manage | bed | none | allowed    (P227)"
        ),
        endpoint="nurse/manage_bed",
        note="Only the admin/P225 row is under test: an admin session hitting a nurse-only page must be denied.",
    ),
    dict(
        name="admin_patient", attacker=None, own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny", method="GET",
        relevant_rows=(
            "admin | manage patients | patient account | none | allowed    (P071)\n"
            "patient | manage patients | patient account | none | denied    (P074)"
        ),
        endpoint="admin/manage_patient",
        note="Send with NO session at all (do not log in). The admin-only page must deny an unauthenticated request.",
    ),
    dict(
        name="pharmacist_medicine", attacker="pharmacist1", own_id=None, victim_id=None, victim_marker=None,
        expected_decision="allow", method="GET",
        relevant_rows=("pharmacist | manage | medicine | none | allowed    (P363)"),
        endpoint="pharmacist/manage_medicine",
        note="This is the legitimate pharmacist's own page -- expected decision is ALLOWED, not denied.",
    ),
    dict(
        name="accountant_invoice", attacker=None, own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny", method="GET",
        relevant_rows=("patient | manage | invoice | none | denied    (P434)"),
        endpoint="accountant/manage_invoice",
        note="Send with NO session at all (do not log in). The accountant-only page must deny an unauthenticated request.",
    ),
    dict(
        name="appointment_list", attacker="doctor4", own_id=None, victim_id=None, victim_marker="MARK_D06_X",
        expected_decision="deny", method="GET",
        relevant_rows=("doctor | view | appointment | other | denied    (P151)"),
        endpoint="doctor/manage_appointment",
        note="This is the plain LIST page (no id in the URL). A different doctor's appointment must not appear in it.",
    ),
    dict(
        name="patient_appointment", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_D08_APPT_X", expected_decision="deny", method="GET+POST",
        relevant_rows=(
            "patient | view | appointment | own | allowed    (P309)\n"
            "patient | view | appointment | other | denied    (P310)"
        ),
        endpoint="patient/view_appointment",
        note=("Test the P310 row two ways: (a) a plain GET; (b) a POST to the same URL with an "
              "extra forged field patient_id=8. Neither must leak a different patient's appointment."),
    ),
    dict(
        name="payment_history", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_PAY08_X", expected_decision="deny", method="GET+POST",
        relevant_rows=(
            "patient | view | payment history | own | allowed    (P293)\n"
            "patient | view | payment history | other | denied    (P294)"
        ),
        endpoint="patient/payment_history",
        note=("Test the P294 row two ways: (a) a plain GET; (b) a POST to the same URL with an "
              "extra forged field patient_id=8."),
    ),
    dict(
        name="admit_history", attacker="patient3", own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny", method="GET",
        relevant_rows=(
            "patient | view | admit history | own | allowed    (P301)\n"
            "patient | view | admit history | other | denied    (P302)"
        ),
        endpoint="patient/view_admit_history",
        note=("No content marker here: patient 8 has a bed allotment of their own; look up patient "
              "8's real name from the `patient` table (column `name`) and check it doesn't appear "
              "in the attacker's response."),
    ),
    dict(
        name="operation_history", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_OP08_X", expected_decision="deny", method="GET",
        relevant_rows=(
            "patient | view | operation history | own | allowed    (P339)\n"
            "patient | view | operation history | other | denied    (P340)"
        ),
        endpoint="patient/view_operation_history",
        note="",
    ),
    dict(
        name="invoice_list", attacker="patient3", own_id=None, victim_id=None,
        victim_marker="MARK_INV08_X", expected_decision="deny", method="GET",
        relevant_rows=(
            "patient | view | invoice | own | allowed    (P331)\n"
            "patient | view | invoice | other | denied    (P332)"
        ),
        endpoint="patient/view_invoice",
        note="This tests the ownership FILTER on the list page itself, a different row from the already-tested invoice guard.",
    ),
    dict(
        name="appointment_doctor_isr", attacker="doctor4", own_id=32, victim_id=35,
        victim_marker="MARK_D06_X", expected_decision="deny", method="POST",
        relevant_rows=(
            "doctor | edit | appointment | own | allowed    (P158)\n"
            "doctor | edit | appointment | other | denied    (P159)"
        ),
        endpoint="doctor/manage_appointment/edit/{id} (POST, forged doctor_id=6)",
        note="POST a forged doctor_id=6 (the real owner's id) alongside the edit request, instead of tampering the URL id.",
    ),
    dict(
        name="manage_profile_isr", attacker="patient3", own_id=None, victim_id=None, victim_marker=None,
        expected_decision="deny", method="POST",
        relevant_rows=(
            "patient | manage | profile | own | allowed    (P285)\n"
            "patient | manage | profile | other | denied    (P286)"
        ),
        endpoint="patient/manage_profile/update_profile_info (POST, forged patient_id=8, phone=0000000008)",
        note=("No content marker: the oracle is a direct, read-only database check of whether patient "
              "8's phone actually changed to 0000000008 after the request."),
    ),
]


def build_prompt(inst):
    attacker = ACCOUNTS[inst["attacker"]] if inst.get("attacker") else None
    expected = inst.get("expected_decision", "see the matrix rows above")
    note = inst.get("note", "")
    if attacker is not None:
        account_line = f"- Account to use: role={attacker['role']}, email={attacker['email']}, password={attacker['password']}"
    else:
        account_line = "- NO session at all: do not log in, just send the request with a fresh requests.Session()."
    extra_note = f"\n- Note: {note}" if note else ""
    return f"""You are testing a Hospital Management System (HMS) for compliance with an access-control permission matrix.

Application description: {APP_DESCRIPTION}

Full permission matrix (excerpt, 9 of 452 rows):
{PERMISSION_MATRIX_EXCERPT}

Rows relevant to this test:
{inst['relevant_rows']}

Test context (no attack scenario is given — derive the test purely from the matrix rows above):
- Base URL: {BASE_URL}
{account_line}
- "Own" resource ID (if applicable): {inst.get('own_id')}
- "Other" resource ID (if applicable, belongs to a different user): {inst.get('victim_id')}
- Endpoint(s): {inst['endpoint']}
- Request method(s) to use: {inst.get('method', 'GET')} (GET+POST means test it both ways: once with a plain
  GET, once with a POST to the same URL carrying an extra forged identifier field as named in the endpoint above)
- Expected decision under test: {expected}{extra_note}
- Login mechanism (skip entirely if "NO session" is specified above): GET {BASE_URL}index.php?/login first to
  obtain the page, then parse the hidden input named "authenticity_token" from its HTML (its value changes per
  page load). POST to {BASE_URL}index.php?/login with form fields: login_type (one of admin, doctor, patient,
  nurse, pharmacist, laboratorist, accountant), email, password, and authenticity_token (the scraped value).
  Use a requests.Session() so the resulting session cookie is kept. Login failed if resp.text still contains
  'name="login_type"' after the POST.
- For any POST with a forged field: first GET the target page to scrape a fresh "authenticity_token" the same
  way as login, then POST to the same URL with that token plus the forged field(s) named in the endpoint above.
- Important application quirk: this application's redirects use CodeIgniter's 'refresh' method, which returns
  HTTP 200 with a Refresh header or a meta-refresh tag instead of a real 3xx redirect. Do NOT use resp.url or
  resp.status_code alone to decide allow/deny; a response is "denied by transport" if it is a classic 3xx
  redirect, OR carries a Refresh header, OR its HTML contains a <meta http-equiv="refresh"> tag.
- Reliable detection method: if a marker string is given below, use it and only it to tell "other" data was
  actually rendered: "{inst.get('victim_marker')}". If this string appears anywhere in resp.text, the "other"
  resource's data was rendered (decision = allowed); if it does not appear, treat the transport-denial check
  above as the decision instead. If no marker string is given, use whatever oracle the Note above describes
  (a direct database check, or the transport-denial check alone). For any "own" resource request, just confirm
  it returns HTTP 200 without a server error.

Task: Write a complete, runnable Python script using the `requests` library that:
1. Logs in using the account above if one is specified, confirming success via resp.text (not resp.url). Skip login if no session is specified.
2. For each matrix row relevant to this endpoint, sends the corresponding request(s) exactly as described above (own/other, GET/POST, forged fields) and checks the outcome against the matrix's stated decision, using the detection method described above.
3. Prints one line per row tested: PASS if the observed behavior matches the matrix's decision, FAIL if it does not, with a short reason.

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
        fname = f"c1_{inst['name']}.py"
        if os.path.exists(fname):
            print(f"=== C1: {inst['name']} === already done, skipping ({fname} exists)")
            continue
        print(f"=== C1: {inst['name']} ===")
        prompt = build_prompt(inst)
        reply, usage = call_groq(prompt)
        code = extract_code(reply)
        fname = f"c1_{inst['name']}.py"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Saved {fname}  (tokens used: {usage})")


if __name__ == "__main__":
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "new":
        run(INSTANCES_C1_NEW)          # only the 14 added for the remaining mutants
    elif arg == "original":
        run(INSTANCES_C1)              # only the original 4 (already run once -- no need to re-spend tokens)
    else:
        run(INSTANCES_C1 + INSTANCES_C1_NEW)
