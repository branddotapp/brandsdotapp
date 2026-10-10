"""Layout / visual QA pass for a built brand app. Usage: python3 tools/layout_check.py SLUG [--base URL] [--sizes 390x844,1280x720,1440x800,1920x1080] [--shots DIR]
Visits every screen and state (tabs, both Shop segments, collection, product, sheets, auth, in-app browser, welcome, rewards,
empty states) and flags, inside the phone screen: horizontal overflow, clipped text (overflow without an ellipsis/clamp),
low-contrast text (WCAG AA), overlapping siblings in rows, misaligned header icons, tiny tap targets, non-brand fonts,
broken images and console errors. On desktop it also checks that the stage fits the viewport with no page scroll, and the three-column layout: phone centred,
4 "Why an app" stat boxes (valid new-tab source links, nothing clipped, overlapping, off-brand or low-contrast), columns never overlapping."""
import sys, os, argparse, json
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('--base', default='http://localhost:8765')
ap.add_argument('--sizes', default='390x844,1280x720,1440x800,1920x1080'); ap.add_argument('--shots'); ap.add_argument('-v', action='store_true')
a = ap.parse_args()
URL = '%s/%s/' % (a.base.rstrip('/'), a.slug)
problems, notes = [], []

CHECK = r"""(name) => {
  const out = [], info = [];
  const scr = document.querySelector('#screen'), sr = scr.getBoundingClientRect();
  const sc = sr.width / 390;
  const roots = [...document.querySelectorAll('.view.top, #sheet.show, #welcome.show, #browser.show, #tabbar:not(.hidden), #push.show, .toast.show, .demo-fab')];
  const desc = el => { let s = el.tagName.toLowerCase(); if (el.id) s += '#' + el.id; if (el.classList.length) s += '.' + [...el.classList].slice(0,2).join('.');
    const t = (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\s+/g,' ').slice(0, 40); return s + (t ? ' "' + t + '"' : ''); };
  const vis = el => { const r = el.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return false; const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    let e = el; while (e && e !== document.body) { const c = getComputedStyle(e); if (+c.opacity < 0.05) return false; e = e.parentElement; } return true; };
  const inScreen = r => r.bottom > sr.top + 1 && r.top < sr.bottom - 1;
  const hscroller = el => el.closest('.hscroll,.chips,.swatches,.gtrack,.marquee,.mq-track,.express');
  const parse = c => { const m = c.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?/); return m ? [+m[1], +m[2], +m[3], m[4] == null ? 1 : +m[4]] : null; };
  const lin = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
  const L = c => .2126 * lin(c[0]) + .7152 * lin(c[1]) + .0722 * lin(c[2]);
  const over = (top, bot) => { const a = top[3]; return [top[0]*a + bot[0]*(1-a), top[1]*a + bot[1]*(1-a), top[2]*a + bot[2]*(1-a), 1]; };
  // effective background: composite ancestor backgrounds down to the app shell, over the page colour (translucent bars
  // like the tab bar sit over page content, not over the black phone screen)
  const pageBg = parse(getComputedStyle(document.querySelector('.view.top') || document.body).backgroundColor) || [243,243,243,1];
  const bgOf = el => { const chain = []; let e = el; while (e && !e.matches('.app,#screen,body')) { chain.push(e); e = e.parentElement; }
    let col = pageBg.slice(); const layers = [];
    for (const n of chain) { const cs = getComputedStyle(n); if (cs.backgroundImage !== 'none' && !/^linear-gradient\(90deg|^none/.test(cs.backgroundImage)) return null;
      if (n.tagName === 'IMG' || n.tagName === 'VIDEO') return null;
      const c = parse(cs.backgroundColor); if (c && c[3] > 0) { layers.push(c); if (c[3] >= .999) break; } }
    for (let i = layers.length - 1; i >= 0; i--) col = over(layers[i], col);
    return col; };
  const onMedia = el => { let e = el; while (e && e !== document.body) { if (e.matches('.hero,.editorial,.feature-card,.drop-card,.cat-tile,.pimg,.gallery,.wl-top,.rcard,.rewards-mini,.ig-tile,.soon-note')) return true; e = e.parentElement; } return false; };
  const els = []; roots.forEach(r => { if (vis(r)) els.push(r, ...r.querySelectorAll('*')); });
  const seen = new Set();
  for (const el of els) {
    if (seen.has(el)) continue; seen.add(el);
    if (el.closest('svg') && el.tagName !== 'svg') continue;
    if (el.closest('.stars')) continue;   // star rating glyphs are graphics (grey track + filled overlay)
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect(); if (!inScreen(r)) continue;
    const cs = getComputedStyle(el);
    // horizontal overflow out of the phone screen
    if (!hscroller(el) && !el.closest('#push,.toast') && (r.right > sr.right + 1 || r.left < sr.left - 1) && !el.closest('.view.leave,.view.under')) out.push('overflow-x: ' + desc(el));
    const txt = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (txt) {
      // clipped text
      const clamp = cs.webkitLineClamp && cs.webkitLineClamp !== 'none';
      if (el.scrollWidth > el.clientWidth + 1 && cs.overflowX !== 'visible' && el.clientWidth > 0 && !hscroller(el)) {
        if (cs.textOverflow === 'ellipsis') info.push('ellipsis: ' + desc(el)); else if (!clamp) out.push('clipped text: ' + desc(el));
      }
      if (clamp && el.scrollHeight > el.clientHeight + 2) info.push('line-clamped: ' + desc(el));
      // contrast
      if (!onMedia(el) && !el.closest('.size.out,.br-body iframe,.xp,.apple-pay,#push')) {
        const bg = bgOf(el), fg = parse(cs.color);
        if (bg && fg) {
          let op = 1, e = el; while (e && e !== document.body) { op *= +getComputedStyle(e).opacity; e = e.parentElement; }
          const f = over([fg[0], fg[1], fg[2], fg[3] * op], bg);
          const ratio = (Math.max(L(f), L(bg)) + .05) / (Math.min(L(f), L(bg)) + .05);
          const px = parseFloat(cs.fontSize) / sc, big = px >= 18.6 || (px >= 14 && +cs.fontWeight >= 700);
          if (ratio < (big ? 3 : 4.5)) out.push('low contrast ' + ratio.toFixed(2) + ' (' + cs.color + ' on rgb(' + bg.slice(0,3).map(Math.round) + ')): ' + desc(el));
        }
      }
      // fonts
      if (!/apple-system|SF Pro|system-ui/.test(cs.fontFamily) || el.closest('.apple-pay,.xp,.br-done,.br-url')) {
        const want = getComputedStyle(document.documentElement).getPropertyValue('--font').trim().replace(/['"]/g,'');
        if (want && want !== '-apple-system' && !cs.fontFamily.replace(/['"]/g,'').includes(want) && !el.closest('.apple-pay,.xp,.br-done,.br-url,.sb-time')) out.push('font ' + cs.fontFamily + ': ' + desc(el));
      }
    }
    // overlapping siblings in flex/grid rows
    if ((cs.display === 'flex' || cs.display === 'grid') && !hscroller(el) && el.children.length > 1) {
      const kids = [...el.children].filter(k => vis(k) && getComputedStyle(k).position !== 'absolute' && getComputedStyle(k).position !== 'fixed');
      for (let i = 0; i < kids.length; i++) for (let j = i + 1; j < kids.length; j++) {
        const p = kids[i].getBoundingClientRect(), q = kids[j].getBoundingClientRect();
        const ox = Math.min(p.right, q.right) - Math.max(p.left, q.left), oy = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top);
        if (ox > 2 && oy > 2) out.push('overlap: ' + desc(kids[i]) + ' × ' + desc(kids[j]));
      }
    }
    // tap targets
    if ((el.matches('button,a,[data-act],.switch') && !el.matches('.link,.remove,.wl-skip,.link-row,.link.sm')) && !el.closest('.pitch')) {
      if ((r.width / sc < 28 || r.height / sc < 28) && !el.matches('.gdots i')) info.push('small target ' + Math.round(r.width/sc) + 'x' + Math.round(r.height/sc) + ': ' + desc(el));
    }
  }
  // header icons vertically centred on the title/logo
  const tb = document.querySelector('.view.top .topbar');
  if (tb && vis(tb)) { const mid = tb.querySelector('.tb-logo,.tb-title'); if (mid) { const m = mid.getBoundingClientRect(), c = (m.top + m.bottom) / 2;
    tb.querySelectorAll('.icon-btn').forEach(b => { const q = b.getBoundingClientRect(); if (Math.abs((q.top + q.bottom) / 2 - c) > 1.5) out.push('header icon off-centre: ' + desc(b)); }); } }
  // floating demo button must not sit on top of a toast or the buy bar
  const fab = document.querySelector('.demo-fab'), toast = document.querySelector('.toast.show'), bb = document.querySelector('.view.top .buybar.show');
  const hit = (x, y) => { const p = x.getBoundingClientRect(), q = y.getBoundingClientRect(); return Math.min(p.right, q.right) > Math.max(p.left, q.left) && Math.min(p.bottom, q.bottom) > Math.max(p.top, q.top); };
  if (fab && vis(fab) && toast && vis(toast) && hit(fab, toast)) out.push('demo button overlaps toast');
  if (fab && vis(fab) && bb && hit(fab, bb)) out.push('demo button overlaps buy bar');
  const v = document.querySelector('.view.top'); if (v && v.scrollWidth > v.clientWidth + 1) out.push('view scrolls horizontally (' + v.scrollWidth + ' > ' + v.clientWidth + ')');
  // broken images
  document.querySelectorAll('.view.top img, #sheet img, #welcome img').forEach(i => { if (i.complete && i.naturalWidth === 0 && i.getBoundingClientRect().width > 0) out.push('broken image ' + i.src.slice(-60)); });
  // desktop stage fit
  if (innerWidth > 520) { if (document.documentElement.scrollHeight > innerHeight + 1) out.push('page scrolls on desktop');
    ['.pitch', '#device', '.why', '.credit'].forEach(s => { const e = document.querySelector(s); if (!e || getComputedStyle(e).display === 'none') return; const q = e.getBoundingClientRect(); if (q.top < -1 || q.bottom > innerHeight + 1 || q.left < -1 || q.right > innerWidth + 1) out.push(s + ' outside viewport'); });
    // three-column stage (>1000px): pitch | phone | "Why an app" stats; below 1100px the stats sit under the pitch
    if (innerWidth > 1000) {
      const box = e => e.getBoundingClientRect(), hit = (p, q) => Math.min(p.right, q.right) - Math.max(p.left, q.left) > 1 && Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top) > 1;
      const why = document.querySelector('.why'), pitch = document.querySelector('.pitch'), dev = document.querySelector('#device');
      if (!why) out.push('stats column missing');
      else {
        const stats = [...why.querySelectorAll('.stat')];
        if (stats.length !== 4) out.push('stats: ' + stats.length + ' boxes (want 4)');
        const pr = box(pitch), dr = box(dev), wr = box(why);
        const cr = (() => { const g = document.createRange(); g.selectNodeContents(document.querySelector('.credit')); return g.getBoundingClientRect(); })();
        if (hit(dr, wr)) out.push('stats column overlaps the phone'); if (hit(dr, pr)) out.push('pitch overlaps the phone');
        if (hit(cr, wr) || hit(cr, pr) || hit(cr, dr)) out.push('credit line overlaps a column');
        if (innerWidth >= 1100) {
          if (!why.parentElement.classList.contains('col-r')) out.push('stats not in the right column');
          if (Math.abs((dr.left + dr.right) / 2 - innerWidth / 2) > 2) out.push('phone not centred (' + Math.round((dr.left + dr.right) / 2) + ' vs ' + innerWidth / 2 + ')');
          if (hit(pr, wr)) out.push('pitch overlaps stats');
        } else if (wr.top < pr.bottom - 1) out.push('stats overlap the pitch (narrow layout)');
        const want = getComputedStyle(document.documentElement).getPropertyValue('--font').trim().replace(/['"]/g,'');
        const pageBg = (() => { const m = getComputedStyle(document.documentElement).getPropertyValue('--stage-b').trim().match(/^#([0-9a-f]{6})$/i); return m ? [0, 2, 4].map(i => parseInt(m[1].substr(i, 2), 16)).concat(1) : [230, 230, 230, 1]; })();
        stats.forEach((s, i) => {
          const sr = box(s), n = 'stat ' + (i + 1);
          stats.slice(i + 1).forEach((t, j) => { if (hit(sr, box(t))) out.push(n + ' overlaps stat ' + (i + j + 2)); });
          ['.stat-num', '.stat-label', '.stat-src'].forEach(q => { if (!s.querySelector(q) || !s.querySelector(q).textContent.trim()) out.push(n + ' missing ' + q); });
          const a = s.querySelector('a.stat-src');
          if (!a || !/^https:\/\/[a-z0-9.-]+\.[a-z]{2,}\//i.test(a.getAttribute('href') || '') || a.target !== '_blank' || !/noopener/.test(a.rel)) out.push(n + ' source link invalid');
          const sbg = over(parse(getComputedStyle(s).backgroundColor) || [255, 255, 255, 0], pageBg);
          s.querySelectorAll('p,a').forEach(e => { if (!vis(e)) return; const r = box(e), cs = getComputedStyle(e);
            if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1) out.push(n + ' text spills out of its box: ' + desc(e));
            if ((e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 2) && cs.overflow !== 'visible') out.push(n + ' clipped text: ' + desc(e));
            if (want && want !== '-apple-system' && !cs.fontFamily.replace(/['"]/g,'').includes(want)) out.push(n + ' font ' + cs.fontFamily);
            const f = parse(cs.color); if (f) { const k = Math.abs(box(why.closest('.col')).width / why.closest('.col').offsetWidth) || 1, fc = over(f, sbg);
              const ratio = (Math.max(L(fc), L(sbg)) + .05) / (Math.min(L(fc), L(sbg)) + .05), big = parseFloat(cs.fontSize) * k >= 18.6;
              if (ratio < (big ? 3 : 4.5)) out.push(n + ' low contrast ' + ratio.toFixed(2) + ': ' + desc(e)); } });
        });
      }
    } }
  return {out: [...new Set(out)], info: [...new Set(info)]};
}"""

