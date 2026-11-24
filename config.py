"""Central settings for the experiment. Edit only the two marked lines."""
import os

BASE_URL = "http://localhost/hms/"                      # your HMS address
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")        # set with: set GROQ_API_KEY=gsk_xxx  (Windows cmd)
GROQ_MODEL = "openai/gpt-oss-120b"                       # free Groq model

DB = dict(host="localhost", user="hms_ro", password="furqan123", database="binaryte_hms")  # <-- EDIT password if different

ACCOUNTS = {
    "admin1":       dict(role="admin",       id=1, email="admin@admin.com",     password="admin123"),
    "doctor4":      dict(role="doctor",      id=4, email="Rizwan@yahoo.com",    password="rizwan123"),
    "doctor6":      dict(role="doctor",      id=6, email="drsohaib@yahoo.com",  password="sohaib123"),
    "patient3":     dict(role="patient",     id=3, email="bilal@gmail.com",     password="bilal123"),
    "patient8":     dict(role="patient",     id=8, email="asif@yahoo.com",      password="asif123"),
    # added for the remaining-mutant extension (M13, M16, M17). No real email/password needed
    # here -- db_check.resolve_dynamic_accounts() fills these in from a real row in your live
    # database the first time any new script runs, so there is nothing to type in by hand.
    "nurse1":       dict(role="nurse",       id=None, email=None, password=None,
                          dynamic=True, dynamic_table="nurse", dynamic_id_col="nurse_id"),
    "pharmacist1":  dict(role="pharmacist",  id=None, email=None, password=None,
                          dynamic=True, dynamic_table="pharmacist", dynamic_id_col="pharmacist_id"),
    "accountant1":  dict(role="accountant", id=None, email=None, password=None,
                          dynamic=True, dynamic_table="accountant", dynamic_id_col="accountant_id"),
}

