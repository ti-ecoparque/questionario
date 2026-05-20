import streamlit as st
from supabase import create_client, Client
import pandas as pd
from fpdf import FPDF

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Puxa a senha definida nas Secrets do Streamlit Cloud
SENHA_CORRETA_RH = st.secrets["SENHA_PAINEL_RH"]

# --- FUNÇÃO PARA GERAR O PDF EM MEMÓRIA (UNIFICADA) ---
def gerar_pdf(df_filtrado, filtro_nome):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
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
    
    # Mapeamento técnico dos grupos de colunas
    grupos = {
        "1. Clareza de Funções e Responsabilidades": ["p01_clareza", "p02_clareza", "p03_clareza", "p04_clareza", "p05_clareza"],
        "2. Comunicação no Ambiente de Trabalho": ["p06_comunicacao", "p07_comunicacao", "p08_comunicacao", "p09_comunicacao", "p10_comunicacao"],
        "3. Relacionamento com a Liderança": ["p11_lideranca", "p12_lideranca", "p13_lideranca", "p14_lideranca", "p15_lideranca"],
        "4. Impacto Psicossocial": ["p16_psico", "p17_psico", "p18_psico"]
    }
    
    total_respostas = len(df_filtrado)
    
    # Varre os blocos numéricos gerando porcentagens E médias
    for grupo_nome, colunas in grupos.items():
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, tratar_texto(grupo_nome.upper()), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        
        # Calcula média do grupo inteiro
        grupo_media_geral = df_filtrado[colunas].mean().mean() if total_respostas > 0 else 0
        
        for col in colunas:
            if col in df_filtrado.columns:
                pdf.set_font("Helvetica", "B", 11)
                # Calcula a média individual da pergunta
                media_pergunta = df_filtrado[col].mean() if total_respostas > 0 else 0
                pdf.cell(0, 6, tratar_texto(f"Indicador: {col.upper()} (Média: {media_pergunta:.2f} de 5.00)"), ln=True)
                pdf.set_font("Helvetica", "", 10)
                
                contagem = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                votos_reais = df_filtrado[col].value_counts().to_dict()
                for o_id, qtd in votos_reais.items():
                    if o_id in contagem: contagem[o_id] = qtd
                
                detalhe_linha = "   "
                for opcao in range(1, 6):
                    qtd_votos = contagem[opcao]
                    perc_votos = (qtd_votos / total_respostas) * 100 if total_respostas > 0 else 0
                    detalhe_linha += f"Op{opcao}: {qtd_votos} ({perc_votos:.1f}%) | "
                
                pdf.multi_cell(0, 6, tratar_texto(detalhe_linha))
                pdf.ln(2)
        
        # Rodapé do grupo com a nota consolidada
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, tratar_texto(f"--> MÉDIA CONSOLIDADA DO GRUPO: {grupo_media_geral:.2f} de 5.00"), ln=True)
        pdf.ln(6)
            
    pdf.ln(5)
    
    # 2. RESPOSTAS DAS PERGUNTAS ABERTAS
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, tratar_texto("RESPOSTAS DAS PERGUNTAS ABERTAS"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    for campo, t_pergunta in [('p19_aberta_texto', 'Pergunta 19 Aberta:'), ('p20_aberta_texto', 'Pergunta 20 Aberta:')]:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, tratar_texto(t_pergunta), ln=True)
        pdf.set_font("Helvetica", "", 10)
        if campo in df_filtrado.columns:
            respostas = df_filtrado[campo].dropna()
            if len(respostas) > 0:
                for resp in respostas:
                    pdf.multi_cell(0, 6, tratar_texto(f"- {resp}"))
                    pdf.ln(2)
            else:
                pdf.cell(0, 6, tratar_texto("Nenhuma resposta registrada."), ln=True)
        pdf.ln(3)

    return bytearray(pdf.output())


