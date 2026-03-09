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
    try:
        # Tenta conectar usando a URL dos Secrets
        return psycopg2.connect(DB_URL)
    except Exception as e:
        st.error(f"❌ Falha de Conexão com o Banco de Dados: {str(e)}")
        st.info("Verifique se a DATABASE_URL nos Secrets está correta e inclui ?sslmode=require")
        st.stop()

def init_db():
    if not DB_URL: return
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

# Segurança de Senhas
def make_hash(pwd): return hashlib.sha256(str.encode(pwd)).hexdigest()

def check_login(user, pwd):
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username = %s AND password = %s', (user, make_hash(pwd)))
        res = cur.fetchone(); cur.close(); conn.close()
        return res[0] if res else None
    except: return None

def register_user(user, pwd):
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password) VALUES (%s,%s)', (user, make_hash(pwd)))
        conn.commit(); cur.close(); conn.close()
        return True
    except: return False

def salvar_historico(uid, q, r):
    try:
        conn = get_connection(); cur = conn.cursor()
        dt = datetime.now().strftime("%d/%m %H:%M")
        cur.execute('INSERT INTO h (user_id, dt, q, r) VALUES (%s,%s,%s,%s)', (uid, dt, q, r))
        conn.commit(); cur.close(); conn.close()
    except Exception as e: st.error(f"Erro ao salvar: {e}")

# Inicializa as tabelas se a URL existir
if DB_URL: init_db()

# --- 3. UTILITÁRIOS ---
def gerar_pdf(query, analise):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16); pdf.cell(0, 10, "SQL NEXUS - RELATORIO TECNICO", ln=True, align='C'); pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 10, "Query Analisada:", ln=True)
    pdf.set_font("courier", size=10); pdf.multi_cell(0, 8, query); pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 10, "Analise do Oraculo:", ln=True)
    pdf.set_font("helvetica", size=11)
    clean = analise.replace('`', '').encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 7, clean)
    return bytes(pdf.output())

def botao_copiar(texto):
    id_btn = f"btn_{hash(texto)}"
    js = f"""<button id="{id_btn}" style="background:#10b981; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; font-weight:bold; width:100%;">📋 COPIAR RESULTADO</button>
    <script>document.getElementById("{id_btn}").onclick = function() {{ navigator.clipboard.writeText(`{texto.replace('`','\\`').replace('$','\\$')}`); alert("✅ Copiado!"); }};</script>"""
    components.html(js, height=45)

