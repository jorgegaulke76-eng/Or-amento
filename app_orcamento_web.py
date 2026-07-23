import streamlit as st
import json
import os

# Configuração Inicial
st.set_page_config(page_title="Alphafest", layout="wide")

# Arquivos de dados
DB_CATALOGO = "banco_produtos_catalogo.json"

def carregar_dados():
    if os.path.exists(DB_CATALOGO):
        with open(DB_CATALOGO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_dados(dados):
    with open(DB_CATALOGO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Sidebar
menu = st.sidebar.radio("📌 SELECIONE O MÓDULO:", ["📄 Orçamentos & Pedidos", "📚 Gerador de Catálogo 3D"])

# ==========================================
# MÓDULO 1: ORÇAMENTOS
# ==========================================
if menu == "📄 Orçamentos & Pedidos":
    st.title("📄 Orçamentos & Pedidos")
    st.info("Módulo de orçamentos carregado.")

# ==========================================
# MÓDULO 2: CATÁLOGO
# ==========================================
elif menu == "📚 Gerador de Catálogo 3D":
    st.title("📚 Catálogo Digital")
    
    # Abas
    tab1, tab2 = st.tabs(["➕ Cadastrar", "🗂️ Ver Catálogo"])
    
    with tab1:
        st.subheader("Cadastro Manual")
        nome = st.text_input("Nome do Produto")
        tema = st.text_input("Tema/Grupo", value="Geral")
        img_url = st.text_input("URL da Imagem")
        preco = st.number_input("Preço", value=20.0)
        
        if st.button("💾 Salvar Produto"):
            dados = carregar_dados()
            novo_item = {
                "id": str(len(dados) + 1),
                "nome": nome,
                "grupo_tema": tema,
                "imagem": img_url,
                "preco_venda": preco
            }
            dados.append(novo_item)
            salvar_dados(dados)
            st.success("Salvo!")
            st.rerun()

    with tab2:
        catalogo = carregar_dados()
        if not catalogo:
            st.warning("Catálogo vazio.")
        else:
            grupos = sorted(list(set(p.get("grupo_tema", "Geral") for p in catalogo)))
            abas = st.tabs([f"🏷️ {g}" for g in grupos])
            
            for i, g in enumerate(grupos):
                with abas[i]:
                    for item in [p for p in catalogo if p.get("grupo_tema") == g]:
                        with st.expander(f"📦 {item.get('nome')}"):
                            if item.get('imagem'):
                                st.image(item['imagem'], width=150)
                            st.write(f"Preço: R$ {item.get('preco_venda')}")
                            if st.button("🗑️ Excluir", key=f"del_{item['id']}"):
                                nova_lista = [p for p in catalogo if p['id'] != item['id']]
                                salvar_dados(nova_lista)
                                st.rerun()

    if st.button("🔥 ZERAR TUDO"):
        salvar_dados([])
        st.rerun()
