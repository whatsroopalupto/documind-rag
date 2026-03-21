import streamlit as st
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
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp { background-color: #0d0f12; color: #e2e8f0; }

[data-testid="stSidebar"] {
    background-color: #111318;
    border-right: 1px solid #1e2330;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

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

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class="logo-container">
            <div class="logo-title">📄 DocuMind</div>
            <div class="logo-subtitle">AI Document Expert</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("**Upload Documents**")
    st.caption("Supports multiple PDFs at once")

    uploaded_files = st.file_uploader(
        label="upload",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    # Detect only new files not yet processed
    new_files = [
        f for f in (uploaded_files or [])
        if f.name not in st.session_state.uploaded_names
    ]

    if new_files:
        with st.spinner(f"Processing {len(new_files)} new file(s)..."):
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

        st.markdown("---")

        if st.button("🔄 New Session"):
            st.session_state.messages = []
            st.session_state.chain = None
            st.session_state.pdfs_processed = False
            st.session_state.uploaded_names = []
            st.session_state.vectorstore = None
            st.rerun()

    st.markdown("---")
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