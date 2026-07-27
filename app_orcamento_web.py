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
if "fk_geral" not in st.session_state: st.session_state.fk_geral = 0
if "fk_item" not in st.session_state: st.session_state.fk_item = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES DE DADOS ---
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

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo">' if logo_base64 else ""
    
    linhas_tabela = ""
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    for item in dados["itens"]:
        sub = item["quantidade"] * item["valor_unitario"]
        linhas_tabela += f"<tr><td><strong>{item['produto']}</strong><br><small>{item['especificacoes']}</small></td><td style='text-align:center;'>{item['quantidade']} un.</td><td style='text-align:right;'>R$ {item['valor_unitario']:.2f}</td><td style='text-align:right;'>R$ {sub:.2f}</td></tr>"
    
    total_final = max(0.0, subtotal_geral - dados.get("desconto_valor", 0.0))
    
    return f"""
    <html><body>
    <div class="container">
        <h1>ORÇAMENTO ALPHAFEST</h1>
        <p><strong>Cliente:</strong> {dados['cliente_nome']}</p>
        <p><strong>Entrega:</strong> {dados['data_entrega']}</p>
        <table border="1" width="100%"><thead><tr><th>Item</th><th>Qtd</th><th>Unit</th><th>Total</th></tr></thead>
        <tbody>{linhas_tabela}</tbody></table>
        <h3>Total: R$ {total_final:.2f}</h3>
    </div></body></html>
    """

# --- INTERFACE ---
aba1, aba2, aba3 = st.tabs(["➕ Orçamento", "📋 Histórico", "🧮 Precificador 3D"])

with aba1:
    st.title("📄 Novo Orçamento")
    cliente_nome = st.text_input("Nome do Cliente", key=f"cli_{st.session_state.fk_geral}")
    cliente_cpf = st.text_input("CPF/CNPJ", key=f"cpf_{st.session_state.fk_geral}")
    cliente_wa = st.text_input("WhatsApp", key=f"wa_{st.session_state.fk_geral}")
    
    prod = st.text_input("Produto", key=f"prod_{st.session_state.fk_item}")
    qtd = st.number_input("Qtd", min_value=1, value=1, key=f"q_{st.session_state.fk_item}")
    v_unit = st.number_input("Valor Unit.", value=10.0, key=f"v_{st.session_state.fk_item}")
    
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
    
    # Alerta de entrega
    pendentes = [p for p in historico if p.get("data_entrega") == hoje_str and not p.get("entregue", False)]
    for p in pendentes:
        st.error(f"🚨 Alerta de Entrega Hoje: {p['cliente_nome']} ({p['numero_proposta']})")

    for p in historico:
        with st.expander(f"{p['numero_proposta']} - {p['cliente_nome']} (Pago: {p.get('pago')}, Entregue: {p.get('entregue')})"):
            c1, c2 = st.columns(2)
            if c1.checkbox("Pago", value=p.get("pago", False), key=f"pago_{p['numero_proposta']}"):
                alternar_status(p['numero_proposta'], "pago", p.get("pago", False)); st.rerun()
            if c2.checkbox("Entregue", value=p.get("entregue", False), key=f"ent_{p['numero_proposta']}"):
                alternar_status(p['numero_proposta'], "entregue", p.get("entregue", False)); st.rerun()

with aba3:
    st.subheader("🧮 Precificador 3D")
    peso = st.number_input("Peso (g)", value=0.0)
    preco_rolo = st.number_input("Preço Rolo (R$)", value=100.0)
    horas = st.number_input("Horas", value=0.0)
    valor_hora = st.number_input("Valor sua hora (R$)", value=30.0)
    margem = st.number_input("Margem (%)", value=100.0)
    
    custo = ((peso/1000)*preco_rolo) + (horas*valor_hora) + 5.0 # 5.0 depreciação fixa
    st.success(f"Preço de Venda: R$ {custo * (1 + (margem/100)):.2f}")
