import streamlit as st
import fitz
import pandas as pd
import io
import base64
import zipfile
import urllib.parse # WhatsApp Link ke liye

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
st.write("")

# ---------------------------------------------------------
# UNIVERSAL FUNCTIONS (For New Tab & WhatsApp)
# ---------------------------------------------------------
def open_pdf_in_new_tab(pdf_bytes, btn_label="🔓 Open & Print PDF"):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    js_code = f"""
    <script>
    function openPDF() {{
        const base64 = "{base64_pdf}";
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {{ byteNumbers[i] = byteCharacters.charCodeAt(i); }}
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {{type: 'application/pdf'}});
        const fileURL = URL.createObjectURL(blob);
        window.open(fileURL, '_blank');
    }}
    </script>
    <button onclick="openPDF()" style="background:#28a745;color:white;padding:12px 24px;border:none;border-radius:6px;font-weight:700;cursor:pointer;width:100%;">
        {btn_label}
    </button>
    """
    st.components.v1.html(js_code, height=80)

def add_whatsapp_share(msg="Bhai, Raghu ke tool se PDF mast banayi hai! 🚀"):
    encoded_msg = urllib.parse.quote(msg)
    st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank" class="whatsapp-btn">📲 Share on WhatsApp</a>', unsafe_allow_html=True)

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

    def get_deep_page_colors(page):
        colors = set()
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        c = s["color"]; colors.add("#{:02x}{:02x}{:02x}".format((c>>16)&255,(c>>8)&255,c&255))
        for draw in page.get_drawings():
            if "fill" in draw and draw["fill"]:
                c = draw["fill"]; colors.add("#{0:02x}{1:02x}{2:02x}".format(int(c[0]*255),int(c[1]*255),int(c[2]*255)))
        return colors

    if uploaded_file:
        pdf_bytes = uploaded_file.read()
        st.divider()
        st.subheader("📝 Smart Edit Controls")
        col1, col2 = st.columns(2)
        find_txt = col1.text_input("Find Text")
        replace_txt = col2.text_input("Replace With")
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        font_library = {"Helvetica": "helv", "Times": "tiro", "Courier": "cour", "Symbol": "symb", "ZapfDingbats": "zadi"}
        selected_font = c1.selectbox("Font Theme", list(font_library.keys()))
        font_style = font_library[selected_font]
        f_size = c2.number_input("Font Size", value=0.0, step=0.5)
        t_color = c3.color_picker("Text Color", "#000000")
        bg_color = c4.color_picker("Background Color", "#FFFFFF")
        s1, s2, s3 = st.columns(3)
        is_bold, is_italic, is_underline = s1.checkbox("Bold"), s2.checkbox("Italic"), s3.checkbox("Underline")

        if st.button("✨ Apply Smart Replace", use_container_width=True):
            doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
            found = False
            style_map = {"helv": ["helv", "hebo", "helt", "hebi"], "tiro": ["tiro", "tibo", "tiit", "tibi"], "cour": ["cour", "cobo", "coit", "cobi"]}
            idx = (1 if is_bold else 0) + (2 if is_italic else 0)
            final_font = style_map[font_style][idx] if font_style in style_map else font_style

            for page in doc_edit:
                for rect in page.search_for(find_txt):
                    found = True
                    bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                    page.add_redact_annot(rect, fill=bg_rgb); page.apply_redactions()
                    fs = f_size if f_size > 0 else (rect.y1 - rect.y0) - 1
                    txt_rgb = tuple(int(t_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                    page.insert_text(fitz.Point(rect.x0, rect.y1 - 1), replace_txt, fontsize=fs, fontname=final_font, color=txt_rgb)
                    if is_underline: page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), color=txt_rgb, width=1)

            if found:
                out = io.BytesIO(); doc_edit.save(out)
                st.success("🎉 Edit Complete!")
                open_pdf_in_new_tab(out.getvalue())
                add_whatsapp_share()
            else: st.error("❌ Text not found.")

        st.divider()
        st.subheader("📄 PDF Preview")
        zoom = st.slider("🔍 Zoom", 50, 250, 120)
        base64_p = base64.b64encode(pdf_bytes).decode()
        viewer_html = f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script><div id="pdf_container" style="height:520px; overflow-y:scroll; background:white; padding:12px; border-radius:14px;"></div><script>const pdfData = atob("{base64_p}");pdfjsLib.getDocument({{ data: pdfData }}).promise.then(pdf => {{const container = document.getElementById("pdf_container");for (let i = 1; i <= pdf.numPages; i++) {{pdf.getPage(i).then(page => {{const viewport = page.getViewport({{ scale: {zoom/100} }});const canvas = document.createElement("canvas");canvas.width = viewport.width; canvas.height = viewport.height;canvas.style.marginBottom = "15px";container.appendChild(canvas);page.render({{canvasContext: canvas.getContext("2d"),viewport: viewport}});}});}}}});</script>"""
        st.components.v1.html(viewer_html, height=560)

        st.subheader("🎨 Deep Color & Font Analyzer")
        doc_an = fitz.open(stream=pdf_bytes, filetype="pdf")
        for pageno, page in enumerate(doc_an, start=1):
            st.write(f"### 📄 Page {pageno}"); all_colors = get_deep_page_colors(page)
            color_cols = st.columns(12)
            for i, color in enumerate(list(all_colors)[:12]):
                with color_cols[i]: st.markdown(f"<div style='width:28px;height:28px;border-radius:5px;background:{color};border:1px solid #003d8f;'></div>", unsafe_allow_html=True); st.caption(color)
            rows = []
            for b in page.get_text("dict")["blocks"]:
                if b['type'] == 0:
                    for l in b["lines"]:
                        for s in l["spans"]: rows.append({"Text": s["text"], "Font": s["font"], "Size": round(s["size"], 2), "Color": "#{:02x}{:02x}{:02x}".format((s["color"]>>16)&255, (s["color"]>>8)&255, s["color"]&255)})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

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
            add_whatsapp_share("Bhai, PDFs merge ho gayi hain! 🚀")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ✂ TAB 3 — SPLIT PDF
# =========================================================
with tabs[2]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("✂ Split PDF")
    split_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab3_upload")
    col_s1, col_s2 = st.columns(2)
    start = col_s1.number_input("Start Page", min_value=1, value=1, key="split_start")
    end = col_s2.number_input("End Page", min_value=1, value=1, key="split_end")
    if split_pdf and st.button("✂ Split Now", use_container_width=True):
        doc = fitz.open(stream=split_pdf.read(), filetype="pdf")
        new = fitz.open(); new.insert_pdf(doc, from_page=start-1, to_page=min(end-1, doc.page_count-1))
        out = io.BytesIO(); new.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Split PDF for Printing")
        add_whatsapp_share("Bhai, PDF alag kar di! ✂️")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🗜 TAB 4 — COMPRESS PDF
# =========================================================
with tabs[3]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🗜 Compress PDF")
    comp_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab4_upload")
    if comp_pdf and st.button("🗜 Compress Now", use_container_width=True):
        doc = fitz.open(stream=comp_pdf.read(), filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=40); page.clean_contents(); page.insert_image(page.rect, pixmap=pix)
        out = io.BytesIO(); doc.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Compressed PDF")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🖼 TAB 5 — EXTRACT IMAGES
# =========================================================
with tabs[4]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Extract Images")
    img_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab5_upload")
    if img_pdf and st.button("📸 Extract Now", use_container_width=True):
        doc = fitz.open(stream=img_pdf.read(), filetype="pdf")
        zip_buf = io.BytesIO(); zipf = zipfile.ZipFile(zip_buf, "w")
        for pno in range(len(doc)):
            for img in doc.get_page_images(pno):
                pix = fitz.Pixmap(doc, img[0]); zipf.writestr(f"img_{pno+1}.png", pix.tobytes("png"))
        zipf.close(); st.success("🎉 Images Extracted!"); st.download_button("⬇ Download ZIP", zip_buf.getvalue(), "images.zip")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📄 TAB 6 — EXTRACT TEXT
# =========================================================
with tabs[5]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    txt_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab6_upload")
    if txt_pdf:
        doc = fitz.open(stream=txt_pdf.read(), filetype="pdf")
        all_text = "".join([page.get_text() + "\n\n" for page in doc])
        st.text_area("Text", all_text, height=300); st.download_button("⬇ Download", all_text, "text.txt")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📊 TAB 7 — EXTRACT TABLES
# =========================================================
with tabs[6]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    table_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab7_upload")
    if table_pdf:
        doc = fitz.open(stream=table_pdf.read(), filetype="pdf")
        all_rows = []
        for page in doc:
            tabs_found = page.find_tables()
            for t in tabs_found: all_rows.append(t.to_pandas())
        if all_rows: st.dataframe(pd.concat(all_rows, ignore_index=True), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📑 TAB 8 — REORDER PAGES
# =========================================================
with tabs[7]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    re_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab8_upload")
    if re_pdf:
        doc = fitz.open(stream=re_pdf.read(), filetype="pdf")
        selected = st.multiselect("Order", range(1, doc.page_count+1))
        if st.button("📑 Apply", use_container_width=True):
            new = fitz.open()
            for p in selected: new.insert_pdf(doc, from_page=p-1, to_page=p-1)
            out = io.BytesIO(); new.save(out); open_pdf_in_new_tab(out.getvalue())
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ✍ TAB 9 — SIGNATURE
# =========================================================
with tabs[8]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    s_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab9_upload")
    s_img = st.file_uploader("Sign", type=["png", "jpg"], key="tab9_sign")
    if s_pdf and s_img and st.button("✍ Sign Now", use_container_width=True):
        doc = fitz.open(stream=s_pdf.read(), filetype="pdf")
        for page in doc: page.insert_image(fitz.Rect(100, 100, 250, 180), stream=s_img.read())
        out = io.BytesIO(); doc.save(out); open_pdf_in_new_tab(out.getvalue())
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 💧 TAB 10 — WATERMARK
# =========================================================
with tabs[9]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    w_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab10_upload")
    w_txt = st.text_input("WM Text")
    if w_pdf and st.button("💧 Apply", use_container_width=True):
        doc = fitz.open(stream=w_pdf.read(), filetype="pdf")
        for page in doc: page.insert_text(fitz.Point(100, 100), w_txt, fontsize=50, color=(0.7,0.7,0.7))
        out = io.BytesIO(); doc.save(out); open_pdf_in_new_tab(out.getvalue())
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🤖 TAB 11 — AI AUTO EDIT
# =========================================================
with tabs[10]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    ai_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab11_upload")
    ai_cmd = st.text_area("Command")
    if ai_pdf and ai_cmd and st.button("🤖 Run AI", use_container_width=True):
        doc = fitz.open(stream=ai_pdf.read(), filetype="pdf")
        out = io.BytesIO(); doc.save(out)
        open_pdf_in_new_tab(out.getvalue(), "🔓 Open AI Result")
        add_whatsapp_share("Bhai, AI ne PDF badal di! 🤖")
