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
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados):
    historico = carregar_historico()
    historico.insert(0, dados)
    salvar_historico_completo(historico)

def alternar_status(num_proposta, campo, novo_valor):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = novo_valor
            break
    salvar_historico_completo(historico)

def atualizar_data_entrega(num_proposta, nova_data):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p["data_entrega"] = nova_data
            break
    salvar_historico_completo(historico)

def excluir_proposta_por_id(num_proposta):
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc_v = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - desc_v)
    
    texto_itens = ""
    for idx, item in enumerate(dados["itens"], 1):
        sub_item = item["quantidade"] * item["valor_unitario"]
        texto_itens += f"  *{idx}. {item['produto']}*\n"
        if item.get('especificacoes'): texto_itens += f"      └ Detalhes: {item['especificacoes']}\n"
        texto_itens += f"      └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f} | Subtotal: R$ {sub_item:.2f}\n\n"

    msg = (f"🔥 *PROPOSTA ALPHAFEST*\n📄 *Nº:* {dados['numero_proposta']}\n\n"
           f"👤 *CLIENTE:* {dados['cliente_nome']}\n"
           f"📦 *ITENS:*\n{texto_itens}"
           f"✅ *TOTAL:* R$ {total_final:.2f}\n"
           f"🔗 *Pague aqui:* {LINK_PIX_OFICIAL}")
    
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    return f"https://wa.me/{num_wa}?text={msg_enc}" if num_wa and len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={msg_enc}"

def gerar_proposta_html(dados):
    linhas = "".join([f"<tr><td><strong>{i['produto']}</strong></td><td>{i['quantidade']} un.</td><td>R$ {i['valor_unitario']:.2f}</td></tr>" for i in dados["itens"]])
    return f"<html><body><h2>Proposta {dados['numero_proposta']}</h2><table>{linhas}</table></body></html>"

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3, aba4 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos", "🚀 Marketing"])

# --- ABA 1 ---
with aba1:
    fk = st.session_state.form_key
    nome = st.text_input("Nome do Cliente", key=f"n_{fk}")
    prod = st.text_input("Produto", key=f"p_{fk}")
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor", min_value=0.0, value=0.0, key=f"v_{fk}")
    if st.button("Adicionar Item"):
        st.session_state.itens.append({"produto": prod, "quantidade": q, "valor_unitario": v, "especificacoes": ""})
        st.rerun()
    if st.session_state.itens and st.button("SALVAR PROPOSTA"):
        num = f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}"
        dados = {"numero_proposta": num, "cliente_nome": nome, "cliente_wa": "", "itens": list(st.session_state.itens), "desconto_valor": 0, "data_geracao": date.today().strftime("%d/%m/%Y"), "data_entrega": date.today().strftime("%d/%m/%Y")}
        salvar_no_historico(dados)
        st.session_state.itens = []
        st.session_state.form_key += 1
        st.rerun()

# --- ABA 2 ---
with aba2:
    st.subheader("Histórico")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            st.write(prop)
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"):
                excluir_proposta_por_id(prop['numero_proposta'])
                st.rerun()

# --- ABA 3 ---
with aba3:
    st.subheader("Relatórios")
    h = carregar_historico()
    if h:
        st.write(pd.DataFrame(h))

# --- ABA 4 ---
with aba4:
    st.subheader("🚀 Gerador de Conteúdo")
    api_key = st.text_input("Cole sua Google Gemini API Key", type="password")
    descricao = st.text_area("O que você produziu hoje?")
    if st.button("Gerar Conteúdo"):
        if not api_key: st.error("Insira a chave.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Marketing Alphafest: {descricao}. Crie posts.")
                st.markdown(res.text)
            except Exception as e: st.error(f"Erro: {e}")
