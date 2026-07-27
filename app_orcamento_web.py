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

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    total_final = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"]) - dados.get("desconto_valor", 0.0)
    msg = f"🔥 *PROPOSTA ALPHAFEST*\n👤 *CLIENTE:* {dados['cliente_nome']}\n✅ *TOTAL:* R$ {total_final:.2f}"
    return f"https://wa.me/{num_wa}?text={urllib.parse.quote(msg)}" if len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" style="max-height:85px;">' if logo_base64 else ""
    linhas_tabela = "".join([f"<tr><td><strong>{item['produto']}</strong><br><small>{item['especificacoes']}</small></td><td>{item['quantidade']} un.</td><td>R$ {item['valor_unitario']:.2f}</td></tr>" for item in dados["itens"]])
    total = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"]) - dados.get("desconto_valor", 0.0)
    
    return f"""
    <html><body>
    <div class="container">
        {logo_tag}
        <h1>PROPOSTA {dados['numero_proposta']}</h1>
        <p><strong>Cliente:</strong> {dados['cliente_nome']}</p>
        <p><strong>Data Entrega:</strong> {dados['data_entrega']}</p>
        <table border="1" width="100%"><thead><tr><th>Item</th><th>Qtd</th><th>Unit</th></tr></thead>
        <tbody>{linhas_tabela}</tbody></table>
        <h3>Total: R$ {total:.2f}</h3>
    </div></body></html>
    """

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "🧮 Precificador 3D"])

with aba1:
    fk = st.session_state.form_key
    cliente_nome = st.text_input("Nome do Cliente", key=f"cli_{fk}")
    cliente_cpf = st.text_input("CPF/CNPJ", key=f"cpf_{fk}")
    cliente_wa = st.text_input("WhatsApp", key=f"wa_{fk}")
    
    prod = st.text_input("Produto", key=f"prod_{fk}")
    col_q, col_v = st.columns(2)
    qtd = col_q.number_input("Qtd", min_value=1, value=1)
    v_unit = col_v.number_input("Valor Unit.", value=10.0)
    
    if st.button("Adicionar Item"):
        st.session_state.itens.append({"produto": prod, "especificacoes": "N/A", "quantidade": qtd, "valor_unitario": v_unit})
        st.rerun()

    if st.session_state.itens:
        for it in st.session_state.itens: st.write(f"- {it['produto']} | {it['quantidade']} un")

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
        st.session_state.form_key += 1
        st.rerun()

with aba2:
    historico = carregar_historico()
    hoje_str = date.today().strftime("%d/%m/%Y")
    
    pendentes = [p for p in historico if str(p.get("data_entrega", "")).strip() == hoje_str and not p.get("entregue", False)]
    for p in pendentes: st.error(f"🚨 Alerta de Entrega Hoje: {p['cliente_nome']} ({p['numero_proposta']})")

    for p in historico:
        is_pago, is_entregue = p.get("pago", False), p.get("entregue", False)
        with st.expander(f"{p['numero_proposta']} - {p['cliente_nome']} | Pago: {'✅' if is_pago else '❌'} | Entregue: {'✅' if is_entregue else '❌'}"):
            st.write("**Itens:**")
            for it in p.get("itens", []): st.write(f"- {it['produto']} ({it['quantidade']} un)")
            c1, c2 = st.columns(2)
            if c1.checkbox("Pago", value=is_pago, key=f"pago_{p['numero_proposta']}"): alternar_status(p['numero_proposta'], "pago", is_pago); st.rerun()
            if c2.checkbox("Entregue", value=is_entregue, key=f"ent_{p['numero_proposta']}"): alternar_status(p['numero_proposta'], "entregue", is_entregue); st.rerun()
            if st.button("🗑️ Excluir", key=f"del_{p['numero_proposta']}"): excluir_proposta_por_id(p['numero_proposta']); st.rerun()

with aba3:
    st.subheader("🧮 Precificador 3D")
    peso = st.number_input("Peso (g)", value=0.0)
    preco_rolo = st.number_input("Preço Rolo (R$)", value=100.0)
    horas = st.number_input("Horas", value=0.0)
    valor_hora = st.number_input("Valor sua hora (R$)", value=30.0)
    margem = st.number_input("Margem (%)", value=100.0)
    custo = ((peso/1000)*preco_rolo) + (horas*valor_hora) + 5.0
    st.success(f"Preço de Venda: R$ {custo * (1 + (margem/100)):.2f}")
