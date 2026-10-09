#!/usr/bin/env python3
"""
build_brand.py — turn a clothing brand's website into a brandsdotapp concept app.

  python3 tools/build_brand.py https://raith-clo.com raith        # scrape + build
  python3 tools/build_brand.py --rebuild raith                    # re-render from brand.json (no network)

Writes  <repo>/<slug>/index.html, brand.json, assets/{app.js,app.css,brand.js,img/*,hero.mp4}
Shared app code lives in <repo>/_template/. Brand-specific content lives in <slug>/brand.json.
Hand edits go in <slug>/brand.overrides.json (deep-merged on top of scraped data, kept between runs).
Instagram feed posts (instagram.posts) are collected separately in a browser and live in brand.overrides.json, so a rebuild keeps them.
Nothing is invented: anything that can't be found is left empty and listed in brand.json -> report.missing.
"""
import argparse, collections, datetime, html, io, json, os, re, shutil, subprocess, sys, tempfile, time
import urllib.parse, urllib.request, urllib.error

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit('Needs beautifulsoup4:  pip install beautifulsoup4')
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, '_template')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
CHROME_CANDIDATES = ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser']

FOUND, MISSING = [], []
def found(msg): FOUND.append(msg); print('  ✓', msg)
def missing(msg): MISSING.append(msg); print('  ✗', msg)
def log(msg): print(msg, flush=True)

