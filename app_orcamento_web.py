import streamlit as st
import base64
import os
import re
from datetime import datetime

st.set_page_config(
    page_title="Orçamento Alphafest",
    page_icon="📄",
    layout="centered"
)

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo">' if logo_base64 else ""
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    
    linhas_tabela = ""
    subtotal_geral = 0.0
    
    for item in dados["itens"]:
        subtotal_item = item["quantidade"] * item["valor_unitario"]
        subtotal_geral += subtotal_item
        linhas_tabela += f"""
        <tr>
            <td>
                <strong>{item['produto']}</strong><br>
                <small style="color: #64748b;">{item['especificacoes']}</small>
            </td>
            <td>{item['quantidade']} un.</td>
            <td>R$ {item['valor_unitario']:.2f}</td>
            <td>R$ {subtotal_item:.2f}</td>
        </tr>
        """
        
    desconto_pct = dados["desconto"]
    valor_desconto = subtotal_geral * (desconto_pct / 100)
    total_final = subtotal_geral - valor_desconto
    sinal = total_final * (dados["sinal_pct"] / 100)
    restante = total_final - sinal
    
    msg_wa = f"Olá! Gostei da Proposta Comercial {dados['numero_proposta']} e gostaria de aprovar o pedido."
    link_wa = f"https://wa.me/5511999999999?text={re.sub(r' ', '%20', msg_wa)}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Proposta Comercial - {dados['numero_proposta']}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; border: 1px solid #e2e8f0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #1e293b; padding-bottom: 15px; margin-bottom: 20px; }}
            .logo {{ max-height: 70px; max-width: 200px; object-fit: contain; }}
            .company-info {{ text-align: right; font-size: 12px; color: #64748b; }}
            .title-box {{ background: #1e293b; color: white; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .title-box h2 {{ margin: 0; font-size: 18px; text-transform: uppercase; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; background: #f1f5f9; padding: 15px; border-radius: 8px; }}
            .info-item label {{ font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: bold; display: block; }}
            .info-item span {{ font-size: 14px; font-weight: 600; color: #0f172a; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th {{ background: #334155; color: white; padding: 10px; text-align: left; font-size: 12px; }}
            td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }}
            .summary-box {{ margin-left: auto; width: 280px; margin-bottom: 20px; }}
            .summary-row {{ display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; color: #475569; }}
            .summary-row.total {{ font-size: 16px; font-weight: bold; color: #22c55e; border-top: 2px solid #e2e8f0; padding-top: 8px; }}
            .conditions {{ background: #fffbe3; border-left: 4px solid #eab308; padding: 12px; border-radius: 4px; margin-bottom: 20px; font-size: 12px; }}
            .terms-box {{ border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; font-size: 11px; color: #475569; line-height: 1.4; margin-bottom: 20px; background: #fafafa; }}
            .btn-wa {{ display: block; width: 100%; background: #22c55e; color: white; text-align: center; padding: 14px; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                {logo_tag}
                <div class="company-info">
                    <strong>{MARCA_FABRICANTE}</strong><br>
                    Produção Digital e Personalização<br>
                    Itatiba / SP &bull; Data: {data_hoje}
                </div>
            </div>
            
            <div class="title-box">
                <h2>Proposta Comercial</h2>
                <span>Nº {dados['numero_proposta']}</span>
            </div>
            
            <div class="info-grid">
                <div class="info-item"><label>Cliente / Empresa</label><span>{dados['cliente_nome']}</span></div>
                <div class="info-item"><label>CPF / CNPJ / Contato</label><span>{dados['cliente_doc']}</span></div>
                <div class="info-item"><label>Prazo de Produção</label><span>{dados['prazo_dias']} dias úteis (pós-aprovação)</span></div>
                <div class="info-item"><label>Validade</label><span>7 dias corridos</span></div>
            </div>
            
            <table>
                <thead>
                    <tr><th>ITEM / DESCRIÇÃO</th><th>QTD</th><th>VALOR UNIT.</th><th>SUBTOTAL</th></tr>
                </thead>
                <tbody>{linhas_tabela}</tbody>
            </table>
            
            <div class="summary-box">
                <div class="summary-row"><span>Subtotal:</span><span>R$ {subtotal_geral:.2f}</span></div>
                <div class="summary-row"><span>Desconto ({desconto_pct}%):</span><span>- R$ {valor_desconto:.2f}</span></div>
                <div class="summary-row total"><span>VALOR TOTAL:</span><span>R$ {total_final:.2f}</span></div>
                <div class="summary-row" style="font-weight: bold; color: #0284c7; margin-top:5px;"><span>Entrada Sinal ({dados['sinal_pct']}%):</span><span>R$ {sinal:.2f}</span></div>
                <div class="summary-row"><span>Restante na Entrega:</span><span>R$ {restante:.2f}</span></div>
            </div>
            
            <div class="conditions">
                <strong>📌 Condições de Produção:</strong><br>
                • Produção iniciada mediante sinal de R$ {sinal:.2f} e aprovação da arte.<br>
                • Frete/Entrega: {dados['frete_tipo']}.
            </div>
            
            <div class="terms-box">
                <strong>Cláusulas Gerais:</strong><br>
                1. A produção seguirá o layout aprovado.<br>
                2. Produto personalizado não cabe devolução por desistência após o início da confecção.
            </div>
            
            <a href="{link_wa}" class="btn-wa" target="_blank">✅ Aprovar Proposta no WhatsApp</a>
        </div>
    </body>
    </html>
    """
    return html_content

st.title("📄 ORÇAMENTO ALPHAFEST")

if "itens" not in st.session_state:
    st.session_state.itens = []

st.subheader("1. Cliente / Empresa")
col1, col2 = st.columns(2)
with col1:
    cliente_nome = st.text_input("Nome / Razão Social", placeholder="Ex: Evento XV Anos / Empresa X")
with col2:
    cliente_doc = st.text_input("CPF / CNPJ / Telefone", placeholder="Ex: 11 99999-9999")

st.divider()

st.subheader("2. Adicionar Itens ao Orçamento")
with st.form("form_item", clear_on_submit=True):
    col_p, col_e = st.columns([2, 2])
    with col_p:
        prod = st.text_input("Produto", value="Copo Térmico 360ml")
    with col_e:
        espec = st.text_input("Especificações", value="Gravação Laser Aço Inox")
        
    col_q, col_v = st.columns(2)
    with col_q:
        qtd = st.number_input("Quantidade", min_value=1, value=180)
    with col_v:
        v_unit = st.number_input("Valor Unitário (R$)", min_value=0.01, value=35.0, step=0.50)
        
    btn_add = st.form_submit_button("➕ Adicionar Item")
    
    if btn_add:
        st.session_state.itens.append({
            "produto": prod,
            "especificacoes": espec,
            "quantidade": int(qtd),
            "valor_unitario": float(v_unit)
        })
        st.success(f"Item '{prod}' adicionado com sucesso!")

if st.session_state.itens:
    st.write("### 📦 Itens no Orçamento:")
    subtotal_acumulado = 0.0
    for idx, item in enumerate(st.session_state.itens, 1):
        sub = item["quantidade"] * item["valor_unitario"]
        subtotal_acumulado += sub
        st.write(f"**{idx}. {item['produto']}** — {item['quantidade']}un x R${item['valor_unitario']:.2f} = **R$ {sub:.2f}**")
        
    st.info(f"**SUBTOTAL DO PACOTE:** R$ {subtotal_acumulado:.2f}")
    
    if st.button("🗑️ Limpar Todos os Itens"):
        st.session_state.itens = []
        st.rerun()

st.divider()

st.subheader("3. Condições Comerciais")
col_d, col_s = st.columns(2)
with col_d:
    desconto = st.number_input("Desconto (%)", min_value=0.0, value=5.0)
with col_s:
    sinal = st.number_input("Entrada / Sinal (%)", min_value=0.0, value=50.0)

col_pr, col_fr = st.columns(2)
with col_pr:
    prazo = st.text_input("Prazo (Dias Úteis)", value="10")
with col_fr:
    frete = st.text_input("Frete / Entrega", value="Retirada em Itatiba")

st.divider()

if st.button("🚀 GERAR PROPOSTA COMERCIAL", type="primary", use_container_width=True):
    if not st.session_state.itens:
        st.error("Adicione pelo menos 1 item antes de gerar a proposta!")
    else:
        dados = {
            "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
            "cliente_nome": cliente_nome or "Cliente Não Informado",
            "cliente_doc": cliente_doc or "Não informado",
            "itens": st.session_state.itens,
            "desconto": desconto,
            "sinal_pct": sinal,
            "prazo_dias": prazo,
            "frete_tipo": frete
        }
        
        html_gerado = gerar_proposta_html(dados)
        
        st.success("✅ Proposta Gerada com Sucesso!")
        
        nome_arquivo = f"Proposta_{dados['numero_proposta']}.html"
        st.download_button(
            label="📥 Baixar Proposta Comercial (HTML)",
            data=html_gerado,
            file_name=nome_arquivo,
            mime="text/html",
            use_container_width=True
        )
        
        with st.expander("👁️ Visualizar Prévia do Documento"):
            st.components.v1.html(html_gerado, height=800, scrolling=True)
