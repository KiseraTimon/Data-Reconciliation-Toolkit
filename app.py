import sys
from pathlib import Path
import streamlit as st

# Ensure root directory is in path
sys.path.insert(0, str(Path(__file__).parent))

# Import separated modules
from assets.ui import CSS
from core.state import _init, sync_session_state
from views.login import login_page
from views.sidebar import sidebar_nav
from views.dashboard import dashboard
from views.reconciliation import reconciliation_page
from views.reports import reports_page
from views.ai import ai_assistant_page
from views.settings import settings_page

st.set_page_config(
    page_title="KRA — Records Reconciler",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

    # Route to the correct page
    pages.get(selected, dashboard)()

    sync_session_state()

main()