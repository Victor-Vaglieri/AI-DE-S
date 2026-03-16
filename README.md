# AI DE&S
Data Extractor & Structurer (DE&S) é um ecossistema de extração projetado para transformar dados não estruturados da web em conhecimento organizado. Utilizando das LLMs para interpretação de contexto e Selenium para navegação dinâmica, o projeto automatiza o fluxo de ETL, do site ao seu dashboard pessoal no Obsidian.

## Visão Geral
Este projeto é um pipeline de automação inteligente desenvolvido para extrair, processar e organizar dados da web de forma autônoma. Utilizando Selenium para navegação e LLMs (IA) para processamento de linguagem natural, o sistema transforma dados da internet em bancos de dados melhor estruturados. O diferencial é sua arquitetura a qual permite trocar o nicho de extração (neste projeto é testado o nicho de "Vagas de emprego" para "preço de Hardware") sem alterar a lógica do código.

### Objetivos do Projeto

+ Extração: Superar sites complexos que exigem interação humana via Selenium.
+ Processamento Inteligente: Eliminar a necessidade de Regex usando IA para limpar e estruturar dados.
+ Custo Zero/Baixo: Utilizar provedores de IA com camadas gratuitas (como Groq/DeepSeek).
+ Automação Total: Rodar de forma independente via GitHub Actions e Docker.
+ Visualização Ágil: Integrar os dados extraídos ao Obsidian para análise e acompanhamento pessoal.

## Ciclo de Desenvolvimento
1. Fase de Estudos:
    + Pesquisa sobre Seletores DOM avançados e estratégias anti-bot com Selenium.
    + Estudo de Prompt Engineering para garantir saídas em JSON via LLMs.
    + Aprendizado de Docker para padronização de ambientes de extração.

2. Desenvolvimento do MVP (Minimum Viable Product):
    + Script base de Selenium focado no nicho de "Vagas de Emprego".
    + Integração com API de IA para estruturação dos dados brutos.

3. Modularização e Escalabilidade:
    + Implementação de esquemas (Pydantic) para permitir a troca fácil para "Preços de Hardware".
    + Containerização da aplicação com Docker.

4. Automação e Deploy:
    + Configuração do GitHub Actions para execuções agendadas (Cron Jobs).

5. Dashboard & Insights (Obsidian):
    + Criação de script para converter os dados do banco/JSON em arquivos Markdown, permitindo a visualização de tendências dentro do Obsidian.


## Stack Tecnológica
+ Linguagem: Python 3.11+
+ Web Scraping: Selenium (Navegação dinâmica)
+ IA (LLM): Groq API (Llama 3 / DeepSeek)
+ Validação: Pydantic (Structured Outputs)
+ Containerização: Docker
+ CI/CD: GitHub Actions
+ Dashboard: Obsidian 


## Execução
Requisitos: Docker e uma API Key da Groq/OpenAI.

1. Clone o projeto e configure o .env:

```
git clone https://github.com/seu-usuario/extrator-ia.git
cp .env.example .env
```

2. Suba o serviço via Docker:
3. 
```
docker build -t extrator-ia .
docker run --env-file .env extrator-ia\
```

3. Visualização:

Os dados processados serão salvos na pasta especificada para que o seu Obsidian os reconheça como notas estruturadas.

## Estrutura do Projeto
```
├── .github/workflows/   # Configuração do GitHub Actions
├── app/
│   ├── main.py          # Ponto de entrada do sistema
│   ├── scraper.py       # Motor de navegação (Selenium)
│   ├── processor.py     # Lógica de integração com a IA
│   └── schemas/         # Definições de dados (Vagas, Hardware, etc.)
├── dashboard/           # Scripts de exportação para Obsidian (.md)
├── Dockerfile           # Receita para criação da imagem do projeto
└── requirements.txt     # Dependências do Python
```
