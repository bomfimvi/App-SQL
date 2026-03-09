import streamlit as st
from groq import Groq
import psycopg2, sqlparse, os, hashlib
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="SQL NEXUS PRO", page_icon="🛡️", layout="wide")

# Recuperação de Segredos (Configurar no Streamlit Cloud)
CHAVE_GROQ = st.secrets.get("GROQ_API_KEY", "")
DB_URL = st.secrets.get("DATABASE_URL", "")

# --- 2. CONEXÃO COM BANCO EXTERNO (POSTGRESQL) ---
def get_connection():
    if not DB_URL:
        st.error("⚠️ DATABASE_URL não configurada nos Secrets!")
        return None
    try:
        # strip() limpa espaços invisíveis que impedem a tradução do host
        return psycopg2.connect(DB_URL.strip())
    except Exception as e:
        st.error(f"❌ Falha de Conexão: {str(e)}")
        st.info("Dica: Verifique se a URL termina com ?sslmode=require e usa a porta 6543")
        return None

def init_db():
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
            cur.execute('CREATE TABLE IF NOT EXISTS h (id SERIAL PRIMARY KEY, user_id INTEGER, dt TEXT, q TEXT, r TEXT)')
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            st.error(f"⚠️ Erro ao inicializar tabelas: {e}")

# Segurança
def make_hash(pwd): return hashlib.sha256(str.encode(pwd)).hexdigest()

def check_login(user, pwd):
    conn = get_connection()
    if not conn: return None
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE username = %s AND password = %s', (user, make_hash(pwd)))
    res = cur.fetchone(); cur.close(); conn.close()
    return res[0] if res else None

def register_user(user, pwd):
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password) VALUES (%s,%s)', (user, make_hash(pwd)))
        conn.commit(); cur.close(); conn.close()
        return True
    except: return False

def salvar_historico(uid, q, r):
    conn = get_connection()
    if conn:
        dt = datetime.now().strftime("%d/%m %H:%M")
        cur = conn.cursor()
        cur.execute('INSERT INTO h (user_id, dt, q, r) VALUES (%s,%s,%s,%s)', (uid, dt, q, r))
        conn.commit(); cur.close(); conn.close()

# Tenta inicializar o banco ao carregar o app
init_db()

# --- 3. UTILITÁRIOS ---
def gerar_pdf(query, analise):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16); pdf.cell(0, 10, "SQL NEXUS - RELATORIO", ln=True, align='C'); pdf.ln(10)
    pdf.set_font("courier", size=10); pdf.multi_cell(0, 8, query); pdf.ln(5)
    pdf.set_font("helvetica", size=11)
    clean = analise.replace('`', '').encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 7, clean)
    return bytes(pdf.output())

def botao_copiar(texto):
    id_btn = f"btn_{hash(texto)}"
    js = f"""<button id="{id_btn}" style="background:#10b981; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; font-weight:bold; width:100%;">📋 COPIAR RESULTADO</button>
    <script>document.getElementById("{id_btn}").onclick = function() {{ navigator.clipboard.writeText(`{texto.replace('`','\\`').replace('$','\\$')}`); alert("✅ Copiado!"); }};</script>"""
    components.html(js, height=45)

