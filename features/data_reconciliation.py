"""Data Reconciliation feature module."""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
from datetime import datetime
from io import BytesIO
from typing import Sequence, Tuple

import streamlit as st


DependencySpec = Sequence[Tuple[str, str]]


def ensure_runtime_dependencies(dependency_spec: DependencySpec) -> set[str]:
    """Attempt to import dependencies, installing them on-demand if missing."""

    missing: list[Tuple[str, str]] = []
    for pip_name, import_name in dependency_spec:
        try:
            __import__(import_name)
        except Exception:
            missing.append((pip_name, import_name))

    if not missing:
        return set()

    with st.spinner("Installing missing dependencies…"):
        still_missing: set[str] = set()
        for pip_name, import_name in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                __import__(import_name)
            except Exception:
                still_missing.add(pip_name)
        return still_missing


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
    for k in list(out.keys()):
        nk = k.strip().lower().replace(" ", "_")
        if nk != k and nk not in out:
            out[nk] = out.pop(k)
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


def encode_image_bytes_to_data_url(b: bytes, mime_hint: str) -> str:
    b64 = base64.b64encode(b).decode("utf-8")
    return f"data:{mime_hint};base64,{b64}"


PROMPT = """
You are an information-extraction system for Demat/CSGL statements.
Return JSON records for each table row with these optional fields:
date, isin, security_name, balance, market_rate, market_value, value, status.
Do not invent values; omit fields if unknown. Output must be valid JSON (no markdown fences).
"""

EXAMPLES: list = []


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
    prefs = [model_choice]
    if ":" not in model_choice:
        prefs.append(f"openai:{model_choice}")
    prefs += [
        "openai:gpt-5-nano",
        "gpt-5-nano",
        "openai:gpt-5-mini",
        "gpt-5-mini",
        "openai:gpt-4.1-mini",
        "gpt-4.1-mini",
    ]
    for mid in prefs:
        res, err = _attempt_extract(mid, text, use_json_object=True, openai_key=openai_key)
        if res is None:
            res, err = _attempt_extract(mid, text, use_json_object=False, openai_key=openai_key)
        if res is not None:
            try:
                payload = json.loads(json.dumps(res))
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


def decrypt_pdf_if_needed(pdf_bytes: bytes, pw: str | None):
    from pypdf import PdfReader, PdfWriter

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception:
        return pdf_bytes, None
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
        bmp = page.render(scale=scale)
        imgs.append(bmp.to_pil())
        page.close()
    pdf.close()
    return imgs


def render(show_error, show_warning, show_info):
    st.markdown(
        """
    <style>
      .rail{ margin-bottom: 2px !important; }
      .formWrap{ width:min(70vw,980px); margin: 0 auto 72px auto !important; }
      [data-testid="stForm"]{ width: min(70vw, 980px) !important; margin-left: auto !important; margin-right: auto !important; }
      div[data-testid="stFileUploadDropzone"], div[data-testid="stTextInput"], div[data-testid="stCheckbox"], div[data-testid="stSelectbox"], div[data-testid="stExpander"]{ max-width: 100% !important; }
      [data-testid="stTextInput"] button[aria-label="Show password"], [data-testid="stTextInput"] button[aria-label="Hide password"]{ margin-right: 0 !important; }
      [data-baseweb="input"]{ padding-right: 6px !important; }
    </style>
    """,
        unsafe_allow_html=True,
    )

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
                    help="Used for OCR (mistral-ocr-latest).",
                )
            with c2:
                openai_key = st.text_input(
                    "OPENAI_API_KEY",
                    value=st.session_state.get("OPENAI_API_KEY", ""),
                    type="password",
                    help="Used by LangExtract for record extraction.",
                )
            remember = st.checkbox("Remember in this browser session", value=True)

        model = st.selectbox(
            "Extraction model (LangExtract)",
            ["gpt-5-nano-2025-08-07", "openai:gpt-5-nano", "openai:gpt-5-mini", "openai:gpt-4.1-mini"],
            index=0,
        )

        run = st.form_submit_button("Run Reconciliation")

    if not run:
        return

    if remember:
        st.session_state["MISTRAL_API_KEY"] = mistral_key
        st.session_state["OPENAI_API_KEY"] = openai_key

    missing = ensure_runtime_dependencies(
        (
            ("pandas", "pandas"),
            ("python-dateutil", "dateutil"),
            ("mistralai", "mistralai"),
            ("langextract[openai]", "langextract"),
            ("pypdfium2", "pypdfium2"),
            ("pypdf", "pypdf"),
            ("pillow", "PIL"),
        )
    )

    if missing:
        show_error(
            "Unable to install required packages automatically. "
            + "Please install before running: "
            + ", ".join(sorted(missing))
        )
        st.stop()

    if not files:
        show_warning("Please upload at least one file.")
        st.stop()

    if not mistral_key or not openai_key:
        show_warning("Please enter MISTRAL_API_KEY and OPENAI_API_KEY in the form above.")
        st.stop()

    import pandas as pd
    from mistralai import Mistral

    mistral_client = Mistral(api_key=mistral_key)

    def run_mistral_ocr_on_image_bytes(b: bytes, mime_hint: str = "image/jpeg") -> str:
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
            show_error(f"OCR failed: {e}")
            return ""

    RUN_TAG = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_rows = []

    with st.status("Processing…", expanded=False) as status:
        for f in files:
            name = (f.name or "").lower()
            b = f.read()

            if name.endswith(".pdf"):
                dec, stt = decrypt_pdf_if_needed(b, pdf_password)
                if stt == "bad_password":
                    show_error(f"Incorrect password for {f.name}.")
                    continue
                if stt == "protected":
                    show_warning(f"{f.name} is password-protected; please provide the password.")
                    continue
                pdf_bytes = dec if dec is not None else b

                try:
                    pages = render_pdf_to_images(pdf_bytes, scale=2.0)
                except Exception as e:
                    show_error(f"PDF render failed for {f.name}: {e}")
                    continue

                for i, pg in enumerate(pages, start=1):
                    buf = BytesIO()
                    pg.save(buf, format="PNG")
                    md_text = run_mistral_ocr_on_image_bytes(buf.getvalue(), "image/png")
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
                md_text = run_mistral_ocr_on_image_bytes(b, mime)
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
                show_info(f"Skipping {f.name} (unsupported).")

        status.update(label="Building Excel…", state="running")

    if not all_rows:
        show_warning("No rows extracted. Try a different page or a crisper scan.")
        st.stop()

    def tidy_name(x):
        return tidy_security_name(x or "")

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

    import pandas as pd  # ensure available for Excel stage

    df = pd.DataFrame(all_rows).reindex(columns=ordered_cols)

    out_name = f"extracted_transactions_{RUN_TAG}.xlsx"
    try:
        import xlsxwriter  # noqa: F401
        engine = "xlsxwriter"
    except Exception:
        engine = None

    out_buf = BytesIO()
    with pd.ExcelWriter(out_buf, engine=engine) as writer:
        df.to_excel(writer, index=False, sheet_name="Extract")
        if engine == "xlsxwriter":
            wb = writer.book
            ws = writer.sheets["Extract"]
            ws.freeze_panes(1, 0)
            width_map = {
                "date": 12,
                "isin": 20,
                "security_name": 40,
                "value": 18,
                "_span": 60,
                "sr_no": 8,
            }
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

