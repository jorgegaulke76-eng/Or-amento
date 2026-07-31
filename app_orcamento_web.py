import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import altair as alt

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamento Alphafest", layout="wide")
ARQUIVO_HISTORICO = "historico_orcamentos.json"

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
    st.rerun()

def excluir_proposta(num_proposta):
    historico = [p for p in carregar_historico() if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico)
    st.rerun()

def criar_grafico_limpo(df, x_col, y_col, titulo):
    # Rotação de -45 graus no eixo X para evitar sobreposição de textos longos
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color='#2e86de').encode(
        x=alt.X(f'{x_col}:O', title="", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f'{y_col}:Q', title="", axis=None),
        tooltip=[x_col, y_col]
    ).properties(title=titulo, height=300)
    text = chart.mark_text(align='center', baseline='bottom', dy=-5, fontWeight='bold', color='#2c3e50').encode(
        text=alt.Text(y_col, format='.0f')
    )
    return (chart + text).configure_view(strokeWidth=0).configure_axis(grid=False)

# --- SIDEBAR: BACKUP ---
with st.sidebar:
    st.header("⚙️ Painel de Segurança")
    h_atual = carregar_historico()
    if h_atual:
        st.download_button("💾 BAIXAR BACKUP", data=json.dumps(h_atual, ensure_ascii=False, indent=4), file_name="backup_historico.json", mime="application/json", type="primary", use_container_width=True)

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios"])

with aba1:
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
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário (R$)", value=0.0, step=0.5, key=f"v_{fk}")
    
    if st.button("➕ Adicionar Item"):
        if "temp_itens" not in st.session_state: st.session_state.temp_itens = []
        st.session_state.temp_itens.append({"produto": prod, "quantidade": q, "valor_unitario": v})
        st.rerun()

    if "temp_itens" in st.session_state and st.session_state.temp_itens:
        st.dataframe(pd.DataFrame(st.session_state.temp_itens))
        if st.button("🚀 SALVAR PROPOSTA"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "cliente_nome": nome, "itens": list(st.session_state.temp_itens),
                "valor_total": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens),
                "pago": False, "entregue": False
            }
            h = carregar_historico()
            h.insert(0, dados)
            salvar_historico_completo(h)
            st.session_state.temp_itens = []
            st.rerun()

with aba2:
    for prop in carregar_historico():
        num_p = prop['numero_proposta']
        with st.expander(f"{num_p} - {prop['cliente_nome']}"):
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{num_p}", on_change=alternar_status, args=(num_p, "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{num_p}", on_change=alternar_status, args=(num_p, "entregue", not prop.get("entregue", False)))
            if st.button("🗑️ Excluir", key=f"del_{num_p}"): excluir_proposta(num_p)

with aba3:
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        df['Data'] = pd.to_datetime(df['data_geracao'], dayfirst=True)
        if 'valor_total' not in df.columns: df['valor_total'] = df['itens'].apply(lambda itens: sum(i['quantidade'] * i['valor_unitario'] for i in itens))
        
        per = st.selectbox("Selecione o Período", ["Dia", "Semana", "Mês", "Ano"])
        r = {"Dia": "D", "Semana": "W-MON", "Mês": "ME", "Ano": "YE"}[per]
        
        # --- SEÇÃO 1: CLIENTES ---
        st.subheader("👥 Desempenho por Cliente")
        st.altair_chart(criar_grafico_limpo(df.groupby('cliente_nome')['valor_total'].sum().reset_index(), 'cliente_nome', 'valor_total', 'Valor Total (R$)'), use_container_width=True)
        st.divider()

        # --- SEÇÃO 2: FINANCEIRO ---
        st.subheader("💰 Faturamento (Valor Pago)")
        st.altair_chart(criar_grafico_limpo(df.set_index('Data').resample(r)['valor_total'].sum().reset_index(), 'Data', 'valor_total', 'Valor Total (R$)'), use_container_width=True)
        st.divider()

        # --- SEÇÃO 3: OPERACIONAL ---
        st.subheader("📝 Volume de Propostas Geradas")
        st.altair_chart(criar_grafico_limpo(df.set_index('Data').resample(r)['numero_proposta'].count().reset_index(), 'Data', 'numero_proposta', 'Qtd de Propostas'), use_container_width=True)
        st.divider()

        # --- SEÇÃO 4: PRODUTOS ---
        st.subheader("📦 Produtos Mais Vendidos")
        df_exp = pd.DataFrame([{'produto': it['produto'], 'qtd': it['quantidade']} for p in h for it in p['itens']])
        st.altair_chart(criar_grafico_limpo(df_exp.groupby('produto')['qtd'].sum().reset_index(), 'produto', 'qtd', 'Total Vendido (Qtd)'), use_container_width=True)
