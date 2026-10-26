
import re, unicodedata
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from attacks import HOMOGLYPH

CONFUSABLE = {v: k for k, v in HOMOGLYPH.items()}   # bản rút gọn; báo cáo ghi rõ là bảng nhỏ
TRACKING = re.compile(r'^(utm_\w+|ref|fbclid|gclid|mc_cid|mc_eid)$')

def d1_normalize(url):
    # Giải punycode -> Unicode -> đổi ký tự giả (Cyrillic) về Latin; bỏ tham số tracking
    try:
        p = urlsplit(url if '://' in url else 'http://' + url)
        host = p.hostname or ''
    except ValueError:
        return url                     # URL hỏng: giữ nguyên
    labels = []
    for lab in host.split('.'):
        if lab.startswith('xn--'):
            try: lab = lab.encode('ascii').decode('idna')
            except UnicodeError: pass
        lab = unicodedata.normalize('NFKC', lab)
        labels.append(''.join(CONFUSABLE.get(ch, ch) for ch in lab))
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not TRACKING.match(k.lower())]
    return urlunsplit((p.scheme, '.'.join(labels), p.path, urlencode(q), ''))
