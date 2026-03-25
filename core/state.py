import uuid
import streamlit as st
from ai_assistant import AIAssistant

@st.cache_resource
def get_session_store():
    return {}

def sync_session_state():
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