# ---------------------------------------------------------------- http
def fetch(url, binary=False, timeout=25, tries=2, headers=None):
    """Returns (status, headers_dict, body) — never raises."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=dict({'User-Agent': UA, 'Accept-Language': 'en-GB,en;q=0.9'}, **(headers or {})))
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                hdrs = {k.lower(): v for k, v in r.headers.items()}
                return r.status, hdrs, body if binary else body.decode(r.headers.get_content_charset() or 'utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, b'' if binary else ''
        except Exception as e:
            last = e; time.sleep(1 + i)
    return 0, {}, b'' if binary else ''

def fetch_json(url):
    st, _, body = fetch(url)
    if st != 200: return None
    try: return json.loads(body)
    except Exception: return None

def absu(base, u):
    if not u: return None
    u = html.unescape(u.strip())
    if u.startswith('//'): u = 'https:' + u
    u = urllib.parse.urljoin(base, u)
    # some CDNs (e.g. speedsize) wrap the real URL: https://cdn/.../https://site/cdn/shop/...
    m = re.search(r'.(https?://.+)$', u[8:])
    if m and '/cdn/shop/' in m.group(1): u = m.group(1)
    return u

# ---------------------------------------------------------------- text helpers
SMALL = {'and', 'or', 'of', 'the', 'a', 'in', 'on', 'for', 'to', 'by', 'with', 'at'}
ACRONYM_OK = {'UK', 'US', 'USA', 'EU', 'DPD', 'DHL', 'UPS', 'AW', 'SS', 'FW', 'XL', 'XXL', 'UAE', 'FAQ', 'FAQS', 'DIY'}
def nice_title(s):
    s = re.sub(r'\s+', ' ', (s or '').strip())
    if not s: return s
    if s != s.upper(): return s.replace(' - ', ' – ')
    s = re.sub(r'\bAND\b', '&', s)
    out = []
    for i, w in enumerate(s.split(' ')):
        core = re.sub(r'[^A-Za-z]', '', w)
        if core.upper() in ACRONYM_OK or re.match(r'^[A-Z]{2}\d{2}$', w) or (len(core) <= 3 and core.isalpha() and core.lower() not in SMALL and len(core) > 1 and not re.search('[AEIOUY]', core)):
            out.append(w)
        elif i and w.lower() in SMALL:
            out.append(w.lower())
        else:
            out.append('-'.join(re.sub(r'[a-z]', lambda m: m.group(0).upper(), p.lower(), count=1) for p in w.split('-')))
    return ' '.join(out).replace(' - ', ' – ').replace('Faqs', 'FAQs')

def sentence_case(s):
    s = re.sub(r'\s+', ' ', s.strip())
    if s and s == s.upper():
        s = s.lower()
        s = s[:1].upper() + s[1:]
        for a in ACRONYM_OK | {'UK', 'US', 'EU'}:
            s = re.sub(r'\b' + a.lower() + r'\b', a, s)
        s = re.sub(r'\btrustpilot\b', 'Trustpilot', s)
        s = re.sub(r'\bklarna\b', 'Klarna', s)
    return s

BLOCK_TAGS = ['p', 'div', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'summary', 'details', 'tr', 'td', 'th', 'section', 'article', 'header', 'footer', 'nav', 'blockquote', 'dt', 'dd', 'table', 'main', 'aside', 'figure', 'figcaption', 'button', 'label']
def visible_lines(soup_or_html):
    soup = BeautifulSoup(str(soup_or_html), 'html.parser')
    for t in soup(['script', 'style', 'noscript', 'svg', 'template', 'iframe', 'select']):
        t.decompose()
    for br in soup.find_all('br'): br.replace_with('\n')
    for t in soup.find_all(BLOCK_TAGS):
        t.insert_before('\n'); t.append('\n')
    txt = soup.get_text()
    return [re.sub(r'\s+', ' ', l).strip() for l in txt.split('\n') if l.strip()]

# ---------------------------------------------------------------- shopify catalogue
def is_shopify(base, home_html):
    j = fetch_json(base + '/products.json?limit=1')
    return bool(j and isinstance(j.get('products'), list))

def paged(url_fmt, key, max_pages=10):
    out = []
    for page in range(1, max_pages + 1):
        j = fetch_json(url_fmt.format(page=page))
        items = (j or {}).get(key) or []
        out += items
        if len(items) < 250: break
    return out

def html_text(s, limit=700):
    t = BeautifulSoup(s or '', 'html.parser').get_text(' ')
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) > limit:
        t = t[:limit].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    return t

def map_product(p):
    title = p.get('title', '').strip()
    name, colour = (title.rsplit(' - ', 1) + [''])[:2] if ' - ' in title else (title, '')
    opts = [o.get('name', '').lower() for o in p.get('options', [])]
    si = next((i for i, n in enumerate(opts) if 'size' in n or n in ('waist', 'fit')), None)
    ci = next((i for i, n in enumerate(opts) if 'colo' in n), None)
    sizes, seen = [], {}
    for v in p.get('variants', []):
        if si is None:
            lab = 'One size' if len(p.get('variants', [])) == 1 else (v.get('title') or 'One size')
        else:
            lab = v.get('option%d' % (si + 1)) or ''
        if lab == 'Default Title': lab = 'One size'
        if lab in seen:
            seen[lab][1] = seen[lab][1] or (1 if v.get('available') else 0)
        else:
            seen[lab] = [lab, 1 if v.get('available') else 0]; sizes.append(seen[lab])
    if not colour and ci is not None and p.get('variants'):
        colour = p['variants'][0].get('option%d' % (ci + 1)) or ''
    prices = [float(v.get('price') or 0) for v in p.get('variants', [])] or [0]
    cps = [float(v.get('compare_at_price') or 0) for v in p.get('variants', [])] or [0]
    price, cp = min(prices), max(cps)
    imgs = [i.get('src') for i in p.get('images', []) if i.get('src')][:6]
    return {'h': p['handle'], 't': title, 'n': name.strip(), 'c': colour.strip(), 'ty': (p.get('product_type') or '').strip(),
            'p': round(price, 2), 'cp': round(cp, 2) if cp > price else 0, 'im': imgs, 'sz': sizes,
            'd': html_text(p.get('body_html')), 'tg': p.get('tags', [])[:30], 'pub': (p.get('published_at') or '')[:10]}

MAX_COLS = 24   # menu collections taken into the app
EDIT_RE = re.compile(r'new|sale|outlet|best|season|edit|collection|\b\d{2}\b|pre.?fall|\baw\d|\bss\d|spring|summer|autumn|winter|gift|mix|luxe|archive|essential|trend|top.?pick|offer|exclusive|limited|drop|resort|holiday|black.?friday|clearance|last.?chance|bundle|sets?\b', re.I)
SEASON_RE = re.compile(r'^(AW|SS|FW|FALL|AUTUMN|WINTER|SPRING|SUMMER|RESORT|PRE[ -]?FALL|HOLIDAY)[ /-]*(\d{2,4})\b', re.I)

def nav_collections(soup, base):
    """Collections linked from the site header/navigation, in menu order, with menu text."""
    areas = soup.select('header, nav, [class*=header], [class*=menu], [id*=header], [class*=drawer]') or [soup]
    seen, out = set(), []
    for area in areas:
        for a in area.find_all('a', href=True):
            # announcement-bar links reuse collection URLs with promo text ("Free UK delivery") — not menu names
            if a.find_parent(class_=re.compile(r'announcement|utility-bar|topbar|ticker', re.I)): continue
            m = re.search(r'/collections/([a-z0-9][a-z0-9\-_]*)/?(?:\?|#|$)', a['href'])
            if not m: continue
            h = m.group(1)
            txt = re.sub(r'\s+', ' ', a.get_text(' ')).strip()
            if h in seen or h in ('all', 'vendors', 'types') or not txt: continue
            seen.add(h); out.append((h, txt))
    return out

def size_groups(products):
    LETTER = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', 'XXXL', '3XL', '4XL']
    cnt = collections.Counter()
    for p in products.values():
        for s in {re.split(r'\s+-\s+|/', x[0])[0].strip().upper() for x in p['sz']}:
            cnt[s] += 1
    groups = []
    letters = [s for s in LETTER if cnt.get(s, 0) >= 3]
    if letters: groups.append({'key': 'top', 'label': 'Clothing size', 'opts': letters})
    waists = sorted({s for s in cnt if s.isdigit() and 24 <= int(s) <= 46 and cnt[s] >= 2}, key=int)
    if waists: groups.append({'key': 'waist', 'label': 'Waist (trousers & jeans)', 'opts': waists, 'prefix': ''})
    return groups

# ---------------------------------------------------------------- pages (help / about / legal)
PAGE_KINDS = [  # (group, label, regex on href+text)
    ('help', 'Shipping', r'shipping|delivery'), ('help', 'Returns', r'returns?(?!.*polic)|exchange'),
    ('help', 'FAQs', r'faq|help'), ('help', 'Contact', r'contact'),
    ('about', 'About us', r'about|our.?story'), ('about', 'Sustainability', r'sustainab|responsib'),
    ('about', 'Stockists', r'stockist|store.?locat|find.?a.?store'),
    ('legal', 'Privacy policy', r'privacy'), ('legal', 'Terms of service', r'terms'),
    ('legal', 'Refund policy', r'refund'), ('legal', 'Cookie policy', r'cookie'),
]
SHOPIFY_POLICIES = {'Privacy policy': '/policies/privacy-policy', 'Terms of service': '/policies/terms-of-service',
                    'Refund policy': '/policies/refund-policy', 'Shipping': '/policies/shipping-policy'}

def find_page_links(soup, base):
    host = urllib.parse.urlparse(base).netloc.replace('www.', '')
    links = []
    for a in soup.find_all('a', href=True):
        u = absu(base, a['href'])
        if not u or urllib.parse.urlparse(u).netloc.replace('www.', '') != host: continue
        path = urllib.parse.urlparse(u).path
        if not re.match(r'^/(pages|policies|blogs/[^/]+/?$|help|faq|about|contact|shipping|returns|privacy|terms|stockists)', path): continue
        links.append((u.split('#')[0].split('?')[0], re.sub(r'\s+', ' ', a.get_text(' ')).strip()))
    chosen = {}
    for group, label, rx in PAGE_KINDS:
        for u, txt in links:
            key = (urllib.parse.urlparse(u).path + ' ' + txt).lower()
            if label == 'Returns' and 'refund' in key: continue
            if label == 'Shipping' and 'polic' in key and any(l == 'Shipping' for l in chosen): continue
            if re.search(rx, key) and u not in [v['url'] for v in chosen.values()]:
                chosen[label] = {'group': group, 't': label, 'url': u}
                break
    return chosen

def main_text_lines(page_html, boiler):
    soup = BeautifulSoup(page_html, 'html.parser')
    for t in soup.select('header, footer, nav, [id*=shopify-section][id*=header], [id*=shopify-section][id*=footer], [id*=announcement], .site-header, .site-footer, [class*=cart-drawer], [class*=popup], [class*=newsletter]'):
        t.decompose()
    root = soup.find('main') or soup.body or soup
    lines = visible_lines(root)
    out, seen = [], set()
    for l in lines:
        if l in boiler or l in seen or len(l) < 3: continue
        seen.add(l); out.append(l)
    return out

FORM_WORDS = {'name', 'e-mail', 'email', 'message', 'send message', 'submit', 'phone', 'phone number', 'send', 'subject', 'first name', 'last name', 'comment'}
def summarise(lines, limit=900):
    """A short plain-text summary of a page. ALL-CAPS headings are folded into the line that follows them."""
    clean = []   # (text, is_heading)
    for l in lines:
        l = l.strip().lstrip('-–—•* ').replace('**', '').replace('*', '').strip()
        if not l or l.lower() in FORM_WORDS or len(l) < 3: continue
        if re.search(r'cookie|subscribe|sign up for|newsletter|javascript|skip to content', l, re.I): continue
        head = l == l.upper() and len(l) <= 45 and re.search('[A-Z]', l) is not None
        txt = nice_title(l) if head else (sentence_case(l) if l == l.upper() else l)
        if not head: txt = re.sub(r"\b[A-Z][A-Z0-9&'’()]+(?:[ -]+[A-Z0-9&'’()£$.]+)*[ -]+[A-Z][A-Z0-9&'’()]+\b", lambda m: nice_title(m.group(0)) if sum(c.isalpha() for c in m.group(0)) > 5 else m.group(0), txt)
        if clean and not clean[-1][1] and not head and not re.search(r'[.!?:)]$', clean[-1][0]) and txt[:1].islower():
            clean[-1] = (clean[-1][0] + ' ' + txt, False); continue
        clean.append((txt, head))
    if len(clean) > 1 and clean[0][1]: clean = clean[1:]   # page title
    out, i, total = [], 0, 0
    while i < len(clean) and total < limit:
        t, head = clean[i]
        if head and i + 1 < len(clean) and not clean[i + 1][1]:
            t = t.rstrip(':') + ': ' + clean[i + 1][0]; i += 1
        out.append(t); total += len(t); i += 1
    s = '\n'.join(out)
    if len(s) > limit + 250: s = s[:limit].rsplit(' ', 1)[0] + '…'
    return s

def parse_shipping(lines):
    ship = {'options': [], 'notes': [], 'freeOver': None, 'region': ''}
    regions = [i for i, l in enumerate(lines) if re.match(r'^(delivery|shipping)\s+to\s*:?', l, re.I)]
    first = lines[regions[0]:regions[1]] if len(regions) > 1 else (lines[regions[0]:] if regions else lines)
    if regions:
        ship['region'] = nice_title(re.sub(r'^(delivery|shipping)\s+to\s*:?\s*', '', lines[regions[0]], flags=re.I)).replace('United Kingdom', 'UK')
        others = [nice_title(re.sub(r'^(delivery|shipping)\s+to\s*:?\s*', '', lines[i], flags=re.I)) for i in regions[1:]]
        if others: ship['notes'].append('We also deliver to ' + ', '.join(others[:-1]) + (' and ' if len(others) > 1 else '') + others[-1] + '.')
    for l in lines:
        if re.search(r'now shipping|ships? from our', l, re.I) and len(l) < 90:
            ship['notes'].insert(0, sentence_case(l).rstrip('.') + '.'); break
    rx = re.compile(r'^(?P<name>[A-Za-z][A-Za-z0-9 ()\'&./+-]{2,60}?)\s*[:\-–—]?\s*(?P<cur>[£$€])\s?(?P<price>\d+(?:\.\d{2})?)\s*(?:[-–—:]\s*(?P<rest>.*))?$')
    # "DPD NEXT BUSINESS DAY - FREE" → priced at 0 so it parses like the £ lines
    first = [re.sub(r'\s[-–—:]\s*free\s*$', ' - £0', l, flags=re.I) for l in first]
    for i, l in enumerate(first):
        m = rx.match(l)
        if not m or re.match(r'^(free|over|orders?)\b', m.group('name'), re.I): continue
        rest = (m.group('rest') or '').replace('*', '').strip()
        j = i + 1
        if not re.sub(r'free.*', '', rest, flags=re.I).strip(' -–—') and j < len(first) and not rx.match(first[j]) and len(first[j]) < 80:
            rest = (rest + ' - ' + first[j].replace('*', '').strip(' -–—')).strip(' -–—'); j += 1
        fo = re.search(r'free\s+(?:on\s+)?(?:orders?\s+)?over\s*[£$€]\s?(\d+(?:\.\d{2})?)', rest, re.I)
        desc = re.sub(r'free\s+(?:on\s+)?(?:orders?\s+)?over\s*[£$€]\s?\d+(?:\.\d{2})?\s*[-–—]?\s*', '', rest, flags=re.I).strip(' -–—')
        if re.fullmatch(r'(order|orders?|by|before)', desc, re.I): desc = ''   # a cut-off split over lines ("ORDER" / "BEFORE 8PM")
        nxt = first[j] if j < len(first) else ''
        name = nice_title(m.group('name').strip(' -–—:'))
        o = {'id': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'), 'name': name, 'desc': sentence_case(desc) if desc else '',
             'price': float(m.group('price'))}
        if re.match(r'^order by', nxt, re.I): o['cutoff'] = nxt
        if fo: o['freeOver'] = float(fo.group(1))
        words = name.split()
        o['short'] = ' '.join(words[-2:]) if len(words) >= 3 and not re.search(r'[()]', name) else name
        ship['options'].append(o)
    ship['options'].sort(key=lambda o: (0 if o.get('freeOver') else 1, o['price']))
    fos = [o['freeOver'] for o in ship['options'] if o.get('freeOver')]
    if fos: ship['freeOver'] = min(fos)
    else:
        for l in lines:
            m = re.search(r'free\s+(?:\w+\s+){0,2}(?:delivery|shipping)\s+(?:on\s+)?(?:orders?\s+)?over\s*[£$€]\s?(\d+)', l, re.I)
            if m: ship['freeOver'] = float(m.group(1)); break
    return ship

# ---------------------------------------------------------------- theme
def rgb_of(v):
    v = v.strip()
    m = re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})\b', v, re.I)
    if m:
        h = m.group(1)
        if len(h) == 3: h = ''.join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r'^(?:rgba?\()?\s*(\d{1,3})[ ,]+(\d{1,3})[ ,]+(\d{1,3})', v)
    if m: return tuple(min(255, int(x)) for x in m.groups())
    return None
hexc = lambda c: '#%02x%02x%02x' % c
lum = lambda c: (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255
mix = lambda a, b, t: tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))

def extract_theme(home_html):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', home_html, re.S))
    vars_ = collections.defaultdict(list)
    for name, val in re.findall(r'--([a-z0-9-]+)\s*:\s*([^;}{]+)', css, re.I):
        c = rgb_of(val)
        if c: vars_[name.lower()].append(c)
    def pick(names, cond):
        for n in names:
            for c in vars_.get(n, []):
                if cond(c): return c
        return None
    bgs = [c for n in ['background', 'color-background', 'colors-background', 'background-color', 'color-base-background-1', 'page-background'] for c in vars_.get(n, []) if lum(c) > 0.85]
    tinted = collections.Counter(c for c in bgs if c != (255, 255, 255))
    bg = tinted.most_common(1)[0][0] if tinted else (bgs[0] if bgs else None)
    text = pick(['text-color', 'color-foreground', 'colors-text', 'color-text', 'text', 'heading-color', 'color-base-text', 'color-heading'], lambda c: lum(c) < 0.35)
    accent = pick(['accent', 'color-accent', 'colors-accent-1', 'color-button', 'button-background', 'primary', 'color-primary'], lambda c: 0.12 < lum(c) < 0.85 and max(c) - min(c) > 8)
    sale = pick(['sale-color', 'color-sale', 'on-sale-accent', 'sale-badge-background', 'product-on-sale-accent', 'color-badge-sale'], lambda c: True)
    m = re.search(r'<meta name="theme-color" content="([^"]+)"', home_html)
    theme_meta = rgb_of(m.group(1)) if m else None
    fonts = {}
    for key, names in (('heading', ['heading-font-family', 'font-heading-family', 'heading-font', 'font-heading']), ('body', ['text-font-family', 'body-font-family', 'font-body-family', 'text-font', 'font-body', 'base-font-family'])):
        for n in names:
            mm = re.search(r'--' + n + r'\s*:\s*([^;]+);', css, re.I)
            if mm:
                fam = mm.group(1).split(',')[0].strip().strip('"\'')
                if fam and not fam.startswith('var('): fonts[key] = fam; break
    if not fonts:
        mm = re.search(r'font-family\s*:\s*["\']?([A-Za-z][A-Za-z0-9 ]+?)["\']?\s*[,;]', css)
        if mm and mm.group(1).lower() not in ('inherit', 'sans-serif', 'serif', 'system-ui', 'arial', 'helvetica'): fonts['body'] = mm.group(1)
    return {'bg': bg, 'text': text, 'accent': accent, 'sale': sale, 'meta': theme_meta, 'fonts': fonts}

def google_font(fam):
    if not fam: return None
    url = 'https://fonts.googleapis.com/css2?family=' + urllib.parse.quote_plus(fam) + ':wght@300;400;500;600;700&display=swap'
    st, _, _ = fetch(url, tries=1)
    if st == 200: return url
    url = 'https://fonts.googleapis.com/css2?family=' + urllib.parse.quote_plus(fam) + '&display=swap'
    st, _, _ = fetch(url, tries=1)
    return url if st == 200 else None

# muted text sits ~41% of the way from ink to the page colour (>= 4.5:1 on the page, WCAG AA); hairlines ~88% (light).
MUTED_T, LINE_T = .41, .88
def normalise_theme(th):
    """Re-derive muted/line from ink + bg so older brand.json files (line was 10% instead of 90% toward the page,
    muted was too light) render correctly on --rebuild."""
    th = dict(th); ink, bg = rgb_of(th['ink']), rgb_of(th['bg'])
    if ink and bg: th['muted'] = hexc(mix(ink, bg, MUTED_T)); th['line'] = hexc(mix(ink, bg, LINE_T))
    return th

def build_theme(t):
    ink = t['text'] or (17, 17, 17)
    if lum(ink) > 0.2: ink = mix(ink, (0, 0, 0), .5)
    bg = t['bg'] or (243, 243, 243)
    if bg == (255, 255, 255): bg = (245, 244, 242)
    acc = t['accent'] or (184, 166, 140)
    th = {'ink': hexc(ink), 'bg': hexc(bg), 'bgRgb': '%d,%d,%d' % bg, 'text': hexc(mix(ink, bg, .22)), 'muted': hexc(mix(ink, bg, MUTED_T)),
          'line': hexc(mix(ink, bg, LINE_T)), 'stone': hexc(acc), 'sand': hexc(mix(acc, (255, 255, 255), .45)), 'sand2': hexc(mix(acc, (255, 255, 255), .82)),
          'sale': hexc(t['sale']) if t['sale'] and lum(t['sale']) < .6 else '#9b3b2a',
          'stageA': hexc(mix(bg, (255, 255, 255), .5)), 'stageB': hexc(mix(bg, acc, .12)), 'stageC': hexc(mix(bg, acc, .25))}
    return th

# ---------------------------------------------------------------- images & media
def save_image(url, path, max_w=None, fmt=None):
    if not url: return False
    st, _, body = fetch(url, binary=True)
    if st != 200 or not body: return False
    if url.lower().split('?')[0].endswith('.svg') or body[:200].lstrip().startswith(b'<svg') or b'<svg' in body[:400]:
        if not Image: return False
        png = svg_to_png(body)
        if not png: return False
        body = png
    if not Image:
        open(path, 'wb').write(body); return True
    try:
        im = Image.open(io.BytesIO(body))
        im.load()
        if max_w and im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        if (fmt or path.rsplit('.', 1)[-1]).lower() in ('jpg', 'jpeg'):
            im = im.convert('RGB'); im.save(path, 'JPEG', quality=82, optimize=True, progressive=True)
        else:
            if im.mode not in ('RGBA', 'LA', 'P'): im = im.convert('RGBA')
            im.save(path, 'PNG', optimize=True)
        return True
    except Exception as e:
        print('    image error', url, e); return False

def svg_to_png(svg_bytes):
    """Rasterise an SVG logo with headless Chrome (no extra python deps)."""
    chrome = next((c for c in CHROME_CANDIDATES if os.path.exists(c)), None)
    if not chrome: return None
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, 'l.svg'); open(sp, 'wb').write(svg_bytes)
        hp = os.path.join(d, 'l.html')
        open(hp, 'w').write('<html><body style="margin:0;background:transparent"><img src="l.svg" style="height:360px;display:block"></body></html>')
        op = os.path.join(d, 'o.png')
        subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--default-background-color=00000000',
                        '--window-size=4000,360', '--screenshot=' + op, 'file://' + hp], capture_output=True, timeout=60)
        if not os.path.exists(op): return None
        im = Image.open(op).convert('RGBA'); bb = im.getbbox()
        if bb: im = im.crop(bb)
        b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()

def logo_tone(path):
    im = Image.open(path).convert('RGBA')
    px = [p for p in list(im.convert('RGBA').tobytes()[i:i+4] for i in range(0, im.width*im.height*4, 4)) if p[3] > 100]
    if not px: return 'dark', True
    L = sum(lum(p[:3]) for p in px) / len(px)
    sat = sum(max(p[:3]) - min(p[:3]) for p in px) / len(px)
    return ('light' if L > 0.6 else 'dark'), sat < 40

def recolour(src, dst, rgb):
    im = Image.open(src).convert('RGBA')
    a = im.split()[3]
    if a.getextrema() == (255, 255):   # no transparency: use luminance as alpha (dark marks on light bg)
        g = im.convert('L'); tone, _ = 'dark', 0
        a = g.point(lambda v: 255 - v) if sum(g.getdata()) / (g.width * g.height) > 127 else g
    solid = Image.new('RGBA', im.size, rgb + (255,)); solid.putalpha(a)
    bb = solid.getbbox()
    if bb: solid = solid.crop(bb)
    solid.save(dst, 'PNG', optimize=True)

def wordmark(text, dst, rgb):
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 64)
    except Exception: font = ImageFont.load_default()
    spaced = '  '.join(text.upper())
    w = int(ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(spaced, font=font)) + 20
    im = Image.new('RGBA', (w, 90), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 8), spaced, font=font, fill=rgb + (255,))
    im.crop(im.getbbox()).save(dst, 'PNG')

# Hero video: shared encoding settings for every brand (see tools/README.md "Hero video").
HERO = {
    'long': 1080,          # px on the long side (portrait: height)
    'aspect': 0.63,        # width / height of the app hero (390x620 on a phone). Cropped to this so no pixels are wasted
    'crf': 23, 'preset': 'slow', 'gop': 48,   # H.264 high profile, keyframe every 2s at 24fps
    'vp9_crf': 34,         # optional WebM / VP9 source
    'loop_min': 8.0, 'loop_max': 12.0, 'loop_target': 10.0, 'xfade': 0.6,
}

def original_video_urls(u, base):
    """Shopify keeps the uploaded original next to its transcodes: /videos/c/vp/<id>/<id>.HD-1080p-….mp4 → /videos/c/o/v/<id>.(mp4|mov)."""
    m = re.search(r'/videos/c/vp/([0-9a-f]{32})/', u or '')
    if not m: return []
    root = (base.rstrip('/') + '/cdn/shop') if '/cdn/shop/' in u else 'https://cdn.shopify.com'
    return [root + '/videos/c/o/v/%s.%s' % (m.group(1), ext) for ext in ('mp4', 'mov')]

def ffprobe_video(path):
    """(width, height, duration, fps) of the first video stream, rotation applied, or None."""
    try:
        j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,duration:stream_side_data=rotation:stream_tags=rotate',
                                       '-show_entries', 'format=duration', '-of', 'json', path], capture_output=True, text=True, timeout=30).stdout)
        s = j['streams'][0]; w, h = int(s['width']), int(s['height'])
        rot = abs(int(float((s.get('tags') or {}).get('rotate') or next((d.get('rotation') for d in s.get('side_data_list', []) if 'rotation' in d), 0) or 0)))
        if rot in (90, 270): w, h = h, w
        n, d = (s.get('r_frame_rate') or '24/1').split('/'); fps = float(n) / float(d or 1)
        dur = float(s.get('duration') or j.get('format', {}).get('duration') or 0)
        return w, h, dur, fps
    except Exception: return None

def scene_cuts(path, limit=20):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-t', str(limit), '-i', path, '-an', '-vf', "scale=320:-2,select='gt(scene,0.3)',showinfo", '-f', 'null', '-'],
                       capture_output=True, text=True, timeout=300)
    return [float(x) for x in re.findall(r'pts_time:([0-9.]+)', r.stderr)]

def encode_hero(src, out_mp4, out_poster, out_webm=None, S=HERO):
    """Re-encode a campaign video for smooth web playback. Returns a dict describing the result, or None."""
    info = ffprobe_video(src)
    if not info: return None
    w, h, dur, fps = info
    # crop to the hero's aspect, then scale so the long side is S['long'] (never upscale)
    a = S['aspect']
    cw, ch = (w, w / a) if w / h < a else (h * a, h)
    oh = min(S['long'], int(ch)) // 2 * 2; ow = int(round(oh * a / 2)) * 2
    vf = 'crop=%d:%d,scale=%d:%d:flags=lanczos,setsar=1,fps=%g,format=yuv420p' % (int(cw) // 2 * 2, int(ch) // 2 * 2, ow, oh, round(fps, 3))
    # loop: end exactly on a hard cut between loop_min and loop_max so the jump back to frame 0 reads as just another cut;
    # otherwise cross-fade the tail into the head so the loop is seamless
    cuts = [c for c in scene_cuts(src, S['loop_max'] + 1) if S['loop_min'] <= c <= S['loop_max']]
    xf = S['xfade']
    if cuts:
        L = min(cuts, key=lambda c: abs(c - S['loop_target']))
        L = round(L * fps) / fps   # cut lands on a frame boundary: keep frames [0, L)
        filt = ['-t', '%.4f' % L, '-vf', vf]; how = 'ends on a scene cut at %.2fs' % L
    else:
        L = min(S['loop_target'], max(1.0, dur - xf - 0.1))
        filt = ['-filter_complex', '[0:v]%s,split[a][b];[a]trim=start=%g:end=%g,setpts=PTS-STARTPTS[A];[b]trim=0:%g,setpts=PTS-STARTPTS[B];[A][B]xfade=transition=fade:duration=%g:offset=%g[v]'
                % (vf, xf, L + xf, xf, xf, L - xf), '-map', '[v]']
        how = 'cross-faded loop'
    x264 = ['-c:v', 'libx264', '-preset', S['preset'], '-crf', str(S['crf']), '-profile:v', 'high', '-level:v', '4.0', '-pix_fmt', 'yuv420p',
            '-g', str(S['gop']), '-keyint_min', str(S['gop'] // 2), '-sc_threshold', '0', '-movflags', '+faststart', '-an']
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', src] + filt + x264 + [out_mp4], capture_output=True, text=True, timeout=900)
    if r.returncode != 0: print('    ffmpeg:', r.stderr[-400:]); return None
    # poster: first frame of the loop at the same crop, high-quality JPEG, so poster → video is seamless
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vf', vf, '-frames:v', '1', '-q:v', '2', out_poster], capture_output=True, timeout=120)
    if out_webm:
        rw = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', out_mp4, '-c:v', 'libvpx-vp9', '-crf', str(S['vp9_crf']), '-b:v', '0', '-row-mt', '1', '-deadline', 'good',
                             '-cpu-used', '2', '-g', str(S['gop']), '-an', out_webm], capture_output=True, timeout=1800)
        if rw.returncode != 0 and os.path.exists(out_webm): os.remove(out_webm)
    size = os.path.getsize(out_mp4)
    return {'w': ow, 'h': oh, 'dur': round(L, 2), 'kbps': round(size * 8 / L / 1000), 'bytes': size, 'how': how, 'src': '%dx%d' % (w, h),
            'webm': bool(out_webm and os.path.exists(out_webm))}

def make_hero_video(urls, out_mp4, out_poster, base=''):
    """Download the homepage campaign video at the best quality available (Shopify original upload if public) and encode it."""
    if not shutil.which('ffmpeg') or not urls: return None
    cands = []
    for u in urls[:4]:
        cands += original_video_urls(u, base) + [u]
    best = None
    with tempfile.TemporaryDirectory() as d:
        for i, u in enumerate(dict.fromkeys(cands)):
            st, _, body = fetch(u, binary=True, timeout=240)
            if st != 200 or len(body) < 10000: continue
            p = os.path.join(d, 'v%d%s' % (i, os.path.splitext(urllib.parse.urlparse(u).path)[1] or '.mp4')); open(p, 'wb').write(body)
            info = ffprobe_video(p)
            if not info: continue
            w, h = info[:2]
            # prefer portrait / 4:5 sources (the hero is portrait), then the most pixels
            score = (1 if h >= w else 0, -round(abs(w / h - 0.8), 1), w * h)
            print('    candidate %dx%d %s' % (w, h, u[:110]))
            if not best or score > best[0]: best = (score, p, u)
        if not best: return None
        webm = os.path.splitext(out_mp4)[0] + '.webm'
        res = encode_hero(best[1], out_mp4, out_poster, webm)
        if res: res['url'] = best[2]
        return res

# ---------------------------------------------------------------- headless render (optional)
def render_home(url):
    """Load the homepage in headless Chrome so JS widgets (announcement bars, Trustpilot) exist. Optional."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('    (playwright not installed, skipping render step)'); return None
    chrome = next((c for c in CHROME_CANDIDATES if os.path.exists(c)), None)
    res = {'frames': [], 'announce': [], 'frame_text': ''}
    try:
        with sync_playwright() as pw:
            kw = {'args': ['--no-sandbox']}
            if chrome: kw['executable_path'] = chrome
            b = pw.chromium.launch(**kw)
            p = b.new_page(user_agent=UA, viewport={'width': 1280, 'height': 900})
            try: p.goto(url, wait_until='networkidle', timeout=60000)
            except Exception: pass
            p.wait_for_timeout(5000)
            for f in p.frames:
                res['frames'].append(f.url)
                if 'trustpilot' in f.url or 'reviews' in f.url:
                    try: res['frame_text'] += '\n' + f.inner_text('body')
                    except Exception: pass
            res['announce'] = p.evaluate("""() => {
              const out = [];
              const sel = '[class*=announcement],[class*=marquee],[class*=ticker],[class*=promo-bar],[class*=topbar],[id*=announcement],[class*=usp],[class*=trust-bar],[class*=cart] .message,.splide__slide.message';
              document.querySelectorAll(sel).forEach(e => {
                const leaves = e.children.length ? [...e.querySelectorAll('*')].filter(x => !x.children.length) : [e];
                leaves.forEach(x => { const t = (x.textContent || '').replace(/\\s+/g, ' ').trim(); if (t.length > 6 && t.length < 90) out.push(t); });
              });
              return out;
            }""")
            res['html'] = p.content()
            b.close()
    except Exception as e:
        print('    render failed:', e); return None
    return res