# --- 4. LANDING PAGE ---
def mostrar_landing():
    st.markdown("""
        <style>
        .hero { text-align: center; padding: 60px 0; background: linear-gradient(135deg, #0e1117 0%, #1a1c24 100%); border-radius: 20px; }
        .hero-h1 { font-size: 50px; font-weight: 800; background: linear-gradient(90deg, #10b981, #58a6ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; text-align: center; }
        </style>
        <div class="hero"><h1 class="hero-h1">SQL NEXUS PRO</h1><p style='color:#8b949e; font-size:20px;'>A Inteligência Artificial que protege sua Performance.</p></div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("<div class='card'><h3>🧠 Oráculo</h3><p>Tuning avançado e regras de negócio.</p></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='card'><h3>⚡ Speed</h3><p>Identifique gargalos e melhore o DDL.</p></div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='card'><h3>🔒 Privacy</h3><p>Histórico privado no banco de São Paulo.</p></div>", unsafe_allow_html=True)
    st.write("---")

# --- 5. LOGICA DE ACESSO ---
if "user_id" not in st.session_state:
    mostrar_landing()
    
    col_l, col_r = st.columns([1,1])
    with col_l:
        st.subheader("🚀 Pronto para evoluir?")
        st.write("Crie sua conta e comece a otimizar queries como um Sênior.")
        
    with col_r:
        aba_log, aba_reg = st.tabs(["🔐 Login", "📝 Cadastro"])
        with aba_log:
            u = st.text_input("Usuário:", key="u_log")
            p = st.text_input("Senha:", type="password", key="p_log")
            if st.button("ACESSAR", use_container_width=True):
                uid = check_login(u, p)
                if uid: st.session_state.update({"user_id": uid, "username": u}); st.rerun()
                else: st.error("Acesso negado. Verifique usuário e senha.")
        with aba_reg:
            nu = st.text_input("Novo Usuário:", key="u_reg")
            np = st.text_input("Nova Senha:", type="password", key="p_reg")
            if st.button("CRIAR MINHA CONTA", use_container_width=True):
                if register_user(nu, np): st.success("Conta criada! Vá na aba Login.")
                else: st.error("Erro: Usuário já existe ou falha no banco.")
    st.stop()

# --- 6. AREA INTERNA (LOGADO) ---
with st.sidebar:
    st.markdown(f"👤 **{st.session_state['username']}**")
    menu = st.radio("Menu:", ["🧠 Oráculo", "🧪 Laboratório", "📜 Histórico"])
    
    # Gamificação
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM h WHERE user_id = %s', (st.session_state["user_id"],))
        total = cur.fetchone()[0]; cur.close(); conn.close()
        st.markdown("---")
        st.subheader(f"🏆 Rank: {['Iniciante','Júnior','Pleno','Sênior','Legend'][min(total//5, 4)]}")
        st.progress(min((total % 5) * 20, 100))
    
    if st.button("🚪 Sair"): del st.session_state["user_id"]; st.rerun()

if menu == "🧠 Oráculo":
    st.title("O Oráculo")
    with st.popover("📖 Guia de Uso"):
        st.write("Dê o DDL para análise de performance e as Regras de Negócio para lógica específica.")
    
    c1, c2 = st.columns(2)
    ddl = c1.text_area("📂 DDL (Schema):", height=100, placeholder="CREATE TABLE...")
    regras = c2.text_area("⚖️ Regras de Negócio:", height=100, placeholder="Ex: Pedidos excluídos não aparecem")
    
    query = st.text_area("✍️ SQL para análise:", height=200, key="sql_input")
    
    if st.button("⚡ ANALISAR AGORA", use_container_width=True):
        if query and CHAVE_GROQ:
            with st.spinner("IA Analisando..."):
                try:
                    client = Groq(api_key=CHAVE_GROQ)
                    prompt = f"Schema:\n{ddl}\nRegras:\n{regras}\nQuery:\n{query}"
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}]).choices[0].message.content
                    salvar_historico(st.session_state["user_id"], query, res)
                    st.markdown(res); botao_copiar(res)
                except Exception as e: st.error(f"Erro na IA: {e}")

elif menu == "🧪 Laboratório":
    st.title("🧪 Laboratório de Performance")
    col1, col2 = st.columns(2)
    qa = col1.text_area("Query A:", height=200)
    qb = col2.text_area("Query B:", height=200)
    if st.button("⚖️ COMPARAR"):
        if qa and qb and CHAVE_GROQ:
            client = Groq(api_key=CHAVE_GROQ)
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":f"Compare performance de A e B: {qa} vs {qb}"}]).choices[0].message.content
            st.success(res)

elif menu == "📜 Histórico":
    st.title("📜 Seu Histórico")
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT dt, q, r FROM h WHERE user_id = %s ORDER BY id DESC', (st.session_state["user_id"],))
        logs = cur.fetchall(); cur.close(); conn.close()
        for d, q, r in logs:
            with st.expander(f"📅 {d} | {q[:30]}..."):
                st.code(q, language='sql'); st.markdown(r)