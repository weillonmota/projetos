import pandas as pd
import numpy as np
import random
import os
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Dict, Optional

# --- CONFIGURACOES DO PROJETO ---
TAMANHO_GRUPO = 100        
TAMANHO_POPULACAO = 20     
GERACOES = 100             
TAXA_MUTACAO = 0.05        
TAXA_CROSSOVER = 0.8       

class OtimizadorBolsas:
    def __init__(self, caminho_dados: str, pesos: Optional[Dict[str, float]] = None):
        """
        Inicializa o otimizador.
        :param pesos: Dicionario com chaves 'notas', 'diversidade', 'regional'. 
                      Se None, usa o padrao do PDF.
        """
        # Define pesos padrao se nao forem passados
        if pesos is None:
            self.pesos = {'notas': 0.5, 'diversidade': 0.3, 'regional': 0.2}
        else:
            self.pesos = pesos

        # Leitura com ponto e virgula
        self.df = pd.read_csv(caminho_dados, sep=';', encoding='latin1')
        self.indices_disponiveis = self.df.index.tolist()
        self.max_nota = 1000 
        print(f"Dados carregados. Pesos: {self.pesos}")

    def calcular_fitness(self, cromossomo: List[int]) -> float:
        grupo = self.df.iloc[cromossomo]

        # 1. Performance Academica
        cols_notas = ['NU_NOTA_MT', 'NU_NOTA_CN', 'NU_NOTA_LC', 'NU_NOTA_CH', 'NU_NOTA_REDACAO']
        media_grupo = grupo[cols_notas].mean().mean()
        score_notas = media_grupo / self.max_nota

        # 2. Diversidade Socioeconomica
        div_renda = len(grupo['Q006'].unique()) / len(self.df['Q006'].unique())
        div_escola = len(grupo['TP_ESCOLA'].unique()) / len(self.df['TP_ESCOLA'].unique())
        div_raca = len(grupo['TP_COR_RACA'].unique()) / len(self.df['TP_COR_RACA'].unique())
        score_diversidade = (div_renda + div_escola + div_raca) / 3

        # 3. Cobertura Regional
        qtd_estados = len(grupo['SG_UF_RESIDENCIA'].unique())
        total_estados = 27
        score_regional = qtd_estados / total_estados

        # Formula Final usando os PESOS DINAMICOS
        fitness = (self.pesos['notas'] * score_notas) + \
                  (self.pesos['diversidade'] * score_diversidade) + \
                  (self.pesos['regional'] * score_regional)
        return fitness

    def gerar_individuo(self) -> List[int]:
        return random.sample(self.indices_disponiveis, TAMANHO_GRUPO)

    def crossover(self, pai1: List[int], pai2: List[int]) -> Tuple[List[int], List[int]]:
        ponto = random.randint(1, TAMANHO_GRUPO - 1)
        filho1 = pai1[:ponto] + pai2[ponto:]
        filho2 = pai2[:ponto] + pai1[ponto:]
        return self.reparar(filho1), self.reparar(filho2)

    def reparar(self, cromossomo: List[int]) -> List[int]:
        unico = list(set(cromossomo))
        faltam = TAMANHO_GRUPO - len(unico)
        if faltam > 0:
            disponiveis = list(set(self.indices_disponiveis) - set(unico))
            novos = random.sample(disponiveis, faltam)
            unico.extend(novos)
        return unico

    def mutacao(self, cromossomo: List[int]) -> List[int]:
        novo_cromo = cromossomo[:]
        if random.random() < TAXA_MUTACAO:
            idx_troca = random.randint(0, TAMANHO_GRUPO - 1)
            novo_candidato = random.choice(self.indices_disponiveis)
            while novo_candidato in novo_cromo:
                novo_candidato = random.choice(self.indices_disponiveis)
            novo_cromo[idx_troca] = novo_candidato
        return novo_cromo

    def selecionar_torneio(self, populacao, fitnesses):
        competidores = random.sample(list(zip(populacao, fitnesses)), 3)
        return max(competidores, key=lambda x: x[1])[0]

    def executar(self) -> Tuple[List[int], List[float]]:
        # Removidos prints excessivos para nao poluir o Streamlit
        populacao = [self.gerar_individuo() for _ in range(TAMANHO_POPULACAO)]
        melhor_historico = []
        melhor_solucao_global = None
        melhor_fit_global = -1.0

        for _ in range(GERACOES):
            fitnesses = [self.calcular_fitness(ind) for ind in populacao]
            
            max_fit_atual = max(fitnesses)
            idx_max = fitnesses.index(max_fit_atual)
            
            if max_fit_atual > melhor_fit_global:
                melhor_fit_global = max_fit_atual
                melhor_solucao_global = populacao[idx_max]

            melhor_historico.append(max_fit_atual)

            nova_pop = [melhor_solucao_global]
            while len(nova_pop) < TAMANHO_POPULACAO:
                pai1 = self.selecionar_torneio(populacao, fitnesses)
                pai2 = self.selecionar_torneio(populacao, fitnesses)
                if random.random() < TAXA_CROSSOVER:
                    f1, f2 = self.crossover(pai1, pai2)
                else:
                    f1, f2 = pai1, pai2
                nova_pop.append(self.mutacao(f1))
                if len(nova_pop) < TAMANHO_POPULACAO:
                    nova_pop.append(self.mutacao(f2))
            populacao = nova_pop

        return melhor_solucao_global, melhor_historico

if __name__ == "__main__":
    # Mantem funcionamento original via terminal
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    arquivo_dados = os.path.join(diretorio_atual, 'dados_enem_processados.csv')

    if os.path.exists(arquivo_dados):
        print("Rodando modo padrao (Terminal)...")
        ga = OtimizadorBolsas(arquivo_dados) # Usa pesos padrao
        melhor_grupo, historico = ga.executar()
        
        # Salva CSV
        df_resultado = ga.df.iloc[melhor_grupo]
        caminho_resultado = os.path.join(diretorio_atual, 'resultado_grupo_ideal.csv')
        df_resultado.to_csv(caminho_resultado, index=False, sep=';')
        print(f"Sucesso! Salvo em {caminho_resultado}")
        
        # Gera Grafico
        plt.figure(figsize=(10, 6))
        plt.plot(historico)
        plt.savefig(os.path.join(diretorio_atual, 'grafico_evolucao.png'))