def trustpilot(rendered, static_html, domain):
    ids = set(re.findall(r'businessunit[-_]?id["\'=:\s]+["\']?([a-f0-9]{24})', static_html or '', re.I))
    for u in (rendered or {}).get('frames', []):
        m = re.search(r'businessunitId=([a-f0-9]{24})', u)
        if m: ids.add(m.group(1))
    for bid in ids:
        j = fetch_json('https://widget.trustpilot.com/trustbox-data/5419b6a8b0d04a076446a9ad?businessUnitId=%s&locale=en-GB' % bid)
        bu = (j or {}).get('businessUnit') or {}
        score, total = bu.get('trustScore'), (bu.get('numberOfReviews') or {}).get('total')
        if score and total:
            label = None
            m = re.search(r'\b(Excellent|Great|Good|Average|Poor|Bad)\b', (rendered or {}).get('frame_text', ''))
            if m: label = m.group(1)
            else: label = 'Excellent' if score >= 4.3 else 'Great' if score >= 3.8 else 'Average' if score >= 2.8 else 'Poor' if score >= 1.8 else 'Bad'
            ident = bu.get('identifyingName') or domain
            return {'source': 'Trustpilot', 'score': score, 'count': int(total), 'label': label,
                    'url': 'https://uk.trustpilot.com/review/' + ident, 'checked': datetime.date.today().isoformat()}
    return None

