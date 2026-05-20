import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# Conexão com o Supabase usando secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📋 Questionario Avaliação Riscos Psicossociais")

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
    # Adicione o parâmetro format="DD/MM/YYYY" no final do componente
    data_nasc = st.date_input(
        "Sua data de nascimento / aniversário:", 
        min_value=datetime(1940, 1, 1),
        format="DD/MM/YYYY"
    )


    if st.button("Entrar"):
        if not cpf:
            st.error("Por favor, informe o CPF.")
        else:
            # Verifica se o funcionário existe na tabela do banco
            res = supabase.table("funcionarios").select("*").eq("cpf", cpf).execute()
            
            if len(res.data) == 0:
                st.error("CPF não localizado na base de dados do RH.")
            else:
                user = res.data[0] # Pega o primeiro registro encontrado
                
                # Gera todas as combinações possíveis com base na data que o usuário escolheu na tela
                formatos_possiveis = [
                    data_nasc.strftime("%Y-%m-%d"), # 1984-02-04 (Padrão do banco)
                    data_nasc.strftime("%d-%m-%Y"), # 04-02-1984 (Com traço BR)
                    data_nasc.strftime("%d%m%Y"),   # 04021984   (Apenas números)
                    data_nasc.strftime("%d/%m/%Y")  # 04/02/1984 (Com barra BR)
                ]
                
                # Pega a data exatamente como está escrita na coluna do Supabase
                data_do_banco = str(user["data_nascimento"]).strip()
                
                # Verifica se a data do banco bate com QUALQUER um dos formatos gerados
                if data_do_banco not in formatos_possiveis:
                    st.error("Data de nascimento incorreta.")
                elif user["ja_respondeu"]:
                    st.warning("Você já respondeu a este questionário anteriormente.")
                else:
                    # Se tudo estiver correto, define as variáveis de sessão
                    st.session_state.logado = True
                    st.session_state.cpf_usuario = cpf
                    st.session_state.cnpj_usuario = user.get("cnpj", None)
                    st.session_state.setor_usuario = user.get("setor", None)
                    st.rerun()


