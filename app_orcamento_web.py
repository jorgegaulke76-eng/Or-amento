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
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "temp_itens" not in st.session_state: st.session_state.temp_itens = []

# --- FUNÇÕES AUXILIARES ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

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
        <meta charset="utf-8">
        <style>
            body {{ font-family: sans-serif; padding: 20px; color: #333; }}
            .container {{ max-width: 800px; margin: auto; border: 1px solid #ccc; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: start; border-bottom: 2px solid #1e293b; margin-bottom: 20px; padding-bottom: 10px; }}
            .header-info {{ text-align: right; font-size: 10px; line-height: 1.4; color: #333; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; padding: 10px; background: #f1f5f9; border: 1px solid #e2e8f0; }}
            .info-item label {{ font-size: 10px; font-weight: bold; color: #1e293b; text-transform: uppercase; display: block; }}
            .info-item span {{ font-size: 13px; font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #1e293b; color: white; padding: 8px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .resumo {{ text-align: right; margin-top: 20px; font-weight: bold; color: #1e293b; }}
            .footer {{ margin-top: 30px; font-size: 11px; border-top: 2px solid #1e293b; padding-top: 10px; }}
            .pix-section {{ display: flex; align-items: start; gap: 20px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div><img src="data:image/png;base64,{logo_base64}" style="max-width: 150px;"></div>
                <div class="header-info">
                    <strong>Alphafest Itatiba</strong><br>
                    CNPJ - 24.374.857/0001-30 | IE - 382105300112<br>
                    Avenida Manoel Verginio de Almeida, 442 - Alto Santa Cruz - Itatiba - SP<br>
                    CEP - 13251-530 | Email - alphafesti@gmail.com<br>
                    Celular - ( 11 ) 9724-9533<br>
                    <strong>Emissão: {prop.get('data_geracao', 'N/A')}</strong>
                </div>
            </div>
            
            <h2 style="color: #1e293b;">PROPOSTA {prop.get('numero_proposta', '')}</h2>
            
            <div class="info-grid">
                <div class="info-item"><label>Cliente / Empresa</label><span>{prop.get('cliente_nome', 'N/A')}</span></div>
                <div class="info-item"><label>CPF / CNPJ</label><span>{prop.get('documento', 'Não informado')}</span></div>
                <div class="info-item"><label>WhatsApp / Contato</label><span>{prop.get('whatsapp', 'Não informado')}</span></div>
                <div class="info-item"><label>Data Prevista de Entrega</label><span>{prop.get('data_entrega', 'N/A')}</span></div>
            </div>

            <table>
                <thead><tr><th>ITEM / DESCRIÇÃO</th><th>QTD</th><th>UNIT.</th><th>SUBTOTAL</th></tr></thead>
                <tbody>{itens_html}</tbody>
            </table>
            
            <div class="resumo">
                <p>Subtotal: R$ {subtotal:.2f}</p>
                <p>Desconto: R$ {desconto:.2f}</p>
                <p style="font-size: 16px;">VALOR TOTAL DO PEDIDO: R$ {total:.2f}</p>
            </div>
            
            <div class="footer">
                <div class="pix-section">
                    <img src="data:image/png;base64,{pix_base64}" style="width: 100px;">
                    <div style="line-height: 1.5;">
                        🤝 Para fechar seu pedido, trabalhamos com pagamento do valor total no pedido!<br>
                        *Tivemos algumas mudanças devido ao novo regime de tributação.<br><br>
                        💳 <strong>PAGAMENTO VIA PIX</strong> - Segue abaixo nossa conta e pix:<br>
                        💳💳 Pix- 24374857000130 (CNPJ)<br>
                        👉 <a href="https://linkspix.app/alphafestitatiba">Clique no link para pagar</a><br>
                        Banco CORA | Ana Lúcia Zepelini<br><br>
                        <strong>Conta Jurídica</strong><br>
                        Agência: 0001 | Conta: 2515972-5<br>
                        Instituição: 403 - Cora SCD<br>
                        Nome da Empresa: ANA LUCIA VIEIRA ZEPELINI 29480359880<br>
                        CNPJ: 24.374.857/0001-30<br><br>
                        👇<br>
                        <em>Somente após realizado pagamento e nos enviando o comprovante daremos seguimento ao seu pedido !!🥰</em><br>
                        <strong>Ps. Orçamento válido por 5 dias.</strong>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def formatar_msg_whatsapp(prop):
    total = prop.get('valor_total', 0)
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
    return chart

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
    st.subheader("📊 Relatórios de Vendas")
    h = carregar_historico()
    if h:
        df = pd.DataFrame(h)
        df['Data'] = pd.to_datetime(df['data_geracao'], dayfirst=True)
        
        # Filtro de Período
        periodo = st.selectbox("Agrupar por Período", ["Dia", "Semana", "Mês", "Ano"])
        
        # 1. Total Receita
        df_rec = df.copy()
        if periodo == "Dia": df_rec['Periodo'] = df_rec['Data'].dt.strftime('%d/%m/%Y')
        elif periodo == "Semana": df_rec['Periodo'] = df_rec['Data'].dt.strftime('%W/%Y')
        elif periodo == "Mês": df_rec['Periodo'] = df_rec['Data'].dt.strftime('%m/%Y')
        else: df_rec['Periodo'] = df_rec['Data'].dt.strftime('%Y')
        
        st.write("### 💰 Receita Total")
        st.altair_chart(criar_grafico_profissional(df_rec.groupby('Periodo')['valor_total'].sum().reset_index(), 'Periodo', 'valor_total', 'Receita Total'), use_container_width=True)
        
        # 2. Produtos mais vendidos
        all_items = []
        for p in h:
            for item in p['itens']:
                date_p = pd.to_datetime(p['data_geracao'], dayfirst=True)
                item_data = {'Produto': item['produto'], 'Qtd': item['quantidade'], 'Data': date_p}
                if periodo == "Dia": item_data['Periodo'] = date_p.strftime('%d/%m/%Y')
                elif periodo == "Semana": item_data['Periodo'] = date_p.strftime('%W/%Y')
                elif periodo == "Mês": item_data['Periodo'] = date_p.strftime('%m/%Y')
                else: item_data['Periodo'] = date_p.strftime('%Y')
                all_items.append(item_data)
        
        df_prod = pd.DataFrame(all_items)
        st.write("### 🏆 Produtos Mais Vendidos")
        st.altair_chart(criar_grafico_profissional(df_prod.groupby(['Periodo', 'Produto'])['Qtd'].sum().reset_index(), 'Produto', 'Qtd', 'Qtd Vendida'), use_container_width=True)
