import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import base64
import io
import streamlit.components.v1 as components
from pdf2image import convert_from_bytes # OCR Support
import pytesseract # OCR Support

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
        🔓 Open & Print Edited PDF
    </button>
    """
    components.html(js_code, height=100)

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    pdf_bytes = uploaded_file.read()

    # ---------------------- FEATURE MENU ----------------------
    st.markdown("### 🛠️ Choose a Feature to Use")
    col_bt1, col_bt2, col_bt3, col_bt4, col_bt5 = st.columns(5)
    
    if "mode" not in st.session_state: st.session_state.mode = "Editor"
    
    if col_bt1.button("✏️ Smart Editor"): st.session_state.mode = "Editor"
    if col_bt2.button("🔍 Replace All"): st.session_state.mode = "ReplaceAll"
    if col_bt3.button("🖼️ PDF to Image"): st.session_state.mode = "ToImage"
    if col_bt4.button("📝 PDF to Text"): st.session_state.mode = "ToText"
    if col_bt5.button("🤖 Smart OCR"): st.session_state.mode = "OCR"

    # ---------------------- POINT 4: SMART OCR ----------------------
    if st.session_state.mode == "OCR":
        st.info("🤖 AI Scanning: Scanned PDF se text nikalne ke liye.")
        if st.button("🔍 Start Deep OCR Scan"):
            with st.spinner("AI is reading the images (Poppler/Tesseract required)..."):
                try:
                    images = convert_from_bytes(pdf_bytes) #
                    full_ocr_text = ""
                    for i, image in enumerate(images):
                        text = pytesseract.image_to_string(image) #
                        full_ocr_text += f"--- Page {i+1} ---\n{text}\n\n"
                    st.text_area("OCR Result", full_ocr_text, height=400)
                    st.download_button("Download OCR Text", full_ocr_text, "ocr_result.txt")
                except Exception as e:
                    st.error(f"Error: {e}. Make sure packages.txt is on GitHub.")

    # ---------------------- POINT 1: GLOBAL REPLACE ----------------------
    elif st.session_state.mode == "ReplaceAll":
        f_all = st.text_input("Find everywhere")
        r_all = st.text_input("Replace everywhere")
        if st.button("🚀 Global Update"):
            doc_all = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc_all:
                for rect in page.search_for(f_all):
                    page.add_redact_annot(rect, fill=(1,1,1))
                    page.apply_redactions()
                    page.insert_text(fitz.Point(rect.x0, rect.y1-1), r_all, fontname="helv", fontsize=10)
            out_all = io.BytesIO()
            doc_all.save(out_all)
            open_pdf_in_new_tab(out_all.getvalue())

    # ---------------------- POINT 2: PDF TO IMAGE ----------------------
    elif st.session_state.mode == "ToImage":
        doc_img = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i in range(len(doc_img)):
            pix = doc_img[i].get_pixmap()
            st.image(pix.tobytes("png"), caption=f"Page {i+1}")

    # ---------------------- POINT 3: PDF TO TEXT ----------------------
    elif st.session_state.mode == "ToText":
        doc_txt = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = "".join([p.get_text() for p in doc_txt])
        st.text_area("Text", full_text, height=300)

    # ---------------------- ORIGINAL SMART EDITOR (UNTOUCHED) ----------------------
    elif st.session_state.mode == "Editor":
        st.markdown("### 📝 Smart AI Edit (Layer Pattern)")
        with st.container():
            col1, col2 = st.columns(2)
            find_txt = col1.text_input("Find Text")
            replace_txt = col2.text_input("Replace With")
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
            font_library = {"Helvetica": "helv", "Times": "tiro", "Courier": "cour"}
            font_style = font_library[c1.selectbox("Font Theme", list(font_library.keys()))]
            f_size_manual = c2.number_input("Size", value=0.00, step=0.01, format="%.2f")
            t_color_manual = c3.color_picker("Text Color", "#000000")
            bg_color_manual = c4.color_picker("BG Color", "#FFFFFF") 
            s1, s2, s3 = st.columns(3)
            is_bold = s1.checkbox("Bold"); is_italic = s2.checkbox("Italic"); is_underline = s3.checkbox("Underline")

            if st.button("✨ Apply Smart Transformation"):
                doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
                style_map = {"helv": ["helv", "hebo", "helt", "hebi"], "tiro": ["tiro", "tibo", "tiit", "tibi"], "cour": ["cour", "cobo", "coit", "cobi"]}
                idx = (1 if is_bold else 0) + (2 if is_italic else 0)
                fname = style_map[font_style][idx] if font_style in style_map else font_style
                for page in doc_edit:
                    for rect in page.search_for(find_txt):
                        bg_rgb = tuple(int(bg_color_manual.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                        page.add_redact_annot(rect, fill=bg_rgb); page.apply_redactions()
                        rgb = tuple(int(t_color_manual.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                        page.insert_text(fitz.Point(rect.x0, rect.y1-1), replace_txt, fontsize=f_size_manual if f_size_manual > 0 else (rect.y1-rect.y0)-1, fontname=fname, color=rgb)
                        if is_underline: page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), color=rgb, width=1)
                out = io.BytesIO(); doc_edit.save(out); open_pdf_in_new_tab(out.getvalue())

    st.divider()

    # ---------------------- VIEWER & ANALYZER (UNTOUCHED) ----------------------
    zoom = st.slider("🔍 Zoom Level", 50, 250, 130)
    base64_pdf = base64.b64encode(pdf_bytes).decode()
    pdf_viewer_html = f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script><div id="container" style="height:500px; overflow-y:scroll; background:#222; padding:10px;"></div><script>const pdfData = atob("{base64_pdf}");pdfjsLib.getDocument({{ data: pdfData }}).promise.then(pdf => {{const container = document.getElementById("container");for (let i = 1; i <= pdf.numPages; i++) {{pdf.getPage(i).then(page => {{const viewport = page.getViewport({{ scale: {zoom/100} }});const canvas = document.createElement("canvas");canvas.width = viewport.width; canvas.height = viewport.height;container.appendChild(canvas);page.render({{ canvasContext: canvas.getContext("2d"), viewport: viewport }});}});}}}});</script>"""
    st.components.v1.html(pdf_viewer_html, height=550)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    st.subheader("🔍 Advanced Document Analysis")
    for page_num, page in enumerate(doc, start=1):
        st.write(f"📄 Page {page_num}")
        all_colors = set(); rows = []
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        c = s["color"]; hex_c = "#{:02x}{:02x}{:02x}".format((c >> 16) & 255, (c >> 8) & 255, c & 255); all_colors.add(hex_c); rows.append({"Text": s["text"], "Font": s["font"], "Size": round(s["size"], 2), "Color": hex_c})
        for draw in page.get_drawings():
            if "fill" in draw and draw["fill"]:
                c = draw["fill"]; all_colors.add("#{:02x}{:02x}{:02x}".format(int(c[0]*255), int(c[1]*255), int(c[2]*255)))
        cp_cols = st.columns(15)
        for i, h_code in enumerate(list(all_colors)):
            with cp_cols[i % 15]: st.markdown(f"<div style='width:30px;height:30px;border-radius:5px;background:{h_code};border:1px solid #777'></div>", unsafe_allow_html=True); st.caption(h_code)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, column_config={"Text": st.column_config.TextColumn("Text (Quick Copy)", width="large")}, hide_index=True)
        
