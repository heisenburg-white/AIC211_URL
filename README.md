# AIC211 Topic 2 – Robust Beyond the Benchmark

Cross-source and adversarial evaluation of lexical malicious URL detectors.

Course: AIC211 – AI for Cybersecurity · Team: Nhóm Trí · Status: draft; result numbers come from the 24 Oct 2026 freeze, a few `[TBD]` remain

---

## Overview

Many papers report 99% accuracy for malicious URL detectors on one benchmark. This project does **not** try to beat that number. It asks:

> How much of the benchmark score survives (a) data from a different source and (b) an attacker who edits the URL on purpose, and which cheap defense wins back the most?

All detectors use the **URL string only**. No page is ever opened, fetched or downloaded.

Four experiments answer the question:

| ID | Question | Short name |
|----|----------|------------|
| E1 | Does the model rely on real signals or on dataset artifacts? (random vs domain split, SHAP, feature ablation) | Check the shortcuts |
| E2 | How much does it drop on a second data source? (A-test vs B, 5 models) | Cross-source |
| E3 | How much does it drop when malicious URLs are edited? (7 transformations T1–T7, budget k, random and greedy black-box attack) | Adversarial |
| E4 | How much do three defenses (D1, D2, D3) recover, and at what cost? | Defense |

Pipeline: raw data → shared cleaning and domain split → two feature sets (F1: 19 handcrafted features, F2: character n-gram TF-IDF) → 5 models → decision threshold locked at 1% false positive rate (FPR) on the validation set of source A → E1–E4.

Terminology used everywhere in this repo: **F1-score** is the metric; **F1 features** is the feature set.

### Repository layout

```
AIC211_URL/
├── README.md
├── requirements.txt        # [TBD] pinned after the reproducibility run
├── .gitignore
├── src/                    # shared modules; do not edit, add new files instead
│   ├── common.py           # cleaning, domain split, F1/F2, threshold_at_fpr, evaluate, log_result
│   ├── attacks.py          # T1–T7, is_valid, to_attack_form, defang
│   ├── e3.py               # make_score_fn, random and greedy attacks, attack_success_rate
│   ├── defenses.py         # d1_normalize
│   ├── d2.py               # d2_features, make_F1D2
│   ├── e4.py               # load_configs (5 defense configurations), clean_eval; written by notebook 07 (cell 3)
│   └── defenses_plus.py    # [TBD] optional D1+ (TV3)
├── notebooks/              # 01_… to 10_demo, in run order (see "How to run")
├── models/                 # small JSON only: thresholds*.json, model_info.json
├── data/                   # EMPTY on GitHub (see "Data")
├── results/
│   ├── results.csv                      # every result, written only through log_result()
│   ├── results_FROZEN_2026-10-24.csv    # source of all numbers in the report (frozen 24 Oct 2026)
│   ├── dedup_log.csv
│   ├── tables/                          # final tables, auto-generated
│   └── appendix/                        # samples_T1.txt … samples_T7.txt (defanged)
└── figures/                # final figures, auto-generated
```

The repo mirrors the working folder on Google Drive (without data and model files), so a notebook only needs its `ROOT` line changed.

---

## Data

**No data is stored in this repository.** Download the datasets yourself and place them under `data/raw/` (git-ignored). Notebook `01_data_baseline.ipynb` builds `data/processed/A.parquet` and `B.parquet` from them.

### Source A – Malicious URLs dataset (Kaggle) · train / validation / test

- Kaggle dataset "Malicious URLs dataset" by `sid321axn`: https://www.kaggle.com/datasets/sid321axn/malicious-urls-dataset `[TBD: verify link in T4-06]`
- Download from the Kaggle page (login required) or with the Kaggle CLI. Expected raw file: `[TBD: exact file name, confirm with TV1]`.
- We draw a random sample of 100,000 URLs (sampling seed: `[TBD]`).
- Labels: benign = 0; phishing + malware = 1; defacement is dropped.
- Split 70/15/15 by **registered domain**, so one domain never appears in two splits.
- This dataset merges several public sources. ISCX-URL-2016 is one of them, but we do not use ISCX directly. `[TBD: confirm wording in T4-06]`

