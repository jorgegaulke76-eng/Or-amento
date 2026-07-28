import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Orçamentos | Alphafest", page_icon="📝", layout="centered")

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

# --- FUNÇÕES DE LAYOUT (FORMATO ALPHA FEST) ---
def gerar_proposta_html(dados):
    linhas_tabela = ""
    subtotal_geral = 0.0
    for item in dados["itens"]:
        sub = item["Qtd"] * item["Valor Unit."]
        subtotal_geral += sub
        linhas_tabela += f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{item['Produto']}<br><small>{item['Detalhes']}</small></td>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{item['Qtd']} un.</td>
            <td style="padding:8px; border-bottom:1px solid #ddd;">R$ {item['Valor Unit.']:.2f}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd;">R$ {sub:.2f}</td>
        </tr>"""
    
    total = max(0, subtotal_geral - dados.get('desconto_valor', 0))
    
    return f"""
    <html>
    <body style="font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px; border: 1px solid #ccc;">
        <div style="border-bottom: 2px solid #000; padding-bottom: 10px;">
            <h2 style="margin:0;">ALPHAFEST ITATIBA</h2>
            <p style="margin:0; font-size: 0.9em;">CNPJ: 24.374.857/0001-30 | Av. Manoel Verginio de Almeida, 442 - Alto Santa Cruz - Itatiba - SP</p>
        </div>
        <div style="background: #333; color: #fff; padding: 10px; margin-top: 10px;"><b>PROPOSTA</b> Nº {dados['numero_proposta']}</div>
        <div style="padding: 10px; border-bottom: 1px solid #ccc;">
            <b>CLIENTE:</b> {dados['cliente_nome']} | <b>CPF/CNPJ:</b> {dados['cliente_cpf_cnpj']}<br>
            <b>DATA PREVISTA:</b> {dados['data_entrega']}
        </div>
        <table style="width:100%; border-collapse:collapse; margin-top:15px;">
            <thead><tr style="background:#f4f4f4;"><th>ITEM / DESCRIÇÃO</th><th>QTD</th><th>VALOR UNIT.</th><th>SUBTOTAL</th></tr></thead>
            <tbody>{linhas_tabela}</tbody>
        </table>
        <div style="text-align:right; margin-top:15px;">
            <p>Subtotal: R$ {subtotal_geral:.2f}</p>
            <p>Desconto: R$ {dados['desconto_valor']:.2f}</p>
            <h3 style="color:green;">VALOR TOTAL: R$ {total:.2f}</h3>
        </div>
        <div style="border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px;">
            <b>PIX:</b> Titular: Ana Lucia Zepelini | Banco: Cora SCD (403) | Ag: 0001 | Conta: 2515972-5<br>
            <i>Somente após realizado pagamento e envio de comprovante daremos seguimento ao pedido!</i>
        </div>
    </body>
    </html>
    """

def formatar_mensagem_whatsapp(dados):
    subtotal_geral = sum(item["Qtd"] * item["Valor Unit."] for item in dados["itens"])
    total = max(0, subtotal_geral - dados.get('desconto_valor', 0))
    
    lista_itens = ""
    for i, item in enumerate(dados["itens"], 1):
        sub = item["Qtd"] * item["Valor Unit."]
        lista_itens += f"{i}. {item['Produto']}\n└ Detalhes: {item['Detalhes']}\n└ Qtd: {item['Qtd']} un. | Unit: R$ {item['Valor Unit.']:.2f} | Sub: R$ {sub:.2f}\n"

    msg = f"""🔥 *PROPOSTA ALPHAFEST ITATIBA*
Nº: {dados['numero_proposta']}
Emissão: {dados['data_geracao']}

👤 *CLIENTE:* {dados['cliente_nome']}
CPF/CNPJ: {dados['cliente_cpf_cnpj']}

📦 *ITENS DO PEDIDO:*
{lista_itens}
---
💰 *Subtotal:* R$ {subtotal_geral:.2f}
📉 *Desconto:* R$ {dados['desconto_valor']:.2f}
✅ *VALOR TOTAL:* R$ {total:.2f}

🚚 *Previsão de Entrega:* {dados['data_entrega']}
🛠 *Prazo de Produção:* 10 dias úteis
📍 *Frete:* {dados['frete_tipo']}

💳 *PAGAMENTO VIA PIX:*
👉 *Titular:* Ana Lúcia Zepelini
👉 *Banco:* Cora SCD (403) | Ag: 0001 | Conta: 2515972-5

👇 Somente após realizado pagamento e envio de comprovante daremos seguimento ao pedido! 😍"""
    
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    return f"https://wa.me/{num_wa if len(num_wa)>10 else '55'+num_wa}?text={urllib.parse.quote(msg)}"

# --- INTERFACE ---
if "itens" not in st.session_state: st.session_state.itens = []
if "previa_dados" not in st.session_state: st.session_state.previa_dados = None

st.title("📝 Orçamentos Alphafest")

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
        st.session_state.previa_dados = {
            "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}", 
            "data_geracao": datetime.now().strftime("%d/%m/%Y"),
            "data_entrega": entrega.strftime("%d/%m/%Y"), 
            "cliente_nome": st.session_state.c_nome,
            "cliente_cpf_cnpj": st.session_state.c_cpf, 
            "cliente_wa": st.session_state.c_wa,
            "itens": st.session_state.itens, 
            "desconto_valor": desc, 
            "prazo_dias": "10", 
            "frete_tipo": "Retirada em Itatiba"
        }
        st.rerun()

if st.session_state.previa_dados:
    st.success("✅ Prévia gerada com sucesso!")
    c_baixar, c_wa = st.columns(2)
    c_baixar.download_button("📥 Baixar Proposta", gerar_proposta_html(st.session_state.previa_dados), "proposta.html")
    c_wa.link_button("📱 WhatsApp", formatar_mensagem_whatsapp(st.session_state.previa_dados))
    
    if st.button("🚀 CONFIRMAR E SALVAR NO HISTÓRICO"):
        if salvar_no_sheets(st.session_state.previa_dados):
            st.success("Orçamento salvo no Google Sheets!")
            st.session_state.itens = []
            st.session_state.previa_dados = None
            st.rerun()
