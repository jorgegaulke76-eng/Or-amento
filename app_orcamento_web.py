import streamlit as st
import pandas as pd
import json
import os
import html
import re
import urllib.parse
from urllib.parse import quote
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
def formatar_msg_whatsapp(prop):
    """Monta a mensagem padrão da proposta para envio pelo WhatsApp."""
    prop = prop or {}

    data_emissao = str(prop.get("data_geracao", prop.get("data", ""))).strip()
    cliente = str(prop.get("cliente_nome", prop.get("cliente", ""))).strip() or "N/A"
    documento = str(
        prop.get("documento", prop.get("cliente_cpf_cnpj", ""))
    ).strip() or "N/A"
    entrega = str(prop.get("data_entrega", "")).strip() or "A combinar"
    prazo = str(prop.get("prazo_dias", "1")).strip() or "1"
    frete = str(prop.get("frete_tipo", "Retirada em Itatiba")).strip() or "Retirada em Itatiba"
    validade = str(prop.get("validade_dias", "5")).strip() or "5"

    def numero(valor, padrao=0.0):
        try:
            return float(valor)
        except (TypeError, ValueError):
            return float(padrao)

    def qtd_txt(valor):
        qtd = numero(valor)
        return str(int(qtd)) if qtd.is_integer() else f"{qtd:.2f}".rstrip("0").rstrip(".")

    itens_txt = []
    total_calculado = 0.0
    for item in prop.get("itens", []) or []:
        produto = str(item.get("produto", "")).strip()
        quantidade = numero(item.get("quantidade", 0))
        valor_unitario = numero(item.get("valor_unitario", 0))
        total_item = quantidade * valor_unitario
        total_calculado += total_item

        if produto:
            itens_txt.append(
                f"{qtd_txt(quantidade)} {produto} --- "
                f"R${valor_unitario:.2f} --- R${total_item:.2f}"
            )

    desconto = numero(prop.get("desconto", prop.get("desconto_valor", 0)))
    total = prop.get("valor_total", prop.get("total"))
    total_valor = numero(total, total_calculado - desconto)
    if total is None:
        total_valor = max(total_calculado - desconto, 0.0)

    unidade_prazo = "dia útil" if prazo == "1" else "dias úteis"
    unidade_validade = "dia corrido" if validade == "1" else "dias corridos"

    linhas = [
        "PROPOSTA ALPHAFEST ITATIBA",
        f"Emissão: {data_emissao}",
        "",
        f"CLIENTE: {cliente}",
        f"CPF/CNPJ: {documento}",
        "-----------------------------------",
        "ITENS DO PEDIDO:",
    ]

    linhas.extend(itens_txt or ["Nenhum item informado"])

    linhas.extend([
        "",
        "-----------------------------------",
        f"VALOR TOTAL DO PEDIDO: R$ {total_valor:.2f}",
        "-----------------------------------",
        f"Previsão de Entrega: {entrega}",
        f"Prazo de Produção: {prazo} {unidade_prazo}",
        f"Frete/Entrega: {frete}",
        f"Validade: {validade} {unidade_validade}",
        "",
        "PAGAMENTO VIA PIX:",
        "https://linkspix.app/alphafestitatiba",
        "",
        "* Titular: Ana Lúcia Zepelini | Conta: 2515972-5",
        "*Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido !",
    ])

    return "\n".join(linhas)

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
    """Salva o histórico, inclusive quando a lista fica vazia."""
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