### Source B – PhiUSIIL Phishing URL dataset (UCI) · test only

- UCI Machine Learning Repository, dataset id 967: https://archive.ics.uci.edu/dataset/967 (CC BY 4.0, 235,795 instances).
- Option 1: download the CSV from the UCI page. Option 2: `ucimlrepo.fetch_ucirepo(id=967)`. Route used by the notebook: `[TBD: confirm with TV1]`.
- We keep only the URL and the label. The original label is 1 = legitimate, 0 = phishing; the pipeline flips it so that 1 = malicious.
- B is used for testing only. Nothing (threshold, hyperparameters) is tuned on B.
- URLs whose registered domain also appears in the training split of A are removed from B.

### Source C – OpenPhish snapshot (optional) · recall only

- A snapshot of the public OpenPhish feed taken on 10 Oct 2026, 300 malicious URLs, stored locally under `data/raw/openphish/`.
- Not redistributed in this repo. `[TBD: file naming and redistribution terms, confirm with TV2]`
- It has no benign URLs, so only recall can be measured.

### Cleaning summary

| Source | Raw | After cleaning | Source file |
|--------|-----|----------------|-------------|
| A | 100,000 (sample) | 98,620 | `results/dedup_log.csv` |
| B | 235,795 | 213,721 | `results/dedup_log.csv` |

Per-step counts (source: `results/dedup_log.csv`):

| Step | A | B |
|------|---|---|
| Raw | 100,000 | 235,795 |
| After dropping missing values | 100,000 (−0) | 235,795 (−0) |
| After dropping URLs that carry both labels | 99,707 (−293) | 235,711 (−84) |
| After exact-duplicate removal | 98,620 (−1,087) | 233,297 (−2,414) |
| Further exact-duplicate removal (`B_after_exact`) | – | 233,284 (−13) `[TBD: confirm meaning with TV1]` |
| Removal of URLs whose registered domain is in the training split of A | – | 213,721 (−19,563) |

### Citations

- Prasad, A., Chandra, S. PhiUSIIL: A diverse security profile empowered phishing URL detection framework based on similarity index and incremental learning. *Computers & Security* (2024). doi:10.1016/j.cose.2023.103545
- Kaggle "Malicious URLs dataset": `[TBD: full citation, T4-06]`

---

## How to run

Everything runs on Google Colab with Google Drive mounted.

### 1. Set up

1. Copy the project folder to Google Drive as `AIC211_URL` (or add a shortcut to My Drive). Put the raw data under `AIC211_URL/data/raw/` as described above.
2. Every notebook starts with the same cell. Only the `ROOT` line may change:

```python
from google.colab import drive
drive.mount('/content/drive')
ROOT = '/content/drive/MyDrive/AIC211_URL'
import sys
sys.path.insert(0, ROOT + '/src')
```

3. Install dependencies: `pip install -r requirements.txt` (Python version: `[TBD]`).

### 2. Run the notebooks in this order

| # | Notebook | What it does | Owner | Runtime |
|---|----------|--------------|-------|---------|
| 1 | `01_data_baseline.ipynb` | Cleaning, domain split, LR-F1 baseline | TV1 | [TBD] |
| 2 | `02_threat_model_T1_T7.ipynb` | Transformations T1–T7 and validity checks | TV2 | [TBD] |
| 3 | `03_models_E1_E2.ipynb` | 5 models, locked thresholds, E1, E2 | TV1 | [TBD] |
| 4 | `04_attack_trial_D1.ipynb` | First attack trials, first version of D1 | TV2 | [TBD] |
| 5 | `05_E3_D1.ipynb` | E3 (seed 0) and final D1 | TV2 | [TBD] |
| 6 | `06_D2_tables.ipynb` | D2 features and summary tables | TV1 | [TBD] |
| 7 | `07_D3_E4.ipynb` | D3 and E4 (seed 0), list of URLs that still evade | TV2 | [TBD] |
| 8 | `08_3seeds_error_analysis.ipynb` | Seeds 1 and 2, error analysis | TV1 | [TBD] |
| 9 | `09_E2b_D1plus.ipynb` | Shape control (E2b) and D1+ `[TBD: optional]` | TV3 | [TBD] |
| 10 | `10_demo.ipynb` | Gradio demo (string processing only) | TV4 | 59s |

