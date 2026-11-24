# HMS BAC Test Generation — Replication Package

Supports the IJACSA paper "LLM-Driven Broken-Access-Control Test
Generation from Authorization-Aware Misuse Cases" (AAMCS / PATM /
multi-evidence oracle / repair loop), evaluated on a Hospital
Management System (HMS) built on CodeIgniter 2, running locally on
WampServer (`D:\wamp64\www\hms`).

## Subject application

- `binaryte_hms.sql` — the original (V0) HMS database dump.
- `binaryte_hms_seeded.sql` — the same schema with synthetic records
  and planted marker strings added for content-evidence detection
  (e.g. `MARK_D06_X`, `MARK_RX05_X`, `MARK_D04_X`, `MARK_INV03_X`).
- `seed_markers.sql` — the script that plants those marker strings.
- `accounts.csv` — synthetic test accounts (one per role) used as
  attacker/victim identities across all conditions.

## Mutants

- `build_variants.py` — builds V1 (the patched baseline) and the 12
  seeded mutants M01–M12 as small folders containing only the changed
  PHP controllers. Never modifies the original HMS in place.
- `mutant_list.csv` — the operator (B1–B4) and one-line description of
  each of the 12 mutants.
- `variants/` — the actual generated variant folders (V1, M01–M12),
  produced by `build_variants.py`.
- `switch_variant.py <hms_path> <variants_path> <V1|M01..M12>` — copies
  the chosen variant's controllers over the live WampServer HMS
  install. Always run `switch_variant.py ... V1` to reset before
  switching to the next variant.

## Permission matrix and PATM (condition C2 / full approach)

- `permission_matrix_hms_DRAFT.csv` — the full 452-row manually written
  permission matrix (role × operation × resource × ownership × decision).
- `permission_matrix_<role>.csv` — the same matrix split by role.
- `instances.json` — the four threat-test instances used across all
  three conditions (appointment, prescription, doctor_account, invoice).
- `prompt_stage2.txt`, `stage2_extract.py`, `complete_patm.py`,
  `validate_patm.py` — the PATM-extraction prompt and pipeline (Stage 2
  of the framework): extracts a Policy-Bound Authorization Test Model
  from the misuse case text and validates it against `patm_schema.json`.
- `patm_schema.json` — the PATM's JSON schema.
- `patm_entries.json` — the 7 real extracted PATM entries used in the
  paper's Table 6.
- `patm_log.json` — the raw extraction log (includes the one retry
  needed before every field validated, reported under RQ3).
- `run_experiment.py`, `run_tests.py`, `hms_client.py`,
  `check_db_access.py`, `db_check.py`, `groq_client.py` — the C2 test
  generation/execution pipeline (paired baseline/attack requests,
  multi-evidence oracle, repair loop).
- `results_V0.csv`, `results_V1.csv`, `results_M01.csv` … `results_M12.csv`
  — per-variant C2 results (native-flaw detection on V0, false-positive
  check on V1, mutation-kill verdicts on M01–M12).

## Baseline conditions C0 and C1

- `config.py` — shared Groq model/key config (`openai/gpt-oss-120b`,
  temperature 0) used identically by C0, C1, and C2 so the comparison
  isolates prompt structure, not model choice.
- `run_c0.py` — direct-prompting condition. Gives the LLM only the
  misuse case + Authorization Context (no PATM, no matrix) and has it
  write the test script itself. Produces `c0_appointment.py`,
  `c0_prescription.py`, `c0_doctor_account.py`, `c0_invoice.py`.
- `run_c1.py` — permission-matrix-only condition. Gives the LLM the
  matrix + application description (no misuse case, no PATM). Produces
  `c1_appointment.py`, `c1_prescription.py`, `c1_doctor_account.py`,
  `c1_invoice.py`.
- `results_C0.csv`, `results_C1.csv` — per-variant, per-attempt verdicts
  for all 13 variants (V1 + M01–M12), reconstructed from the terminal
  logs of the actual runs.
- `raw_terminal_log_C0_C1.txt` — the underlying raw terminal transcript
  the two CSVs above were built from (API keys redacted; the original
  keys were rotated after accidental exposure during this work).
- `cost_summary_C0_C1.csv` — per-instance Groq token/time usage for the
  final reported C0 and C1 generation runs (source for Table 9's cost
  columns: ~2033 tokens/test and ~2.58 s/test for C0; ~2074 tokens/test
  and ~2.58 s/test for C1).
- `list_appointments.py` — utility to check which appointment rows in
  the seeded database are still unconsumed (several tests delete
  appointment rows, so fresh IDs are needed across repeated runs).

## How to reproduce

1. Restore `binaryte_hms_seeded.sql` into MySQL and point WampServer's
   `hms` vhost at it.
2. `python build_variants.py D:\wamp64\www\hms D:\hms_experiment\variants`
   to (re)generate V1 and M01–M12.
3. `python switch_variant.py D:\wamp64\www\hms D:\hms_experiment\variants V1`
   to put the patched baseline live.
4. For C2: run the Stage 2 PATM extraction, then `run_experiment.py` /
   `run_tests.py` against V0, V1, and each mutant in turn (switching
   variants between runs).
5. For C0/C1: `python run_c0.py` (or `run_c1.py`) once per experiment
   to generate the four scripts, then run each `c0_*.py` / `c1_*.py`
   script against V1 and each mutant in turn, switching variants with
   `switch_variant.py` between runs.
6. Results for all three conditions are single runs (not averaged over
   multiple runs — see the paper's Threats to Validity section for why).

## Notes on data integrity

- All experiments ran against local, synthetic data only. No real
  patient or user data was used at any point.
- Two Groq API keys were exposed in terminal output during this work
  and were revoked/rotated immediately upon discovery; no key in this
  package or in the paper is live.
- Results reflect a single run per condition per variant, due to the
  per-call cost of the LLM API (see paper's Analysis and Threats to
  Validity sections).
