# Appendix tables (T4-05)

Draft by TV4 (SE211085), 24 Oct 2026. Tables are in English for the report. `[TBD]` marks what still needs a confirmation.

## Table A1. Cleaning and de-duplication log

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
- Source A is split 70/15/15 by registered domain after cleaning. Source B is used for testing only.

## Table A2. The 19 F1 features

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
