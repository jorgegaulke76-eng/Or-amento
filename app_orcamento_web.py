import streamlit as st
import base64
import os
import re
import json
import urllib.parse
import pandas as pd
from datetime import datetime, date, timedelta
import altair as alt # Adicionado para permitir rótulos nos gráficos

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO ---
if "form_key" not in st.session_state: 
    st.session_state.form_key = 0
if "itens" not in st.session_state: 
    st.session_state.itens = []
if "ultima_proposta" not in st.session_state: 
    st.session_state.ultima_proposta = None
if "target_prop" not in st.session_state: 
    st.session_state.target_prop = None

# --- FUNÇÕES DE APOIO ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: 
                return json.load(f)
        except: 
            return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    salvar_historico_completo(historico)

def alternar_status(num_proposta, campo, novo_valor):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = novo_valor
            break
    salvar_historico_completo(historico)

def atualizar_data_proposta(num_proposta, nova_data):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p["data_geracao"] = nova_data
            break
    salvar_historico_completo(historico)

def excluir_proposta_por_id(num_proposta):
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

# Função auxiliar para criar gráficos com labels (Altair)
def criar_grafico_com_labels(df, x_col, y_col, titulo):
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f'{x_col}:O', title=x_col),
        y=alt.Y(f'{y_col}:Q', title=y_col),
        tooltip=[x_col, y_col]
    ).properties(title=titulo)
    
    text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(text=y_col)
    return chart + text

# ... (funções extrair_link_whatsapp_completo e gerar_proposta_html permanecem iguais) ...
# [MANTIVE AS FUNÇÕES ANTERIORES AQUI PARA O SCRIPT FUNCIONAR]
def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): 
        num_wa = "55" + num_wa
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc_v = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - desc_v)
    texto_itens = ""
    for idx, item in enumerate(dados["itens"], 1):
        sub_item = item["quantidade"] * item["valor_unitario"]
        texto_itens += f"  *{idx}. {item['produto']}*\n"
        if item.get('especificacoes'): 
            texto_itens += f"      └ Detalhes: {item['especificacoes']}\n"
        texto_itens += f"      └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f} | Subtotal: R$ {sub_item:.2f}\n\n"
    msg = (f"🔥 *PROPOSTA ALPHAFEST ITATIBA*\n📄 *Nº:* {dados['numero_proposta']}\n🗓️ *Emissão:* {dados.get('data_geracao', '')}\n\n"
           f"👤 *CLIENTE:* {dados['cliente_nome']}\n🪪 *CPF/CNPJ:* {dados.get('cliente_cpf_cnpj', 'Não informado')}\n"
           f"-----------------------------------\n📦 *ITENS DO PEDIDO:*\n\n{texto_itens}-----------------------------------\n"
           f"💵 *Subtotal:* R$ {subtotal_geral:.2f}\n🏷️ *Desconto:* - R$ {desc_v:.2f}\n✅ *VALOR TOTAL DO PEDIDO:* R$ {total_final:.2f}\n"
           f"-----------------------------------\n📅 *Previsão de Entrega:* {dados.get('data_entrega', 'A combinar')}\n"
           f"⏳ *Prazo de Produção:* {dados.get('prazo_dias', '10')} dias úteis\n🚚 *Frete/Entrega:* {dados.get('frete_tipo', 'Retirada em Itatiba')}\n"
           f"⏰ *Validade:* 5 dias corridos\n\n💳 *PAGAMENTO VIA PIX:*\n👉 *Clique no link para pagar:* {LINK_PIX_OFICIAL}\n\n"
           f"• *Titular:* Ana Lúcia Zepelini | *Banco:* Cora SCD (403)\n• *Agência:* 0001 | *Conta:* 2515972-5\n"
           f"• *Empresa:* ANA LUCIA VIEIRA ZEPELINI 29480359880\n\n"
           f"👇 *Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido ! 🥰*")
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    return f"https://wa.me/{num_wa}?text={msg_enc}" if num_wa and len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={msg_enc}"

