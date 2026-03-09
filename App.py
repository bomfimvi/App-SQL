import streamlit as st
from groq import Groq
import sqlite3, sqlparse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SQL NEXUS PRO", page_icon="🛡️", layout="wide")

# BUSCA CHAVE (Proteção do GitHub: Usando Secrets)
# Localmente, crie o arquivo .streamlit/secrets.toml para testar
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

# --- UTILITÁRIOS (PDF E CÓPIA) ---
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
            if not CHAVE_GROQ:
                st.error("Erro: API Key não configurada nos Secrets!")
            else:
                with st.spinner("Analisando..."):
                    try:
                        client = Groq(api_key=CHAVE_GROQ) # CORRIGIDO: CHAVE -> CHAVE_GROQ
                        res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": "DBA Senior. Use blocos ```sql."},
                                      {"role": "user", "content": f"{ddl}\n\n{st.session_state.sql_input}"}]
                        ).choices[0].message.content
                        salvar(st.session_state.sql_input, res)
                        st.markdown(res)
                        botao_copiar(res)
                        st.download_button("📥 PDF", data=gerar_pdf(st.session_state.sql_input, res), file_name="analise.pdf")
                    except Exception as e: st.error(f"Erro: {e}")

elif menu == "📜 Histórico":
    st.title("Histórico de Estudos")
    if st.button("🗑️ ZERAR TUDO"):
        if os.path.exists(db_path): 
            os.remove(db_path)
            init_db()
            st.rerun()

    conn = sqlite3.connect(db_path)
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
                    conn = sqlite3.connect(db_path)
                    conn.execute('DELETE FROM h WHERE id = ?', (id_reg,))
                    conn.commit(); conn.close(); st.rerun()