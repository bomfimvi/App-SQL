import streamlit as st
from groq import Groq
import sqlite3
import sqlparse
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="SQL NEXUS PRO", page_icon="🛡️", layout="wide")

# Lógica para pegar a chave: primeiro tenta nos Secrets (Cloud), se não tiver, usa string vazia
# No Streamlit Cloud, você configurará isso no painel lateral em "Secrets"
API_KEY = st.secrets.get("GROQ_API_KEY", "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")

# --- 2. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('nexus_pro_v5.db')
    conn.execute('CREATE TABLE IF NOT EXISTS h (id INTEGER PRIMARY KEY AUTOINCREMENT, dt TEXT, q TEXT, r TEXT)')
    conn.close()

def salvar(q, r):
    conn = sqlite3.connect('nexus_pro_v5.db')
    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn.execute('INSERT INTO h (dt, q, r) VALUES (?,?,?)', (dt, q, r))
    conn.commit()
    conn.close()

init_db()

# --- 3. CALLBACK PARA FORMATAR SQL (Evita o erro de StreamlitAPIException) ---
def formatar_sql_callback():
    if "sql_input" in st.session_state:
        raw = st.session_state["sql_input"]
        if raw:
            st.session_state["sql_input"] = sqlparse.format(raw, reindent=True, keyword_case='upper')

# --- 4. UTILITÁRIOS ---
def gerar_pdf(query, analise):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16); pdf.cell(0, 10, "SQL NEXUS - RELATORIO", ln=True, align='C'); pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 10, "Query:", ln=True)
    pdf.set_font("courier", size=10); pdf.multi_cell(0, 8, query); pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 10, "Analise:", ln=True)
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
            navigator.clipboard.writeText(t).then(() => alert("✅ Copiado!"));
        }};
        </script>
    """
    components.html(js, height=45)

# --- 5. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    st.markdown("<h1 style='text-align:center;'>🛡️ SQL NEXUS</h1>", unsafe_allow_html=True)
    chave = st.text_input("Chave de Acesso:", type="password")
    if st.button("ENTRAR"):
        if chave == "NEXUS-PRO-2026": st.session_state["auth"] = True; st.rerun()
        else: st.error("Chave inválida!")
    st.stop()

# --- 6. SIDEBAR DASHBOARD ---
with st.sidebar:
    st.markdown("<h2 style='color:#10b981'>SQL NEXUS PRO</h2>", unsafe_allow_html=True)
    menu = st.radio("Menu:", ["🧠 Oráculo IA", "🧪 Laboratório", "📜 Histórico"])
    
    # Dashboard de Nível
    conn = sqlite3.connect('nexus_pro_v5.db')
    total = conn.execute('SELECT COUNT(*) FROM h').fetchone()[0]
    conn.close()
    
    st.markdown("---")
    st.metric("Consultas Feitas", total)
    st.progress(min((total % 10) * 10, 100))
    st.caption(f"Nível de DBA: { (total // 10) + 1 }")
    
    if st.button("🚪 Sair"): st.session_state["auth"] = False; st.rerun()

# --- 7. PÁGINAS ---
if menu == "🧠 Oráculo IA":
    st.title("O Oráculo")
    
    with st.expander("📂 CONTEXTO DE SCHEMA (DDL)"):
        ddl_txt = st.text_area("Cole seu CREATE TABLE aqui para análise precisa:", height=100)

    st.text_area("Sua Query SQL:", height=200, key="sql_input")
    
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        st.button("🪄 FORMATAR", on_click=formatar_sql_callback)

    if st.button("⚡ ANALISAR AGORA", use_container_width=True):
        query = st.session_state["sql_input"]
        if query:
            with st.spinner("O Oráculo está pensando..."):
                try:
                    client = Groq(api_key=API_KEY)
                    sys_msg = "Você é um DBA Sênior. Use blocos ```sql para códigos."
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_msg},
                                  {"role": "user", "content": f"Schema Context:\n{ddl_txt}\n\nAnalise: {query}"}]
                    ).choices[0].message.content
                    
                    salvar(query, res)
                    st.markdown(res)
                    botao_copiar(res)
                    st.download_button("📥 BAIXAR PDF", data=gerar_pdf(query, res), file_name="analise.pdf")
                except Exception as e:
                    st.error(f"Erro: {e}")
        else: st.warning("Digite uma query!")

elif menu == "🧪 Laboratório":
    st.title("🧪 Laboratório")
    c1, c2 = st.columns(2)
    with c1: q1 = st.text_area("Versão A:", height=200, key="la")
    with c2: q2 = st.text_area("Versão B:", height=200, key="lb")
    
    if st.button("⚖️ COMPARAR PERFORMANCE"):
        if q1 and q2:
            with st.spinner("Comparando..."):
                client = Groq(api_key=API_KEY)
                comp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Compare a performance de A e B:\nA: {q1}\nB: {q2}"}]
                ).choices[0].message.content
                st.success(comp)
                botao_copiar(comp)

elif menu == "📜 Histórico":
    st.title("📜 Histórico")
    if st.button("🗑️ ZERAR TUDO"):
        conn = sqlite3.connect('nexus_pro_v5.db'); conn.execute('DELETE FROM h'); conn.commit(); conn.close()
        st.rerun()

    conn = sqlite3.connect('nexus_pro_v5.db')
    logs = conn.execute('SELECT id, dt, q, r FROM h ORDER BY id DESC').fetchall()
    conn.close()
    
    for id_reg, d, q, r in logs:
        with st.expander(f"📅 {d} | {q[:30]}..."):
            st.code(q, language='sql')
            st.markdown(r)
            c_c, c_d = st.columns([4, 1])
            with c_c: botao_copiar(r)
            with c_d: 
                if st.button("🗑️", key=f"del_{id_reg}"):
                    conn = sqlite3.connect('nexus_pro_v5.db')
                    conn.execute('DELETE FROM h WHERE id = ?', (id_reg,))
                    conn.commit(); conn.close(); st.rerun()