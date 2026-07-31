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
    html = f"<h1>Orçamento {prop['numero_proposta']}</h1><p>Cliente: {prop['cliente_nome']}</p><ul>"
    for item in prop['itens']:
        html += f"<li>{item['produto']} - Qtd: {item['quantidade']}</li>"
    html += "</ul><h3>Total: R$ {:.2f}</h3>".format(prop['valor_total'])
    return html

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

# --- ALERTAS ---
hoje = date.today()
for p in carregar_historico():
    try:
        data_entrega = datetime.strptime(p.get("data_entrega", ""), "%d/%m/%Y").date()
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
                "cliente_nome": nome, "itens": list(st.session_state.temp_itens),
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
            for item in prop.get('itens', []): st.write(f"• {item['produto']} (Qtd: {item['quantidade']})")
            
            # BOTÕES DE AÇÃO RESTAURADOS
            c1, c2 = st.columns(2)
            msg_zap = f"Olá {prop['cliente_nome']}, seu orçamento {num_p} está pronto!"
            c1.link_button("📱 Enviar WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg_zap)}")
            c2.download_button("📄 Gerar HTML", gerar_html(prop), file_name=f"{num_p}.html")
            
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{num_p}", on_change=alternar_status, args=(num_p, "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{num_p}", on_change=alternar_status, args=(num_p, "entregue", not prop.get("entregue", False)))
            if st.button("🗑️ Excluir", key=f"del_{num_p}"): excluir_proposta(num_p)

with aba3:
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        df['valor_total'] = df.apply(lambda row: sum(i['quantidade'] * i['valor_unitario'] for i in row['itens']) if (pd.isna(row.get('valor_total')) or row.get('valor_total') == 0) else row['valor_total'], axis=1)
        df['Data'] = pd.to_datetime(df['data_geracao'], dayfirst=True)
        
        per = st.selectbox("Período de Agrupamento", ["Dia", "Semana", "Mês", "Ano"], key="per_rel")
        
        st.subheader("👥 Total por Cliente")
        st.altair_chart(criar_grafico_profissional(df.groupby('cliente_nome')['valor_total'].sum().reset_index(), 'cliente_nome', 'valor_total', 'Valor Total (R$)'), use_container_width=True)
        st.divider()
        
        if per == "Dia": df_plot = df.groupby(df['Data'].dt.strftime('%d/%m/%Y'))
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
