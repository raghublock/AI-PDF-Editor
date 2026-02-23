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
    st.info("Tip: Font detail niche table se check karein aur wahi yahan fill karein.")
    
    with st.container():
        # Line 1: Text Inputs
        col1, col2 = st.columns(2)
        find_txt = col1.text_input("Find Text (Jo mitaana hai)")
        replace_txt = col2.text_input("Replace With (Naya word)")
        
        # Line 2: Advanced MS Word Style Controls
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        
        # Multiple Fonts Theme Option
        font_style = c1.selectbox("Font Theme (MS Word Style)", 
                                ["helv", "times-roman", "courier", "arial", "hebo"])
        
        # Font Size with Point/Decimal support
        f_size_manual = c2.number_input("Font Size", value=0.0, step=0.1, format="%.1f")
        
        t_color_manual = c3.color_picker("Text Color", "#000000")
        
        if c4.button("✨ Apply Transformation"):
            doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
            found = False
            
            for page in doc_edit:
                areas = page.search_for(find_txt)
                for rect in areas:
                    found = True
                    # Step 1: Redaction (Wipe old layer)
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    page.apply_redactions()
                    
                    # Step 2: Overlay New Layer with Selected Font
                    fs = f_size_manual if f_size_manual > 0 else (rect.y1 - rect.y0) - 1
                    rgb = tuple(int(t_color_manual.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                    
                    # Inserting text with specific font and point size
                    page.insert_text(fitz.Point(rect.x0, rect.y1 - 1), 
                                     replace_txt, 
                                     fontsize=fs, 
                                     fontname=font_style, 
                                     color=rgb)
            
            if found:
                out = io.BytesIO()
                doc_edit.save(out)
                st.success("Edit Complete! Check below to open.")
                open_pdf_in_new_tab(out.getvalue())
            else:
                st.error("Bhai, text nahi mila! Spelling check karein.")

    st.divider()

    # ---------------------- ORIGINAL VIEWER & ANALYZER ----------------------
    zoom = st.slider("🔍 Zoom Level", 50, 250, 130)
    base64_pdf = base64.b64encode(pdf_bytes).decode()
    
    pdf_viewer_html = f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
        <div id="container" style="height:500px; overflow-y:scroll; background:#222; padding:10px;"></div>
        <script>
            const pdfData = atob("{base64_pdf}");
            pdfjsLib.getDocument({{ data: pdfData }}).promise.then(pdf => {{
                const container = document.getElementById("container");
                for (let i = 1; i <= pdf.numPages; i++) {{
                    pdf.getPage(i).then(page => {{
                        const viewport = page.getViewport({{ scale: {zoom/100} }});
                        const canvas = document.createElement("canvas");
                        canvas.width = viewport.width; canvas.height = viewport.height;
                        container.appendChild(canvas);
                        page.render({{ canvasContext: canvas.getContext("2d"), viewport: viewport }});
                    }});
                }}
            }});
        </script>
    """
    st.components.v1.html(pdf_viewer_html, height=550)

    # Font Analyzer Table (Same as your logic but rounded)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    st.subheader("🔍 Font & Color Analysis")
    for page_num, page in enumerate(doc, start=1):
        st.write(f"📄 Page {page_num}")
        blocks = page.get_text("dict")["blocks"]
        rows = []
        for b in blocks:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        rows.append({
                            "Text": s["text"], 
                            "Font": s["font"], 
                            "Size": round(s["size"], 2),
                            "Color": "#{:02x}{:02x}{:02x}".format((s["color"] >> 16) & 255, (s["color"] >> 8) & 255, s["color"] & 255)
                        })
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, 
                    column_config={"Text": st.column_config.TextColumn("Text", width="large")})
