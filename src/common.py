
import re, math, os, csv, datetime
from collections import Counter
from urllib.parse import unquote
import numpy as np, pandas as pd
import tldextract
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import confusion_matrix, average_precision_score, f1_score

EXTRACT = tldextract.TLDExtract(suffix_list_urls=())   # danh sách đuôi domain đóng gói sẵn, không cần mạng

def reg_domain_of_host(host):
    ext = EXTRACT(host)
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain   # IP -> chính IP đó

def normalize_url(u):
    # Mọi nguồn về CÙNG một dạng: bỏ scheme, bỏ 'www.', host chữ thường, giải mã %xx 1 lần, bỏ #fragment
    u = unquote(str(u).strip())
    u = re.sub(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', '', u)
    u = u.split('#', 1)[0]
    host = re.match(r'[^/?]*', u).group(0)
    rest = u[len(host):]
    host = host.lower()
    if host.startswith('www.'):
        host = host[4:]
    return host + rest

def split_parts(url_norm):
    host = re.match(r'[^/?]*', url_norm).group(0)
    return host, url_norm[len(host):]

def prepare_source(df, url_col='url', label_col='label'):
    # df: cột url (chuỗi gốc) + label (0 = benign, 1 = malicious). Trả về df sạch + log số dòng sau mỗi bước.
    log = {'raw': len(df)}
    df = df[[url_col, label_col]].dropna().rename(columns={url_col: 'url', label_col: 'label'})
    df['url_norm'] = df['url'].map(normalize_url)
    df = df[df['url_norm'].str.len() > 3]
    log['after_dropna'] = len(df)
    n_lab = df.groupby('url_norm')['label'].transform('nunique')
    df = df[n_lab == 1]                                   # URL mang cả 2 nhãn -> bỏ
    log['after_drop_conflict'] = len(df)
    df = df.drop_duplicates('url_norm')
    log['after_exact_dedup'] = len(df)
    parts = df['url_norm'].map(split_parts)
    df['host'] = parts.str[0]
    df['rest'] = parts.str[1]
    df['reg_domain'] = df['host'].map(reg_domain_of_host)
    return df.reset_index(drop=True), log

def domain_split(df, seed=42):
    # 70/15/15 theo registered domain (20 fold: 3 test, 3 val, 14 train)
    sgkf = StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=seed)
    fold = np.empty(len(df), dtype=int)
    for i, (_, idx) in enumerate(sgkf.split(df, df['label'], df['reg_domain'])):
        fold[idx] = i
    df = df.copy()
    df['split'] = np.where(fold < 3, 'test', np.where(fold < 6, 'val', 'train'))
    assert df.groupby('reg_domain')['split'].nunique().max() == 1, 'RÒ RỈ: có domain nằm ở 2 tập'
    return df

def remove_cross_source_overlap(df_b, df_a_train):
    # Nguồn B: bỏ URL trùng nguyên văn và URL có domain đã nằm trong train của A
    log = {'B_before': len(df_b)}
    df_b = df_b[~df_b['url_norm'].isin(set(df_a_train['url_norm']))]
    log['B_after_exact'] = len(df_b)
    df_b = df_b[~df_b['reg_domain'].isin(set(df_a_train['reg_domain']))]
    log['B_after_domain'] = len(df_b)
    df_b = df_b.copy(); df_b['split'] = 'test'
    return df_b.reset_index(drop=True), log

SUSPICIOUS = ['login', 'signin', 'verify', 'account', 'update', 'secure', 'bank', 'confirm',
              'password', 'webscr', 'billing', 'suspend', 'unlock', 'wallet', 'free', 'bonus']
IP_RE = re.compile(r'^\d{1,3}(\.\d{1,3}){3}(:\d+)?$')

def entropy(s):
    if not s: return 0.0
    c = Counter(s); n = len(s)
    return -sum(v / n * math.log2(v / n) for v in c.values())

def f1_features(url_norm):
    host, rest = split_parts(url_norm)
    path, _, query = rest.partition('?')
    low = url_norm.lower()
    return {
        'len_url': len(url_norm), 'len_host': len(host), 'len_path': len(path), 'len_query': len(query),
        'n_dots': url_norm.count('.'), 'n_dots_host': host.count('.'),
        'n_hyphen': url_norm.count('-'), 'n_hyphen_host': host.count('-'),
        'n_digits': sum(ch.isdigit() for ch in url_norm),
        'n_digits_host': sum(ch.isdigit() for ch in host),
        'n_special': sum(not ch.isalnum() for ch in url_norm),
        'n_slash': path.count('/'), 'n_params': query.count('&') + (1 if query else 0),
        'has_ip': int(bool(IP_RE.match(host))), 'has_at': int('@' in url_norm),
        'has_punycode': int('xn--' in host),
        'n_susp_kw': sum(kw in low for kw in SUSPICIOUS),
        'entropy_url': entropy(url_norm), 'entropy_host': entropy(host),
    }

def make_F1(df):
    return pd.DataFrame([f1_features(u) for u in df['url_norm']], index=df.index)

def make_F2_vectorizer():
    from sklearn.compose import ColumnTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    tf = lambda: TfidfVectorizer(analyzer='char', ngram_range=(3, 5), min_df=3,
                                 max_features=200_000, sublinear_tf=True)
    return ColumnTransformer([('host', tf(), 'host'), ('path', tf(), 'rest')])

def get_scores(model, X):
    # Điểm độc hại liên tục (càng cao càng độc)
    if hasattr(model, 'predict_proba'):
        return model.predict_proba(X)[:, 1]
    return model.decision_function(X)

def threshold_at_fpr(y_val, s_val, target_fpr=0.01):
    # Chọn ngưỡng trên VALIDATION nguồn A sao cho FPR ≈ 1%. Chốt xong KHÔNG đổi nữa.
    return float(np.quantile(np.asarray(s_val)[np.asarray(y_val) == 0], 1 - target_fpr))

def evaluate(y, s, thr):
    y = np.asarray(y); pred = (np.asarray(s) > thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'precision': tp / max(tp + fp, 1), 'recall': tp / max(tp + fn, 1),
            'f1': f1_score(y, pred, zero_division=0), 'fpr': fp / max(fp + tn, 1),
            'pr_auc': average_precision_score(y, s), 'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)}

def log_result(root, exp, model, source, metrics, defense='none', seed=0, k=0, ops='-', mode='-'):
    # Mọi kết quả đều ghi qua hàm này vào results/results.csv
    path = f'{root}/results/results.csv'
    row = {'time': datetime.datetime.now().isoformat(timespec='seconds'), 'exp': exp, 'model': model,
           'defense': defense, 'source': source, 'seed': seed, 'k': k, 'ops': ops, 'mode': mode, **metrics}
    new = not os.path.exists(path)
    with open(path, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(row));
        if new: w.writeheader()
        w.writerow(row)

# --- v2 (tuan 5): log_result chiu duoc cac thi nghiem co cot khac nhau
def log_result(root, exp, model, source, metrics, defense='none', seed=0, k=0, ops='-', mode='-'):
    path = f'{root}/results/results.csv'
    row = {'time': datetime.datetime.now().isoformat(timespec='seconds'), 'exp': exp, 'model': model,
           'defense': defense, 'source': source, 'seed': seed, 'k': k, 'ops': ops, 'mode': mode, **metrics}
    new = pd.DataFrame([row])
    if os.path.exists(path):
        new = pd.concat([pd.read_csv(path), new], ignore_index=True)
    new.to_csv(path, index=False)
