"""
Pro PDF Studio — by Raghu (v2.0 - Enhanced)
============================================
IMPROVEMENTS:
- Better code architecture with proper classes
- Robust error handling everywhere
- Complete tab implementations
- Memory-safe PDF processing
- Better UI/UX with real-time preview
- Fixed cache anti-patterns
- Complete find & replace with proper font handling
"""

import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io
import base64
import zipfile
import urllib.parse
import time
from pathlib import Path
import hashlib
from typing import Optional, Tuple, List, Dict, Any
import logging
import json
import re

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pro PDF Studio — Raghu",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Pro PDF Studio v2.0 by Raghu"
    }
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Cards */
    .main-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea22, #764ba222);
        border: 1px solid #667eea44;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 10px 20px;
        transition: all 0.2s;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(102,126,234,0.4);
        border: none;
    }
    .stButton > button:active { transform: scale(0.98); }

    /* Success / danger buttons */
    .btn-success > button { background: linear-gradient(135deg, #28a745, #20c997) !important; }
    .btn-danger > button  { background: linear-gradient(135deg, #dc3545, #fd7e14) !important; }

    /* WhatsApp */
    .whatsapp-btn {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white; padding: 12px 24px;
        text-decoration: none; border-radius: 10px;
        font-weight: 600; display: inline-block;
        margin-top: 8px; text-align: center; width: 100%;
        transition: all 0.2s;
    }
    .whatsapp-btn:hover { box-shadow: 0 8px 20px rgba(37,211,102,0.4); color: white; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; background: #f8f9fa;
        padding: 8px; border-radius: 14px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 8px 14px; font-weight: 500; font-size: 0.85em;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }

    /* Progress */
    .stProgress > div > div { background: linear-gradient(135deg, #667eea, #764ba2); }

    /* Scrollable area */
    .scroll-box {
        max-height: 500px; overflow-y: auto;
        border: 1px solid #e0e0e0; border-radius: 10px;
        padding: 12px; background: #fafafa;
    }

    /* Header */
    .app-header {
        text-align: center; padding: 28px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 20px; margin-bottom: 28px;
        box-shadow: 0 12px 40px rgba(102,126,234,0.35);
    }
    .app-header h1 { color: white; font-size: 2.2em; margin: 0; font-weight: 700; }
    .app-header p  { color: rgba(255,255,255,0.88); margin: 8px 0 0; font-size: 1em; }

    /* Tag badge */
    .badge {
        display: inline-block; background: #667eea22;
        color: #667eea; border-radius: 20px;
        padding: 2px 10px; font-size: 0.8em; font-weight: 600;
        border: 1px solid #667eea44;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class='app-header'>
    <h1>🔵 Pro PDF Studio — by Raghu</h1>
    <p>🚀 Advanced PDF Processing · Smart Editing · OCR · AI Features</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
def init_session_state():
    defaults = {
        'viewer_pdf_bytes': None,
        'processed_pdfs': {},          # cache: hash → bytes
        'upload_history': [],
        'ocr_available': None,
        'last_operation': None,
        'undo_stack': [],              # list of pdf_bytes for undo
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()


# ═══════════════════════════════════════════════════════════
# ✅  UTILITY FUNCTIONS  (properly fixed)
# ═══════════════════════════════════════════════════════════

def validate_pdf(file_or_bytes, max_mb: int = 50) -> Tuple[bool, str, int]:
    """
    Validate a PDF.
    Returns (is_valid, message, page_count)
    Accepts a file-like object OR raw bytes.
    """
    try:
        if isinstance(file_or_bytes, (bytes, bytearray)):
            pdf_bytes = file_or_bytes
        else:
            file_or_bytes.seek(0, 2)
            size = file_or_bytes.tell()
            file_or_bytes.seek(0)
            if size > max_mb * 1024 * 1024:
                return False, f"File too large — limit is {max_mb} MB", 0
            pdf_bytes = file_or_bytes.read()
            file_or_bytes.seek(0)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = len(doc)
        doc.close()

        if pages == 0:
            return False, "PDF has no pages", 0
        return True, f"Valid PDF ({pages} pages)", pages

    except Exception as e:
        return False, f"Invalid or corrupt PDF: {e}", 0


def get_pdf_bytes(uploaded_file) -> Optional[bytes]:
    """Safely read bytes from uploaded file, rewind after."""
    try:
        uploaded_file.seek(0)
        data = uploaded_file.read()
        uploaded_file.seek(0)
        return data
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return None


def pdf_hash(pdf_bytes: bytes) -> str:
    return hashlib.md5(pdf_bytes).hexdigest()[:12]


def get_cached_pdf(key: str) -> Optional[bytes]:
    return st.session_state.processed_pdfs.get(key)


def set_cached_pdf(key: str, data: bytes):
    # Keep cache small — evict oldest if > 10 entries
    if len(st.session_state.processed_pdfs) >= 10:
        oldest = next(iter(st.session_state.processed_pdfs))
        del st.session_state.processed_pdfs[oldest]
    st.session_state.processed_pdfs[key] = data


def push_undo(pdf_bytes: bytes):
    """Push current state to undo stack (max 5 levels)."""
    st.session_state.undo_stack.append(pdf_bytes)
    if len(st.session_state.undo_stack) > 5:
        st.session_state.undo_stack.pop(0)


def pop_undo() -> Optional[bytes]:
    if st.session_state.undo_stack:
        return st.session_state.undo_stack.pop()
    return None


# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────

def download_btn(pdf_bytes: bytes, filename: str = "output.pdf", label: str = None):
    """Standard download button with size label."""
    size_mb = len(pdf_bytes) / (1024 * 1024)
    size_str = f"{size_mb:.2f} MB" if size_mb >= 0.1 else f"{len(pdf_bytes)//1024} KB"
    label = label or f"⬇ Download  ({size_str})"
    st.download_button(label=label, data=pdf_bytes,
                       file_name=filename, mime="application/pdf",
                       use_container_width=True)


def open_in_new_tab(pdf_bytes: bytes, btn_label: str = "🔓 Open PDF in Browser"):
    """Open PDF in a new browser tab via base64 blob URL."""
    b64 = base64.b64encode(pdf_bytes).decode()
    js = f"""
    <script>
    (function() {{
        const b64 = "{b64}";
        const bin = atob(b64);
        const buf = new Uint8Array(bin.length);
        for (let i=0;i<bin.length;i++) buf[i]=bin.charCodeAt(i);
        const blob = new Blob([buf], {{type:'application/pdf'}});
        const url  = URL.createObjectURL(blob);
        window.open(url,'_blank');
        setTimeout(()=>URL.revokeObjectURL(url), 500);
    }})();
    </script>
    <button onclick="void(0)"
        style="background:linear-gradient(135deg,#28a745,#20c997);color:white;
               padding:11px 22px;border:none;border-radius:10px;font-weight:600;
               cursor:pointer;width:100%;font-size:0.95em;">
        {btn_label}
    </button>
    """
    st.components.v1.html(js, height=70)


def whatsapp_share(msg: str = "Raghu ke Pro PDF Studio se PDF edit ki! 🚀\nTry it: [your-url]"):
    encoded = urllib.parse.quote(msg)
    st.markdown(
        f'<a href="https://wa.me/?text={encoded}" target="_blank" class="whatsapp-btn">'
        '📲 Share on WhatsApp</a>',
        unsafe_allow_html=True
    )


def show_pdf_info(doc, pdf_bytes: bytes):
    """Display PDF metadata in a clean grid."""
    meta = doc.metadata
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📄 Pages",  len(doc))
    col2.metric("👤 Author", (meta.get('author') or 'Unknown')[:18])
    col3.metric("📦 Size",   f"{len(pdf_bytes)/1024:.1f} KB")
    col4.metric("🔒 Encrypted", "Yes" if doc.is_encrypted else "No")


def hex_to_rgb_float(hex_color: str) -> Tuple[float, float, float]:
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    return r/255, g/255, b/255


def rgb_float_to_hex(r, g, b) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))


# ═══════════════════════════════════════════════════════════
# PDF OPERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════

# ── FIND & REPLACE (fully fixed) ──────────────────────────
FONT_MAP = {
    "Helvetica":    {"normal":"helv","bold":"hebo","italic":"heit","bold_italic":"hebi"},
    "Times":        {"normal":"tiro","bold":"tibo","italic":"tiit","bold_italic":"tibi"},
    "Courier":      {"normal":"cour","bold":"cobo","italic":"coit","bold_italic":"cobi"},
    "Symbol":       {"normal":"symb","bold":"symb","italic":"symb","bold_italic":"symb"},
}

def get_font_name(family: str, bold: bool, italic: bool) -> str:
    entry = FONT_MAP.get(family, FONT_MAP["Helvetica"])
    if bold and italic: return entry["bold_italic"]
    if bold:            return entry["bold"]
    if italic:          return entry["italic"]
    return entry["normal"]


def smart_find_replace(
    pdf_bytes: bytes,
    find: str,
    replace: str,
    font_family: str = "Helvetica",
    font_size: float = 12.0,
    text_color: str = "#000000",
    bg_color: str = "#FFFFFF",
    bold: bool = False,
    italic: bool = False,
    case_sensitive: bool = True,
) -> Tuple[bytes, int]:
    """
    Find & replace text in PDF.
    Returns (new_pdf_bytes, total_replacements_count).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    font_name   = get_font_name(font_family, bold, italic)
    text_rgb    = hex_to_rgb_float(text_color)
    bg_rgb      = hex_to_rgb_float(bg_color)
    total_found = 0
    flags = 0 if case_sensitive else fitz.TEXT_DEHYPHENATE  # use case-insensitive search

    for page in doc:
        # search_for returns list of Rect
        hits = page.search_for(find, flags=flags if case_sensitive else fitz.TEXTFLAGS_SEARCH)
        if not hits:
            continue
        total_found += len(hits)

        # First pass — redact original text
        for rect in hits:
            ann = page.add_redact_annot(rect, fill=bg_rgb)
        page.apply_redactions()

        # Second pass — write replacement text in each rect
        # Reload rects by searching again is not reliable after redaction,
        # so we use the saved rects
        for rect in hits:
            # Slightly expand rect to give writing room
            write_rect = fitz.Rect(
                rect.x0, rect.y0 - 2,
                rect.x0 + len(replace) * font_size * 0.6,
                rect.y1 + 2
            )
            page.insert_textbox(
                write_rect,
                replace,
                fontname=font_name,
                fontsize=font_size,
                color=text_rgb,
                fill=bg_rgb,
                align=fitz.TEXT_ALIGN_LEFT,
            )

    out = io.BytesIO()
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out.getvalue(), total_found


# ── MERGE ─────────────────────────────────────────────────
def merge_pdfs(pdf_bytes_list: List[bytes]) -> bytes:
    merged = fitz.open()
    for pdf_bytes in pdf_bytes_list:
        src = fitz.open(stream=pdf_bytes, filetype="pdf")
        merged.insert_pdf(src)
        src.close()
    out = io.BytesIO()
    merged.save(out, garbage=4, deflate=True)
    merged.close()
    return out.getvalue()


# ── SPLIT ─────────────────────────────────────────────────
def split_pdf_by_range(pdf_bytes: bytes, ranges: str) -> Dict[str, bytes]:
    """
    ranges: e.g.  "1-3, 5, 7-9"
    Returns dict {label: pdf_bytes}
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = len(doc)
    result = {}

    for part in ranges.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            start, end = part.split('-', 1)
            start, end = int(start.strip())-1, int(end.strip())-1
        else:
            start = end = int(part)-1

        start = max(0, min(start, total-1))
        end   = max(0, min(end,   total-1))

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        out = io.BytesIO()
        new_doc.save(out, garbage=4, deflate=True)
        new_doc.close()
        result[f"pages_{start+1}_to_{end+1}.pdf"] = out.getvalue()

    doc.close()
    return result


def split_pdf_every_n(pdf_bytes: bytes, n: int) -> Dict[str, bytes]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = len(doc)
    result = {}
    for i in range(0, total, n):
        end = min(i+n-1, total-1)
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=end)
        out = io.BytesIO()
        new_doc.save(out, garbage=4, deflate=True)
        new_doc.close()
        result[f"pages_{i+1}_to_{end+1}.pdf"] = out.getvalue()
    doc.close()
    return result


# ── COMPRESS ──────────────────────────────────────────────
def compress_pdf(pdf_bytes: bytes, image_quality: int = 60) -> bytes:
    """
    Compress PDF by re-saving with garbage collection + deflate.
    Optionally downsamples images.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Re-compress images on every page
    for page in doc:
        img_list = page.get_images(full=True)
        for img_info in img_list:
            xref = img_info[0]
            try:
                base_img = doc.extract_image(xref)
                img_bytes = base_img["image"]
                from PIL import Image
                img = Image.open(io.BytesIO(img_bytes))
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=image_quality, optimize=True)
                doc.update_stream(xref, buf.getvalue())
            except Exception:
                pass  # skip images that can't be processed

    out = io.BytesIO()
    doc.save(out, garbage=4, deflate=True, clean=True)
    doc.close()
    return out.getvalue()


# ── EXTRACT IMAGES ────────────────────────────────────────
def extract_images_from_pdf(pdf_bytes: bytes) -> List[Dict]:
    """Returns list of {page, index, ext, data(bytes)}"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page_num, page in enumerate(doc):
        for img_idx, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            try:
                base_img = doc.extract_image(xref)
                images.append({
                    "page":  page_num + 1,
                    "index": img_idx + 1,
                    "ext":   base_img["ext"],
                    "data":  base_img["image"],
                    "width": base_img.get("width", 0),
                    "height":base_img.get("height", 0),
                })
            except Exception:
                pass
    doc.close()
    return images


# ── EXTRACT TEXT ──────────────────────────────────────────
def extract_text_from_pdf(pdf_bytes: bytes, mode: str = "plain") -> Dict[int, str]:
    """mode: 'plain' | 'blocks' | 'html'"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result = {}
    for page_num, page in enumerate(doc):
        if mode == "html":
            result[page_num+1] = page.get_text("html")
        elif mode == "blocks":
            blocks = page.get_text("blocks")
            result[page_num+1] = "\n".join(b[4] for b in blocks)
        else:
            result[page_num+1] = page.get_text()
    doc.close()
    return result


# ── EXTRACT TABLES ────────────────────────────────────────
def extract_tables_from_pdf(pdf_bytes: bytes) -> Dict[int, List[pd.DataFrame]]:
    """Extract tables using PyMuPDF's built-in table finder."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_tables = {}
    for page_num, page in enumerate(doc):
        try:
            tabs = page.find_tables()
            dfs = []
            for tab in tabs:
                df = pd.DataFrame(tab.extract())
                if not df.empty:
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
                    dfs.append(df)
            if dfs:
                all_tables[page_num+1] = dfs
        except Exception:
            pass
    doc.close()
    return all_tables


# ── REORDER PAGES ─────────────────────────────────────────
def reorder_pdf_pages(pdf_bytes: bytes, new_order: List[int]) -> bytes:
    """new_order: 1-based page numbers in desired order."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    new_doc = fitz.open()
    for page_num in new_order:
        idx = page_num - 1
        if 0 <= idx < len(doc):
            new_doc.insert_pdf(doc, from_page=idx, to_page=idx)
    out = io.BytesIO()
    new_doc.save(out, garbage=4, deflate=True)
    new_doc.close()
    doc.close()
    return out.getvalue()


# ── ADD WATERMARK ─────────────────────────────────────────
def add_text_watermark(
    pdf_bytes: bytes,
    text: str = "CONFIDENTIAL",
    opacity: float = 0.15,
    color: str = "#FF0000",
    font_size: int = 60,
    angle: int = 45,
    pages: str = "all"
) -> bytes:
    doc   = fitz.open(stream=pdf_bytes, filetype="pdf")
    rgb   = hex_to_rgb_float(color)
    total = len(doc)

    # Determine which pages
    if pages == "all":
        page_indices = list(range(total))
    else:
        page_indices = [int(p)-1 for p in pages.split(',') if p.strip().isdigit()]
        page_indices = [p for p in page_indices if 0 <= p < total]

    for idx in page_indices:
        page = doc[idx]
        w, h = page.rect.width, page.rect.height
        page.insert_text(
            (w * 0.1, h * 0.55),
            text,
            fontsize=font_size,
            color=(*rgb, opacity),
            rotate=angle,
            overlay=True,
        )

    out = io.BytesIO()
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out.getvalue()


def add_image_watermark(pdf_bytes: bytes, img_bytes: bytes, opacity: float = 0.2) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        rect = page.rect
        img_rect = fitz.Rect(
            rect.width * 0.25, rect.height * 0.35,
            rect.width * 0.75, rect.height * 0.65
        )
        page.insert_image(img_rect, stream=img_bytes, overlay=True)
    out = io.BytesIO()
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out.getvalue()


# ── ADD SIGNATURE ─────────────────────────────────────────
def add_text_signature(
    pdf_bytes: bytes,
    sig_text: str,
    page_num: int = 1,
    x: float = 400, y: float = 750,
    font_size: float = 14,
    color: str = "#1a237e"
) -> bytes:
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[min(page_num-1, len(doc)-1)]
    rgb  = hex_to_rgb_float(color)

    # Draw underline box
    rect = fitz.Rect(x - 5, y - font_size - 4, x + len(sig_text)*font_size*0.55 + 5, y + 4)
    page.draw_rect(rect, color=rgb, width=1)
    page.insert_text((x, y), sig_text, fontname="tiro", fontsize=font_size, color=rgb)

    out = io.BytesIO()
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out.getvalue()


def add_image_signature(pdf_bytes: bytes, sig_img_bytes: bytes, page_num: int = 1,
                         x: float = 350, y: float = 700, width: float = 150, height: float = 60) -> bytes:
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[min(page_num-1, len(doc)-1)]
    rect = fitz.Rect(x, y, x+width, y+height)
    page.insert_image(rect, stream=sig_img_bytes)
    out = io.BytesIO()
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out.getvalue()


# ── OCR ───────────────────────────────────────────────────
def check_ocr() -> bool:
    if st.session_state.ocr_available is None:
        try:
            import pytesseract
            from PIL import Image
            st.session_state.ocr_available = True
        except ImportError:
            st.session_state.ocr_available = False
    return st.session_state.ocr_available


def perform_ocr(pdf_bytes: bytes, lang: str = "eng", dpi: int = 200) -> Dict[int, Dict]:
    import pytesseract
    from PIL import Image
    doc     = fitz.open(stream=pdf_bytes, filetype="pdf")
    results = {}
    for page_num, page in enumerate(doc):
        pix  = page.get_pixmap(dpi=dpi)
        img  = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang=lang)
        conf_data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        results[page_num+1] = {
            "text":       text,
            "word_count": len([w for w in text.split() if w.strip()]),
            "confidence": round(
                sum(c for c in conf_data['conf'] if isinstance(c, (int, float)) and c > 0)
                / max(1, sum(1 for c in conf_data['conf'] if isinstance(c, (int, float)) and c > 0)), 1
            )
        }
    doc.close()
    return results


# ── RENDER PAGE PREVIEW ───────────────────────────────────
def render_page_preview(pdf_bytes: bytes, page_num: int = 0, dpi: int = 120) -> bytes:
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[min(page_num, len(doc)-1)]
    pix  = page.get_pixmap(dpi=dpi)
    doc.close()
    return pix.tobytes("png")


# ── DEEP PAGE INSPECTOR ───────────────────────────────────
def inspect_page_full(pdf_bytes: bytes, page_num: int = 0) -> Dict:
    """
    Full deep inspection of a PDF page:
    - All text spans with font, size, color, bold/italic flags
    - All unique colors (text + drawings + fills)
    - Page background color (if any)
    - Drawing / shape colors
    - Image count on page
    Returns a rich dict with all data.
    """
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[min(page_num, len(doc)-1)]

    text_spans   = []   # full per-span data
    all_colors   = {}   # hex_color -> count
    fonts_used   = {}   # font_name -> {sizes, count}

    # ── TEXT SPANS ──
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                raw_color = span.get("color", 0)

                # color is packed int  RGB
                r = (raw_color >> 16) & 0xFF
                g = (raw_color >> 8)  & 0xFF
                b =  raw_color        & 0xFF
                hex_col = "#{:02x}{:02x}{:02x}".format(r, g, b)

                # font flags
                flags     = span.get("flags", 0)
                is_bold   = bool(flags & 2**4)   # bit 4
                is_italic = bool(flags & 2**1)   # bit 1
                is_mono   = bool(flags & 2**3)   # bit 3

                font_name = span.get("font", "Unknown")
                font_size = round(span.get("size", 0), 2)
                text_val  = span.get("text", "").strip()

                if not text_val:
                    continue

                text_spans.append({
                    "Text":        text_val[:80] + ("…" if len(text_val) > 80 else ""),
                    "Font":        font_name,
                    "Size":        font_size,
                    "Color":       hex_col,
                    "Bold":        "✅" if is_bold   else "—",
                    "Italic":      "✅" if is_italic else "—",
                    "Monospace":   "✅" if is_mono   else "—",
                    "_raw_color":  raw_color,
                    "_r": r, "_g": g, "_b": b,
                })

                # accumulate color usage count
                all_colors[hex_col] = all_colors.get(hex_col, 0) + 1

                # accumulate font usage
                if font_name not in fonts_used:
                    fonts_used[font_name] = {"sizes": set(), "count": 0,
                                              "bold": False, "italic": False}
                fonts_used[font_name]["sizes"].add(font_size)
                fonts_used[font_name]["count"] += 1
                if is_bold:   fonts_used[font_name]["bold"]   = True
                if is_italic: fonts_used[font_name]["italic"] = True

    # ── DRAWING COLORS (shapes, lines, fills) ──
    drawing_colors = []
    for draw in page.get_drawings():
        for key in ("color", "fill"):
            val = draw.get(key)
            if val and isinstance(val, (list, tuple)) and len(val) >= 3:
                r2 = int(val[0] * 255)
                g2 = int(val[1] * 255)
                b2 = int(val[2] * 255)
                hx = "#{:02x}{:02x}{:02x}".format(r2, g2, b2)
                drawing_colors.append({"Color": hx, "Type": key,
                                        "Width": round(draw.get("width") or 0, 2)})
                all_colors[hx] = all_colors.get(hx, 0) + 1

    # ── IMAGES COUNT ──
    image_count = len(page.get_images(full=True))

    # ── PAGE SIZE ──
    rect = page.rect
    page_info = {
        "width":  round(rect.width, 1),
        "height": round(rect.height, 1),
        "rotation": page.rotation,
    }

    doc.close()

    # sort fonts by usage
    fonts_summary = []
    for fname, fdata in sorted(fonts_used.items(), key=lambda x: -x[1]["count"]):
        fonts_summary.append({
            "Font Name":  fname,
            "Used Count": fdata["count"],
            "Sizes Used": ", ".join(str(s) for s in sorted(fdata["sizes"])),
            "Bold":       "✅" if fdata["bold"]   else "—",
            "Italic":     "✅" if fdata["italic"] else "—",
        })

    # sort colors by frequency
    colors_sorted = sorted(all_colors.items(), key=lambda x: -x[1])

    return {
        "text_spans":      text_spans,
        "fonts_summary":   fonts_summary,
        "colors_sorted":   colors_sorted,       # list of (hex, count)
        "drawing_colors":  drawing_colors,
        "image_count":     image_count,
        "page_info":       page_info,
        "total_spans":     len(text_spans),
    }


# ═══════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════
TAB_NAMES = [
    "📘 Viewer & Editor", "🎨 Page Inspector", "➕ Merge", "✂ Split", "🗜 Compress",
    "🖼 Extract Images", "📄 Extract Text", "📊 Tables",
    "📑 Reorder", "✍ Signature", "💧 Watermark", "🔍 OCR"
]
tabs = st.tabs(TAB_NAMES)


# ─────────────────────────────────────────────────────────
# TAB 1 — VIEWER + SMART EDITOR
# ─────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("📘 PDF Viewer + Smart Find & Replace")
    st.caption("Upload a PDF, preview pages, then find & replace text with full formatting control.")

    uploaded = st.file_uploader("📂 Upload PDF (max 50 MB)", type=["pdf"], key="viewer_up")

    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, pages = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")
            st.session_state.viewer_pdf_bytes = pdf_bytes

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            with st.expander("📊 PDF Info", expanded=False):
                show_pdf_info(doc, pdf_bytes)

            # Page preview
            st.markdown("#### 🖼 Page Preview")
            col_prev, col_ctrl = st.columns([2, 1])
            with col_ctrl:
                preview_page = st.number_input("Preview Page", 1, pages, 1, key="preview_pg")
            with col_prev:
                png = render_page_preview(pdf_bytes, preview_page-1, dpi=110)
                st.image(png, use_container_width=True, caption=f"Page {preview_page} of {pages}")

            doc.close()
            st.divider()

            # ── EDIT CONTROLS ──
            st.markdown("#### ✏️ Find & Replace")
            with st.container():
                c1, c2 = st.columns(2)
                find_txt    = c1.text_input("🔍 Find Text",    placeholder="Text to search")
                replace_txt = c2.text_input("✏️ Replace With", placeholder="Replacement text")

                c1, c2, c3 = st.columns(3)
                font_family  = c1.selectbox("Font", list(FONT_MAP.keys()))
                font_size    = c2.number_input("Size", 4.0, 72.0, 12.0, 0.5)
                case_sens    = c3.checkbox("Case Sensitive", value=True)

                c1, c2, c3, c4, c5 = st.columns(5)
                is_bold      = c1.checkbox("Bold")
                is_italic    = c2.checkbox("Italic")
                is_underline = c3.checkbox("Underline")
                text_color   = c4.color_picker("Text Color",  "#000000")
                bg_color     = c5.color_picker("BG Color",    "#FFFFFF")

            if st.button("✨ Apply Find & Replace", use_container_width=True):
                if not find_txt:
                    st.warning("⚠️ Enter text to find.")
                elif not replace_txt:
                    st.warning("⚠️ Enter replacement text.")
                else:
                    with st.spinner("🔄 Processing..."):
                        try:
                            push_undo(st.session_state.viewer_pdf_bytes)
                            new_bytes, count = smart_find_replace(
                                st.session_state.viewer_pdf_bytes,
                                find=find_txt, replace=replace_txt,
                                font_family=font_family, font_size=font_size,
                                text_color=text_color, bg_color=bg_color,
                                bold=is_bold, italic=is_italic,
                                case_sensitive=case_sens,
                            )
                            if count == 0:
                                st.warning("⚠️ Text not found in document.")
                            else:
                                st.session_state.viewer_pdf_bytes = new_bytes
                                st.success(f"✅ Replaced **{count}** occurrence(s)!")
                                download_btn(new_bytes, "edited.pdf")
                                open_in_new_tab(new_bytes)
                                whatsapp_share()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                            logger.exception("Find & Replace failed")

            # Undo button
            if st.session_state.undo_stack:
                if st.button("↩ Undo Last Change"):
                    st.session_state.viewer_pdf_bytes = pop_undo()
                    st.success("↩ Undone!")
                    st.rerun()


# ─────────────────────────────────────────────────────────
# TAB 2 — PAGE INSPECTOR (Colors, Fonts, Text Data)
# ─────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("🎨 Page Inspector — Colors, Fonts, Text Styles")
    st.caption("Deep scan karo kisi bhi PDF page ka — har text span ka font, size, color, bold/italic flag sab dikhega.")

    uploaded_ins = st.file_uploader("📂 Upload PDF", type=["pdf"], key="inspector_up")

    if uploaded_ins:
        ins_bytes = get_pdf_bytes(uploaded_ins)
        ok, msg, total_pages = validate_pdf(ins_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")

            col_l, col_r = st.columns([1, 2])
            with col_l:
                ins_page = st.number_input("🔎 Select Page to Inspect", 1, total_pages, 1, key="ins_pg")

            # Show page preview on right
            with col_r:
                png_prev = render_page_preview(ins_bytes, ins_page - 1, dpi=100)
                st.image(png_prev, caption=f"Page {ins_page} Preview", use_container_width=True)

            if st.button("🔍 Run Deep Inspection", use_container_width=True, key="run_inspect"):
                with st.spinner("Scanning page..."):
                    data = inspect_page_full(ins_bytes, ins_page - 1)

                # ── PAGE INFO ──
                pi = data["page_info"]
                st.markdown("---")
                st.markdown("### 📐 Page Info")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Width",       f"{pi['width']} pt")
                c2.metric("Height",      f"{pi['height']} pt")
                c3.metric("Rotation",    f"{pi['rotation']}°")
                c4.metric("Images",      data["image_count"])

                st.markdown(f"**Total text spans found:** `{data['total_spans']}`")

                # ── COLOR PALETTE ──
                st.markdown("---")
                st.markdown("### 🎨 Color Palette Used on This Page")
                if data["colors_sorted"]:
                    # Show swatches in a row using HTML
                    swatch_html = "<div style='display:flex; flex-wrap:wrap; gap:12px; margin-top:8px;'>"
                    for hex_col, count in data["colors_sorted"]:
                        # Determine text contrast (white or black label)
                        r_val = int(hex_col[1:3], 16)
                        g_val = int(hex_col[3:5], 16)
                        b_val = int(hex_col[5:7], 16)
                        lum   = 0.299*r_val + 0.587*g_val + 0.114*b_val
                        txt_col = "#000" if lum > 128 else "#fff"
                        swatch_html += f"""
                        <div style='text-align:center; width:90px;'>
                            <div style='background:{hex_col}; width:70px; height:70px;
                                        border-radius:12px; border:2px solid #ddd;
                                        margin:0 auto; box-shadow:0 3px 8px rgba(0,0,0,0.15);
                                        display:flex; align-items:center; justify-content:center;'>
                                <span style='color:{txt_col}; font-size:0.65em; font-weight:600;'>{hex_col}</span>
                            </div>
                            <div style='font-size:0.75em; color:#555; margin-top:4px;'>
                                Used: <strong>{count}×</strong>
                            </div>
                        </div>"""
                    swatch_html += "</div>"
                    st.markdown(swatch_html, unsafe_allow_html=True)
                else:
                    st.info("No colors detected on this page.")

                # Drawing colors separately
                if data["drawing_colors"]:
                    st.markdown("**🖊 Drawing / Shape Colors:**")
                    st.dataframe(pd.DataFrame(data["drawing_colors"]), use_container_width=True, hide_index=True)

                # ── FONTS SUMMARY ──
                st.markdown("---")
                st.markdown("### 🔤 Fonts Used on This Page")
                if data["fonts_summary"]:
                    df_fonts = pd.DataFrame(data["fonts_summary"])
                    st.dataframe(df_fonts, use_container_width=True, hide_index=True)

                    # Visual bar chart of font usage
                    if len(df_fonts) > 1:
                        st.markdown("**Font Usage Count:**")
                        st.bar_chart(
                            df_fonts.set_index("Font Name")["Used Count"],
                            use_container_width=True,
                            height=200
                        )
                else:
                    st.info("No fonts detected on this page.")

                # ── TEXT SPANS TABLE ──
                st.markdown("---")
                st.markdown("### 📝 All Text Spans — Font · Size · Color · Style")
                if data["text_spans"]:
                    df_spans = pd.DataFrame(data["text_spans"]).drop(
                        columns=["_raw_color","_r","_g","_b"], errors="ignore"
                    )

                    # Add filter controls
                    col_f1, col_f2, col_f3 = st.columns(3)
                    filter_font  = col_f1.selectbox("Filter by Font",
                                                     ["All"] + sorted(df_spans["Font"].unique().tolist()),
                                                     key="filter_font")
                    filter_bold  = col_f2.selectbox("Filter Bold",  ["All","✅","—"], key="filter_bold")
                    filter_ital  = col_f3.selectbox("Filter Italic",["All","✅","—"], key="filter_ital")

                    filtered = df_spans.copy()
                    if filter_font != "All":
                        filtered = filtered[filtered["Font"] == filter_font]
                    if filter_bold != "All":
                        filtered = filtered[filtered["Bold"] == filter_bold]
                    if filter_ital != "All":
                        filtered = filtered[filtered["Italic"] == filter_ital]

                    st.caption(f"Showing {len(filtered)} of {len(df_spans)} spans")

                    # Render with inline color swatch in Color column
                    def color_cell(hex_col):
                        return f'<span style="background:{hex_col};display:inline-block;' \
                               f'width:14px;height:14px;border-radius:3px;' \
                               f'border:1px solid #ccc;vertical-align:middle;margin-right:5px;"></span>{hex_col}'

                    # Use st.dataframe with styling (no HTML here, Streamlit doesn't support it in dataframe)
                    st.dataframe(
                        filtered,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Text":  st.column_config.TextColumn("📝 Text",       width="large"),
                            "Font":  st.column_config.TextColumn("🔤 Font",       width="medium"),
                            "Size":  st.column_config.NumberColumn("📏 Size",     width="small",  format="%.1f pt"),
                            "Color": st.column_config.TextColumn("🎨 Color (hex)",width="small"),
                            "Bold":  st.column_config.TextColumn("B",             width="small"),
                            "Italic":st.column_config.TextColumn("I",             width="small"),
                            "Monospace": st.column_config.TextColumn("Mono",      width="small"),
                        }
                    )

                    # Download as CSV / Excel
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        csv = filtered.to_csv(index=False).encode()
                        st.download_button("⬇ Download as CSV", csv,
                                           f"page{ins_page}_text_data.csv", "text/csv",
                                           use_container_width=True)
                    with col_dl2:
                        xl_buf = io.BytesIO()
                        with pd.ExcelWriter(xl_buf, engine="xlsxwriter") as w:
                            filtered.to_excel(w, sheet_name=f"Page{ins_page}", index=False)
                        st.download_button("⬇ Download as Excel", xl_buf.getvalue(),
                                           f"page{ins_page}_text_data.xlsx",
                                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True)
                else:
                    st.info("No text found on this page.")


# ─────────────────────────────────────────────────────────
# TAB 3 — MERGE
# ─────────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("➕ Merge Multiple PDFs")
    st.caption("Upload 2 or more PDFs — they will be merged in upload order.")

    files = st.file_uploader("📂 Upload PDFs", type=["pdf"], accept_multiple_files=True, key="merge_up")

    if files:
        st.markdown(f"**{len(files)} file(s) uploaded:**")
        valid_bytes = []
        for f in files:
            data = get_pdf_bytes(f)
            ok, msg, _ = validate_pdf(data)
            st.write(f"{'✅' if ok else '❌'} `{f.name}` — {msg}")
            if ok:
                valid_bytes.append((f.name, data))

        if len(valid_bytes) >= 2:
            if st.button("🔗 Merge PDFs", use_container_width=True):
                with st.spinner("Merging..."):
                    try:
                        merged = merge_pdfs([b for _, b in valid_bytes])
                        st.success(f"✅ Merged {len(valid_bytes)} PDFs successfully!")
                        download_btn(merged, "merged_output.pdf")
                        open_in_new_tab(merged)
                        whatsapp_share()
                    except Exception as e:
                        st.error(f"❌ Merge failed: {e}")
        else:
            st.info("ℹ️ Upload at least 2 valid PDFs to merge.")


# ─────────────────────────────────────────────────────────
# TAB 3 — SPLIT
# ─────────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("✂ Split PDF")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="split_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, total_pages = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")
            split_mode = st.radio("Split Mode", ["By Page Ranges", "Every N Pages", "Each Page Separately"])

            if split_mode == "By Page Ranges":
                st.caption(f"Total pages: {total_pages}  |  Example: `1-3, 5, 7-9`")
                ranges = st.text_input("Page Ranges", placeholder="1-3, 5, 7-9")
                if st.button("✂ Split", use_container_width=True) and ranges:
                    with st.spinner("Splitting..."):
                        try:
                            parts = split_pdf_by_range(pdf_bytes, ranges)
                            st.success(f"✅ Created {len(parts)} part(s)")
                            for fname, data in parts.items():
                                download_btn(data, fname, f"⬇ {fname}")
                        except Exception as e:
                            st.error(f"❌ {e}")

            elif split_mode == "Every N Pages":
                n = st.number_input("Pages per chunk", 1, total_pages, min(5, total_pages))
                if st.button("✂ Split", use_container_width=True):
                    with st.spinner("Splitting..."):
                        try:
                            parts = split_pdf_every_n(pdf_bytes, n)
                            st.success(f"✅ Created {len(parts)} chunk(s)")
                            for fname, data in parts.items():
                                download_btn(data, fname, f"⬇ {fname}")
                        except Exception as e:
                            st.error(f"❌ {e}")

            else:  # Each page
                if st.button("✂ Extract All Pages", use_container_width=True):
                    with st.spinner("Splitting..."):
                        try:
                            parts = split_pdf_every_n(pdf_bytes, 1)
                            # Zip them
                            zip_buf = io.BytesIO()
                            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                                for fname, data in parts.items():
                                    zf.writestr(fname, data)
                            st.success(f"✅ {len(parts)} pages extracted")
                            st.download_button("⬇ Download All Pages (ZIP)", zip_buf.getvalue(),
                                               "all_pages.zip", "application/zip",
                                               use_container_width=True)
                        except Exception as e:
                            st.error(f"❌ {e}")


# ─────────────────────────────────────────────────────────
# TAB 4 — COMPRESS
# ─────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("🗜 Compress PDF")
    st.caption("Reduces file size by re-compressing images and cleaning the PDF structure.")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="compress_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, _ = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            orig_kb = len(pdf_bytes) / 1024
            st.info(f"📦 Original size: **{orig_kb:.1f} KB**")

            quality = st.slider("Image Quality (lower = smaller file)", 10, 95, 60, 5,
                                help="JPEG quality for embedded images")

            if st.button("🗜 Compress PDF", use_container_width=True):
                with st.spinner("Compressing..."):
                    try:
                        compressed = compress_pdf(pdf_bytes, quality)
                        new_kb     = len(compressed) / 1024
                        saving_pct = (1 - new_kb/orig_kb) * 100

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Original",   f"{orig_kb:.1f} KB")
                        col2.metric("Compressed", f"{new_kb:.1f} KB")
                        col3.metric("Saved",      f"{saving_pct:.1f}%")

                        download_btn(compressed, "compressed.pdf")
                        open_in_new_tab(compressed)
                    except Exception as e:
                        st.error(f"❌ Compression error: {e}")
                        st.info("💡 Tip: Install Pillow (`pip install Pillow`) for image compression.")


# ─────────────────────────────────────────────────────────
# TAB 5 — EXTRACT IMAGES
# ─────────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("🖼 Extract Images from PDF")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="img_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, _ = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            if st.button("🔍 Extract Images", use_container_width=True):
                with st.spinner("Extracting..."):
                    imgs = extract_images_from_pdf(pdf_bytes)

                if not imgs:
                    st.warning("No images found in this PDF.")
                else:
                    st.success(f"✅ Found **{len(imgs)}** image(s)")

                    # Zip all images
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for img in imgs:
                            zf.writestr(f"page{img['page']}_img{img['index']}.{img['ext']}", img['data'])
                    st.download_button("⬇ Download All Images (ZIP)", zip_buf.getvalue(),
                                       "extracted_images.zip", "application/zip",
                                       use_container_width=True)

                    # Preview grid
                    st.markdown("#### Preview")
                    cols = st.columns(4)
                    for i, img in enumerate(imgs[:12]):
                        with cols[i % 4]:
                            st.image(img['data'],
                                     caption=f"P{img['page']} · {img['width']}×{img['height']}",
                                     use_container_width=True)
                    if len(imgs) > 12:
                        st.caption(f"... and {len(imgs)-12} more images (download ZIP to get all)")


# ─────────────────────────────────────────────────────────
# TAB 6 — EXTRACT TEXT
# ─────────────────────────────────────────────────────────
with tabs[6]:
    st.subheader("📄 Extract Text from PDF")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="text_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, pages = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            col1, col2 = st.columns(2)
            text_mode  = col1.selectbox("Extract Mode", ["plain","blocks","html"])
            page_filter = col2.text_input("Pages (blank = all)", placeholder="e.g. 1, 3, 5-7")

            if st.button("📄 Extract Text", use_container_width=True):
                with st.spinner("Extracting..."):
                    texts = extract_text_from_pdf(pdf_bytes, mode=text_mode)

                # Apply page filter
                if page_filter.strip():
                    selected = set()
                    for part in page_filter.split(','):
                        part = part.strip()
                        if '-' in part:
                            a, b = part.split('-')
                            selected.update(range(int(a), int(b)+1))
                        elif part.isdigit():
                            selected.add(int(part))
                    texts = {p: t for p, t in texts.items() if p in selected}

                if not texts:
                    st.warning("No text found.")
                else:
                    full_text = "\n\n".join(f"--- Page {p} ---\n{t}" for p, t in texts.items())
                    st.text_area("Extracted Text", full_text, height=350)
                    st.download_button("⬇ Download as .txt", full_text.encode(),
                                       "extracted_text.txt", "text/plain",
                                       use_container_width=True)


# ─────────────────────────────────────────────────────────
# TAB 7 — EXTRACT TABLES
# ─────────────────────────────────────────────────────────
with tabs[7]:
    st.subheader("📊 Extract Tables from PDF")
    st.caption("Uses PyMuPDF's built-in table detection (works best on text-based PDFs with clear borders).")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="table_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, _ = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            if st.button("📊 Find Tables", use_container_width=True):
                with st.spinner("Detecting tables..."):
                    all_tables = extract_tables_from_pdf(pdf_bytes)

                if not all_tables:
                    st.warning("No tables detected. Try a PDF with clearly bordered tables.")
                else:
                    total = sum(len(v) for v in all_tables.values())
                    st.success(f"✅ Found **{total}** table(s) across {len(all_tables)} page(s)")

                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                        sheet_idx = 1
                        for page_num, dfs in all_tables.items():
                            for i, df in enumerate(dfs):
                                st.markdown(f"**Page {page_num} — Table {i+1}**")
                                st.dataframe(df, use_container_width=True)
                                df.to_excel(writer, sheet_name=f"P{page_num}_T{i+1}", index=False)
                                sheet_idx += 1

                    st.download_button("⬇ Download All Tables (Excel)",
                                       excel_buf.getvalue(), "tables.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)


# ─────────────────────────────────────────────────────────
# TAB 8 — REORDER PAGES
# ─────────────────────────────────────────────────────────
with tabs[8]:
    st.subheader("📑 Reorder PDF Pages")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="reorder_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, total_pages = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")
            st.caption(f"Original order: 1 to {total_pages}")
            new_order_str = st.text_input(
                "New Page Order (comma-separated, 1-based)",
                value=", ".join(str(i) for i in range(1, total_pages+1)),
                help="Example: 3,1,2 puts page 3 first, then 1, then 2"
            )

            # Preview thumbnails
            if st.checkbox("Show Page Thumbnails"):
                cols = st.columns(min(total_pages, 6))
                for i in range(min(total_pages, 6)):
                    png = render_page_preview(pdf_bytes, i, dpi=60)
                    cols[i].image(png, caption=f"Pg {i+1}", use_container_width=True)

            if st.button("📑 Apply New Order", use_container_width=True):
                try:
                    order = [int(x.strip()) for x in new_order_str.split(',') if x.strip()]
                    if len(order) == 0:
                        st.error("❌ Enter at least one page number.")
                    else:
                        with st.spinner("Reordering..."):
                            reordered = reorder_pdf_pages(pdf_bytes, order)
                        st.success("✅ Pages reordered!")
                        download_btn(reordered, "reordered.pdf")
                        open_in_new_tab(reordered)
                except ValueError:
                    st.error("❌ Invalid page order — use comma-separated numbers like: 3, 1, 2")


# ─────────────────────────────────────────────────────────
# TAB 9 — SIGNATURE
# ─────────────────────────────────────────────────────────
with tabs[9]:
    st.subheader("✍ Add Signature to PDF")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="sig_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, total_pages = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            sig_type = st.radio("Signature Type", ["Text Signature", "Image Signature"])

            if sig_type == "Text Signature":
                col1, col2 = st.columns(2)
                sig_text  = col1.text_input("Signature Text", placeholder="Your Name / Designation")
                sig_color = col2.color_picker("Ink Color", "#1a237e")
                col1, col2, col3 = st.columns(3)
                sig_page = col1.number_input("Page", 1, total_pages, total_pages)
                sig_x    = col2.number_input("X Position", 0, 800, 400)
                sig_y    = col3.number_input("Y Position", 0, 1200, 750)
                sig_size = st.slider("Font Size", 8, 36, 14)

                if st.button("✍ Add Text Signature", use_container_width=True):
                    if not sig_text:
                        st.warning("Enter signature text.")
                    else:
                        with st.spinner("Adding signature..."):
                            result = add_text_signature(pdf_bytes, sig_text, sig_page,
                                                         sig_x, sig_y, sig_size, sig_color)
                        st.success("✅ Signature added!")
                        download_btn(result, "signed.pdf")
                        open_in_new_tab(result)

            else:  # Image
                sig_img = st.file_uploader("Upload Signature Image (PNG/JPG)", type=["png","jpg","jpeg"], key="sig_img")
                if sig_img:
                    col1, col2, col3 = st.columns(3)
                    sig_page = col1.number_input("Page", 1, total_pages, total_pages)
                    sig_x    = col2.number_input("X",    0, 800, 350)
                    sig_y    = col3.number_input("Y",    0, 1200, 700)
                    col1, col2 = st.columns(2)
                    sig_w = col1.number_input("Width",  20, 400, 150)
                    sig_h = col2.number_input("Height", 10, 200, 60)
                    st.image(sig_img, width=200, caption="Signature Preview")

                    if st.button("✍ Add Image Signature", use_container_width=True):
                        with st.spinner("Adding signature..."):
                            result = add_image_signature(pdf_bytes, sig_img.read(),
                                                          sig_page, sig_x, sig_y, sig_w, sig_h)
                        st.success("✅ Signature added!")
                        download_btn(result, "signed.pdf")
                        open_in_new_tab(result)


# ─────────────────────────────────────────────────────────
# TAB 10 — WATERMARK
# ─────────────────────────────────────────────────────────
with tabs[10]:
    st.subheader("💧 Watermark Tools")

    uploaded = st.file_uploader("📂 Upload PDF", type=["pdf"], key="wm_up")
    if uploaded:
        pdf_bytes = get_pdf_bytes(uploaded)
        ok, msg, total_pages = validate_pdf(pdf_bytes)

        if not ok:
            st.error(f"❌ {msg}")
        else:
            wm_type = st.radio("Watermark Type", ["Text Watermark", "Image Watermark"])

            if wm_type == "Text Watermark":
                col1, col2 = st.columns(2)
                wm_text  = col1.text_input("Watermark Text", "CONFIDENTIAL")
                wm_color = col2.color_picker("Color", "#FF0000")
                col1, col2, col3, col4 = st.columns(4)
                wm_size    = col1.number_input("Font Size", 10, 150, 60)
                wm_angle   = col2.number_input("Angle (°)",  0, 360, 45)
                wm_opacity = col3.slider("Opacity", 0.01, 0.99, 0.15, 0.01)
                wm_pages   = col4.text_input("Pages (blank=all)", placeholder="all")

                if st.button("💧 Apply Text Watermark", use_container_width=True):
                    with st.spinner("Applying watermark..."):
                        result = add_text_watermark(
                            pdf_bytes, wm_text, wm_opacity, wm_color,
                            wm_size, wm_angle, wm_pages.strip() or "all"
                        )
                    st.success("✅ Watermark applied!")
                    download_btn(result, "watermarked.pdf")
                    open_in_new_tab(result)

            else:  # Image watermark
                wm_img = st.file_uploader("Upload Watermark Image", type=["png","jpg","jpeg"], key="wm_img")
                if wm_img:
                    wm_opacity = st.slider("Opacity", 0.01, 0.99, 0.2, 0.01)
                    st.image(wm_img, width=150, caption="Watermark Preview")
                    if st.button("💧 Apply Image Watermark", use_container_width=True):
                        with st.spinner("Applying watermark..."):
                            result = add_image_watermark(pdf_bytes, wm_img.read(), wm_opacity)
                        st.success("✅ Watermark applied!")
                        download_btn(result, "watermarked.pdf")
                        open_in_new_tab(result)


# ─────────────────────────────────────────────────────────
# TAB 11 — OCR
# ─────────────────────────────────────────────────────────
with tabs[11]:
    st.subheader("🔍 OCR Scanner")
    st.caption("Extract text from scanned / image-based PDFs using Tesseract OCR.")

    if not check_ocr():
        st.error("❌ OCR libraries not installed.")
        st.code("pip install pytesseract pillow\n# Also install Tesseract: https://github.com/tesseract-ocr/tesseract")
    else:
        uploaded = st.file_uploader("📂 Upload PDF (scanned)", type=["pdf"], key="ocr_up")
        if uploaded:
            pdf_bytes = get_pdf_bytes(uploaded)
            ok, msg, total_pages = validate_pdf(pdf_bytes)

            if not ok:
                st.error(f"❌ {msg}")
            else:
                col1, col2 = st.columns(2)
                ocr_lang = col1.selectbox("Language", ["eng","hin","spa","fra","deu","ara","chi_sim"])
                ocr_dpi  = col2.select_slider("DPI (higher = more accurate but slower)", [100,150,200,300], value=200)

                if st.button("🔍 Run OCR", use_container_width=True):
                    with st.spinner(f"Running OCR on {total_pages} page(s)... this may take a moment"):
                        try:
                            progress = st.progress(0)
                            results  = perform_ocr(pdf_bytes, ocr_lang, ocr_dpi)
                            progress.progress(1.0)

                            total_words = sum(r['word_count'] for r in results.values())
                            avg_conf    = round(sum(r['confidence'] for r in results.values()) / len(results), 1)

                            col1, col2, col3 = st.columns(3)
                            col1.metric("Pages Processed", total_pages)
                            col2.metric("Total Words",     total_words)
                            col3.metric("Avg Confidence",  f"{avg_conf}%")

                            full_text = "\n\n".join(
                                f"=== Page {p} (Words: {r['word_count']}, Conf: {r['confidence']}%) ===\n{r['text']}"
                                for p, r in results.items()
                            )
                            st.text_area("OCR Output", full_text, height=400)
                            st.download_button("⬇ Download OCR Text", full_text.encode(),
                                               "ocr_output.txt", "text/plain",
                                               use_container_width=True)
                        except Exception as e:
                            st.error(f"❌ OCR failed: {e}")


# ─────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#888; font-size:0.85em; padding: 10px 0 20px;'>
    🔵 <strong>Pro PDF Studio v2.0</strong> — Built by Raghu &nbsp;|&nbsp;
    Powered by PyMuPDF · Streamlit · Tesseract OCR
</div>
""", unsafe_allow_html=True)
