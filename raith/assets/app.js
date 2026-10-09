(function(){
'use strict';
const P = window.RAITH_PRODUCTS, COLS = window.RAITH_COLLECTIONS;
const colBy = h => COLS.find(c => c.h === h);
const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const img = (u, w=600) => u + (u.includes('?') ? '&' : '?') + 'width=' + w + '&format=pjpg';
const money = n => '£' + n.toFixed(2);
const prods = h => (colBy(h)?.p || []).map(x => P[x]).filter(Boolean);
const FREE_SHIP = 150;

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
  apple:'<svg viewBox="0 0 24 24"><path d="M16.4 12.6c0-2.3 1.9-3.4 2-3.5-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.1-2.8.9-3.5.9-.7 0-1.8-.8-3-.8-1.5 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.4 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3 .7c1.3 0 2.1-1.1 2.8-2.3.9-1.3 1.3-2.6 1.3-2.6s-2.5-1-2.5-3.8zM14.2 5.8c.6-.8 1.1-1.9 1-3-.9 0-2.1.6-2.7 1.4-.6.7-1.1 1.8-1 2.9 1 .1 2.1-.5 2.7-1.3z"/></svg>'
};

// ---------- persistent state ----------
const store = {
  get(k, d){ try { return JSON.parse(localStorage.getItem('raith_'+k)) ?? d; } catch(e){ return d; } },
  set(k, v){ try { localStorage.setItem('raith_'+k, JSON.stringify(v)); } catch(e){} }
};
let bag = store.get('bag', []).filter(i => P[i.h]);
let wish = store.get('wish', []).filter(h => P[h]);
let recent = store.get('recent', []);
let dropAlerts = store.get('drops', true);
let unread = true;

function saveBag(){ store.set('bag', bag); updateBadges(true); }
function saveWish(){ store.set('wish', wish); updateBadges(); }
function updateBadges(popBag){
  const n = bag.reduce((a,i)=>a+i.q,0);
  const bb = $('#bagBadge'), wb = $('#wishBadge');
  bb.textContent = n; bb.classList.toggle('show', n>0);
  wb.textContent = wish.length; wb.classList.toggle('show', wish.length>0);
  if (popBag){ bb.classList.remove('pop'); void bb.offsetWidth; bb.classList.add('pop'); }
}
const inWish = h => wish.includes(h);
function toggleWish(h, btn){
  if (inWish(h)) { wish = wish.filter(x=>x!==h); toast('Removed from wishlist'); }
  else { wish.unshift(h); toast('Saved to wishlist', I.heart); }
  saveWish();
  $$('[data-wish="'+CSS.escape(h)+'"]').forEach(b => { b.classList.toggle('on', inWish(h)); b.classList.remove('burst'); void b.offsetWidth; b.classList.add('burst'); });
}

// ---------- toast ----------
let toastT;
function toast(msg, icon){
  const t = $('#toast');
  t.innerHTML = (icon || I.check) + '<span>'+esc(msg)+'</span>';
  t.classList.toggle('raise', !!$('.view.top .buybar.show'));
  t.classList.add('show'); clearTimeout(toastT);
  toastT = setTimeout(()=>t.classList.remove('show'), 1900);
}

// ---------- sheet ----------
function openSheet(html, onMount){
  const s = $('#sheet');
  s.innerHTML = '<div class="grab"></div>' + html;
  $('#sheetBackdrop').classList.add('show'); s.classList.add('show');
  onMount && onMount(s);
}
function closeSheet(){ $('#sheet').classList.remove('show'); $('#sheetBackdrop').classList.remove('show'); }
$('#sheetBackdrop').addEventListener('click', closeSheet);

// ---------- navigation ----------
const stackEl = $('#stack');
let stack = [];          // [{el, opts}]
let currentTab = 'home';
const roots = { home: Home, shop: Shop, search: Search, wishlist: Wishlist, bag: Bag };

function makeView(fn, args){
  const el = document.createElement('section');
  el.className = 'view';
  const opts = fn(el, args) || {};
  el._render = () => { el.innerHTML=''; fn(el, args); };
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
  if (prev){ prev.el.classList.add('under'); setTimeout(()=>{ prev.el.classList.remove('under'); prev.el.style.visibility='hidden'; }, 430); }
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
  closeSheet();
  if (tab === currentTab && stack.length === 1 && !args){ stack[0].el.scrollTo({top:0, behavior:'smooth'}); return; }
  currentTab = tab;
  $$('#tabbar button').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  stack.forEach(s => s.el.remove()); stack = [];
  const v = makeView(roots[tab], args);
  v.el.classList.add('fade'); stackEl.appendChild(v.el); stack.push(v);
  applyChrome(v);
}
$$('#tabbar button').forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));
function setStatus(light){ $('#statusbar').classList.toggle('light', !!light); }

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
  else if (a === 'rewards') push(Rewards);
  else if (a === 'notifs') { unread=false; push(Notifs); }
  else if (a === 'bagtab') switchTab('bag');
  else if (a === 'close') closeSheet();
});

