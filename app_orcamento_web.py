import streamlit as st
import base64
import os
import re
import json
import urllib.parse
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")
MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
PATH_PIX_QRCODE = "pix.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_DIRETO = "https://linkspix.app/alphafestitatiba"

# --- ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES ---
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

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios"])

with aba1:
    # ... [Aqui vai o seu formulário original de Novo Orçamento] ...
    # IMPORTANTE: Ao salvar o dado (no botão Gerar), certifique-se de salvar:
    # "entregue": False
    pass

with aba2:
    st.subheader("Histórico de Pedidos")
    historico = carregar_historico()
    hoje_str = date.today().strftime("%d/%m/%Y")
    
    # Alerta apenas para não entregues
    pendentes_hoje = [p for p in historico if p.get("data_entrega") == hoje_str and not p.get("entregue", False)]
    if pendentes_hoje:
        st.error(f"🚨 {len(pendentes_hoje)} entrega(s) pendente(s) para hoje!")
    
    for prop in historico:
        status = "✅ [ENTREGUE]" if prop.get('entregue') else "⏳ [PENDENTE]"
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']} {status}"):
            st.write(f"Data de entrega: {prop.get('data_entrega')}")
            if not prop.get('entregue'):
                if st.button("📦 Marcar como ENTREGUE", key=f"ent_{prop['numero_proposta']}"):
                    atualizar_pedido(prop['numero_proposta'], "entregue", True)
                    st.rerun()
            # ... [Aqui vai o restante dos botões de WhatsApp, Baixar, Excluir que já tínhamos] ...
