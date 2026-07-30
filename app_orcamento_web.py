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

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
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
    # TRAVA DE SEGURANÇA: Não permite salvar lista vazia que apagaria dados
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

def atualizar_data_proposta(num_proposta, nova_data):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p["data_geracao"] = nova_data
            break
    salvar_historico_completo(historico)

def excluir_proposta_por_id(num_proposta):
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

# --- SIDEBAR: BACKUP OBRIGATÓRIO ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    st.info("⚠️ Proteja seu trabalho! Baixe o backup após cada alteração.")
    historico_atual = carregar_historico()
    if historico_atual:
        json_backup = json.dumps(historico_atual, ensure_ascii=False, indent=4)
        st.download_button(
            label="💾 BAIXAR BACKUP AGORA",
            data=json_backup,
            file_name=f"backup_historico_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            type="primary",
            use_container_width=True
        )
    else:
        st.warning("Histórico vazio.")

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

# --- ALERTA DE ENTREGA ---
hoje = date.today()
for p in carregar_historico():
    try:
        data_entrega = datetime.strptime(p.get("data_entrega", ""), "%d/%m/%Y").date()
    except: continue
    
    esta_pendente = not p.get("pago", False) or not p.get("entregue", False)
    if esta_pendente:
        if data_entrega == hoje:
            st.warning(f"⚠️ ENTREGA HOJE: {p['numero_proposta']} - {p['cliente_nome']}")
        elif data_entrega < hoje:
            st.error(f"🚨 ATRASADO: {p['numero_proposta']} | {p['cliente_nome']} | Vencido em {p.get('data_entrega')}")

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

with aba1:
    # (Mantido o código de formulário...)
    if st.session_state.ultima_proposta:
        p = st.session_state.ultima_proposta
        st.success("✅ Proposta gerada!")
        st.divider()

    fk = st.session_state.form_key
    nome = st.text_input("Nome / Razão Social", key=f"c_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF/CNPJ", key=f"d_{fk}")
    wa = c2.text_input("WhatsApp", key=f"w_{fk}")
    
    # ... (Itens e Lógica de Salvar permanecem iguais ao que você tinha)
    prod = st.text_input("Produto", key=f"p_{fk}")
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário", value=0.0, step=0.5, key=f"v_{fk}")
    
    if st.button("➕ Adicionar Item"):
        st.session_state.itens.append({"produto": prod, "quantidade": q, "valor_unitario": v})
        st.rerun()

    if st.button("🚀 SALVAR PROPOSTA FINAL"):
        num = f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}"
        dados = {
            "numero_proposta": num, 
            "data_geracao": datetime.now().strftime("%d/%m/%Y"), 
            "data_entrega": date.today().strftime("%d/%m/%Y"),
            "cliente_nome": nome, "pago": False, "entregue": False,
            "itens": list(st.session_state.itens)
        }
        salvar_no_historico(dados)
        st.session_state.itens = []
        st.session_state.form_key += 1
        st.rerun()

with aba2:
    st.subheader("📋 Pedidos")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "entregue", not prop.get("entregue", False)))

with aba3:
    st.subheader("📊 Relatórios")
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        st.write("Visão Geral de Pedidos", df)
