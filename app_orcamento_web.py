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
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None
if "target_prop" not in st.session_state: st.session_state.target_prop = None

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
    st.header("⚙️ Painel de Segurança")
    st.info("⚠️ Proteja seu trabalho! Baixe o backup após cada alteração.")
    historico_atual = carregar_historico()
    if historico_atual:
        json_backup = json.dumps(historico_atual, ensure_ascii=False, indent=4)
        st.download_button("💾 BAIXAR BACKUP AGORA", data=json_backup, file_name="backup_historico.json", mime="application/json", type="primary", use_container_width=True)

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

with aba1:
    fk = st.session_state.form_key
    st.subheader("1. Dados do Cliente")
    nome = st.text_input("Nome / Razão Social", key=f"c_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF / CNPJ", key=f"d_{fk}")
    wa = c2.text_input("WhatsApp", key=f"w_{fk}")
    
    st.divider()
    st.subheader("2. Adicionar Itens")
    prod = st.text_input("Produto", key=f"p_{fk}")
    with st.expander("🎨 Personalização & Especificações (Opcionais)", expanded=True):
        c1, c2 = st.columns(2)
        et = c1.text_input("Tema / Ocasião", key=f"et_{fk}")
        en = c1.text_input("Nome(s) Personalizado(s)", key=f"en_{fk}")
        ec = c1.text_input("Cor / Material", key=f"ec_{fk}")
        ei = c2.text_input("Idade / Data do Evento", key=f"ei_{fk}")
        eg = c2.text_input("Outros Detalhes", key=f"eg_{fk}")
    
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário (R$)", min_value=0.0, value=0.0, step=0.5, key=f"v_{fk}")
    
    if st.button("➕ Adicionar Item à Lista"):
        det = f"Tema: {et} | Nome: {en} | Idade: {ei} | Cor: {ec} | Obs: {eg}"
        st.session_state.itens.append({"produto": prod, "especificacoes": det, "quantidade": q, "valor_unitario": v})
        st.rerun()

    if st.session_state.itens:
        st.write("📋 **Prévia dos itens:**")
        st.dataframe(pd.DataFrame(st.session_state.itens), use_container_width=True)
        if st.button("🗑️ Limpar Lista"): 
            st.session_state.itens = []
            st.rerun()

    st.divider()
    desc = st.number_input("Desconto (R$)", 0.0, key=f"desc_{fk}")
    prazo = st.text_input("Prazo (Dias)", value="10", key=f"prazo_{fk}")
    dt_entrega = st.date_input("📅 Data Entrega", value=date.today(), format="DD/MM/YYYY", key=f"dt_{fk}")
    frete = st.text_input("Frete", value="Retirada em Itatiba", key=f"frete_{fk}")
    
    if st.button("🚀 SALVAR PROPOSTA"):
        num = f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}"
        dados = {
            "numero_proposta": num, "data_geracao": datetime.now().strftime("%d/%m/%Y"), 
            "data_entrega": dt_entrega.strftime("%d/%m/%Y"), "cliente_nome": nome, 
            "cliente_cpf_cnpj": doc, "cliente_wa": wa, "itens": list(st.session_state.itens),
            "desconto_valor": desc, "prazo_dias": prazo, "frete_tipo": frete, 
            "pago": False, "entregue": False
        }
        salvar_no_historico(dados)
        st.session_state.itens = []
        st.session_state.form_key += 1
        st.success("Proposta Salva!")
        st.rerun()

with aba2:
    st.subheader("📋 Central de Propostas")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']} {'✅' if prop.get('entregue') else ''}"):
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "entregue", not prop.get("entregue", False)))
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"):
                excluir_proposta_por_id(prop['numero_proposta'])
                st.rerun()

with aba3:
    st.subheader("📊 Relatórios")
    h = carregar_historico()
    if h:
        df_itens = pd.DataFrame([item for sublist in [p['itens'] for p in h] for item in sublist])
        st.altair_chart(criar_grafico_com_labels(df_itens.groupby('produto')['quantidade'].sum().reset_index(), 'produto', 'quantidade', 'Produtos mais vendidos'), use_container_width=True)
        st.altair_chart(criar_grafico_com_labels(pd.DataFrame(h).groupby('cliente_nome')['numero_proposta'].count().reset_index(), 'cliente_nome', 'numero_proposta', 'Pedidos por Cliente'), use_container_width=True)