def hero_video(vids, out_dir, base):
    """Fetch + encode the hero video into <out>/assets/hero.mp4 (+ hero.webm, img/hero-poster.jpg). Returns the hero dict fields."""
    img_dir = os.path.join(out_dir, 'assets', 'img'); os.makedirs(img_dir, exist_ok=True)
    res = make_hero_video(vids, os.path.join(out_dir, 'assets', 'hero.mp4'), os.path.join(img_dir, 'hero-poster.jpg'), base) if vids else None
    if not res: return {}
    hero = {'video': 'assets/hero.mp4', 'poster': 'assets/img/hero-poster.jpg', 'videoW': res['w'], 'videoH': res['h']}
    if res['webm']: hero['videoWebm'] = 'assets/hero.webm'
    found('Hero video from homepage: source %s → %dx%d H.264 CRF %d, %.1fs loop (%s), %d kbps, %.2f MB%s' % (
        res['src'], res['w'], res['h'], HERO['crf'], res['dur'], res['how'], res['kbps'], res['bytes'] / 1e6, ' + WebM/VP9' if res['webm'] else ''))
    return hero

def homepage_videos(soup, base):
    vids = []
    for v in soup.find_all('video'):
        for s in [v] + v.find_all('source'):
            u = s.get('src') or s.get('data-src')
            if u and re.search(r'\.(mp4|webm|mov)', u): vids.append(absu(base, u))
    return list(dict.fromkeys(vids))