# --- 4. LANDING PAGE PREMIUM ---
def mostrar_landing():
    st.markdown("""
        <style>
        .hero { text-align: center; padding: 80px 0; background: linear-gradient(135deg, #0e1117 0%, #1a1c24 100%); border-radius: 20px; margin-bottom: 40px; }
        .hero-h1 { font-size: 60px; font-weight: 800; background: linear-gradient(90deg, #10b981, #58a6ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .feature-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 30px; text-align: center; height: 100%; }
        .neon { color: #10b981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.5); font-weight: bold; }
        </style>
        <div class="hero">
            <h1 class="hero-h1">SQL NEXUS PRO</h1>
            <p style='color:#8b949e; font-size:24px;'>A Elite da Otimização de Consultas SQL.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("<div class='feature-card'><h2 class='neon'>🧠 Oráculo</h2><p>IA que entende suas Regras de Negócio e Schema.</p></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='feature-card'><h2 class='neon'>⚡ Speed</h2><p>Identificação de gargalos e ganho de performance real.</p></div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='feature-card'><h2 class='neon'>🛡️ Privacy</h2><p>Histórico persistente e 100% privado.</p></div>", unsafe_allow_html=True)
    st.write("---")

# --- 5. LÓGICA DE NAVEGAÇÃO / LOGIN ---
if "user_id" not in st.session_state:
    mostrar_landing()
    
    col_msg, col_form = st.columns([1, 1])
    with col_msg:
        st.subheader("🚀 Pronto para o Próximo Nível?")
        st.write("Crie sua conta agora e tenha acesso ao Oráculo de Performance mais avançado do mercado.")
        st.info("💡 Suas análises ficam salvas para sempre em nosso banco de dados seguro.")

    with col_form:
        t1, t2 = st.tabs(["🔐 Acessar Conta", "📝 Criar Cadastro"])
        with t1:
            u = st.text_input("Usuário:", key="login_user")
            p = st.text_input("Senha:", type="password", key="login_pwd")
            if st.button("DESBLOQUEAR SISTEMA", use_container_width=True):
                uid = check_login(u, p)
                if uid:
                    st.session_state.update({"user_id": uid, "username": u})
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")
        
        with t2:
            nu = st.text_input("Escolha um Usuário:", key="reg_user")
            np = st.text_input("Defina uma Senha:", type="password", key="reg_pwd")
            if st.button("CRIAR MINHA CONTA", use_container_width=True):
                if register_user(nu, np):
                    st.success("Conta criada com sucesso! Faça login na aba ao lado.")
                else: st.error("Erro: Usuário já existe ou banco indisponível.")
    st.stop()

# --- 6. ÁREA INTERNA (LOGADO) ---
with st.sidebar:
    st.markdown(f"👤 **Olá, {st.session_state['username']}**")
    menu = st.radio("Navegação:", ["🧠 Oráculo", "🧪 Laboratório", "📜 Meu Histórico"])
    
    # Sistema de Rank (Gamificação)
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM h WHERE user_id = %s', (st.session_state["user_id"],))
        total_q = cur.fetchone()[0]; cur.close(); conn.close()
    except: total_q = 0

    st.markdown("---")
    rank_names = ["Estagiário", "Júnior", "Pleno", "Sênior", "Nexus Legend"]
    current_rank = rank_names[min(total_q // 5, len(rank_names)-1)]
    st.subheader(f"🏆 Rank: {current_rank}")
    st.progress(min((total_q % 5) * 20, 100))
    st.caption(f"Consultas realizadas: {total_q}")
    
    st.markdown("---")
    if st.button("🚪 Sair do Sistema"):
        del st.session_state["user_id"]
        st.rerun()

# PÁGINA: ORÁCULO
if menu == "🧠 Oráculo":
    st.title("🧠 O Oráculo de SQL")
    
    with st.popover("📖 GUIA: Como extrair o máximo do Oráculo?"):
        st.markdown("""
        1. **Contexto (DDL):** Cole seu `CREATE TABLE`. Isso ajuda a IA a ver índices e tipos.
        2. **Regras de Negócio:** Informe detalhes como: *"Ignorar pedidos cancelados"* ou *"Calcular 10% de imposto"*.
        3. **Envio:** Use **Ctrl + Enter** para aplicar o texto nos campos.
        """)

    col_ctx1, col_ctx2 = st.columns(2)
    ddl = col_ctx1.text_area("📂 Schema Context (DDL):", height=120, placeholder="Cole seu CREATE TABLE aqui...")
    biz = col_ctx2.text_area("⚖️ Regras de Negócio:", height=120, placeholder="Ex: Apenas vendas confirmadas...")

    query = st.text_area("✍️ Sua Query SQL para análise:", height=200, key="main_sql")
    
    if st.button("⚡ ANALISAR PERFORMANCE", use_container_width=True):
        if query and CHAVE_GROQ:
            with st.spinner("O Oráculo está meditando sobre seus dados..."):
                try:
                    client = Groq(api_key=CHAVE_GROQ)
                    prompt = f"Considere o Schema:\n{ddl}\nRegras de Negocio:\n{biz}\nAnalise e otimize esta query SQL:\n{query}"
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": "Voce e um DBA Senior especialista em performance PostgreSQL/SQL Server."},
                                  {"role": "user", "content": prompt}]
                    ).choices[0].message.content
                    
                    salvar_historico(st.session_state["user_id"], query, res)
                    st.markdown("---")
                    st.markdown(res)
                    botao_copiar(res)
                    st.download_button("📥 Baixar Relatório PDF", gerar_pdf(query, res), "analise_nexus.pdf")
                except Exception as e: st.error(f"Erro na IA: {e}")
        else: st.warning("Preencha a query e verifique a chave da API.")

# PÁGINA: LABORATÓRIO
elif menu == "🧪 Laboratório":
    st.title("🧪 Laboratório de Benchmarking")
    st.write("Compare duas versões da mesma query e descubra qual é mais eficiente.")
    
    c1, c2 = st.columns(2)
    qa = c1.text_area("Query A (Original):", height=250)
    qb = c2.text_area("Query B (Refatorada):", height=250)
    
    if st.button("⚖️ COMPARAR QUERIES", use_container_width=True):
        if qa and qb:
            with st.spinner("Comparando planos de execução teóricos..."):
                client = Groq(api_key=CHAVE_GROQ)
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Compare a performance técnica entre A e B. Diga qual vence e por que:\nA: {qa}\nB: {qb}"}]
                ).choices[0].message.content
                st.success("### Veredito do Laboratório")
                st.markdown(res)

# PÁGINA: HISTÓRICO
elif menu == "📜 Meu Histórico":
    st.title("📜 Seu Histórico de Consultas")
    st.write("Todas as suas otimizações ficam salvas aqui de forma privada.")
    
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute('SELECT dt, q, r FROM h WHERE user_id = %s ORDER BY id DESC', (st.session_state["user_id"],))
        logs = cur.fetchall(); cur.close(); conn.close()
        
        if not logs: st.info("Você ainda não realizou consultas.")
        
        for dt, q, r in logs:
            with st.expander(f"📅 {dt} | {q[:40]}..."):
                st.code(q, language='sql')
                st.markdown(r)
                botao_copiar(r)
    except Exception as e: st.error(f"Erro ao carregar histórico: {e}")