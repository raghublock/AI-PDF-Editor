import streamlit as st
import fitz
import pandas as pd
import io
import base64
import zipfile
# PyPDF2 ko import rehne diya hai par merging fitz (PyMuPDF) se hi kar rahe hain fast performance ke liye

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
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#003d8f;'>🔵 Pro PDF Studio — by Raghu</h1>", unsafe_allow_html=True)
st.write("")

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

    # Added unique key
    uploaded_file = st.file_uploader("📂 Upload PDF", type=["pdf"], key="tab1_upload")

    def open_pdf_in_new_tab(pdf_bytes):
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        js_code = f"""<script>function openPDF() {{ const base64 = "{base64_pdf}"; const byteCharacters = atob(base64); const byteNumbers = new Array(byteCharacters.length); for (let i = 0; i < byteCharacters.length; i++) {{ byteNumbers[i] = byteCharacters.charCodeAt(i); }} const byteArray = new Uint8Array(byteNumbers); const blob = new Blob([byteArray], {{type: 'application/pdf'}}); const fileURL = URL.createObjectURL(blob); window.open(fileURL, '_blank'); }}</script><button onclick="openPDF()" style="background:#005ce6;color:white;padding:10px 20px;border:none;border-radius:6px;font-weight:700;cursor:pointer;">🔓 Open Edited PDF</button>"""
        st.components.v1.html(js_code, height=120)

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
                    page.add_redact_annot(rect, fill=bg_rgb)
                    page.apply_redactions()
                    fs = f_size if f_size > 0 else (rect.y1 - rect.y0) - 1
                    txt_rgb = tuple(int(t_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                    page.insert_text(fitz.Point(rect.x0, rect.y1 - 1), replace_txt, fontsize=fs, fontname=final_font, color=txt_rgb)
                    if is_underline: page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), color=txt_rgb, width=1)

            if found:
                out = io.BytesIO(); doc_edit.save(out)
                st.success("🎉 Edit Complete!"); open_pdf_in_new_tab(out.getvalue())
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
            st.write(f"### 📄 Page {pageno}")
            all_colors = get_deep_page_colors(page)
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
            out = io.BytesIO(); merger.save(out); st.success("🎉 Merged!"); st.download_button("⬇ Download", out.getvalue(), "merged.pdf")
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
    if split_pdf:
        if st.button("✂ Split Now", use_container_width=True):
            doc = fitz.open(stream=split_pdf.read(), filetype="pdf")
            new = fitz.open(); new.insert_pdf(doc, from_page=start-1, to_page=min(end-1, doc.page_count-1))
            out = io.BytesIO(); new.save(out); st.success("🎉 Split Done!"); st.download_button("⬇ Download", out.getvalue(), "split.pdf")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🗜 TAB 4 — COMPRESS PDF
# =========================================================
with tabs[3]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🗜 Compress PDF")
    comp_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab4_upload")
    level = st.radio("Compression Level", ["Low", "Medium", "High"], horizontal=True)
    quality_map = {"Low": 70, "Medium": 40, "High": 20}
    if comp_pdf:
        if st.button("🗜 Compress Now", use_container_width=True):
            doc = fitz.open(stream=comp_pdf.read(), filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=quality_map[level])
                page.clean_contents(); page.insert_image(page.rect, pixmap=pix)
            out = io.BytesIO(); doc.save(out); st.success("🎉 Compressed!"); st.download_button("⬇ Download", out.getvalue(), "comp.pdf")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🖼 TAB 5 — EXTRACT IMAGES
# =========================================================
with tabs[4]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Extract Images")
    img_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab5_upload")
    if img_pdf:
        if st.button("📸 Extract Now", use_container_width=True):
            doc = fitz.open(stream=img_pdf.read(), filetype="pdf")
            zip_buffer = io.BytesIO(); zipf = zipfile.ZipFile(zip_buffer, "w")
            count = 0
            for page_no in range(len(doc)):
                for img in doc.get_page_images(page_no):
                    pix = fitz.Pixmap(doc, img[0])
                    zipf.writestr(f"img_{page_no+1}_{count}.png", pix.tobytes("png")); count += 1
            zipf.close(); st.success(f"🎉 {count} Images Extracted!"); st.download_button("⬇ Download ZIP", zip_buffer.getvalue(), "images.zip")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📄 TAB 6 — EXTRACT TEXT
# =========================================================
with tabs[5]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📄 Extract Text")
    txt_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab6_upload")
    if txt_pdf:
        doc = fitz.open(stream=txt_pdf.read(), filetype="pdf")
        all_text = "".join([page.get_text() + "\n\n" for page in doc])
        st.text_area("📄 Extracted Text", all_text, height=300)
        st.download_button("⬇ Download Text", all_text, "text.txt")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📊 TAB 7 — EXTRACT TABLES
