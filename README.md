# AI-DE-S: Sistema de Extração e Estruturação de Dados com IA

O AI-DE-S é uma solução de engenharia de dados projetada para capturar informações não estruturadas da web e transformá-las em dados estruturados (JSON) utilizando modelos de linguagem de larga escala (LLM). O sistema integra automação de navegador com Playwright, processamento inteligente de HTML e uma arquitetura de pipeline paralela assíncrona para garantir eficiência e escalabilidade.

## Arquitetura e Funcionalidades

O projeto é fundamentado em um pipeline de ETL (Extração, Transformação e Carga) modular, permitindo a transição entre diferentes nichos de dados (ex: vagas de emprego, hardware) apenas pela alteração de esquemas Pydantic e configurações YAML.

<img width="780" height="545" alt="Imagem1" src="https://github.com/user-attachments/assets/cca51ef9-55c3-4930-a0f0-99b711900ea9" />

### Componentes Principais

*   **Extração Resiliente:** Utiliza `Playwright` assíncrono com técnicas de emulação de comportamento humano (scroll dinâmico) e gerenciamento de retentativas automáticas para mitigar bloqueios anti-bot.
*   **Processamento:** Integra `BeautifulSoup4` para a limpeza densa de HTML, removendo ruídos de código (scripts, estilos, navegação) para otimizar o contexto enviado à IA e reduzir o consumo de tokens.
*   **Pipeline Paralelo:** Execução simultânea de URLs via `asyncio.gather` e concorrência controlada por `asyncio.Semaphore`, maximizando a performance de forma assíncrona.
*   **Interface CLI:** Controle do sistema através de argumentos de linha de comando, permitindo definir modos de operação, arquivos de entrada e configurações.
*   **Múltiplos Exportadores:** Suporte para persistência em Banco de Dados SQL (SQLite), arquivos Markdown para Obsidian e integração direta com o GitHub Projects via GraphQL.

## Stack Tecnológica

*   **Linguagem:** Python 3.11+
*   **Automação Web:** Playwright (Assíncrono)
*   **Inteligência Artificial:** Google Gemini API (via Instructor)
*   **Estruturação de Dados:** Pydantic / BeautifulSoup4
*   **Banco de Dados:** SQLAlchemy (SQLite)
*   **Infraestrutura:** Docker / GitHub Actions

## Configuração e Instalação

### Requisitos Prévios
*   Python 3.11 ou superior instalado.
*   Chave de API do provedor LLM (ex: Google Gemini, OpenAI, etc) configurada nas variáveis de ambiente.

### Procedimento de Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/Victor-Vaglieri/AI-DE-S.git
   cd AI-DE-S
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure o arquivo `.env` com base no `.env.example`:
   ```env
   LLM_API_KEY=sua_chave_aqui
   GITHUB_TOKEN=seu_token_aqui
   PROJECT_ID=id_do_projeto
   ```

## Utilização via CLI

O sistema é operado através do módulo principal com suporte aos seguintes argumentos:

| Argumento | Descrição | Padrão |
| :--- | :--- | :--- |
| `--mode` | Define o nicho de extração (`jobs` ou `hardware`) | `jobs` |
| `--urls` | Caminho para o arquivo de texto com a lista de URLs | Automático por modo |
| `--config` | Caminho para o arquivo de configuração YAML | `config/settings.yaml` |

**Exemplo de execução:**
```bash
python -m app.main --mode hardware --urls config/sites-hardware.txt
```

## Estrutura do Projeto

*   `app/main.py`: Ponto de entrada e interface CLI.
*   `app/pipeline.py`: Orquestrador de execução paralela e deduplicação.
*   `app/scraper.py`: Gerenciador de navegação e captura de conteúdo.
*   `app/processor.py`: Limpeza de HTML e integração com LLM.
*   `app/settings.py`: Gestor de configurações centralizadas.
*   `app/schemas/`: Definições de estruturas de dados (Pydantic).
*   `config/settings.yaml`: Parâmetros técnicos do sistema (modelos, tempos, limites).

---

## 5. Motivação e Escolhas Arquiteturais (Trade-offs)

*   **Playwright (Assíncrono) vs Requests/Selenium:** A escolha do **Playwright** foi baseada na sua capacidade de lidar com SPAs (Single Page Applications) e renderização client-side. Bibliotecas puras como `requests` falharam em sites com proteções antibot e conteúdo carregado via JS, enquanto o Selenium consome mais recursos e é mais lento que a arquitetura assíncrona do Playwright.
*   **BeautifulSoup4 na Pré-limpeza vs LLM Puro:** Para evitar enviar todo o código de uma página ao LLM, o que estourou a janela de contexto e gerou aumento de custos, foi escolhido o **BeautifulSoup4** como camada intermediária ja que ele atua removendo scripts, CSS, e lixo de HTML, entregando apenas o contexto textual melhor para a IA processar.
*   **Banco de Dados Local (SQLite/SQLAlchemy):** Em vez de exigir a instalação e orquestração de bancos para testes locais, o uso de **SQLite** acoplado ao SQLAlchemy simplifica a carga inicial, rodando de maneira autossuficiente (mesmo em containers via mapeamento de volumes).

## 6. Desafios Enfrentados e Soluções

*   **Bloqueios de Acesso e Proteções (Anti-Bot):**
    *   *Desafio:* Vários sites recusavam conexões sucessivas ou limitavam o carregamento de dados ao identificar as requisições como atividade não humana.
    *   *Solução:* Implementação de emulação de comportamento mais "orgânico" no Scraper, aplicando scroll nas páginas para engatilhar carregamentos *lazy-loaded* e gerenciamento de retentativas usando concorrência.
*   **Consistência Estrutural da Saída do LLM:**
    *   *Desafio:* Modelos LLM podem perder a formatação desejada no meio da resposta ou omitir chaves na hora de entregar o dado estruturado.
    *   *Solução:* Utilização do **Instructor** atrelado aos schemas do **Pydantic** obrigando a API da IA a gerar saídas condizentes à estrutura de dados tipada pelo projeto, validando as respostas e garantindo melhor confiabilidade na pipeline.