def criar_grafico_profissional(df, campo_categoria, campo_valor, titulo, horizontal=False, formato=",.2f"):
    """Cria gráfico Altair com validação para evitar erros nos relatórios."""
    if df is None or df.empty:
        return None
    if campo_categoria not in df.columns or campo_valor not in df.columns:
        return None

    dados = df[[campo_categoria, campo_valor]].copy()
    dados[campo_categoria] = dados[campo_categoria].fillna("Não informado").astype(str)
    dados[campo_valor] = pd.to_numeric(dados[campo_valor], errors="coerce").fillna(0)
    dados = dados[dados[campo_valor] >= 0]
    if dados.empty:
        return None

    tooltip = [
        alt.Tooltip(f"{campo_categoria}:N", title=campo_categoria.replace("_", " ").title()),
        alt.Tooltip(f"{campo_valor}:Q", title=campo_valor.replace("_", " ").title(), format=formato),
    ]

    if horizontal:
        ordem = alt.SortField(field=campo_valor, order="descending")
        grafico = (
            alt.Chart(dados)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X(f"{campo_valor}:Q", title=None),
                y=alt.Y(f"{campo_categoria}:N", title=None, sort=ordem),
                tooltip=tooltip,
            )
        )
    else:
        ordem = alt.SortField(field=campo_valor, order="descending")
        grafico = (
            alt.Chart(dados)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X(f"{campo_categoria}:N", title=None, sort=ordem),
                y=alt.Y(f"{campo_valor}:Q", title=None),
                tooltip=tooltip,
            )
        )

    return grafico.properties(title=titulo, height=max(280, min(620, len(dados) * 34)))


def gerar_html(proposta):
    """Gera uma proposta comercial A4, visualmente profissional e pronta para impressão/PDF.

    Recebe diretamente o dicionário salvo no historico_orcamentos.json, evitando
    divergência entre os campos usados na tela de Histórico e os campos do HTML.
    """
    proposta = proposta or {}

    numero = proposta.get("numero_proposta", "")
    data = proposta.get("data_geracao", proposta.get("data", ""))
    cliente = proposta.get("cliente_nome", proposta.get("cliente", ""))
    documento = proposta.get("documento", proposta.get("cliente_cpf_cnpj", ""))
    whatsapp = proposta.get("whatsapp", proposta.get("cliente_wa", ""))
    data_entrega = proposta.get("data_entrega", "")
    itens = proposta.get("itens", []) or []
    subtotal = proposta.get("subtotal", 0)
    desconto = proposta.get("desconto", proposta.get("desconto_valor", 0))
    total = proposta.get("valor_total", proposta.get("total", 0))
    pagamento = proposta.get("pagamento", "")
    observacoes = proposta.get("observacoes", "")


    def esc(valor, vazio="Não informado"):
        if valor is None:
            return vazio
        texto = str(valor).strip()
        return html.escape(texto) if texto else vazio

    def moeda(valor):
        try:
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return "R$ 0,00"

    def data_br(valor):
        if valor is None:
            return ""
        texto = str(valor).strip()

        # Datas ISO: 2026-07-31 ou 2026-07-31T...
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", texto)
        if m:
            return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"

        # Datas já no padrão brasileiro
        m = re.match(r"^(\d{2})[/-](\d{2})[/-](\d{4})", texto)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"

        return esc(texto, "")

    numero_txt = esc(numero)
    data_txt = data_br(data)
    cliente_txt = esc(cliente)
    documento_txt = esc(documento)
    whatsapp_txt = esc(whatsapp)
    entrega_txt = data_br(data_entrega) or "A combinar"

    linhas = []

    for item in itens or []:
        produto = esc(item.get("produto", ""), "Produto não informado")
        especificacoes = esc(
            item.get("especificacoes", ""),
            "—"
        )

        try:
            quantidade = float(item.get("quantidade", 0))
        except (TypeError, ValueError):
            quantidade = 0

        quantidade_txt = (
            str(int(quantidade))
            if quantidade.is_integer()
            else f"{quantidade:.2f}".replace(".", ",")
        )

        try:
            valor_unitario = float(item.get("valor_unitario", 0))
        except (TypeError, ValueError):
            valor_unitario = 0

        total_item = quantidade * valor_unitario

        linhas.append(f"""
            <tr>
                <td class="produto">
                    <strong>{produto}</strong>
                </td>
                <td class="spec">{especificacoes}</td>
                <td class="qtd">{quantidade_txt}</td>
                <td class="money">{moeda(valor_unitario)}</td>
                <td class="money total-item">{moeda(total_item)}</td>
            </tr>
        """)

    if not linhas:
        linhas.append("""
            <tr>
                <td colspan="5" class="empty-row">Nenhum item informado.</td>
            </tr>
        """)

    desconto_valor = 0
    try:
        desconto_valor = float(desconto or 0)
    except (TypeError, ValueError):
        desconto_valor = 0

    subtotal_valor = 0
    try:
        subtotal_valor = float(subtotal or 0)
    except (TypeError, ValueError):
        subtotal_valor = 0

    # Propostas antigas podem não ter o campo subtotal.
    if subtotal_valor == 0 and itens:
        for item in itens:
            try:
                subtotal_valor += float(item.get("quantidade", 0)) * float(item.get("valor_unitario", 0))
            except (TypeError, ValueError, AttributeError):
                pass

    total_valor = 0
    try:
        total_valor = float(total or 0)
    except (TypeError, ValueError):
        total_valor = 0

    if total_valor == 0 and subtotal_valor:
        total_valor = max(0, subtotal_valor - desconto_valor)

    observacoes_txt = esc(observacoes, "Nenhuma observação adicional.")
    pagamento_txt = esc(pagamento, "A combinar")

    # Dados de contato da empresa: usa os dados já existentes no aplicativo
    # quando disponíveis, com fallback seguro.
    empresa_nome = "ALPHAFEST"
    empresa_subtitulo = "Personalizados • Impressão 3D • Papelaria"
    empresa_whatsapp = "(41) 99999-9999"
    empresa_instagram = "@alphafest"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Proposta {numero_txt} - {cliente_txt}</title>

