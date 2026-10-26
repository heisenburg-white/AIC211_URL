
import re, random
from urllib.parse import urlsplit, urlunsplit
import tldextract
EXTRACT = tldextract.TLDExtract(suffix_list_urls=())

FREE_OPS, PAID_OPS = ['T1', 'T2', 'T3', 'T4'], ['T5', 'T6', 'T7']
PARAMS = [('utm_source', 'mail'), ('utm_medium', 'email'), ('ref', 'home'), ('lang', 'en'), ('page', '1')]
NEUTRAL_SUBS = ['account', 'support', 'app', 'portal', 'my', 'service', 'home', 'm']
NEUTRAL_WORDS = {'login': 'member', 'signin': 'portal', 'verify': 'profile', 'secure': 'home',
                 'account': 'user', 'update': 'news', 'confirm': 'continue', 'password': 'settings',
                 'webscr': 'page', 'billing': 'orders', 'wallet': 'items', 'bank': 'center'}
HOMOGLYPH = {'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с', 'x': 'х', 'y': 'у', 'i': 'і'}  # chữ Cyrillic
TYPO = {'l': '1', 'o': '0', 'i': 'l', 'e': '3', 's': '5', 'a': '4', 'm': 'rn'}

def reg_domain_of_host(host):
    ext = EXTRACT(host)
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain

def to_attack_form(url_norm):
    return 'http://' + url_norm          # URL kẻ tấn công gửi đi luôn có scheme

def _host_parts(url):
    p = urlsplit(url)
    return p, EXTRACT(p.hostname or '')

def _rebuild(p, sub, dom, suf):
    host = '.'.join(x for x in [sub, dom, suf] if x)
    return urlunsplit((p.scheme, host, p.path, p.query, ''))

def t1_add_param(url, rng):          # T1: thêm tham số trông bình thường (miễn phí)
    p = urlsplit(url); k, v = rng.choice(PARAMS)
    q = (p.query + '&' if p.query else '') + f'{k}={v}'
    return urlunsplit((p.scheme, p.netloc, p.path or '/', q, ''))

def t2_add_subdomain(url, rng):      # T2: thêm subdomain (miễn phí, wildcard DNS)
    p, ext = _host_parts(url)
    if not ext.suffix: return None
    sub = rng.choice(NEUTRAL_SUBS) + ('.' + ext.subdomain if ext.subdomain else '')
    return _rebuild(p, sub, ext.domain, ext.suffix)

def t3_neutral_word(url, rng):       # T3: thay từ khóa đáng ngờ bằng từ trung tính (miễn phí)
    p = urlsplit(url); low = (p.path + '?' + p.query).lower()
    hits = [w for w in NEUTRAL_WORDS if w in low]
    if not hits: return None
    w = rng.choice(hits)
    path = re.sub(w, NEUTRAL_WORDS[w], p.path, flags=re.I)
    query = re.sub(w, NEUTRAL_WORDS[w], p.query, flags=re.I)
    return urlunsplit((p.scheme, p.netloc, path, query, ''))

def t4_https(url, rng):              # T4: http -> https (gần như miễn phí)
    return 'https://' + url[len('http://'):] if url.startswith('http://') else None

def t5_hyphen(url, rng):             # T5: chèn gạch nối vào domain (phải mua domain mới)
    p, ext = _host_parts(url); d = ext.domain
    if not ext.suffix or len(d) < 4 or d.startswith('xn--'): return None
    i = rng.randint(2, len(d) - 2)
    if '-' in (d[i - 1], d[i]): return None
    return _rebuild(p, ext.subdomain, d[:i] + '-' + d[i:], ext.suffix)

def t6_typo(url, rng):               # T6: typosquatting (phải mua domain mới)
    p, ext = _host_parts(url); d = ext.domain
    idx = [i for i, ch in enumerate(d) if ch in TYPO]
    if not ext.suffix or not idx or d.startswith('xn--'): return None
    i = rng.choice(idx)
    return _rebuild(p, ext.subdomain, d[:i] + TYPO[d[i]] + d[i + 1:], ext.suffix)

def t7_homoglyph(url, rng):          # T7: ký tự Cyrillic giống chữ Latin, lưu dạng punycode (phải mua domain)
    p, ext = _host_parts(url); d = ext.domain
    idx = [i for i, ch in enumerate(d) if ch in HOMOGLYPH]
    if not ext.suffix or not idx or d.startswith('xn--'): return None
    i = rng.choice(idx)
    uni = d[:i] + HOMOGLYPH[d[i]] + d[i + 1:]
    try:
        puny = uni.encode('idna').decode('ascii')
    except UnicodeError:
        return None
    return _rebuild(p, ext.subdomain, puny, ext.suffix)

TRANSFORMS = {'T1': t1_add_param, 'T2': t2_add_subdomain, 'T3': t3_neutral_word, 'T4': t4_https,
              'T5': t5_hyphen, 'T6': t6_typo, 'T7': t7_homoglyph}

def reg_domain_of_url(url):
    return reg_domain_of_host(urlsplit(url).hostname or '')

def is_valid(old, new, op, benign_domains):
    if new is None or len(new) > 2048: return False
    try:
        p = urlsplit(new)
    except ValueError:
        return False
    if not p.hostname: return False
    rd_old, rd_new = reg_domain_of_url(old), reg_domain_of_url(new)
    if op in FREE_OPS and rd_old != rd_new: return False          # T1–T4 giữ nguyên registered domain
    if op in PAID_OPS and rd_new in benign_domains: return False  # không "mượn" domain thật
    return True

def apply_op(op, url, rng):
    try:
        return TRANSFORMS[op](url, rng)
    except (ValueError, UnicodeError):
        return None

def defang(url):
    # Viết URL độc ở dạng vô hiệu hóa khi đưa vào báo cáo: hxxp, [.]
    return url.replace('http', 'hxxp', 1).replace('.', '[.]')
