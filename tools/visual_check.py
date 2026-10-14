"""Automated visual checks. Usage: python3 tools/visual_check.py SLUG [--sizes 393x852,375x667]
1. text-edge: any visible text line closer than 8px to the screen edge, or clipped by its box (overflow)
2. image-text crop: OCR (tesseract) each cover-cropped image; warn when detected words fall partly outside the visible crop
3. vertical wording: brands with no size groups must not show size UI/wording (size prefs, 'in my size', 'back in size')
Exit 1 on any failure; prints WARN lines for crop risk."""
import sys, os, json, argparse, subprocess, tempfile, urllib.request, hashlib
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('--sizes', default='393x852,375x667'); ap.add_argument('--base', default='http://localhost:8765')
a = ap.parse_args(); URL = '%s/%s/' % (a.base.rstrip('/'), a.slug)
EDGE_JS = r"""() => {
  const scr = document.querySelector('.screen') || document.body, R = scr.getBoundingClientRect(), out = [];
  const view = document.querySelector('.view.top') || scr;
  const walker = document.createTreeWalker(view, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const t = walker.currentNode; if (!t.textContent.trim()) continue;
    const el = t.parentElement; const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
    if (el.closest('.hc-track,.rail,.chips,.scroller,.marquee,.ann,[data-scroll-x]')) continue;
    let a = el, sx = false; while (a && a !== view) { const c = getComputedStyle(a); if (/auto|scroll/.test(c.overflowX) && a.scrollWidth > a.clientWidth + 4) { sx = true; break; } a = a.parentElement; }
    if (sx || /^[★☆\s]+$/.test(t.textContent)) continue;
    const rg = document.createRange(); rg.selectNodeContents(t);
    for (const r of rg.getClientRects()) {
      if (r.width < 2 || r.bottom < R.top || r.top > R.bottom) continue;
      if (r.left < R.left + 8 || r.right > R.right - 8) out.push({k:'edge', t:t.textContent.trim().slice(0,50), l:Math.round(r.left-R.left), r:Math.round(R.right-r.right)});
    }
    if ((cs.overflow === 'hidden' || cs.overflowX === 'hidden') && cs.textOverflow !== 'ellipsis' && cs.webkitLineClamp === 'none' && el.scrollWidth > el.clientWidth + 2)
      out.push({k:'clip', t:t.textContent.trim().slice(0,50)});
  }
  return out; }"""
IMG_JS = r"""async () => { const out = [], view = document.querySelector('.view.top') || document.body;
  const add = (src, nw, nh, b, fit, posS) => { if (!src || nw < 200 || b.width < 120 || fit !== 'cover') return; const s = Math.max(b.width / nw, b.height / nh), pos = (posS || '50% 50%').split(' ').map(v => parseFloat(v) / 100);
    const vw = b.width / s, vh = b.height / s; out.push({src, nw, nh, x: (nw - vw) * (isNaN(pos[0]) ? .5 : pos[0]), y: (nh - vh) * (isNaN(pos[1]) ? .5 : pos[1]), w: vw, h: vh}); };
  for (const i of view.querySelectorAll('img')) add(i.currentSrc || i.src, i.naturalWidth, i.naturalHeight, i.getBoundingClientRect(), getComputedStyle(i).objectFit, getComputedStyle(i).objectPosition);
  for (const v of view.querySelectorAll('video[poster]')) { const im = new Image(); im.src = v.poster; await im.decode().catch(()=>{}); add(im.src, im.naturalWidth, im.naturalHeight, v.getBoundingClientRect(), getComputedStyle(v).objectFit, getComputedStyle(v).objectPosition); }
  for (const e of view.querySelectorAll('*')) { const c = getComputedStyle(e); const m = c.backgroundImage.match(/url\("?([^")]+)"?\)/); if (!m || c.backgroundSize !== 'cover') continue; const im = new Image(); im.src = m[1]; await im.decode().catch(()=>{}); add(im.src, im.naturalWidth, im.naturalHeight, e.getBoundingClientRect(), 'cover', c.backgroundPosition); }
  return out; }"""