# ---------------------------------------------------------------- scrape
GENERIC_WORDS = r'\b(clothing|clothes|clo|apparel|official|store|shop|online|ltd|limited|uk|co|company|menswear|womenswear|london)\b'

def scrape(url, slug, out_dir, do_render=True, max_products=400, extra_cols=()):
    base = url.rstrip('/')
    if not re.match(r'^https?://', base): base = 'https://' + base
    st, hdrs, home = fetch(base + '/')
    if st != 200 or not home:
        sys.exit('Could not load %s (HTTP %s)' % (base, st))
    base = base.replace('http://', 'https://')
    domain = urllib.parse.urlparse(base).netloc.replace('www.', '')
    soup = BeautifulSoup(home, 'html.parser')
    img_dir = os.path.join(out_dir, 'assets', 'img'); os.makedirs(img_dir, exist_ok=True)
    B = {'slug': slug, 'site': base, 'domain': domain, 'generator': 'brandsdotapp/tools/build_brand.py',
         'generatedAt': datetime.datetime.now().isoformat(timespec='seconds'), 'discount': {'code': 'APP10', 'pct': 10}}

    log('· Brand basics')
    og = soup.find('meta', property='og:site_name')
    site_name = (og.get('content') if og else '') or (soup.title.string if soup.title else '') or domain
    site_name = re.split(r'\s[|\-–—]\s', site_name.strip())[0].strip()
    short = re.sub(GENERIC_WORDS, '', site_name, flags=re.I).strip(' -&|') or site_name
    B['legalName'], B['name'], B['short'] = site_name, nice_title(short) if short.isupper() else short, nice_title(short) if short.isupper() else short
    found('Name: %s (site calls itself “%s”)' % (B['name'], site_name))
    md = soup.find('meta', attrs={'name': 'description'})
    meta_desc = md.get('content', '').strip() if md else ''

    log('· Catalogue')
    shopify = is_shopify(base, home)
    B['platform'] = 'shopify' if shopify else 'unknown'
    products, cols = {}, []
    all_cols = []
    if shopify:
        found('Shopify store detected (/products.json is public)')
        raw = paged(base + '/products.json?limit=250&page={page}', 'products', 8)
        all_cols = paged(base + '/collections.json?limit=250&page={page}', 'collections', 4)
        found('%d products in /products.json, %d collections in /collections.json' % (len(raw), len(all_cols)))
        by_handle = {p['handle']: p for p in raw}
        nav = nav_collections(soup, base)
        colmeta = {c['handle']: c for c in all_cols}
        total = len(raw) or 1
        for h, txt in nav:
            cm = colmeta.get(h, {})
            if cm.get('products_count', 1) == 0: continue
            if cm.get('products_count', 0) > 0.8 * total and len(nav) > 4: continue   # skip "all products" style links
            items = paged(base + '/collections/' + h + '/products.json?limit=250&page={page}', 'products', 2)
            if not items: continue
            for p in items: by_handle.setdefault(p['handle'], p)
            title = nice_title(txt)
            ct = nice_title(cm.get('title', ''))
            if ct and ct.lower().startswith(title.lower()) and len(ct) > len(title): title = ct
            # sub-menu labels like "View all" / a second "Tees" under a sub-brand: use the collection's own title
            if ct and (re.fullmatch(r'(view|shop)? ?all', title, re.I) or title.lower() in {c['t'].lower() for c in cols}): title = ct
            cols.append({'h': h, 't': title, 'p': [p['handle'] for p in items]})
            if len(cols) >= MAX_COLS: break
        # collections that aren't in the menu but the app wants (brand.overrides.json -> scrape.extraCollections)
        for h in extra_cols:
            if h in [c['h'] for c in cols]: continue
            items = paged(base + '/collections/' + h + '/products.json?limit=250&page={page}', 'products', 2)
            if not items: missing('Extra collection %s: no public products' % h); continue
            for p in items: by_handle.setdefault(p['handle'], p)
            cols.append({'h': h, 't': nice_title(colmeta.get(h, {}).get('title', h.replace('-', ' '))), 'p': [p['handle'] for p in items]})
            found('Extra collection (from overrides): %s, %d products' % (h, len(items)))
        used = []
        for c in cols:
            for h in c['p']:
                if h not in used: used.append(h)
        for h in used[:max_products]:
            if h in by_handle: products[h] = map_product(by_handle[h])
        for c in cols: c['p'] = [h for h in c['p'] if h in products]
        cols = [c for c in cols if c['p']]
        found('%d menu collections → %d products in the app' % (len(cols), len(products)))
        if not cols: missing('No collections linked from the site menu')
    else:
        missing('Not a Shopify store (or /products.json is blocked): no products or collections could be read')
    B['products'], B['collections'] = products, cols

    # classify collections
    handles = [c['h'] for c in cols]
    title_of = {c['h']: c['t'] for c in cols}
    find = lambda rx: next((h for h in handles if re.search(rx, h + ' ' + title_of[h], re.I)), None)
    new_c, best_c, sale_c = find(r'\bnew\b|new-in|latest|just'), find(r'best|popular|top'), find(r'outlet|sale|clearance|last.?chance')
    edits = [h for h in handles if EDIT_RE.search(h + ' ' + title_of[h])]
    cats = [h for h in handles if h not in edits]
    season = [h for h in edits if re.search(r'\d{2}', title_of[h]) and h not in (new_c, best_c, sale_c)]
    hero_c = season[0] if season else new_c or (handles[0] if handles else None)
    feature_c = next((h for h in edits if h not in (new_c, best_c, sale_c, hero_c)), None)
    outer = next((h for h in cats if re.search(r'jacket|outer|coat', h + title_of[h], re.I)), cats[0] if cats else None)

    log('· Theme, logo, favicon')
    t = extract_theme(home)
    theme = build_theme(t)
    fam = t['fonts'].get('heading') or t['fonts'].get('body')
    gf = google_font(fam)
    theme['font'] = fam if gf else None
    theme['fontHref'] = gf
    (found('Theme colours from site CSS: bg %s, text %s, accent %s' % (theme['bg'], theme['ink'], theme['stone'])) if t['bg'] or t['text'] else missing('Theme colours not found in site CSS: using neutral defaults'))
    if gf: found('Font: %s (Google Fonts)' % fam)
    else: missing('Font: %s (not on Google Fonts, falling back to system font)' % (fam or 'not found'))
    B['theme'] = theme
    assets = {}
    logo_imgs = [i for i in soup.select('header img, [class*=header] img, [class*=logo] img, img[class*=logo]') if i.get('src') or i.get('data-src')]
    dark_url = light_url = None
    for i in logo_imgs:
        u = absu(base, i.get('src') or i.get('data-src'))
        cls = ' '.join(i.get('class', [])) + ' ' + u
        if re.search(r'transparent|white|light|inverse', cls, re.I): light_url = light_url or u
        else: dark_url = dark_url or u
    if not dark_url:
        svg = soup.select_one('header a[href="/"] svg, [class*=logo] svg')
        if svg and Image:
            png = svg_to_png(str(svg).encode())
            if png: open(os.path.join(img_dir, 'logo-src.png'), 'wb').write(png); dark_url = 'file'
    lp = os.path.join(img_dir, 'logo-src.png')
    big = lambda u: (u + ('&' if '?' in u else '?') + 'width=600') if u and '/cdn/shop/' in u and 'width=' not in u else (re.sub(r'width=\d+', 'width=600', u) if u else u)
    def svg_logo(u):   # an <img src="logo.svg">: rasterise the vector itself (sharp at any size) instead of a CDN thumbnail
        if not (u and re.search(r'\.svg(\?|$)', u, re.I) and Image): return False
        st, _, body = fetch(re.sub(r'[?&]width=\d+', '', u))
        png = svg_to_png(body.encode() if isinstance(body, str) else body) if st == 200 and body else None
        if png: open(lp, 'wb').write(png)
        return bool(png)
    got = dark_url == 'file' or svg_logo(dark_url) or (dark_url and save_image(big(dark_url), lp)) or svg_logo(light_url) or (light_url and save_image(big(light_url), lp))
    if got and Image:
        tone, mono = logo_tone(lp)
        if mono:
            recolour(lp, os.path.join(img_dir, 'logo-black.png'), (17, 17, 17))
            recolour(lp, os.path.join(img_dir, 'logo-white.png'), (255, 255, 255))
            assets['logoLight'] = 'assets/img/logo-white.png'
        else:
            shutil.copy(lp, os.path.join(img_dir, 'logo-black.png'))
        os.remove(lp)
        assets['logoDark'] = 'assets/img/logo-black.png'
        found('Logo from site header (%s, %s)' % (tone, 'monochrome → dark + light versions' if mono else 'colour'))
    else:
        wordmark(B['name'], os.path.join(img_dir, 'logo-black.png'), (17, 17, 17))
        wordmark(B['name'], os.path.join(img_dir, 'logo-white.png'), (255, 255, 255))
        assets['logoDark'], assets['logoLight'] = 'assets/img/logo-black.png', 'assets/img/logo-white.png'
        missing('Logo not found: generated a plain text wordmark placeholder')
    fav = soup.find('link', rel=lambda r: r and ('icon' in [x.lower() for x in (r if isinstance(r, list) else [r])]))
    fav_url = absu(base, fav['href']) if fav and fav.get('href') else base + '/favicon.ico'
    if save_image(fav_url, os.path.join(img_dir, 'favicon.png'), max_w=96, fmt='png'):
        found('Favicon'); assets['favicon'] = 'assets/img/favicon.png'
    else:
        shutil.copy(os.path.join(img_dir, 'logo-black.png'), os.path.join(img_dir, 'favicon.png')); assets['favicon'] = 'assets/img/favicon.png'
        missing('Favicon not found: using the logo instead')

    log('· Homepage hero media')
    vids = homepage_videos(soup, base)
    hero = hero_video(vids, out_dir, base)
    big_imgs = []
    main = soup.find('main') or soup
    for im in main.find_all('img'):
        u = im.get('src') or im.get('data-src') or ''
        srcset = im.get('srcset') or im.get('data-srcset') or ''
        w = max([int(x) for x in re.findall(r'\s(\d{3,4})w', srcset)] or [int(im.get('width') or 0)])
        if u and w >= 900 and '/products/' not in u and 'logo' not in u.lower():
            big_imgs.append(absu(base, u))
    big_imgs = list(dict.fromkeys(big_imgs))
    ogi = soup.find('meta', property='og:image')
    if not hero.get('poster'):
        cand = big_imgs[:1] + ([absu(base, ogi['content'])] if ogi and ogi.get('content') else [])
        for u in cand:
            if save_image(re.sub(r'width=\d+', 'width=1200', u), os.path.join(img_dir, 'hero-poster.jpg'), max_w=1000, fmt='jpg'):
                hero['poster'] = 'assets/img/hero-poster.jpg'; found('Hero image from homepage'); break
    if not hero.get('video'): missing('No homepage video found (hero uses a still image)')
    if not hero.get('poster') and products:
        p0 = next(iter(products.values()))
        if p0['im'] and save_image(p0['im'][0] + ('&' if '?' in p0['im'][0] else '?') + 'width=1000', os.path.join(img_dir, 'hero-poster.jpg'), max_w=1000, fmt='jpg'):
            hero['poster'] = 'assets/img/hero-poster.jpg'; missing('No homepage hero image found: using a product photo')
    wide = None
    for u in big_imgs[1:4]:
        if save_image(re.sub(r'width=\d+', 'width=1400', u), os.path.join(img_dir, 'campaign-wide.jpg'), max_w=1200, fmt='jpg'):
            wide = 'assets/img/campaign-wide.jpg'; found('Campaign image from homepage'); break
    if not wide and outer and products:
        p0 = products[next(c for c in cols if c['h'] == outer)['p'][0]]
        u = (p0['im'][1:2] or p0['im'])[0]
        if save_image(u + ('&' if '?' in u else '?') + 'width=1200', os.path.join(img_dir, 'campaign-wide.jpg'), max_w=1200, fmt='jpg'):
            wide = 'assets/img/campaign-wide.jpg'; missing('No second campaign image on the homepage: editorial banner uses a product photo')
    B['assets'] = assets

    log('· Help / about / legal pages')
    boiler = set(visible_lines(home))
    pages = find_page_links(soup, base)
    if shopify:
        for label, path in SHOPIFY_POLICIES.items():
            if label not in pages:
                st2, _, _ = fetch(base + path, tries=1)
                if st2 == 200:
                    grp = 'help' if label == 'Shipping' else 'legal'
                    pages[label] = {'group': grp, 't': label, 'url': base + path}
    page_text, emails, frame_hdrs = {}, set(), None
    for label, pg in pages.items():
        st2, h2, body = fetch(pg['url'])
        if st2 != 200: pg['sum'] = ''; continue
        frame_hdrs = frame_hdrs or h2
        lines = main_text_lines(body, boiler)
        page_text[label] = lines
        emails |= set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', ' '.join(lines)))
        pg['sum'] = summarise(lines)
    if 'Contact' in pages and len(pages['Contact'].get('sum', '')) < 40 and emails:
        pages['Contact']['sum'] = 'Email: ' + ', '.join(sorted(emails)) + '\nYou can also use the contact form on the site.'
    grouped = {'help': [], 'about': [], 'legal': []}
    for g, label, _ in PAGE_KINDS:
        if label in pages: grouped[g].append({'t': label, 'url': pages[label]['url'], 'sum': pages[label].get('sum', '')})
    B['pages'] = grouped
    for g, label, _ in PAGE_KINDS:
        (found if label in pages else missing)('%s page%s' % (label, (': ' + pages[label]['url']) if label in pages else ' not found'))
    xfo = (frame_hdrs or hdrs).get('x-frame-options', '').lower()
    csp = (frame_hdrs or hdrs).get('content-security-policy', '').lower()
    B['frameable'] = not (xfo in ('deny', 'sameorigin') or re.search(r"frame-ancestors\s+('none'|'self')", csp))
    found('Site pages %s be framed (X-Frame-Options: %s) → in-app browser %s' % ('can' if B['frameable'] else 'cannot', xfo or 'none', 'uses an iframe' if B['frameable'] else 'shows a summary + “Open on site”'))

    log('· Delivery & returns')
    ship = parse_shipping(page_text.get('Shipping', []))
    if ship['options']: found('Delivery options: ' + '; '.join('%s £%.2f' % (o['name'], o['price']) for o in ship['options']))
    else: missing('Delivery options could not be parsed from a shipping page')
    if ship['freeOver']: found('Free delivery threshold: %s%g' % ('£', ship['freeOver']))
    B['shipping'] = ship
    cur = (fetch_json(base + '/cart.js') or {}).get('currency') if shopify else None
    B['currency'] = {'code': cur or 'GBP', 'symbol': {'GBP': '£', 'USD': '$', 'EUR': '€', 'AUD': 'A$', 'CAD': 'C$'}.get(cur or 'GBP', '£')}
    rl = page_text.get('Returns') or page_text.get('Refund policy') or []
    rsum = ' '.join(l for l in rl if len(l) > 40)[:600]
    rsum = re.split(r'(?<=[.!?])\s', rsum)
    B['returns'] = {'summary': ' '.join(rsum[:2]).strip() if rsum and rsum[0] else ''}
    rtxt = ' '.join(rl)
    m_days = re.search(r'within (\d+) days', rtxt, re.I); m_from = re.search(r'from\s*([£$€]\s?\d+(?:\.\d{2})?)', rtxt, re.I)
    B['returns']['short'] = ('Returns from %s' % m_from.group(1)) if m_from else ('%s-day returns' % m_days.group(1)) if m_days else ('Easy returns' if rl else '')
    (found if B['returns']['summary'] else missing)('Returns copy' + (': ' + B['returns']['summary'][:80] + '…' if B['returns']['summary'] else ' not found'))

    log('· Socials, reviews, announcement bar')
    igs = [h for h in re.findall(r'instagram\.com/([A-Za-z0-9_.]{2,30})', home) if h.lower() not in ('p', 'reel', 'explore', 'accounts', 'stories', 'tv', 'reels')]
    B['socials'] = {'instagram': igs[0].rstrip('.') if igs else None}
    for net, rx in (('tiktok', r'tiktok\.com/@([A-Za-z0-9_.]+)'), ('facebook', r'facebook\.com/([A-Za-z0-9_.-]+)'), ('youtube', r'youtube\.com/(@?[A-Za-z0-9_.-]+)'), ('pinterest', r'pinterest\.[a-z.]+/([A-Za-z0-9_.-]+)')):
        mm = re.findall(rx, home)
        mm = [x for x in mm if x.lower() not in ('sharer', 'share', 'tr', 'plugins', 'dialog', 'pin', 'embed', 'watch')]
        if mm: B['socials'][net] = mm[0]
    (found if B['socials']['instagram'] else missing)('Instagram: ' + ('@' + B['socials']['instagram'] if B['socials']['instagram'] else 'not found'))
    # Instagram feed (Home grid): Instagram can't be scraped, so followers/posts are collected separately in a browser and
    # stored in brand.overrides.json -> instagram (merged on top of this stub, so re-scrapes and --rebuild keep them).
    ig = B['socials']['instagram']
    B['instagram'] = {'handle': ig, 'url': 'https://www.instagram.com/%s/' % ig if ig else None, 'followers': None, 'posts': []}
    if not ig_override_posts(out_dir):
        missing('Instagram feed: posts not collected (gather them in a browser into brand.overrides.json -> instagram.posts; Home grid hidden until then)')
    rendered = render_home(base) if do_render else None
    B['reviews'] = trustpilot(rendered, home, domain)
    if B['reviews']: found('Trustpilot: %s %s/5 from %d reviews (live widget data)' % (B['reviews']['label'], B['reviews']['score'], B['reviews']['count']))
    else: missing('No review score found on the site (social proof block hidden; nothing invented)')
    ann = []
    src_ann = (rendered or {}).get('announce') or []
    if not src_ann:
        for e in soup.select('[class*=announcement], [class*=marquee], [class*=ticker], [class*=usp], .splide__slide.message'):
            src_ann += [l for l in visible_lines(e) if 6 < len(l) < 90]
    for a in src_ann:
        s = sentence_case(a)
        if s.lower() not in [x.lower() for x in ann] and not re.search(r'cookie|accept|close|menu|search|cart|£\d+\.\d\d', s, re.I): ann.append(s)
    perks = []
    if ship['freeOver']: perks.append('Free %s delivery over %s%g' % (ship['region'] or '', B['currency']['symbol'], ship['freeOver']))
    perks += [x for x in ann[:6] if not re.fullmatch(r'\s*(instagram|tiktok|facebook|twitter|x|youtube|pinterest|snapchat|email|contact( us)?)\s*', x, re.I)][:5]
    if B['returns']['short'] and not any('return' in p.lower() for p in perks): perks.append(B['returns']['short'])
    for n in ship['notes'][:1]:
        if re.search(r'now shipping|warehouse', n, re.I): perks.append(n.rstrip('.'))
    B['perks'] = [re.sub(r'\s+', ' ', p).strip() for p in dict.fromkeys(perks) if p]
    # payment methods from the store's payment icons (Shopify renders <svg aria-labelledby="pi-apple_pay">…)
    pays = list(dict.fromkeys(re.findall(r'\bpi-([a-z_]+)"', home)))
    if pays: B['payments'] = pays; found('Payment methods (footer icons): ' + ', '.join(pays))
    else: missing('Payment icons not found: checkout shows the default Apple Pay / Shop Pay / Klarna set')
    (found if ann else missing)('Announcement bar: ' + (' | '.join(ann[:5]) if ann else 'nothing found (perks built from delivery/returns copy only)'))

    rewards_link = soup.find('a', href=re.compile(r'loyal|reward', re.I))
    B['rewards'] = {'enabled': True, 'name': B['short'] + ' Rewards', 'real': bool(rewards_link), 'stockists': 'Stockists' in pages}
    (found if rewards_link else missing)('Loyalty programme ' + ('page: ' + absu(base, rewards_link['href']) if rewards_link else 'not found (rewards card is illustrative only)'))

    log('· Home, shop, search, drop')
    def ctitle(h): return title_of.get(h, '')
    B['home'] = {'newCol': new_c, 'bestCol': best_c, 'newSub': ('The latest %s pieces' % ctitle(hero_c)) if hero_c and hero_c != new_c else 'The latest arrivals',
                 'hero': dict(hero, eyebrow='New Season' if hero_c and hero_c != new_c else 'New In', title=ctitle(hero_c).upper() if hero_c else B['name'].upper(), cta='Shop ' + ctitle(hero_c) if hero_c else 'Shop now', col=hero_c),
                 'tiles': [[h, title_of[h]] for h in cats[:6]],
                 'editorial': {'col': outer, 'img': wide, 'eyebrow': 'Shop the edit', 'title': ctitle(outer).upper()} if outer and wide else None,
                 'feature': {'col': feature_c, 'title': ctitle(feature_c).upper(), 'cta': 'Shop now'} if feature_c else None}
    B['shop'] = {'kicker': B['legalName'], 'cats': cats, 'edits': edits,
                 'featureCats': {'col': hero_c, 'title': ctitle(hero_c).upper(), 'cta': 'Shop now', 'idx': 1} if hero_c else None,
                 'featureEdits': {'col': sale_c, 'title': ctitle(sale_c).upper(), 'cta': 'Shop the ' + ctitle(sale_c).lower()} if sale_c else None}
    types = collections.Counter(p['ty'] for p in products.values() if p['ty'])
    B['search'] = {'trending': [re.sub(r's$', '', t) if not t.lower().endswith(('ss', 'ts', 'wear')) else t for t, _ in types.most_common(8)], 'popular': [h for h in [new_c] + cats[:4] if h]}
    B['sizes'] = {'groups': size_groups(products)}
    (found if B['sizes']['groups'] else missing)('Size options from variants: ' + ('; '.join('%s %s' % (g['label'], '/'.join(g['opts'])) for g in B['sizes']['groups']) or 'none'))
    # drop: most recently published season collection that isn't the current hero collection
    drop = None
    if shopify:
        seasons = [c for c in all_cols if SEASON_RE.match(c.get('title', '').strip()) and c.get('products_count', 0) >= 4 and c['handle'] != hero_c]
        seasons.sort(key=lambda c: ((c.get('published_at') or '')[:10], SEASON_RE.match(c['title'].strip()).end() >= len(c['title'].strip()), c.get('products_count', 0)), reverse=True)
        if seasons:
            dc = seasons[0]
            items = paged(base + '/collections/' + dc['handle'] + '/products.json?limit=250&page={page}', 'products', 2)
            avoid = set((next((c['p'] for c in cols if c['h'] == new_c), [])) + (next((c['p'] for c in cols if c['h'] == hero_c), [])))
            items.sort(key=lambda p: p.get('published_at') or '', reverse=True)
            pick = [p for p in items if p['handle'] not in avoid]
            if len(pick) < 6: pick += [p for p in items if p['handle'] in avoid][:6 - len(pick)]
            pick = pick[:8]
            if len(pick) % 2: pick = pick[:-1] or pick
            for p in pick:
                if p['handle'] not in products: products[p['handle']] = map_product(p)
            tags = [t for p in products.values() for t in p['tg']]
            nums = [int(m.group(1)) for t in tags for m in [re.match(r'^[A-Z]{2,}\d{2}D(\d{1,2})$', t)] if m]
            mt = SEASON_RE.match(dc['title'].strip())
            names = {'AW': 'Autumn Winter', 'SS': 'Spring Summer', 'FW': 'Fall Winter'}
            pretty = (names.get(mt.group(1).upper(), nice_title(mt.group(1))) + ' ' + mt.group(2)) if mt else dc['title']
            drop = {'num': '%02d' % ((max(nums) + 1) if nums else 1), 'name': dc['title'].strip().upper(), 'title': pretty, 'col': dc['handle'],
                    'products': [p['handle'] for p in pick], 'weekday': 4, 'hour': 19, 'earlyHours': 24,
                    'previous': {'col': hero_c, 'title': ctitle(hero_c).upper()} if hero_c else None}
            found('Next drop: DROP %s / %s (collection “%s”, %d first-look products; drop number %s)' % (drop['num'], drop['name'], dc['title'], len(pick), 'from existing drop tags' if nums else 'defaulted to 01'))
            missing('Drop date is not published anywhere: countdown uses a rolling placeholder (app early access Wed 19:00, website Thu 19:00)')
    if not drop: missing('No upcoming season collection found: Drops tab hidden')
    B['drop'] = drop
    about = summarise(page_text.get('About us', []), 420).split('\n')[0] if page_text.get('About us') else meta_desc
    B['copy'] = {'about': about, 'emptyBag': 'Start with the latest %s pieces.' % (ctitle(hero_c) or 'new'), 'heroNotif': 'The new season is here.'}
    if not about: missing('About copy not found')
    B['pitch'] = {'title': B['name'] + ',<br>one tap away.',
                  'copy': 'A concept for a native %s shopping app: drop alerts, early access, saved sizes and a faster path from first look to checkout. Tap around, everything works.' % B['name'],
                  'list': ['Drops with app-only early access', 'Saved size and back-in-size alerts', 'Shopify checkout with Apple Pay, Shop Pay and %s' % ('Klarna' if 'klarna' in (B.get('payments') or ['klarna']) else 'PayPal' if 'paypal' in B['payments'] else 'cards')]}
    B['pdpPerks'] = [p for p in [('Free %s delivery over %s%g' % (ship['region'], B['currency']['symbol'], ship['freeOver'])).replace('  ', ' ') if ship['freeOver'] else 'Tracked delivery',
                                 'Easy returns' if B['returns']['summary'] else 'Secure checkout', 'Earn %s' % B['rewards']['name'] if B['rewards']['real'] else
                                 ('Klarna available' if 'klarna' in (B.get('payments') or ['klarna']) else 'PayPal available' if 'paypal' in B['payments'] else 'Secure checkout')]]
    B['report'] = {'found': FOUND, 'missing': MISSING}
    return B

