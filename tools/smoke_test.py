"""Headless smoke test for a built brand app. Usage: python3 tools/smoke_test.py SLUG [--base URL] [--shots DIR]
Clicks through every tab and feature at phone (390x844) and desktop (1280x720, 1440x800, 1920x1080) sizes, reports console errors,
failed requests and broken images, and saves screenshots. Desktop also checks the three-column stage: the "Why an app" stats column
(4 boxes matching BRAND.stats, source links valid and opening in a new tab, hover + fade-in, nothing clipped or overlapping, phone centred)."""
import sys, os, argparse, json, re, urllib.request, urllib.error
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('--base', default='http://localhost:8765'); ap.add_argument('--shots')
a = ap.parse_args()
URL = '%s/%s/' % (a.base.rstrip('/'), a.slug)
SH = a.shots or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', a.slug + '-shots')
os.makedirs(SH, exist_ok=True)
problems, log = [], []
def ok(m): log.append('  ✓ ' + m); print('  ✓ ' + m, flush=True)
def bad(m): problems.append(m); print('  ✗ ' + m, flush=True)

STATS_JS = r"""() => {
  const why = document.querySelector('.why'), B = window.BRAND, want = (B.stats && B.stats.items) || [];
  const rect = e => { const r = e.getBoundingClientRect(); return {l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height}; };
  const shown = e => e && getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().width > 0;
  const cols = {pitch: document.querySelector('.pitch'), device: document.querySelector('#device'), why};
  const R = {}; for (const k in cols) if (shown(cols[k])) R[k] = rect(cols[k]);
  const stats = why ? [...why.querySelectorAll('.stat')].map(s => {
    const q = c => s.querySelector(c), a = q('a.stat-src'), sr = s.getBoundingClientRect();
    const spill = [...s.querySelectorAll('*')].filter(e => shown(e) && !e.closest('svg')).some(e => { const r = e.getBoundingClientRect(); return r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1; });
    const clipped = [...s.querySelectorAll('p,a')].some(e => shown(e) && (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 2) && getComputedStyle(e).overflow !== 'visible');
    return {num: (q('.stat-num') || {}).textContent, label: (q('.stat-label') || {}).textContent, copy: (q('.stat-copy') || {}).textContent, copyShown: shown(q('.stat-copy')),
            src: a ? a.textContent : null, href: a ? a.getAttribute('href') : null, target: a ? a.target : null, rel: a ? a.rel : null, spill, clipped, rect: rect(s),
            anim: getComputedStyle(s).animationName, font: getComputedStyle(q('.stat-num')).fontFamily};
  }) : [];
  return {R, stats, want, heading: why ? why.querySelector('.why-h').textContent : null, parent: why ? why.parentElement.className : null,
          vw: innerWidth, vh: innerHeight, scrollH: document.documentElement.scrollHeight, font: getComputedStyle(document.documentElement).getPropertyValue('--font').trim().replace(/['"]/g, ''),
          credit: (() => { const c = document.querySelector('.credit'); if (!shown(c)) return null; const g = document.createRange(); g.selectNodeContents(c); const r = g.getBoundingClientRect(); return {l: r.left, t: r.top, r: r.right, b: r.bottom}; })()};
}"""

def check_stats(p, tag, w, h, shot):
    """Desktop three-column stage + "Why an app" stats column (>=1100 wide: own column right of a centred phone; 1001-1099: under the pitch)."""
    d = p.evaluate(STATS_JS)
    if w <= 1000:
        (ok if 'why' not in d['R'] and 'pitch' not in d['R'] else bad)('%s: phone only, no pitch/stats columns' % tag if 'why' not in d['R'] and 'pitch' not in d['R'] else '[%s] side columns visible on a phone-only width: %s' % (tag, list(d['R'])))
        return
    want = d['want']
    if len(d['stats']) == 4 and len(want) == 4: ok('stats: 4 boxes under "%s"' % d['heading'])
    else: bad('[%s] stats: %d boxes rendered, %d in BRAND.stats (want 4)' % (tag, len(d['stats']), len(want)))
    for i, (s, x) in enumerate(zip(d['stats'], want)):
        n = i + 1
        same = (s['num'], s['label'], s['copy'], s['src'], s['href']) == (x.get('num'), x.get('label'), x.get('copy'), x.get('source'), x.get('url'))
        link = bool(s['href'] and re.match(r'^https://[a-z0-9.-]+\.[a-z]{2,}/\S*$', s['href'])) and s['target'] == '_blank' and 'noopener' in (s['rel'] or '')
        if not same: bad('[%s] stat %d text differs from config: %s vs %s' % (tag, n, s, x))
        if not link: bad('[%s] stat %d source link invalid (href %r, target %r, rel %r)' % (tag, n, s['href'], s['target'], s['rel']))
        if s['spill'] or s['clipped']: bad('[%s] stat %d content clipped/spilling out of its box' % (tag, n))
        if s['anim'] != 'statIn': bad('[%s] stat %d has no fade-in (animation %r)' % (tag, n, s['anim']))
        if d['font'] and d['font'] != '-apple-system' and d['font'] not in s['font'].replace('"', '').replace("'", ''): bad('[%s] stat %d not in the brand font: %s' % (tag, n, s['font']))
        if same and link and not s['spill'] and not s['clipped']: ok('stat %d: %s %s, source "%s" -> %s (new tab)%s' % (n, s['num'], s['label'], s['src'], s['href'], '' if s['copyShown'] else ' [compact: copy as tooltip]'))
    # boxes must not overlap each other
    rs = [s['rect'] for s in d['stats']]
    ov = [(i + 1, j + 1) for i in range(len(rs)) for j in range(i + 1, len(rs)) if min(rs[i]['r'], rs[j]['r']) - max(rs[i]['l'], rs[j]['l']) > 1 and min(rs[i]['b'], rs[j]['b']) - max(rs[i]['t'], rs[j]['t']) > 1]
    (ok if not ov else bad)('stat boxes do not overlap' if not ov else '[%s] stat boxes overlap: %s' % (tag, ov))
    # every column inside the window, columns + credit line never overlap, phone fully visible
    R = dict(d['R']); 
    if d['credit']: R['credit'] = d['credit']
    out = [k for k, r in R.items() if r['l'] < -1 or r['t'] < -1 or r['r'] > w + 1 or r['b'] > h + 1]
    ks = list(R); hits = [(a, b) for i, a in enumerate(ks) for b in ks[i + 1:] if min(R[a]['r'], R[b]['r']) - max(R[a]['l'], R[b]['l']) > 1 and min(R[a]['b'], R[b]['b']) - max(R[a]['t'], R[b]['t']) > 1
                          and not ({a, b} == {'pitch', 'why'} and d['parent'].startswith('col col-l'))]
    if d['parent'] and 'col-l' in d['parent'] and 'pitch' in R and 'why' in R and R['why']['t'] < R['pitch']['b'] - 1: hits.append(('pitch', 'why'))
    good = not out and not hits and d['scrollH'] <= h + 1
    (ok if good else bad)('%dx%d: %s fit the window, no overlaps, no page scroll' % (w, h, '/'.join(R)) if good else '[%s] stage layout: outside %s, overlaps %s, scrollHeight %s' % (tag, out, hits, d['scrollH']))
    if w >= 1100:
        dv, pt, wy = R.get('device'), R.get('pitch'), R.get('why')
        mid = (dv['l'] + dv['r']) / 2 if dv else 0
        three = dv and pt and wy and 'col-r' in d['parent'] and pt['r'] <= dv['l'] and wy['l'] >= dv['r'] and abs(mid - w / 2) <= 2
        (ok if three else bad)('three columns: pitch | phone (centre %.0f of %d) | stats' % (mid, w) if three else '[%s] not a centred three-column layout: %s parent=%s' % (tag, R, d['parent']))
        gl, gr = (dv['l'] - pt['r'], wy['l'] - dv['r']) if three else (0, 0)
        if three and abs(gl - gr) > 2: bad('[%s] side gaps unequal: %.0f vs %.0f' % (tag, gl, gr))
    else:
        (ok if 'col-l' in (d['parent'] or '') else bad)('narrow desktop: stats sit under the pitch' if 'col-l' in (d['parent'] or '') else '[%s] stats not under the pitch below 1100px' % tag)
    if d['stats']:
        # hover: box lifts and brightens
        p.hover('.why .stat >> nth=1'); p.wait_for_timeout(500)
        hv = p.evaluate("() => { const s = document.querySelectorAll('.why .stat')[1], cs = getComputedStyle(s); return {tf: cs.transform, bg: cs.backgroundColor}; }")
        (ok if hv['tf'] != 'none' and hv['bg'] in ('rgb(255, 255, 255)', 'rgba(255, 255, 255, 1)') else bad)('stat hover lifts + brightens (%s)' % hv['tf'] if hv['tf'] != 'none' else '[%s] stat hover state missing: %s' % (tag, hv))
        shot('00-stats-hover'); p.mouse.move(2, 2); p.wait_for_timeout(300)
        # a source link opens in a new tab (target page stubbed, nothing loaded from the network)
        url = d['stats'][0]['href']
        p.context.route(url, lambda r: r.fulfill(status=200, content_type='text/html', body='<title>stub</title>'))
        try:
            with p.context.expect_page(timeout=5000) as pg: p.click('.why .stat >> nth=0 >> a.stat-src')
            np = pg.value; np.wait_for_load_state(); (ok if np.url == url else bad)('source link opens in a new tab: %s' % np.url if np.url == url else '[%s] new tab opened %s, want %s' % (tag, np.url, url)); np.close()
        except Exception as e: bad('[%s] source link did not open a new tab: %s' % (tag, e))

