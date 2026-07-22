import streamlit as st
import base64
import os
import re
import json
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Orçamento Alphafest",
    page_icon="📄",
    layout="centered"
)

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"

# --- GERENCIAMENTO DE ESTADO / LIMPEZA ---
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "itens" not in st.session_state:
    st.session_state.itens = []
if "ultima_proposta" not in st.session_state:
    st.session_state.ultima_proposta = None

# --- FUNÇÕES DE BANCO DE DADOS / HISTÓRICO ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def carregar_logo_base64():
    # Verifica se a logo existe no repositório ou no carregamento local
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    
    # Cabeçalho da logo com visual profissional
    if logo_base64:
        logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Alphafest Logo">'
    else:
        # Fallback elegante caso a imagem logo.png ainda não esteja na pasta
        logo_tag = f'<div style="font-size:24px; font-weight:bold; color:#1e293b;">🔥 {MARCA_FABRICANTE}</div>'
        
    data_hoje = dados.get("data_geracao", datetime.now().strftime("%d/%m/%Y"))
    
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
    
    # Limpa apenas números para o link do WhatsApp
    num_wa = re.sub(r'\D', '', dados['cliente_doc'])
    dest_wa = num_wa if len(num_wa) >= 10 else "5511999999999"
    msg_wa = f"Olá! Gostei da Proposta Comercial {dados['numero_proposta']} da Alphafest e gostaria de aprovar o pedido."
    link_wa = f"https://wa.me/{dest_wa}?text={re.sub(r' ', '%20', msg_wa)}"

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
            .logo {{ max-height: 80px; max-width: 220px; object-fit: contain; }}
            .company-info {{ text-align: right; font-size: 12px; color: #64748b; line-height: 1.4; }}
            .title-box {{ background: #1e293b; color: white; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .title-box h2 {{ margin: 0; font-size: 18px; text-transform: uppercase; letter-spacing: 0.5px; }}
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

# --- INTERFACE PRINCIPAL ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

aba1, aba2 = st.tabs(["➕ Criar Novo Orçamento", "📋 Histórico de Propostas"])

with aba1:
    if st.session_state.ultima_proposta:
        p_info = st.session_state.ultima_proposta
        st.success(f"✅ Proposta {p_info['numero']} ({p_info['cliente']}) salva com sucesso!")
        st.download_button(
            label=f"📥 Baixar Proposta Gerada ({p_info['numero']})",
            data=p_info["html"],
            file_name=f"Proposta_{p_info['numero']}.html",
            mime="text/html",
            use_container_width=True
        )
        st.divider()

    fk = st.session_state.form_key

    st.subheader("1. Dados do Cliente")
    col1, col2 = st.columns(2)
    with col1:
        cliente_nome = st.text_input(
            "Nome / Razão Social",
            placeholder="Ex: Ana Silva / Empresa X",
            key=f"cliente_{fk}"
        )
    with col2:
        cliente_doc = st.text_input(
            "CPF / CNPJ / WhatsApp (com DDD)",
            placeholder="Ex: (11) 99999-9999 ou 00.000.000/0001-00",
            key=f"doc_{fk}"
        )

    st.divider()

    st.subheader("2. Adicionar Itens ao Orçamento")
    with st.form(f"form_item_{fk}", clear_on_submit=True):
        col_p, col_e = st.columns([2, 2])
        with col_p:
            prod = st.text_input("Produto", placeholder="Ex: Copo Térmico 360ml / Troféu 3D")
        with col_e:
            espec = st.text_input("Especificações", placeholder="Ex: Gravação Laser Inox / Impressão PLA")
            
        col_q, col_v = st.columns(2)
        with col_q:
            qtd = st.number_input("Quantidade", min_value=1, value=1, step=1)
        with col_v:
            v_unit = st.number_input("Valor Unitário (R$)", min_value=0.01, value=10.00, step=0.50, format="%.2f")
            
        btn_add = st.form_submit_button("➕ Adicionar Item")
        
        if btn_add:
            if not prod.strip():
                st.error("Informe o nome do produto!")
            else:
                st.session_state.itens.append({
                    "produto": prod,
                    "especificacoes": espec or "Conforme alinhado",
                    "quantidade": int(qtd),
                    "valor_unitario": float(v_unit)
                })
                st.success(f"Item '{prod}' adicionado!")

    if st.session_state.itens:
        st.write("### 📦 Itens no Orçamento:")
        subtotal_acumulado = 0.0
        for idx, item in enumerate(st.session_state.itens, 1):
            sub = item["quantidade"] * item["valor_unitario"]
            subtotal_acumulado += sub
            st.write(f"**{idx}. {item['produto']}** — {item['quantidade']} un. x R$ {item['valor_unitario']:.2f} = **R$ {sub:.2f}**")
            
        st.info(f"**SUBTOTAL DO PACOTE:** R$ {subtotal_acumulado:.2f}")
        
        if st.button("🗑️ Limpar Lista de Itens"):
            st.session_state.itens = []
            st.rerun()

    st.divider()

    st.subheader("3. Condições Comerciais")
    col_d, col_s = st.columns(2)
    with col_d:
        desconto = st.number_input("Desconto (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, format="%.1f", key=f"desc_{fk}")
    with col_s:
        sinal = st.number_input("Entrada / Sinal (%)", min_value=0.0, max_value=100.0, value=50.0, step=5.0, format="%.1f", key=f"sinal_{fk}")

    col_pr, col_fr = st.columns(2)
    with col_pr:
        prazo = st.text_input("Prazo (Dias Úteis)", value="10", key=f"prazo_{fk}")
    with col_fr:
        frete = st.text_input("Frete / Entrega", value="Retirada em Itatiba", key=f"frete_{fk}")

    st.divider()

    if st.button("🚀 GERAR, SALVAR E ZERAR FORMULÁRIO", type="primary", use_container_width=True):
        if not st.session_state.itens:
            st.error("Adicione pelo menos 1 item antes de gerar a proposta!")
        else:
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "cliente_nome": cliente_nome or "Cliente Não Informado",
                "cliente_doc": cliente_doc or "Não informado",
                "itens": list(st.session_state.itens),
                "desconto": desconto,
                "sinal_pct": sinal,
                "prazo_dias": prazo,
                "frete_tipo": frete
            }
            
            salvar_no_historico(dados)
            html_gerado = gerar_proposta_html(dados)
            
            st.session_state.ultima_proposta = {
                "numero": dados["numero_proposta"],
                "cliente": dados["cliente_nome"],
                "html": html_gerado
            }
            
            st.session_state.itens = []
            st.session_state.form_key += 1
            st.rerun()

with aba2:
    st.subheader("📋 Central de Propostas Geradas")
    historico = carregar_historico()
    
    if not historico:
        st.info("Nenhuma proposta gerada até o momento.")
    else:
        st.write(f"**Total de propostas registradas:** {len(historico)}")
        
        for prop in historico:
            sub_total = sum(i["quantidade"] * i["valor_unitario"] for i in prop["itens"])
            tot_final = sub_total * (1 - prop["desconto"]/100)
            
            with st.expander(f"📄 {prop['numero_proposta']} - {prop['cliente_nome']} (R$ {tot_final:.2f})"):
                st.write(f"**Data:** {prop.get('data_geracao', 'N/A')}")
                st.write(f"**Documento/Contato:** {prop['cliente_doc']}")
                st.write(f"**Prazo:** {prop['prazo_dias']} dias úteis | **Frete:** {prop['frete_tipo']}")
                
                st.write("**Itens:**")
                for it in prop["itens"]:
                    st.write(f"• {it['produto']} ({it['quantidade']}un x R${it['valor_unitario']:.2f})")
                
                html_prop = gerar_proposta_html(prop)
                st.download_button(
                    label="📥 Baixar esta proposta novamente",
                    data=html_prop,
                    file_name=f"Proposta_{prop['numero_proposta']}.html",
                    mime="text/html",
                    key=f"dl_{prop['numero_proposta']}"
                )
