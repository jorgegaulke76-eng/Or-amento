import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime
import base64
import os

st.set_page_config(page_title="Alphafest | Orçamentos", page_icon="📝", layout="wide")

# --- FUNÇÕES DE SUPORTE ---
def get_img(p): return base64.b64encode(open(p, "rb").read()).decode() if os.path.exists(p) else ""

def gerar_html(d):
    tabela = "".join([f"<tr><td style='padding:5px; border-bottom:1px solid #ddd;'>{i['Produto']}<br><small>{i['Detalhes']}</small></td><td style='padding:5px; text-align:center;'>{i['Qtd']}</td><td style='padding:5px; text-align:right;'>R$ {i['Valor Unit.']:.2f}</td><td style='padding:5px; text-align:right;'>R$ {i['Qtd']*i['Valor Unit.']:.2f}</td></tr>" for i in d["itens"]])
    total = sum(i['Qtd']*i['Valor Unit.'] for i in d["itens"]) - d['desconto_valor']
    return f"""<html><head><meta charset='UTF-8'></head><body style='font-family:sans-serif; max-width:700px; margin:auto;'>
    <div style='display:flex; justify-content:space-between; border-bottom:2px solid #000;'>
        <img src='data:image/png;base64,{get_img("logo.png")}' style='width:80px;'>
        <div style='text-align:right; font-size:10px;'><b>ALPHAFEST ITATIBA</b><br>CNPJ: 24.374.857/0001-30<br>Emissão: {d['data_geracao']}</div>
    </div>
    <div style='background:#333; color:#fff; padding:5px; font-weight:bold; margin-top:10px;'>PROPOSTA Nº {d['numero_proposta']}</div>
    <table style='width:100%; border-collapse:collapse; margin-top:10px; font-size:12px;'>
        <thead><tr style='background:#f4f4f4;'><th>ITEM</th><th>QTD</th><th>UNIT.</th><th>TOTAL</th></tr></thead>
        <tbody>{tabela}</tbody>
    </table>
    <p style='text-align:right; font-weight:bold;'>TOTAL: R$ {total:.2f}</p>
    <div style='border:1px solid #ccc; padding:10px; font-size:11px;'>
        <img src='data:image/png;base64,{get_img("pix.png")}' style='width:50px; float:left; margin-right:10px;'>
        <b>Pagamento Pix:</b> Ana Lúcia Zepelini | Cora SCD (403)<br>Ag: 0001 | Conta: 2515972-5<br>
        <a href='https://linkspix.app/alphafestitatiba'>Acesse nosso link PIX</a>
    </div></body></html>"""

# --- DASHBOARD E FORMULÁRIO ---
tab1, tab2 = st.tabs(["📝 Orçamento", "📊 Dashboard"])

with tab1:
    st.header("Novo Orçamento")
    c_nome = st.text_input("Cliente")
    c_wa = st.text_input("WhatsApp")
    if "itens" not in st.session_state: st.session_state.itens = []
    
    col1, col2 = st.columns(2)
    p = col1.text_input("Produto")
    q = col2.number_input("Qtd", 1)
    v = col2.number_input("Valor", 0.0)
    if st.button("Adicionar"): st.session_state.itens.append({"Produto": p, "Qtd": q, "Valor Unit.": v, "Detalhes": "..."}); st.rerun()
    
    if st.session_state.itens:
        st.write(pd.DataFrame(st.session_state.itens))
        if st.button("Gerar Proposta"):
            dados = {"numero_proposta": "PROP-123", "data_geracao": "28/07/2026", "data_entrega": "30/07/2026", "cliente_nome": c_nome, "cliente_cpf_cnpj": "", "cliente_wa": c_wa, "itens": st.session_state.itens, "desconto_valor": 0, "frete_tipo": "Retirada"}
            st.download_button("Baixar HTML", gerar_html(dados), "proposta.html")
            st.success("Proposta pronta para baixar!")

with tab2:
    st.header("Dashboard")
    try:
        client = get_sheets_client()
        df = pd.DataFrame(client.open("HistoricoAlphafest").sheet1.get_all_records())
        st.metric("Total de Pedidos", len(df))
        st.line_chart(df.groupby('data_geracao').size())
        st.dataframe(df)
    except: st.error("Conecte a planilha.")
