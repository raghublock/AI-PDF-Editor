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
    qr_b64     = make_qr_b64(UPI_LINK)
    enc_upi    = urllib.parse.quote(UPI_LINK)
    CRYPTO_ADR = "0x9c45F8098D1887EfFe84A4781c877f297D42604A"

    if qr_b64:
        qr_tag = f'<img src="data:image/png;base64,{qr_b64}" width="170" style="border-radius:10px;display:block;margin:6px auto;border:2px solid #667eea44;"/>'
    else:
        qr_tag = (f'<img src="https://api.qrserver.com/v1/create-qr-code/?size=170x170'
                  f'&color=667eea&data={enc_upi}" width="170" '
                  f'style="border-radius:10px;display:block;margin:6px auto;" '
                  f'onerror="this.style.display:none"/>')

    # Inject popup directly into Streamlit's parent DOM via postMessage trick
    # The component sends JS up to the parent window to create a real fixed overlay
    st.components.v1.html(f"""
<!DOCTYPE html><html><head>
<script>
// Inject overlay into the parent Streamlit page
(function(){{
  var UPI    = '{UPI_ID}';
  var CRYPTO = '{CRYPTO_ADR}';
  var QR_B64 = '{qr_b64}';
  var QR_URL = 'https://api.qrserver.com/v1/create-qr-code/?size=170x170&color=667eea&data={enc_upi}';

  var qrHtml = QR_B64
    ? '<img src="data:image/png;base64,'+QR_B64+'" width="160" style="border-radius:10px;display:block;margin:6px auto;border:2px solid #667eea44;box-shadow:0 4px 12px rgba(102,126,234,0.2);">'
    : '<img src="'+QR_URL+'" width="160" style="border-radius:10px;display:block;margin:6px auto;" onerror="this.style.display=\'none\'">';

  var css = `
    #raghu-don-overlay{{
      position:fixed;top:0;left:0;width:100%;height:100%;
      background:rgba(10,10,30,0.78);z-index:999999;
      display:flex;align-items:center;justify-content:center;
      backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);
      font-family:'Inter','Segoe UI',sans-serif;
      animation:donFadeIn 0.3s ease;
    }}
    @keyframes donFadeIn{{from{{opacity:0}}to{{opacity:1}}}}
    #raghu-don-box{{
      background:#fff;border-radius:22px;padding:22px 20px 18px;
      max-width:380px;width:92%;text-align:center;
      box-shadow:0 24px 80px rgba(0,0,0,0.4);
      max-height:90vh;overflow-y:auto;
      animation:donSlideUp 0.35s cubic-bezier(.34,1.56,.64,1);
    }}
    @keyframes donSlideUp{{from{{transform:translateY(40px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
    #raghu-don-box h2{{color:#667eea;font-size:1.25em;margin:4px 0 3px;font-weight:700;}}
    .don-sub{{color:#555;font-size:0.83em;line-height:1.5;margin-bottom:6px;}}
    .don-min{{background:#fff8e1;border:1.5px solid #ffc107;border-radius:20px;
              padding:4px 14px;font-size:0.78em;color:#92600a;font-weight:700;
              display:inline-block;margin-bottom:8px;}}
    .don-sec{{font-size:0.7em;color:#999;font-weight:700;text-transform:uppercase;
              letter-spacing:0.6px;margin:8px 0 4px;}}
    .don-upi-row{{display:flex;align-items:center;gap:7px;
                  background:#f3f4f8;border:2px dashed #667eea;
                  border-radius:10px;padding:7px 10px;margin:3px 0 6px;}}
    .don-upi-id{{font-family:monospace;font-size:0.95em;font-weight:700;
                 color:#667eea;flex:1;text-align:left;word-break:break-all;}}
    .don-crypto-row{{display:flex;align-items:center;gap:7px;
                     background:#12122a;border-radius:10px;
                     padding:8px 10px;margin:3px 0 5px;}}
    .don-crypto-id{{font-family:monospace;font-size:0.68em;font-weight:600;
                    color:#a78bfa;flex:1;text-align:left;word-break:break-all;}}
    .don-cbtn{{border:none;border-radius:8px;padding:6px 12px;font-weight:700;
               font-size:0.76em;cursor:pointer;flex-shrink:0;
               -webkit-tap-highlight-color:transparent;transition:all 0.15s;}}
    .don-cbtn-u{{background:#667eea;color:#fff;}}
    .don-cbtn-u:active{{background:#4f46e5;transform:scale(0.93);}}
    .don-cbtn-c{{background:#7c3aed;color:#fff;}}
    .don-cbtn-c:active{{background:#5b21b6;transform:scale(0.93);}}
    .don-apps{{font-size:0.68em;color:#bbb;margin:3px 0 6px;}}
    .don-chains{{font-size:0.67em;color:#7c3aed;margin-top:4px;line-height:1.6;}}
    .don-close{{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);
               color:#fff;border:none;border-radius:12px;padding:13px;
               font-size:0.97em;font-weight:700;cursor:pointer;margin-top:10px;
               -webkit-tap-highlight-color:transparent;
               box-shadow:0 6px 20px rgba(102,126,234,0.4);
               transition:all 0.2s;}}
    .don-close:hover{{transform:translateY(-1px);box-shadow:0 10px 28px rgba(102,126,234,0.5);}}
    .don-close:active{{transform:scale(0.97);}}
    .don-foot{{font-size:0.68em;color:#ccc;margin-top:7px;}}
    #don-toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);
                background:rgba(0,0,0,0.85);color:#fff;padding:8px 20px;
                border-radius:24px;font-size:0.8em;opacity:0;
                transition:opacity 0.25s;pointer-events:none;
                z-index:9999999;white-space:nowrap;}}
    #don-toast.show{{opacity:1;}}
  `;

  var html = `
    <div id="raghu-don-overlay">
      <div id="raghu-don-box">
        <div style="font-size:2em;line-height:1;">🙏</div>
        <h2>Support Raghu's Work!</h2>
        <p class="don-sub">Yeh tool free hai — agar helpful laga toh<br>ek chhoti si chai ki kimat donate karo! ☕</p>
        <span class="don-min">💛 Minimum donation: sirf ₹10</span>

        <div class="don-sec">🇮🇳 UPI / Indian Payment</div>
        `+qrHtml+`
        <p style="font-size:0.72em;color:#aaa;margin:3px 0 2px;">Scan karo ya UPI ID copy karo</p>
        <div class="don-upi-row">
          <span class="don-upi-id">`+UPI+`</span>
          <button class="don-cbtn don-cbtn-u" onclick="donCopy('`+UPI+`','UPI ID copy ho gaya ✅')">Copy</button>
        </div>
        <p class="don-apps">GPay · PhonePe · Paytm · BHIM · Any UPI App</p>

        <div class="don-sec">🌍 Crypto / International</div>
        <p style="font-size:0.7em;color:#888;margin:2px 0 3px;">EVM wallet — ETH/MATIC/BNB/USDT koi bhi chain pe</p>
        <div class="don-crypto-row">
          <span class="don-crypto-id">`+CRYPTO+`</span>
          <button class="don-cbtn don-cbtn-c" onclick="donCopy('`+CRYPTO+`','Wallet copy ho gaya ✅')">Copy</button>
        </div>
        <p class="don-chains">✅ ETH · Polygon · BSC · Arbitrum · Optimism · Base<br>USDT · USDC · ETH · MATIC · BNB · any ERC-20</p>

        <button class="don-close" onclick="donClose()">✅ Thanks! Ab App Use Karo</button>
        <p class="don-foot">Donation optional hai — app hamesha free rahega 💙</p>
      </div>
    </div>
    <div id="don-toast"></div>
  `;

  function donClose(){{
    var el=document.getElementById('raghu-don-overlay');
    if(el){{el.style.animation='donFadeOut 0.2s ease forwards';
            setTimeout(function(){{if(el)el.remove();}},200);}}
    var t=document.getElementById('don-toast');if(t)t.remove();
  }}
  function donCopy(txt,msg){{
    if(navigator.clipboard&&navigator.clipboard.writeText){{
      navigator.clipboard.writeText(txt).then(function(){{donToast(msg);}});
    }}else{{
      var ta=document.createElement('textarea');
      ta.value=txt;ta.style.cssText='position:fixed;opacity:0;top:0;left:0;';
      document.body.appendChild(ta);ta.focus();ta.select();
      try{{document.execCommand('copy');donToast(msg);}}catch(e){{}}
      document.body.removeChild(ta);
    }}
  }}
  function donToast(msg){{
    var t=document.getElementById('don-toast');
    if(!t)return;t.textContent=msg;t.classList.add('show');
    setTimeout(function(){{t.classList.remove('show');}},2000);
  }}

  // Inject into parent window
  function inject(win){{
    try{{
      // add style
      var s=win.document.createElement('style');
      s.id='raghu-don-style';s.textContent=css;
      win.document.head.appendChild(s);
      // add html
      var div=win.document.createElement('div');
      div.innerHTML=html;
      win.document.body.appendChild(div);
      // expose functions to parent
      win.donClose=donClose;win.donCopy=donCopy;win.donToast=donToast;
      // close on overlay background click
      setTimeout(function(){{
        var ov=win.document.getElementById('raghu-don-overlay');
        if(ov)ov.addEventListener('click',function(e){{
          if(e.target===ov)donClose();
        }});
      }},100);
      // add fade-out keyframe
      var s2=win.document.createElement('style');
      s2.textContent='@keyframes donFadeOut{{to{{opacity:0}}}}';
      win.document.head.appendChild(s2);
    }}catch(e){{console.log('inject err',e);}}
  }}

  // Try parent, then parent.parent (Streamlit double-iframe)
  try{{inject(window.parent);}}catch(e){{}}
  try{{inject(window.parent.parent);}}catch(e){{}}
}})();
</script>
</head><body style="background:transparent;margin:0;height:1px;"></body></html>
""", height=1, scrolling=False)
    st.session_state.donation_shown = True

