import streamlit as st
import base64
import os
import re
import json
import urllib.parse
import pandas as pd
from datetime import datetime, date
import altair as alt

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="wide")

PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- FUNÇÕES DE APOIO ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: 
                return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    if not historico:
        st.error("⚠️ ERRO: O sistema tentou salvar dados vazios. Ação bloqueada para proteger seu histórico!")
        return
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)
    st.toast("Dados salvos com sucesso!", icon="✅")

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    salvar_historico_completo(historico)

def alternar_status(num_proposta, campo, novo_valor):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = novo_valor
            break
    salvar_historico_completo(historico)

def excluir_proposta_por_id(num_proposta):
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

def criar_grafico_com_labels(df, x_col, y_col, titulo):
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f'{x_col}:O', title=x_col),
        y=alt.Y(f'{y_col}:Q', title=y_col),
        tooltip=[x_col, y_col]
    ).properties(title=titulo)
    text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(text=y_col)
    return chart + text

# --- SIDEBAR: BACKUP ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    st.info("⚠️ Proteja seu trabalho! Baixe o backup após cada alteração.")
    historico_atual = carregar_historico()
    if historico_atual:
        json_backup = json.dumps(historico_atual, ensure_ascii=False, indent=4)
        st.download_button("💾 BAIXAR BACKUP AGORA", data=json_backup, file_name="backup_historico.json", mime="application/json", type="primary", use_container_width=True)

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

with aba1:
    nome = st.text_input("Nome / Razão Social")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF / CNPJ")
    wa = c2.text_input("WhatsApp")
    
    st.subheader("2. Itens")
    prod = st.text_input("Produto")
    c1, c2 = st.columns(2)
    et = c1.text_input("Tema")
    ei = c2.text_input("Idade/Data")
    q = st.number_input("Qtd", min_value=1, value=1)
    v = st.number_input("Valor Unitário (R$)", value=0.0, step=0.5)
    
    if st.button("➕ Adicionar Item à Lista temporária"):
        if "temp_itens" not in st.session_state: st.session_state.temp_itens = []
        st.session_state.temp_itens.append({"produto": prod, "especificacoes": f"{et} - {ei}", "quantidade": q, "valor_unitario": v})
        st.rerun()

    if "temp_itens" in st.session_state and st.session_state.temp_itens:
        st.dataframe(pd.DataFrame(st.session_state.temp_itens))
        if st.button("🚀 SALVAR PROPOSTA FINAL"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "data_entrega": date.today().strftime("%d/%m/%Y"),
                "cliente_nome": nome,
                "itens": list(st.session_state.temp_itens),
                "pago": False, "entregue": False
            }
            salvar_no_historico(dados)
            st.session_state.temp_itens = []
            st.rerun()

with aba2:
    st.subheader("📋 Central de Propostas")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "entregue", not prop.get("entregue", False)))
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"):
                excluir_proposta_por_id(prop['numero_proposta'])
                st.rerun()

with aba3:
    st.subheader("📊 Relatórios")
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        # Explode itens para contar produtos
        df_itens = pd.DataFrame([item for sublist in [p['itens'] for p in h] for item in sublist])
        st.altair_chart(criar_grafico_com_labels(df_itens.groupby('produto')['quantidade'].sum().reset_index(), 'produto', 'quantidade', 'Produtos mais vendidos'), use_container_width=True)
        # Gráfico de Pedidos
        st.altair_chart(criar_grafico_com_labels(df.groupby('cliente_nome')['numero_proposta'].count().reset_index(), 'cliente_nome', 'numero_proposta', 'Total de Pedidos por Cliente'), use_container_width=True)
