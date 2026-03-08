import streamlit as st
from groq import Groq
import time
from fpdf import FPDF
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SQL NEXUS PRO", page_icon="🛡️", layout="wide")

# --- CSS DE ALTO CONTRASTE (MELHOR VISIBILIDADE) ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    
    /* EDITOR SQL - TEXTO BRANCO NO FUNDO PRETO */
    .stTextArea textarea {
        background-color: #000000 !important;
        color: #ffffff !important; 
        border: 2px solid #58a6ff !important;
        border-radius: 10px !important;
        font-family: 'Consolas', monospace !important;
        font-size: 16px !important;
    }
    .stTextArea textarea::placeholder { color: #8b949e !important; }

    /* BOTÕES */
    .stButton>button {
        background-color: #238636 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 20px !important;
    }
    .gradient-text {
        background: linear-gradient(90deg, #58a6ff, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 2.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE ACESSO ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("<h1 style='text-align: center; color: #10b981;'>🔐 SQL NEXUS LOGIN</h1>", unsafe_allow_html=True)
    chave = st.text_input("Chave de Acesso:", type="password")
    if st.button("DESCRIPTOGRAFAR"):
        if chave == "NEXUS-2026": # Sua senha
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Chave Inválida.")
    st.stop()

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('nexus.db')
    conn.execute('CREATE TABLE IF NOT EXISTS h (dt TEXT, q TEXT, r TEXT)')
    conn.close()

def save(q, r):
    conn = sqlite3.connect('nexus.db')
    conn.execute('INSERT INTO h VALUES (?,?,?)', (datetime.now().strftime("%d/%m %H:%M"), q, r))
    conn.commit()
    conn.close()

init_db()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>🛡️ SQL NEXUS</h2>", unsafe_allow_html=True)
    menu = st.radio("Navegação:", ["🧠 Oráculo IA", "📜 Histórico", "🧪 Lab"])
    if st.button("🚪 Sair"):
        st.session_state["auth"] = False
        st.rerun()

# --- PÁGINAS ---
if menu == "🧠 Oráculo IA":
    st.markdown("<h2 class='gradient-text'>O Oráculo SQL</h2>", unsafe_allow_html=True)
    q_in = st.text_area("Digite sua query (Texto Branco para melhor leitura):", height=250)
    
    if st.button("⚡ ANALISAR"):
        if q_in:
            with st.spinner("Analisando..."):
                client = Groq(api_key="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")
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"DBA Senior, analise: {q_in}"}]
                ).choices[0].message.content
                save(q_in, res)
                st.info(res)
        else: st.warning("Insira uma query.")

elif menu == "📜 Histórico":
    st.markdown("<h2 class='gradient-text'>Seu Histórico</h2>", unsafe_allow_html=True)
    conn = sqlite3.connect('nexus.db')
    logs = conn.execute('SELECT * FROM h ORDER BY dt DESC').fetchall()
    for dt, q, r in logs:
        with st.expander(f"📅 {dt} | {q[:40]}..."):
            st.code(q, language='sql')
            st.write(r)