Model files (`.joblib`) are not in the repo. They are regenerated by notebooks 03, 06 and 07.

### 3. Reproducibility check

Do **not** re-run notebooks in the main folder: they append rows to `results/results.csv`. Copy the folder to `AIC211_URL_repro`, copy `data/raw/` into it, change only the `ROOT` line, run the notebooks in the order above, then compare the seed 0 numbers (thresholds, LR-F1 baseline, E3 at k = 1, E4 seed 0) with `results/results_FROZEN_2026-10-24.csv`. Outcome of the check: `[TBD]`.

Results are written only through `log_result()`. Tables and figures are generated from `results.csv`, never typed by hand.

---

## Results

All numbers below come from `results/results_FROZEN_2026-10-24.csv` (frozen on 24 Oct 2026). Rows that repeat the same key (experiment, model, defense, source, seed, k, ops, mode) are counted once, keeping the last one, as in notebook 08. Metric of record: **recall at 1% FPR**, with the threshold chosen on the validation split of A and never changed. Recall, FPR and ASR are shown in percent; F1-score and PR-AUC are between 0 and 1.

**E1 – is the score real? (RF-F1, threshold locked, A-test)**

| Split of A-test | F1-score | Recall | FPR |
|-----------------|----------|--------|-----|
| A-test-random | 0.663 | 51.5% | 1.06% |
| A-test-domain | 0.546 | 38.7% | 0.82% |

**E2 – cross-source (A-test vs B, locked thresholds)**

| Model | Test set | Precision | Recall | F1-score | FPR | PR-AUC |
|-------|----------|-----------|--------|----------|-----|--------|
| LR-F1 | A-test | 0.839 | 0.144 | 0.245 | 0.72% | 0.526 |
| LR-F1 | B | 0.956 | 0.035 | 0.068 | 0.10% | 0.432 |
| RF-F1 | A-test | 0.925 | 0.387 | 0.546 | 0.82% | 0.715 |
| RF-F1 | B | 0.226 | 0.465 | 0.304 | 100.00% | 0.254 |
| XGB-F1 | A-test | 0.931 | 0.385 | 0.545 | 0.74% | 0.722 |
| XGB-F1 | B | 0.237 | 0.496 | 0.321 | 99.99% | 0.262 |
| LR-F2 | A-test | 0.882 | 0.336 | 0.487 | 1.17% | 0.765 |
| LR-F2 | B | 0.771 | 0.240 | 0.366 | 4.48% | 0.638 |
| SVM-F2 | A-test | 0.880 | 0.333 | 0.483 | 1.18% | 0.751 |
| SVM-F2 | B | 0.762 | 0.252 | 0.379 | 4.94% | 0.637 |

Confusion matrices: `results/tables/[TBD]`.

**E3 – recall under attack (all changes T1–T7, mean of 3 seeds, standard deviation at most 3.6 points)**

Source A-test:

| Model | Attack | k = 0 | k = 1 | k = 2 | k = 3 | k = 5 |
|-------|--------|-------|-------|-------|-------|-------|
| RF-F1 | random | 39.0% | 27.0% | 18.9% | 15.9% | 6.9% |
| RF-F1 | greedy | 39.0% | 5.3% | 4.2% | 3.8% | 3.4% |
| LR-F2 | random | 36.0% | 33.6% | 31.7% | 30.6% | 29.4% |
| LR-F2 | greedy | 36.0% | 23.6% | 17.2% | 12.9% | 9.3% |

Source B:

| Model | Attack | k = 0 | k = 1 | k = 2 | k = 3 | k = 5 |
|-------|--------|-------|-------|-------|-------|-------|
| RF-F1 | random | 46.0% | 36.7% | 27.9% | 21.3% | 9.4% |
| RF-F1 | greedy | 46.0% | 0.7% | 0.4% | 0.3% | 0.3% |
| LR-F2 | random | 22.7% | 19.7% | 17.3% | 17.3% | 16.6% |
| LR-F2 | greedy | 22.7% | 8.0% | 2.6% | 0.6% | 0.2% |

