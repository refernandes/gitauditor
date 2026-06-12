import os
import sys

# Adiciona o diretório atual ao sys.path para permitir imports relativos de src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.cli import GitAuditorCLI

def main():
    cli = GitAuditorCLI()
    cli.run()

if __name__ == "__main__":
    main()
