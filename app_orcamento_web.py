import streamlit as st
import base64
import os
import re
import json
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- FUNÇÕES ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo">' if logo_base64 else ""
    data_hoje = dados.get("data_geracao", datetime.now().strftime("%d/%m/%Y"))
    
    linhas_tabela = ""
    subtotal_geral = 0.0
    
    for item in dados["itens"]:
        subtotal_item = item["quantidade"] * item["valor_unitario"]
        subtotal_geral += subtotal_item
        linhas_tabela += f"""<tr><td><strong>{item['produto']}</strong><br><small style="color: #64748b;">{item['especificacoes']}</small></td><td>{item['quantidade']} un.</td><td>R$ {item['valor_unitario']:.2f}</td><td>R$ {subtotal_item:.2f}</td></tr>"""
        
    desconto_pct = dados["desconto"]
    valor_desconto = subtotal_geral * (desconto_pct / 100)
    total_final = subtotal_geral - valor_desconto
    sinal = total_final * (dados["sinal_pct"] / 100)
    restante = total_final - sinal
    
    msg_wa = f"Olá! Gostei da Proposta {dados['numero_proposta']}."
    link_wa = f"https://wa.me/5511999999999?text={re.sub(r' ', '%20', msg_wa)}"

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>body{{font-family: Arial, sans-serif; padding: 20px;}} .container{{max-width: 800px; margin: auto;}} .btn-wa {{display: block; background: #22c55e; color: white; text-align: center; padding: 14px; border-radius: 8px; text-decoration: none;}}</style></head>
    <body><div class="container">
        <h2>Proposta Comercial: {dados['numero_proposta']}</h2>
        <p><strong>Cliente:</strong> {dados['cliente_nome']}</p>
        <table border="1" style="width:100%; border-collapse: collapse;">
            <thead><tr><th>ITEM</th><th>QTD</th><th>VALOR</th></tr></thead>
            <tbody>{linhas_tabela}</tbody>
        </table>
        <p><strong>TOTAL: R$ {total_final:.2f}</strong></p>
        <a href="{link_wa}" class="btn-wa">✅ Aprovar no WhatsApp</a>
    </div></body></html>
    """
    return html_content

# --- INTERFACE ---
st.title("📄 SISTEMA DE ORÇAMENTOS ALPHAFEST")

if "itens" not in st.session_state: st.session_state.itens = []

aba1, aba2 = st.tabs(["➕ Criar Novo Orçamento", "📋 Histórico de Propostas"])

with aba1:
    st.subheader("1. Cliente / Empresa")
    # Usando keys para controlar a limpeza
    cliente_nome = st.text_input("Nome / Razão Social", key="input_nome")
    cliente_doc = st.text_input("CPF / CNPJ / Contato", key="input_doc")

    st.subheader("2. Adicionar Itens")
    with st.form("form_item", clear_on_submit=True):
        col_p, col_e = st.columns([2, 2])
        prod = st.text_input("Produto")
        espec = st.text_input("Especificações")
        col_q, col_v = st.columns(2)
        qtd = st.number_input("Quantidade", min_value=1, value=1)
        v_unit = st.number_input("Valor Unitário (R$)", min_value=0.01, value=10.00, step=0.50)
        btn_add = st.form_submit_button("➕ Adicionar Item")
        if btn_add:
            if prod:
                st.session_state.itens.append({"produto": prod, "especificacoes": espec, "quantidade": int(qtd), "valor_unitario": float(v_unit)})
            else: st.error("Produto vazio!")

    if st.session_state.itens:
        st.write("### Itens atuais:")
        for item in st.session_state.itens:
            st.write(f"- {item['produto']} | {item['quantidade']}un")
        if st.button("🗑️ Limpar itens"):
            st.session_state.itens = []
            st.rerun()

    st.subheader("3. Condições")
    col_d, col_s = st.columns(2)
    desconto = st.number_input("Desconto (%)", min_value=0.0, value=0.0, key="input_desc")
    sinal = st.number_input("Sinal (%)", min_value=0.0, value=50.0, key="input_sinal")
    prazo = st.text_input("Prazo (Dias)", value="10", key="input_prazo")
    frete = st.text_input("Frete", value="Retirada em Itatiba", key="input_frete")

    if st.button("🚀 GERAR, SALVAR E ZERAR"):
        if not st.session_state.itens: st.error("Adicione itens!")
        else:
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "cliente_nome": st.session_state.input_nome,
                "cliente_doc": st.session_state.input_doc,
                "itens": st.session_state.itens,
                "desconto": desconto,
                "sinal_pct": sinal,
                "prazo_dias": prazo,
                "frete_tipo": frete
            }
            salvar_no_historico(dados)
            
            # --- ZERAR TUDO ---
            st.session_state.itens = []
            st.session_state.input_nome = ""
            st.session_state.input_doc = ""
            st.session_state.input_desc = 0.0
            st.session_state.input_sinal = 50.0
            st.session_state.input_prazo = "10"
            st.session_state.input_frete = "Retirada em Itatiba"
            
            st.success("Proposta gerada! Campos limpos para a próxima.")
            st.rerun()

with aba2:
    st.subheader("📋 Histórico")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            st.write(f"Data: {prop['data_geracao']}")
