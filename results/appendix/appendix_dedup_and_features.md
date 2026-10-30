# Appendix tables (T4-05)

Draft by TV4 (SE211085), 24 Oct 2026; A3 added 29 Oct 2026. Tables are in English for the report. `[TBD]` marks what still needs a confirmation.

## Table A2. Cleaning and de-duplication log

Source: `results/dedup_log.csv`. Removed counts are the difference between consecutive steps.

| Step | Source A | Source B |
|------|---------:|---------:|
| Raw | 100,000 | 235,795 |
| After dropping missing values | 100,000 (−0) | 235,795 (−0) |
| After dropping URLs that carry both labels | 99,707 (−293) | 235,711 (−84) |
| After exact-duplicate removal | 98,620 (−1,087) | 233,297 (−2,414) |
| Further exact-duplicate removal (`B_after_exact`) | – | 233,284 (−13) |
| After removing URLs whose registered domain is in the training split of A | – | 213,721 (−19,563) |
| **Final** | **98,620** | **213,721** |

Notes
- Source A: 100,000 raw rows is the random sample drawn from the Kaggle dataset; the log does not show the removal of the defacement class, so that step happens before this log. `[TBD: confirm order with TV1]`
- Source B: the 13 URLs removed in `B_after_exact` come from a second exact-duplicate pass. `[TBD: confirm what this pass compares, with TV1]`
- Source B: total removed = 22,074 (84 + 2,414 + 13 + 19,563).
- Source A is split ≈ 73/13/14 by registered domain after cleaning. Source B is used for testing only.

## Table A3. The 19 F1 features

Source: file "Bức tranh toàn cảnh", Section 6.1. Features are computed from the normalized URL string (scheme and `www.` removed) and never from the page content.

| # | Feature | Group | Meaning |
|--:|---------|-------|---------|
| 1 | `len_url` | Length | Number of characters in the whole URL |
| 2 | `len_host` | Length | Number of characters in the host |
| 3 | `len_path` | Length | Number of characters in the path |
| 4 | `len_query` | Length | Number of characters in the query (the part after `?`) |
| 5 | `n_dots` | Character count | Number of dots in the URL |
| 6 | `n_dots_host` | Character count | Number of dots in the host |
| 7 | `n_hyphen` | Character count | Number of hyphens in the URL |
| 8 | `n_hyphen_host` | Character count | Number of hyphens in the host |
| 9 | `n_digits` | Character count | Number of digits in the URL |
| 10 | `n_digits_host` | Character count | Number of digits in the host |
| 11 | `n_special` | Character count | Number of special characters (exact set: `[TBD: see common.py]`) |
| 12 | `n_slash` | Character count | Number of `/` in the path |
| 13 | `n_params` | Character count | Number of query parameters |
| 14 | `has_ip` | Indicator | 1 if the host is an IP address |
| 15 | `has_at` | Indicator | 1 if the URL contains `@` |
| 16 | `has_punycode` | Indicator | 1 if the URL contains `xn--` |
| 17 | `n_susp_kw` | Indicator | Number of suspicious keywords found (16 words, for example `login`, `verify`, `bank`; full list: `[TBD: see common.py]`) |
| 18 | `entropy_url` | Entropy | Shannon entropy of the URL characters; higher means closer to random |
| 19 | `entropy_host` | Entropy | Shannon entropy of the host characters |

Notes
- A home page (no path) has `len_path = 0`, `n_slash = 0` and `n_params = 0`. If these features rank high in the SHAP result of E1, it is direct evidence that the model learns URL shape rather than malicious signals (finding 1).
- Terminology: **F1 features** is this feature set; **F1-score** is the metric.
- Feature definitions above follow the team documents. Exact formulas are in `src/common.py` (`make_F1`); `[TBD: TV1 or TV4 to compare each row with the code]`.

## Note on the attack sample files (for Appendix A)

Files: `results/samples_T1.txt` … `samples_T7.txt` (all URLs defanged), the same path as on the team Drive and in the report. The report shows selected examples in Appendix A (Table A1).

Table 3 of the Threat Model section reports each transformation's result on a set of 50 malicious URLs (for T3: 4 of 50). The sample files were drawn from the malicious URLs of A-train (notebook `02_threat_model_T1_T7.ipynb`, cell 5), not from the OpenPhish snapshot, so that each file can show up to 20 examples; `samples_T3.txt`, for instance, has 20. The files show what each edit looks like. They do not show how often an edit works or evades a detector; those numbers are in Table 3 and in E3.

**Label noise in the first example.** In several files the first sample is hxxp://parasoft[.]com/jsp/products[.]jsp?itemId=13. This is a benign product page that source A labels as malicious (label noise in source A; see report Section 7.2 and 10.1). Do not use it as an example in the report; if it must appear, mark it "label noise in source A".

Two things a reader may notice in `samples_T3.txt`, worth one sentence each if space allows:
- One T3 edit replaces every occurrence of the same keyword in a URL (for example `account` → `user` twice in one URL), but it counts as one step toward the budget k.
- Some URLs labeled malicious in source A look like ordinary CDN image links. This is likely label noise inherited from the dataset, not an effect of the attack.