// ---------- components ----------
function pcard(p, opts={}){
  const sale = p.cp > p.p;
  const out = p.sz.every(s=>!s[1]);
  const isNew = colBy('new').p.includes(p.h);
  const tag = out ? '<span class="tag">Sold out</span>' : sale ? '<span class="tag sale">-'+Math.round((1-p.p/p.cp)*100)+'%</span>' : isNew ? '<span class="tag">New in</span>' : '';
  return '<div class="pcard" data-act="pdp" data-v="'+esc(p.h)+'">'+
    '<div class="pimg"><img loading="lazy" src="'+img(p.im[0], opts.w||500)+'" alt="'+esc(p.t)+'">'+tag+
    '<button class="heart '+(inWish(p.h)?'on':'')+'" data-act="wish" data-v="'+esc(p.h)+'" data-wish="'+esc(p.h)+'" aria-label="Save">'+I.heart+'</button></div>'+
    '<div class="pmeta"><div class="pname">'+esc(p.n)+'</div>'+(p.c?'<div class="pcol">'+esc(p.c)+'</div>':'')+priceHTML(p)+'</div></div>';
}
function priceHTML(p){
  return p.cp > p.p ? '<div class="price sale"><b>'+money(p.p)+'</b><s>'+money(p.cp)+'</s></div>' : '<div class="price">'+money(p.p)+'</div>';
}
function topbar({title, logo, back:bk, right='', left='', clear}={}){
  return '<header class="topbar'+(clear?' clear':'')+'">'+
    (bk ? '<button class="icon-btn" data-act="back" aria-label="Back">'+I.back+'</button>' : (left || '<span style="width:40px"></span>'))+
    (logo ? '<img class="tb-logo" src="assets/img/logo-black.png" alt="Raith">' : '<div class="tb-title">'+esc(title||'')+'</div>')+
    (right || '<span style="width:40px"></span>')+'</header>';
}
const bagBtn = () => '<button class="icon-btn" data-act="bagtab" aria-label="Bag">'+I.bag+'</button>';
const credit = '<p class="credit-inline">Concept app mockup for Raith</p>';

// drag-to-scroll for desktop mice
function enableDrag(root){
  $$('.hscroll,.chips,.swatches', root).forEach(el => {
    let down=false, sx=0, sl=0, moved=false;
    el.addEventListener('pointerdown', e => { if (e.pointerType!=='mouse') return; down=true; moved=false; sx=e.clientX; sl=el.scrollLeft; el.style.scrollSnapType='none'; });
    window.addEventListener('pointermove', e => { if(!down) return; const dx=e.clientX-sx; if(Math.abs(dx)>5){ moved=true; el.classList.add('dragging'); } el.scrollLeft = sl - dx; });
    window.addEventListener('pointerup', () => { if(!down) return; down=false; el.style.scrollSnapType=''; setTimeout(()=>el.classList.remove('dragging'),0); });
    el.addEventListener('click', e => { if (moved){ e.stopPropagation(); e.preventDefault(); moved=false; } }, true);
  });
}

// ---------- HOME ----------
function Home(el){
  const newIn = prods('new').slice(0, 12);
  const best = prods('best-sellers').slice(0, 12);
  const cover = h => { const p = prods(h)[0]; return p ? img(p.im[0], 500) : ''; };
  const tiles = [['outerwear-jackets','Jackets & Outerwear'],['knitwear','Knitwear'],['pants','Trousers'],['polos','Polo Shirts'],['jeans','Denim'],['tees','T-Shirts']];
  el.innerHTML =
    topbar({ logo:true, clear:true, left:'<button class="icon-btn" data-act="notifs" aria-label="Notifications">'+I.bell+(unread?'<i class="dot"></i>':'')+'</button>', right:bagBtn() }) +
    '<div class="hero"><img class="poster" src="assets/img/hero-poster.jpg" alt=""><video src="assets/hero.mp4" poster="assets/img/hero-poster.jpg" autoplay muted loop playsinline></video>'+
      '<div class="hero-copy"><div class="eyebrow">New Season</div><div class="hero-title">PRE FALL 26</div><button class="btn btn-light" data-act="col" data-v="prefall-26">Shop Pre Fall</button></div></div>'+
    '<div class="rewards-mini" data-act="rewards"><div class="rm-left"><small>Raith Rewards</small><b>1,250 pts</b><div class="rm-bar"><i></i></div><p>750 pts to your next reward</p></div><div class="rm-right">'+I.card+'</div></div>'+
    '<section class="section"><div class="sec-head"><div><h2>New In</h2><p>The latest Pre Fall 26 drops</p></div><button class="link" data-act="col" data-v="new">View all</button></div>'+
      '<div class="hscroll">'+newIn.map(p=>pcard(p,{w:400})).join('')+'</div></section>'+
    '<div class="drop-banner"><div class="db-ic">'+I.bell+'</div><div class="db-t"><b>Drop alerts</b><p>Be first to know when new pieces land.</p></div><button class="switch '+(dropAlerts?'on':'')+'" id="dropSwitch" aria-label="Toggle drop alerts"></button></div>'+
    '<section class="section"><div class="sec-head"><div><h2>Shop by Category</h2></div><button class="link" data-act="tab" data-v="shop">All</button></div>'+
      '<div class="cat-grid">'+tiles.map((t,i)=>'<div class="cat-tile" data-act="col" data-v="'+t[0]+'"><img loading="lazy" src="'+cover(t[0])+'" alt=""><span>'+esc(t[1])+'</span></div>').join('')+'</div></section>'+
    '<div class="editorial" data-act="col" data-v="outerwear-jackets"><img loading="lazy" src="assets/img/campaign-wide.jpg" alt=""><div class="hero-copy"><div class="eyebrow">AW26</div><div class="hero-title">JACKETS &amp; OUTERWEAR</div><span class="btn btn-light">Shop now</span></div></div>'+
    '<section class="section"><div class="sec-head"><div><h2>Best Sellers</h2><p>The pieces everyone’s wearing</p></div><button class="link" data-act="col" data-v="best-sellers">View all</button></div>'+
      '<div class="hscroll">'+best.map(p=>pcard(p,{w:400})).join('')+'</div></section>'+
    '<div class="feature-card" style="margin-top:28px" data-act="col" data-v="mercerised-tees"><img loading="lazy" src="'+img(prods('mercerised-tees')[0].im[1]||prods('mercerised-tees')[0].im[0],700)+'" alt=""><div><b>LUXE T-SHIRT</b><span class="btn btn-light" style="height:40px;padding:0 18px">Mix &amp; Match</span></div></div>'+
    '<div class="about"><img src="assets/img/logo-black.png" alt="Raith"><p>At Raith, we reimagine timeless styles with a modern edge. Our vision is to present a menswear concept that embodies simplicity, minimalism, and versatility.</p></div>'+credit;
  const tb = $('.topbar', el);
  el.addEventListener('scroll', () => {
    const s = el.scrollTop > 480;
    tb.classList.toggle('scrolled', s);
    if (el.classList.contains('top')) setStatus(!s);
  }, {passive:true});
  $('#dropSwitch', el).addEventListener('click', e => {
    dropAlerts = !dropAlerts; store.set('drops', dropAlerts);
    e.currentTarget.classList.toggle('on', dropAlerts);
    toast(dropAlerts ? 'Drop alerts on' : 'Drop alerts off', I.bell);
    if (dropAlerts) setTimeout(showDropPush, 1300);
  });
  const vid = $('video', el); vid.addEventListener('playing', ()=>{ const pi=$('.poster',el); if(pi) pi.style.opacity=0; });
  enableDrag(el);
  return { light:true, lightUntil:480 };
}

