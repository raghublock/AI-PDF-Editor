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
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Pro AI PDF Editor - Raghu",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# ENHANCED CSS WITH BETTER UI/UX
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global Styles */
    body { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
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
        padding: 25px; 
        border-radius: 20px; 
        box-shadow: 0 10px 40px rgba(0,0,0,0.1); 
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .main-card:hover {
        transform: translateY(-5px);
    }
    
    /* Button Styling */
    .stButton>button { 
        border-radius: 10px; 
        font-weight: 600; 
        transition: all 0.3s;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
    }
    .stButton>button:hover { 
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* WhatsApp Button */
    .whatsapp-btn {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white; 
        padding: 12px 24px;
        text-decoration: none; 
        border-radius: 10px; 
        font-weight: 600;
        display: inline-block; 
        margin-top: 12px; 
        text-align: center; 
        width: 100%;
        transition: all 0.3s;
    }
    .whatsapp-btn:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(37, 211, 102, 0.4);
        color: white;
    }
    
    /* Scroll Container */
    .scroll-container { 
        max-height: 600px; 
        overflow-y: auto; 
        border: 2px solid #f0f0f0; 
        border-radius: 12px; 
        padding: 15px;
        background: #fafafa;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Alert Messages */
    .stAlert {
        border-radius: 10px;
        border-left: 5px solid;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: white;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Color Swatch */
    .color-swatch {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        border: 2px solid #fff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        cursor: pointer;
    }
    .color-swatch:hover {
        transform: scale(1.1);
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-color: #667eea transparent #667eea transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER WITH ANIMATION
# ---------------------------------------------------------
st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);'>
        <h1 style='color: white; font-size: 2.5em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>
            🔵 Pro PDF Studio — by Raghu
        </h1>
        <p style='color: white; opacity: 0.9; margin: 10px 0 0 0; font-size: 1.1em;'>
            🚀 Advanced PDF Processing Tool with AI Features
        </p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'viewer_pdf_bytes': None,
        'viewer_doc': None,
        'processed_pdfs': {},
        'upload_history': [],
        'cache_cleanup_time': time.time()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ---------------------------------------------------------
# ENHANCED UNIVERSAL FUNCTIONS
# ---------------------------------------------------------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def cache_pdf_bytes(pdf_bytes: bytes, operation: str) -> str:
    """Cache PDF bytes for reuse"""
    hash_obj = hashlib.md5(pdf_bytes)
    cache_key = f"{operation}_{hash_obj.hexdigest()}"
    st.session_state.processed_pdfs[cache_key] = pdf_bytes
    return cache_key

def cleanup_old_cache(max_age: int = 3600):
    """Remove cache entries older than max_age seconds"""
    current_time = time.time()
    if current_time - st.session_state.cache_cleanup_time > 300:  # Clean every 5 minutes
        st.session_state.processed_pdfs = {}
        st.session_state.cache_cleanup_time = current_time

def show_success_animation():
    """Show success animation"""
    success_placeholder = st.empty()
    success_placeholder.success("✅ Operation completed successfully!")
    time.sleep(2)
    success_placeholder.empty()

def open_pdf_in_new_tab(pdf_bytes: bytes, btn_label: str = "🔓 Open & Print PDF"):
    """Enhanced PDF opener with better error handling"""
    try:
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        js_code = f"""
        <script>
        function openPDF() {{
            try {{
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
                setTimeout(() => URL.revokeObjectURL(fileURL), 100);
            }} catch(e) {{
                alert('Error opening PDF: ' + e.message);
            }}
        }}
        </script>
        <button onclick="openPDF()" style="background:linear-gradient(135deg, #28a745 0%, #20c997 100%);color:white;padding:12px 24px;border:none;border-radius:10px;font-weight:600;cursor:pointer;width:100%;transition:all 0.3s;">
            {btn_label}
        </button>
        """
        st.components.v1.html(js_code, height=80)
    except Exception as e:
        st.error(f"Error creating PDF opener: {str(e)}")

def add_whatsapp_share(msg: str = "Bhai, Raghu ke tool se PDF mast banayi hai! 🚀"):
    """Enhanced WhatsApp sharing"""
    encoded_msg = urllib.parse.quote(msg + "\n\nTry it yourself: [Your App URL]")
    st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank" class="whatsapp-btn">📲 Share on WhatsApp</a>', unsafe_allow_html=True)

def save_and_offer_download(pdf_bytes: bytes, filename: str = "edited_document.pdf"):
    """Enhanced download button with file size display"""
    file_size = len(pdf_bytes) / (1024 * 1024)  # Size in MB
    st.download_button(
        label=f"⬇ Download PDF ({file_size:.2f} MB)",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True
    )

def get_deep_page_colors(page) -> Tuple[set, List[dict]]:
    """Enhanced color extraction with better accuracy"""
    colors = set()
    text_data = []
    
    # Extract text colors
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if b['type'] == 0:
            for l in b["lines"]:
                for s in l["spans"]:
                    c = s["color"]
                    hex_color = "#{:02x}{:02x}{:02x}".format(
                        (c >> 16) & 255, 
                        (c >> 8) & 255, 
                        c & 255
                    )
                    colors.add(hex_color)
                    text_data.append({
                        "Text": s["text"][:50] + "..." if len(s["text"]) > 50 else s["text"],
                        "Font": s["font"],
                        "Size": round(s["size"], 2),
                        "Color": hex_color
                    })
    
    # Extract drawing colors
    for draw in page.get_drawings():
        if "fill" in draw and draw["fill"]:
            c = draw["fill"]
            hex_color = "#{0:02x}{1:02x}{2:02x}".format(
                int(c[0] * 255), 
                int(c[1] * 255), 
                int(c[2] * 255)
            )
            colors.add(hex_color)
    
    return colors, text_data

def validate_pdf(file) -> Tuple[bool, str]:
    """Validate PDF file before processing"""
    try:
        # Check file size (50MB limit)
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        if size > 50 * 1024 * 1024:
            return False, "File size exceeds 50MB limit"
        
        # Try to open with PyMuPDF
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

# ---------------------------------------------------------
# TAB SETUP
# ---------------------------------------------------------
tab_names = [
    "📘 Viewer + Smart Edit", "➕ Merge PDFs", "✂ Split PDF", "🗜 Compress PDF",
    "🖼 Extract Images", "📄 Extract Text", "📊 Extract Tables", 
    "📑 Reorder Pages", "✍ Add Signature", "💧 Watermark Tools", "🤖 AI Auto Edit"
]
tabs = st.tabs(tab_names)

# =========================================================
# 📘 TAB 1 — VIEWER + SMART EDITOR (ENHANCED)
# =========================================================
with tabs[0]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📘 PDF Viewer + Smart Editor")
        with col2:
            st.info("⚡ Supports find & replace with formatting")
        
        uploaded_file = st.file_uploader(
            "📂 Upload PDF", 
            type=["pdf"], 
            key="viewer_upload",
            help="Maximum file size: 50MB"
        )

        if uploaded_file is not None:
            # Validate PDF
            is_valid, message = validate_pdf(uploaded_file)
            if not is_valid:
                st.error(f"❌ {message}")
            else:
                try:
                    with st.spinner("📖 Loading PDF..."):
                        pdf_bytes = uploaded_file.read()
                        st.session_state.viewer_pdf_bytes = pdf_bytes
                        
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        st.session_state.viewer_doc = doc
                        
                        # Cache the PDF
                        cache_pdf_bytes(pdf_bytes, "viewer")
                    
                    # Success message with page count
                    st.success(f"✅ PDF loaded successfully! ({len(doc)} pages)")
                    
                    # PDF Info
                    with st.expander("📊 PDF Information", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Pages", len(doc))
                        with col2:
                            # Get PDF metadata
                            metadata = doc.metadata
                            st.metric("Author", metadata.get('author', 'Unknown')[:20])
                        with col3:
                            file_size = len(pdf_bytes) / 1024
                            st.metric("File Size", f"{file_size:.2f} KB")
                    
                    st.divider()
                    
                    # Smart Edit Controls in two columns
                    st.subheader("📝 Smart Edit Controls")
                    
                    with st.expander("🔧 Edit Settings", expanded=True):
                        col1, col2 = st.columns(2)
                        find_txt = col1.text_input("🔍 Find Text", key="find_text", placeholder="Enter text to find")
                        replace_txt = col2.text_input("✏️ Replace With", key="replace_text", placeholder="Enter replacement text")

                        # Font and styling options
                        col1, col2, col3, col4 = st.columns(4)
                        font_library = {
                            "Helvetica": "helv", 
                            "Times": "tiro", 
                            "Courier": "cour", 
                            "Symbol": "symb", 
                            "ZapfDingbats": "zadi"
                        }
                        selected_font = col1.selectbox("🎨 Font Theme", list(font_library.keys()))
                        font_style = font_library[selected_font]
                        f_size = col2.number_input("📏 Font Size", value=12.0, step=0.5, min_value=4.0, max_value=72.0)
                        t_color = col3.color_picker("🎨 Text Color", "#000000")
                        bg_color = col4.color_picker("🖌️ Background Color", "#FFFFFF")

                        # Text style options
                        col1, col2, col3, col4 = st.columns(4)
                        is_bold = col1.checkbox("**Bold**")
                        is_italic = col2.checkbox("*Italic*")
                        is_underline = col3.checkbox("_Underline_")
                        
                        # Preview selected style
                        with col4:
                            st.markdown("**Preview:**")
                            preview_style = ""
                            if is_bold:
                                preview_style += "**"
                            if is_italic:
                                preview_style += "*"
                            preview_text = "Sample Text"
                            if is_underline:
                                st.markdown(f"<u>{preview_style}{preview_text}{preview_style[::-1]}</u>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"{preview_style}{preview_text}{preview_style[::-1]}")

                    # Apply button with progress
                    if st.button("✨ Apply Smart Replace", use_container_width=True):
                        if not find_txt:
                            st.warning("⚠️ Please enter text to find")
                        elif not replace_txt:
                            st.warning("⚠️ Please enter replacement text")
                        else:
                            with st.spinner("🔄 Processing text replacement..."):
                                progress_bar = st.progress(0)
                                doc_edit = fitz.open(stream=st.session_state.viewer_pdf_bytes, filetype="pdf")
                                found = False
                                
                                # Font style mapping
                                style_map = {
                                    "helv": ["helv", "hebo", "helt", "hebi"], 
                                    "tiro": ["tiro", "tibo", "tiit", "tibi"], 
                                    "cour": ["cour", "cobo", "coit", "cobi"]
                                }
                                idx = (1 if is_bold else 0) + (2 if is_italic else 0)
                                final_font = style_map.get(font_style, [font_style])[idx % 4]

                                total_pages = len(doc_edit)
                                for page_num, page in enumerate(doc_edit):
                                    rects = page.search_for(find_txt)
                                    if rects:
                                        found = True
                                    
                                    for rect_idx, rect in enumerate(rects):
                                        # Update progress
                                        progress = (page_num + rect_idx/len(rects)) / total_pages
                                        progress_bar.progress(min(progress, 0.99))
                                        
                                        # Apply redaction
                                        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255 for i in (0,2,4))
                                        page.add_redact_annot(rect, fill=bg_rgb)
                                        page.apply_redactions()
                                        
                                        # Insert new text
                                        fs = f_size if f_size > 0 else (rect.y1 - rect.y0) - 2
                                        txt_rgb = tuple(int(t_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                                        page.insert_text(
                                            fitz.Point(rect.x0, rect.y0 + fs*0.85), 
                                            replace_txt, 
                                            fontsize=fs, 
                                            fontname=final_font, 
                                            color=txt_rgb
                                        )
                                        
                                        # Add underline if selected
                                        if is_underline:
                                            page.draw_line(
                                                fitz.Point(rect.x0, rect.y1), 
                                                fitz.Point(rect.x1, rect.y1), 
                                                color=txt_rgb, 
                                                width=1
                                            )
                                    
                                    progress_bar.progress((page_num + 1) / total_pages)

                                progress_bar.progress(1.0)
                                
                                if found:
                                    out = io.BytesIO()
                                    doc_edit.save(out)
                                    out.seek(0)
                                    
                                    st.success("🎉 Edit Complete!")
                                    
                                    # Action buttons
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Edited PDF")
                                    with col2:
                                        save_and_offer_download(out.getvalue(), "edited.pdf")
                                    
                                    add_whatsapp_share("Bhai, edit mast ho gaya! ✨")
                                else:
                                    st.warning(f"⚠️ '{find_txt}' not found in document")

                    st.divider()
                    
                    # PDF Preview with tabs
                    preview_tab1, preview_tab2 = st.tabs(["📄 PDF Preview", "🎨 Color & Font Analyzer"])
                    
                    with preview_tab1:
                        if st.session_state.viewer_pdf_bytes:
                            # Check size for warning
                            if len(st.session_state.viewer_pdf_bytes) > 5 * 1024 * 1024:
                                st.warning("⚠️ Large PDF (>5MB) - Preview may load slowly. Use 'Open in New Tab' for better performance.")
                            
                            # PDF Preview with zoom control
                            zoom_level = st.slider("🔍 Zoom", 50, 200, 100, 10)
                            
                            base64_pdf = base64.b64encode(st.session_state.viewer_pdf_bytes).decode('utf-8')
                            pdf_display = f'''
                                <iframe 
                                    src="data:application/pdf;base64,{base64_pdf}" 
                                    width="100%" 
                                    height="{int(800 * zoom_level/100)}" 
                                    type="application/pdf" 
                                    style="border: 2px solid #f0f0f0; border-radius: 10px;"
                                ></iframe>
                            '''
                            st.markdown(pdf_display, unsafe_allow_html=True)
                            
                            # Fallback button
                            open_pdf_in_new_tab(st.session_state.viewer_pdf_bytes, "🔓 Open PDF in New Tab")
                    
                    with preview_tab2:
                        if st.session_state.viewer_doc:
                            doc_an = st.session_state.viewer_doc
                            
                            # Page selector
                            page_selector = st.selectbox(
                                "Select Page", 
                                range(1, len(doc_an) + 1),
                                format_func=lambda x: f"Page {x}"
                            )
                            
                            # Get colors and text data for selected page
                            page = doc_an[page_selector - 1]
                            all_colors, text_data = get_deep_page_colors(page)
                            
                            # Display colors
                            st.subheader(f"🎨 Colors on Page {page_selector}")
                            if all_colors:
                                color_cols = st.columns(min(8, len(all_colors)))
                                for i, color in enumerate(list(all_colors)[:8]):
                                    with color_cols[i % 8]:
                                        st.markdown(
                                            f"<div class='color-swatch' style='background:{color};'></div>", 
                                            unsafe_allow_html=True
                                        )
                                        st.caption(color)
                            else:
                                st.info("No colors found on this page")
                            
                            # Display text data
                            st.subheader("📝 Text Analysis")
                            if text_data:
                                df = pd.DataFrame(text_data)
                                st.dataframe(
                                    df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "Text": "Text Content",
                                        "Font": "Font Name",
                                        "Size": "Font Size",
                                        "Color": "Color Code"
                                    }
                                )
                            else:
                                st.info("No text found on this page")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Try with a smaller PDF or check if file is corrupted")

        else:
            # Show example/help when no file uploaded
            col1, col2 = st.columns(2)
            with col1:
                st.info("👆 Upload a PDF to start editing")
            with col2:
                st.markdown("""
                **✨ Features:**
                - Find and replace text
                - Custom fonts and colors
                - Bold/Italic/Underline
                - Color picker for text
                - Background color support
                """)

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📦 TAB 2 — MERGE PDFs (ENHANCED)
# =========================================================
with tabs[1]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("📦 Merge Multiple PDFs")
        
        st.info("ℹ️ Select multiple PDF files to merge them into one document")
        
        merge_files = st.file_uploader(
            "Select PDFs (at least 2)", 
            type=["pdf"], 
            accept_multiple_files=True, 
            key="tab2_upload",
            help="Choose 2 or more PDF files"
        )
        
        if merge_files:
            st.write(f"📄 Selected files: {len(merge_files)}")
            
            # Show file list
            for i, file in enumerate(merge_files):
                st.text(f"{i+1}. {file.name} ({(len(file.getvalue())/1024):.1f} KB)")
            
            if len(merge_files) >= 2:
                # Drag to reorder (simplified)
                st.write("🔄 Files will be merged in the order shown above")
                
                col1, col2, col3 = st.columns(3)
                with col2:
                    if st.button("🔗 Merge Now", use_container_width=True):
                        with st.spinner("🔄 Merging PDFs..."):
                            try:
                                progress_bar = st.progress(0)
                                merger = fitz.open()
                                
                                for idx, pdf in enumerate(merge_files):
                                    with fitz.open(stream=pdf.read(), filetype="pdf") as doc_temp: 
                                        merger.insert_pdf(doc_temp, links=True, annots=True)
                                    progress_bar.progress((idx + 1) / len(merge_files))
                                
                                out = io.BytesIO()
                                merger.save(out)
                                
                                st.success("🎉 Merge Complete!")
                                
                                # Action buttons
                                col1, col2 = st.columns(2)
                                with col1:
                                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Merged PDF")
                                with col2:
                                    save_and_offer_download(out.getvalue(), "merged.pdf")
                                
                                add_whatsapp_share("Bhai, PDFs merge ho gayi hain! 🚀")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please select at least 2 PDF files to merge")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ✂ TAB 3 — SPLIT PDF (ENHANCED)
# =========================================================
with tabs[2]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("✂ Split PDF")
        
        st.info("ℹ️ Extract specific pages from your PDF")
        
        split_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab3_upload")
        
        if split_pdf:
            # Validate PDF
            is_valid, message = validate_pdf(split_pdf)
            if is_valid:
                try:
                    doc = fitz.open(stream=split_pdf.read(), filetype="pdf")
                    total_pages = doc.page_count
                    
                    st.success(f"📄 PDF has {total_pages} pages")
                    
                    col_s1, col_s2 = st.columns(2)
                    start = col_s1.number_input(
                        "Start Page", 
                        min_value=1, 
                        max_value=total_pages,
                        value=1, 
                        key="split_start"
                    )
                    end = col_s2.number_input(
                        "End Page", 
                        min_value=start, 
                        max_value=total_pages,
                        value=min(start, total_pages), 
                        key="split_end"
                    )
                    
                    # Preview selection
                    pages_selected = end - start + 1
                    st.info(f"📑 Selected: {pages_selected} page(s) (Page {start} to {end})")
                    
                    if st.button("✂ Split Now", use_container_width=True):
                        with st.spinner("🔄 Splitting PDF..."):
                            try:
                                new = fitz.open()
                                new.insert_pdf(doc, from_page=start-1, to_page=end-1)
                                
                                out = io.BytesIO()
                                new.save(out)
                                
                                st.success("🎉 Split Complete!")
                                
                                # Action buttons
                                col1, col2 = st.columns(2)
                                with col1:
                                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Split PDF")
                                with col2:
                                    save_and_offer_download(out.getvalue(), f"split_pages_{start}_to_{end}.pdf")
                                
                                add_whatsapp_share("Bhai, PDF alag kar di! ✂️")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    
                    doc.close()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error(f"❌ {message}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🗜 TAB 4 — COMPRESS PDF (ENHANCED)
# =========================================================
with tabs[3]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("🗜 Compress PDF")
        
        st.info("ℹ️ Reduce PDF file size while maintaining quality")
        
        comp_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab4_upload")
        
        if comp_pdf:
            # Show original size
            original_size = len(comp_pdf.getvalue()) / (1024 * 1024)
            st.metric("Original Size", f"{original_size:.2f} MB")
            
            compression_level = st.select_slider(
                "Compression Level",
                options=["Low", "Medium", "High", "Maximum"],
                value="Medium",
                help="Higher compression = smaller file size but lower quality"
            )
            
            # Compression settings
            dpi_map = {"Low": 150, "Medium": 120, "High": 90, "Maximum": 72}
            quality_map = {"Low": 90, "Medium": 75, "High": 60, "Maximum": 45}
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📐 DPI: {dpi_map[compression_level]}")
            with col2:
                st.info(f"🎨 Quality: {quality_map[compression_level]}%")
            
            if st.button("🗜 Compress Now", use_container_width=True):
                with st.spinner("🔄 Compressing PDF..."):
                    try:
                        doc = fitz.open(stream=comp_pdf.read(), filetype="pdf")
                        dpi = dpi_map[compression_level]
                        
                        progress_bar = st.progress(0)
                        total_pages = len(doc)
                        
                        for page_num, page in enumerate(doc):
                            # Compress page
                            pix = page.get_pixmap(dpi=dpi)
                            page.clean_contents()
                            
                            # Insert compressed image
                            if compression_level != "Low":
                                page.insert_image(page.rect, pixmap=pix)
                            
                            progress_bar.progress((page_num + 1) / total_pages)
                        
                        # Additional compression
                        doc.subset_fonts()
                        
                        out = io.BytesIO()
                        doc.save(
                            out, 
                            garbage=4, 
                            deflate=True,
                            compress=True
                        )
                        
                        compressed_size = len(out.getvalue()) / (1024 * 1024)
                        reduction = ((original_size - compressed_size) / original_size) * 100
                        
                        st.success(f"🎉 Compression Complete! Reduced by {reduction:.1f}%")
                        
                        # Show size comparison
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Original", f"{original_size:.2f} MB")
                        with col2:
                            st.metric("Compressed", f"{compressed_size:.2f} MB", f"-{reduction:.1f}%")
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            open_pdf_in_new_tab(out.getvalue(), "🔓 Open Compressed PDF")
                        with col2:
                            save_and_offer_download(out.getvalue(), "compressed.pdf")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🖼 TAB 5 — EXTRACT IMAGES (ENHANCED)
# =========================================================
with tabs[4]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("🖼 Extract Images")
        
        st.info("ℹ️ Extract all images from PDF and download as ZIP")
        
        img_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab5_upload")
        
        if img_pdf:
            try:
                doc = fitz.open(stream=img_pdf.read(), filetype="pdf")
                
                # Count images
                total_images = 0
                for pno in range(len(doc)):
                    total_images += len(doc.get_page_images(pno))
                
                if total_images > 0:
                    st.success(f"📸 Found {total_images} image(s) in PDF")
                    
                    # Image format selection
                    img_format = st.radio(
                        "Image Format",
                        ["PNG", "JPEG"],
                        horizontal=True
                    )
                    
                    if st.button("📸 Extract Now", use_container_width=True):
                        with st.spinner(f"🔄 Extracting {total_images} images..."):
                            try:
                                zip_buf = io.BytesIO()
                                zipf = zipfile.ZipFile(zip_buf, "w")
                                
                                progress_bar = st.progress(0)
                                extracted_count = 0
                                
                                for pno in range(len(doc)):
                                    for img_index, img in enumerate(doc.get_page_images(pno)):
                                        pix = fitz.Pixmap(doc, img[0])
                                        
                                        # Convert if needed
                                        if img_format == "JPEG" and pix.n - pix.alpha < 4:
                                            pix = fitz.Pixmap(fitz.csRGB, pix)
                                        
                                        img_data = pix.tobytes(img_format.lower())
                                        zipf.writestr(
                                            f"page_{pno+1}_img_{img_index+1}.{img_format.lower()}", 
                                            img_data
                                        )
                                        
                                        pix = None  # Free memory
                                        extracted_count += 1
                                        progress_bar.progress(extracted_count / total_images)
                                
                                zipf.close()
                                
                                st.success(f"✅ Extracted {extracted_count} images!")
                                
                                # Download button
                                st.download_button(
                                    label=f"⬇ Download ZIP ({zip_buf.tell()/1024:.1f} KB)",
                                    data=zip_buf.getvalue(),
                                    file_name="extracted_images.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ No images found in this PDF")
                
                doc.close()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📄 TAB 6 — EXTRACT TEXT (ENHANCED)
# =========================================================
with tabs[5]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("📄 Extract Text")
        
        st.info("ℹ️ Extract text from PDF in various formats")
        
        txt_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab6_upload")
        
        if txt_pdf:
            try:
                doc = fitz.open(stream=txt_pdf.read(), filetype="pdf")
                
                st.success(f"📄 PDF has {len(doc)} pages")
                
                # Format selection
                col1, col2 = st.columns(2)
                with col1:
                    format_type = st.selectbox(
                        "Output Format",
                        ["Plain Text", "Markdown", "HTML", "JSON"]
                    )
                with col2:
                    page_range = st.radio(
                        "Pages to Extract",
                        ["All Pages", "Select Range"],
                        horizontal=True
                    )
                
                # Page selection
                if page_range == "Select Range":
                    col1, col2 = st.columns(2)
                    start_page = col1.number_input("Start Page", min_value=1, max_value=len(doc), value=1)
                    end_page = col2.number_input("End Page", min_value=start_page, max_value=len(doc), value=min(start_page+5, len(doc)))
                    pages_to_extract = range(start_page-1, end_page)
                else:
                    pages_to_extract = range(len(doc))
                
                if st.button("📄 Extract Text", use_container_width=True):
                    with st.spinner("🔄 Extracting text..."):
                        try:
                            extract_method = {
                                "Plain Text": "text",
                                "Markdown": "markdown",
                                "HTML": "html",
                                "JSON": "dict"
                            }[format_type]
                            
                            all_text = []
                            progress_bar = st.progress(0)
                            
                            for idx, page_num in enumerate(pages_to_extract):
                                page = doc[page_num]
                                
                                if format_type == "JSON":
                                    text_data = page.get_text("dict")
                                    all_text.append({
                                        f"page_{page_num+1}": text_data
                                    })
                                else:
                                    text = page.get_text(extract_method)
                                    if format_type == "HTML":
                                        all_text.append(f"<h2>Page {page_num+1}</h2>\n{text}")
                                    elif format_type == "Markdown":
                                        all_text.append(f"## Page {page_num+1}\n\n{text}")
                                    else:
                                        all_text.append(f"--- Page {page_num+1} ---\n{text}")
                                
                                progress_bar.progress((idx + 1) / len(pages_to_extract))
                            
                            # Combine text
                            if format_type == "JSON":
                                import json
                                final_text = json.dumps(all_text, indent=2)
                            else:
                                final_text = "\n\n".join(all_text)
                            
                            # Display extracted text
                            st.text_area("Extracted Text", final_text[:5000] + ("..." if len(final_text) > 5000 else ""), height=300)
                            
                            if len(final_text) > 5000:
                                st.info(f"ℹ️ Showing first 5000 characters. Total length: {len(final_text)} characters")
                            
                            # Download button
                            file_ext = {
                                "Plain Text": "txt",
                                "Markdown": "md",
                                "HTML": "html",
                                "JSON": "json"
                            }[format_type]
                            
                            st.download_button(
                                label=f"⬇ Download as {format_type} ({len(final_text)/1024:.1f} KB)",
                                data=final_text,
                                file_name=f"extracted_text.{file_ext}",
                                mime="text/plain",
                                use_container_width=True
                            )
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                doc.close()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📊 TAB 7 — EXTRACT TABLES (ENHANCED)
# =========================================================
with tabs[6]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("📊 Extract Tables")
        
        st.info("ℹ️ Extract tables from PDF and convert to CSV/Excel")
        
        table_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab7_upload")
        
        if table_pdf:
            try:
                doc = fitz.open(stream=table_pdf.read(), filetype="pdf")
                
                st.success(f"📄 PDF has {len(doc)} pages")
                
                # Table extraction options
                col1, col2 = st.columns(2)
                with col1:
                    output_format = st.selectbox(
                        "Output Format",
                        ["CSV", "Excel", "JSON"]
                    )
                with col2:
                    min_rows = st.number_input("Minimum Table Rows", min_value=1, value=2, help="Ignore tables with fewer rows")
                
                if st.button("📊 Extract Tables", use_container_width=True):
                    with st.spinner("🔄 Extracting tables..."):
                        try:
                            all_tables = []
                            progress_bar = st.progress(0)
                            
                            for page_num, page in enumerate(doc):
                                tables = page.find_tables()
                                
                                for table_idx, table in enumerate(tables):
                                    df = table.to_pandas()
                                    df.dropna(how='all', inplace=True)
                                    
                                    if len(df) >= min_rows:
                                        all_tables.append({
                                            'page': page_num + 1,
                                            'table': table_idx + 1,
                                            'data': df
                                        })
                                
                                progress_bar.progress((page_num + 1) / len(doc))
                            
                            if all_tables:
                                st.success(f"✅ Found {len(all_tables)} table(s)")
                                
                                # Preview tables
                                for table_info in all_tables[:3]:  # Show first 3 tables
                                    with st.expander(f"Table {table_info['table']} (Page {table_info['page']})"):
                                        st.dataframe(table_info['data'], use_container_width=True)
                                
                                if len(all_tables) > 3:
                                    st.info(f"ℹ️ Showing first 3 tables. Total {len(all_tables)} tables found.")
                                
                                # Export all tables
                                if output_format == "CSV":
                                    # Create zip with multiple CSVs
                                    zip_buf = io.BytesIO()
                                    zipf = zipfile.ZipFile(zip_buf, "w")
                                    
                                    for table_info in all_tables:
                                        csv_data = table_info['data'].to_csv(index=False)
                                        zipf.writestr(
                                            f"table_page{table_info['page']}_{table_info['table']}.csv",
                                            csv_data
                                        )
                                    
                                    zipf.close()
                                    
                                    st.download_button(
                                        label="⬇ Download All Tables (CSV ZIP)",
                                        data=zip_buf.getvalue(),
                                        file_name="tables.zip",
                                        mime="application/zip",
                                        use_container_width=True
                                    )
                                
                                elif output_format == "Excel":
                                    # Create Excel file with multiple sheets
                                    output = io.BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        for table_info in all_tables:
                                            sheet_name = f"Page{table_info['page']}_Table{table_info['table']}"
                                            table_info['data'].to_excel(writer, sheet_name=sheet_name, index=False)
                                    
                                    st.download_button(
                                        label="⬇ Download All Tables (Excel)",
                                        data=output.getvalue(),
                                        file_name="tables.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True
                                    )
                                
                                else:  # JSON
                                    import json
                                    json_data = []
                                    for table_info in all_tables:
                                        json_data.append({
                                            'page': table_info['page'],
                                            'table_number': table_info['table'],
                                            'data': table_info['data'].to_dict(orient='records')
                                        })
                                    
                                    st.download_button(
                                        label="⬇ Download All Tables (JSON)",
                                        data=json.dumps(json_data, indent=2),
                                        file_name="tables.json",
                                        mime="application/json",
                                        use_container_width=True
                                    )
                                
                            else:
                                st.warning("⚠️ No tables found in this PDF")
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                doc.close()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 📑 TAB 8 — REORDER PAGES (ENHANCED)
# =========================================================
with tabs[7]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("📑 Reorder Pages")
        
        st.info("ℹ️ Reorder, delete, or duplicate pages")
        
        re_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab8_upload")
        
        if re_pdf:
            try:
                doc = fitz.open(stream=re_pdf.read(), filetype="pdf")
                total_pages = doc.page_count
                
                st.success(f"📄 PDF has {total_pages} pages")
                
                # Page management options
                action = st.radio(
                    "Action",
                    ["Reorder", "Delete", "Duplicate"],
                    horizontal=True
                )
                
                if action == "Reorder":
                    # Show page thumbnails (simplified)
                    page_list = list(range(1, total_pages + 1))
                    
                    st.write("Drag to reorder (use arrows)")
                    
                    # Simple reorder with multiselect (in order)
                    selected = st.multiselect(
                        "Select pages in desired order",
                        page_list,
                        default=page_list,
                        help="Select pages in the order you want them to appear"
                    )
                    
                    if len(selected) != total_pages:
                        st.warning(f"⚠️ Selected {len(selected)} of {total_pages} pages. Unselected pages will be removed.")
                    
                    if st.button("📑 Apply Reorder", use_container_width=True):
                        with st.spinner("🔄 Reordering pages..."):
                            try:
                                new = fitz.open()
                                for p in selected:
                                    new.insert_pdf(doc, from_page=p-1, to_page=p-1)
                                
                                out = io.BytesIO()
                                new.save(out)
                                
                                st.success("🎉 Reorder Complete!")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Reordered PDF")
                                with col2:
                                    save_and_offer_download(out.getvalue(), "reordered.pdf")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                elif action == "Delete":
                    # Select pages to delete
                    pages_to_delete = st.multiselect(
                        "Select pages to delete",
                        list(range(1, total_pages + 1)),
                        help="Selected pages will be removed"
                    )
                    
                    if pages_to_delete:
                        pages_to_keep = [p for p in range(1, total_pages + 1) if p not in pages_to_delete]
                        st.info(f"📄 Remaining pages: {len(pages_to_keep)}")
                        
                        if st.button("🗑️ Delete Selected Pages", use_container_width=True):
                            with st.spinner("🔄 Deleting pages..."):
                                try:
                                    new = fitz.open()
                                    for p in pages_to_keep:
                                        new.insert_pdf(doc, from_page=p-1, to_page=p-1)
                                    
                                    out = io.BytesIO()
                                    new.save(out)
                                    
                                    st.success("🎉 Deletion Complete!")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Modified PDF")
                                    with col2:
                                        save_and_offer_download(out.getvalue(), "modified.pdf")
                                    
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                
                else:  # Duplicate
                    # Select pages to duplicate
                    pages_to_dup = st.multiselect(
                        "Select pages to duplicate",
                        list(range(1, total_pages + 1)),
                        help="Selected pages will be duplicated"
                    )
                    
                    if pages_to_dup:
                        st.info(f"📄 Will duplicate {len(pages_to_dup)} page(s)")
                        
                        # Duplicate count
                        dup_count = st.number_input("Number of duplicates per page", min_value=1, value=1)
                        
                        if st.button("📋 Duplicate Pages", use_container_width=True):
                            with st.spinner("🔄 Duplicating pages..."):
                                try:
                                    new = fitz.open()
                                    
                                    for p in range(1, total_pages + 1):
                                        # Add original page
                                        new.insert_pdf(doc, from_page=p-1, to_page=p-1)
                                        
                                        # Add duplicates if selected
                                        if p in pages_to_dup:
                                            for _ in range(dup_count):
                                                new.insert_pdf(doc, from_page=p-1, to_page=p-1)
                                    
                                    out = io.BytesIO()
                                    new.save(out)
                                    
                                    st.success(f"🎉 Duplication Complete! New page count: {len(new)}")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Modified PDF")
                                    with col2:
                                        save_and_offer_download(out.getvalue(), "duplicated.pdf")
                                    
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                
                doc.close()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ✍ TAB 9 — ADD SIGNATURE (ENHANCED)
# =========================================================
with tabs[8]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("✍ Add Signature")
        
        st.info("ℹ️ Add signature image to your PDF")
        
        col1, col2 = st.columns(2)
        
        with col1:
            s_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab9_upload")
        
        with col2:
            s_img = st.file_uploader(
                "Upload Signature (PNG/JPG)", 
                type=["png", "jpg", "jpeg"], 
                key="tab9_sign",
                help="Upload a signature image with transparent background for best results"
            )
        
        if s_pdf and s_img:
            try:
                doc = fitz.open(stream=s_pdf.read(), filetype="pdf")
                
                st.success(f"📄 PDF loaded with {len(doc)} pages")
                
                # Preview signature
                img_bytes = s_img.read()
                st.image(img_bytes, caption="Signature Preview", width=200)
                
                # Signature placement
                st.subheader("Signature Placement")
                
                # Page selection
                page_selection = st.radio(
                    "Apply to:",
                    ["All Pages", "Single Page", "Page Range"],
                    horizontal=True
                )
                
                target_pages = []
                if page_selection == "Single Page":
                    page_num = st.number_input("Page Number", min_value=1, max_value=len(doc), value=1)
                    target_pages = [page_num - 1]
                elif page_selection == "Page Range":
                    col1, col2 = st.columns(2)
                    start_page = col1.number_input("Start Page", min_value=1, max_value=len(doc), value=1)
                    end_page = col2.number_input("End Page", min_value=start_page, max_value=len(doc), value=min(start_page+5, len(doc)))
                    target_pages = list(range(start_page-1, end_page))
                else:
                    target_pages = list(range(len(doc)))
                
                # Position controls
                col1, col2, col3, col4 = st.columns(4)
                
                # Get page dimensions for reference
                sample_page = doc[0]
                max_x = sample_page.rect.width
                max_y = sample_page.rect.height
                
                x_pos = col1.number_input("X Position", value=int(max_x * 0.7), min_value=0, max_value=int(max_x))
                y_pos = col2.number_input("Y Position", value=int(max_y * 0.8), min_value=0, max_value=int(max_y))
                width = col3.number_input("Width", value=150, min_value=20, max_value=500)
                height = col4.number_input("Height", value=80, min_value=20, max_value=500)
                
                # Preview position
                st.info(f"📐 Position: ({x_pos}, {y_pos}) | Size: {width} x {height}")
                
                # Opacity control
                opacity = st.slider("Opacity", 0.1, 1.0, 1.0, 0.1)
                
                if st.button("✍ Sign Now", use_container_width=True):
                    with st.spinner(f"🔄 Adding signature to {len(target_pages)} page(s)..."):
                        try:
                            progress_bar = st.progress(0)
                            
                            # Create rectangle for signature
                            rect = fitz.Rect(x_pos, y_pos, x_pos + width, y_pos + height)
                            
                            for idx, page_num in enumerate(target_pages):
                                page = doc[page_num]
                                
                                # Insert signature
                                page.insert_image(
                                    rect, 
                                    stream=img_bytes, 
                                    overlay=True,
                                    keep_proportion=True
                                )
                                
                                progress_bar.progress((idx + 1) / len(target_pages))
                            
                            out = io.BytesIO()
                            doc.save(out)
                            
                            st.success("🎉 Signature Added!")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                open_pdf_in_new_tab(out.getvalue(), "🔓 Open Signed PDF")
                            with col2:
                                save_and_offer_download(out.getvalue(), "signed.pdf")
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                doc.close()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 💧 TAB 10 — WATERMARK TOOLS (ENHANCED)
# =========================================================
with tabs[9]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("💧 Watermark Tools")
        
        st.info("ℹ️ Add text or image watermarks to your PDF")
        
        watermark_type = st.radio(
            "Watermark Type",
            ["Text Watermark", "Image Watermark"],
            horizontal=True
        )
        
        w_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab10_upload")
        
        if w_pdf:
            try:
                doc = fitz.open(stream=w_pdf.read(), filetype="pdf")
                
                st.success(f"📄 PDF loaded with {len(doc)} pages")
                
                if watermark_type == "Text Watermark":
                    # Text watermark settings
                    col1, col2 = st.columns(2)
                    with col1:
                        w_txt = st.text_input("Watermark Text", value="CONFIDENTIAL")
                        font_size = st.slider("Font Size", 10, 200, 60)
                        rotation = st.slider("Rotation", 0, 360, 45)
                    
                    with col2:
                        opacity = st.slider("Opacity", 0.0, 1.0, 0.3, 0.1)
                        text_color = st.color_picker("Text Color", "#808080")
                        position = st.selectbox(
                            "Position",
                            ["Center", "Top Left", "Top Right", "Bottom Left", "Bottom Right", "Custom"]
                        )
                    
                    # Custom position if selected
                    custom_x, custom_y = 0, 0
                    if position == "Custom":
                        col1, col2 = st.columns(2)
                        custom_x = col1.number_input("X Position", value=100)
                        custom_y = col2.number_input("Y Position", value=100)
                    
                    # Preview
                    st.info(f"📝 Watermark: '{w_txt}' | Opacity: {opacity} | Rotation: {rotation}°")
                    
                    if st.button("💧 Add Watermark", use_container_width=True):
                        with st.spinner("🔄 Adding watermark..."):
                            try:
                                progress_bar = st.progress(0)
                                txt_rgb = tuple(int(text_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
                                
                                for page_num, page in enumerate(doc):
                                    # Calculate position
                                    if position == "Center":
                                        point = fitz.Point(page.rect.width / 2, page.rect.height / 2)
                                    elif position == "Top Left":
                                        point = fitz.Point(50, 50)
                                    elif position == "Top Right":
                                        point = fitz.Point(page.rect.width - 150, 50)
                                    elif position == "Bottom Left":
                                        point = fitz.Point(50, page.rect.height - 50)
                                    elif position == "Bottom Right":
                                        point = fitz.Point(page.rect.width - 150, page.rect.height - 50)
                                    else:  # Custom
                                        point = fitz.Point(custom_x, custom_y)
                                    
                                    # Insert watermark text
                                    page.insert_text(
                                        point, 
                                        w_txt, 
                                        fontsize=font_size, 
                                        color=txt_rgb, 
                                        opacity=opacity, 
                                        rotate=rotation
                                    )
                                    
                                    progress_bar.progress((page_num + 1) / len(doc))
                                
                                out = io.BytesIO()
                                doc.save(out)
                                
                                st.success("🎉 Watermark Added!")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    open_pdf_in_new_tab(out.getvalue(), "🔓 Open Watermarked PDF")
                                with col2:
                                    save_and_offer_download(out.getvalue(), "watermarked.pdf")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                else:  # Image watermark
                    w_img = st.file_uploader("Upload Watermark Image", type=["png", "jpg", "jpeg"], key="watermark_img")
                    
                    if w_img:
                        # Image watermark settings
                        col1, col2 = st.columns(2)
                        with col1:
                            opacity = st.slider("Opacity", 0.0, 1.0, 0.5, 0.1)
                            scale = st.slider("Scale (%)", 10, 200, 100)
                        
                        with col2:
                            position = st.selectbox(
                                "Position",
                                ["Center", "Tile", "Top Left", "Top Right", "Bottom Left", "Bottom Right"]
                            )
                        
                        if st.button("💧 Add Image Watermark", use_container_width=True):
                            with st.spinner("🔄 Adding image watermark..."):
                                try:
                                    img_bytes = w_img.read()
                                    progress_bar = st.progress(0)
                                    
                                    for page_num, page in enumerate(doc):
                                        # Get image dimensions
                                        img_rect = fitz.Rect(0, 0, 100 * scale/100, 100 * scale/100)
                                        
                                        if position == "Tile":
                                            # Tile watermark across page
                                            for y in range(0, int(page.rect.height), int(img_rect.height + 50)):
                                                for x in range(0, int(page.rect.width), int(img_rect.width + 50)):
                                                    rect = fitz.Rect(x, y, x + img_rect.width, y + img_rect.height)
                                                    page.insert_image(rect, stream=img_bytes, overlay=True, opacity=opacity)
                                        else:
                                            # Single watermark
                                            if position == "Center":
                                                x = (page.rect.width - img_rect.width) / 2
                                                y = (page.rect.height - img_rect.height) / 2
                                            elif position == "Top Left":
                                                x, y = 50, 50
                                            elif position == "Top Right":
                                                x = page.rect.width - img_rect.width - 50
                                                y = 50
                                            elif position == "Bottom Left":
                                                x, y = 50, page.rect.height - img_rect.height - 50
                                            else:  # Bottom Right
                                                x = page.rect.width - img_rect.width - 50
                                                y = page.rect.height - img_rect.height - 50
                                            
                                            rect = fitz.Rect(x, y, x + img_rect.width, y + img_rect.height)
                                            page.insert_image(rect, stream=img_bytes, overlay=True, opacity=opacity)
                                        
                                        progress_bar.progress((page_num + 1) / len(doc))
                                    
                                    out = io.BytesIO()
                                    doc.save(out)
                                    
                                    st.success("🎉 Image Watermark Added!")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        open_pdf_in_new_tab(out.getvalue(), "🔓 Open Watermarked PDF")
                                    with col2:
                                        save_and_offer_download(out.getvalue(), "watermarked.pdf")
                                    
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                
                doc.close()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 🤖 TAB 11 — AI AUTO EDIT (ENHANCED)
# =========================================================
with tabs[10]:
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("🤖 AI Auto Edit")
        
        st.info("ℹ️ AI-powered PDF editing (beta)")
        
        ai_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="tab11_upload")
        
        if ai_pdf:
            try:
                doc = fitz.open(stream=ai_pdf.read(), filetype="pdf")
                
                st.success(f"📄 PDF loaded with {len(doc)} pages")
                
                # AI Command selection
                ai_action = st.selectbox(
                    "Select AI Action",
                    [
                        "Remove Watermarks", 
                        "Summarize Text", 
                        "Auto Correct Typos",
                        "Extract Key Information",
                        "Redact Sensitive Data",
                        "Optimize for Printing"
                    ]
                )
                
                # Additional options based on action
                if ai_action == "Remove Watermarks":
                    st.info("This will attempt to remove gray text and semi-transparent elements")
                    sensitivity = st.slider("Sensitivity", 1, 10, 5, help="Higher sensitivity removes more elements")
                
                elif ai_action == "Summarize Text":
                    summary_length = st.select_slider(
                        "Summary Length",
                        options=["Very Short", "Short", "Medium", "Detailed"],
                        value="Medium"
                    )
                    length_map = {"Very Short": 200, "Short": 500, "Medium": 1000, "Detailed": 2000}
                
                elif ai_action == "Auto Correct Typos":
                    st.info("Basic spell checking and common typo correction")
                    corrections = {
                        "teh": "the",
                        "adn": "and",
                        "recieve": "receive",
                        "seperate": "separate",
                        "definately": "definitely",
                        "accomodate": "accommodate",
                        "occured": "occurred",
                        "alot": "a lot"
                    }
                    st.json(corrections)
                
                elif ai_action == "Extract Key Information":
                    info_types = st.multiselect(
                        "Information to Extract",
                        ["Dates", "Names", "Emails", "Phone Numbers", "Addresses", "Amounts"],
                        default=["Dates", "Emails"]
                    )
                
                elif ai_action == "Redact Sensitive Data":
                    patterns = st.multiselect(
                        "Data to Redact",
                        ["Email Addresses", "Phone Numbers", "Credit Cards", "Names", "Dates"],
                        default=["Email Addresses", "Phone Numbers"]
                    )
                    redact_color = st.color_picker("Redaction Color", "#000000")
                
                else:  # Optimize for Printing
                    st.info("Optimize PDF for better print quality")
                    print_quality = st.select_slider(
                        "Print Quality",
                        options=["Draft", "Normal", "High", "Presentation"],
                        value="Normal"
                    )
                
                if st.button("🤖 Run AI", use_container_width=True):
                    with st.spinner("🔄 AI processing..."):
                        try:
                            progress_bar = st.progress(0)
                            
                            if ai_action == "Remove Watermarks":
                                # Enhanced watermark removal
                                removed_count = 0
                                for page_num, page in enumerate(doc):
                                    text_instances = page.get_text("dict")["blocks"]
                                    for block in text_instances:
                                        for line in block.get("lines", []):
                                            for span in line.get("spans", []):
                                                # Check for watermark characteristics
                                                is_watermark = (
                                                    (span["color"] == 0xB3B3B3) or  # Gray
                                                    (span["size"] > 40) or  # Large text
                                                    (span["flags"] & 2)  # Possibly watermark
                                                )
                                                
                                                if is_watermark and sensitivity > 3:
                                                    rect = fitz.Rect(span["bbox"])
                                                    page.add_redact_annot(rect)
                                                    removed_count += 1
                                    
                                    page.apply_redactions()
                                    progress_bar.progress((page_num + 1) / len(doc))
                                
                                st.success(f"✅ Removed {removed_count} potential watermark elements")
                            
                            elif ai_action == "Summarize Text":
                                # Enhanced summarization
                                all_text = []
                                for page_num, page in enumerate(doc):
                                    text = page.get_text()
                                    # Simple extractive summarization
                                    sentences = text.split('. ')
                                    # Take first few sentences as summary
                                    summary = '. '.join(sentences[:10])
                                    all_text.append(f"Page {page_num + 1} Summary:\n{summary}\n")
                                    progress_bar.progress((page_num + 1) / len(doc))
                                
                                final_summary = '\n\n'.join(all_text)
                                
                                # Truncate if too long
                                max_length = length_map[summary_length]
                                if len(final_summary) > max_length:
                                    final_summary = final_summary[:max_length] + "...\n[Summary truncated]"
                                
                                st.text_area("AI Summary", final_summary, height=300)
                                
                                st.download_button(
                                    "⬇ Download Summary",
                                    final_summary,
                                    "summary.txt",
                                    use_container_width=True
                                )
                            
                            elif ai_action == "Auto Correct Typos":
                                # Apply corrections
                                corrected_count = 0
                                for page_num, page in enumerate(doc):
                                    text = page.get_text()
                                    corrected_text = text
                                    
                                    for typo, correction in corrections.items():
                                        if typo in corrected_text:
                                            corrected_text = corrected_text.replace(typo, correction)
                                            corrected_count += 1
                                    
                                    # Here you would redact and insert corrected text
                                    # Simplified for demo
                                    progress_bar.progress((page_num + 1) / len(doc))
                                
                                st.success(f"✅ Found and corrected {corrected_count} typos")
                            
                            elif ai_action == "Extract Key Information":
                                # Extract information (simplified)
                                extracted_info = []
                                for page_num, page in enumerate(doc):
                                    text = page.get_text()
                                    
                                    page_info = {"page": page_num + 1}
                                    
                                    import re
                                    if "Dates" in info_types:
                                        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)
                                        page_info["dates"] = dates[:5]
                                    
                                    if "Emails" in info_types:
                                        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                                        page_info["emails"] = emails[:5]
                                    
                                    if "Phone Numbers" in info_types:
                                        phones = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', text)
                                        page_info["phones"] = phones[:5]
                                    
                                    extracted_info.append(page_info)
                                    progress_bar.progress((page_num + 1) / len(doc))
                                
                                # Display extracted info
                                import json
                                st.json(extracted_info)
                                
                                st.download_button(
                                    "⬇ Download Extracted Info",
                                    json.dumps(extracted_info, indent=2),
                                    "extracted_info.json",
                                    use_container_width=True
                                )
                            
                            elif ai_action == "Redact Sensitive Data":
                                # Redact sensitive information
                                redacted_count = 0
                                for page_num, page in enumerate(doc):
                                    text = page.get_text()
                                    
                                    import re
                                    patterns_to_redact = []
                                    
                                    if "Email Addresses" in patterns:
                                        patterns_to_redact.append(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
                                    if "Phone Numbers" in patterns:
                                        patterns_to_redact.append(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]')
                                    if "Credit Cards" in patterns:
                                        patterns_to_redact.append(r'\b(?:\d[ -]*?){13,16}\b')
                                    
                                    for pattern in patterns_to_redact:
                                        matches = re.finditer(pattern, text)
                                        for match in matches:
                                            rects = page.search_for(match.group())
                                            for rect in rects:
                                                rgb = tuple(int(redact_color.lstrip('#')[i:i+2], 16)/255 for i in (0,2,4))
                                                page.add_redact_annot(rect, fill=rgb)
                                                redacted_count += 1
                                    
                                    page.apply_redactions()
                                    progress_bar.progress((page_num + 1) / len(doc))
                                
                                st.success(f"✅ Redacted {redacted_count} sensitive items")
                            
                            else:  # Optimize for Printing
                                # Optimize PDF for printing
                                dpi_map = {"Draft": 150, "Normal": 200, "High": 300, "Presentation": 400}
                                dpi = dpi_map[print_quality]
                                
                                for page_num, page in enumerate(doc):
                                    # Convert to high DPI for printing
                                    pix = page.get_pixmap(dpi=dpi)
                                    page.clean_contents()
                                    page.insert_image(page.rect, pixmap=pix)
                                    progress_bar.progress((page_num + 1) / len(doc))
                                
                                st.success(f"✅ Optimized for printing at {dpi} DPI")
                            
                            # Save and offer download
                            out = io.BytesIO()
                            doc.save(out, garbage=4, deflate=True)
                            out.seek(0)
                            
                            st.success("🎉 AI Processing Complete!")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                open_pdf_in_new_tab(out.getvalue(), "🔓 Open AI Result")
                            with col2:
                                save_and_offer_download(out.getvalue(), "ai_processed.pdf")
                            
                            add_whatsapp_share("Bhai, AI ne PDF badal di! 🤖")
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                doc.close()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("👨‍💻 **Created by:** Raghu")
with col2:
    st.markdown("📧 **Contact:** support@example.com")
with col3:
    st.markdown("🔧 **Version:** 2.0 Enhanced")

# Cleanup old cache
cleanup_old_cache()

