import streamlit as st


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;600&family=Fira+Code:wght@400;500&display=swap');
:root{--bg:#141618;--surface:#1c1f23;--surface2:#23282e;--border:#2e333a;--gold:#c8a84b;--gold-dim:#9e7f38;--ivory:#f0ead8;--muted:#8a9099;--text:#dde1e7;--ok:#5a8f6e;--warn:#b8903a;--danger:#c25f5f;--info:#4a7fa5;--r:8px;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.stApp{background:var(--bg);color:var(--text);}
.block-container{padding:1.5rem 2rem;}
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--surface);}::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px;}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border);}
[data-testid="stSidebar"] *{color:var(--text)!important;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:1.5rem;margin-bottom:1rem;}
.card-sm{background:var(--surface2);border:1px solid var(--border);border-radius:var(--r);padding:1rem 1.25rem;margin-bottom:.75rem;}
h1,h2,h3{font-family:'Cormorant Garamond',serif;color:var(--ivory)!important;letter-spacing:.02em;}
h1{font-size:2.1rem;font-weight:600;margin-bottom:.2rem;}h2{font-size:1.55rem;font-weight:500;}h3{font-size:1.2rem;font-weight:500;}
.stTextInput>div>div>input,[data-baseweb="select"] div{background:var(--surface2)!important;border-color:var(--border)!important;color:var(--text)!important;border-radius:var(--r)!important;}
.stTextInput>div>div>input:focus{border-color:var(--gold)!important;box-shadow:0 0 0 2px rgba(200,168,75,.15)!important;}
label{color:var(--muted)!important;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;}
.stButton>button{background:transparent;border:1px solid var(--gold-dim);color:var(--gold)!important;border-radius:var(--r);font-weight:500;letter-spacing:.04em;padding:.45rem 1.5rem;transition:all .2s ease;}
.stButton>button:hover{background:rgba(200,168,75,.1);border-color:var(--gold);box-shadow:0 0 12px rgba(200,168,75,.12);}
.btn-primary .stButton>button{background:var(--gold)!important;color:#111!important;border-color:var(--gold)!important;font-weight:600;}
.btn-primary .stButton>button:hover{background:#d4ad50!important;box-shadow:0 4px 16px rgba(200,168,75,.3)!important;}
.stProgress>div>div>div{background:var(--gold)!important;border-radius:4px;}
[data-testid="stMetric"]{background:var(--surface2);border:1px solid var(--border);border-radius:var(--r);padding:1rem;}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;}
[data-testid="stMetricValue"]{color:var(--ivory)!important;font-family:'Cormorant Garamond',serif;font-size:1.9rem;}
.stDataFrame{border:1px solid var(--border)!important;border-radius:var(--r)!important;}
.stDataFrame thead tr th{background:var(--surface2)!important;color:var(--gold)!important;border-bottom:1px solid var(--border)!important;font-size:.76rem;text-transform:uppercase;}
.stat-card{background:var(--surface2);border:1px solid var(--border);border-radius:var(--r);padding:1.2rem 1.5rem;}
.stat-label{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:.3rem;}
.stat-value{font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:600;color:var(--ivory);line-height:1.1;}
.stat-sub{font-size:.76rem;color:var(--muted);margin-top:.25rem;}.stat-gold{color:var(--gold);}
.hero-banner{background:linear-gradient(135deg,var(--surface2) 0%,#1a1e24 100%);border:1px solid var(--border);border-radius:10px;padding:1.8rem 2.2rem;position:relative;overflow:hidden;margin-bottom:1.5rem;}
.hero-banner::before{content:'KRA';position:absolute;right:-12px;top:-18px;font-family:'Cormorant Garamond',serif;font-size:8rem;font-weight:700;color:rgba(200,168,75,.04);pointer-events:none;}
.hero-time{font-size:.78rem;color:var(--muted);margin-top:.2rem;}
.step-bar{display:flex;align-items:center;margin-bottom:2rem;}
.step-item{display:flex;flex-direction:column;align-items:center;flex:1;position:relative;}
.step-item:not(:last-child)::after{content:'';position:absolute;top:16px;left:55%;width:90%;height:1px;background:var(--border);z-index:0;}
.step-item.done::after{background:var(--gold);}
.step-circle{width:32px;height:32px;border-radius:50%;border:2px solid var(--border);background:var(--surface2);color:var(--muted);font-size:.8rem;font-weight:600;display:flex;align-items:center;justify-content:center;position:relative;z-index:1;}
.step-circle.active{border-color:var(--gold);color:var(--gold);background:rgba(200,168,75,.1);box-shadow:0 0 12px rgba(200,168,75,.2);}
.step-circle.done{border-color:var(--ok);color:var(--ok);background:rgba(90,143,110,.1);}
.step-label{font-size:.7rem;color:var(--muted);margin-top:6px;text-transform:uppercase;letter-spacing:.07em;}
.step-label.active{color:var(--gold);}
.kra-wordmark{font-family:'Cormorant Garamond',serif;font-size:1.45rem;font-weight:700;color:var(--ivory);letter-spacing:.06em;}
.kra-wordmark span{color:var(--gold);}
[data-testid="stFileUploadDropzone"]{background:var(--surface2)!important;border:1px dashed var(--border)!important;border-radius:var(--r)!important;}
[data-testid="stFileUploadDropzone"]:hover{border-color:var(--gold)!important;}
.stSpinner>div{border-top-color:var(--gold)!important;}
.stSuccess{background:rgba(90,143,110,.1)!important;border-left:3px solid var(--ok)!important;color:#7ec89b!important;}
.stError{background:rgba(194,95,95,.1)!important;border-left:3px solid var(--danger)!important;color:#e08080!important;}
.stWarning{background:rgba(184,144,58,.1)!important;border-left:3px solid var(--warn)!important;color:#d4a84b!important;}
.stInfo{background:rgba(74,127,165,.1)!important;border-left:3px solid var(--info)!important;color:#7aafd0!important;}
</style>
"""


KRA_LOGO = """<svg width="44" height="44" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <polygon points="24,3 44,10 44,30 24,45 4,30 4,10" fill="none" stroke="#c8a84b" stroke-width="1.5"/>
  <polygon points="24,7 40,13 40,29 24,41 8,29 8,13" fill="#1c1f23" stroke="#c8a84b" stroke-width="0.7"/>
  <circle cx="24" cy="24" r="8" fill="none" stroke="#c8a84b" stroke-width="1.2"/>
  <text x="24" y="27.5" text-anchor="middle" font-family="serif" font-size="7" font-weight="bold" fill="#c8a84b">KRA</text>
</svg>"""


def step_bar(current):
    steps = ["Upload", "Mapping", "Processing", "Results"]
    parts = []
    for i, s in enumerate(steps, 1):
        cls = "done" if i < current else ""
        circ = "done" if i < current else ("active" if i == current else "")
        lbl = "active" if i == current else ""
        sym = "\u2713" if i < current else str(i)
        parts.append(f"<div class='step-item {cls}'><div class='step-circle {circ}'>{sym}</div><div class='step-label {lbl}'>{s}</div></div>")
    st.markdown(f"<div class='step-bar'>{''.join(parts)}</div>", unsafe_allow_html=True)

