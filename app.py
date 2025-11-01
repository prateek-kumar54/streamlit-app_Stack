"""STACK Streamlit front-end orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import streamlit as st
import streamlit.components.v1 as components
from html import escape

from features import (
    data_reconciliation,
    deal_document_parsing,
    sample3,
    sample4,
    sample5,
)

st.set_page_config(
    page_title="STACK – Automation | Data | Insights",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@dataclass(frozen=True)
class Feature:
    slug: str
    title: str
    blurb: str
    module: object


FeatureMap = Dict[str, Feature]


# ---------------------------------------------
# Pop-up helpers (toasts)
# ---------------------------------------------
def show_popup_error(msg, *, title="Error"):
    components.html(
        f"""
    <style>
      #sx-alert-wrap {{
        position: fixed; top: 18px; right: 18px; z-index: 99999;
        font-family: ui-sans-serif, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
      }}
      .sx-card {{
        position: relative;
        background: #fff5f5; color: #842029;
        border: 1px solid #f5c2c7; border-radius: 12px;
        box-shadow: 0 10px 24px rgba(0,0,0,.12);
        max-width: 520px; padding: 14px 44px 14px 14px;
      }}
      .sx-title {{ font-weight: 700; margin-bottom: 4px; }}
      .sx-close {{
        position: absolute; top: 8px; right: 10px;
        background: transparent; border: 0; cursor: pointer;
        font-size: 22px; line-height: 1; color: inherit;
      }}
    </style>
    <div id="sx-alert-wrap">
      <div class="sx-card">
        <button class="sx-close" onclick="this.closest('#sx-alert-wrap').remove()">×</button>
        <div class="sx-title">{escape(title)}</div>
        <div class="sx-body">{escape(msg)}</div>
      </div>
    </div>
    """,
        height=140,
        scrolling=False,
    )


def show_popup_warning(msg, *, title="Warning"):
    components.html(
        f"""
    <style>
      #sx-warn-wrap {{
        position: fixed; top: 18px; right: 18px; z-index: 99999;
        font-family: ui-sans-serif, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
      }}
      .sx-card {{
        position: relative;
        background: #fff8e1; color: #7a4d00;
        border: 1px solid #ffe08a; border-radius: 12px;
        box-shadow: 0 10px 24px rgba(0,0,0,.12);
        max-width: 520px; padding: 14px 44px 14px 14px;
      }}
      .sx-title {{ font-weight: 700; margin-bottom: 4px; }}
      .sx-close {{
        position: absolute; top: 8px; right: 10px;
        background: transparent; border: 0; cursor: pointer;
        font-size: 22px; line-height: 1; color: inherit;
      }}
    </style>
    <div id="sx-warn-wrap">
      <div class="sx-card">
        <button class="sx-close" onclick="this.closest('#sx-warn-wrap').remove()">×</button>
        <div class="sx-title">{escape(title)}</div>
        <div class="sx-body">{escape(msg)}</div>
      </div>
    </div>
    """,
        height=140,
        scrolling=False,
    )


def show_popup_info(msg, *, title="Info"):
    components.html(
        f"""
    <style>
      #sx-info-wrap {{
        position: fixed; top: 18px; right: 18px; z-index: 99999;
        font-family: ui-sans-serif, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
      }}
      .sx-card {{
        position: relative;
        background: #f1f5ff; color: #1e40af;
        border: 1px solid #bfdbfe; border-radius: 12px;
        box-shadow: 0 10px 24px rgba(0,0,0,.12);
        max-width: 520px; padding: 14px 44px 14px 14px;
      }}
      .sx-title {{ font-weight: 700; margin-bottom: 4px; }}
      .sx-close {{
        position: absolute; top: 8px; right: 10px;
        background: transparent; border: 0; cursor: pointer;
        font-size: 22px; line-height: 1; color: inherit;
      }}
    </style>
    <div id="sx-info-wrap">
      <div class="sx-card">
        <button class="sx-close" onclick="this.closest('#sx-info-wrap').remove()">×</button>
        <div class="sx-title">{escape(title)}</div>
        <div class="sx-body">{escape(msg)}</div>
      </div>
    </div>
    """,
        height=140,
        scrolling=False,
    )


# ---------------------------------------------
# Global CSS / Theme
# ---------------------------------------------
st.markdown(
    """
