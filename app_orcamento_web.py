def gerar_proposta_html(dados):
    linhas_tabela = ""
    subtotal_geral = 0.0
    for item in dados["itens"]:
        sub = item["Qtd"] * item["Valor Unit."]
        subtotal_geral += sub
        d = item['Detalhes'].split('|')
        detalhes_txt = f"{d[0]} {d[1]} {d[2]}"
        linhas_tabela += f"""
        <tr>
            <td style="padding:6px; border-bottom:1px solid #eee;"><b>{item['Produto']}</b><br><small style="color:#666;">{detalhes_txt}</small></td>
            <td style="padding:6px; text-align:center; border-bottom:1px solid #eee;">{item['Qtd']} un.</td>
            <td style="padding:6px; text-align:right; border-bottom:1px solid #eee;">R$ {item['Valor Unit.']:.2f}</td>
            <td style="padding:6px; text-align:right; border-bottom:1px solid #eee;">R$ {sub:.2f}</td>
        </tr>"""
    
    total = max(0, subtotal_geral - dados.get('desconto_valor', 0))
    
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @media print {{ 
                @page {{ size: A4 portrait; margin: 0.5cm; }}
                body {{ -webkit-print-color-adjust: exact; }}
            }}
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 10px; width: 210mm; box-sizing: border-box; }}
        </style>
    </head>
    <body>
        <!-- Cabeçalho -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #003366; padding-bottom: 5px;">
            <img src="data:image/png;base64,{logo_b64}" style="max-width: 80px;">
            <div style="text-align: right; font-size: 9px; line-height: 1.1;">
                <b>ALPHAFEST ITATIBA</b><br>
                CNPJ: 24.374.857/0001-30 | Av. Manoel Verginio de Almeida, 442<br>
                Itatiba - SP | Emissão: {dados['data_geracao']}
            </div>
        </div>
        
        <div style="background: #003366; color: #fff; padding: 5px; margin-top: 10px; font-size: 12px; font-weight: bold;">
            PROPOSTA Nº {dados['numero_proposta']}
        </div>
        
        <div style="padding: 8px; border: 1px solid #ccc; font-size: 11px; margin-top: 5px;">
            <b>CLIENTE:</b> {dados['cliente_nome']} | <b>CPF/CNPJ:</b> {dados['cliente_cpf_cnpj']} | <b>DATA ENTREGA:</b> {dados['data_entrega']}
        </div>
        
        <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size: 11px;">
            <thead><tr style="background:#f4f4f4; text-align:left;"><th style="padding:6px;">ITEM / DESCRIÇÃO</th><th style="padding:6px; text-align:center;">QTD</th><th style="padding:6px; text-align:right;">UNIT.</th><th style="padding:6px; text-align:right;">TOTAL</th></tr></thead>
            <tbody>{linhas_tabela}</tbody>
        </table>
        
        <div style="text-align:right; font-size: 12px; margin-top: 10px;">
            Subtotal: R$ {subtotal_geral:.2f} | Desconto: R$ {dados['desconto_valor']:.2f}<br>
            <b style="color:green; font-size: 14px;">VALOR TOTAL DO PEDIDO: R$ {total:.2f}</b>
        </div>
        
        <!-- Rodapé fixo na parte inferior -->
        <div style="margin-top: 20px; border: 1px solid #ccc; padding: 10px; font-size: 10px;">
            <b>Condições de Produção & Pagamento:</b>
            <div style="display:flex; align-items:center; margin-top:5px;">
                <img src="data:image/png;base64,{qr_b64}" style="width:50px; margin-right:10px;">
                <div>
                    Titular: Ana Lúcia Zepelini | Banco: Cora SCD (403) | Ag: 0001 | Conta: 2515972-5<br>
                    <a href="https://linkspix.app/alphafestitatiba">Acesse nosso link PIX</a>
                </div>
            </div>
            <p style="margin-top:5px;"><i>Somente após realizado pagamento e envio de comprovante daremos seguimento ao pedido!</i><br>
            Frete/Entrega: {dados['frete_tipo']} | Validade: 5 dias corridos</p>
        </div>
    </body>
    </html>
    """
