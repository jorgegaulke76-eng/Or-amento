import streamlit as st
import base64
import os
import re
import json
import urllib.parse
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Orçamento Alphafest",
    page_icon="📄",
    layout="centered"
)

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
PATH_PIX_QRCODE = "pix.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_DIRETO = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO / LIMPEZA ---
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "itens" not in st.session_state:
    st.session_state.itens = []
if "ultima_proposta" not in st.session_state:
    st.session_state.ultima_proposta = None

# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
def formatar_doc_para_wa(doc):
    apenas_num = re.sub(r'\D', '', str(doc or ''))
    if len(apenas_num) == 11:
        # Espaçamento para o WhatsApp não criar link de telefone sobre o CPF do cliente
        return f"{apenas_num[:3]}. {apenas_num[3:6]}. {apenas_num[6:9]} - {apenas_num[9:]}"
    elif len(apenas_num) == 14:
        return f"{apenas_num[:2]}.{apenas_num[2:5]}.{apenas_num[5:8]}/{apenas_num[8:12]}-{apenas_num[12:]}"
    return doc or "Não informado"

def formatar_cpf_cnpj_padrao(doc):
    apenas_num = re.sub(r'\D', '', str(doc or ''))
    if len(apenas_num) == 11:
        return f"{apenas_num[:3]}.{apenas_num[3:6]}.{apenas_num[6:9]}-{apenas_num[9:]}"
    elif len(apenas_num) == 14:
        return f"{apenas_num[:2]}.{apenas_num[2:5]}.{apenas_num[5:8]}/{apenas_num[8:12]}-{apenas_num[12:]}"
    return doc or "Não informado"

# --- FUNÇÕES DE BANCO DE DADOS / HISTÓRICO ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    salvar_historico_completo(historico)

def alternar_status_aprovado(num_proposta, status_atual):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p["aprovado"] = not status_atual
            break
    salvar_historico_completo(historico)
    
def alternar_status_entregue(num_proposta, status_atual):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p["entregue"] = not status_atual
            break
    salvar_historico_completo(historico)

def excluir_proposta_por_id(num_proposta):
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

def zerar_todo_historico():
    salvar_historico_completo([])

def carregar_imagem_base64(path_imagem):
    if os.path.exists(path_imagem):
        try:
            with open(path_imagem, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def exibir_logo_interface():
    if os.path.exists(PATH_LOGO_OFICIAL):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            st.image(PATH_LOGO_OFICIAL, use_container_width=True)

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"):
        num_wa = "55" + num_wa
    
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc_v = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - desc_v)
    
    doc_wa = formatar_doc_para_wa(dados.get('cliente_cpf_cnpj', ''))

    texto_itens = ""
    for idx, item in enumerate(dados["itens"], 1):
        sub_item = item["quantidade"] * item["valor_unitario"]
        texto_itens += f"  *{idx}. {item['produto']}*\n"
        if item.get('especificacoes'):
            texto_itens += f"     └ Detalhes: {item['especificacoes']}\n"
        texto_itens += f"     └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f} | Subtotal: R$ {sub_item:.2f}\n\n"

    msg = (
        f"*PROPOSTA ALPHAFEST ITATIBA*\n"
        f"Nº: {dados['numero_proposta']}\n"
        f"Emissão: {dados.get('data_geracao', '')}\n\n"
        f"CLIENTE: {dados['cliente_nome']}\n"
        f"CPF/CNPJ: {doc_wa}\n"
        f"-----------------------------------\n"
        f"ITENS DO PEDIDO:\n\n"
        f"{texto_itens}"
        f"-----------------------------------\n"
        f"Subtotal: R$ {subtotal_geral:.2f}\n"
        f"Desconto: - R$ {desc_v:.2f}\n"
        f"*VALOR TOTAL DO PEDIDO: R$ {total_final:.2f}*\n"
        f"-----------------------------------\n"
        f"Previsão de Entrega: {dados.get('data_entrega', 'A combinar')}\n"
        f"Prazo de Produção: {dados.get('prazo_dias', '10')} dias úteis\n"
        f"Frete/Entrega: {dados.get('frete_tipo', 'Retirada em Itatiba')}\n"
        f"Validade: 5 dias corridos\n\n"
        f"DADOS PARA PAGAMENTO:\n"
        f"🔗 *PAGAR VIA PIX (Clique no link abaixo):*\n"
        f"{LINK_PIX_DIRETO}\n\n"
        f"PIX (CNPJ): 24374857000130\n"
        f"Titular: Ana Lúcia Zepelini\n"
        f"Banco: Cora SCD (403)\n"
        f"Agência: 0001 | Conta: 2515972-5\n"
        f"Empresa: ANA LUCIA VIEIRA ZEPELINI\n\n"
        f"Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido !!"
    )
    
    msg_enc = urllib.parse.quote(msg)
    if num_wa and len(num_wa) >= 12:
        return f"https://wa.me/{num_wa}?text={msg_enc}"
    else:
        return f"https://api.whatsapp.com/send?text={msg_enc}"

