"""
Runs every new c0_<name>.py / c1_<name>.py script twice each: once with V1 (the patched
baseline) live, once with its own mutant(s) live -- switching variants automatically with
switch_variant.py in between. Captures all raw stdout/stderr into one log file, clearly
labelled per run, so it can be read back and turned into results_C0.csv / results_C1.csv rows
(same way the original 4 scripts' results were reconstructed from a raw terminal log, per
README.md's description of raw_terminal_log_C0_C1.txt).

This script only drives switch_variant.py and the already-generated c0_*/c1_*.py files -- it
does not modify, regenerate, or re-run anything you've already produced.

Usage: python run_c0_c1_variants.py <hms_path> <variants_path>
e.g.:  python run_c0_c1_variants.py D:\\wamp64\\www\\hms variants
"""
import os, subprocess, sys, datetime

# instance name -> list of mutant ids whose live code it should be tested against
# (two instances map to two mutants each, since one misuse case/script covers both)
MAPPING = {
    "nurse_bed":            ["M13"],
    "admin_patient":        ["M14"],
    "pharmacist_medicine":  ["M16"],
    "accountant_invoice":   ["M17"],
    "appointment_list":     ["M19"],
    "patient_appointment":  ["M20", "M26"],
    "payment_history":      ["M21", "M27"],
    "admit_history":        ["M22"],
    "operation_history":    ["M23"],
    "invoice_list":         ["M24"],
    "appointment_doctor_isr": ["M28"],
    "manage_profile_isr":   ["M29"],
}

def run(cmd, log):
    log.write(f"$ {' '.join(cmd)}\n")
    log.flush()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    log.write(r.stdout)
    if r.stderr:
        log.write("--- stderr ---\n" + r.stderr)
    log.write(f"(exit code {r.returncode})\n")
    log.flush()

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python run_c0_c1_variants.py <hms_path> <variants_path>")
    hms_path, variants_path = sys.argv[1], sys.argv[2]
    logname = "c0_c1_new_raw_log.txt"
    with open(logname, "a", encoding="utf-8") as log:
        log.write(f"\n\n=== Run started {datetime.datetime.now().isoformat()} ===\n")
        for name, mutants in MAPPING.items():
            for cond in ("c0", "c1"):
                script = f"{cond}_{name}.py"
                if not os.path.exists(script):
                    log.write(f"\n### {cond} {name}: SKIPPED ({script} not found) ###\n")
                    continue
                # 1) baseline V1
                log.write(f"\n### {cond} {name} -- variant V1 (expect PASS / no violation) ###\n")
                run(["python", "switch_variant.py", hms_path, variants_path, "V1"], log)
                run(["python", script], log)
                # 2) each mapped mutant
                for mid in mutants:
                    log.write(f"\n### {cond} {name} -- variant {mid} (expect FAIL / violation found) ###\n")
                    run(["python", "switch_variant.py", hms_path, variants_path, mid], log)
                    run(["python", script], log)
        log.write(f"\n=== Run finished {datetime.datetime.now().isoformat()} ===\n")
    print(f"Done. Full output saved to {logname}")

if __name__ == "__main__":
    main()
