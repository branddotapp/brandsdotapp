/* brandsdotapp shared app shell. All brand-specific content comes from window.BRAND (brand.json). */
(function(){
'use strict';
const B = window.BRAND;
const P = B.products || {};
const COLS = (B.collections || []).slice();
const H = B.home || {}, SH = B.shop || {}, DR = B.drop || null, SHIP = B.shipping || {}, PAGES = B.pages || {};
const CUR = (B.currency && B.currency.symbol) || '£';
const DISC = B.discount || { code:'APP10', pct:10 };
const NAME = B.name, SITE = B.site;
const LOGO = B.assets.logoDark, LOGO_L = B.assets.logoLight || B.assets.logoDark;
const colBy = h => COLS.find(c => c.h === h);
const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const img = (u, w=600) => !u ? '' : (/cdn\.shopify\.com|\/cdn\/shop\//.test(u) ? u + (u.includes('?') ? '&' : '?') + 'width=' + w : u);
const money = n => CUR + (Math.round(n*100)/100).toFixed(2);
const prods = h => ((colBy(h) || {}).p || []).map(x => P[x]).filter(Boolean);
const ALL = Object.values(P);
const FREE_SHIP = SHIP.freeOver || 0;
const IG = B.socials && B.socials.instagram;
if (DR && DR.products && DR.products.length) COLS.push({ h:'__drop', t:DR.title || DR.name, p:DR.products.filter(h=>P[h]) });

// ---------- icons ----------
const I = {
  back:'<svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg>',
  bell:'<svg viewBox="0 0 24 24"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/></svg>',
  bag:'<svg viewBox="0 0 24 24"><path d="M5 8h14l-1 12.5H6z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/></svg>',
  heart:'<svg viewBox="0 0 24 24"><path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20z"/></svg>',
  share:'<svg viewBox="0 0 24 24"><path d="M12 3v12M7.5 7.5 12 3l4.5 4.5"/><path d="M5 12v7.5h14V12"/></svg>',
  chev:'<svg class="chev" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg>',
  plus:'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  check:'<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>',
  star:'<svg viewBox="0 0 24 24"><path d="M12 3.5l2.6 5.3 5.9.9-4.2 4.1 1 5.8L12 16.9l-5.3 2.7 1-5.8-4.2-4.1 5.9-.9z"/></svg>',
  ruler:'<svg viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="8" rx="1"/><path d="M7 8v3M11 8v4M15 8v3M19 8v4"/></svg>',
  truck:'<svg viewBox="0 0 24 24"><path d="M2.5 6.5h11v9h-11zM13.5 9.5h4l3 3v3h-7z"/><circle cx="6.5" cy="17.5" r="1.6"/><circle cx="17" cy="17.5" r="1.6"/></svg>',
  ret:'<svg viewBox="0 0 24 24"><path d="M4 9h11a5 5 0 0 1 0 10H8"/><path d="M8 5 4 9l4 4"/></svg>',
  card:'<svg viewBox="0 0 24 24"><rect x="2.5" y="5.5" width="19" height="13" rx="2"/><path d="M2.5 10h19"/></svg>',
  gift:'<svg viewBox="0 0 24 24"><rect x="3.5" y="9" width="17" height="11.5"/><path d="M2.5 9h19v-3h-19zM12 6v14.5M12 6S10.5 2.5 8 3.5 9 6 12 6zm0 0s1.5-3.5 4-2.5S15 6 12 6z"/></svg>',
  bolt:'<svg viewBox="0 0 24 24"><path d="M13 2.5 5 13.5h6l-1 8 8-11h-6z"/></svg>',
  pin:'<svg viewBox="0 0 24 24"><path d="M12 21s-6.5-6.2-6.5-11.2a6.5 6.5 0 0 1 13 0C18.5 14.8 12 21 12 21z"/><circle cx="12" cy="9.8" r="2.3"/></svg>',
  user:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="4"/><path d="M4.5 20.5c1-4 4-6 7.5-6s6.5 2 7.5 6"/></svg>',
  drop:'<svg viewBox="0 0 24 24"><circle cx="12" cy="13" r="7.5"/><path d="M12 9v4.2l2.6 1.6M9.5 2.5h5"/></svg>',
  tag:'<svg viewBox="0 0 24 24"><path d="M3.5 12.5V4.5h8l9 9-8 8z"/><circle cx="8" cy="9" r="1.4"/></svg>',
  copy:'<svg viewBox="0 0 24 24"><rect x="8.5" y="8.5" width="11" height="11" rx="1.5"/><path d="M15.5 8.5V5a1.5 1.5 0 0 0-1.5-1.5H5A1.5 1.5 0 0 0 3.5 5v9A1.5 1.5 0 0 0 5 15.5h3.5"/></svg>',
  ext:'<svg viewBox="0 0 24 24"><path d="M14 4.5h5.5V10M19.5 4.5 11 13M18 14v5.5H4.5V6H10"/></svg>',
  lock:'<svg viewBox="0 0 24 24"><rect x="5" y="10.5" width="14" height="10" rx="1.5"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/></svg>',
  ig:'<svg viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".6"/></svg>',
  apple:'<svg viewBox="0 0 24 24"><path d="M16.4 12.6c0-2.3 1.9-3.4 2-3.5-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.1-2.8.9-3.5.9-.7 0-1.8-.8-3-.8-1.5 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.4 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3 .7c1.3 0 2.1-1.1 2.8-2.3.9-1.3 1.3-2.6 1.3-2.6s-2.5-1-2.5-3.8zM14.2 5.8c.6-.8 1.1-1.9 1-3-.9 0-2.1.6-2.7 1.4-.6.7-1.1 1.8-1 2.9 1 .1 2.1-.5 2.7-1.3z"/></svg>'
};
const TABS = [['home','Home','<path d="M3.5 10.5 12 4l8.5 6.5V20a1 1 0 0 1-1 1h-5v-6h-5v6h-5a1 1 0 0 1-1-1z"/>'],
  ['shop','Shop','<rect x="3.5" y="3.5" width="7" height="7" rx="1"/><rect x="13.5" y="3.5" width="7" height="7" rx="1"/><rect x="3.5" y="13.5" width="7" height="7" rx="1"/><rect x="13.5" y="13.5" width="7" height="7" rx="1"/>'],
  ['drops','Drops','<circle cx="12" cy="13" r="7.5"/><path d="M12 9v4.2l2.6 1.6M9.5 2.5h5"/>'],
  ['wishlist','Wishlist','<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20z"/>'],
  ['bag','Bag','<path d="M5 8h14l-1 12.5H6z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>'],
  ['account','Account','<circle cx="12" cy="8.5" r="4"/><path d="M4.5 20.5c1-4 4-6 7.5-6s6.5 2 7.5 6"/>']].filter(t => t[0] !== 'drops' || DR);

// ---------- persistent state ----------
const store = {
  get(k, d){ try { const v = JSON.parse(localStorage.getItem(B.slug+'_'+k)); return v == null ? d : v; } catch(e){ return d; } },
  set(k, v){ try { localStorage.setItem(B.slug+'_'+k, JSON.stringify(v)); } catch(e){} }
};
let bag = store.get('bag', []).filter(i => P[i.h]);
let wish = store.get('wish', []).filter(h => P[h]);
let recent = store.get('recent', []);
let prefs = Object.assign({ drops:true, early:true, restock:true, price:true, orders:true }, store.get('prefs', {}));
let mySize = store.get('size', {});
let promo = store.get('promo', false);
let dropNotify = store.get('dropNotify', false);
let priceDrop = store.get('priceDrop', null);   // {h}
let dropLive = false;
let unread = true;
let signedIn = false; // demo only, never persisted
const savePrefs = () => store.set('prefs', prefs);

function saveBag(){ store.set('bag', bag); updateBadges(true); }
function saveWish(){ store.set('wish', wish); updateBadges(); }
function updateBadges(popBag){
  const n = bag.reduce((a,i)=>a+i.q,0);
  const bb = $('#bagBadge'), wb = $('#wishBadge');
  if (bb){ bb.textContent = n; bb.classList.toggle('show', n>0); if (popBag){ bb.classList.remove('pop'); void bb.offsetWidth; bb.classList.add('pop'); } }
  if (wb){ wb.textContent = wish.length; wb.classList.toggle('show', wish.length>0); }
}
const inWish = h => wish.includes(h);
function toggleWish(h){
  if (inWish(h)) { wish = wish.filter(x=>x!==h); toast('Removed from wishlist'); }
  else { wish.unshift(h); toast('Saved to wishlist', I.heart); }
  saveWish();
  $$('[data-wish="'+CSS.escape(h)+'"]').forEach(b => { b.classList.toggle('on', inWish(h)); b.classList.remove('burst'); void b.offsetWidth; b.classList.add('burst'); });
}

// ---------- sizes ----------
const SIZE_GROUPS = (B.sizes && B.sizes.groups) || [];
const normSize = s => String(s).split(' - ')[0].trim().toUpperCase();
const hasSize = () => SIZE_GROUPS.some(g => mySize[g.key]);
const sizeLabel = () => SIZE_GROUPS.filter(g => mySize[g.key]).map(g => (g.prefix||'') + mySize[g.key]).join(' · ');
const sizeMatch = label => { const n = normSize(label); return SIZE_GROUPS.some(g => mySize[g.key] && String(mySize[g.key]).toUpperCase() === n); };
const inMySize = p => p.sz.some(s => s[1] && sizeMatch(s[0]));
const prettySize = s => String(s).replace(' - ',' · ');
function openSizeSheet(done){
  let tmp = Object.assign({}, mySize);
  openSheet('<h3>Your size</h3><p class="center sheet-sub">We’ll pre-select it on product pages and can hide anything that isn’t in stock in your size.</p>'+
    SIZE_GROUPS.map(g=>'<div class="sz-group"><div class="label-row" style="margin-top:6px"><b>'+esc(g.label)+'</b></div><div class="sizes">'+g.opts.map(o=>'<button class="size'+(String(tmp[g.key])===String(o)?' on':'')+'" data-g="'+g.key+'" data-o="'+esc(o)+'">'+esc((g.prefix||'')+o)+'</button>').join('')+'</div></div>').join('')+
    '<div class="btns" style="margin-top:20px"><button class="btn btn-dark btn-block" id="szSave">Save my size</button>'+(hasSize()?'<button class="btn btn-outline btn-block" id="szClear">Clear saved size</button>':'')+'</div>',
    s => {
      $$('.size', s).forEach(b => b.addEventListener('click', () => { const g=b.dataset.g; tmp[g] = tmp[g]===b.dataset.o ? null : b.dataset.o; $$('.size[data-g="'+g+'"]', s).forEach(x=>x.classList.toggle('on', x.dataset.o===tmp[g])); }));
      $('#szSave', s).addEventListener('click', () => { mySize = tmp; store.set('size', mySize); closeSheet(); toast(hasSize() ? 'Saved size: '+sizeLabel() : 'Size cleared', I.ruler); done && done(); refreshAll(); });
      const c = $('#szClear', s); if (c) c.addEventListener('click', () => { mySize = {}; store.set('size', mySize); closeSheet(); toast('Size cleared', I.ruler); done && done(); refreshAll(); });
    });
}

// ---------- toast ----------
let toastT;
function toast(msg, icon){
  const t = $('#toast');
  t.innerHTML = (icon || I.check) + '<span>'+esc(msg)+'</span>';
  t.classList.toggle('raise', !!$('.view.top .buybar.show'));
  t.classList.add('show'); clearTimeout(toastT);
  toastT = setTimeout(()=>t.classList.remove('show'), 2000);
}

// ---------- sheet ----------
function openSheet(html, onMount){
  const s = $('#sheet');
  s.innerHTML = '<div class="grab"></div>' + html;
  s.scrollTop = 0;
  $('#sheetBackdrop').classList.add('show'); s.classList.add('show');
  onMount && onMount(s);
}
function closeSheet(){ $('#sheet').classList.remove('show'); $('#sheetBackdrop').classList.remove('show'); }

// ---------- navigation ----------
let stackEl, stack = [], currentTab = 'home';
const roots = { home: Home, shop: Shop, drops: Drops, search: Search, wishlist: Wishlist, bag: Bag, account: Account };

function makeView(fn, args){
  const el = document.createElement('section');
  el.className = 'view';
  const opts = fn(el, args) || {};
  // hairline under the pinned top block once content scrolls beneath it (all tabs)
  el.addEventListener('scroll', () => { const s = el.scrollTop > 2; if (s !== el.classList.contains('scrolled')) el.classList.toggle('scrolled', s); }, {passive:true});
  return { el, opts, fn, args };
}
function applyChrome(v){
  $('#tabbar').classList.toggle('hidden', !!v.opts.hideTabs);
  setStatus(v.opts.light && (v.el.scrollTop < (v.opts.lightUntil || 9999)));
  stack.forEach(s => s.el.classList.remove('top')); v.el.classList.add('top');
}
function push(fn, args){
  const prev = stack[stack.length-1];
  const v = makeView(fn, args);
  stackEl.appendChild(v.el); stack.push(v);
  v.el.classList.add('enter');
  if (prev){ prev.el.classList.add('under'); setTimeout(()=>{ prev.el.classList.remove('under'); if (stack.includes(prev) && stack[stack.length-1] !== prev) prev.el.style.visibility='hidden'; }, 430); }
  setTimeout(()=>v.el.classList.remove('enter'), 450);
  applyChrome(v);
}
function back(){
  if (stack.length < 2) return;
  const v = stack.pop(), prev = stack[stack.length-1];
  prev.el.style.visibility=''; prev.el.classList.add('reveal');
  if (prev.el._refresh) prev.el._refresh();
  v.el.classList.add('leave');
  setTimeout(()=>{ v.el.remove(); prev.el.classList.remove('reveal'); }, 360);
  applyChrome(prev);
}
function switchTab(tab, args){
  closeSheet(); closeBrowser();
  if (tab === currentTab && stack.length === 1 && !args){ stack[0].el.scrollTo({top:0, behavior:'smooth'}); if (stack[0].el._refresh) stack[0].el._refresh(); return; }
  currentTab = tab;
  $$('#tabbar button').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  stack.forEach(s => s.el.remove()); stack = [];
  const v = makeView(roots[tab], args);
  v.el.classList.add('fade'); stackEl.appendChild(v.el); stack.push(v);
  applyChrome(v);
}
function refreshAll(){ stack.forEach(s => s.el._refresh && s.el._refresh()); }
function setStatus(light){ $('#statusbar').classList.toggle('light', !!light); }

// ---------- components ----------
const isComing = h => DR && !dropLive && (DR.products||[]).includes(h);
function pcard(p, opts={}){
  const sale = p.cp > p.p;
  const out = p.sz.every(s=>!s[1]);
  const isNew = H.newCol && (colBy(H.newCol)||{p:[]}).p.includes(p.h);
  const pd = priceDrop && priceDrop.h === p.h;
  const tag = (opts.dropGrid && isComing(p.h)) ? '<span class="tag soon">Coming soon</span>'
    : pd ? '<span class="tag drop">Price drop</span>'
    : out ? '<span class="tag">Sold out</span>' : sale ? '<span class="tag sale">-'+Math.round((1-p.p/p.cp)*100)+'%</span>' : isNew ? '<span class="tag">New in</span>' : '';
  return '<div class="pcard" data-act="pdp" data-v="'+esc(p.h)+'">'+
    '<div class="pimg"><img loading="lazy" src="'+img(p.im[0], opts.w||500)+'" alt="'+esc(p.t)+'">'+tag+
    '<button class="heart '+(inWish(p.h)?'on':'')+'" data-act="wish" data-v="'+esc(p.h)+'" data-wish="'+esc(p.h)+'" aria-label="Save">'+I.heart+'</button></div>'+
    '<div class="pmeta"><div class="pname">'+esc(p.n)+'</div>'+(p.c?'<div class="pcol">'+esc(p.c)+'</div>':'')+priceHTML(p)+'</div></div>';
}
function priceHTML(p){
  return p.cp > p.p ? '<div class="price sale"><b>'+money(p.p)+'</b><s>'+money(p.cp)+'</s></div>' : '<div class="price">'+money(p.p)+'</div>';
}
function topbar({title, logo, back:bk, right='', left='', clear}={}){
  if (!title && !bk) logo = true;   // root tabs without a title carry the logo, same header row as Home
  return '<header class="topbar'+(clear?' clear':'')+'">'+
    (bk ? '<button class="icon-btn" data-act="back" aria-label="Back">'+I.back+'</button>' : (left || '<span style="width:40px"></span>'))+
    (logo ? '<img class="tb-logo" src="'+LOGO+'" alt="'+esc(NAME)+'">' : '<div class="tb-title">'+esc(title||'')+'</div>')+
    (right || '<span style="width:40px"></span>')+'</header>';
}
const bagBtn = () => '<button class="icon-btn" data-act="bagtab" aria-label="Bag">'+I.bag+'</button>';
const searchBtn = () => '<button class="icon-btn" data-act="search" aria-label="Search">'+I.search+'</button>';
const credit = () => '<p class="credit-inline">Concept app mockup for '+esc(NAME)+'</p>';
const stars = n => '<span class="stars" style="--r:'+(n/5*100)+'%"><i>★★★★★</i><i>★★★★★</i></span>';
function marquee(){
  const items = (B.perks || []).concat(['App members, '+DISC.pct+'% off your first app order']);
  if (B.reviews && B.reviews.score) items.push('Rated '+(B.reviews.label?B.reviews.label+', ':'')+B.reviews.score+'/5 on '+B.reviews.source);
  const run = items.map(t=>'<span>'+esc(t)+'</span><i>✦</i>').join('');
  return '<div class="marquee" aria-label="Perks"><div class="mq-track">'+run+run+'</div></div>';
}
function proofHTML(compact){
  const R = B.reviews;
  if (!R || !R.score) return '';
  if (compact) return '<div class="proof-mini" data-act="reviews">'+stars(R.score)+'<span><b>'+R.score+'</b> '+esc(R.label||'')+' on '+esc(R.source)+' · '+Number(R.count).toLocaleString('en-GB')+' reviews</span></div>';
  return '<div class="proof" data-act="reviews"><div class="pr-l"><small>'+esc(R.source)+'</small><b>'+esc(R.label||'Rated')+'</b></div><div class="pr-r">'+stars(R.score)+'<p><b>'+R.score+' out of 5</b> · based on '+Number(R.count).toLocaleString('en-GB')+' reviews</p></div></div>';
}

// drag-to-scroll for desktop mice
function enableDrag(root){
  $$('.hscroll,.chips,.swatches', root).forEach(el => {
    if (el._drag) return; el._drag = true;
    let down=false, sx=0, sl=0, moved=false;
    el.addEventListener('pointerdown', e => { if (e.pointerType!=='mouse') return; down=true; moved=false; sx=e.clientX; sl=el.scrollLeft; el.style.scrollSnapType='none'; });
    window.addEventListener('pointermove', e => { if(!down) return; const dx=e.clientX-sx; if(Math.abs(dx)>5){ moved=true; el.classList.add('dragging'); } el.scrollLeft = sl - dx; });
    window.addEventListener('pointerup', () => { if(!down) return; down=false; el.style.scrollSnapType=''; setTimeout(()=>el.classList.remove('dragging'),0); });
    el.addEventListener('click', e => { if (moved){ e.stopPropagation(); e.preventDefault(); moved=false; } }, true);
  });
}

// ---------- drop timing ----------
function dropTimes(){
  const early = (DR && DR.earlyHours) || 24;
  let web;
  if (DR && DR.opensAt && new Date(DR.opensAt) - Date.now() > early*3600e3) web = new Date(DR.opensAt);
  else {
    const wd = DR && DR.weekday != null ? DR.weekday : 4, hr = DR && DR.hour != null ? DR.hour : 19;
    web = new Date(); web.setHours(hr,0,0,0);
    web.setDate(web.getDate() + (wd - web.getDay() + 7) % 7);
    while (web - Date.now() < early*3600e3 + 3600e3) web.setDate(web.getDate()+7);
  }
  return { app: new Date(web - early*3600e3), web };
}
const fmtDay = d => d.toLocaleDateString('en-GB',{weekday:'short', day:'numeric', month:'short'}) + ', ' + d.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'});
function cdParts(){ const ms = Math.max(0, dropTimes().app - Date.now()); return [Math.floor(ms/864e5), Math.floor(ms/36e5)%24, Math.floor(ms/6e4)%60, Math.floor(ms/1e3)%60]; }
const pad = n => String(n).padStart(2,'0');
function cdHTML(){ const c = cdParts(); return ['Days','Hrs','Min','Sec'].map((l,i)=>'<div><b data-cd="'+i+'">'+pad(c[i])+'</b><small>'+l+'</small></div>').join(''); }
setInterval(() => { const els = $$('[data-cd]'); if (!els.length) return; const c = cdParts(); els.forEach(e => { const v = pad(c[+e.dataset.cd]); if (e.textContent !== v) e.textContent = v; }); }, 1000);
const dropImg = () => DR && (DR.image || (P[DR.products[0]] && img(P[DR.products[0]].im[0], 700)));

// ---------- hero video ----------
// Built once per Home view and re-attached on every re-render, so refreshing Home (size saved, demo pushes, back
// navigation) never recreates the <video> and restarts/re-buffers it.
function heroEl(){
  const hero = H.hero || {};
  const d = document.createElement('div');
  d.className = 'hero';
  const v = hero.video ? '<video autoplay muted loop playsinline preload="auto" disablepictureinpicture disableremoteplayback'+(hero.poster?' poster="'+esc(hero.poster)+'"':'')+(hero.videoW?' width="'+hero.videoW+'" height="'+hero.videoH+'"':'')+'>'+
    '<source src="'+esc(hero.video)+'" type="video/mp4">'+(hero.videoWebm?'<source src="'+esc(hero.videoWebm)+'" type="video/webm">':'')+'</video>' : '';
  d.innerHTML = '<img class="poster" src="'+esc(hero.poster||'')+'" alt="">'+v+
    '<div class="hero-copy"><div class="eyebrow">'+esc(hero.eyebrow||'')+'</div><div class="hero-title">'+esc(hero.title||NAME)+'</div>'+(hero.col&&colBy(hero.col)?'<button class="btn btn-light" data-act="col" data-v="'+esc(hero.col)+'">'+esc(hero.cta||'Shop now')+'</button>':'')+'</div>';
  const vid = $('video', d);
  if (vid){
    vid.muted = true; vid.defaultMuted = true;
    vid.addEventListener('playing', () => { const pi = $('.poster', d); if (pi) pi.style.opacity = 0; });
    // play only while the hero is on screen and the page is visible (saves decode work for the rest of the app)
    let onScreen = true;
    const sync = () => { if (onScreen && !document.hidden && d.isConnected) { const pr = vid.play(); if (pr && pr.catch) pr.catch(()=>{}); } else vid.pause(); };
    if ('IntersectionObserver' in window) new IntersectionObserver(es => { onScreen = es[es.length-1].isIntersecting; sync(); }, { threshold: 0.01 }).observe(d);
    document.addEventListener('visibilitychange', sync);
    d._sync = sync;
  }
  return d;
}

// ---------- HOME ----------
function Home(el){
  const heroNode = heroEl();
  const render = () => {
    const newIn = prods(H.newCol).slice(0, 12);
    const best = prods(H.bestCol).slice(0, 12);
    const cover = h => { const p = prods(h)[0]; return p ? img(p.im[0], 500) : ''; };
    const tiles = (H.tiles || []).filter(t => prods(t[0]).length);
    const mine = hasSize() ? ALL.filter(inMySize).sort((a,b)=>(newIn.includes(b)?1:0)-(newIn.includes(a)?1:0)).slice(0,12) : [];
    const fc = H.feature && prods(H.feature.col)[0];
    el.innerHTML =
      '<div class="home-head"><div class="home-band">'+marquee()+topbar({ logo:true, left:'<button class="icon-btn" data-act="notifs" aria-label="Notifications">'+I.bell+(unread?'<i class="dot"></i>':'')+'</button>', right:'<div class="tb-r">'+searchBtn()+bagBtn()+'</div>' }) + '</div></div>'+
      '<div class="hero-slot"></div>'+
      (B.rewards && B.rewards.enabled ? '<div class="rewards-mini" data-act="rewards"><div class="rm-left"><small>'+esc(B.rewards.name)+'</small><b>1,250 pts</b><div class="rm-bar"><i></i></div><p>750 pts to your next reward</p></div><div class="rm-right">'+I.card+'</div></div>' : '')+
      (newIn.length ? '<section class="section"><div class="sec-head"><div><h2>New In</h2><p>'+esc(H.newSub||'The latest arrivals')+'</p></div><button class="link" data-act="col" data-v="'+esc(H.newCol)+'">View all</button></div><div class="hscroll">'+newIn.map(p=>pcard(p,{w:400})).join('')+'</div></section>' : '')+
      (SIZE_GROUPS.length ? (hasSize()
        ? '<section class="section"><div class="sec-head"><div><h2>In stock in your size</h2><p>Size '+esc(sizeLabel())+' · ready to ship</p></div><button class="link" data-act="size">Change</button></div>'+(mine.length?'<div class="hscroll">'+mine.map(p=>pcard(p,{w:400})).join('')+'</div>':'<p class="count">Nothing in stock in your size right now. We’ll alert you when it lands.</p>')+'</section>'
        : '<div class="size-cta" data-act="size"><div class="db-ic">'+I.ruler+'</div><div class="db-t"><b>In stock in your size</b><p>Save your size to see what’s ready to ship in it, pre-selected on every product.</p></div>'+I.chev+'</div>') : '')+
      '<div class="drop-banner"><div class="db-ic">'+I.bell+'</div><div class="db-t"><b>Drop alerts</b><p>Be first to know when new pieces land.</p></div><button class="switch '+(prefs.drops?'on':'')+'" id="dropSwitch" aria-label="Toggle drop alerts"></button></div>'+
      (tiles.length ? '<section class="section"><div class="sec-head"><div><h2>Shop by Category</h2></div><button class="link" data-act="tab" data-v="shop">All</button></div><div class="cat-grid">'+tiles.map(t=>'<div class="cat-tile" data-act="col" data-v="'+esc(t[0])+'"><img loading="lazy" src="'+cover(t[0])+'" alt=""><span>'+esc(t[1])+'</span></div>').join('')+'</div></section>' : '')+
      (H.editorial && H.editorial.img && colBy(H.editorial.col) ? '<div class="editorial" data-act="col" data-v="'+esc(H.editorial.col)+'"><img loading="lazy" src="'+esc(H.editorial.img)+'" alt=""><div class="hero-copy"><div class="eyebrow">'+esc(H.editorial.eyebrow||'')+'</div><div class="hero-title">'+esc(H.editorial.title||'')+'</div><span class="btn btn-light">Shop now</span></div></div>' : '')+
      (best.length ? '<section class="section"><div class="sec-head"><div><h2>Best Sellers</h2><p>'+esc(H.bestSub||'The pieces everyone’s wearing')+'</p></div><button class="link" data-act="col" data-v="'+esc(H.bestCol)+'">View all</button></div><div class="hscroll">'+best.map(p=>pcard(p,{w:400})).join('')+'</div></section>' : '')+
      (fc ? '<div class="feature-card" style="margin-top:28px" data-act="col" data-v="'+esc(H.feature.col)+'"><img loading="lazy" src="'+img(fc.im[1]||fc.im[0],700)+'" alt=""><div><b>'+esc(H.feature.title)+'</b><span class="btn btn-light" style="height:40px;padding:0 18px">'+esc(H.feature.cta||'Shop now')+'</span></div></div>' : '')+
      proofHTML()+
      (!ALL.length ? '<div class="empty"><div class="eic">'+I.bag+'</div><h3>Catalogue not found</h3><p>The product feed for '+esc(NAME)+' couldn’t be read, so there’s nothing to show here yet.</p></div>' : '')+
      '<div class="about"><img src="'+LOGO+'" alt="'+esc(NAME)+'"><p>'+esc(B.copy && B.copy.about || '')+'</p></div>'+credit();
    $('.hero-slot', el).replaceWith(heroNode);
    if (heroNode._sync) heroNode._sync();
    $('#dropSwitch', el).addEventListener('click', e => {
      prefs.drops = !prefs.drops; savePrefs();
      e.currentTarget.classList.toggle('on', prefs.drops);
      toast(prefs.drops ? 'Drop alerts on' : 'Drop alerts off', I.bell);
      if (prefs.drops) setTimeout(()=>Demo.newin(), 1300);
    });
    enableDrag(el);
  };
  render();
  // past the hero the band gets denser so it stays readable over light content
  let deep = null;
  el.addEventListener('scroll', () => { const d = el.scrollTop > 480; if (d === deep) return; deep = d; const h = $('.home-head', el); if (h) h.classList.toggle('deep', d); }, {passive:true});
  el._refresh = () => { const st = el.scrollTop; render(); el.scrollTop = st; deep = null; el.dispatchEvent(new Event('scroll')); };
  return { light:true };
}

// ---------- SHOP ----------
function Shop(el, seg){
  seg = seg || 'cats';
  const row = h => { const c = colBy(h), p = prods(h)[0]; if (!c || !p) return ''; return '<div class="cat-row" data-act="col" data-v="'+esc(h)+'"><img loading="lazy" src="'+img(p.im[0],200)+'" alt=""><div><b>'+esc(c.t)+'</b><small>'+c.p.length+' styles</small></div>'+I.chev+'</div>'; };
  const list = (seg === 'cats' ? SH.cats : SH.edits) || [];
  const f = seg === 'cats' ? SH.featureCats : SH.featureEdits;
  const fp = f && prods(f.col)[f.idx||0];
  el.innerHTML = topbar({ title:'', right:'<div class="tb-r">'+searchBtn()+bagBtn()+'</div>', left:'<span style="width:40px"></span>' }) +
    '<div class="large-title"><small>'+esc(SH.kicker || NAME)+'</small>Shop</div>'+
    '<div class="seg"><button class="'+(seg==='cats'?'on':'')+'" data-seg="cats">Shop by Product</button><button class="'+(seg==='edits'?'on':'')+'" data-seg="edits">Collections</button></div>'+
    (fp ? '<div class="feature-card" data-act="col" data-v="'+esc(f.col)+'"><img src="'+img(fp.im[0],700)+'" alt=""><div><b>'+esc(f.title)+'</b><span class="btn btn-light" style="height:40px;padding:0 18px">'+esc(f.cta||'Shop now')+'</span></div></div>' : '')+
    '<div class="cat-list">'+list.map(row).join('')+'</div>'+(list.length?'':'<div class="empty"><h3>No collections found</h3></div>')+credit();
  $$('.seg button', el).forEach(b => b.addEventListener('click', () => { el.innerHTML=''; Shop(el, b.dataset.seg); }));
}

// ---------- COLLECTION ----------
function Collection(el, h){
  const c = colBy(h);
  if (!c){ el.innerHTML = topbar({back:true,title:'Not found'}) + '<div class="empty"><h3>Collection unavailable</h3><button class="btn btn-dark" data-act="back">Go back</button></div>'; return {}; }
  let sort = 'featured', stockOnly = false, mineOnly = store.get('mineOnly', false) && hasSize();
  const sizeFilterHTML = () => SIZE_GROUPS.length ? '<div class="size-filter"><div><b>Only show items in stock in my size</b><small>'+(hasSize()?'Your size: '+esc(sizeLabel())+' · <u data-sz>change</u>':'Set your size to use this filter')+'</small></div><span class="switch '+(mineOnly?'on':'')+'"></span></div>' : '';
  const render = () => {
    let list = prods(h);
    if (stockOnly) list = list.filter(p => p.sz.some(s=>s[1]));
    if (mineOnly) list = list.filter(inMySize);
    if (sort === 'low') list = list.slice().sort((a,b)=>a.p-b.p);
    if (sort === 'high') list = list.slice().sort((a,b)=>b.p-a.p);
    if (sort === 'sale') list = list.filter(p=>p.cp>p.p);
    $('.count', el).textContent = list.length + ' styles' + (mineOnly ? ' in stock in size '+sizeLabel() : '');
    const sfw = $('.sf-wrap', el); if (sfw) sfw.innerHTML = sizeFilterHTML();
    $('.grid', el).innerHTML = list.map(p=>pcard(p, {dropGrid: h==='__drop'})).join('');
    const em = $('.grid-empty', el);
    em.innerHTML = list.length ? '' : (mineOnly
      ? '<div class="empty" style="padding-top:30px"><div class="eic">'+I.ruler+'</div><h3>Nothing in your size here</h3><p>None of the '+prods(h).length+' styles in '+esc(c.t)+' are in stock in size '+esc(sizeLabel())+' right now. Turn on back-in-size alerts and we’ll tell you the moment they’re back.</p><div class="btns col"><button class="btn btn-dark" id="emAlert">'+(prefs.restock?'Back-in-size alerts on ✓':'Get back-in-size alerts')+'</button><button class="btn btn-outline" id="emAll">Show all sizes</button><button class="link" id="emSize">Change my size</button></div></div>'
      : '<div class="empty" style="padding-top:30px"><h3>No styles match</h3><p>Try a different filter.</p></div>');
    if (!list.length && mineOnly){
      $('#emAlert', el).addEventListener('click', e => { prefs.restock = true; savePrefs(); e.currentTarget.textContent = 'Back-in-size alerts on ✓'; toast('We’ll alert you when size '+sizeLabel()+' is back', I.bell); });
      $('#emAll', el).addEventListener('click', () => { mineOnly = false; store.set('mineOnly', false); render(); });
      $('#emSize', el).addEventListener('click', () => openSizeSheet());
    }
  };
  const hasSale = prods(h).some(p=>p.cp>p.p);
  el.innerHTML = topbar({ back:true, title:c.t, right:bagBtn() }) +
    '<div class="large-title"><small>'+esc(h==='__drop' ? 'First look' : NAME)+'</small>'+esc(c.t)+'</div>'+
    '<div class="chips">'+[['featured','Featured'],['low','Price: Low–High'],['high','Price: High–Low']].concat(hasSale?[['sale','On sale']]:[]).map(s=>'<button class="chip '+(s[0]===sort?'on':'')+'" data-sort="'+s[0]+'">'+s[1]+'</button>').join('')+'<button class="chip" data-stock>In stock</button></div>'+
    '<div class="sf-wrap"></div><div class="count"></div><div class="grid"></div><div class="grid-empty"></div>'+credit();
  $$('[data-sort]', el).forEach(b => b.addEventListener('click', () => { sort=b.dataset.sort; $$('[data-sort]',el).forEach(x=>x.classList.toggle('on',x===b)); render(); }));
  $('[data-stock]', el).addEventListener('click', e => { stockOnly=!stockOnly; e.currentTarget.classList.toggle('on',stockOnly); render(); });
  $('.sf-wrap', el).addEventListener('click', e => {
    if (!e.target.closest('.size-filter')) return;
    if (e.target.closest('[data-sz]') || !hasSize()) { openSizeSheet(() => { if (hasSize()){ mineOnly = true; store.set('mineOnly', true); } render(); }); return; }
    mineOnly = !mineOnly; store.set('mineOnly', mineOnly); render();
  });
  render(); enableDrag(el);
  el._refresh = () => { if (!hasSize()) mineOnly = false; render(); };
}

// ---------- PDP ----------
function PDP(el, h){
  const p = P[h];
  if (!p){ el.innerHTML = topbar({back:true,title:'Not found'}) + '<div class="empty"><h3>Product unavailable</h3><button class="btn btn-dark" data-act="back">Go back</button></div>'; return {}; }
  let size = null;
  const coming = isComing(h);
  const sibs = ALL.filter(x => x.n === p.n);
  const generic = [H.newCol, H.bestCol, H.hero && H.hero.col, '__drop'].concat(SH.edits||[]);
  const related = ((COLS.find(c => !generic.includes(c.h) && c.p.includes(h)) || colBy(H.newCol) || {p:[]}).p).filter(x=>x!==h && P[x]).slice(0,10).map(x=>P[x]);
  const long = p.sz.some(s => s[0].length > 4);
  const sale = p.cp > p.p, pd = priceDrop && priceDrop.h === h;
  const soldOut = p.sz.every(s=>!s[1]);
  const mineAvail = hasSize() ? p.sz.find(s => s[1] && sizeMatch(s[0])) : null;
  const mineOut = hasSize() && !mineAvail && p.sz.some(s => sizeMatch(s[0]));
  if (mineAvail) size = mineAvail[0];
  const ship = (SHIP.options||[]);
  el.classList.add('pdp');
  el.innerHTML =
    '<div class="pdp-top"><button class="icon-btn glass" data-act="back" aria-label="Back">'+I.back+'</button><div class="r"><button class="icon-btn glass" id="shareBtn" aria-label="Share">'+I.share+'</button><button class="icon-btn glass" data-act="bagtab" aria-label="Bag">'+I.bag+'</button></div></div>'+
    '<div class="pscroll"><div class="gallery"><div class="gtrack">'+p.im.map((u,i)=>'<img src="'+img(u,800)+'" '+(i>1?'loading="lazy"':'')+' alt="'+esc(p.t)+' image '+(i+1)+'" draggable="false">').join('')+'</div>'+
      (coming?'<span class="g-badge">Coming soon · First look</span>':pd?'<span class="g-badge drop">Price drop</span>':'')+
      '<div class="gdots">'+p.im.map((_,i)=>'<i class="'+(i?'':'on')+'"></i>').join('')+'</div><span class="gcount">1 / '+p.im.length+'</span></div>'+
    '<div class="pdp-info">'+
      '<div class="ptype">'+esc(p.ty || NAME)+'</div><h1>'+esc(p.n)+'</h1>'+(p.c?'<div class="pc">'+esc(p.c)+'</div>':'')+
      (sale ? '<div class="price sale"><b>'+money(p.p)+'</b><s>'+money(p.cp)+'</s>'+(pd?'<span class="pd-badge">Price drop</span>':'')+'</div>' : '<div class="price">'+money(p.p)+'</div>')+
      '<div class="klarna">Or 3 payments of '+money(p.p/3)+' with Klarna</div>'+proofHTML(true)+
      (coming ? '<div class="soon-note">'+I.drop+'<div><b>DROP '+esc(DR.num)+' / '+esc(DR.name)+'</b><span>App early access '+fmtDay(dropTimes().app)+'. Website 24 hours later.</span></div></div>' : '')+
      (sibs.length > 1 ? '<div class="label-row"><b>Colour</b><span>'+esc(p.c)+'</span></div><div class="swatches">'+sibs.map(s=>'<button class="swatch '+(s.h===h?'on':'')+'" data-sib="'+esc(s.h)+'" aria-label="'+esc(s.c)+'"><img loading="lazy" src="'+img(s.im[0],150)+'" alt=""></button>').join('')+'</div>' : '')+
      '<div class="label-row"><b>Size</b><span id="sizeLbl">'+(mineAvail?'Your saved size: '+esc(prettySize(size)):mineOut?'Your size ('+esc(sizeLabel())+') is sold out':'Select a size')+'</span></div>'+
      '<div class="sizes">'+p.sz.map(s=>'<button class="size '+(long?'sm ':'')+(s[1]?'':'out ')+(s[0]===size?'on ':'')+(hasSize()&&sizeMatch(s[0])?'mine':'')+'" data-size="'+esc(s[0])+'" data-in="'+s[1]+'">'+esc(prettySize(s[0]))+'</button>').join('')+'</div>'+
      '<div class="size-hint">'+I.bell+'<span>'+(mineOut?'Tap your size for a back-in-size alert':'Tap a sold-out size for a back-in-stock alert')+'</span>'+(SIZE_GROUPS.length?'<button class="link sm" data-act="size">'+(hasSize()?'Change size':'Save my size')+'</button>':'')+'</div>'+
      '<div class="perks">'+(B.pdpPerks||[]).slice(0,3).map((t,i)=>'<div>'+[I.truck,I.ret,I.star][i]+esc(t)+'</div>').join('')+'</div>'+
      '<div class="acc">'+
        '<details open><summary>Description'+I.plus+'</summary><div class="acc-body">'+esc(p.d || 'Designed by '+NAME+'.')+'</div></details>'+
        (ship.length ? '<details><summary>Delivery'+I.plus+'</summary><div class="acc-body"><ul>'+ship.map(o=>'<li><b>'+esc(o.name)+'</b> — '+(o.price?money(o.price):'Free')+(o.freeOver?', free on orders over '+money(o.freeOver):'')+(o.desc?', '+esc(o.desc):'')+'</li>').join('')+(SHIP.notes||[]).map(n=>'<li>'+esc(n)+'</li>').join('')+'</ul></div></details>' : '')+
        (B.returns && B.returns.summary ? '<details><summary>Returns'+I.plus+'</summary><div class="acc-body">'+esc(B.returns.summary)+'</div></details>' : '')+
      '</div>'+
    '</div>'+
    (related.length ? '<section class="section"><div class="sec-head"><h2>You may also like</h2></div><div class="hscroll">'+related.map(r=>pcard(r,{w:400})).join('')+'</div></section>' : '')+credit()+'</div>'+
    '<div class="buybar show"><button class="hbtn '+(inWish(h)?'on':'')+'" data-act="wish" data-v="'+esc(h)+'" data-wish="'+esc(h)+'" aria-label="Save">'+I.heart+'</button><button class="btn btn-dark" id="addBtn">'+(coming?(dropNotify?'On the list ✓':'Notify me when it drops'):soldOut?'Notify me':'Add to bag — '+money(p.p))+'</button></div>';

  const track = $('.gtrack', el), dots = $$('.gdots i', el), cnt = $('.gcount', el);
  const idx = () => Math.round(track.scrollLeft / track.clientWidth);
  track.addEventListener('scroll', () => { const i = idx(); dots.forEach((d,j)=>d.classList.toggle('on', i===j)); cnt.textContent = (i+1)+' / '+p.im.length; }, {passive:true});
  const go = i => track.scrollTo({ left: Math.max(0, Math.min(p.im.length-1, i)) * track.clientWidth, behavior:'smooth' });
  dots.forEach((d,i)=>d.addEventListener('click',()=>go(i)));
  let sx = null;
  track.addEventListener('pointerdown', e => { if (e.pointerType==='mouse'){ sx = e.clientX; e.preventDefault(); } });
  track.addEventListener('pointerup', e => { if (sx===null) return; const dx = e.clientX - sx; sx = null; if (Math.abs(dx) > 30) go(idx() + (dx<0?1:-1)); else go(idx()+1 >= p.im.length ? 0 : idx()+1); });
  track.addEventListener('pointerleave', () => sx = null);

  $$('[data-sib]', el).forEach(b => b.addEventListener('click', () => { if (b.dataset.sib !== h){ const v = stack[stack.length-1]; v.args = b.dataset.sib; el.innerHTML=''; PDP(el, b.dataset.sib); } }));
  $$('.size', el).forEach(b => b.addEventListener('click', () => {
    if (b.dataset.in === '0'){ toast('We’ll alert you when '+prettySize(b.dataset.size)+' is back', I.bell); return; }
    size = b.dataset.size; $$('.size', el).forEach(x=>x.classList.toggle('on', x===b));
    const l = $('#sizeLbl', el); l.textContent = (sizeMatch(size)?'Your saved size: ':'Size ') + prettySize(size); l.style.color='';
  }));
  $('#addBtn', el).addEventListener('click', e => {
    if (coming) { dropNotify = true; store.set('dropNotify', true); e.currentTarget.textContent = 'On the list ✓'; toast('We’ll notify you when DROP '+DR.num+' opens', I.bell); return; }
    if (soldOut) { toast('We’ll alert you when it’s back in stock', I.bell); return; }
    if (!size){ const sz = $('.sizes', el); sz.classList.remove('shake'); void sz.offsetWidth; sz.classList.add('shake'); const l=$('#sizeLbl', el); l.textContent = 'Please select a size'; l.style.color='var(--sale)'; sz.scrollIntoView({behavior:'smooth', block:'center'}); return; }
    addToBag(h, size);
  });
  $('#shareBtn', el).addEventListener('click', () => {
    const url = SITE + '/products/' + h;
    if (navigator.share) navigator.share({ title:p.t, url }).catch(()=>{});
    else { navigator.clipboard && navigator.clipboard.writeText(url).catch(()=>{}); toast('Link copied', I.share); }
  });
  enableDrag(el);
  el._refresh = () => $$('[data-wish]', el).forEach(b => b.classList.toggle('on', inWish(b.dataset.v)));
  return { hideTabs:true };
}
function addToBag(h, size, silent){
  const p = P[h];
  const ex = bag.find(i => i.h===h && i.s===size);
  if (ex) ex.q++; else bag.push({ h, s:size, q:1 });
  saveBag();
  if (silent) return;
  const total = bag.reduce((a,i)=>a+P[i.h].p*i.q,0);
  const left = FREE_SHIP - total;
  openSheet('<h3>Added to bag</h3><div class="added"><img src="'+img(p.im[0],200)+'" alt=""><div><b>'+esc(p.t)+'</b><small>Size '+esc(prettySize(size))+' · '+money(p.p)+'</small></div></div>'+
    (FREE_SHIP ? '<div class="ship-prog" style="margin:0 0 16px"><p>'+(left>0?'You’re <b>'+money(left)+'</b> away from free '+esc(SHIP.region||'')+' delivery':'<b>You’ve unlocked free '+esc(SHIP.region||'')+' delivery</b>')+'</p><div class="bar"><i style="width:'+Math.min(100,total/FREE_SHIP*100)+'%"></i></div></div>' : '')+
    '<div class="btns"><button class="btn btn-dark btn-block" id="goBag">View bag & checkout</button><button class="btn btn-outline btn-block" data-act="close">Continue shopping</button></div>',
    s => $('#goBag', s).addEventListener('click', () => { closeSheet(); switchTab('bag'); }));
}

// ---------- BAG ----------
const baseShip = () => (SHIP.options||[])[0] || { name:'Standard delivery', price:0 };
function bagTotals(){
  const sub = bag.reduce((a,i)=>a+P[i.h].p*i.q,0);
  const disc = promo ? Math.round(sub*DISC.pct)/100 : 0;
  const o = baseShip();
  const ship = (o.freeOver && sub >= o.freeOver) ? 0 : (o.price||0);
  return { sub, disc, ship, total: sub - disc + ship, cnt: bag.reduce((a,i)=>a+i.q,0) };
}
function Bag(el){
  const render = () => {
    if (!bag.length){
      el.innerHTML = topbar({title:'Bag'}) + '<div class="empty"><div class="eic">'+I.bag+'</div><h3>Your bag is empty</h3><p>'+esc(B.copy && B.copy.emptyBag || 'Start with the latest arrivals.')+'</p>'+(colBy(H.newCol)?'<button class="btn btn-dark" data-act="col" data-v="'+esc(H.newCol)+'">Shop New In</button>':'')+'</div>'+
        (prods(H.bestCol).length ? '<section class="section"><div class="sec-head"><h2>Best Sellers</h2></div><div class="hscroll">'+prods(H.bestCol).slice(0,8).map(p=>pcard(p,{w:400})).join('')+'</div></section>' : '')+credit();
      enableDrag(el); return;
    }
    const T = bagTotals(), o = baseShip();
    const saved = bag.reduce((a,i)=>a+(P[i.h].cp>P[i.h].p?(P[i.h].cp-P[i.h].p)*i.q:0),0);
    el.innerHTML = topbar({title:'Bag ('+T.cnt+')'}) +
      (FREE_SHIP ? '<div class="ship-prog"><p>'+(T.sub<FREE_SHIP?'Spend <b>'+money(FREE_SHIP-T.sub)+'</b> more for free '+esc(SHIP.region||'')+' delivery':'<b>Free '+esc(SHIP.region||'')+' delivery unlocked</b> — '+esc(o.name))+'</p><div class="bar"><i style="width:'+Math.min(100,T.sub/FREE_SHIP*100)+'%"></i></div></div>' : '')+
      bag.map((it,ix)=>{ const p=P[it.h]; return '<div class="bag-item" data-ix="'+ix+'"><img src="'+img(p.im[0],250)+'" alt="" data-act="pdp" data-v="'+esc(p.h)+'"><div class="bi-info"><b>'+esc(p.n)+'</b><small>'+esc(p.c)+(p.c?' · ':'')+'Size '+esc(prettySize(it.s))+'</small>'+priceHTML(p)+
        '<div class="bi-bottom"><div class="qty"><button data-q="-1" aria-label="Decrease">−</button><span>'+it.q+'</span><button data-q="1" aria-label="Increase">+</button></div><button class="remove" data-rm>Remove</button></div></div></div>'; }).join('')+
      (promo ? '<div class="promo on">'+I.tag+'<div><b>'+esc(DISC.code)+' applied</b><small>'+DISC.pct+'% off your first app order</small></div><button class="remove" id="promoRm">Remove</button></div>'
             : '<button class="promo" id="promoAdd">'+I.gift+'<div><b>First app order?</b><small>Tap to apply '+esc(DISC.code)+' for '+DISC.pct+'% off</small></div><span class="promo-cta">Apply</span></button>')+
      '<div class="summary"><div class="row"><span>Subtotal</span><span>'+money(T.sub)+'</span></div>'+(saved?'<div class="row" style="color:var(--sale)"><span>You’re saving</span><span>−'+money(saved)+'</span></div>':'')+
        (promo?'<div class="row disc"><span>'+esc(DISC.code)+' ('+DISC.pct+'% off)</span><span>−'+money(T.disc)+'</span></div>':'')+
        '<div class="row"><span>Delivery ('+esc(o.short||o.name)+')</span><span>'+(T.ship?money(T.ship):'Free')+'</span></div><div class="row total"><span>Total</span><span id="bagTotal">'+money(T.total)+'</span></div>'+
        (B.rewards && B.rewards.enabled ? '<div class="pts">'+I.star+'<span>Members earn '+esc(B.rewards.name)+' points on this order</span></div>' : '')+'</div>'+
      '<div class="pay-row"><button class="btn btn-dark btn-block" id="checkout" style="height:52px">Checkout — '+money(T.total)+'</button><button class="apple-pay" id="applePay">'+I.apple+'Pay</button><div class="pay-icons"><span>Klarna</span>·<span>PayPal</span>·<span>Shop Pay</span>·<span>Google Pay</span></div></div>'+credit();
    $$('.bag-item', el).forEach(row => {
      const ix = +row.dataset.ix;
      $$('[data-q]', row).forEach(b => b.addEventListener('click', () => { bag[ix].q += +b.dataset.q; if (bag[ix].q < 1){ removeAt(row, ix); return; } saveBag(); render(); }));
      $('[data-rm]', row).addEventListener('click', () => removeAt(row, ix));
    });
    const pa = $('#promoAdd', el); if (pa) pa.addEventListener('click', () => { promo = true; store.set('promo', true); render(); toast(DISC.code+' applied, '+DISC.pct+'% off', I.tag); });
    const pr = $('#promoRm', el); if (pr) pr.addEventListener('click', () => { promo = false; store.set('promo', false); render(); toast(DISC.code+' removed'); });
    $('#checkout', el).addEventListener('click', () => checkout());
    $('#applePay', el).addEventListener('click', () => checkout(true));
  };
  const removeAt = (row, ix) => { row.classList.add('removing'); setTimeout(()=>{ bag.splice(ix,1); saveBag(); render(); toast('Removed from bag'); }, 320); };
  render();
  el._refresh = render;
}
function checkout(quick){
  const T = bagTotals();
  const opts = (SHIP.options && SHIP.options.length ? SHIP.options : [{id:'std',name:'Standard delivery',desc:'',price:0}]).slice(0,4).map(o => [o.id, o.name, o.desc||'', (o.freeOver && T.sub >= o.freeOver) ? 0 : (o.price||0)]);
  let sel = opts[0][0];
  const totalFor = () => T.sub - T.disc + opts.find(o=>o[0]===sel)[3];
  openSheet('<h3 style="margin-bottom:4px">Checkout</h3><p class="co-sub">'+I.lock+'Shopify checkout, inside the app</p>'+
    '<div class="express"><button class="xp apple" data-pay="Apple Pay">'+I.apple+'Pay</button><button class="xp shop" data-pay="Shop Pay"><b>shop</b><span>Pay</span></button><button class="xp klarna" data-pay="Klarna"><b>Klarna.</b><span id="klarna3">3 payments of '+money(totalFor()/3)+'</span></button></div>'+
    '<div class="or"><span>or pay by card</span></div>'+
    '<div class="co-row"><div>Deliver to<small>Your saved address</small></div><span>Change</span></div>'+
    opts.map(o=>'<div class="ship-opt '+(o[0]===sel?'on':'')+'" data-o="'+esc(o[0])+'"><i class="radio"></i><div>'+esc(o[1])+'<small>'+esc(o[2])+'</small></div><span>'+(o[3]?money(o[3]):'Free')+'</span></div>').join('')+
    (promo?'<div class="co-row"><div>Discount<small>'+esc(DISC.code)+', '+DISC.pct+'% off first app order</small></div><span style="color:var(--sale)">−'+money(T.disc)+'</span></div>':'')+
    '<div class="co-row" style="margin-top:8px"><div>Pay with<small>'+(quick?'Apple Pay':'Card ending ···· 4242')+'</small></div><span>Change</span></div>'+
    '<div class="co-row"><div><b>Total</b></div><span id="coTotal" style="font-size:15px;font-weight:600">'+money(totalFor())+'</span></div>'+
    '<div class="btns" style="margin-top:12px"><button class="'+(quick?'apple-pay':'btn btn-dark btn-block')+'" id="payNow">'+(quick?I.apple+'Pay':'Place order')+'</button></div>'+
    '<p class="center" style="font-size:10.5px;margin:12px 0 0">Concept demo — no order is placed and no payment is taken.</p>',
    s => {
      $$('.ship-opt', s).forEach(o => o.addEventListener('click', () => { sel = o.dataset.o; $$('.ship-opt', s).forEach(x=>x.classList.toggle('on',x===o)); $('#coTotal', s).textContent = money(totalFor()); $('#klarna3', s).textContent = '3 payments of '+money(totalFor()/3); }));
      const done = (method) => {
        const ref = (NAME[0]||'R').toUpperCase() + Math.floor(100000 + Math.random()*899999);
        const paid = totalFor();
        bag = []; saveBag(); if (promo){ promo = false; store.set('promo', false); }
        openSheet('<div class="check-anim">'+I.check+'</div><h3>Order confirmed</h3><p class="center">Demo order #'+ref+' · '+money(paid)+' via '+esc(method)+'.<br>Nothing was charged and no real order was placed.<br>In the live app you’d get tracking updates on your lock screen.</p><div class="btns"><button class="btn btn-dark btn-block" id="contShop">Continue shopping</button>'+(B.rewards&&B.rewards.enabled?'<button class="btn btn-outline btn-block" id="seeRw">View '+esc(B.rewards.name)+'</button>':'')+'</div>',
          s2 => { $('#contShop', s2).addEventListener('click', () => { closeSheet(); switchTab('home'); }); const rw = $('#seeRw', s2); if (rw) rw.addEventListener('click', () => { closeSheet(); push(Rewards); }); });
        if (currentTab==='bag') stack[0].el._refresh();
      };
      $$('.xp', s).forEach(b => b.addEventListener('click', () => done(b.dataset.pay)));
      $('#payNow', s).addEventListener('click', () => done(quick ? 'Apple Pay' : 'card'));
    });
}

// ---------- WISHLIST ----------
function Wishlist(el){
  const render = () => {
    el.innerHTML = topbar({title:'Wishlist'}) + '<div class="large-title"><small>Saved for later</small>Wishlist</div>' +
      (wish.length ? '<div class="count">'+wish.length+' saved '+(wish.length===1?'item':'items')+' · we’ll let you know if prices drop</div><div class="grid">'+wish.map(h=>pcard(P[h])).join('')+'</div>'
                   : '<div class="empty" style="padding-top:40px"><div class="eic">'+I.heart+'</div><h3>Nothing saved yet</h3><p>Tap the heart on any piece to save it here — we’ll alert you if the price drops or your size is running low.</p>'+(H.hero&&colBy(H.hero.col)?'<button class="btn btn-dark" data-act="col" data-v="'+esc(H.hero.col)+'">'+esc(H.hero.cta||'Shop now')+'</button>':'')+'</div>') + credit();
  };
  render();
  el._refresh = render;
  el.addEventListener('click', e => { if (e.target.closest('[data-act="wish"]')) setTimeout(render, 380); });
}

// ---------- SEARCH ----------
function Search(el, q0){
  const TR = (B.search && B.search.trending) || [];
  const POP = ((B.search && B.search.popular) || []).filter(h => prods(h).length);
  el.innerHTML = '<div class="searchbar"><button class="icon-btn" data-act="back" aria-label="Back">'+I.back+'</button><label class="sfield">'+I.search+'<input id="sq" type="search" placeholder="Search '+esc(NAME)+'" autocomplete="off" enterkeyhint="search"><button class="clear" id="sclear" aria-label="Clear">×</button></label></div><div id="sbody"></div>';
  const inp = $('#sq', el), body = $('#sbody', el), field = $('.sfield', el);
  const bindQ = () => $$('[data-q]', body).forEach(b => b.addEventListener('click', () => { inp.value = b.dataset.q; run(true); }));
  const idle = () => {
    body.innerHTML =
      (recent.length ? '<div class="s-sec"><h4>Recent</h4><div class="chips">'+recent.map(r=>'<button class="chip" data-q="'+esc(r)+'">'+esc(r)+'</button>').join('')+'</div></div>' : '')+
      (TR.length ? '<div class="s-sec"><h4>Trending</h4><div class="chips">'+TR.map(r=>'<button class="chip" data-q="'+esc(r)+'">'+esc(r)+'</button>').join('')+'</div></div>' : '')+
      (POP.length ? '<div class="s-sec"><h4>Popular categories</h4></div><div class="cat-list">'+POP.map(h=>{const c=colBy(h),p=prods(h)[0];return '<div class="cat-row" data-act="col" data-v="'+esc(h)+'"><img loading="lazy" src="'+img(p.im[0],200)+'" alt=""><div><b>'+esc(c.t)+'</b><small>'+c.p.length+' styles</small></div>'+I.chev+'</div>';}).join('')+'</div>' : '')+credit();
    bindQ();
  };
  const run = (commit) => {
    const q = inp.value.trim().toLowerCase();
    field.classList.toggle('has', !!q);
    if (!q) return idle();
    const terms = q.split(/\s+/);
    const res = ALL.filter(p => { const hay = (p.t+' '+p.ty).toLowerCase(); return terms.every(t => hay.includes(t)); });
    if (commit){ recent = [inp.value.trim(), ...recent.filter(r=>r.toLowerCase()!==q)].slice(0,5); store.set('recent', recent); }
    const re = new RegExp('('+terms.map(t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')','ig');
    body.innerHTML = res.length
      ? '<div class="count" style="padding-top:4px">'+res.length+' results for “'+esc(inp.value.trim())+'”</div><div class="s-res">'+res.slice(0,40).map(p=>'<div class="s-row" data-act="pdp" data-v="'+esc(p.h)+'"><img loading="lazy" src="'+img(p.im[0],150)+'" alt=""><div><b>'+esc(p.t).replace(re,'<mark>$1</mark>')+'</b><small>'+esc(p.ty)+'</small></div>'+priceHTML(p)+'</div>').join('')+'</div>'
      : '<div class="empty" style="padding-top:40px"><div class="eic">'+I.search+'</div><h3>No results</h3><p>Nothing matched “'+esc(inp.value.trim())+'”. Try a trending search instead.</p><div class="chips" style="justify-content:center;flex-wrap:wrap">'+TR.slice(0,4).map(r=>'<button class="chip" data-q="'+esc(r)+'">'+esc(r)+'</button>').join('')+'</div></div>';
    bindQ();
  };
  inp.addEventListener('input', () => run(false));
  inp.addEventListener('keydown', e => { if (e.key === 'Enter'){ run(true); inp.blur(); } });
  $('#sclear', el).addEventListener('click', e => { e.preventDefault(); inp.value=''; run(); inp.focus(); });
  if (q0){ inp.value = q0; run(true); } else idle();
  if (window.matchMedia('(min-width:521px)').matches) setTimeout(()=>inp.focus({preventScroll:true}), 300);
}

// ---------- DROPS ----------
function Drops(el){
  const render = () => {
    const t = dropTimes();
    const items = (DR.products||[]).map(h=>P[h]).filter(Boolean);
    const prev = DR.previous && colBy(DR.previous.col) ? DR.previous : null;
    el.innerHTML = topbar({title:'', right:bagBtn()}) +
      '<div class="large-title"><small>App early access</small>Drops</div>'+
      '<div class="drop-card'+(dropLive?' live':'')+'"><img src="'+esc(dropImg()||'')+'" alt=""><div class="dc-in">'+
        '<div class="dc-tag">'+(dropLive?'<span class="live-dot"></span>Live now for app users':'Next drop')+'</div>'+
        '<div class="dc-title">DROP '+esc(DR.num)+' <span>/</span> '+esc(DR.name)+'</div>'+(DR.title&&DR.title!==DR.name?'<div class="dc-sub">'+esc(DR.title)+'</div>':'')+
        (dropLive ? '<div class="cd"><div class="wide"><b>LIVE</b><small>Website opens '+t.web.toLocaleDateString('en-GB',{weekday:'long'})+'</small></div></div>' : '<div class="cd">'+cdHTML()+'</div>')+
        '<p class="dc-early">'+I.bolt+'App users get in 24 hours before the website</p>'+
        (dropLive ? '<button class="btn btn-light btn-block" data-act="col" data-v="__drop">Shop the drop</button>'
                  : '<button class="btn btn-light btn-block" id="notifyBtn">'+(dropNotify?'You’re on the list ✓':'Notify me when it opens')+'</button>')+
      '</div></div>'+
      '<div class="drop-times"><div><small>App early access</small><b>'+fmtDay(t.app)+'</b></div><div><small>Website</small><b>'+fmtDay(t.web)+'</b></div></div>'+
      (items.length ? '<section class="section"><div class="sec-head"><div><h2>First Look</h2><p>'+items.length+' pieces from '+esc(DR.title||DR.name)+'</p></div>'+(dropLive?'<button class="link" data-act="col" data-v="__drop">View all</button>':'')+'</div><div class="grid">'+items.map(p=>pcard(p,{dropGrid:true})).join('')+'</div></section>' : '')+
      (prev ? '<section class="section"><div class="sec-head"><div><h2>Latest drop</h2><p>Out now</p></div></div><div class="feature-card" data-act="col" data-v="'+esc(prev.col)+'"><img loading="lazy" src="'+img((prods(prev.col)[0]||{im:['']}).im[0],700)+'" alt=""><div><b>'+esc(prev.title)+'</b><span class="btn btn-light" style="height:40px;padding:0 18px">Shop now</span></div></div></section>' : '')+
      '<div class="drop-banner"><div class="db-ic">'+I.bell+'</div><div class="db-t"><b>Early access alerts</b><p>Get a push the moment app early access opens.</p></div><button class="switch '+(prefs.early?'on':'')+'" id="earlySw" aria-label="Early access alerts"></button></div>'+credit();
    const nb = $('#notifyBtn', el);
    if (nb) nb.addEventListener('click', () => { dropNotify = !dropNotify; store.set('dropNotify', dropNotify); if (dropNotify){ prefs.early = true; savePrefs(); } render(); toast(dropNotify ? 'We’ll notify you when DROP '+DR.num+' opens' : 'Notification cancelled', I.bell); });
    $('#earlySw', el).addEventListener('click', e => { prefs.early = !prefs.early; savePrefs(); e.currentTarget.classList.toggle('on', prefs.early); toast(prefs.early?'Early access alerts on':'Early access alerts off', I.bell); });
  };
  render();
  el._refresh = render;
}

// ---------- ACCOUNT ----------
function Account(el){
  const prefRows = [['drops','New drops','The moment a new collection lands'],['early','Early access','App-only access 24 hours before the website'],['restock','Back in stock','When your size comes back'],['price','Price drops','On items in your wishlist'],['orders','Order updates','Dispatch and live delivery tracking']];
  const group = (key, title) => { const list = PAGES[key]; return list && list.length ? '<details class="acct-acc"><summary>'+esc(title)+I.plus+'</summary><div>'+list.map((pg,i)=>'<button class="link-row" data-page="'+key+':'+i+'">'+esc(pg.t)+I.chev+'</button>').join('')+'</div></details>' : ''; };
  const render = () => {
    el.innerHTML = topbar({title:'', right:bagBtn()}) +
      '<div class="large-title"><small>'+esc(NAME)+'</small>Account</div>'+
      (signedIn ? '<div class="acct-card"><div class="av">'+I.user+'</div><div><b>Signed in (demo)</b><small>Nothing was saved or sent</small></div><button class="link" id="signOut">Sign out</button></div>'
                : '<div class="acct-card"><div class="av">'+I.user+'</div><div><b>Welcome</b><small>Log in for faster checkout, order tracking and early access.</small></div></div><div class="acct-btns"><button class="btn btn-dark" data-act="login">Log in</button><button class="btn btn-outline" data-act="signup">Sign up</button></div>')+
      (B.rewards && B.rewards.enabled ? '<div class="rewards-mini" data-act="rewards" style="margin-top:14px"><div class="rm-left"><small>'+esc(B.rewards.name)+'</small><b>1,250 pts</b><div class="rm-bar"><i></i></div><p>Tap to show your card</p></div><div class="rm-right">'+I.card+'</div></div>' : '')+
      (SIZE_GROUPS.length ? '<div class="s-sec acct-h"><h4>Your size</h4></div><div class="acct-size">'+SIZE_GROUPS.map(g=>'<div class="label-row" style="margin:4px 0 8px"><b>'+esc(g.label)+'</b>'+(mySize[g.key]?'<span>Saved: '+esc((g.prefix||'')+mySize[g.key])+'</span>':'<span>Not set</span>')+'</div><div class="sizes">'+g.opts.map(o=>'<button class="size'+(String(mySize[g.key])===String(o)?' on':'')+'" data-g="'+esc(g.key)+'" data-o="'+esc(o)+'">'+esc((g.prefix||'')+o)+'</button>').join('')+'</div>').join('')+'<p class="acct-note">'+I.ruler+'<span>Pre-selected on product pages, used for the “in my size” filter and back-in-size alerts.</span></p></div>' : '')+
      '<div class="s-sec acct-h"><h4>Notifications</h4></div>'+
      prefRows.map(x=>'<div class="pref" data-pref="'+x[0]+'"><div><b>'+x[1]+'</b><small>'+x[2]+'</small></div><span class="switch '+(prefs[x[0]]?'on':'')+'"></span></div>').join('')+
      '<div class="s-sec acct-h"><h4>Information</h4></div><div class="acct-groups">'+group('help','Help')+group('about','About')+group('legal','Legal')+'</div>'+
      '<div class="acct-foot">'+(IG?'<a class="ig" href="https://www.instagram.com/'+esc(IG)+'/" target="_blank" rel="noopener">'+I.ig+'@'+esc(IG)+'</a>':'')+'<img src="'+LOGO+'" alt="'+esc(NAME)+'"><p>Version 1.0, concept</p></div>'+credit();
    $$('.acct-size .size', el).forEach(b => b.addEventListener('click', () => {
      const g = b.dataset.g; mySize[g] = String(mySize[g])===b.dataset.o ? null : b.dataset.o; store.set('size', mySize);
      toast(mySize[g] ? 'Saved size: '+sizeLabel() : 'Size cleared', I.ruler); const st = el.scrollTop; render(); el.scrollTop = st;
    }));
    $$('.pref', el).forEach(r => r.addEventListener('click', () => { const k = r.dataset.pref; prefs[k] = !prefs[k]; savePrefs(); $('.switch',r).classList.toggle('on', prefs[k]); toast(r.querySelector('b').textContent+(prefs[k]?' on':' off'), I.bell); }));
    $$('[data-page]', el).forEach(b => b.addEventListener('click', () => { const [g,i] = b.dataset.page.split(':'); openBrowser(PAGES[g][+i]); }));
    const so = $('#signOut', el); if (so) so.addEventListener('click', () => { signedIn = false; render(); toast('Signed out'); });
  };
  render();
  el._refresh = () => { const st = el.scrollTop; render(); el.scrollTop = st; };
}
const demoNote = '<div class="demo-note">'+I.lock+'<span><b>Demo only.</b> This is a concept. Nothing you type is saved or sent anywhere.</span></div>';
function AuthView(kind){
  return function(el){
    const cfg = {
      login:{ title:'Log in', head:'Welcome back', sub:'Log in to your '+NAME+' account.', fields:[['email','Email'],['password','Password']], btn:'Log in' },
      signup:{ title:'Sign up', head:'Create an account', sub:'Faster checkout, order tracking and app early access.', fields:[['text','First name'],['text','Last name'],['email','Email'],['password','Password']], btn:'Create account', opt:'Email me about new drops and offers' },
      recover:{ title:'Recover password', head:'Reset your password', sub:'Enter your email and we’d send you a link to reset your password.', fields:[['email','Email']], btn:'Send reset link' }
    }[kind];
    el.innerHTML = topbar({back:true, title:cfg.title}) + '<form class="auth" novalidate><img src="'+LOGO+'" alt="'+esc(NAME)+'" class="auth-logo"><h2>'+esc(cfg.head)+'</h2><p>'+esc(cfg.sub)+'</p>'+demoNote+
      cfg.fields.map(f=>'<label class="field"><span>'+f[1]+'</span><input type="'+f[0]+'" autocomplete="off" placeholder="'+f[1]+'"></label>').join('')+
      (cfg.opt?'<label class="opt"><input type="checkbox"><span>'+esc(cfg.opt)+'</span></label>':'')+
      (kind==='login'?'<button type="button" class="link sm forgot" data-act="recover">Forgot password?</button>':'')+
      '<button class="btn btn-dark btn-block" type="submit">'+cfg.btn+'</button>'+
      (kind==='login'?'<p class="auth-alt">New to '+esc(NAME)+'? <button type="button" class="link sm" data-act="signup">Create an account</button></p>':kind==='signup'?'<p class="auth-alt">Already have an account? <button type="button" class="link sm" data-act="login">Log in</button></p>':'<p class="auth-alt"><button type="button" class="link sm" data-act="back">Back to log in</button></p>')+
      '</form>';
    $('form', el).addEventListener('submit', e => {
      e.preventDefault();
      $$('input', el).forEach(i => { if (i.type !== 'checkbox') i.value = ''; });
      if (kind !== 'recover') signedIn = true;
      $('form', el).innerHTML = '<div class="check-anim">'+I.check+'</div><h2>'+(kind==='recover'?'Demo: no email sent':'Demo: you’d now be signed in')+'</h2><p>'+(kind==='recover'?'In the live app a reset link would be emailed to you. In this concept nothing was sent.':'In this concept nothing was saved or sent, and the form has been cleared.')+'</p><button type="button" class="btn btn-dark btn-block" id="authDone">Back to account</button>';
      $('#authDone', el).addEventListener('click', () => switchTab('account', true));
    });
    return { hideTabs:true };
  };
}

// ---------- in-app browser ----------
function openBrowser(pg){
  if (!pg) return;
  const br = $('#browser');
  let host = '', path = '';
  try { const u = new URL(pg.url); host = u.host.replace(/^www\./,''); path = u.pathname; } catch(e){}
  const fallback = '<div class="br-fallback"><small>'+esc(host+path)+'</small><h3>'+esc(pg.t)+'</h3>'+
    '<p class="br-why">'+I.lock+'<span>'+esc(host)+' doesn’t allow its pages to be shown inside other apps, so here’s a short summary taken from the page.</span></p>'+
    '<div class="br-sum">'+(pg.sum ? pg.sum.split(/\n+/).map(x=>'<p>'+esc(x)+'</p>').join('') : '<p>No summary could be extracted from this page.</p>')+'</div>'+
    '<a class="btn btn-dark btn-block" href="'+esc(pg.url)+'" target="_blank" rel="noopener">Open on site'+I.ext+'</a></div>';
  br.innerHTML = '<div class="br-bar"><button class="br-done" id="brDone">Done</button><div class="br-url">'+I.lock+'<span>'+esc(host)+'</span></div><a class="icon-btn" href="'+esc(pg.url)+'" target="_blank" rel="noopener" aria-label="Open on site">'+I.ext+'</a></div><div class="br-body">'+
    (B.frameable ? '<iframe src="'+esc(pg.url)+'" title="'+esc(pg.t)+'" referrerpolicy="no-referrer"></iframe><button class="br-trouble" id="brTrouble">Page not loading? Show summary</button>' : fallback)+'</div>';
  br.classList.add('show');
  $('#brDone').addEventListener('click', closeBrowser);
  const tr = $('#brTrouble'); if (tr) tr.addEventListener('click', () => { $('.br-body', br).innerHTML = fallback; });
}
function closeBrowser(){ const b = $('#browser'); if (b) b.classList.remove('show'); }

// ---------- REWARDS ----------
function Rewards(el){
  const bars = Array.from({length:46},(_,i)=>'<i style="width:'+[1,2,3,1,2,1,3,2][(i*7)%8]+'px"></i>').join('');
  const RN = B.rewards.name;
  el.innerHTML = topbar({back:true, title:RN}) +
    '<div class="rcard" id="rcard"><div class="rc-top"><img src="'+LOGO+'" alt="'+esc(NAME)+'"><span class="tier">Member</span></div><div class="rc-pts"><small>Points balance</small><b>1,250</b></div><div class="rc-bot"><span>'+esc(RN)+'</span><span>Since 2024</span></div></div>'+
    '<div class="barcode"><div class="bars">'+bars+'</div><small>SCAN IN STORE · 2024 0917 1250</small></div>'+
    '<div class="tiers"><h4>Your next reward</h4><div class="tbar"><i></i></div><div class="tline"><span>1,250 pts</span><span>750 pts to go</span></div></div>'+
    '<div class="r-actions"><div>'+I.bag+'<b>Shop &amp; earn</b><small>Collect points on every order in the app.</small></div><div>'+I.gift+'<b>Birthday treat</b><small>A little something from us each year.</small></div><div>'+I.bolt+'<b>Early access</b><small>First look at new drops before they go live.</small></div><div>'+I.pin+'<b>'+(B.rewards.stockists?'Stockists':'In store')+'</b><small>'+(B.rewards.stockists?'Show your card at '+esc(NAME)+' stockists.':'Show your card at checkout.')+'</small></div></div>'+
    (colBy(H.newCol)?'<div style="padding:18px 18px 0"><button class="btn btn-dark btn-block" data-act="col" data-v="'+esc(H.newCol)+'">Shop New In &amp; earn</button></div>':'')+
    '<p class="fineprint">Concept preview — balance, benefits and card design are illustrative'+(B.rewards.real?' and would connect to '+esc(NAME)+'’s existing loyalty programme.':'.')+'</p>'+credit();
  const card = $('#rcard', el);
  card.addEventListener('pointermove', e => { const r = card.getBoundingClientRect(); const x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5; card.style.transform='perspective(800px) rotateY('+(x*10)+'deg) rotateX('+(-y*10)+'deg)'; });
  card.addEventListener('pointerleave', () => card.style.transform='');
}

// ---------- NOTIFICATIONS ----------
function Notifs(el){
  const items = [];
  const n0 = prods(H.newCol)[0]; if (n0) items.push(['pdp', n0.h, n0.im[0], 'New drop', n0.t+' has just landed. Be first to shop it.', 'Just now', true]);
  if (DR) { const d0 = P[DR.products[0]]; if (d0) items.push(['tab', 'drops', d0.im[0], 'DROP '+DR.num+' / '+DR.name, 'App early access opens '+fmtDay(dropTimes().app)+'. Tap to set a reminder.', '1h ago', true]); }
  const hc = H.hero && prods(H.hero.col)[0]; if (hc) items.push(['col', H.hero.col, hc.im[0], H.hero.title, (B.copy && B.copy.heroNotif) || 'The new season is here.', '2h ago', false]);
  const fc = H.feature && prods(H.feature.col)[0]; if (fc) items.push(['col', H.feature.col, fc.im[0], H.feature.title, 'Build your rotation.', 'Yesterday', false]);
  const sc = SH.featureEdits && prods(SH.featureEdits.col)[0]; if (sc) items.push(['col', SH.featureEdits.col, sc.im[0], SH.featureEdits.title, 'Last chance on selected styles while sizes last.', '3d ago', false]);
  el.innerHTML = topbar({back:true, title:'Notifications'}) +
    items.map(n=>'<div class="notif" data-act="'+n[0]+'" data-v="'+esc(n[1])+'"><img loading="lazy" src="'+img(n[2],150)+'" alt=""><div><b>'+esc(n[3])+'</b><p>'+esc(n[4])+'</p><small>'+n[5]+'</small></div>'+(n[6]?'<i class="unread"></i>':'')+'</div>').join('')+
    '<div class="s-sec" style="padding-top:26px"><h4>Alert preferences</h4></div>'+
    [['drops','Drop alerts','New collections the moment they land'],['restock','Back in stock','When a saved size returns'],['price','Price drops','On items in your wishlist'],['orders','Order updates','Live delivery tracking']].map(x=>'<div class="pref" data-pref="'+x[0]+'"><div><b>'+x[1]+'</b><small>'+x[2]+'</small></div><span class="switch '+(prefs[x[0]]?'on':'')+'"></span></div>').join('')+
    '<div style="padding:20px 18px 0"><button class="btn btn-outline btn-block" id="previewPush">Preview a drop alert</button></div>'+credit();
  $$('.pref', el).forEach(r => r.addEventListener('click', () => { const k=r.dataset.pref; prefs[k]=!prefs[k]; savePrefs(); $('.switch',r).classList.toggle('on', prefs[k]); toast(prefs[k]?'Alerts on':'Alerts off', I.bell); }));
  $('#previewPush', el).addEventListener('click', () => setTimeout(()=>Demo.newin(), 500));
}

// ---------- push notification + demo triggers ----------
let pushT, pushAction = null;
function showPush(title, text, thumb, action){
  $('#pushTitle').textContent = title;
  $('#pushText').textContent = text;
  $('#pushThumb').src = thumb || B.assets.favicon;
  pushAction = action;
  const el = $('#push');
  el.classList.remove('show'); void el.offsetWidth; el.classList.add('show'); clearTimeout(pushT);
  pushT = setTimeout(()=>el.classList.remove('show'), 6000);
}
const firstSize = p => (p.sz.find(s => s[1] && sizeMatch(s[0])) || p.sz.find(s => s[1]) || p.sz[0] || ['One size'])[0];
const Demo = {
  bag(){
    if (!bag.length){ const p = prods(H.bestCol).find(x => x.sz.some(s=>s[1])) || ALL.find(x => x.sz.some(s=>s[1])); if (!p){ toast('No products available'); return; } addToBag(p.h, firstSize(p), true); }
    const p = P[bag[0].h];
    showPush('You left something in your bag', p.n+(p.c?' in '+p.c:'')+' is still waiting, and sizes are going fast. Use '+DISC.code+' for '+DISC.pct+'% off.', img(p.im[0],120), () => switchTab('bag'));
  },
  restock(){
    const pool = prods(H.newCol).concat(ALL);
    const p = (hasSize() ? pool.find(inMySize) : null) || pool.find(x => x.sz.some(s=>s[1]));
    if (!p){ toast('No products available'); return; }
    showPush('Back in stock in your size', p.n+(p.c?' ('+p.c+')':'')+' is back in size '+prettySize(firstSize(p))+'. Tap to grab it before it goes again.', img(p.im[0],120), () => push(PDP, p.h));
  },
  price(){
    let h = wish.find(x => P[x].cp > P[x].p);
    if (!h){ const p = ALL.find(x => x.cp > x.p && x.sz.some(s=>s[1])); if (!p){ toast('No reduced items in the catalogue right now'); return; } h = p.h; wish.unshift(h); saveWish(); }
    priceDrop = { h }; store.set('priceDrop', priceDrop);
    const p = P[h];
    showPush('Price drop on your wishlist', p.n+(p.c?' ('+p.c+')':'')+' is now '+money(p.p)+', was '+money(p.cp)+'.', img(p.im[0],120), () => push(PDP, h));
    refreshAll();
  },
  drop(){
    if (!DR){ const p = prods(H.newCol)[0]; if (p) showPush('New in', p.t+' has just landed.', img(p.im[0],120), () => push(PDP, p.h)); return; }
    dropLive = true;
    const p = P[DR.products[0]];
    showPush('DROP '+DR.num+' / '+DR.name+' is live', 'App early access is open now, 24 hours before the website. Tap to shop first.', p ? img(p.im[0],120) : '', () => switchTab('drops', true));
    refreshAll();
  },
  newin(){
    const p = prods(H.newCol)[0] || ALL[0]; if (!p) return;
    showPush('New in'+(H.hero && H.hero.title ? ': '+H.hero.title : ''), p.t+' has just landed. Tap to shop before it sells out.', img(p.im[0],120), () => push(PDP, p.h));
  },
  welcome(){ showWelcome(); }
};
function showWelcome(){
  const m = $('#welcome');
  m.innerHTML = '<div class="wl-card"><div class="wl-top">'+(H.hero && H.hero.poster ? '<img src="'+esc(H.hero.poster)+'" alt="">' : '')+'<img src="'+LOGO_L+'" alt="'+esc(NAME)+'" class="wl-logo'+(B.assets.logoLight?'':' inv')+'"></div><div class="wl-body">'+
    '<small>Welcome to the app</small><h2>'+DISC.pct+'% off your first order</h2>'+
    '<button class="wl-code" id="wlCode"><span>'+esc(DISC.code)+'</span><em>'+I.copy+'Tap to copy</em></button>'+
    '<button class="btn btn-dark btn-block" id="wlGo">Start shopping</button><button class="wl-skip" id="wlSkip">Maybe later</button></div></div>';
  m.classList.add('show');
  const close = () => m.classList.remove('show');   // not remembered: the offer shows again on the next page load
  $('#wlCode').addEventListener('click', () => {
    if (navigator.clipboard) navigator.clipboard.writeText(DISC.code).catch(()=>{});
    $('#wlCode em').innerHTML = I.check+'Copied'; $('#wlCode').classList.add('done');
    toast(DISC.code+' copied. Apply it in your bag', I.copy);
  });
  $('#wlGo').addEventListener('click', close); $('#wlSkip').addEventListener('click', close);
  m.onclick = e => { if (e.target === m) close(); };
}

// ---------- build the page chrome from brand config ----------
let demoHTML = '';
function buildChrome(){
  const pitch = B.pitch || {};
  const demoBtns = [['bag','Abandoned bag','What’s still in the bag, plus '+DISC.code],['restock','Back in stock','In your saved size'],['price','Price drop on wishlist','A real reduced item, badged in-app'],['drop','Drop is live', DR ? 'DROP '+DR.num+' / '+DR.name+', app early access' : 'New arrivals'],['welcome','Show welcome message','The '+DISC.code+' offer shown on open']];
  demoHTML = demoBtns.map(d=>'<button class="demo-btn" data-demo="'+d[0]+'"><span><b>'+esc(d[1])+'</b><small>'+esc(d[2])+'</small></span>'+I.bell+'</button>').join('');
  document.body.innerHTML =
  '<div class="stage">'+
    '<aside class="pitch"><img class="pitch-logo" src="'+LOGO+'" alt="'+esc(NAME)+'">'+
      '<p class="pitch-kicker">'+esc((B.short||NAME).toUpperCase())+' APP, CONCEPT</p><h1 class="pitch-title">'+(pitch.title||esc(NAME)+',<br>one tap away.')+'</h1>'+
      '<p class="pitch-copy">'+esc(pitch.copy||'')+'</p>'+
      (pitch.list && pitch.list.length ? '<ul class="pitch-list">'+pitch.list.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>' : '')+
      '<div class="demo-panel"><p class="demo-h">Try it: send a push to the phone</p>'+demoHTML+'</div></aside>'+
    '<div class="device" id="device"><div class="device-btn b1"></div><div class="device-btn b2"></div><div class="device-btn b3"></div><div class="device-btn b4"></div>'+
      '<div class="screen" id="screen">'+
        '<div class="statusbar" id="statusbar"><span class="sb-time" id="sbTime">9:41</span><span class="island"></span><span class="sb-icons">'+
          '<svg width="18" height="12" viewBox="0 0 18 12"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>'+
          '<svg width="16" height="12" viewBox="0 0 16 12"><path d="M8 2.6c2.2 0 4.2.8 5.7 2.2l1.2-1.3C13 1.7 10.6.7 8 .7S3 1.7 1.1 3.5l1.2 1.3C3.8 3.4 5.8 2.6 8 2.6zm0 3.6c1.2 0 2.3.4 3.2 1.2l1.2-1.3C11.2 5 9.7 4.3 8 4.3S4.8 5 3.6 6.1l1.2 1.3C5.7 6.6 6.8 6.2 8 6.2zm0 3.4L6.2 7.9c.5-.4 1.1-.6 1.8-.6s1.3.2 1.8.6L8 9.6z"/></svg>'+
          '<svg width="27" height="12" viewBox="0 0 27 12"><rect x=".5" y=".5" width="23" height="11" rx="3.2" fill="none" stroke="currentColor" opacity=".4"/><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="24.5" y="4" width="1.6" height="4" rx=".8" opacity=".4"/></svg></span></div>'+
        '<div class="push" id="push" role="button" tabindex="0"><img src="'+B.assets.favicon+'" alt="" class="push-icon"><div class="push-body"><div class="push-top"><b>'+esc((B.short||NAME).toUpperCase())+'</b><span>now</span></div><div class="push-title" id="pushTitle"></div><div class="push-text" id="pushText"></div></div><img class="push-thumb" id="pushThumb" src="'+B.assets.favicon+'" alt=""></div>'+
        '<div class="splash" id="splash"><img src="'+LOGO_L+'" alt="'+esc(NAME)+'" class="splash-logo'+(B.assets.logoLight?'':' inv')+'"><div class="splash-line"><span></span></div></div>'+
        '<main class="app" id="app"><div class="stack" id="stack"></div>'+
          '<nav class="tabbar" id="tabbar">'+TABS.map(t=>'<button data-tab="'+t[0]+'"'+(t[0]==='home'?' class="active"':'')+'><svg viewBox="0 0 24 24">'+t[2]+'</svg><span>'+t[1]+'</span>'+(t[0]==='wishlist'?'<i class="badge" id="wishBadge"></i>':t[0]==='bag'?'<i class="badge" id="bagBadge"></i>':'')+'</button>').join('')+'</nav>'+
          '<div class="toast" id="toast"></div><div class="sheet-backdrop" id="sheetBackdrop"></div><div class="sheet" id="sheet"></div>'+
          '<div class="browser" id="browser"></div><div class="welcome" id="welcome"></div>'+
          '<button class="demo-fab" id="demoFab" aria-label="Demo controls">'+I.bell+'Demo</button>'+
        '</main><div class="home-indicator"></div></div></div>'+
    '<p class="credit">Concept app mockup for '+esc(NAME)+'</p>'+
  '</div>';
  stackEl = $('#stack');
  $$('#tabbar button').forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));
  $('#sheetBackdrop').addEventListener('click', closeSheet);
  $$('.pitch [data-demo]').forEach(b => b.addEventListener('click', () => runDemo(b.dataset.demo)));
  $('#demoFab').addEventListener('click', () => openSheet('<h3>Demo controls</h3><p class="center sheet-sub">Trigger the push notifications this app would send.</p><div class="demo-panel in-sheet">'+demoHTML+'</div>',
    s => $$('[data-demo]', s).forEach(b => b.addEventListener('click', () => { closeSheet(); setTimeout(()=>runDemo(b.dataset.demo), 350); }))));
  $('#push').addEventListener('click', () => { $('#push').classList.remove('show'); unread=false; const a = pushAction; pushAction = null; if (a){ closeSheet(); closeBrowser(); $('#welcome').classList.remove('show'); a(); } });
  let py=null; $('#push').addEventListener('touchstart', e=>py=e.touches[0].clientY,{passive:true});
  $('#push').addEventListener('touchmove', e=>{ if(py!==null && e.touches[0].clientY-py < -20){ $('#push').classList.remove('show'); py=null; } },{passive:true});
  let ex=null, ey=0;
  stackEl.addEventListener('touchstart', e => { const r = stackEl.getBoundingClientRect(); const x = e.touches[0].clientX - r.left; if (x < 24 && stack.length>1){ ex = x; ey = e.touches[0].clientY; } }, {passive:true});
  stackEl.addEventListener('touchend', e => { if (ex===null) return; const r = stackEl.getBoundingClientRect(); const dx = e.changedTouches[0].clientX - r.left - ex, dy = Math.abs(e.changedTouches[0].clientY - ey); ex=null; if (dx > 70 && dy < 60) back(); }, {passive:true});
}
function runDemo(k){ if (k === 'welcome') return Demo.welcome(); $('#welcome').classList.remove('show'); Demo[k](); }

// global delegated actions
document.addEventListener('click', e => {
  const t = e.target.closest('[data-act]');
  if (!t || t.closest('.dragging')) return;
  const a = t.dataset.act, v = t.dataset.v;
  if (a === 'back') back();
  else if (a === 'pdp') { e.stopPropagation(); closeSheet(); push(PDP, v); }
  else if (a === 'col') { closeSheet(); push(Collection, v); }
  else if (a === 'wish') { e.stopPropagation(); toggleWish(v); }
  else if (a === 'tab') switchTab(v);
  else if (a === 'rewards') { if (B.rewards && B.rewards.enabled) push(Rewards); }
  else if (a === 'notifs') { unread=false; push(Notifs); }
  else if (a === 'bagtab') switchTab('bag');
  else if (a === 'search') push(Search);
  else if (a === 'close') closeSheet();
  else if (a === 'size') openSizeSheet();
  else if (a === 'login') push(AuthView('login'));
  else if (a === 'signup') push(AuthView('signup'));
  else if (a === 'recover') push(AuthView('recover'));
  else if (a === 'reviews') { const R = B.reviews; if (R && R.url) openBrowser({ t: R.source+' reviews', url: R.url, sum: (R.label?R.label+'. ':'')+R.score+' out of 5, based on '+Number(R.count).toLocaleString('en-GB')+' reviews on '+R.source+(R.checked?' (as shown on '+B.domain+', checked '+R.checked+').':'.') }); }
});

// ---------- desktop fit ----------
// Everything fits the viewport with no page scroll: the phone is scaled to the height left after the stage padding
// (16px top, 34px bottom strip for the credit line), and the pitch panel is scaled down too if it is still taller.
const STAGE_PAD = { t:16, b:34, x:24 };
function fit(){
  const d = $('#device'), pt = $('.pitch');
  if (window.innerWidth <= 520){ d.style.transform=''; d.style.margin=''; if (pt) pt.style.transform=''; return; }
  const availH = window.innerHeight - STAGE_PAD.t - STAGE_PAD.b;
  const s = Math.min(1, availH / 868, (window.innerWidth - STAGE_PAD.x*2) / 414);
  d.style.transform = s < 1 ? 'scale('+s+')' : '';
  d.style.margin = s < 1 ? (-(868*(1-s))/2)+'px '+(-(414*(1-s))/2)+'px' : '';
  if (pt && getComputedStyle(pt).display !== 'none'){
    pt.style.transform = '';
    const ps = Math.min(1, availH / pt.offsetHeight);
    pt.style.transform = ps < 1 ? 'scale('+ps+')' : '';
    pt.style.marginRight = ps < 1 ? (-(pt.offsetWidth*(1-ps)))+'px' : '';
  }
}

// ---------- boot ----------
buildChrome();
window.addEventListener('resize', fit); fit();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
{ const pl = $('.pitch-logo'); if (pl && !pl.complete) pl.addEventListener('load', fit); }
updateBadges();
const params = new URLSearchParams(location.search);
switchTab('home');
setStatus(true);
const skip = params.has('nosplash');
setTimeout(() => {
  $('#splash').classList.add('hide');
  const deep = params.get('p'); if (deep && P[deep]) push(PDP, deep);
  const tab = params.get('tab'); if (tab && roots[tab]) switchTab(tab);
  // welcome offer on every page load, shortly after the splash (?nowelcome turns it off)
  if (!params.has('nowelcome')) setTimeout(showWelcome, skip ? 400 : 900);
  else if (!skip && !params.has('nopush') && prefs.drops) setTimeout(()=>Demo.newin(), 2600);
}, skip ? 0 : 2100);
window.__app = { Demo, switchTab, push, openBrowser, showWelcome, back };
})();