WORDS_JS = r"""() => { const t = (document.querySelector('.view.top') || document.body).innerText; const m = []; const re = /(in my size|in your size|back in size|your size|save my size|clothing size|select a size)/ig; let x; while ((x = re.exec(t))) m.push(t.slice(Math.max(0, x.index - 30), x.index + 40).replace(/\s+/g, ' ')); return m; }"""
ocr_cache = {}
def ocr_words(src):
  if src in ocr_cache: return ocr_cache[src]
  fn = os.path.join(tempfile.gettempdir(), 'vc-' + hashlib.md5(src.encode()).hexdigest())
  try:
    urllib.request.urlretrieve(src, fn)
    tsv = subprocess.run(['tesseract', fn, '-', '--psm', '11', 'tsv'], capture_output=True, text=True, timeout=60).stdout
  except Exception: tsv = ''
  ws = []
  for ln in tsv.splitlines()[1:]:
    c = ln.split('\t')
    if len(c) == 12 and c[11].strip() and float(c[10]) > 75 and len(c[11].strip()) >= 3 and c[11].strip().isalpha():
      ws.append((c[11], int(c[6]), int(c[7]), int(c[8]), int(c[9])))
  ocr_cache[src] = ws; return ws
fails = []; warns = []
with sync_playwright() as pw:
  br = pw.chromium.launch(executable_path='/usr/bin/google-chrome')
  for size in a.sizes.split(','):
    w, h = map(int, size.split('x'))
    ctx = br.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True); p = ctx.new_page()
    p.goto(URL + '?nosplash&nowelcome&nopush', wait_until='networkidle'); p.wait_for_timeout(1200)
    nosize = p.evaluate("!(window.BRAND.sizes && window.BRAND.sizes.groups && window.BRAND.sizes.groups.length)")
    def check(state):
      H = p.evaluate("(document.querySelector('.view.top')||{}).scrollHeight || 0"); y = 0
      while True:
        p.evaluate("y => { const v = document.querySelector('.view.top'); if (v) v.scrollTop = y; const s = v && v.querySelector('.pscroll'); if (s) s.scrollTop = y; }", y); p.wait_for_timeout(350)
        for e in p.evaluate(EDGE_JS): fails.append('%s %s %s: %s' % (size, state, e['k'], json.dumps(e, ensure_ascii=False)))
        for im in p.evaluate(IMG_JS):
          for (wd, l, t, ww, hh) in ocr_words(im['src']):
            # scale OCR coords (from downloaded file) to natural size (same file, so 1:1)
            inside = l >= im['x'] and t >= im['y'] and l + ww <= im['x'] + im['w'] and t + hh <= im['y'] + im['h']
            outside = l + ww <= im['x'] or t + hh <= im['y'] or l >= im['x'] + im['w'] or t >= im['y'] + im['h']
            if not inside: warns.append('%s %s %s word %r %s by crop (%s)' % (size, state, 'CUT' if not outside else 'hidden', wd, 'cut' if not outside else 'hidden', im['src'].split('/')[-1]))
        if nosize:
          for m in p.evaluate(WORDS_JS): fails.append('%s %s size-wording: …%s…' % (size, state, m))
        y += h - 100
        if y >= H: break
    check('home')
    for tab in ['shop', 'drops', 'wishlist', 'bag', 'account']:
      if p.locator('#tabbar button[data-tab="%s"]' % tab).count(): p.click('#tabbar button[data-tab="%s"]' % tab); p.wait_for_timeout(900); check(tab)
    p.evaluate("window.__app.switchTab('shop')"); p.wait_for_timeout(700)
    if p.locator('.view.top .cat-row').count():
      p.locator('.view.top .cat-row').first.click(); p.wait_for_timeout(1000); check('collection')
      if p.locator('.view.top .pcard').count(): p.locator('.view.top .pcard').first.click(); p.wait_for_timeout(1200); check('product')
    ctx.close()
  br.close()
fails = list(dict.fromkeys(fails)); warns = [x for x in dict.fromkeys(warns) if 'CUT' in x]
for x in fails: print('FAIL', x)
for x in warns: print('WARN', x)
print('%s: %d fail, %d crop warnings' % (a.slug, len(fails), len(warns))); sys.exit(1 if fails else 0)
