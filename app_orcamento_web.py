import streamlit as st
import base64
import os
import re
import json
import urllib.parse
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamento Alphafest", page_icon="📄", layout="centered")

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"

# --- GERENCIAMENTO DE ESTADO ---
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None

# --- FUNÇÕES ---
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
    if len(num_wa) <= 11 and not num_wa.startswith("55"): num_wa = "55" + num_wa
    
    subtotal_geral = sum(i["quantidade"] * i["valor_unitario"] for i in dados["itens"])
    desc_v = dados.get("desconto_valor", 0.0)
    total_final = max(0.0, subtotal_geral - desc_v)
    
    texto_itens = ""
    for idx, item in enumerate(dados["itens"], 1):
        texto_itens += f"  *{idx}. {item['produto']}*\n     └ Detalhes: {item['especificacoes']}\n     └ Qtd: {item['quantidade']} un. | Unit: R$ {item['valor_unitario']:.2f}\n\n"

    msg = (f"🔥 *PROPOSTA ALPHAFEST ITATIBA*\n📄 *Nº:* {dados['numero_proposta']}\n👤 *CLIENTE:* {dados['cliente_nome']}\n📅 *Entrega:* {dados['data_entrega']}\n-----------------------------------\n{texto_itens}-----------------------------------\n✅ *VALOR TOTAL:* R$ {total_final:.2f}\n👉 *PIX:* {LINK_PIX_OFICIAL}\n\n👇 *Somente após realizado o pagamento daremos seguimento ao seu pedido ! 🥰*")
    return f"https://wa.me/{num_wa}?text={urllib.parse.quote(msg)}"

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo">' if logo_base64 else f'<h3>{MARCA_FABRICANTE}</h3>'
    
    linhas_tabela = ""
    subtotal_geral = 0.0
    for item in dados["itens"]:
        sub = item["quantidade"] * item["valor_unitario"]
        subtotal_geral += sub
        linhas_tabela += f"<tr><td><strong>{item['produto']}</strong><br><small>{item['especificacoes']}</small></td><td>{item['quantidade']}</td><td>R$ {item['valor_unitario']:.2f}</td><td>R$ {sub:.2f}</td></tr>"
    
    html = f"""<html><body><div style="font-family: Arial; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ccc;">
        {logo_tag}<h2>Proposta: {dados['numero_proposta']}</h2>
        <p><strong>Cliente:</strong> {dados['cliente_nome']}</p>
        <p><strong>CPF/CNPJ:</strong> {dados['cliente_cpf_cnpj']}</p>
        <p><strong>Data Entrega:</strong> {dados['data_entrega']}</p>
        <table width="100%" border="1" style="border-collapse:collapse;">
            <thead><tr><th>Item</th><th>Qtd</th><th>Unit</th><th>Sub</th></tr></thead>
            <tbody>{linhas_tabela}</tbody>
        </table>
        <p><strong>Total: R$ {max(0, subtotal_geral - dados.get('desconto_valor', 0)):.2f}</strong></p>
    </div></body></html>"""
    return html

# --- INTERFACE PRINCIPAL ---
exibir_logo_interface()
st.title("📄 ORÇAMENTOS ALPHAFEST")
aba1, aba2 = st.tabs(["➕ Novo Orçamento", "📋 Histórico & Alertas"])

with aba1:
    if st.session_state.ultima_proposta:
        p_info = st.session_state.ultima_proposta
        st.success("Proposta Gerada!")
        c_d, c_w = st.columns(2)
        c_d.download_button("📥 Baixar HTML", p_info["html"], "proposta.html", use_container_width=True)
        c_w.link_button("📱 WhatsApp", p_info["link_wa"], type="primary", use_container_width=True)

    st.subheader("1. Dados do Cliente")
    cliente_nome = st.text_input("Nome / Razão Social", key="c_nome")
    col1, col2 = st.columns(2)
    cliente_cpf = col1.text_input("CPF / CNPJ", key="c_cpf")
    cliente_wa = col2.text_input("WhatsApp", key="c_wa")
    
    st.subheader("2. Itens")
    prod = st.text_input("Produto", key="i_prod")
    
    # CAMPOS DETALHADOS REINSERIDOS AQUI
    with st.expander("🎨 Detalhes de Personalização (Tema, Nome, Idade, Cor, Obs)", expanded=True):
        col_esp1, col_esp2 = st.columns(2)
        tema = col_esp1.text_input("Tema / Ocasião", key="i_tema")
        nome = col_esp1.text_input("Nome(s) Personalizado(s)", key="i_nome")
        cor = col_esp1.text_input("Cor / Material", key="i_cor")
        idade = col_esp2.text_input("Idade / Data do Evento", key="i_idade")
        obs = col_esp2.text_input("Outros Detalhes", key="i_obs")
    
    cq, cv = st.columns(2)
    qtd = cq.number_input("Qtd", 1, key="i_qtd")
    v_unit = cv.number_input("Valor Unit.", 0.0, key="i_vunit")
    
    if st.button("➕ Adicionar Item"):
        # Monta a string de especificações usando os campos acima
        detalhes = f"Tema: {tema} | Nome: {nome} | Cor: {cor} | Idade: {idade} | Obs: {obs}"
        st.session_state.itens.append({
            "produto": prod, 
            "quantidade": qtd, 
            "valor_unitario": v_unit, 
            "especificacoes": detalhes if detalhes.strip() != "Tema:  | Nome:  | Cor:  | Idade:  | Obs: " else "Conforme alinhado"
        })
        st.rerun()

    if st.session_state.itens:
        st.write("### Itens atuais:")
        st.write(st.session_state.itens)
        
        desconto = st.number_input("Desconto (R$)", 0.0, key="c_desc")
        prazo = st.text_input("Prazo (dias)", "10", key="c_prazo")
        entrega = st.date_input("Data Entrega", key="c_dt")
        frete = st.text_input("Frete", "Retirada em Itatiba", key="c_frete")
        
        if st.button("🚀 GERAR PROPOSTA"):
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "data_entrega": entrega.strftime("%d/%m/%Y"),
                "cliente_nome": st.session_state.c_nome,
                "cliente_cpf_cnpj": st.session_state.c_cpf,
                "cliente_wa": st.session_state.c_wa,
                "itens": st.session_state.itens,
                "desconto_valor": desconto,
                "prazo_dias": prazo,
                "frete_tipo": frete
            }
            salvar_no_historico(dados)
            st.session_state.ultima_proposta = {"html": gerar_proposta_html(dados), "link_wa": extrair_link_whatsapp_completo(dados)}
            st.session_state.itens = []
            st.rerun()

with aba2:
    hist = carregar_historico()
    hoje = date.today().strftime("%d/%m/%Y")
    for p in hist:
        if p.get("data_entrega") == hoje: st.error(f"🚨 ENTREGA HOJE: {p['cliente_nome']}")
        with st.expander(f"{p['numero_proposta']} - {p['cliente_nome']}"):
            st.write(p)
            if st.button("🗑️ Excluir", key=f"del_{p['numero_proposta']}"): 
                # (Lógica de exclusão aqui)
                import json
                h = carregar_historico()
                new_h = [x for x in h if x['numero_proposta'] != p['numero_proposta']]
                salvar_historico_completo(new_h)
                st.rerun()
