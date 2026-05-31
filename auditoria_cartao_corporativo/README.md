# Auditoria e Governança de Dados

Este repositório contém a suíte completa para processamento, higienização e validação contínua de transações financeiras (CPGF). O sistema foi arquitetado para não apenas tratar dados brutos e prepará-los para visualização em dashboards (Airtable), mas também garantir a confiabilidade, resiliência e segurança dessa extração através de robustos testes automatizados.

O projeto está dividido em dois módulos principais, operando de forma complementar e desacoplada:

---

## 📊 1. Módulo de Extração e Dashboard

Este módulo é o "motor" de processamento de dados do projeto. Ele é responsável por ingerir grandes volumes de dados brutos de transações financeiras, aplicar regras de higienização de nomes e mascaramento, e processar as **6 Regras de Auditoria** estabelecidas pela governança.


## 🛡️ 2. Módulo de Testes Auditoria

Não basta apenas extrair os dados é preciso garantir a resiliência do sistema em cenários adversos e a segurança das informações publicadas. Neste módulo, demonstro na prática como um Auditor de TI implementa soluções de testes de estresse, assegurando a integridade, a confiabilidade e a conformidade de todo o pipeline de dados.
