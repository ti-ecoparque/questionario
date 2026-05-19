import streamlit as st
from supabase import create_client, Client
import pandas as pd

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Puxa a senha definida nas Secrets do Streamlit Cloud
SENHA_CORRETA_RH = st.secrets["SENHA_PAINEL_RH"]

st.title("📊 Painel de Resultados do RH")

# Controle de sessão para o login do RH
if "rh_autenticado" not in st.session_state:
    st.session_state.rh_autenticado = False

# Se o RH não estiver autenticado, mostra a tela de bloqueio
if not st.session_state.rh_autenticado:
    st.subheader("🔒 Acesso Restrito - Área de Gestão")
    senha_digitada = st.text_input("Digite a senha de acesso ao painel:", type="password")
    
    if st.button("Acessar Painel"):
        if senha_digitada == SENHA_CORRETA_RH:
            st.session_state.rh_autenticado = True
            st.success("Acesso liberado!")
            st.rerun()
        else:
            st.error("Senha incorreta. Acesso negado.")

# SE ESTIVER AUTENTICADO, MOSTRA OS GRÁFICOS DO SEU PAINEL FILTRADOS
else:
    st.caption("Dados consolidados de forma estritamente anônima")
    
    # Botão na barra lateral para deslogar do painel
    if st.sidebar.button("Sair / Bloquear"):
        st.session_state.rh_autenticado = False
        st.rerun()

    # Busca dados originais do banco
    res = supabase.table("respostas_questionario").select("*").execute()

    if len(res.data) == 0:
        st.info("Nenhuma resposta coletada até o momento.")
    else:
        df_total = pd.DataFrame(res.data)

        # --- ÁREA DE FILTRO POR CNPJ ---
        st.markdown("### 🏢 Filtrar Resultados")
        
        # Cria a lista de CNPJs únicos baseada nas respostas existentes no banco
        lista_cnpjs = ["Todos os CNPJs"]
        if "cnpj" in df_total.columns:
            lista_cnpjs += list(df_total["cnpj"].dropna().unique())
            
        cnpj_selecionado = st.selectbox("Selecione a unidade / CNPJ para análise:", lista_cnpjs)

        # Filtra o DataFrame dinamicamente de acordo com a seleção do usuário
        if cnpj_selecionado == "Todos os CNPJs" or "cnpj" not in df_total.columns:
            df = df_total
        else:
            df = df_total[df_total["cnpj"] == cnpj_selecionado]
        # ------------------------------------

        # Exibe a métrica total com base no filtro atual
        st.metric(f"Total de Respondentes ({cnpj_selecionado})", len(df))
        st.markdown("---")

        # Verifica se o CNPJ selecionado possui dados cadastrados antes de gerar gráficos
        if len(df) == 0:
            st.warning(f"Nenhum dado encontrado para o filtro: {cnpj_selecionado}")
        else:
            # Mapeamento dos grupos de colunas das 18 perguntas
            cols_clareza = ["p01_clareza", "p02_clareza", "p03_clareza", "p04_clareza", "p05_clareza"]
            cols_comunicacao = ["p06_comunicacao", "p07_comunicacao", "p08_comunicacao", "p09_comunicacao", "p10_comunicacao"]
            cols_lideranca = ["p11_lideranca", "p12_lideranca", "p13_lideranca", "p14_lideranca", "p15_lideranca"]
            cols_psico = ["p16_psico", "p17_psico", "p18_psico"]

            # 1. GRUPO: CLAREZA
            st.subheader("🔍 1. Clareza de Funções e Responsabilidades")
            media_clareza = df[cols_clareza].mean()
            st.bar_chart(media_clareza)
            st.caption(f"Média geral do grupo: {media_clareza.mean():.2f} de 5.00")

            # 2. GRUPO: COMUNICAÇÃO
            st.subheader("🗣️ 2. Comunicação no Ambiente de Trabalho")
            media_comunicacao = df[cols_comunicacao].mean()
            st.bar_chart(media_comunicacao)
            st.caption(f"Média geral do grupo: {media_comunicacao.mean():.2f} de 5.00")

            # 3. GRUPO: LIDERANÇA
            st.subheader("👔 3. Relacionamento com a Liderança")
            media_lideranca = df[cols_lideranca].mean()
            st.bar_chart(media_lideranca)
            st.caption(f"Média geral do grupo: {media_lideranca.mean():.2f} de 5.00")

            # 4. GRUPO: PSICOSSOCIAL
            st.subheader("🧠 4. Impacto Psicossocial")
            media_psico = df[cols_psico].mean()
            st.bar_chart(media_psico)
            st.caption(f"Média geral do grupo: {media_psico.mean():.2f} de 5.00")

            st.markdown("---")

            # 5. PERGUNTAS ABERTAS (FILTRADAS)
            st.subheader("✍️ 5. Respostas das Perguntas Abertas")
            
            tab1, tab2 = st.tabs(["Pontos Positivos (Pergunta A)", "Melhorias no Setor (Pergunta B)"])
            
            with tab1:
                if 'p19_aberta_texto' in df.columns:
                    df_p19 = df[['criado_em', 'p19_aberta_texto']].dropna()
                    st.dataframe(df_p19, use_container_width=True)
                    
            with tab2:
                if 'p20_aberta_texto' in df.columns:
                    df_p20 = df[['criado_em', 'p20_aberta_texto']].dropna()
                    st.dataframe(df_p20, use_container_width=True)