<style>
    @page {{
        size: A4;
        margin: 12mm;
    }}

    * {{
        box-sizing: border-box;
    }}

    html, body {{
        margin: 0;
        padding: 0;
        background: #eef1f5;
        color: #20252b;
        font-family: Arial, Helvetica, sans-serif;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    body {{
        padding: 24px;
    }}

    .page {{
        width: 210mm;
        min-height: 297mm;
        margin: 0 auto;
        background: #ffffff;
        box-shadow: 0 8px 30px rgba(0,0,0,.10);
        overflow: hidden;
    }}

    .top-line {{
        height: 6px;
        background: linear-gradient(90deg, #111827, #374151, #9ca3af);
    }}

    .header {{
        padding: 25px 30px 20px;
        display: flex;
        justify-content: space-between;
        gap: 30px;
        align-items: flex-start;
        border-bottom: 1px solid #e5e7eb;
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: 14px;
    }}

    .brand-mark {{
        width: 52px;
        height: 52px;
        border-radius: 13px;
        background: #111827;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 21px;
        font-weight: 800;
        letter-spacing: -1px;
    }}

    .brand-name {{
        font-size: 25px;
        line-height: 1;
        font-weight: 900;
        letter-spacing: .5px;
        color: #111827;
    }}

    .brand-subtitle {{
        margin-top: 6px;
        font-size: 10px;
        color: #6b7280;
        letter-spacing: .5px;
    }}

    .proposal-meta {{
        text-align: right;
        min-width: 180px;
    }}

    .proposal-label {{
        font-size: 10px;
        color: #6b7280;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }}

    .proposal-number {{
        margin-top: 4px;
        font-size: 23px;
        font-weight: 900;
        color: #111827;
    }}

    .proposal-date {{
        margin-top: 5px;
        font-size: 11px;
        color: #6b7280;
    }}

    .content {{
        padding: 22px 30px 28px;
    }}

    .section-title {{
        display: flex;
        align-items: center;
        gap: 9px;
        margin: 0 0 11px;
        font-size: 11px;
        font-weight: 900;
        color: #111827;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .section-title::before {{
        content: "";
        width: 4px;
        height: 16px;
        border-radius: 3px;
        background: #111827;
    }}

    .client-card {{
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        background: #fafafa;
        padding: 16px;
        margin-bottom: 23px;
    }}

    .client-grid {{
        display: grid;
        grid-template-columns: 1.8fr 1fr 1fr 1fr;
        gap: 14px;
    }}

    .field-label {{
        font-size: 9px;
        color: #6b7280;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .7px;
        margin-bottom: 5px;
    }}

    .field-value {{
        font-size: 12px;
        color: #111827;
        font-weight: 600;
        word-break: break-word;
    }}

    .client-main .field-value {{
        font-size: 15px;
        font-weight: 800;
    }}

    .delivery {{
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px dashed #d1d5db;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .delivery strong {{
        color: #111827;
    }}

    .badge {{
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: #111827;
        color: #fff;
        font-size: 10px;
        font-weight: 800;
    }}

    table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        overflow: hidden;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        margin-bottom: 20px;
    }}

    thead th {{
        background: #111827;
        color: #fff;
        padding: 11px 9px;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: .7px;
        text-align: left;
    }}

    thead th.qtd,
    thead th.money {{
        text-align: right;
    }}

    tbody td {{
        padding: 12px 9px;
        border-top: 1px solid #edf0f2;
        font-size: 10px;
        vertical-align: top;
    }}

    tbody tr:nth-child(even) td {{
        background: #fafafa;
    }}

    td.produto {{
        width: 25%;
        color: #111827;
    }}

    td.spec {{
        width: 36%;
        color: #6b7280;
        line-height: 1.45;
    }}

    td.qtd {{
        width: 8%;
        text-align: right;
        font-weight: 700;
        white-space: nowrap;
    }}

    td.money {{
        width: 15%;
        text-align: right;
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
    }}

    td.total-item {{
        font-weight: 800;
        color: #111827;
    }}

    .empty-row {{
        text-align: center;
        color: #9ca3af;
        padding: 22px !important;
    }}

    .bottom-grid {{
        display: grid;
        grid-template-columns: 1.35fr .65fr;
        gap: 18px;
        align-items: start;
    }}

    .info-card {{
        border: 1px solid #e5e7eb;
        border-radius: 11px;
        padding: 15px;
        background: #fff;
        margin-bottom: 13px;
    }}

    .info-card-title {{
        font-size: 10px;
        font-weight: 900;
        color: #111827;
        text-transform: uppercase;
        letter-spacing: .8px;
        margin-bottom: 8px;
    }}

    .info-text {{
        font-size: 10px;
        line-height: 1.55;
        color: #4b5563;
        white-space: pre-line;
    }}

    .totals {{
        border-radius: 12px;
        background: #f7f7f8;
        border: 1px solid #e5e7eb;
        padding: 16px;
    }}

    .total-row {{
        display: flex;
        justify-content: space-between;
        gap: 15px;
        padding: 7px 0;
        font-size: 11px;
        color: #4b5563;
    }}

    .total-row.discount {{
        color: #15803d;
    }}

    .grand-total {{
        margin-top: 7px;
        padding-top: 13px;
        border-top: 2px solid #111827;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 12px;
    }}

    .grand-total span:first-child {{
        font-size: 11px;
        font-weight: 900;
        color: #111827;
        text-transform: uppercase;
        letter-spacing: .7px;
    }}

    .grand-total .value {{
        font-size: 21px;
        font-weight: 900;
        color: #111827;
        white-space: nowrap;
    }}

    .payment-highlight {{
        background: #111827;
        color: #fff;
        border-radius: 11px;
        padding: 15px;
        margin-bottom: 13px;
    }}

    .payment-highlight .info-card-title {{
        color: #fff;
    }}

    .payment-highlight .info-text {{
        color: #e5e7eb;
    }}

    .footer {{
        margin-top: 24px;
        padding: 17px 30px;
        background: #111827;
        color: #fff;
        display: flex;
        justify-content: space-between;
        gap: 25px;
        align-items: center;
    }}

    .footer-brand {{
        font-size: 13px;
        font-weight: 900;
        letter-spacing: .5px;
    }}

    .footer-contact {{
        text-align: right;
        font-size: 9px;
        line-height: 1.5;
        color: #d1d5db;
    }}

    .validity {{
        margin-top: 18px;
        font-size: 8.5px;
        line-height: 1.45;
        color: #9ca3af;
        text-align: center;
    }}

    @media print {{
        html, body {{
            background: #fff;
        }}

        body {{
            padding: 0;
        }}

        .page {{
            width: 100%;
            min-height: auto;
            margin: 0;
            box-shadow: none;
        }}

        .no-print {{
            display: none !important;
        }}

        tr, .client-card, .info-card, .totals, .payment-highlight {{
            break-inside: avoid;
            page-break-inside: avoid;
        }}
    }}

    @media (max-width: 800px) {{
        body {{
            padding: 0;
        }}

        .page {{
            width: 100%;
        }}

        .header {{
            flex-direction: column;
        }}

        .proposal-meta {{
            text-align: left;
        }}

        .client-grid,
        .bottom-grid {{
            grid-template-columns: 1fr 1fr;
        }}

        .footer {{
            flex-direction: column;
            align-items: flex-start;
        }}

        .footer-contact {{
            text-align: left;
        }}
    }}
</style>
</head>

<body>
<div class="page">

    <div class="top-line"></div>

    <header class="header">
        <div class="brand">
            <div class="brand-mark">AF</div>
            <div>
                <div class="brand-name">{empresa_nome}</div>
                <div class="brand-subtitle">{empresa_subtitulo}</div>
            </div>
        </div>

        <div class="proposal-meta">
            <div class="proposal-label">Proposta Comercial</div>
            <div class="proposal-number">#{numero_txt}</div>
            <div class="proposal-date">Emissão: {data_txt}</div>
        </div>
    </header>

    <main class="content">

        <div class="section-title">Dados do cliente</div>

        <section class="client-card">
            <div class="client-grid">

                <div class="client-main">
                    <div class="field-label">Cliente / Razão Social</div>
                    <div class="field-value">{cliente_txt}</div>
                </div>

                <div>
                    <div class="field-label">CPF / CNPJ</div>
                    <div class="field-value">{documento_txt}</div>
                </div>

                <div>
                    <div class="field-label">WhatsApp</div>
                    <div class="field-value">{whatsapp_txt}</div>
                </div>

                <div>
                    <div class="field-label">Proposta</div>
                    <div class="field-value">#{numero_txt}</div>
                </div>

            </div>

            <div class="delivery">
                <div>
                    <span class="field-label">Previsão de entrega</span><br>
                    <strong>{entrega_txt}</strong>
                </div>
                <span class="badge">PROPOSTA COMERCIAL</span>
            </div>
        </section>

        <div class="section-title">Itens da proposta</div>

        <table>
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Especificações</th>
                    <th class="qtd">Qtd.</th>
                    <th class="money">Valor unit.</th>
                    <th class="money">Total</th>
                </tr>
            </thead>
            <tbody>
                {''.join(linhas)}
            </tbody>
        </table>

        <div class="bottom-grid">

            <div>
                <div class="section-title">Condições comerciais</div>

                <div class="payment-highlight">
                    <div class="info-card-title">Forma de pagamento</div>
                    <div class="info-text">{pagamento_txt}</div>
                </div>

                <div class="info-card">
                    <div class="info-card-title">Observações</div>
                    <div class="info-text">{observacoes_txt}</div>
                </div>

                <div class="info-card">
                    <div class="info-card-title">Validade e produção</div>
                    <div class="info-text">
                        Esta proposta está sujeita à disponibilidade de materiais e à confirmação do pedido.
                        O prazo de produção/entrega deverá ser confirmado no fechamento da proposta.
                    </div>
                </div>
            </div>

            <div>
                <div class="section-title">Resumo financeiro</div>

                <div class="totals">
                    <div class="total-row">
                        <span>Subtotal</span>
                        <strong>{moeda(subtotal_valor)}</strong>
                    </div>

                    <div class="total-row discount">
                        <span>Desconto</span>
                        <strong>- {moeda(desconto_valor)}</strong>
                    </div>

                    <div class="grand-total">
                        <span>Total</span>
                        <span class="value">{moeda(total_valor)}</span>
                    </div>
                </div>
            </div>

        </div>

        <div class="validity">
            Documento gerado eletronicamente • Proposta #{numero_txt} • {empresa_nome}
        </div>

    </main>

    <footer class="footer">
        <div class="footer-brand">{empresa_nome}</div>
        <div class="footer-contact">
            WhatsApp: {empresa_whatsapp}<br>
            Instagram: {empresa_instagram}
        </div>
    </footer>

</div>
</body>
</html>"""


# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Painel de Segurança")
    h_atual = carregar_historico()
    if h_atual:
        st.download_button("💾 BAIXAR BACKUP", data=json.dumps(h_atual, ensure_ascii=False, indent=4), file_name="backup_historico.json", mime="application/json", type="primary", use_container_width=True)

# --- INTERFACE ---
st.title("📄 ORÇAMENTOS ALPHAFEST")

# --- ALERTAS DE VENCIMENTO ---
hoje = date.today()
for p in carregar_historico():
    try:
        data_entrega_str = p.get("data_entrega", "")
        if data_entrega_str:
            data_entrega = datetime.strptime(data_entrega_str, "%d/%m/%Y").date()
            if (not p.get("pago", False) or not p.get("entregue", False)):
                if data_entrega == hoje: st.warning(f"⚠️ ENTREGA HOJE: {p['numero_proposta']} - {p['cliente_nome']}")
                elif data_entrega < hoje: st.error(f"🚨 ATRASADO: {p['numero_proposta']} | {p['cliente_nome']} | Vencido em {p.get('data_entrega')}")
    except: continue

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
                "subtotal": sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens),
                "desconto": desc,
                "valor_total": max(0.0, sum(i['quantidade'] * i['valor_unitario'] for i in st.session_state.temp_itens) - desc),
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
        num_p = prop.get("numero_proposta", "SEM-NÚMERO")
        cliente_p = prop.get("cliente_nome", "Cliente não informado")
        with st.expander(f"{num_p} - {cliente_p}"):
            st.write(f"📅 **Entrega:** {prop.get('data_entrega')}")
            for item in prop.get('itens', []): 
                st.write(f"• {item.get('produto', '')} (Qtd: {item.get('quantidade', 0)})")
            
            c1, c2 = st.columns(2)
            c1.link_button("📱 Enviar WhatsApp", f"https://wa.me/?text={quote(formatar_msg_whatsapp(prop))}")
            c2.download_button("📄 Gerar HTML", gerar_html(prop), file_name=f"{num_p}.html", mime="text/html")
            
            st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{num_p}", on_change=alternar_status, args=(num_p, "pago", not prop.get("pago", False)))
            st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{num_p}", on_change=alternar_status, args=(num_p, "entregue", not prop.get("entregue", False)))
            
            if st.button("🗑️ Excluir", key=f"del_{num_p}"): excluir_proposta(num_p)

with aba3:
    h = carregar_historico()

    if not h:
        st.info("📊 Ainda não existem propostas cadastradas para gerar relatórios.")
    else:
        df = pd.DataFrame(h)

        if "pago" not in df.columns:
            df["pago"] = False
        if "entregue" not in df.columns:
            df["entregue"] = False
        if "valor_total" not in df.columns:
            df["valor_total"] = 0.0
        if "itens" not in df.columns:
            df["itens"] = [[] for _ in range(len(df))]

        def calcular_total(row):
            try:
                valor = row.get("valor_total", 0)
                if pd.isna(valor):
                    valor = 0
                valor = float(valor)
                if valor != 0:
                    return valor

                total = 0.0
                for item in row.get("itens", []) or []:
                    try:
                        total += float(item.get("quantidade", 0)) * float(item.get("valor_unitario", 0))
                    except (TypeError, ValueError):
                        pass
                return total
            except (TypeError, ValueError):
                return 0.0

        df["valor_total"] = df.apply(calcular_total, axis=1)
        df["Data"] = pd.to_datetime(
            df.get("data_geracao"), dayfirst=True, errors="coerce"
        )

        st.subheader("📊 Dashboard Comercial")

        c1, c2 = st.columns(2)
        periodo = c1.selectbox(
            "Período de Agrupamento",
            ["Dia", "Semana", "Mês", "Ano"],
            key="per_rel"
        )
        top_n = c2.selectbox(
            "Produtos no ranking",
            [5, 10, 15, 20],
            index=1,
            key="top_produtos"
        )

        total_propostas = len(df)
        total_orcado = float(df["valor_total"].sum())

        df_pago_base = df[df["pago"].fillna(False).astype(bool)].copy()
        total_recebido = float(df_pago_base["valor_total"].sum())

        total_unidades = 0
        for itens in df["itens"]:
            for item in itens or []:
                try:
                    total_unidades += float(item.get("quantidade", 0))
                except (TypeError, ValueError):
                    pass

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📝 Propostas", f"{total_propostas:,}".replace(",", "."))
        m2.metric(
            "💰 Total Orçado",
            f"R$ {total_orcado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        m3.metric(
            "✅ Total Recebido",
            f"R$ {total_recebido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        m4.metric("📦 Unidades", f"{total_unidades:,.0f}".replace(",", "."))

        st.divider()

        st.subheader("👥 Total por Cliente")
        df_clientes = (
            df.groupby("cliente_nome", dropna=False)["valor_total"]
            .sum()
            .reset_index()
            .sort_values("valor_total", ascending=False)
        )
        grafico = criar_grafico_profissional(
            df_clientes, "cliente_nome", "valor_total",
            "Valor Total por Cliente", horizontal=True
        )
        if grafico:
            st.altair_chart(grafico, use_container_width=True)

        st.divider()

        df_data = df.dropna(subset=["Data"]).copy()

        if periodo == "Dia":
            df_data["Periodo"] = df_data["Data"].dt.strftime("%d/%m/%Y")
        elif periodo == "Semana":
            df_data["Periodo"] = df_data["Data"].dt.to_period("W").apply(lambda x: x.start_time)
        elif periodo == "Mês":
            df_data["Periodo"] = df_data["Data"].dt.to_period("M").dt.to_timestamp()
        else:
            df_data["Periodo"] = df_data["Data"].dt.to_period("Y").dt.to_timestamp()

        df_vendas = (
            df_data.groupby("Periodo")["valor_total"].sum().reset_index()
            if not df_data.empty else pd.DataFrame(columns=["Periodo", "valor_total"])
        )

        st.subheader("📊 Total de Vendas (Orçamentos Gerados)")
        if not df_vendas.empty:
            st.line_chart(
                df_vendas.set_index("Periodo")["valor_total"],
                use_container_width=True
            )
        else:
            st.info("Não há dados suficientes para este período.")

        st.divider()

        st.subheader("💰 Total Recebido (Valores Efetivamente PAGOS)")
        if not df_pago_base.empty:
            df_pago_data = df_pago_base.dropna(subset=["Data"]).copy()

            if periodo == "Dia":
                df_pago_data["Periodo"] = df_pago_data["Data"].dt.strftime("%d/%m/%Y")
            elif periodo == "Semana":
                df_pago_data["Periodo"] = df_pago_data["Data"].dt.to_period("W").apply(lambda x: x.start_time)
            elif periodo == "Mês":
                df_pago_data["Periodo"] = df_pago_data["Data"].dt.to_period("M").dt.to_timestamp()
            else:
                df_pago_data["Periodo"] = df_pago_data["Data"].dt.to_period("Y").dt.to_timestamp()

            df_pago = (
                df_pago_data.groupby("Periodo")["valor_total"].sum().reset_index()
                if not df_pago_data.empty else pd.DataFrame()
            )

            if not df_pago.empty:
                st.line_chart(
                    df_pago.set_index("Periodo")["valor_total"],
                    use_container_width=True
                )
            else:
                st.info("Não há dados de pagamento para este período.")
        else:
            st.info("Ainda não existem propostas marcadas como pagas.")

        st.divider()

        st.subheader("📝 Volume de Propostas Geradas")
        if not df_data.empty:
            df_volume = (
                df_data.groupby("Periodo")["numero_proposta"]
                .count()
                .reset_index()
            )
            st.bar_chart(
                df_volume.set_index("Periodo")["numero_proposta"],
                use_container_width=True
            )
        else:
            st.info("Não há dados para o volume de propostas.")

        st.divider()

        st.subheader("🏆 Produtos Mais Vendidos")

        produtos = []
        for prop in h:
            for item in prop.get("itens", []) or []:
                produto = str(item.get("produto", "")).strip()
                try:
                    quantidade = float(item.get("quantidade", 0))
                except (TypeError, ValueError):
                    quantidade = 0
                try:
                    valor_unitario = float(item.get("valor_unitario", 0))
                except (TypeError, ValueError):
                    valor_unitario = 0

                if produto and quantidade > 0:
                    produtos.append({
                        "produto": produto,
                        "quantidade": quantidade,
                        "faturamento": quantidade * valor_unitario
                    })

        if produtos:
            df_produtos = pd.DataFrame(produtos)

            df_ranking = (
                df_produtos.groupby("produto", as_index=False)
                .agg(
                    quantidade=("quantidade", "sum"),
                    faturamento=("faturamento", "sum")
                )
                .sort_values("quantidade", ascending=False)
            )

            df_top = df_ranking.head(top_n).copy()

            grafico_produtos = criar_grafico_profissional(
                df_top, "produto", "quantidade",
                f"Top {top_n} - Produtos Mais Vendidos",
                horizontal=True, formato=".0f"
            )
            if grafico_produtos:
                st.altair_chart(grafico_produtos, use_container_width=True)

            tabela = df_top.copy()
            tabela.insert(0, "Posição", range(1, len(tabela) + 1))
            tabela["quantidade"] = tabela["quantidade"].apply(
                lambda x: int(x) if float(x).is_integer() else round(x, 2)
            )
            tabela["faturamento"] = tabela["faturamento"].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            tabela.columns = ["Posição", "Produto", "Quantidade Vendida", "Faturamento"]

            st.dataframe(tabela, use_container_width=True, hide_index=True)

            st.divider()

            st.subheader("💰 Produtos que Mais Faturam")

            df_faturamento = (
                df_ranking.sort_values("faturamento", ascending=False)
                .head(top_n)
                .copy()
            )

            grafico_faturamento = criar_grafico_profissional(
                df_faturamento, "produto", "faturamento",
                f"Top {top_n} - Produtos por Faturamento",
                horizontal=True, formato=",.2f"
            )
            if grafico_faturamento:
                st.altair_chart(grafico_faturamento, use_container_width=True)

            st.divider()

            st.subheader("✅ Produtos Efetivamente Vendidos (Propostas Pagas)")

            produtos_pagos = []
            for prop in h:
                if not prop.get("pago", False):
                    continue

                for item in prop.get("itens", []) or []:
                    produto = str(item.get("produto", "")).strip()
                    try:
                        quantidade = float(item.get("quantidade", 0))
                    except (TypeError, ValueError):
                        quantidade = 0
                    try:
                        valor_unitario = float(item.get("valor_unitario", 0))
                    except (TypeError, ValueError):
                        valor_unitario = 0

                    if produto and quantidade > 0:
                        produtos_pagos.append({
                            "produto": produto,
                            "quantidade": quantidade,
                            "faturamento": quantidade * valor_unitario
                        })

            if produtos_pagos:
                df_pagos = (
                    pd.DataFrame(produtos_pagos)
                    .groupby("produto", as_index=False)
                    .agg(
                        quantidade=("quantidade", "sum"),
                        faturamento=("faturamento", "sum")
                    )
                    .sort_values("quantidade", ascending=False)
                    .head(top_n)
                )

                grafico_pagos = criar_grafico_profissional(
                    df_pagos, "produto", "quantidade",
                    f"Top {top_n} - Produtos Pagos",
                    horizontal=True, formato=".0f"
                )
                if grafico_pagos:
                    st.altair_chart(grafico_pagos, use_container_width=True)

                tabela_pagos = df_pagos.copy()
                tabela_pagos.insert(0, "Posição", range(1, len(tabela_pagos) + 1))
                tabela_pagos["quantidade"] = tabela_pagos["quantidade"].apply(
                    lambda x: int(x) if float(x).is_integer() else round(x, 2)
                )
                tabela_pagos["faturamento"] = tabela_pagos["faturamento"].apply(
                    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )
                tabela_pagos.columns = [
                    "Posição", "Produto", "Quantidade Vendida", "Faturamento"
                ]
                st.dataframe(
                    tabela_pagos,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(
                    "Ainda não existem produtos em propostas marcadas como pagas."
                )
        else:
            st.info("Ainda não existem produtos registrados nas propostas.")

