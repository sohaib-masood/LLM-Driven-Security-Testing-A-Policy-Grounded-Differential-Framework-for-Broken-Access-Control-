"""Stage 2: builds the real statements for the four instances, sends each to the LLM,
validates and completes each entry. Writes patm_entries.json. No HTTP, no database used here."""
import json, re
from groq_client import call_llm
from validate_patm import validate
from complete_patm import load_matrix, load_instances, complete
from config import INSTANCES

CONTEXT = ("Roles: admin, doctor, nurse, patient, pharmacist, laboratorist, accountant. "
           "Operations: view, edit, and delete appointment; view prescription; manage doctors; view invoice. "
           "Resource types: appointment, prescription, doctor account, invoice. Ownership model: own, other, none. "
           "A resource with owner field none has no owner. The doctor account resource has no owner field, so its "
           "ownership value is always none, never other.")

STATEMENT = {
    ("appointment", "BTF"): "BTF 6. The MALICIOUS_DOCTOR replaces the appointment identifier with the identifier of an appointment of another doctor.",
    ("appointment", "SATF1"): "SATF 1.2. The MALICIOUS_DOCTOR replaces the action with delete and sends the request with the identifier of an appointment of another doctor.",
    ("prescription", "BTF"): "BTF 6. The MALICIOUS_PATIENT replaces the prescription identifier with the identifier of a prescription of another patient.",
    ("doctor account", "SATF2"): "SATF 2.2. The MALICIOUS_PATIENT performs the manage operation on the doctor account resource by replacing the role segment of the URL with the admin segment to reach the doctor account page.",
    ("doctor account", "SATF3"): "SATF 3.2. The MALICIOUS_PATIENT performs the manage operation on the doctor account resource and sends the request without a session.",
    ("invoice", "SATF2"): "SATF 2.2. The MALICIOUS_DOCTOR performs the view operation on the invoice resource by replacing the role segment of the URL with the patient segment to reach the invoice page.",
    ("invoice", "SATF3"): "SATF 3.2. The MALICIOUS_DOCTOR performs the view operation on the invoice resource, to view invoices belonging to another patient, and sends the request without a session.",
}
MAX_RETRY = 3

def run():
    tpl = open("prompt_stage2.txt").read()
    matrix = load_matrix("permission_matrix_hms_DRAFT.csv")
    instances = load_instances("instances.json")
    log = []
    results = []
    for inst in INSTANCES:
        for step in inst["steps"]:
            key = (inst["name"], step["step"])
            text = STATEMENT.get(key)
            if text is None:
                print("SKIP (no statement written for)", key); continue
            step_label = re.match(r"(BTF|SATF|SAF) ?\d+(\.\d+)?", text).group(0)
            errors = ""; entry = None
            for attempt in range(MAX_RETRY + 1):
                prompt = tpl.format(context=CONTEXT, statement=text, errors=errors)
                raw = call_llm(prompt).strip()
                err, entry = validate(raw, step_label, {"appointment", "prescription", "doctor account", "invoice"})
                print(f"{inst['name']} {step['step']} attempt {attempt}: {'OK' if not err else err}")
                if not err:
                    break
                errors = "ERRORS OF THE PREVIOUS OUTPUT (correct them):\n" + "\n".join(err) + "\n"
            if entry is None:
                log.append((key, "failed after retries")); continue
            completed = complete(entry, matrix, instances, log)
            completed["instance_id"] = inst["id"]
            results.append(completed)
    with open("patm_entries.json", "w") as f:
        json.dump(results, f, indent=2)
    with open("patm_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print(f"\nWrote {len(results)} PATM entries to patm_entries.json")
    if log:
        print(f"{len(log)} issues logged in patm_log.json")

if __name__ == "__main__":
    run()
