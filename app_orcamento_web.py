import streamlit as st
import base64
import os
import re
import json
import urllib.parse
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Orçamento Alphafest",
    page_icon="📄",
    layout="centered"
)

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO / LIMPEZA ---
if "fk_geral" not in st.session_state: st.session_state.fk_geral = 0
if "fk_item" not in st.session_state: st.session_state.fk_item = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
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
    historico = [p for p in carregar_historico() if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico)

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        with open(PATH_LOGO_OFICIAL, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

def exibir_logo_interface():
    if os.path.exists(PATH_LOGO_OFICIAL):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2: st.image(PATH_LOGO_OFICIAL, use_container_width=True)

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc_v = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - desc_v)
    texto_itens = "\n".join([f"  *{idx}. {item['produto']}* (Qtd: {item['quantidade']} un.)" for idx, item in enumerate(dados["itens"], 1)])
    msg = f"🔥 *PROPOSTA ALPHAFEST*\n👤 *CLIENTE:* {dados['cliente_nome']}\n✅ *TOTAL:* R$ {total_final:.2f}"
    return f"https://wa.me/{num_wa}?text={urllib.parse.quote(msg)}" if len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo">' if logo_base64 else ""
    linhas_tabela = "".join([f"<tr><td>{item['produto']}</td><td>{item['quantidade']}</td><td>R$ {item['valor_unitario']:.2f}</td></tr>" for item in dados["itens"]])
    
    return f"""
    <html><body>
    <div class="container">
        <h1>PROPOSTA {dados['numero_proposta']}</h1>
        <p><strong>Cliente:</strong> {dados['cliente_nome']}</p>
        <p><strong>Data Entrega:</strong> {dados['data_entrega']}</p>
        <table><thead><tr><th>Produto</th><th>Qtd</th><th>Unit</th></tr></thead><tbody>{linhas_tabela}</tbody></table>
    </div></body></html>
    """

# --- INTERFACE ---
exibir_logo_interface()
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios"])

with aba1:
    fkg, fki = st.session_state.fk_geral, st.session_state.fk_item
    cliente_nome = st.text_input("Nome do Cliente", key=f"cli_{fkg}")
    cliente_cpf = st.text_input("CPF/CNPJ", key=f"cpf_{fkg}")
    cliente_wa = st.text_input("WhatsApp", key=f"wa_{fkg}")
    
    prod = st.text_input("Produto", key=f"prod_{fki}")
    qtd = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fki}")
    v_unit = st.number_input("Valor Unit.", value=10.0, key=f"v_{fki}")
    
    if st.button("Adicionar Item"):
        st.session_state.itens.append({"produto": prod, "especificacoes": "N/A", "quantidade": qtd, "valor_unitario": v_unit})
        st.session_state.fk_item += 1
        st.rerun()

    prazo = st.text_input("Prazo (dias)", value="10")
    dt_entrega = st.date_input("Data de Entrega", value=date.today())
    
    if st.button("🚀 GERAR ORÇAMENTO"):
        dados = {
            "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
            "data_geracao": datetime.now().strftime("%d/%m/%Y"),
            "data_entrega": dt_entrega.strftime("%d/%m/%Y"),
            "cliente_nome": cliente_nome,
            "cliente_cpf_cnpj": cliente_cpf,
            "cliente_wa": cliente_wa,
            "itens": st.session_state.itens,
            "desconto_valor": 0.0,
            "prazo_dias": prazo,
            "frete_tipo": "Retirada",
            "pago": False,
            "entregue": False
        }
        salvar_no_historico(dados)
        st.session_state.itens = []
        st.session_state.fk_geral += 1
        st.rerun()

with aba2:
    historico = carregar_historico()
    hoje_str = date.today().strftime("%d/%m/%Y")
    
    # Alerta (só mostra se não foi entregue)
    for p in historico:
        if p.get("data_entrega") == hoje_str and not p.get("entregue", False):
            st.error(f"🚨 Alerta de Entrega Hoje: {p['cliente_nome']} ({p['numero_proposta']})")

    for p in historico:
        status_txt = f"Pago: {'✅' if p.get('pago') else '❌'} | Entregue: {'✅' if p.get('entregue') else '❌'}"
        with st.expander(f"{p['numero_proposta']} - {p['cliente_nome']} | {status_txt}"):
            c1, c2 = st.columns(2)
            if c1.checkbox("Marcar como Pago", value=p.get("pago", False), key=f"pago_{p['numero_proposta']}"):
                alternar_status(p['numero_proposta'], "pago", p.get("pago", False)); st.rerun()
            if c2.checkbox("Marcar como Entregue", value=p.get("entregue", False), key=f"ent_{p['numero_proposta']}"):
                alternar_status(p['numero_proposta'], "entregue", p.get("entregue", False)); st.rerun()

with aba3:
    st.write("Relatórios...")
