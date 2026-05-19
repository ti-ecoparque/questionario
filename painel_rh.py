import streamlit as st
from supabase import create_client, Client
import pandas as pd

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📊 Painel de Resultados do RH")
st.caption("Dados consolidados de forma estritamente anônima")

# Busca dados do banco
res = supabase.table("respostas_questionario").select("*").execute()

if len(res.data) == 0:
    st.info("Nenhuma resposta coletada até o momento.")
else:
    df = pd.DataFrame(res.data)

    # Exibe métrica total
    st.metric("Total de Respondentes", len(df))

    # Gráfico Pergunta 1
    st.subheader("Clima de trabalho atual")
    p1_counts = df['pergunta_1'].value_counts()
    st.bar_chart(p1_counts)

    # Gráfico Pergunta 2
    st.subheader("Ferramentas necessárias para trabalhar")
    p2_counts = df['pergunta_2'].value_counts()
    st.pie_chart(p2_counts) # Disponível no Streamlit moderno

    # Tabela com as respostas de texto livre (Pergunta 3)
    st.subheader("Sugestões e Críticas Textuais")
    st.dataframe(df[['criado_em', 'pergunta_3']].dropna(), use_container_width=True)
