"""Capture every screen of a built brand app for visual review. Usage: python3 tools/screens.py SLUG [--sizes 393x852,375x667] [--out DIR]
Safe areas are simulated (notch/home bar) because headless Chrome reports env(safe-area-inset-*) as 0.
Writes DIR/<slug>/<size>/NN-name.png plus a contact sheet DIR/<slug>/<size>-sheet-K.png (8 screens per sheet)."""
import sys, os, argparse
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('--sizes', default='393x852,375x667')
ap.add_argument('--base', default='http://localhost:8765'); ap.add_argument('--out', default='/workspace/review')
a = ap.parse_args()
SAFE = {'393x852': (59, 34), '375x667': (20, 0), '430x932': (59, 34)}
def css(t, b): return ":root{--sat:%dpx !important}.tabbar{padding-bottom:%dpx !important;height:calc(60px + %dpx) !important}.buybar{padding-bottom:%dpx !important}.sheet{padding-bottom:%dpx !important}" % (t, b + 8, b, b + 12, b + 20)
URL = '%s/%s/' % (a.base.rstrip('/'), a.slug)
with sync_playwright() as pw:
  br = pw.chromium.launch(executable_path='/usr/bin/google-chrome')
  for size in a.sizes.split(','):
    w, h = map(int, size.split('x')); t, bt = SAFE.get(size, (47, 34))
    od = os.path.join(a.out, a.slug, size); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx.add_init_script("window.__deptDefault = true")
    p = ctx.new_page(); n = [0]; names = []
    def shot(name):
      n[0] += 1; fn = os.path.join(od, '%02d-%s.png' % (n[0], name)); p.screenshot(path=fn); names.append(fn)
    def go(q=''):
      p.goto(URL + '?nosplash&nowelcome&nopush' + q, wait_until='networkidle'); p.add_style_tag(content=css(t, bt)); p.wait_for_timeout(1200)
    def tab(x):
      if p.locator('#tabbar.hidden').count(): p.evaluate("window.__app.switchTab('home')"); p.wait_for_timeout(400)
      if p.locator('#tabbar button[data-tab="%s"]' % x).count(): p.click('#tabbar button[data-tab="%s"]' % x); p.wait_for_timeout(900); return True
      if x == 'wishlist' and p.locator('.view.top .hw-btn').count(): p.click('.view.top .hw-btn'); p.wait_for_timeout(900); return True
      return False
    def scroll_shots(name, maxn=8):
      H = p.evaluate("document.querySelector('.view.top').scrollHeight"); step = h - 160; y = 0; k = 0
      while k < maxn:
        p.evaluate("y => document.querySelector('.view.top').scrollTop = y", y); p.wait_for_timeout(700); shot('%s-%d' % (name, k)); k += 1
        y += step
        if y >= H - 100: break
      p.evaluate("document.querySelector('.view.top').scrollTop = 0")
    # splash + welcome
    p.goto(URL + '?nopush', wait_until='domcontentloaded'); p.add_style_tag(content=css(t, bt)); p.wait_for_timeout(500); shot('splash')
    p.wait_for_timeout(3500); shot('welcome')
    go(); scroll_shots('home', 10)
    tab('shop'); shot('shop-cats'); scroll_shots('shop', 3)
    if p.locator('.view.top .seg button[data-seg="edits"]').count(): p.click('.view.top .seg button[data-seg="edits"]'); p.wait_for_timeout(600); shot('shop-edits')
    if p.locator('.view.top .seg button[data-seg="cats"]').count(): p.click('.view.top .seg button[data-seg="cats"]'); p.wait_for_timeout(400)
    if p.locator('.view.top .cat-row').count(): p.locator('.view.top .cat-row').first.click(); p.wait_for_timeout(1200); scroll_shots('collection', 2)
    if p.locator('.view.top .pcard').count():
      i = p.evaluate("[...document.querySelectorAll('.view.top .pcard')].findIndex(c => !(window.__app.coming && window.__app.coming(c.dataset.v)))")
      p.locator('.view.top .pcard').nth(max(i, 0)).click(); p.wait_for_timeout(1400); shot('product')
      p.evaluate("document.querySelector('.view.top .pscroll').scrollTop = 520"); p.wait_for_timeout(500); shot('product-options')
      p.evaluate("document.querySelector('.view.top .pscroll').scrollTop = 1100"); p.wait_for_timeout(500); shot('product-more')
      if p.locator('.view.top .size:not(.out)').count() and not p.locator('.view.top .size.on').count(): p.locator('.view.top .size:not(.out)').first.click()
      if p.locator('#addBtn').count(): p.click('#addBtn'); p.wait_for_timeout(1400); shot('added')
    p.evaluate("window.__app.switchTab('bag')"); p.wait_for_timeout(900); scroll_shots('bag', 2)
    if p.locator('#checkout').count(): p.click('#checkout'); p.wait_for_timeout(900); shot('checkout'); p.keyboard.press('Escape'); p.wait_for_timeout(500)
    if tab('drops'): scroll_shots('drops', 3)
    tab('wishlist'); shot('wishlist')
    tab('home'); 
    if p.locator('.view.top [data-act="search"]').count():
      p.locator('.view.top [data-act="search"]').first.click(); p.wait_for_timeout(800); shot('search')
      p.fill('#sq', p.evaluate("(window.BRAND.search && window.BRAND.search.trending && window.BRAND.search.trending[0]) || 'a'")); p.wait_for_timeout(900); shot('search-results')
    tab('account'); 
    for d in p.locator('.view.top .acct-acc').all():
      try: d.locator('summary').click(); p.wait_for_timeout(150)
      except Exception: pass
    scroll_shots('account', 6)
    links = p.locator('.view.top [data-page]'); k = links.count()
    for i in range(k):
      try:
        p.locator('.view.top [data-page]').nth(i).scroll_into_view_if_needed(); p.locator('.view.top [data-page]').nth(i).click(); p.wait_for_timeout(900); shot('page-%d' % i)
        p.click('#brDone'); p.wait_for_timeout(400)
      except Exception as e: print('page', i, e)
    if p.locator('.view.top [data-act="rewards"]').count(): p.locator('.view.top [data-act="rewards"]').first.click(); p.wait_for_timeout(900); shot('rewards'); p.evaluate("window.__app.switchTab('home')"); p.wait_for_timeout(400)
    if p.locator('.view.top [data-act="size"]').count(): p.locator('.view.top [data-act="size"]').first.click(); p.wait_for_timeout(700); shot('size-sheet'); p.keyboard.press('Escape'); p.wait_for_timeout(400)
    # demo pushes
    demos = p.evaluate("[...new DOMParser().parseFromString(document.querySelector('#demoFab') ? '' : '', 'text/html').body.children].length") if False else None
    go(); tab('home')
    for d in ['bag', 'restock', 'price', 'drop', 'welcome', 'community']:
      try:
        p.click('#demoFab'); p.wait_for_timeout(500)
        if not p.locator('#sheet [data-demo="%s"]' % d).count(): p.keyboard.press('Escape'); p.wait_for_timeout(300); continue
        if d == 'bag': shot('demo-sheet')
        p.click('#sheet [data-demo="%s"]' % d); p.wait_for_timeout(1500); shot('push-' + d)
        p.evaluate("() => { const e = document.getElementById('push'); e && e.classList.remove('show'); document.getElementById('sheet').classList.remove('show'); const b = document.getElementById('sheetBackdrop'); b && b.classList.remove('show'); document.getElementById('welcome') && document.getElementById('welcome').classList.remove('show'); }")
        p.evaluate("window.__app.switchTab('home')"); p.wait_for_timeout(600)
      except Exception as e: print('demo', d, e)
    ctx.close()
    # contact sheets
    for si in range(0, len(names), 8):
      ims = [Image.open(f) for f in names[si:si + 8]]; tw = 300; th = int(tw * ims[0].height / ims[0].width)
      sheet = Image.new('RGB', (tw * 4, (th + 22) * ((len(ims) + 3) // 4)), 'white'); d = ImageDraw.Draw(sheet)
      for j, im in enumerate(ims):
        x, y = (j % 4) * tw, (j // 4) * (th + 22); sheet.paste(im.convert('RGB').resize((tw - 6, th - 6)), (x + 3, y + 22)); d.text((x + 4, y + 4), os.path.basename(names[si + j]), fill='black')
      sheet.save(os.path.join(a.out, a.slug, '%s-sheet-%d.png' % (size, si // 8)))
    print(a.slug, size, len(names), 'screens')
  # desktop pitch
  ctx = br.new_context(viewport={'width': 1440, 'height': 900}); p = ctx.new_page()
  p.goto(URL + '?nosplash&nowelcome&nopush', wait_until='networkidle'); p.wait_for_timeout(1500); p.screenshot(path=os.path.join(a.out, a.slug, 'desktop-pitch.png')); ctx.close()
  br.close()
