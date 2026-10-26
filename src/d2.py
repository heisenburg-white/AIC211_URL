
import numpy as np, pandas as pd
from rapidfuzz.distance import Levenshtein
from common import split_parts, entropy, EXTRACT, make_F1

BRANDS = ['paypal', 'apple', 'microsoft', 'google', 'amazon', 'facebook', 'netflix', 'instagram',
          'whatsapp', 'chase', 'wellsfargo', 'bankofamerica', 'dhl', 'fedex', 'office365', 'outlook']

def d2_features(url_norm):
    host, rest = split_parts(url_norm)
    ext = EXTRACT(host); path, _, query = rest.partition('?')
    dom, sub = ext.domain, ext.subdomain
    dists = [Levenshtein.distance(dom, b) for b in BRANDS]
    j = int(np.argmin(dists))
    f = {'brand_min_dist': dists[j],
         'brand_typo': int(0 < dists[j] <= 2),          # gần giống thương hiệu nhưng KHÔNG phải thương hiệu
         'brand_in_sub': int(any(b in sub for b in BRANDS)),
         'brand_in_path': int(any(b in rest.lower() for b in BRANDS)),
         'n_sub_labels': len(sub.split('.')) if sub else 0}
    for name, part in [('sub', sub), ('dom', dom), ('path', path), ('query', query)]:
        f[f'len_{name}'] = len(part)
        f[f'digits_{name}'] = sum(c.isdigit() for c in part)
        f[f'hyph_{name}'] = part.count('-')
        f[f'ent_{name}'] = entropy(part)
    return {f'd2_{k}': v for k, v in f.items()}   # tiền tố d2_ để không trùng tên cột với F1

def make_F1D2(df):
    d2 = pd.DataFrame([d2_features(u) for u in df['url_norm']], index=df.index)
    return pd.concat([make_F1(df), d2], axis=1)
