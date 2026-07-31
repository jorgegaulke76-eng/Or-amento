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
                    CEP - 13251-530 | Email - alphafesti@gmail.com | Celular - ( 11 ) 9724-9533<br>
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
    if total == 0:
        total = sum(i.get('quantidade', 0) * i.get('valor_unitario', 0) for i in prop.get('itens', []))
    
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

def criar_grafico_profissional(df, x_col, y_col, titulo, horizontal=False, formato=".2f"):
    if df is None or df.empty:
        return None

    dados = df.copy()

    if horizontal:
        chart = alt.Chart(dados).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y(f"{x_col}:N", title="", sort="-x",
                    axis=alt.Axis(labelLimit=260)),
            x=alt.X(f"{y_col}:Q", title=""),
            tooltip=[
                alt.Tooltip(x_col, title="Produto"),
                alt.Tooltip(y_col, title="Valor", format=formato)
            ]
        ).properties(title=titulo, height=max(300, len(dados) * 28))

        texto = chart.mark_text(
            align="left", baseline="middle", dx=5, fontWeight="bold"
        ).encode(text=alt.Text(y_col, format=formato))
    else:
        chart = alt.Chart(dados).mark_bar(
            cornerRadiusTopLeft=4, cornerRadiusTopRight=4
        ).encode(
            x=alt.X(f"{x_col}:N", title="",
                    sort="-y", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y(f"{y_col}:Q", title=""),
            tooltip=[
                alt.Tooltip(x_col, title="Categoria"),
                alt.Tooltip(y_col, title="Valor", format=formato)
            ]
        ).properties(title=titulo, height=320)

        texto = chart.mark_text(
            align="center", baseline="bottom", dy=-5, fontWeight="bold"
        ).encode(text=alt.Text(y_col, format=formato))

    return (chart + texto).configure_view(
        strokeWidth=0
    ).configure_axis(grid=False)


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

