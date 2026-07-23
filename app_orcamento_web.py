import streamlit as st
import json
import os
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alphafest Control Center", page_icon="🔥", layout="wide")

ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- FUNÇÕES ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

# --- MENU ---
st.sidebar.title("🔥 ALPHAFEST")
st.sidebar.markdown("---")

modulo_selecionado = st.sidebar.radio(
    "📌 SELECIONE O MÓDULO:",
    ["📄 Orçamentos & Pedidos", "📊 Dashboard & Métricas"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Alphafest Itatiba**\nGestão Comercial")

# ==========================================
# MÓDULO 1: ORÇAMENTOS & PEDIDOS
# ==========================================
if modulo_selecionado == "📄 Orçamentos & Pedidos":
    st.title("📄 GESTÃO DE ORÇAMENTOS E PROPOSTAS")
    st.write("Módulo de orçamentos ativo e pronto para uso.")
    # (Seu código de orçamentos continua aqui...)

# ==========================================
# MÓDULO 2: DASHBOARD & MÉTRICAS
# ==========================================
elif modulo_selecionado == "📊 Dashboard & Métricas":
    st.title("📊 PAINEL DE GESTÃO & MÉTRICAS")
    # (Seu código de dashboard continua aqui...)
