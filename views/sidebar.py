import streamlit as st
from streamlit_option_menu import option_menu
from assets.ui import KRA_LOGO
from core.state import get_session_store

def sidebar_nav():
    with st.sidebar:
        st.markdown(
            f"""<div style='display:flex;align-items:center;gap:11px;padding:1rem .5rem .5rem;'>{KRA_LOGO}
            <div><div class='kra-wordmark'>KI<span>R</span>A</div>
            <div style='font-size:.62rem;color:#8a9099;letter-spacing:.1em;'>RECONCILIATION v2</div></div></div>
            <div style='height:1px;background:var(--border);margin:1rem 0;'></div>""",
            unsafe_allow_html=True,
        )

        options = ["Dashboard", "Reconciliation", "Reports", "AI Assistant", "Settings"]

        target_page = st.session_state.get('current_page', 'Dashboard')

        try:
            target_idx = options.index(target_page)
        except ValueError:
            target_idx = 0

        # 3. Render the menu WITHOUT the 'key' parameter to prevent state fighting
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=["grid", "arrow-repeat", "file-earmark-bar-graph", "robot", "gear"],
            default_index=target_idx,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "#8a9099", "font-size": "14px"},
                "nav-link": {"font-size": "0.87rem", "color": "#8a9099", "padding": "0.55rem 1rem", "border-radius": "6px", "margin-bottom": "2px"},
                "nav-link-selected": {"background-color": "rgba(200,168,75,0.1)", "color": "#c8a84b", "font-weight": "500"},
            },
        )

        if selected != target_page:
            st.session_state.current_page = selected
            st.rerun()

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
                if "sid" in st.session_state:
                    store = get_session_store()
                    store.pop(st.session_state["sid"], None)
                    st.query_params.clear()

                for k in ['authenticated', 'scrapper', 'reconciled_data', 'uploaded_df', 'case_num_col', 'citation_col']:
                    st.session_state[k] = False if k == 'authenticated' else None
                st.session_state.step = 1
                st.session_state.current_page = 'Dashboard'
                st.rerun()

    return selected