def check_stat_links(items):
    """Each source URL answers (2xx/3xx). 401/403/429 are bot walls on publisher/vendor sites (the page loads in a browser): noted, not failed."""
    for x in items:
        u = x.get('url')
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36', 'Accept': 'text/html'}), timeout=25)
            ok('source link live: HTTP %d %s' % (r.status, u))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429): ok('source link reachable, bot wall HTTP %d (not a dead link): %s' % (e.code, u))
            else: bad('source link broken: HTTP %d %s' % (e.code, u))
        except Exception as e: bad('source link unreachable: %s (%s)' % (u, e))

def run(pw, w, h, tag):
    # real desktop Chrome autoplay policy (no --autoplay-policy override): muted autoplay must work on its own
    br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2 if w < 600 else 1, has_touch=w < 600, is_mobile=w < 600)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=a.base)
    p = ctx.new_page()
    p.on('console', lambda m: m.type == 'error' and bad('[%s] console: %s' % (tag, m.text)))
    p.on('pageerror', lambda e: bad('[%s] pageerror: %s' % (tag, e)))
    p.on('requestfailed', lambda r: ('youtube' not in r.url and r.failure != 'net::ERR_ABORTED') and bad('[%s] request failed: %s %s' % (tag, r.url, r.failure)))
    p.on('response', lambda r: r.status >= 400 and bad('[%s] HTTP %d %s' % (tag, r.status, r.url)))
    print('== %s %dx%d' % (tag, w, h))
    shot = lambda n: p.screenshot(path=os.path.join(SH, '%s-%s.png' % (tag, n)))
    top = lambda: p.locator('.view.top')
    def broken_imgs():
        n = p.evaluate("""() => [...document.querySelectorAll('img')].filter(i => i.complete && i.getBoundingClientRect().width > 0 && i.naturalWidth === 0).map(i => i.src)""")
        for s in n: bad('[%s] broken image: %s' % (tag, s))
    def tab(t):
        p.click('#tabbar button[data-tab="%s"]' % t); p.wait_for_timeout(500)
    def to_root():
        # the mobile Demo button is tucked away on product/auth screens and while a toast shows
        if p.locator('#tabbar.hidden').count(): p.evaluate("window.__app.switchTab('home')"); p.wait_for_timeout(500)
        p.wait_for_function("() => !document.querySelector('#app').classList.contains('toasting')", timeout=4000)
    def scroll_lazy():
        p.evaluate("""async () => { const v = document.querySelector('.view.top'); for (let y = 0; y < v.scrollHeight; y += 500){ v.scrollTop = y; await new Promise(r => setTimeout(r, 120)); } v.scrollTop = 0; }""")
        p.wait_for_timeout(1500)

    def assert_hero_playing(label):
        # clock advancing AND visibly rendered: opaque all the way up, poster faded, nothing covering it, pixels changing
        vi = p.evaluate("""async () => { const v = document.querySelector('.view.top .hero video'); if (!v) return null;
            const t0 = v.currentTime; await new Promise(r => setTimeout(r, 900));
            let op = 1, e = v, hidden = false; while (e && e !== document.documentElement) { const cs = getComputedStyle(e); op *= +cs.opacity; if (cs.visibility !== 'visible' || cs.display === 'none') hidden = true; e = e.parentElement; }
            const r = v.getBoundingClientRect(), vh = innerHeight, vw = innerWidth;
            // sample the part of the hero actually on screen, below the (deliberately clear) menu band
            const hb = Math.max(0, ...[...document.querySelectorAll('.view.top .home-head, .view.top .home-band, .view.top .topbar')].map(e => e.getBoundingClientRect().bottom));
            const y0 = Math.max(r.top, hb, 0) + 10, y1 = Math.min(r.bottom, vh) - 70;
            const pts = y1 - y0 < 40 ? [] : [[.5,.2],[.3,.5],[.7,.5]].map(([fx, fy]) => [r.left + r.width*fx, y0 + (y1 - y0)*fy]).filter(([x]) => x > 0 && x < vw);
            if (!pts.length) return {offscreen: true, rect: [r.left, r.top, r.width, r.height].map(Math.round)};
            const covered = pts.map(([x, y]) => document.elementFromPoint(x, y)).filter(el => !el || !el.closest('.hero') || (el.closest('.hero') !== v.closest('.hero'))).map(el => el ? el.tagName + '.' + el.className : 'none');
            const poster = v.parentElement.querySelector('.poster');
            return {paused: v.paused, ready: v.readyState, advanced: +(v.currentTime - t0).toFixed(2), t: +v.currentTime.toFixed(2), op: +op.toFixed(2), hidden,
                    posterOp: poster ? +getComputedStyle(poster).opacity : 0, covered, rect: [r.left, r.top, r.width, r.height].map(Math.round), band: Math.max(Math.round(hb), 0), vw: v.videoWidth}; }""")
        if not vi: bad('[%s] %s: no hero video' % (tag, label)); return
        if vi.get('offscreen'):
            p.evaluate("document.querySelector('.view.top').scrollTo(0, 0)"); p.wait_for_timeout(500); return assert_hero_playing(label + ' (scrolled to top)')
        playing = (not vi['paused']) and vi['advanced'] > 0.2 and vi['ready'] >= 2
        visible = vi['op'] >= 0.99 and not vi['hidden'] and vi['posterOp'] < 0.05 and not vi['covered'] and vi['vw'] > 0
        # pixels: two captures of the visible hero area ~600ms apart must differ (catches a frozen or blank layer)
        x, y, w_, h_ = vi['rect']; y0 = max(y, vi['band']); h_ = min(y + h_, p.viewport_size['height']) - 70 - y0
        clip = {'x': x + w_ * 0.15, 'y': y0 + 10, 'width': w_ * 0.7, 'height': max(h_ - 10, 10)}
        import hashlib
        a_ = hashlib.md5(p.screenshot(clip=clip, animations='allow')).hexdigest(); p.wait_for_timeout(600)
        b_ = hashlib.md5(p.screenshot(clip=clip, animations='allow')).hexdigest()
        moving = a_ != b_
        good = playing and visible and moving
        (ok if good else bad)(('%s: hero playing + visible (advanced %.2fs, opacity %.2f, poster %.2f, frames changing)' % (label, vi['advanced'], vi['op'], vi['posterOp'])) if good
                              else '[%s] %s: hero not playing/visible: playing=%s visible=%s pixels-changing=%s %s' % (tag, label, playing, visible, moving, vi))

    p.goto(URL + '?nosplash', wait_until='networkidle'); p.wait_for_timeout(1200)
    BR = p.evaluate("(() => { const B = window.BRAND; return {video: !!(B.home && B.home.hero && B.home.hero.video), reviews: !!(B.reviews && B.reviews.score), about: !!(B.pages && B.pages.about && B.pages.about.length), sale: Object.values(B.products).some(p => p.cp > p.p)}; })()")
    if not BR['video']:
        # still-image hero: the poster must be loaded and visible instead
        def assert_hero_playing(label):
            r = p.evaluate("() => { const i = document.querySelector('.view.top .hero img.poster'); if (!i) return null; const b = i.getBoundingClientRect(); return {ok: i.complete && i.naturalWidth > 0, op: +getComputedStyle(i).opacity, w: Math.round(b.width), h: Math.round(b.height), video: !!document.querySelector('.view.top .hero video')}; }")
            good = r and r['ok'] and r['op'] > .95 and r['w'] > 200 and not r['video']
            (ok if good else bad)(('%s: still hero image shown (no video on this brand) %s' % (label, r)) if good else '[%s] %s: hero image: %s' % (tag, label, r))
    # 1 welcome
    if p.locator('#welcome.show').count(): ok('welcome pop-up on open'); shot('01-welcome')
    else: bad('[%s] welcome did not show on open' % tag)
    p.click('#wlCode'); p.wait_for_timeout(400)
    if 'copied' in p.inner_text('#toast').lower(): ok('APP10 tap-to-copy')
    else: bad('[%s] copy toast missing' % tag)
    p.click('#wlGo'); p.wait_for_timeout(600)
    check_stats(p, tag, w, h, shot)
    assert_hero_playing('initial load')
    # 2 home
    t = p.text_content('.view.top')
    for need in ['New In']:
        (ok if need.lower() in t.lower() else bad)(('home has "%s"' % need) if need.lower() in t.lower() else '[%s] home missing "%s"' % (tag, need))
    if 'in stock in your size' in t.lower() or p.locator('.view.top .size-cta').count():
        bad('[%s] home still shows in-stock-in-your-size card/rail' % tag)
    else: ok('home has no in-stock-in-your-size card/rail')
    if p.locator('.view.top #dropSwitch').count() or p.locator('.view.top .drop-banner').count():
        bad('[%s] home still shows drop alerts card' % tag)
    else: ok('home has no drop alerts card')
    if p.locator('.view.top .next-drop').count() or 'next drop, app early access' in t.lower(): bad('[%s] home still shows the next-drop countdown card' % tag)
    else: ok('home has no next-drop countdown card')
    if p.locator('.view.top .rewards-mini').count() or '1,250 pts' in t: bad('[%s] home still shows the rewards points card' % tag)
    else: ok('home has no rewards points card (it lives on Account)')
    # review block sits near the bottom: after the product rails and categories, before the About footer
    order = p.evaluate("""() => { const v = document.querySelector('.view.top'); const kids = [...v.children];
        const at = s => { const e = v.querySelector(s); return e ? kids.indexOf(e.closest('.view.top > *')) : -1; };
        return {proof: at('.proof'), cats: at('.cat-grid'), rails: Math.max(...[...v.querySelectorAll('.hscroll')].map(e => kids.indexOf(e.closest('.view.top > *')))), about: at('.about'), hero: at('.hero')}; }""")
    if not BR['reviews']: (ok if order['proof'] < 0 else bad)('no review score on the site: review block left out' if order['proof'] < 0 else '[%s] review block shown without a review score' % tag)
    elif order['proof'] < 0: bad('[%s] no review block on home' % tag)
    elif order['proof'] > order['cats'] and order['proof'] > order['rails'] and order['proof'] < order['about']: ok('review block near the bottom (after rails + categories, above About): %s' % order)
    else: bad('[%s] review block in the wrong place: %s' % (tag, order))
    # hero video
    vi = None if not BR['video'] else p.evaluate("""async () => { const v = document.querySelector('.view.top .hero video'); if (!v) return null;
        const t0 = v.currentTime; let frames = 0; const t = performance.now();
        if (v.requestVideoFrameCallback) { const cb = () => { frames++; if (performance.now() - t < 2000) v.requestVideoFrameCallback(cb); }; v.requestVideoFrameCallback(cb); }
        await new Promise(r => setTimeout(r, 2100)); const r = v.getBoundingClientRect(), cs = getComputedStyle(v);
        return {autoplay: v.autoplay, muted: v.muted, loop: v.loop, playsinline: v.hasAttribute('playsinline'), preload: v.preload, fit: cs.objectFit,
                src: v.currentSrc.split('/').pop(), vw: v.videoWidth, vh: v.videoHeight, cw: r.width, ch: r.height, dpr: devicePixelRatio, paused: v.paused,
                ready: v.readyState, advanced: +(v.currentTime - t0).toFixed(2), fps: +(frames / 2).toFixed(1)}; }""")
    if not vi: (ok if not BR['video'] else bad)('still-image hero (brand has no video)' if not BR['video'] else '[%s] no hero video' % tag)
    else:
        flags_ok = vi['autoplay'] and vi['muted'] and vi['loop'] and vi['playsinline'] and vi['preload'] == 'auto' and vi['fit'] == 'cover'
        playing = not vi['paused'] and vi['ready'] >= 3 and vi['advanced'] > 1
        scale = max(vi['cw'] / vi['vw'], vi['ch'] / vi['vh']) if vi['vw'] else 0
        (ok if flags_ok else bad)(('hero video attrs ok: %s' % vi) if flags_ok else '[%s] hero video attributes: %s' % (tag, vi))
        (ok if playing else bad)('hero video playing (%.1fs advanced in 2.1s, %s fps presented)' % (vi['advanced'], vi['fps']) if playing else '[%s] hero video not playing smoothly: %s' % (tag, vi))
        (ok if scale <= 1.0 else bad)('hero video not upscaled: %dx%d source drawn at %dx%d CSS px (%.2fx; %.2fx in device px at DPR %g)' % (vi['vw'], vi['vh'], vi['cw'], vi['ch'], scale, scale * vi['dpr'], vi['dpr'])
                                      if scale <= 1.0 else '[%s] hero video upscaled %.2fx in CSS px' % (tag, scale))
    if p.locator('.marquee').count(): ok('marquee: ' + p.locator('.marquee').first.inner_text()[:120].replace('\n', ' | '))
    else: bad('[%s] no marquee' % tag)
    tb = p.evaluate(r"""() => {
        const b = document.querySelector('.view.top .home-band');
        const hero = document.querySelector('.view.top .hero');
        const m = hero && hero.querySelector('.marquee');
        const t = b && b.querySelector('.topbar');
        const copy = hero && hero.querySelector('.hero-copy');
        if (!b || !m || !t || !hero) return {missing:true, b:!!b, m:!!m, t:!!t, hero:!!hero};
        const ms = getComputedStyle(m), ts = getComputedStyle(t), bs = getComputedStyle(b);
        const mq = ms.backgroundColor.match(/rgba\((\d+), (\d+), (\d+), ([\d.]+)\)/);
        const hb = hero.getBoundingClientRect(), mb = m.getBoundingClientRect(), cb = copy ? copy.getBoundingClientRect() : null;
        const left = t.querySelector('.icon-btn');
        return {band: bs.backgroundColor, mq: ms.backgroundColor, tb: ts.backgroundColor,
                mqAlpha: mq && +mq[4], mask: /gradient/.test(ms.maskImage || ms.webkitMaskImage),
                tbColor: ts.color,
                perksAtBottom: Math.abs(mb.bottom - hb.bottom) <= 2,
                copyAbove: !cb || cb.bottom <= mb.top + 1,
                bandHasMarquee: !!b.querySelector('.marquee'),
                leftAccount: left && left.getAttribute('data-act')==='tab' && left.getAttribute('data-v')==='account',
                hasBell: !!t.querySelector('[data-act="notifs"]')}; }""")
    clear = tb and tb.get('band') in ('rgba(0, 0, 0, 0)', 'transparent') and tb.get('tb') in ('rgba(0, 0, 0, 0)', 'transparent')
    strip = tb and tb.get('mqAlpha') and 0.35 <= tb['mqAlpha'] <= 0.55
    if clear and strip and tb.get('mask') and tb.get('tbColor') == 'rgb(255, 255, 255)' and tb.get('perksAtBottom') and tb.get('copyAbove') and not tb.get('bandHasMarquee'):
        ok('home top: clear menu over hero; perks strip at hero bottom %s edge-faded' % tb['mq'])
    else: bad('[%s] home top/hero perks: %s' % (tag, tb))
    if tb and tb.get('leftAccount') and not tb.get('hasBell'): ok('home header Account icon (no bell)')
    else: bad('[%s] home header Account/bell: %s' % (tag, {k: tb.get(k) for k in ('leftAccount','hasBell')} if tb else tb))
    if p.locator('.proof').count(): ok('review block: ' + p.locator('.proof').first.inner_text().replace('\n', ' '))
    shot('02-home')
    scroll_lazy(); broken_imgs()
    p.evaluate("document.querySelector('.view.top').scrollTop = 700"); p.wait_for_timeout(600); shot('03-home-scrolled')
    p.evaluate("(() => { const v = document.querySelector('.view.top'), e = v.querySelector('.proof'); if (e) v.scrollTop = e.offsetTop - v.clientHeight * 0.45; })()"); p.wait_for_timeout(800); shot('03b-home-trustpilot')
    # 2a Instagram feed: directly below the review block, header + Follow, 3x3 square grid, every tile an instagram.com post in a new tab
    ig_posts = p.evaluate("() => ((window.BRAND.instagram || {}).posts || []).length")
    if not ig_posts:
        (ok if not p.locator('.view.top .ig-feed').count() else bad)('no Instagram posts in brand data, feed hidden' if not p.locator('.view.top .ig-feed').count() else '[%s] Instagram feed shown with no posts' % tag)
    else:
        p.evaluate("(() => { const v = document.querySelector('.view.top'), e = v.querySelector('.ig-feed'); if (e) v.scrollTop = e.offsetTop + e.offsetHeight - v.clientHeight + 120; })()"); p.wait_for_timeout(900)  # bottom of the section just above the tab bar, clear of the sticky header
        ig = p.evaluate(r"""() => {
            const v = document.querySelector('.view.top'), s = v.querySelector('.ig-feed'), pr = v.querySelector('.proof');
            if (!s) return {missing: true};
            const D = window.BRAND.instagram, posts = D.posts.slice(0, 9);
            const vr = v.getBoundingClientRect(), sr = s.getBoundingClientRect();
            const tiles = [...s.querySelectorAll('.ig-grid > a.ig-tile')];
            const rects = tiles.map(t => t.getBoundingClientRect());
            const fol = s.querySelector('.ig-follow'), fr = fol && fol.getBoundingClientRect();
            const h = s.querySelector('.sec-head'), hr = h.getBoundingClientRect();
            const bad = [];
            tiles.forEach((t, i) => {
                const u = t.getAttribute('href') || '';
                let url = null; try { url = new URL(u); } catch (e) {}
                if (!url || url.protocol !== 'https:' || !/^(www\.)?instagram\.com$/.test(url.hostname) || !/^\/(p|reel|tv)\/[A-Za-z0-9_-]+\/?$/.test(url.pathname)) bad.push('tile ' + (i+1) + ' href ' + u);
                if (t.target !== '_blank') bad.push('tile ' + (i+1) + ' target ' + t.target);
                if (!/noopener/.test(t.rel)) bad.push('tile ' + (i+1) + ' rel ' + t.rel);
                if (posts[i] && u !== posts[i].url) bad.push('tile ' + (i+1) + ' order: ' + u + ' != ' + posts[i].url);
                const im = t.querySelector('img');
                if (!im || !im.complete || !im.naturalWidth) bad.push('tile ' + (i+1) + ' image not loaded');
                const want = posts[i] && (posts[i].type === 'reel' || posts[i].type === 'carousel') ? 1 : 0;
                const b = t.querySelector('.ig-badge');
                if (!!b !== !!want) bad.push('tile ' + (i+1) + ' badge ' + (!!b) + ' for ' + (posts[i] || {}).type);
                if (b) { const br = b.getBoundingClientRect(), r = rects[i]; if (br.right > r.right + .5 || br.top < r.top - .5 || br.width > r.width * .3 || br.left < r.left + r.width / 2) bad.push('tile ' + (i+1) + ' badge not small in top-right corner'); }
                const r = rects[i]; if (Math.abs(r.width - r.height) > 1) bad.push('tile ' + (i+1) + ' not square ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
                if (r.left < sr.left - .5 || r.right > sr.right + .5) bad.push('tile ' + (i+1) + ' overflows section');
            });
            const cols = new Set(rects.map(r => Math.round(r.left))).size, rows = new Set(rects.map(r => Math.round(r.top))).size;
            if (tiles.length !== Math.min(9, posts.length)) bad.push('tiles ' + tiles.length + ' != posts ' + posts.length);
            if (posts.length >= 9 && (cols !== 3 || rows !== 3)) bad.push('grid ' + cols + 'x' + rows);
            if (!fol || fol.getAttribute('href') !== (D.url || 'https://www.instagram.com/' + D.handle + '/') || fol.target !== '_blank') bad.push('follow button ' + (fol && fol.outerHTML));
            if (fr && (fr.right > hr.right + .5 || fr.bottom > hr.bottom + .5 || fr.top < hr.top - .5)) bad.push('follow button outside header');
            const head = h.innerText;
            if (head.indexOf('@' + D.handle) < 0) bad.push('header missing @' + D.handle);
            if (D.followers && head.indexOf(D.followers + ' followers') < 0) bad.push('header missing followers');
            if (sr.left < vr.left - .5 || sr.right > vr.right + .5 || v.scrollWidth > v.clientWidth) bad.push('horizontal overflow');
            const kids = [...v.children], next = pr && pr.nextElementSibling;
            // When the brand has a review block, Instagram sits directly under it; with no reviews, proofHTML() is empty and the feed still sits above About.
            if (pr) { if (next !== s) bad.push('not directly below the review block (next after .proof: ' + (next && next.className) + ')'); }
            else {
              const about = v.querySelector('.about');
              if (about && s.nextElementSibling !== about) bad.push('with no review block, ig-feed should sit above About (next: ' + (s.nextElementSibling && s.nextElementSibling.className) + ')');
            }
            // hidden when the brand has no posts
            const keep = D.posts; D.posts = []; const empty = window.__app.igHTML(); D.posts = keep;
            if (empty !== '') bad.push('igHTML not empty with no posts');
            return {bad, n: tiles.length, cols, rows, tile: rects[0] && Math.round(rects[0].width), head: head.replace(/\n+/g, ' | ')};
        }""")
        if ig.get('missing'): bad('[%s] no Instagram feed on Home (brand has %d posts)' % (tag, ig_posts))
        elif ig['bad']:
            for x in ig['bad']: bad('[%s] instagram: %s' % (tag, x))
        else: ok('instagram feed below reviews: %d tiles %dx%d (%dpx), valid instagram.com hrefs, target=_blank, badges ok, hidden with no posts; header "%s"' % (ig['n'], ig['cols'], ig['rows'], ig['tile'], ig['head']))
        # press/hover state is visible
        t0 = p.locator('.view.top .ig-tile').first
        if w >= 1000:
            t0.hover(); p.wait_for_timeout(600)
            hv = p.evaluate("() => { const t = document.querySelector('.view.top .ig-tile'); return {tr: getComputedStyle(t.querySelector('img')).transform, ov: getComputedStyle(t, '::after').backgroundColor}; }")
            (ok if hv['tr'] not in ('none', '') else bad)('instagram tile hover state: %s' % hv if hv['tr'] not in ('none', '') else '[%s] instagram tile has no hover state: %s' % (tag, hv))
            p.mouse.move(5, 5); p.wait_for_timeout(600)
        p.locator('.view.top .ig-feed').screenshot(path=os.path.join(SH, '%s-25-instagram.png' % tag))
        if tag == 'mobile': p.locator('.view.top .ig-feed').screenshot(path=os.path.join(SH, 'instagram.png'))
    p.evaluate("document.querySelector('.view.top').scrollTop = 0"); p.wait_for_timeout(300)
    # 2b hero video resume: tab bar Home↔Shop, and Home→Shop→product→back→Home
    tab('shop'); p.wait_for_timeout(500)
    tab('home'); p.wait_for_timeout(700)
    assert_hero_playing('after tab bar Home←Shop')
    tab('shop'); p.wait_for_timeout(400)
    p.locator('.view.top [data-act="col"]').first.click(); p.wait_for_timeout(700)
    p.locator('.view.top .pcard').first.click(); p.wait_for_timeout(700)
    p.click('.view.top [data-act="back"]'); p.wait_for_timeout(500)
    p.click('.view.top [data-act="back"]'); p.wait_for_timeout(400)
    tab('home'); p.wait_for_timeout(700)
    assert_hero_playing('after Shop→product→back→Home')
    # push a product from Home (hero node is kept across back), must resume
    p.locator('.view.top .hscroll .pcard').first.click(); p.wait_for_timeout(700)
    p.click('.view.top [data-act="back"]'); p.wait_for_timeout(700)
    assert_hero_playing('after Home product push/back')
    # ---------- v11 motion + interaction checks ----------
    def press_scale(sel):
        """hold the mouse down on an element and read its transform scale while :active"""
        b = p.locator(sel).first; b.scroll_into_view_if_needed(); bb = b.bounding_box()
        p.mouse.move(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2); p.mouse.down(); p.wait_for_timeout(160)
        sc = p.evaluate("(s) => { const m = getComputedStyle(document.querySelector(s)).transform; if (!m || m === 'none') return 1; const v = m.match(/matrix\\(([^,]+),\\s*([^,]+)/); return v ? Math.hypot(+v[1], +v[2]) : 1; }", sel)
        p.mouse.move(3, 3); p.mouse.up(); p.wait_for_timeout(250); return sc   # release off the element: no click
    tab('shop'); p.wait_for_timeout(500)
    seg = p.evaluate("""() => { const s = document.querySelector('.view.top .seg'), i = s && s.querySelector('.seg-ind'); if (!i) return null; const cs = getComputedStyle(i);
        const on = s.querySelector('button.on').getBoundingClientRect(), r = i.getBoundingClientRect();
        return {dur: cs.transitionDuration, prop: cs.transitionProperty, ease: cs.transitionTimingFunction, bg: cs.backgroundColor,
                aligned: Math.abs(r.left - on.left) < 1.5 && Math.abs(r.width - on.width) < 1.5, onBg: getComputedStyle(s.querySelector('button.on')).backgroundColor}; }""")
    if not seg: bad('[%s] Shop segmented control has no sliding indicator' % tag)
    else:
        good = seg['aligned'] and '0.28s' in seg['dur'] and 'transform' in seg['prop'] and 'width' in seg['prop'] and 'cubic-bezier' in seg['ease'] and seg['bg'] == 'rgb(255, 255, 255)' and seg['onBg'] in ('rgba(0, 0, 0, 0)', 'transparent')
        (ok if good else bad)(('segmented: white pill under active option, transition %s %s %s' % (seg['prop'], seg['dur'], seg['ease'])) if good else '[%s] segmented indicator setup: %s' % (tag, seg))
        rows0 = p.evaluate("() => [...document.querySelectorAll('.view.top .seg-body .cat-row b')].map(b => b.textContent).join('|')")
        x0 = p.evaluate("() => document.querySelector('.view.top .seg-ind').getBoundingClientRect().left")
        p.evaluate("""() => { window.__segSamples = []; const i = document.querySelector('.view.top .seg-ind'), t0 = performance.now();
            const tick = () => { window.__segSamples.push([performance.now() - t0, i.getBoundingClientRect().left]); if (performance.now() - t0 < 600) requestAnimationFrame(tick); };
            document.querySelector('.view.top .seg button[data-seg="edits"]').click(); requestAnimationFrame(tick); }""")
        if tag == 'mobile': p.wait_for_timeout(120); shot('26-seg-midflight')
        p.wait_for_timeout(700)
        mv = p.evaluate("""(x0) => { const s = document.querySelector('.view.top .seg'), i = s.querySelector('.seg-ind'), on = s.querySelector('button.on');
            const r = i.getBoundingClientRect(), b = on.getBoundingClientRect(), S = window.__segSamples, x1 = r.left;
            const mid = S.filter(x => x[1] > x0 + 2 && x[1] < x1 - 2).length;
            const body = document.querySelector('.view.top .seg-body');
            return {active: on.dataset.seg, aligned: Math.abs(r.left - b.left) < 1.5 && Math.abs(r.width - b.width) < 1.5, moved: x1 - x0, midFrames: mid, frames: S.length,
                    settledAt: Math.round((S.find(x => Math.abs(x[1] - x1) < .5) || [0])[0]), opacity: getComputedStyle(body).opacity,
                    rows: [...body.querySelectorAll('.cat-row b')].map(b => b.textContent).join('|'), selected: on.getAttribute('aria-selected')}; }""", x0)
        good = mv['active'] == 'edits' and mv['aligned'] and mv['moved'] > 40 and mv['midFrames'] >= 3 and 150 <= mv['settledAt'] <= 450 and mv['rows'] != rows0 and mv['opacity'] == '1' and mv['selected'] == 'true'
        (ok if good else bad)(('segmented: pill slid %dpx over %d in-between frames, settled at ~%dms, content swapped' % (mv['moved'], mv['midFrames'], mv['settledAt'])) if good else '[%s] segmented indicator did not slide/swap: %s' % (tag, mv))
        if tag == 'mobile': shot('27-shop-collections')
        # remembered when coming back to Shop from a collection
        p.locator('.view.top .seg-body .cat-row').first.click(); p.wait_for_timeout(600); p.click('.view.top [data-act="back"]'); p.wait_for_timeout(500)
        kept = p.evaluate("() => document.querySelector('.view.top .seg button.on').dataset.seg")
        (ok if kept == 'edits' else bad)('segmented: selection kept after back' if kept == 'edits' else '[%s] segment reset after back: %s' % (tag, kept))
        p.click('.view.top .seg button[data-seg="cats"]'); p.wait_for_timeout(500)
        back_ok = p.evaluate("() => { const s = document.querySelector('.view.top .seg'), i = s.querySelector('.seg-ind').getBoundingClientRect(), b = s.querySelector('button.on').getBoundingClientRect(); return s.querySelector('button.on').dataset.seg === 'cats' && Math.abs(i.left - b.left) < 1.5; }")
        (ok if back_ok else bad)('segmented: pill slides back to the first option' if back_ok else '[%s] segmented pill did not return' % tag)
    # tab bar: cross-fade (old view kept briefly, non-interactive) + active icon spring
    p.evaluate("""() => { window.__tab = null; const old = document.querySelector('.view.top'); document.querySelector('#tabbar button[data-tab="wishlist"]').click();
        const nw = document.querySelector('.view.top'), btn = document.querySelector('#tabbar button.active');
        window.__tab = {oldKept: old.isConnected, oldOut: old.classList.contains('tab-out'), oldPE: getComputedStyle(old).pointerEvents, newAnim: getComputedStyle(nw).animationName,
                        icon: getComputedStyle(btn.querySelector('svg')).animationName, cur: btn.getAttribute('aria-current')};
        setTimeout(() => { window.__tab.oldGone = !old.isConnected; }, 420); }""")
    p.wait_for_timeout(500); tb2 = p.evaluate('window.__tab')
    good = tb2['oldKept'] and tb2['oldOut'] and tb2['oldPE'] == 'none' and tb2['newAnim'] == 'tabIn' and tb2['icon'] == 'tabPop' and tb2['oldGone'] and tb2['cur'] == 'page'
    (ok if good else bad)('tab switch cross-fades (tabIn), old view removed, active icon tabPop' if good else '[%s] tab transition: %s' % (tag, tb2))
    # push/pop: iOS slide + parallax under an opacity-only shade
    tab('home'); p.wait_for_timeout(400)
    p.evaluate("""() => { const prev = document.querySelector('.view.top'); document.querySelector('.view.top .hscroll .pcard').click();
        const nw = document.querySelector('.view.top'), sh = document.querySelector('.nav-shade');
        window.__push = {enter: getComputedStyle(nw).animationName, under: getComputedStyle(prev).animationName, shade: !!sh && getComputedStyle(sh).animationName,
                         filter: getComputedStyle(prev).filter}; }""")
    p.wait_for_timeout(700); pu = p.evaluate('window.__push')
    p.evaluate("""() => { const v = document.querySelector('.view.top'); document.querySelector('.view.top [data-act="back"]').click();
        const prev = document.querySelector('.view.top'), sh = document.querySelector('.nav-shade');
        window.__pop = {leave: getComputedStyle(v).animationName, reveal: getComputedStyle(prev).animationName, shade: !!sh && getComputedStyle(sh).animationName, leaveTop: v.classList.contains('top')}; }""")
    p.wait_for_timeout(600); po = p.evaluate('window.__pop')
    good = pu['enter'] == 'pushIn' and pu['under'] == 'dimOut' and pu['shade'] == 'shadeIn' and pu['filter'] == 'none' and po['leave'] == 'pushOut' and po['reveal'] == 'dimIn' and po['shade'] == 'shadeOut' and not po['leaveTop']
    (ok if good else bad)('push/pop: slide + 28%% parallax + shade (%s / %s)' % (pu, po) if good else '[%s] push/pop motion: %s %s' % (tag, pu, po))
    assert_hero_playing('after motion checks push/back')
    # press feedback (desktop mouse)
    if w >= 1000:
        sc_btn = press_scale('.view.top .hero .btn'); sc_chip = None
        (ok if 0.955 <= sc_btn <= 0.985 else bad)('button press scale %.3f' % sc_btn if 0.955 <= sc_btn <= 0.985 else '[%s] button press scale %.3f (want ~0.97)' % (tag, sc_btn))
        p.locator('.view.top .hero .btn').hover(); p.wait_for_timeout(300)
        hv = p.evaluate("() => getComputedStyle(document.querySelector('.view.top .hero .btn')).backgroundColor")
        hv0 = p.evaluate("() => { const b = document.querySelector('.view.top .hero .btn').cloneNode(true); b.style.transition = 'none'; document.querySelector('.view.top .hero .hero-copy').appendChild(b); const c = getComputedStyle(b).backgroundColor; b.remove(); return c; }")
        (ok if hv != hv0 else bad)('button hover state (%s → %s)' % (hv0, hv) if hv != hv0 else '[%s] no hover on light button' % tag)
        p.mouse.move(5, 5)
    # wishlist heart pop
    p.evaluate("document.querySelector('.view.top').scrollTop = 600"); p.wait_for_timeout(300)
    hb = p.locator('.view.top .hscroll .pcard .heart').nth(1); hb.click(); p.wait_for_timeout(60)
    ht = p.evaluate("""() => { const h = document.querySelectorAll('.view.top .hscroll .pcard .heart')[1]; return {on: h.classList.contains('on'), burst: h.classList.contains('burst'),
        svg: getComputedStyle(h.querySelector('svg')).animationName, ring: getComputedStyle(h, '::after').animationName}; }""")
    (ok if ht['on'] and ht['svg'] == 'heartPop' and ht['ring'] == 'heartRing' else bad)('heart pop + ring on save' if ht['on'] and ht['svg'] == 'heartPop' and ht['ring'] == 'heartRing' else '[%s] heart animation: %s' % (tag, ht))
    p.wait_for_timeout(600); hb.click(); p.wait_for_timeout(2200)
    # demo button steps aside while a toast is up (mobile)
    if w < 1000:
        p.evaluate("document.querySelector('.view.top .hscroll .pcard .heart').click()"); p.wait_for_timeout(350)
        fo = p.evaluate("() => +getComputedStyle(document.querySelector('#demoFab')).opacity")
        (ok if fo < 0.05 else bad)('demo button hidden while toast shows' if fo < 0.05 else '[%s] demo button visible under toast (opacity %s)' % (tag, fo))
        p.evaluate("document.querySelector('.view.top .hscroll .pcard .heart').click()"); p.wait_for_timeout(2300)
    p.evaluate("document.querySelector('.view.top').scrollTop = 0"); p.wait_for_timeout(200)
    # images: product images fade in (.in) once loaded; shimmer placeholder while loading
    im = p.evaluate("""() => { const imgs = [...document.querySelectorAll('.view.top .pimg img')].filter(i => i.complete && i.naturalWidth);
        const notIn = imgs.filter(i => !i.classList.contains('in') || getComputedStyle(i).opacity !== '1').length;
        const pend = document.querySelector('.view.top .pimg:not(:has(img.in))');
        const t = document.createElement('div'); t.className = 'pimg'; t.style.cssText = 'position:absolute;width:10px;height:10px'; t.innerHTML = '<img>'; document.querySelector('.view.top').appendChild(t);
        const sh = getComputedStyle(t, '::before').animationName; t.remove();
        return {loaded: imgs.length, notIn, shimmer: sh, tr: getComputedStyle(document.querySelector('.view.top .pimg img')).transitionProperty}; }""")
    good = im['loaded'] > 0 and im['notIn'] == 0 and im['shimmer'] == 'shimmer' and 'opacity' in im['tr']
    (ok if good else bad)('images fade in (%d loaded, all .in), shimmer placeholder while loading' % im['loaded'] if good else '[%s] image fade/shimmer: %s' % (tag, im))
    rail = p.evaluate("() => { const h = document.querySelector('.view.top .hscroll'); const c = getComputedStyle(h); return {snap: c.scrollSnapType, ob: c.overscrollBehaviorX, align: getComputedStyle(h.firstElementChild).scrollSnapAlign}; }")
    (ok if 'mandatory' in rail['snap'] and rail['ob'] == 'contain' and 'start' in rail['align'] else bad)('rails: scroll-snap %s, overscroll %s' % (rail['snap'], rail['ob']) if 'mandatory' in rail['snap'] else '[%s] rail snap: %s' % (tag, rail))
    # add to bag micro-interaction: "Added" + drawn check, header bag count bumps, sheet rises after
    p.locator('.view.top .hscroll .pcard').first.click(); p.wait_for_timeout(700)
    hidden_fab = p.evaluate("() => +getComputedStyle(document.querySelector('#demoFab')).opacity < .05 || getComputedStyle(document.querySelector('#demoFab')).display === 'none'")
    (ok if hidden_fab else bad)('demo button tucked away on product page' if hidden_fab else '[%s] demo button over product page' % tag)
    n0 = p.evaluate("() => { const c = document.querySelector('.view.top .pdp-top .hb-count'); return c ? +c.textContent : -1; }")
    p.locator('.view.top .size:not(.out)').first.click(); p.click('#addBtn'); p.wait_for_timeout(120)
    ad = p.evaluate("""() => { const b = document.querySelector('#addBtn'), c = document.querySelector('.view.top .pdp-top .hb-count');
        return {txt: b.innerText.trim().toLowerCase(), check: !!b.querySelector('svg'), anim: getComputedStyle(b.querySelector('.ab-l')).animationName, count: c && +c.textContent, pop: c && c.classList.contains('pop'),
                countAnim: c && getComputedStyle(c).animationName, sheet: document.querySelector('#sheet').classList.contains('show')}; }""")
    if tag == 'mobile': shot('28-added-button')
    p.wait_for_timeout(900)
    ad['sheetLater'] = p.evaluate("() => document.querySelector('#sheet.show') && /added to bag/i.test(document.querySelector('#sheet').innerText)")
    good = ad['txt'] == 'added' and ad['check'] and ad['anim'] == 'abIn' and ad['count'] == n0 + 1 and ad['pop'] and ad['countAnim'] == 'pop' and not ad['sheet'] and ad['sheetLater']
    (ok if good else bad)('add to bag: "Added" + check, bag count %d→%d bumps, sheet follows' % (n0, ad['count']) if good else '[%s] add-to-bag interaction: %s (count before %s)' % (tag, ad, n0))
    # sheet: spring rise, backdrop fade, handle; drag the handle down to dismiss
    sh = p.evaluate("() => { const s = getComputedStyle(document.querySelector('#sheet')), b = getComputedStyle(document.querySelector('#sheetBackdrop')), g = document.querySelector('#sheet .grab'); return {t: s.transitionProperty + ' ' + s.transitionDuration + ' ' + s.transitionTimingFunction, bd: b.transitionProperty, grab: !!g && g.getBoundingClientRect().width > 20}; }")
    (ok if 'transform' in sh['t'] and 'opacity' in sh['bd'] and sh['grab'] else bad)('sheet: %s, backdrop fade, drag handle' % sh['t'] if 'transform' in sh['t'] else '[%s] sheet motion: %s' % (tag, sh))
    g = p.locator('#sheet .grab').bounding_box()
    p.mouse.move(g['x'] + g['width'] / 2, g['y'] + 2); p.mouse.down()
    for k in range(1, 9): p.mouse.move(g['x'] + g['width'] / 2, g['y'] + 2 + k * 30); p.wait_for_timeout(16)
    p.mouse.up(); p.wait_for_timeout(600)
    closed = not p.locator('#sheet.show').count()
    (ok if closed else bad)('sheet: drag handle down dismisses' if closed else '[%s] sheet did not dismiss on drag' % tag)
    if not closed: p.evaluate("document.querySelector('#sheetBackdrop').click()"); p.wait_for_timeout(400)
    # PDP solid title bar once the gallery scrolls away
    p.evaluate("document.querySelector('.view.top .pscroll').scrollTop = 900"); p.wait_for_timeout(450)
    bar = p.evaluate("() => +getComputedStyle(document.querySelector('.view.top .pdp-bar')).opacity")
    (ok if bar > .95 else bad)('PDP title bar appears past the gallery' if bar > .95 else '[%s] PDP bar opacity %s' % (tag, bar))
    if tag == 'mobile': shot('29-pdp-bar')
    p.keyboard.press('Escape'); p.wait_for_timeout(600)
    esc_ok = not p.locator('.view.top.pdp').count()
    (ok if esc_ok else bad)('Escape pops the product page' if esc_ok else '[%s] Escape did not go back' % tag)
    # bag: header pattern, quantity, totals; checkout "Change" are real buttons
    tab('bag'); p.wait_for_timeout(300)
    bg = p.evaluate("() => ({logo: !!document.querySelector('.view.top .topbar .tb-logo'), title: document.querySelector('.view.top .large-title').innerText.replace(/\\s+/g, ' ')})")
    (ok if bg['logo'] and 'bag' in bg['title'].lower() else bad)('bag header: %s' % bg['title'] if bg['logo'] else '[%s] bag header: %s' % (tag, bg))
    q0 = p.evaluate("() => [+document.querySelector('.view.top .qty span').textContent, document.querySelector('#bagTotal').textContent]")
    p.click('.view.top .qty button[data-q="1"]'); p.wait_for_timeout(350)
    q1 = p.evaluate("() => [+document.querySelector('.view.top .qty span').textContent, document.querySelector('#bagTotal').textContent, document.querySelector('#bagBadge').textContent, document.querySelector('.view.top .large-title small').textContent]")
    p.click('.view.top .qty button[data-q="-1"]'); p.wait_for_timeout(350)
    q2 = p.evaluate("() => [+document.querySelector('.view.top .qty span').textContent, document.querySelector('#bagTotal').textContent]")
    good = q1[0] == q0[0] + 1 and q1[1] != q0[1] and q2 == q0
    (ok if good else bad)('bag quantity +/- updates qty, total, badge (%s → %s → %s)' % (q0, q1, q2) if good else '[%s] bag quantity: %s %s %s' % (tag, q0, q1, q2))
    p.click('#checkout'); p.wait_for_timeout(700)
    ch = p.locator('#sheet .co-change'); nch = ch.count()
    if nch: ch.first.click(); p.wait_for_timeout(300)
    (ok if nch == 2 and 'demo' in p.inner_text('#toast').lower() else bad)('checkout "Change" rows respond' if nch == 2 else '[%s] checkout change buttons: %d' % (tag, nch))
    p.keyboard.press('Escape'); p.wait_for_timeout(500)
    (ok if not p.locator('#sheet.show').count() else bad)('Escape closes the sheet' if not p.locator('#sheet.show').count() else '[%s] Escape left sheet open' % tag)
    # toggles: knob glides
    tab('account'); p.wait_for_timeout(300)
    sw = p.evaluate("() => { const s = document.querySelector('.view.top .pref .switch'); return getComputedStyle(s, '::after').transitionProperty + ' ' + getComputedStyle(s, '::after').transitionDuration; }")
    (ok if 'transform' in sw else bad)('switch knob transition: %s' % sw if 'transform' in sw else '[%s] switch knob has no transition: %s' % (tag, sw))
    grp = p.evaluate("() => { const g = document.querySelector('.view.top .pref-group'), a = document.querySelector('.view.top .acct-size'); return g && a && Math.abs(g.getBoundingClientRect().left - a.getBoundingClientRect().left) < 1; }")
    (ok if grp else bad)('notification rows inset like the other account cards' if grp else '[%s] notification rows not inset' % tag)
    # leftovers from removed features must stay gone
    lo = p.evaluate("() => ({bell: !!document.querySelector('[data-act=\"notifs\"]'), dot: !!document.querySelector('.icon-btn .dot'), inbox: /notifications inbox|your inbox/i.test(document.body.innerText)})")
    (ok if not any(lo.values()) else bad)('no notifications inbox/bell leftovers' if not any(lo.values()) else '[%s] leftovers: %s' % (tag, lo))
    tab('home'); p.wait_for_timeout(500)
    # 3 drops
    tab('drops'); t = p.text_content('.view.top')
    for need in ['DROP', '24 hours', 'First Look', 'Coming soon']:
        (ok if need.lower() in t.lower() else bad)(('drops has "%s"' % need) if need.lower() in t.lower() else '[%s] drops missing "%s"' % (tag, need))
    cd1 = p.inner_text('.drop-card'); p.wait_for_timeout(1300); cd2 = p.inner_text('.drop-card')
    (ok if cd1 != cd2 else bad)('countdown ticking' if cd1 != cd2 else '[%s] countdown not ticking' % tag)
    shot('04-drops'); scroll_lazy(); broken_imgs()
    p.click('#notifyBtn'); p.wait_for_timeout(400)
    (ok if 'on the list' in p.inner_text('.view.top').lower() else bad)('notify me toggles' if 'on the list' in p.inner_text('.view.top').lower() else '[%s] notify failed' % tag)
    p.locator('.view.top .pcard').first.scroll_into_view_if_needed(); p.locator('.view.top .pcard').first.click(); p.wait_for_timeout(700)
    t = p.text_content('.view.top'); (ok if 'Coming soon' in t or 'DROP' in t else bad)('first-look PDP shows coming soon' if ('Coming soon' in t or 'DROP' in t) else '[%s] first look PDP not marked' % tag)
    shot('05-pdp-coming-soon'); p.click('.view.top [data-act="back"]'); p.wait_for_timeout(500)
    # 4 account: size, prefs, auth, browser
    tab('account'); t = p.text_content('.view.top')
    for need in ['Log in', 'Sign up', 'Drop alerts', 'Be first to know', 'Your size', 'New drops', 'Early access', 'Back in stock', 'Price drops', 'Order updates', 'Help'] + (['About'] if BR['about'] else []) + ['Legal', 'Version 1.0, concept', '@']:
        if need.lower() not in t.lower(): bad('[%s] account missing "%s"' % (tag, need))
    ok('account sections present')
    order_da = p.evaluate("""() => {
      const v = document.querySelector('.view.top');
      const drop = v.querySelector('#dropBanner') || v.querySelector('.drop-banner');
      let sizeH = null;
      for (const h of v.querySelectorAll('.acct-h h4')) { if (/your size/i.test(h.textContent)) { sizeH = h; break; } }
      if (!drop || !sizeH) return {ok:false, reason:'missing', drop:!!drop, size:!!sizeH};
      const following = !!(drop.compareDocumentPosition(sizeH) & Node.DOCUMENT_POSITION_FOLLOWING);
      return {ok:following, dropTop: Math.round(drop.getBoundingClientRect().top), sizeTop: Math.round(sizeH.getBoundingClientRect().top)};
    }""")
    (ok if order_da.get('ok') else bad)('drop alerts above your size' if order_da.get('ok') else '[%s] drop alerts not above your size: %s' % (tag, order_da))
    before = p.evaluate("() => document.querySelector('#dropSwitch').classList.contains('on')")
    p.click('#dropSwitch'); p.wait_for_timeout(400)
    synced = p.evaluate("""() => {
      const a = document.querySelector('#dropSwitch').classList.contains('on');
      const b = document.querySelector('.pref[data-pref="drops"] .switch').classList.contains('on');
      return {a:a, b:b, match:a===b};
    }""")
    (ok if synced['match'] and synced['a'] != before else bad)('drop alerts toggles and syncs with New drops' if synced['match'] and synced['a'] != before else '[%s] drop/new-drops sync failed: %s before=%s' % (tag, synced, before))
    p.click('.pref[data-pref="drops"]'); p.wait_for_timeout(300)
    synced2 = p.evaluate("""() => {
      const a = document.querySelector('#dropSwitch').classList.contains('on');
      const b = document.querySelector('.pref[data-pref="drops"] .switch').classList.contains('on');
      return {a:a, b:b, match:a===b};
    }""")
    (ok if synced2['match'] else bad)('New drops pref syncs drop alerts card' if synced2['match'] else '[%s] New drops did not sync drop card: %s' % (tag, synced2))
    shot('06-account')
    p.click('.acct-size .size[data-o="M"]'); p.wait_for_timeout(400)
    waist = p.locator('.acct-size .size[data-o="32"]')
    if waist.count(): waist.click(); p.wait_for_timeout(300)
    ok('saved size: ' + p.inner_text('#toast'))
    p.locator('.pref').nth(4).click(); p.wait_for_timeout(200); p.locator('.pref').nth(4).click()
    p.click('[data-act="login"]'); p.wait_for_timeout(500); shot('07-login')
    p.fill('.view.top input[type=email]', 'test@example.com'); p.fill('.view.top input[type=password]', 'x')
    p.click('.view.top button[type=submit]'); p.wait_for_timeout(400)
    (ok if 'nothing was saved' in p.inner_text('.view.top').lower() else bad)('login demo submit' if 'nothing was saved' in p.inner_text('.view.top').lower() else '[%s] login submit' % tag)
    p.click('#authDone'); p.wait_for_timeout(500)
    if p.locator('#signOut').count(): p.click('#signOut'); p.wait_for_timeout(300)
    p.click('[data-act="login"]'); p.wait_for_timeout(400); p.click('.view.top [data-act="recover"]'); p.wait_for_timeout(400); shot('08-recover')
    p.click('.view.top [data-act="back"]'); p.wait_for_timeout(300); p.click('.view.top [data-act="signup"]'); p.wait_for_timeout(400); shot('09-signup')
    p.click('.view.top [data-act="back"]'); p.wait_for_timeout(300); p.click('.view.top [data-act="back"]'); p.wait_for_timeout(400)
    for i, d in enumerate(p.locator('.acct-acc').all()):
        d.locator('summary').click(); p.wait_for_timeout(200)
    links = p.locator('[data-page]')
    n = links.count(); ok('%d info links' % n)
    for i in range(n):
        p.locator('[data-page]').nth(i).scroll_into_view_if_needed(); p.locator('[data-page]').nth(i).click(); p.wait_for_timeout(500)
        txt = p.inner_text('#browser')
        if 'No summary' in txt or len(txt) < 120: bad('[%s] thin browser page: %s' % (tag, txt[:100].replace('\n', ' ')))
        if i in (0, 1): shot('10-browser-%d' % i)
        p.click('#brDone'); p.wait_for_timeout(400)
    # 5 shop + listing filter
    tab('shop'); shot('11-shop'); scroll_lazy(); broken_imgs()
    p.locator('.view.top [data-act="col"]').first.click(); p.wait_for_timeout(700)
    before = p.locator('.view.top .pcard').count()
    p.locator('.view.top .size-filter .switch').click(); p.wait_for_timeout(500)
    after = p.locator('.view.top .pcard').count(); ok('size filter: %d → %d items' % (before, after)); shot('12-listing-filter')
    p.locator('.view.top .pcard').first.click(); p.wait_for_timeout(700)
    t = p.text_content('.view.top'); (ok if 'Your saved size' in t else bad)('PDP pre-selects saved size' if 'Your saved size' in t else '[%s] PDP saved size missing: %s' % (tag, p.inner_text('#sizeLbl')))
    shot('13-pdp'); p.click('#addBtn'); p.wait_for_timeout(1300); shot('14-added')
    if p.locator('#goBag').count(): p.click('#goBag')
    else: tab('bag')
    p.wait_for_timeout(600)
    tot1 = p.inner_text('#bagTotal'); p.click('#promoAdd'); p.wait_for_timeout(500); tot2 = p.inner_text('#bagTotal')
    (ok if tot1 != tot2 else bad)('APP10 applied: %s → %s' % (tot1, tot2) if tot1 != tot2 else '[%s] APP10 did not change total' % tag)
    shot('15-bag-app10')
    p.click('#checkout'); p.wait_for_timeout(700); t = p.inner_text('#sheet')
    pays = p.evaluate("window.BRAND.payments || null")
    needs = ['Shopify checkout', 'Shop'] + (['Klarna', '3 payments'] if not pays or 'klarna' in pays else (['PayPal'] if 'paypal' in pays else []))
    if pays and 'klarna' not in pays and 'Klarna' in t: bad('[%s] checkout offers Klarna but the brand does not: %s' % (tag, pays))
    for need in needs:
        if need not in t: bad('[%s] checkout missing %s' % (tag, need))
    ok('checkout: ' + ' '.join(t.split())[:160]); shot('16-checkout')
    p.click('#payNow'); p.wait_for_timeout(1800); shot('17-order'); p.keyboard.press('Escape')
    p.evaluate("document.querySelector('#sheetBackdrop').click()"); p.wait_for_timeout(400)
    # 6 search, wishlist
    tab('home'); p.click('.view.top [data-act="search"]'); p.wait_for_timeout(400); q = p.evaluate("(() => { const B = window.BRAND, all = Object.values(B.products || {}); if (all.some(x => /polo/i.test(x.t))) return 'polo'; return ((B.search || {}).trending || [])[0] || (all[0] ? all[0].n.split(' ')[0] : 'a'); })()")   # a term this catalogue has (not every brand sells polos)
    p.fill('#sq', q); p.wait_for_timeout(600)
    ok('search: ' + p.inner_text('.view.top .count')); shot('18-search'); p.click('.view.top [data-act="back"]'); p.wait_for_timeout(300)
    # 7 demo pushes
    for k in ['bag', 'restock'] + (['price'] if BR['sale'] else []) + ['drop', 'welcome']:
        if w >= 1000: p.click('.pitch [data-demo="%s"]' % k)
        else:
            to_root()
            p.click('#demoFab'); p.wait_for_timeout(500); p.click('#sheet [data-demo="%s"]' % k); p.wait_for_timeout(400)
        p.wait_for_timeout(900)
        if k == 'welcome':
            (ok if p.locator('#welcome.show').count() else bad)('demo welcome' if p.locator('#welcome.show').count() else '[%s] demo welcome' % tag)
            shot('19-demo-welcome'); p.click('#wlSkip'); p.wait_for_timeout(400); continue
        if not p.locator('#push.show').count(): bad('[%s] push %s did not show' % (tag, k)); continue
        ok('push %s: %s / %s' % (k, p.inner_text('#pushTitle'), p.inner_text('#pushText')))
        shot('20-push-' + k); p.click('#push'); p.wait_for_timeout(900); shot('21-after-' + k)
        if k == 'price' and not p.locator('.pd-badge, .g-badge').count(): bad('[%s] no PRICE DROP badge after price push' % tag)
    # 7b back-to-back pushes must each replay the entrance animation (no content-only swap)
    p.evaluate("""() => {
        window.__pushEnter = 0;
        const el = document.getElementById('push');
        if (el._enterSpy) el.removeEventListener('animationstart', el._enterSpy);
        el._enterSpy = (e) => { if (e.animationName === 'pushToastIn') window.__pushEnter++; };
        el.addEventListener('animationstart', el._enterSpy);
        el.classList.remove('show', 'hiding');
    }""")
    if w >= 1000:
        p.click('.pitch [data-demo="bag"]')
        p.wait_for_timeout(100)
        p.click('.pitch [data-demo="restock"]')
    else:
        to_root()
        p.click('#demoFab'); p.wait_for_timeout(400); p.click('#sheet [data-demo="bag"]')
        p.wait_for_function("() => document.getElementById('push').classList.contains('show')", timeout=3000)
        p.wait_for_timeout(80)  # still visible when the next demo is armed
        p.click('#demoFab'); p.wait_for_timeout(400); p.click('#sheet [data-demo="restock"]')
    p.wait_for_timeout(1400)
    enters = p.evaluate('window.__pushEnter')
    showing = p.locator('#push.show').count()
    if enters >= 2 and showing:
        ok('push entrance replayed on stacked demos (%d animationstart, still showing)' % enters)
    else:
        bad('[%s] stacked push entrance expected >=2 animationstarts + visible toast, got %s / showing=%s' % (tag, enters, showing))
    shot('20b-push-stacked')
    # dismiss without activating the deep-link (keeps tab bar tappable)
    p.evaluate("""() => {
        const el = document.getElementById('push');
        el.classList.remove('show', 'hiding');
        const sheet = document.getElementById('sheet');
        const bd = document.getElementById('sheetBackdrop');
        if (sheet) sheet.classList.remove('show');
        if (bd) bd.classList.remove('show');
    }""")
    p.wait_for_timeout(300)
    tab('wishlist'); p.wait_for_timeout(500); shot('22-wishlist'); broken_imgs()
    tab('drops'); p.wait_for_timeout(500); shot('23-drops-live')
    # rewards card
    tab('account')
    (ok if p.locator('.view.top .rewards-mini').count() == 1 else bad)('rewards points card on Account' if p.locator('.view.top .rewards-mini').count() == 1 else '[%s] rewards card missing on Account' % tag)
    p.click('.view.top [data-act="rewards"]'); p.wait_for_timeout(700); shot('24-rewards'); broken_imgs()
    # welcome shows again on every page load (dismissal is not remembered)
    p.goto(URL + '?nosplash', wait_until='networkidle'); p.wait_for_timeout(1200)
    (ok if p.locator('#welcome.show').count() else bad)('welcome shows again on reload' if p.locator('#welcome.show').count() else '[%s] welcome did not show again on reload' % tag)
    br.close()

