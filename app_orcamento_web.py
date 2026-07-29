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
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES DE BANCO DE DADOS / HISTÓRICO ---
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

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file: return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def exibir_logo_interface():
    if os.path.exists(PATH_LOGO_OFICIAL):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2: st.image(PATH_LOGO_OFICIAL, use_container_width=True)

# --- FUNÇÃO CORRIGIDA: WHATSAPP SEM INTERROGAÇÕES ---
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
           f"-----------------------------------\n📦 *ITENS DO PEDIDO:*\n\n{texto_itens}-----------------------------------\n"
           f"💵 *Subtotal:* R$ {subtotal_geral:.2f}\n🏷️ *Desconto:* - R$ {desc_v:.2f}\n✅ *VALOR TOTAL DO PEDIDO:* R$ {total_final:.2f}\n"
           f"-----------------------------------\n📅 *Previsão de Entrega:* {dados.get('data_entrega', 'A combinar')}\n"
           f"⏳ *Prazo de Produção:* {dados.get('prazo_dias', '10')} dias úteis\n🚚 *Frete/Entrega:* {dados.get('frete_tipo', 'Retirada em Itatiba')}\n"
           f"⏰ *Validade:* 5 dias corridos\n\n💳 *PAGAMENTO VIA PIX:*\n👉 *Clique no link para pagar:* {LINK_PIX_OFICIAL}\n\n"
           f"• *Titular:* Ana Lúcia Zepelini | *Banco:* Cora SCD (403)\n• *Agência:* 0001 | *Conta:* 2515972-5\n"
           f"• *Empresa:* ANA LUCIA VIEIRA ZEPELINI 29480359880\n\n"
           f"👇 *Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido ! 🥰*")
    
    # CORREÇÃO: .encode('utf-8') garante que acentos não virem ?
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    return f"https://wa.me/{num_wa}?text={msg_enc}" if num_wa and len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={msg_enc}"

# --- FUNÇÃO CORRIGIDA: HTML (A4 + UTF-8 + ESPAÇAMENTO) ---
def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Alphafest Logo">' if logo_base64 else f'<div style="font-size:24px; font-weight:bold; color:#1e293b;">{MARCA_FABRICANTE}</div>'
    
    linhas_tabela = "".join([f"<tr><td><strong>{i['produto']}</strong><br><small style='color: #64748b;'>{i['especificacoes']}</small></td><td style='text-align:center;'>{i['quantidade']} un.</td><td style='text-align:right;'>R$ {i['valor_unitario']:.2f}</td><td style='text-align:right;'>R$ {(i['quantidade']*i['valor_unitario']):.2f}</td></tr>" for i in dados["itens"]])
    
    # CSS: Adicionado @media print para A4 e garantindo espaçamento profissional
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @media print {{ @page {{ size: A4 portrait; margin: 15mm; }} }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; color: #1e293b; line-height: 1.5; }}
            .container {{ max-width: 780px; margin: auto; min-height: 250mm; display: flex; flex-direction: column; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e293b; padding-bottom: 10px; margin-bottom: 20px; }}
            .logo {{ max-height: 80px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #334155; color: white; padding: 10px; text-align: left; font-size: 12px; }}
            td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; }}
            .footer-box {{ margin-top: auto; border: 1px solid #cbd5e1; padding: 15px; border-radius: 6px; font-size: 11px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                {logo_tag}
                <div style="text-align:right; font-size:10px;"><strong>{MARCA_FABRICANTE}</strong><br>CNPJ: 24.374.857/0001-30<br>Emissão: {dados['data_geracao']}</div>
            </div>
            <h2>Proposta Nº {dados['numero_proposta']}</h2>
            <div style="padding:10px; background:#f1f5f9; margin-bottom:20px;"><strong>Cliente:</strong> {dados['cliente_nome']}</div>
            <table>
                <thead><tr><th>ITEM</th><th>QTD</th><th>UNIT.</th><th>TOTAL</th></tr></thead>
                <tbody>{linhas_tabela}</tbody>
            </table>
            <div style="text-align:right; font-size:14px; font-weight:bold;">TOTAL: R$ {(sum(i['quantidade']*i['valor_unitario'] for i in dados['itens']) - dados.get('desconto_valor', 0)):.2f}</div>
            <div class="footer-box">
                <b>Condições de Pagamento:</b> Ana Lúcia Zepelini | PIX: {LINK_PIX_OFICIAL} | Ag: 0001 | Conta: 2515972-5
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# --- INTERFACE PRINCIPAL (Original) ---
exibir_logo_interface()
st.title("📄 ORÇAMENTOS ALPHAFEST")

# ... (O restante da sua lógica de interface e abas permanece idêntica ao que você já tinha) ...
