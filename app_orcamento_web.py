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
PATH_PIX_QRCODE = "pix.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_DIRETO = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES DE DADOS ---
def formatar_doc_para_wa(doc):
    apenas_num = re.sub(r'\D', '', str(doc or ''))
    if len(apenas_num) == 11: return f"{apenas_num[:3]}. {apenas_num[3:6]}. {apenas_num[6:9]} - {apenas_num[9:]}"
    if len(apenas_num) == 14: return f"{apenas_num[:2]}.{apenas_num[2:5]}.{apenas_num[5:8]}/{apenas_num[8:12]}-{apenas_num[12:]}"
    return doc or "Não informado"

def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f: json.dump(historico, f, ensure_ascii=False, indent=4)

def atualizar_pedido(num_proposta, campo, valor):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = valor
            break
    salvar_historico_completo(historico)

# --- FUNÇÕES DE PROPOSTA ---
def carregar_imagem_base64(path_imagem):
    if os.path.exists(path_imagem):
        try:
            with open(path_imagem, "rb") as image_file: return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    
    subtotal = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc = dados.get("desconto_valor", 0.0)
    total = max(0.0, subtotal - desc)
    
    msg = (f"*PROPOSTA ALPHAFEST ITATIBA*\nNº: {dados['numero_proposta']}\n\n"
           f"CLIENTE: {dados['cliente_nome']}\nCPF/CNPJ: {formatar_doc_para_wa(dados.get('cliente_cpf_cnpj', ''))}\n"
           f"VALOR TOTAL: R$ {total:.2f}\n\n"
           f"🔗 *PAGAR VIA PIX:* {LINK_PIX_DIRETO}\n\n"
           f"Somente após comprovante daremos seguimento!")
    
    return f"https://wa.me/{num_wa}?text={urllib.parse.quote(msg)}" if len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"

def gerar_proposta_html(dados):
    logo = carregar_imagem_base64(PATH_LOGO_OFICIAL)
    pix = carregar_imagem_base64(PATH_PIX_QRCODE)
    
    qr_tag = f'<div style="text-align:center;"><img src="data:image/png;base64,{pix}" style="max-width:130px;"></div>' if pix else f'<div style="text-align:center;"><a href="{LINK_PIX_DIRETO}"><img src="https://api.qrserver.com/v1/create-qr-code/?size=130x130&data={urllib.parse.quote(LINK_PIX_DIRETO)}" style="max-width:130px;"></a></div>'
    
    subtotal = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    total = max(0.0, subtotal - dados.get("desconto_valor", 0.0))

    html = f"""
    <html><body>
    <div style="font-family:Arial; max-width:600px; margin:auto; border:1px solid #ccc; padding:20px;">
        <h2 style="text-align:center;">{MARCA_FABRICANTE}</h2>
        <p><strong>Cliente:</strong> {dados['cliente_nome']}</p>
        <p><strong>Total:</strong> R$ {total:.2f}</p>
        <div style="border-top:1px dashed #000; padding-top:10px;">
            <strong>Pagamento PIX:</strong>
            <p>Link: <a href="{LINK_PIX_DIRETO}">{LINK_PIX_DIRETO}</a></p>
            {qr_tag}
        </div>
    </div>
    </body></html>
    """
    return html

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo", "📋 Histórico", "📊 Relatórios"])

with aba1:
    # ... (Seu código de formulário permanece igual, apenas certifique-se de salvar os novos campos 'aprovado' e 'entregue' como False)
    # No botão "GERAR":
    # dados = {..., "aprovado": False, "entregue": False}
    pass

with aba2:
    historico = carregar_historico()
    hoje_str = date.today().strftime("%d/%m/%Y")
    
    # Filtra apenas os NÃO entregues para o alerta
    pendentes_hoje = [p for p in historico if p.get("data_entrega") == hoje_str and not p.get("entregue", False)]
    
    if pendentes_hoje:
        st.error(f"🚨 **ALERTA: {len(pendentes_hoje)} entrega(s) para hoje pendente(s)!**")
        for p in pendentes_hoje: st.write(f"👉 {p['cliente_nome']} ({p['numero_proposta']})")

    for prop in historico:
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']} {'✅ [ENTREGUE]' if prop.get('entregue') else '⏳ [PENDENTE]'}"):
            if not prop.get("entregue"):
                if st.button("📦 Marcar como ENTREGUE", key=f"ent_{prop['numero_proposta']}"):
                    atualizar_pedido(prop['numero_proposta'], "entregue", True)
                    st.rerun()
            # ... resto do código de botões (excluir, wa, etc)
