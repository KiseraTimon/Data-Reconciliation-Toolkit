from datetime import datetime
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go


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

