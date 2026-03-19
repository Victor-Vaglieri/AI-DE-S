# AI DE&S
Data Extractor & Structurer (DE&S) é um ecossistema de extração projetado para transformar dados não estruturados da web em conhecimento organizado. Utilizando LLMs para interpretação de contexto e Selenium para navegação dinâmica, o projeto automatiza o fluxo de ETL, do site ao Kanban no GitHub ou ao acesso local no Obsidian.

## Visão Geral
Este projeto é um pipeline de automação inteligente desenvolvido para extrair, processar e organizar dados da web de forma autônoma. O sistema utiliza Selenium para navegação e Processamento de Linguagem Natural (LLM) para estruturação. O diferencial reside na sua arquitetura modular a qual permite alternar o nicho de extração (ex: de "Vagas de emprego" para "Preços de Hardware") via esquemas Pydantic, sem alteração na lógica core.

<img width="1652" height="352" alt="image" src="https://github.com/user-attachments/assets/216f7194-6d9d-4505-a0cf-b10ebf62f424" />


### Objetivos do Projeto

+ Extração: Superar sites complexos que exigem interação humana via Selenium.
+ Processamento Inteligente: Eliminar a necessidade de Regex usando IA para limpar e estruturar dados.
+ Dashboard Automatizado: Integração direta com GitHub Projects (V2) para gestão visual de tarefas e oportunidades.
+ Custo Zero/Baixo: Utilizar provedores de IA com camadas gratuitas (como Groq/DeepSeek).
+ Persistência Local: Exportação para Obsidian em formato Markdown para consulta offline e histórico pessoal.
+ Automação CI/CD: Execução agendada via GitHub Actions e containerização com Docker.

## Ciclo de Desenvolvimento
1. Fase de Estudos:
    + Estudo de seletores DOM e contorno de proteções anti-bot com Selenium.
    + Engenharia de Prompt para garantir extração de dados estritamente em JSON.
    + Padronização de ambientes de execução isolados com Docker.

2. Desenvolvimento do MVP (Minimum Viable Product):
    + Arquitetura do motor de scraping focado em resiliência e performance.
    + Integração com LLMs (Groq/OpenAI) para limpeza e estruturação de dados não estruturados.

3. Modularização e Escalabilidade:
    + Uso de Pydantic para validação de esquemas, permitindo a troca dinâmica de nichos (Vagas, Hardware, etc.).
    + Criação de exportadores desacoplados (Interface Pattern) para múltiplos destinos.

4. Integração com Ecossistema GitHub (Dashboard):
    + Implementação de cliente GraphQL para alimentação automática do GitHub Projects V2.
    + Lógica de sincronização com cache em memória para evitar redundância de dados no Kanban.

5. Persistência e Automação:

    + Obsidian: Exportação em Markdown para manutenção de uma base de conhecimento (Second Brain) local.
    + CI/CD: Pipeline no GitHub Actions para execução periódica (Cron) e deploy do container.


## Stack Tecnológica

+ Linguagem: Python 3.11+
+ Web Scraping: Selenium (Navegação dinâmica)
+ IA (LLM): Groq API (Llama 3 / DeepSeek)
+ Integração: GitHub GraphQL API (para Projects V2)
+ Validação: Pydantic (Structured Outputs)
+ Infraestrutura: Docker & GitHub Actions


## Execução
Requisitos: Docker e uma API Key da Groq/OpenAI.

1. Clone o projeto e configure o .env:

```
git clone https://github.com/Victor-Vaglieri/AI-DE-S.git
cp .env.example .env
```
2. Variáveis obrigatórias no .env:
```
# jobs ou hardware
TARGET_MODE=jobs

GITHUB_TOKEN=seu_token_aqui
PROJECT_ID=id_do_seu_projeto_github
GROQ_API_KEY=sua_chave_aqui
```
3. Suba o serviço via Docker:
```
docker build -t extrator-ia .
docker run --env-file .env extrator-ia\
```

## Estrutura do Projeto
```
├── .github/workflows/   # Configuração do GitHub Actions
├── app/
│   ├── main.py          # Ponto de entrada do sistema
│   ├── scraper.py       # Motor de navegação (Selenium)
│   ├── processor.py     # Lógica de integração com a IA
│   ├── github_project_ex.py # Exportador Sênior para GitHub (GraphQL + Cache)
│   └── schemas/         # Definições de dados (Vagas, Hardware, etc.)
├── dashboard/           # Scripts de exportação para Obsidian (.md)
├── Dockerfile           # Receita para criação da imagem do projeto
└── requirements.txt     # Dependências do Python
```
