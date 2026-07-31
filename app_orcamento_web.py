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
            body {{ font-family: sans-serif; padding: 20px; color: #333; }}
            .container {{ max-width: 800px; margin: auto; border: 1px solid #ccc; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e293b; margin-bottom: 15px; padding-bottom: 5px; }}
            .header-info {{ text-align: right; font-size: 9px; line-height: 1.2; color: #333; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; padding: 10px; background: #f1f5f9; border: 1px solid #e2e8f0; }}
            .info-item label {{ font-size: 9px; font-weight: bold; color: #1e293b; text-transform: uppercase; display: block; }}
            .info-item span {{ font-size: 12px; font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #1e293b; color: white; padding: 6px; text-align: left; font-size: 11px; }}
            td {{ padding: 6px; border-bottom: 1px solid #eee; font-size: 12px; }}
            .resumo {{ text-align: right; margin-top: 15px; font-weight: bold; color: #1e293b; font-size: 13px; }}
            .footer-box {{ margin-top: 20px; padding: 10px; border: 2px solid #1e293b; border-radius: 5px; font-size: 11px; display: flex; gap: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div><img src="data:image/png;base64,{logo_base64}" style="max-width: 120px;"></div>
                <div class="header-info">
                    <strong>Alphafest Itatiba</strong><br>
                    CNPJ - 24.374.857/0001-30 | IE - 382105300112<br>
                    Avenida Manoel Verginio de Almeida, 442 - Alto Santa Cruz - Itatiba - SP<br>
                    Email - alphafesti@gmail.com | Celular - ( 11 ) 9724-9533<br>
                    <strong>Emissão: {prop.get('data_geracao', 'N/A')}</strong>
                </div>
            </div>
            <h2 style="color: #1e293b; margin: 5px 0;">PROPOSTA {prop.get('numero_proposta', '')}</h2>
            <div class="info-grid">
                <div class="info-item"><label>Cliente</label><span>{prop.get('cliente_nome', 'N/A')}</span></div>
                <div class="info-item"><label>CPF / CNPJ</label><span>{prop.get('documento', 'Não informado')}</span></div>
                <div class="info-item"><label>WhatsApp</label><span>{prop.get('whatsapp', 'Não informado')}</span></div>
                <div class="info-item"><label>Entrega</label><span>{prop.get('data_entrega', 'N/A')}</span></div>
            </div>
            <table>
                <thead><tr><th>ITEM / DESCRIÇÃO</th><th>QTD</th><th>UNIT.</th><th>SUBTOTAL</th></tr></thead>
                <tbody>{itens_html}</tbody>
            </table>
            <div class="resumo">
                <p>Subtotal: R$ {subtotal:.2f} | Desconto: R$ {desconto:.2f}</p>
                <p style="font-size: 15px;">VALOR TOTAL: R$ {total:.2f}</p>
            </div>
            <div class="footer-box">
                <img src="data:image/png;base64,{pix_base64}" style="width: 80px;">
                <div>
                    🤝 Para fechar seu pedido, trabalhamos com pagamento do valor total!<br>
                    💳 <strong>PAGAMENTO VIA PIX</strong>: 24374857000130 (CNPJ)<br>
                    👉 <a href="https://linkspix.app/alphafestitatiba">Link para pagar</a> | Banco CORA | Ana Lúcia Zepelini<br>
                    <strong>Conta Jurídica:</strong> Ag: 0001 | CC: 2515972-5<br>
                    <em>Somente após enviado comprovante daremos seguimento ao seu pedido !!🥰</em><br>
                    <strong>Ps. Orçamento válido por 5 dias.</strong>
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
        itens_str += f"{item.get('quantidade', 0)} {item.get('produto', '')} --- R${item.get('valor_unitario', 0):.2f}\n"
    return f"*PROPOSTA ALPHAFEST ITATIBA*\n*Cliente:* {prop.get('cliente_nome', '')}\n*Valor:* R$ {total:.2f}\n\n{itens_str}\n\n*Pagamento:* https://linkspix.app/alphafestitatiba"

def criar_grafico_profissional(df, x_col, y_col, titulo):
    return alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color='#2e86de').encode(
        x=alt.X(f'{x_col}:O', title="", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f'{y_col}:Q', title="", axis=None),
        tooltip=[x_col, y_col]
    ).properties(title=titulo, height=300)

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
hoje = date.today()
for p in carregar_historico():
    try:
        data_entrega = datetime.strptime(p.get("data_entrega", ""), "%d/%m/%Y").date()
        if (not p.get("pago", False) or not p.get("entregue", False)):
            if data_entrega == hoje: st.warning(f"⚠️ ENTREGA HOJE: {p['numero_proposta']}")
            elif data_entrega < hoje: st.error(f"🚨 ATRASADO: {p['numero_proposta']}")
    except: continue

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios"])

with aba1:
    fk = st.session_state.form_key
    nome = st.text_input("Nome", key=f"c_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF/CNPJ", key=f"d_{fk}")
    wa = c2.text_input("WhatsApp", key=f"w_{fk}")
    prod = st.text_input("Produto", key=f"p_{fk}")
    with st.expander("🎨 Detalhes", expanded=True):
        c1, c2 = st.columns(2)
        et = c1.text_input("Tema", key=f"et_{fk}")
        eg = c1.text_input("Obs", key=f"eg_{fk}")
    q = st.number_input("Qtd", 1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor", 0.0, step=0.5, key=f"v_{fk}")
    if st.button("➕ Adicionar"):
        st.session_state.temp_itens.append({"produto": prod, "especificacoes": f"{et}|{eg}", "quantidade": q, "valor_unitario": v})
        st.rerun()
    if st.session_state.temp_itens:
        desc = st.number_input("Desconto", 0.0, key=f"desc_{fk}")
        dt_e = st.date_input("Entrega")
        if st.button("🚀 SALVAR"):
            dados = {"numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", "data_geracao": datetime.now().strftime("%d/%m/%Y"), "data_entrega": dt_e.strftime("%d/%m/%Y"), "cliente_nome": nome, "documento": doc, "whatsapp": wa, "itens": list(st.session_state.temp_itens), "valor_total": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens) - desc, "pago": False, "entregue": False}
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
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "entregue", not prop.get("entregue", False)))
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"): excluir_proposta(prop['numero_proposta'])

with aba3:
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        df['Data'] = pd.to_datetime(df['data_geracao'], dayfirst=True)
        # Flatten itens para produtos mais vendidos
        all_items = []
        for prop in h:
            for item in prop['itens']:
                all_items.append({'Data': pd.to_datetime(prop['data_geracao'], dayfirst=True), 'Produto': item['produto'], 'Qtd': item['quantidade']})
        df_itens = pd.DataFrame(all_items)
        
        per = st.selectbox("Agrupar por", ["Dia", "Semana", "Mês", "Ano"])
        res = {"Dia": "%d/%m/%Y", "Semana": "W-MON", "Mês": "M", "Ano": "Y"}[per]
        
        st.subheader("💰 Total Receita")
        st.altair_chart(criar_grafico_profissional(df.groupby(df['Data'].dt.strftime(res) if per == "Dia" else df.set_index('Data').resample(res).groups.keys())['valor_total'].sum().reset_index(), 'Data', 'valor_total', 'Receita'), use_container_width=True)
        
        st.subheader("🏆 Produtos Mais Vendidos")
        st.altair_chart(criar_grafico_profissional(df_itens.groupby(['Produto'])['Qtd'].sum().reset_index(), 'Produto', 'Qtd', 'Vendas'), use_container_width=True)
