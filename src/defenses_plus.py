
from urllib.parse import urlsplit, urlunsplit
from defenses import d1_normalize

def d1p_normalize(url):
    # D1+ = D1 + bỏ dấu '/' khi path chỉ là '/' và không có query (trang chủ luôn về một dạng)
    u = d1_normalize(url)
    try:
        p = urlsplit(u if '://' in u else 'http://' + u)
    except ValueError:
        return u
    if p.path == '/' and not p.query:
        return urlunsplit((p.scheme, p.netloc, '', '', ''))
    return u
