import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import os
import re
import json
import urllib.parse
from datetime import datetime, date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

# --- CONEXÃO COM GOOGLE SHEETS ---
def get_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def salvar_no_sheets(dados):
    client = get_sheets_client()
    sheet = client.open("HistoricoAlphafest").sheet1
    row = [
        dados['numero_proposta'], dados['data_geracao'], dados['data_entrega'],
        dados['cliente_nome'], dados['cliente_cpf_cnpj'], dados['cliente_wa'],
        str(dados['itens']), dados['desconto_valor'], dados['prazo_dias'],
        dados['frete_tipo'], "Não", "Não"
    ]
    sheet.append_row(row)

# --- RESTANTE DO CÓDIGO (Interface e Funções) ---
# [Mantenha aqui as suas funções de gerar_proposta_html e extrair_link_whatsapp_completo]
# [Mantenha a interface do seu formulário, mas substitua a chamada 'salvar_no_historico' por 'salvar_no_sheets']

# --- AÇÃO NO BOTÃO GERAR ---
if st.button("🚀 GERAR PROPOSTA"):
    dados = {
        "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
        "data_geracao": datetime.now().strftime("%d/%m/%Y"),
        "data_entrega": entrega.strftime("%d/%m/%Y"),
        "cliente_nome": st.session_state.c_nome,
        "cliente_cpf_cnpj": st.session_state.c_cpf,
        "cliente_wa": st.session_state.c_wa,
        "itens": st.session_state.itens,
        "desconto_valor": desconto,
        "prazo_dias": prazo,
        "frete_tipo": frete
    }
    salvar_no_sheets(dados) # Agora salva na planilha!
    st.session_state.ultima_proposta = {"html": gerar_proposta_html(dados), "link_wa": extrair_link_whatsapp_completo(dados)}
    st.session_state.itens = []
    st.rerun()
