"""
Async Research Assistant — Streamlit UI
Run: streamlit run src/ui.py
"""
 
import asyncio
import time
import streamlit as st
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
load_dotenv()
 
# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Research Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main background */
.stApp { background-color: #f8f9fc; }
 
/* Answer card */
.answer-card {
    background: white;
    border-left: 4px solid #0B3D91;
    border-radius: 8px;
    padding: 20px 24px;
    margin: 12px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    font-size: 1.05rem;
    line-height: 1.7;
}
 
/* Citation badge */
.cite-card {
    background: #f0f4ff;
    border: 1px solid #d0dbf5;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.9rem;
}
 
/* Source tag */
.tag-wiki  { background:#e8f5e9; color:#1b5e20;
             padding:2px 8px; border-radius:10px; font-size:0.78rem; }
.tag-arxiv { background:#fff3e0; color:#e65100;
             padding:2px 8px; border-radius:10px; font-size:0.78rem; }
.tag-web   { background:#e3f2fd; color:#0d47a1;
             padding:2px 8px; border-radius:10px; font-size:0.78rem; }
 
/* Metric box */
.metric-row { display:flex; gap:16px; margin:10px 0; }
.metric-box {
    background:white; border-radius:8px; padding:12px 18px;
    text-align:center; flex:1;
    box-shadow:0 1px 4px rgba(0,0,0,0.08);
}
.metric-val { font-size:1.5rem; font-weight:700; color:#0B3D91; }
.metric-lbl { font-size:0.78rem; color:#666; }
</style>
""", unsafe_allow_html=True)
 
 
# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Parametrlər")
    st.divider()
 
    sources = st.multiselect(
        "📡 Mənbələr",
        options=["wiki", "arxiv", "web"],
        default=["wiki", "arxiv", "web"],
        help="Hansı mənbələrdən axtarılsın?"
    )
 
    use_cache = st.toggle("⚡ Cache istifadə et", value=True,
                          help="Eyni sual əvvəl soruşulubsa, saxlanmış cavabı qaytarır")
 
    st.divider()
    st.markdown("**Timeout (saniyə)**")
    timeout = st.slider("", min_value=5, max_value=30, value=10, label_visibility="collapsed")
 
    st.divider()
    st.markdown("""
    **Mənbələr haqqında**
    - 🟢 **Wikipedia** — ümumi məlumat
    - 🟠 **arXiv** — elmi məqalələr
    - 🔵 **Web** — ən son məlumat
    """)
 
 
# ── Header ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.markdown("# 🔬")
with col_title:
    st.markdown("# AI Research Assistant")
    st.caption("Wikipedia · arXiv · Web — paralel axtarış, AI sintezi")
 
st.divider()
 
 
# ── Input ───────────────────────────────────────────────────────────────────
question = st.text_input(
    "💬 Sualınızı yazın",
    placeholder="What is quantum computing and how does it work?",
    label_visibility="visible"
)
 
col_btn, col_ex = st.columns([2, 8])
with col_btn:
    search_clicked = st.button("🔍 Araşdır", type="primary", use_container_width=True)
 
with col_ex:
    example = st.selectbox(
        "Nümunə suallar",
        ["", "What is photosynthesis?",
         "How do transformer language models work?",
         "What causes climate change?",
         "Explain quantum entanglement"],
        label_visibility="collapsed"
    )
    if example:
        question = example
 
 
# ── Search ──────────────────────────────────────────────────────────────────
def tag(origin: str) -> str:
    cls = {"wikipedia": "tag-wiki", "arxiv": "tag-arxiv", "web": "tag-web"}
    label = {"wikipedia": "Wikipedia", "arxiv": "arXiv", "web": "Web"}
    return (f'<span class="{cls.get(origin, "tag-web")}">'
            f'{label.get(origin, origin.upper())}</span>')
 
 
if (search_clicked or example) and question:
    if not sources:
        st.warning("⚠️ Ən azı bir mənbə seçin.")
        st.stop()
 
    try:
        from src.core.researcher import ResearchAssistant
    except ImportError:
        st.error("❌ `src.core.researcher` tapılmadı. "
                 "Layihə qovluğundan çalıştırın: `streamlit run src/ui.py`")
        st.stop()
 
    with st.status("🔍 Araşdırılır...", expanded=True) as status:
        st.write(f"📡 Mənbələr sorğulanır: {', '.join(sources)}")
        t0 = time.perf_counter()
 
        assistant = ResearchAssistant()
        result = asyncio.run(
            assistant.conduct_research(
                question,
                no_cache=not use_cache 
            )
        )
        elapsed = time.perf_counter() - t0
        status.update(label="✅ Cavab hazırdır!", state="complete")
 
    # ── Metrics ─────────────────────────────────────────────────────────
    n_citations = len(result.citations) if hasattr(result, "citations") else 0
    cache_hit = "✅ Bəli" if use_cache else "⛔ Xeyr"
 
    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box">
        <div class="metric-val">{elapsed:.2f}s</div>
        <div class="metric-lbl">Vaxt</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">{n_citations}</div>
        <div class="metric-lbl">İstinad</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">{len(sources)}</div>
        <div class="metric-lbl">Mənbə</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">{cache_hit}</div>
        <div class="metric-lbl">Cache</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
 
    st.divider()
 
    # ── Answer ───────────────────────────────────────────────────────────
    if hasattr(result, "answer"):
        st.markdown("### 📝 Cavab")
        st.markdown(
            f'<div class="answer-card">{result.answer}</div>',
            unsafe_allow_html=True
        )
 
        # ── Citations ────────────────────────────────────────────────────
        if result.citations:
            st.markdown("### 📚 İstinadlar")
            for c in result.citations:
                st.markdown(
                    f'<div class="cite-card">'
                    f'<b>[{c.index}]</b> &nbsp; {tag(c.source.origin)} &nbsp; '
                    f'<a href="{c.source.url}" target="_blank">'
                    f'<b>{c.source.title}</b></a><br>'
                    f'<small style="color:#666">{c.source.url}</small>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    else:
        st.error(f"❌ {result}")
 
 
# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("🔬 PFIP Team · AI-ENG-110 · Spring 2026 · "
           "AI Academy, National AI Center")
 