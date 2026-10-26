
import random
import numpy as np, pandas as pd
from common import normalize_url, split_parts, get_scores, make_F1
from attacks import apply_op, is_valid

FEATURIZE = {'F1': make_F1, 'F2': lambda d: d[['host', 'rest']]}

def make_score_fn(model, featurize, preprocess=None):
    # Hộp đen: nhận list URL -> mảng điểm độc. preprocess = phòng thủ D1 (None = không phòng thủ)
    def score_fn(urls):
        u = [preprocess(x) if preprocess else x for x in urls]
        d = pd.DataFrame({'url_norm': [normalize_url(x) for x in u]})
        parts = d['url_norm'].map(split_parts)
        d['host'] = parts.str[0]; d['rest'] = parts.str[1]
        return get_scores(model, featurize(d))
    return score_fn

def random_attack(url, k, ops, rng, benign_domains):
    # Kẻ tấn công không biết gì: chọn bừa k biến đổi hợp lệ
    cur, applied, tries = url, [], 0
    while len(applied) < k and tries < 20 * max(k, 1):
        tries += 1
        op = rng.choice(ops)
        new = apply_op(op, cur, rng)
        if is_valid(cur, new, op, benign_domains):
            cur, applied = new, applied + [op]
    return cur, applied

def greedy_attack(url, score_fn, thr, k, ops, rng, benign_domains, n_cand=3):
    # Hộp đen có truy vấn: mỗi bước thử mọi loại biến đổi (n_cand cách mỗi loại), giữ cách làm điểm giảm nhiều nhất
    cur = url; s = score_fn([cur])[0]; queries = 1; applied = []
    for _ in range(k):
        if s <= thr: break                       # đã lọt -> dừng
        cands = []
        for op in ops:
            for _ in range(n_cand):
                new = apply_op(op, cur, rng)
                if is_valid(cur, new, op, benign_domains):
                    cands.append((op, new))
        if not cands: break
        sc = score_fn([c[1] for c in cands]); queries += len(cands)
        j = int(np.argmin(sc))
        if sc[j] >= s: break                     # không giảm được nữa
        cur, s = cands[j][1], sc[j]; applied.append(cands[j][0])
    return {'adv_url': cur, 'ops': applied, 'queries': queries}

def greedy_attack_batch(urls, score_fn, thr, k, ops, rng, benign_domains, n_cand=3):
    # Giống greedy_attack nhưng chấm điểm CẢ LÔ URL trong 1 lần gọi (nhanh hơn rất nhiều với Random Forest)
    n = len(urls); cur = list(urls); s = np.asarray(score_fn(cur), dtype=float)
    queries = [1] * n; applied = [[] for _ in range(n)]
    active = s > thr
    for _ in range(k):
        cands = []                                   # (chỉ số URL, op, URL mới)
        for i in np.where(active)[0]:
            for op in ops:
                for _ in range(n_cand):
                    new = apply_op(op, cur[i], rng)
                    if is_valid(cur[i], new, op, benign_domains):
                        cands.append((i, op, new))
        if not cands: break
        sc = np.asarray(score_fn([c[2] for c in cands]), dtype=float)
        best = {}
        for (i, op, new), v in zip(cands, sc):
            queries[i] += 1
            if i not in best or v < best[i][0]:
                best[i] = (v, op, new)
        for i in np.where(active)[0]:
            if i in best and best[i][0] < s[i]:
                s[i] = best[i][0]; cur[i] = best[i][2]; applied[i].append(best[i][1])
            else:
                active[i] = False                    # không giảm được nữa
        active &= s > thr                            # đã lọt -> dừng
    return [{'adv_url': cur[i], 'ops': applied[i], 'queries': queries[i]} for i in range(n)]

def attack_success_rate(mal_urls, score_fn, thr, k, ops, mode, benign_domains, seed=0):
    # ASR = trong số URL độc BAN ĐẦU bị bắt, bao nhiêu % lọt sau khi biến đổi
    rng = random.Random(seed)
    base = score_fn(mal_urls)
    detected = [u for u, s in zip(mal_urls, base) if s > thr]
    if mode == 'random':
        rows = []
        for u in detected:
            adv, applied = random_attack(u, k, ops, rng, benign_domains)
            rows.append({'adv_url': adv, 'ops': applied, 'queries': 0})
    else:
        rows = greedy_attack_batch(detected, score_fn, thr, k, ops, rng, benign_domains) if detected else []
    res = pd.DataFrame(rows)
    if len(res):
        res['evaded'] = score_fn(list(res['adv_url'])) <= thr
    asr = float(res['evaded'].mean()) if len(res) else 0.0
    n_evaded = int(res['evaded'].sum()) if len(res) else 0
    return {'asr': asr,
            'recall_clean': len(detected) / max(len(mal_urls), 1),
            'recall_attack': (len(detected) - n_evaded) / max(len(mal_urls), 1),
            'n_detected': len(detected),
            'mean_queries': float(res['queries'].mean()) if len(res) else 0.0}, res
