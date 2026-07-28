import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamentos | Alphafest", page_icon="📝", layout="centered")

# --- CONEXÃO COM GOOGLE SHEETS ---
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
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- INTERFACE ---
if "itens" not in st.session_state: st.session_state.itens = []
if "previa" not in st.session_state: st.session_state.previa = None

st.title("📝 Orçamentos Alphafest")
st.markdown("---")

with st.container():
    st.subheader("👤 Dados do Cliente")
    st.text_input("Nome / Razão Social", key="c_nome", placeholder="Ex: Maria Silva")
    c1, c2 = st.columns(2)
    c1.text_input("CPF / CNPJ", key="c_cpf")
    c2.text_input("WhatsApp", key="c_wa", placeholder="(11) 99999-9999")

with st.container():
    st.subheader("➕ Adicionar Item")
    st.text_input("Produto", key="i_prod", placeholder="Ex: Topo de Bolo")
    c1, c2 = st.columns(2)
    t = c1.text_input("Tema", key="i_tema")
    n = c1.text_input("Nome/Idade", key="i_nome")
    c = c1.text_input("Cor/Material", key="i_cor")
    ob = c2.text_input("Observações Adicionais", key="i_obs")
    q, v = st.columns(2)
    qtd = q.number_input("Quantidade", 1, key="i_qtd")
    v_unit = v.number_input("Valor Unitário (R$)", 0.0, key="i_vunit", format="%.2f")
    
    if st.button("Adicionar à Lista"):
        detalhes = f"Tema: {t} | Nome: {n} | Cor: {c} | Obs: {ob}"
        st.session_state.itens.append({"Produto": st.session_state.i_prod, "Qtd": qtd, "Valor Unit.": v_unit, "Especificações": detalhes})
        st.rerun()

# --- TABELA PROFISSIONAL ---
if st.session_state.itens:
    st.subheader("📋 Itens do Orçamento")
    
    # Formatação Profissional do DataFrame
    df = pd.DataFrame(st.session_state.itens)
    
    # Exibe a tabela formatada
    st.dataframe(
        df, 
        use_container_width=True,
        column_config={
            "Valor Unit.": st.column_config.NumberColumn("Valor Unit. (R$)", format="R$ %.2f"),
        },
        hide_index=True
    )
    
    if st.button("🗑️ Limpar Lista"):
        st.session_state.itens = []
        st.rerun()

    st.markdown("---")
    c1, c2 = st.columns(2)
    desc = c1.number_input("Desconto (R$)", 0.0, key="c_desc", format="%.2f")
    prazo = c2.text_input("Prazo de Entrega (dias)", "10", key="c_pz")
    entrega = st.date_input("Data Limite", key="c_dt")
    frete = st.text_input("Frete/Entrega", "Retirada em Itatiba", key="c_ft")

    if st.button("👁️ GERAR PRÉVIA DA PROPOSTA", type="primary"):
        dados_previa = {
            "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", 
            "data_geracao": datetime.now().strftime("%d/%m/%Y"),
            "data_entrega": entrega.strftime("%d/%m/%Y"), 
            "cliente_nome": st.session_state.c_nome,
            "cliente_cpf_cnpj": st.session_state.c_cpf, 
            "cliente_wa": st.session_state.c_wa,
            "itens": st.session_state.itens, 
            "desconto_valor": desc, 
            "prazo_dias": prazo, 
            "frete_tipo": frete
        }
        st.session_state.previa = dados_previa
        st.rerun()

if st.session_state.previa:
    st.success("✅ Prévia pronta para conferência.")
    if st.button("🚀 CONFIRMAR E SALVAR NO HISTÓRICO"):
        if salvar_no_sheets(st.session_state.previa):
            st.success("Orçamento salvo com sucesso!")
            st.session_state.itens = []
            st.session_state.previa = None
            st.rerun()
