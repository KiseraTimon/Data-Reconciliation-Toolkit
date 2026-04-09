import os
import tempfile
import traceback
import concurrent.futures
from pathlib import Path
from datetime import datetime
import urllib.parse
import json

import streamlit as st
import pandas as pd

from modules import Scanner
from utils import errhandler
from assets.ui import step_bar


def parallel_extract(scrapper, file_data, workers=8):
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
            if st.button("⬇ Download PDF Report", use_container_width=True):
                fp = st.session_state.temp_file_path
                if fp and os.path.exists(fp):
                    with st.spinner("Generating PDF..."):
                        pdf_path = st.session_state.scrapper.generate_pdf_report(data=data, file_path=fp)
                        if pdf_path and os.path.exists(pdf_path):
                            # Move the generated PDF to the /reports folder for the dashboard to see
                            final_dir = Path("reports")
                            final_dir.mkdir(exist_ok=True)
                            final_path = final_dir / f"RECONCILED_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.pdf"
                            os.rename(pdf_path, final_path)

                            st.success("✅ Saved to /reports")
                        else:
                            st.error("Failed to generate PDF.")
                else:
                    st.error("Source file missing.")
            st.markdown('</div>', unsafe_allow_html=True)
        with ec2:
            csv_b = df_res.to_csv(index=False).encode()
            st.download_button(
                "⬇ Export CSV", csv_b,
                file_name=f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv", use_container_width=True,
            )
        with ec3:
            if st.button("⊕ New Reconciliation", use_container_width=True):
                st.session_state.step = 1
                st.session_state.reconciled_data = None
                st.session_state.uploaded_df = None
                st.rerun()