def gerar_proposta_html(dados):
    logo_base64 = carregar_imagem_base64(PATH_LOGO_OFICIAL)
    pix_qr_base64 = carregar_imagem_base64(PATH_PIX_QRCODE)
    
    if logo_base64:
        logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Alphafest Logo">'
    else:
        logo_tag = f'<div style="font-size:24px; font-weight:bold; color:#1e293b;">ALPHAFEST ITATIBA</div>'
        
    if pix_qr_base64:
        pix_qr_tag = f'<div style="text-align:center; margin-left:15px;"><img src="data:image/png;base64,{pix_qr_base64}" style="max-width:130px; border-radius:4px;" alt="QR Code Pix"><br><small style="color:#64748b; font-size:9px;">Escanear no App do Banco</small></div>'
    else:
        url_qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=130x130&data={urllib.parse.quote(LINK_PIX_DIRETO)}"
        pix_qr_tag = f'<div style="text-align:center; margin-left:15px;"><a href="{LINK_PIX_DIRETO}" target="_blank"><img src="{url_qr_api}" style="max-width:130px; border-radius:4px;" alt="QR Code Pix"></a><br><small style="color:#64748b; font-size:9px;">Escanear ou Clicar para Pagar</small></div>'

    data_hoje = dados.get("data_geracao", datetime.now().strftime("%d/%m/%Y"))
    data_entrega = dados.get("data_entrega", "A combinar")
    doc_formatado = formatar_cpf_cnpj_padrao(dados.get('cliente_cpf_cnpj', ''))
    
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
            <td style="text-align:center;">{item['quantidade']} un.</td>
            <td style="text-align:right;">R$ {item['valor_unitario']:.2f}</td>
            <td style="text-align:right;">R$ {subtotal_item:.2f}</td>
        </tr>
        """
        
    valor_desconto = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - valor_desconto)
    
    link_wa = extrair_link_whatsapp_completo(dados)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Proposta - {dados['numero_proposta']}</title>
        <style>
            @page {{
                size: A4 portrait;
                margin: 8mm;
            }}
            * {{
                box-sizing: border-box;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f8fafc;
                color: #1e293b;
                margin: 0;
                padding: 10px;
            }}
            .container {{
                max-width: 780px;
                margin: 0 auto;
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #1e293b;
                padding-bottom: 10px;
                margin-bottom: 12px;
            }}
            .logo {{
                max-height: 85px;
                max-width: 280px;
                object-fit: contain;
            }}
            .company-info {{
                text-align: right;
                font-size: 10.5px;
                color: #475569;
                line-height: 1.35;
            }}
            .title-box {{
                background: #1e293b !important;
                color: white !important;
                padding: 8px 14px;
                border-radius: 6px;
                margin-bottom: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .title-box h2 {{
                margin: 0;
                font-size: 15px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px 15px;
                margin-bottom: 12px;
                background: #f1f5f9;
                padding: 10px 14px;
                border-radius: 6px;
            }}
            .info-item label {{
                font-size: 9px;
                text-transform: uppercase;
                color: #64748b;
                font-weight: bold;
                display: block;
            }}
            .info-item span {{
                font-size: 12px;
                font-weight: 600;
                color: #0f172a;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
            }}
            th {{
                background: #334155 !important;
                color: white !important;
                padding: 6px 10px;
                text-align: left;
                font-size: 11px;
            }}
            td {{
                padding: 6px 10px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 11px;
            }}
            .summary-box {{
                margin-left: auto;
                width: 260px;
                margin-bottom: 12px;
            }}
            .summary-row {{
                display: flex;
                justify-content: space-between;
                padding: 3px 0;
                font-size: 11px;
                color: #475569;
            }}
            .summary-row.total {{
                font-size: 14px;
                font-weight: bold;
                color: #16a34a;
                border-top: 2px solid #e2e8f0;
                padding-top: 5px;
            }}
            .conditions {{
                background: #f8fafc;
                border: 1px solid #cbd5e1;
                border-left: 4px solid #0284c7;
                padding: 10px 12px;
                border-radius: 6px;
                margin-bottom: 12px;
                font-size: 10.5px;
                color: #334155;
                line-height: 1.4;
            }}
            .bank-box {{
                background: #f1f5f9;
                border: 1px dashed #94a3b8;
                padding: 8px 10px;
                border-radius: 5px;
                margin: 6px 0;
                font-size: 10.5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .terms-box {{
                border: 1px solid #cbd5e1;
                padding: 8px 10px;
                border-radius: 6px;
                font-size: 9.5px;
                color: #64748b;
                line-height: 1.3;
                margin-bottom: 12px;
                background: #fafafa;
            }}
            .btn-wa {{
                display: block;
                width: 100%;
                background: #22c55e;
                color: white;
                text-align: center;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                text-decoration: none;
                font-size: 13px;
            }}
            @media print {{
                html, body {{
                    background: #ffffff;
                    padding: 0;
                    margin: 0;
                }}
                .container {{
                    border: none;
                    padding: 0;
                    width: 100%;
                    max-width: 100%;
                }}
                .btn-wa {{
                    display: none !important;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                {logo_tag}
                <div class="company-info">
                    <strong>{MARCA_FABRICANTE}</strong><br>
                    <strong>CNPJ:</strong> 24.374.857/0001-30 &bull; <strong>IE:</strong> 382105300112<br>
                    Av. Manoel Verginio de Almeida, 442 - Alto Santa Cruz<br>
                    Itatiba - SP &bull; CEP: 13251-530<br>
                    <strong>E-mail:</strong> alphafesti@gmail.com &bull; <strong>Celular:</strong> (11) 9724-9533<br>
                    <strong>Emissão:</strong> {data_hoje}
                </div>
            </div>
            
            <div class="title-box">
                <h2>Proposta</h2>
                <span>Nº {dados['numero_proposta']}</span>
            </div>
            
            <div class="info-grid">
                <div class="info-item"><label>Cliente / Empresa</label><span>{dados['cliente_nome']}</span></div>
                <div class="info-item"><label>CPF / CNPJ</label><span>{doc_formatado}</span></div>
                <div class="info-item"><label>WhatsApp / Contato</label><span>{dados.get('cliente_wa', 'Não informado')}</span></div>
                <div class="info-item"><label>Data Prevista de Entrega</label><span style="color:#0284c7;">{data_entrega}</span></div>
            </div>
            
            <table>
                <thead>
                    <tr><th>ITEM / DESCRIÇÃO</th><th style="text-align:center;">QTD</th><th style="text-align:right;">VALOR UNIT.</th><th style="text-align:right;">SUBTOTAL</th></tr>
                </thead>
                <tbody>{linhas_tabela}</tbody>
            </table>
            
            <div class="summary-box">
                <div class="summary-row"><span>Subtotal:</span><span>R$ {subtotal_geral:.2f}</span></div>
                <div class="summary-row"><span>Desconto:</span><span>- R$ {valor_desconto:.2f}</span></div>
                <div class="summary-row total"><span>VALOR TOTAL DO PEDIDO:</span><span>R$ {total_final:.2f}</span></div>
            </div>
            
            <div class="conditions">
                <strong>Condições de Produção & Pagamento:</strong><br>
                Para fechar seu pedido, trabalhamos com pagamento do valor total no pedido!<br>
                *Tivemos algumas mudanças devido ao novo regime de tributação. Envie seu CPF ou CNPJ para emissão de cupom fiscal/NF.<br>
                
                <div class="bank-box">
                    <div>
                        <strong>Segue abaixo nossa conta e PIX:</strong><br>
                        <strong>Link Direto Pix:</strong> <a href="{LINK_PIX_DIRETO}" target="_blank">{LINK_PIX_DIRETO}</a><br>
                        <strong>PIX (CNPJ):</strong> 24374857000130 &bull; <strong>Titular:</strong> Ana Lúcia Zepelini<br>
                        <strong>Conta Jurídica:</strong> Ag: 0001 | Conta: 2515972-5 | Banco Cora (403)<br>
                        <strong>Empresa:</strong> ANA LUCIA VIEIRA ZEPELINI
                    </div>
                    {pix_qr_tag}
                </div>
                
                <strong>Somente após realizado pagamento e envio do comprovante daremos seguimento ao seu pedido !!</strong><br>
                • <strong>Prazo de Produção:</strong> {dados['prazo_dias']} dias úteis (Entrega prevista: {data_entrega}).<br>
                • <strong>Frete / Entrega:</strong> {dados['frete_tipo']} &bull; <strong>Validade:</strong> 5 dias corridos.
            </div>
            
            <div class="terms-box">
                <strong>Cláusulas Gerais:</strong><br>
                1. A produção seguirá estritamente o layout aprovado pelo cliente.<br>
                2. Por se tratar de produto personalizado, não aceitamos devolução por desistência após o início da confecção.
            </div>
            
            <a href="{link_wa}" class="btn-wa" target="_blank">Enviar Comprovante de Pagamento no WhatsApp</a>
        </div>
    </body>
    </html>
    """
    return html_content

