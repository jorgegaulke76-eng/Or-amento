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

# NOVA FUNÇÃO PARA ENTREGUE
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
            @page {{ size: A4 portrait; margin: 8mm; }}
            * {{ box-sizing: border-box; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 10px; }}
            .container {{ max-width: 780px; margin: 0 auto; background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e293b; padding-bottom: 10px; margin-bottom: 12px; }}
            .logo {{ max-height: 85px; max-width: 280px; object-fit: contain; }}
            .company-info {{ text-align: right; font-size: 10.5px; color: #475569; line-height: 1.35; }}
            .title-box {{ background: #1e293b !important; color: white !important; padding: 8px 14px; border-radius: 6px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }}
            .title-box h2 {{ margin: 0; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 15px; margin-bottom: 12px; background: #f1f5f9; padding: 10px 14px; border-radius: 6px; }}
            .info-item label {{ font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: bold; display: block; }}
            .info-item span {{ font-size: 12px; font-weight: 600; color: #0f172a; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
            th {{ background: #334155 !important; color: white !important; padding: 6px 10px; text-align: left; font-size: 11px; }}
            td {{ padding: 6px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11px; }}
            .summary-box {{ margin-left: auto; width: 260px; margin-bottom: 12px; }}
            .summary-row {{ display: flex; justify-content: space-between; padding: 3px 0; font-size: 11px; color: #475569; }}
            .summary-row.total {{ font-size: 14px; font-weight: bold; color: #16a34a; border-top: 2px solid #e2e8f0; padding-top: 5px; }}
            .conditions {{ background: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0284c7; padding: 10px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 10.5px; color: #334155; line-height: 1.4; }}
            .bank-box {{ background: #f1f5f9; border: 1px dashed #94a3b8; padding: 8px 10px; border-radius: 5px; margin: 6px 0; font-size: 10.5px; display: flex; justify-content: space-between; align-items: center; }}
            .terms-box {{ border: 1px solid #cbd5e1; padding: 8px 10px; border-radius: 6px; font-size: 9.5px; color: #64748b; line-height: 1.3; margin-bottom: 12px; background: #fafafa; }}
            .btn-wa {{ display: block; width: 100%; background: #22c55e; color: white; text-align: center; padding: 10px; border-radius: 6px; font-weight: bold; text-decoration: none; font-size: 13px; }}
            @media print {{
                html, body {{ background: #ffffff; padding: 0; margin: 0; }}
                .container {{ border: none; padding: 0; width: 100%; max-width: 100%; }}
                .btn-wa {{ display: none !important; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"> {logo_tag}
                <div class="company-info"> <strong>{MARCA_FABRICANTE}</strong><br> <strong>CNPJ:</strong> 24.374.857/0001-30 &bull; <strong>IE:</strong> 382105300112<br> Av. Manoel Verginio de Almeida, 442 - Alto Santa Cruz<br> Itatiba - SP &bull; CEP: 13251-530<br> <strong>E-mail:</strong> alphafesti@gmail.com &bull; <strong>Celular:</strong> (11) 9724-9533<br> <strong>Emissão:</strong> {data_hoje} </div>
            </div>
            <div class="title-box"> <h2>Proposta</h2> <span>Nº {dados['numero_proposta']}</span> </div>
            <div class="info-grid">
                <div class="info-item"><label>Cliente / Empresa</label><span>{dados['cliente_nome']}</span></div>
                <div class="info-item"><label>CPF / CNPJ</label><span>{doc_formatado}</span></div>
                <div class="info-item"><label>WhatsApp / Contato</label><span>{dados.get('cliente_wa', 'Não informado')}</span></div>
                <div class="info-item"><label>Data Prevista de Entrega</label><span style="color:#0284c7;">{data_entrega}</span></div>
            </div>
            <table>
                <thead> <tr><th>ITEM / DESCRIÇÃO</th><th style="text-align:center;">QTD</th><th style="text-align:right;">VALOR UNIT.</th><th style="text-align:right;">SUBTOTAL</th></tr> </thead>
                <tbody>{linhas_tabela}</tbody>
            </table>
            <div class="summary-box">
                <div class="summary-row"><span>Subtotal:</span><span>R$ {subtotal_geral:.2f}</span></div>
                <div class="summary-row"><span>Desconto:</span><span>- R$ {valor_desconto:.2f}</span></div>
                <div class="summary-row total"><span>VALOR TOTAL DO PEDIDO:</span><span>R$ {total_final:.2f}</span></div>
            </div>
            <div class="conditions">
                <strong>Condições de Produção & Pagamento:</strong><br>
                <div class="bank-box">
                    <div>
                        <strong>Segue abaixo nossa conta e PIX:</strong><br>
                        <strong>Link Direto Pix:</strong> <a href="{LINK_PIX_DIRETO}" target="_blank">{LINK_PIX_DIRETO}</a><br>
                        <strong>PIX (CNPJ):</strong> 24374857000130 &bull; <strong>Titular:</strong> Ana Lúcia Zepelini<br>
                        <strong>Empresa:</strong> ANA LUCIA VIEIRA ZEPELINI
                    </div>
                    {pix_qr_tag}
                </div>
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
        st.divider()

    fk = st.session_state.form_key
    st.subheader("1. Dados do Cliente")
    cliente_nome = st.text_input("Nome / Razão Social", key=f"cliente_{fk}")
    col_doc, col_wa = st.columns(2)
    cliente_cpf_cnpj = col_doc.text_input("CPF / CNPJ", key=f"cpf_{fk}")
    cliente_wa = col_wa.text_input("WhatsApp", key=f"wa_{fk}")

    st.subheader("2. Itens")
    with st.form(f"f_{fk}"):
        prod = st.text_input("Produto")
        col_q, col_v = st.columns(2)
        qtd = col_q.number_input("Qtd", min_value=1, value=1)
        v_unit = col_v.number_input("Valor Unitário", min_value=0.01, value=10.00, format="%.2f")
        if st.form_submit_button("Adicionar"):
            st.session_state.itens.append({"produto": prod, "especificacoes": "N/A", "quantidade": qtd, "valor_unitario": v_unit})
            st.rerun()

    if st.session_state.itens:
        st.write(st.session_state.itens)
        if st.button("Gerar Orçamento"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_geracao": datetime.now().strftime("%d/%m/%Y"),
                "data_entrega": date.today().strftime("%d/%m/%Y"),
                "cliente_nome": cliente_nome,
                "cliente_cpf_cnpj": cliente_cpf_cnpj,
                "cliente_wa": cliente_wa,
                "itens": list(st.session_state.itens),
                "desconto_valor": 0,
                "prazo_dias": "10",
                "frete_tipo": "Retirada",
                "aprovado": False,
                "entregue": False # <--- A NOVA FUNCIONALIDADE
            }
            salvar_no_historico(dados)
            st.session_state.itens = []
            st.session_state.form_key += 1
            st.rerun()

with aba2:
    st.subheader("📋 Histórico")
    historico = carregar_historico()
    hoje_str = date.today().strftime("%d/%m/%Y")
    
    # Alerta
    pendentes = [p for p in historico if p.get("data_entrega") == hoje_str and not p.get("entregue", False)]
    if pendentes:
        st.error(f"🚨 {len(pendentes)} entrega(s) pendente(s) para hoje!")

    for prop in historico:
        # Status
        status = "✅ [ENTREGUE]" if prop.get('entregue') else "⏳ [PENDENTE]"
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']} {status}"):
            if not prop.get('entregue'):
                if st.button("📦 Marcar como ENTREGUE", key=f"ent_{prop['numero_proposta']}"):
                    alternar_status_entregue(prop['numero_proposta'], False)
                    st.rerun()
            # Botões de ação antigos...
            col_d, col_w, col_del = st.columns(3)
            if col_del.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"):
                excluir_proposta_por_id(prop['numero_proposta'])
                st.rerun()

with aba3:
    st.write("Relatórios...")
