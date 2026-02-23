import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import base64
import io
import streamlit.components.v1 as components
from pdf2image import convert_from_bytes # OCR Support
import pytesseract # OCR Support
from PIL import Image # Photo Support

# --- Smart UI Page Config ---
st.set_page_config(page_title="Pro AI PDF Editor - Raghu", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Beauty and Systematic Buttons
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #45a049; transform: scale(1.02); }
    .sidebar-text { font-size: 18px; font-weight: bold; color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 AI PDF Analyzer & Smart Editor – Made by Raghu 🚀")

# Sidebar for Systematic Feature Selection
with st.sidebar:
    st.markdown("<p class='sidebar-text'>🛠️ Feature Menu</p>", unsafe_allow_html=True)
    mode = st.radio("Choose Activity:", 
                    ["✏️ Smart Editor", "🔍 Replace All", "🤖 Smart OCR", 
                     "🖼️ PDF to Image", "📝 PDF to Text", "🔗 Merge PDFs", 
                     "✂️ Split PDF", "📸 Img to PDF"])
    st.markdown("---")
    st.info("Bikaner's Best AI PDF Suite")

# New Tab Logic (Untouched)
def open_pdf_in_new_tab(pdf_bytes):
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
    <button onclick="openPDF()" style="background-color: #2E7D32; color: white; padding: 15px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 18px; font-weight: bold;">
        🔓 Open & Print PDF
    </button>
    """
    components.html(js_code, height=100)

# ---------------------- FEATURE IMPLEMENTATION ----------------------

# Feature: Merge PDFs
if mode == "🔗 Merge PDFs":
    merge_files = st.file_uploader("Upload PDFs to Merge", type=["pdf"], accept_multiple_files=True)
    if st.button("🚀 Merge Files") and merge_files:
        res = fitz.open()
        for f in merge_files:
            with fitz.open(stream=f.read(), filetype="pdf") as m: res.insert_pdf(m)
        out = io.BytesIO(); res.save(out); open_pdf_in_new_tab(out.getvalue())

# Feature: Image to PDF
elif mode == "📸 Img to PDF":
    imgs = st.file_uploader("Upload JPEGs/PNGs", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if st.button("🚀 Convert to PDF") and imgs:
        doc_img = fitz.open()
        for img_f in imgs:
            img = Image.open(img_f); img_pdf = io.BytesIO(); img.save(img_pdf, format='PDF')
            with fitz.open(stream=img_pdf.getvalue(), filetype="pdf") as f: doc_img.insert_pdf(f)
        out = io.BytesIO(); doc_img.save(out); open_pdf_in_new_tab(out.getvalue())

# Main Logic for Existing Features
else:
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file:
        pdf_bytes = uploaded_file.read()

        # Split PDF Feature (Needs uploaded_file)
        if mode == "✂️ Split PDF":
            doc_sp = fitz.open(stream=pdf_bytes, filetype="pdf")
            pg = st.number_input(f"Page to Extract (1-{len(doc_sp)})", 1, len(doc_sp), 1)
            if st.button("🚀 Split Page"):
                new = fitz.open(); new.insert_pdf(doc_sp, from_page=pg-1, to_page=pg-1)
                out = io.BytesIO(); new.save(out); open_pdf_in_new_tab(out.getvalue())

        # Smart OCR
        elif mode == "🤖 Smart OCR":
            st.info("🤖 AI Scanning active.")
            if st.button("🔍 Start Deep OCR Scan"):
                images = convert_from_bytes(pdf_bytes)
                txt = "".join([f"--- Page {i+1} ---\n{pytesseract.image_to_string(img)}\n" for i, img in enumerate(images)])
                st.text_area("OCR Text", txt, height=300)

        # Global Replace
        elif mode == "🔍 Replace All":
            f_all = st.text_input("Find everywhere"); r_all = st.text_input("Replace everywhere")
            if st.button("🚀 Global Update"):
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    for rect in page.search_for(f_all):
                        page.add_redact_annot(rect, fill=(1,1,1)); page.apply_redactions()
                        page.insert_text(fitz.Point(rect.x0, rect.y1-1), r_all, fontname="helv", fontsize=10)
                out = io.BytesIO(); doc.save(out); open_pdf_in_new_tab(out.getvalue())

        # Smart Editor (Untouched Full Logic)
        elif mode == "✏️ Smart Editor":
            st.markdown("### 📝 Smart AI Edit (Layer Pattern)")
            with st.container():
                col1, col2 = st.columns(2)
                find_txt = col1.text_input("Find Text"); replace_txt = col2.text_input("Replace With")
                c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
                font_lib = {"Helvetica": "helv", "Times": "tiro", "Courier": "cour", "Symbol": "symb", "ZapfDingbats": "zadi"}
                f_style = font_lib[c1.selectbox("Font Theme", list(font_lib.keys()))]
                f_size = c2.number_input("Font Size", value=0.00, step=0.01, format="%.2f")
                t_color = c3.color_picker("Text Color", "#000000"); bg_color = c4.color_picker("BG Color", "#FFFFFF")
                s1, s2, s3 = st.columns(3); b, it, u = s1.checkbox("Bold"), s2.checkbox("Italic"), s3.checkbox("Underline")

                if st.button("✨ Apply Smart Transformation"):
                    doc_ed = fitz.open(stream=pdf_bytes, filetype="pdf")
                    style_map = {"helv": ["helv", "hebo", "helt", "hebi"], "tiro": ["tiro", "tibo", "tiit", "tibi"], "cour": ["cour", "cobo", "coit", "cobi"]}
                    idx = (1 if b else 0) + (2 if it else 0)
                    fname = style_map[f_style][idx] if f_style in style_map else f_style
                    for page in doc_ed:
                        for rect in page.search_for(find_txt):
                            page.add_redact_annot(rect, fill=tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)))
                            page.apply_redactions()
                            page.insert_text(fitz.Point(rect.x0, rect.y1-1), replace_txt, fontsize=f_size if f_size > 0 else (rect.y1-rect.y0)-1, fontname=fname, color=tuple(int(t_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)))
                            if u: page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), color=tuple(int(t_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)), width=1)
                    out = io.BytesIO(); doc_ed.save(out); open_pdf_in_new_tab(out.getvalue())

        # PDF to Image/Text Logic (Untouched)
        elif mode == "🖼️ PDF to Image":
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for i in range(len(doc)): st.image(doc[i].get_pixmap().tobytes("png"), caption=f"Page {i+1}")
        elif mode == "📝 PDF to Text":
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            st.text_area("Text", "".join([p.get_text() for p in doc]), height=300)

        # ---------------------- VIEWER & ANALYZER (UNTOUCHED) ----------------------
        st.divider()
        zoom = st.slider("🔍 Zoom Level", 50, 250, 130)
        base64_p = base64.b64encode(pdf_bytes).decode()
        pdf_viewer_html = f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script><div id="container" style="height:500px; overflow-y:scroll; background:#222; padding:10px; border-radius:10px;"></div><script>const pdfData = atob("{base64_p}");pdfjsLib.getDocument({{ data: pdfData }}).promise.then(pdf => {{const container = document.getElementById("container");for (let i = 1; i <= pdf.numPages; i++) {{pdf.getPage(i).then(page => {{const viewport = page.getViewport({{ scale: {zoom/100} }});const canvas = document.createElement("canvas");canvas.width = viewport.width; canvas.height = viewport.height;container.appendChild(canvas);page.render({{ canvasContext: canvas.getContext("2d"), viewport: viewport }});}});}}}});</script>"""
        st.components.v1.html(pdf_viewer_html, height=550)

        doc_an = fitz.open(stream=pdf_bytes, filetype="pdf")
        st.subheader("🔍 Advanced Document Analysis")
        for page_num, page in enumerate(doc_an, start=1):
            st.write(f"📄 Page {page_num}"); rows = []
            for b in page.get_text("dict")["blocks"]:
                if b['type'] == 0:
                    for l in b["lines"]:
                        for s in l["spans"]: rows.append({"Text": s["text"], "Font": s["font"], "Size": round(s["size"], 2), "Color": "#{:02x}{:02x}{:02x}".format((s["color"] >> 16) & 255, (s["color"] >> 8) & 255, s["color"] & 255)})
            cp_cols = st.columns(15)
            for i, h_code in enumerate(list(set([r["Color"] for r in rows]))):
                with cp_cols[i % 15]: st.markdown(f"<div style='width:30px;height:30px;border-radius:5px;background:{h_code};border:1px solid #777'></div>", unsafe_allow_html=True); st.caption(h_code)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            
