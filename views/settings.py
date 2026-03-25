import sys
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd

from modules.scrapper import Scrapper


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
            from bs4 import BeautifulSoup as _BS

            AUTH_URL = "https://ilaw.kra.go.ke/ilaw/users/login"
            d_user = st.session_state.get("d_u", "").strip()
            d_pass = st.session_state.get("d_p", "").strip()
            if not d_user or not d_pass:
                st.warning("Enter credentials above first.")
            else:
                with st.spinner("Probing KRA iLaw login page\u2026"):
                    try:
                        sess = requests.Session()
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

