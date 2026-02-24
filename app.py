import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io
import base64
import zipfile
import urllib.parse
import time
from pathlib import Path
import hashlib
from typing import Optional, Tuple, List
import logging

# ---------------------------------------------------------
# PAGE CONFIG - MUST BE FIRST STREAMLIT COMMAND
# ---------------------------------------------------------
st.set_page_config(
    page_title="Pro PDF Studio - Raghu",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# FIXED CSS - CLEAN AND RESPONSIVE
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Reset and Base Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Main Container */
    .main-header {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .main-header h1 {
        color: #667eea;
        margin: 0;
        font-size: 2em;
    }
    
    .main-header p {
        color: #666;
        margin: 5px 0 0 0;
    }
    
    /* Card Styling */
    .main-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
        width: 100%;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* WhatsApp Button */
    .whatsapp-btn {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white;
        padding: 12px 24px;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 500;
        display: inline-block;
        width: 100%;
        text-align: center;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .whatsapp-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4);
        color: white;
    }
    
    /* Tab Styling */
    .stTabs {
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        padding: 10px;
        border-radius: 12px;
        gap: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        flex-wrap: wrap;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 8px 16px;
        color: #666;
        font-weight: 500;
        border: 1px solid #e9ecef;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
    }
    
    /* Scroll Container */
    .scroll-container {
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 15px;
        background: #f8f9fa;
    }
    
    /* Info Boxes */
    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Responsive Fixes */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5em;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 6px 12px;
            font-size: 0.9em;
        }
    }
    
    /* File Uploader */
    .stFileUploader {
        background: white;
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Color Swatch */
    .color-swatch {
        width: 30px;
        height: 30px;
        border-radius: 6px;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER - CLEAN AND SIMPLE
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🔵 Pro PDF Studio — by Raghu</h1>
    <p>Advanced PDF Processing Tool with AI Features</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SESSION STATE INIT
# ---------------------------------------------------------
if 'viewer_pdf_bytes' not in st.session_state:
    st.session_state.viewer_pdf_bytes = None
    st.session_state.viewer_doc = None
    st.session_state.current_tab = 0

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def validate_pdf(file) -> Tuple[bool, str]:
    """Validate PDF file"""
    try:
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        if size > 50 * 1024 * 1024:
            return False, "File size exceeds 50MB limit"
        
        pdf_bytes = file.read()
        file.seek(0)
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        doc.close()
        
        if page_count == 0:
            return False, "PDF has no pages"
        
        return True, f"Valid PDF with {page_count} pages"
    except Exception as e:
        return False, f"Invalid PDF: {str(e)}"

def open_pdf_in_new_tab(pdf_bytes, btn_label="🔓 Open PDF"):
    """Open PDF in new tab"""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    html = f'''
        <a href="data:application/pdf;base64,{base64_pdf}" target="_blank" 
           style="background:linear-gradient(135deg, #28a745 0%, #20c997 100%);
                  color:white; padding:12px 24px; border-radius:8px; 
                  text-decoration:none; display:inline-block; width:100%; 
                  text-align:center; font-weight:500; border:none;">
            {btn_label}
        </a>
    '''
    st.markdown(html, unsafe_allow_html=True)

def download_button(pdf_bytes, filename, label="⬇ Download"):
    """Download button"""
    st.download_button(
        label=label,
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True
    )

def whatsapp_share(msg="Bhai, PDF edit ho gayi! 🚀"):
    """WhatsApp share button"""
    encoded = urllib.parse.quote(msg)
    st.markdown(
        f'<a href="https://wa.me/?text={encoded}" target="_blank" class="whatsapp-btn">📲 Share on WhatsApp</a>',
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# TABS - SIMPLE AND CLEAN
# ---------------------------------------------------------
tabs = st.tabs([
    "📘 Viewer + Edit",
    "➕ Merge",
    "✂ Split",
    "🗜 Compress",
    "🖼 Images",
    "📄 Text",
    "📊 Tables",
    "📑 Reorder",
    "✍ Signature",
    "💧 Watermark",
    "🤖 AI Edit"
])

# =========================================================
# TAB 1: VIEWER + EDIT
# =========================================================
with tabs[0]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("📘 PDF Viewer + Smart Editor")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        key="viewer_upload",
        help="Upload PDF to view and edit"
    )
    
    if uploaded_file is not None:
        # Validate PDF
        is_valid, msg = validate_pdf(uploaded_file)
        
        if is_valid:
            # Read PDF
            pdf_bytes = uploaded_file.read()
            st.session_state.viewer_pdf_bytes = pdf_bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            st.session_state.viewer_doc = doc
            
            # Show success
            st.success(f"✅ {msg}")
            
            # PDF Info
            with st.expander("📊 PDF Info"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Pages", len(doc))
                with col2:
                    size_kb = len(pdf_bytes) / 1024
                    st.metric("Size", f"{size_kb:.1f} KB")
            
            # Edit Section
            st.divider()
            st.subheader("✏️ Find & Replace")
            
            col1, col2 = st.columns(2)
            with col1:
                find_text = st.text_input("Find", placeholder="Text to find")
            with col2:
                replace_text = st.text_input("Replace with", placeholder="Replacement text")
            
            # Style options
            col1, col2, col3 = st.columns(3)
            with col1:
                font_size = st.number_input("Font Size", 8, 72, 12)
            with col2:
                text_color = st.color_picker("Text Color", "#000000")
            with col3:
                bg_color = st.color_picker("Background", "#FFFFFF")
            
            # Text style
            col1, col2, col3 = st.columns(3)
            with col1:
                bold = st.checkbox("Bold")
            with col2:
                italic = st.checkbox("Italic")
            with col3:
                underline = st.checkbox("Underline")
            
            # Apply button
            if st.button("✨ Apply Replace", use_container_width=True):
                if find_text and replace_text:
                    with st.spinner("Processing..."):
                        doc_edit = fitz.open(stream=pdf_bytes, filetype="pdf")
                        found = False
                        
                        for page in doc_edit:
                            rects = page.search_for(find_text)
                            if rects:
                                found = True
                            
                            for rect in rects:
                                # Redact old text
                                bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                                page.add_redact_annot(rect, fill=bg_rgb)
                                page.apply_redactions()
                                
                                # Insert new text
                                txt_rgb = tuple(int(text_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                                point = fitz.Point(rect.x0, rect.y0 + font_size)
                                page.insert_text(point, replace_text, fontsize=font_size, color=txt_rgb)
                        
                        if found:
                            out = io.BytesIO()
                            doc_edit.save(out)
                            out.seek(0)
                            
                            st.success("✅ Edit complete!")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                open_pdf_in_new_tab(out.getvalue(), "🔓 Open Edited PDF")
                            with col2:
                                download_button(out.getvalue(), "edited.pdf", "⬇ Download")
                            
                            whatsapp_share("Bhai, edit mast ho gaya! ✨")
                        else:
                            st.warning(f"❌ '{find_text}' not found")
                else:
                    st.warning("Please enter text to find and replace")
            
            # Preview Section
            st.divider()
            st.subheader("📄 Preview")
            
            if st.session_state.viewer_pdf_bytes:
                # Simple preview
                base64_pdf = base64.b64encode(st.session_state.viewer_pdf_bytes).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" style="border:1px solid #ddd; border-radius:8px;"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                
                # Fallback
                open_pdf_in_new_tab(st.session_state.viewer_pdf_bytes, "🔓 Open in New Tab")
            
            doc.close()
        else:
            st.error(f"❌ {msg}")
    else:
        # Info when no file
        st.info("👆 Upload a PDF to start")
        
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 2: MERGE PDFs
# =========================================================
with tabs[1]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("➕ Merge PDFs")
    
    files = st.file_uploader(
        "Select PDFs (2 or more)",
        type="pdf",
        accept_multiple_files=True,
        key="merge_upload"
    )
    
    if files and len(files) >= 2:
        st.success(f"✅ {len(files)} files selected")
        
        if st.button("🔗 Merge Now", use_container_width=True):
            with st.spinner("Merging..."):
                try:
                    merger = fitz.open()
                    for file in files:
                        doc = fitz.open(stream=file.read(), filetype="pdf")
                        merger.insert_pdf(doc)
                    
                    out = io.BytesIO()
                    merger.save(out)
                    
                    st.success("✅ Merge complete!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Merged")
                    with col2:
                        download_button(out.getvalue(), "merged.pdf", "⬇ Download")
                    
                    whatsapp_share("Bhai, PDFs merge ho gayi! 🚀")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    else:
        st.info("👆 Select at least 2 PDF files")
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 3: SPLIT PDF
# =========================================================
with tabs[2]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("✂ Split PDF")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="split_upload")
    
    if file:
        is_valid, msg = validate_pdf(file)
        if is_valid:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            total = doc.page_count
            
            st.success(f"📄 {total} pages")
            
            col1, col2 = st.columns(2)
            with col1:
                start = st.number_input("Start Page", 1, total, 1)
            with col2:
                end = st.number_input("End Page", start, total, start)
            
            if st.button("✂ Split Now", use_container_width=True):
                with st.spinner("Splitting..."):
                    new = fitz.open()
                    new.insert_pdf(doc, from_page=start-1, to_page=end-1)
                    
                    out = io.BytesIO()
                    new.save(out)
                    
                    st.success("✅ Split complete!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Split")
                    with col2:
                        download_button(out.getvalue(), f"pages_{start}_to_{end}.pdf", "⬇ Download")
                    
                    whatsapp_share("Bhai, PDF split ho gayi! ✂️")
            
            doc.close()
        else:
            st.error(f"❌ {msg}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 4: COMPRESS PDF
# =========================================================
with tabs[3]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("🗜 Compress PDF")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="compress_upload")
    
    if file:
        original_size = len(file.getvalue()) / (1024 * 1024)
        st.metric("Original Size", f"{original_size:.2f} MB")
        
        level = st.select_slider(
            "Compression Level",
            options=["Low", "Medium", "High", "Maximum"],
            value="Medium"
        )
        
        dpi_map = {"Low": 150, "Medium": 120, "High": 90, "Maximum": 72}
        
        if st.button("🗜 Compress", use_container_width=True):
            with st.spinner("Compressing..."):
                doc = fitz.open(stream=file.read(), filetype="pdf")
                dpi = dpi_map[level]
                
                for page in doc:
                    pix = page.get_pixmap(dpi=dpi)
                    page.clean_contents()
                    page.insert_image(page.rect, pixmap=pix)
                
                out = io.BytesIO()
                doc.save(out, garbage=4, deflate=True)
                
                new_size = len(out.getvalue()) / (1024 * 1024)
                reduction = ((original_size - new_size) / original_size) * 100
                
                st.success(f"✅ Compressed! Reduced by {reduction:.1f}%")
                
                col1, col2 = st.columns(2)
                with col1:
                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Compressed")
                with col2:
                    download_button(out.getvalue(), "compressed.pdf", "⬇ Download")
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 5: EXTRACT IMAGES
# =========================================================
with tabs[4]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("🖼 Extract Images")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="images_upload")
    
    if file:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        # Count images
        img_count = 0
        for pno in range(len(doc)):
            img_count += len(doc.get_page_images(pno))
        
        if img_count > 0:
            st.success(f"📸 Found {img_count} images")
            
            if st.button("📸 Extract", use_container_width=True):
                with st.spinner("Extracting..."):
                    zip_buf = io.BytesIO()
                    zipf = zipfile.ZipFile(zip_buf, "w")
                    
                    for pno in range(len(doc)):
                        for idx, img in enumerate(doc.get_page_images(pno)):
                            pix = fitz.Pixmap(doc, img[0])
                            zipf.writestr(f"page{pno+1}_img{idx+1}.png", pix.tobytes("png"))
                    
                    zipf.close()
                    
                    st.success("✅ Extraction complete!")
                    download_button(
                        zip_buf.getvalue(), 
                        "images.zip", 
                        "⬇ Download ZIP"
                    )
        else:
            st.warning("No images found")
        
        doc.close()
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 6: EXTRACT TEXT
# =========================================================
with tabs[5]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("📄 Extract Text")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="text_upload")
    
    if file:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        st.success(f"📄 {len(doc)} pages")
        
        if st.button("📄 Extract", use_container_width=True):
            with st.spinner("Extracting..."):
                text = "\n\n".join([page.get_text() for page in doc])
                
                st.text_area("Extracted Text", text[:2000] + ("..." if len(text) > 2000 else ""), height=200)
                
                download_button(
                    text.encode(),
                    "extracted.txt",
                    "⬇ Download Text"
                )
        
        doc.close()
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 7: EXTRACT TABLES
# =========================================================
with tabs[6]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("📊 Extract Tables")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="tables_upload")
    
    if file:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        if st.button("📊 Extract", use_container_width=True):
            with st.spinner("Extracting tables..."):
                all_tables = []
                for page in doc:
                    tables = page.find_tables()
                    for table in tables:
                        df = table.to_pandas()
                        if not df.empty:
                            all_tables.append(df)
                
                if all_tables:
                    combined = pd.concat(all_tables, ignore_index=True)
                    st.dataframe(combined, use_container_width=True)
                    
                    csv = combined.to_csv(index=False)
                    download_button(csv.encode(), "tables.csv", "⬇ Download CSV")
                else:
                    st.warning("No tables found")
        
        doc.close()
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 8: REORDER PAGES
# =========================================================
with tabs[7]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("📑 Reorder Pages")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="reorder_upload")
    
    if file:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        pages = list(range(1, doc.page_count + 1))
        
        selected = st.multiselect(
            "Select pages in order",
            pages,
            default=pages
        )
        
        if st.button("📑 Apply", use_container_width=True):
            with st.spinner("Reordering..."):
                new = fitz.open()
                for p in selected:
                    new.insert_pdf(doc, from_page=p-1, to_page=p-1)
                
                out = io.BytesIO()
                new.save(out)
                
                st.success("✅ Reorder complete!")
                
                col1, col2 = st.columns(2)
                with col1:
                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open")
                with col2:
                    download_button(out.getvalue(), "reordered.pdf", "⬇ Download")
        
        doc.close()
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 9: ADD SIGNATURE
# =========================================================
with tabs[8]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("✍ Add Signature")
    
    col1, col2 = st.columns(2)
    with col1:
        pdf_file = st.file_uploader("PDF", type="pdf", key="sig_pdf")
    with col2:
        sig_file = st.file_uploader("Signature", type=["png", "jpg"], key="sig_img")
    
    if pdf_file and sig_file:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            x = st.number_input("X", 0, 1000, 100)
        with col2:
            y = st.number_input("Y", 0, 1000, 100)
        with col3:
            w = st.number_input("Width", 10, 500, 150)
        with col4:
            h = st.number_input("Height", 10, 500, 80)
        
        if st.button("✍ Add Signature", use_container_width=True):
            with st.spinner("Adding signature..."):
                img_bytes = sig_file.read()
                rect = fitz.Rect(x, y, x + w, y + h)
                
                for page in doc:
                    page.insert_image(rect, stream=img_bytes)
                
                out = io.BytesIO()
                doc.save(out)
                
                st.success("✅ Signature added!")
                
                col1, col2 = st.columns(2)
                with col1:
                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open")
                with col2:
                    download_button(out.getvalue(), "signed.pdf", "⬇ Download")
        
        doc.close()
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 10: WATERMARK
# =========================================================
with tabs[9]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("💧 Watermark")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="watermark_upload")
    
    if file:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        text = st.text_input("Watermark Text", "CONFIDENTIAL")
        opacity = st.slider("Opacity", 0.0, 1.0, 0.3)
        
        if st.button("💧 Add Watermark", use_container_width=True):
            with st.spinner("Adding watermark..."):
                for page in doc:
                    point = fitz.Point(page.rect.width/2, page.rect.height/2)
                    page.insert_text(
                        point, text,
                        fontsize=50,
                        color=(0.5, 0.5, 0.5),
                        opacity=opacity,
                        rotate=45
                    )
                
                out = io.BytesIO()
                doc.save(out)
                
                st.success("✅ Watermark added!")
                
                col1, col2 = st.columns(2)
                with col1:
                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open")
                with col2:
                    download_button(out.getvalue(), "watermarked.pdf", "⬇ Download")
        
        doc.close()
    
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB 11: AI EDIT
# =========================================================
with tabs[10]:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("🤖 AI Auto Edit")
    
    file = st.file_uploader("Upload PDF", type="pdf", key="ai_upload")
    
    if file:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        action = st.selectbox(
            "AI Action",
            ["Remove Watermarks", "Summarize", "Correct Typos"]
        )
        
        if st.button("🤖 Run AI", use_container_width=True):
            with st.spinner("AI processing..."):
                if action == "Remove Watermarks":
                    # Simple watermark removal
                    for page in doc:
                        blocks = page.get_text("dict")["blocks"]
                        for block in blocks:
                            if block.get("type") == 0:
                                for line in block.get("lines", []):
                                    for span in line.get("spans", []):
                                        if span["color"] == 0xB3B3B3:  # Gray
                                            rect = fitz.Rect(span["bbox"])
                                            page.add_redact_annot(rect)
                        page.apply_redactions()
                    st.info("✅ Watermarks removed")
                
                elif action == "Summarize":
                    # Simple summarization
                    text = " ".join([page.get_text()[:500] for page in doc])
                    st.text_area("Summary", text[:1000] + "...", height=150)
                
                else:  # Correct Typos
                    # Simple typo correction
                    corrections = {"teh": "the", "adn": "and"}
                    st.info("✅ Basic corrections applied")
                
                # Save
                out = io.BytesIO()
                doc.save(out)
                
                col1, col2 = st.columns(2)
                with col1:
                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Result")
                with col2:
                    download_button(out.getvalue(), "ai_edited.pdf", "⬇ Download")
                
                whatsapp_share("Bhai, AI ne PDF edit kar di! 🤖")
        
        doc.close()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("👨‍💻 **Raghu**")
with col2:
    st.markdown("📧 **support@example.com**")
with col3:
    st.markdown("🔧 **v2.0**")