# --- INTERFACE PRINCIPAL ---
exibir_logo_interface()
st.title("📄 ORÇAMENTOS ALPHAFEST")

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

with aba1:
    if st.session_state.get("ultima_proposta"):
        p_info = st.session_state["ultima_proposta"]
        st.success(f"✅ Proposta {p_info['numero']} ({p_info['cliente']}) salva com sucesso!")
        
        col_down, col_wsp = st.columns(2)
        with col_down:
            st.download_button(
                label=f"📥 Baixar Proposta ({p_info['numero']})",
                data=p_info["html"],
                file_name=f"Proposta_{p_info['numero']}.html",
                mime="text/html",
                use_container_width=True
            )
        with col_wsp:
            st.link_button(
                label="📱 Enviar Proposta Completa no WhatsApp",
                url=p_info["link_wa"],
                type="primary",
                use_container_width=True
            )
        st.divider()

    fk = st.session_state.form_key

    st.subheader("1. Dados do Cliente")
    cliente_nome = st.text_input("Nome / Razão Social", placeholder="Ex: Ana Silva / Empresa X", key=f"cliente_{fk}")
    
    col_doc, col_wa = st.columns(2)
    with col_doc:
        cliente_cpf_cnpj = st.text_input("CPF / CNPJ (para Cupom Fiscal/NF)", placeholder="Ex: 000.000.000-00", key=f"cpf_cnpj_{fk}")
    with col_wa:
        cliente_wa = st.text_input("WhatsApp / Telefone", placeholder="Ex: (11) 99999-9999", key=f"wa_{fk}")

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

    st.subheader("3. Condições Comerciais & Prazos")
    desconto_valor = st.number_input("Desconto em Valor (R$)", min_value=0.0, value=0.0, step=1.0, format="%.2f", key=f"desc_{fk}")

    col_pr, col_dt = st.columns(2)
    with col_pr:
        prazo = st.text_input("Prazo (Dias Úteis)", value="10", key=f"prazo_{fk}")
    with col_dt:
        dt_entrega_input = st.date_input("📅 Data Prevista de Entrega", value=date.today(), format="DD/MM/YYYY", key=f"dt_entrega_{fk}")

    frete = st.text_input("Frete / Entrega", value="Retirada em Itatiba", key=f"frete_{fk}")

    st.divider()

    if st.button("🚀 GERAR, SALVAR E ZERAR FORMULÁRIO", type="primary", use_container_width=True):
        if not st.session_state.itens:
            st.error("Adicione pelo menos 1 item antes de gerar a proposta!")
        else:
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "data_entrega": dt_entrega_input.strftime("%d/%m/%Y"),
                "cliente_nome": cliente_nome or "Cliente Não Informado",
                "cliente_cpf_cnpj": cliente_cpf_cnpj or "",
                "cliente_wa": cliente_wa or "",
                "itens": list(st.session_state.itens),
                "desconto_valor": desconto_valor,
                "desconto": 0.0,
                "sinal_pct": 100.0,
                "prazo_dias": prazo,
                "frete_tipo": frete,
                "aprovado": False,
                "entregue": False
            }
            
            salvar_no_historico(dados)
            html_gerado = gerar_proposta_html(dados)
            link_wa_direto = extrair_link_whatsapp_completo(dados)

            st.session_state.ultima_proposta = {
                "numero": dados["numero_proposta"],
                "cliente": dados["cliente_nome"],
                "html": html_gerado,
                "link_wa": link_wa_direto
            }
            
            st.session_state.itens = []
            st.session_state.form_key += 1
            st.rerun()

