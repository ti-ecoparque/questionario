import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# Conexão com o Supabase usando secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📋 Questionário Interno de RH")

# Controle de estado de login no Streamlit
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.cpf_usuario = ""
    st.session_state.cnpj_usuario = ""

# Dicionário de conversão de texto para o valor numérico que vai para o banco (1 a 5)
OPCOES_LIKERT = {
    "(1) Discordo totalmente": 1,
    "(2) Discordo parcialmente": 2,
    "(3) Nem concordo nem discordo": 3,
    "(4) Concordo parcialmente": 4,
    "(5) Concordo totalmente": 5
}
lista_opcoes = list(OPCOES_LIKERT.keys())


# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.subheader("Por favor, identifique-se para responder:")
    cpf = st.text_input("Digite seu CPF (apenas números):", max_chars=11)
    data_nasc = st.date_input("Sua data de nascimento / aniversário:", min_value=datetime(1940, 1, 1))

    if st.button("Entrar"):
        if not cpf:
            st.error("Por favor, informe o CPF.")
        else:
            # Verifica se o funcionário existe na tabela do banco
            res = supabase.table("funcionarios").select("*").eq("cpf", cpf).execute()
            
            if len(res.data) == 0:
                st.error("CPF não localizado na base de dados do RH.")
            else:
                user = res.data[0]
                
                # Valida a data de nascimento como senha
                if user["data_nascimento"] != str(data_nasc):
                    st.error("Data de nascimento incorreta.")
                elif user["ja_respondeu"]:
                    st.warning("Você já respondeu a este questionário anteriormente.")
                else:
                    # Se tudo estiver correto, define as variáveis de sessão
                    st.session_state.logado = True
                    st.session_state.cpf_usuario = cpf
                    st.session_state.cnpj_usuario = user.get("cnpj", None) # Captura o CNPJ cadastrado
                    st.rerun()


