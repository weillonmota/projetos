# Extração e Processamento de Dados

Este documento detalha o processo de extração, higienização, análise e geração de métricas de risco implementado no script `extraçao_dados.py`. Este módulo é o coração da auditoria dos dados de despesas.

## 1. Entrada de Dados

O script inicia sua execução lendo todos os arquivos `.csv` presentes no diretório `dados_brutos`. 
Ele é flexível com o formato de codificação (tenta inicialmente `utf-8` e, em caso de falha, faz fallback para `latin1`), consolidando as informações de todos os arquivos em um único DataFrame unificado.

## 2. Higienização e Tratamento

Antes de aplicar as regras de negócio, o script realiza um tratamento essencial dos dados:
- **Conversão Numérica e de Data:** Transforma a coluna de `VALOR TRANSAÇÃO` de string formatada no padrão brasileiro (ex: `1.000,00`) para ponto flutuante, e `DATA TRANSAÇÃO` em objetos datetime, extraindo também o agrupamento de `ANO_MES`.
- **Higienização de Sigilosos e Saques:** Ajusta o nome do favorecido para operações como saques em espécie e despesas sigilosas, padronizando os favorecidos anômalos (ex: "NAO S. A.", "SEM I.") sob rubricas conhecidas. Além disso, foi feito um **refinamento nos dados do nome do favorecido** juntamente com os casos onde o **CNPJ ou CPF estava zerado** (ou preenchido de forma inválida), o que permite avaliar com precisão a origem da movimentação (identificando claramente quando o dinheiro virou saque em espécie ou despesa operacional/sigilosa).
- **Mascaramento de Nomes (LGPD):** Os nomes de portadores e favorecidos nas métricas exportadas passam por uma função `mascarar_nome`, que preserva o primeiro nome e apenas as iniciais do sobrenome. Exceção feita a saques, operações sigilosas/operacionais.

## 3. As 6 Regras de Auditoria

Sobre a base higienizada, o script executa as seguintes 6 regras para encontrar anomalias:

1. **R1 - Gasto Diário Elevado:** Transações isoladas com valor superior a R$ 3.000,00.
2. **R2 - Suspeita de Fracionamento:** Gastos pelo mesmo portador que superem R$ 5.000,00 na soma de 3 transações sucessivas num curto intervalo (até 2 dias).
3. **R3 - Uso em Dias Não Úteis:** Transações realizadas aos finais de semana (sábado e domingo) ou em feriados nacionais fixos.
4. **R4 - Operação de Saque:** Transações identificadas explicitamente como operações de saque.
5. **R5 - Transação Duplicada no Dia:** Transações repetidas exatamente no mesmo dia, com o mesmo valor exato e para o mesmo favorecido.
6. **R6 - Despesa Sigilosa Excedente:** Gastos sigilosos cuja soma mensal para um determinado órgão (unidade) ultrapasse R$ 10.000,00.

## 4. Métricas de Risco (Geração de Alertas) e Integração com Airtable

Com base nos registros que caíram nas 6 regras acima e no perfil geral dos gastos, o sistema constrói duas métricas avançadas. Foram gerados **dois arquivos CSV** específicos, onde cada um deles servirá para alimentar e gerar um **painel (dashboard) exclusivo no Airtable**:

### Métrica 1: Score Ponderado de Fraude por Portador e Mês (Painel de Criticidade)
Avalia a criticidade dos gastos suspeitos por pessoa/mês. 
- **Cálculo:** `SCORE_RISCO = (Valor Total em Alertas) * (Número de Regras Diferentes Violadas)`
- **Exportação (Arquivo 1):** Salva o Top 5 mais crítico por mês no arquivo `resultados_auditoria/airtable_top5_criticidade_mensal.csv` (com nomes mascarados). Este arquivo gerará o painel no Airtable focado nos **Maiores Riscos e Alertas Mensais**.

### Métrica 2: Concentração em Fornecedor Único (Painel de Direcionamento)
Identifica se um portador concentra grande parte dos seus gastos em um único fornecedor, sugerindo possível direcionamento de verba.
- **Gatilhos:** Gasta mais que R$ 1.500,00 totais no mês **E** mais de 75% deste montante foi destinado a um único CNPJ/CPF favorecido.
- **Exportação (Arquivo 2):** Salva os Top 5 maiores indicativos de concentração por mês no arquivo `resultados_auditoria/airtable_indicio_direcionamento.csv` (com nomes mascarados). Este arquivo gerará o painel no Airtable voltado para a **Análise de Direcionamento e Concentração de Gastos em um único favorecido**.

## 5. Como Executar

O script não requer parâmetros de linha de comando. Basta que o diretório `dados_brutos` exista e contenha os arquivos de origem (CSVs).

```bash
python extraçao_dados.py
```

Os resultados analíticos finais serão salvos automaticamente na pasta `resultados_auditoria`.
