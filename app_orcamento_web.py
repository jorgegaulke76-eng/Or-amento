import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamentos | Alphafest", page_icon="📝", layout="centered")

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

# --- FUNÇÕES DE PROPOSTA ---
def gerar_proposta_html(dados):
    linhas_tabela = ""
    for item in dados["itens"]:
        linhas_tabela += f"<tr><td>{item['Produto']}</td><td>{item['Qtd']}</td></tr>"
    return f"<html><body><h2>Proposta {dados['numero_proposta']}</h2><table border='1'>{linhas_tabela}</table></body></html>"

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    msg = f"Orçamento Alphafest: {dados['numero_proposta']}"
    return f"https://wa.me/{num_wa if len(num_wa)>10 else '55'+num_wa}?text={urllib.parse.quote(msg)}"

# --- INTERFACE ---
if "itens" not in st.session_state: st.session_state.itens = []
if "previa_dados" not in st.session_state: st.session_state.previa_dados = None

st.title("📝 Orçamentos Alphafest")

with st.expander("👤 Dados do Cliente", expanded=True):
    st.text_input("Nome / Razão Social", key="c_nome")
    c1, c2 = st.columns(2)
    c1.text_input("CPF / CNPJ", key="c_cpf")
    c2.text_input("WhatsApp", key="c_wa")

with st.expander("➕ Adicionar Item", expanded=True):
    st.text_input("Produto", key="i_prod")
    c1, c2 = st.columns(2)
    t = c1.text_input("Tema", key="i_tema")
    n = c1.text_input("Nome/Idade", key="i_nome")
    c = c1.text_input("Cor/Material", key="i_cor")
    ob = c2.text_input("Observações", key="i_obs")
    q, v = st.columns(2)
    qtd = q.number_input("Quantidade", 1, key="i_qtd")
    v_unit = v.number_input("Valor Unit. (R$)", 0.0, key="i_vunit", format="%.2f")
    if st.button("Adicionar à Lista"):
        st.session_state.itens.append({"Produto": st.session_state.i_prod, "Qtd": qtd, "Valor Unit.": v_unit, "Detalhes": f"{t}|{n}|{c}|{ob}"})
        st.rerun()

if st.session_state.itens:
    st.subheader("📋 Itens do Orçamento")
    st.dataframe(pd.DataFrame(st.session_state.itens), use_container_width=True, hide_index=True)
    if st.button("🗑️ Limpar Lista"):
        st.session_state.itens = []
        st.rerun()

    desc = st.number_input("Desconto (R$)", 0.0, key="c_desc", format="%.2f")
    entrega = st.date_input("Data Limite", key="c_dt")
    
    if st.button("👁️ GERAR PRÉVIA", type="primary"):
        st.session_state.previa_dados = {
            "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", 
            "data_geracao": datetime.now().strftime("%d/%m/%Y"),
            "data_entrega": entrega.strftime("%d/%m/%Y"), 
            "cliente_nome": st.session_state.c_nome,
            "cliente_cpf_cnpj": st.session_state.c_cpf, 
            "cliente_wa": st.session_state.c_wa,
            "itens": st.session_state.itens, 
            "desconto_valor": desc, 
            "prazo_dias": "10", 
            "frete_tipo": "Retirada"
        }
        st.rerun()

# --- EXIBIÇÃO DA PRÉVIA COM BOTÕES ---
if st.session_state.previa_dados:
    st.success("✅ Prévia gerada!")
    
    # Botões de ação de volta!
    c_baixar, c_wa = st.columns(2)
    c_baixar.download_button("📥 Baixar HTML", gerar_proposta_html(st.session_state.previa_dados), "proposta.html")
    c_wa.link_button("📱 WhatsApp", extrair_link_whatsapp_completo(st.session_state.previa_dados))
    
    if st.button("🚀 CONFIRMAR E SALVAR NO HISTÓRICO"):
        if salvar_no_sheets(st.session_state.previa_dados):
            st.success("Orçamento salvo!")
            st.session_state.itens = []
            st.session_state.previa_dados = None
            st.rerun()
