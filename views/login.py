import uuid
import requests
from bs4 import BeautifulSoup
import streamlit as st

from modules.scrapper import Scrapper
from assets.ui import KRA_LOGO


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

