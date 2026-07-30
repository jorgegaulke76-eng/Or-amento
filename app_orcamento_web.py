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
st.set_page_config(page_title="Orçamento Alphafest", layout="centered")
ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []

# --- FUNÇÕES ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

# --- ABAS ---
aba1, aba2, aba3, aba4 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios", "🚀 Marketing"])

with aba1:
    st.title("Novo Orçamento")
    nome = st.text_input("Nome do Cliente")
    if st.button("Salvar"): st.success("Salvando...")

with aba2:
    st.title("Histórico")
    st.write(carregar_historico())

with aba3:
    st.title("Relatórios")

with aba4:
    st.title("🚀 Marketing")
    api_key = st.text_input("Cole sua API Key", type="password")
    descricao = st.text_area("O que você produziu?")
    if st.button("Gerar Conteúdo"):
        if not api_key:
            st.error("Chave obrigatória")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(f"Marketing Alphafest: {descricao}")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Erro: {e}")
