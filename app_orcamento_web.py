import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

def get_sheets_client():
    creds_dict = dict(st.secrets["gcp"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def salvar_no_sheets(dados):
    try:
        sheet = get_sheets_client().open("HistoricoAlphafest").sheet1
        row = [dados['numero_proposta'], dados['data_geracao'], dados['data_entrega'], dados['cliente_nome'], 
               dados['cliente_cpf_cnpj'], dados['cliente_wa'], str(dados['itens']), 
               str(dados['desconto_valor']), str(dados['prazo_dias']), dados['frete_tipo'], "Não", "Não"]
        sheet.append_row(row)
        return True
    except: return False

# --- INTERFACE ---
if "itens" not in st.session_state: st.session_state.itens = []
if "previa" not in st.session_state: st.session_state.previa = None

st.title("📄 ORÇAMENTOS ALPHAFEST")

with st.expander("👤 Dados do Cliente", expanded=True):
    st.text_input("Nome / Razão Social", key="c_nome")
    col1, col2 = st.columns(2)
    col1.text_input("CPF / CNPJ", key="c_cpf")
    col2.text_input("WhatsApp", key="c_wa")

with st.expander("➕ Adicionar Novo Item", expanded=True):
    st.text_input("Produto", key="i_prod")
    c1, c2 = st.columns(2)
    t = c1.text_input("Tema", key="i_tema")
    n = c1.text_input("Nome", key="i_nome")
    c = c1.text_input("Cor", key="i_cor")
    id = c2.text_input("Idade", key="i_idade")
    ob = c2.text_input("Obs", key="i_obs")
    q, v = st.columns(2)
    qtd = q.number_input("Qtd", 1, key="i_qtd")
    v_unit = v.number_input("Valor Unit.", 0.0, key="i_vunit")
    if st.button("Adicionar à Lista"):
        detalhes = f"T:{t} | N:{n} | C:{c} | I:{id} | O:{ob}"
        st.session_state.itens.append({"Produto": st.session_state.i_prod, "Qtd": qtd, "Valor": v_unit, "Detalhes": detalhes})
        st.rerun()

# --- TABELA DE ITENS BONITA ---
if st.session_state.itens:
    st.write("### 📋 Itens do Orçamento")
    df = pd.DataFrame(st.session_state.itens)
    st.table(df)
    
    if st.button("🗑️ Limpar Tudo"):
        st.session_state.itens = []
        st.rerun()

    st.write("---")
    desc = st.number_input("Desconto (R$)", 0.0, key="c_desc")
    prazo = st.text_input("Prazo (dias)", "10", key="c_pz")
    entrega = st.date_input("Data Entrega", key="c_dt")
    frete = st.text_input("Frete", "Retirada", key="c_ft")

    if st.button("👁️ GERAR PRÉVIA DA PROPOSTA"):
        # (Lógica de gerar prévia mantida igual)
        dados_previa = {"numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", 
                        "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                        "data_entrega": entrega.strftime("%d/%m/%Y"), "cliente_nome": st.session_state.c_nome,
                        "cliente_cpf_cnpj": st.session_state.c_cpf, "cliente_wa": st.session_state.c_wa,
                        "itens": st.session_state.itens, "desconto_valor": desc, "prazo_dias": prazo, "frete_tipo": frete}
        st.session_state.previa = dados_previa
        st.rerun()

if st.session_state.previa:
    st.success("Prévia gerada com sucesso!")
    if st.button("✅ CONFIRMAR E SALVAR NO SISTEMA"):
        if salvar_no_sheets(st.session_state.previa):
            st.success("Salvo!")
            st.session_state.itens = []
            st.session_state.previa = None
            st.rerun()
