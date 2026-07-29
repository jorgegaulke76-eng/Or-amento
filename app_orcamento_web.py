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
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "itens" not in st.session_state:
    st.session_state.itens = []
if "ultima_proposta" not in st.session_state:
    st.session_state.ultima_proposta = None

# --- FUNÇÕES DE BANCO DE DADOS / HISTÓRICO ---
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
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def exibir_logo_interface():
    if os.path.exists(PATH_LOGO_OFICIAL):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            st.image(PATH_LOGO_OFICIAL, use_container_width=True)

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"):
        num_wa = "55" + num_wa
    
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc_v = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - desc_v)
    
    texto_itens = ""
    for idx, item in enumerate(dados["itens"], 1):
        sub_item = item["quantidade"] * item["valor_unitario"]
        texto_itens += f"  *{idx}. {item['produto']}*\n"
        if item.get('especificacoes'):
            texto_itens += f"     └ Detalhes: {item['especificacoes']}\n"
        texto_itens += f"     └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f} | Subtotal: R$ {sub_item:.2f}\n\n"

    msg = (
        f"🔥 *PROPOSTA ALPHAFEST ITATIBA*\n"
        f"📄 *Nº:* {dados['numero_proposta']}\n"
        f"🗓️ *Emissão:* {dados.get('data_geracao', '')}\n\n"
        f"👤 *CLIENTE:* {dados['cliente_nome']}\n"
        f"🪪 *CPF/CNPJ:* {dados.get('cliente_cpf_cnpj', 'Não informado')}\n"
        f"-----------------------------------\n"
        f"📦 *ITENS DO PEDIDO:*\n\n"
        f"{texto_itens}"
        f"-----------------------------------\n"
        f"💵 *Subtotal:* R$ {subtotal_geral:.2f}\n"
        f"🏷️ *Desconto:* - R$ {desc_v:.2f}\n"
        f"✅ *VALOR TOTAL DO PEDIDO:* R$ {total_final:.2f}\n"
        f"-----------------------------------\n"
        f"📅 *Previsão de Entrega:* {dados.get('data_entrega', 'A combinar')}\n"
        f"⏳ *Prazo de Produção:* {dados.get('prazo_dias', '10')} dias úteis\n"
        f"🚚 *Frete/Entrega:* {dados.get('frete_tipo', 'Retirada em Itatiba')}\n"
        f"⏰ *Validade:* 5 dias corridos\n\n"
        f"💳 *PAGAMENTO VIA PIX (100%):*\n"
        f"👉 *Clique no link para pagar:* {LINK_PIX_OFICIAL}\n\n"
        f"• *Titular:* Ana Lúcia Zepelini\n"
        f"• *Banco:* Cora SCD (403)\n"
        f"• *Agência:* 0001 | *Conta:* 2515972-5\n"
        f"• *Empresa:* ANA LUCIA VIEIRA ZEPELINI 29480359880\n\n"
        f"👇 *Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido ! 🥰*"
    )
    
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    if num_wa and len(num_wa) >= 12:
        return f"https://wa.me/{num_wa}?text={msg_enc}"
    else:
        return f"https://api.whatsapp.com/send?text={msg_enc}"

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Alphafest Logo">' if logo_base64 else f'<div style="font-size:24px; font-weight:bold; color:#1e293b;">🔥 {MARCA_FABRICANTE}</div>'
    
    linhas_tabela = ""
    subtotal_geral = 0.0
    for item in dados["itens"]:
        subtotal_item = item["quantidade"] * item["valor_unitario"]
        subtotal_geral += subtotal_item
        linhas_tabela += f"""<tr><td><strong>{item['produto']}</strong><br><small style="color: #64748b;">{item['especificacoes']}</small></td><td style="text-align:center;">{item['quantidade']} un.</td><td style="text-align:right;">R$ {item['valor_unitario']:.2f}</td><td style="text-align:right;">R$ {subtotal_item:.2f}</td></tr>"""
    
    valor_desconto = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - valor_desconto)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @media print {{ @page {{ size: A4 portrait; margin: 8mm; }} }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #1e293b; padding-bottom: 10px; margin-bottom: 20px; }}
            .logo {{ max-height: 80px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #334155; color: white; padding: 10px; text-align: left; font-size: 12px; }}
            td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">{logo_tag} <div style="text-align:right;"><b>{MARCA_FABRICANTE}</b><br>Emissão: {dados['data_geracao']}</div></div>
        <h2>Proposta Nº {dados['numero_proposta']}</h2>
        <div style="padding:10px; background:#f1f5f9; margin-bottom:20px;"><b>Cliente:</b> {dados['cliente_nome']} | <b>CPF/CNPJ:</b> {dados.get('cliente_cpf_cnpj', 'N/A')}</div>
        <table><thead><tr><th>ITEM</th><th>QTD</th><th>UNIT.</th><th>TOTAL</th></tr></thead><tbody>{linhas_tabela}</tbody></table>
        <div style="text-align:right; font-size:16px; font-weight:bold;">TOTAL: R$ {total_final:.2f}</div>
    </body>
    </html>
    """

# --- INTERFACE PRINCIPAL ---
exibir_logo_interface()
st.title("📄 ORÇAMENTOS ALPHAFEST")

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

with aba1:
    if st.session_state.ultima_proposta:
        p_info = st.session_state.ultima_proposta
        st.success(f"✅ Proposta {p_info['numero']} ({p_info['cliente']}) salva!")
        c_down, c_wsp = st.columns(2)
        c_down.download_button("📥 Baixar Proposta", p_info["html"], f"Proposta_{p_info['numero']}.html", mime="text/html", use_container_width=True)
        c_wsp.link_button("📱 WhatsApp", p_info["link_wa"], type="primary", use_container_width=True)
        st.divider()

    fk = st.session_state.form_key
    st.subheader("1. Dados do Cliente")
    nome = st.text_input("Nome / Razão Social", key=f"cliente_{fk}")
    doc = st.text_input("CPF / CNPJ", key=f"cpf_{fk}")
    wa = st.text_input("WhatsApp", key=f"wa_{fk}")

    st.divider()
    st.subheader("2. Itens")
    prod = st.text_input("Produto", key=f"prod_{fk}")
    q = st.number_input("Qtd", 1, key=f"q_{fk}")
    v = st.number_input("Valor", 10.0, key=f"v_{fk}")
    
    if st.button("Adicionar"):
        st.session_state.itens.append({"produto": prod, "especificacoes": "...", "quantidade": q, "valor_unitario": v})
        st.rerun()

    if st.session_state.itens:
        st.write(pd.DataFrame(st.session_state.itens))
        if st.button("🗑️ Limpar"): st.session_state.itens = []; st.rerun()

    st.divider()
    desc = st.number_input("Desconto", 0.0, key=f"desc_{fk}")
    
    if st.button("🚀 GERAR PROPOSTA"):
        # CAPTURA FORÇADA DOS DADOS VIA SESSION_STATE
        dados = {
            "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
            "data_geracao": datetime.now().strftime("%d/%m/%Y"),
            "data_entrega": "A combinar",
            "cliente_nome": st.session_state.get(f"cliente_{fk}", "N/A"),
            "cliente_cpf_cnpj": st.session_state.get(f"cpf_{fk}", "N/A"),
            "cliente_wa": st.session_state.get(f"wa_{fk}", "N/A"),
            "itens": list(st.session_state.itens),
            "desconto_valor": desc,
            "prazo_dias": 10,
            "frete_tipo": "Retirada"
        }
        salvar_no_historico(dados)
        st.session_state.ultima_proposta = {"numero": dados["numero_proposta"], "cliente": dados["cliente_nome"], "html": gerar_proposta_html(dados), "link_wa": extrair_link_whatsapp_completo(dados)}
        st.session_state.itens = []
        st.session_state.form_key += 1
        st.rerun()

with aba2:
    st.subheader("📋 Central de Propostas")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            st.write(f"**Cliente:** {prop['cliente_nome']}")
            st.write(f"**CPF/CNPJ:** {prop.get('cliente_cpf_cnpj', 'N/A')}")
            st.write(f"**Itens:**")
            for it in prop['itens']: st.write(f"- {it['produto']} ({it['quantidade']} un)")
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"): excluir_proposta_por_id(prop['numero_proposta']); st.rerun()

with aba3:
    st.subheader("📊 Relatórios")
    h = carregar_historico()
    if h: st.metric("Total", f"R$ {sum(sum(i['quantidade']*i['valor_unitario'] for i in p['itens']) for p in h):.2f}")
