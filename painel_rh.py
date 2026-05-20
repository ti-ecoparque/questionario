import streamlit as st
from supabase import create_client, Client
import pandas as pd
from fpdf import FPDF
import io

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SENHA_CORRETA_RH = st.secrets["SENHA_PAINEL_RH"]

# --- FUNÇÃO PARA GERAR O PDF EM MEMÓRIA (NATIVA E COMPATÍVEL COM NUVEM) ---
def gerar_pdf(df_filtrado, cnpj_nome):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Função interna para limpar o texto e garantir compatibilidade com latin-1
    def tratar_texto(texto):
        if not texto:
            return ""
        # Remove caracteres que quebram o PDF padrão, mantendo acentuação básica PT-BR
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Título Principal (Usando a fonte core 'Helvetica' nativa do PDF)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, tratar_texto("Relatório de Clima Organizacional - RH"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, tratar_texto(f"Unidade / CNPJ: {cnpj_nome}"), ln=True, align="C")
    pdf.cell(0, 5, tratar_texto(f"Total de Respondentes: {len(df_filtrado)}"), ln=True, align="C")
    pdf.ln(10)
    
    # Definição dos grupos de perguntas para iterar
    grupos = {
        "1. Clareza de Funções e Responsabilidades": ["p01_clareza", "p02_clareza", "p03_clareza", "p04_clareza", "p05_clareza"],
        "2. Comunicação no Ambiente de Trabalho": ["p06_comunicacao", "p07_comunicacao", "p08_comunicacao", "p09_comunicacao", "p10_comunicacao"],
        "3. Relacionamento com a Liderança": ["p11_lideranca", "p12_lideranca", "p13_lideranca", "p14_lideranca", "p15_lideranca"],
        "4. Impacto Psicossocial": ["p16_psico", "p17_psico", "p18_psico"]
    }
    
    # 1. Escreve as Médias das Perguntas Objetivas
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, tratar_texto("MÉDIAS DAS RESPOSTAS OBJETIVAS (Escala de 1 a 5)"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    for grupo_nome, colunas in grupos.items():
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, tratar_texto(grupo_nome), ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        # Calcula médias do bloco
        medias = df_filtrado[colunas].mean()
        for col in colunas:
            nota = medias.get(col, 0)
            pdf.cell(0, 6, tratar_texto(f"   - {col.upper()}: {nota:.2f} de 5.00"), ln=True)
        
        pdf.cell(0, 6, tratar_texto(f"   -> Média Geral do Bloco: {medias.mean():.2f}"), ln=True)
        pdf.ln(4)
        
    pdf.ln(5)
    
    # 2. Escreve as Perguntas Abertas
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, tratar_texto("RESPOSTAS DAS PERGUNTAS ABERTAS"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Pergunta A
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
    
    # Pergunta B
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, tratar_texto("Pergunta 20 Aberta"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    if 'p20_aberta_texto' in df_filtrado.columns:
        respostas_p20 = df_filtrado['p20_aberta_texto'].dropna()
        if len(respostas_p20) > 0:
            for resp in respostas_p20:
                pdf.multi_cell(0, 6, tratar_texto(f"- {resp}"))
                pdf.ln(2)
        else:
            pdf.cell(0, 6, tratar_texto("Nenhuma resposta registrada."), ln=True)

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
        
        # 1. FILTRO DE CNPJ (Existente)
        lista_cnpjs = ["Todos os CNPJs"]
        if "cnpj" in df_total.columns:
            lista_cnpjs += list(df_total["cnpj"].dropna().unique())
        cnpj_selecionado = st.selectbox("Selecione a unidade / CNPJ para análise:", lista_cnpjs)

        # 2. NOVO FILTRO DE SETOR
        opcoes_setor = {
            "Todos os Setores": None,
            "1 - Administrativo": 1,
            "2 - Operacional": 2
        }
        setor_selecionado = st.selectbox("Selecione o Setor:", list(opcoes_setor.keys()))
        setor_id = opcoes_setor[setor_selecionado]

        # --- APLICAÇÃO DOS FILTROS COMBINADOS NO DATAFRAME ---
        df = df_total.copy()
        
        # Filtra por CNPJ se não for "Todos"
        if cnpj_selecionado != "Todos os CNPJs" and "cnpj" in df.columns:
            df = df[df["cnpj"] == cnpj_selecionado]
            
        # Filtra por Setor se não for "Todos"
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
            st.warning(f"Nenhum dado encontrado para o filtro: {cnpj_selecionado}")
        else:
            cols_clareza = ["p01_clareza", "p02_clareza", "p03_clareza", "p04_clareza", "p05_clareza"]
            cols_comunicacao = ["p06_comunicacao", "p07_comunicacao", "p08_comunicacao", "p09_comunicacao", "p10_comunicacao"]
            cols_lideranca = ["p11_lideranca", "p12_lideranca", "p13_lideranca", "p14_lideranca", "p15_lideranca"]
            cols_psico = ["p16_psico", "p17_psico", "p18_psico"]

            st.subheader("🔍 1. Clareza de Funções e Responsabilidades")
            media_clareza = df[cols_clareza].mean()
            st.bar_chart(media_clareza)
            st.caption(f"Média geral do grupo: {media_clareza.mean():.2f} de 5.00")

            st.subheader("🗣️ 2. Comunicação no Ambiente de Trabalho")
            media_comunicacao = df[cols_comunicacao].mean()
            st.bar_chart(media_comunicacao)
            st.caption(f"Média geral do grupo: {media_comunicacao.mean():.2f} de 5.00")

            st.subheader("👔 3. Relacionamento com a Liderança")
            media_lideranca = df[cols_lideranca].mean()
            st.bar_chart(media_lideranca)
            st.caption(f"Média geral do grupo: {media_lideranca.mean():.2f} de 5.00")

            st.subheader("🧠 4. Impacto Psicossocial")
            media_psico = df[cols_psico].mean()
            st.bar_chart(media_psico)
            st.caption(f"Média geral do grupo: {media_psico.mean():.2f} de 5.00")

            st.markdown("---")

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
