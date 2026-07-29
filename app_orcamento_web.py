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
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

# --- FUNÇÕES DE LAYOUT ---
def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        with open(PATH_LOGO_OFICIAL, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

def exibir_logo_interface():
    if os.path.exists(PATH_LOGO_OFICIAL):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2: st.image(PATH_LOGO_OFICIAL, use_container_width=True)

# --- FUNÇÃO WHATSAPP CORRIGIDA (UTF-8) ---
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
           f"📦 *ITENS DO PEDIDO:*\n\n{texto_itens}💵 *Subtotal:* R$ {subtotal_geral:.2f}\n🏷️ *Desconto:* - R$ {desc_v:.2f}\n"
           f"✅ *VALOR TOTAL DO PEDIDO:* R$ {total_final:.2f}\n"
           f"📅 *Entrega:* {dados.get('data_entrega', 'A combinar')}\n🚚 *Frete:* {dados.get('frete_tipo', 'Retirada em Itatiba')}\n\n"
           f"💳 *PAGAMENTO VIA PIX:*\n👉 *Link:* {LINK_PIX_OFICIAL}\n"
           f"• *Titular:* Ana Lúcia Zepelini | *Banco:* Cora SCD (403)\n• *Agência:* 0001 | *Conta:* 2515972-5\n\n"
           f"👇 *Somente após comprovante daremos seguimento ao seu pedido ! 🥰*")
    
    # CORREÇÃO AQUI: .encode('utf-8') evita as interrogações
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    return f"https://wa.me/{num_wa}?text={msg_enc}" if num_wa and len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={msg_enc}"

# --- FUNÇÃO HTML CORRIGIDA (A4 + UTF-8) ---
def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Logo">' if logo_base64 else ""
    
    # CSS ADICIONADO PARA A4 E IMPRESSÃO
    css = """
    <style>
        @page { size: A4 portrait; margin: 8mm; }
        body { font-family: Arial, sans-serif; }
        .container { max-width: 780px; margin: 0 auto; padding: 20px; }
        /* Adicione aqui todo o resto do seu CSS original... */
    </style>
    """
    
    # (MANTENHA AQUI O RESTO DO SEU HTML ORIGINAL)
    # Apenas adicione <meta charset='utf-8'> logo após o <head>
    return f"<html><head><meta charset='utf-8'>{css}</head><body>...</body></html>"

# [RESTO DO SEU CÓDIGO AQUI...]
