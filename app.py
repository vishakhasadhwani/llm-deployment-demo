import streamlit as st
import requests
import json
import os
import time
from datetime import datetime

st.set_page_config(page_title="vLLM Nexus", page_icon="⚡", layout="wide")

VLLM_HOST = os.environ.get("VLLM_HOST", "http://localhost:8000")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@300;400;500&family=Rajdhani:wght@400;500;600&display=swap');
:root { --cyan:#00f5ff; --purple:#b400ff; --green:#00ff88; --bg0:#020b14; --bg2:#0c2137; --border:rgba(0,245,255,0.18); --dim:#3a6070; }
html,body,[class*="css"] { font-family:'Rajdhani',sans-serif !important; color:#d0eeff !important; }
.stApp { background: linear-gradient(rgba(0,245,255,0.03) 1px,transparent 1px), linear-gradient(90deg,rgba(0,245,255,0.03) 1px,transparent 1px), radial-gradient(ellipse at 15% 0%,rgba(0,180,255,0.07) 0%,transparent 55%), radial-gradient(ellipse at 85% 100%,rgba(180,0,255,0.07) 0%,transparent 55%), #020b14 !important; background-size:48px 48px,48px 48px,100% 100%,100% 100%,100% 100% !important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#050f1e,#020b14) !important; border-right:1px solid var(--border) !important; }
.logo { padding:22px 0 18px; text-align:center; border-bottom:1px solid var(--border); margin-bottom:18px; }
.logo-title { font-family:'Orbitron',monospace; font-size:1.05rem; font-weight:900; letter-spacing:.18em; color:var(--cyan); text-shadow:0 0 18px rgba(0,245,255,.55); }
.logo-sub { font-family:'JetBrains Mono',monospace; font-size:.6rem; color:var(--dim); letter-spacing:.22em; margin-top:4px; }
.slabel { font-family:'JetBrains Mono',monospace; font-size:.6rem; letter-spacing:.2em; color:var(--cyan); text-transform:uppercase; margin:14px 0 5px; display:block; opacity:.8; }
.pill { display:inline-flex; align-items:center; gap:7px; padding:4px 13px; border-radius:20px; font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.1em; margin-top:8px; }
.pill.on  { background:rgba(0,255,136,.08); border:1px solid rgba(0,255,136,.3); color:var(--green); }
.pill.off { background:rgba(255,80,80,.08); border:1px solid rgba(255,80,80,.3); color:#ff6060; }
.dot { width:6px; height:6px; border-radius:50%; }
.dot.on  { background:var(--green); box-shadow:0 0 6px var(--green); animation:blink 2s infinite; }
.dot.off { background:#ff6060; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.minfo { background:rgba(0,245,255,.04); border:1px solid var(--border); border-radius:8px; padding:9px 12px; margin:6px 0 2px; font-family:'JetBrains Mono',monospace; font-size:.62rem; color:var(--dim); line-height:1.9; }
.minfo b { color:var(--cyan); font-weight:500; }
.stButton > button { width:100% !important; background:rgba(0,245,255,.06) !important; border:1px solid var(--cyan) !important; border-radius:7px !important; color:var(--cyan) !important; font-family:'Orbitron',monospace !important; font-size:.65rem !important; font-weight:700 !important; letter-spacing:.12em !important; padding:.5rem !important; transition:all .2s !important; }
.stButton > button:hover { background:rgba(0,245,255,.14) !important; box-shadow:0 0 18px rgba(0,245,255,.3) !important; }
[data-testid="stSelectbox"] > div > div { background:var(--bg2) !important; border:1px solid var(--border) !important; border-radius:7px !important; color:#d0eeff !important; }
[data-testid="stSlider"] > div > div > div { background:var(--cyan) !important; }
.phead { font-family:'Orbitron',monospace; font-size:1.7rem; font-weight:900; letter-spacing:.08em; background:linear-gradient(90deg,var(--cyan),var(--purple)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.psub { font-family:'JetBrains Mono',monospace; font-size:.68rem; color:var(--dim); letter-spacing:.16em; margin-bottom:1.4rem; }
.modelbar { display:flex; align-items:center; gap:10px; margin-bottom:1.2rem; padding:8px 14px; background:rgba(0,245,255,.04); border:1px solid var(--border); border-radius:8px; }
.modelbar .tag { font-family:'JetBrains Mono',monospace; font-size:.6rem; color:var(--dim); letter-spacing:.14em; }
.modelbar .name { font-family:'Rajdhani',sans-serif; font-size:1rem; font-weight:600; color:var(--cyan); }
[data-testid="stChatMessage"] { background:transparent !important; border:none !important; }
.ububble { max-width:72%; margin-left:auto; background:linear-gradient(135deg,rgba(0,245,255,.1),rgba(0,180,255,.05)); border:1px solid rgba(0,245,255,.25); border-radius:14px 14px 3px 14px; padding:11px 15px; font-size:1rem; line-height:1.55; }
.abubble { max-width:80%; background:linear-gradient(135deg,rgba(180,0,255,.08),rgba(100,0,180,.04)); border:1px solid rgba(180,0,255,.2); border-radius:14px 14px 14px 3px; padding:11px 15px; font-size:1rem; line-height:1.65; }
.meta { font-family:'JetBrains Mono',monospace; font-size:.58rem; color:var(--dim); margin-top:4px; letter-spacing:.07em; }
.meta.r { text-align:right; }
[data-testid="stChatInput"] textarea { background:var(--bg2) !important; border:1px solid var(--border) !important; border-radius:10px !important; color:#d0eeff !important; font-family:'Rajdhani',sans-serif !important; font-size:1rem !important; }
::-webkit-scrollbar{width:4px} ::-webkit-scrollbar-track{background:var(--bg0)} ::-webkit-scrollbar-thumb{background:rgba(0,245,255,.22);border-radius:3px}
hr { border-color:var(--border) !important; }
</style>
""", unsafe_allow_html=True)

for k, v in {"messages": [], "req_count": 0, "total_tokens": 0, "last_latency": 0.0}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def check_health():
    try:
        r = requests.get(f"{VLLM_HOST}/health", timeout=2)
        return "online" if r.status_code == 200 else "offline"
    except Exception:
        return "offline"

def fetch_models():
    try:
        r = requests.get(f"{VLLM_HOST}/v1/models", timeout=3)
        if r.status_code == 200:
            return [m["id"] for m in r.json().get("data", [])]
    except Exception:
        pass
    return []

def chat_stream(model_id, messages, temperature, top_p):
    return requests.post(
        f"{VLLM_HOST}/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={"model": model_id, "messages": messages, "temperature": temperature, "top_p": top_p, "stream": True},
        stream=True, timeout=120,
    )

def parse_stream(response):
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                delta = json.loads(data)["choices"][0]["delta"]
                if "content" in delta and delta["content"]:
                    yield delta["content"]
            except Exception:
                continue

with st.sidebar:
    st.markdown('<div class="logo"><div class="logo-title">⚡ vLLM NEXUS</div><div class="logo-sub">INFERENCE TERMINAL</div></div>', unsafe_allow_html=True)

    status = check_health()
    models = fetch_models()

    if status == "online":
        st.markdown('<div class="pill on"><div class="dot on"></div>SERVER ONLINE</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pill off"><div class="dot off"></div>SERVER OFFLINE</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="slabel">// model</span>', unsafe_allow_html=True)

    if models:
        chosen_id = st.selectbox("model", models, label_visibility="collapsed")
        st.markdown(f'<div class="minfo"><b>ID</b> {chosen_id}<br><b>STATUS</b> serving</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="minfo"><b>NO MODELS FOUND</b><br>Start the vLLM server first.</div>', unsafe_allow_html=True)
        chosen_id = None

    st.markdown('<span class="slabel">// inference</span>', unsafe_allow_html=True)
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.05)
    top_p       = st.slider("Top-P", 0.1, 1.0, 0.95, 0.05)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑  CLEAR CHAT"):
        st.session_state.messages     = []
        st.session_state.req_count    = 0
        st.session_state.total_tokens = 0
        st.rerun()

    if st.button("🔄  REFRESH"):
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("REQS", st.session_state.req_count)
    c2.metric("TOKENS", st.session_state.total_tokens)
    st.metric("LATENCY", f"{st.session_state.last_latency:.2f}s")

st.markdown('<div class="phead">vLLM NEXUS</div>', unsafe_allow_html=True)
st.markdown('<div class="psub">// OPEN-SOURCE LLM INFERENCE TERMINAL</div>', unsafe_allow_html=True)
st.markdown(f'<div class="modelbar"><span class="tag">ACTIVE MODEL ›</span><span class="name">{chosen_id or "No model loaded"}</span></div>', unsafe_allow_html=True)
st.markdown("---")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<div class="ububble">{msg["content"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="meta r">{msg.get("ts","")}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar="⚡"):
            st.markdown(f'<div class="abubble">{msg["content"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="meta">{msg.get("ts","")} · {msg.get("latency","")} · ~{msg.get("tokens",0)} tokens</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Transmit message…"):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({"role": "user", "content": prompt, "ts": ts})
    with st.chat_message("user", avatar="👤"):
        st.markdown(f'<div class="ububble">{prompt}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="meta r">{ts}</div>', unsafe_allow_html=True)

    if status != "online" or not chosen_id:
        st.warning("⚠  vLLM server offline or no model loaded.")
    else:
        api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] in ("user", "assistant")]
        with st.chat_message("assistant", avatar="⚡"):
            placeholder = st.empty()
            full = ""
            t0 = time.time()
            try:
                for chunk in parse_stream(chat_stream(chosen_id, api_msgs, temperature, top_p)):
                    full += chunk
                    placeholder.markdown(f'<div class="abubble">{full}▌</div>', unsafe_allow_html=True)
                latency = round(time.time() - t0, 2)
                toks    = len(full.split())
                ts_r    = datetime.now().strftime("%H:%M:%S")
                placeholder.markdown(f'<div class="abubble">{full}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="meta">{ts_r} · {latency}s · ~{toks} tokens</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": full, "ts": ts_r, "latency": f"{latency}s", "tokens": toks})
                st.session_state.req_count    += 1
                st.session_state.total_tokens += toks
                st.session_state.last_latency  = latency
            except Exception as e:
                st.error(f"⚠  Stream error: {e}")