<style>
  :root {
    --bg-cream: #FEFFEC;
    --ink:#222222;
    --btn-bg:#D6B4FC;
    --btn-text:#000;
  }
  html, body, .stApp {
    background: var(--bg-cream) !important;
    color: var(--ink) !important;
  }
  [data-testid="stAppViewContainer"]{ padding:0 !important; }
  .block-container{ padding-top:0 !important; padding-left:0 !important; padding-right:0 !important; }
  header[data-testid="stHeader"], [data-testid="stToolbar"]{ background: var(--bg-cream) !important; }

  /* Buttons rack */
  .btnRack{
    margin: clamp(18px, 3.2vw, 28px) auto 40px auto;
    display: grid; grid-auto-flow: column; grid-auto-columns: 1fr;
    gap: clamp(10px, 1.6vw, 16px);
    width: min(88vw, 980px);
  }
  a.swatch{
    text-decoration: none !important; background: var(--btn-bg); color: var(--btn-text);
    border: 0; border-radius: 18px; aspect-ratio: 2 / 3;
    display: flex; flex-direction: column; align-items:flex-start; justify-content: space-between;
    padding: clamp(12px, 1.8vw, 16px);
    box-shadow: 0 1px 0 rgba(255,255,255,.35) inset, 0 6px 18px rgba(0,0,0,.08);
    transition: transform .12s ease, box-shadow .12s ease;
  }
  a.swatch:hover{ transform: translateY(-2px); box-shadow: 0 1px 0 rgba(255,255,255,.45) inset, 0 10px 26px rgba(0,0,0,.12); }

  .btnTitle{ font-family: "EB Garamond", Garamond, "Times New Roman", serif; font-weight:700; font-size: clamp(16px, 2.0vw, 22px); line-height:1.1; }
  .btnText{ font-family: "EB Garamond", Garamond, "Times New Roman", serif; font-weight:600; line-height:1.22; }
  .btnText.tiny{ font-size: clamp(10px, 1.12vw, 12.8px); }

  .formWrap{ width:min(70vw,980px); margin: 8px auto 80px auto; }
  .formHead{ font-family:"EB Garamond", Garamond, "Times New Roman", serif; font-weight:800; font-size: clamp(18px,2.6vw,28px); margin: 0 0 0; }
  .hint{ opacity:.9; font-size: 1rem; margin: 2px 0 10px; }
  .divider{ height:1px; background:rgba(0,0,0,.08); margin: 12px 0 8px; }

  .stButton > button, .stDownloadButton > button, .stForm button, .stFileUploader button{
    background: var(--btn-bg) !important; color: var(--btn-text) !important; border: 0 !important; border-radius: 10px !important;
  }
  .stButton > button:hover, .stDownloadButton > button:hover, .stForm button:hover, .stFileUploader button:hover{ filter: brightness(0.95); }
  div[data-testid="stFileUploadDropzone"]{ border-radius: 10px; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------
# Hero (logo + title + tagline)
# ---------------------------------------------
HERO_HTML = r"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@800;900&family=EB+Garamond:wght@400;600;700;800&display=swap');
  :root{
    --bg: #FEFFEC;
    --ink:#222;
    --railW: min(40vw, 560px);
    --lockupH: clamp(64px, 8vw, 110px);
  }
  html, body { background: transparent; }
  .rail{ width: var(--railW); margin: 34px 0 12px 34px; }
  .lockup{ height: var(--lockupH); display:flex; align-items:center; gap:clamp(14px,2.4vw,28px); }
  .textWrap{ display:flex; flex-direction:column; align-items:flex-start; }
  .word{
    font-family:"Orbitron",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    font-weight:900; font-size:calc(var(--lockupH) * .576); line-height:1; letter-spacing:.04em; color:var(--ink); white-space:nowrap;
  }
  .tagline{
    margin-top: clamp(4px, .7vw, 8px);
    font-family: "EB Garamond", Garamond, "Times New Roman", serif;
    font-weight: 800; font-size: calc(var(--lockupH) * .154); letter-spacing: .06em; color: var(--ink); opacity: .9; white-space: nowrap;
  }
  .logoWrap{ height:calc(var(--lockupH) * .92); aspect-ratio:1/1; display:grid; place-items:center; }
  svg#stackLogo{ height:100%; width:100%; }
  .facelet{ stroke:var(--ink); stroke-width:1.4; vector-effect:non-scaling-stroke; shape-rendering:geometricPrecision; stroke-linejoin:round; stroke-linecap:round; fill:var(--bg); }
</style>

<style>
.homeAnchor{ display:inline-block; text-decoration:none; color:inherit; }
.lockup{ cursor:pointer; }
</style>

<div class="rail">
  <a class="homeAnchor" href="?page=home" target="_top" aria-label="Go to home">
    <div class="lockup">
      <div class="logoWrap"><svg id="stackLogo" viewBox="0 0 260 260" role="img" aria-label="STACK stacked-cube logo rotating"></svg></div>
      <div class="textWrap">
        <div class="word">STACK</div>
        <div class="tagline">Automation | Data | Insights</div>
      </div>
    </div>
  </a>
</div>

<script>
(function(){
  const svg = document.getElementById('stackLogo');
  const NS = 'http://www.w3.org/2000/svg';
  const SIZE=24, SPEED=(2*Math.PI)/10, PITCH=0.30, GAP=0.06;
  const SHIFT_X=0.18, SHIFT_Y=0.11;
  const LAYER_SHIFT=[
    [2*SHIFT_X, 2*SHIFT_Y, 0],
    [SHIFT_X, SHIFT_Y, 0],
    [0, 0, 0],
    [-SHIFT_X, -SHIFT_Y, 0],
    [-2*SHIFT_X, -2*SHIFT_Y, 0]
  ];
  const COS=Math.sqrt(3)/2, SIN=0.5;
  function rotX(p,a){const[x,y,z]=p,c=Math.cos(a),s=Math.sin(a);return [x,y*c-z*s,y*s+z*c];}
  function rotY(p,a){const[x,y,z]=p,c=Math.cos(a),s=Math.sin(a);return [x*c+z*s,y,-x*s+z*c];}
  function project(x,y,z){return[(x-y)*COS*SIZE,(x+y)*SIN*SIZE-z*SIZE];}
  const GRID_X=[-1.5,-0.5,0.5,1.5];
  const GRID_Y=GRID_X;
  const GRID_Z=[-1.5,-0.9,-0.3,0.3,0.9,1.5];
  function insetQuad(q,axis){
    const cx=(q[0][0]+q[1][0]+q[2][0]+q[3][0])/4, cy=(q[0][1]+q[1][1]+q[2][1]+q[3][1])/4, cz=(q[0][2]+q[1][2]+q[2][2]+q[3][2])/4;
    return q.map(([x,y,z])=>{
      let dx=x-cx, dy=y-cy, dz=z-cz;
      if(axis==='x')dx=0; if(axis==='y')dy=0; if(axis==='z')dz=0;
      return [x-dx*GAP,y-dy*GAP,z-dz*GAP];
    });
  }
  function layerFromZ(zc){
    if(zc<-1.2) return 0;
    if(zc<-0.6) return 1;
    if(zc<0.6) return 2;
    if(zc<1.2) return 3;
    return 4;
  }
  function buildFace(axis,value){
    const quads=[];
    if(axis==='x'){
      for(let yi=0; yi<GRID_Y.length-1; yi++){
        for(let zi=0; zi<GRID_Z.length-1; zi++){
          const y0=GRID_Y[yi], y1=GRID_Y[yi+1];
          const z0=GRID_Z[zi], z1=GRID_Z[zi+1];
          const quad=insetQuad([
            [value,y0,z0],
            [value,y1,z0],
            [value,y1,z1],
            [value,y0,z1]
          ],axis);
          const el=document.createElementNS(NS,'polygon');
          el.setAttribute('class','facelet');
          quads.push({quad,el,layer:layerFromZ((z0+z1)/2)});
        }
      }
      return quads;
    }
    if(axis==='y'){
      for(let xi=0; xi<GRID_X.length-1; xi++){
        for(let zi=0; zi<GRID_Z.length-1; zi++){
          const x0=GRID_X[xi], x1=GRID_X[xi+1];
          const z0=GRID_Z[zi], z1=GRID_Z[zi+1];
          const quad=insetQuad([
            [x0,value,z0],
            [x1,value,z0],
            [x1,value,z1],
            [x0,value,z1]
          ],axis);
          const el=document.createElementNS(NS,'polygon');
          el.setAttribute('class','facelet');
          quads.push({quad,el,layer:layerFromZ((z0+z1)/2)});
        }
      }
      return quads;
    }
    for(let xi=0; xi<GRID_X.length-1; xi++){
      for(let yi=0; yi<GRID_Y.length-1; yi++){
        const x0=GRID_X[xi], x1=GRID_X[xi+1];
        const y0=GRID_Y[yi], y1=GRID_Y[yi+1];
        const quad=insetQuad([
          [x0,y0,value],
          [x1,y0,value],
          [x1,y1,value],
          [x0,y1,value]
        ],axis);
        const el=document.createElementNS(NS,'polygon');
        el.setAttribute('class','facelet');
        quads.push({quad,el,layer:layerFromZ(value)});
      }
    }
    return quads;
  }
  let facelets=[]
    .concat(buildFace('z',1.5))
    .concat(buildFace('z',-1.5))
    .concat(buildFace('x',-1.5))
    .concat(buildFace('x',1.5))
    .concat(buildFace('y',-1.5))
    .concat(buildFace('y',1.5));
  const g=document.createElementNS(NS,'g'); facelets.forEach(f=>g.appendChild(f.el)); svg.appendChild(g);
  (function setViewBox(){
    let minx=Infinity,miny=Infinity,maxx=-Infinity,maxy=-Infinity;
    const samples=32;
    for(let s=0;s<samples;s++){
      const a=(s/samples)*Math.PI*2;
      for(const f of facelets){
        for(const p of f.quad){
          const o=LAYER_SHIFT[f.layer];
          const q=[p[0]+o[0],p[1]+o[1],p[2]+o[2]];
          const r=rotX(rotY(q,a),PITCH);
          const [X,Y]=project(...r);
          if(X<minx)minx=X;
          if(Y<miny)miny=Y;
          if(X>maxx)maxx=X;
          if(Y>maxy)maxy=Y;
        }
      }
    }
    const pad=12;
    svg.setAttribute('viewBox',`${minx-pad} ${miny-pad} ${(maxx-minx)+2*pad} ${(maxy-miny)+2*pad}`);
  })();
  let t0=performance.now();
  function frame(t){
    const theta=((t-t0)/1000)*SPEED;
    render(theta);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  function render(theta){
    const ordered=[];
    for(const f of facelets){
      let depth=0;
      const pts2d=[];
      const o=LAYER_SHIFT[f.layer];
      for(const p of f.quad){
        const q=[p[0]+o[0],p[1]+o[1],p[2]+o[2]];
        const r=rotX(rotY(q,theta),PITCH);
        depth+=r[0]+r[1]+r[2];
        const [X,Y]=project(...r);
        pts2d.push([X,Y]);
      }
      ordered.push({el:f.el,depth,pts2d});
    }
    ordered.sort((a,b)=>a.depth-b.depth);
    ordered.forEach(o=>{
      o.el.setAttribute('points', o.pts2d.map(([x,y])=>`${x},${y}`).join(' '));
      g.appendChild(o.el);
    });
  }
})();
</script>
"""

components.html(HERO_HTML, height=190, scrolling=False)
st.markdown(
    """
<style>
a.stackHomeHotspot{
  position: fixed; top: 26px; left: 34px; width: min(40vw, 560px);
  height: clamp(64px, 8vw, 110px); z-index: 99999; display: block; background: transparent; cursor: pointer; pointer-events: auto;
}
</style>
<a class="stackHomeHotspot" href="?page=home" target="_self" aria-label="Go to home"></a>
""",
    unsafe_allow_html=True,
)

VALUEPROP_HTML = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@800;900&family=EB+Garamond:wght@400;600;700;800&display=swap');
.valuePropInner, .btnRack, .swatch, .btnTitle, .btnText { font-family: "EB Garamond", Garamond, "Times New Roman", serif; }
.valueProp{ width:100%; margin: clamp(5px, 1vw, 5px) auto 0 auto; display:grid; place-items:center; }
.valuePropInner{ max-width: min(100ch, 90vw); text-align: center; color:#222; }
.vpTitle{ font-weight: 800; font-size: clamp(24px, 3.2vw, 32px); line-height: 1.2; }
.vpText{ margin-top: 10px; font-weight: 700; font-size: clamp(12.6px, 1.62vw, 18px); line-height: 1.35; }
</style>
<section class="valueProp">
  <div class="valuePropInner">
    <div class="vpTitle">Heavy Lifting, Human Thinking</div>
    <div class="vpText">
      With transformer models at its core, the platform serves as an extra pair of expert hands,<br>
      an assistive layer for handling the heavy lifting of data wrangling and information gathering
    </div>
  </div>
</section>
"""

FEATURES: FeatureMap = {
    "datarecon": Feature(
        slug="datarecon",
        title="Data Reconciliation",
        blurb="Data wrangling from Demat and CSGL statements, delivering outputs in a ready-to-compare format.",
        module=data_reconciliation,
    ),
    "dealparse": Feature(
        slug="dealparse",
        title="Deal Document Parsing",
        blurb="Extract structured data from deal documents in a ready-to-use format.",
        module=deal_document_parsing,
    ),
    "sample3": Feature(
        slug="sample3",
        title="Sample 3",
        blurb="Button subtext",
        module=sample3,
    ),
    "sample4": Feature(
        slug="sample4",
        title="Sample 4",
        blurb="Button subtext",
        module=sample4,
    ),
    "sample5": Feature(
        slug="sample5",
        title="Sample 5",
        blurb="Button subtext",
        module=sample5,
    ),
}

page = st.query_params.get("page", "home")

if page == "home":
    components.html(VALUEPROP_HTML, height=110, scrolling=False)
    swatches = "".join(
        f"""
          <a class=\"swatch\" href=\"?page={feat.slug}\" target=\"_self\">
            <div class=\"btnTitle\">{feat.title}</div>
            <div class=\"btnText tiny\">{feat.blurb}</div>
          </a>
        """
        for feat in FEATURES.values()
    )
    st.markdown(
        f"""
        <div class="btnRack" aria-label="Samples">
        {swatches}
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    feature = FEATURES.get(page)
    if not feature:
        st.error("Unknown page.")
    else:
        feature.module.render(show_popup_error, show_popup_warning, show_popup_info)

