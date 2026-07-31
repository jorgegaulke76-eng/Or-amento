import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime, date
import altair as alt

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", layout="wide")
ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- INICIALIZAÇÃO DE SEGURANÇA ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "temp_itens" not in st.session_state: st.session_state.temp_itens = []

# --- FUNÇÕES ---
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

# --- FUNÇÃO GERAR HTML (LAYOUT CORRIGIDO CONFORME IMAGEM) ---
def gerar_html(prop):
    # Cálculo
    total_bruto = sum(i.get('quantidade', 0) * i.get('valor_unitario', 0) for i in prop.get('itens', []))
    valor_final = prop.get('valor_total', total_bruto)
    desconto = total_bruto - valor_final
    
    itens_html = ""
    for item in prop.get('itens', []):
        subtotal_item = item.get('quantidade', 0) * item.get('valor_unitario', 0)
        itens_html += f"""
        <tr>
            <td><strong>{item.get('produto', '')}</strong><br><small>{item.get('especificacoes', '')}</small></td>
            <td>{item.get('quantidade', 0)}</td>
            <td>R$ {item.get('valor_unitario', 0):.2f}</td>
            <td>R$ {subtotal_item:.2f}</td>
        </tr>"""

    wa_link = f"https://wa.me/?text={urllib.parse.quote(formatar_msg_whatsapp(prop))}"

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4 portrait; margin: 10mm; }}
            body {{ font-family: 'Segoe UI', sans-serif; color: #333; }}
            .container {{ max-width: 750px; margin: auto; border: 1px solid #ddd; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: start; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 20px 0; background: #f4f4f4; padding: 10px; }}
            .info-item label {{ font-size: 10px; font-weight: bold; text-transform: uppercase; color: #555; display: block; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #333; color: white; padding: 8px; text-align: left; font-size: 12px; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; font-size: 13px; }}
            .resumo {{ text-align: right; margin-top: 15px; font-size: 14px; }}
            .footer {{ margin-top: 30px; font-size: 11px; border-top: 1px solid #ddd; padding-top: 10px; }}
            .btn-wa {{ display: block; width: 100%; background: #25D366; color: white; text-align: center; padding: 15px; border-radius: 5px; font-weight: bold; text-decoration: none; margin-top: 20px; }}
            @media print {{ .btn-wa {{ display: none; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div><h2>ALPHAFEST</h2></div>
                <div style="text-align: right; font-size: 12px;">
                    Itatiba - SP<br>Emissão: {prop.get('data_geracao', 'N/A')}
                </div>
            </div>
            <h3>PROPOSTA {prop.get('numero_proposta', '')}</h3>
            <div class="info-grid">
                <div class="info-item"><label>Cliente</label><span>{prop.get('cliente_nome', 'N/A')}</span></div>
                <div class="info-item"><label>CPF/CNPJ</label><span>{prop.get('documento', 'N/A')}</span></div>
                <div class="info-item"><label>WhatsApp</label><span>{prop.get('whatsapp', 'N/A')}</span></div>
                <div class="info-item"><label>Data Entrega</label><span>{prop.get('data_entrega', 'N/A')}</span></div>
            </div>
            <table>
                <thead><tr><th>ITEM / DESCRIÇÃO</th><th>QTD</th><th>UNIT.</th><th>SUBTOTAL</th></tr></thead>
                <tbody>{itens_html}</tbody>
            </table>
            <div class="resumo">
                <p>Subtotal: R$ {total_bruto:.2f}</p>
                <p>Desconto: R$ {desconto:.2f}</p>
                <p><strong>VALOR TOTAL: R$ {valor_final:.2f}</strong></p>
            </div>
            <div class="footer">
                <p><strong>Condições de Produção & Pagamento:</strong><br>
                Para firmar seu pedido, trabalhamos com pagamento do valor total no pedido.<br>
                Titular: Ana Lúcia Zepelini | Conta: 2515972-5<br>
                Prazo de Produção: 1 dia útil | Validade: 5 dias corridos.</p>
            </div>
            <a href="{wa_link}" class="btn-wa">ENVIAR COMPROVANTE NO WHATSAPP</a>
        </div>
    </body>
    </html>
    """
    return html

def formatar_msg_whatsapp(prop):
    total = prop.get('valor_total', 0)
    itens_str = ""
    for item in prop.get('itens', []):
        valor_unit = item.get('valor_unitario', 0)
        total_item = item.get('quantidade', 0) * valor_unit
        itens_str += f"{item.get('quantidade', 0)}x {item.get('produto', '')} = R${total_item:.2f}\n"
    
    msg = f"*PROPOSTA ALPHAFEST ITATIBA*\n*Cliente:* {prop.get('cliente_nome', '')}\n*Valor:* R$ {total:.2f}\n\nItens:\n{itens_str}\n\n*Pagamento:* https://linkspix.app/alphafestitatiba"
    return msg

def criar_grafico_profissional(df, x_col, y_col, titulo):
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color='#2e86de').encode(
        x=alt.X(f'{x_col}:O', title="", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f'{y_col}:Q', title="", axis=None),
        tooltip=[x_col, y_col]
    ).properties(title=titulo, height=300)
    return chart

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios"])

with aba1:
    fk = st.session_state.form_key
    nome = st.text_input("Nome", key=f"c_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF/CNPJ", key=f"d_{fk}")
    wa = c2.text_input("WhatsApp", key=f"w_{fk}")
    prod = st.text_input("Produto", key=f"p_{fk}")
    with st.expander("🎨 Detalhes"):
        et = st.text_input("Tema/Ocasião", key=f"et_{fk}")
        eg = st.text_area("Outros Detalhes", key=f"eg_{fk}")
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário", value=0.0, key=f"v_{fk}")
    if st.button("➕ Adicionar"):
        st.session_state.temp_itens.append({"produto": prod, "especificacoes": f"{et} | {eg}", "quantidade": q, "valor_unitario": v})
        st.rerun()
    if st.session_state.temp_itens:
        st.write(pd.DataFrame(st.session_state.temp_itens))
        desc = st.number_input("Desconto (R$)", 0.0)
        dt_e = st.date_input("Entrega")
        if st.button("🚀 SALVAR"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "data_entrega": dt_e.strftime("%d/%m/%Y"),
                "cliente_nome": nome, "documento": doc, "whatsapp": wa,
                "itens": list(st.session_state.temp_itens),
                "valor_total": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens) - desc
            }
            h = carregar_historico()
            h.insert(0, dados)
            salvar_historico_completo(h)
            st.session_state.temp_itens = []
            st.session_state.form_key += 1
            st.rerun()

with aba2:
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            c1, c2 = st.columns(2)
            c1.link_button("📱 WhatsApp", f"https://wa.me/?text={urllib.parse.quote(formatar_msg_whatsapp(prop))}")
            c2.download_button("📄 HTML", gerar_html(prop), file_name=f"{prop['numero_proposta']}.html")
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"): excluir_proposta(prop['numero_proposta'])

with aba3:
    st.write("Relatórios disponíveis")
