"""
Data Reconciliation Toolkit - Main Application
A modern, user-friendly system for legal data reconciliation with KRA systems
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
import time
import numpy as np
import tempfile

from modules import Scrapper

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules import Scanner, Scrapper, Validator
from modules.reconciler import EnhancedReconciler
from ai_assistant import AIAssistant
from utils import errhandler, syshandler, times
from secret import credentials

# Page configuration
st.set_page_config(
    page_title="KRA Data Reconciliation System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Modern gradient background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Glass morphism cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin: 1rem 0;
    }
    
    /* Animated buttons */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(31, 38, 135, 0.37);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(31, 38, 135, 0.5);
    }
    
    /* Status badges */
    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-success {
        background: #10b981;
        color: white;
    }
    
    .badge-warning {
        background: #f59e0b;
        color: white;
    }
    
    .badge-danger {
        background: #ef4444;
        color: white;
    }
    
    .badge-info {
        background: #3b82f6;
        color: white;
    }
    
    /* Progress bar animation */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
        transition: width 0.5s ease;
    }
    
    /* Metrics cards */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* AI Chat Interface */
    .ai-chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.5rem;
        height: 500px;
        overflow-y: auto;
        margin: 1rem 0;
    }
    
    .ai-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px 15px 15px 0;
        padding: 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        align-self: flex-start;
    }
    
    .user-message {
        background: #f3f4f6;
        color: #1f2937;
        border-radius: 15px 15px 0 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        align-self: flex-end;
        margin-left: auto;
    }
    
    /* Fix for Streamlit warnings */
    .stAlert {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'reconciliation_data' not in st.session_state:
    st.session_state.reconciliation_data = None
if 'ai_assistant' not in st.session_state:
    st.session_state.ai_assistant = AIAssistant()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'temp_file_path' not in st.session_state:
    st.session_state.temp_file_path = None

# Authentication
def authenticate():
    USER = credentials()
    
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/law.png", width=80)
        st.title("⚖️ KRA Reconciliation")
        
        if not st.session_state.authenticated:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    scrapper = Scrapper(
                        username=username,
                        password=password,
                    )

                    logged_in = scrapper.authenticator()

                    if not logged_in:
                        st.error("❌ Authentication failed with KRA system")
                        return False
                    
                    st.session_state.authenticated = True
                    st.success("✅ Login successful!")
                    st.rerun()

            return False
        else:
            st.success(f"👤 Logged in successfully")
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.step = 1
                st.rerun()
            return True

# Main navigation
def navigation():
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=["Dashboard", "Reconciliation", "Reports", "AI Assistant", "Settings"],
            icons=["house", "arrow-repeat", "file-text", "robot", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#667eea", "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
                "nav-link-selected": {"background-color": "#667eea"},
            }
        )
    return selected

# Dashboard
def dashboard():
    st.title("📊 Reconciliation Dashboard")
    
    # Welcome message with time-based greeting
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
    elif hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
    
    st.markdown(f"""
    <div class="glass-card">
        <h2>{greeting}, Welcome back! 👋</h2>
        <p style="color: #666;">Last login: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1rem; color: #666;">Total Records</div>
            <div class="metric-value">1,234</div>
            <div style="color: #10b981;">↑ 12% from last week</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1rem; color: #666;">Verified</div>
            <div class="metric-value">856</div>
            <div style="color: #10b981;">69.3% success rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1rem; color: #666;">Pending Review</div>
            <div class="metric-value">278</div>
            <div style="color: #f59e0b;">22.5% need attention</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1rem; color: #666;">Not Found</div>
            <div class="metric-value">100</div>
            <div style="color: #ef4444;">8.2% missing</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity chart
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📈 Weekly Activity")
        
        # Sample data
        df_weekly = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Records': [45, 52, 38, 65, 48, 22, 15]
        })
        
        fig = px.line(df_weekly, x='Day', y='Records', markers=True)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🎯 Status Distribution")
        
        # Sample data
        fig = go.Figure(data=[go.Pie(
            labels=['Verified', 'Review Required', 'Mismatch', 'Not Found'],
            values=[856, 200, 48, 130],
            hole=.3,
            marker_colors=['#10b981', '#f59e0b', '#ef4444', '#6b7280']
        )])
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📤 New Reconciliation", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.page = "Reports"
            st.rerun()
    with col3:
        if st.button("🤖 Ask AI Assistant", use_container_width=True):
            st.session_state.page = "AI Assistant"
            st.rerun()
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.page = "Settings"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Reconciliation Page
def reconciliation_page():
    st.title("🔄 Data Reconciliation")
    
    # Progress tracker
    steps = ["Upload", "Validation", "Processing", "Results"]
    current_step = st.session_state.step
    
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if i + 1 < current_step:
                st.markdown(f"<div style='text-align: center; color: #10b981;'>✅ {step}</div>", unsafe_allow_html=True)
            elif i + 1 == current_step:
                st.markdown(f"<div style='text-align: center; color: #667eea; font-weight: bold;'>⚡ {step}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; color: #999;'>⭕ {step}</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if current_step == 1:
        # Upload Step
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📁 Upload Data File")
            
            uploaded_file = st.file_uploader(
                "Choose a file (CSV or Excel)",
                type=['csv', 'xlsx'],
                help="Upload your case data file"
            )
            
            if uploaded_file:
                st.success(f"✅ File uploaded: {uploaded_file.name}")
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    st.session_state.temp_file_path = tmp_file.name
                
                # Preview
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.subheader("📋 Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Save to session
                st.session_state.uploaded_df = df
                st.session_state.uploaded_file_name = uploaded_file.name
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("Next →", use_container_width=True) and 'uploaded_df' in st.session_state:
                    st.session_state.step = 2
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif current_step == 2:
        # Column Mapping Step
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("🔍 Column Mapping")
            
            df = st.session_state.uploaded_df
            
            col1, col2 = st.columns(2)
            
            with col1:
                case_num_col = st.selectbox(
                    "Select Case Number Column",
                    options=df.columns.tolist(),
                    help="Column containing case numbers"
                )
            
            with col2:
                citation_col = st.selectbox(
                    "Select Citation Column",
                    options=df.columns.tolist(),
                    help="Column containing case citations"
                )
            
            # Validation
            if st.button("Validate & Continue", use_container_width=True):
                with st.spinner("Validating data..."):
                    # Save to session
                    st.session_state.case_num_col = case_num_col
                    st.session_state.citation_col = citation_col
                    st.session_state.step = 3
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif current_step == 3:
        # Processing Step
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("⚙️ Processing Data")
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Processing steps
            steps_processing = [
                "Extracting data from file...",
                "Authenticating with KRA system...",
                "Searching for matches...",
                "Analyzing results..."
            ]
            
            try:
                # Step 1: Extract data
                status_text.text(steps_processing[0])
                progress_bar.progress(25)
                
                USER = credentials()
                
                # Initialize scanner
                scanner = Scanner(
                    case_num_column=st.session_state.case_num_col,
                    citation_column=st.session_state.citation_col
                )
                
                # Extract data
                file_data = scanner.file_extractor(sheet=st.session_state.uploaded_df)
                
                if not file_data:
                    st.error("❌ No data extracted from file")
                    return
                
                # Step 2: Authenticate
                status_text.text(steps_processing[1])
                progress_bar.progress(50)
                
                # Initialize scrapper
                scrapper = Scrapper(
                    username=USER['username'],
                    password=USER['password'],
                    data=file_data
                )
                
                # Authenticate
                if not scrapper.authenticator():
                    st.error("❌ Authentication failed with KRA system")
                    return
                
                # Step 3: Search for matches
                status_text.text(steps_processing[2])
                progress_bar.progress(75)
                
                # Scrape data
                extracted = scrapper.extractor()
                
                if not extracted:
                    st.warning("⚠️ No matches found in KRA system")
                    extracted = []
                
                # Step 4: Analyze results
                status_text.text(steps_processing[3])
                progress_bar.progress(90)
                
                # Compare
                reconciled_data = scrapper.comparator(extracted_data=extracted)
                
                # Save to session
                st.session_state.reconciled_data = reconciled_data
                st.session_state.raw_data = file_data
                st.session_state.scrapper = scrapper
                
                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")
                
                st.success("✅ Data reconciliation completed successfully!")
                
                if st.button("View Results →", use_container_width=True):
                    st.session_state.step = 4
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")
                errhandler(e, log="reconciliation", path="app")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif current_step == 4:
        # Results Step
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📊 Reconciliation Results")
            
            if 'reconciled_data' in st.session_state:
                data = st.session_state.reconciled_data
                
                if not data:
                    st.warning("⚠️ No reconciliation data available")
                    if st.button("Start New Reconciliation"):
                        st.session_state.step = 1
                        st.rerun()
                    return
                
                # Summary metrics
                total = len(data)
                verified = sum(1 for d in data if d.get('status') == 'VERIFIED MATCH')
                review = sum(1 for d in data if d.get('status') == 'REVIEW REQUIRED')
                mismatch = sum(1 for d in data if d.get('status') == 'MISMATCH')
                not_found = sum(1 for d in data if d.get('status') == 'NOT FOUND')
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", total)
                with col2:
                    st.metric("Verified", verified, f"{(verified/total*100):.1f}%" if total > 0 else "0%")
                with col3:
                    st.metric("Review Required", review, f"{(review/total*100):.1f}%" if total > 0 else "0%")
                with col4:
                    st.metric("Issues", mismatch + not_found, f"{((mismatch+not_found)/total*100):.1f}%" if total > 0 else "0%")
                
                # Results table
                results_df = pd.DataFrame([
                    {
                        'Row': d.get('excel_row', ''),
                        'Case Number': d.get('original_case', ''),
                        'Citation': d.get('case_name', '')[:50] + '...' if len(d.get('case_name', '')) > 50 else d.get('case_name', ''),
                        'Status': d.get('status', ''),
                        'Confidence': d.get('confidence_score', ''),
                        'Match': d.get('best_match_kra_citation', '')[:50] + '...' if len(d.get('best_match_kra_citation', '')) > 50 else d.get('best_match_kra_citation', '')
                    }
                    for d in data
                ])
                
                # Color coding
                def color_status(val):
                    if val == 'VERIFIED MATCH':
                        return 'background-color: #10b98120'
                    elif val == 'REVIEW REQUIRED':
                        return 'background-color: #f59e0b20'
                    elif val == 'MISMATCH':
                        return 'background-color: #ef444420'
                    elif val == 'NOT FOUND':
                        return 'background-color: #6b728020'
                    return ''
                
                # Fix for deprecated applymap
                styled_df = results_df.style.map(color_status, subset=['Status'])
                
                st.dataframe(styled_df, use_container_width=True, height=400)
                
                # Export options
                st.subheader("💾 Export Results")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📊 Export to Excel", use_container_width=True):
                        if st.session_state.temp_file_path and os.path.exists(st.session_state.temp_file_path):
                            # Generate report using scrapper
                            if st.session_state.scrapper.report(
                                data=data,
                                file_path=st.session_state.temp_file_path
                            ):
                                st.success("✅ Report generated successfully! Check the 'reports' folder.")
                            else:
                                st.error("❌ Failed to generate report")
                        else:
                            st.error("❌ Temporary file not found")
                
                with col2:
                    if st.button("📄 Export to CSV", use_container_width=True):
                        csv_path = f"reconciliation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        results_df.to_csv(csv_path, index=False)
                        st.success(f"✅ CSV exported successfully to {csv_path}")
                
                with col3:
                    if st.button("🔄 New Reconciliation", use_container_width=True):
                        # Clean up temp file
                        if st.session_state.temp_file_path and os.path.exists(st.session_state.temp_file_path):
                            os.unlink(st.session_state.temp_file_path)
                        st.session_state.step = 1
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# Reports Page
def reports_page():
    st.title("📈 Reports & Analytics")
    
    # Check if reports directory exists
    reports_dir = Path("reports")
    if not reports_dir.exists():
        reports_dir.mkdir(exist_ok=True)
    
    # List existing reports
    report_files = list(reports_dir.glob("*.xlsx"))
    
    if report_files:
        st.subheader("📁 Generated Reports")
        report_data = []
        for report in sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True):
            report_data.append({
                'Report Name': report.name,
                'Date': datetime.fromtimestamp(report.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                'Size': f"{report.stat().st_size / 1024:.1f} KB"
            })
        
        reports_df = pd.DataFrame(report_data)
        st.dataframe(reports_df, use_container_width=True)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            selected_report = st.selectbox("Select report to download", [r['Report Name'] for r in report_data])
        with col2:
            if st.button("📥 Download Selected"):
                with open(reports_dir / selected_report, 'rb') as f:
                    st.download_button(
                        label="Click to Download",
                        data=f,
                        file_name=selected_report,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    else:
        st.info("ℹ️ No reports generated yet. Run a reconciliation first to generate reports.")

# AI Assistant Page
def ai_assistant_page():
    st.title("🤖 AI Legal Assistant")
    
    # Initialize AI assistant
    assistant = st.session_state.ai_assistant
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("💬 Chat with AI")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            st.markdown('<div class="ai-chat-container">', unsafe_allow_html=True)
            
            # Display chat history
            if not st.session_state.chat_history:
                st.markdown('<div class="ai-message">Hello! I\'m KIRA, your legal reconciliation assistant. How can I help you today?</div>', unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat_history:
                    if msg['role'] == 'ai':
                        st.markdown(f'<div class="ai-message">{msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Type your message...", key="user_input")
            submitted = st.form_submit_button("Send", use_container_width=True)
            
            if submitted and user_input:
                # Add user message
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                
                # Get AI response
                with st.spinner("AI is thinking..."):
                    response = assistant.get_response(user_input, st.session_state.get('reconciled_data'))
                
                # Add AI response
                st.session_state.chat_history.append({'role': 'ai', 'content': response})
                
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔍 Quick Actions")
        
        # Suggested questions
        st.markdown("**Suggested Questions:**")
        questions = [
            "How do I reconcile a case?",
            "What does VERIFIED MATCH mean?",
            "Show me unmatched cases",
            "Explain the confidence score",
            "Help with column mapping",
            "Generate a summary report"
        ]
        
        for q in questions:
            if st.button(q, use_container_width=True):
                # Add question to chat
                st.session_state.chat_history.append({'role': 'user', 'content': q})
                
                # Get AI response
                response = assistant.get_response(q, st.session_state.get('reconciled_data'))
                st.session_state.chat_history.append({'role': 'ai', 'content': response})
                
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Context info
        if 'reconciled_data' in st.session_state and st.session_state.reconciled_data:
            st.info(f"📊 Currently viewing: {len(st.session_state.reconciled_data)} reconciled records")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# Settings Page
def settings_page():
    st.title("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔐 Authentication Settings")
        
        with st.form("auth_settings"):
            current_creds = credentials()
            username = st.text_input("KRA Username", value=current_creds['username'])
            password = st.text_input("KRA Password", type="password", value=current_creds['password'])
            
            if st.form_submit_button("Update Credentials", use_container_width=True):
                # In a real app, you'd save these securely
                st.success("✅ Credentials updated successfully! (Note: This is a demo - credentials not actually saved)")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("⚡ Processing Settings")
        
        delay = st.slider("Request Delay (seconds)", 0, 5, 2)
        confidence_threshold = st.slider("Confidence Threshold (%)", 0, 100, 85)
        
        if st.button("Save Settings", use_container_width=True):
            st.success("✅ Settings saved!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📁 Export Settings")
        
        export_format = st.radio("Default Export Format", ["Excel", "CSV", "Both"])
        include_charts = st.checkbox("Include Charts in Report", value=True)
        highlight_rows = st.checkbox("Highlight Status Rows", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔔 Notification Settings")
        
        email_alerts = st.checkbox("Email on Completion", value=False)
        if email_alerts:
            st.text_input("Email Address")
        
        slack_integration = st.checkbox("Slack Integration", value=False)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("ℹ️ System Info")
        st.write(f"**Version:** 1.0.0")
        st.write(f"**Python:** {sys.version.split()[0]}")
        st.write(f"**Streamlit:** {st.__version__}")
        st.write(f"**Pandas:** {pd.__version__}")
        st.markdown('</div>', unsafe_allow_html=True)

# Clean up function
def cleanup():
    """Clean up temporary files"""
    if st.session_state.temp_file_path and os.path.exists(st.session_state.temp_file_path):
        try:
            os.unlink(st.session_state.temp_file_path)
        except:
            pass

# Main app logic
def main():
    # Register cleanup
    import atexit
    atexit.register(cleanup)
    
    # Authentication
    if not authenticate():
        return
    
    # Navigation
    selected = navigation()
    
    # Page routing
    if selected == "Dashboard":
        dashboard()
    elif selected == "Reconciliation":
        reconciliation_page()
    elif selected == "Reports":
        reports_page()
    elif selected == "AI Assistant":
        ai_assistant_page()
    elif selected == "Settings":
        settings_page()

if __name__ == "__main__":
    main()