# =========================================================
with tabs[6]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📊 Smart Table Extraction")
    table_pdf = st.file_uploader("Upload PDF with Tables", type=["pdf"], key="tab7_upload")
    if table_pdf:
        doc = fitz.open(stream=table_pdf.read(), filetype="pdf")
        all_rows = []
        for page in doc:
            # Smart table finding logic
            tabs_found = page.find_tables()
            for t in tabs_found:
                df_temp = t.to_pandas()
                all_rows.append(df_temp)
        if all_rows:
            final_df = pd.concat(all_rows, ignore_index=True)
            st.dataframe(final_df, use_container_width=True)
            st.download_button("⬇ Download Excel", final_df.to_csv(index=False).encode(), "tables.csv")
        else: st.warning("No clear tables found. Trying basic line extraction...")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📑 TAB 8 — REORDER PAGES
# =========================================================
with tabs[7]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📑 Reorder / Delete")
    re_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab8_upload")
    if re_pdf:
        doc = fitz.open(stream=re_pdf.read(), filetype="pdf")
        selected = st.multiselect("Select Pages (Order will be preserved)", range(1, doc.page_count+1))
        if st.button("📑 Apply Order", use_container_width=True):
            new = fitz.open()
            for p in selected: new.insert_pdf(doc, from_page=p-1, to_page=p-1)
            out = io.BytesIO(); new.save(out); st.download_button("⬇ Download", out.getvalue(), "ordered.pdf")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ✍ TAB 9 — SIGNATURE
# =========================================================
with tabs[8]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("✍ Add Signature")
    s_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab9_upload")
    s_img = st.file_uploader("Upload Sign (Transparent PNG recommended)", type=["png", "jpg"], key="tab9_sign")
    col_sig1, col_sig2, col_sig3 = st.columns(3)
    sig_x = col_sig1.number_input("X", value=50); sig_y = col_sig2.number_input("Y", value=50); sig_w = col_sig3.number_input("Width", value=120)
    if s_pdf and s_img:
        if st.button("✍ Sign PDF", use_container_width=True):
            doc = fitz.open(stream=s_pdf.read(), filetype="pdf")
            img_b = s_img.read()
            for page in doc: page.insert_image(fitz.Rect(sig_x, sig_y, sig_x+sig_w, sig_y+80), stream=img_b)
            out = io.BytesIO(); doc.save(out); st.download_button("⬇ Download", out.getvalue(), "signed.pdf")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 💧 TAB 10 — WATERMARK
# =========================================================
with tabs[9]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("💧 Watermark")
    w_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab10_upload")
    w_txt = st.text_input("Watermark Text"); w_img = st.file_uploader("Or Image", type=["png"], key="tab10_img")
    if w_pdf:
        if st.button("💧 Apply", use_container_width=True):
            doc = fitz.open(stream=w_pdf.read(), filetype="pdf")
            for page in doc:
                if w_txt: page.insert_text(fitz.Point(100, 100), w_txt, fontsize=60, color=(0.8, 0.8, 0.8), rotate=45)
                if w_img: page.insert_image(page.rect, stream=w_img.read(), opacity=0.2)
            out = io.BytesIO(); doc.save(out); st.download_button("⬇ Download", out.getvalue(), "wm.pdf")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🤖 TAB 11 — AI AUTO EDIT
# =========================================================
with tabs[10]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🤖 AI Auto Edit")
    ai_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab11_upload")
    ai_cmd = st.text_area("Command (e.g., Replace 'John' with 'Raghu' everywhere)")
    if ai_pdf and ai_cmd:
        if st.button("🤖 Run AI", use_container_width=True):
            doc = fitz.open(stream=ai_pdf.read(), filetype="pdf")
            # Improved logic parsing
            if "replace" in ai_cmd.lower():
                parts = ai_cmd.lower().split("with")
                f = parts[0].replace("replace", "").strip().replace("'", "")
                r = parts[1].split("everywhere")[0].strip().replace("'", "")
                for page in doc:
                    for rect in page.search_for(f):
                        page.add_redact_annot(rect, fill=(1,1,1)); page.apply_redactions()
                        page.insert_text(fitz.Point(rect.x0, rect.y1-1), r, fontname="helv", fontsize=10)
            out = io.BytesIO(); doc.save(out); st.success("🎉 AI Task Done!"); st.download_button("⬇ Download", out.getvalue(), "ai.pdf")
    st.markdown("</div>", unsafe_allow_html=True)
