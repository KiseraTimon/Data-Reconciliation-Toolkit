import streamlit as st


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

