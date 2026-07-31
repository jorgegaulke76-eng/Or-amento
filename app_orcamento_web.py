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

def gerar_html(prop):
    # Segurança para calcular valor se não existir
    total = prop.get('valor_total', 0)
    if total == 0: total = sum(i.get('quantidade',0) * i.get('valor_unitario',0) for i in prop.get('itens',[]))
    
    # Construção do HTML com CSS embutido e Grid 2x2
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; border: 1px solid #ccc; padding: 20px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; padding: 10px; background: #f9f9f9; border: 1px solid #ddd; }}
            .info-item label {{ font-size: 10px; font-weight: bold; color: #555; text-transform: uppercase; display: block; }}
            .info-item span {{ font-size: 13px; font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #eee; padding: 8px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Orçamento {prop['numero_proposta']}</h1>
            
            <div class="info-grid">
                <div class="info-item"><label>Cliente / Empresa</label><span>{prop.get('cliente_nome', 'N/A')}</span></div>
                <div class="info-item"><label>CPF / CNPJ</label><span>{prop.get('documento', 'Não informado')}</span></div>
                <div class="info-item"><label>WhatsApp / Contato</label><span>{prop.get('whatsapp', 'Não informado')}</span></div>
                <div class="info-item"><label>Data Prevista de Entrega</label><span>{prop.get('data_entrega', 'N/A')}</span></div>
            </div>

            <table>
                <thead><tr><th>Produto</th><th>Qtd</th></tr></thead>
                <tbody>
    """
    for item in prop.get('itens', []):
        html += f"<tr><td>{item.get('produto', '')}</td><td>{item.get('quantidade', 0)}</td></tr>"
    
    html += f"""
                </tbody>
            </table>
            <h3>Total: R$ {total:.2f}</h3>
        </div>
    </body>
    </html>
    """
    return html

def formatar_msg_whatsapp(prop):
    total = prop.get('valor_total', 0)
    if total == 0:
        total = sum(i.get('quantidade', 0) * i.get('valor_unitario', 0) for i in prop.get('itens', []))
    
    itens_str = ""
    for item in prop.get('itens', []):
        valor_unit = item.get('valor_unitario', 0)
        total_item = item.get('quantidade', 0) * valor_unit
        itens_str += f"{item.get('quantidade', 0)} {item.get('produto', '')} --- R${valor_unit:.2f} --- R${total_item:.2f}\n"
    
    msg = f"""*PROPOSTA ALPHAFEST ITATIBA*
*Emissão:* {prop.get('data_geracao', '')}

*CLIENTE:* {prop.get('cliente_nome', '')}
*CPF/CNPJ:* {prop.get('documento', 'N/A')}
-----------------------------------
*ITENS DO PEDIDO:*
{itens_str}
-----------------------------------
*VALOR TOTAL DO PEDIDO:* R$ {total:.2f}
-----------------------------------
*Previsão de Entrega:* {prop.get('data_entrega', 'N/A')}
*Prazo de Produção:* 1 dia útil
*Frete/Entrega:* Retirada em Itatiba
*Validade:* 5 dias corridos

*PAGAMENTO VIA PIX:*
https://linkspix.app/alphafestitatiba

* Titular: Ana Lúcia Zepelini | *Conta:* 2515972-5
*Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido !"""
    return msg

def criar_grafico_profissional(df, x_col, y_col, titulo):
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color='#2e86de').encode(
        x=alt.X(f'{x_col}:O', title="", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f'{y_col}:Q', title="", axis=None),
        tooltip=[x_col, y_col]
    ).properties(title=titulo, height=300)
    text = chart.mark_text(align='center', baseline='bottom', dy=-5, fontWeight='bold', color='#2c3e50').encode(
        text=alt.Text(y_col, format='.2f')
    )
    return (chart + text).configure_view(strokeWidth=0).configure_axis(grid=False)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Painel de Segurança")
    h_atual = carregar_historico()
    if h_atual:
        st.download_button("💾 BAIXAR BACKUP", data=json.dumps(h_atual, ensure_ascii=False, indent=4), file_name="backup_historico.json", mime="application/json", type="primary", use_container_width=True)

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

# --- ALERTAS DE VENCIMENTO ---
hoje = date.today()
for p in carregar_historico():
    try:
        data_entrega_str = p.get("data_entrega", "")
        if data_entrega_str:
            data_entrega = datetime.strptime(data_entrega_str, "%d/%m/%Y").date()
            if (not p.get("pago", False) or not p.get("entregue", False)):
                if data_entrega == hoje: st.warning(f"⚠️ ENTREGA HOJE: {p['numero_proposta']} - {p['cliente_nome']}")
                elif data_entrega < hoje: st.error(f"🚨 ATRASADO: {p['numero_proposta']} | {p['cliente_nome']} | Vencido em {p.get('data_entrega')}")
    except: continue

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios"])

with aba1:
    fk = st.session_state.form_key
    nome = st.text_input("Nome / Razão Social", key=f"c_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF / CNPJ", key=f"d_{fk}")
    wa = c2.text_input("WhatsApp", key=f"w_{fk}")
    
    prod = st.text_input("Produto", key=f"p_{fk}")
    with st.expander("🎨 Personalização & Especificações", expanded=True):
        c1, c2 = st.columns(2)
        et = c1.text_input("Tema / Ocasião", key=f"et_{fk}")
        en = c1.text_input("Nome(s) Personalizado(s)", key=f"en_{fk}")
        ec = c1.text_input("Cor / Material", key=f"ec_{fk}")
        ei = c2.text_input("Idade / Data do Evento", key=f"ei_{fk}")
        eg = c2.text_input("Outros Detalhes", key=f"eg_{fk}")
    
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário (R$)", value=0.0, step=0.5, key=f"v_{fk}")
    
    if st.button("➕ Adicionar Item"):
        detalhes = f"Tema: {et} | Nome: {en} | Idade: {ei} | Cor: {ec} | Obs: {eg}"
        st.session_state.temp_itens.append({"produto": prod, "especificacoes": detalhes, "quantidade": q, "valor_unitario": v})
        st.rerun()

    if st.session_state.temp_itens:
        st.write("📋 **Prévia dos itens:**")
        st.dataframe(pd.DataFrame(st.session_state.temp_itens), use_container_width=True)
        st.divider()
        desc = st.number_input("Desconto (R$)", 0.0, key=f"desc_{fk}")
        dt_entrega = st.date_input("📅 Data Entrega", value=date.today(), key=f"dt_{fk}")
        
        if st.button("🚀 SALVAR PROPOSTA"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "data_entrega": dt_entrega.strftime("%d/%m/%Y"),
                "cliente_nome": nome,
                "documento": doc,
                "whatsapp": wa,
                "itens": list(st.session_state.temp_itens),
                "valor_total": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens) - desc,
                "pago": False, "entregue": False
            }
            h = carregar_historico()
            h.insert(0, dados)
            salvar_historico_completo(h)
            st.session_state.temp_itens = []
            st.session_state.form_key += 1
            st.rerun()

with aba2:
    for prop in carregar_historico():
        num_p = prop['numero_proposta']
        with st.expander(f"{num_p} - {prop['cliente_nome']}"):
            st.write(f"📅 **Entrega:** {prop.get('data_entrega')}")
            for item in prop.get('itens', []): 
                st.write(f"• {item.get('produto', '')} (Qtd: {item.get('quantidade', 0)})")
            
            c1, c2 = st.columns(2)
            c1.link_button("📱 Enviar WhatsApp", f"https://wa.me/?text={urllib.parse.quote(formatar_msg_whatsapp(prop))}")
            c2.download_button("📄 Gerar HTML", gerar_html(prop), file_name=f"{num_p}.html")
            
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{num_p}", on_change=alternar_status, args=(num_p, "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{num_p}", on_change=alternar_status, args=(num_p, "entregue", not prop.get("entregue", False)))
            
            if st.button("🗑️ Excluir", key=f"del_{num_p}"): excluir_proposta(num_p)

with aba3:
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        df['valor_total'] = df.apply(lambda row: sum(i.get('quantidade', 0) * i.get('valor_unitario', 0) for i in row.get('itens', [])) if (pd.isna(row.get('valor_total')) or row.get('valor_total') == 0) else row.get('valor_total', 0), axis=1)
        df['Data'] = pd.to_datetime(df['data_geracao'], dayfirst=True)
        
        per = st.selectbox("Período de Agrupamento", ["Dia", "Semana", "Mês", "Ano"], key="per_rel")
        
        st.subheader("👥 Total por Cliente")
        st.altair_chart(criar_grafico_profissional(df.groupby('cliente_nome')['valor_total'].sum().reset_index(), 'cliente_nome', 'valor_total', 'Valor Total (R$)'), use_container_width=True)
        st.divider()
        
        if per == "Dia": 
            df_plot = df.groupby(df['Data'].dt.strftime('%d/%m/%Y'))
        else:
            r = {"Semana": "W-MON", "Mês": "ME", "Ano": "YE"}[per]
            df_plot = df.set_index('Data').resample(r)
        
        df_vendas = df_plot['valor_total'].sum().reset_index()
        col_x = 'Data' if per != "Dia" else 'Data'
        st.subheader("📊 Total de Vendas (Orçamentos Gerados)")
        st.altair_chart(criar_grafico_profissional(df_vendas, col_x, 'valor_total', 'Valor Total Orçado (R$)'), use_container_width=True)
        st.divider()
        
        df_pago = df[df['pago'] == True].groupby(df['Data'].dt.strftime('%d/%m/%Y') if per == "Dia" else df.set_index('Data').resample(r).groups)['valor_total'].sum().reset_index() if per == "Dia" else df[df['pago'] == True].set_index('Data').resample(r)['valor_total'].sum().reset_index()
        st.subheader("💰 Total Recebido (Valores Efetivamente PAGOS)")
        st.altair_chart(criar_grafico_profissional(df_pago, 'Data' if per != "Dia" else 'Data', 'valor_total', 'Total em Caixa (R$)'), use_container_width=True)
        st.divider()
        
        df_prop = df.groupby(df['Data'].dt.strftime('%d/%m/%Y'))['numero_proposta'].count().reset_index() if per == "Dia" else df.set_index('Data').resample(r)['numero_proposta'].count().reset_index()
        st.subheader("📝 Volume de Propostas Geradas")
        st.altair_chart(criar_grafico_profissional(df_prop, 'Data' if per != "Dia" else 'Data', 'numero_proposta', 'Quantidade de Propostas'), use_container_width=True)
