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

# --- DEFINIÇÃO DAS ABAS (TEM QUE VIR ANTES DE QUALQUER 'with abaX:') ---
# Nota: Remova qualquer código que chame 'abaX' antes desta linha abaixo
aba1, aba2, aba3, aba4 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos", "🚀 Marketing"])

# --- RESTO DO CÓDIGO (COLE O RESTO DO SEU SISTEMA AQUI) ---
# ... (aqui você mantém todas as suas funções carregar_historico, salvar, etc)

# --- ABA 4: MARKETING (O CÓDIGO QUE ESTAVA DANDO ERRO) ---
with aba4:
    st.subheader("🚀 Gerador de Conteúdo Alphafest")
    api_key = st.text_input("Cole sua Google Gemini API Key", type="password")
    descricao = st.text_area("O que você produziu hoje?", placeholder="Ex: Fiz um topo de bolo em papel...")
    
    if st.button("✨ Gerar Roteiros e Posts"):
        if not api_key: st.error("Por favor, insira sua chave da API do Gemini.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Atue como um especialista em marketing da Alphafest Itatiba. Com base na descrição: '{descricao}', crie 3 variações de posts para Reels, TikTok e Shorts."
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e: st.error(f"Erro: {e}")
