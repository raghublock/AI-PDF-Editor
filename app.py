"""
Pro PDF Studio — by Raghu (v3.0)
- Merge/Split/Compress tabs REMOVED
- Page Inspector: mobile-friendly cards, 50+ fonts, Find & Replace integrated
- Donation QR (UPI: raghubhati@slc) — popup on every page load + dedicated tab
"""

import streamlit as st
import fitz
import pandas as pd
import io
import base64
import zipfile
import urllib.parse
import hashlib
from typing import Optional, Tuple, List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pro PDF Studio — Raghu",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={'About': "Pro PDF Studio v3.0 by Raghu"}
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}

.stButton>button{
    border-radius:10px;font-weight:600;
    background:linear-gradient(135deg,#667eea,#764ba2);
    color:white;border:none;padding:10px 18px;
    transition:all 0.2s;width:100%;
}
.stButton>button:hover{transform:translateY(-1px);
    box-shadow:0 8px 20px rgba(102,126,234,0.4);border:none;}

.stTabs [data-baseweb="tab-list"]{
    gap:4px;background:#f0f2f6;padding:6px;
    border-radius:14px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{
    border-radius:8px;padding:7px 12px;
    font-weight:500;font-size:0.82em;white-space:nowrap;}
.stTabs [aria-selected="true"]{
    background:linear-gradient(135deg,#667eea,#764ba2)!important;color:white!important;}

.stProgress>div>div{background:linear-gradient(135deg,#667eea,#764ba2);}

/* Mobile span cards */
.span-card{background:#fff;border:1px solid #e8e8e8;border-radius:12px;
    padding:12px 14px;margin-bottom:10px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);}
.span-card .sc-text{font-size:0.95em;font-weight:600;color:#1a1a2e;
    margin-bottom:6px;word-break:break-word;}
.span-card .sc-meta{display:flex;flex-wrap:wrap;gap:6px;font-size:0.75em;}
.sc-chip{background:#f0f2f6;border-radius:20px;padding:3px 10px;
    color:#444;font-weight:500;border:1px solid #e0e0e0;}
.sc-chip.bold{background:#fff3cd;border-color:#ffc107;color:#856404;}
.sc-chip.italic{background:#d1ecf1;border-color:#0dcaf0;color:#0c5460;}
.sc-chip.mono{background:#e2e3ff;border-color:#667eea;color:#3730a3;}

/* Donation popup */
.don-overlay{position:fixed;top:0;left:0;width:100%;height:100%;
    background:rgba(0,0,0,0.68);z-index:99999;
    display:flex;align-items:center;justify-content:center;}
.don-box{background:white;border-radius:20px;padding:28px 22px;
    max-width:360px;width:92%;text-align:center;
    box-shadow:0 20px 60px rgba(0,0,0,0.3);}
.don-box h2{color:#667eea;margin:0 0 6px;font-size:1.35em;}
.don-box p{color:#555;font-size:0.88em;margin:5px 0 14px;}
.upi-chip{background:#f0f2f6;border-radius:8px;padding:8px 14px;
    font-family:monospace;font-size:1em;font-weight:700;color:#667eea;
    display:inline-block;margin:6px 0;border:2px dashed #667eea;}
.don-close{margin-top:14px;
    background:linear-gradient(135deg,#667eea,#764ba2);
    color:white;border:none;border-radius:10px;
    padding:10px 28px;font-weight:600;cursor:pointer;
    font-size:0.95em;width:100%;}

.whatsapp-btn{background:linear-gradient(135deg,#25D366,#128C7E);
    color:white;padding:11px 20px;text-decoration:none;
    border-radius:10px;font-weight:600;display:inline-block;
    text-align:center;width:100%;transition:all 0.2s;}
.whatsapp-btn:hover{box-shadow:0 8px 20px rgba(37,211,102,0.4);color:white;}

.app-header{text-align:center;padding:22px;
    background:linear-gradient(135deg,#667eea,#764ba2);
    border-radius:20px;margin-bottom:24px;
    box-shadow:0 12px 40px rgba(102,126,234,0.35);}
.app-header h1{color:white;font-size:clamp(1.2em,4vw,2em);margin:0;font-weight:700;}
.app-header p{color:rgba(255,255,255,0.88);margin:8px 0 0;font-size:0.9em;}

@media(max-width:640px){
    .stTabs [data-baseweb="tab"]{padding:5px 8px;font-size:0.76em;}
    .span-card{padding:9px 11px;}
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
def init_ss():
    defs = {
        'viewer_pdf_bytes': None,
        'processed_pdfs':   {},
        'ocr_available':    None,
        'undo_stack':       [],
        'donation_shown':   False,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_ss()

# ─────────────────────────────────────────────
# DONATION POPUP  (once per session)
# ─────────────────────────────────────────────
UPI_ID   = "raghubhati@slc"
UPI_LINK = f"upi://pay?pa={UPI_ID}&pn=Raghu&cu=INR"

def make_qr_b64(data_str: str) -> str:
    try:
        import qrcode
        qr = qrcode.QRCode(version=2,
                           error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=7, border=3)
        qr.add_data(data_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#667eea", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""

if not st.session_state.donation_shown:
    qr_b64 = make_qr_b64(UPI_LINK)
    enc_upi = urllib.parse.quote(UPI_LINK)
    if qr_b64:
        qr_tag = f'<img src="data:image/png;base64,{qr_b64}" width="185" style="border-radius:10px;margin:8px auto;display:block;border:2px solid #667eea44;"/>'
    else:
        qr_tag = (f'<img src="https://api.qrserver.com/v1/create-qr-code/?size=185x185'
                  f'&color=667eea&data={enc_upi}" width="185" '
                  f'style="border-radius:10px;margin:8px auto;display:block;" '
                  f'onerror="this.style.display=\'none\'"/>')

    st.markdown(f"""
    <div class="don-overlay" id="donOverlay">
      <div class="don-box">
        <div style="font-size:2.2em;margin-bottom:4px;">🙏</div>
        <h2>Support Raghu's Work!</h2>
        <p>Yeh tool free hai — agar helpful laga toh ek chhoti si<br>chai ki kimat donate karo! ☕</p>
        {qr_tag}
        <p style="margin:4px 0 2px;font-size:0.8em;color:#888;">Scan karo ya UPI ID pe bhejo:</p>
        <div class="upi-chip">{UPI_ID}</div><br/>
        <button class="don-close"
          onclick="document.getElementById('donOverlay').style.display='none'">
          ✅ Thanks! Ab App Use Karo
        </button>
        <p style="font-size:0.72em;color:#bbb;margin-top:10px;">
          Donation optional hai — app bilkul free hai 💙
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.donation_shown = True

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class='app-header'>
  <h1>🔵 Pro PDF Studio — by Raghu</h1>
  <p>Advanced PDF Processing · Smart Editing · OCR · Page Inspector</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# 50+ FONT MAP
# ═══════════════════════════════════════════════
FONT_MAP = {
    # ── Sans-Serif ──────────────────────────────
    "Helvetica":         {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Arial":             {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Arial Black":       {"n":"hebo","b":"hebo","i":"hebi","bi":"hebi"},
    "Calibri":           {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Verdana":           {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Tahoma":            {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Trebuchet MS":      {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Century Gothic":    {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Futura":            {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Gill Sans":         {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Segoe UI":          {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Myriad Pro":        {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Franklin Gothic":   {"n":"hebo","b":"hebo","i":"hebi","bi":"hebi"},
    "Impact":            {"n":"hebo","b":"hebo","i":"hebi","bi":"hebi"},
    "Optima":            {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Lucida Sans":       {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Raleway":           {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Open Sans":         {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Roboto":            {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Lato":              {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Nunito":            {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Poppins":           {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Montserrat":        {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Source Sans Pro":   {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Ubuntu":            {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Exo 2":             {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Karla":             {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "DM Sans":           {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    "Inter":             {"n":"helv","b":"hebo","i":"heit","bi":"hebi"},
    # ── Serif ────────────────────────────────────
    "Times New Roman":   {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Times":             {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Georgia":           {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Garamond":          {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Palatino":          {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Book Antiqua":      {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Cambria":           {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Constantia":        {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Caslon":            {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Minion Pro":        {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Baskerville":       {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Didot":             {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Bodoni":            {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Rockwell":          {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Merriweather":      {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Playfair Display":  {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Libre Baskerville": {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Lora":              {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "PT Serif":          {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Source Serif Pro":  {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    "Crimson Text":      {"n":"tiro","b":"tibo","i":"tiit","bi":"tibi"},
    # ── Monospace ────────────────────────────────
    "Courier New":       {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Courier":           {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Consolas":          {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Lucida Console":    {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Monaco":            {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Fira Code":         {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Source Code Pro":   {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Inconsolata":       {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "JetBrains Mono":    {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "Roboto Mono":       {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    "IBM Plex Mono":     {"n":"cour","b":"cobo","i":"coit","bi":"cobi"},
    # ── Special ──────────────────────────────────
    "Symbol":            {"n":"symb","b":"symb","i":"symb","bi":"symb"},
    "ZapfDingbats":      {"n":"zadi","b":"zadi","i":"zadi","bi":"zadi"},
}
FONT_NAMES = list(FONT_MAP.keys())  # 62 fonts

def get_font_name(family:str, bold:bool, italic:bool)->str:
    e = FONT_MAP.get(family, FONT_MAP["Helvetica"])
    if bold and italic: return e["bi"]
    if bold:            return e["b"]
    if italic:          return e["i"]
    return e["n"]

# ═══════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════
def validate_pdf(f_or_b, max_mb=50)->Tuple[bool,str,int]:
    try:
        if isinstance(f_or_b,(bytes,bytearray)):
            pb=f_or_b
        else:
            f_or_b.seek(0,2); sz=f_or_b.tell(); f_or_b.seek(0)
            if sz>max_mb*1024*1024: return False,f"Too large (max {max_mb}MB)",0
            pb=f_or_b.read(); f_or_b.seek(0)
        doc=fitz.open(stream=pb,filetype="pdf"); pg=len(doc); doc.close()
        if pg==0: return False,"No pages",0
        return True,f"Valid PDF ({pg} pages)",pg
    except Exception as e:
        return False,f"Invalid PDF: {e}",0

def get_pdf_bytes(f)->Optional[bytes]:
    try: f.seek(0); d=f.read(); f.seek(0); return d
    except: return None

def hex_to_rgb(h:str)->Tuple[float,float,float]:
    h=h.lstrip('#'); return int(h[:2],16)/255,int(h[2:4],16)/255,int(h[4:6],16)/255

def push_undo(pb:bytes):
    st.session_state.undo_stack.append(pb)
    if len(st.session_state.undo_stack)>5: st.session_state.undo_stack.pop(0)

def pop_undo()->Optional[bytes]:
    return st.session_state.undo_stack.pop() if st.session_state.undo_stack else None

def download_btn(pb:bytes, fn:str="output.pdf", lbl:str=None):
    sz=len(pb); lbl=lbl or f"⬇ Download ({sz/1024:.1f} KB)"
    st.download_button(lbl,pb,fn,"application/pdf",use_container_width=True)

def open_in_new_tab(pb:bytes, lbl:str="🔓 Open in Browser"):
    b64=base64.b64encode(pb).decode()
    st.components.v1.html(f"""
    <script>(function(){{
        const b=atob("{b64}"),a=new Uint8Array(b.length);
        for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);
        const u=URL.createObjectURL(new Blob([a],{{type:'application/pdf'}}));
        window.open(u,'_blank');setTimeout(()=>URL.revokeObjectURL(u),500);
    }})();</script>
    <button onclick="void(0)" style="background:linear-gradient(135deg,#28a745,#20c997);
        color:white;padding:11px;border:none;border-radius:10px;font-weight:600;
        cursor:pointer;width:100%;font-size:0.93em;">{lbl}</button>""",height=68)

def whatsapp_share(msg="Raghu ke Pro PDF Studio se PDF edit ki! 🚀"):
    enc=urllib.parse.quote(msg)
    st.markdown(f'<a href="https://wa.me/?text={enc}" target="_blank" class="whatsapp-btn">📲 Share on WhatsApp</a>',
                unsafe_allow_html=True)

def render_preview(pb:bytes, pg:int=0, dpi:int=120)->bytes:
    doc=fitz.open(stream=pb,filetype="pdf")
    pix=doc[min(pg,len(doc)-1)].get_pixmap(dpi=dpi); doc.close()
    return pix.tobytes("png")

def pdf_info(doc,pb:bytes):
    m=doc.metadata; c1,c2,c3,c4=st.columns(4)
    c1.metric("📄 Pages",len(doc))
    c2.metric("👤 Author",(m.get('author') or 'Unknown')[:16])
    c3.metric("📦 Size",f"{len(pb)/1024:.1f} KB")
    c4.metric("🔒 Enc.","Yes" if doc.is_encrypted else "No")

# ═══════════════════════════════════════════════
# PDF OPERATIONS
# ═══════════════════════════════════════════════
def smart_replace(pb,find,repl,font="Helvetica",size=12.0,
                  tc="#000",bgc="#fff",bold=False,italic=False,
                  case=True)->Tuple[bytes,int]:
    doc=fitz.open(stream=pb,filetype="pdf")
    fn=get_font_name(font,bold,italic)
    tr=hex_to_rgb(tc); br=hex_to_rgb(bgc); tot=0
    for page in doc:
        hits=page.search_for(find)
        if not hits: continue
        tot+=len(hits); saved=list(hits)
        for r in saved: page.add_redact_annot(r,fill=br)
        page.apply_redactions()
        for r in saved:
            wr=fitz.Rect(r.x0,r.y0-2,
                         r.x0+max(r.width,len(repl)*size*0.55),r.y1+2)
            page.insert_textbox(wr,repl,fontname=fn,fontsize=size,
                                color=tr,fill=br,align=fitz.TEXT_ALIGN_LEFT)
    out=io.BytesIO(); doc.save(out,garbage=4,deflate=True); doc.close()
    return out.getvalue(),tot

def split_range(pb:bytes,ranges:str)->Dict[str,bytes]:
    doc=fitz.open(stream=pb,filetype="pdf"); tot=len(doc); res={}
    for p in ranges.split(','):
        p=p.strip()
        if not p: continue
        if '-' in p: s,e=p.split('-',1); s,e=int(s)-1,int(e)-1
        else: s=e=int(p)-1
        s,e=max(0,min(s,tot-1)),max(0,min(e,tot-1))
        nd=fitz.open(); nd.insert_pdf(doc,from_page=s,to_page=e)
        buf=io.BytesIO(); nd.save(buf,garbage=4,deflate=True); nd.close()
        res[f"pages_{s+1}_to_{e+1}.pdf"]=buf.getvalue()
    doc.close(); return res

def merge_pdfs(pbs:List[bytes])->bytes:
    m=fitz.open()
    for pb in pbs:
        s=fitz.open(stream=pb,filetype="pdf"); m.insert_pdf(s); s.close()
    out=io.BytesIO(); m.save(out,garbage=4,deflate=True); m.close()
    return out.getvalue()

def extract_images(pb:bytes)->List[Dict]:
    doc=fitz.open(stream=pb,filetype="pdf"); imgs=[]
    for pn,page in enumerate(doc):
        for ii,info in enumerate(page.get_images(full=True)):
            try:
                bi=doc.extract_image(info[0])
                imgs.append({"page":pn+1,"index":ii+1,"ext":bi["ext"],
                             "data":bi["image"],"width":bi.get("width",0),
                             "height":bi.get("height",0)})
            except: pass
    doc.close(); return imgs

def extract_text(pb:bytes,mode="plain")->Dict[int,str]:
    doc=fitz.open(stream=pb,filetype="pdf"); res={}
    for pn,page in enumerate(doc):
        if mode=="html": res[pn+1]=page.get_text("html")
        elif mode=="blocks": res[pn+1]="\n".join(b[4] for b in page.get_text("blocks"))
        else: res[pn+1]=page.get_text()
    doc.close(); return res

def extract_tables(pb:bytes)->Dict[int,List[pd.DataFrame]]:
    doc=fitz.open(stream=pb,filetype="pdf"); all_t={}
    for pn,page in enumerate(doc):
        try:
            dfs=[]
            for tab in page.find_tables():
                df=pd.DataFrame(tab.extract())
                if not df.empty:
                    df.columns=df.iloc[0]; df=df[1:].reset_index(drop=True); dfs.append(df)
            if dfs: all_t[pn+1]=dfs
        except: pass
    doc.close(); return all_t

def reorder_pages(pb:bytes,order:List[int])->bytes:
    doc=fitz.open(stream=pb,filetype="pdf"); nd=fitz.open()
    for p in order:
        idx=p-1
        if 0<=idx<len(doc): nd.insert_pdf(doc,from_page=idx,to_page=idx)
    out=io.BytesIO(); nd.save(out,garbage=4,deflate=True)
    nd.close(); doc.close(); return out.getvalue()

def add_text_sig(pb,txt,pg=1,x=400,y=750,sz=14,col="#1a237e")->bytes:
    doc=fitz.open(stream=pb,filetype="pdf")
    page=doc[min(pg-1,len(doc)-1)]; rgb=hex_to_rgb(col)
    rect=fitz.Rect(x-5,y-sz-4,x+len(txt)*sz*0.55+5,y+4)
    page.draw_rect(rect,color=rgb,width=1)
    page.insert_text((x,y),txt,fontname="tiro",fontsize=sz,color=rgb)
    out=io.BytesIO(); doc.save(out,garbage=4,deflate=True); doc.close()
    return out.getvalue()

def add_img_sig(pb,imgb,pg=1,x=350,y=700,w=150,h=60)->bytes:
    doc=fitz.open(stream=pb,filetype="pdf")
    doc[min(pg-1,len(doc)-1)].insert_image(fitz.Rect(x,y,x+w,y+h),stream=imgb)
    out=io.BytesIO(); doc.save(out,garbage=4,deflate=True); doc.close()
    return out.getvalue()

def add_text_wm(pb,txt="CONFIDENTIAL",op=0.15,col="#FF0000",
                sz=60,ang=45,pgs="all")->bytes:
    doc=fitz.open(stream=pb,filetype="pdf"); rgb=hex_to_rgb(col)
    idxs=list(range(len(doc))) if pgs=="all" else \
         [int(p)-1 for p in pgs.split(',') if p.strip().isdigit()]
    for i in idxs:
        if 0<=i<len(doc):
            page=doc[i]; w,h=page.rect.width,page.rect.height
            page.insert_text((w*0.1,h*0.55),txt,fontsize=sz,
                             color=(*rgb,op),rotate=ang,overlay=True)
    out=io.BytesIO(); doc.save(out,garbage=4,deflate=True); doc.close()
    return out.getvalue()

def add_img_wm(pb,imgb,op=0.2)->bytes:
    doc=fitz.open(stream=pb,filetype="pdf")
    for page in doc:
        r=page.rect
        page.insert_image(fitz.Rect(r.width*0.25,r.height*0.35,
                                    r.width*0.75,r.height*0.65),
                          stream=imgb,overlay=True)
    out=io.BytesIO(); doc.save(out,garbage=4,deflate=True); doc.close()
    return out.getvalue()

def check_ocr()->bool:
    if st.session_state.ocr_available is None:
        try: import pytesseract; from PIL import Image; st.session_state.ocr_available=True
        except: st.session_state.ocr_available=False
    return st.session_state.ocr_available

def run_ocr(pb:bytes,lang="eng",dpi=200)->Dict[int,Dict]:
    import pytesseract; from PIL import Image
    doc=fitz.open(stream=pb,filetype="pdf"); res={}
    for pn,page in enumerate(doc):
        pix=page.get_pixmap(dpi=dpi)
        img=Image.open(io.BytesIO(pix.tobytes("png")))
        txt=pytesseract.image_to_string(img,lang=lang)
        cd=pytesseract.image_to_data(img,lang=lang,output_type=pytesseract.Output.DICT)
        confs=[c for c in cd['conf'] if isinstance(c,(int,float)) and c>0]
        res[pn+1]={"text":txt,"word_count":len([w for w in txt.split() if w.strip()]),
                   "confidence":round(sum(confs)/max(1,len(confs)),1)}
    doc.close(); return res

def inspect_page(pb:bytes,pg:int=0)->Dict:
    doc=fitz.open(stream=pb,filetype="pdf")
    page=doc[min(pg,len(doc)-1)]
    spans=[]; all_c={}; fonts={}

    for block in page.get_text("dict",flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]:
        if block.get("type")!=0: continue
        for line in block.get("lines",[]):
            for sp in line.get("spans",[]):
                raw=sp.get("color",0)
                r,g,b=(raw>>16)&0xFF,(raw>>8)&0xFF,raw&0xFF
                hx="#{:02x}{:02x}{:02x}".format(r,g,b)
                flg=sp.get("flags",0)
                txt=sp.get("text","").strip()
                if not txt: continue
                entry={"text":txt,"font":sp.get("font","?"),
                       "size":round(sp.get("size",0),2),"color":hx,
                       "bold":bool(flg&(1<<4)),"italic":bool(flg&(1<<1)),
                       "mono":bool(flg&(1<<3)),"r":r,"g":g,"b":b}
                spans.append(entry)
                all_c[hx]=all_c.get(hx,0)+1
                fn=entry["font"]
                if fn not in fonts:
                    fonts[fn]={"sizes":set(),"count":0,"bold":False,"italic":False}
                fonts[fn]["sizes"].add(entry["size"]); fonts[fn]["count"]+=1
                if entry["bold"]:   fonts[fn]["bold"]=True
                if entry["italic"]: fonts[fn]["italic"]=True

    draw_c=[]
    for draw in page.get_drawings():
        for key in("color","fill"):
            val=draw.get(key)
            if val and isinstance(val,(list,tuple)) and len(val)>=3:
                r2,g2,b2=int(val[0]*255),int(val[1]*255),int(val[2]*255)
                hx="#{:02x}{:02x}{:02x}".format(r2,g2,b2)
                draw_c.append({"Color":hx,"Type":key,
                               "Width":round(draw.get("width") or 0,2)})
                all_c[hx]=all_c.get(hx,0)+1

    pi={"width":round(page.rect.width,1),"height":round(page.rect.height,1),
        "rotation":page.rotation}
    img_n=len(page.get_images(full=True)); doc.close()

    fs=[{"Font Name":fn,"Used":fd["count"],
         "Sizes":  ", ".join(str(s) for s in sorted(fd["sizes"])),
         "Bold":   "✅" if fd["bold"] else "—",
         "Italic": "✅" if fd["italic"] else "—"}
        for fn,fd in sorted(fonts.items(),key=lambda x:-x[1]["count"])]

    return {"spans":spans,"fonts":fs,
            "colors":sorted(all_c.items(),key=lambda x:-x[1]),
            "draw_colors":draw_c,"imgs":img_n,"page_info":pi,
            "total":len(spans)}

# ═══════════════════════════════════════════════
# TABS  — Merge/Split/Compress removed
# ═══════════════════════════════════════════════
TABS=[
    "📘 Viewer & Editor",
    "🎨 Page Inspector",
    "🖼 Extract Images",
    "📄 Extract Text",
    "📊 Tables",
    "📑 Reorder",
    "✍ Signature",
    "💧 Watermark",
    "🔍 OCR",
    "💙 Donate",
]
tabs=st.tabs(TABS)


# ══════════════════════════════════
# T0 — VIEWER + FIND & REPLACE
# ══════════════════════════════════
with tabs[0]:
    st.subheader("📘 PDF Viewer + Smart Find & Replace")
    up=st.file_uploader("📂 Upload PDF",type=["pdf"],key="v_up")
    if up:
        pb=get_pdf_bytes(up)
        ok,msg,pgs=validate_pdf(pb)
        if not ok: st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")
            st.session_state.viewer_pdf_bytes=pb
            doc=fitz.open(stream=pb,filetype="pdf")
            with st.expander("📊 PDF Info",expanded=False): pdf_info(doc,pb)
            doc.close()

            c_l,c_r=st.columns([1,2])
            with c_l: ppg=st.number_input("Preview Page",1,pgs,1,key="vp")
            with c_r: st.image(render_preview(pb,ppg-1,110),
                               caption=f"Page {ppg}/{pgs}",use_container_width=True)
            st.divider()
            st.markdown("#### ✏️ Find & Replace")
            c1,c2=st.columns(2)
            vf=c1.text_input("🔍 Find",placeholder="Text to find",key="vf")
            vr=c2.text_input("✏️ Replace",placeholder="Replacement",key="vr")
            c1,c2,c3=st.columns(3)
            vfont=c1.selectbox("Font",FONT_NAMES,key="vfont")
            vsz=c2.number_input("Size",4.0,72.0,12.0,0.5,key="vsz")
            vcs=c3.checkbox("Case Sensitive",True,key="vcs")
            c1,c2,c3,c4=st.columns(4)
            vbd=c1.checkbox("Bold",key="vbd"); vit=c2.checkbox("Italic",key="vit")
            vtc=c3.color_picker("Text","#000000",key="vtc")
            vbc=c4.color_picker("BG","#FFFFFF",key="vbc")

            if st.button("✨ Apply Replace",use_container_width=True,key="vapp"):
                if not vf: st.warning("⚠️ Enter find text.")
                elif not vr: st.warning("⚠️ Enter replace text.")
                else:
                    with st.spinner("Processing..."):
                        try:
                            push_undo(st.session_state.viewer_pdf_bytes)
                            nb,cnt=smart_replace(st.session_state.viewer_pdf_bytes,
                                                 vf,vr,vfont,vsz,vtc,vbc,vbd,vit,vcs)
                            if cnt==0: st.warning("⚠️ Not found.")
                            else:
                                st.session_state.viewer_pdf_bytes=nb
                                st.success(f"✅ Replaced {cnt}×!")
                                download_btn(nb,"edited.pdf"); open_in_new_tab(nb)
                                whatsapp_share()
                        except Exception as e: st.error(f"❌ {e}")

            if st.session_state.undo_stack:
                if st.button("↩ Undo",key="vundo"):
                    st.session_state.viewer_pdf_bytes=pop_undo()
                    st.success("↩ Done!"); st.rerun()


# ══════════════════════════════════
# T1 — PAGE INSPECTOR
# ══════════════════════════════════
with tabs[1]:
    st.subheader("🎨 Page Inspector — Colors · Fonts · Text Styles")
    st.caption("Kisi bhi page ka poora data — phone pe bhi readable mobile cards mein.")

    up1=st.file_uploader("📂 Upload PDF",type=["pdf"],key="ins_up")
    if up1:
        pb1=get_pdf_bytes(up1)
        ok,msg,tp=validate_pdf(pb1)
        if not ok: st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")
            cl,cr=st.columns([1,2])
            with cl: ipg=st.number_input("Page",1,tp,1,key="ipg")
            with cr: st.image(render_preview(pb1,ipg-1,100),
                              caption=f"Page {ipg}",use_container_width=True)

            if st.button("🔍 Inspect This Page",use_container_width=True,key="irun"):
                with st.spinner("Scanning..."):
                    idata=inspect_page(pb1,ipg-1)

                # Page info
                pi=idata["page_info"]
                st.markdown("---"); st.markdown("### 📐 Page Info")
                c1,c2,c3,c4=st.columns(4)
                c1.metric("Width",f"{pi['width']} pt")
                c2.metric("Height",f"{pi['height']} pt")
                c3.metric("Rotation",f"{pi['rotation']}°")
                c4.metric("Images",idata["imgs"])
                st.caption(f"Total text spans found: **{idata['total']}**")

                # Color palette
                st.markdown("---"); st.markdown("### 🎨 Color Palette")
                if idata["colors"]:
                    sw="<div style='display:flex;flex-wrap:wrap;gap:10px;margin-top:6px;'>"
                    for hx,cnt in idata["colors"]:
                        rv,gv,bv=int(hx[1:3],16),int(hx[3:5],16),int(hx[5:7],16)
                        lum=0.299*rv+0.587*gv+0.114*bv
                        tc2="#000" if lum>128 else "#fff"
                        sw+=f"""<div style='text-align:center;width:78px;'>
                            <div style='background:{hx};width:62px;height:62px;
                                border-radius:10px;border:2px solid #ddd;margin:0 auto;
                                box-shadow:0 3px 8px rgba(0,0,0,0.1);
                                display:flex;align-items:center;justify-content:center;'>
                                <span style='color:{tc2};font-size:0.58em;font-weight:700;'>{hx}</span>
                            </div>
                            <div style='font-size:0.7em;color:#666;margin-top:3px;'>×{cnt}</div>
                        </div>"""
                    st.markdown(sw+"</div>",unsafe_allow_html=True)
                else: st.info("No colors.")
                if idata["draw_colors"]:
                    st.markdown("**🖊 Drawing/Shape Colors:**")
                    st.dataframe(pd.DataFrame(idata["draw_colors"]),
                                 use_container_width=True,hide_index=True)

                # Fonts
                st.markdown("---"); st.markdown("### 🔤 Fonts Used")
                if idata["fonts"]:
                    st.dataframe(pd.DataFrame(idata["fonts"]),
                                 use_container_width=True,hide_index=True,
                                 column_config={
                                     "Font Name":st.column_config.TextColumn(width="large"),
                                     "Used":st.column_config.NumberColumn(width="small"),
                                     "Sizes":st.column_config.TextColumn(width="medium"),
                                 })
                else: st.info("No fonts.")

                # Mobile cards
                st.markdown("---")
                st.markdown("### 📝 Text Spans — Mobile Card View")
                if idata["spans"]:
                    af=sorted(set(s["font"] for s in idata["spans"]))
                    fc1,fc2,fc3=st.columns(3)
                    ff=fc1.selectbox("Font",["All"]+af,key="iff")
                    fb=fc2.selectbox("Bold",["All","✅ Bold","— Normal"],key="ifb")
                    fi=fc3.selectbox("Italic",["All","✅ Italic","— Normal"],key="ifi")

                    fspans=idata["spans"]
                    if ff!="All": fspans=[s for s in fspans if s["font"]==ff]
                    if fb=="✅ Bold":    fspans=[s for s in fspans if s["bold"]]
                    elif fb=="— Normal": fspans=[s for s in fspans if not s["bold"]]
                    if fi=="✅ Italic":   fspans=[s for s in fspans if s["italic"]]
                    elif fi=="— Normal": fspans=[s for s in fspans if not s["italic"]]

                    st.caption(f"Showing {len(fspans)} of {len(idata['spans'])} spans")

                    cards=""
                    for sp in fspans[:80]:
                        td=sp["text"][:90]+("…" if len(sp["text"])>90 else "")
                        lum2=0.299*sp["r"]+0.587*sp["g"]+0.114*sp["b"]
                        chips=(f"<span class='sc-chip'>🔤 {sp['font'][:20]}</span>"
                               f"<span class='sc-chip'>📏 {sp['size']} pt</span>"
                               f"<span class='sc-chip' style='background:{sp['color']};"
                               f"color:{'#000' if lum2>128 else '#fff'};border-color:{sp['color']};'>"
                               f"● {sp['color']}</span>")
                        if sp["bold"]:   chips+="<span class='sc-chip bold'>B Bold</span>"
                        if sp["italic"]: chips+="<span class='sc-chip italic'>I Italic</span>"
                        if sp["mono"]:   chips+="<span class='sc-chip mono'>⌨ Mono</span>"
                        cards+=f"<div class='span-card'><div class='sc-text'>\"{td}\"</div><div class='sc-meta'>{chips}</div></div>"

                    if len(fspans)>80:
                        cards+=f"<p style='color:#999;text-align:center;font-size:0.78em;'>...aur {len(fspans)-80} spans — CSV download karo</p>"

                    st.markdown(f"<div style='max-height:520px;overflow-y:auto;padding:2px;'>{cards}</div>",
                                unsafe_allow_html=True)

                    df_dl=pd.DataFrame([{"Text":s["text"],"Font":s["font"],
                        "Size":s["size"],"Color":s["color"],
                        "Bold":s["bold"],"Italic":s["italic"]} for s in fspans])
                    st.download_button("⬇ Download CSV",df_dl.to_csv(index=False).encode(),
                                       f"p{ipg}_spans.csv","text/csv",use_container_width=True)
                else: st.info("No text found.")

            # ── FIND & REPLACE inside Inspector ──────────────
            st.markdown("---")
            st.markdown("### ✏️ Edit This PDF — Find & Replace")
            st.caption("Inspect karne ke baad yahan se seedha edit karo.")
            c1,c2=st.columns(2)
            if_=c1.text_input("🔍 Find",key="if_",placeholder="Dhundna hai")
            ir_=c2.text_input("✏️ Replace",key="ir_",placeholder="Replace karna hai")
            c1,c2,c3=st.columns(3)
            ifnt=c1.selectbox("Font",FONT_NAMES,key="ifnt")
            isz=c2.number_input("Size",4.0,72.0,12.0,0.5,key="isz")
            ics=c3.checkbox("Case Sensitive",True,key="ics")
            c1,c2,c3,c4=st.columns(4)
            ibd=c1.checkbox("Bold",key="ibd"); iit=c2.checkbox("Italic",key="iit")
            itc=c3.color_picker("Text","#000000",key="itc")
            ibc=c4.color_picker("BG","#FFFFFF",key="ibc")

            iscope=st.radio("Replace on:",
                            [f"Only Page {ipg if up1 else 1}","All Pages"],
                            horizontal=True,key="iscope")

            if st.button("✨ Apply Replace",use_container_width=True,key="iapp"):
                if not if_: st.warning("⚠️ Find text daalo.")
                elif not ir_: st.warning("⚠️ Replace text daalo.")
                else:
                    with st.spinner("Processing..."):
                        try:
                            push_undo(pb1)
                            if "All Pages" in iscope:
                                rb,_=smart_replace(pb1,if_,ir_,ifnt,isz,itc,ibc,ibd,iit,ics)
                            else:
                                doc_t=fitz.open(stream=pb1,filetype="pdf")
                                tot_t=len(doc_t); doc_t.close()
                                parts=[]
                                if ipg>1:
                                    bfr=split_range(pb1,f"1-{ipg-1}")
                                    parts.append(list(bfr.values())[0])
                                single=split_range(pb1,str(ipg))
                                es,_=smart_replace(list(single.values())[0],
                                                   if_,ir_,ifnt,isz,itc,ibc,ibd,iit,ics)
                                parts.append(es)
                                if ipg<tot_t:
                                    aft=split_range(pb1,f"{ipg+1}-{tot_t}")
                                    parts.append(list(aft.values())[0])
                                rb=merge_pdfs(parts) if len(parts)>1 else es

                            st.success("✅ Replace ho gaya!")
                            download_btn(rb,"edited.pdf"); open_in_new_tab(rb)
                        except Exception as e:
                            st.error(f"❌ {e}")
                            logger.exception("Inspector replace error")


# ══════════════════════════════════
# T2 — EXTRACT IMAGES
# ══════════════════════════════════
with tabs[2]:
    st.subheader("🖼 Extract Images from PDF")
    up2=st.file_uploader("📂 Upload PDF",type=["pdf"],key="img_up")
    if up2:
        pb2=get_pdf_bytes(up2)
        ok,msg,_=validate_pdf(pb2)
        if not ok: st.error(f"❌ {msg}")
        else:
            if st.button("🔍 Extract Images",use_container_width=True):
                with st.spinner("Extracting..."): imgs=extract_images(pb2)
                if not imgs: st.warning("No images found.")
                else:
                    st.success(f"✅ Found {len(imgs)} image(s)")
                    zb=io.BytesIO()
                    with zipfile.ZipFile(zb,'w',zipfile.ZIP_DEFLATED) as zf:
                        for img in imgs:
                            zf.writestr(f"p{img['page']}_i{img['index']}.{img['ext']}",img['data'])
                    st.download_button("⬇ Download All (ZIP)",zb.getvalue(),
                                       "images.zip","application/zip",use_container_width=True)
                    cols=st.columns(3)
                    for i,img in enumerate(imgs[:9]):
                        cols[i%3].image(img['data'],
                                        caption=f"P{img['page']} {img['width']}×{img['height']}",
                                        use_container_width=True)


# ══════════════════════════════════
# T3 — EXTRACT TEXT
# ══════════════════════════════════
with tabs[3]:
    st.subheader("📄 Extract Text from PDF")
    up3=st.file_uploader("📂 Upload PDF",type=["pdf"],key="txt_up")
    if up3:
        pb3=get_pdf_bytes(up3)
        ok,msg,pg3=validate_pdf(pb3)
        if not ok: st.error(f"❌ {msg}")
        else:
            c1,c2=st.columns(2)
            tm=c1.selectbox("Mode",["plain","blocks","html"])
            pf=c2.text_input("Pages (blank=all)",placeholder="1, 3, 5-7")
            if st.button("📄 Extract",use_container_width=True):
                txts=extract_text(pb3,tm)
                if pf.strip():
                    sel=set()
                    for p in pf.split(','):
                        p=p.strip()
                        if '-' in p: a,b=p.split('-'); sel.update(range(int(a),int(b)+1))
                        elif p.isdigit(): sel.add(int(p))
                    txts={p:t for p,t in txts.items() if p in sel}
                if not txts: st.warning("No text.")
                else:
                    full="\n\n".join(f"--- Page {p} ---\n{t}" for p,t in txts.items())
                    st.text_area("Text",full,height=350)
                    st.download_button("⬇ Download .txt",full.encode(),
                                       "text.txt","text/plain",use_container_width=True)


# ══════════════════════════════════
# T4 — TABLES
# ══════════════════════════════════
with tabs[4]:
    st.subheader("📊 Extract Tables from PDF")
    up4=st.file_uploader("📂 Upload PDF",type=["pdf"],key="tbl_up")
    if up4:
        pb4=get_pdf_bytes(up4)
        ok,msg,_=validate_pdf(pb4)
        if not ok: st.error(f"❌ {msg}")
        else:
            if st.button("📊 Find Tables",use_container_width=True):
                with st.spinner("Detecting..."): all_t=extract_tables(pb4)
                if not all_t: st.warning("No tables detected.")
                else:
                    st.success(f"✅ Found {sum(len(v) for v in all_t.values())} table(s)")
                    xl=io.BytesIO()
                    with pd.ExcelWriter(xl,engine='openpyxl') as w:
                        for pn,dfs in all_t.items():
                            for i,df in enumerate(dfs):
                                st.markdown(f"**Page {pn} — Table {i+1}**")
                                st.dataframe(df,use_container_width=True)
                                df.to_excel(w,sheet_name=f"P{pn}_T{i+1}",index=False)
                    st.download_button("⬇ Download Excel",xl.getvalue(),"tables.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)


# ══════════════════════════════════
# T5 — REORDER
# ══════════════════════════════════
with tabs[5]:
    st.subheader("📑 Reorder PDF Pages")
    up5=st.file_uploader("📂 Upload PDF",type=["pdf"],key="ro_up")
    if up5:
        pb5=get_pdf_bytes(up5)
        ok,msg,tp5=validate_pdf(pb5)
        if not ok: st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")
            no=st.text_input("New Order",value=", ".join(str(i) for i in range(1,tp5+1)))
            if st.checkbox("Show Thumbnails"):
                cs=st.columns(min(tp5,5))
                for i in range(min(tp5,5)):
                    cs[i].image(render_preview(pb5,i,60),caption=f"Pg {i+1}",use_container_width=True)
            if st.button("📑 Apply",use_container_width=True):
                try:
                    ord_=[int(x.strip()) for x in no.split(',') if x.strip()]
                    with st.spinner("Reordering..."): res=reorder_pages(pb5,ord_)
                    st.success("✅ Done!"); download_btn(res,"reordered.pdf"); open_in_new_tab(res)
                except: st.error("❌ Invalid order")


# ══════════════════════════════════
# T6 — SIGNATURE
# ══════════════════════════════════
with tabs[6]:
    st.subheader("✍ Add Signature")
    up6=st.file_uploader("📂 Upload PDF",type=["pdf"],key="sig_up")
    if up6:
        pb6=get_pdf_bytes(up6)
        ok,msg,tp6=validate_pdf(pb6)
        if not ok: st.error(f"❌ {msg}")
        else:
            st=st  # scope fix not needed, using direct calls
            stype=globals()['st'].radio("Type",["Text","Image"],horizontal=True,key="stype")
            if stype=="Text":
                c1,c2=globals()['st'].columns(2)
                stxt=c1.text_input("Text"); scol=c2.color_picker("Color","#1a237e")
                c1,c2,c3=globals()['st'].columns(3)
                spg=c1.number_input("Page",1,tp6,tp6)
                sx=c2.number_input("X",0,800,400); sy=c3.number_input("Y",0,1200,750)
                ssz=globals()['st'].slider("Font Size",8,36,14)
                if globals()['st'].button("✍ Add Signature",use_container_width=True):
                    if not stxt: globals()['st'].warning("Enter text.")
                    else:
                        res=add_text_sig(pb6,stxt,spg,sx,sy,ssz,scol)
                        globals()['st'].success("✅ Added!")
                        download_btn(res,"signed.pdf"); open_in_new_tab(res)
            else:
                simg=globals()['st'].file_uploader("Signature Image",
                                                    type=["png","jpg","jpeg"],key="sig_img")
                if simg:
                    c1,c2,c3=globals()['st'].columns(3)
                    sp2=c1.number_input("Page",1,tp6,tp6)
                    sx2=c2.number_input("X",0,800,350); sy2=c3.number_input("Y",0,1200,700)
                    c1,c2=globals()['st'].columns(2)
                    sw2=c1.number_input("W",20,400,150); sh2=c2.number_input("H",10,200,60)
                    globals()['st'].image(simg,width=160)
                    if globals()['st'].button("✍ Add Image Sig",use_container_width=True):
                        res=add_img_sig(pb6,simg.read(),sp2,sx2,sy2,sw2,sh2)
                        globals()['st'].success("✅ Added!")
                        download_btn(res,"signed.pdf"); open_in_new_tab(res)


# ══════════════════════════════════
# T7 — WATERMARK
# ══════════════════════════════════
with tabs[7]:
    st.subheader("💧 Watermark Tools")
    up7=st.file_uploader("📂 Upload PDF",type=["pdf"],key="wm_up")
    if up7:
        pb7=get_pdf_bytes(up7)
        ok,msg,tp7=validate_pdf(pb7)
        if not ok: st.error(f"❌ {msg}")
        else:
            wt=st.radio("Type",["Text","Image"],horizontal=True)
            if wt=="Text":
                c1,c2=st.columns(2)
                wtxt=c1.text_input("Text","CONFIDENTIAL"); wcol=c2.color_picker("Color","#FF0000")
                c1,c2,c3,c4=st.columns(4)
                wsz=c1.number_input("Size",10,150,60); wang=c2.number_input("Angle",0,360,45)
                wop=c3.slider("Opacity",0.01,0.99,0.15,0.01)
                wpgs=c4.text_input("Pages","all")
                if st.button("💧 Apply",use_container_width=True):
                    with st.spinner("Applying..."):
                        res=add_text_wm(pb7,wtxt,wop,wcol,wsz,wang,wpgs.strip() or "all")
                    st.success("✅ Done!"); download_btn(res,"wm.pdf"); open_in_new_tab(res)
            else:
                wimg=st.file_uploader("Watermark Image",type=["png","jpg","jpeg"],key="wm_img")
                if wimg:
                    wop2=st.slider("Opacity",0.01,0.99,0.2,0.01)
                    st.image(wimg,width=130)
                    if st.button("💧 Apply",use_container_width=True):
                        res=add_img_wm(pb7,wimg.read(),wop2)
                        st.success("✅ Done!"); download_btn(res,"wm.pdf"); open_in_new_tab(res)


# ══════════════════════════════════
# T8 — OCR
# ══════════════════════════════════
with tabs[8]:
    st.subheader("🔍 OCR Scanner")
    if not check_ocr():
        st.error("❌ pytesseract / pillow not installed.")
        st.code("pip install pytesseract pillow")
    else:
        up8=st.file_uploader("📂 Upload PDF (scanned)",type=["pdf"],key="ocr_up")
        if up8:
            pb8=get_pdf_bytes(up8)
            ok,msg,tp8=validate_pdf(pb8)
            if not ok: st.error(f"❌ {msg}")
            else:
                c1,c2=st.columns(2)
                olang=c1.selectbox("Language",["eng","hin","spa","fra","deu","ara","chi_sim"])
                odpi=c2.select_slider("DPI",[100,150,200,300],value=200)
                if st.button("🔍 Run OCR",use_container_width=True):
                    with st.spinner(f"OCR on {tp8} pages..."):
                        try:
                            prog=st.progress(0)
                            res=run_ocr(pb8,olang,odpi); prog.progress(1.0)
                            tw=sum(r['word_count'] for r in res.values())
                            ac=round(sum(r['confidence'] for r in res.values())/len(res),1)
                            c1,c2,c3=st.columns(3)
                            c1.metric("Pages",tp8); c2.metric("Words",tw)
                            c3.metric("Avg Conf",f"{ac}%")
                            full="\n\n".join(f"=== Page {p} ===\n{r['text']}"
                                             for p,r in res.items())
                            st.text_area("OCR Output",full,height=320)
                            st.download_button("⬇ Download",full.encode(),
                                               "ocr.txt","text/plain",use_container_width=True)
                        except Exception as e: st.error(f"❌ {e}")


# ══════════════════════════════════
# T9 — DONATE
# ══════════════════════════════════
with tabs[9]:
    st.subheader("💙 Support Raghu's Work")
    cl,cr=st.columns(2)
    with cl:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#667eea18,#764ba218);
                    border:1px solid #667eea44;border-radius:16px;
                    padding:24px;text-align:center;'>
            <div style='font-size:2.5em;'>🙏</div>
            <h3 style='color:#667eea;margin:8px 0;'>Donate via UPI</h3>
            <p style='color:#555;font-size:0.88em;margin-bottom:14px;'>
                Kisi bhi UPI app se scan karo ya ID copy karo:
            </p>
            <div class='upi-chip'>{UPI_ID}</div>
            <br/><br/>
            <p style='color:#888;font-size:0.78em;'>
                GPay · PhonePe · Paytm · BHIM · Any UPI App
            </p>
        </div>
        """,unsafe_allow_html=True)

    with cr:
        qr_d=make_qr_b64(UPI_LINK)
        if qr_d:
            st.markdown(f"""
            <div style='text-align:center;padding:10px;'>
                <img src='data:image/png;base64,{qr_d}'
                     style='width:220px;border-radius:14px;
                            box-shadow:0 8px 24px rgba(102,126,234,0.25);
                            border:3px solid #667eea44;'/>
                <p style='color:#888;font-size:0.78em;margin-top:8px;'>
                    📱 Phone se scan karo — direct UPI pe jayega
                </p>
            </div>""",unsafe_allow_html=True)
        else:
            enc_u=urllib.parse.quote(UPI_LINK)
            st.markdown(f"""
            <div style='text-align:center;padding:10px;'>
                <img src='https://api.qrserver.com/v1/create-qr-code/?size=220x220&color=667eea&data={enc_u}'
                     style='width:220px;border-radius:14px;
                            box-shadow:0 8px 24px rgba(102,126,234,0.25);'
                     onerror="this.parentElement.innerHTML='<p>QR load nahi hua — ID copy karo</p>'"/>
                <p style='color:#888;font-size:0.78em;margin-top:8px;'>📱 Phone se scan karo</p>
            </div>""",unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center;margin-top:20px;padding:14px;
                background:#f8f9fa;border-radius:12px;color:#888;font-size:0.83em;'>
        💙 Donation optional hai — app free hai aur hamesha rahega<br>
        Teri support se better features banane ki motivation milti hai! 🚀
    </div>""",unsafe_allow_html=True)


# ─────────────────────────────────
# FOOTER
# ─────────────────────────────────
st.divider()
st.markdown(f"""
<div style='text-align:center;color:#bbb;font-size:0.8em;padding:6px 0 16px;'>
    🔵 <strong>Pro PDF Studio v3.0</strong> — Built with ❤️ by Raghu &nbsp;|&nbsp;
    PyMuPDF · Streamlit · OCR &nbsp;|&nbsp;
    <span style='color:#667eea;'>UPI: {UPI_ID}</span>
</div>
""",unsafe_allow_html=True)