with aba2:
    
    st.subheader("📋 Central de Propostas Geradas")
    historico = carregar_historico()
    hoje_str = date.today().strftime("%d/%m/%Y")
    
    # Alerta de entrega - Filtra propostas onde data é hoje E NÃO foi entregue
    entregas_hoje = [p for p in historico if p.get("data_entrega") == hoje_str and p.get("entregue") != True]

    if entregas_hoje:
        st.error(f"🚨 **ALERTA: {len(entregas_hoje)} entrega(s) para hoje pendente(s)!**")
        for e_hoje in entregas_hoje:
            st.markdown(f"👉 **{e_hoje.get('cliente_nome', 'Cliente')}** ({e_hoje.get('numero_proposta', 'N/A')})")
        st.divider()
st.write("### 📊 Agrupar por Período de Emissão:")
opcao_periodo = st.radio(
"Selecione o período:",
["Todas", "📅 Hoje", "🗓️ Esta Semana", "📆 Este Mês", "📊 Este Ano"],
horizontal=True,
key="filtro_periodo"
)

propostas_periodo = []
for p in historico:
        data_emissao_str = p.get("data_geracao", "")
        try:
            dt_emissao = datetime.strptime(data_emissao_str, "%d/%m/%Y").date()
        except:
            dt_emissao = hoje
        
        if opcao_periodo == "📅 Hoje":
            if dt_emissao == hoje: propostas_periodo.append(p)
        elif opcao_periodo == "📅 Esta Semana":
            inicio_semana = hoje - timedelta(days=hoje.weekday())
            if dt_emissao >= inicio_semana: propostas_periodo.append(p)
        elif opcao_periodo == "📅 Este Mês":
            if dt_emissao.month == hoje.month and dt_emissao.year == hoje.year: propostas_periodo.append(p)
        elif opcao_periodo == "📅 Este Ano":
            if dt_emissao.year == hoje.year: propostas_periodo.append(p)
        else:
            propostas_periodo.append(p)

        termo_busca = st.text_input(
            "🔍 Filtrar por Palavra-Chave",
            placeholder="Digite nome, produto, telefone, CPF/CNPJ ou data (ex: Copo, 11999)",
            key="busca_historico"
        ).strip().lower()

        if termo_busca:
            propostas_filtradas = []
            for prop in propostas_periodo:
                produtos_concat = " ".join([f"{it['produto']} {it['especificacoes']}" for it in prop["itens"]]).lower()
                texto_pesquisa = f"{prop['numero_proposta']} {prop['cliente_nome']} {prop.get('cliente_cpf_cnpj', '')} {prop.get('cliente_wa', '')} {prop.get('data_geracao', '')} {prop.get('data_entrega', '')} {produtos_concat}".lower()
                if termo_busca in texto_pesquisa:
                    propostas_filtradas.append(prop)
        else:
            propostas_filtradas = propostas_periodo

        if not propostas_filtradas:
            st.warning("Nenhum orçamento encontrado para o filtro selecionado.")
        else:
            for prop in propostas_filtradas:
                sub_total = sum(i["quantidade"] * i["valor_unitario"] for i in prop["itens"])
                desc_v = prop.get("desconto_valor", sub_total * (prop.get("desconto", 0.0) / 100))
                tot_final = max(0.0, sub_total - desc_v)
                
                dt_ent = prop.get('data_entrega', 'Não informada')
                tag_hoje = " 🚨 [HOJE]" if dt_ent == hoje_str else ""
                is_aprovado = prop.get("aprovado", False)
                status_tag = " ✅ [PAGO / APROVADO]" if is_aprovado else " ⏳ [PENDENTE]"
                
                # Definir o status visual
                tag_entregue = " ✅ [ENTREGUE]" if prop.get("entregue", False) else " ⏳ [PENDENTE]"
                
                with st.expander(f"📄 {prop['numero_proposta']} - {prop['cliente_nome']} | R$ {tot_final:.2f}{status_tag}{tag_hoje}{tag_entregue}"):
                    # ... (manter o código original de CPF, WhatsApp aqui) ...
                    
                    # ADICIONE ESTE NOVO BOTÃO
                    check_entregue = st.checkbox(
                        "📦 Marcar como ENTREGUE",
                        value=prop.get("entregue", False),
                        key=f"chk_ent_{prop['numero_proposta']}"
                    )
                    if check_entregue != prop.get("entregue", False):
                        alternar_status_entregue(prop['numero_proposta'], prop.get("entregue", False))
                        st.rerun()
                    
                    # ... (manter os botões de download, whats e excluir originais abaixo) ...
                    
                    check_aprovado = st.checkbox(
                        "✅ Marcar como PAGAMENTO CONFIRMADO / PEDIDO EFETIVADO",
                        value=is_aprovado,
                        key=f"chk_aprov_{prop['numero_proposta']}"
                    )
                    if check_aprovado != is_aprovado:
                        alternar_status_aprovado(prop['numero_proposta'], is_aprovado)
                        st.rerun()

                    st.write("**Itens do Orçamento:**")
                    for it in prop["itens"]:
                        st.write(f"• {it['produto']} ({it['especificacoes']}) — {it['quantidade']}un x R${it['valor_unitario']:.2f}")
                    
                    col_dl, col_wa, col_del = st.columns([2, 2, 1])
                    with col_dl:
                        html_prop = gerar_proposta_html(prop)
                        st.download_button(
                            label="📥 Baixar Proposta",
                            data=html_prop,
                            file_name=f"Proposta_{prop['numero_proposta']}.html",
                            mime="text/html",
                            key=f"dl_{prop['numero_proposta']}"
                        )
                    with col_wa:
                        link_w = extrair_link_whatsapp_completo(prop)
                        st.link_button(
                            label="📱 Enviar WhatsApp",
                            url=link_w,
                            use_container_width=True
                        )
                    with col_del:
                        if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"):
                            excluir_proposta_por_id(prop['numero_proposta'])
                            st.success(f"Proposta {prop['numero_proposta']} removida!")
                            st.rerun()

        st.divider()
        with st.expander("⚙️ Zona de Segurança / Limpeza Geral"):
            if st.button("🔥 ZERAR TODO O HISTÓRICO DE TESTES"):
                zerar_todo_historico()
                st.success("Histórico completamente zerado!")
                st.rerun()