// ---------- SHOP ----------
const SHOP_CATS = ['outerwear-jackets','pants','shirts-overshirts','knitwear','hoods-sweats','polos','tees','jeans','matchingsets'];
const SHOP_EDITS = ['new','prefall-26','mercerised-tees','best-sellers','outlet'];
function Shop(el, seg){
  seg = seg || 'cats';
  const row = h => { const c = colBy(h), p = prods(h)[0]; return '<div class="cat-row" data-act="col" data-v="'+h+'"><img loading="lazy" src="'+img(p.im[0],200)+'" alt=""><div><b>'+esc(c.t)+'</b><small>'+c.p.length+' styles</small></div>'+I.chev+'</div>'; };
  const list = seg === 'cats' ? SHOP_CATS : SHOP_EDITS;
  const fp = prods(seg==='cats'?'prefall-26':'outlet')[seg==='cats'?1:0];
  el.innerHTML = topbar({ title:'', right:bagBtn(), left:'<span style="width:40px"></span>' }) +
    '<div class="large-title"><small>Raith Menswear</small>Shop</div>'+
    '<div class="seg"><button class="'+(seg==='cats'?'on':'')+'" data-seg="cats">Shop by Product</button><button class="'+(seg==='edits'?'on':'')+'" data-seg="edits">Collections</button></div>'+
    (seg==='cats' ? '<div class="feature-card" data-act="col" data-v="prefall-26"><img src="'+img(fp.im[0],700)+'" alt=""><div><b>PRE FALL 26</b><span class="btn btn-light" style="height:40px;padding:0 18px">Shop now</span></div></div>'
                  : '<div class="feature-card" data-act="col" data-v="outlet"><img src="'+img(fp.im[0],700)+'" alt=""><div><b>OUTLET</b><span class="btn btn-light" style="height:40px;padding:0 18px">Shop the outlet</span></div></div>')+
    '<div class="cat-list">'+list.map(row).join('')+'</div>'+credit;
  $$('.seg button', el).forEach(b => b.addEventListener('click', () => { const sc = el.scrollTop; el.innerHTML=''; Shop(el, b.dataset.seg); }));
}

// ---------- COLLECTION ----------
function Collection(el, h){
  const c = colBy(h);
  let sort = 'featured', stockOnly = false;
  const render = () => {
    let list = prods(h);
    if (stockOnly) list = list.filter(p => p.sz.some(s=>s[1]));
    if (sort === 'low') list = list.slice().sort((a,b)=>a.p-b.p);
    if (sort === 'high') list = list.slice().sort((a,b)=>b.p-a.p);
    if (sort === 'sale') list = list.filter(p=>p.cp>p.p);
    $('.count', el).textContent = list.length + ' styles';
    $('.grid', el).innerHTML = list.map(p=>pcard(p)).join('');
  };
  el.innerHTML = topbar({ back:true, title:c.t, right:bagBtn() }) +
    '<div class="large-title"><small>Raith</small>'+esc(c.t)+'</div>'+
    '<div class="chips">'+[['featured','Featured'],['low','Price: Low–High'],['high','Price: High–Low']].concat(h==='outlet'||prods(h).some(p=>p.cp>p.p)?[['sale','On sale']]:[]).map(s=>'<button class="chip '+(s[0]===sort?'on':'')+'" data-sort="'+s[0]+'">'+s[1]+'</button>').join('')+'<button class="chip" data-stock>In stock</button></div>'+
    '<div class="count"></div><div class="grid"></div>'+credit;
  $$('[data-sort]', el).forEach(b => b.addEventListener('click', () => { sort=b.dataset.sort; $$('[data-sort]',el).forEach(x=>x.classList.toggle('on',x===b)); render(); }));
  $('[data-stock]', el).addEventListener('click', e => { stockOnly=!stockOnly; e.currentTarget.classList.toggle('on',stockOnly); render(); });
  render(); enableDrag(el);
  el._refresh = () => $$('[data-wish]', el).forEach(b => b.classList.toggle('on', inWish(b.dataset.v)));
}

