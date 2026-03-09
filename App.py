import streamlit as st
from groq import Groq
import sqlite3
import sqlparse
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SQL NEXUS PRO", page_icon="🛡️", layout="wide")

# 🔑 CHAVE DA API (Insira sua gsk_... aqui)
MINHA_CHAVE_GROQ = "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" 

# --- 2. BANCO DE DADOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('nexus_v4_final.db')
    conn.execute('CREATE TABLE IF NOT EXISTS h (id INTEGER PRIMARY KEY AUTOINCREMENT, dt TEXT, q TEXT, r TEXT)')
    conn.close()

def salvar(q, r):
    conn = sqlite3.connect('nexus_v4_final.db')
    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn.execute('INSERT INTO h (dt, q, r) VALUES (?,?,?)', (dt, q, r))
    conn.commit()
    conn.close()

init_db()

# --- 3. CALLBACKS (Evita erro de manipulação de Widgets) ---
def formatar_sql_callback():
    if "main_sql_area" in st.session_state:
        raw = st.session_state["main_sql_area"]
        if raw:
            # Formata e atualiza o estado de forma segura para o Streamlit
            st.session_state["main_sql_area"] = sqlparse.format(raw, reindent=True, keyword_case='upper')

# --- 4. UTILITÁRIOS (PDF E CÓPIA) ---
def gerar_pdf(query, analise):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16); pdf.cell(0, 10, "SQL NEXUS - RELATORIO TECNICO", ln=True, align='C'); pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 10, "Query Analisada:", ln=True)
    pdf.set_font("courier", size=10); pdf.multi_cell(0, 8, query); pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 10, "Parecer do Oraculo:", ln=True)
    pdf.set_font("helvetica", size=11)
    clean = analise.replace('`', '').encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 7, clean)
    return bytes(pdf.output())

def botao_copiar(texto):
    id_btn = f"btn_{hash(texto)}"
    js = f"""
        <button id="{id_btn}" style="background:#10b981; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; font-weight:bold; width:100%;">📋 COPIAR RESULTADO</button>
        <script>
        document.getElementById("{id_btn}").onclick = function() {{
            const t = `{texto.replace('`', '\\`').replace('$', '\\$')}`;
            navigator.clipboard.writeText(t).then(() => alert("✅ Copiado para a área de transferência!"));
        }};
        </script>
    """
    components.html(js, height=45)

# --- 5. INTERFACE DE LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    st.markdown("<h1 style='text-align:center; color:#10b981;'>🛡️ LOGIN SQL NEXUS PRO</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        chave = st.text_input("Insira sua Chave de Acesso:", type="password")
        if st.button("DESCRIPTOGRAFAR ACESSO"):
            if chave == "NEXUS-PRO-2026": 
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Chave inválida. Entre em contato com o suporte.")
    st.stop()

# --- 6. MENU LATERAL E DASHBOARD ---
with st.sidebar:
    st.markdown("<h2 style='color:#10b981'>SQL NEXUS PRO</h2>", unsafe_allow_html=True)
    menu = st.radio("Navegação:", ["🧠 Oráculo IA", "🧪 Laboratório", "📜 Histórico"])
    st.markdown("---")
    
    # Contador de Queries
    conn = sqlite3.connect('nexus_v4_final.db')
    total_q = conn.execute('SELECT COUNT(*) FROM h').fetchone()[0]
    conn.close()
    
    st.markdown(f"📊 **Otimizações Feitas:** {total_q}")
    if st.button("🚪 Sair do Sistema"): 
        st.session_state["auth"] = False
        st.rerun()

# --- 7. PÁGINAS ---

if menu == "🧠 Oráculo IA":
    st.markdown("<h1 style='color:#58a6ff;'>O Oráculo</h1>", unsafe_allow_html=True)
    
    with st.expander("📂 ADICIONAR CONTEXTO DE SCHEMA (Melhora a Precisão)"):
        ddl = st.text_area("Cole o CREATE TABLE aqui:", height=100, placeholder="Opcional: Informe a estrutura das tabelas...")

    # Campo de Query com suporte a Callback para formatação
    st.text_area("Sua Query SQL:", height=250, key="main_sql_area", placeholder="SELECT * FROM ...")
    
    c1, c2 = st.columns([1, 4])
    with c1:
        # O segredo para não dar erro: on_click executa o código ANTES da reconstrução do widget
        st.button("🪄 FORMATAR", on_click=formatar_sql_callback)
    
    if st.button("⚡ ANALISAR E OTIMIZAR", use_container_width=True):
        q_in = st.session_state["main_sql_area"]
        if q_in:
            with st.spinner("Consultando cérebro da IA..."):
                try:
                    client = Groq(api_key=MINHA_CHAVE_GROQ)
                    sys_prompt = "Você é um DBA Sênior especialista em performance. OBRIGATÓRIO: Sempre forneça o código SQL final em blocos ```sql."
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt},
                                  {"role": "user", "content": f"Schema:\n{ddl}\n\nQuery:\n{q_in}"}]
                    ).choices[0].message.content
                    
                    salvar(q_in, res)
                    st.markdown("---")
                    st.markdown(res)
                    botao_copiar(res)
                    
                    pdf_data = gerar_pdf(q_in, res)
                    st.download_button("📥 BAIXAR PARECER EM PDF", data=pdf_data, file_name=f"analise_sql_{datetime.now().strftime('%d%m%Y')}.pdf")
                except Exception as e:
                    st.error(f"Erro na análise: {e}")
        else: st.warning("Por favor, insira uma consulta SQL.")

elif menu == "🧪 Laboratório":
    st.markdown("<h1 style='color:#58a6ff;'>Laboratório de Testes</h1>", unsafe_allow_html=True)
    st.write("Compare duas versões e veja o veredito técnico.")
    
    col1, col2 = st.columns(2)
    with col1: qa = st.text_area("Versão A (Original):", height=200, key="lab_a")
    with col2: qb = st.text_area("Versão B (Otimizada):", height=200, key="lab_b")
    
    if st.button("⚖️ COMPARAR PERFORMANCE"):
        if qa and qb:
            with st.spinner("Avaliando planos de execução teóricos..."):
                client = Groq(api_key=MINHA_CHAVE_GROQ)
                comp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Aja como um Tuning Expert. Compare performance: \nQuery A: {qa}\nQuery B: {qb}"}]
                ).choices[0].message.content
                st.success("### 📊 Veredito do Expert")
                st.markdown(comp)
                botao_copiar(comp)

elif menu == "📜 Histórico":
    st.markdown("<h1 style='color:#58a6ff;'>Histórico de Consultas</h1>", unsafe_allow_html=True)
    
    if st.button("🔥 LIMPAR TODO O HISTÓRICO"):
        conn = sqlite3.connect('nexus_v4_final.db'); conn.execute('DELETE FROM h'); conn.commit(); conn.close()
        st.rerun()

    conn = sqlite3.connect('nexus_v4_final.db')
    logs = conn.execute('SELECT id, dt, q, r FROM h ORDER BY id DESC').fetchall()
    conn.close()
    
    for id_reg, d, q, r in logs:
        with st.expander(f"📅 {d} | {q[:40]}..."):
            st.code(q, language='sql')
            st.markdown(r)
            
            c_c, c_d = st.columns([4, 1])
            with c_c: botao_copiar(r)
            with c_d: 
                if st.button("🗑️", key=f"del_{id_reg}"):
                    conn = sqlite3.connect('nexus_v4_final.db')
                    conn.execute('DELETE FROM h WHERE id = ?', (id_reg,))
                    conn.commit(); conn.close(); st.rerun()