# The four test instances from Table II of the paper, with enough detail to build real HTTP requests.
INSTANCES = [
    dict(
        id=1, name="appointment",
        attacker="doctor4", own_id=30, victim_id=46, victim_marker="MARK_D06_X",
        steps=[
            dict(step="BTF",     method="GET", path="doctor/manage_appointment/edit/{id}",   evidence="transport"),
            dict(step="SATF1",   method="GET", path="doctor/manage_appointment/delete/{id}", evidence="state",
                 state_query="SELECT COUNT(*) FROM appointment WHERE appointment_id=%s"),
            # M28 (added for the remaining-mutant extension): forges a POST doctor_id field
            # instead of a wrong URL segment, to defeat the _own_appointment() helper directly.
            dict(step="M28", method="POST", path="doctor/manage_appointment/edit/{id}", evidence="transport",
                 post_data={"doctor_id": "6"}),
        ],
    ),
    dict(
        id=2, name="prescription",
        attacker="patient3", own_id=3, victim_id=5, victim_marker="MARK_RX05_X",
        steps=[
            dict(step="BTF", method="GET", path="patient/view_prescription/edit/{id}", evidence="content"),
        ],
    ),
    dict(
        id=3, name="doctor account",
        attacker="patient3", own_id=None, victim_id=None, victim_marker="MARK_D04_X",
        steps=[
            dict(step="SATF2", method="GET", path="admin/manage_doctor", evidence="transport_and_content", no_session=False),
            dict(step="SATF3", method="GET", path="admin/manage_doctor", evidence="transport", no_session=True),
        ],
    ),
    dict(
        id=4, name="invoice",
        attacker="doctor4", own_id=None, victim_id=None, victim_marker="MARK_INV03_X",
        steps=[
            dict(step="SATF2", method="GET", path="patient/view_invoice", evidence="transport", no_session=False),
            dict(step="SATF3", method="GET", path="patient/view_invoice", evidence="transport", no_session=True),
        ],
    ),
    # --- remaining mutants: M13, M14, M16, M17, M19-M24, M26, M27, M29 ---
    dict(
        id=5, name="nurse_bed",
        attacker="admin1", own_id=None, victim_id=None, victim_marker=None,
        steps=[dict(step="M13", method="GET", path="nurse/manage_bed", evidence="transport")],
    ),
    dict(
        id=6, name="admin_patient",
        attacker="patient3", own_id=None, victim_id=None, victim_marker=None,
        steps=[dict(step="M14", method="GET", path="admin/manage_patient", evidence="transport", no_session=True)],
    ),
    dict(
        id=7, name="pharmacist_medicine",
        attacker="pharmacist1", own_id=None, victim_id=None, victim_marker=None,
        steps=[dict(step="M16", method="GET", path="pharmacist/manage_medicine", evidence="transport_inverted")],
    ),
    dict(
        id=8, name="accountant_invoice",
        attacker="patient3", own_id=None, victim_id=None, victim_marker=None,
        steps=[dict(step="M17", method="GET", path="accountant/manage_invoice", evidence="transport", no_session=True)],
    ),
    dict(
        id=9, name="appointment_list",
        attacker="doctor4", own_id=None, victim_id=None, victim_marker="MARK_D06_X",
        steps=[dict(step="M19", method="GET", path="doctor/manage_appointment", evidence="content")],
    ),
    dict(
        id=10, name="patient_appointment",
        attacker="patient3", own_id=None, victim_id=None, victim_marker="MARK_D08_APPT_X",
        steps=[
            dict(step="M20", method="GET",  path="patient/view_appointment", evidence="content"),
            # view_appointment has no HTML form on it (no form_open()), so there's no CSRF
            # token to scrape from that page itself -- borrow one from manage_profile, which
            # does have a real form, so this forged POST actually reaches the controller
            # instead of being silently rejected by CSRF protection first.
            dict(step="M26", method="POST", path="patient/view_appointment", evidence="content",
                 token_path="patient/manage_profile", post_data={"patient_id": "8"}),
        ],
    ),
    dict(
        id=11, name="payment_history",
        attacker="patient3", own_id=None, victim_id=None, victim_marker="MARK_PAY08_X",
        steps=[
            dict(step="M21", method="GET",  path="patient/payment_history", evidence="content"),
            # payment_history has no HTML form either -- same fix as M26, borrow the token
            # from manage_profile's real form.
            dict(step="M27", method="POST", path="patient/payment_history", evidence="content",
                 token_path="patient/manage_profile", post_data={"patient_id": "8"}),
        ],
    ),
    dict(
        id=12, name="admit_history",
        attacker="patient3", own_id=None, victim_id=None,
        victim_marker=dict(table="patient", id_col="patient_id", id=8, col="name"),
        steps=[dict(step="M22", method="GET", path="patient/view_admit_history", evidence="content")],
    ),
    dict(
        id=13, name="operation_history",
        attacker="patient3", own_id=None, victim_id=None, victim_marker="MARK_OP08_X",
        steps=[dict(step="M23", method="GET", path="patient/view_operation_history", evidence="content")],
    ),
    dict(
        id=14, name="invoice_list",
        attacker="patient3", own_id=None, victim_id=None, victim_marker="MARK_INV08_X",
        steps=[dict(step="M24", method="GET", path="patient/view_invoice", evidence="content")],
    ),
    dict(
        id=15, name="manage_profile",
        attacker="patient3", own_id=None, victim_id=8,
        # NOTE: update_profile_info() always writes name/email/address/phone/sex/birth_date/age/
        # blood_group to whichever patient_id ends up in the WHERE clause -- the attacker's own
        # (patient3) row when this mutant is NOT live, patient 8's row when it IS live. To make the
        # not-live (every-other-mutant-run) case a harmless no-op, every field below except
        # `phone` is set to patient3's OWN real value, so it just writes itself back to itself.
        # Only `phone` carries a marker value, which is what the oracle actually checks.
        # token_path: the controller runs update_profile_info's write logic on ANY request to
        # that URL (GET included -- it only checks the URI segment, not the HTTP method), so
        # fetching the CSRF token from that same URL would itself silently wipe the attacker's
        # own profile with empty fields before the real POST even runs. Fetch the token from
        # the plain "patient/manage_profile" page instead, which only displays the form.
        steps=[dict(step="M29", method="POST", path="patient/manage_profile/update_profile_info",
                    token_path="patient/manage_profile",
                    evidence="state_changed", state_query="SELECT phone FROM patient WHERE patient_id=%s",
                    post_data={"patient_id": "8", "phone": "9998880008", "name": "Bilal",
                               "email": "bilal@gmail.com", "address": "Wah Cantt", "sex": "Male",
                               "birth_date": "2000-01-01", "age": "25", "blood_group": "O+"})],
    ),
]