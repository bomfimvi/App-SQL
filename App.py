import streamlit as st
from groq import Groq
import psycopg2, sqlparse, os, hashlib
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="SQL NEXUS PRO", page_icon="🛡️", layout="wide")

# 🔐 SEGURANÇA: Chaves nos Secrets
CHAVE_GROQ = st.secrets.get("GROQ_API_KEY", "")
DB_URL = st.secrets.get("DATABASE_URL", "") # Vamos configurar isso no Streamlit Cloud

# --- 2. CONEXÃO COM BANCO EXTERNO ---
def get_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Tabela de Usuários
    cur.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    # Tabela de Histórico
    cur.execute('''CREATE TABLE IF NOT EXISTS h 
                 (id SERIAL PRIMARY KEY, user_id INTEGER, dt TEXT, q TEXT, r TEXT)''')
    conn.commit()
    cur.close()
    conn.close()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_login(user, pwd):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE username = %s AND password = %s', (user, make_hash(pwd)))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res[0] if res else None

def register_user(user, pwd):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password) VALUES (%s,%s)', (user, make_hash(pwd)))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except: return False

def salvar_historico(user_id, q, r):
    conn = get_connection()
    cur = conn.cursor()
    dt = datetime.now().strftime("%d/%m %H:%M")
    cur.execute('INSERT INTO h (user_id, dt, q, r) VALUES (%s,%s,%s,%s)', (user_id, dt, q, r))
    conn.commit()
    cur.close()
    conn.close()

if DB_URL: init_db()

# --- 3. TELA DE LOGIN ---
if "user_id" not in st.session_state:
    st.markdown("<h1 style='text-align:center; color:#10b981;'>🛡️ SQL NEXUS PRO</h1>", unsafe_allow_html=True)
    if not DB_URL:
        st.error("Configure a DATABASE_URL nos Secrets para continuar.")
        st.stop()
    
    aba_log, aba_reg = st.tabs(["Acessar Conta", "Criar Nova Conta"])
    with aba_log:
        u = st.text_input("Usuário:", key="u_log")
        p = st.text_input("Senha:", type="password", key="p_log")
        if st.button("ENTRAR"):
            uid = check_login(u, p)
            if uid:
                st.session_state["user_id"] = uid
                st.session_state["username"] = u
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")

    with aba_reg:
        new_u = st.text_input("Escolha um Usuário:", key="u_reg")
        new_p = st.text_input("Escolha uma Senha:", type="password", key="p_reg")
        if st.button("CADASTRAR"):
            if register_user(new_u, new_p):
                st.success("Conta criada! Vá na aba 'Acessar'.")
            else: st.error("Erro ao criar conta (usuário já existe).")
    st.stop()

# --- 4. INTERFACE PRINCIPAL ---
with st.sidebar:
    st.markdown(f"👤 **Olá, {st.session_state['username']}**")
    menu = st.radio("Menu:", ["🧠 Oráculo", "🧪 Laboratório", "📜 Meu Histórico"])
    
    # Gamificação persistente
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM h WHERE user_id = %s', (st.session_state["user_id"],))
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    st.progress(min((total % 10) * 10, 100))
    st.caption(f"Nível de DBA: { (total // 10) + 1 }")
    if st.button("🚪 Sair"):
        del st.session_state["user_id"]
        st.rerun()

# --- PÁGINAS ---
if menu == "🧠 Oráculo":
    st.title("O Oráculo")
    with st.popover("📖 Guia de Uso"):
        st.write("Dê o DDL e as Regras de Negócio para o Oráculo.")

    ddl = st.text_area("DDL Context:", height=100)
    regras = st.text_area("Regras de Negócio:", height=100)
    query = st.text_area("Sua Query SQL:", height=150)

    if st.button("⚡ ANALISAR", use_container_width=True):
        if query and CHAVE_GROQ:
            with st.spinner("O Oráculo está pensando..."):
                client = Groq(api_key=CHAVE_GROQ)
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Schema:\n{ddl}\nRegras:\n{regras}\nAnalise: {query}"}]
                ).choices[0].message.content
                salvar_historico(st.session_state["user_id"], query, res)
                st.markdown(res)

elif menu == "📜 Meu Histórico":
    st.title("Meu Histórico Privado")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT dt, q, r FROM h WHERE user_id = %s ORDER BY id DESC', (st.session_state["user_id"],))
    logs = cur.fetchall()
    cur.close()
    conn.close()
    
    for d, q, r in logs:
        with st.expander(f"📅 {d} | {q[:30]}..."):
            st.code(q, language='sql')
            st.markdown(r)