**E4 – defenses (RF-F1 on A-test; attack columns are the mean of 3 seeds, k = 3, all changes; clean columns come from seed 0 because the models are not retrained per seed)**

| Configuration | F1-score (clean A) | FPR A | FPR B | Recall under greedy | ASR greedy | ASR random | ASR T6 only (k = 1) | Avg. queries (greedy) |
|---------------|--------------------|-------|-------|---------------------|------------|------------|---------------------|-----------------------|
| none | 0.546 | 0.82% | 100.00% | 3.8% | 90.3% | 59.3% | 8.8% | 15.6 |
| D1 | 0.542 | 0.86% | 100.00% | 12.0% | 69.0% | 39.9% | 7.8% | 17.8 |
| D2 | 0.545 | 1.19% | 100.00% | 12.7% | 68.3% | 43.6% | 9.4% | 17.6 |
| D1+D2 | 0.541 | 1.18% | 100.00% | 12.7% | 68.3% | 38.9% | 10.0% | 17.9 |
| D1+D2+D3 | 0.544 | 0.94% | 100.00% | 14.7% | 63.9% | 22.4% | 6.8% | 18.5 |

ASR (attack success rate) = share of malicious URLs that were detected before the edit and evade after it.

**Extra analyses**

E2b shape control (recall at the locked threshold; home page = URL with no path):

| Model | A-test all | A-test home | A-test path | B all | B home | B path |
|-------|-----------|-------------|-------------|-------|--------|--------|
| RF-F1 | 38.7% | 92.6% | 24.9% | 46.5% | 65.0% | 2.1% |
| LR-F2 | 33.6% | 18.9% | 37.4% | 24.0% | 22.7% | 27.2% |

D1+ (TV3): `[TBD]`

**Negative results** reported in the paper: `[TBD]`

Figures: `figures/` `[TBD]`.

---

## Safety

- **No live malicious URLs in this repo.** Every URL shown in the README, report, appendix, figures and demo is defanged (`hxxp`, `[.]`).
- **Never open, click or download** any URL from the datasets. The code only processes strings and never makes a network request to a URL from the data.
- The demo (`10_demo.ipynb`) is string-only: it scores and edits text and blocks outbound connections while it does so.
- Raw datasets and the OpenPhish snapshot are git-ignored. Model files are git-ignored.
- Every attacker edit is checked by `is_valid()`. Edits that need a new domain (T5–T7) must not reuse a known benign domain, and no real brand domain is used.
- The attacks are for evaluating and hardening detectors. Do not use them against real systems.
- Pre-commit check (should print nothing): `grep -rEn "https?://" results/ figures/ notebooks/ README.md`
  Links to datasets in this README are the only expected matches.

---

## AI usage

Declaration draft (final wording: T4-08, `[TBD]`).

- Tool: Claude (Anthropic). Version and dates: `[TBD]`.
- Used for: drafting Colab code, README and report text, and explaining concepts. Exact sections per member: `[TBD]`.
- Not delegated: running the code, choosing thresholds, and all reported numbers. Code was run by team members on Colab and output was pasted back.
- How we checked: every number in a draft is traced to a named source file; results are written only by `log_result()`; numbers in the report and slides are compared with `results_FROZEN_2026-10-24.csv`; citations are compared with the original papers.

---

## Team

Two members are both named Nguyễn Minh Trí; always use the TV number or student ID.

| Member | Name | Student ID | Role |
|--------|------|------------|------|
| TV1 | Nguyễn Minh Trí | SE204163 | Data and models: cleaning, split, F1/F2, 5 models, thresholds, E1, E2, D2, 3 seeds |
| TV2 | Ngô Minh Nhựt | SE204149 | Attacks and defenses: threat model, T1–T7, E3, D1, D3, E4 |
| TV3 | Nguyễn Minh Trí | SE211087 | Team lead: extra analyses, introduction to conclusion, editing, submission |
| TV4 | Nguyễn Trần Đan Huy | SE211085 | Repo, README, demo, reproducibility check, appendix, references, AI declaration |

License: `[TBD]`
