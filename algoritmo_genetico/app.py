import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from algoritmo_genetico import OtimizadorBolsas

# Configuracao da Pagina
st.set_page_config(page_title="Gestão de Bolsas ENEM", layout="wide")

st.title("🎓 Otimização de Bolsas de Estudo - IA")
st.markdown("""
Esta ferramenta utiliza **Algoritmos Genéticos** para selecionar o grupo ideal de bolsistas.
Ajuste os critérios abaixo de acordo com a estratégia da fundação.
""")

# --- SIDEBAR: CONTROLES ---
st.sidebar.header("Critérios de Seleção")
st.sidebar.info("Defina a importância de cada fator (0 a 100). O sistema irá normalizar os pesos.")

p_notas = st.sidebar.slider("Performance Acadêmica", 0, 100, 50)
p_diversidade = st.sidebar.slider("Diversidade Social", 0, 100, 30)
p_regional = st.sidebar.slider("Cobertura Regional", 0, 100, 20)

# Botao de Acao
btn_executar = st.sidebar.button("🤖 Encontrar Bolsistas", type="primary")

# --- LÓGICA PRINCIPAL ---
if btn_executar:
    # 1. Normalizacao dos Pesos (Garante que a soma seja 1.0)
    total = p_notas + p_diversidade + p_regional
    if total == 0:
        st.error("A soma dos pesos não pode ser zero!")
    else:
        pesos_normalizados = {
            'notas': p_notas / total,
            'diversidade': p_diversidade / total,
            'regional': p_regional / total
        }
        
        st.write("---")
        st.subheader("🚀 Executando Otimização...")
        
        # Mostra os pesos reais usados
        col1, col2, col3 = st.columns(3)
        col1.metric("Peso: Notas", f"{pesos_normalizados['notas']:.2%}")
        col2.metric("Peso: Diversidade", f"{pesos_normalizados['diversidade']:.2%}")
        col3.metric("Peso: Regional", f"{pesos_normalizados['regional']:.2%}")

        # Localiza o arquivo de dados
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
        arquivo_dados = os.path.join(diretorio_atual, 'dados_enem_processados.csv')

        if not os.path.exists(arquivo_dados):
            st.error(f"Erro: Arquivo '{arquivo_dados}' não encontrado. Rode o script de preparação primeiro.")
        else:
            # Roda o Algoritmo com Spinner
            with st.spinner('O algoritmo genético está evoluindo as gerações... Aguarde.'):
                # Instancia passando os pesos da interface
                ga = OtimizadorBolsas(arquivo_dados, pesos=pesos_normalizados)
                melhor_indices, historico = ga.executar()
                
                # Prepara os dados finais
                df_resultado = ga.df.iloc[melhor_indices]

            st.success("Otimização Concluída!")

            # --- EXIBICAO DOS RESULTADOS ---
            tab1, tab2 = st.tabs(["📊 Análise da Evolução", "📋 Lista de Bolsistas"])

            with tab1:
                st.markdown("### Melhoria da Solução (Fitness) por Geração")
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(historico, color='green', marker='o', markersize=3)
                ax.set_xlabel("Gerações")
                ax.set_ylabel("Score de Aptidão")
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                
                st.info(f"Fitness Final Alcançado: **{historico[-1]:.4f}**")

            with tab2:
                st.markdown(f"### Grupo Selecionado ({len(df_resultado)} candidatos)")
                st.dataframe(df_resultado)
                
                # Botao de Download
                csv = df_resultado.to_csv(index=False, sep=';').encode('utf-8')
                st.download_button(
                    label="📥 Baixar Planilha Excel (CSV)",
                    data=csv,
                    file_name="bolsistas_selecionados.csv",
                    mime="text/csv",
                )