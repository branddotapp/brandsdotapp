"""Headless smoke test for a built brand app. Usage: python3 tools/smoke_test.py SLUG [--base URL] [--shots DIR]
Clicks through every tab and feature at phone (390x844) and desktop (1440x800) sizes, reports console errors,
failed requests and broken images, and saves screenshots."""
import sys, os, argparse, json
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('--base', default='http://localhost:8765'); ap.add_argument('--shots')
a = ap.parse_args()
URL = '%s/%s/' % (a.base.rstrip('/'), a.slug)
SH = a.shots or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', a.slug + '-shots')
os.makedirs(SH, exist_ok=True)
problems, log = [], []
def ok(m): log.append('  ✓ ' + m); print('  ✓ ' + m, flush=True)
def bad(m): problems.append(m); print('  ✗ ' + m, flush=True)

def run(pw, w, h, tag):
    br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
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
    def scroll_lazy():
        p.evaluate("""async () => { const v = document.querySelector('.view.top'); for (let y = 0; y < v.scrollHeight; y += 500){ v.scrollTop = y; await new Promise(r => setTimeout(r, 120)); } v.scrollTop = 0; }""")
        p.wait_for_timeout(1500)

    def assert_hero_playing(label):
        vi = p.evaluate("""async () => { const v = document.querySelector('.view.top .hero video'); if (!v) return null;
            const t0 = v.currentTime; await new Promise(r => setTimeout(r, 900));
            return {paused: v.paused, ready: v.readyState, advanced: +(v.currentTime - t0).toFixed(2), t: +v.currentTime.toFixed(2)}; }""")
        if not vi: bad('[%s] %s: no hero video' % (tag, label)); return
        playing = (not vi['paused']) and vi['advanced'] > 0.2
        (ok if playing else bad)(('%s: hero playing (advanced %.2fs, t=%.2f)' % (label, vi['advanced'], vi['t'])) if playing else '[%s] %s: hero not playing after resume: %s' % (tag, label, vi))

    p.goto(URL + '?nosplash', wait_until='networkidle'); p.wait_for_timeout(1200)
    # 1 welcome
    if p.locator('#welcome.show').count(): ok('welcome pop-up on open'); shot('01-welcome')
    else: bad('[%s] welcome did not show on open' % tag)
    p.click('#wlCode'); p.wait_for_timeout(400)
    if 'copied' in p.inner_text('#toast').lower(): ok('APP10 tap-to-copy')
    else: bad('[%s] copy toast missing' % tag)
    p.click('#wlGo'); p.wait_for_timeout(600)
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
    # review block sits near the bottom: after the product rails and categories, before the About footer
    order = p.evaluate("""() => { const v = document.querySelector('.view.top'); const kids = [...v.children];
        const at = s => { const e = v.querySelector(s); return e ? kids.indexOf(e.closest('.view.top > *')) : -1; };
        return {proof: at('.proof'), cats: at('.cat-grid'), rails: Math.max(...[...v.querySelectorAll('.hscroll')].map(e => kids.indexOf(e.closest('.view.top > *')))), about: at('.about'), hero: at('.hero')}; }""")
    if order['proof'] < 0: bad('[%s] no review block on home' % tag)
    elif order['proof'] > order['cats'] and order['proof'] > order['rails'] and order['proof'] < order['about']: ok('review block near the bottom (after rails + categories, above About): %s' % order)
    else: bad('[%s] review block in the wrong place: %s' % (tag, order))
    # hero video
    vi = p.evaluate("""async () => { const v = document.querySelector('.view.top .hero video'); if (!v) return null;
        const t0 = v.currentTime; let frames = 0; const t = performance.now();
        if (v.requestVideoFrameCallback) { const cb = () => { frames++; if (performance.now() - t < 2000) v.requestVideoFrameCallback(cb); }; v.requestVideoFrameCallback(cb); }
        await new Promise(r => setTimeout(r, 2100)); const r = v.getBoundingClientRect(), cs = getComputedStyle(v);
        return {autoplay: v.autoplay, muted: v.muted, loop: v.loop, playsinline: v.hasAttribute('playsinline'), preload: v.preload, fit: cs.objectFit,
                src: v.currentSrc.split('/').pop(), vw: v.videoWidth, vh: v.videoHeight, cw: r.width, ch: r.height, dpr: devicePixelRatio, paused: v.paused,
                ready: v.readyState, advanced: +(v.currentTime - t0).toFixed(2), fps: +(frames / 2).toFixed(1)}; }""")
    if not vi: bad('[%s] no hero video' % tag)
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
    for need in ['Log in', 'Sign up', 'Drop alerts', 'Be first to know', 'Your size', 'New drops', 'Early access', 'Back in stock', 'Price drops', 'Order updates', 'Help', 'About', 'Legal', 'Version 1.0, concept', '@']:
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
    shot('13-pdp'); p.click('#addBtn'); p.wait_for_timeout(700); shot('14-added')
    if p.locator('#goBag').count(): p.click('#goBag')
    else: tab('bag')
    p.wait_for_timeout(600)
    tot1 = p.inner_text('#bagTotal'); p.click('#promoAdd'); p.wait_for_timeout(500); tot2 = p.inner_text('#bagTotal')
    (ok if tot1 != tot2 else bad)('APP10 applied: %s → %s' % (tot1, tot2) if tot1 != tot2 else '[%s] APP10 did not change total' % tag)
    shot('15-bag-app10')
    p.click('#checkout'); p.wait_for_timeout(700); t = p.inner_text('#sheet')
    for need in ['Shopify checkout', 'Klarna', '3 payments', 'Shop']:
        if need not in t: bad('[%s] checkout missing %s' % (tag, need))
    ok('checkout: ' + ' '.join(t.split())[:160]); shot('16-checkout')
    p.click('#payNow'); p.wait_for_timeout(1800); shot('17-order'); p.keyboard.press('Escape')
    p.evaluate("document.querySelector('#sheetBackdrop').click()"); p.wait_for_timeout(400)
    # 6 search, wishlist
    tab('home'); p.click('.view.top [data-act="search"]'); p.wait_for_timeout(400); p.fill('#sq', 'polo'); p.wait_for_timeout(600)
    ok('search: ' + p.inner_text('.view.top .count')); shot('18-search'); p.click('.view.top [data-act="back"]'); p.wait_for_timeout(300)
    # 7 demo pushes
    for k in ['bag', 'restock', 'price', 'drop', 'welcome']:
        if w >= 1000: p.click('.pitch [data-demo="%s"]' % k)
        else:
            p.click('#demoFab'); p.wait_for_timeout(500); p.click('#sheet [data-demo="%s"]' % k); p.wait_for_timeout(400)
        p.wait_for_timeout(900)
        if k == 'welcome':
            (ok if p.locator('#welcome.show').count() else bad)('demo welcome' if p.locator('#welcome.show').count() else '[%s] demo welcome' % tag)
            shot('19-demo-welcome'); p.click('#wlSkip'); p.wait_for_timeout(400); continue
        if not p.locator('#push.show').count(): bad('[%s] push %s did not show' % (tag, k)); continue
        ok('push %s: %s / %s' % (k, p.inner_text('#pushTitle'), p.inner_text('#pushText')))
        shot('20-push-' + k); p.click('#push'); p.wait_for_timeout(900); shot('21-after-' + k)
        if k == 'price' and not p.locator('.pd-badge, .g-badge').count(): bad('[%s] no PRICE DROP badge after price push' % tag)
    tab('wishlist'); p.wait_for_timeout(500); shot('22-wishlist'); broken_imgs()
    tab('drops'); p.wait_for_timeout(500); shot('23-drops-live')
    # rewards card
    tab('account'); p.click('.view.top [data-act="rewards"]'); p.wait_for_timeout(700); shot('24-rewards'); broken_imgs()
    # welcome shows again on every page load (dismissal is not remembered)
    p.goto(URL + '?nosplash', wait_until='networkidle'); p.wait_for_timeout(1200)
    (ok if p.locator('#welcome.show').count() else bad)('welcome shows again on reload' if p.locator('#welcome.show').count() else '[%s] welcome did not show again on reload' % tag)
    br.close()

with sync_playwright() as pw:
    run(pw, 390, 844, 'mobile')
    run(pw, 1440, 800, 'desktop')
print('\n%d problem(s)' % len(problems))
for x in problems: print(' -', x)
sys.exit(1 if problems else 0)
