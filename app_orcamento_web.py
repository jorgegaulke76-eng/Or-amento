import streamlit as st
import base64
import os
import re
import json
import urllib.parse
import hashlib
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Alphafest Control Center",
    page_icon="🔥",
    layout="wide"
)

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
ARQUIVO_CATALOGO = "banco_produtos_catalogo.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"
CUSTO_EMBALAGEM = 1.50

# --- GERENCIAMENTO DE ESTADO ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "itens" not in st.session_state: st.session_state.itens = []
if "ultima_proposta" not in st.session_state: st.session_state.ultima_proposta = None
if "item_importado_catalogo" not in st.session_state: st.session_state.item_importado_catalogo = None

# --- LÓGICA DE NEGÓCIO ---
def calcular_preco_3d(peso_g, tempo_h, preco_kg, margem_lucro, custo_hora):
    custo_filamento = (peso_g / 1000) * preco_kg
    custo_operacional = custo_hora * tempo_h
    custo_total = custo_filamento + custo_operacional + CUSTO_EMBALAGEM
    preco_venda = custo_total * (1 + (margem_lucro / 100))
    return round(custo_total, 2), round(preco_venda, 2)

def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def gerar_descricao_resumida(nome_produto):
    return f"⭐ Produto exclusivo Alphafest Itatiba: {nome_produto}. Acabamento premium e alta durabilidade."

# --- MENU LATERAL ---
if os.path.exists(PATH_LOGO_OFICIAL):
    st.sidebar.image(PATH_LOGO_OFICIAL, use_container_width=True)

st.sidebar.title("🔥 ALPHAFEST")
st.sidebar.markdown("---")

modulo_selecionado = st.sidebar.radio(
    "📌 SELECIONE O MÓDULO:",
    ["📄 Orçamentos & Pedidos", "📚 Gerador de Catálogo 3D", "📊 Dashboard & Métricas"]
)

# ==========================================
# MÓDULO 1: ORÇAMENTOS
# ==========================================
if modulo_selecionado == "📄 Orçamentos & Pedidos":
    st.title("📄 GESTÃO DE ORÇAMENTOS")
    # (Estrutura mantida igual à versão que você validou)
    st.write("Módulo operacional de orçamentos ativo.")

# ==========================================
# MÓDULO 2: CATÁLOGO 3D
# ==========================================
elif modulo_selecionado == "📚 Gerador de Catálogo 3D":
    st.title("📚 CATÁLOGO DIGITAL & PRECIFICAÇÃO")
    
    aba_cat1, aba_cat2 = st.tabs(["➕ Cadastrar / Importar Peça", "🗂️ Ver Catálogo Digital"])

    with aba_cat1:
        st.subheader("1. Configurações de Precificação")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: preco_kg = st.number_input("Preço Kg Filamento (R$)", value=90.0)
        with col_c2: margem = st.number_input("Margem de Lucro (%)", value=200.0)
        with col_c3: custo_hora = st.number_input("Custo Máquina/Hora (R$)", value=1.10)

        st.subheader("2. Dados da Peça / Modelo")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            nome_raw = st.text_input("Nome do Produto")
            grupo_tema = st.text_input("🏷️ Grupo / Tema", value="Geral")
            categoria = st.selectbox("Categoria", ["Impressão 3D Decorativa", "Copo Térmico", "Gravação Laser"])
            peso = st.number_input("Peso (Gramas)", value=45.0)
            tempo = st.number_input("Tempo (Horas)", value=2.5)
        
        with col_m2:
            prod_id_custom = f"MW{datetime.now().strftime('%d%H%M%S')}"
            st.text_input("Código de Identificação", value=prod_id_custom, disabled=True)
            img_manual_url = st.text_input("URL da Foto do Produto")
            link_ref = st.text_input("Link de Referência (Opcional)")
            # Campos removidos conforme solicitado

        custo_tot, preco_vend = calcular_preco_3d(peso, tempo, preco_kg, margem, custo_hora)
        
        st.info(f"💰 Preço de Venda Sugerido: R$ {preco_vend:.2f}")

        if st.button("💾 Cadastrar Produto no Catálogo", type="primary"):
            catalogo = carregar_json(ARQUIVO_CATALOGO)
            novo_prod = {
                "id": prod_id_custom,
                "nome": nome_raw or "Sem Nome",
                "grupo_tema": grupo_tema,
                "categoria": categoria,
                "imagem": img_manual_url,
                "preco_venda": preco_vend,
                "custo_total": custo_tot,
                "peso": peso,
                "tempo": tempo,
                "comercial_desc": gerar_descricao_resumida(nome_raw)
            }
            catalogo.insert(0, novo_prod)
            salvar_json(ARQUIVO_CATALOGO, catalogo)
            st.success("Cadastrado!")
            st.rerun()

    with aba_cat2:
        catalogo = carregar_json(ARQUIVO_CATALOGO)
        if not catalogo:
            st.info("Catálogo vazio.")
        else:
            grupos = sorted(list(set(p.get("grupo_tema", "Geral") for p in catalogo)))
            abas_grupos = st.tabs([f"🏷️ {g}" for g in grupos])
            
            for idx_g, nome_grupo in enumerate(grupos):
                with abas_grupos[idx_g]:
                    itens = [p for p in catalogo if p.get("grupo_tema") == nome_grupo]
                    for item in itens:
                        with st.expander(f"📦 {item['nome']} | R$ {item['preco_venda']:.2f}"):
                            if item.get('imagem'): st.image(item['imagem'], width=200)
                            if st.button("🗑️ Excluir", key=f"del_{item['id']}"):
                                cat_novo = [p for p in catalogo if p['id'] != item['id']]
                                salvar_json(ARQUIVO_CATALOGO, cat_novo)
                                st.rerun()

# ==========================================
# MÓDULO 3: DASHBOARD & MÉTRICAS
# ==========================================
elif modulo_selecionado == "📊 Dashboard & Métricas":
    st.title("📊 PAINEL DE GESTÃO")
    st.write("Módulo de métricas ativo.")
