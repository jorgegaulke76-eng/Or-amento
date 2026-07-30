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

# --- DEFINIÇÃO DAS ABAS ---
aba1, aba2, aba3, aba4 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos", "🚀 Marketing"])

# --- COLE AQUI TODAS AS SUAS FUNÇÕES ANTIGAS (carregar_historico, salvar_no_historico, etc.) ---
# [COLE SEU CÓDIGO ORIGINAL AQUI]

# --- ABA 4 ---
with aba4:
    st.subheader("🚀 Gerador de Conteúdo Alphafest")
    api_key = st.text_input("Cole sua Google Gemini API Key", type="password")
    descricao = st.text_area("O que você produziu hoje?", placeholder="Ex: Fiz um topo de bolo em papel...")
    if st.button("✨ Gerar Roteiros e Posts"):
        if not api_key: st.error("Por favor, insira sua chave da API.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"Atue como marketing Alphafest. Descrição: {descricao}. Crie 3 posts (Reels/TikTok/Shorts).")
                st.markdown(response.text)
            except Exception as e: st.error(f"Erro: {e}")
