import streamlit as st
from auth_utils import sign_up, login
import tempfile
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ingest import ingest_pdfs
from rag_core.chain import create_conversation_chain, get_answer

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocuMind — AI Document Expert",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
/* ── Header & Sidebar Control Fix ── */

/* 1. Hide the top decoration line */
[data-testid="stDecoration"] {
    display: none;
}

/* 2. Hide Main Menu and Footer */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* 3. INSTEAD OF header {visibility: hidden;}:
   Makeheader transparent and non-blocking, but keep it 
   technically "visible" so the sidebar arrow can exist. */
header[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0) !important;
    border: none !important;
}

/* 4. Style the Arrow (the collapsed control) */
/* This makes the arrow visible against your dark background */
[data-testid="collapsedControl"] {
    display: flex !important;
    color: #60a5fa !important;
    background-color: #111318 !important; /* Matches sidebar color */
    border: 1px solid #1e2330 !important;
    border-radius: 0 8px 8px 0 !important;
    top: 10px !important;
}

[data-testid="collapsedControl"]:hover {
    background-color: #1e2330 !important;
    color: #e2e8f0 !important;
}

.logo-container {
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid #1e2330;
    margin-bottom: 1.5rem;
}
.logo-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    font-weight: 600;
    color: #60a5fa !important;
    letter-spacing: -0.5px;
}
.logo-subtitle {
    font-size: 0.7rem;
    color: #64748b !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}

[data-testid="stFileUploader"] {
    background-color: #161a24;
    border: 1.5px dashed #1e2a45;
    border-radius: 10px;
    padding: 0.5rem;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #3b82f6; }

.stButton > button {
    background-color: #1e2330;
    color: #94a3b8;
    border: 1px solid #2d3748;
    border-radius: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    padding: 0.4rem 1rem;
    transition: all 0.2s;
    width: 100%;
}
.stButton > button:hover {
    background-color: #2d3748;
    color: #e2e8f0;
    border-color: #3b82f6;
}

[data-testid="stChatMessage"] {
    background-color: #111318;
    border: 1px solid #1e2330;
    border-radius: 12px;   
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
}

[data-testid="stExpander"] {
    background-color: #0d1117;
    border: 1px solid #1e2330;
    border-radius: 8px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background-color: #0f2a1a;
    border: 1px solid #166534;
    color: #4ade80;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    padding: 4px 10px;
    border-radius: 20px;
    margin-bottom: 1rem;
}
.status-dot {
    width: 6px;
    height: 6px;
    background-color: #4ade80;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

.file-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background-color: #161a24;
    border: 1px solid #1e2a45;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 0;
    font-size: 0.8rem;
    color: #94a3b8;
    font-family: 'IBM Plex Mono', monospace;
}

.welcome-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 60vh;
    text-align: center;
    gap: 1rem;
}
.welcome-icon { font-size: 3rem; margin-bottom: 0.5rem; }
.welcome-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem;
    font-weight: 600;
    color: #e2e8f0;
}
.welcome-subtitle {
    font-size: 0.9rem;
    color: #64748b;
    max-width: 400px;
    line-height: 1.6;
}
.welcome-steps { display: flex; gap: 1rem; margin-top: 1rem; }
.step-card {
    background-color: #111318;
    border: 1px solid #1e2330;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: left;
    width: 160px;
}
.step-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #3b82f6;
    margin-bottom: 4px;
}
.step-text { font-size: 0.82rem; color: #94a3b8; }

.new-files-banner {
    background-color: #1a1f2e;
    border: 1px solid #2d3a5a;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.78rem;
    color: #60a5fa;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 0.5rem;
}

hr { border-color: #1e2330; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d0f12; }
::-webkit-scrollbar-thumb { background: #1e2330; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #3b82f6; }

[data-testid="collapsedControl"] {
    display: block !important;
    color: #60a5fa !important;
    background-color: #1e2330 !important;
    border-radius: 0 6px 6px 0 !important;
}

[data-testid="collapsedControl"]:hover {
    background-color: #2d3748 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chain" not in st.session_state:
    st.session_state.chain = None
if "pdfs_processed" not in st.session_state:
    st.session_state.pdfs_processed = False
if "uploaded_names" not in st.session_state:
    st.session_state.uploaded_names = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_session_name" not in st.session_state:
    st.session_state.current_session_name = "Session 1"

# This block cleans up the login/sidebar inputs by removing duplicate browser 
# icons (like the double password eye) and hiding the 'Press Enter' hint.
st.markdown("""
    <style>
        /* 1. Remove the duplicate browser eye */
        input::-ms-reveal, input::-ms-clear { display: none !important; }

        /* 2. Shrink font for a tighter fit */
        .stTextInput input {
            font-size: 0.85rem !important;
            padding: 0.4rem !important;
        }

        /* 3. Delete the 'Press Enter' clutter and the ghost icon */
        div[data-testid="InputInstructions"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # 1. TOP SECTION: Logo
    st.markdown("""
        <div style="padding: 1rem 0 1.5rem 0;">
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; font-weight: 700; color: #60a5fa;">📄 DocuMind</div>
            <div style="font-size: 0.7rem; color: #64748b; letter-spacing: 2px; text-transform: uppercase;">AI Document Expert</div>
        </div>
    """, unsafe_allow_html=True)

    # 2. AUTHENTICATION CHECK
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        # --- LOGGED OUT VIEW ---
        mode = st.radio("Access", ["Login", "Sign Up"], label_visibility="collapsed")
        
        # 1. ICONIZED EMAIL INPUT (Fixed Spacing)
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg>
                <span style="color: #94a3b8; font-size: 0.9rem; font-weight: 500;">Email</span>
            </div>
        """, unsafe_allow_html=True)
        email = st.text_input("Email", label_visibility="collapsed")

        # 2. ICONIZED PASSWORD INPUT (Fixed Spacing)
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px; margin-top: 2px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3-3.5 3.5z"></path></svg>
                <span style="color: #94a3b8; font-size: 0.9rem; font-weight: 500;">Password</span>
            </div>
        """, unsafe_allow_html=True)
        password = st.text_input("Password", type="password", label_visibility="collapsed")

# --- LOGIN / SIGN UP LOGIC ---
        if mode == "Sign Up":
            # --- FIRST & LAST NAME SECTION ---
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px; margin-top: 5px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        <span style="color: #94a3b8; font-size: 0.9rem; font-weight: 500;">First Name</span>
                    </div>
                """, unsafe_allow_html=True)
                first_name = st.text_input("First Name", label_visibility="collapsed")
                
            with col2:
                st.markdown("""
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px; margin-top: 5px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        <span style="color: #94a3b8; font-size: 0.9rem; font-weight: 500;">Last Name</span>
                    </div>
                """, unsafe_allow_html=True)
                last_name = st.text_input("Last Name", label_visibility="collapsed")

            full_name = f"{first_name} {last_name}"

            if st.button("Create Account", use_container_width=True):
                from auth_utils import sign_up
                sign_up(email, password, full_name)
                
        else:
            # --- LOGIN BUTTON ---
            if st.button("Login", use_container_width=True):
                with st.spinner("Authenticating..."):
                    from auth_utils import login
                    if login(email, password):
                        st.rerun()
            
            st.markdown("---")
            if st.button("Forgot Password?", key="forgot_pw"):
                if email:
                    from auth_utils import reset_password
                    reset_password(email) 
                else:
                    st.warning("Please enter your email address first.")

    else:        
        # --- LOGGED IN VIEW ---
        # A. Navigation & Chat History
        # Search-style box
        st.markdown("""
            <div style="background-color: #1e2330; border-radius: 8px; padding: 8px 12px; margin-bottom: 24px; border: 1px solid #2d3343; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <span style="color: #94a3b8; font-size: 0.85rem;">Search chats</span>
                </div>
                <span style="background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #475569; font-size: 0.65rem; border: 1px solid #1e293b;">⌘ K</span>
            </div>
        """, unsafe_allow_html=True)

        # Dynamic Chat Sessions History
        st.markdown("**Previous Sessions**")
        
        # Pre-save the current active session if it isn't saved yet but has activity
        if st.session_state.messages or st.session_state.pdfs_processed:
            st.session_state.chat_sessions[st.session_state.current_session_name] = {
                 "messages": list(st.session_state.messages),
                 "uploaded_names": list(st.session_state.uploaded_names),
                 "vectorstore": st.session_state.vectorstore,
                 "chain": st.session_state.chain,
                 "pdfs_processed": st.session_state.pdfs_processed
             }
             
        if st.session_state.chat_sessions:
            for session_name in reversed(list(st.session_state.chat_sessions.keys())):
                # Visually indicate active session with a primary button color
                btn_type = "primary" if session_name == st.session_state.current_session_name else "secondary"
                if st.button(f"💬 {session_name}", key=f"btn_{session_name}", type=btn_type, use_container_width=True):
                    saved = st.session_state.chat_sessions[session_name]
                    st.session_state.current_session_name = session_name
                    st.session_state.messages = list(saved["messages"])
                    st.session_state.uploaded_names = list(saved["uploaded_names"])
                    st.session_state.vectorstore = saved["vectorstore"]
                    st.session_state.chain = saved["chain"]
                    st.session_state.pdfs_processed = saved["pdfs_processed"]
                    st.rerun()
        else:
            st.caption("No chat history yet.")

        st.markdown("<hr style='margin: 8px 0px; border-top: 1px solid #31333F;'>", unsafe_allow_html=True)

        # B. Document Uploads & Knowledge Base
        st.markdown("**Upload Documents**")
        st.caption("Supports multiple PDFs at once")

        uploaded_files = st.file_uploader(
            label="upload",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        # Detect only new files not yet processed
        new_files = [f for f in (uploaded_files or []) if f.name not in st.session_state.uploaded_names]

        if new_files:
            with st.spinner(f"Processing {len(new_files)} files..."):
                temp_paths = []
                new_names = []

                for uploaded_file in new_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        temp_paths.append(tmp.name)
                        new_names.append(uploaded_file.name)

                if st.session_state.pdfs_processed:
                    st.markdown("""
                        <div class="new-files-banner">
                            ↻ Updating knowledge base with new files...
                        </div>
                    """, unsafe_allow_html=True)
                            
            # Incremental ingestion — only process new files
            # passes existing vectorstore so old chunks are preserved
                vectorstore = ingest_pdfs(
                    temp_paths,
                    original_names=new_names,
                    existing_vectorstore=st.session_state.vectorstore
                )

                # Update session state
                st.session_state.vectorstore = vectorstore
                st.session_state.chain = create_conversation_chain(vectorstore)
                st.session_state.pdfs_processed = True
                st.session_state.uploaded_names.extend(new_names)

                # Clean up temp files
                for path in temp_paths:
                    try:
                        os.unlink(path)
                    except Exception:
                        pass

        # Show status once files are loaded
        if st.session_state.pdfs_processed:
            st.markdown("""
                <div class="status-pill">
                    <div class="status-dot"></div>
                    KNOWLEDGE BASE READY
                </div>
            """, unsafe_allow_html=True)           

            for name in st.session_state.uploaded_names:
                st.markdown(f"""
                    <div class="file-badge">📎 {name}</div>
                """, unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0px; border-top: 1px solid #31333F;'>", unsafe_allow_html=True)
            
        if st.sidebar.button("🔄 New Session", use_container_width=True):
            # Only process if they actually did something in the current session
            if st.session_state.messages or st.session_state.pdfs_processed:
                st.session_state.chat_sessions[st.session_state.current_session_name] = {
                    "messages": list(st.session_state.messages),
                    "uploaded_names": list(st.session_state.uploaded_names),
                    "vectorstore": st.session_state.vectorstore,
                    "chain": st.session_state.chain,
                    "pdfs_processed": st.session_state.pdfs_processed
                }
            
            # Switch to a fresh identity
            new_id = len(st.session_state.chat_sessions) + 1
            st.session_state.current_session_name = f"Session {new_id}"
            
            # Wipe active fields
            st.session_state.messages = []
            st.session_state.chain = None
            st.session_state.pdfs_processed = False
            st.session_state.uploaded_names = []
            st.session_state.vectorstore = None
            st.rerun()

        st.markdown("<hr style='margin: 10px 0px; border-top: 1px solid #31333F;'>", unsafe_allow_html=True)

        # C. BOTTOM ANCHOR: User Profile Card
        user_name = st.session_state.user.display_name or "User"
        user_email = st.session_state.user.email
        
        st.markdown(f"""
            <div style="background-color: #111318; border: 1px solid #1e2330; border-radius: 12px; padding: 12px; display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <div style="width: 32px; height: 32px; background: #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.9rem;">
                    {user_name[0].upper()}
                </div>
                <div style="overflow: hidden;">
                    <div style="font-size: 0.9rem; font-weight: 600; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{user_name}</div>
                    <div style="font-size: 0.8rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{user_email}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # 3. FOOTER: Institution Info (Bottom-most)
    st.markdown("""
        <div style="font-size:0.7rem; color:#334155; line-height:1.8;">
            <div>Powered by</div>
            <div style="color:#475569;">Gemini 2.5 · LangChain · ChromaDB</div>
            <br/>
            <div>Government Engineering College</div>
            <div style="color:#475569;">Ajmer · VI Semester · 2026</div>
        </div>
    """, unsafe_allow_html=True)

# ── Main Chat Area ────────────────────────────────────────────────────────────
if not st.session_state.pdfs_processed:
    st.markdown("""
        <div class="welcome-container">
            <div class="welcome-icon">📄</div>
            <div class="welcome-title">DocuMind</div>
            <div class="welcome-subtitle">
                Upload your PDF documents in the sidebar and start asking questions.
                Get instant answers with verified page-level citations.
            </div>
            <div class="welcome-steps">
                <div class="step-card">
                    <div class="step-number">STEP 01</div>
                    <div class="step-text">Upload one or more PDF files</div>
                </div>
                <div class="step-card">
                    <div class="step-number">STEP 02</div>
                    <div class="step-text">Ask any question naturally</div>
                </div>
                <div class="step-card">
                    <div class="step-number">STEP 03</div>
                    <div class="step-text">Get cited answers instantly</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📌 Sources"):
                    seen = set()
                    for source in message["sources"]:
                        key = (source['page'], source['file'])
                        if key not in seen:
                            seen.add(key)
                            st.markdown(
                                f"<div style='font-family:IBM Plex Mono,monospace; font-size:0.72rem; color:#64748b; "
                                f"background:#0d1117; border:1px solid #1e2330; border-radius:6px; "
                                f"padding:8px 12px; margin:4px 0;'>"
                                f"<span style='color:#3b82f6;'>▸ {os.path.basename(source['file'])}</span>"
                                f"<span style='color:#475569;'> · Page {source['page'] + 1} · Line ~{source['line']}</span>"
                                f"<br/><span style='color:#4b5563; font-size:0.68rem;'>❝ {source['preview']}</span>"
                                f"</div>",
                                unsafe_allow_html=True
                            )

    # Chat input
    if user_input := st.chat_input("Ask anything about your documents..."):
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("assistant"):
            with st.spinner(""):
                answer, sources = get_answer(st.session_state.chain, user_input)
            st.write(answer)
            if sources:
                with st.expander("📌 Sources"):
                    seen = set()
                    for source in sources:
                        key = (source['page'], source['file'])
                        if key not in seen:
                            seen.add(key)
                            st.markdown(
                                f"<div style='font-family:IBM Plex Mono,monospace; font-size:0.72rem; color:#64748b; "
                                f"background:#0d1117; border:1px solid #1e2330; border-radius:6px; "
                                f"padding:8px 12px; margin:4px 0;'>"
                                f"<span style='color:#3b82f6;'>▸ {os.path.basename(source['file'])}</span>"
                                f"<span style='color:#475569;'> · Page {source['page'] + 1} · Line ~{source['line']}</span>"
                                f"<br/><span style='color:#4b5563; font-size:0.68rem;'>❝ {source['preview']}</span>"
                                f"</div>",
                                unsafe_allow_html=True
                            )

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })