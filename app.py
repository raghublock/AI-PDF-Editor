import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import base64

st.set_page_config(page_title="PDF Viewer + Font Analyzer", layout="wide")

st.title("📄 PDF Viewer + Font & Color Analyzer")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:

    pdf_bytes = uploaded_file.read()

    # ---------------------- ZOOM OPTION ----------------------
    zoom = st.slider("🔍 Zoom Level", min_value=50, max_value=250, value=130, step=10)
    scale = zoom / 100  # PDF.js scale factor

    # ---------------------- MULTI-PAGE SCROLLABLE PDF VIEWER ----------------------
    st.subheader("📘 PDF Preview (Scrollable + Zoomable)")

    base64_pdf = base64.b64encode(pdf_bytes).decode()

    pdf_viewer = f"""
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>

            <style>
                body {{
                    margin: 0;
                    background: #222;
                    color: white;
                }}

                #container {{
                    height: 700px;
                    overflow-y: scroll;
                    padding: 10px;
                }}

                canvas {{
                    display: block;
                    margin: 20px auto;
                    border: 1px solid #555;
                }}
            </style>
        </head>

        <body>
            <div id="container"></div>

            <script>
                const pdfData = atob("{base64_pdf}");
                const userScale = {scale};

                pdfjsLib.getDocument({{ data: pdfData }}).promise.then(pdf => {{
                    const container = document.getElementById("container");
                    container.innerHTML = "";   // clear previous render

                    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {{
                        pdf.getPage(pageNum).then(page => {{

                            const viewport = page.getViewport({{ scale: userScale }});
                            const canvas = document.createElement("canvas");
                            const context = canvas.getContext("2d");

                            canvas.width = viewport.width;
                            canvas.height = viewport.height;

                            container.appendChild(canvas);

                            page.render({{
                                canvasContext: context,
                                viewport: viewport
                            }});
                        }});
                    }}
                }});
            </script>
        </body>
        </html>
    """

    st.components.v1.html(pdf_viewer, height=750, scrolling=False)

    # ---------------------- TEXT + FONT ANALYZER ----------------------
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    st.subheader("🔍 PDF Text + Font Details")

    for page_num, page in enumerate(doc, start=1):

        st.markdown(f"## 📄 Page {page_num}")

        text_blocks = page.get_text("dict")["blocks"]
        page_colors = set()
        rows = []

        for block in text_blocks:
            if block['type'] == 0:  # text block
                for line in block["lines"]:
                    for span in line["spans"]:

                        text = span["text"]
                        font = span["font"]
                        size = span["size"]
                        color = span["color"]
                        flags = span["flags"]

                        is_bold = bool(flags & 2)
                        is_italic = bool(flags & 1)
                        is_underlined = bool(flags & 4)

                        r = (color >> 16) & 255
                        g = (color >> 8) & 255
                        b = color & 255

                        page_colors.add((r, g, b))

                        rows.append({
                            "Text": text,
                            "Font": font,
                            "Size": size,
                            "Bold": is_bold,
                            "Italic": is_italic,
                            "Underline": is_underlined,
                            "Color (RGB)": f"({r},{g},{b})"
                        })

        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch")

        st.subheader("🎨 Page Colors")
        cols = st.columns(10)

        for i, (r, g, b) in enumerate(page_colors):
            hex_code = "#{:02x}{:02x}{:02x}".format(r, g, b)
            with cols[i % 10]:
                st.write(hex_code)
                st.markdown(
                    f"<div style='width:40px;height:40px;border-radius:5px;background:{hex_code}'></div>",
                    unsafe_allow_html=True
                )