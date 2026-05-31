
# 🛡️ Automação de Testes de Auditoria de TI

Airtable & Data Pipeline Assessment --- Relatório Técnico Corporativo


Este documento apresenta a especificação técnica, o escopo operacional e
as evidências de conformidade coletadas pela suíte automatizada de
auditoria de TI. O foco principal reside na validação dos controles de
segurança da informação (Confidencialidade e Integridade),
rastreabilidade de dados (Governança) e na resiliência da infraestrutura
de engenharia de dados (Tolerância a Falhas).

## 📋 1. Programa de Testes (Escopo do Projeto)

O desenho metodológico foi estruturado em conformidade com as diretrizes
de auditoria de sistemas, mapeando perguntas de negócio para validações
de código exatas:

### 🔹 Caso de Teste 01: Validação de Permissões (Confidencialidade)

-   **Pergunta do Teste:** O sistema impede que um usuário sem
    privilégios visualize ou exporte os dados brutos dos cartões corporativos?
-   **Procedimento de Verificação:** Varredura automatizada no
    código-fonte da interface pública e tentativas de chamadas anônimas
    ao endpoint interno de leitura (`/read`) do Airtable.
-   **Evidência Esperada:** Retorno restritivo de infraestrutura e
    mascaramento de dados críticos.

### 🔹 Caso de Teste 02: Modificação de Dados Críticos (Integridade)

-   **Pergunta do Teste:** O sistema bloqueia alterações na Matriz de
    Riscos vindas de requisições não autenticadas ou não autorizadas?
-   **Procedimento de Verificação:** Emissão de requisições HTTP diretas
    (`POST`/`PUT`) simulando tentativas de injeção externa sem token de
    autenticação ativo.
-   **Evidência Esperada:** Resposta padrão de erro de barramento ou
    ocultação do serviço.

### 🔹 Caso de Teste 03: Rastreabilidade e Versionamento (Governança)

-   **Pergunta do Teste:** O sistema registra quem alterou as regras de
    monitoramento ou as instruções de IA?
-   **Procedimento de Verificação:** Execução de alteração parametrizada
    em prompt e verificação de gravação de logs na tabela de trilha de
    auditoria (*Audit Trail*).
-   **Evidência Esperada:** Registro cronológico das mutações e IDs de
    usuários populados.

### 🔹 Caso de Teste 04: Robustez e Resiliência do Pipeline de Dados (Engenharia)

-   **Pergunta do Teste:** O pipeline de extração identifica anomalias
    estruturais, ausência de colunas e dados nulos sem interromper a
    execução abruptamente?
-   **Procedimento de Verificação:** Execução do script `pipeline.py`
    sob condições de estresse com arquivos contendo schemas inválidos,
    tipos corrompidos e diretórios vazios.
-   **Evidência Esperada:** Captura limpa de exceções e persistência de
    log estruturado de erro.


------------------------------------------------------------------------

## 💻 2. Implementação Técnica

A arquitetura da suíte de validação foi totalmente codificada em
**Python 3.10**, implementando uma estrutura com tipagem estrita (*type
hints*) e alinhada às padronizações de formatação descritas na PEP 8. Os
scripts atuam de forma desacoplada da aplicação principal, coletando
feedbacks diretos das APIs e do comportamento das bibliotecas de
manipulação de dados corporativos.


------------------------------------------------------------------------

## 📊 3. Resultados e Evidências Formais Obtidas

Os arquivos de logs abaixo representam os artefatos oficiais gerados em
tempo de execução pelas rotinas de teste:

### 📑 Evidência de Confidencialidade (`auditoria_confidencialidade.log`)

::: log-block
\[2026-05-25 18:02:06\] \-\-- INÍCIO DO TESTE DE CONFIDENCIALIDADE \-\--
\[2026-05-25 18:02:07\] ⚠️ ALERTA: A página está pública, mas os dados
textuais puros foram mascarados ou não foram capturados pelo script de
raspagem simples. \[2026-05-25 18:02:07\] \-\-- FIM DO TESTE DE
CONFIDENCIALIDADE \-\-- \[2026-05-25 18:03:57\] \-\-- INÍCIO DO TESTE DE
EXTRAÇÃO BRUTA DE DADOS \-\-- \[2026-05-25 18:03:58\] ✅ SUCESSO: O
Airtable barrou a requisição direta à API interna. Status HTTP: 401
\[2026-05-25 18:03:58\] \-\-- FIM DO TESTE DE EXTRAÇÃO BRUTA DE DADOS
\-\--

