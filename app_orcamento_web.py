import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime
import base64
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamentos | Alphafest", page_icon="📝", layout="centered")

# --- FUNÇÃO PARA EMBUTIR IMAGENS ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

logo_b64 = get_image_base64("logo.png")
qr_b64 = get_image_base64("pix.png")

# --- CONEXÃO COM GOOGLE SHEETS ---
def get_sheets_client():
    creds_dict = dict(st.secrets["gcp"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def salvar_no_sheets(dados):
    try:
        client = get_sheets_client()
        sheet = client.open("HistoricoAlphafest").sheet1
        row = [dados['numero_proposta'], dados['data_geracao'], dados['data_entrega'], dados['cliente_nome'], 
               dados['cliente_cpf_cnpj'], dados['cliente_wa'], str(dados['itens']), 
               str(dados['desconto_valor']), str(dados['prazo_dias']), dados['frete_tipo'], "Não", "Não"]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- FUNÇÃO HTML ---
def gerar_proposta_html(dados):
    linhas_tabela = ""
    subtotal_geral = 0.0
    for item in dados["itens"]:
        sub = item["Qtd"] * item["Valor Unit."]
        subtotal_geral += sub
        d = item['Detalhes'].split('|')
        detalhes_txt = f"{d[0]} {d[1]} {d[2]}"
        linhas_tabela += f"""
        <tr>
            <td style="padding:6px; border-bottom:1px solid #eee;"><b>{item['Produto']}</b><br><small style="color:#666;">{detalhes_txt}</small></td>
            <td style="padding:6px; text-align:center; border-bottom:1px solid #eee;">{item['Qtd']} un.</td>
            <td style="padding:6px; text-align:right; border-bottom:1px solid #eee;">R$ {item['Valor Unit.']:.2f}</td>
            <td style="padding:6px; text-align:right; border-bottom:1px solid #eee;">R$ {sub:.2f}</td>
        </tr>"""
    
    total = max(0, subtotal_geral - dados.get('desconto_valor', 0))
    
    return f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 700px; margin: auto; padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #003366; padding-bottom: 5px;">
            <img src="data:image/png;base64,{logo_b64}" style="max-width: 80px;">
            <div style="text-align: right; font-size: 9px; line-height: 1.1;">
                <b>ALPHAFEST ITATIBA</b><br>
                CNPJ: 24.374.857/0001-30 | Av. Manoel Verginio de Almeida, 442<br>
                Itatiba - SP | Emissão: {dados['data_geracao']}
            </div>
        </div>
        <div style="background: #003366; color: #fff; padding: 5px; margin-top: 10px; font-size: 12px; font-weight: bold;">
            PROPOSTA Nº {dados['numero_proposta']}
        </div>
        <div style="padding: 8px; border: 1px solid #ccc; font-size: 11px; margin-top: 5px;">
            <b>CLIENTE:</b> {dados['cliente_nome']} | <b>CPF/CNPJ:</b> {dados['cliente_cpf_cnpj']} | <b>DATA ENTREGA:</b> {dados['data_entrega']}
        </div>
        <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size: 11px;">
            <thead><tr style="background:#f4f4f4; text-align:left;"><th style="padding:6px;">ITEM / DESCRIÇÃO</th><th style="padding:6px; text-align:center;">QTD</th><th style="padding:6px; text-align:right;">UNIT.</th><th style="padding:6px; text-align:right;">TOTAL</th></tr></thead>
            <tbody>{linhas_tabela}</tbody>
        </table>
        <div style="text-align:right; font-size: 12px; margin-top: 10px;">
            Subtotal: R$ {subtotal_geral:.2f} | Desconto: R$ {dados['desconto_valor']:.2f}<br>
            <b style="color:green; font-size: 14px;">VALOR TOTAL DO PEDIDO: R$ {total:.2f}</b>
        </div>
        <div style="margin-top: 20px; border: 1px solid #ccc; padding: 10px; font-size: 10px;">
            <b>Condições de Produção & Pagamento:</b>
            <div style="display:flex; align-items:center; margin-top:5px;">
                <img src="data:image/png;base64,{qr_b64}" style="width:50px; margin-right:10px;">
                <div>
                    Titular: Ana Lúcia Zepelini | Banco: Cora SCD (403) | Ag: 0001 | Conta: 2515972-5<br>
                    <a href="https://linkspix.app/alphafestitatiba">Acesse nosso link PIX</a>
                </div>
            </div>
            <p style="margin-top:5px;"><i>Somente após realizado pagamento e envio de comprovante daremos seguimento ao pedido!</i><br>
            Frete/Entrega: {dados['frete_tipo']} | Validade: 5 dias corridos</p>
        </div>
    </body>
    </html>
    """

def formatar_mensagem_whatsapp(dados):
    subtotal_geral = sum(item["Qtd"] * item["Valor Unit."] for item in dados["itens"])
    total = max(0, subtotal_geral - dados.get('desconto_valor', 0))
    lista_itens = ""
    for i, item in enumerate(dados["itens"], 1):
        d = item['Detalhes'].split('|')
        lista_itens += f"{i}. {item['Produto']}\n Detalhes: {d[0]} {d[1]} {d[2]}\n Qtd: {item['Qtd']} un. | Unit: R$ {item['Valor Unit.']:.2f} | Sub: R$ {item['Qtd'] * item['Valor Unit.']:.2f}\n\n"

    msg = f"PROPOSTA ALPHAFEST ITATIBA\nNº: {dados['numero_proposta']}\nEmissão: {dados['data_geracao']}\n\nCLIENTE: {dados['cliente_nome']}\nCPF/CNPJ: {dados['cliente_cpf_cnpj']}\n\nITENS DO PEDIDO:\n{lista_itens}---\nSubtotal: R$ {subtotal_geral:.2f}\nDesconto: R$ {dados['desconto_valor']:.2f}\nVALOR TOTAL: R$ {total:.2f}\n\nPrevisão: {dados['data_entrega']}\nFrete: {dados['frete_tipo']}\nValidade: 5 dias\n\nPAGAMENTO VIA PIX:\nPix: https://linkspix.app/alphafestitatiba\nTitular: Ana Lúcia Zepelini\nBanco: Cora SCD (403)\nAgência: 0001 | Conta: 2515972-5\n\nSomente após realizado pagamento e envio de comprovante daremos seguimento ao pedido!"
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    return f"https://wa.me/{num_wa if len(num_wa)>10 else '55'+num_wa}?text={urllib.parse.quote(msg)}"

# --- INTERFACE ---
if "itens" not in st.session_state: st.session_state.itens = []
if "previa_dados" not in st.session_state: st.session_state.previa_dados = None

st.title("📝 Orçamentos Alphafest")

# MUDANÇA IMPORTANTE: A Prévia aparece NO TOPO para você não perder!
if st.session_state.previa_dados:
    st.success("✅ Prévia gerada com sucesso!")
    c_baixar, c_wa = st.columns(2)
    c_baixar.download_button("📥 Baixar Proposta", gerar_proposta_html(st.session_state.previa_dados), "proposta.html")
    c_wa.link_button("📱 WhatsApp", formatar_mensagem_whatsapp(st.session_state.previa_dados))
    
    if st.button("🚀 CONFIRMAR E SALVAR"):
        if salvar_no_sheets(st.session_state.previa_dados):
            st.success("Orçamento salvo!")
            st.session_state.itens = []
            st.session_state.previa_dados = None
            st.rerun()

with st.expander("👤 Dados do Cliente", expanded=True):
    st.text_input("Nome / Razão Social", key="c_nome")
    c1, c2 = st.columns(2)
    c1.text_input("CPF / CNPJ", key="c_cpf")
    c2.text_input("WhatsApp", key="c_wa")

with st.expander("➕ Adicionar Item", expanded=True):
    st.text_input("Produto", key="i_prod")
    c1, c2 = st.columns(2)
    t = c1.text_input("Tema", key="i_tema")
    n = c1.text_input("Nome/Idade", key="i_nome")
    c = c1.text_input("Cor/Material", key="i_cor")
    ob = c2.text_input("Observações", key="i_obs")
    q, v = st.columns(2)
    qtd = q.number_input("Quantidade", 1, key="i_qtd")
    v_unit = v.number_input("Valor Unit. (R$)", 0.0, key="i_vunit", format="%.2f")
    if st.button("Adicionar à Lista"):
        st.session_state.itens.append({"Produto": st.session_state.i_prod, "Qtd": qtd, "Valor Unit.": v_unit, "Detalhes": f"{t}|{n}|{c}|{ob}"})
        st.rerun()

if st.session_state.itens:
    st.subheader("📋 Itens do Orçamento")
    st.dataframe(pd.DataFrame(st.session_state.itens), use_container_width=True, hide_index=True)
    if st.button("🗑️ Limpar Lista"):
        st.session_state.itens = []
        st.rerun()
    desc = st.number_input("Desconto (R$)", 0.0, key="c_desc", format="%.2f")
    entrega = st.date_input("Data Limite", key="c_dt")
    if st.button("👁️ GERAR PRÉVIA", type="primary"):
        st.session_state.previa_dados = {"numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", "data_geracao": datetime.now().strftime("%d/%m/%Y"), "data_entrega": entrega.strftime("%d/%m/%Y"), "cliente_nome": st.session_state.c_nome, "cliente_cpf_cnpj": st.session_state.c_cpf, "cliente_wa": st.session_state.c_wa, "itens": st.session_state.itens, "desconto_valor": desc, "prazo_dias": "10", "frete_tipo": "Retirada em Itatiba"}
        st.rerun()
