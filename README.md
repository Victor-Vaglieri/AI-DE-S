# AI-DE-S: Sistema de Extração e Estruturação de Dados com IA

O AI-DE-S é uma solução de engenharia de dados projetada para capturar informações não estruturadas da web e transformá-las em dados estruturados (JSON) utilizando modelos de linguagem de larga escala (LLM). O sistema integra automação de navegador com Selenium, processamento inteligente de HTML e uma arquitetura de pipeline paralela para garantir eficiência e escalabilidade.

## Arquitetura e Funcionalidades

O projeto é fundamentado em um pipeline de ETL (Extração, Transformação e Carga) modular, permitindo a transição entre diferentes nichos de dados (ex: vagas de emprego, hardware) apenas pela alteração de esquemas Pydantic e configurações YAML.

### Componentes Principais

*   **Extração Resiliente:** Utiliza `undetected-chromedriver` com técnicas de emulação de comportamento humano (scroll dinâmico) e gerenciamento de retentativas automáticas para mitigar bloqueios anti-bot.
*   **Processamento:** Integra `BeautifulSoup4` para a limpeza densa de HTML, removendo ruídos de código (scripts, estilos, navegação) para otimizar o contexto enviado à IA e reduzir o consumo de tokens.
*   **Pipeline Paralelo:** Execução simultânea de URLs via `ThreadPoolExecutor`, com instâncias isoladas de navegadores para maximizar a performance.
*   **Interface CLI:** Controle do sistema através de argumentos de linha de comando, permitindo definir modos de operação, arquivos de entrada e configurações.
*   **Múltiplos Exportadores:** Suporte para persistência em Banco de Dados SQL (SQLite), arquivos Markdown para Obsidian e integração direta com o GitHub Projects via GraphQL.

## Stack Tecnológica

*   **Linguagem:** Python 3.11+
*   **Automação Web:** Selenium / undetected-chromedriver
*   **Inteligência Artificial:** Groq API (Llama-3 / Llama-3.3)
*   **Estruturação de Dados:** Pydantic / BeautifulSoup4
*   **Banco de Dados:** SQLAlchemy (SQLite)
*   **Infraestrutura:** Docker / GitHub Actions

## Configuração e Instalação

### Requisitos Prévios
*   Python 3.11 ou superior instalado.
*   Chave de API do provedor Groq configurada nas variáveis de ambiente.

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
   GROQ_API_KEY=sua_chave_aqui
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