with aba3:
    st.subheader("📊 Relatórios Financeiros & Comercial")
    historico = carregar_historico()
    
    if not historico:
        st.info("Nenhuma proposta registrada para gerar relatórios.")
    else:
        tot_orçado = 0.0
        tot_efetivado = 0.0
        qtd_total = len(historico)
        qtd_aprovadas = 0
        
        produtos_dict = {}

        for p in historico:
            sub = sum(i["quantidade"] * i["valor_unitario"] for i in p["itens"])
            desc_v = p.get("desconto_valor", sub * (p.get("desconto", 0.0) / 100))
            v_final = max(0.0, sub - desc_v)
            tot_orçado += v_final
            
            if p.get("aprovado", False):
                tot_efetivado += v_final
                qtd_aprovadas += 1
                
            for item in p["itens"]:
                p_nome = item["produto"].strip().capitalize()
                produtos_dict[p_nome] = produtos_dict.get(p_nome, 0) + item["quantidade"]

        taxa_conversao = (qtd_aprovadas / qtd_total * 100) if qtd_total > 0 else 0.0

        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Total Orçado", f"R$ {tot_orçado:.2f}")
        with col_r2:
            st.metric("Total Pago / Efetivado", f"R$ {tot_efetivado:.2f}")
        with col_r3:
            st.metric("Taxa de Conversão", f"{taxa_conversao:.1f}%")

        st.divider()

        st.write("### 📈 Desempenho Financeiro por Período")
        visao_grafico = st.radio("Agrupar gráficos por:", ["Dia", "Mês", "Ano"], horizontal=True)

        agrupado_orcado = {}
        agrupado_efetivado = {}

        for p in historico:
            dt_str = p.get("data_geracao", "")
            try:
                dt_obj = datetime.strptime(dt_str, "%d/%m/%Y")
            except:
                dt_obj = datetime.now()

            if visao_grafico == "Dia":
                chave = dt_obj.strftime("%d/%m/%Y")
            elif visao_grafico == "Mês":
                chave = dt_obj.strftime("%m/%Y")
            else:
                chave = dt_obj.strftime("%Y")

            sub = sum(i["quantidade"] * i["valor_unitario"] for i in p["itens"])
            desc_v = p.get("desconto_valor", sub * (p.get("desconto", 0.0) / 100))
            val = max(0.0, sub - desc_v)

            agrupado_orcado[chave] = agrupado_orcado.get(chave, 0.0) + val
            if p.get("aprovado", False):
                agrupado_efetivado[chave] = agrupado_efetivado.get(chave, 0.0) + val

        chaves_ordenadas = sorted(agrupado_orcado.keys())
        dados_grafico = {
            "Período": chaves_ordenadas,
            "Total Orçado (R$)": [agrupado_orcado[k] for k in chaves_ordenadas],
            "Pago / Efetivado (R$)": [agrupado_efetivado.get(k, 0.0) for k in chaves_ordenadas]
        }
        
        st.bar_chart(dados_grafico, x="Período", y=["Total Orçado (R$)", "Pago / Efetivado (R$)"])

        st.divider()

        st.write("### 🏆 Produtos Mais Orçados (Quantidade em Peças)")
        if produtos_dict:
            prod_ordenados = dict(sorted(produtos_dict.items(), key=lambda item: item[1], reverse=True))
            dados_prod = {
                "Produto": list(prod_ordenados.keys())[:10],
                "Qtd Peças": list(prod_ordenados.values())[:10]
            }
            st.bar_chart(dados_prod, x="Produto", y="Qtd Peças")
