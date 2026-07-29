import streamlit as st
import base64
import os
import re
import json
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None
if "edit_mode" not in st.session_state: st.session_state.edit_mode = None

# --- FUNÇÕES ---
def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_historico_completo(historico):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def salvar_no_historico(dados_proposta):
    historico = carregar_historico()
    historico = [p for p in historico if p.get("numero_proposta") != dados_proposta["numero_proposta"]]
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

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file: return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def exibir_logo_interface():
    if os.path.exists(PATH_LOGO_OFICIAL):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2: st.image(PATH_LOGO_OFICIAL, use_container_width=True)

def extrair_link_whatsapp_completo(dados):
    num_wa = re.sub(r'\D', '', dados.get('cliente_wa', ''))
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc_v = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - desc_v)
    
    texto_itens = ""
    for idx, item in enumerate(dados["itens"], 1):
        sub_item = item["quantidade"] * item["valor_unitario"]
        texto_itens += f"  *{idx}. {item['produto']}*\n"
        if item.get('especificacoes'): texto_itens += f"     └ Detalhes: {item['especificacoes']}\n"
        texto_itens += f"     └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f} | Subtotal: R$ {sub_item:.2f}\n\n"

    msg = (f"🔥 *PROPOSTA ALPHAFEST ITATIBA*\n📄 *Nº:* {dados['numero_proposta']}\n🗓️ *Emissão:* {dados.get('data_geracao', '')}\n\n"
           f"👤 *CLIENTE:* {dados['cliente_nome']}\n🪪 *CPF/CNPJ:* {dados.get('cliente_cpf_cnpj', 'Não informado')}\n"
           f"-----------------------------------\n📦 *ITENS DO PEDIDO:*\n\n{texto_itens}-----------------------------------\n"
           f"💵 *Subtotal:* R$ {subtotal_geral:.2f}\n🏷️ *Desconto:* - R$ {desc_v:.2f}\n✅ *VALOR TOTAL DO PEDIDO:* R$ {total_final:.2f}\n"
           f"-----------------------------------\n📅 *Previsão de Entrega:* {dados.get('data_entrega', 'A combinar')}\n"
           f"⏳ *Prazo de Produção:* {dados.get('prazo_dias', '10')} dias úteis\n🚚 *Frete/Entrega:* {dados.get('frete_tipo', 'Retirada em Itatiba')}\n"
           f"⏰ *Validade:* 5 dias corridos\n\n💳 *PAGAMENTO VIA PIX:*\n👉 *Clique no link para pagar:* {LINK_PIX_OFICIAL}\n\n"
           f"• *Titular:* Ana Lúcia Zepelini | *Banco:* Cora SCD (403)\n• *Agência:* 0001 | *Conta:* 2515972-5\n"
           f"• *Empresa:* ANA LUCIA VIEIRA ZEPELINI 29480359880\n\n"
           f"👇 *Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido ! 🥰*")
    
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    return f"https://wa.me/{num_wa}?text={msg_enc}" if num_wa and len(num_wa) >= 12 else f"https://api.whatsapp.com/send?text={msg_enc}"