def reduced_motion(pw):
    """prefers-reduced-motion: segmented control, tabs and sheets still work but switch instantly; marquee and shimmer stop."""
    # real desktop Chrome autoplay policy (no --autoplay-policy override): muted autoplay must work on its own
    br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True, reduced_motion='reduce')
    p = ctx.new_page(); tag = 'reduced-motion'
    p.on('pageerror', lambda e: bad('[%s] pageerror: %s' % (tag, e)))
    print('== %s 390x844' % tag)
    p.goto(URL + '?nosplash&nowelcome&nopush', wait_until='networkidle'); p.wait_for_timeout(800)
    mq = p.evaluate("() => getComputedStyle(document.querySelector('.mq-track')).animationName")
    (ok if mq == 'none' else bad)('reduced motion: marquee stopped' if mq == 'none' else '[%s] marquee still animating: %s' % (tag, mq))
    p.click('#tabbar button[data-tab="shop"]'); p.wait_for_timeout(400)
    r = p.evaluate("""async () => { const s = document.querySelector('.view.top .seg'); const rows0 = document.querySelector('.view.top .seg-body').innerText;
        s.querySelector('button[data-seg="edits"]').click(); await new Promise(r => setTimeout(r, 60));
        const i = s.querySelector('.seg-ind').getBoundingClientRect(), b = s.querySelector('button.on').getBoundingClientRect();
        return {aligned: Math.abs(i.left - b.left) < 1.5, swapped: document.querySelector('.view.top .seg-body').innerText !== rows0, dur: getComputedStyle(s.querySelector('.seg-ind')).transitionDuration}; }""")
    (ok if r['aligned'] and r['swapped'] else bad)('reduced motion: segmented switches instantly (%s)' % r['dur'] if r['aligned'] and r['swapped'] else '[%s] reduced-motion segmented: %s' % (tag, r))
    p.locator('.view.top .cat-row').first.click(); p.wait_for_timeout(120)
    v = p.evaluate("() => ({n: document.querySelectorAll('.view').length, img: [...document.querySelectorAll('.view.top .pimg img')].some(i => i.complete && i.naturalWidth && getComputedStyle(i).opacity !== '1')})")
    (ok if not v['img'] else bad)('reduced motion: push is instant, images shown without fade' if not v['img'] else '[%s] reduced-motion images: %s' % (tag, v))
    br.close()

