import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
import altair as alt

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", layout="wide")
ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- FUNÇÕES DE APOIO ---
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

def criar_grafico_com_labels(df, x_col, y_col, titulo):
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f'{x_col}:O', title=x_col),
        y=alt.Y(f'{y_col}:Q', title=y_col),
        tooltip=[x_col, y_col]
    ).properties(title=titulo, height=300)
    text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(text=y_col)
    return chart + text

# --- SIDEBAR: BACKUP ---
with st.sidebar:
    st.header("⚙️ Painel de Segurança")
    st.info("⚠️ Baixe o backup após cada alteração.")
    h_atual = carregar_historico()
    if h_atual:
        st.download_button("💾 BAIXAR BACKUP", data=json.dumps(h_atual, ensure_ascii=False), file_name="backup_historico.json", mime="application/json", type="primary", use_container_width=True)

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios & Gráficos"])

with aba1:
    # (Formulário completo original)
    fk = st.session_state.get("form_key", 0)
    nome = st.text_input("Nome / Razão Social", key=f"c_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF / CNPJ", key=f"d_{fk}")
    wa = c2.text_input("WhatsApp", key=f"w_{fk}")
    
    prod = st.text_input("Produto", key=f"p_{fk}")
    with st.expander("🎨 Personalização"):
        c1, c2 = st.columns(2)
        et = c1.text_input("Tema", key=f"et_{fk}")
        en = c1.text_input("Nome", key=f"en_{fk}")
        ec = c1.text_input("Cor", key=f"ec_{fk}")
        ei = c2.text_input("Idade", key=f"ei_{fk}")
    
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário (R$)", value=0.0, step=0.5, key=f"v_{fk}")
    
    if st.button("➕ Adicionar Item"):
        if "itens" not in st.session_state: st.session_state.itens = []
        st.session_state.itens.append({"produto": prod, "especificacoes": f"{et}/{en}", "quantidade": q, "valor_unitario": v})
        st.rerun()

    if "itens" in st.session_state and st.session_state.itens:
        st.dataframe(pd.DataFrame(st.session_state.itens))
        if st.button("🚀 SALVAR PROPOSTA"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "cliente_nome": nome, "itens": list(st.session_state.itens),
                "valor_total": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.itens),
                "pago": False, "entregue": False
            }
            salvar_no_historico(dados)
            st.session_state.itens = []
            st.session_state.form_key += 1
            st.rerun()

with aba2:
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']}"):
            pago = st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}", on_change=alternar_status, args=(prop['numero_proposta'], "pago", not prop.get("pago", False)))
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"):
                excluir_proposta_por_id(prop['numero_proposta'])
                st.rerun()

with aba3:
    st.subheader("📊 Relatórios Detalhados")
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        df['Data'] = pd.to_datetime(df['data_geracao'], dayfirst=True)
        
        # Periodo
        periodo = st.selectbox("Selecione o Período", ["Dia", "Semana", "Mês", "Ano"])
        resample_rule = {"Dia": "D", "Semana": "W-MON", "Mês": "ME", "Ano": "YE"}[periodo]
        
        # 1. Por Clientes (Total)
        st.subheader("👥 Total de Pedidos por Cliente")
        st.altair_chart(criar_grafico_com_labels(df.groupby('cliente_nome')['numero_proposta'].count().reset_index(), 'cliente_nome', 'numero_proposta', 'Qtd Pedidos'), use_container_width=True)

        # 2. Valor Pago por Periodo
        st.subheader(f"💰 Valor Total (R$) por {periodo}")
        df_val = df.set_index('Data').resample(resample_rule)['valor_total'].sum().reset_index()
        df_val['Data_Fmt'] = df_val['Data'].dt.strftime('%d/%m/%Y' if periodo=='Dia' else '%m/%Y')
        st.altair_chart(criar_grafico_com_labels(df_val, 'Data_Fmt', 'valor_total', 'Valor Total'), use_container_width=True)

        # 3. Propostas por Periodo
        st.subheader(f"📝 Propostas Geradas por {periodo}")
        df_prop = df.set_index('Data').resample(resample_rule)['numero_proposta'].count().reset_index()
        df_prop['Data_Fmt'] = df_prop['Data'].dt.strftime('%d/%m/%Y' if periodo=='Dia' else '%m/%Y')
        st.altair_chart(criar_grafico_com_labels(df_prop, 'Data_Fmt', 'numero_proposta', 'Qtd Propostas'), use_container_width=True)

        # 4. Produtos Vendidos por Periodo
        st.subheader(f"📦 Quantidade de Produtos por {periodo}")
        # Explodir itens para calcular
        lista_exp = []
        for p in h:
            for item in p['itens']:
                lista_exp.append({'Data': pd.to_datetime(p['data_geracao'], dayfirst=True), 'produto': item['produto'], 'quantidade': item['quantidade']})
        df_exp = pd.DataFrame(lista_exp)
        df_prod = df_exp.set_index('Data').resample(resample_rule)['quantidade'].sum().reset_index()
        df_prod['Data_Fmt'] = df_prod['Data'].dt.strftime('%d/%m/%Y' if periodo=='Dia' else '%m/%Y')
        st.altair_chart(criar_grafico_com_labels(df_prod, 'Data_Fmt', 'quantidade', 'Total Produtos'), use_container_width=True)
