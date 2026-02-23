import streamlit as st
import fitz
import pandas as pd
import io
import base64
import zipfile
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Pro AI PDF Editor - Raghu",
    layout="wide",
)

# ---------------------------------------------------------
# MINIMAL CLEAN UI CSS
# ---------------------------------------------------------
st.markdown("""
<style>
body {
    background: #eef5ff;
    font-family: 'Inter', sans-serif;
}

.main-card {
    background: white;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.10);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#003d8f;'>🔵 Pro PDF Studio — by Raghu</h1>", unsafe_allow_html=True)
st.write("")

# ---------------------------------------------------------
# TAB SETUP (Top Tabs)
# ---------------------------------------------------------
tabs = st.tabs([
    "📘 Viewer + Smart Edit",
    "➕ Merge PDFs",
    "✂ Split PDF",
    "🗜 Compress PDF",
    "🖼 Extract Images",
    "📄 Extract Text",
    "📊 Extract Tables",
    "📑 Reorder / Delete Pages",
    "✍ Add Signature",
    "💧 Watermark Tools",
    "🤖 AI Auto Edit"
])
# =========================================================
# 📘 TAB 1 — VIEWER + SMART EDITOR
# =========================================================
with tabs[0]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)

    st.subheader("📘 PDF Viewer + Smart Editor")

    uploaded_file = st.file_uploader("📂 Upload PDF", type=["pdf"])

    # --------------------------- FUNCTION: OPEN PDF IN NEW TAB
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
        <button onclick="openPDF()" style="
            background:#005ce6;color:white;padding:10px 20px;
            border:none;border-radius:6px;font-weight:700;cursor:pointer;">
            🔓 Open Edited PDF
        </button>
        """
        st.components.v1.html(js_code, height=120)

    # --------------------------- FUNCTION: DEEP COLOR SCAN
    def get_deep_page_colors(page):
        colors = set()
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        c = s["color"]
                        colors.add(
                            "#{:02x}{:02x}{:02x}".format((c>>16)&255,(c>>8)&255,c&255)
                        )

        for draw in page.get_drawings():
            if "fill" in draw and draw["fill"]:
                c = draw["fill"]
                colors.add("#{0:02x}{1:02x}{2:02x}".format(
                    int(c[0]*255),int(c[1]*255),int(c[2]*255)
                ))
        return colors

    # --------------------------- MAIN LOGIC
    if uploaded_file:
        pdf_bytes = uploaded_file.read()

        st.divider()
        st.subheader("📝 Smart Edit Controls")

        col1, col2 = st.columns(2)
        find_txt = col1.text_input("Find Text")
        replace_txt = col2.text_input("Replace With")

        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        font_library = {
            "Helvetica": "helv",
            "Times": "tiro",
            "Courier": "cour",
            "Symbol": "symb",
            "ZapfDingbats": "zadi"
        }

        selected_font = c1.selectbox("Font Theme", list(font_library.keys()))
        font_style = font_library[selected_font]

        f_size = c2.number_input("Font Size", value=0.0, step=0.5)
        t_color = c3.color_picker("Text Color", "#000000")
        bg_color = c4.color_picker("Background Color", "#FFFFFF")

        s1, s2, s3 = st.columns(3)
        is_bold = s1.checkbox("Bold")
        is_italic = s2.checkbox("Italic")
        is_underline = s3.checkbox("Underline")

        # ---------------- APPLY TRANSFORMATION ----------------
        if st.button("✨ Apply Smart Replace", use_container_width=True):
            doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
            found = False

            # FONT STYLE CALC
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

                    # BACKGROUND PATCH
                    bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255
                                   for i in (0, 2, 4))
                    page.add_redact_annot(rect, fill=bg_rgb)
                    page.apply_redactions()

                    # TEXT INSERT
                    fs = f_size if f_size > 0 else (rect.y1 - rect.y0) - 1
                    txt_rgb = tuple(int(t_color.lstrip('#')[i:i+2],16)/255
                                    for i in (0,2,4))

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
                st.success("🎉 Edit Complete!")
                open_pdf_in_new_tab(out.getvalue())
            else:
                st.error("❌ Text not found.")

        st.divider()

        # --------------------------- PDF VIEWER SECTION
        st.subheader("📄 PDF Preview")
        zoom = st.slider("🔍 Zoom", 50, 250, 120)

        base64_pdf = base64.b64encode(pdf_bytes).decode()
        viewer_html = f"""
            <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
            <div id="pdf_container" style="height:520px; overflow-y:scroll;
                background:white; padding:12px; border-radius:14px;"></div>
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

        # --------------------------- ANALYZER TABLE SECTION
        st.subheader("🎨 Deep Color & Font Analyzer")

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        for pageno, page in enumerate(doc, start=1):
            st.write(f"### 📄 Page {pageno}")

            all_colors = get_deep_page_colors(page)
            color_cols = st.columns(12)

            for i, color in enumerate(all_colors):
                with color_cols[i % 12]:
                    st.markdown(
                        f"<div style='width:28px;height:28px;"
                        f"border-radius:5px;background:{color};"
                        f"border:1px solid #003d8f;'></div>",
                        unsafe_allow_html=True
                    )
                    st.caption(color)

            rows = []
            for b in page.get_text("dict")["blocks"]:
                if b['type'] == 0:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            c = s["color"]
                            hex_c = "#{:02x}{:02x}{:02x}".format(
                                (c>>16)&255, (c>>8)&255, c&255
                            )
                            rows.append({
                                "Text": s["text"],
                                "Font": s["font"],
                                "Size": round(s["size"], 2),
                                "Color": hex_c
                            })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
    # =========================================================
# 📦 TAB 2 — MERGE PDFs
# =========================================================
with tabs[1]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📦 Merge Multiple PDFs")

    merge_files = st.file_uploader("Select 2 or more PDFs", type=["pdf"], accept_multiple_files=True)

    if merge_files and len(merge_files) >= 2:
        if st.button("🔗 Merge PDFs", use_container_width=True):
            merger = fitz.open()

            for pdf in merge_files:
                doc_temp = fitz.open(stream=pdf.read(), filetype="pdf")
                merger.insert_pdf(doc_temp)

            out = io.BytesIO()
            merger.save(out)
            st.success("🎉 PDFs Merged Successfully!")
            st.download_button("⬇ Download Merged PDF", out.getvalue(), "merged.pdf")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# ✂ TAB 3 — SPLIT PDF
# =========================================================
with tabs[2]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("✂ Split PDF by Page Range")

    split_pdf = st.file_uploader("Upload PDF to Split", type=["pdf"])
    start = st.number_input("Start Page", min_value=1, value=1)
    end = st.number_input("End Page", min_value=1, value=1)

    if split_pdf:
        if st.button("✂ Split Now", use_container_width=True):
            doc = fitz.open(stream=split_pdf.read(), filetype="pdf")
            new = fitz.open()

            for p in range(start-1, min(end, doc.page_count)):
                new.insert_pdf(doc, from_page=p, to_page=p)

            out = io.BytesIO()
            new.save(out)
            st.success("🎉 Split Successful!")
            st.download_button("⬇ Download Split PDF", out.getvalue(), "split.pdf")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 🗜 TAB 4 — COMPRESS PDF
# =========================================================
with tabs[3]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🗜 Compress PDF")

    comp_pdf = st.file_uploader("Upload PDF to Compress", type=["pdf"])
    level = st.radio("Compression Level", ["Low", "Medium", "High"], horizontal=True)

    quality_map = {"Low": 70, "Medium": 40, "High": 20}

    if comp_pdf:
        if st.button("🗜 Compress Now", use_container_width=True):
            doc = fitz.open(stream=comp_pdf.read(), filetype="pdf")

            for page in doc:
                pix = page.get_pixmap(dpi=quality_map[level])
                page.clean_contents()
                page.insert_image(page.rect, pixmap=pix)

            out = io.BytesIO()
            doc.save(out)

            st.success("🎉 Compression Successful!")
            st.download_button("⬇ Download Compressed PDF", out.getvalue(), "compressed.pdf")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 🖼 TAB 5 — EXTRACT IMAGES
# =========================================================
with tabs[4]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🖼 Extract Images from PDF")

    img_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if img_pdf:
        if st.button("📸 Extract Images", use_container_width=True):
            doc = fitz.open(stream=img_pdf.read(), filetype="pdf")
            zip_buffer = io.BytesIO()
            import zipfile
            zipf = zipfile.ZipFile(zip_buffer, "w")

            img_count = 0
            for page_no in range(len(doc)):
                for img in doc.get_page_images(page_no):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    img_bytes = pix.tobytes("png")
                    zipf.writestr(f"image_{page_no+1}_{img_count}.png", img_bytes)
                    img_count += 1

            zipf.close()
            st.success(f"🎉 Extracted {img_count} images!")
            st.download_button("⬇ Download Images ZIP", zip_buffer.getvalue(), "images.zip")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 📄 TAB 6 — EXTRACT TEXT
# =========================================================
with tabs[5]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📄 Extract Text")

    txt_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if txt_pdf:
        doc = fitz.open(stream=txt_pdf.read(), filetype="pdf")
        all_text = ""

        for page in doc:
            all_text += page.get_text() + "\n\n"

        st.text_area("📄 Extracted Text", all_text, height=300)

        st.download_button("⬇ Download Text File", all_text, "text.txt")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 📊 TAB 7 — EXTRACT TABLES
# =========================================================
with tabs[6]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📊 Extract Tables from PDF")

    table_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if table_pdf:
        doc = fitz.open(stream=table_pdf.read(), filetype="pdf")
        rows = []

        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b["type"] == 0:
                    for l in b["lines"]:
                        row_text = " ".join([span["text"] for span in l["spans"]])
                        rows.append([row_text])

        df = pd.DataFrame(rows, columns=["Extracted Data"])
        st.dataframe(df, use_container_width=True)

        st.download_button("⬇ Download CSV", df.to_csv(index=False).encode(), "table.csv")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 📑 TAB 8 — REORDER / DELETE PAGES
# =========================================================
with tabs[7]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📑 Reorder or Delete Pages")

    reorder_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if reorder_pdf:
        doc = fitz.open(stream=reorder_pdf.read(), filetype="pdf")
        pages = list(range(1, doc.page_count + 1))

        selected = st.multiselect("Select pages (order = final order)", pages)

        if st.button("📑 Apply Changes", use_container_width=True):
            new = fitz.open()
            for p in selected:
                new.insert_pdf(doc, from_page=p-1, to_page=p-1)

            out = io.BytesIO()
            new.save(out)

            st.success("🎉 Pages Updated!")
            st.download_button("⬇ Download Updated PDF", out.getvalue(), "updated.pdf")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# ✍ TAB 9 — SIGNATURE
# =========================================================
with tabs[8]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("✍ Add Signature")

    sig_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    sig_img = st.file_uploader("Upload Signature Image", type=["png", "jpg"])

    x = st.number_input("X Position", min_value=0, value=50)
    y = st.number_input("Y Position", min_value=0, value=50)
    w = st.number_input("Width", min_value=50, value=120)

    if sig_pdf and sig_img:
        if st.button("✍ Apply Signature", use_container_width=True):
            doc = fitz.open(stream=sig_pdf.read(), filetype="pdf")
            img_bytes = sig_img.read()

            for page in doc:
                page.insert_image(page.rect, stream=img_bytes, keep_proportion=True, x=x, y=y, width=w)

            out = io.BytesIO()
            doc.save(out)
            st.success("🎉 Signature Added!")
            st.download_button("⬇ Download Signed PDF", out.getvalue(), "signed.pdf")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 💧 TAB 10 — WATERMARK
# =========================================================
with tabs[9]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("💧 Watermark")

    wm_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    wm_text = st.text_input("Text Watermark (optional)")
    wm_img = st.file_uploader("Image Watermark", type=["png", "jpg"])

    if wm_pdf:
        if st.button("💧 Apply Watermark", use_container_width=True):
            doc = fitz.open(stream=wm_pdf.read(), filetype="pdf")

            for page in doc:
                if wm_text:
                    page.insert_text(
                        fitz.Point(50, 50),
                        wm_text,
                        fontsize=50,
                        rotate=45,
                        color=(0.7, 0.7, 0.7)
                    )

                if wm_img:
                    img_bytes = wm_img.read()
                    page.insert_image(page.rect, stream=img_bytes, opacity=0.3)

            out = io.BytesIO()
            doc.save(out)
            st.success("🎉 Watermark Added!")
            st.download_button("⬇ Download", out.getvalue(), "watermarked.pdf")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 🤖 TAB 11 — AI AUTO EDIT MODE
# =========================================================
with tabs[10]:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🤖 AI Auto Edit (Natural Language Commands)")

    ai_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    ai_cmd = st.text_area("Enter command (simple English)", placeholder="Remove name 'Amit' from all pages...")

    if ai_pdf and ai_cmd:
        if st.button("🤖 Run AI Edit", use_container_width=True):

            doc = fitz.open(stream=ai_pdf.read(), filetype="pdf")

            # Very basic rule-based AI engine
            if "remove" in ai_cmd.lower():
                word = ai_cmd.lower().replace("remove", "").strip()

                for page in doc:
                    areas = page.search_for(word)
                    for r in areas:
                        page.add_redact_annot(r, fill=(1, 1, 1))
                        page.apply_redactions()

            out = io.BytesIO()
            doc.save(out)

            st.success("🎉 AI Edit Complete!")
            st.download_button("⬇ Download Edited PDF", out.getvalue(), "ai_edited.pdf")

    st.markdown("</div>", unsafe_allow_html=True)
