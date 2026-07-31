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

# --- INICIALIZAÇÃO DE SEGURANÇA ---
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "temp_itens" not in st.session_state:
    st.session_state.temp_itens = []


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    return ""


def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def salvar_historico_completo(historico):
    if historico is None:
        return
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)


def alternar_status(num_proposta, campo, novo_valor):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = novo_valor
    salvar_historico_completo(historico)


def excluir_proposta(num_proposta):
    historico = [p for p in carregar_historico() if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico)
    st.rerun()


# ============================================================
# GERAÇÃO DO HTML DA PROPOSTA
# ============================================================

def gerar_html(prop):
    subtotal = sum(i.get("quantidade", 0) * i.get("valor_unitario", 0) for i in prop.get("itens", []))
    total = prop.get("valor_total", subtotal)
    desconto = subtotal - total
    logo_base64 = get_image_base64("logo.png")
    pix_base64 = get_image_base64("pix.png")
    
    itens_html = ""
    for item in prop.get("itens", []):
        sub_item = (item.get("quantidade", 0) * item.get("valor_unitario", 0))
        itens_html += f"""
        <tr>
            <td><strong>{item.get('produto', '')}</strong><br><small>{item.get('especificacoes', '')}</small></td>
            <td>{item.get('quantidade', 0)}</td>
            <td>R$ {item.get('valor_unitario', 0):.2f}</td>
            <td>R$ {sub_item:.2f}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
    <html lang="pt-br">
    <head><meta charset="utf-8"><style>body{{font-family:sans-serif;padding:20px;color:#333}}.container{{max-width:800px;margin:auto;border:1px solid #ccc;padding:20px}}.header{{display:flex;justify-content:space-between;align-items:start;border-bottom:2px solid #1e293b;margin-bottom:20px;padding-bottom:10px}}.header-info{{text-align:right;font-size:10px;line-height:1.4}}.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin:20px 0;padding:10px;background:#f1f5f9}}.info-item label{{font-weight:bold;text-transform:uppercase;display:block}}.resumo{{text-align:right;margin-top:20px;font-weight:bold}}.pix-section{{display:flex;align-items:start;gap:20px;margin-top:15px}}</style></head>
    <body><div class="container"><div class="header"><div><img src="data:image/png;base64,{logo_base64}" style="max-width:150px;"></div><div class="header-info"><strong>Alphafest Itatiba</strong><br>CNPJ - 24.374.857/0001-30<br>Emissão: {prop.get('data_geracao', 'N/A')}</div></div>
    <h2>PROPOSTA {prop.get('numero_proposta', '')}</h2>
    <div class="info-grid"><div class="info-item"><label>Cliente</label><span>{prop.get('cliente_nome', 'N/A')}</span></div><div class="info-item"><label>Data Entrega</label><span>{prop.get('data_entrega', 'N/A')}</span></div></div>
    <table><thead><tr><th>ITEM</th><th>QTD</th><th>UNIT.</th><th>TOTAL</th></tr></thead><tbody>{itens_html}</tbody></table>
    <div class="resumo"><p>Total: R$ {total:.2f}</p></div></div></body></html>"""


# ============================================================
# MENSAGEM WHATSAPP
# ============================================================

def formatar_msg_whatsapp(prop):
    total = prop.get("valor_total", 0)
    itens_str = "\n".join([f"{i.get('quantidade', 0)} {i.get('produto', '')} - R${i.get('valor_unitario', 0):.2f}" for i in prop.get("itens", [])])
    return f"*PROPOSTA ALPHAFEST ITATIBA*\n*Cliente:* {prop.get('cliente_nome', '')}\n\n*Itens:*\n{itens_str}\n\n*Total:* R$ {total:.2f}"


# ============================================================
# GRÁFICO PROFISSIONAL
# ============================================================

def criar_grafico_profissional(df, x_col, y_col, titulo, ordenar=False):
    if df.empty: return None
    if ordenar: df = df.sort_values(y_col, ascending=False)
    chart = alt.Chart(df).mark_bar(color="#2e86de").encode(
        x=alt.X(f"{x_col}:O", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f"{y_col}:Q", axis=None),
        tooltip=[x_col, y_col]
    ).properties(title=titulo, height=350)
    return chart


# ============================================================
# INTERFACE PRINCIPAL
# ============================================================

st.title("📄 ORÇAMENTOS ALPHAFEST")

# ... (O restante da lógica segue o mesmo padrão de organização)
