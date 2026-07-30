import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import google.generativeai as genai

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", layout="wide")
ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- FUNÇÕES DE CARREGAMENTO (MANTIDAS IGUAIS) ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

# --- ESTRUTURA DAS ABAS ---
aba1, aba2, aba3, aba4 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos", "🚀 Marketing"])

# --- ABA 1, 2 e 3: (SUA LÓGICA ORIGINAL) ---
with aba1:
    st.write("Aqui entra sua lógica original de orçamentos...")

with aba2:
    st.write("Aqui entra sua lógica original de histórico...")
    st.json(carregar_historico()) # Isso mostrará o arquivo JSON que você já tem

with aba3:
    st.write("Aqui entra sua lógica original de relatórios...")

# --- ABA 4: MARKETING (ISOLADA) ---
with aba4:
    st.subheader("🚀 Gerador de Conteúdo Alphafest")
    api_key = st.text_input("Cole sua Google Gemini API Key", type="password")
    descricao = st.text_area("O que você produziu hoje?")
    
    if st.button("✨ Gerar Roteiros"):
        if not api_key:
            st.error("Insira a chave da API.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"Marketing Alphafest. Descrição: {descricao}")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Erro na IA: {e}")
