import streamlit as st
import fitz  # PyMuPDF
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
# CLEAN UI CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    body { background: #eef5ff; font-family: 'Inter', sans-serif; }
    .main-card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 20px; }
    .stButton>button { border-radius: 8px; font-weight: 700; transition: all 0.3s; }
    .stButton>button:hover { transform: scale(1.03); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .whatsapp-btn {
        background-color: #25D366; color: white; padding: 12px 24px;
        text-decoration: none; border-radius: 8px; font-weight: bold;
        display: inline-block; margin-top: 12px; text-align: center; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#003d8f;'>🔵 Pro PDF Studio — by Raghu</h1>", unsafe_allow_html=True)
st.write("")

# ---------------------------------------------------------
# UNIVERSAL FUNCTIONS
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
    <button onclick="openPDF()" style="background:#28a745;color:white;padding:12px 24px;border:none;border-radius:8px;font-weight:700;cursor:pointer;width:100%;">
        {btn_label}
    </button>
    """
    st.components.v1.html(js_code, height=80)

def add_whatsapp_share(msg="Bhai, Raghu ke tool se PDF mast banayi hai! 🚀"):
    encoded_msg = urllib.parse.quote(msg)
    st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank" class="whatsapp-btn">📲 Share on WhatsApp</a>', unsafe_allow_html=True)

def save_and_offer_download(pdf_bytes, filename="edited_document.pdf"):
    st.download_button(
        label="⬇ Download Edited PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True
    )

def get_deep_page_colors(page):
    colors = set()
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if b['type'] == 0:
            for l in b["lines"]:
                for s in l["spans"]:
                    c = s["color"]
                    colors.add("#{:02x}{:02x}{:02x}".format((c >> 16) & 255, (c >> 8) & 255, c & 255))
    for draw in page.get_drawings():
        if "fill" in draw and draw["fill"]:
            c = draw["fill"]
            colors.add("#{0:02x}{1:02x}{2:02x}".format(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)))
    return colors

# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------
tab_names = [
    "📘 Viewer + Smart Edit", "➕ Merge PDFs", "✂ Split PDF", "🗜 Compress PDF",
    "🖼 Extract Images", "📄 Extract Text", "📊 Extract Tables", 
    "📑 Reorder / Delete Pages", "✍ Add Signature", "💧 Watermark Tools", "🤖 AI Auto Edit"
]
tabs = st.tabs(tab_names)

# =========================================================
# 📘 TAB 1 — VIEWER + SMART EDITOR (FIXED & IMPROVED)
# =========================================================
with tabs[0]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📘 PDF Viewer + Smart Editor")
    
    # Use session state to persist uploaded bytes
    if 'viewer_pdf_bytes' not in st.session_state:
        st.session_state.viewer_pdf_bytes = None
        st.session_state.viewer_doc = None

    uploaded_file = st.file_uploader("📂 Upload PDF", type=["pdf"], key="viewer_upload")

    if uploaded_file is not None:
        try:
            # Read only once
            pdf_bytes = uploaded_file.read()
            st.session_state.viewer_pdf_bytes = pdf_bytes
            
            # Open doc once
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            st.session_state.viewer_doc = doc
            
            st.success(f"PDF loaded successfully! ({len(doc)} pages)")
            
            st.divider()
            st.subheader("📝 Smart Edit Controls")
            col1, col2 = st.columns(2)
            find_txt = col1.text_input("Find Text", key="find_text")
            replace_txt = col2.text_input("Replace With", key="replace_text")

            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
            font_library = {"Helvetica": "helv", "Times": "tiro", "Courier": "cour", "Symbol": "symb", "ZapfDingbats": "zadi"}
            selected_font = c1.selectbox("Font Theme", list(font_library.keys()))
            font_style = font_library[selected_font]
            f_size = c2.number_input("Font Size", value=0.0, step=0.5, min_value=0.0)
            t_color = c3.color_picker("Text Color", "#000000")
            bg_color = c4.color_picker("Background Color", "#FFFFFF")

            s1, s2, s3 = st.columns(3)
            is_bold = s1.checkbox("Bold")
            is_italic = s2.checkbox("Italic")
            is_underline = s3.checkbox("Underline")

            if st.button("✨ Apply Smart Replace", use_container_width=True):
                # Use stored bytes/doc for editing
                doc_edit = fitz.open(stream=st.session_state.viewer_pdf_bytes, filetype="pdf")
                found = False
                
                style_map = {"helv": ["helv", "hebo", "helt", "hebi"], 
                             "tiro": ["tiro", "tibo", "tiit", "tibi"], 
                             "cour": ["cour", "cobo", "coit", "cobi"]}
                idx = (1 if is_bold else 0) + (2 if is_italic else 0)
                final_font = style_map.get(font_style, [font_style])[idx % 4]

                for page in doc_edit:
                    rects = page.search_for(find_txt)
                    for rect in rects:
                        found = True
                        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255 for i in (0,2,4))
                        page.add_redact_annot(rect, fill=bg_rgb)
                        page.apply_redactions()
                        
                        fs = f_size if f_size > 0 else (rect.y1 - rect.y0) - 2
                        txt_rgb = tuple(int(t_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                        page.insert_text(fitz.Point(rect.x0, rect.y0 + fs*0.85), replace_txt, 
                                       fontsize=fs, fontname=final_font, color=txt_rgb)
                        if is_underline:
                            page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), 
                                         color=txt_rgb, width=1)

                if found:
                    out = io.BytesIO()
                    doc_edit.save(out)
                    out.seek(0)
                    st.success("🎉 Edit Complete!")
                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Edited PDF")
                    save_and_offer_download(out.getvalue(), "edited.pdf")
                    add_whatsapp_share("Bhai, edit mast ho gaya! ✨")
                else:
                    st.warning("Text nahi mila document mein.")

            st.divider()
            st.subheader("📄 PDF Preview")

            if st.session_state.viewer_pdf_bytes:
                zoom = st.slider("🔍 Zoom Level (%)", 50, 300, 100, step=10)
                
                try:
                    base64_pdf = base64.b64encode(st.session_state.viewer_pdf_bytes).decode('utf-8')
                    viewer_html = f"""
                    <div style="border:1px solid #ddd; border-radius:8px; overflow:hidden; background:#f8f9fa; padding:10px;">
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.338/pdf.min.js"></script>
                        <div id="pdfViewer" style="height:600px; overflow-y:auto;"></div>
                        <script>
                        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.338/pdf.worker.min.js';
                        const pdfData = atob("{base64_pdf}");
                        pdfjsLib.getDocument({{data: pdfData}}).promise.then(pdf => {{
                            const container = document.getElementById('pdfViewer');
                            for(let i=1; i<=pdf.numPages; i++){{
                                pdf.getPage(i).then(page => {{
                                    const scale = {zoom/100};
                                    const viewport = page.getViewport({{scale: scale}});
                                    const canvas = document.createElement('canvas');
                                    canvas.height = viewport.height;
                                    canvas.width = viewport.width;
                                    canvas.style.margin = '10px auto';
                                    canvas.style.display = 'block';
                                    container.appendChild(canvas);
                                    page.render({{canvasContext: canvas.getContext('2d'), viewport: viewport}});
                                }});
                            }}
                        }}).catch(err => {{
                            document.getElementById('pdfViewer').innerHTML = '<p style="color:red; text-align:center; padding:20px;">PDF preview load nahi ho paya: ' + err.message + '</p>';
                        }});
                        </script>
                    </div>
                    """
                    st.components.v1.html(viewer_html, height=680, scrolling=True)
                except Exception as e:
                    st.error(f"Preview load nahi ho raha: {str(e)}")
                    st.info("Bada PDF hai? Direct open kar lo niche se.")
                    open_pdf_in_new_tab(st.session_state.viewer_pdf_bytes, "🔓 Open PDF in New Tab")
            
            st.divider()
            st.subheader("🎨 Deep Color & Font Analyzer")
            if st.session_state.viewer_doc:
                doc_an = st.session_state.viewer_doc
                for pageno, page in enumerate(doc_an, start=1):
                    st.write(f"### 📄 Page {pageno}")
                    all_colors = get_deep_page_colors(page)
                    color_cols = st.columns(12)
                    for i, color in enumerate(list(all_colors)[:12]):
                        with color_cols[i]:
                            st.markdown(f"<div style='width:28px;height:28px;border-radius:5px;background:{color};border:1px solid #003d8f;'></div>", unsafe_allow_html=True)
                            st.caption(color)
                    rows = []
                    for b in page.get_text("dict")["blocks"]:
                        if b['type'] == 0:
                            for l in b["lines"]:
                                for s in l["spans"]:
                                    rows.append({
                                        "Text": s["text"],
                                        "Font": s["font"],
                                        "Size": round(s["size"], 2),
                                        "Color": "#{:02x}{:02x}{:02x}".format((s["color"] >> 16) & 255, (s["color"] >> 8) & 255, s["color"] & 255)
                                    })
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("No text found on this page.")

        except Exception as e:
            st.error(f"PDF open nahi ho paya: {str(e)}")
            st.info("File corrupt hai ya size bahut badi hai? Chhoti PDF try karo.")

    else:
        st.info("Upload PDF to start viewing & editing...")

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
            try:
                merger = fitz.open()
                for pdf in merge_files:
                    with fitz.open(stream=pdf.read(), filetype="pdf") as doc_temp: 
                        merger.insert_pdf(doc_temp, links=True, annots=True)
                out = io.BytesIO()
                merger.save(out)
                st.success("🎉 Merge Complete!")
                open_pdf_in_new_tab(out.getvalue(), "🔓 Open Merged PDF for Printing")
                save_and_offer_download(out.getvalue(), "merged.pdf")
                add_whatsapp_share("Bhai, PDFs merge ho gayi hain! 🚀")
            except Exception as e:
                st.error(f"Error: {str(e)}")
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
        try:
            doc = fitz.open(stream=split_pdf.read(), filetype="pdf")
            new = fitz.open()
            new.insert_pdf(doc, from_page=start-1, to_page=min(end-1, doc.page_count-1))
            out = io.BytesIO()
            new.save(out)
            st.success("🎉 Split Complete!")
            open_pdf_in_new_tab(out.getvalue(), "🔓 Open Split PDF for Printing")
            save_and_offer_download(out.getvalue(), "split.pdf")
            add_whatsapp_share("Bhai, PDF alag kar di! ✂️")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🗜 TAB 4 — COMPRESS PDF
# =========================================================
with tabs[3]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🗜 Compress PDF")
    comp_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab4_upload")
    compression_level = st.selectbox("Compression Level", ["Low", "Medium", "High"], index=1)
    dpi_map = {"Low": 150, "Medium": 96, "High": 72}
    if comp_pdf and st.button("🗜 Compress Now", use_container_width=True):
        try:
            doc = fitz.open(stream=comp_pdf.read(), filetype="pdf")
            dpi = dpi_map[compression_level]
            for page in doc:
                pix = page.get_pixmap(dpi=dpi)
                page.clean_contents()
                page.insert_image(page.rect, pixmap=pix)
            doc.subset_fonts()
            out = io.BytesIO()
            doc.save(out, garbage=3, deflate=True)
            st.success("🎉 Compression Complete!")
            open_pdf_in_new_tab(out.getvalue(), "🔓 Open Compressed PDF")
            save_and_offer_download(out.getvalue(), "compressed.pdf")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🖼 TAB 5 — EXTRACT IMAGES
# =========================================================
with tabs[4]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Extract Images")
    img_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab5_upload")
    if img_pdf and st.button("📸 Extract Now", use_container_width=True):
        try:
            doc = fitz.open(stream=img_pdf.read(), filetype="pdf")
            zip_buf = io.BytesIO()
            zipf = zipfile.ZipFile(zip_buf, "w")
            for pno in range(len(doc)):
                for img in doc.get_page_images(pno):
                    pix = fitz.Pixmap(doc, img[0])
                    zipf.writestr(f"img_{pno+1}.png", pix.tobytes("png"))
            zipf.close()
            st.success("🎉 Images Extracted!")
            st.download_button("⬇ Download ZIP", zip_buf.getvalue(), "images.zip")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📄 TAB 6 — EXTRACT TEXT
# =========================================================
with tabs[5]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📄 Extract Text")
    txt_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab6_upload")
    if txt_pdf:
        try:
            doc = fitz.open(stream=txt_pdf.read(), filetype="pdf")
            all_text = "".join([page.get_text() + "\n\n" for page in doc])
            st.text_area("Extracted Text", all_text, height=300)
            st.download_button("⬇ Download", all_text, "text.txt")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📊 TAB 7 — EXTRACT TABLES
# =========================================================
with tabs[6]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📊 Extract Tables")
    table_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab7_upload")
    if table_pdf:
        try:
            doc = fitz.open(stream=table_pdf.read(), filetype="pdf")
            all_rows = []
            for page in doc:
                tabs_found = page.find_tables()
                for t in tabs_found:
                    df = t.to_pandas()
                    df.dropna(how='all', inplace=True)
                    all_rows.append(df)
            if all_rows:
                combined_df = pd.concat(all_rows, ignore_index=True)
                st.dataframe(combined_df, use_container_width=True)
                csv = combined_df.to_csv(index=False)
                st.download_button("⬇ Download CSV", csv, "tables.csv")
            else:
                st.info("No tables found.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📑 TAB 8 — REORDER / DELETE PAGES
# =========================================================
with tabs[7]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📑 Reorder / Delete Pages")
    re_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab8_upload")
    if re_pdf:
        try:
            doc = fitz.open(stream=re_pdf.read(), filetype="pdf")
            page_list = list(range(1, doc.page_count + 1))
            selected = st.multiselect("Select Pages to Keep (in order)", page_list, default=page_list)
            if st.button("📑 Apply", use_container_width=True):
                new = fitz.open()
                for p in selected:
                    new.insert_pdf(doc, from_page=p-1, to_page=p-1)
                out = io.BytesIO()
                new.save(out)
                st.success("🎉 Reorder Complete!")
                open_pdf_in_new_tab(out.getvalue())
                save_and_offer_download(out.getvalue(), "reordered.pdf")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ✍ TAB 9 — ADD SIGNATURE
# =========================================================
with tabs[8]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("✍ Add Signature")
    s_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab9_upload")
    s_img = st.file_uploader("Upload Signature (PNG/JPG)", type=["png", "jpg"], key="tab9_sign")
    if s_pdf and s_img:
        col1, col2, col3, col4 = st.columns(4)
        x_pos = col1.number_input("X Position", value=100)
        y_pos = col2.number_input("Y Position", value=100)
        width = col3.number_input("Width", value=150)
        height = col4.number_input("Height", value=80)
        if st.button("✍ Sign Now", use_container_width=True):
            try:
                doc = fitz.open(stream=s_pdf.read(), filetype="pdf")
                img_bytes = s_img.read()
                rect = fitz.Rect(x_pos, y_pos, x_pos + width, y_pos + height)
                for page in doc:
                    page.insert_image(rect, stream=img_bytes, overlay=True)
                out = io.BytesIO()
                doc.save(out)
                st.success("🎉 Signature Added!")
                open_pdf_in_new_tab(out.getvalue())
                save_and_offer_download(out.getvalue(), "signed.pdf")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 💧 TAB 10 — WATERMARK TOOLS
# =========================================================
with tabs[9]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("💧 Watermark Tools")
    w_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab10_upload")
    w_txt = st.text_input("Watermark Text", value="CONFIDENTIAL")
    opacity = st.slider("Opacity", 0.0, 1.0, 0.3)
    rotate = st.slider("Rotate (degrees)", -90, 90, 45)
    if w_pdf and st.button("💧 Apply", use_container_width=True):
        try:
            doc = fitz.open(stream=w_pdf.read(), filetype="pdf")
            for page in doc:
                point = fitz.Point(page.rect.width / 2, page.rect.height / 2)
                page.insert_text(point, w_txt, fontsize=50, color=(0.5, 0.5, 0.5), opacity=opacity, rotate=rotate)
            out = io.BytesIO()
            doc.save(out)
            st.success("🎉 Watermark Added!")
            open_pdf_in_new_tab(out.getvalue())
            save_and_offer_download(out.getvalue(), "watermarked.pdf")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🤖 TAB 11 — AI AUTO EDIT
# =========================================================
with tabs[10]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🤖 AI Auto Edit")
    ai_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab11_upload")
    ai_cmd = st.text_area("AI Command (e.g., 'Remove all watermarks')")
    if ai_pdf and ai_cmd and st.button("🤖 Run AI", use_container_width=True):
        try:
            doc = fitz.open(stream=ai_pdf.read(), filetype="pdf")
            # Placeholder for AI logic - add real AI here if possible
            st.info("AI processing... (Placeholder: No changes made yet)")
            out = io.BytesIO()
            doc.save(out)
            open_pdf_in_new_tab(out.getvalue(), "🔓 Open AI Result")
            save_and_offer_download(out.getvalue(), "ai_edited.pdf")
            add_whatsapp_share("Bhai, AI ne PDF badal di! 🤖")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)
