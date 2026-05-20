import streamlit as st
from supabase import create_client, Client
import pandas as pd
from fpdf import FPDF
import io

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SENHA_CORRETA_RH = st.secrets["SENHA_PAINEL_RH"]

# --- FUNÇÃO PARA GERAR O PDF EM MEMÓRIA ---
def gerar_pdf(df_filtrado, filtro_nome):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Função interna para limpar o texto e garantir compatibilidade com latin-1
    def tratar_texto(texto):
        if not texto: 
            return ""
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Cabeçalho do Documento
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, tratar_texto("Relatório Estatístico de Clima Organizacional - RH"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, tratar_texto(f"Filtro Aplicado: {filtro_nome}"), ln=True, align="C")
    pdf.cell(0, 8, tratar_texto(f"Volume de Amostragem: {len(df_filtrado)} respondentes"), ln=True, align="C")
    pdf.ln(10)
    
    # 1. DISTRIBUIÇÃO PERCENTUAL DAS PERGUNTAS OBJETIVAS
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, tratar_texto("DISTRIBUIÇÃO PERCENTUAL POR PERGUNTA (1 a 5)"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Lista com mapeamento técnico exato das 18 colunas do seu banco
    todas_colunas = [
        f"p{str(i).zfill(2)}" + ("_clareza" if i<=5 else "_comunicacao" if i<=10 else "_lideranca" if i<=15 else "_psico")
        for i in range(1, 19)
    ]
    
    total_respostas = len(df_filtrado)
    
    # Varre cada uma das 18 colunas numéricas calculando a porcentagem
    for col in todas_colunas:
        if col in df_filtrado.columns:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, tratar_texto(f"Indicador: {col.upper()}"), ln=True)
            pdf.set_font("Helvetica", "", 10)
            
            # CORREÇÃO AQUI: Garante o fechamento correto do reindex com fillvalue=0
            contagem = df_filtrado[col].value_counts().reindex([1, 2, 3, 4, 5], fillvalue=0)
            
            detalhe_linha = "   "
            for opcao in range(1, 6):
                qtd_votos = contagem[opcao]
                perc_votos = (qtd_votos / total_respostas) * 100 if total_respostas > 0 else 0
                detalhe_linha += f"Opção {opcao}: {qtd_votos} vts ({perc_votos:.1f}%)   |   "
            
            pdf.multi_cell(0, 6, tratar_texto(detalhe_linha))
            pdf.ln(3)
            
    pdf.ln(5)
    
    # 2. RESPOSTAS DAS PERGUNTAS ABERTAS
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, tratar_texto("RESPOSTAS DAS PERGUNTAS ABERTAS"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Pergunta 19 Aberta
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, tratar_texto("Pergunta 19 Aberta:"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    if 'p19_aberta_texto' in df_filtrado.columns:
        respostas_p19 = df_filtrado['p19_aberta_texto'].dropna()
        if len(respostas_p19) > 0:
            for resp in respostas_p19:
                pdf.multi_cell(0, 6, tratar_texto(f"- {resp}"))
                pdf.ln(2)
        else:
            pdf.cell(0, 6, tratar_texto("Nenhuma resposta registrada."), ln=True)
            
    pdf.ln(5)
    
    # Pergunta 20 Aberta
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, tratar_texto("Pergunta 20 Aberta:"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    if 'p20_aberta_texto' in df_filtrado.columns:
        respostas_p20 = df_filtrado['p20_aberta_texto'].dropna()
        if len(respostas_p20) > 0:
            for resp in respostas_p20:
                pdf.multi_cell(0, 6, tratar_texto(f"- {resp}"))
                pdf.ln(2)
        else:
            pdf.cell(0, 6, tratar_texto("Nenhuma resposta registrada."), ln=True)

    # Retorna explicitamente em formato de string de bytes para o Streamlit
    return pdf.output()


# --- CODIGOS DA INTERFACE ---
st.title("📊 Painel de Resultados do RH")

if "rh_autenticado" not in st.session_state:
    st.session_state.rh_autenticado = False

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

else:
    st.caption("Dados consolidados de forma estritamente anônima")
    
    if st.sidebar.button("Sair / Bloquear"):
        st.session_state.rh_autenticado = False
        st.rerun()

    res = supabase.table("respostas_questionario").select("*").execute()

    if len(res.data) == 0:
        st.info("Nenhuma resposta coletada até o momento.")
    else:
        df_total = pd.DataFrame(res.data)

        st.markdown("### 🏢 Filtrar Resultados")
        
        # 1. FILTRO DE CNPJ
        lista_cnpjs = ["Todos os CNPJs"]
        if "cnpj" in df_total.columns:
            lista_cnpjs += list(df_total["cnpj"].dropna().unique())
        cnpj_selecionado = st.selectbox("Selecione a unidade / CNPJ para análise:", lista_cnpjs)

        # 2. FILTRO DE SETOR
        opcoes_setor = {
            "Todos os Setores": None,
            "1 - Administrativo": 1,
            "2 - Operacional": 2
        }
        setor_selecionado = st.selectbox("Selecione o Setor:", list(opcoes_setor.keys()))
        setor_id = opcoes_setor[setor_selecionado]

        # --- APLICAÇÃO DOS FILTROS COMBINADOS NO DATAFRAME ---
        df = df_total.copy()
        
        if cnpj_selecionado != "Todos os CNPJs" and "cnpj" in df.columns:
            df = df[df["cnpj"] == cnpj_selecionado]
            
        if setor_id is not None and "setor" in df.columns:
            df = df[df["setor"] == setor_id]
        # ----------------------------------------------------

        # Botão de exportar PDF atualizado para usar o 'df' com os dois filtros aplicados
        if len(df) > 0:
            pdf_bytes = gerar_pdf(df, f"{cnpj_selecionado} - {setor_selecionado}")
            st.download_button(
                label="📥 Baixar Relatório em PDF",
                data=bytes(pdf_bytes),
                file_name=f"Relatorio_RH_{cnpj_selecionado}_{setor_selecionado}.pdf",
                mime="application/pdf"
            )

        # Exibe a métrica total atualizada com os dois filtros
        st.metric(f"Respondentes ({cnpj_selecionado} / {setor_selecionado})", len(df))
        st.markdown("---")

        if len(df) == 0:
            st.warning(f"Nenhum dado encontrado para o filtro selecionado.")
        else:
            # --- FUNÇÃO INTERNA PARA GERAR OS GRÁFICOS DE PORCENTAGEM (0-100%) ---
            def plotar_pergunta_porcentagem(titulo_pergunta, nome_coluna):
                st.markdown(f"##### {titulo_pergunta.upper()}")
                if nome_coluna in df.columns:
                    # Conta os votos e garante que apareçam as opções de 1 a 5 (mesmo se tiverem 0 votos)
                    contagem = df[nome_coluna].value_counts().reindex([1, 2, 3, 4, 5], fillvalue=0)
                    
                    # Transforma em porcentagem com base no total de respondentes filtrados
                    porcentagem = (contagem / len(df)) * 100
                    
                    # Monta o DataFrame estruturado para o gráfico
                    df_grafico = pd.DataFrame({
                        "Porcentagem (%)": porcentagem.values
                    }, index=["Discordo totalmente (1)", "Discordo parcialmente (2)", "Nem concordo/discordo (3)", "Concordo parcialmente (4)", "Concordo totalmente (5)"])
                    
                    # Renderiza o gráfico de barras vertical (0 a 100%)
                    st.bar_chart(df_grafico["Porcentagem (%)"])
                    
                    # Exibe a legenda textual com a quantidade exata de votos e a respectiva porcentagem
                    texto_resumo = " | ".join([f"Opção {i}: {contagem[i]} votos ({porcentagem[i]:.1f}%)" for i in range(1, 6)])
                    st.caption(texto_resumo)
                    st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.error(f"Coluna {nome_coluna} não localizada no banco de dados.")

            # --- GRUPO 1: CLAREZA ---
            st.subheader("🔍 1. Clareza de Funções e Responsabilidades")
            plotar_pergunta_porcentagem("Pergunta 1: Eu compreendo claramente quais são as minhas responsabilidades diárias.", "p01_clareza")
            plotar_pergunta_porcentagem("Pergunta 2: Sei exatamente o que a liderança espera do meu desempenho profissional.", "p02_clareza")
            plotar_pergunta_porcentagem("Pergunta 3: Os objetivos e metas do meu cargo são definidos de forma clara.", "p03_clareza")
            plotar_pergunta_porcentagem("Pergunta 4: Entendo como o meu trabalho diário contribui para o sucesso da empresa.", "p04_clareza")
            plotar_pergunta_porcentagem("Pergunta 5: Existe uma division justa de tarefas dentro da minha equipe de trabalho.", "p05_clareza")

            # --- GRUPO 2: COMUNICAÇÃO ---
            st.subheader("🗣️ 2. Comunicação no Ambiente de Trabalho")
            plotar_pergunta_porcentagem("Pergunta 6: As informações importantes sobre a empresa são compartilhadas de forma transparente.", "p06_comunicacao")
            plotar_pergunta_porcentagem("Pergunta 7: Sinto que tenho liberdade para expor minhas opiniões e novas ideias.", "p07_comunicacao")
            plotar_pergunta_porcentagem("Pergunta 8: A comunicação entre os diferentes setores da empresa flui sem problemas.", "p08_comunicacao")
            plotar_pergunta_porcentagem("Pergunta 9: Recebo feedbacks construtivos com frequência sobre o meu trabalho.", "p09_comunicacao")
            plotar_pergunta_porcentagem("Pergunta 10: Os canais oficiais de comunicação da empresa funcionam de forma eficiente.", "p10_comunicacao")

            # --- GRUPO 3: LIDERANÇA ---
            st.subheader("👔 3. Relacionamento com a Liderança")
            plotar_pergunta_porcentagem("Pergunta 11: Minha liderança direta me trata com respeito profissional e consideração.", "p11_lideranca")
            plotar_pergunta_porcentagem("Pergunta 12: Sinto que posso confiar nas decisões tomadas pela minha liderança.", "p12_lideranca")
            plotar_pergunta_porcentagem("Pergunta 13: O gestor está disponível para me apoiar quando enfrento dificuldades no trabalho.", "p13_lideranca")
            plotar_pergunta_porcentagem("Pergunta 14: Minha liderança reconhece e valoriza os meus esforços e bons resultados.", "p14_lideranca")
            plotar_pergunta_porcentagem("Pergunta 15: As decisões da gestão são explicadas de forma clara para a equipe.", "p15_lideranca")

            # --- GRUPO 4: PSICOSSOCIAL ---
            st.subheader("🧠 4. Impacto Psicossocial")
            plotar_pergunta_porcentagem("Pergunta 16: Consigo equilibrar de forma saudável as demandas do trabalho com minha vida pessoal.", "p16_psico")
            plotar_pergunta_porcentagem("Pergunta 17: O ambiente de trabalho é psicologicamente seguro e livre de pressões desproporcionais.", "p17_psico")
            plotar_pergunta_porcentagem("Pergunta 18: Sinto motivação e energia ao iniciar a minha jornada de trabalho nesta empresa.", "p18_psico")

            st.markdown("---")

            # --- GRUPO 5: PERGUNTAS ABERTAS (LIMPAS SEM DATA) ---
            st.subheader("✍️ 5. Respostas das Perguntas Abertas")
            tab1, tab2 = st.tabs(["Pergunta 19 Aberta", "Pergunta 20 Aberta "])
            
            with tab1:
                if 'p19_aberta_texto' in df.columns:
                    df_p19 = df[['p19_aberta_texto']].dropna()
                    df_p19.columns = ["Respostas Computadas"]
                    st.dataframe(df_p19, use_container_width=True)
                    
            with tab2:
                if 'p20_aberta_texto' in df.columns:
                    df_p20 = df[['p20_aberta_texto']].dropna()
                    df_p20.columns = ["Respostas Computadas"]
                    st.dataframe(df_p20, use_container_width=True)
