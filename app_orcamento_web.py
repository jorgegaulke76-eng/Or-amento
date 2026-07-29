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
        f"💳 *PAGAMENTO VIA PIX:*\n"
        f"👉 *Clique no link para pagar:* {LINK_PIX_OFICIAL}\n\n"
        f"• *Titular:* Ana Lúcia Zepelini\n"
        f"• *Banco:* Cora SCD (403)\n"
        f"• *Agência:* 0001 | *Conta:* 2515972-5\n"
        f"• *Empresa:* ANA LUCIA VIEIRA ZEPELINI 29480359880\n\n"
        f"👇 *Somente após realizado o pagamento e nos enviando o comprovante daremos seguimento ao seu pedido ! 🥰*"
    )
    
    # A correção está aqui: .encode('utf-8') remove as interrogações e mantemos a mensagem limpa
    msg_enc = urllib.parse.quote(msg.encode('utf-8'))
    
    if num_wa and len(num_wa) >= 12:
        return f"https://wa.me/{num_wa}?text={msg_enc}"
    else:
        return f"https://api.whatsapp.com/send?text={msg_enc}"
