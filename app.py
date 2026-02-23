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
    st.info("Tip: Niche palette se color code copy karein aur font details table se check karein.")
    
    with st.container():
        # Line 1: Text Inputs
        col1, col2 = st.columns(2)
        find_txt = col1.text_input("Find Text (Jo mitaana hai)")
        replace_txt = col2.text_input("Replace With (Naya word)")
        
        # Line 2: Advanced Controls
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        
        # Extended Font Themes (Base 14 Fonts)
        all_fonts = [
            "helv", "heit", "hebo", "hebi", 
            "cour", "coit", "cobo", "cobi", 
            "tiro", "tiit", "tibo", "tibi", 
            "symb", "zadi"
        ]
        font_style = c1.selectbox("Font Theme", all_fonts, help="helv=Arial/Helvetica, tiro=Times New Roman, cour=Courier")
        
        f_size_manual = c2.number_input("Font Size", value=0.0, step=0.1, format="%.1f")
        t_color_manual = c3.color_picker("Text Color", "#000000")
        
        # Style Options (MS Word Style)
        s1, s2, s3, s4 = st.columns([1, 1, 1, 3])
        is_bold = s1.checkbox("Bold")
        is_italic = s2.checkbox("Italic")
        is_underline = s3.checkbox("Underline")

        if st.button("✨ Apply Smart Transformation"):
            doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
            found = False
            
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
                    
                    # Logic to handle bold/italic based on font name mapping
                    final_font = font_style
                    page.insert_text(
                        fitz.Point(rect.x0, rect.y1 - 1), 
                        replace_txt, 
                        fontsize=fs, 
                        fontname=final_font, 
                        color=rgb,
                        stroke_main=is_bold # Bold effect
                    )
                    
                    # Underline effect (Drawing a line)
                    if is_underline:
                        page.draw_line(fitz.Point(rect.x0, rect.y1), fitz.Point(rect.x1, rect.y1), color=rgb, width=1)
            
            if found:
                out = io.BytesIO()
                doc_edit.save(out)
                st.success("Edit Complete! Check below.")
                open_pdf_in_new_tab(out.getvalue())
            else:
                st.error("Bhai, text nahi mila!")

    st.divider()

    # ---------------------- VIEWER & ANALYZER ----------------------
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

    # --- ADVANCED COLOR & FONT ANALYZER ---
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    st.subheader("🎨 Document Analysis (Fonts & Every Color Code)")
    
    for page_num, page in enumerate(doc, start=1):
        st.write(f"📄 Page {page_num} Details:")
        
        all_colors = set()
        rows = []
        
        # Extract Text Info
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        c = s["color"]
                        hex_c = "#{:02x}{:02x}{:02x}".format((c >> 16) & 255, (c >> 8) & 255, c & 255)
                        all_colors.add(hex_c)
                        rows.append({
                            "Text": s["text"], "Font": s["font"], "Size": round(s["size"], 2), "Color": hex_c
                        })

        # Extract Background/Shape Colors
        for draw in page.get_drawings():
            if "fill" in draw and draw["fill"]:
                c = draw["fill"]
                hex_fill = "#{:02x}{:02x}{:02x}".format(int(c[0]*255), int(c[1]*255), int(c[2]*255))
                all_colors.add(hex_fill)

        # Show Color Palette
        cp_cols = st.columns(15)
        for i, h_code in enumerate(list(all_colors)):
            with cp_cols[i % 15]:
                st.markdown(f"<div title='{h_code}' style='width:30px;height:30px;border-radius:5px;background:{h_code};border:1px solid #777'></div>", unsafe_allow_html=True)
                st.caption(h_code)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, column_config={"Text": st.column_config.TextColumn("Text", width="large")})
