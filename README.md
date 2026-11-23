# LLM-Driven Security Testing: A Policy-Grounded Differential Framework for Broken Access Control Testing in Web Applications

Replication package for the paper submitted to the *International Journal of Advanced Computer Science and Applications (IJACSA)*.

**Authors:** Sohaib Masood¹*, Rizwan Bin Faiz¹˒², Aamer Nadeem²
¹ Faculty of Computing, Riphah International University, Islamabad, Pakistan
² Software Engineering, Capital University of Science and Technology, Islamabad, Pakistan
*Corresponding author: sohaib.masood@au.edu.pk

---

## Overview

This repository contains the replication package for an LLM-driven approach to generate and judge Broken Access Control (BAC) tests using authorization-aware misuse case specifications. The framework introduces:

- **AAMCS** — Authorization-Aware Misuse Case Specification, an extension of Restricted Misuse Case Modeling (RMCM) that explicitly captures roles, ownership relations, resources, and access decisions.
- **PATM** — Policy-Bound Authorization Test Model, extracted from AAMCS by a large language model. Each PATM entry has three parts: the threat step, the authorization fact, and the test directive.
- **Paired differential testing** — every attack request is paired with an authorized baseline request, judged by a multi-evidence permission oracle (HTTP behavior, response content, database state).
- **Verdict-preserving repair loop** — repairs tests that fail to execute without changing their policy-derived verdict.

The framework was evaluated on a role-based Hospital Management System (HMS) across three conditions: **C0** (direct prompting), **C1** (permission-matrix-only prompting), and **C2** (the full AAMCS + PATM approach).

## Repository Contents

```
.
├── README.md                  # This file
├── prompts/                   # LLM prompt templates used for PATM extraction (C0, C1, C2)
├── patm-schema/                # PATM schema definition and example entries
├── permission-matrices/       # Role × resource × operation permission matrices for the HMS
├── mutants/                   # List and description of the 26 seeded mutants
├── generated-tests/           # Generated executable test scripts per condition (C0/C1/C2)
├── logs/                      # Execution logs, oracle verdicts, and repair-loop traces
└── results/                   # Raw evaluation data (ETR, detection rate, FPR per condition)
```

## Evaluation Metrics

- **ETR** — Executable Test Rate
- **Detection rate** — mutation score against seeded and pre-existing flaws
- **FPR** — False-positive rate on the patched application

## Key Results

| Condition | Detection Rate |
|---|---|
| C0 — Direct prompting | 34.6% (9/26) |
| C1 — Permission-matrix-only | 23.1% (6/26) |
| C2 — Full AAMCS + PATM | 73.1% (19/26) |

On the patched application, all three conditions reached an executable-test rate of 100%, and no condition reported a false positive.

## Requirements

- Python 3.10+
- Access to an LLM API (experiments used Groq's OpenAI-compatible endpoint; model/version details and prompts are reported in the Experimental Design section of the paper)
- A deployable instance of the target Hospital Management System (HMS) — see `generated-tests/README.md` for setup notes

## Reproducing the Experiments

1. Deploy the HMS instance (vulnerable and patched variants).
2. Load the permission matrix and AAMCS specifications from `permission-matrices/` and provide them to the model per the prompts in `prompts/`.
3. Run PATM extraction to generate threat test sequences.
4. Execute the paired baseline/attack requests using the scripts in `generated-tests/`.
5. Compare oracle verdicts against `mutants/` ground truth to compute ETR, detection rate, and FPR.

## Data Availability

All experiments were performed on local copies of the HMS with synthetic data; no real user data was used. The full package is available in this repository.

## Declaration on Generative AI

A generative AI assistant helped draft and edit parts of the manuscript and prepare the tables and framework figure; large language models are also part of the proposed method and its experiments, with versions and prompts reported in the Experimental Design section. The authors reviewed and edited all content and take full responsibility for it.

## Citation

If you use this framework or replication package, please cite:

```bibtex
@article{masood2026llmbac,
  title     = {LLM-Driven Security Testing: A Policy-Grounded Differential Framework for Broken Access Control Testing in Web Applications},
  author    = {Masood, Sohaib and Faiz, Rizwan Bin and Nadeem, Aamer},
  journal   = {International Journal of Advanced Computer Science and Applications (IJACSA)},
  year      = {2026}
}
```

## License

No external funding was received for this research. Add a LICENSE file of your choice (MIT or CC-BY-4.0 recommended for a replication package) before making this repository fully public.

## Contact

For questions, open an issue in this repository or contact the corresponding author: sohaib.masood@au.edu.pk
