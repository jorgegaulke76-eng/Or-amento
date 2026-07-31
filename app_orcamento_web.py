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

# --- FUNÇÃO GERAR HTML CORRIGIDA COM SEU DESIGN ---
def gerar_html(prop):
    total = prop.get('valor_total', 0)
    # Calculando subtotal para exibir o resumo
    subtotal_calculado = sum(i.get('quantidade',0) * i.get('valor_unitario',0) for i in prop.get('itens',[]))
    if total == 0: total = subtotal_calculado
    desconto = subtotal_calculado - total
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; border: 1px solid #ccc; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: start; border-bottom: 2px solid #333; margin-bottom: 20px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; padding: 10px; background: #f9f9f9; border: 1px solid #ddd; }}
            .info-item label {{ font-size: 10px; font-weight: bold; color: #555; text-transform: uppercase; display: block; }}
            .info-item span {{ font-size: 13px; font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #333; color: white; padding: 8px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .resumo {{ text-align: right; margin-top: 20px; font-size: 14px; }}
            .footer {{ margin-top: 30px; font-size: 11px; border-top: 1px solid #ddd; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div><h1>ALPHAFEST</h1></div>
                <div style="text-align: right; font-size: 12px;">Emissão: {prop.get('data_geracao', 'N/A')}</div>
            </div>
            <h3>PROPOSTA {prop['numero_proposta']}</h3>
            
            <div class="info-grid">
                <div class="info-item"><label>Cliente / Empresa</label><span>{prop.get('cliente_nome', 'N/A')}</span></div>
                <div class="info-item"><label>CPF / CNPJ</label><span>{prop.get('documento', 'Não informado')}</span></div>
                <div class="info-item"><label>WhatsApp / Contato</label><span>{prop.get('whatsapp', 'Não informado')}</span></div>
                <div class="info-item"><label>Data Prevista de Entrega</label><span>{prop.get('data_entrega', 'N/A')}</span></div>
            </div>

            <table>
                <thead><tr><th>ITEM / DESCRIÇÃO</th><th>QTD</th><th>UNIT.</th><th>SUBTOTAL</th></tr></thead>
                <tbody>
    """
    for item in prop.get('itens', []):
        subtotal = item.get('quantidade', 0) * item.get('valor_unitario', 0)
        html += f"<tr><td>{item.get('produto', '')}<br><small>{item.get('especificacoes', '')}</small></td><td>{item.get('quantidade', 0)}</td><td>R$ {item.get('valor_unitario', 0):.2f}</td><td>R$ {subtotal:.2f}</td></tr>"
    
    html += f"""
                </tbody>
            </table>
            <div class="resumo">
                <p>Subtotal: R$ {subtotal_calculado:.2f}</p>
                <p>Desconto: R$ {desconto:.2f}</p>
                <p><strong>VALOR TOTAL DO PEDIDO: R$ {total:.2f}</strong></p>
            </div>
            <div class="footer">
                <p><strong>Condições de Produção & Pagamento:</strong><br>
                Titular: Ana Lúcia Zepelini | Conta: 2515972-5<br>
                Prazo de Produção: 1 dia útil | Validade: 5 dias corridos.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# ... (MANTENDO O RESTANTE DO SEU CÓDIGO ORIGINAL IDÊNTICO) ...
# [Cole aqui o restante do seu código original, a partir da função 'formatar_msg_whatsapp' até o final]
