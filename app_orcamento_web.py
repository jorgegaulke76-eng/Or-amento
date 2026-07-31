import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime, date
import altair as alt
import base64

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", layout="wide")
ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- INICIALIZAÇÃO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "temp_itens" not in st.session_state: st.session_state.temp_itens = []

# --- FUNÇÕES ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    if not historico: return
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def alternar_status(num_proposta, campo, novo_valor):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta: p[campo] = novo_valor
    salvar_historico_completo(historico)

def excluir_proposta(num_proposta):
    historico = [p for p in carregar_historico() if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico)
    st.rerun()

def gerar_html(prop):
    subtotal = sum(i.get('quantidade', 0) * i.get('valor_unitario', 0) for i in prop.get('itens', []))
    total = prop.get('valor_total', subtotal)
    desconto = subtotal - total
    logo_base64 = get_image_base64("logo.png")
    pix_base64 = get_image_base64("pix.png")
    
    itens_html = ""
    for item in prop.get('itens', []):
        sub_item = item.get('quantidade', 0) * item.get('valor_unitario', 0)
        itens_html += f"<tr><td><strong>{item.get('produto', '')}</strong><br><small>{item.get('especificacoes', '')}</small></td><td>{item.get('quantidade', 0)}</td><td>R$ {item.get('valor_unitario', 0):.2f}</td><td>R$ {sub_item:.2f}</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: sans-serif; color: #333; }}
            .container {{ max-width: 750px; margin: auto; border: 1px solid #ccc; padding: 15px; }}
            .header {{ display: flex; justify-content: space-between; align-items: start; border-bottom: 2px solid #333; padding-bottom: 5px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; background: #f9f9f9; padding: 10px; border: 1px solid #ddd; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #333; color: white; padding: 8px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .resumo {{ text-align: right; margin-top: 15px; font-weight: bold; }}
            .footer-box {{ margin-top: 20px; padding: 10px; border: 1px solid #333; border-radius: 5px; font-size: 11px; display: flex; gap: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="data:image/png;base64,{logo_base64}" style="max-width: 100px;">
                <div style="text-align: right; font-size: 9px;">
                    <strong>Alphafest Itatiba</strong><br>CNPJ 24.374.857/0001-30 | IE 382105300112<br>
                    Av. Manoel Verginio de Almeida, 442 - Itatiba - SP<br>Emissão: {prop.get('data_geracao', 'N/A')}
                </div>
            </div>
            <h3>PROPOSTA {prop.get('numero_proposta', '')}</h3>
            <div class="info-grid">
                <div><label style="font-size: 9px; font-weight:bold;">CLIENTE</label><br>{prop.get('cliente_nome', 'N/A')}</div>
                <div><label style="font-size: 9px; font-weight:bold;">CPF/CNPJ</label><br>{prop.get('documento', 'N/A')}</div>
                <div><label style="font-size: 9px; font-weight:bold;">WHATSAPP</label><br>{prop.get('whatsapp', 'N/A')}</div>
                <div><label style="font-size: 9px; font-weight:bold;">ENTREGA</label><br>{prop.get('data_entrega', 'N/A')}</div>
            </div>
            <table>
                <thead><tr><th>ITEM / DESCRIÇÃO</th><th>QTD</th><th>UNIT.</th><th>SUBTOTAL</th></tr></thead>
                <tbody>{itens_html}</tbody>
            </table>
            <div class="resumo">
                Subtotal: R$ {subtotal:.2f} | Desconto: R$ {desconto:.2f}<br>VALOR TOTAL: R$ {total:.2f}
            </div>
            <div class="footer-box">
                <img src="data:image/png;base64,{pix_base64}" style="width: 70px;">
                <div>
                    🤝 Para fechar seu pedido, trabalhamos com pagamento do valor total!<br>
                    💳 <strong>PIX:</strong> 24374857000130 | <a href="https://linkspix.app/alphafestitatiba">Link para pagar</a><br>
                    <strong>Banco CORA:</strong> Ag: 0001 | CC: 2515972-5 | Ana Lúcia Zepelini<br>
                    <strong>CNPJ:</strong> 24.374.857/0001-30 | <strong>Ps:</strong> Válido por 5 dias.
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def formatar_msg_whatsapp(prop):
    total = prop.get('valor_total', 0)
    itens_str = ""
    for item in prop.get('itens', []):
        itens_str += f"{item.get('quantidade', 0)} {item.get('produto', '')} - R${item.get('valor_unitario', 0):.2f}\n"
    return f"*PROPOSTA ALPHAFEST*\nCliente: {prop.get('cliente_nome', '')}\nTotal: R$ {total:.2f}\n\nItens:\n{itens_str}\nPagamento: https://linkspix.app/alphafestitatiba"

def criar_grafico_profissional(df, x_col, y_col, titulo):
    return alt.Chart(df).mark_bar().encode(x=f'{x_col}:O', y=f'{y_col}:Q').properties(title=titulo)

# --- UI ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
hoje = date.today()
for p in carregar_historico():
    try:
        if (not p.get("pago", False) or not p.get("entregue", False)) and datetime.strptime(p.get("data_entrega", ""), "%d/%m/%Y").date() == hoje:
            st.warning(f"⚠️ ENTREGA HOJE: {p['numero_proposta']}")
    except: continue

aba1, aba2, aba3 = st.tabs(["➕ Novo", "📋 Histórico", "📊 Relatórios"])

with aba1:
    nome = st.text_input("Nome")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF/CNPJ")
    wa = c2.text_input("WhatsApp")
    prod = st.text_input("Produto")
    et = st.text_input("Tema/Detalhes")
    q = st.number_input("Qtd", 1, value=1)
    v = st.number_input("Valor Unitário", 0.0)
    if st.button("➕ Adicionar"):
        st.session_state.temp_itens.append({"produto": prod, "especificacoes": et, "quantidade": q, "valor_unitario": v})
        st.rerun()
    if st.session_state.temp_itens:
        desc = st.number_input("Desconto", 0.0)
        dt_e = st.date_input("Entrega")
        if st.button("🚀 SALVAR"):
            dados = {"numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", "data_geracao": datetime.now().strftime("%d/%m/%Y"), "data_entrega": dt_e.strftime("%d/%m/%Y"), "cliente_nome": nome, "documento": doc, "whatsapp": wa, "itens": list(st.session_state.temp_itens), "valor_total": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens) - desc, "pago": False, "entregue": False}
            h = carregar_historico()
            h.insert(0, dados)
            salvar_historico_completo(h)
            st.session_state.temp_itens = []
            st.rerun()

with aba2:
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            c1, c2 = st.columns(2)
            c1.link_button("📱 WhatsApp", f"https://wa.me/?text={urllib.parse.quote(formatar_msg_whatsapp(prop))}")
            c2.download_button("📄 HTML", gerar_html(prop), file_name=f"{prop['numero_proposta']}.html")
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "entregue", not prop.get("entregue", False)))
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"): excluir_proposta(prop['numero_proposta'])

with aba3:
    h = carregar_historico()
    if h: st.altair_chart(criar_grafico_profissional(pd.DataFrame(h).groupby('cliente_nome')['valor_total'].sum().reset_index(), 'cliente_nome', 'valor_total', 'Total'), use_container_width=True)
