# app.py
import streamlit as st
import pandas as pd
import PyPDF2
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="🍔 Agente Marketing Fast Food", layout="wide")
st.title("👨‍💼 Carlos Vega - Consultor de Marketing de Fast Food")

st.markdown("""
> 'O cardápio é a sua vitrine. Se não vende desejo, está vendendo menos.'  
> — Carlos Vega
""")

# Carregar histórico
if "historico" not in st.session_state:
    if os.path.exists("historico.csv"):
        try:
            st.session_state.historico = pd.read_csv("historico.csv")
        except pd.errors.EmptyDataError:
            st.session_state.historico = pd.DataFrame(columns=["nome", "itens", "data"])
    else:
        st.session_state.historico = pd.DataFrame(columns=["nome", "itens", "data"])

# Funções de leitura
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
        return texto.strip()
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

# Interface de upload
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
                with st.expander("🔍 Ver texto extraído"):
                    st.text_area("Conteúdo", raw_text[:2000], height=300)
            else:
                st.error("❌ Falha ao extrair texto do PDF.")
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

# --- Processar dados ---
produtos = []

if df is not None:
    # Padronizar colunas
    df.columns = [str(c).lower().replace('ç', 'c').replace('ã', 'a').replace('ó', 'o') for c in df.columns]
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
    linhas = [linha.strip() for linha in raw_text.split('\n') if linha.strip()]
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if 'R$' in linha or 'r$' in linha:
            preco_part = None
            if any(c.isdigit() for c in linha):
                preco_part = linha
            elif i + 1 < len(linhas) and any(c.isdigit() for c in linhas[i+1]):
                preco_part = linhas[i+1]
                i += 1
            preco = preco_part.replace('R$', '').replace('r$', '').strip() if preco_part else "???"

            nome_candidato = ""
            for j in range(i+1, min(i+6, len(linhas))):
                prox = linhas[j]
                if any(x in prox.lower() for x in ['/', 'pedaço', 'fatia', 'sabor', 'acompanha']):
                    continue
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
            i += 6
        else:
            i += 1

# --- Mostrar e analisar com IA (Google Gemini) ---
if produtos:
    st.subheader("🔍 Produtos Encontrados")
    st.dataframe(pd.DataFrame(produtos))

    if st.button("🎯 Gerar Análise de Marketing com IA"):
        st.subheader("🧠 Relatório do Especialista: Carlos Vega (com IA real)")

        lista_itens = "\n".join([f"• {p['nome']} | {p['preco']}" for p in produtos[:20]])
        prompt = f"""
Você é Carlos Vega, especialista em marketing de fast food com 20 anos de experiência.
Analise este cardápio com {len(produtos)} itens:

{lista_itens}

Dê:
1. Crítica direta dos nomes — são atrativos?
2. 3 sugestões de nomes poderosos (ex: 'Bacon Turbo', 'Cheddar Flame')
3. Uma descrição emocional com gatilhos mentais
4. Dica de combo ou upsell
5. Exemplo de rede que faz bem isso (ex: Madero, Burguer King)

Fale com autoridade, em português, máximo 200 palavras.
"""

        try:
            import google.generativeai as genai

            with st.spinner("Carlos Vega está analisando com inteligência artificial..."):

                # 🔑 Chave de API do Gemini
                # ⚠️ Recomendado: use Secrets no Streamlit Cloud
                try:
                    api_key = st.secrets["GEMINI_API_KEY"]
                except:
                    api_key = "AIzaSyAthybXPNx3oT5AWw9INwOX9A6BT10OEao"  # 👈 COLE SUA CHAVE AQUI (temporário)

                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)

                if response.text:
                    st.markdown(f"> {response.text}")
                else:
                    st.error("❌ A IA não conseguiu gerar uma resposta.")

        except Exception as e:
            st.error(f"❌ Erro ao conectar com Gemini: {e}")
            st.info("""
            🔧 Solução:
            1. Obtenha sua chave em: https://aistudio.google.com/app/apikey
            2. Adicione no `st.secrets` ou substitua `AIzaSyAthybXPNx3oT5AWw9INwOX9A6BT10OEao`
            """)

        # Salvar no histórico
        novo_registro = pd.DataFrame([{
            "nome": "Análise com IA",
            "itens": len(produtos),
            "data": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        st.session_state.historico = pd.concat([st.session_state.historico, novo_registro], ignore_index=True)
        st.session_state.historico.to_csv("historico.csv", index=False)

# --- Sidebar ---
st.sidebar.subheader("📌 Histórico de Análises")
if not st.session_state.historico.empty:
    st.sidebar.dataframe(st.session_state.historico[["nome", "itens", "data"]])
else:
    st.sidebar.info("Nenhuma análise feita ainda.")

st.sidebar.subheader("🧠 Ajude o agente a evoluir")
feedback = st.sidebar.radio("Essa análise foi útil?", ["", "Sim", "Não"], index=0)
if feedback == "Sim":
    st.sidebar.success("Obrigado! Isso ajuda o Carlos Vega a melhorar.")
elif feedback == "Não":
    st.sidebar.warning("Vamos ajustar para a próxima!")

