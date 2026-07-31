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

# --- FUNÇÕES AUXILIARES ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

# [Manter aqui as funções carregar_historico, salvar_historico_completo, alternar_status, excluir_proposta idênticas às suas]

def gerar_html(prop):
    subtotal = sum(i.get('quantidade', 0) * i.get('valor_unitario', 0) for i in prop.get('itens', []))
    total = prop.get('valor_total', subtotal)
    desconto = subtotal - total
    logo_base64 = get_image_base64("logo.png")
    pix_base64 = get_image_base64("pix.png")
    
    itens_html = ""
    for item in prop.get('itens', []):
        sub_item = item.get('quantidade', 0) * item.get('valor_unitario', 0)
        itens_html += f"""
        <tr>
            <td><strong>{item.get('produto', '')}</strong><br><small>{item.get('especificacoes', '')}</small></td>
            <td>{item.get('quantidade', 0)}</td>
            <td>R$ {item.get('valor_unitario', 0):.2f}</td>
            <td>R$ {sub_item:.2f}</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <style>
            body {{ font-family: sans-serif; padding: 20px; color: #333; }}
            .container {{ max-width: 800px; margin: auto; border: 1px solid #ddd; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #1e293b; padding-bottom: 10px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; padding: 10px; background: #f1f5f9; }}
            .info-item label {{ font-size: 10px; font-weight: bold; color: #1e293b; text-transform: uppercase; display: block; }}
            .info-item span {{ font-size: 13px; font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #1e293b; color: white; padding: 8px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .resumo {{ text-align: right; margin-top: 20px; font-weight: bold; color: #1e293b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div><img src="data:image/png;base64,{logo_base64}" style="max-width: 120px;"></div>
                <div style="font-size: 10px; text-align: right;">Emissão: {prop.get('data_geracao', 'N/A')}</div>
            </div>
            <h2>PROPOSTA {prop.get('numero_proposta', '')}</h2>
            <div class="info-grid">
                <div class="info-item"><label>Cliente</label><span>{prop.get('cliente_nome', 'N/A')}</span></div>
                <div class="info-item"><label>WhatsApp</label><span>{prop.get('whatsapp', 'Não informado')}</span></div>
                <div class="info-item"><label>CPF/CNPJ</label><span>{prop.get('documento', 'Não informado')}</span></div>
                <div class="info-item"><label>Entrega</label><span>{prop.get('data_entrega', 'N/A')}</span></div>
            </div>
            <table>
                <thead><tr><th>ITEM</th><th>QTD</th><th>SUBTOTAL</th></tr></thead>
                <tbody>{itens_html}</tbody>
            </table>
            <div class="resumo">
                <p>Subtotal: R$ {subtotal:.2f}</p>
                <p>Desconto: R$ {desconto:.2f}</p>
                <p>VALOR TOTAL: R$ {total:.2f}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html
