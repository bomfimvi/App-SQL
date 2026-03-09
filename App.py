import streamlit as st
from groq import Groq
import sqlite3, sqlparse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SQL NEXUS PRO", page_icon="🛡️", layout="wide")

# BUSCA CHAVE (Local ou Cloud)
# No topo do seu App.py, procure a linha da chave e mude para:
CHAVE_GROQ = st.secrets.get("GROQ_API_KEY", "")

# --- BANCO DE DADOS ---
db_path = os.path.join(os.path.dirname(__file__), 'nexus_final_v5.db')

def init_db():
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS h (id INTEGER PRIMARY KEY AUTOINCREMENT, dt TEXT, q TEXT, r TEXT)')
    conn.close()

def salvar(q, r):
    conn = sqlite3.connect(db_path)
    dt = datetime.now().strftime("%d/%m %H:%M")
    conn.execute('INSERT INTO h (dt, q, r) VALUES (?,?,?)', (dt, q, r))
    conn.commit()
    conn.close()

init_db()

# --- CALLBACK FORMATADOR ---
def format_callback():
    if st.session_state.sql_input:
        st.session_state.sql_input = sqlparse.format(st.session_state.sql_input, reindent=True, keyword_case='upper')

# --- INTERFACE ---
with st.sidebar:
    st.title("🛡️ SQL NEXUS PRO")
    menu = st.radio("Menu:", ["🧠 Oráculo", "📜 Histórico"])
    if st.button("Sair"): st.session_state.clear(); st.rerun()

if menu == "🧠 Oráculo":
    st.markdown("<h1 style='color:#58a6ff;'>O Oráculo</h1>", unsafe_allow_html=True)
    with st.expander("📂 SCHEMA (OPCIONAL)"):
        ddl = st.text_area("Crie aqui o contexto...")
    
    st.text_area("Sua Query:", height=200, key="sql_input")
    st.button("🪄 FORMATAR", on_click=format_callback)
    
    if st.button("⚡ ANALISAR AGORA", use_container_width=True):
        if st.session_state.sql_input:
            with st.spinner("Analisando..."):
                try:
                    client = Groq(api_key=CHAVE)
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": "DBA Senior. Use blocos ```sql."},
                                  {"role": "user", "content": f"{ddl}\n\n{st.session_state.sql_input}"}]
                    ).choices[0].message.content
                    salvar(st.session_state.sql_input, res)
                    st.markdown(res)
                except Exception as e: st.error(f"Erro: {e}")

elif menu == "📜 Histórico":
    st.title("Histórico")
    if st.button("🗑️ ZERAR TUDO"):
        if os.exists(db_path): os.remove(db_path); init_db(); st.rerun()
    # Listagem de logs aqui...