def gerar_proposta_html(dados):
    linhas = "".join([f"<tr><td><strong>{i['produto']}</strong><br><small>{i['especificacoes']}</small></td><td>{i['quantidade']} un.</td><td>R$ {i['valor_unitario']:.2f}</td><td>R$ {(i['quantidade']*i['valor_unitario']):.2f}</td></tr>" for i in dados["itens"]])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{{font-family:sans-serif; padding:20px;}} table{{width:100%; border-collapse:collapse;}} th{{background:#334155; color:white; padding:10px;}} td{{padding:10px; border-bottom:1px solid #ddd;}}</style></head><body><h2>Proposta {dados['numero_proposta']}</h2><div style="background:#f1f5f9; padding:10px;"><b>Cliente:</b> {dados['cliente_nome']}</div><table><thead><tr><th>ITEM</th><th>QTD</th><th>UNIT.</th><th>TOTAL</th></tr></thead><tbody>{linhas}</tbody></table><div style="text-align:right; font-weight:bold;">TOTAL: R$ {(sum(i['quantidade']*i['valor_unitario'] for i in dados['itens']) - dados.get('desconto_valor', 0)):.2f}</div></body></html>"""

# --- INTERFACE ---
exibir_logo_interface()
st.title("📄 ORÇAMENTOS ALPHAFEST")

# --- ALERTA DE ENTREGA ---
hoje = datetime.now().strftime("%d/%m/%Y")
entregas = [p for p in carregar_historico() if p.get("data_entrega") == hoje and not p.get("entregue")]
for p in entregas:
    st.error(f"⚠️ ENTREGA HOJE: {p['numero_proposta']} - Cliente: {p['cliente_nome']}")

aba1, aba2, aba3 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Pedidos", "📊 Relatórios & Gráficos"])

with aba1:
    if st.session_state.ultima_proposta:
        p = st.session_state.ultima_proposta
        st.success(f"✅ Proposta {p['numero']} ({p['cliente']}) gerada!")
        c1, c2 = st.columns(2)
        c1.download_button("📥 Baixar", p["html"], f"Proposta_{p['numero']}.html", mime="text/html", use_container_width=True)
        c2.link_button("📱 WhatsApp", p["link_wa"], type="primary", use_container_width=True)
        st.divider()

    fk = st.session_state.form_key
    edit = st.session_state.edit_mode
    
    st.subheader("1. Dados do Cliente")
    nome = st.text_input("Nome / Razão Social", value=edit['cliente_nome'] if edit else "", key=f"cliente_{fk}")
    c1, c2 = st.columns(2)
    doc = c1.text_input("CPF / CNPJ", value=edit.get('cliente_cpf_cnpj', '') if edit else "", key=f"cpf_{fk}")
    wa = c2.text_input("WhatsApp", value=edit.get('cliente_wa', '') if edit else "", key=f"wa_{fk}")
    
    st.divider()
    st.subheader("2. Adicionar Itens")
    prod = st.text_input("Produto", key=f"prod_{fk}")
    with st.expander("🎨 Personalização & Especificações (Opcionais)", expanded=True):
        c1, c2 = st.columns(2)
        et = c1.text_input("Tema / Ocasião", key=f"et_{fk}")
        en = c1.text_input("Nome(s) Personalizado(s)", key=f"en_{fk}")
        ec = c1.text_input("Cor / Material", key=f"ec_{fk}")
        ei = c2.text_input("Idade / Data do Evento", key=f"ei_{fk}")
        eg = c2.text_input("Outros Detalhes", key=f"eg_{fk}")
    q = st.number_input("Qtd", 1, key=f"q_{fk}")
    v = st.number_input("Valor Unitário", 10.0, key=f"v_{fk}")
    
    if st.button("➕ Adicionar Item à Lista"):
        det = f"Tema: {et} | Nome: {en} | Idade: {ei} | Cor: {ec} | Obs: {eg}"
        st.session_state.itens.append({"produto": prod, "especificacoes": det, "quantidade": q, "valor_unitario": v})
        st.rerun()

    if st.session_state.itens:
        if st.button("🗑️ Limpar Lista"): st.session_state.itens = []; st.rerun()

    st.divider()
    desc = st.number_input("Desconto (R$)", value=edit['desconto_valor'] if edit else 0.0, key=f"desc_{fk}")
    prazo = st.text_input("Prazo (Dias)", value=edit['prazo_dias'] if edit else "10", key=f"prazo_{fk}")
    
    if st.button("🚀 SALVAR PROPOSTA"):
        num = edit['numero_proposta'] if edit else f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}"
        dados = {"numero_proposta": num, "data_geracao": datetime.now().strftime("%d/%m/%Y"), "data_entrega": date.today().strftime("%d/%m/%Y"), "cliente_nome": nome, "cliente_cpf_cnpj": doc, "cliente_wa": wa, "itens": list(st.session_state.itens), "desconto_valor": desc, "prazo_dias": prazo, "frete_tipo": "Retirada em Itatiba", "pago": False, "entregue": False}
        salvar_no_historico(dados)
        st.session_state.ultima_proposta = {"numero": num, "cliente": nome, "html": gerar_proposta_html(dados), "link_wa": extrair_link_whatsapp_completo(dados)}
        st.session_state.itens = []; st.session_state.edit_mode = None; st.session_state.form_key += 1; st.rerun()

with aba2:
    st.subheader("📋 Central de Propostas Geradas")
    for prop in carregar_historico():
        with st.expander(f"{prop['numero_proposta']} - {prop['cliente_nome']} {'✅' if prop.get('entregue') else ''}"):
            st.write(f"**Cliente:** {prop['cliente_nome']} | **CPF:** {prop.get('cliente_cpf_cnpj', 'N/A')}")
            for it in prop.get('itens', []): st.write(f"• {it['produto']} ({it['quantidade']} un)")
            if st.checkbox("Pago", value=prop.get("pago", False), key=f"p_{prop['numero_proposta']}"): alternar_status(prop['numero_proposta'], "pago", False); st.rerun()
            if st.checkbox("Entregue", value=prop.get("entregue", False), key=f"e_{prop['numero_proposta']}"): alternar_status(prop['numero_proposta'], "entregue", False); st.rerun()
            if st.button("✏️ Editar", key=f"edit_{prop['numero_proposta']}"): st.session_state.edit_mode = prop; st.rerun()
            if st.button("🗑️ Excluir", key=f"del_{prop['numero_proposta']}"): excluir_proposta_por_id(prop['numero_proposta']); st.rerun()