// ---------- PDP ----------
function PDP(el, h){
  const p = P[h];
  if (!p){ el.innerHTML = topbar({back:true,title:'Not found'}) + '<div class="empty"><h3>Product unavailable</h3><button class="btn btn-dark" data-act="back">Go back</button></div>'; return {}; }
  let size = null;
  const sibs = Object.values(P).filter(x => x.n === p.n);
  const related = (COLS.find(c => !['new','best-sellers','prefall-26','outlet'].includes(c.h) && c.p.includes(h)) || colBy('new')).p.filter(x=>x!==h && P[x]).slice(0,10).map(x=>P[x]);
  const long = p.sz.some(s => s[0].length > 4);
  const sale = p.cp > p.p;
  el.classList.add('pdp');
  el.innerHTML =
    '<div class="pdp-top"><button class="icon-btn glass" data-act="back" aria-label="Back">'+I.back+'</button><div class="r"><button class="icon-btn glass" id="shareBtn" aria-label="Share">'+I.share+'</button><button class="icon-btn glass" data-act="bagtab" aria-label="Bag">'+I.bag+'</button></div></div>'+
    '<div class="pscroll"><div class="gallery"><div class="gtrack">'+p.im.map((u,i)=>'<img src="'+img(u,800)+'" '+(i>1?'loading="lazy"':'')+' alt="'+esc(p.t)+' image '+(i+1)+'" draggable="false">').join('')+'</div>'+
      '<div class="gdots">'+p.im.map((_,i)=>'<i class="'+(i?'':'on')+'"></i>').join('')+'</div><span class="gcount">1 / '+p.im.length+'</span></div>'+
    '<div class="pdp-info">'+
      '<div class="ptype">'+esc(p.ty || 'Raith')+'</div><h1>'+esc(p.n)+'</h1>'+(p.c?'<div class="pc">'+esc(p.c)+'</div>':'')+
      (sale ? '<div class="price sale"><b>'+money(p.p)+'</b><s>'+money(p.cp)+'</s></div>' : '<div class="price">'+money(p.p)+'</div>')+
      '<div class="klarna">Or 3 payments of '+money(p.p/3)+' with Klarna</div>'+
      (sibs.length > 1 ? '<div class="label-row"><b>Colour</b><span>'+esc(p.c)+'</span></div><div class="swatches">'+sibs.map(s=>'<button class="swatch '+(s.h===h?'on':'')+'" data-sib="'+esc(s.h)+'" aria-label="'+esc(s.c)+'"><img loading="lazy" src="'+img(s.im[0],150)+'" alt=""></button>').join('')+'</div>' : '')+
      '<div class="label-row"><b>Size</b><span id="sizeLbl">Select a size</span></div>'+
      '<div class="sizes">'+p.sz.map(s=>'<button class="size '+(long?'sm ':'')+(s[1]?'':'out')+'" data-size="'+esc(s[0])+'" data-in="'+s[1]+'">'+esc(s[0].replace(' - ',' · '))+'</button>').join('')+'</div>'+
      '<div class="size-hint">'+I.bell+'<span>Tap a sold-out size to get a back-in-stock alert</span></div>'+
      '<div class="perks"><div>'+I.truck+'Free UK delivery over £150</div><div>'+I.ret+'Easy returns</div><div>'+I.star+'Earn Raith Rewards</div></div>'+
      '<div class="acc">'+
        '<details open><summary>Description'+I.plus+'</summary><div class="acc-body">'+esc(p.d || 'Designed by Raith.')+'</div></details>'+
        '<details><summary>Delivery'+I.plus+'</summary><div class="acc-body"><ul><li><b>Royal Mail Tracked 48</b> — £3.99, free on orders over £150</li><li><b>Royal Mail Tracked 24</b> — £5.49, next day</li><li><b>DPD Express (Next Day)</b> — £5.99, order by 8pm Mon–Fri</li><li><b>DPD Saturday</b> — £12.99, order by 8pm Friday</li><li>Now shipping to the USA from our US warehouse.</li></ul></div></details>'+
        '<details><summary>Returns'+I.plus+'</summary><div class="acc-body">Not quite right? Start a return straight from your order history in the app — see the Raith returns policy for full details.</div></details>'+
      '</div>'+
    '</div>'+
    (related.length ? '<section class="section"><div class="sec-head"><h2>You may also like</h2></div><div class="hscroll">'+related.map(r=>pcard(r,{w:400})).join('')+'</div></section>' : '')+credit+'</div>'+
    '<div class="buybar show"><button class="hbtn '+(inWish(h)?'on':'')+'" data-act="wish" data-v="'+esc(h)+'" data-wish="'+esc(h)+'" aria-label="Save">'+I.heart+'</button><button class="btn btn-dark" id="addBtn">'+(p.sz.every(s=>!s[1])?'Notify me':'Add to bag')+' — '+money(p.p)+'</button></div>';

  // gallery
  const track = $('.gtrack', el), dots = $$('.gdots i', el), cnt = $('.gcount', el);
  const idx = () => Math.round(track.scrollLeft / track.clientWidth);
  track.addEventListener('scroll', () => { const i = idx(); dots.forEach((d,j)=>d.classList.toggle('on', i===j)); cnt.textContent = (i+1)+' / '+p.im.length; }, {passive:true});
  const go = i => track.scrollTo({ left: Math.max(0, Math.min(p.im.length-1, i)) * track.clientWidth, behavior:'smooth' });
  dots.forEach((d,i)=>d.addEventListener('click',()=>go(i)));
  let sx = null;
  track.addEventListener('pointerdown', e => { if (e.pointerType==='mouse'){ sx = e.clientX; e.preventDefault(); } });
  track.addEventListener('pointerup', e => { if (sx===null) return; const dx = e.clientX - sx; sx = null; if (Math.abs(dx) > 30) go(idx() + (dx<0?1:-1)); else go(idx()+1 >= p.im.length ? 0 : idx()+1); });
  track.addEventListener('pointerleave', () => sx = null);

  // swatches
  $$('[data-sib]', el).forEach(b => b.addEventListener('click', () => { if (b.dataset.sib !== h){ const v = stack[stack.length-1]; v.args = b.dataset.sib; el.innerHTML=''; PDP(el, b.dataset.sib); } }));
  // sizes
  $$('.size', el).forEach(b => b.addEventListener('click', () => {
    if (b.dataset.in === '0'){ toast('We’ll alert you when '+b.dataset.size.replace(' - ',' ')+' is back', I.bell); return; }
    size = b.dataset.size; $$('.size', el).forEach(x=>x.classList.toggle('on', x===b));
    $('#sizeLbl', el).textContent = 'Size ' + size.replace(' - ',' · ');
  }));
  $('#addBtn', el).addEventListener('click', () => {
    if (p.sz.every(s=>!s[1])) { toast('We’ll alert you when it’s back in stock', I.bell); return; }
    if (!size){ const sz = $('.sizes', el); sz.classList.remove('shake'); void sz.offsetWidth; sz.classList.add('shake'); $('#sizeLbl', el).textContent = 'Please select a size'; $('#sizeLbl',el).style.color='#9b3b2a'; sz.scrollIntoView({behavior:'smooth', block:'center'}); return; }
    addToBag(h, size);
  });
  $('#shareBtn', el).addEventListener('click', () => {
    const url = 'https://raith-clo.com/products/' + h;
    if (navigator.share) navigator.share({ title:p.t, url }).catch(()=>{});
    else { navigator.clipboard && navigator.clipboard.writeText(url).catch(()=>{}); toast('Link copied', I.share); }
  });
  enableDrag(el);
  el._refresh = () => $$('[data-wish]', el).forEach(b => b.classList.toggle('on', inWish(b.dataset.v)));
  return { hideTabs:true };
}
function addToBag(h, size){
  const p = P[h];
  const ex = bag.find(i => i.h===h && i.s===size);
  if (ex) ex.q++; else bag.push({ h, s:size, q:1 });
  saveBag();
  const total = bag.reduce((a,i)=>a+P[i.h].p*i.q,0);
  const left = FREE_SHIP - total;
  openSheet('<h3>Added to bag</h3><div class="added"><img src="'+img(p.im[0],200)+'" alt=""><div><b>'+esc(p.t)+'</b><small>Size '+esc(size.replace(' - ',' · '))+' · '+money(p.p)+'</small></div></div>'+
    '<div class="ship-prog" style="margin:0 0 16px"><p>'+(left>0?'You’re <b>'+money(left)+'</b> away from free UK delivery':'<b>You’ve unlocked free UK delivery</b>')+'</p><div class="bar"><i style="width:'+Math.min(100,total/FREE_SHIP*100)+'%"></i></div></div>'+
    '<div class="btns"><button class="btn btn-dark btn-block" id="goBag">View bag & checkout</button><button class="btn btn-outline btn-block" data-act="close">Continue shopping</button></div>',
    s => $('#goBag', s).addEventListener('click', () => { closeSheet(); switchTab('bag'); }));
}

