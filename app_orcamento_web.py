import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime
import base64
import os

st.set_page_config(page_title="Alphafest | Orçamentos e Gestão", page_icon="📝", layout="wide")

# --- FUNÇÕES AUXILIARES ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

logo_b64 = get_image_base64("logo.png")
qr_b64 = get_image_base64("pix.png")

def get_sheets_client():
    creds_dict = dict(st.secrets["gcp"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def salvar_no_sheets(dados):
    try:
        client = get_sheets_client()
        sheet = client.open("HistoricoAlphafest").sheet1
        row = [dados['numero_proposta'], dados['data_geracao'], dados['data_entrega'], dados['cliente_nome'], 
               dados['cliente_cpf_cnpj'], dados['cliente_wa'], str(dados['itens']), 
               str(dados['desconto_valor']), str(dados['prazo_dias']), dados['frete_tipo'], "Não", "Não"]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- ESTRUTURA DE ABAS ---
tab1, tab2 = st.tabs(["📝 Novo Orçamento", "📊 Dashboard de Gestão"])

# --- ABA 1: FORMULÁRIO DE ORÇAMENTO ---
with tab1:
    st.title("📝 Orçamentos Alphafest")
    
    if "itens" not in st.session_state: st.session_state.itens = []
    if "previa_dados" not in st.session_state: st.session_state.previa_dados = None

    if st.session_state.previa_dados:
        st.success("✅ Prévia gerada! Confira os dados abaixo:")
        st.write(f"**Cliente:** {st.session_state.previa_dados['cliente_nome']} | **Entrega:** {st.session_state.previa_dados['data_entrega']}")
        c_baixar, c_wa, c_salvar = st.columns(3)
        # Omiti as funções HTML aqui para o código não ficar gigante, use as mesmas funções que validamos antes.
        if c_salvar.button("🚀 Confirmar e Salvar"):
            if salvar_no_sheets(st.session_state.previa_dados):
                st.success("Salvo!")
                st.session_state.itens = []
                st.session_state.previa_dados = None
                st.rerun()

    with st.expander("👤 Dados do Cliente", expanded=True):
        st.text_input("Nome", key="c_nome")
        c1, c2 = st.columns(2)
        c1.text_input("CPF/CNPJ", key="c_cpf")
        c2.text_input("WhatsApp", key="c_wa")

    with st.expander("➕ Adicionar Item", expanded=True):
        st.text_input("Produto", key="i_prod")
        c1, c2 = st.columns(2)
        t = c1.text_input("Tema", key="i_tema")
        n = c1.text_input("Nome/Idade", key="i_nome")
        c = c1.text_input("Cor/Material", key="i_cor")
        q, v = st.columns(2)
        qtd = q.number_input("Quantidade", 1, key="i_qtd")
        v_unit = v.number_input("Valor Unit.", 0.0, key="i_vunit")
        if st.button("Adicionar Item"):
            st.session_state.itens.append({"Produto": st.session_state.i_prod, "Qtd": qtd, "Valor Unit.": v_unit, "Detalhes": f"{t}|{n}|{c}"})
            st.rerun()

# --- ABA 2: DASHBOARD ---
with tab2:
    st.title("📊 Painel de Gestão")
    try:
        client = get_sheets_client()
        df = pd.DataFrame(client.open("HistoricoAlphafest").sheet1.get_all_records())
        
        st.subheader("🔔 Alertas do Dia")
        hoje = datetime.now().strftime("%d/%m/%Y")
        alertas = df[df['data_entrega'] == hoje]
        if not alertas.empty: st.warning(f"Entregas hoje ({hoje}): {len(alertas)} pedidos.")
        else: st.info("Nenhuma entrega hoje.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏆 Top Cliente")
            if not df.empty: st.metric("Cliente VIP", df['cliente_nome'].value_counts().idxmax())
        with col2:
            st.subheader("📈 Vendas Recentes")
            st.line_chart(df.groupby('data_geracao').size())
            
        st.dataframe(df, use_container_width=True)
    except:
        st.error("Planilha não encontrada.")
