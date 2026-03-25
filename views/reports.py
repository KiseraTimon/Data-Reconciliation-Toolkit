from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd


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