def autoplay_refused(pw, w, h):
    """A browser that refuses autoplay (Safari Low Power / 'Never Auto-Play', Firefox 'Block Audio and Video', a power-saving
    pause): the poster must stay visible, and the first click anywhere must start the hero; a pause we did not ask for must resume."""
    br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    m = w < 600
    ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2 if m else 1, has_touch=m, is_mobile=m)
    # strip autoplay from the hero markup and make play() reject until there has been a user gesture
    ctx.add_init_script("""(() => {
      const d = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
      Object.defineProperty(Element.prototype, 'innerHTML', { configurable: true, get: d.get, set(v){ if (typeof v === 'string' && v.includes('<video')) v = v.replace(' autoplay', ''); d.set.call(this, v); } });
      const play = HTMLMediaElement.prototype.play;
      HTMLMediaElement.prototype.play = function(){ return (navigator.userActivation && navigator.userActivation.hasBeenActive) ? play.call(this) : Promise.reject(new DOMException('blocked', 'NotAllowedError')); };
    })()""")
    p = ctx.new_page(); tag = 'autoplay-refused-%d' % w
    p.on('pageerror', lambda e: bad('[%s] pageerror: %s' % (tag, e)))
    print('== %s %dx%d' % (tag, w, h))
    p.goto(URL + '?nosplash&nowelcome&nopush', wait_until='networkidle'); p.wait_for_timeout(1500)
    if not p.evaluate("!!(window.BRAND.home && window.BRAND.home.hero && window.BRAND.home.hero.video)"):
        ok('brand has a still-image hero: autoplay checks not applicable'); br.close(); return
    st = p.evaluate("() => { const v = document.querySelector('.view.top .hero video'), po = document.querySelector('.view.top .hero .poster'); return {paused: v.paused, poster: +getComputedStyle(po).opacity, posterOk: po.complete && po.naturalWidth > 0}; }")
    (ok if st['paused'] and st['poster'] > 0.95 and st['posterOk'] else bad)('autoplay refused: poster shown while blocked %s' % st if st['paused'] and st['poster'] > 0.95 and st['posterOk'] else '[%s] blocked state: %s' % (tag, st))
    # first gesture anywhere (desktop: the empty stage beside the phone; phone: the bare hero), hero must start
    if w >= 1000: p.mouse.click(40, h - 40)
    else: p.touchscreen.tap(195, 300)   # bare hero area (no action there)
    p.wait_for_timeout(1500)
    r = p.evaluate("async () => { const v = document.querySelector('.view.top .hero video'); const t0 = v.currentTime; await new Promise(r => setTimeout(r, 800)); return {paused: v.paused, adv: +(v.currentTime - t0).toFixed(2), poster: +getComputedStyle(document.querySelector('.view.top .hero .poster')).opacity}; }")
    (ok if not r['paused'] and r['adv'] > 0.3 and r['poster'] < 0.05 else bad)('autoplay refused: first click/tap starts the hero %s' % r if not r['paused'] and r['adv'] > 0.3 and r['poster'] < 0.05 else '[%s] hero did not start on first gesture: %s' % (tag, r))
    # a pause the app did not ask for (browser power saving) is resumed by the watchdog
    p.evaluate("document.querySelector('.view.top .hero video').pause()"); p.wait_for_timeout(2600)
    r = p.evaluate("async () => { const v = document.querySelector('.view.top .hero video'); const t0 = v.currentTime; await new Promise(r => setTimeout(r, 700)); return {paused: v.paused, adv: +(v.currentTime - t0).toFixed(2)}; }")
    (ok if not r['paused'] and r['adv'] > 0.3 else bad)('unrequested pause resumes on its own %s' % r if not r['paused'] and r['adv'] > 0.3 else '[%s] hero stayed paused after a browser pause: %s' % (tag, r))
    # and it still stops when Home is not showing (no decode work behind other tabs)
    p.evaluate("window.__app.switchTab('shop')"); p.wait_for_timeout(900)
    n = p.evaluate("() => [...document.querySelectorAll('.hero video')].filter(v => !v.paused).length")
    (ok if n == 0 else bad)('hero paused/removed while on another tab' if n == 0 else '[%s] %d hero video(s) still playing off Home' % (tag, n))
    br.close()

with sync_playwright() as pw:
    run(pw, 390, 844, 'mobile')
    run(pw, 1280, 720, 'desktop-1280')
    run(pw, 1440, 800, 'desktop')
    run(pw, 1920, 1080, 'desktop-1920')
    reduced_motion(pw)
    autoplay_refused(pw, 1440, 800)
    autoplay_refused(pw, 390, 844)
print('== stats source links')
check_stat_links((json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', a.slug, 'assets', 'brand.js')).read().split('window.BRAND=', 1)[1].rstrip().rstrip(';')).get('stats') or {}).get('items', []))
print('\n%d problem(s)' % len(problems))
for x in problems: print(' -', x)
sys.exit(1 if problems else 0)
