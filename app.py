import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import base64
import io
import streamlit.components.v1 as components

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
    
    # ---------------------- SMART AI EDIT SECTION ----------------------
    st.markdown("### 📝 Smart AI Edit (Layer Pattern)")
    
    with st.container():
        col1, col2 = st.columns(2)
        find_txt = col1.text_input("Find Text (Jo mitaana hai)")
        replace_txt = col2.text_input("Replace With (Naya word)")
        
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        
        # Standard Fonts
        all_fonts = ["helv", "cour", "tiro", "symb", "zadi"]
        font_style = c1.selectbox("Font Theme", all_fonts)
        f_size_manual = c2.number_input("Font Size", value=0.0, step=0.1, format="%.1f")
        t_color_manual = c3.color_picker("Text Color", "#000000")
        
        # Style Options
        s1, s2, s3, s4 = st.columns([1, 1, 1, 3])
        is_bold = s1.checkbox("Bold")
        is_italic = s2.checkbox("Italic")
        is_underline = s3.checkbox("Underline")

        if c4.button("✨ Apply Smart Transformation"):
            doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
            found = False
            
            # Logic for Bold/Italic Font Name
            suffix = ""
            if is_bold and is_italic: suffix = "-BoldItalic"
            elif is_bold: suffix = "-Bold"
            elif is_italic: suffix = "-Italic"
            
            # Mapping standard names to match PyMuPDF format
            font_map = {"helv": "helvetica", "cour": "courier", "tiro": "times-roman"}
            base_font = font_map.get(font_style, font_style)
            final_font_name = f"{base_font}{suffix}"

            for page in doc_edit:
                areas = page.search_for(find_txt)
                for rect in areas:
                    found = True
                    # Step 1: Redaction
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    page.apply_redactions()
                    
                    # Step 2: Overlay New Layer
                    fs = f_size_manual if f_size_manual > 0 else (rect.y1 - rect.y0) - 1
                    rgb = tuple(int(t_color_manual.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                    
                    # Fixed insert_text call (stroke_main removed)
                    page.insert_text(
                        fitz.Point(rect.x0, rect.y1 - 1), 
                        replace_txt, 
                        fontsize=fs, 
                        fontname=final_font_name, 
                        color=rgb
                    )
                    
                    if is_underline:
                        page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), color=rgb, width=1)
            
            if found:
                out = io.BytesIO()
                doc_edit.save(out)
                st.success("Edit Complete!")
                open_pdf_in_new_tab(out.getvalue())
            else:
                st.error("Text nahi mila!")

    st.divider()
    # (Viewer and Analyzer part remains same)
