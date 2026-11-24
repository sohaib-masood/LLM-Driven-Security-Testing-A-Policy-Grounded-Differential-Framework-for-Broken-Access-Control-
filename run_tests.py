"""Stage 3 + oracle for condition C2, tailored to the four test instances.
Builds the baseline and attack request for each PATM entry, sends them to the live HMS,
and judges the verdict against the expected decision from the permission matrix.
Run this once for V1 (expect no violation) and once for each mutant M01..M12 (expect detection)."""
import csv, json, sys
import hms_client as hc
from db_check import row_exists, marker_present, resolve_dynamic_accounts
from config import ACCOUNTS, INSTANCES

def find_instance(name):
    for i in INSTANCES:
        if i["name"] == name:
            return i
    raise KeyError(name)

def run_one(entry, inst, step_cfg):
    acc = ACCOUNTS[inst["attacker"]]
    results = {"instance": inst["name"], "step": entry["step"], "role": entry["role"],
               "policy_ref": entry["policy_ref"], "expected_decision": entry["expected_decision"]}

    no_session = step_cfg.get("no_session", False)
    session = hc.new_session()
    logged_in = False
    if not no_session:
        logged_in = hc.login(session, acc["email"], acc["password"], acc["role"])
        results["login_ok"] = logged_in
        if not logged_in:
            results["observed_decision"] = "inconclusive"
            results["notes"] = "attacker login failed, baseline cannot be checked"
            return results

    path_tpl = step_cfg["path"]
    victim_id = inst.get("victim_id")
    own_id = inst.get("own_id")
    evidence = step_cfg["evidence"]
    method = step_cfg.get("method", "GET")
    post_data = step_cfg.get("post_data")
    token_path = step_cfg.get("token_path")

    # A victim_marker is usually a literal seeded string. For a page that leaks a real DB
    # value instead of a planted marker (e.g. patient 8's own name on view_admit_history,
    # which has no free-text field to seed), it can instead be a dict
    # {"table":, "id_col":, "id":, "col":}, resolved here into the literal string to look for.
    victim_marker = inst.get("victim_marker")
    if isinstance(victim_marker, dict):
        vm = victim_marker
        row = row_exists(f"SELECT {vm['col']} FROM {vm['table']} WHERE {vm['id_col']}=%s", (vm["id"],))
        victim_marker = str(row[0]) if row else None

    def send(path, data=None):
        if method == "POST":
            return hc.post(session, path, data or {}, token_path=token_path)
        return hc.get(session, path)

    # Baseline: own record, should be allowed (skip if the instance has no per-record id, e.g. instance 3 and 4)
    if own_id is not None:
        if evidence == "state":
            # This app redirects to the same list page whether a write succeeds or is denied,
            # so for a write (e.g. delete) we check the database, not the redirect, to see if
            # the baseline (own record) really went through.
            own_before = row_exists(step_cfg["state_query"], (own_id,))
            base_resp = send(path_tpl.format(id=own_id))
            own_after = row_exists(step_cfg["state_query"], (own_id,))
            baseline_ok = (own_before is not None and own_before[0] == 1 and
                           own_after is not None and own_after[0] == 0)
            results["baseline_denied"] = not baseline_ok
        else:
            base_resp = send(path_tpl.format(id=own_id))
            results["baseline_denied"] = hc.is_denied(base_resp)
        if results["baseline_denied"]:
            results["observed_decision"] = "inconclusive"
            results["notes"] = "baseline (own record) was denied, or was already consumed by an earlier run -- restore the seeded database and try again"
            return results

    # For state evidence, capture the database BEFORE sending the attack, not after.
    before = None
    if evidence in ("state", "state_changed"):
        before = row_exists(step_cfg["state_query"], (victim_id,))
        results["state_before"] = before

    # Attack: victim record, tampered role segment, forged POST field, or no session
    attack_path = path_tpl.format(id=victim_id) if victim_id is not None else path_tpl
    attack_resp = send(attack_path, post_data)
    denied_by_transport = hc.is_denied(attack_resp)

    violation = False
    if evidence == "transport":
        violation = not denied_by_transport
    elif evidence == "transport_inverted":
        # M16: the mutation denies a *legitimate* user instead of letting an attacker in, so
        # here the violation is the baseline-equivalent request itself being wrongly denied.
        violation = denied_by_transport
    elif evidence == "content":
        violation = (not denied_by_transport) and (victim_marker is not None) and (victim_marker in attack_resp.text)
    elif evidence == "transport_and_content":
        violation = (not denied_by_transport) and (victim_marker is not None) and (victim_marker in attack_resp.text)
    elif evidence == "state":
        after = row_exists(step_cfg["state_query"], (victim_id,))
        violation = (before is not None and before[0] == 1 and after is not None and after[0] == 0)
        results["state_after"] = after
    elif evidence == "state_changed":
        # M29: the oracle is whether a DB value actually changed (ISR via a forged POST
        # field), not whether a row count dropped to zero like the delete-based M01 check above.
        after = row_exists(step_cfg["state_query"], (victim_id,))
        violation = (before is not None and after is not None and before[0] != after[0])
        results["state_after"] = after

    results["denied_by_transport"] = denied_by_transport
    # observed_decision is computed exactly as in the original 12-mutant run (keyed off
    # `violation`), so results_M01..M12/V0/V1.csv stay directly comparable to a fresh re-run.
    results["observed_decision"] = "allow" if violation else "deny"
    # verdict: FAIL whenever a violation is found, PASS otherwise. For every entry with
    # expected_decision=="deny" (all of the original 12, and all but one of the new ones) this
    # is byte-for-byte the original formula. The one exception is M16, whose PATM entry has
    # expected_decision=="allow" because its "attacker" is really the legitimate pharmacist --
    # the original formula had no real branch for that case ("CHECK: expected allow" regardless
    # of outcome); `violation` already means "wrongly denied" there, so the same FAIL/PASS rule
    # applies correctly without needing a separate branch.
    results["verdict"] = "FAIL (violation found)" if violation else "PASS"
    return results

def run_all(target_name):
    resolve_dynamic_accounts(ACCOUNTS)  # fills in nurse1/pharmacist1/accountant1 from the live DB
    entries = json.load(open("patm_entries.json"))
    out = []
    for entry in entries:
        inst = next(i for i in INSTANCES if i["id"] == entry["instance_id"])
        estep = entry["step"].replace(" ", "")
        step_cfg = next(s for s in inst["steps"] if estep.startswith(s["step"].replace(" ", "")))
        try:
            r = run_one(entry, inst, step_cfg)
        except Exception as e:
            r = {"instance": inst["name"], "step": entry["step"], "observed_decision": "error", "notes": str(e)}
        out.append(r)
        print(r)
    fname = f"results_{target_name}.csv"
    cols = sorted({k for r in out for k in r})
    with open(fname, "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(out)
    print(f"\nWrote {fname}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "UNKNOWN"
    run_all(target)
