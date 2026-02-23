import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import base64
import io
import streamlit.components.v1 as components

# ================== GLOBAL PAGE CONFIG ==================
st.set_page_config(
    page_title="Pro AI PDF Editor - Raghu",
    layout="wide",
)

# ================== FORCE CSS OVERRIDE (IMPORTANT) ==================
st.markdown("""
<style>

:root {
    --blue-ice-1: #cfeaff;
    --blue-ice-2: #e9f5ff;
    --blue-ice-strong: #0059b3;
}

/* FORCE REMOVE STREAMLIT DEFAULT PADDING */
.main, .block-container {
    padding-top: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
}

/* GLOBAL BACKGROUND */
body, .stApp {
    background: linear-gradient(135deg, var(--blue-ice-1) 0%, var(--blue-ice-2) 100%) !important;
    font-family: 'Inter', sans-serif !important;
}

/* HIDING STREAMLIT DEFAULT HEADER & FOOTER */
header, footer {
    visibility: hidden !important;
}

/* BIG CENTER GLASS CARD */
.big-glass-card {
    width: 100%;
    padding: 40px;
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.20);
    box-shadow: 0 12px 40px rgba(0, 60, 150, 0.20);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.45);
    text-align: center;
    margin-bottom: 40px;
    margin-top: 10px;
}

.big-glass-card h1 {
    color: var(--blue-ice-strong);
    font-size: 50px;
    font-weight: 900;
    margin-bottom: 5px;
}

.big-glass-card h3 {
    color: var(--blue-ice-strong);
    font-size: 22px;
    opacity: 0.8;
    margin-top: -10px;
}

/* Blue Ice Button */
.blue-btn {
    background: linear-gradient(135deg, #2a7cc8 0%, #5bb2ff 100%);
    color: white !important;
    padding: 14px 20px;
    border: none;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
    width: 100%;
    transition: 0.2s ease;
    text-align: center;
}
.blue-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 110, 200, 0.3);
}

/* Force Button Style */
.stButton>button {
    background: linear-gradient(135deg, #2a7cc8 0%, #5bb2ff 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    height: 55px !important;
    transition: 0.2s ease !important;
}
.stButton>button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 110, 200, 0.3) !important;
}

/* Inputs Force Style */
input, textarea, select {
    border-radius: 10px !important;
    border: 1px solid #70aeea !important;
    background: #ffffffdd !important;
}

/* Scrollbar Style */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-thumb { background: #7bb6f0; border-radius: 6px; }
::-webkit-scrollbar-track { background: #e1efff; }

</style>
""", unsafe_allow_html=True)

# ================== HEADER ==================
st.markdown("""
<div class="big-glass-card">
    <h1>🔮 Pro AI PDF Editor</h1>
    <h3>Blue Ice Ultra Edition — by Raghu</h3>
</div>
""", unsafe_allow_html=True)

st.title("")  # spacing

