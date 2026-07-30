import streamlit as st
import os
import re
import json
import urllib.parse
import pandas as pd
from datetime import datetime, date
import altair as alt
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES DE APOIO ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    salvar_historico_completo(historico)

# --- DEFINIÇÃO DAS ABAS ---
aba1, aba2, aba3, aba4 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos", "🚀 Marketing"])

# --- ABA 1: NOVO ORÇAMENTO ---
with aba1:
    st.subheader("1. Dados do Cliente")
    nome = st.text_input("Nome do Cliente", key="nome_cli")
    wa = st.text_input("WhatsApp", key="wa_cli")
    prod = st.text_input("Produto", key="prod_cli")
    q = st.number_input("Qtd", min_value=1, value=1)
    v = st.number_input("Valor Unitário (R$)", min_value=0.0, value=0.0)
    
    if st.button("➕ Adicionar Item"):
        st.session_state.itens.append({"produto": prod, "quantidade": q, "valor_unitario": v})
        st.rerun()
    
    if st.session_state.itens:
        st.write("Itens adicionados:", st.session_state.itens)
        if st.button("🚀 SALVAR PROPOSTA"):
            num = f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}"
            dados = {"numero_proposta": num, "cliente_nome": nome, "itens": list(st.session_state.itens)}
            salvar_no_historico(dados)
            st.session_state.itens = []
            st.success("Salvo com sucesso!")
            st.rerun()

# --- ABA 2: HISTÓRICO ---
with aba2:
    st.subheader("📋 Histórico")
    for prop in carregar_historico():
        st.write(f"**{prop['numero_proposta']}** - Cliente: {prop['cliente_nome']}")

# --- ABA 3: RELATÓRIOS ---
with aba3:
    st.subheader("📊 Relatórios")
    st.info("Painel de relatórios ativo.")

# --- ABA 4: MARKETING ---
with aba4:
    st.subheader("🚀 Gerador de Conteúdo Alphafest")
    api_key = st.text_input("Cole sua Google Gemini API Key", type="password")
    descricao = st.text_area("O que você produziu hoje?")
    
    if st.button("✨ Gerar Roteiros"):
        if not api_key: st.error("Insira a chave da API.")
        else:
            try:
                genai.configure(api_key=api_key)
                # Modelo genérico para máxima compatibilidade no servidor
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"Marketing Alphafest: {descricao}. Crie 3 posts (Reels, TikTok, Shorts) com títulos, roteiros curtos e legendas com hashtags."
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e: st.error(f"Erro: {e}")
