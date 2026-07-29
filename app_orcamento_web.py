import streamlit as st
import base64
import os
import re
import json
import urllib.parse
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    salvar_historico_completo(historico)

def alternar_status(num_proposta, campo, status_atual):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = not status_atual
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
        if item.get('especificacoes'): texto_itens += f"     └ Detalhes: {item['especificacoes']}\n"
        texto_itens += f"     └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f} | Subtotal: R$ {sub_item:.2f}\n\n"

    msg = (f"🔥 *PROPOSTA ALPHAFEST ITATIBA*\n📄 *Nº:* {dados['numero_proposta']}\n🗓️ *Emissão:* {dados.get('data_geracao', '')}\n\n"
           f"👤 *CLIENTE:* {dados['cliente_nome']}\n🪪 *CPF/CNPJ:* {dados.get('cliente_cpf_cnpj', 'Não informado')}\n"
           f"📦 *ITENS DO PEDIDO:*\n\n{texto_itens}✅ *VALOR TOTAL DO PEDIDO:* R$ {total_final:.2f}\n"
           f"📅 *Entrega:* {dados.get('data_entrega', 'A combinar')}\n🚚 *Frete:* {dados.get('frete_tipo', 'Retirada em Itatiba')}\n\n"
           f"👇 *Somente após comprovante daremos seguimento ao seu pedido ! 🥰*")
    
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    return f"https://wa.me/{num_wa}?text={msg_enc}" if num_wa and len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={msg_enc}"

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

with aba1:
    fk = st.session_state.form_key
    st.subheader("1. Dados do Cliente")
    nome = st.text_input("Nome / Razão Social", key=f"cliente_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF / CNPJ", key=f"cpf_{fk}")
    wa = c2.text_input("WhatsApp", key=f"wa_{fk}")
    
    st.divider()
    st.subheader("2. Adicionar Itens")
    prod = st.text_input("Produto", key=f"prod_{fk}")
    
    # RESTAURANDO OS CAMPOS DE DETALHAMENTO
    with st.expander("🎨 Personalização & Especificações", expanded=True):
        col_esp1, col_esp2 = st.columns(2)
        esp_tema = col_esp1.text_input("Tema / Ocasião", key=f"et_{fk}")
        esp_nome = col_esp1.text_input("Nome(s) Personalizado(s)", key=f"en_{fk}")
        esp_cor = col_esp1.text_input("Cor / Material", key=f"ec_{fk}")
        esp_idade = col_esp2.text_input("Idade / Data do Evento", key=f"ei_{fk}")
        esp_geral = col_esp2.text_input("Outros Detalhes", key=f"eg_{fk}")

    col_q, col_v = st.columns(2)
    q = col_q.number_input("Quantidade", 1, key=f"q_{fk}")
    v = col_v.number_input("Valor Unitário", 10.0, key=f"v_{fk}")
    
    if st.button("➕ Adicionar Item à Lista"):
        partes = [f"Tema: {esp_tema}", f"Nome: {esp_nome}", f"Idade: {esp_idade}", f"Cor: {esp_cor}", f"Obs: {esp_geral}"]
        detalhes = " | ".join([p for p in partes if p.split(": ")[1]])
        st.session_state.itens.append({"produto": prod, "especificacoes": detalhes, "quantidade": q, "valor_unitario": v})
        st.rerun()

    if st.session_state.itens:
        st.write("Itens adicionados:", len(st.session_state.itens))
        if st.button("🗑️ Limpar"): st.session_state.itens = []; st.rerun()

    st.divider()
    desc = st.number_input("Desconto (R$)", 0.0, key=f"desc_{fk}")
    
    if st.button("🚀 GERAR PROPOSTA", type="primary"):
        dados = {
            "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
            "data_geracao": datetime.now().strftime("%d/%m/%Y"),
            "data_entrega": date.today().strftime("%Y-%m-%d"),
            "cliente_nome": st.session_state.get(f"cliente_{fk}", "N/A"),
            "cliente_cpf_cnpj": st.session_state.get(f"cpf_{fk}", "N/A"),
            "cliente_wa": st.session_state.get(f"wa_{fk}", "N/A"),
            "itens": list(st.session_state.itens),
            "desconto_valor": desc,
            "prazo_dias": "10",
            "frete_tipo": "Retirada em Itatiba"
        }
        salvar_no_historico(dados)
        st.session_state.ultima_proposta = {"numero": dados["numero_proposta"], "cliente": dados["cliente_nome"], "link_wa": extrair_link_whatsapp_completo(dados)}
        st.session_state.itens = []
        st.session_state.form_key += 1
        st.rerun()

with aba2:
    st.subheader("📋 Central de Propostas")
    hoje = date.today().strftime("%Y-%m-%d")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            st.write(f"**Cliente:** {prop['cliente_nome']}")
            if prop.get("data_entrega") == hoje and not prop.get("entregue"): st.warning("⚠️ ENTREGA HOJE!")
            if st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}"): alternar_status(prop['numero_proposta'], "pago", False)
            if st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{prop['numero_proposta']}"): alternar_status(prop['numero_proposta'], "entregue", False)
            if st.button("🗑️ Excluir", key=f"d_{prop['numero_proposta']}"): excluir_proposta_por_id(prop['numero_proposta']); st.rerun()