def ig_override_posts(out_dir):
    """Instagram posts hand-collected into <slug>/brand.overrides.json (instagram.posts), or []."""
    try: return ((json.load(open(os.path.join(out_dir, 'brand.overrides.json'))).get('instagram') or {}).get('posts')) or []
    except (OSError, ValueError): return []

def check_instagram(B, out_dir):
    """Log the Instagram feed status and drop posts whose url isn't an instagram.com post or whose thumbnail is missing."""
    ig = B.get('instagram') or {}
    posts = []
    for p in ig.get('posts') or []:
        url, im = p.get('url') or '', p.get('image') or ''
        if not re.match(r'^https://(www\.)?instagram\.com/(p|reel|tv)/[A-Za-z0-9_-]+/?', url): log('  ✗ Instagram post skipped, not an instagram.com post URL: %r' % url); continue
        if not im or not os.path.exists(os.path.join(out_dir, im)): log('  ✗ Instagram post skipped, thumbnail missing: %s (%s)' % (im, url)); continue
        if p.get('type') not in ('reel', 'carousel', 'photo'): p = dict(p, type='photo')
        posts.append(p)
    if ig: ig['posts'] = posts
    if posts: log('· Instagram feed: @%s, %s followers, %d posts (collected %s, from brand.overrides.json)' % (ig.get('handle'), ig.get('followers') or '?', len(posts), ig.get('collected') or '?'))
    else: log('· Instagram feed: no posts (Home grid hidden). Collect them in a browser into brand.overrides.json -> instagram.posts')

