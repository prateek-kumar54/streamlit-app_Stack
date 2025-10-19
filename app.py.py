# app.py
# STREAMLIT COMMUNITY CLOUD–READY
# - No Colab/cloudflared commands
# - No system apt-get deps; uses pypdfium2 for PDF->image
# - API keys are entered by the user at runtime (not stored on disk)

import os, re, json, base64
from io import BytesIO
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from html import escape

# ---------------------------------------------
# Page setup
# ---------------------------------------------
st.set_page_config(
    page_title="STACK – Automation | Data | Insights",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------
# Pop-up helpers (toasts)
# ---------------------------------------------
def show_popup_error(msg, *, title="Error"):
    components.html(f"""
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
    """, height=140, scrolling=False)

def show_popup_warning(msg, *, title="Warning"):
    components.html(f"""
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
    """, height=140, scrolling=False)

def show_popup_info(msg, *, title="Info"):
    components.html(f"""
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
    """, height=140, scrolling=False)

# ---------------------------------------------
# Global CSS / Theme
# ---------------------------------------------
st.markdown("""
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
""", unsafe_allow_html=True)

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
  const SHIFT_X=0.20, SHIFT_Y=0.12;
  const LAYER_SHIFT=[[0,0,0],[SHIFT_X,SHIFT_Y,0],[-SHIFT_X,-SHIFT_Y,0]];
  const COS=Math.sqrt(3)/2, SIN=0.5;
  function rotX(p,a){const[x,y,z]=p,c=Math.cos(a),s=Math.sin(a);return [x,y*c-z*s,y*s+z*c];}
  function rotY(p,a){const[x,y,z]=p,c=Math.cos(a),s=Math.sin(a);return [x*c+z*s,y,-x*s+z*c];}
  function project(x,y,z){return[(x-y)*COS*SIZE,(x+y)*SIN*SIZE-z*SIZE];}
  const grid=[-1.5,-0.5,0.5,1.5];
  function insetQuad(q,axis){
    const cx=(q[0][0]+q[1][0]+q[2][0]+q[3][0])/4, cy=(q[0][1]+q[1][1]+q[2][1]+q[3][1])/4, cz=(q[0][2]+q[1][2]+q[2][2]+q[3][2])/4;
    return q.map(([x,y,z])=>{
      let dx=x-cx, dy=y-cy, dz=z-cz;
      if(axis==='x')dx=0; if(axis==='y')dy=0; if(axis==='z')dz=0;
      return [x-dx*GAP,y-dy*GAP,z-dz*GAP];
    });
  }
  function layerFromZ(zc){ if(zc<=-0.5) return 0; if(zc>=0.5) return 2; return 1; }
  function buildFace(axis,value){
    const quads=[];
    for(let i=0;i<3;i++){
      for(let j=0;j<3;j++){
        let p00,p10,p11,p01,zc;
        if(axis==='x'){
          p00=[value,grid[i],grid[j]];
          p10=[value,grid[i+1],grid[j]];
          p11=[value,grid[i+1],grid[j+1]];
          p01=[value,grid[i],grid[j+1]];
          zc=(grid[j]+grid[j+1])/2;
        } else if(axis==='y'){
          p00=[grid[i],value,grid[j]];
          p10=[grid[i+1],value,grid[j]];
          p11=[grid[i+1],value,grid[j+1]];
          p01=[grid[i],value,grid[j+1]];
          zc=(grid[j]+grid[j+1])/2;
        } else {
          p00=[grid[i],grid[j],value];
          p10=[grid[i+1],grid[j],value];
          p11=[grid[i+1],grid[j+1],value];
          p01=[grid[i],grid[j+1],value];
          zc=value;
        }
        const quad=insetQuad([p00,p10,p11,p01],axis);
        const el=document.createElementNS(NS,'polygon');
        el.setAttribute('class','facelet');
        quads.push({quad,el,layer:layerFromZ(zc)});
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
st.markdown("""
<style>
a.stackHomeHotspot{
  position: fixed; top: 26px; left: 34px; width: min(40vw, 560px);
  height: clamp(64px, 8vw, 110px); z-index: 99999; display: block; background: transparent; cursor: pointer; pointer-events: auto;
}
</style>
<a class="stackHomeHotspot" href="?page=home" target="_self" aria-label="Go to home"></a>
""", unsafe_allow_html=True)

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

# ---------------------------------------------
# Routing
# ---------------------------------------------
page = st.query_params.get("page", "home")

# ---------------------------------------------
# HOME
# ---------------------------------------------
if page == "home":
    components.html(VALUEPROP_HTML, height=110, scrolling=False)
    st.markdown(
        """
        <div class="btnRack" aria-label="Samples">
          <a class="swatch" href="?page=datarecon" target="_self">
            <div class="btnTitle">Data Reconciliation</div>
            <div class="btnText tiny">Data wrangling from Demat and CSGL statements, delivering outputs in a ready-to-compare format.</div>
          </a>
          <a class="swatch" href="?page=dealparse" target="_self">
            <div class="btnTitle">Deal Document Parsing</div>
            <div class="btnText tiny">Extract structured data from deal documents in a ready-to-use format.</div>
          </a>
          <a class="swatch" href="?page=sample3" target="_self"><div class="btnTitle">Sample 3</div><div class="btnText tiny">Button subtext</div></a>
          <a class="swatch" href="?page=sample4" target="_self"><div class="btnTitle">Sample 4</div><div class="btnText tiny">Button subtext</div></a>
          <a class="swatch" href="?page=sample5" target="_self"><div class="btnTitle">Sample 5</div><div class="btnText tiny">Button subtext</div></a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------
import math

def _find_isin_in_text(text: str):
    m = re.search(r"\bIN[A-Z0-9]{10}\b", str(text).upper())
    return m.group(0) if m else None

def tidy_security_name(s: str) -> str:
    if not s:
        return s
    x = str(s)
    x = x.replace("%", "%")
    x = re.sub(r"^\s*\d+\s*\|\s*", "", x)
    x = x.replace("|", " ")
    x = re.sub(r"%(?=[A-Za-z0-9])", "% ", x)
    x = " ".join(x.split())
    x = re.split(r"\bISIN\b", x, maxsplit=1)[0].strip()
    return x

def _to_number(x):
    if x is None:
        return None
    s = str(x).strip()
    sign = -1 if re.match(r"^\(.*\)$", s) else 1
    s = s.strip("()")
    s = re.sub(r"[₹$, ]", "", s).replace(",", "")
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return None
    try:
        return sign * float(s)
    except Exception:
        return None

def canonicalize_row(r: dict) -> dict:
    out = dict(r)
    # normalize keys
    for k in list(out.keys()):
        nk = k.strip().lower().replace(" ", "_")
        if nk != k and nk not in out:
            out[nk] = out.pop(k)
    # tidy values
    if out.get("security_name"):
        out["security_name"] = tidy_security_name(out["security_name"])
    if out.get("isin"):
        out["isin"] = str(out["isin"]).replace(" ", "").upper()
    candidates = [
        out.get("market_value"),
        out.get("saleable_position_holding"),
        out.get("total_face_value"),
        out.get("amount"),
        out.get("value"),
    ]
    chosen = None
    for c in candidates:
        s = re.sub(r"[₹$, ,]", "", str(c)) if c is not None else ""
        if s and s.strip("0") != "":
            chosen = c
            break
    if chosen is None:
        bal = _to_number(out.get("balance"))
        rate = _to_number(out.get("market_rate"))
        if (bal is not None) and (rate is not None):
            chosen = bal * rate
    out["value"] = chosen
    return out

def segment_rows_by_isin(md_text: str):
    raw_lines = [ln.strip() for ln in str(md_text).splitlines() if ln and ln.strip()]
    # drop table border lines like '---- | ----'
    lines = [ln for ln in raw_lines if not set(ln.replace("|", "").strip()) <= set("-:")]
    chunks, cur = [], None

    def flush():
        nonlocal cur, chunks
        if cur and _find_isin_in_text(cur["row_text"]):
            m = re.search(r"\|\s*(\d+)\s*\|", cur["row_text"])
            cur["sr_no"] = int(m.group(1)) if m else None
            chunks.append(cur)
        cur = None

    for ln in lines:
        if _find_isin_in_text(ln):
            flush()
            cur = {"row_text": ln}
        else:
            if cur:
                if re.search(r"\b(?:isin|company|scrip|balance|market rate|market value|status)\b", ln, flags=re.I):
                    flush()
                    continue
                cur["row_text"] += " | " + ln
    flush()
    return chunks

def parse_single_row_fallback(row_text: str):
    rec = {"_span": row_text}
    rec["isin"] = _find_isin_in_text(row_text)
    cells = [c.strip() for c in row_text.split("|")]
    sec = None
    for i, c in enumerate(cells):
        if rec["isin"] and rec["isin"] in c.replace(" ", ""):
            if i + 1 < len(cells):
                sec = tidy_security_name(cells[i + 1])
                break
    rec["security_name"] = sec
    for i, c in enumerate(cells):
        cl = c.lower()
        nxt = cells[i + 1] if i + 1 < len(cells) else ""
        if "balance" in cl:
            rec["balance"] = _to_number(nxt) or _to_number(c)
        if "market rate" in cl:
            rec["market_rate"] = _to_number(nxt) or _to_number(c)
        if "market value" in cl:
            rec["market_value"] = _to_number(nxt) or _to_number(c)
        if "status" in cl and not rec.get("status"):
            rec["status"] = nxt if nxt else c
    return rec

# OCR: mistral
def encode_image_bytes_to_data_url(b: bytes, mime_hint: str) -> str:
    b64 = base64.b64encode(b).decode("utf-8")
    return f"data:{mime_hint};base64,{b64}"

def run_mistral_ocr_on_image_bytes(mistral_client, b: bytes, mime_hint: str = "image/jpeg") -> str:
    try:
        data_url = encode_image_bytes_to_data_url(b, mime_hint=mime_hint)
        resp = mistral_client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "image_url", "image_url": data_url},
            include_image_base64=False,
        )
        pages = getattr(resp, "pages", None) or (resp.get("pages", []) if isinstance(resp, dict) else [])
        md_chunks = []
        for p in pages:
            md = getattr(p, "markdown", None) or (p.get("markdown", "") if isinstance(p, dict) else "")
            if md:
                md_chunks.append(md)
        return "\n\n".join(md_chunks).strip()
    except Exception as e:
        show_popup_error(f"OCR failed: {e}")
        return ""

# LangExtract wrapper
PROMPT = """
You are an information-extraction system for Demat/CSGL statements.
Return JSON records for each table row with these optional fields:
date, isin, security_name, balance, market_rate, market_value, value, status.
Do not invent values; omit fields if unknown. Output must be valid JSON (no markdown fences).
"""
EXAMPLES = []

def _attempt_extract(model_id: str, text: str, *, use_json_object: bool, openai_key: str):
    import langextract as lx
    try:
        lm_params = {"temperature": 0, "seed": 7, "max_output_tokens": 600}
        fence = True
        if use_json_object:
            fence = False
            lm_params["response_format"] = {"type": "json_object"}
        res = lx.extract(
            text_or_documents=text,
            prompt_description=PROMPT,
            examples=EXAMPLES,
            model_id=model_id,
            api_key=openai_key,
            fence_output=fence,
            use_schema_constraints=False,
            language_model_params=lm_params,
        )
        return res, None
    except Exception as e:
        return None, e

def extract_records_with_langextract(text: str, model_choice: str, openai_key: str):
    # Try preferred ID then sensible fallbacks
    prefs = [model_choice]
    if ":" not in model_choice:
        prefs.append(f"openai:{model_choice}")
    prefs += ["openai:gpt-5-nano", "gpt-5-nano", "openai:gpt-5-mini", "gpt-5-mini", "openai:gpt-4.1-mini", "gpt-4.1-mini"]
    for mid in prefs:
        res, err = _attempt_extract(mid, text, use_json_object=True, openai_key=openai_key)
        if res is None:
            res, err = _attempt_extract(mid, text, use_json_object=False, openai_key=openai_key)
        if res is not None:
            try:
                payload = json.loads(json.dumps(res))  # cast to plain dict
                rows = []
                for ext in payload.get("extractions", []):
                    if ext.get("extraction_class") == "record":
                        attrs = ext.get("attributes", {}) or {}
                        attrs["_span"] = ext.get("extraction_text", "")
                        rows.append(attrs)
                return rows
            except Exception:
                return []
    return []

# PDF helpers (pure Python wheels: pypdf + pypdfium2)
def decrypt_pdf_if_needed(pdf_bytes: bytes, pw: str | None):
    from pypdf import PdfReader, PdfWriter
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception:
        return pdf_bytes, None  # not a standard PDF? pass through
    if reader.is_encrypted:
        if not pw:
            return None, "protected"
        try:
            ok = reader.decrypt(pw)
            if ok == 0:
                return None, "bad_password"
        except Exception:
            return None, "bad_password"
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        out = BytesIO()
        writer.write(out)
        out.seek(0)
        return out.getvalue(), None
    return pdf_bytes, None

def render_pdf_to_images(pdf_bytes: bytes, scale: float = 2.0):
    import pypdfium2 as pdfium
    imgs = []
    pdf = pdfium.PdfDocument(pdf_bytes)
    n = len(pdf)
    for i in range(n):
        page = pdf[i]
        bmp = page.render(scale=scale)  # ~ 144–200 dpi depending on scale
        imgs.append(bmp.to_pil())
        page.close()
    pdf.close()
    return imgs

# -----------------------------------------------------------
# DATA RECONCILIATION PAGE
# -----------------------------------------------------------
if page == "datarecon":
    st.markdown("""
    <style>
      .rail{ margin-bottom: 2px !important; }
      .formWrap{ width:min(70vw,980px); margin: 0 auto 72px auto !important; }
      [data-testid="stForm"]{ width: min(70vw, 980px) !important; margin-left: auto !important; margin-right: auto !important; }
      div[data-testid="stFileUploadDropzone"], div[data-testid="stTextInput"], div[data-testid="stCheckbox"], div[data-testid="stSelectbox"], div[data-testid="stExpander"]{ max-width: 100% !important; }
      [data-testid="stTextInput"] button[aria-label="Show password"], [data-testid="stTextInput"] button[aria-label="Hide password"]{ margin-right: 0 !important; }
      [data-baseweb="input"]{ padding-right: 6px !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.form("recon_form", border=False):
        st.markdown('<div class="formHead">Data Reconciliation</div>', unsafe_allow_html=True)

        files = st.file_uploader(
            "Upload Statements (Accepted formats: PDF/PNG/JPG/JPEG)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )

        colA, colB = st.columns([1, 1])
        with colA:
            pdf_password = st.text_input(
                "PDF password (optional) (If file is password protected, upload single file at a time)",
                type="password",
            )
        with colB:
            add_assist = st.checkbox("Conservative ‘missed row’ assist", value=False)

        with st.expander("API keys (required – not stored on disk)", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                mistral_key = st.text_input(
                    "MISTRAL_API_KEY",
                    value=st.session_state.get("MISTRAL_API_KEY", ""),
                    type="password",
                    help="Used for OCR (mistral-ocr-latest)."
                )
            with c2:
                openai_key = st.text_input(
                    "OPENAI_API_KEY",
                    value=st.session_state.get("OPENAI_API_KEY", ""),
                    type="password",
                    help="Used by LangExtract for record extraction."
                )
            remember = st.checkbox("Remember in this browser session", value=True)

        model = st.selectbox(
            "Extraction model (LangExtract)",
            ["gpt-5-nano-2025-08-07", "openai:gpt-5-nano", "openai:gpt-5-mini", "openai:gpt-4.1-mini"],
            index=0,
        )

        run = st.form_submit_button("Run Reconciliation")

    if run:
        if remember:
            st.session_state["MISTRAL_API_KEY"] = mistral_key
            st.session_state["OPENAI_API_KEY"] = openai_key

        # Dependency sanity checks (these are installed via requirements.txt)
        missing = []
        try:
            import pandas as pd  # noqa
        except Exception:
            missing.append("pandas")
        try:
            from dateutil import parser as dparser  # noqa
        except Exception:
            missing.append("python-dateutil")
        try:
            from mistralai import Mistral  # noqa
        except Exception:
            missing.append("mistralai")
        try:
            import langextract as lx  # noqa
        except Exception:
            missing.append("langextract[openai]")
        try:
            import pypdfium2  # noqa
        except Exception:
            missing.append("pypdfium2")
        try:
            import pypdf  # noqa
        except Exception:
            missing.append("pypdf")
        try:
            from PIL import Image  # noqa
        except Exception:
            missing.append("pillow")

        if missing:
            show_popup_error("Please install required packages before running: " + ", ".join(missing))
            st.stop()

        if not files:
            show_popup_warning("Please upload at least one file.")
            st.stop()

        if not mistral_key or not openai_key:
            show_popup_warning("Please enter MISTRAL_API_KEY and OPENAI_API_KEY in the form above.")
            st.stop()

        import pandas as pd
        from mistralai import Mistral

        mistral_client = Mistral(api_key=mistral_key)

        RUN_TAG = datetime.now().strftime("%Y%m%d_%H%M%S")
        all_rows = []

        with st.status("Processing…", expanded=False) as status:
            for f in files:
                name = (f.name or "").lower()
                b = f.read()

                if name.endswith(".pdf"):
                    dec, stt = decrypt_pdf_if_needed(b, pdf_password)
                    if stt == "bad_password":
                        show_popup_error(f"Incorrect password for {f.name}.")
                        continue
                    if stt == "protected":
                        show_popup_warning(f"{f.name} is password-protected; please provide the password.")
                        continue
                    pdf_bytes = dec if dec is not None else b

                    # Render to images with pypdfium2 (no system deps)
                    try:
                        pages = render_pdf_to_images(pdf_bytes, scale=2.0)
                    except Exception as e:
                        show_popup_error(f"PDF render failed for {f.name}: {e}")
                        continue

                    for i, pg in enumerate(pages, start=1):
                        buf = BytesIO()
                        pg.save(buf, format="PNG")
                        md_text = run_mistral_ocr_on_image_bytes(mistral_client, buf.getvalue(), "image/png")
                        chunks = segment_rows_by_isin(md_text)
                        for ch in chunks:
                            span_tag = f"[SOURCE_PDF: {f.name} | PAGE: {i}] | {ch['row_text']}"
                            recs = extract_records_with_langextract(span_tag, model, openai_key=openai_key)
                            r = recs[0] if len(recs) == 1 else parse_single_row_fallback(ch["row_text"])
                            r = canonicalize_row(r)
                            r["source_pdf"] = f.name
                            r["page"] = i
                            r["sr_no"] = ch.get("sr_no")
                            all_rows.append(r)

                elif name.endswith((".png", ".jpg", ".jpeg")):
                    mime = "image/png" if name.endswith(".png") else "image/jpeg"
                    md_text = run_mistral_ocr_on_image_bytes(mistral_client, b, mime)
                    chunks = segment_rows_by_isin(md_text)
                    for ch in chunks:
                        span_tag = f"[SOURCE_IMAGE: {f.name}] | {ch['row_text']}"
                        recs = extract_records_with_langextract(span_tag, model, openai_key=openai_key)
                        r = recs[0] if len(recs) == 1 else parse_single_row_fallback(ch["row_text"])
                        r = canonicalize_row(r)
                        r["source_image"] = f.name
                        r["sr_no"] = ch.get("sr_no")
                        all_rows.append(r)
                else:
                    show_popup_info(f"Skipping {f.name} (unsupported).")

            status.update(label="Building Excel…", state="running")

        if not all_rows:
            show_popup_warning("No rows extracted. Try a different page or a crisper scan.")
            st.stop()

        # De-dup & DataFrame
        def tidy_name(x): return tidy_security_name(x or "")
        seen = set()
        dedup = []
        for r in all_rows:
            key = (
                (r.get("isin") or "").strip().upper(),
                tidy_name(r.get("security_name")),
                str(r.get("value") or r.get("market_value") or "").strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            dedup.append(r)
        all_rows = dedup

        base_cols = ["date", "isin", "security_name", "value"]
        all_keys = set().union(*[r.keys() for r in all_rows])
        extra_cols = [c for c in sorted(all_keys) if c not in base_cols + ["_span"]]
        ordered_cols = base_cols + ["_span"] + extra_cols + ["sr_no"]
        df = pd.DataFrame(all_rows).reindex(columns=ordered_cols)

        # Excel to bytes
        out_name = f"extracted_transactions_{RUN_TAG}.xlsx"
        try:
            import xlsxwriter  # noqa
            engine = "xlsxwriter"
        except Exception:
            engine = None  # Pandas will try openpyxl if present

        out_buf = BytesIO()
        with pd.ExcelWriter(out_buf, engine=engine) as writer:
            df.to_excel(writer, index=False, sheet_name="Extract")
            if engine == "xlsxwriter":
                wb = writer.book
                ws = writer.sheets["Extract"]
                ws.freeze_panes(1, 0)
                width_map = {"date": 12, "isin": 20, "security_name": 40, "value": 18, "_span": 60, "sr_no": 8}
                for i, col in enumerate(df.columns):
                    ws.set_column(i, i, width_map.get(col, 18))
                num_fmt = wb.add_format({"num_format": "#,##0"})
                if "value" in df.columns:
                    ci = df.columns.get_loc("value")
                    ws.set_column(ci, ci, 18, num_fmt)

        st.success(f"Done. {len(df)} rows.")
        st.dataframe(df.head(50), use_container_width=True)
        st.download_button(
            "Download Excel",
            data=out_buf.getvalue(),
            file_name=out_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