# ─────────────────────────────────────────────
# HEADER  — animated, vibrant
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Animated gradient background for the whole page */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}
[data-testid="stMain"] {
    background: transparent;
}
/* Make main content area cards feel elevated */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
    background: rgba(255,255,255,0.03);
    border-radius: 16px;
}
/* Sidebar / top bar */
[data-testid="stHeader"] { background: transparent; }

/* Input fields */
.stTextInput input, .stNumberInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(102,126,234,0.4) !important;
    color: #e0e0ff !important;
    border-radius: 8px !important;
}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stSlider label,
.stCheckbox label, .stRadio label,
.stFileUploader label { color: #c0c0e0 !important; }

/* Selectbox — fix white dropdown bg */
.stSelectbox div[data-baseweb="select"] > div,
.stSelectbox div[data-baseweb="select"] > div:hover,
.stSelectbox [data-baseweb="popover"],
.stSelectbox [role="listbox"],
.stSelectbox [role="option"],
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"],
[role="option"] {
    background: #1e1b4b !important;
    background-color: #1e1b4b !important;
    border-color: rgba(102,126,234,0.5) !important;
    color: #e0e0ff !important;
}
[role="option"]:hover,
[data-baseweb="option"]:hover {
    background: rgba(102,126,234,0.3) !important;
}
/* Force all select inputs dark */
.stSelectbox svg { color: #a0a0cc !important; }
.stSelectbox [data-testid="stMarkdownContainer"] { color: #e0e0ff !important; }
/* Number input */
.stNumberInput [data-baseweb="input"] {
    background: rgba(255,255,255,0.07) !important;
    border-color: rgba(102,126,234,0.4) !important;
}
.stNumberInput button {
    background: rgba(102,126,234,0.25) !important;
    border-color: rgba(102,126,234,0.4) !important;
    color: #e0e0ff !important;
}
/* Color picker */
.stColorPicker > div { border-color: rgba(102,126,234,0.3) !important; }
/* Radio */
.stRadio > div { color: #c0c0dd !important; }
/* Checkbox */
.stCheckbox > label > div:first-child { border-color: rgba(102,126,234,0.5) !important; }

/* Metrics */
[data-testid="metric-container"] {
    background: rgba(102,126,234,0.12);
    border: 1px solid rgba(102,126,234,0.25);
    border-radius: 12px;
    padding: 12px !important;
}
[data-testid="metric-container"] label { color: #a0a0cc !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #fff !important; }

/* Subheader */
h3 { color: #e0e0ff !important; }
.stMarkdown p { color: #c0c0dd; }
.stCaption { color: #8888aa !important; }

/* expander */
.streamlit-expanderHeader { color: #c0c0ee !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(102,126,234,0.2);
}
.stTabs [data-baseweb="tab"] { color: #a0a0cc !important; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#667eea,#764ba2) !important;
    color: white !important;
}

/* Span cards on dark bg */
.span-card {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(102,126,234,0.25) !important;
    color: #e0e0ff;
}
.span-card .sc-text { color: #f0f0ff !important; }
.sc-chip { background: rgba(102,126,234,0.18) !important;
           border-color: rgba(102,126,234,0.3) !important; color: #c0c0ee !important; }
.sc-chip.bold   { background:rgba(255,193,7,0.15)!important;  color:#ffd54f!important; }
.sc-chip.italic { background:rgba(13,202,240,0.12)!important; color:#80deea!important; }
.sc-chip.mono   { background:rgba(102,126,234,0.2)!important; color:#9fa8da!important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(102,126,234,0.07);
    border: 2px dashed rgba(102,126,234,0.35);
    border-radius: 12px;
}

/* Download button */
.stDownloadButton button {
    background: linear-gradient(135deg,#28a745,#20c997) !important;
    color: white !important; border-radius: 10px !important;
    border: none !important; font-weight: 600 !important;
}

/* Divider */
hr { border-color: rgba(102,126,234,0.2) !important; }
</style>

<div style="
  text-align:center;
  padding:32px 20px 24px;
  background: linear-gradient(135deg,rgba(102,126,234,0.9),rgba(118,75,162,0.95));
  border-radius:24px;
  margin-bottom:20px;
  box-shadow:0 16px 48px rgba(102,126,234,0.4), 0 4px 12px rgba(0,0,0,0.3);
  position:relative;
  overflow:hidden;
">
  <!-- Background glow blobs -->
  <div style="position:absolute;top:-40px;right:-40px;width:160px;height:160px;
    background:rgba(255,255,255,0.08);border-radius:50%;pointer-events:none;"></div>
  <div style="position:absolute;bottom:-30px;left:-30px;width:120px;height:120px;
    background:rgba(255,255,255,0.06);border-radius:50%;pointer-events:none;"></div>

  <div style="font-size:2.6em;line-height:1;margin-bottom:8px;">🔵</div>
  <h1 style="color:white;font-size:clamp(1.4em,4.5vw,2.3em);margin:0;
             font-weight:800;letter-spacing:-0.5px;
             text-shadow:0 2px 12px rgba(0,0,0,0.25);">
    Pro PDF Studio
    <span style="background:rgba(255,255,255,0.15);border-radius:20px;
                 padding:2px 12px;font-size:0.55em;font-weight:600;
                 vertical-align:middle;margin-left:6px;
                 border:1px solid rgba(255,255,255,0.25);">v3.0</span>
  </h1>
  <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;
            font-size:clamp(0.8em,2.2vw,1em);font-weight:400;">
    Built by <strong style="color:#ffd54f;">Raghu</strong> &nbsp;·&nbsp;
    Smart Editing &nbsp;·&nbsp; Page Inspector &nbsp;·&nbsp; OCR &nbsp;·&nbsp; Watermark
  </p>

  <!-- Feature pills -->
  <div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:6px;justify-content:center;">
    <span style="background:rgba(255,255,255,0.15);color:white;border-radius:20px;
                 padding:4px 12px;font-size:0.72em;font-weight:600;
                 border:1px solid rgba(255,255,255,0.2);">📄 Text Extract</span>
    <span style="background:rgba(255,255,255,0.15);color:white;border-radius:20px;
                 padding:4px 12px;font-size:0.72em;font-weight:600;
                 border:1px solid rgba(255,255,255,0.2);">🎨 Color Inspector</span>
    <span style="background:rgba(255,255,255,0.15);color:white;border-radius:20px;
                 padding:4px 12px;font-size:0.72em;font-weight:600;
                 border:1px solid rgba(255,255,255,0.2);">🔤 63 Fonts</span>
    <span style="background:rgba(255,255,255,0.15);color:white;border-radius:20px;
                 padding:4px 12px;font-size:0.72em;font-weight:600;
                 border:1px solid rgba(255,255,255,0.2);">✍ Signature</span>
    <span style="background:rgba(255,255,255,0.15);color:white;border-radius:20px;
                 padding:4px 12px;font-size:0.72em;font-weight:600;
                 border:1px solid rgba(255,255,255,0.2);">🔍 OCR</span>
    <span style="background:rgba(255,255,255,0.15);color:white;border-radius:20px;
                 padding:4px 12px;font-size:0.72em;font-weight:600;
                 border:1px solid rgba(255,255,255,0.2);">💧 Watermark</span>
  </div>
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
    st.components.v1.html(f"""<!DOCTYPE html><html><head>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;padding:4px 0;}}
button{{width:100%;padding:12px;border:none;border-radius:10px;
  background:linear-gradient(135deg,#28a745,#20c997);color:white;
  font-weight:700;font-size:0.95em;cursor:pointer;letter-spacing:0.2px;
  font-family:system-ui,sans-serif;
  box-shadow:0 4px 14px rgba(40,167,69,0.4);transition:all 0.18s;
  -webkit-tap-highlight-color:transparent;}}
button:hover{{transform:translateY(-1px);box-shadow:0 8px 22px rgba(40,167,69,0.5);}}
button:active{{transform:scale(0.97);opacity:0.9;}}
</style></head><body>
<button onclick="openPDF()">{lbl}</button>
<script>
var DATA="{b64}";
function openPDF(){{
  var arr=new Uint8Array(atob(DATA).split('').map(function(c){{return c.charCodeAt(0);}}));
  var blob=new Blob([arr],{{type:'application/pdf'}});
  var url=URL.createObjectURL(blob);
  var w=null;
  try{{w=window.parent.open(url,'_blank');}}catch(e){{}}
  if(!w||w.closed)try{{w=window.top.open(url,'_blank');}}catch(e){{}}
  if(!w||w.closed)w=window.open(url,'_blank');
  setTimeout(function(){{URL.revokeObjectURL(url);}},4000);
}}
</script></body></html>""", height=56)

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

                # ── Beautiful Interactive Table (replaces cards) ──
                st.markdown("---")
                st.markdown("### 📋 Text Spans — Interactive Table")
                if idata["spans"]:
                    af=sorted(set(s["font"] for s in idata["spans"]))
                    fc1,fc2,fc3=st.columns(3)
                    ff=fc1.selectbox("🔤 Filter Font",["All"]+af,key="iff")
                    fb=fc2.selectbox("B Filter Bold",["All","✅ Bold","— Normal"],key="ifb")
                    fi=fc3.selectbox("I Filter Italic",["All","✅ Italic","— Normal"],key="ifi")

                    fspans=idata["spans"]
                    if ff!="All": fspans=[s for s in fspans if s["font"]==ff]
                    if fb=="✅ Bold":    fspans=[s for s in fspans if s["bold"]]
                    elif fb=="— Normal": fspans=[s for s in fspans if not s["bold"]]
                    if fi=="✅ Italic":   fspans=[s for s in fspans if s["italic"]]
                    elif fi=="— Normal": fspans=[s for s in fspans if not s["italic"]]

                    st.caption(f"Showing {min(len(fspans),200)} of {len(idata['spans'])} spans")

                    # Build rows JSON for the HTML table
                    import json as _json
                    rows_data = []
                    for sp in fspans[:200]:
                        lum=0.299*sp["r"]+0.587*sp["g"]+0.114*sp["b"]
                        tc="#000" if lum>128 else "#fff"
                        rows_data.append({
                            "text": sp["text"][:120],
                            "font": sp["font"],
                            "size": sp["size"],
                            "color": sp["color"],
                            "color_tc": tc,
                            "bold": sp["bold"],
                            "italic": sp["italic"],
                            "mono": sp["mono"],
                        })
                    rows_json = _json.dumps(rows_data)

                    st.components.v1.html(f"""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Inter',system-ui,sans-serif;}}
body{{background:transparent;padding:0;}}
.tbl-wrap{{
  border-radius:14px;overflow:hidden;
  border:1px solid rgba(102,126,234,0.3);
  box-shadow:0 8px 32px rgba(0,0,0,0.3);
}}
.tbl-header{{
  display:flex;align-items:center;justify-content:space-between;
  padding:12px 16px;
  background:linear-gradient(135deg,rgba(102,126,234,0.9),rgba(118,75,162,0.9));
}}
.tbl-header span{{color:white;font-weight:700;font-size:0.9em;}}
.copy-all-btn{{
  background:rgba(255,255,255,0.2);color:white;border:1px solid rgba(255,255,255,0.3);
  border-radius:8px;padding:5px 12px;font-size:0.76em;font-weight:600;cursor:pointer;
  transition:all 0.15s;-webkit-tap-highlight-color:transparent;
}}
.copy-all-btn:hover{{background:rgba(255,255,255,0.3);}}
.copy-all-btn:active{{transform:scale(0.95);}}
table{{width:100%;border-collapse:collapse;}}
thead tr{{background:rgba(30,27,75,0.95);}}
thead th{{
  padding:10px 12px;text-align:left;font-size:0.75em;font-weight:700;
  color:#a78bfa;text-transform:uppercase;letter-spacing:0.6px;
  border-bottom:1px solid rgba(102,126,234,0.3);white-space:nowrap;
}}
tbody tr{{
  background:rgba(15,12,41,0.8);
  border-bottom:1px solid rgba(102,126,234,0.1);
  transition:background 0.12s;
}}
tbody tr:hover{{background:rgba(102,126,234,0.12);}}
tbody tr:nth-child(even){{background:rgba(30,27,75,0.6);}}
tbody tr:nth-child(even):hover{{background:rgba(102,126,234,0.14);}}
td{{padding:9px 12px;font-size:0.8em;vertical-align:middle;}}
.td-text{{
  color:#f0f0ff;font-weight:500;max-width:320px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  cursor:default;
}}
.td-text:hover{{white-space:normal;word-break:break-word;}}
.td-font{{color:#c0b0ff;font-size:0.78em;white-space:nowrap;}}
.td-size{{color:#80deea;font-weight:600;text-align:center;white-space:nowrap;}}
.color-pill{{
  display:inline-flex;align-items:center;gap:5px;
  border-radius:20px;padding:3px 8px;font-size:0.75em;font-weight:700;
  font-family:monospace;white-space:nowrap;
}}
.color-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;border:1px solid rgba(255,255,255,0.2);}}
.badge{{
  display:inline-block;border-radius:20px;padding:2px 8px;
  font-size:0.7em;font-weight:700;white-space:nowrap;
}}
.badge-bold{{background:rgba(255,193,7,0.2);color:#ffd54f;border:1px solid rgba(255,193,7,0.3);}}
.badge-italic{{background:rgba(13,202,240,0.15);color:#80deea;border:1px solid rgba(13,202,240,0.25);}}
.badge-mono{{background:rgba(102,126,234,0.25);color:#9fa8da;border:1px solid rgba(102,126,234,0.35);}}
.td-badges{{display:flex;gap:4px;flex-wrap:wrap;}}
.copy-row-btn{{
  background:rgba(102,126,234,0.2);color:#a78bfa;border:1px solid rgba(102,126,234,0.3);
  border-radius:6px;padding:4px 8px;font-size:0.7em;font-weight:600;cursor:pointer;
  white-space:nowrap;transition:all 0.12s;-webkit-tap-highlight-color:transparent;
}}
.copy-row-btn:hover{{background:rgba(102,126,234,0.4);color:#fff;}}
.copy-row-btn:active{{transform:scale(0.93);}}
.toast{{
  position:fixed;bottom:16px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,0.85);color:#fff;padding:7px 18px;
  border-radius:20px;font-size:0.8em;opacity:0;
  transition:opacity 0.2s;pointer-events:none;z-index:9999;white-space:nowrap;
}}
.toast.show{{opacity:1;}}
.tbl-scroll{{max-height:480px;overflow-y:auto;}}
.tbl-scroll::-webkit-scrollbar{{width:6px;}}
.tbl-scroll::-webkit-scrollbar-track{{background:rgba(255,255,255,0.05);}}
.tbl-scroll::-webkit-scrollbar-thumb{{background:rgba(102,126,234,0.4);border-radius:3px;}}
</style></head><body>

<div class="tbl-wrap">
  <div class="tbl-header">
    <span id="rowCount">Loading...</span>
    <button class="copy-all-btn" onclick="copyAll()">📋 Copy All as CSV</button>
  </div>
  <div class="tbl-scroll">
    <table id="spanTable">
      <thead>
        <tr>
          <th style="width:36%">📝 Text</th>
          <th style="width:22%">🔤 Font</th>
          <th style="width:8%">📏 Size</th>
          <th style="width:12%">🎨 Color</th>
          <th style="width:14%">✨ Flags</th>
          <th style="width:8%">Copy</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
var ROWS = {rows_json};

function render(){{
  var tbody=document.getElementById('tbody');
  var html='';
  ROWS.forEach(function(r,i){{
    var lum=parseInt(r.color.slice(1,3),16)*0.299+parseInt(r.color.slice(3,5),16)*0.587+parseInt(r.color.slice(5,7),16)*0.114;
    var tc=lum>128?'#000':'#fff';
    var badges='';
    if(r.bold)   badges+='<span class="badge badge-bold">B Bold</span>';
    if(r.italic) badges+='<span class="badge badge-italic">I Italic</span>';
    if(r.mono)   badges+='<span class="badge badge-mono">⌨ Mono</span>';
    html+='<tr>'
      +'<td><div class="td-text" title="'+esc(r.text)+'">'+esc(r.text)+'</div></td>'
      +'<td class="td-font">'+esc(r.font)+'</td>'
      +'<td class="td-size">'+r.size+'</td>'
      +'<td><span class="color-pill" style="background:'+r.color+';color:'+tc+';">'
      +'<span class="color-dot" style="background:'+r.color+';"></span>'+r.color+'</span></td>'
      +'<td><div class="td-badges">'+badges+'</div></td>'
      +'<td><button class="copy-row-btn" onclick="copyRow('+i+')">Copy</button></td>'
      +'</tr>';
  }});
  tbody.innerHTML=html;
  document.getElementById('rowCount').textContent=ROWS.length+' text spans';
}}

function esc(s){{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function copyRow(i){{
  var r=ROWS[i];
  var txt=r.text+'\\t'+r.font+'\\t'+r.size+' pt\\t'+r.color
          +(r.bold?' Bold':'')+(r.italic?' Italic':'')+(r.mono?' Mono':'');
  copyText(txt,'Row copy ho gaya ✅');
}}

function copyAll(){{
  var lines=['Text,Font,Size,Color,Bold,Italic,Mono'];
  ROWS.forEach(function(r){{
    lines.push('"'+r.text.replace(/"/g,'""')+'","'+r.font+'",'+r.size+',"'+r.color+'",'+r.bold+','+r.italic+','+r.mono);
  }});
  copyText(lines.join('\\n'),ROWS.length+' rows CSV copy ho gaya ✅');
}}

function copyText(txt,msg){{
  if(navigator.clipboard&&navigator.clipboard.writeText){{
    navigator.clipboard.writeText(txt).then(function(){{showToast(msg);}});
  }}else{{
    var ta=document.createElement('textarea');
    ta.value=txt;ta.style.cssText='position:fixed;opacity:0;top:0;left:0;';
    document.body.appendChild(ta);ta.focus();ta.select();
    try{{document.execCommand('copy');showToast(msg);}}catch(e){{}}
    document.body.removeChild(ta);
  }}
}}

function showToast(msg){{
  var t=document.getElementById('toast');
  t.textContent=msg;t.classList.add('show');
  setTimeout(function(){{t.classList.remove('show');}},2000);
}}

render();
</script>
</body></html>""", height=540, scrolling=False)

                    # CSV download button below
                    df_dl=pd.DataFrame([{"Text":s["text"],"Font":s["font"],
                        "Size(pt)":s["size"],"Color":s["color"],
                        "Bold":s["bold"],"Italic":s["italic"],"Mono":s["mono"]} for s in fspans])
                    st.download_button("⬇ Download Full CSV",df_dl.to_csv(index=False).encode(),
                                       f"spans_p{ipg}.csv","text/csv",use_container_width=True)
                else: st.info("No text found on this page.")

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
    CRYPTO_ADR = "0x9c45F8098D1887EfFe84A4781c877f297D42604A"
    qr_d = make_qr_b64(UPI_LINK)
    enc_u = urllib.parse.quote(UPI_LINK)
    if qr_d:
        qr_img = f'<img src="data:image/png;base64,{qr_d}" style="width:200px;border-radius:12px;display:block;margin:8px auto;border:3px solid #667eea44;box-shadow:0 8px 24px rgba(102,126,234,0.2);"/>'
    else:
        qr_img = f'<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&color=667eea&data={enc_u}" style="width:200px;border-radius:12px;display:block;margin:8px auto;" onerror="this.style.display=\'none\'"/>'

    st.components.v1.html(f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Inter',system-ui,sans-serif;}}
body{{background:#f8f9fa;padding:16px;}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:800px;margin:0 auto;}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr;}}}}
.card{{background:#fff;border-radius:16px;padding:20px;
       box-shadow:0 4px 20px rgba(0,0,0,0.08);text-align:center;}}
.card h3{{font-size:1.05em;margin-bottom:8px;}}
.upi-card h3{{color:#667eea;}}
.crypto-card h3{{color:#7c3aed;}}
.min-badge{{background:#fff3cd;border:1px solid #ffc107;border-radius:20px;
            padding:4px 12px;font-size:0.75em;color:#856404;font-weight:700;
            display:inline-block;margin-bottom:10px;}}
.label{{font-size:0.72em;color:#888;font-weight:600;text-transform:uppercase;
        letter-spacing:0.5px;margin:8px 0 4px;}}
.copy-row{{display:flex;align-items:center;gap:6px;
           background:#f0f2f6;border:2px dashed #667eea;
           border-radius:10px;padding:8px 10px;}}
.copy-row2{{display:flex;align-items:center;gap:6px;
            background:#1a1a2e;border-radius:10px;padding:8px 10px;}}
.upi-txt{{font-family:monospace;font-size:0.95em;font-weight:700;
          color:#667eea;flex:1;text-align:left;}}
.crypto-txt{{font-family:monospace;font-size:0.7em;font-weight:600;
             color:#a78bfa;flex:1;text-align:left;word-break:break-all;}}
.cbtn{{border:none;border-radius:8px;padding:6px 12px;font-weight:700;
       font-size:0.78em;cursor:pointer;flex-shrink:0;transition:all 0.18s;
       -webkit-tap-highlight-color:transparent;}}
.cbtn-upi{{background:#667eea;color:#fff;}}
.cbtn-upi:active{{background:#4f46e5;transform:scale(0.95);}}
.cbtn-crypto{{background:#7c3aed;color:#fff;}}
.cbtn-crypto:active{{background:#5b21b6;transform:scale(0.95);}}
.apps{{font-size:0.72em;color:#aaa;margin-top:6px;}}
.chains{{font-size:0.7em;color:#7c3aed;margin-top:5px;line-height:1.6;}}
.footer{{text-align:center;margin-top:16px;padding:12px;
         background:#fff;border-radius:12px;
         font-size:0.8em;color:#888;max-width:800px;margin:16px auto 0;}}
.toast{{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);
        background:rgba(0,0,0,0.8);color:#fff;padding:8px 20px;
        border-radius:20px;font-size:0.82em;opacity:0;
        transition:opacity 0.25s;pointer-events:none;white-space:nowrap;}}
.toast.show{{opacity:1;}}
</style>
</head>
<body>
<div class="grid">

  <!-- UPI Card -->
  <div class="card upi-card">
    <div style="font-size:1.8em;">🇮🇳</div>
    <h3>UPI / Indian Payment</h3>
    <div class="min-badge">💛 Minimum: ₹10 only</div>
    {qr_img}
    <p style="font-size:0.75em;color:#888;margin-bottom:6px;">
      Scan karo ya UPI ID copy karke kisi bhi app mein bhejo
    </p>
    <div class="label">UPI ID</div>
    <div class="copy-row">
      <span class="upi-txt">{UPI_ID}</span>
      <button class="cbtn cbtn-upi"
        onclick="copyTxt('{UPI_ID}','UPI ID copy ho gaya ✅')">Copy</button>
    </div>
    <p class="apps">GPay · PhonePe · Paytm · BHIM · Any UPI App</p>
  </div>

  <!-- Crypto Card -->
  <div class="card crypto-card">
    <div style="font-size:1.8em;">🌍</div>
    <h3>Crypto / International</h3>
    <div class="min-badge" style="background:#f3e8ff;border-color:#a78bfa;color:#5b21b6;">
      💜 Any amount welcome
    </div>
    <p style="font-size:0.78em;color:#555;margin:6px 0 8px;line-height:1.5;">
      Kisi bhi EVM-compatible chain pe send kar sakte ho.<br>
      ETH, MATIC, BNB, USDT, USDC — sab accept hai!
    </p>
    <div class="label" style="color:#7c3aed;">EVM Wallet Address</div>
    <div class="copy-row2">
      <span class="crypto-txt" id="cryptoAddr">{CRYPTO_ADR}</span>
      <button class="cbtn cbtn-crypto"
        onclick="copyTxt('{CRYPTO_ADR}','Wallet address copy ho gaya ✅')">Copy</button>
    </div>
    <p class="chains">
      ✅ <strong>Chains:</strong> Ethereum · Polygon · BSC · Arbitrum · Optimism · Base<br>
      ✅ <strong>Tokens:</strong> ETH · MATIC · BNB · USDT · USDC · any ERC-20
    </p>
    <p style="font-size:0.7em;color:#aaa;margin-top:8px;">
      MetaMask · Trust Wallet · Coinbase Wallet — koi bhi chalega
    </p>
  </div>

</div>

<div class="footer">
  💙 Donation optional hai — app free hai aur hamesha rahega<br>
  Teri support se aur better features banane ki motivation milti hai! 🚀
</div>

<div class="toast" id="toast"></div>

<script>
function copyTxt(txt, msg) {{
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(txt).then(function(){{ showToast(msg); }});
  }} else {{
    var ta = document.createElement('textarea');
    ta.value = txt; ta.style.cssText = 'position:fixed;opacity:0;';
    document.body.appendChild(ta); ta.focus(); ta.select();
    try {{ document.execCommand('copy'); showToast(msg); }} catch(e) {{}}
    document.body.removeChild(ta);
  }}
}}
function showToast(msg) {{
  var t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(function(){{ t.classList.remove('show'); }}, 2200);
}}
</script>
</body>
</html>
""", height=620, scrolling=True)


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