def gerar_proposta_html(dados):
    linhas = "".join([f"<tr><td><strong>{i['produto']}</strong><br><small>{i['especificacoes']}</small></td><td>{i['quantidade']} un.</td><td>R$ {i['valor_unitario']:.2f}</td><td>R$ {(i['quantidade']*i['valor_unitario']):.2f}</td></tr>" for i in dados["itens"]])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{{font-family:sans-serif; padding:20px;}} table{{width:100%; border-collapse:collapse;}} th{{background:#334155; color:white; padding:10px;}} td{{padding:10px; border-bottom:1px solid #ddd;}}</style></head><body><h2>Proposta {dados['numero_proposta']}</h2><div style="background:#f1f5f9; padding:10px;"><b>Cliente:</b> {dados['cliente_nome']}</div><table><thead><tr><th>ITEM</th><th>QTD</th><th>UNIT.</th><th>TOTAL</th></tr></thead><tbody>{linhas}</tbody></table><div style="text-align:right; font-weight:bold;">TOTAL: R$ {(sum(i['quantidade']*i['valor_unitario'] for i in dados['itens']) - dados.get('desconto_valor', 0)):.2f}</div></body></html>"""

# --- INTERFACE ---
if os.path.exists(PATH_LOGO_OFICIAL):
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2: 
        st.image(PATH_LOGO_OFICIAL, use_container_width=True)

st.title("📄 ORÇAMENTOS ALPHAFEST")

# --- ALERTA DE ENTREGA (CORRIGIDO) ---
hoje = date.today().strftime("%d/%m/%Y")
entregas = [p for p in carregar_historico() if p.get("data_entrega") == hoje and not p.get("entregue")]
for p in entregas:
    if st.button(f"⚠️ ENTREGA HOJE: {p['numero_proposta']} - Cliente: {p['cliente_nome']}"):
        st.session_state.target_prop = p['numero_proposta']
        st.rerun()

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

# --- ABA 1, 2 (Omitidas por brevidade, permanecem iguais) ---
# [O código das abas 1 e 2 continua como você enviou]

# --- ABA 3: RELATÓRIOS (COM GRÁFICOS MELHORADOS) ---
with aba3:
    st.subheader("📊 Relatórios Detalhados")
    h = carregar_historico()
    if h:
        # ... (lógica de preparação dos dados continua igual até o gráfico)
        props_unicas = []
        itens_lista = []
        for p in h:
            val_total = sum(i['quantidade'] * i['valor_unitario'] for i in p['itens']) - p.get('desconto_valor', 0)
            dt = pd.to_datetime(p['data_geracao'], dayfirst=True)
            props_unicas.append({'Data': dt, 'Proposta': p['numero_proposta'], 'Cliente': p['cliente_nome'], 'Valor': max(0.0, val_total), 'Pago': p.get('pago', False)})
            for it in p['itens']:
                itens_lista.append({'Data': dt, 'Cliente': p['cliente_nome'], 'Produto': it['produto'], 'Qtd': it['quantidade'], 'Pago': p.get('pago', False)})
        
        df_props = pd.DataFrame(props_unicas)
        df_itens = pd.DataFrame(itens_lista)
        periodo = st.selectbox("Selecione o Período de Agrupamento", ["Dia", "Semana", "Mês", "Ano"])
        resample_rule = {"Dia": "D", "Semana": "W-MON", "Mês": "ME", "Ano": "YE"}[periodo]
        format_str = {"Dia": "%d/%m/%Y", "Semana": "Semana %W (%Y)", "Mês": "%m/%Y", "Ano": "%Y"}[periodo]

        # Vendas
        st.subheader(f"💰 Valor de Vendas por {periodo}")
        df_vendas = df_props.set_index('Data').resample(resample_rule)['Valor'].sum().reset_index()
        df_vendas['Data_Fmt'] = df_vendas['Data'].dt.strftime(format_str)
        st.altair_chart(criar_grafico_com_labels(df_vendas, 'Data_Fmt', 'Valor', 'Vendas (R$)'), use_container_width=True)

        # Clientes
        st.subheader("👥 Total de Compras por Cliente")
        df_cli = df_props.groupby('Cliente')['Proposta'].count().reset_index()
        st.altair_chart(criar_grafico_com_labels(df_cli, 'Cliente', 'Proposta', 'Nº de Propostas'), use_container_width=True)

        # Pagas
        st.subheader(f"✅ Propostas Pagas por {periodo}")
        df_pagas = df_props[df_props['Pago'] == True].set_index('Data').resample(resample_rule)['Proposta'].count().reset_index()
        if not df_pagas.empty:
            df_pagas['Data_Fmt'] = df_pagas['Data'].dt.strftime(format_str)
            st.altair_chart(criar_grafico_com_labels(df_pagas, 'Data_Fmt', 'Proposta', 'Qtd Propostas Pagas'), use_container_width=True)
        else:
            st.info("Nenhuma proposta paga registrada.")

        # Produtos
        st.subheader("📦 Produtos Mais Vendidos")
        df_prod = df_itens.groupby('Produto')['Qtd'].sum().reset_index()
        st.altair_chart(criar_grafico_com_labels(df_prod, 'Produto', 'Qtd', 'Quantidade Total'), use_container_width=True)