def run(pw, w, h):
    m = w < 600; tag = '%dx%d' % (w, h)
    br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
    ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2 if m else 1, is_mobile=m, has_touch=m)
    p = ctx.new_page()
    p.on('console', lambda x: x.type == 'error' and problems.append('[%s] console: %s' % (tag, x.text)))
    p.on('pageerror', lambda e: problems.append('[%s] pageerror: %s' % (tag, e)))
    print('== layout %s' % tag, flush=True)
    def check(name, settle=650):
        p.wait_for_timeout(settle)
        r = p.evaluate(CHECK, name)
        for x in r['out']: problems.append('[%s] %s: %s' % (tag, name, x)); print('  ✗ %s: %s' % (name, x), flush=True)
        if a.v:
            for x in r['info']: print('    · %s: %s' % (name, x))
        notes.extend('[%s] %s: %s' % (tag, name, x) for x in r['info'])
        if not r['out']: print('  ✓ %s' % name, flush=True)
        if a.shots: os.makedirs(a.shots, exist_ok=True); p.screenshot(path=os.path.join(a.shots, 'layout-%s-%s.png' % (tag, name)))
    def tab(t):
        # brands with a Community tab keep the Wishlist behind a heart in the Home header
        if t == 'wishlist' and not p.locator('#tabbar button[data-tab="wishlist"]').count():
            if not p.locator('.view.top .hw-btn').count(): p.click('#tabbar button[data-tab="home"]'); p.wait_for_timeout(500)
            p.click('.view.top .hw-btn'); return
        p.click('#tabbar button[data-tab="%s"]' % t)
    top = lambda s: p.locator('.view.top ' + s).first
    p.goto(URL + '?nosplash', wait_until='networkidle'); p.wait_for_timeout(900)
    check('welcome'); p.click('#wlSkip')
    check('home')
    p.evaluate("document.querySelector('.view.top').scrollTop = 900"); check('home-scrolled')
    p.evaluate("(() => { const v = document.querySelector('.view.top'); v.scrollTop = v.scrollHeight; })()"); check('home-bottom')
    tab('shop'); check('shop-product')
    p.click('.view.top .seg button[data-seg="edits"]'); check('shop-collections')
    p.click('.view.top .seg button[data-seg="cats"]'); p.wait_for_timeout(400)
    top('.cat-row').click(); check('collection')
    top('[data-sort="low"]').click(); check('collection-sorted')
    top('.size-filter').click(); check('size-sheet')
    p.locator('#sheet .size').first.click(); p.click('#szSave'); check('collection-my-size')
    top('.pcard').click(); check('pdp')
    p.evaluate("document.querySelector('.view.top .pscroll').scrollTop = 600"); check('pdp-scrolled')
    sold = p.locator('.view.top .size.out')
    if sold.count(): sold.first.click(); check('pdp-sold-out-size', 300)
    p.locator('.view.top .size:not(.out)').first.click(); p.click('#addBtn'); check('added-sheet', 1200)
    p.click('#goBag'); check('bag')
    p.click('#promoAdd'); check('bag-app10')
    p.click('#checkout'); check('checkout')
    p.evaluate("document.querySelector('#sheet').scrollTop = 999"); check('checkout-bottom', 300)
    p.click('#payNow'); check('order-confirmed', 1200)
    p.click('#contShop'); p.wait_for_timeout(500)
    tab('bag'); check('bag-empty')
    tab('wishlist'); check('wishlist-empty')
    tab('home'); p.wait_for_timeout(400); top('.hscroll .heart').click(); tab('wishlist'); check('wishlist')
    tab('home'); p.wait_for_timeout(400); top('[data-act="search"]').click(); check('search')
    p.fill('#sq', 'jacket'); check('search-results')
    p.fill('#sq', 'zzzz'); check('search-none')
    top('[data-act="back"]').click()
    tab('drops'); check('drops')
    if p.locator('#tabbar button[data-tab="community"]').count():
        tab('community'); p.wait_for_timeout(300)
        if p.locator('.view.top .ev-card').count():
            check('community-events')
            p.evaluate("document.querySelector('.view.top').scrollTop = 560"); check('community-events-cards')
            p.evaluate("(() => { const v = document.querySelector('.view.top'); v.scrollTop = v.scrollHeight; })()"); check('community-events-bottom')
            p.evaluate("document.querySelector('.view.top').scrollTop = 0"); top('.ev-cta').click(); check('community-event-browser')
            p.click('#brDone'); p.wait_for_timeout(300)
        if p.locator('.view.top .seg button[data-seg="forum"]').count(): top('.seg button[data-seg="forum"]').click()
        if p.locator('.view.top .fm-compose').count() or p.locator('.view.top .seg button[data-seg="forum"]').count():
            p.wait_for_timeout(500); check('community-forum')
            p.evaluate("document.querySelector('.view.top').scrollTop = 99999"); check('community-forum-bottom')
            p.evaluate("document.querySelector('.view.top').scrollTop = 0"); p.wait_for_timeout(300)
            top('.fm-chips .chip:nth-child(3)').click(); check('community-forum-topic')
            top('.fm-chips .chip').click(); p.wait_for_timeout(400)
            top('.thread h3').click(); check('community-thread')
            p.fill('.view.top #replyIn', 'Count me in for Sunday'); top('#replySend').click(); check('community-thread-replied', 900)
            top('[data-act="back"]').click(); p.wait_for_timeout(500)
            top('.fm-compose').click(); check('community-compose')
            p.click('#sheet [data-act="close"]'); p.wait_for_timeout(400)
        tab('home'); p.wait_for_timeout(400)
        p.evaluate("(() => { const v = document.querySelector('.view.top'), t = v.querySelector('.comm-teaser'); if (t) v.scrollTop = t.offsetTop - 300; })()"); check('home-community-teaser')
        p.evaluate("window.__app.Demo.community()"); check('community-push', 900)
        p.click('#push'); check('community-push-opened', 900)
        p.evaluate("window.__app.switchTab('home')"); p.wait_for_timeout(400)
    tab('account'); check('account')
    p.evaluate("document.querySelector('.view.top').scrollTop = 99999"); check('account-bottom')
    for d in p.locator('.view.top .acct-acc summary').all(): d.click()
    p.locator('.view.top [data-page]').first.click(); check('browser')
    p.click('#brDone'); p.wait_for_timeout(300)
    p.evaluate("document.querySelector('.view.top').scrollTop = 0")
    top('[data-act="login"]').click(); check('login')
    top('[data-act="recover"]').click(); check('recover')
    top('[data-act="back"]').click(); p.wait_for_timeout(400); top('[data-act="signup"]').click(); check('signup')
    top('[data-act="back"]').click(); p.wait_for_timeout(400); top('[data-act="back"]').click(); p.wait_for_timeout(400)
    top('[data-act="rewards"]').click(); check('rewards')
    if m: p.click('#demoFab'); check('demo-sheet'); p.click('#sheetBackdrop'); p.wait_for_timeout(400)
    p.evaluate("window.__app.Demo.drop()"); check('push', 900)
    br.close()

with sync_playwright() as pw:
    for s in a.sizes.split(','):
        w, h = map(int, s.split('x')); run(pw, w, h)
print('\nlayout: %d problem(s), %d note(s)' % (len(problems), len(notes)))
for x in problems: print(' -', x)
sys.exit(1 if problems else 0)
