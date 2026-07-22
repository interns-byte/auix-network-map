from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AUiX Network Map", layout="wide", initial_sidebar_state="collapsed")

DATA_FILE = Path(__file__).with_name("Streamlit.xlsx")

CATEGORY_STYLE = {
    "Air University": {"color": "#e32119", "label": "AIR UNIVERSITY"},
    "Academia": {"color": "#0a55d5", "label": "ACADEMIA"},
    "Industry": {"color": "#ff9800", "label": "INDUSTRY"},
    "MIL & GOV": {"color": "#57a52c", "label": "MIL & GOV"},
}


def normalize_category(value: object) -> str:
    text = str(value).strip()
    aliases = {
        "Air Univerity": "Air University",
        "Air university": "Air University",
        "Mil & Gov": "MIL & GOV",
        "MIL&GOV": "MIL & GOV",
        "MIL & Gov": "MIL & GOV",
    }
    return aliases.get(text, text)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    data = pd.read_excel(DATA_FILE)
    data.columns = [str(column).strip().lower() for column in data.columns]

    if "engagament" in data.columns and "engagement" not in data.columns:
        data = data.rename(columns={"engagament": "engagement"})

    required = {"name", "type", "engagement"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    for optional in ("relationship", "expertise"):
        if optional not in data.columns:
            data[optional] = "Not provided"

    data = data.dropna(subset=["name", "type"]).copy()
    data["name"] = data["name"].astype(str).str.strip()
    data["type"] = data["type"].map(normalize_category)
    data["engagement"] = pd.to_numeric(data["engagement"], errors="coerce").fillna(0)
    data["relationship"] = data["relationship"].fillna("Not provided").astype(str).str.strip()
    data["expertise"] = data["expertise"].fillna("Not provided").astype(str).str.strip()
    return data[data["type"].isin(CATEGORY_STYLE)].copy()


st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"], .stApp { background:#031630 !important; }
header[data-testid="stHeader"] { display:none; }
[data-testid="stToolbar"] { display:none; }
.block-container { padding:0 !important; max-width:none !important; }
iframe { display:block; width:100%; border:0; }
</style>
""",
    unsafe_allow_html=True,
)

try:
    df = load_data()
except Exception as exc:
    st.error(f"The spreadsheet could not be loaded: {exc}")
    st.stop()

records = []
for row in df.to_dict(orient="records"):
    records.append(
        {
            "name": str(row["name"]),
            "type": str(row["type"]),
            "engagement": float(row["engagement"]),
            "relationship": str(row["relationship"]),
            "expertise": str(row["expertise"]),
        }
    )

payload = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
styles_payload = json.dumps(CATEGORY_STYLE, ensure_ascii=False).replace("</", "<\\/")

html = r'''<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
<style>
:root { --bg:#031630; --panel:#0a2448; --line:rgba(255,255,255,.74); --muted:#aac9f5; }
* { box-sizing:border-box; }
html, body { margin:0; width:100%; height:100%; overflow:hidden; background:var(--bg); color:white; font-family:Arial, Helvetica, sans-serif; }
#app { width:100vw; height:100vh; display:grid; grid-template-columns:minmax(0, 1fr) 340px; background:radial-gradient(circle at 42% 42%, #0b2a52 0%, #031630 62%, #020d1f 100%); }
#mapWrap { min-width:0; height:100vh; position:relative; overflow:hidden; }
#map { width:100%; height:100%; display:block; }
#panel { height:100vh; overflow-y:auto; padding:88px 18px 18px; border-left:1px solid rgba(255,255,255,.18); background:rgba(2,13,31,.78); }
#panelTitle { position:absolute; top:22px; right:18px; width:304px; color:#d8e8ff; font-weight:800; font-size:14px; letter-spacing:.02em; }
.empty { background:rgba(10,36,72,.94); border:1px solid rgba(255,255,255,.3); border-radius:16px; padding:18px; color:#c8daf4; line-height:1.45; }
.card { position:relative; background:rgba(10,36,72,.96); border:1px solid rgba(255,255,255,.32); border-radius:16px; padding:17px 42px 17px 18px; margin-bottom:12px; box-shadow:0 8px 28px rgba(0,0,0,.3); }
.card h3 { margin:0 0 12px; font-size:22px; }
.close { position:absolute; right:12px; top:10px; width:26px; height:26px; border:0; border-radius:50%; background:white; color:#0a2448; font-weight:900; font-size:16px; cursor:pointer; }
.label { color:var(--muted); font-weight:800; font-size:13px; margin-top:9px; }
.value { font-size:15px; margin-top:2px; overflow-wrap:anywhere; }
#tooltip { position:absolute; z-index:20; min-width:190px; max-width:280px; pointer-events:none; opacity:0; transform:translate(-50%, calc(-100% - 16px)); background:#10284b; border:1px solid rgba(255,255,255,.38); border-radius:10px; padding:10px 12px; box-shadow:0 8px 24px rgba(0,0,0,.35); font-size:13px; line-height:1.35; transition:opacity .08s; }
#tooltip b { font-size:15px; }
.title { font-weight:900; fill:white; text-anchor:middle; }
.subtitle { fill:#d9e7ff; text-anchor:middle; font-size:12px; }
.edge { stroke:var(--line); stroke-linecap:round; }
.node { cursor:pointer; }
.node circle { stroke:white; stroke-width:2; transition:filter .12s, stroke-width .12s; }
.node:hover circle { filter:brightness(1.12); stroke-width:3; }
.node.selected circle { stroke:#ffe66d; stroke-width:5; }
.catText, .centerText { fill:white; font-weight:900; text-anchor:middle; dominant-baseline:middle; pointer-events:none; }
.orgText { fill:white; font-weight:800; font-size:13px; dominant-baseline:middle; pointer-events:none; paint-order:stroke; stroke:#031630; stroke-width:4px; stroke-linejoin:round; }
.mobileTabs { display:none; }

@media (max-width: 700px) {
  #app { grid-template-columns:1fr; grid-template-rows:100vh; }
  #mapWrap { height:100vh; }
  #panel { position:absolute; z-index:30; left:8px; right:8px; bottom:8px; height:auto; max-height:39vh; overflow-y:auto; padding:0; border:0; background:transparent; display:none; }
  #panel.hasCards { display:block; }
  #panelTitle { display:none; }
  .card { margin:0 0 7px; padding:12px 38px 12px 14px; border-radius:13px; }
  .card h3 { font-size:18px; margin-bottom:7px; }
  .label { font-size:11px; margin-top:6px; }
  .value { font-size:13px; }
  .empty { display:none; }
  #tooltip { max-width:235px; min-width:170px; font-size:12px; }
}
</style>
</head>
<body>
<div id="app">
  <div id="mapWrap">
    <svg id="map" role="img" aria-label="Interactive AUiX network map"></svg>
    <div id="tooltip"></div>
  </div>
  <aside id="panel">
    <div id="panelTitle">Pinned organization details</div>
    <div id="cards"></div>
  </aside>
</div>
<script>
const DATA = __DATA__;
const STYLES = __STYLES__;
const categories = ["Air University", "Academia", "Industry", "MIL & GOV"];
const svg = document.getElementById('map');
const wrap = document.getElementById('mapWrap');
const tooltip = document.getElementById('tooltip');
const cards = document.getElementById('cards');
const panel = document.getElementById('panel');
let expanded = null;
let pinned = [];
let touchTipTimer = null;

function esc(v) { return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function isMobile() { return window.matchMedia('(max-width: 700px)').matches; }
function make(tag, attrs={}) { const el=document.createElementNS('http://www.w3.org/2000/svg', tag); Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v)); return el; }
function line(x1,y1,x2,y2,w=2) { return make('line',{x1,y1,x2,y2,'class':'edge','stroke-width':w}); }
function text(x,y,value,cls,size,anchor='middle') { const t=make('text',{x,y,'class':cls,'font-size':size,'text-anchor':anchor}); t.textContent=value; return t; }
function categoryData(cat) { return DATA.filter(d=>d.type===cat).sort((a,b)=>b.engagement-a.engagement || a.name.localeCompare(b.name)); }

function layout() {
  const w = wrap.clientWidth, h = wrap.clientHeight;
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  const mobile = isMobile();
  const titleY = mobile ? 28 : 42;
  svg.appendChild(text(w/2,titleY,'2025–2026 AUiX Network Map','title',mobile?22:34));
  svg.appendChild(text(w/2,titleY+(mobile?20:24), mobile ? 'Tap a category, then tap an organization.' : 'Click a category to open it. Hover for details. Click organizations to pin cards.','subtitle',mobile?10:12));

  if (mobile) drawMobile(w,h); else drawDesktop(w,h);
  renderCards();
}

function drawDesktop(w,h) {
  const panelSafe = 0;
  const cx=w*0.50, cy=h*0.54;
  const xGap=Math.min(w*0.31, 390), yGap=Math.min(h*0.29, 250);
  const pos={
    'Air University':[cx-xGap,cy-yGap], 'Academia':[cx+xGap,cy-yGap],
    'Industry':[cx-xGap,cy+yGap], 'MIL & GOV':[cx+xGap,cy+yGap]
  };
  // Lower categories need extra room beneath them when their organization ring opens.
  // Move only the expanded lower hub upward; the normal four-hub view stays unchanged.
  if(expanded==='Industry' || expanded==='MIL & GOV') {
    pos[expanded][1] = Math.min(pos[expanded][1], h*0.68);
  }
  categories.forEach(cat=>{ const [x,y]=pos[cat]; svg.appendChild(line(cx,cy,x,y,3)); });
  drawHub(cx,cy,76,'#f4c542','AUiX','center');
  categories.forEach(cat=>{ const [x,y]=pos[cat]; drawHub(x,y,78,STYLES[cat].color,STYLES[cat].label,'category',cat); });
  if (expanded) drawOrganizationsDesktop(expanded,pos[expanded][0],pos[expanded][1],w,h);
}

function drawHub(x,y,r,color,label,type,cat=null) {
  const g=make('g',{'class':'node','data-type':type});
  g.appendChild(make('circle',{cx:x,cy:y,r,fill:color}));
  const parts=label.split(' ');
  if (label==='AIR UNIVERSITY' || label==='MIL & GOV') {
    const l1=label==='AIR UNIVERSITY'?'AIR':'MIL &';
    const l2=label==='AIR UNIVERSITY'?'UNIVERSITY':'GOV';
    g.appendChild(text(x,y-10,l1,'catText',type==='center'?31:20));
    g.appendChild(text(x,y+14,l2,'catText',type==='center'?31:20));
  } else g.appendChild(text(x,y,label,type==='center'?'centerText':'catText',type==='center'?31:20));
  g.addEventListener('click',()=>{
    if(type==='center'){ expanded=null; layout(); return; }
    expanded = expanded===cat ? null : cat; layout();
  });
  g.addEventListener('mouseenter',e=>showTip(e, {name:cat||'AUiX', type:cat||'Center', engagement:'', relationship:type==='category'?(expanded===cat?'Click to hide organizations':'Click to show organizations'):'Click to collapse map', expertise:''}));
  g.addEventListener('mouseleave',hideTip);
  svg.appendChild(g);
}

function drawOrganizationsDesktop(cat,hx,hy,w,h) {
  const items=categoryData(cat), n=items.length;
  if(!n) return;

  // Reserve room for labels on every side, then size the ellipse to the space that
  // actually exists around the selected category. This prevents the lower and left
  // Industry bubbles from being clipped by the map boundary.
  const sideLabelRoom = cat==='Industry' ? 165 : 135;
  const verticalRoom = 58;
  const maxRx = Math.max(120, Math.min(hx-sideLabelRoom, w-hx-sideLabelRoom));
  const maxRy = Math.max(105, Math.min(hy-verticalRoom, h-hy-verticalRoom));

  let desiredRx=Math.max(175,n*18);
  let desiredRy=Math.max(135,n*10);
  if(cat==='Industry') {
    desiredRx=Math.max(255,n*20);
    desiredRy=Math.max(145,n*10);
  }
  const rx=Math.min(desiredRx, w*0.25, maxRx);
  const ry=Math.min(desiredRy, h*0.23, maxRy);

  const max=Math.max(...items.map(d=>d.engagement),1);
  items.forEach((d,i)=>{
    const a=-Math.PI/2 + i*(Math.PI*2/n);
    const x=hx+rx*Math.cos(a), y=hy+ry*Math.sin(a);
    const r=17+17*Math.sqrt(d.engagement/max);
    svg.insertBefore(line(hx,hy,x,y,1.2+Math.min(d.engagement,60)/35), svg.querySelector('.node'));
    drawOrg(d,x,y,r,a,w,h);
  });
}

function drawMobile(w,h) {
  const top=78, margin=12, gap=8;
  const tabW=(w-margin*2-gap)/2, tabH=54;
  categories.forEach((cat,i)=>{
    const col=i%2,row=Math.floor(i/2),x=margin+col*(tabW+gap),y=top+row*(tabH+gap);
    const g=make('g',{'class':'node'});
    g.appendChild(make('rect',{x,y,width:tabW,height:tabH,rx:18,fill:STYLES[cat].color,stroke:'white','stroke-width':expanded===cat?4:1.8}));
    g.appendChild(text(x+tabW/2,y+tabH/2+1,STYLES[cat].label,'catText',cat==='Air University'?15:16));
    g.addEventListener('click',()=>{expanded=expanded===cat?null:cat; layout();});
    svg.appendChild(g);
  });
  const contentTop=top+2*(tabH+gap)+10;
  if(!expanded){ svg.appendChild(text(w/2,contentTop+90,'Choose a category above','title',20)); return; }
  const hx=w/2, hy=contentTop+Math.min(165,(h-contentTop)*0.30);
  const hubR=58;
  drawHubMobile(hx,hy,hubR,STYLES[expanded].color,STYLES[expanded].label,expanded);
  const items=categoryData(expanded), n=items.length, max=Math.max(...items.map(d=>d.engagement),1);
  const availableBottom = pinned.length ? h*0.57 : h-26;
  const rx=Math.min(w*0.38,150), ry=Math.min(Math.max(120,n*11), Math.max(120,(availableBottom-hy)*0.72));
  items.forEach((d,i)=>{
    const a=-Math.PI/2+i*(Math.PI*2/n), x=hx+rx*Math.cos(a), y=hy+ry*Math.sin(a);
    const r=15+13*Math.sqrt(d.engagement/max);
    svg.insertBefore(line(hx,hy,x,y,1.2), svg.querySelector('.node'));
    drawOrg(d,x,y,r,a,w,h,true);
  });
}

function drawHubMobile(x,y,r,color,label,cat){
  const g=make('g',{'class':'node'}); g.appendChild(make('circle',{cx:x,cy:y,r,fill:color}));
  const l=label==='AIR UNIVERSITY'?['AIR','UNIVERSITY']:label==='MIL & GOV'?['MIL &','GOV']:[label];
  l.forEach((s,i)=>g.appendChild(text(x,y+(i-(l.length-1)/2)*18,s,'catText',16)));
  g.addEventListener('click',()=>{expanded=null;layout();}); svg.appendChild(g);
}

function drawOrg(d,x,y,r,a,w,h,mobile=false){
  const g=make('g',{'class':'node orgNode'+(pinned.some(p=>p.name===d.name)?' selected':''),'data-name':d.name});
  g.appendChild(make('circle',{cx:x,cy:y,r,fill:STYLES[d.type].color}));
  const cos=Math.cos(a), sin=Math.sin(a); let tx=x,ty=y,anchor='middle';
  const pad=r+8;
  if(cos>0.28){tx=x+pad;anchor='start';} else if(cos<-0.28){tx=x-pad;anchor='end';}
  else if(sin<0){ty=y-pad-4;} else {ty=y+pad+8;}
  // Keep names inside the visible map region.
  if(anchor==='start' && tx>w-145){anchor='end';tx=x-pad;}
  if(anchor==='end' && tx<145){anchor='start';tx=x+pad;}
  const t=text(tx,ty,d.name,'orgText',mobile?11:13,anchor);
  g.appendChild(t);
  g.addEventListener('mouseenter',e=>showTip(e,d));
  g.addEventListener('mousemove',moveTip);
  g.addEventListener('mouseleave',hideTip);
  g.addEventListener('touchstart',e=>{showTipAtNode(g,d); clearTimeout(touchTipTimer); touchTipTimer=setTimeout(hideTip,2300);},{passive:true});
  g.addEventListener('click',()=>{ pin(d); });
  svg.appendChild(g);
}

function tipHtml(d){ return `<b>${esc(d.name)}</b><br>Category: ${esc(d.type)}${d.engagement!==''?`<br>Engagements: ${esc(Number(d.engagement).toLocaleString())}`:''}<br>Relationship: ${esc(d.relationship)}${d.expertise?`<br>Expertise: ${esc(d.expertise)}`:''}`; }
function showTip(e,d){ tooltip.innerHTML=tipHtml(d); tooltip.style.opacity='1'; moveTip(e); }
function moveTip(e){ const r=wrap.getBoundingClientRect(); tooltip.style.left=(e.clientX-r.left)+'px'; tooltip.style.top=(e.clientY-r.top)+'px'; }
function showTipAtNode(g,d){ const c=g.querySelector('circle'); if(!c)return; const p=svg.createSVGPoint(); p.x=parseFloat(c.getAttribute('cx')); p.y=parseFloat(c.getAttribute('cy')); const sp=p.matrixTransform(svg.getScreenCTM()); const r=wrap.getBoundingClientRect(); tooltip.innerHTML=tipHtml(d); tooltip.style.left=(sp.x-r.left)+'px'; tooltip.style.top=(sp.y-r.top)+'px'; tooltip.style.opacity='1'; }
function hideTip(){ tooltip.style.opacity='0'; }

function pin(d){ if(!pinned.some(p=>p.name===d.name)){ pinned.push(d); if(pinned.length>4)pinned.shift(); } renderCards(); updateSelection(); }
function closePin(name){ pinned=pinned.filter(p=>p.name!==name); renderCards(); updateSelection(); }
function updateSelection(){ document.querySelectorAll('.orgNode').forEach(g=>g.classList.toggle('selected',pinned.some(p=>p.name===g.dataset.name))); }
function renderCards(){
  cards.innerHTML='';
  if(!pinned.length){ cards.innerHTML='<div class="empty"><b>Organization details</b><br><br>Hover over a bubble for a quick preview. Click a bubble to pin its details here. Pinned cards stay open until you close them with ×.</div>'; panel.classList.remove('hasCards'); return; }
  panel.classList.add('hasCards');
  pinned.forEach(d=>{
    const card=document.createElement('div'); card.className='card';
    card.innerHTML=`<button class="close" aria-label="Close ${esc(d.name)}">×</button><h3>${esc(d.name)}</h3><div class="label">Category</div><div class="value">${esc(d.type)}</div><div class="label">Engagements</div><div class="value">${esc(Number(d.engagement).toLocaleString())}</div><div class="label">Relationship</div><div class="value">${esc(d.relationship)}</div><div class="label">Expertise</div><div class="value">${esc(d.expertise)}</div>`;
    card.querySelector('.close').addEventListener('click',()=>closePin(d.name)); cards.appendChild(card);
  });
}

let resizeTimer; window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(layout,120);});
layout();
</script>
</body>
</html>'''.replace('__DATA__', payload).replace('__STYLES__', styles_payload)

components.html(html, height=980, scrolling=False)
