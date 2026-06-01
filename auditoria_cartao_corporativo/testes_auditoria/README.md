# Auditoria de Sistemas: Garantindo Segurança e Confiabilidade

A auditoria de sistemas é um pilar fundamental para qualquer organização que lida com dados sensíveis e processos críticos. Ela consiste na avaliação rigorosa e sistemática das operações, controles e segurança de um sistema de informação. A principal importância da auditoria reside em:

1.  **Garantir a Segurança da Informação:** Identificar vulnerabilidades que possam ser exploradas por agentes maliciosos, protegendo os dados contra acesso não autorizado, alteração ou destruição.
2.  **Assegurar a Conformidade (Compliance):** Verificar se os sistemas e processos estão de acordo com as leis, regulamentações e políticas internas da empresa (ex: LGPD).
3.  **Aumentar a Confiabilidade:** Garantir que as informações processadas e geradas pelo sistema sejam precisas, íntegras e consistentes, o que é vital para a tomada de decisão.
4.  **Mitigar Riscos Financeiros e de Reputação:** Prevenir fraudes, vazamentos de dados e falhas operacionais que podem resultar em multas pesadas e danos irreversíveis à imagem da empresa.

---

## Módulos de Teste de Auditoria

Este diretório contém scripts desenvolvidos para testar automatizadamente diferentes aspectos de segurança e robustez do nosso sistema de extração e apresentação de dados (Dashboard e Airtable). Abaixo, detalhamos a função de cada um:

### 1. `confidencialidade.py`

*   **O que faz:** Este script simula uma tentativa de acesso direto à API interna do Airtable, sem passar pela interface pública padrão. Ele envia requisições HTTP forjando os cabeçalhos para tentar extrair os dados brutos de forma não autorizada.
*   **Objetivo:** O objetivo é testar se o endpoint da API interna está devidamente protegido contra acessos anônimos ou extrações em massa (scraping/dump de dados).
*   **Importância:** A verificação de confidencialidade é crucial para garantir que dados sensíveis (neste caso, gastos de cartões corporativos) não estejam expostos publicamente de forma indevida, prevenindo vazamentos de informações críticas.

### 2. `integridade.py`

*   **O que faz:** Este script tenta realizar uma "injeção de dados" (Data Injection) na base do Airtable. Ele simula o envio de uma requisição `POST` com uma carga maliciosa (dados falsos de gastos) tentando forçar a inserção desse registro na base de dados, simulando a ação de um usuário não autenticado.
*   **Objetivo:** Avaliar se o sistema possui controles de acesso adequados para operações de escrita (alteração, inserção ou exclusão de dados), bloqueando tentativas anônimas ou de usuários sem os privilégios necessários.
*   **Importância:** A integridade garante que a base de dados em que o dashboard confia não possa ser adulterada por terceiros. Sem integridade, as informações perdem o valor, pois não se pode confiar na veracidade dos dados apresentados.

### 3. `pipeline.py`

*   **O que faz:** É uma suite de testes automatizados que avalia a robustez do script principal de processamento de dados (`extraçao_dados.py`). Ele cria cenários de dados de entrada defeituosos:
    *   **Cenário 1:** Dados corrompidos (ex: texto onde deveria haver número).
    *   **Cenário 2:** Arquivos CSV sem as colunas obrigatórias.
    *   **Cenário 3:** Diretório de dados vazio.
    *   **Cenário 4:** Valores nulos/vazios em campos críticos.
*   **Objetivo:** Garantir que o pipeline de extração e análise não "quebre" (crash) de forma inesperada diante de anomalias nos dados. Ele deve ser capaz de tratar os erros de forma controlada e previsível.
*   **Importância:** Um pipeline resiliente é vital para a operação diária. Se o script de ingestão falhar silenciosamente ou corromper a execução diante de um dado mal formatado, o dashboard ficará desatualizado ou, pior, exibirá informações incorretas.

### 4. `versionamento.py`

*   **O que faz:** Este script autentica-se diretamente na API oficial do Airtable utilizando um token de acesso seguro (extraído de variáveis de ambiente) e tenta consultar o endpoint de logs de auditoria corporativos (`auditLogs`).
*   **Objetivo:** Verificar de forma robusta se a conta conectada possui os privilégios e a licença necessária (Plano Enterprise) para acessar trilhas de auditoria (Audit Trails), confirmando se podemos monitorar quem altera os dados e as regras.
*   **Importância:** A rastreabilidade (versionamento) é essencial para investigar incidentes de segurança. Se um dado for alterado indevidamente, os logs da API são a forma correta e segura de identificar a origem da alteração e responsabilizar as partes envolvidas.