// ---------- BAG ----------
function Bag(el){
  const render = () => {
    if (!bag.length){
      el.innerHTML = topbar({title:'Bag'}) + '<div class="empty"><div class="eic">'+I.bag+'</div><h3>Your bag is empty</h3><p>Fewer, but superior choices. Start with the latest Pre Fall 26 pieces.</p><button class="btn btn-dark" data-act="col" data-v="new">Shop New In</button></div>'+
        '<section class="section"><div class="sec-head"><h2>Best Sellers</h2></div><div class="hscroll">'+prods('best-sellers').slice(0,8).map(p=>pcard(p,{w:400})).join('')+'</div></section>'+credit;
      enableDrag(el); return;
    }
    const sub = bag.reduce((a,i)=>a+P[i.h].p*i.q,0);
    const cnt = bag.reduce((a,i)=>a+i.q,0);
    const ship = sub >= FREE_SHIP ? 0 : 3.99;
    const saved = bag.reduce((a,i)=>a+(P[i.h].cp>P[i.h].p?(P[i.h].cp-P[i.h].p)*i.q:0),0);
    el.innerHTML = topbar({title:'Bag ('+cnt+')'}) +
      '<div class="ship-prog"><p>'+(sub<FREE_SHIP?'Spend <b>'+money(FREE_SHIP-sub)+'</b> more for free UK delivery':'<b>Free UK delivery unlocked</b> — Royal Mail Tracked 48')+'</p><div class="bar"><i style="width:'+Math.min(100,sub/FREE_SHIP*100)+'%"></i></div></div>'+
      bag.map((it,ix)=>{ const p=P[it.h]; return '<div class="bag-item" data-ix="'+ix+'"><img src="'+img(p.im[0],250)+'" alt="" data-act="pdp" data-v="'+esc(p.h)+'"><div class="bi-info"><b>'+esc(p.n)+'</b><small>'+esc(p.c)+(p.c?' · ':'')+'Size '+esc(it.s.replace(' - ',' · '))+'</small>'+priceHTML(p)+
        '<div class="bi-bottom"><div class="qty"><button data-q="-1" aria-label="Decrease">−</button><span>'+it.q+'</span><button data-q="1" aria-label="Increase">+</button></div><button class="remove" data-rm>Remove</button></div></div></div>'; }).join('')+
      '<div class="summary"><div class="row"><span>Subtotal</span><span>'+money(sub)+'</span></div>'+(saved?'<div class="row" style="color:#9b3b2a"><span>You’re saving</span><span>−'+money(saved)+'</span></div>':'')+
        '<div class="row"><span>Delivery (Tracked 48)</span><span>'+(ship?money(ship):'Free')+'</span></div><div class="row total"><span>Total</span><span>'+money(sub+ship)+'</span></div>'+
        '<div class="pts">'+I.star+'<span>Members earn Raith Rewards points on this order</span></div></div>'+
      '<div class="pay-row"><button class="btn btn-dark btn-block" id="checkout" style="height:52px">Checkout — '+money(sub+ship)+'</button><button class="apple-pay" id="applePay">'+I.apple+'Pay</button><div class="pay-icons"><span>Klarna</span>·<span>PayPal</span>·<span>Shop Pay</span>·<span>Google Pay</span></div></div>'+credit;
    $$('.bag-item', el).forEach(row => {
      const ix = +row.dataset.ix;
      $$('[data-q]', row).forEach(b => b.addEventListener('click', () => { bag[ix].q += +b.dataset.q; if (bag[ix].q < 1){ removeAt(row, ix); return; } saveBag(); render(); }));
      $('[data-rm]', row).addEventListener('click', () => removeAt(row, ix));
    });
    $('#checkout', el).addEventListener('click', () => checkout(sub));
    $('#applePay', el).addEventListener('click', () => checkout(sub, true));
  };
  const removeAt = (row, ix) => { row.classList.add('removing'); setTimeout(()=>{ bag.splice(ix,1); saveBag(); render(); toast('Removed from bag'); }, 320); };
  render();
  el._refresh = render;
}
function checkout(sub, quick){
  const opts = [['t48','Royal Mail Tracked 48','Delivered within 2–3 working days', sub>=FREE_SHIP?0:3.99],['t24','Royal Mail Tracked 24','Next day delivery',5.49],['dpd','DPD Express (Next Day)','Order by 8pm Mon–Fri',5.99]];
  let sel = 't48';
  const totalFor = () => sub + opts.find(o=>o[0]===sel)[3];
  openSheet('<h3>Checkout</h3>'+
    '<div class="co-row"><div>Deliver to<small>Your saved address</small></div><span>Change</span></div>'+
    opts.map(o=>'<div class="ship-opt '+(o[0]===sel?'on':'')+'" data-o="'+o[0]+'"><i class="radio"></i><div>'+o[1]+'<small>'+o[2]+'</small></div><span>'+(o[3]?money(o[3]):'Free')+'</span></div>').join('')+
    '<div class="co-row" style="margin-top:8px"><div>Pay with<small>'+(quick?'Apple Pay':'Card ending ···· 4242')+'</small></div><span>Change</span></div>'+
    '<div class="co-row"><div><b>Total</b></div><span id="coTotal" style="font-size:15px;font-weight:600">'+money(totalFor())+'</span></div>'+
    '<div class="btns" style="margin-top:12px"><button class="'+(quick?'apple-pay':'btn btn-dark btn-block')+'" id="payNow">'+(quick?I.apple+'Pay':'Place order')+'</button></div>'+
    '<p class="center" style="font-size:10.5px;margin:12px 0 0">Concept demo — no order is placed and no payment is taken.</p>',
    s => {
      $$('.ship-opt', s).forEach(o => o.addEventListener('click', () => { sel = o.dataset.o; $$('.ship-opt', s).forEach(x=>x.classList.toggle('on',x===o)); $('#coTotal', s).textContent = money(totalFor()); }));
      $('#payNow', s).addEventListener('click', () => {
        const ref = 'R' + Math.floor(100000 + Math.random()*899999);
        bag = []; saveBag();
        openSheet('<div class="check-anim">'+I.check+'</div><h3>Order confirmed</h3><p class="center">Thanks — order #'+ref+' is on its way.<br>We’ll send live tracking updates straight to your lock screen.</p><div class="btns"><button class="btn btn-dark btn-block" id="contShop">Continue shopping</button><button class="btn btn-outline btn-block" data-act="rewards" id="seeRw">View Raith Rewards</button></div>',
          s2 => { $('#contShop', s2).addEventListener('click', () => { closeSheet(); switchTab('home'); }); $('#seeRw', s2).addEventListener('click', () => { closeSheet(); }); });
        if (currentTab==='bag') stack[0].el._refresh();
      });
    });
}