# ---------------------------------------------------------------- write the app
def deep_merge(a, b):
    """b wins. dicts merge recursively; lists and scalars are replaced. Keys starting with '_' are comments."""
    if not isinstance(a, dict) or not isinstance(b, dict): return b
    out = dict(a)
    for k, v in b.items():
        if k.startswith('_'): continue
        out[k] = deep_merge(a.get(k), v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out

def theme_css(th):
    font = th.get('font')
    pairs = [('ink', th['ink']), ('bg', th['bg']), ('bg-rgb', th['bgRgb']), ('text', th['text']), ('muted', th['muted']), ('line', th['line']),
             ('sand', th['sand']), ('sand-2', th['sand2']), ('stone', th['stone']), ('sale', th['sale']),
             ('stage-a', th['stageA']), ('stage-b', th['stageB']), ('stage-c', th['stageC'])]
    css = ':root{' + ';'.join('--%s:%s' % kv for kv in pairs) + (";--font:'%s'" % font if font else ";--font:-apple-system") + '}'
    return css

def write_app(B, out_dir):
    os.makedirs(os.path.join(out_dir, 'assets', 'img'), exist_ok=True)
    for f in ('app.js', 'app.css'):
        shutil.copy(os.path.join(TEMPLATE, f), os.path.join(out_dir, 'assets', f))
    # drop internal-only product fields to keep the payload small
    slim = dict(B)
    slim['products'] = {h: {k: v for k, v in p.items() if k not in ('pub',)} for h, p in B.get('products', {}).items()}
    with open(os.path.join(out_dir, 'assets', 'brand.js'), 'w') as f:
        f.write('/* Generated from brand.json by tools/build_brand.py. Do not edit; edit brand.json / brand.overrides.json and run --rebuild. */\n')
        f.write('window.BRAND=' + json.dumps(slim, ensure_ascii=False, separators=(',', ':')) + ';\n')
    th = B['theme'] = normalise_theme(B['theme'])
    tpl = open(os.path.join(TEMPLATE, 'index.html')).read()
    rep = {'{{NAME}}': html.escape(B['name']), '{{THEME_COLOR}}': th['ink'], '{{FAVICON}}': B['assets'].get('favicon', ''),
           '{{FONT_LINK}}': ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="%s" rel="stylesheet">' % html.escape(th['fontHref'])) if th.get('fontHref') else '',
           '{{THEME_CSS}}': theme_css(th), '{{VERSION}}': datetime.datetime.now().strftime('%Y%m%d%H%M')}
    # optional per-brand stylesheet (<slug>/brand.css): corner radii, type scale, logo sizes... loaded after app.css
    bcss = os.path.join(out_dir, 'brand.css')
    if os.path.exists(bcss):
        shutil.copy(bcss, os.path.join(out_dir, 'assets', 'brand.css'))
        rep['{{BRAND_CSS}}'] = '<link rel="stylesheet" href="assets/brand.css?v=%s">' % rep['{{VERSION}}']
    else:
        rep['{{BRAND_CSS}}'] = ''
        if os.path.exists(os.path.join(out_dir, 'assets', 'brand.css')): os.remove(os.path.join(out_dir, 'assets', 'brand.css'))
    for k, v in rep.items(): tpl = tpl.replace(k, v)
    open(os.path.join(out_dir, 'index.html'), 'w').write(tpl)

def main():
    ap = argparse.ArgumentParser(description='Build a brandsdotapp concept app from a brand website.')
    ap.add_argument('url', nargs='?', help='Brand website, e.g. https://raith-clo.com')
    ap.add_argument('slug', nargs='?', help='Folder name, e.g. raith')
    ap.add_argument('--rebuild', metavar='SLUG', help='Re-render SLUG from its brand.json + brand.overrides.json without scraping')
    ap.add_argument('--refetch-video', metavar='SLUG', help='Re-download SLUG\'s homepage hero video at the best quality available, re-encode it with the HERO settings, then rebuild')
    ap.add_argument('--no-render', action='store_true', help='Skip the headless-Chrome pass (no announcement bar / Trustpilot widget data)')
    ap.add_argument('--max-products', type=int, default=400)
    ap.add_argument('--root', default=ROOT, help='Repo root (default: parent of tools/)')
    a = ap.parse_args()
    if a.rebuild or a.refetch_video:
        out = os.path.join(a.root, a.rebuild or a.refetch_video)
        B = json.load(open(os.path.join(out, 'brand.json')))
        if a.refetch_video:
            log('· Hero video for %s' % B['site'])
            st, _, home = fetch(B['site'] + '/')
            vids = homepage_videos(BeautifulSoup(home, 'html.parser'), B['site']) if st == 200 else []
            hero = hero_video(vids, out, B['site'])
            if not hero: sys.exit('No hero video could be fetched/encoded from %s' % B['site'])
            B.setdefault('home', {}).setdefault('hero', {})
            for k in ('video', 'videoWebm', 'videoW', 'videoH', 'poster'): B['home']['hero'].pop(k, None)
            B['home']['hero'].update(hero)
    else:
        if not a.url or not a.slug: ap.error('give URL and SLUG, or --rebuild SLUG')
        if not re.match(r'^[a-z0-9][a-z0-9-]*$', a.slug): ap.error('slug must be lowercase letters, digits and dashes')
        out = os.path.join(a.root, a.slug)
        os.makedirs(out, exist_ok=True)
        log('Scraping %s → %s/' % (a.url, os.path.relpath(out, a.root)))
        ovp = os.path.join(out, 'brand.overrides.json')
        extra = (json.load(open(ovp)).get('scrape', {}) if os.path.exists(ovp) else {}).get('extraCollections', [])
        B = scrape(a.url, a.slug, out, do_render=not a.no_render, max_products=a.max_products, extra_cols=extra)
    ov = os.path.join(out, 'brand.overrides.json')
    if os.path.exists(ov):
        B = deep_merge(B, json.load(open(ov)))
        # collection titles can be renamed without replacing the whole list: "collectionTitles": {"handle": "Title"}
        for c in B.get('collections', []):
            if c['h'] in (B.get('collectionTitles') or {}): c['t'] = B['collectionTitles'][c['h']]
        log('· Applied overrides from %s' % os.path.relpath(ov, a.root))
    check_instagram(B, out)
    json.dump(B, open(os.path.join(out, 'brand.json'), 'w'), ensure_ascii=False, indent=1)
    write_app(B, out)
    rep = B.get('report', {})
    log('\nBuilt %s/  (%d products, %d collections)' % (os.path.relpath(out, a.root), len(B.get('products', {})), len(B.get('collections', []))))
    if rep.get('missing'):
        log('\nMissing / placeholder (%d):' % len(rep['missing']))
        for m in rep['missing']: log('  - ' + m)
    log('\nPreview:  cd %s && python3 -m http.server 8000  →  http://localhost:8000/%s/' % (a.root, os.path.basename(out)))

if __name__ == '__main__':
    main()
