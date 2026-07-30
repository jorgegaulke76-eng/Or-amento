import streamlit as st
import os
import pandas as pd
from datetime import datetime, date
import altair as alt
import google.generativeai as genai

# [MANTENHA AS FUNÇÕES carregar_historico, salvar_historico_completo, etc., IGUAIS AO QUE VOCÊ JÁ TEM]
# (Pode manter as funções de apoio que você já tinha, o código abaixo foca na ABA 4)

# --- ABA 4: MARKETING ---
with aba4:
    st.subheader("🚀 Gerador de Conteúdo Alphafest")
    api_key = st.text_input("Cole sua Google Gemini API Key", type="password")
    descricao = st.text_area("O que você produziu hoje?", placeholder="Ex: Fiz um topo de bolo em papel...")
    
    if st.button("✨ Gerar Roteiros e Posts"):
        if not api_key:
            st.error("Por favor, insira sua chave da API do Gemini.")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # Vamos tentar listar os modelos disponíveis primeiro se der erro
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Atue como um especialista em marketing da Alphafest Itatiba. Com base na descrição: '{descricao}', crie 3 variações de posts para Reels, TikTok e Shorts."
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error("Erro ao conectar. Diagnóstico:")
                    st.write(e)
                    st.write("Modelos disponíveis:")
                    for m in genai.list_models():
                        st.write(m.name)
            except Exception as e:
                st.error(f"Erro geral: {e}")
