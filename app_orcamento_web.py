import streamlit as st
import base64
import os
import re
import json
import urllib.parse
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
PATH_PIX_QRCODE = "pix.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_DIRETO = "https://linkspix.app/alphafestitatiba"

# --- ESTADO INICIAL ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES ---
def formatar_doc_para_wa(doc):
    apenas_num = re.sub(r'\D', '', str(doc or ''))
    if len(apenas_num) == 11: return f"{apenas_num[:3]}. {apenas_num[3:6]}. {apenas_num[6:9]} - {apenas_num[9:]}"
    if len(apenas_num) == 14: return f"{apenas_num[:2]}.{apenas_num[2:5]}.{apenas_num[5:8]}/{apenas_num[8:12]}-{apenas_num[12:]}"
    return doc or "Não informado"

def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f: json.dump(historico, f, ensure_ascii=False, indent=4)

def atualizar_pedido(num_proposta, campo, valor):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = valor
            break
    salvar_historico_completo(historico)

def carregar_imagem_base64(path_imagem):
    if os.path.exists(path_imagem):
        try:
            with open(path_imagem, "rb") as image_file: return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
if os.path.exists(PATH_LOGO_OFICIAL):
    st.image(PATH_LOGO_OFICIAL, width=200)

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios"])

with aba1:
    st.subheader("Novo Orçamento")
    cliente_nome = st.text_input("Nome do Cliente")
    cpf_cnpj = st.text_input("CPF/CNPJ")
    wa = st.text_input("WhatsApp")
    
    # Simulação de adição de itens para não deixar a aba vazia
    if st.button("Adicionar Item"):
        st.session_state.itens.append({"produto": "Item Exemplo", "quantidade": 1, "valor_unitario": 10.0})
        st.rerun()
    
    st.write("Itens:", st.session_state.itens)
    
    if st.button("Gerar Proposta"):
        # Lógica de salvar...
        st.success("Proposta gerada!")

with aba2:
    st.subheader("Histórico")
    historico = carregar_historico()
    if not historico:
        st.info("Nenhuma proposta encontrada.")
    else:
        for prop in historico:
            status = "✅ [ENTREGUE]" if prop.get('entregue') else "⏳ [PENDENTE]"
            with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']} {status}"):
                if not prop.get('entregue'):
                    if st.button("📦 Marcar como ENTREGUE", key=f"ent_{prop['numero_proposta']}"):
                        atualizar_pedido(prop['numero_proposta'], "entregue", True)
                        st.rerun()

with aba3:
    st.subheader("Relatórios")
    st.write("Aqui aparecerão seus relatórios de venda.")
