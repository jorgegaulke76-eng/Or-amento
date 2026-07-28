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
    # Garante que a chave existe nos secrets
    creds_dict = dict(st.secrets["gcp"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def salvar_no_sheets(dados):
    try:
        client = get_sheets_client()
        sheet = client.open("HistoricoAlphafest").sheet1
        row = [
            dados['numero_proposta'], dados['data_geracao'], dados['data_entrega'],
            dados['cliente_nome'], dados['cliente_cpf_cnpj'], dados['cliente_wa'],
            str(dados['itens']), str(dados['desconto_valor']), str(dados['prazo_dias']),
            dados['frete_tipo'], "Não", "Não"
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no Sheets: {e}")
        return False

# --- FUNÇÕES ---
def gerar_proposta_html(dados):
    linhas_tabela = ""
    subtotal = 0.0
    for item in dados["itens"]:
        sub = item["quantidade"] * item["valor_unitario"]
        subtotal += sub
        linhas_tabela += f"<tr><td>{item['produto']}<br><small>{item['especificacoes']}</small></td><td>{item['quantidade']}</td><td>R${item['valor_unitario']:.2f}</td><td>R${sub:.2f}</td></tr>"
    return f"<html><body><h2>Proposta: {dados['numero_proposta']}</h2><table border='1'>{linhas_tabela}</table><p>Total: R${max(0, subtotal - dados.get('desconto_valor', 0)):.2f}</p></body></html>"

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    msg = f"🔥 *PROPOSTA ALPHAFEST*\nCliente: {dados['cliente_nome']}\nEntrega: {dados['data_entrega']}\nTotal: R${max(0, sum(i['quantidade']*i['valor_unitario'] for i in dados['itens']) - dados.get('desconto_valor', 0)):.2f}"
    return f"https://wa.me/{num_wa}?text={urllib.parse.quote(msg)}"

# --- ESTADO INICIAL ---
if "itens" not in st.session_state: st.session_state.itens = []
if "previa" not in st.session_state: st.session_state.previa = None

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

st.subheader("1. Dados do Cliente")
st.text_input("Nome / Razão Social", key="c_nome")
st.text_input("CPF / CNPJ", key="c_cpf")
st.text_input("WhatsApp", key="c_wa")

st.subheader("2. Adicionar Itens")
st.text_input("Produto", key="i_prod")
with st.expander("🎨 Detalhes"):
    c1, c2 = st.columns(2)
    t = c1.text_input("Tema", key="i_tema")
    n = c1.text_input("Nome", key="i_nome")
    c = c1.text_input("Cor", key="i_cor")
    id = c2.text_input("Idade", key="i_idade")
    ob = c2.text_input("Obs", key="i_obs")
q, v = st.columns(2)
qtd = q.number_input("Qtd", 1, key="i_qtd")
v_unit = v.number_input("Valor Unit.", 0.0, key="i_vunit")

if st.button("➕ Adicionar Item"):
    detalhes = f"Tema:{t}|Nome:{n}|Cor:{c}|Idade:{id}|Obs:{ob}"
    st.session_state.itens.append({"produto": st.session_state.i_prod, "quantidade": qtd, "valor_unitario": v_unit, "especificacoes": detalhes})
    st.rerun()

# --- FLUXO DE PRÉVIA E CONFIRMAÇÃO ---
if st.session_state.itens:
    st.write("---")
    st.write("### Itens Atuais (Confira antes de gerar):")
    st.write(st.session_state.itens)
    
    desc = st.number_input("Desconto (R$)", 0.0, key="c_desc")
    prazo = st.text_input("Prazo (dias)", "10", key="c_pz")
    entrega = st.date_input("Data Entrega", key="c_dt")
    frete = st.text_input("Frete", "Retirada", key="c_ft")

    if st.button("👁️ GERAR PRÉVIA DA PROPOSTA"):
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
        st.session_state.previa = {
            "html": gerar_proposta_html(dados_previa),
            "link_wa": extrair_link_whatsapp_completo(dados_previa),
            "dados_completos": dados_previa
        }
        st.rerun()

# --- EXIBIÇÃO DA PRÉVIA ---
if st.session_state.previa:
    st.success("Prévia Gerada! Confira os detalhes abaixo.")
    
    # Exibe os botões de ação
    c_d, c_w = st.columns(2)
    c_d.download_button("📥 Baixar HTML", st.session_state.previa["html"], "proposta.html")
    c_w.link_button("📱 WhatsApp", st.session_state.previa["link_wa"])
    
    st.warning("Se estiver tudo correto, clique no botão abaixo para confirmar e salvar no histórico.")
    
    if st.button("✅ CONFIRMAR E SALVAR NO SISTEMA"):
        sucesso = salvar_no_sheets(st.session_state.previa["dados_completos"])
        if sucesso:
            st.success("Salvo com sucesso!")
            st.session_state.itens = []
            st.session_state.previa = None
            st.rerun()
