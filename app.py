import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import base64
import io
import streamlit.components.v1 as components
from pdf2image import convert_from_bytes # OCR Support
import pytesseract # OCR Support
from PIL import Image # Image support ke liye

st.set_page_config(page_title="Pro AI PDF Editor - Raghu", layout="wide")

st.title("📄 AI PDF Analyzer & Smart Editor – Made by Raghu 🚀")

# Sidebar for Navigation & New Tab Logic
def open_pdf_in_new_tab(pdf_bytes):
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
    <button onclick="openPDF()" style="background-color: #4CAF50; color: white; padding: 15px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 18px; font-weight: bold;">
        🔓 Open & Print PDF
    </button>
    """
    components.html(js_code, height=100)

# ---------------------- FEATURE MENU (8 Buttons) ----------------------
st.markdown("### 🛠️ Choose a Feature to Use")
col_bt1, col_bt2, col_bt3, col_bt4, col_bt5, col_bt6, col_bt7, col_bt8 = st.columns(8)

if "mode" not in st.session_state: st.session_state.mode = "Editor"

if col_bt1.button("✏️ Editor"): st.session_state.mode = "Editor"
if col_bt2.button("🔍 Replace All"): st.session_state.mode = "ReplaceAll"
if col_bt3.button("🖼️ PDF to Image"): st.session_state.mode = "ToImage"
if col_bt4.button("📝 PDF to Text"): st.session_state.mode = "ToText"
if col_bt5.button("🤖 Smart OCR"): st.session_state.mode = "OCR"
if col_bt6.button("🔗 Merge"): st.session_state.mode = "Merge"
if col_bt7.button("✂️ Split"): st.session_state.mode = "Split"
if col_bt8.button("📸 Img to PDF"): st.session_state.mode = "ImgToPdf"

uploaded_file = st.file_uploader("Upload PDF (Required for Editor, Replace, OCR, Split)", type=["pdf"])

# ---------------------- POINT 6: MERGE PDFs ----------------------
if st.session_state.mode == "Merge":
    st.subheader("🔗 Merge Multiple PDFs")
    merge_files = st.file_uploader("Upload PDFs to Merge", type=["pdf"], accept_multiple_files=True, key="merger")
    if st.button("🚀 Merge Now") and merge_files:
        result_pdf = fitz.open()
        for f in merge_files:
            with fitz.open(stream=f.read(), filetype="pdf") as m_pdf:
                result_pdf.insert_pdf(m_pdf)
        out = io.BytesIO()
        result_pdf.save(out)
        st.success("PDFs Merged Successfully!")
        open_pdf_in_new_tab(out.getvalue())

# ---------------------- POINT 7: SPLIT PDF ----------------------
elif st.session_state.mode == "Split" and uploaded_file:
    st.subheader("✂️ Split PDF Pages")
    doc_split = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page_num = st.number_input(f"Enter Page Number to Extract (1 to {len(doc_split)})", 1, len(doc_split), 1)
    if st.button("🚀 Extract Page"):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc_split, from_page=page_num-1, to_page=page_num-1)
        out_split = io.BytesIO()
        new_doc.save(out_split)
        st.success(f"Page {page_num} Extracted!")
        open_pdf_in_new_tab(out_split.getvalue())

# ---------------------- POINT 8: IMAGE TO PDF (JPEG ADD) ----------------------
elif st.session_state.mode == "ImgToPdf":
    st.subheader("🖼️ Convert Images to PDF")
    uploaded_imgs = st.file_uploader("Upload JPEG/PNG Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if st.button("🚀 Convert to PDF") and uploaded_imgs:
        img_doc = fitz.open()
        for img_file in uploaded_imgs:
            img = Image.open(img_file)
            pdf_bytes_img = img_file.read() # Read image bytes
            img_pdf_bytes = img_doc.convert_to_pdf(pdf_bytes_img) # PyMuPDF magic
            img_doc.insert_pdf(fitz.open("pdf", img_pdf_bytes))
        out_img_pdf = io.BytesIO()
        img_doc.save(out_img_pdf)
        st.success("Images Converted to PDF!")
        open_pdf_in_new_tab(out_img_pdf.getvalue())

# ---------------------- ORIGINAL FEATURES ----------------------
elif uploaded_file:
    pdf_bytes = uploaded_file.read()

    if st.session_state.mode == "OCR":
        st.info("🤖 AI Scanning: Scanned PDF se text nikalne ke liye.")
        if st.button("🔍 Start Deep OCR Scan"):
            with st.spinner("AI reading images..."):
                try:
                    images = convert_from_bytes(pdf_bytes)
                    full_ocr_text = "".join([f"--- Page {i+1} ---\n{pytesseract.image_to_string(img)}\n\n" for i, img in enumerate(images)])
                    st.text_area("OCR Result", full_ocr_text, height=400)
                except Exception as e: st.error(f"Error: {e}")

    elif st.session_state.mode == "ReplaceAll":
        f_all = st.text_input("Find everywhere"); r_all = st.text_input("Replace everywhere")
        if st.button("🚀 Global Update"):
            doc_all = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc_all:
                for rect in page.search_for(f_all):
                    page.add_redact_annot(rect, fill=(1,1,1)); page.apply_redactions()
                    page.insert_text(fitz.Point(rect.x0, rect.y1-1), r_all, fontname="helv", fontsize=10)
            out_all = io.BytesIO(); doc_all.save(out_all); open_pdf_in_new_tab(out_all.getvalue())

    elif st.session_state.mode == "ToImage":
        doc_img = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i in range(len(doc_img)):
            st.image(doc_img[i].get_pixmap().tobytes("png"), caption=f"Page {i+1}")

    elif st.session_state.mode == "ToText":
        doc_txt = fitz.open(stream=pdf_bytes, filetype="pdf")
        st.text_area("Text", "".join([p.get_text() for p in doc_txt]), height=300)

    elif st.session_state.mode == "Editor":
        st.markdown("### 📝 Smart AI Edit (Layer Pattern)")
        with st.container():
            col1, col2 = st.columns(2)
            find_txt = col1.text_input("Find Text"); replace_txt = col2.text_input("Replace With")
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
            font_lib = {"Helvetica (Arial Style)": "helv", "Times New Roman Style": "tiro", "Courier (Typewriter Style)": "cour", "Symbol": "symb", "ZapfDingbats": "zadi"}
            font_style = font_lib[c1.selectbox("Font Theme", list(font_lib.keys()))]
            f_size = c2.number_input("Font Size", value=0.00, step=0.01, format="%.2f")
            t_color = c3.color_picker("Text Color", "#000000")
            bg_color = c4.color_picker("BG Color", "#FFFFFF")
            s1, s2, s3 = st.columns(3)
            is_bold, is_italic, is_underline = s1.checkbox("Bold"), s2.checkbox("Italic"), s3.checkbox("Underline")

            if st.button("✨ Apply Transformation"):
                doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
                style_map = {"helv": ["helv", "hebo", "helt", "hebi"], "tiro": ["tiro", "tibo", "tiit", "tibi"], "cour": ["cour", "cobo", "coit", "cobi"]}
                idx = (1 if is_bold else 0) + (2 if is_italic else 0)
                fname = style_map[font_style][idx] if font_style in style_map else font_style
                for page in doc_edit:
                    for rect in page.search_for(find_txt):
                        page.add_redact_annot(rect, fill=tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)))
                        page.apply_redactions()
                        fs = f_size if f_size > 0 else (rect.y1 - rect.y0) - 1
                        rgb = tuple(int(t_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                        page.insert_text(fitz.Point(rect.x0, rect.y1-1), replace_txt, fontsize=fs, fontname=fname, color=rgb)
                        if is_underline: page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), color=rgb, width=1)
                out_ed = io.BytesIO(); doc_edit.save(out_ed); open_pdf_in_new_tab(out_ed.getvalue())

    st.divider()
    # Analyzer aur Viewer waisa hi rahega
    zoom = st.slider("🔍 Zoom Level", 50, 250, 130)
    base64_p = base64.b64encode(pdf_bytes).decode()
    pdf_viewer_html = f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script><div id="container" style="height:500px; overflow-y:scroll; background:#222; padding:10px;"></div><script>const pdfData = atob("{base64_p}");pdfjsLib.getDocument({{ data: pdfData }}).promise.then(pdf => {{const container = document.getElementById("container");for (let i = 1; i <= pdf.numPages; i++) {{pdf.getPage(i).then(page => {{const viewport = page.getViewport({{ scale: {zoom/100} }});const canvas = document.createElement("canvas");canvas.width = viewport.width; canvas.height = viewport.height;container.appendChild(canvas);page.render({{ canvasContext: canvas.getContext("2d"), viewport: viewport }});}});}}}});</script>"""
    st.components.v1.html(pdf_viewer_html, height=550)
    doc_an = fitz.open(stream=pdf_bytes, filetype="pdf")
    for p_num, page in enumerate(doc_an, start=1):
        st.write(f"📄 Page {p_num}"); rows = []
        for b in page.get_text("dict")["blocks"]:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]: rows.append({"Text": s["text"], "Font": s["font"], "Size": round(s["size"], 2), "Color": "#{:02x}{:02x}{:02x}".format((s["color"] >> 16) & 255, (s["color"] >> 8) & 255, s["color"] & 255)})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        
