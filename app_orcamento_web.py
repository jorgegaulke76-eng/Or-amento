import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime
import base64
import os

st.set_page_config(page_title="Gestão | Alphafest", page_icon="📝", layout="wide")

# --- FUNÇÕES DE CARREGAMENTO E IMAGENS ---
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

# --- MÓDULO ORÇAMENTO (CÓDIGO JÁ VALIDADO) ---
# [O código do formulário de orçamento ficaria aqui, exatamente como validamos antes]
# (Por brevidade, focarei em como estruturar as abas abaixo)

# --- ESTRUTURA DE ABAS ---
tab1, tab2 = st.tabs(["📝 Novo Orçamento", "📊 Dashboard de Gestão"])

with tab1:
    st.title("📝 Orçamentos Alphafest")
    # ... aqui entra o seu formulário de orçamento completo ...

with tab2:
    st.title("📊 Painel de Gestão")
    
    try:
        client = get_sheets_client()
        sheet = client.open("HistoricoAlphafest").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # --- ALERTAS DO DIA ---
        st.subheader("🔔 Alertas do Dia")
        hoje = datetime.now().strftime("%d/%m/%Y")
        alertas = df[df['data_entrega'] == hoje]
        if not alertas.empty:
            st.warning(f"Entregas para hoje ({hoje}):")
            st.table(alertas[['cliente_nome', 'itens']])
        else:
            st.info("Nenhuma entrega pendente para hoje.")

        # --- KPI E GRÁFICOS ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Cliente que mais compra")
            if not df.empty:
                top_cliente = df['cliente_nome'].value_counts().idxmax()
                st.metric("Cliente VIP", top_cliente)
        
        with col2:
            st.subheader("📈 Histórico de Vendas")
            if 'data_geracao' in df.columns:
                df_chart = df.groupby('data_geracao').size()
                st.line_chart(df_chart)

        # --- HISTÓRICO COMPLETO ---
        st.subheader("📜 Histórico de Orçamentos")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error("Não foi possível carregar o histórico. Verifique a conexão com a planilha.")
