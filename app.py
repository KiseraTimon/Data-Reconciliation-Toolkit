import os
import sys
import json
import tempfile
import traceback
import concurrent.futures
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from modules.scrapper import Scrapper
from modules import Scanner, Validator
from modules.reconciler import EnhancedReconciler
from ai_assistant import AIAssistant
from utils import errhandler, syshandler, times

st.set_page_config(page_title="KRA \u2014 Records Reconciler", page_icon="\u2696\ufe0f",
                   layout="wide", initial_sidebar_state="expanded")

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


import uuid

@st.cache_resource
def get_session_store():
    """Stores user sessions globally across page refreshes."""
    return {}

def sync_session_state():
    """Saves the current user's state to the global store."""
    if "sid" in st.session_state and st.session_state.get('authenticated'):
        store = get_session_store()
        sid = st.session_state["sid"]
        store[sid] = {
            'authenticated': st.session_state.authenticated,
            'scrapper': st.session_state.scrapper,
            'step': st.session_state.step,
            'reconciled_data': st.session_state.get('reconciled_data'),
            'uploaded_df': st.session_state.get('uploaded_df'),
            'case_num_col': st.session_state.get('case_num_col'),
            'citation_col': st.session_state.get('citation_col'),
            'chat_history': st.session_state.get('chat_history', []),
            'temp_file_path': st.session_state.get('temp_file_path'),
            'current_page': st.session_state.get('current_page', 'Dashboard'),
        }

def _init():
    store = get_session_store()

    if "sid" in st.query_params:
        sid = st.query_params["sid"]
        if sid in store:
            st.session_state["sid"] = sid
            for k, v in store[sid].items():
                if k not in st.session_state:
                    st.session_state[k] = v

    defaults = {
        'authenticated': False,
        'chat_history': [],
        'step': 1,
        'temp_file_path': None,
        'scrapper': None,
        'uploaded_df': None,
        'case_num_col': None,
        'citation_col': None,
        'reconciled_data': None,
        'ai_assistant': None,
        'workers': 8,
        'current_page': 'Dashboard',
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.ai_assistant is None:
        try:
            st.session_state.ai_assistant = AIAssistant()
        except Exception:
            pass


def parallel_extract(scrapper, file_data, workers=8):
    import urllib.parse
    import json as _json

    ajax_hdrs = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://ilaw.kra.go.ke/ilaw/search/universal",
    }
    payload = {"dataType": "litigation_data"}

    def fetch_one(item):
        try:
            resp = scrapper.session.post(
                f"{scrapper.url}{urllib.parse.quote(item['keyword'])}",
                data=payload,
                headers=ajax_hdrs,
                timeout=30,
            )
            if resp.status_code != 200:
                return scrapper._empty_result(item)
            try:
                jd = resp.json()
            except _json.JSONDecodeError:
                return scrapper._empty_result(item)
            html = jd.get('html', '')
            if not html:
                return {**scrapper._empty_result(item), 'matches': [], 'matches_found': 0}
            matches = scrapper._parse_results(html)
            return {
                "excel_row": item.get('excel_row'),
                "original_case": item['case_number'],
                "case_name": item['citation'],
                "search_keyword": item['keyword'],
                "matches_found": len(matches),
                "matches": matches,
            }
        except Exception:
            return scrapper._empty_result(item)

    results = [None] * len(file_data)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_one, item): i for i, item in enumerate(file_data)}
        for fut in concurrent.futures.as_completed(futures):
            idx = futures[fut]
            try:
                results[idx] = fut.result()
            except Exception:
                results[idx] = scrapper._empty_result(file_data[idx])
    return results


