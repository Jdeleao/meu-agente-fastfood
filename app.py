# app.py
import streamlit as st
import pandas as pd
import PyPDF2
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Configuração
st.set_page_config(page_title="Agente Marketing Fast Food", layout="wide")
st.title("Carlos Vega - Consultor de Marketing de Fast Food")

st.markdown("""
> 'O cardapio e a sua vitrine. Se nao vende desejo, esta vendendo menos.'  
> -- Carlos Vega
""")

# Carregar historico
if "historico" not in st.session_state:
    if os.path.exists("historico.csv"):
        st.session_state.historico = pd.read_csv("historico.csv")
    else:
        st.session_state.historico = pd.DataFrame(columns=["nome", "itens", "data"])

# Funcoes
def ler_csv_ou_excel(uploaded_file):
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return None

def ler_pdf(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return None

def extrair_de_link(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        for script in soup(["script", "style"]): 
            script.decompose()
        texto = soup.get_text()
        linhas = [linha.strip() for linha in texto.splitlines() if len(linha.strip()) > 10]
        return "\n".join(linhas[:500])
    except Exception as e:
        st.error(f"Erro ao acessar o link: {e}")
        return None

# --- Interface ---
st.subheader("📥 Envie seu cardápio (PDF, Planilha ou Link)")
input_type = st.radio("Como deseja enviar?", [
    "📤 Enviar arquivo (PDF, Excel, CSV)",
    "🔗 Colar link do cardápio online"
])

df = None
raw_text = None

if input_type == "📤 Enviar arquivo (PDF, Excel, CSV)":
    uploaded_file = st.file_uploader("Escolha um arquivo", type=["pdf", "csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".pdf"):
            raw_text = ler_pdf(uploaded_file)
            if raw_text:
                st.success("✅ PDF carregado!")
                with st.expander("🔍 Ver texto extraído do PDF"):
                    st.text_area("Texto encontrado", raw_text[:2000], height=300)
            else:
                st.error("❌ Não foi possível extrair texto do PDF.")
        else:
            df = ler_csv_ou_excel(uploaded_file)
            if df is not None:
                st.success("✅ Planilha carregada!")

elif input_type == "🔗 Colar link do cardápio online":
    url = st.text_input("Cole o link (ex: ifood, site)")
    if url:
        raw_text = extrair_de_link(url)
        if raw_text:
            st.success("✅ Página carregada!")
            # Descomente abaixo se quiser ver o texto extraído do link
            # with st.expander("Ver conteúdo da página"):
            #     st.text_area("Texto", raw_text[:2000], height=300)

# --- Processar dados ---
produtos = []

if df is not None:
    # Tratar planilha (CSV ou Excel)
    df.columns = [c.lower().replace('ç', 'c').replace('ã', 'a').replace('ó', 'o') for c in df.columns]
    nome_col = 'nome' if 'nome' in df.columns else df.columns[0]
    preco_col = 'preco' if 'preco' in df.columns else 'preço' if 'preço' in df.columns else df.columns[1]
    desc_col = 'descricao' if 'descricao' in df.columns else 'descrição' if 'descrição' in df.columns else None

    for _, row in df.iterrows():
        produtos.append({
            "nome": str(row[nome_col]),
            "preco": row[preco_col],
            "descricao": str(row[desc_col]) if desc_col else "Sem descrição"
        })

elif raw_text:
    # Extrair produtos do texto do PDF
    linhas = [linha.strip() for linha in raw_text.split('\n') if linha.strip()]
    i = 0
    while i < len(linhas):
        linha = linhas[i]

        # Procurar "R$" seguido de valor
        if 'R$' in linha or 'r$' in linha:
            preco_part = None
            # Verificar se o preço está na mesma linha
            if any(c.isdigit() for c in linha):
                preco_part = linha
            # Ou na próxima linha
            elif i + 1 < len(linhas) and any(c.isdigit() for c in linhas[i+1]):
                preco_part = linhas[i+1]
                i += 1  # pular a linha do preço

            preco = preco_part.replace('R$', '').replace('r$', '').strip() if preco_part else "???"

            # Procurar nome nas próximas linhas
            nome_candidato = ""
            for j in range(i+1, min(i+6, len(linhas))):
                prox = linhas[j]
                # Ignorar linhas de detalhe
                if any(x in prox.lower() for x in ['/', 'pedaço', 'fatia', 'sabor', 'acompanha', 'broto']):
                    continue
                # Se tem texto bom, usa como nome
                if len(prox) > 10 and not prox.replace(",", "").replace(".", "").isdigit():
                    nome_candidato = prox
                    break

            if not nome_candidato:
                nome_candidato = "Item detectado"

            produtos.append({
                "nome": nome_candidato,
                "preco": f"R$ {preco}",
                "descricao": f"{nome_candidato} - R$ {preco}"
            })
            i += 6  # pular para evitar duplicação
        else:
            i += 1

# Mostrar resultados
if produtos:
    st.subheader("Produtos Encontrados")
    st.dataframe(pd.DataFrame(produtos))

    if st.button("Gerar Analise de Marketing"):
        st.subheader("Relatorio do Especialista: Carlos Vega")
        st.markdown(f"""
        ### Diagnostico Geral do Cardapio

        Seu cardapio tem **{len(produtos)} itens**.

        - **Nomes dos produtos:** Funcionais, mas sem emocao.
          Ex: "{produtos[0]['nome']}" -> precisa de mais desejo.

        - **Dicas de melhoria:**
          1. **Nomes marcantes:**
             - "Hamburguer com Queijo" -> "Cheddar Turbo"
             - "Refrigerante" -> "Gelo Total"

          2. **Descricoes que vendem:**
             "Nosso {produtos[0]['nome']} e grelhado na hora, com queijo derretido e molho secreto."

          3. **Crie combos:** Aumente o ticket medio.

          4. **Posicionamento de preco:** Destaque qualidade ou economia.

          5. **Inspire-se:** Burguer King (nomes fortes), Giraffas (historias).

        ### Conclusao

        Voce tem um bom cardapio, mas ele nao esta vendendo desejo.
        Pequenas mudancas podem aumentar suas vendas em 20% ou mais.
        """)

        # Salvar no historico
        novo = pd.DataFrame([{
            "nome": "Cardapio analisado",
            "itens": len(produtos),
            "data": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        st.session_state.historico = pd.concat([st.session_state.historico, novo], ignore_index=True)
        st.session_state.historico.to_csv("historico.csv", index=False)

# Sidebar
st.sidebar.subheader("Historico")
if not st.session_state.historico.empty:
    st.sidebar.dataframe(st.session_state.historico[["nome", "itens", "data"]])
else:
    st.sidebar.info("Nenhuma analise feita.")

st.sidebar.subheader("Feedback")
util = st.sidebar.radio("Util?", ["", "Sim", "Nao"], index=0)
if util == "Sim":
    st.sidebar.success("Obrigado pelo feedback!")
elif util == "Nao":
    st.sidebar.warning("Vamos melhorar!")