# --- TELA DO QUESTIONÁRIO (SÓ APARECE APÓS LOGIN CORRETO) ---
else:
    st.success("""
            Como parte das ações de prevenção e promoção da saúde e segurança no trabalho, informamos que estamos realizando uma avaliação de riscos psicossociais, conforme diretrizes da NR-1 (Gerenciamento de Riscos Ocupacionais).

            Para isso, disponibilizamos este questionário que tem como objetivo entender melhor aspectos do nosso ambiente de trabalho que podem impactar o bem-estar e a saúde mental de todos.

            📋 **Sobre o questionário:**
            - O preenchimento é rápido e simples
            - As respostas são confidenciais
            - Não há identificação individual dos participantes
            - Os dados serão utilizados apenas para melhorias internas

            🎯 **Sua contribuição é essencial para:**
            - Identificar oportunidades de melhoria no ambiente de trabalho
            - Prevenir situações de estresse e sobrecarga
            - Promover um ambiente mais saudável e equilibrado
            """)
    
    # 1. TÍTULO EM CAIXA ALTA (Usando o .upper())
    titulo_grupo1 = "🔍 1. Clareza de Funções e Responsabilidades"
    st.header(titulo_grupo1.upper())

    # --- PERGUNTA 1 ---
    txt_p01 = "1: Sei exatamente quais são minhas responsabilidades no trabalho."
    # Markdown com HTML (Aumenta o tamanho usando font-size)
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p01.upper()}</p>", unsafe_allow_html=True)
    # st.radio agora fica sem texto interno, servindo apenas para exibir as opções
    p01 = st.radio("", lista_opcoes, index=2, key="rad_p01", label_visibility="collapsed")

    # --- PERGUNTA 2 ---
    txt_p02 = "2: As expectativas sobre meu desempenho são claras."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p02.upper()}</p>", unsafe_allow_html=True)
    p02 = st.radio("", lista_opcoes, index=2, key="rad_p02", label_visibility="collapsed")

    # --- PERGUNTA 3 ---
    txt_p03 = "3: Recebo orientações claras sobre como executar minhas atividades."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p03.upper()}</p>", unsafe_allow_html=True)
    p03 = st.radio("", lista_opcoes, index=2, key="rad_p03", label_visibility="collapsed")

    # --- PERGUNTA 4 ---
    txt_p04 = "4: Sei a quem recorrer quando tenho dúvidas sobre minhas tarefas."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p04.upper()}</p>", unsafe_allow_html=True)
    p04 = st.radio("", lista_opcoes, index=2, key="rad_p04", label_visibility="collapsed")

    # --- PERGUNTA 5 ---
    txt_p05 = "5: Mudanças nas minhas funções são comunicadas de forma clara."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p05.upper()}</p>", unsafe_allow_html=True)
    p05 = st.radio("", lista_opcoes, index=2, key="rad_p05", label_visibility="collapsed")

    st.markdown("---")

    # --- GRUPO 2: COMUNICAÇÃO NO AMBIENTE DE TRABALHO ---
    titulo_grupo2 = "🗣️ 2. Comunicação no Ambiente de Trabalho"
    st.header(titulo_grupo2.upper())

    # --- PERGUNTA 6 ---
    txt_p06 = "6: A comunicação interna é clara e objetiva."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p06.upper()}</p>", unsafe_allow_html=True)
    p06 = st.radio("", lista_opcoes, index=2, key="rad_p06", label_visibility="collapsed")

    # --- PERGUNTA 7 ---
    txt_p07 = "7: Recebo as informações necessárias para realizar meu trabalho adequadamente."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p07.upper()}</p>", unsafe_allow_html=True)
    p07 = st.radio("", lista_opcoes, index=2, key="rad_p07", label_visibility="collapsed")

    # --- PERGUNTA 8 ---
    txt_p08 = "8: As informações importantes chegam em tempo hábil."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p08.upper()}</p>", unsafe_allow_html=True)
    p08 = st.radio("", lista_opcoes, index=2, key="rad_p08", label_visibility="collapsed")

    # --- PERGUNTA 9 ---
    txt_p09 = "9: Sinto-me à vontade para expressar opiniões ou dificuldades"
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p09.upper()}</p>", unsafe_allow_html=True)
    p09 = st.radio("", lista_opcoes, index=2, key="rad_p09", label_visibility="collapsed")

    # --- PERGUNTA 10 ---
    txt_p10 = "10: Há abertura para diálogo no ambiente de trabalho."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p10.upper()}</p>", unsafe_allow_html=True)
    p10 = st.radio("", lista_opcoes, index=2, key="rad_p10", label_visibility="collapsed")

    st.markdown("---")

    # --- GRUPO 3: RELACIONAMENTO COM A LIDERANÇA ---
    titulo_grupo3 = "👔 3. Relacionamento com a Liderança"
    st.header(titulo_grupo3.upper())

    # --- PERGUNTA 11 ---
    txt_p11 = "11: Meu gestor demonstra respeito no relacionamento com a equipe"
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p11.upper()}</p>", unsafe_allow_html=True)
    p11 = st.radio("", lista_opcoes, index=2, key="rad_p11", label_visibility="collapsed")

    # --- PERGUNTA 12 ---
    txt_p12 = "12: Recebo feedbacks construtivos sobre meu trabalho."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p12.upper()}</p>", unsafe_allow_html=True)
    p12 = st.radio("", lista_opcoes, index=2, key="rad_p12", label_visibility="collapsed")

    # --- PERGUNTA 13 ---
    txt_p13 = "13: Meu gestor está disponível quando preciso de apoio."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p13.upper()}</p>", unsafe_allow_html=True)
    p13 = st.radio("", lista_opcoes, index=2, key="rad_p13", label_visibility="collapsed")

    # --- PERGUNTA 14 ---
    txt_p14 = "14: As decisões da liderança são comunicadas de forma transparente."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p14.upper()}</p>", unsafe_allow_html=True)
    p14 = st.radio("", lista_opcoes, index=2, key="rad_p14", label_visibility="collapsed")

    # --- PERGUNTA 15 ---
    txt_p15 = "15: Sinto-me tratado(a) de forma justa pela liderança."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p15.upper()}</p>", unsafe_allow_html=True)
    p15 = st.radio("", lista_opcoes, index=2, key="rad_p15", label_visibility="collapsed")

    st.markdown("---")

    # --- GRUPO 4: IMPACTO PSICOSSOCIAL ---
    titulo_grupo4 = "🧠 4. Impacto Psicossocial"
    st.header(titulo_grupo4.upper())

    # --- PERGUNTA 16 ---
    txt_p16 = "16: A falta de clareza ou falhas de comunicação já me causaram estresse no trabalho."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p16.upper()}</p>", unsafe_allow_html=True)
    p16 = st.radio("", lista_opcoes, index=2, key="rad_p16", label_visibility="collapsed")

    # Nota de critério formatada em itálico e caixa alta discreta
    nota_criterio = "*(NOTA: O CRITÉRIO DE AVALIAÇÃO DA PERGUNTA 17 E 18 SEGUE O MESMO PADRÃO)*"
    st.markdown(nota_criterio)

    # --- PERGUNTA 17 ---
    txt_p17 = "17: O relacionamento com a liderança impacta meu bem-estar emocional."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p17.upper()}</p>", unsafe_allow_html=True)
    p17 = st.radio("", lista_opcoes, index=2, key="rad_p17", label_visibility="collapsed")

    # --- PERGUNTA 18 ---
    txt_p18 = "18: Já me senti sobrecarregado(a) devido à má comunicação ou orientação."
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p18.upper()}</p>", unsafe_allow_html=True)
    p18 = st.radio("", lista_opcoes, index=2, key="rad_p18", label_visibility="collapsed")

    st.markdown("---")

    # --- GRUPO 5: PERGUNTAS ABERTAS ---
    titulo_grupo5 = "✍️ 5. Perguntas Abertas (Opcionais)"
    st.header(titulo_grupo5.upper())

    # --- PERGUNTA 19 ---
    txt_p19 = "19: O que poderia melhorar a clareza de funções no seu trabalho?"
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p19.upper()}</p>", unsafe_allow_html=True)
    p19 = st.text_area("", key="txt_p19", label_visibility="collapsed")

    # --- PERGUNTA 20 ---
    txt_p20 = "20: O que poderia melhorar a comunicação ou o relacionamento com a liderança?"
    st.markdown(f"<p style='font-size:18px; font-weight:bold;'>{txt_p20.upper()}</p>", unsafe_allow_html=True)
    p20 = st.text_area("", key="txt_p20", label_visibility="collapsed")

    # --- BOTÃO DE ENVIO REAL ---
    if st.button("Finalizar e Enviar Questionário"):
        try:
            # 1. Monta o dicionário contendo as respostas e vinculando APENAS o CNPJ (Preserva o anonimato do CPF)
            dados_para_salvar = {
                "cnpj": st.session_state.cnpj_usuario,
                "setor": st.session_state.setor_usuario,
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
