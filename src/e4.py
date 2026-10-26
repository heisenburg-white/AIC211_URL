
import json, os, joblib
from common import make_F1, evaluate
from d2 import make_F1D2
from defenses import d1_normalize
from e3 import make_score_fn

FEAT = {'F1': make_F1, 'F1D2': make_F1D2}
#           tên cấu hình   file model        file ngưỡng           key ngưỡng       feature  có D1?
CONFIGS = [('none',      'RF_F1',          'thresholds.json',    'RF_F1',          'F1',   False),
           ('D1',        'RF_F1_D1',       'thresholds_D1.json', 'RF_F1_D1',       'F1',   True),
           ('D2',        'RF_F1D2',        'thresholds_D2.json', 'RF_F1D2',        'F1D2', False),
           ('D1+D2',     'RF_F1D2_D1',     'thresholds_D2.json', 'RF_F1D2_D1',     'F1D2', True),
           ('D1+D2+D3',  'RF_F1D2_D1_D3',  'thresholds_D3.json', 'RF_F1D2_D1_D3',  'F1D2', True)]

def load_configs(root):
    out = {}
    for name, mfile, tfile, tkey, fs, use_d1 in CONFIGS:
        mp, tp = f'{root}/models/{mfile}.joblib', f'{root}/models/{tfile}'
        if not (os.path.exists(mp) and os.path.exists(tp)):
            print('  (chưa có cấu hình', name, '- bỏ qua)'); continue
        m = joblib.load(mp); pre = d1_normalize if use_d1 else None
        out[name] = {'thr': json.load(open(tp))[tkey], 'score': make_score_fn(m, FEAT[fs], pre)}
    return out

def clean_eval(cfg, df):
    # Chấm điểm qua đúng đường ống của cấu hình (D1 nếu có) trên URL sạch
    s = cfg['score'](['http://' + u for u in df['url_norm']])
    return evaluate(df['label'], s, cfg['thr'])
