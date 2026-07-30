import streamlit as st
import os
import re
import json
import urllib.parse
import pandas as pd
from datetime import datetime, date
import altair as alt
import google.generativeai as genai

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None
if "target_prop" not in st.session_state: st.session_state.target_prop = None

# --- FUNÇÕES ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados):
    historico = carregar_historico()
    historico.insert(0, dados)
    salvar_historico_completo(historico)

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    msg = f"Proposta Alphafest: {dados['cliente_nome']} - Total: R$ {sum(i['quantidade']*i['valor_unitario'] for i in dados['itens']):.2f}"
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    return f"https://wa.me/{num_wa}?text={msg_enc}"

# --- ABAS ---
aba1, aba2, aba3, aba4 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos", "🚀 Marketing"])

with aba1:
    st.subheader("Novo Orçamento")
    nome = st.text_input("Nome do Cliente", key="nome_c")
    wa = st.text_input("WhatsApp", key="wa_c")
    prod = st.text_input("Produto", key="prod_c")
    q = st.number_input("Qtd", min_value=1, value=1)
    v = st.number_input("Valor Unitário (R$)", min_value=0.0, value=0.0)
    if st.button("Adicionar Item"):
        st.session_state.itens.append({"produto": prod, "quantidade": q, "valor_unitario": v})
        st.rerun()
    if st.session_state.itens:
        if st.button("SALVAR"):
            dados = {"numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", "cliente_nome": nome, "cliente_wa": wa, "itens": list(st.session_state.itens)}
            salvar_no_historico(dados)
            st.session_state.itens = []
            st.success("Proposta salva!")
            st.rerun()

with aba2:
    st.subheader("Histórico")
    for prop in carregar_historico():
        st.write(f"{prop['numero_proposta']} - {prop['cliente_nome']}")

with aba3:
    st.subheader("Relatórios")
    st.info("Relatórios ativos.")

with aba4:
    st.subheader("🚀 Gerador de Conteúdo")
    api_key = st.text_input("Cole sua Google Gemini API Key", type="password")
    descricao = st.text_area("O que você produziu hoje?")
    if st.button("Gerar"):
        if not api_key: st.error("Insira a chave.")
        else:
            try:
                genai.configure(api_key=api_key)
                # Modelo padrão robusto
                model = genai.GenerativeModel('gemini-pro')
                res = model.generate_content(f"Marketing Alphafest: {descricao}. Crie posts engajadores.")
                st.markdown(res.text)
            except Exception as e: st.error(f"Erro: {e}")