# --- TELA DO QUESTIONÁRIO (SÓ APARECE APÓS LOGIN CORRETO) ---
else:
    st.success("Identificação validada com sucesso! Suas respostas serão salvas de forma 100% anônima por unidade.")
    
    # --- GRUPO 1: CLAREZA DE FUNÇÕES E RESPONSABILIDADES ---
    st.header("🔍 1. Clareza de Funções e Responsabilidades")
    p01 = st.radio("Pergunta 1: Eu compreendo claramente quais são as minhas responsabilidades diárias.", lista_opcoes, index=2)
    p02 = st.radio("Pergunta 2: Sei exatamente o que a liderança espera do meu desempenho profissional.", lista_opcoes, index=2)
    p03 = st.radio("Pergunta 3: Os objetivos e metas do meu cargo são definidos de forma clara.", lista_opcoes, index=2)
    p04 = st.radio("Pergunta 4: Entendo como o meu trabalho diário contribui para o sucesso da empresa.", lista_opcoes, index=2)
    p05 = st.radio("Pergunta 5: Existe uma divisão justa de tarefas dentro da minha equipe de trabalho.", lista_opcoes, index=2)

    st.markdown("---")

    # --- GRUPO 2: COMUNICAÇÃO NO AMBIENTE DE TRABALHO ---
    st.header("🗣️ 2. Comunicação no Ambiente de Trabalho")
    p06 = st.radio("Pergunta 6: As informações importantes sobre a empresa são compartilhadas de forma transparente.", lista_opcoes, index=2)
    p07 = st.radio("Pergunta 7: Sinto que tenho liberdade para expor minhas opiniões e novas ideias.", lista_opcoes, index=2)
    p08 = st.radio("Pergunta 8: A comunicação entre os diferentes setores da empresa flui sem problemas.", lista_opcoes, index=2)
    p09 = st.radio("Pergunta 9: Recebo feedbacks construtivos com frequência sobre o meu trabalho.", lista_opcoes, index=2)
    p10 = st.radio("Pergunta 10: Os canais oficiais de comunicação da empresa funcionam de forma eficiente.", lista_opcoes, index=2)

    st.markdown("---")

    # --- GRUPO 3: RELACIONAMENTO COM A LIDERANÇA ---
    st.header("👔 3. Relacionamento com a Liderança")
    p11 = st.radio("Pergunta 11: Minha liderança direta me trata com respeito profissional e consideração.", lista_opcoes, index=2)
    p12 = st.radio("Pergunta 12: Sinto que posso confiar nas decisões tomadas pela minha liderança.", lista_opcoes, index=2)
    p13 = st.radio("Pergunta 13: O gestor está disponível para me apoiar quando enfrento dificuldades no trabalho.", lista_opcoes, index=2)
    p14 = st.radio("Pergunta 14: Minha liderança reconhece e valoriza os meus esforços e bons resultados.", lista_opcoes, index=2)
    p15 = st.radio("Pergunta 15: As decisões da gestão são explicadas de forma clara para a equipe.", lista_opcoes, index=2)

    st.markdown("---")

    # --- GRUPO 4: IMPACTO PSICOSSOCIAL ---
    st.header("🧠 4. Impacto Psicossocial")
    p16 = st.radio("Pergunta 16: Consigo equilibrar de forma saudável as demandas do trabalho com minha vida pessoal.", lista_opcoes, index=2)
    st.markdown("*(Nota: o critério de avaliação da pergunta 17 e 18 segue o mesmo padrão)*")
    p17 = st.radio("Pergunta 17: O ambiente de trabalho é psicologicamente seguro e livre de pressões desproporcionais.", lista_opcoes, index=2)
    p18 = st.radio("Pergunta 18: Sinto motivação e energia ao iniciar a minha jornada de trabalho nesta empresa.", lista_opcoes, index=2)

    st.markdown("---")

    # --- GRUPO 5: PERGUNTAS ABERTAS ---
    st.header("✍️ 5. Perguntas Abertas (Opcionais)")
    p19 = st.text_area("Pergunta Aberta A: Quais são os principais pontos positivos do ambiente de trabalho atual?")
    p20 = st.text_area("Pergunta Aberta B: O que você sugeriria para melhorar a rotina ou o clima no seu setor?")

    # --- BOTÃO DE ENVIO REAL ---
    if st.button("Finalizar e Enviar Questionário"):
        try:
            # 1. Monta o dicionário contendo as respostas e vinculando APENAS o CNPJ (Preserva o anonimato do CPF)
            dados_para_salvar = {
                "cnpj": st.session_state.cnpj_usuario,
                "p01_clareza": OPCOES_LIKERT[p01],
                "p02_clareza": OPCOES_LIKERT[p02],
                "p03_clareza": OPCOES_LIKERT[p03],
                "p04_clareza": OPCOES_LIKERT[p04],
                "p05_clareza": OPCOES_LIKERT[p05],
                
                "p06_comunicacao": OPCOES_LIKERT[p06],
                "p07_comunicacao": OPCOES_LIKERT[p07],
                "p08_comunicacao": OPCOES_LIKERT[p08],
                "p09_comunicacao": OPCOES_LIKERT[p09],
                "p10_comunicacao": OPCOES_LIKERT[p10],
                
                "p11_lideranca": OPCOES_LIKERT[p11],
                "p12_lideranca": OPCOES_LIKERT[p12],
                "p13_lideranca": OPCOES_LIKERT[p13],
                "p14_lideranca": OPCOES_LIKERT[p14],
                "p15_lideranca": OPCOES_LIKERT[p15],
                
                "p16_psico": OPCOES_LIKERT[p16],
                "p17_psico": OPCOES_LIKERT[p17],
                "p18_psico": OPCOES_LIKERT[p18],
                
                "p19_aberta_texto": p19 if p19.strip() != "" else None,
                "p20_aberta_texto": p20 if p20.strip() != "" else None
            }

            # 2. Envia de forma limpa para a tabela anônima
            supabase.table("respostas_questionario").insert(dados_para_salvar).execute()

            # 3. Altera o status do funcionário na tabela de cadastros para impedir novo envio
            supabase.table("funcionarios").update({"ja_respondeu": True}).eq("cpf", st.session_state.cpf_usuario).execute()

            st.balloons()
            st.success("Obrigado! Suas respostas foram salvas com sucesso de forma anônima.")
            
            # Limpa o estado da sessão para fechar a página com segurança
            st.session_state.logado = False
            st.session_state.cpf_usuario = ""
            st.session_state.cnpj_usuario = ""
            
        except Exception as e:
            st.error(f"Erro ao salvar dados no Supabase: {e}")
