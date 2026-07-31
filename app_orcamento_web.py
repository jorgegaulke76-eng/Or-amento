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
        if p.get("numero_proposta") == num_p: p[campo] = novo_valor # Corrigido aqui
    salvar_historico_completo(historico)

def excluir_proposta(num_proposta):
    historico = [p for p in carregar_historico() if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico)
    st.rerun()

def gerar_html(prop):
    # Segurança para calcular valor se não existir
    total = prop.get('valor_total', 0)
    if total == 0: total = sum(i.get('quantidade',0) * i.get('valor_unitario',0) for i in prop.get('itens',[]))
    html = f"<h1>Orçamento {prop['numero_proposta']}</h1><p>Cliente: {prop['cliente_nome']}</p><ul>"
    for item in prop['itens']:
        html += f"<li>{item['produto']} - Qtd: {item['quantidade']}</li>"
    html += "</ul><h3>Total: R$ {:.2f}</h3>".format(total)
    return html

def formatar_msg_whatsapp(prop):
    # SEGURANÇA TOTAL: Calcula o valor total se a chave não existir
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
*CPF/CNPJ:* 
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
*Clique no link para pagar:* https://linkspix.app/alphafestitatiba

* Titular: Ana Lúcia Zepelini | *Banco:* Cora SCD (403)
* Agência: 0001 | *Conta:* 2515972-5
* Empresa: ANA LUCIA VIEIRA ZEPELINI 29480359880

*Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido !"""
    return msg

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico", "📊 Relatórios"])

with aba1:
    fk = st.session_state.form_key
    nome = st.text_input("Nome / Razão Social", key=f"c_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF / CNPJ", key=f"d_{fk}")
    wa = c2.text_input("WhatsApp", key=f"w_{fk}")
    prod = st.text_input("Produto", key=f"p_{fk}")
    with st.expander("🎨 Personalização", expanded=True):
        c1, c2 = st.columns(2)
        et = c1.text_input("Tema", key=f"et_{fk}")
        en = c1.text_input("Nome", key=f"en_{fk}")
    q = st.number_input("Qtd", min_value=1, value=1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário (R$)", value=0.0, step=0.5, key=f"v_{fk}")
    if st.button("➕ Adicionar Item"):
        st.session_state.temp_itens.append({"produto": prod, "quantidade": q, "valor_unitario": v})
        st.rerun()
    if st.session_state.temp_itens:
        st.dataframe(pd.DataFrame(st.session_state.temp_itens))
        dt_entrega = st.date_input("📅 Data Entrega", value=date.today())
        if st.button("🚀 SALVAR PROPOSTA"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "data_entrega": dt_entrega.strftime("%d/%m/%Y"),
                "cliente_nome": nome, "itens": list(st.session_state.temp_itens),
                "valor_total": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens),
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
            c1, c2 = st.columns(2)
            c1.link_button("📱 WhatsApp", f"https://wa.me/?text={urllib.parse.quote(formatar_msg_whatsapp(prop))}")
            c2.download_button("📄 HTML", gerar_html(prop), file_name=f"{num_p}.html")
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{num_p}", on_change=alternar_status, args=(num_p, "pago", not prop.get("pago", False)))
            if st.button("🗑️ Excluir", key=f"del_{num_p}"): excluir_proposta(num_p)
