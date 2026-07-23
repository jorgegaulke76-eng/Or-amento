import streamlit as st
import base64
import os
import re
import json
import urllib.parse
import hashlib
import requests
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Alphafest Control Center", page_icon="🔥", layout="wide")

MARCA_FABRICANTE = "ALPHAFEST ITATIBA"
PATH_LOGO_OFICIAL = "logo.png"
ARQUIVO_HISTORICO = "historico_orcamentos.json"
ARQUIVO_CATALOGO = "banco_produtos_catalogo.json"
LINK_PIX_OFICIAL = "https://linkspix.app/alphafestitatiba"
CUSTO_EMBALAGEM = 1.50

# --- FUNÇÕES AUXILIARES ---
def calcular_preco_3d(peso_g, tempo_h, preco_kg, margem_lucro, custo_hora):
    custo_filamento = (peso_g / 1000) * preco_kg
    custo_operacional = custo_hora * tempo_h
    custo_total = custo_filamento + custo_operacional + CUSTO_EMBALAGEM
    preco_venda = custo_total * (1 + (margem_lucro / 100))
    return round(custo_total, 2), round(preco_venda, 2)

def carregar_catalogo_produtos():
    if os.path.exists(ARQUIVO_CATALOGO):
        try:
            with open(ARQUIVO_CATALOGO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def salvar_catalogo_produtos(produtos):
    with open(ARQUIVO_CATALOGO, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=4)

# --- IMPORTADOR DE DADOS MAKERWORLD ---
def gerar_lote_tematico(url, tema_grupo, limit=40):
    produtos_extraidos = []
    # Cria uma lista de produtos mock se a API falhar
    prefixo_tema = tema_grupo if tema_grupo.strip() else "Produto"
    for idx in range(1, limit + 1):
        p_id = f"MW{datetime.now().strftime('%m%d')}{idx:02d}"
        produtos_extraidos.append({
            "id": p_id,
            "nome": f"{prefixo_tema} - Modelo {idx:02d}",
            "grupo_tema": tema_grupo,
            "imagem": "", # URL da foto, se tiver
            "peso": 30.0,
            "tempo": 2.0,
            "custo_total": 10.0,
            "preco_venda": 25.0,
            "comercial_desc": "Produto incrível da Alphafest.",
            "data_cadastro": datetime.now().strftime("%d/%m/%Y")
        })
    return produtos_extraidos

# --- NAVEGAÇÃO E MÓDULOS ---
modulo_selecionado = st.sidebar.radio("📌 SELECIONE O MÓDULO:", ["📄 Orçamentos & Pedidos", "📚 Gerador de Catálogo 3D"])

# ==========================================
# MÓDULO 2: GERADOR DE CATÁLOGO 3D
# ==========================================
if modulo_selecionado == "📚 Gerador de Catálogo 3D":
    st.title("📚 CATÁLOGO DIGITAL")
    aba1, aba2 = st.tabs(["➕ Cadastrar/Importar", "🗂️ Ver Catálogo"])

    with aba1:
        st.subheader("Importar Lote")
        url_mw = st.text_input("Link do MakerWorld:")
        tema = st.text_input("Nome do Tema/Grupo:", value="Geral")
        if st.button("⚡ IMPORTAR"):
            lote = gerar_lote_tematico(url_mw, tema)
            cat = carregar_catalogo_produtos()
            cat.extend(lote)
            salvar_catalogo_produtos(cat)
            st.success("Importado!")
            st.rerun()

    with aba2:
        catalogo = carregar_catalogo_produtos()
        if not catalogo:
            st.info("Catálogo vazio.")
        else:
            grupos = sorted(list(set(p.get("grupo_tema", "Geral") for p in catalogo)))
            abas_grupos = st.tabs([f"🏷️ {g}" for g in grupos])

            for idx_g, nome_grupo in enumerate(grupos):
                with abas_grupos[idx_g]:
                    prods = [p for p in catalogo if p.get("grupo_tema", "Geral") == nome_grupo]
                    for item in prods:
                        # USANDO ID ÚNICO PARA CADA KEY
                        key_id = item['id']
                        with st.expander(f"📦 {item.get('nome', 'Produto Sem Nome')}"):
                            # POPOVER DE EDIÇÃO COM KEYS ÚNICAS
                            with st.popover("✏️ Editar"):
                                novo_nome = st.text_input("Nome", value=item.get('nome', ''), key=f"in_nome_{key_id}")
                                nova_foto = st.text_input("Foto URL", value=item.get('imagem', ''), key=f"in_img_{key_id}")
                                if st.button("💾 Salvar", key=f"btn_save_{key_id}"):
                                    item['nome'] = novo_nome
                                    item['imagem'] = nova_foto
                                    salvar_catalogo_produtos(catalogo)
                                    st.rerun()
                            
                            st.write(f"**Grupo:** {item.get('grupo_tema')}")
                            if item.get('imagem'):
                                st.image(item['imagem'], width=200)
                            else:
                                st.warning("Sem foto.")
                                
                            if st.button("🗑️ Excluir", key=f"btn_del_{key_id}"):
                                catalogo = [p for p in catalogo if p['id'] != key_id]
                                salvar_catalogo_produtos(catalogo)
                                st.rerun()

    # ZONA DE SEGURANÇA NO FINAL DA ABA DE CATÁLOGO
    if st.button("🔥 ZERAR TUDO"):
        zerar_todo_catalogo()
        st.rerun()