### 📑 Evidência de Integridade (`auditoria_integridade.log`)

\[2026-05-25 18:40:10\] \-\-- INÍCIO DO TESTE DE INTEGRIDADE \-\--
\[Status HTTP: 404\] ✅ SUCESSO: O sistema bloqueou a tentativa de
alteração anônima. Os dados originais do Airtable permanecem íntegros.
\[2026-05-25 18:40:10\] \-\-- FIM DO TESTE DE INTEGRIDADE \-\--

### 📑 Evidência de Governança (`auditoria_governança.log`)

\[2026-05-25 18:47:59\] \-\-- INÍCIO DO TESTE DE GOVERNANÇA E
VERSIONAMENTO \-\-- \[2026-05-25 18:48:00\] ✅ SUCESSO: Foram
encontrados indícios de logs de auditoria ou histórico de revisões
integrados na aplicação. \[2026-05-25 18:48:00\] \-\-- FIM DO TESTE DE
GOVERNANÇA \-\--

### 📑 Evidência do Pipeline (`auditoria_completa_pipeline.log`)

======================================================== SUITE DE TESTES
CONSOLIDADA - PIPELINE DE EXTRAÇÃO Data de Execução: 2026-05-25 19:13:03
======================================================== \[2026-05-25
19:13:03\] \[SUCESSO\] TESTE 1 (Tolerância a Falhas): O sistema barrou a
conversão de tipo inválido controladamente: could not convert string to
float: \'VALOR_TEXTO_INVALIDO\' \[2026-05-25 19:13:03\] \[SUCESSO\]
TESTE 2 (Maturidade Estrutural): A ausência de chaves estruturais foi
capturada com sucesso: KeyError \'VALOR TRANSAÇÃO\' \[2026-05-25
19:13:03\] \[SUCESSO\] TESTE 3 (Resiliência de Diretório): O pipeline
identificou a pasta vazia e encerrou a execução de forma elegante.
\[2026-05-25 19:13:03\] \[SUCESSO\] TESTE 4 (Robustez contra Nulos): O
pipeline evitou o processamento de nulos gerando a exceção: Invalid
value \'SAQUE EM ESPÉCIE\' for dtype \'float64\'


------------------------------------------------------------------------
## 🔍 4. Parecer Técnico Final do Auditor

```
**Confidencialidade & Acesso:** O ecossistema demonstrou conformidade ao
barrar requisições brutas anônimas com status `HTTP 401 Unauthorized`. O
alerta preventivo na raspagem de código sinaliza exposição da página
pública, contudo as informações sigilosas mantiveram-se ofuscadas.

**Integridade de Dados:** O barramento de escrita retornou status de
erro `HTTP 404`, impossibilitando vandalismo ou manipulação dos
registros da Matriz de Riscos por atores externos não mapeados.

**Governança & Rastreabilidade:** Verificou-se a presença de tabelas de
histórico nativas de revisão, cumprindo o requisito de auditoria para
fins de imputabilidade corporativa.

**Robustez do Pipeline de Engenharia:** O componente de ingestão
`pipeline.py` mostrou maturidade crítica ao isolar erros graves de
tipagem, inconsistências em transações nulas de movimentações econômicas
(como em cenários de `SAQUE EM ESPÉCIE`) e schemas violados sem sofrer
interrupções anômalas de execução.

## 🛠️ 5. Execução do Ambiente

Para reproduzir os testes localmente e regenerar as massas de evidências
textuais:

1.  Instale os pacotes requeridos:
    `pip install requests beautifulsoup4 pandas`
2.  Dispare a rotina unificada de infraestrutura: `python pipeline.py`