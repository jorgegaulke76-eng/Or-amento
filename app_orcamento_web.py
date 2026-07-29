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

# --- GERENCIAMENTO DE ESTADO / LIMPEZA ---
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

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        with open(PATH_LOGO_OFICIAL, "rb") as image_file: return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    
    subtotal = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    total_final = max(0.0, subtotal - dados.get("desconto_valor", 0.0))
    
    msg = (f"🔥 *PROPOSTA ALPHAFEST ITATIBA*\n📄 *Nº:* {dados['numero_proposta']}\n🗓️ *Emissão:* {dados.get('data_geracao', '')}\n\n"
           f"👤 *CLIENTE:* {dados['cliente_nome']}\n✅ *VALOR TOTAL:* R$ {total_final:.2f}\n"
           f"💳 *PAGAMENTO VIA PIX:* {LINK_PIX_OFICIAL}\n\n"
           f"👇 *Somente após comprovante daremos seguimento ao pedido ! 🥰*")
    
    return f"https://wa.me/{num_wa}?text={urllib.parse.quote(msg.encode('utf-8'))}"

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    linhas_tabela = "".join([f"<tr><td>{i['produto']}</td><td style='text-align:center;'>{i['quantidade']} un.</td><td style='text-align:right;'>R$ {i['valor_unitario']:.2f}</td></tr>" for i in dados["itens"]])
    
    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @media print {{ @page {{ size: A4 portrait; margin: 8mm; }} }}
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .logo {{ max-height: 80px; }}
        </style>
    </head>
    <body>
        <div style="display:flex; justify-content:space-between;">
            <img src="data:image/png;base64,{logo_base64}" class="logo">
            <div style="text-align:right; font-size:10px;"><b>{MARCA_FABRICANTE}</b><br>Emissão: {dados['data_geracao']}</div>
        </div>
        <h3>Proposta {dados['numero_proposta']}</h3>
        <table style="width:100%; border-collapse:collapse;">
            <thead><tr style="background:#eee;"><th>ITEM</th><th>QTD</th><th>UNIT.</th></tr></thead>
            <tbody>{linhas_tabela}</tbody>
        </table>
    </body>
    </html>
    """

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios"])

with aba1:
    cliente_nome = st.text_input("Nome")
    cliente_wa = st.text_input("WhatsApp")
    if st.button("Adicionar Item"):
        st.session_state.itens.append({"produto": "Produto Exemplo", "quantidade": 1, "valor_unitario": 10.0, "especificacoes": "..."})
    
    if st.button("🚀 GERAR PROPOSTA"):
        dados = {"numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", "data_geracao": datetime.now().strftime("%d/%m/%Y"), "cliente_nome": cliente_nome, "cliente_wa": cliente_wa, "itens": st.session_state.itens, "desconto_valor": 0, "prazo_dias": 10, "frete_tipo": "Retirada"}
        salvar_no_historico(dados)
        st.session_state.ultima_proposta = {"numero": dados["numero_proposta"], "html": gerar_proposta_html(dados), "link_wa": extrair_link_whatsapp_completo(dados)}
        st.rerun()

    if st.session_state.ultima_proposta:
        p = st.session_state.ultima_proposta
        st.download_button("📥 Baixar Proposta", p["html"], f"{p['numero']}.html")
        st.link_button("📱 WhatsApp", p["link_wa"])

with aba2:
    st.write("Histórico carregado...")
    st.write(carregar_historico())

with aba3:
    st.write("Relatórios...")