// ---------- WISHLIST ----------
function Wishlist(el){
  const render = () => {
    el.innerHTML = topbar({title:'Wishlist'}) + '<div class="large-title"><small>Saved for later</small>Wishlist</div>' +
      (wish.length ? '<div class="count">'+wish.length+' saved '+(wish.length===1?'item':'items')+' · we’ll let you know if prices drop</div><div class="grid">'+wish.map(h=>pcard(P[h])).join('')+'</div>'
                   : '<div class="empty" style="padding-top:40px"><div class="eic">'+I.heart+'</div><h3>Nothing saved yet</h3><p>Tap the heart on any piece to save it here — we’ll alert you if your size is running low.</p><button class="btn btn-dark" data-act="col" data-v="prefall-26">Shop Pre Fall 26</button></div>') + credit;
  };
  render();
  el._refresh = render;
  // re-render when hearts toggled inside this view
  el.addEventListener('click', e => { if (e.target.closest('[data-act="wish"]')) setTimeout(render, 380); });
}

// ---------- SEARCH ----------
const TRENDING = ['Trench','Knitwear','Mercerised','Jeans','Polo','Overshirt','Cardigan','Suede'];
function Search(el, q0){
  el.innerHTML = '<div class="searchbar"><label class="sfield">'+I.search+'<input id="sq" type="search" placeholder="Search Raith" autocomplete="off" enterkeyhint="search"><button class="clear" id="sclear" aria-label="Clear">×</button></label></div><div id="sbody"></div>';
  const inp = $('#sq', el), body = $('#sbody', el), field = $('.sfield', el);
  const idle = () => {
    body.innerHTML =
      (recent.length ? '<div class="s-sec"><h4>Recent</h4><div class="chips">'+recent.map(r=>'<button class="chip" data-q="'+esc(r)+'">'+esc(r)+'</button>').join('')+'</div></div>' : '')+
      '<div class="s-sec"><h4>Trending</h4><div class="chips">'+TRENDING.map(r=>'<button class="chip" data-q="'+r+'">'+r+'</button>').join('')+'</div></div>'+
      '<div class="s-sec"><h4>Popular categories</h4></div><div class="cat-list">'+['new','outerwear-jackets','knitwear','pants','jeans'].map(h=>{const c=colBy(h),p=prods(h)[0];return '<div class="cat-row" data-act="col" data-v="'+h+'"><img loading="lazy" src="'+img(p.im[0],200)+'" alt=""><div><b>'+esc(c.t)+'</b><small>'+c.p.length+' styles</small></div>'+I.chev+'</div>';}).join('')+'</div>'+credit;
    $$('[data-q]', body).forEach(b => b.addEventListener('click', () => { inp.value = b.dataset.q; run(true); }));
  };
  const all = Object.values(P);
  const run = (commit) => {
    const q = inp.value.trim().toLowerCase();
    field.classList.toggle('has', !!q);
    if (!q) return idle();
    const terms = q.split(/\s+/);
    const res = all.filter(p => { const hay = (p.t+' '+p.ty).toLowerCase(); return terms.every(t => hay.includes(t)); });
    if (commit){ recent = [inp.value.trim(), ...recent.filter(r=>r.toLowerCase()!==q)].slice(0,5); store.set('recent', recent); }
    const re = new RegExp('('+terms.map(t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')','ig');
    body.innerHTML = res.length
      ? '<div class="count" style="padding-top:4px">'+res.length+' results for “'+esc(inp.value.trim())+'”</div><div class="s-res">'+res.slice(0,40).map(p=>'<div class="s-row" data-act="pdp" data-v="'+esc(p.h)+'"><img loading="lazy" src="'+img(p.im[0],150)+'" alt=""><div><b>'+esc(p.t).replace(re,'<mark>$1</mark>')+'</b><small>'+esc(p.ty)+'</small></div>'+priceHTML(p)+'</div>').join('')+'</div>'
      : '<div class="empty" style="padding-top:40px"><div class="eic">'+I.search+'</div><h3>No results</h3><p>Nothing matched “'+esc(inp.value.trim())+'”. Try a trending search instead.</p><div class="chips" style="justify-content:center;flex-wrap:wrap">'+TRENDING.slice(0,4).map(r=>'<button class="chip" data-q="'+r+'">'+r+'</button>').join('')+'</div></div>';
    $$('[data-q]', body).forEach(b => b.addEventListener('click', () => { inp.value = b.dataset.q; run(true); }));
  };
  inp.addEventListener('input', () => run(false));
  inp.addEventListener('keydown', e => { if (e.key === 'Enter'){ run(true); inp.blur(); } });
  $('#sclear', el).addEventListener('click', e => { e.preventDefault(); inp.value=''; run(); inp.focus(); });
  if (q0){ inp.value = q0; run(true); } else idle();
  if (window.matchMedia('(min-width:521px)').matches) setTimeout(()=>inp.focus({preventScroll:true}), 300);
}

// ---------- REWARDS ----------
function Rewards(el){
  const bars = Array.from({length:46},(_,i)=>'<i style="width:'+[1,2,3,1,2,1,3,2][(i*7)%8]+'px"></i>').join('');
  el.innerHTML = topbar({back:true, title:'Raith Rewards'}) +
    '<div class="rcard" id="rcard"><div class="rc-top"><img src="assets/img/logo-black.png" alt="Raith"><span class="tier">Member</span></div><div class="rc-pts"><small>Points balance</small><b>1,250</b></div><div class="rc-bot"><span>Raith Rewards</span><span>Since 2024</span></div></div>'+
    '<div class="barcode"><div class="bars">'+bars+'</div><small>SCAN IN STORE · 2024 0917 1250</small></div>'+
    '<div class="tiers"><h4>Your next reward</h4><div class="tbar"><i></i></div><div class="tline"><span>1,250 pts</span><span>750 pts to go</span></div></div>'+
    '<div class="r-actions"><div>'+I.bag+'<b>Shop &amp; earn</b><small>Collect points on every order in the app.</small></div><div>'+I.gift+'<b>Birthday treat</b><small>A little something from us each year.</small></div><div>'+I.bolt+'<b>Early access</b><small>First look at new drops before they go live.</small></div><div>'+I.pin+'<b>Stockists</b><small>Show your card at Raith stockists.</small></div></div>'+
    '<div style="padding:18px 18px 0"><button class="btn btn-dark btn-block" data-act="col" data-v="new">Shop New In &amp; earn</button></div>'+
    '<p class="fineprint">Concept preview — balance, benefits and card design are illustrative and would connect to Raith’s existing loyalty programme.</p>'+credit;
  const card = $('#rcard', el);
  card.addEventListener('pointermove', e => { const r = card.getBoundingClientRect(); const x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5; card.style.transform='perspective(800px) rotateY('+(x*10)+'deg) rotateX('+(-y*10)+'deg)'; });
  card.addEventListener('pointerleave', () => card.style.transform='');
  return { hideTabs:false };
}

// ---------- NOTIFICATIONS ----------
function Notifs(el){
  const drop = prods('new')[0], pf = prods('prefall-26')[0], mt = prods('mercerised-tees')[0], ol = prods('outlet')[0];
  const items = [
    ['pdp', drop.h, drop.im[0], 'New drop', drop.t+' has just landed. Be first to shop it.', 'Just now', true],
    ['col', 'prefall-26', pf.im[0], 'PRE FALL 26', 'The new season is here. Timeless pieces with a modern edge.', '2h ago', true],
    ['col', 'mercerised-tees', mt.im[0], 'Luxe T-Shirt — Mix & Match', 'Build your rotation of mercerised essentials.', 'Yesterday', false],
    ['col', 'outlet', ol.im[0], 'Outlet', 'Last chance on selected styles while sizes last.', '3d ago', false]
  ];
  el.innerHTML = topbar({back:true, title:'Notifications'}) +
    items.map(n=>'<div class="notif" data-act="'+n[0]+'" data-v="'+esc(n[1])+'"><img loading="lazy" src="'+img(n[2],150)+'" alt=""><div><b>'+esc(n[3])+'</b><p>'+esc(n[4])+'</p><small>'+n[5]+'</small></div>'+(n[6]?'<i class="unread"></i>':'')+'</div>').join('')+
    '<div class="s-sec" style="padding-top:26px"><h4>Alert preferences</h4></div>'+
    [['drops','Drop alerts','New collections the moment they land',dropAlerts],['restock','Back in stock','When a saved size returns',true],['price','Price drops','On items in your wishlist',true],['orders','Order updates','Live delivery tracking',true]].map(x=>'<div class="pref" data-pref="'+x[0]+'"><div><b>'+x[1]+'</b><small>'+x[2]+'</small></div><span class="switch '+(x[3]?'on':'')+'"></span></div>').join('')+
    '<div style="padding:20px 18px 0"><button class="btn btn-outline btn-block" id="previewPush">Preview a drop alert</button></div>'+credit;
  $$('.pref', el).forEach(r => r.addEventListener('click', () => { const sw=$('.switch',r); sw.classList.toggle('on'); if (r.dataset.pref==='drops'){ dropAlerts = sw.classList.contains('on'); store.set('drops', dropAlerts); } toast(sw.classList.contains('on')?'Alerts on':'Alerts off', I.bell); }));
  $('#previewPush', el).addEventListener('click', () => setTimeout(showDropPush, 500));
}

// ---------- push notification ----------
let pushT;
function showDropPush(){
  const p = prods('new')[0];
  $('#pushTitle').textContent = 'New drop: PRE FALL 26';
  $('#pushText').textContent = p.t + ' has just landed. Tap to shop before it sells out.';
  $('#pushThumb').src = img(p.im[0], 120);
  const el = $('#push'); el.dataset.h = p.h;
  el.classList.add('show'); clearTimeout(pushT);
  pushT = setTimeout(()=>el.classList.remove('show'), 5200);
}
$('#push').addEventListener('click', () => { const el=$('#push'); el.classList.remove('show'); unread=false; push(PDP, el.dataset.h); });
let py=null; $('#push').addEventListener('touchstart', e=>py=e.touches[0].clientY,{passive:true});
$('#push').addEventListener('touchmove', e=>{ if(py!==null && e.touches[0].clientY-py < -20){ $('#push').classList.remove('show'); py=null; } },{passive:true});

// ---------- edge swipe back ----------
let ex=null, ey=0;
stackEl.addEventListener('touchstart', e => { const r = stackEl.getBoundingClientRect(); const x = e.touches[0].clientX - r.left; if (x < 24 && stack.length>1){ ex = x; ey = e.touches[0].clientY; } }, {passive:true});
stackEl.addEventListener('touchend', e => { if (ex===null) return; const r = stackEl.getBoundingClientRect(); const dx = e.changedTouches[0].clientX - r.left - ex, dy = Math.abs(e.changedTouches[0].clientY - ey); ex=null; if (dx > 70 && dy < 60) back(); }, {passive:true});

// ---------- desktop device scaling ----------
function fit(){
  const d = $('#device');
  if (window.innerWidth <= 520){ d.style.transform=''; return; }
  const s = Math.min(1, (window.innerHeight - 56) / 868, (window.innerWidth - 24) / 414);
  d.style.transform = s < 1 ? 'scale('+s+')' : '';
  d.style.margin = s < 1 ? (-(868*(1-s))/2)+'px '+(-(414*(1-s))/2)+'px' : '';
}
window.addEventListener('resize', fit); fit();

// ---------- boot ----------
updateBadges();
const params = new URLSearchParams(location.search);
switchTab('home');
setStatus(true);
const skip = params.has('nosplash');
setTimeout(() => {
  $('#splash').classList.add('hide');
  const deep = params.get('p'); if (deep && P[deep]) push(PDP, deep);
  const tab = params.get('tab'); if (tab && roots[tab]) switchTab(tab);
  if (!skip && !params.has('nopush') && dropAlerts) setTimeout(showDropPush, 2600);
}, skip ? 0 : 2100);
})();
