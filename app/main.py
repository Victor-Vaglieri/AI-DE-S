import argparse
import sys
import asyncio
from dotenv import load_dotenv
from app.pipeline import Pipeline
from app.settings import settings

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="AI-DE-S: Scraper de Vagas")
    parser.add_argument(
        "--urls", 
        help="Caminho para o arquivo de URLs (opcional)",
        default="config/sites-vagas.txt"
    )
    parser.add_argument(
        "--config", 
        default="config/settings.yaml", 
        help="Caminho para o arquivo de configuracao YAML"
    )

    args = parser.parse_args()

    if args.config != "config/settings.yaml":
        settings.__init__(args.config)

    pipeline = Pipeline(urls_file=args.urls)
    
    try:
        asyncio.run(pipeline.run())
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"Erro fatal não tratado no sistema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