# ================== NEW TAB PDF OPEN ==================
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
    <button onclick="openPDF()" class="blue-btn">🔓 Open & Print Edited PDF</button>
    """
    components.html(js_code, height=120)

# ================== DEEP COLOR SCAN FUNCTION ==================
def get_deep_page_colors(page):
    colors = set()
    blocks = page.get_text("dict")["blocks"]

    for b in blocks:
        if b['type'] == 0:
            for l in b["lines"]:
                for s in l["spans"]:
                    c = s["color"]
                    colors.add("#{0:02x}{1:02x}{2:02x}".format((c>>16)&255,(c>>8)&255,c&255))

    for draw in page.get_drawings():
        if "fill" in draw and draw["fill"]:
            c = draw["fill"]
            colors.add("#{0:02x}{1:02x}{2:02x}".format(int(c[0]*255),int(c[1]*255),int(c[2]*255)))

    return colors


# ================== MAIN APP ==================
uploaded_file = st.file_uploader("📂 Upload Your PDF", type=["pdf"])

if uploaded_file:
    pdf_bytes = uploaded_file.read()

    st.markdown("### 📝 Smart AI Edit Controls")
    st.info("👇 Jo text change karna hai woh yahan set karein.")

    with st.container():
        col1, col2 = st.columns(2)
        find_txt = col1.text_input("Find Text")
        replace_txt = col2.text_input("Replace With")

        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])

        font_library = {
            "Helvetica (Arial Style)": "helv",
            "Times New Roman Style": "tiro",
            "Courier (Typewriter Style)": "cour",
            "Symbol": "symb",
            "ZapfDingbats": "zadi"
        }

        selected_font_label = c1.selectbox("Font Theme", list(font_library.keys()))
        font_style = font_library[selected_font_label]

        f_size_manual = c2.number_input("Font Size", value=0.00, step=0.01, format="%.2f")
        t_color_manual = c3.color_picker("Text Color", "#000000")
        bg_color_manual = c4.color_picker("Background Patch Color", "#FFFFFF")

        s1, s2, s3, s4 = st.columns([1, 1, 1, 3])
        is_bold = s1.checkbox("Bold")
        is_italic = s2.checkbox("Italic")
        is_underline = s3.checkbox("Underline")

        if st.button("✨ Apply Smart Transformation", use_container_width=True):
            doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
            found = False

            style_map = {
                "helv": ["helv", "hebo", "helt", "hebi"],
                "tiro": ["tiro", "tibo", "tiit", "tibi"],
                "cour": ["cour", "cobo", "coit", "cobi"]
            }

            if font_style in style_map:
                idx = (1 if is_bold else 0) + (2 if is_italic else 0)
                final_font = style_map[font_style][idx]
            else:
                final_font = font_style

            for page in doc_edit:
                areas = page.search_for(find_txt)
                for rect in areas:
                    found = True

                    bg_rgb = tuple(int(bg_color_manual.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                    page.add_redact_annot(rect, fill=bg_rgb)
                    page.apply_redactions()

                    fs = f_size_manual if f_size_manual > 0 else (rect.y1 - rect.y0) - 1
                    txt_rgb = tuple(int(t_color_manual.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))

                    page.insert_text(
                        fitz.Point(rect.x0, rect.y1 - 1),
                        replace_txt,
                        fontsize=fs,
                        fontname=final_font,
                        color=txt_rgb
                    )

                    if is_underline:
                        page.draw_line(
                            fitz.Point(rect.x0, rect.y1),
                            fitz.Point(rect.x1, rect.y1),
                            color=txt_rgb, width=1
                        )

            if found:
                out = io.BytesIO()
                doc_edit.save(out)
                st.success("🎉 Edit Complete! Open PDF below")
                open_pdf_in_new_tab(out.getvalue())
            else:
                st.error("❌ Text not found. Check spelling.")

    st.divider()

    # ============ PDF VIEWER ============
    zoom = st.slider("🔍 Zoom Level", 50, 250, 130)
    base64_pdf = base64.b64encode(pdf_bytes).decode()

    viewer_html = f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
        <div id="pdf_container" style="height:520px; overflow-y:scroll; background:#e6f3ff; padding:12px; border-radius:14px;"></div>
        <script>
            const pdfData = atob("{base64_pdf}");
            pdfjsLib.getDocument({{ data: pdfData }}).promise.then(pdf => {{
                const container = document.getElementById("pdf_container");
                for (let i = 1; i <= pdf.numPages; i++) {{
                    pdf.getPage(i).then(page => {{
                        const viewport = page.getViewport({{ scale: {zoom/100} }});
                        const canvas = document.createElement("canvas");
                        canvas.width = viewport.width;
                        canvas.height = viewport.height;
                        canvas.style.marginBottom = "15px";
                        container.appendChild(canvas);
                        page.render({{
                            canvasContext: canvas.getContext("2d"),
                            viewport: viewport
                        }});
                    }});
                }}
            }});
        </script>
    """
    st.components.v1.html(viewer_html, height=560)

    # ============ ANALYZER ============
    st.subheader("🎨 Deep Color Analyzer + Copy Table")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for pageno, page in enumerate(doc, start=1):
        st.write(f"### 📄 Page {pageno}")

        all_colors = get_deep_page_colors(page)

        color_cols = st.columns(15)
        for i, color in enumerate(all_colors):
            with color_cols[i % 15]:
                st.markdown(f"""
                <div style='width:30px;height:30px;border-radius:6px;background:{color};
                border:1px solid #004b90'></div>
                """, unsafe_allow_html=True)
                st.caption(color)

        rows = []
        for b in page.get_text("dict")["blocks"]:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        c = s["color"]
                        hex_c = "#{:02x}{:02x}{:02x}".format((c>>16)&255,(c>>8)&255,c&255)
                        rows.append({
                            "Text": s["text"],
                            "Font": s["font"],
                            "Size": round(s["size"], 2),
                            "Color": hex_c
                        })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
