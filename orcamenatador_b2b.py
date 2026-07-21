# ==================================================================================
# MÓDULO DE ORÇAMENTOS (MÚLTIPLOS ITENS) - ALPHAFEST ITATIBA
# ==================================================================================
import os
import re
import base64
from datetime import datetime
import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "b2b_propostas")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = os.path.join(BASE_DIR, "logo.png")

def carregar_logo_base64():
    if os.path.exists(PATH_LOGO_OFICIAL):
        try:
            with open(PATH_LOGO_OFICIAL, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except: pass
    return ""

def gerar_proposta_html(dados):
    logo_base64 = carregar_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo">' if logo_base64 else ""
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    
    # Processa os múltiplos itens
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
    
    msg_wa = f"Olá! Gostei da Proposta Comercial {dados['numero_proposta']} e gostaria de aprovar o pedido."
    link_wa = f"https://wa.me/5511999999999?text={re.sub(r' ', '%20', msg_wa)}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Proposta Comercial - {dados['numero_proposta']} - {MARCA_FABRICANTE}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #1e293b; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ max-height: 80px; max-width: 220px; object-fit: contain; }}
            .company-info {{ text-align: right; font-size: 13px; color: #64748b; }}
            .title-box {{ background: #1e293b; color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }}
            .title-box h2 {{ margin: 0; font-size: 20px; text-transform: uppercase; letter-spacing: 1px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; background: #f1f5f9; padding: 20px; border-radius: 8px; }}
            .info-item label {{ font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: bold; display: block; margin-bottom: 4px; }}
            .info-item span {{ font-size: 15px; font-weight: 600; color: #0f172a; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
            th {{ background: #334155; color: white; padding: 12px; text-align: left; font-size: 13px; }}
            td {{ padding: 14px 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
            
            .summary-box {{ margin-left: auto; width: 320px; margin-bottom: 30px; }}
            .summary-row {{ display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px; color: #475569; }}
            .summary-row.total {{ font-size: 18px; font-weight: bold; color: #22c55e; border-top: 2px solid #e2e8f0; padding-top: 12px; margin-top: 8px; }}
            
            .conditions {{ background: #fffbe3; border-left: 4px solid #eab308; padding: 18px; border-radius: 4px; margin-bottom: 30px; font-size: 13px; line-height: 1.6; color: #713f12; }}
            .terms-box {{ border: 1px solid #cbd5e1; padding: 20px; border-radius: 8px; font-size: 12px; color: #475569; line-height: 1.5; margin-bottom: 30px; background: #fafafa; }}
            .terms-box h4 {{ margin-top: 0; color: #1e293b; text-transform: uppercase; font-size: 13px; }}
            
            .btn-wa {{ display: block; width: 100%; background: #22c55e; color: white; text-align: center; padding: 16px; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 16px; margin-top: 20px; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3); }}
            .btn-wa:hover {{ background: #16a34a; }}
            
            @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; border: none; padding: 0; }} .btn-wa {{ display: none; }} }}
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
                <div class="info-item">
                    <label>Cliente / Empresa</label>
                    <span>{dados['cliente_nome']}</span>
                </div>
                <div class="info-item">
                    <label>CPF / CNPJ / Contato</label>
                    <span>{dados['cliente_doc']}</span>
                </div>
                <div class="info-item">
                    <label>Prazo de Produção</label>
                    <span>{dados['prazo_dias']} dias úteis (após aprovação da arte)</span>
                </div>
                <div class="info-item">
                    <label>Validade da Proposta</label>
                    <span>7 dias corridos</span>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>ITEM / DESCRIÇÃO TÉCNICA</th>
                        <th>QTD</th>
                        <th>VALOR UNIT.</th>
                        <th>SUBTOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_tabela}
                </tbody>
            </table>
            
            <div class="summary-box">
                <div class="summary-row">
                    <span>Subtotal:</span>
                    <span>R$ {subtotal_geral:.2f}</span>
                </div>
                <div class="summary-row">
                    <span>Desconto ({desconto_pct}%):</span>
                    <span>- R$ {valor_desconto:.2f}</span>
                </div>
                <div class="summary-row total">
                    <span>VALOR TOTAL:</span>
                    <span>R$ {total_final:.2f}</span>
                </div>
                <div class="summary-row" style="margin-top: 10px; font-weight: bold; color: #0284c7;">
                    <span>Entrada Sinal ({dados['sinal_pct']}%):</span>
                    <span>R$ {sinal:.2f}</span>
                </div>
                <div class="summary-row" style="font-size: 12px;">
                    <span>Restante na Entrega:</span>
                    <span>R$ {restante:.2f}</span>
                </div>
            </div>
            
            <div class="conditions">
                <strong>📌 Condições de Produção e Pagamento:</strong><br>
                • Produção iniciada mediante confirmação do sinal de <strong>R$ {sinal:.2f}</strong> e aprovação do layout virtual.<br>
                • Frete/Entrega: {dados['frete_tipo']}.
            </div>
            
            <div class="terms-box">
                <h4>Cláusulas Gerais e Contrato Simplificado</h4>
                1. <strong>Aprovação do Layout:</strong> O cliente declara estar ciente de que a produção seguirá rigorosamente a amostra digital/virtual aprovada.<br>
                2. <strong>Personalização Exclusiva:</strong> Por se tratar de produto customizado com marca/nome do cliente, não cabe devolução por desistência após o início da gravação/impressão.<br>
                3. <strong>Garantia:</strong> Garantimos a substituição de qualquer peça que apresente defeito de fabricação ou gravação incorreta em relação ao layout aprovado.
            </div>
            
            <a href="{link_wa}" class="btn-wa" target="_blank">✅ Aprovar Proposta no WhatsApp</a>
        </div>
    </body>
    </html>
    """
    
    nome_arquivo = f"Proposta_{dados['numero_proposta']}_{re.sub(r'[^\w]', '_', dados['cliente_nome'].lower())}.html"
    caminho_final = os.path.join(OUTPUT_DIR, nome_arquivo)
    
    with open(caminho_final, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return caminho_final

# --- INTERFACE GRÁFICA INTERATIVA ---
class AppB2B(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ORÇAMENTO ALPHAFEST")
        self.geometry("600x780")
        self.resizable(False, False)
        
        self.lista_itens = []
        
        ctk.CTkLabel(self, text="ORÇAMENTO ALPHAFEST", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        # Cliente
        f_cli = ctk.CTkFrame(self)
        f_cli.pack(padx=20, pady=5, fill="x")
        
        ctk.CTkLabel(f_cli, text="Cliente/Empresa:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.e_cliente = ctk.CTkEntry(f_cli, width=180, placeholder_text="Nome do cliente")
        self.e_cliente.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(f_cli, text="CPF/CNPJ/Tel:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.e_doc = ctk.CTkEntry(f_cli, width=160, placeholder_text="Documento/Contato")
        self.e_doc.grid(row=0, column=3, padx=5, pady=5)

        # Adicionar Item
        f_add = ctk.CTkFrame(self)
        f_add.pack(padx=20, pady=5, fill="x")
        ctk.CTkLabel(f_add, text="Adicionar Produtos ao Orçamento", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=4, padx=10, pady=3, sticky="w")
        
        ctk.CTkLabel(f_add, text="Produto:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        self.e_produto = ctk.CTkEntry(f_add, width=200)
        self.e_produto.insert(0, "Copo Térmico 360ml")
        self.e_produto.grid(row=1, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(f_add, text="Especs:").grid(row=1, column=2, padx=5, pady=2, sticky="e")
        self.e_especs = ctk.CTkEntry(f_add, width=200)
        self.e_especs.insert(0, "Gravação Laser Aço Inox")
        self.e_especs.grid(row=1, column=3, padx=5, pady=2)
        
        ctk.CTkLabel(f_add, text="Qtd:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.e_qtd = ctk.CTkEntry(f_add, width=80)
        self.e_qtd.insert(0, "180")
        self.e_qtd.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(f_add, text="Valor Unit (R$):").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.e_val_unit = ctk.CTkEntry(f_add, width=80)
        self.e_val_unit.insert(0, "35.00")
        self.e_val_unit.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        btn_add = ctk.CTkButton(f_add, text="➕ Adicionar Item à Lista", command=self.adicionar_item, fg_color="#0284c7")
        btn_add.grid(row=3, column=0, columnspan=4, padx=10, pady=8, sticky="ew")

        # Caixas de Lista de Itens Adicionados
        self.box_itens = ctk.CTkTextbox(self, height=130, width=560)
        self.box_itens.pack(padx=20, pady=5)
        self.box_itens.insert("1.0", "Nenhum item adicionado ainda...")

        # Condições Gerais
        f_val = ctk.CTkFrame(self)
        f_val.pack(padx=20, pady=5, fill="x")
        
        ctk.CTkLabel(f_val, text="Desconto (%):").grid(row=0, column=0, padx=10, pady=4, sticky="e")
        self.e_desc = ctk.CTkEntry(f_val, width=80)
        self.e_desc.insert(0, "5")
        self.e_desc.grid(row=0, column=1, padx=10, pady=4, sticky="w")

        ctk.CTkLabel(f_val, text="Sinal Entrada (%):").grid(row=0, column=2, padx=10, pady=4, sticky="e")
        self.e_sinal = ctk.CTkEntry(f_val, width=80)
        self.e_sinal.insert(0, "50")
        self.e_sinal.grid(row=0, column=3, padx=10, pady=4, sticky="w")
        
        ctk.CTkLabel(f_val, text="Prazo (Dias Úteis):").grid(row=1, column=0, padx=10, pady=4, sticky="e")
        self.e_prazo = ctk.CTkEntry(f_val, width=80)
        self.e_prazo.insert(0, "10")
        self.e_prazo.grid(row=1, column=1, padx=10, pady=4, sticky="w")
        
        ctk.CTkLabel(f_val, text="Frete / Retirada:").grid(row=1, column=2, padx=10, pady=4, sticky="e")
        self.e_frete = ctk.CTkEntry(f_val, width=160)
        self.e_frete.insert(0, "Retirada em Itatiba")
        self.e_frete.grid(row=1, column=3, padx=10, pady=4, sticky="w")

        self.btn_gerar = ctk.CTkButton(self, text="📄 Gerar Proposta Comercial HTML", command=self.gerar_documento, font=ctk.CTkFont(size=14, weight="bold"), height=45)
        self.btn_gerar.pack(pady=12, padx=20, fill="x")
        
        self.lbl_status = ctk.CTkLabel(self, text="Status: Pronto para gerar", text_color="gray")
        self.lbl_status.pack()

    def adicionar_item(self):
        try:
            prod = self.e_produto.get().strip()
            especs = self.e_especs.get().strip()
            qtd = int(self.e_qtd.get().strip())
            v_unit = float(self.e_val_unit.get().strip().replace(",", "."))
            
            if not prod or qtd <= 0 or v_unit <= 0: return
            
            self.lista_itens.append({
                "produto": prod,
                "especificacoes": especs,
                "quantidade": qtd,
                "valor_unitario": v_unit
            })
            
            # Atualiza visual da caixa de texto
            self.box_itens.delete("1.0", "end")
            texto_box = ""
            subtotal_acumulado = 0.0
            
            for idx, item in enumerate(self.lista_itens, 1):
                sub = item["quantidade"] * item["valor_unitario"]
                subtotal_acumulado += sub
                texto_box += f"{idx}. {item['produto']} ({item['quantidade']}un x R${item['valor_unitario']:.2f}) = R${sub:.2f}\n"
                
            texto_box += f"\n--- SUBTOTAL GERAL: R$ {subtotal_acumulado:.2f} ---"
            self.box_itens.insert("1.0", texto_box)
            self.lbl_status.configure(text=f"Item adicionado com sucesso ({len(self.lista_itens)} no total)", text_color="green")
        except:
            self.lbl_status.configure(text="Erro ao adicionar item! Verifique os números.", text_color="red")

    def gerar_documento(self):
        try:
            if not self.lista_itens:
                self.lbl_status.configure(text="Erro: Adicione pelo menos 1 item!", text_color="red")
                return
                
            dados = {
                "numero_proposta": f"PROP-{datetime.now().strftime('%Y%m%d%H%M')}",
                "cliente_nome": self.e_cliente.get().strip() or "Cliente Não Informado",
                "cliente_doc": self.e_doc.get().strip() or "Não informado",
                "itens": self.lista_itens,
                "desconto": float(self.e_desc.get().strip().replace(",", ".")),
                "sinal_pct": float(self.e_sinal.get().strip().replace(",", ".")),
                "prazo_dias": self.e_prazo.get().strip(),
                "frete_tipo": self.e_frete.get().strip()
            }
            
            caminho = gerar_proposta_html(dados)
            os.system(f'start "" "{caminho}"')
            
            self.lbl_status.configure(text=f"Sucesso! Gerado em output/b2b_propostas", text_color="green")
        except Exception as e:
            self.lbl_status.configure(text=f"Erro: {str(e)}", text_color="red")

if __name__ == "__main__":
    AppB2B().mainloop()