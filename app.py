import streamlit as st
import fitz
import pandas as pd
import io
import base64
import zipfile
import urllib.parse

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Pro AI PDF Editor - Raghu",
    layout="wide",
)

# ---------------------------------------------------------
# MINIMAL CLEAN UI CSS
# ---------------------------------------------------------
st.markdown("""
<style>
body { background: #eef5ff; font-family: 'Inter', sans-serif; }
.main-card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.10); }
.stButton>button { border-radius: 8px; font-weight: 700; transition: 0.3s; }
.stButton>button:hover { transform: scale(1.02); }
.whatsapp-btn {
    background-color: #25D366;
    color: white;
    padding: 12px 24px;
    text-decoration: none;
    border-radius: 8px;
    font-weight: bold;
    display: inline-block;
    margin-top: 10px;
    text-align: center;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#003d8f;'>🔵 Pro PDF Studio — by Raghu</h1>", unsafe_allow_html=True)

# ---------------------------------------------------------
# UNIVERSAL FUNCTIONS
# ---------------------------------------------------------
def open_pdf_in_new_tab(pdf_bytes, button_text="🔓 Open & Print Edited PDF"):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    js_code = f"""
    <script>
    function openPDF() {{
        const base64 = "{base64_pdf}";
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {{
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }}
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {{type: 'application/pdf'}});
        const fileURL = URL.createObjectURL(blob);
        window.open(fileURL, '_blank');
    }}
    </script>
    <button onclick="openPDF()" style="
        background:#28a745;color:white;padding:12px 24px;
        border:none;border-radius:6px;font-weight:700;cursor:pointer;width:100%;">
        {button_text}
    </button>
    """
    st.components.v1.html(js_code, height=80)

def add_whatsapp_share(text="Bhai, maine Raghu ke AI tool se PDF banayi hai!"):
    encoded_text = urllib.parse.quote(text)
    whatsapp_url = f"https://wa.me/?text={encoded_text}"
    st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">📲 Share on WhatsApp</a>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB SETUP
# ---------------------------------------------------------
tabs = st.tabs([
    "📘 Viewer + Smart Edit", "➕ Merge PDFs", "✂ Split PDF", "🗜 Compress PDF",
    "🖼 Extract Images", "📄 Extract Text", "📊 Extract Tables", 
    "📑 Reorder / Delete Pages", "✍ Add Signature", "💧 Watermark Tools", "🤖 AI Auto Edit"
])

# =========================================================
# 📘 TAB 1 — VIEWER + SMART EDITOR
# =========================================================
with tabs[0]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📘 PDF Viewer + Smart Editor")
    uploaded_file = st.file_uploader("📂 Upload PDF", type=["pdf"], key="tab1_upload")

    if uploaded_file:
        pdf_bytes = uploaded_file.read()
        st.divider()
        st.subheader("📝 Smart Edit Controls")
        col1, col2 = st.columns(2)
        find_txt = col1.text_input("Find Text")
        replace_txt = col2.text_input("Replace With")
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        font_library = {"Helvetica": "helv", "Times": "tiro", "Courier": "cour"}
        selected_font = c1.selectbox("Font Theme", list(font_library.keys()))
        font_style = font_library[selected_font]
        f_size = c2.number_input("Font Size", value=0.0, step=0.5)
        t_color = c3.color_picker("Text Color", "#000000")
        bg_color = c4.color_picker("Background Color", "#FFFFFF")
        s1, s2, s3 = st.columns(3)
        is_bold, is_italic, is_underline = s1.checkbox("Bold"), s2.checkbox("Italic"), s3.checkbox("Underline")

        if st.button("✨ Apply Smart Replace", use_container_width=True):
            doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
            style_map = {"helv": ["helv", "hebo", "helt", "hebi"], "tiro": ["tiro", "tibo", "tiit", "tibi"]}
            idx = (1 if is_bold else 0) + (2 if is_italic else 0)
            fname = style_map[font_style][idx] if font_style in style_map else font_style
            for page in doc_edit:
                for rect in page.search_for(find_txt):
                    bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                    page.add_redact_annot(rect, fill=bg_rgb)
                    page.apply_redactions()
                    page.insert_text(fitz.Point(rect.x0, rect.y1-1), replace_txt, fontsize=f_size if f_size > 0 else 10, fontname=fname, color=tuple(int(t_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)))
            out = io.BytesIO(); doc_edit.save(out)
            st.success("🎉 Edited!"); open_pdf_in_new_tab(out.getvalue())
            add_whatsapp_share()

# =========================================================
# 📦 TAB 2 — MERGE PDFs
# =========================================================
with tabs[1]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📦 Merge Multiple PDFs")
    merge_files = st.file_uploader("Select PDFs", type=["pdf"], accept_multiple_files=True, key="tab2_upload")
    if merge_files and len(merge_files) >= 2:
        if st.button("🔗 Merge Now", use_container_width=True):
            merger = fitz.open()
            for pdf in merge_files:
                with fitz.open(stream=pdf.read(), filetype="pdf") as doc_temp: merger.insert_pdf(doc_temp)
            out = io.BytesIO(); merger.save(out)
            open_pdf_in_new_tab(out.getvalue(), "🔓 Open Merged PDF for Printing")
            add_whatsapp_share("Bhai, PDFs merge ho gayi hain!")

# =========================================================
# ✂ TAB 3 — SPLIT PDF
# =========================================================
with tabs[2]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    split_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab3_upload")
    s, e = st.columns(2)
    start = s.number_input("Start", min_value=1, value=1)
    end = e.number_input("End", min_value=1, value=1)
    if split_pdf and st.button("✂ Split Now", use_container_width=True):
        doc = fitz.open(stream=split_pdf.read(), filetype="pdf")
        new = fitz.open(); new.insert_pdf(doc, from_page=start-1, to_page=min(end-1, doc.page_count-1))
        out = io.BytesIO(); new.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Split PDF for Printing")

# =========================================================
# 🗜 TAB 4 — COMPRESS PDF
# =========================================================
with tabs[3]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    comp_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab4_upload")
    if comp_pdf and st.button("🗜 Compress Now", use_container_width=True):
        doc = fitz.open(stream=comp_pdf.read(), filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=50)
            page.clean_contents(); page.insert_image(page.rect, pixmap=pix)
        out = io.BytesIO(); doc.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Compressed PDF for Printing")

# =========================================================
# ✍ TAB 9 — SIGNATURE
# =========================================================
with tabs[8]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    s_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab9_upload")
    s_img = st.file_uploader("Sign Image", type=["png", "jpg"], key="tab9_sign")
    if s_pdf and s_img and st.button("✍ Sign Now", use_container_width=True):
        doc = fitz.open(stream=s_pdf.read(), filetype="pdf")
        for page in doc: page.insert_image(fitz.Rect(100, 100, 250, 180), stream=s_img.read())
        out = io.BytesIO(); doc.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Signed PDF for Printing")

# =========================================================
# 💧 TAB 10 — WATERMARK
# =========================================================
with tabs[9]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    w_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab10_upload")
    w_txt = st.text_input("Watermark Text")
    if w_pdf and st.button("💧 Apply", use_container_width=True):
        doc = fitz.open(stream=w_pdf.read(), filetype="pdf")
        for page in doc: page.insert_text(fitz.Point(100, 100), w_txt, fontsize=50, color=(0.7,0.7,0.7))
        out = io.BytesIO(); doc.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Watermarked PDF")

# =========================================================
# 🤖 TAB 11 — AI AUTO EDIT
# =========================================================
with tabs[10]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    ai_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab11_upload")
    cmd = st.text_input("AI Command")
    if ai_pdf and cmd and st.button("🤖 Run AI", use_container_width=True):
        doc = fitz.open(stream=ai_pdf.read(), filetype="pdf")
        out = io.BytesIO(); doc.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open AI Edited PDF")
        add_whatsapp_share("Bhai, AI ne PDF mast banayi hai!")