def login_page():
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none}.block-container{padding:0!important}</style>",
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("<div style='height:7vh'></div>", unsafe_allow_html=True)
        logo_big = KRA_LOGO.replace('width="44"', 'width="62"').replace('height="44"', 'height="62"')
        st.markdown(
            f"""<div style='text-align:center;margin-bottom:2.2rem;'>{logo_big}
            <div style='margin-top:1rem;font-family:"Cormorant Garamond",serif;font-size:2rem;font-weight:700;color:#f0ead8;letter-spacing:.1em;'>KRA</div>
            <div style='font-size:.72rem;color:#8a9099;letter-spacing:.18em;text-transform:uppercase;margin-top:3px;'>KRA Intelligent Reconciliation Assistant</div>
        </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='card' style='padding:2.2rem;'>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#8a9099;font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:1.2rem;'>Sign in with your KRA credentials</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#8a9099;font-size:.73rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px;'>Username</p>",
            unsafe_allow_html=True,
        )
        st.text_input("Username", placeholder="", key="lu", label_visibility="hidden")
        st.markdown(
            "<p style='color:#8a9099;font-size:.73rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px;margin-top:.5rem;'>Password</p>",
            unsafe_allow_html=True,
        )
        st.text_input("Password", type="password", placeholder="", key="lp", label_visibility="hidden")
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        login_btn = st.button("Connect to KRA iLaw \u2192", use_container_width=True, key="lbtn")
        st.markdown('</div>', unsafe_allow_html=True)
        if login_btn:
            username = st.session_state.get("lu", "").strip()
            password = st.session_state.get("lp", "").strip()
            if not username or not password:
                st.error("Enter both username and password.")
            else:
                with st.spinner("Authenticating\u2026"):
                    sc = Scrapper(username=username, password=password)

                    if sc.authenticator():

                        sid = str(uuid.uuid4())
                        st.session_state["sid"] = sid
                        st.query_params["sid"] = sid

                        st.session_state.scrapper = sc
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Authentication failed. Check your credentials.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center;margin-top:1.4rem;color:#3e4550;font-size:.72rem;'>Use your authorised KRA iLaw credentials only.</div>",
            unsafe_allow_html=True,
        )

        with st.expander("🔬 Login not working? Run diagnostics"):
            st.markdown(
                "<p style='color:#8a9099;font-size:.8rem;'>Enter your credentials below to see exactly what KRA iLaw returns — this reveals the real cause of any login failure.</p>",
                unsafe_allow_html=True,
            )
            with st.form("diag_f"):
                dg_u = st.text_input("Username (diag)", key="dg_u", label_visibility="hidden")
                dg_p = st.text_input("Password (diag)", type="password", key="dg_p", label_visibility="hidden")
                run_diag = st.form_submit_button("Run Diagnostics", use_container_width=True)
            if run_diag:
                import requests as _rq
                from bs4 import BeautifulSoup as _BS

                AUTH_URL = "https://ilaw.kra.go.ke/ilaw/users/login"
                _u = st.session_state.get("dg_u", "").strip()
                _p = st.session_state.get("dg_p", "").strip()
                if not _u or not _p:
                    st.warning("Enter credentials above.")
                else:
                    with st.spinner("Probing KRA iLaw\u2026"):
                        try:
                            sess = _rq.Session()
                            sess.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                            r1 = sess.get(AUTH_URL, timeout=15)
                            st.markdown(f"**GET login page** \u2192 `{r1.status_code}` \u00b7 `{r1.url}`")
                            soup = _BS(r1.text, "html.parser")
                            rows = [{"name": i.get("name", "\u2014"), "type": i.get("type", "text"), "id": i.get("id", "\u2014")} for i in soup.find_all("input")]
                            st.markdown("**Form inputs on login page:**")
                            st.table(rows)
                            hidden = {}
                            ufield = pfield = None
                            SKIP = {"redirect_to", "csrf_token", "_token", "authenticity_token", "token", "submit"}
                            for i in soup.find_all("input"):
                                t = (i.get("type") or "text").lower()
                                n = (i.get("name") or "")
                                if t == "hidden" and n:
                                    hidden[n] = i.get("value", "")
                                if t == "password" and not pfield:
                                    pfield = n
                                if t in ("text", "email") and n.lower() not in SKIP and not ufield:
                                    ufield = n
                            ufield = ufield or "username"
                            pfield = pfield or "password"
                            payload = {ufield: _u, pfield: _p}
                            payload.update(hidden)
                            st.markdown(f"**POST payload keys:** `{list(payload.keys())}`")
                            r2 = sess.post(
                                AUTH_URL,
                                data=payload,
                                headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": AUTH_URL, "Origin": "https://ilaw.kra.go.ke"},
                                allow_redirects=True,
                                timeout=30,
                            )
                            st.markdown(f"**POST response** \u2192 `{r2.status_code}` \u00b7 `{r2.url}`")
                            soup2 = _BS(r2.text, "html.parser")
                            for tag in soup2(["script", "style", "head"]):
                                tag.decompose()
                            body = " ".join(soup2.get_text(" ", strip=True).split())[:1000]
                            st.markdown("**Page content after POST:**")
                            st.code(body, language="text")
                            alerts = [
                                e.get_text(strip=True)
                                for e in soup2.find_all(class_=lambda c: c and any(x in c for x in ["alert", "error", "flash", "message", "notice", "danger", "warning"]))
                                if e.get_text(strip=True)
                            ]
                            if alerts:
                                st.markdown("**\u26a0\ufe0f Messages on page:**")
                                for a in alerts:
                                    st.warning(a)
                        except Exception as ex:
                            st.error(f"Diagnostic error: {ex}")


def sidebar_nav():
    with st.sidebar:
        st.markdown(
            f"""<div style='display:flex;align-items:center;gap:11px;padding:1rem .5rem .5rem;'>{KRA_LOGO}
            <div><div class='kra-wordmark'>KI<span>R</span>A</div>
            <div style='font-size:.62rem;color:#8a9099;letter-spacing:.1em;'>RECONCILIATION v2</div></div></div>
            <div style='height:1px;background:var(--border);margin:1rem 0;'></div>""",
            unsafe_allow_html=True,
        )

        # 1. Define your options
        options = ["Dashboard", "Reconciliation", "Reports", "AI Assistant", "Settings"]

        # 2. Find the index of the current page (default to 0 if something goes wrong)
        try:
            default_idx = options.index(st.session_state.get('current_page', 'Dashboard'))
        except ValueError:
            default_idx = 0

        # 3. Pass the dynamic index to the menu
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=["grid", "arrow-repeat", "file-earmark-bar-graph", "robot", "gear"],
            default_index=default_idx,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "#8a9099", "font-size": "14px"},
                "nav-link": {"font-size": "0.87rem", "color": "#8a9099", "padding": "0.55rem 1rem", "border-radius": "6px", "margin-bottom": "2px"},
                "nav-link-selected": {"background-color": "rgba(200,168,75,0.1)", "color": "#c8a84b", "font-weight": "500"},
            },
        )

        # 4. Save the user's selection to state so it gets picked up by sync_session_state()
        st.session_state.current_page = selected

        st.markdown("<div style='height:1px;background:var(--border);margin:1rem 0;'></div>", unsafe_allow_html=True)
        if st.session_state.authenticated:
            uname = st.session_state.scrapper.username if st.session_state.scrapper else "—"
            st.markdown(
                f"""<div class='card-sm'><div style='font-size:.68rem;color:#8a9099;text-transform:uppercase;letter-spacing:.07em;'>Session</div>
                <div style='color:#7ec89b;font-size:.83rem;margin-top:3px;'>● Connected</div>
                <div style='font-size:.7rem;color:#8a9099;margin-top:2px;font-family:"Fira Code",monospace;'>{uname}</div></div>""",
                unsafe_allow_html=True,
            )
            if st.button("Sign Out", use_container_width=True):
                # Remove from global store and clear URL parameters
                if "sid" in st.session_state:
                    store = get_session_store()
                    store.pop(st.session_state["sid"], None)
                    st.query_params.clear()

                for k in ['authenticated', 'scrapper', 'reconciled_data', 'uploaded_df', 'case_num_col', 'citation_col']:
                    st.session_state[k] = False if k == 'authenticated' else None
                st.session_state.step = 1
                st.session_state.current_page = 'Dashboard' # Reset page on logout
                st.rerun()

    return selected


def dashboard():
    hour = datetime.now().hour
    greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
    now = datetime.now().strftime("%A, %d %B %Y  \u00b7  %H:%M")
    data = st.session_state.get('reconciled_data') or []
    total = len(data)
    verified = sum(1 for d in data if d.get('status') == 'VERIFIED MATCH')
    review = sum(1 for d in data if d.get('status') == 'REVIEW REQUIRED')
    mismatch = sum(1 for d in data if d.get('status') == 'MISMATCH')
    nf = sum(1 for d in data if d.get('status') == 'NOT FOUND')

    st.markdown(
        f"""<div class='hero-banner'><div style='font-size:.72rem;color:#8a9099;text-transform:uppercase;letter-spacing:.12em;'>{greet}</div>
        <h1 style='margin:.15rem 0 .05rem;'>Reconciliation Dashboard</h1>
        <div class='hero-time'>{now}</div></div>""",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)

    def stat(col, lbl, val, sub, gold=False):
        col.markdown(
            f"""<div class='stat-card'><div class='stat-label'>{lbl}</div>
            <div class='stat-value {"stat-gold" if gold else ""}'>{val}</div>
            <div class='stat-sub'>{sub}</div></div>""",
            unsafe_allow_html=True,
        )

    if total:
        stat(c1, "Total Records", total, "this session")
        stat(c2, "Verified Match", verified, f"{verified/total*100:.1f}%", gold=True)
        stat(c3, "Under Review", review, f"{review/total*100:.1f}%")
        stat(c4, "Issues", mismatch + nf, f"{(mismatch+nf)/total*100:.1f}%")
    else:
        for c, l in zip([c1, c2, c3, c4], ["Total Records", "Verified Match", "Under Review", "Issues"]):
            stat(c, l, "\u2014", "no data yet")

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    ch1, ch2 = st.columns([3, 2])
    with ch1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Session Results</h3>", unsafe_allow_html=True)
        if total:
            fig = go.Figure(
                go.Bar(
                    x=['Verified', 'Review Req.', 'Mismatch', 'Not Found'],
                    y=[verified, review, mismatch, nf],
                    marker_color=['#5a8f6e', '#b8903a', '#c25f5f', '#4a7fa5'],
                    text=[verified, review, mismatch, nf],
                    textposition='outside',
                    textfont=dict(color='#8a9099', size=11),
                )
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8a9099', family='DM Sans'), height=250,
                margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
                xaxis=dict(showgrid=False, color='#8a9099'),
                yaxis=dict(showgrid=True, gridcolor='#2e333a', color='#8a9099'),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<p style='color:#8a9099;text-align:center;padding:3rem 0;'>Run a reconciliation to see results.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with ch2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Status Split</h3>", unsafe_allow_html=True)
        if total:
            fig2 = go.Figure(
                go.Pie(
                    labels=['Verified', 'Review', 'Mismatch', 'Not Found'],
                    values=[max(verified, .01), max(review, .01), max(mismatch, .01), max(nf, .01)],
                    hole=.62,
                    marker=dict(colors=['#5a8f6e', '#b8903a', '#c25f5f', '#4a7fa5'], line=dict(color='#1c1f23', width=2)),
                    textinfo='none',
                )
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8a9099', family='DM Sans'), height=250,
                margin=dict(l=0, r=0, t=10, b=0), showlegend=True,
                legend=dict(orientation='v', font=dict(color='#8a9099', size=11), bgcolor='rgba(0,0,0,0)'),
                annotations=[dict(text=str(total), x=.5, y=.5, font=dict(size=20, color='#f0ead8', family='Cormorant Garamond'), showarrow=False)],
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown("<p style='color:#8a9099;text-align:center;padding:3rem 0;'>No data yet.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Quick Actions</h3>", unsafe_allow_html=True)
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("\u2295  New Reconciliation", use_container_width=True):
            st.session_state.step = 1
    with qa2:
        rdir = Path("reports")
        files = sorted(rdir.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True) if rdir.exists() else []
        if files:
            with open(files[0], 'rb') as fh:
                st.download_button(
                    "\u2b07  Last Report", fh.read(), file_name=files[0].name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        else:
            st.button("\u2b07  Last Report", disabled=True, use_container_width=True)
    with qa3:
        if st.button("\u2715  Clear Session", use_container_width=True):
            st.session_state.reconciled_data = None
            st.session_state.uploaded_df = None
            st.session_state.step = 1
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


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


def reconciliation_page():
    st.markdown("<h1>Data Reconciliation</h1>", unsafe_allow_html=True)
    current = st.session_state.step
    step_bar(current)

    if current == 1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2>Upload Case File</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#8a9099;font-size:.88rem;'>Upload your Excel or CSV containing case numbers and citations.</p>", unsafe_allow_html=True)
        uploaded = st.file_uploader("File", type=['csv', 'xlsx'], label_visibility="hidden")
        if uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
                tmp.write(uploaded.getvalue())
                st.session_state.temp_file_path = tmp.name
            try:
                df = pd.read_csv(uploaded) if uploaded.name.endswith('.csv') else pd.read_excel(uploaded)
                st.session_state.uploaded_df = df
                st.session_state.uploaded_file_name = uploaded.name
                st.success(f"Loaded **{uploaded.name}** \u2014 {len(df):,} rows \u00d7 {len(df.columns)} columns")
                st.dataframe(df.head(8), use_container_width=True, height=260)
            except Exception as e:
                st.error(f"Error reading file: {e}")
        _, cc, _ = st.columns([2, 1, 2])
        with cc:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Next \u2192", use_container_width=True) and st.session_state.uploaded_df is not None:
                st.session_state.step = 2
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif current == 2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2>Column Mapping</h2>", unsafe_allow_html=True)
        df = st.session_state.uploaded_df
        cols = df.columns.tolist()
        c1, c2 = st.columns(2)
        with c1:
            cn_col = st.selectbox("Case Number Column", ['-- select --'] + cols)
        with c2:
            cit_col = st.selectbox("Citation Column", ['-- select --'] + cols)
        bc1, _, bc3 = st.columns([1, 1, 1])
        with bc1:
            if st.button("\u2190 Back", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with bc3:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Continue \u2192", use_container_width=True):
                if cn_col == '-- select --' or cit_col == '-- select --':
                    st.error("Select both columns.")
                else:
                    st.session_state.case_num_col = cn_col
                    st.session_state.citation_col = cit_col
                    st.session_state.step = 3
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif current == 3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2>Processing</h2>", unsafe_allow_html=True)
        if not st.session_state.authenticated or not st.session_state.scrapper:
            st.error("Not connected to KRA iLaw. Please sign in first.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        workers = st.session_state.get('workers', 8)

        # Guard: Only runs if we haven't processed this batch yet
        if st.session_state.get('reconciled_data') is None:
            pb = st.progress(0)
            msg = st.empty()
            sub = st.empty()
            try:
                msg.markdown("<span style='color:#c8a84b'>⧡ Extracting records from file…</span>", unsafe_allow_html=True)
                pb.progress(5)
                scanner = Scanner(case_num_column=st.session_state.case_num_col, citation_column=st.session_state.citation_col)
                file_data = scanner.file_extractor(sheet=st.session_state.uploaded_df)
                if not file_data:
                    st.error("No data extracted.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                sub.markdown(f"<span style='color:#8a9099;font-size:.85rem;'>→ {len(file_data)} records</span>", unsafe_allow_html=True)

                pb.progress(15)
                msg.markdown(f"<span style='color:#c8a84b'>⧡ Searching KRA iLaw ({workers} parallel workers)…</span>", unsafe_allow_html=True)
                st.session_state.scrapper.data = file_data
                extracted = parallel_extract(st.session_state.scrapper, file_data, workers=workers)

                pb.progress(72)
                sub.markdown(f"<span style='color:#8a9099;font-size:.85rem;'>→ {len(extracted)} records searched</span>", unsafe_allow_html=True)

                msg.markdown("<span style='color:#c8a84b'>⧡ Comparing & scoring…</span>", unsafe_allow_html=True)
                reconciled = st.session_state.scrapper.comparator(extracted_data=extracted)

                # Saving the data
                st.session_state.reconciled_data = reconciled

                pb.progress(100)
                msg.markdown("<span style='color:#7ec89b'>✓ Reconciliation complete</span>", unsafe_allow_html=True)
                sub.empty()

                # Auto Transition to results step
                st.session_state.step = 4
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
                errhandler(e, log="reconciliation", path="app")
                traceback.print_exc()
        else:
            # Fallback in case Streamlit re-renders Step 3 but data already exists
            st.session_state.step = 4
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    elif current == 4:
        data = st.session_state.reconciled_data or []
        if not data:
            st.warning("No reconciliation data.")
            if st.button("Start New"):
                st.session_state.step = 1
                st.rerun()
            return
        total = len(data)
        verified = sum(1 for d in data if d.get('status') == 'VERIFIED MATCH')
        review = sum(1 for d in data if d.get('status') == 'REVIEW REQUIRED')
        mismatch = sum(1 for d in data if d.get('status') == 'MISMATCH')
        nf = sum(1 for d in data if d.get('status') == 'NOT FOUND')
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2>Results</h2>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("Verified", verified, f"{verified/total*100:.1f}%")
        m3.metric("Review", review, f"{review/total*100:.1f}%")
        m4.metric("Issues", mismatch + nf, f"{(mismatch+nf)/total*100:.1f}%")
        rows = []
        for d in data:
            cit = d.get('case_name', '')
            km = d.get('best_match_kra_citation', '')
            rows.append({
                'Row': d.get('excel_row', ''),
                'Case No.': d.get('original_case', ''),
                'Citation': cit[:55] + '\u2026' if len(cit) > 55 else cit,
                'Status': d.get('status', ''),
                'Confidence': d.get('confidence_score', ''),
                'KRA Match': km[:55] + '\u2026' if len(km) > 55 else km,
                'KRA Ref': d.get('best_match_kra_ref', ''),
            })
        df_res = pd.DataFrame(rows)

        def color_status(s):
            p = {
                'VERIFIED MATCH': 'background-color:#1a3326;color:#7ec89b',
                'REVIEW REQUIRED': 'background-color:#2e2006;color:#d4a84b',
                'MISMATCH': 'background-color:#2d1212;color:#e08080',
                'NOT FOUND': 'background-color:#0e1c2c;color:#7aafd0',
            }
            return [p.get(v, '') for v in s]

        st.dataframe(df_res.style.apply(color_status, subset=['Status'], axis=0), use_container_width=True, height=420)
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("\u2b07 Excel Report", use_container_width=True):
                fp = st.session_state.temp_file_path
                if fp and os.path.exists(fp):
                    with st.spinner("Building\u2026"):
                        if st.session_state.scrapper.report(data=data, file_path=fp):
                            st.success("Saved to /reports")
                        else:
                            st.error("Failed.")
                else:
                    st.error("Source file missing.")
            st.markdown('</div>', unsafe_allow_html=True)
        with ec2:
            csv_b = df_res.to_csv(index=False).encode()
            st.download_button(
                "\u2b07 Export CSV", csv_b,
                file_name=f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv", use_container_width=True,
            )
        with ec3:
            if st.button("\u2295 New Reconciliation", use_container_width=True):
                st.session_state.step = 1
                st.session_state.reconciled_data = None
                st.session_state.uploaded_df = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def reports_page():
    st.markdown("<h1>Reports</h1>", unsafe_allow_html=True)
    rdir = Path("reports")
    rdir.mkdir(exist_ok=True)
    files = sorted(list(rdir.glob("*.xlsx")) + list(rdir.glob("*.csv")), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        st.markdown("<div class='card'><p style='color:#8a9099;text-align:center;padding:3rem 0;'>No reports yet. Complete a reconciliation first.</p></div>", unsafe_allow_html=True)
        return
    rows = [{'Name': f.name, 'Type': f.suffix[1:].upper(), 'Date': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M'), 'Size': f"{f.stat().st_size/1024:.1f} KB"} for f in files]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    rc1, rc2 = st.columns([2, 1])
    with rc1:
        sel = st.selectbox("Report", [f.name for f in files], label_visibility="hidden")
    with rc2:
        rp = rdir / sel
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if sel.endswith('.xlsx') else "text/csv"
        with open(rp, 'rb') as fh:
            st.download_button("\u2b07 Download", fh.read(), file_name=sel, mime=mime, use_container_width=True)
    if st.button("\U0001f5d1 Clear All Reports", use_container_width=True):
        for f in files:
            try:
                f.unlink()
            except Exception:
                pass
        st.rerun()


def ai_assistant_page():
    st.markdown("<h1>AI Assistant \u2014 KRA</h1>", unsafe_allow_html=True)
    assistant = st.session_state.ai_assistant
    ac1, ac2 = st.columns([2, 1])
    with ac1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        chat_html = ""
        if not st.session_state.chat_history:
            chat_html = "<div style='background:rgba(200,168,75,.06);border:1px solid rgba(200,168,75,.18);border-radius:0 8px 8px 8px;padding:.9rem 1rem;max-width:85%;color:#c8a84b;font-size:.88rem;'>Hello. I\u2019m KRA \u2014 your legal reconciliation assistant. How can I help?</div>"
        else:
            for m in st.session_state.chat_history:
                if m['role'] == 'ai':
                    chat_html += f"<div style='background:rgba(200,168,75,.06);border:1px solid rgba(200,168,75,.15);border-radius:0 8px 8px 8px;padding:.85rem 1rem;margin:.4rem 0;max-width:85%;color:#dde1e7;font-size:.87rem;'>{m['content']}</div>"
                else:
                    chat_html += f"<div style='background:rgba(255,255,255,.04);border:1px solid #2e333a;border-radius:8px 0 8px 8px;padding:.85rem 1rem;margin:.4rem 0 .4rem auto;max-width:85%;color:#dde1e7;font-size:.87rem;text-align:right;'>{m['content']}</div>"
        st.markdown(f"<div style='min-height:280px;max-height:400px;overflow-y:auto;margin-bottom:1rem;'>{chat_html}</div>", unsafe_allow_html=True)
        with st.form("cf", clear_on_submit=True):
            ui = st.text_input("Message", placeholder="Ask about your reconciliation\u2026", label_visibility="hidden")
            if st.form_submit_button("Send \u2192", use_container_width=True) and ui:
                st.session_state.chat_history.append({'role': 'user', 'content': ui})
                resp = assistant.get_response(ui, st.session_state.get('reconciled_data')) if assistant else "AI not available."
                st.session_state.chat_history.append({'role': 'ai', 'content': resp})
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with ac2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Suggested Questions</h3>", unsafe_allow_html=True)
        for q in [
            "What does VERIFIED MATCH mean?",
            "Explain REVIEW REQUIRED",
            "How is confidence scored?",
            "Summarise my results",
            "What courts are on KRA iLaw?",
            "Help with column mapping",
        ]:
            if st.button(q, use_container_width=True, key=f"sq_{q[:10]}"):
                st.session_state.chat_history.append({'role': 'user', 'content': q})
                resp = assistant.get_response(q, st.session_state.get('reconciled_data')) if assistant else "AI not available."
                st.session_state.chat_history.append({'role': 'ai', 'content': resp})
                st.rerun()
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def settings_page():
    st.markdown("<h1>Settings</h1>", unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>KRA iLaw Connection</h3>", unsafe_allow_html=True)
        with st.form("kra_s"):
            cur = st.session_state.scrapper
            username = st.text_input("Username", value=cur.username if cur else "", placeholder="", label_visibility="hidden")
            password = st.text_input("Password", type="password", placeholder="", label_visibility="hidden")
            if st.form_submit_button("Update & Test", use_container_width=True):
                if username and password:
                    ts = Scrapper(username=username, password=password)
                    with st.spinner("Testing\u2026"):
                        if ts.authenticator():
                            st.session_state.scrapper = ts
                            st.session_state.authenticated = True
                            st.success("Connection successful.")
                        else:
                            st.error("Connection failed.")
                else:
                    st.warning("Enter both fields.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>🔬 Auth Diagnostics</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#8a9099;font-size:.82rem;'>Inspect exactly what KRA iLaw returns — use this to diagnose login failures.</p>", unsafe_allow_html=True)
        with st.form("diag_form"):
            d_user = st.text_input("Username", key="d_u", label_visibility="hidden")
            d_pass = st.text_input("Password", type="password", key="d_p", label_visibility="hidden")
            run_diag = st.form_submit_button("Run Diagnostics", use_container_width=True)
        if run_diag:
            import requests as _req
            from bs4 import BeautifulSoup as _BS

            AUTH_URL = "https://ilaw.kra.go.ke/ilaw/users/login"
            d_user = st.session_state.get("d_u", "").strip()
            d_pass = st.session_state.get("d_p", "").strip()
            if not d_user or not d_pass:
                st.warning("Enter credentials above first.")
            else:
                with st.spinner("Probing KRA iLaw login page\u2026"):
                    try:
                        sess = _req.Session()
                        sess.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                        r1 = sess.get(AUTH_URL, timeout=15)
                        st.markdown("**Step 1 \u2014 GET login page**")
                        st.code(f"Status : {r1.status_code}\nURL    : {r1.url}", language="text")
                        soup = _BS(r1.text, "html.parser")
                        inputs = [{"name": inp.get("name", ""), "type": inp.get("type", "text"), "id": inp.get("id", ""), "value": inp.get("value", "")[:40] if inp.get("value") else ""} for inp in soup.find_all("input")]
                        st.markdown("**Form inputs detected:**")
                        st.table(inputs)
                        hidden = {}
                        ufield = pfield = None
                        SKIP = {"redirect_to", "csrf_token", "_token", "authenticity_token", "token", "submit"}
                        for inp in soup.find_all("input"):
                            t = (inp.get("type") or "text").lower()
                            n = (inp.get("name") or "")
                            if t == "hidden" and n:
                                hidden[n] = inp.get("value", "")
                            if t == "password" and not pfield:
                                pfield = n
                            if t in ("text", "email") and n.lower() not in SKIP and not ufield:
                                ufield = n
                        if not ufield:
                            ufield = "username"
                        if not pfield:
                            pfield = "password"
                        payload = {ufield: d_user, pfield: d_pass}
                        payload.update(hidden)
                        st.markdown(f"**Step 2 \u2014 POST payload fields:** `{list(payload.keys())}`")
                        r2 = sess.post(
                            AUTH_URL, data=payload,
                            headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": AUTH_URL, "Origin": "https://ilaw.kra.go.ke"},
                            allow_redirects=True, timeout=30,
                        )
                        st.markdown("**Step 3 \u2014 POST response:**")
                        st.code(f"Status : {r2.status_code}\nURL    : {r2.url}", language="text")
                        soup2 = _BS(r2.text, "html.parser")
                        for tag in soup2(["script", "style", "head"]):
                            tag.decompose()
                        body_text = " ".join(soup2.get_text(" ", strip=True).split())[:800]
                        st.markdown("**Page text after login attempt:**")
                        st.code(body_text, language="text")
                        alerts = [el.get_text(strip=True) for el in soup2.find_all(class_=lambda c: c and any(x in c for x in ["alert", "error", "flash", "message", "notice", "danger", "warning"]))]
                        if alerts:
                            st.markdown("**\u26a0\ufe0f Alert / error messages on page:**")
                            for a in alerts:
                                st.warning(a)
                        else:
                            st.success("No error alerts detected on the response page.")
                    except Exception as ex:
                        st.error(f"Diagnostic error: {ex}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>\u26a1 Processing Speed</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#8a9099;font-size:.83rem;'>More workers = faster processing. Keep below 15 to avoid rate-limiting KRA servers.</p>", unsafe_allow_html=True)
        w = st.slider("Parallel Workers", 1, 20, st.session_state.get('workers', 8))
        if st.button("Save", use_container_width=True):
            st.session_state.workers = w
            st.success(f"Set to {w} workers.")
        st.markdown("</div>", unsafe_allow_html=True)

    with sc2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Export Options</h3>", unsafe_allow_html=True)
        st.radio("Format", ["Excel", "CSV", "Both"])
        st.checkbox("Highlight Status Rows", value=True)
        st.checkbox("Include Confidence Score", value=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>System Info</h3>", unsafe_allow_html=True)
        import streamlit as _st
        import pandas as _pd

        sc = st.session_state.authenticated
        st.markdown(
            f"""<table style='width:100%;font-size:.82rem;color:#8a9099;border-collapse:collapse;'>
          <tr><td style='padding:5px 0;color:#dde1e7;'>Version</td><td>2.1.0</td></tr>
          <tr><td style='padding:5px 0;color:#dde1e7;'>KRA Status</td><td style='color:{"#7ec89b" if sc else "#c25f5f"}'>{"\u25cf Connected" if sc else "\u25cf Disconnected"}</td></tr>
          <tr><td style='padding:5px 0;color:#dde1e7;'>Workers</td><td>{st.session_state.get("workers", 8)}</td></tr>
          <tr><td style='padding:5px 0;color:#dde1e7;'>Python</td><td>{sys.version.split()[0]}</td></tr>
          <tr><td style='padding:5px 0;color:#dde1e7;'>Streamlit</td><td>{_st.__version__}</td></tr>
          <tr><td style='padding:5px 0;color:#dde1e7;'>Pandas</td><td>{_pd.__version__}</td></tr>
        </table>""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.markdown(CSS, unsafe_allow_html=True)
    _init()
    if not st.session_state.authenticated:
        login_page()
        return
    selected = sidebar_nav()
    pages = {
        "Dashboard": dashboard,
        "Reconciliation": reconciliation_page,
        "Reports": reports_page,
        "AI Assistant": ai_assistant_page,
        "Settings": settings_page,
    }
    pages.get(selected, dashboard)()

    # Auto-save state at the end of every interaction
    sync_session_state()


# ── Entry point ───────────────────────────────────────────────────────────────
# Called unconditionally so Streamlit's re-execution model works correctly.
# The old `if __name__ == "__main__": main()` guard prevented the script from
# running on hot-reloads and in certain deployment environments where Streamlit
# imports the module rather than executing it as __main__.
main()