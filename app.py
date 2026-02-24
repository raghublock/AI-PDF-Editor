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
# TAB 1 — VIEWER + SMART EDITOR
# =========================================================
with tabs[0]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📘 PDF Viewer + Smart Editor")
    uploaded_file = st.file_uploader("📂 Upload PDF", type=["pdf"], key="viewer_upload")

    if uploaded_file:
        try:
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            st.divider()
            st.subheader("📝 Smart Replace")
            col1, col2 = st.columns(2)
            find_txt = col1.text_input("Find", placeholder="Text to find...")
            replace_txt = col2.text_input("Replace with", placeholder="New text...")

            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
            font_library = {"Helvetica": "helv", "Times": "tiro", "Courier": "cour"}
            selected_font = c1.selectbox("Font", list(font_library.keys()), index=0)
            fontname = font_library[selected_font]
            fontsize = c2.number_input("Font Size", min_value=6.0, value=11.0, step=0.5)
            text_color = c3.color_picker("Text Color", "#000000")
            bg_color = c4.color_picker("Background", "#ffffff")

            cols = st.columns(3)
            bold = cols[0].checkbox("Bold")
            italic = cols[1].checkbox("Italic")
            underline = cols[2].checkbox("Underline")

            if st.button("✨ Apply Replace", use_container_width=True):
                with st.spinner("Processing..."):
                    style_map = {"helv": ["helv", "hebo", "helt", "hebi"], "tiro": ["tiro", "tibo", "tiit", "tibi"], "cour": ["cour", "cobo", "coit", "cobi"]}
                    style_idx = (1 if bold else 0) + (2 if italic else 0)
                    final_font = style_map.get(fontname, [fontname])[style_idx % len(style_map.get(fontname, [fontname]))]

                    found = False
                    for page in doc:
                        rects = page.search_for(find_txt)
                        for rect in rects:
                            found = True
                            # Redact background
                            bg = tuple(int(bg_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                            page.add_redact_annot(rect, fill=bg)
                            page.apply_redactions()
                            # Insert new text
                            txt_rgb = tuple(int(text_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                            fs = fontsize if fontsize > 0 else rect.height - 2
                            page.insert_text((rect.x0, rect.y0 + fs*0.8), replace_txt, fontsize=fs, fontname=final_font, color=txt_rgb)
                            if underline:
                                page.draw_line((rect.x0, rect.y1), (rect.x1, rect.y1), color=txt_rgb, width=1)

                    if found:
                        out = io.BytesIO()
                        doc.save(out)
                        out.seek(0)
                        st.success("Edit successful!")
                        open_pdf_in_new_tab(out.getvalue())
                        save_and_offer_download(out.getvalue(), "smart_edited.pdf")
                        add_whatsapp_share("Bhai, smart edit ho gaya! 🔥")
                    else:
                        st.warning("Text not found in document.")

        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 2 — MERGE PDFs
# =========================================================
with tabs[1]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📦 Merge Multiple PDFs")
    merge_files = st.file_uploader("Upload PDFs to merge", type=["pdf"], accept_multiple_files=True, key="merge_upload")

    if merge_files and len(merge_files) >= 2:
        if st.button("🔗 Merge Now", use_container_width=True):
            with st.spinner("Merging PDFs..."):
                try:
                    merger = fitz.open()
                    for file in merge_files:
                        file.seek(0)
                        temp_doc = fitz.open(stream=file.read(), filetype="pdf")
                        merger.insert_pdf(temp_doc, links=True, annots=True)
                        temp_doc.close()

                    out = io.BytesIO()
                    merger.save(out)
                    out.seek(0)
                    st.success(f"Merged {len(merge_files)} PDFs!")
                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Merged PDF")
                    save_and_offer_download(out.getvalue(), "merged.pdf")
                    add_whatsapp_share("Bhai, saari PDFs merge ho gayi! 🚀")
                except Exception as e:
                    st.error(f"Merge failed: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 3 — SPLIT PDF
# =========================================================
with tabs[2]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("✂ Split PDF")
    split_file = st.file_uploader("Upload PDF", type=["pdf"], key="split_upload")

    if split_file:
        try:
            split_file.seek(0)
            doc = fitz.open(stream=split_file.read(), filetype="pdf")
            total_pages = len(doc)

            col1, col2 = st.columns(2)
            start = col1.number_input("From Page", min_value=1, max_value=total_pages, value=1)
            end = col2.number_input("To Page", min_value=1, max_value=total_pages, value=total_pages)

            if st.button("✂ Split Now", use_container_width=True):
                with st.spinner("Splitting..."):
                    new_doc = fitz.open()
                    new_doc.insert_pdf(doc, from_page=start-1, to_page=end-1)
                    out = io.BytesIO()
                    new_doc.save(out)
                    out.seek(0)
                    st.success(f"Pages {start}–{end} extracted!")
                    open_pdf_in_new_tab(out.getvalue())
                    save_and_offer_download(out.getvalue(), f"split_{start}-{end}.pdf")
                    add_whatsapp_share("PDF split ho gayi bhai! ✂️")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 4 — COMPRESS PDF
# =========================================================
with tabs[3]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🗜 Compress PDF")
    comp_file = st.file_uploader("Upload PDF", type=["pdf"], key="compress_upload")

    compression_level = st.selectbox("Compression Level", ["Light (fast)", "Medium (good)", "Strong (smallest)"], index=1)

    if comp_file and st.button("🗜 Compress Now", use_container_width=True):
        with st.spinner("Compressing..."):
            try:
                comp_file.seek(0)
                doc = fitz.open(stream=comp_file.read(), filetype="pdf")
                dpi = {"Light (fast)": 150, "Medium (good)": 96, "Strong (smallest)": 72}[compression_level]

                for page in doc:
                    pix = page.get_pixmap(dpi=dpi, alpha=False)
                    page.clean_contents()
                    page.insert_image(page.rect, pixmap=pix)

                doc.subset_fonts()  # reduce font size

                out = io.BytesIO()
                doc.save(out, garbage=4, deflate=True, clean=True)
                out.seek(0)
                st.success("Compression done!")
                open_pdf_in_new_tab(out.getvalue())
                save_and_offer_download(out.getvalue(), "compressed.pdf")
            except Exception as e:
                st.error(f"Compression failed: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 5 — EXTRACT IMAGES  (unchanged + error handling)
# =========================================================
with tabs[4]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Extract Images")
    img_file = st.file_uploader("Upload PDF", type=["pdf"], key="img_extract")

    if img_file and st.button("📸 Extract Now", use_container_width=True):
        with st.spinner("Extracting images..."):
            try:
                img_file.seek(0)
                doc = fitz.open(stream=img_file.read(), filetype="pdf")
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zipf:
                    count = 0
                    for pno in range(len(doc)):
                        for img_idx, img in enumerate(doc.get_page_images(pno)):
                            xref = img[0]
                            pix = fitz.Pixmap(doc, xref)
                            img_bytes = pix.tobytes("png")
                            zipf.writestr(f"page_{pno+1}_img_{img_idx+1}.png", img_bytes)
                            count += 1
                zip_buf.seek(0)
                st.success(f"Extracted {count} images!")
                st.download_button("⬇ Download ZIP", zip_buf.getvalue(), "extracted_images.zip", "application/zip")
            except Exception as e:
                st.error(f"Error extracting images: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 9 — SIGNATURE (improved position)
# =========================================================
with tabs[8]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("✍ Add Signature / Image")
    sig_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="sig_pdf")
    sig_img = st.file_uploader("Signature / Stamp (PNG/JPG)", type=["png", "jpg", "jpeg"], key="sig_img")

    if sig_pdf and sig_img:
        colx, coly, colw, colh = st.columns(4)
        x = colx.number_input("X position", value=100, step=10)
        y = coly.number_input("Y position", value=600, step=10)
        w = colw.number_input("Width", value=150, step=5)
        h = colh.number_input("Height", value=80, step=5)

        if st.button("✍ Apply Signature", use_container_width=True):
            with st.spinner("Adding signature..."):
                try:
                    sig_pdf.seek(0)
                    sig_img.seek(0)
                    doc = fitz.open(stream=sig_pdf.read(), filetype="pdf")
                    img_data = sig_img.read()

                    rect = fitz.Rect(x, y, x + w, y + h)

                    for page in doc:
                        page.insert_image(rect, stream=img_data, overlay=True)

                    out = io.BytesIO()
                    doc.save(out)
                    out.seek(0)
                    st.success("Signature added!")
                    open_pdf_in_new_tab(out.getvalue())
                    save_and_offer_download(out.getvalue(), "signed.pdf")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 10 — WATERMARK (improved)
# =========================================================
with tabs[9]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("💧 Add Watermark")
    wm_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="wm_pdf")
    wm_text = st.text_input("Watermark Text", "CONFIDENTIAL")
    opacity = st.slider("Opacity", 0.1, 1.0, 0.3, step=0.05)
    rotation = st.slider("Rotation (degrees)", -90, 90, 45, step=5)

    if wm_pdf and wm_text and st.button("💧 Apply Watermark", use_container_width=True):
        with st.spinner("Applying watermark..."):
            try:
                wm_pdf.seek(0)
                doc = fitz.open(stream=wm_pdf.read(), filetype="pdf")

                for page in doc:
                    page.insert_text(
                        (page.rect.width/2, page.rect.height/2),
                        wm_text,
                        fontsize=60,
                        color=(0.7, 0.7, 0.7),
                        opacity=opacity,
                        rotate=rotation,
                        overlay=False
                    )

                out = io.BytesIO()
                doc.save(out)
                out.seek(0)
                st.success("Watermark applied!")
                open_pdf_in_new_tab(out.getvalue())
                save_and_offer_download(out.getvalue(), "watermarked.pdf")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# Other tabs (6,7,11) ko same rakh sakte ho ya chhote improvements daal sakte ho
# Example TAB 6:
with tabs[5]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📄 Extract Text")
    txt_file = st.file_uploader("Upload PDF", type=["pdf"], key="txt_extract")

    if txt_file:
        try:
            txt_file.seek(0)
            doc = fitz.open(stream=txt_file.read(), filetype="pdf")
            full_text = "\n\n".join(page.get_text("text") for page in doc)
            st.text_area("Extracted Text", full_text, height=400)
            st.download_button("⬇ Download TXT", full_text, "extracted_text.txt")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# REMAINING TABS (simple placeholders with error handling)
# =========================================================
for i, tab in enumerate(tabs[6:]):
    with tab:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader(tab_names[i+6])
        st.info("Feature coming soon with improvements...")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Pro PDF Studio v2.0 • Made with ❤️ by Raghu • Jodhpur")