# --- INTERFACE GRÁFICA ---
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
        
        lista_cnpjs = ["Todos os CNPJs"]
        if "cnpj" in df_total.columns:
            lista_cnpjs += list(df_total["cnpj"].dropna().unique())
        cnpj_selecionado = st.selectbox("Selecione a unidade / CNPJ para análise:", lista_cnpjs)

        opcoes_setor = {"Todos os Setores": None, "1 - Administrativo": 1, "2 - Operacional": 2}
        setor_selecionado = st.selectbox("Selecione o Setor:", list(opcoes_setor.keys()))
        setor_id = opcoes_setor[setor_selecionado]

        df = df_total.copy()
        if cnpj_selecionado != "Todos os CNPJs" and "cnpj" in df.columns:
            df = df[df["cnpj"] == cnpj_selecionado]
        if setor_id is not None and "setor" in df.columns:
            df = df[df["setor"] == setor_id]

        if len(df) > 0:
            pdf_bytes = gerar_pdf(df, f"{cnpj_selecionado} - {setor_selecionado}")
            st.download_button(
                label="📥 Baixar Relatório em PDF",
                data=bytes(pdf_bytes),
                file_name=f"Relatorio_RH_{cnpj_selecionado}_{setor_selecionado}.pdf",
                mime="application/pdf"
            )

        st.metric(f"Respondentes ({cnpj_selecionado} / {setor_selecionado})", len(df))
        st.markdown("---")

        if len(df) == 0:
            st.warning(f"Nenhum dado encontrado para o filtro selecionado.")
        else:
            # --- FUNÇÃO ATUALIZADA COM GRÁFICO % + MÉDIA DA PERGUNTA ---
            def plotar_pergunta_completa(titulo_pergunta, nome_coluna):
                st.markdown(f"##### {titulo_pergunta.upper()}")
                if nome_coluna in df.columns:
                    contagem = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                    votos_reais = df[nome_coluna].value_counts().to_dict()
                    for o_id, qtd in votos_reais.items():
                        if o_id in contagem: contagem[o_id] = qtd
                    
                    lista_votos = [contagem[1], contagem[2], contagem[3], contagem[4], contagem[5]]
                    total_rep = len(df)
                    lista_porcentagens = [(v / total_rep) * 100 if total_rep > 0 else 0 for v in lista_votos]
                    
                    df_grafico = pd.DataFrame({
                        "Porcentagem (%)": lista_porcentagens
                    }, index=["Discordo total (1)", "Discordo parcial (2)", "Neutro (3)", "Concordo parcial (4)", "Concordo total (5)"])
                    
                    st.bar_chart(df_grafico["Porcentagem (%)"])
                    
                    # CÁLCULO DA MÉDIA DA PERGUNTA INDIVIDUAL
                    media_individual = df[nome_coluna].mean()
                    
                    texto_resumo = " | ".join([f"Opção {i}: {contagem[i]} vts ({lista_porcentagens[i-1]:.1f}%)" for i in range(1, 6)])
                    st.caption(texto_resumo)
                    # Exibe a nota média da pergunta destacada em verde claro
                    st.success(f"🎯 **Média desta pergunta: {media_individual:.2f} de 5.00**")
                    st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.error(f"Coluna {nome_coluna} não localizada.")
            #
                        # Mapeamento dos blocos de colunas para cálculo das médias de grupo
            cols_clareza = ["p01_clareza", "p02_clareza", "p03_clareza", "p04_clareza", "p05_clareza"]
            cols_comunicacao = ["p06_comunicacao", "p07_comunicacao", "p08_comunicacao", "p09_comunicacao", "p10_comunicacao"]
            cols_lideranca = ["p11_lideranca", "p12_lideranca", "p13_lideranca", "p14_lideranca", "p15_lideranca"]
            cols_psico = ["p16_psico", "p17_psico", "p18_psico"]

            # --- GRUPO 1: CLAREZA ---
            st.subheader("🔍 1. CLAREZA DE FUNÇÕES E RESPONSABILIDADES")
            media_g1 = df[cols_clareza].mean().mean()
            porc_g1 = (media_g1 / 5.0) * 100
            st.info(f"📊 **MÉDIA GERAL DO GRUPO (CLAREZA): {media_g1:.2f} de 5.00 ({porc_g1:.1f}%)**")
            st.markdown("<br>", unsafe_allow_html=True)
            plotar_pergunta_completa("Pergunta 1: Sei exatamente quais são minhas responsabilidades no trabalho.", "p01_clareza")
            plotar_pergunta_completa("Pergunta 2: As expectativas sobre meu desempenho são claras.", "p02_clareza")
            plotar_pergunta_completa("Pergunta 3: Recebo orientações claras sobre como executar minhas atividades.", "p03_clareza")
            plotar_pergunta_completa("Pergunta 4: Sei a quem recorrer quando tenho dúvidas sobre minhas tarefas.", "p04_clareza")
            plotar_pergunta_completa("Pergunta 5: Mudanças nas minhas funções são comunicadas de forma clara.", "p05_clareza")

            # --- GRUPO 2: COMUNICAÇÃO ---
            st.subheader("🗣️ 2. COMUNICAÇÃO NO AMBIENTE DE TRABALHO")
            media_g2 = df[cols_comunicacao].mean().mean()
            porc_g2 = (media_g2 / 5.0) * 100
            st.info(f"📊 **MÉDIA GERAL DO GRUPO (COMUNICAÇÃO): {media_g2:.2f} de 5.00 ({porc_g2:.1f}%)**")
            st.markdown("<br>", unsafe_allow_html=True)
            plotar_pergunta_completa("Pergunta 6: A comunicação interna é clara e objetiva.", "p06_comunicacao")
            plotar_pergunta_completa("Pergunta 7: Recebo as informações necessárias para realizar meu trabalho adequadamente.", "p07_comunicacao")
            plotar_pergunta_completa("Pergunta 8: As informações importantes chegam em tempo hábil.", "p08_comunicacao")
            plotar_pergunta_completa("Pergunta 9: Sinto-me à vontade para expressar opiniões ou dificuldades.", "p09_comunicacao")
            plotar_pergunta_completa("Pergunta 10: Há abertura para diálogo no ambiente de trabalho.", "p10_comunicacao")

            # --- GRUPO 3: LIDERANÇA ---
            st.subheader("👔 3. RELACIONAMENTO COM A LIDERANÇA")
            media_g3 = df[cols_lideranca].mean().mean()
            porc_g3 = (media_g3 / 5.0) * 100
            st.info(f"📊 **MÉDIA GERAL DO GRUPO (LIDERANÇA): {media_g3:.2f} de 5.00 ({porc_g3:.1f}%)**")
            st.markdown("<br>", unsafe_allow_html=True)
            plotar_pergunta_completa("Pergunta 11: Meu gestor demonstra respeito no relacionamento com a equipe.", "p11_lideranca")
            plotar_pergunta_completa("Pergunta 12: Recebo feedbacks construtivos sobre meu trabalho.", "p12_lideranca")
            plotar_pergunta_completa("Pergunta 13: Meu gestor está disponível quando preciso de apoio.", "p13_lideranca")
            plotar_pergunta_completa("Pergunta 14: As decisões da liderança são comunicadas de forma transparente.", "p14_lideranca")
            plotar_pergunta_completa("Pergunta 15: Sinto-me tratado(a) de forma justa pela liderança.", "p15_lideranca")

            # --- GRUPO 4: PSICOSSOCIAL ---
            st.subheader("🧠 4. IMPACTO PSICOSSOCIAL")
            media_g4 = df[cols_psico].mean().mean()
            porc_g4 = (media_g4 / 5.0) * 100
            st.info(f"📊 **MÉDIA GERAL DO GRUPO (PSICOSSOCIAL): {media_g4:.2f} de 5.00 ({porc_g4:.1f}%)**")
            st.markdown("<br>", unsafe_allow_html=True)
            plotar_pergunta_completa("Pergunta 16: A falta de clareza ou falhas de comunicação já me causaram estresse no trabalho.", "p16_psico")
            plotar_pergunta_completa("Pergunta 17: O relacionamento com a liderança impacta meu bem-estar emocional.", "p17_psico")
            plotar_pergunta_completa("Pergunta 18: Já me senti sobrecarregado(a) devido à má comunicação ou orientação.", "p18_psico")

            st.markdown("---")

            # --- GRUPO 5: PERGUNTAS ABERTAS ---
            st.subheader("✍️ 5. RESPOSTAS DAS PERGUNTAS ABERTAS")
            tab1, tab2 = st.tabs(["Melhoria nas Funções (P19)", "Melhoria na Liderança/Comunicação (P20)"])
            with tab1:
                if 'p19_aberta_texto' in df.columns:
                    st.dataframe(df[['p19_aberta_texto']].dropna().rename(columns={'p19_aberta_texto': 'Respostas Computadas'}), use_container_width=True)
            with tab2:
                if 'p20_aberta_texto' in df.columns:
                    st.dataframe(df[['p20_aberta_texto']].dropna().rename(columns={'p20_aberta_texto': 'Respostas Computadas'}), use_container_width=True)
