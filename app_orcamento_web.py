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
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

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

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico.insert(0, dados_proposta)
    salvar_historico_completo(historico)

def alternar_status(num_proposta, campo, status_atual):
    historico = carregar_historico()
    for p in historico:
        if p.get("numero_proposta") == num_proposta:
            p[campo] = not status_atual
            break
    salvar_historico_completo(historico)

def excluir_proposta_por_id(num_proposta):
    historico = carregar_historico()
    historico_atualizado = [p for p in historico if p.get("numero_proposta") != num_proposta]
    salvar_historico_completo(historico_atualizado)

def zerar_todo_historico():
    salvar_historico_completo([])

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file:
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
    
    texto_itens = ""
    for idx, item in enumerate(dados["itens"], 1):
        sub_item = item["quantidade"] * item["valor_unitario"]
        texto_itens += f"  *{idx}. {item['produto']}*\n"
        if item.get('especificacoes'):
            texto_itens += f"     └ Detalhes: {item['especificacoes']}\n"
        texto_itens += f"     └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f} | Subtotal: R$ {sub_item:.2f}\n\n"

    msg = (
        f"🔥 *PROPOSTA ALPHAFEST ITATIBA*\n"
        f"📄 *Nº:* {dados['numero_proposta']}\n"
        f"🗓️ *Emissão:* {dados.get('data_geracao', '')}\n\n"
        f"👤 *CLIENTE:* {dados['cliente_nome']}\n"
        f"🪪 *CPF/CNPJ:* {dados.get('cliente_cpf_cnpj', 'Não informado')}\n"
        f"-----------------------------------\n"
        f"📦 *ITENS DO PEDIDO:*\n\n"
        f"{texto_itens}"
        f"-----------------------------------\n"
        f"💵 *Subtotal:* R$ {subtotal_geral:.2f}\n"
        f"🏷️ *Desconto:* - R$ {desc_v:.2f}\n"
        f"✅ *VALOR TOTAL DO PEDIDO:* R$ {total_final:.2f}\n"
        f"-----------------------------------\n"
        f"📅 *Previsão de Entrega:* {dados.get('data_entrega', 'A combinar')}\n"
        f"⏳ *Prazo de Produção:* {dados.get('prazo_dias', '10')} dias úteis\n"
        f"🚚 *Frete/Entrega:* {dados.get('frete_tipo', 'Retirada em Itatiba')}\n"
        f"⏰ *Validade:* 5 dias corridos\n\n"
        f"💳 *PAGAMENTO VIA PIX (100%):*\n"
        f"👉 *Clique no link para pagar:* {LINK_PIX_OFICIAL}\n\n"
        f"• *Titular:* Ana Lúcia Zepelini\n"
        f"• *Banco:* Cora SCD (403)\n"
        f"• *Agência:* 0001 | *Conta:* 2515972-5\n"
        f"• *Empresa:* ANA LUCIA VIEIRA ZEPELINI 29480359880\n\n"
        f"👇 *Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido ! 🥰*"
    )
    
    msg_enc = urllib.parse.quote(msg)
    if num_wa and len(num_wa) >= 12:
        return f"https://wa.me/{num_wa}?text={msg_enc}"
    else:
        return f"https://api.whatsapp.com/send?text={msg_enc}"

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    
    if logo_base64:
        logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Alphafest Logo">'
    else:
        logo_tag = f'<div style="font-size:24px; font-weight:bold; color:#1e293b;">🔥 {MARCA_FABRICANTE}</div>'
        
    data_hoje = dados.get("data_geracao", datetime.now().strftime("%d/%m/%Y"))
    data_entrega = dados.get("data_entrega", "A combinar")
    
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
    qr_code_pix_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(LINK_PIX_OFICIAL)}"

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
            .bank-container {{
                display: flex;
                align-items: center;
                gap: 15px;
                background: #f1f5f9;
                border: 1px dashed #94a3b8;
                padding: 10px;
                border-radius: 6px;
                margin: 8px 0;
            }}
            .qr-code {{
                width: 100px;
                height: 100px;
                border-radius: 4px;
                border: 1px solid #cbd5e1;
                background: #ffffff;
                padding: 3px;
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
                <div class="info-item"><label>CPF / CNPJ</label><span>{dados.get('cliente_cpf_cnpj', 'Não informado')}</span></div>
                <div class="info-item"><label>WhatsApp / Contato</label><span>{dados.get('cliente_wa', 'Não informado')}</span></div>
                <div class="info-item"><label>Data Prevista de Entrega</label><span style="color:#0284c7;">📅 {data_entrega}</span></div>
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
                <strong>📌 Condições de Produção & Pagamento:</strong><br>
                🤝 <strong>Para fechar seu pedido, trabalhamos com pagamento do valor total no pedido!</strong><br>
                *Tivemos algumas mudanças devido ao novo regime de tributação. Envie seu CPF ou CNPJ para emissão de cupom fiscal/NF.<br>
                
                <div class="bank-container">
                    <img src="{qr_code_pix_url}" class="qr-code" alt="QR Code PIX">
                    <div>
                        <strong style="font-size: 11px; color: #0f172a;">📱 Escaneie o QR Code ou acesse nosso link PIX:</strong><br>
                        👉 <a href="{LINK_PIX_OFICIAL}" target="_blank" style="color: #0284c7; font-weight: bold;">{LINK_PIX_OFICIAL}</a><br>
                        💳 <strong>Titular:</strong> Ana Lúcia Zepelini &bull; <strong>Banco:</strong> Cora SCD (403)<br>
                        <strong>Agência:</strong> 0001 | <strong>Conta:</strong> 2515972-5<br>
                        <strong>Empresa:</strong> ANA LUCIA VIEIRA ZEPELINI 29480359880
                    </div>
                </div>
                
                👇 <strong>Somente após realizado pagamento e envio do comprovante daremos seguimento ao seu pedido ! 🥰</strong><br>
                • <strong>Prazo de Produção:</strong> {dados['prazo_dias']} dias úteis (Entrega prevista: {data_entrega}).<br>
                • <strong>Frete / Entrega:</strong> {dados['frete_tipo']} &bull; <strong>Validade:</strong> 5 dias corridos.
            </div>
            
            <div class="terms-box">
                <strong>Cláusulas Gerais:</strong><br>
                1. A produção seguirá estritamente o layout aprovado pelo cliente.<br>
                2. Por se tratar de produto personalizado, não aceitamos devolução por desistência após o início da confecção.
            </div>
            
            <a href="{link_wa}" class="btn-wa" target="_blank">✅ Enviar Comprovante de Pagamento no WhatsApp</a>
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
    if st.session_state.ultima_proposta:
        p_info = st.session_state.ultima_proposta
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
    
    prod = st.text_input("Produto / Item", placeholder="Ex: Copo Térmico 360ml / Letras Impressas 3D", key=f"p_{fk}")
    
    with st.expander("🎨 Personalização & Especificações (Opcionais)", expanded=True):
        col_esp1, col_esp2 = st.columns(2)
        with col_esp1:
            esp_tema = st.text_input("Tema / Ocasião", placeholder="Ex: Aniversário 15 Anos, Festa Infantil, Corporativo", key=f"et_{fk}")
            esp_nome = st.text_input("Nome(s) Personalizado(s)", placeholder="Ex: Enrico, Giuliana & Felipe", key=f"en_{fk}")
            esp_cor = st.text_input("Cor / Material", placeholder="Ex: Rosa Bebê / PLA Azul / Laser Inox", key=f"ec_{fk}")
        with col_esp2:
            esp_idade = st.text_input("Idade / Data do Evento", placeholder="Ex: 50 Anos / 27/02", key=f"ei_{fk}")
            esp_geral = st.text_input("Outros Detalhes", placeholder="Ex: Gravação frente e verso", key=f"eg_{fk}")

    col_q, col_v = st.columns(2)
    with col_q:
        qtd = st.number_input("Quantidade", min_value=1, value=1, step=1, key=f"q_{fk}")
    with col_v:
        v_unit = st.number_input("Valor Unitário (R$)", min_value=0.01, value=10.00, step=0.50, format="%.2f", key=f"v_{fk}")

    partes_espec = []
    if esp_tema.strip(): partes_espec.append(f"Tema: {esp_tema.strip()}")
    if esp_nome.strip(): partes_espec.append(f"Nome: {esp_nome.strip()}")
    if esp_idade.strip(): partes_espec.append(f"Idade/Data: {esp_idade.strip()}")
    if esp_cor.strip(): partes_espec.append(f"Cor/Material: {esp_cor.strip()}")
    if esp_geral.strip(): partes_espec.append(f"Obs: {esp_geral.strip()}")
    
    espec_final_str = " | ".join(partes_espec) if partes_espec else "Conforme alinhado"

    prod_temp = prod.strip() or "Nome do Produto"
    sub_temp = float(qtd) * float(v_unit)
    
    st.markdown(
        f"""
        <div style="background-color: #f1f5f9; border-left: 4px solid #0284c7; padding: 12px; border-radius: 6px; margin: 10px 0;">
            <small style="color: #64748b; font-weight: bold; text-transform: uppercase;">👁️ PRÉVIA DO ITEM EM TEMPO REAL:</small><br>
            <strong style="font-size: 15px; color: #0f172a;">{prod_temp}</strong><br>
            <span style="color: #475569; font-size: 13px;">🔹 <em>Especificações:</em> {espec_final_str}</span><br>
            <span style="color: #16a34a; font-weight: bold; font-size: 13px;">📦 {qtd} un. x R$ {v_unit:.2f} = R$ {sub_temp:.2f}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if st.button("➕ Adicionar Item à Lista", use_container_width=True):
        if not prod.strip():
            st.error("Informe o nome do produto!")
        else:
            st.session_state.itens.append({
                "produto": prod.strip(),
                "especificacoes": espec_final_str,
                "quantidade": int(qtd),
                "valor_unitario": float(v_unit)
            })
            st.success(f"Item '{prod.strip()}' adicionado!")
            st.session_state.form_key += 1
            st.rerun()

    if st.session_state.itens:
        st.write("### 📦 Itens no Orçamento:")
        subtotal_acumulado = 0.0
        for idx, item in enumerate(st.session_state.itens, 1):
            sub = item["quantidade"] * item["valor_unitario"]
            subtotal_acumulado += sub
            st.write(f"**{idx}. {item['produto']}** — {item['quantidade']} un. x R$ {item['valor_unitario']:.2f} = **R$ {sub:.2f}**")
            st.caption(f"└ Detalhes: {item['especificacoes']}")
            
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
                "cliente_cpf_cnpj": cliente_cpf_cnpj or "Não informado",
                "cliente_wa": cliente_wa or "",
                "itens": list(st.session_state.itens),
                "desconto_valor": desconto_valor,
                "desconto": 0.0,
                "sinal_pct": 100.0,
                "prazo_dias": prazo,
                "frete_tipo": frete,
                "pago": False,
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
    
    # ALERTA: Só mostra se data for hoje E se ainda não foi entregue
    pendentes_hoje = [p for p in historico if str(p.get("data_entrega", "")).strip() == hoje_str and not p.get("entregue", False)]
    if pendentes_hoje:
        st.error(f"🚨 **ALERTA DE ENTREGA PARA HOJE ({hoje_str})**")
        for e_hoje in pendentes_hoje:
            st.markdown(f"👉 **{e_hoje['cliente_nome']}** ({e_hoje['numero_proposta']})")
        st.divider()

    for prop in historico:
        is_pago = prop.get("pago", False)
        is_entregue = prop.get("entregue", False)
        
        status_txt = f"Pago: {'✅' if is_pago else '❌'} | Entregue: {'✅' if is_entregue else '❌'}"
        
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']} | {status_txt}"):
            st.write("**Itens do Pedido:**")
            for it in prop.get("itens", []):
                st.write(f"• {it['produto']} — {it['quantidade']} un. (R${it['valor_unitario']:.2f})")
            st.divider()
            
            c1, c2 = st.columns(2)
            if c1.checkbox("Marcar como PAGO", value=is_pago, key=f"pago_{prop['numero_proposta']}"):
                alternar_status(prop['numero_proposta'], "pago", is_pago); st.rerun()
            if c2.checkbox("Marcar como ENTREGUE", value=is_entregue, key=f"ent_{prop['numero_proposta']}"):
                alternar_status(prop['numero_proposta'], "entregue", is_entregue); st.rerun()
            
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"):
                excluir_proposta_por_id(prop['numero_proposta']); st.rerun()

with aba3:
    st.subheader("📊 Relatórios Financeiros & Comercial")
    historico = carregar_historico()
    
    if not historico:
        st.info("Nenhuma proposta registrada.")
    else:
        # Lógica de relatórios mantida como no seu script
        tot_orçado = sum(sum(i["quantidade"] * i["valor_unitario"] for i in p["itens"]) - p.get("desconto_valor", 0) for p in historico)
        st.metric("Total Orçado", f"R$ {tot_orçado:.2f}")
