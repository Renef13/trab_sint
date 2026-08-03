"""
Geração de gráficos comparativos a partir dos resultados salvos por
scripts/run_experiments.py (resumo_experimentos.json).

Uso:
    python scripts/generate_plots.py --config config.yaml
"""

import argparse
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import visualization


def parse_argumentos():
    parser = argparse.ArgumentParser(description="Geração de gráficos comparativos")
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--resumo", type=str, default=None,
                         help="Caminho para resumo_experimentos.json "
                              "(default: caminhos.outputs/resumo_experimentos.json).")
    return parser.parse_args()


def carregar_config(caminho_config):
    with open(caminho_config, "r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def carregar_resumo(caminho_resumo):
    with open(caminho_resumo, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def main():
    argumentos = parse_argumentos()
    config = carregar_config(argumentos.config)

    caminho_resumo = argumentos.resumo or os.path.join(
        config["caminhos"]["outputs"], "resumo_experimentos.json"
    )
    resumo_experimentos = carregar_resumo(caminho_resumo)

    resultados_por_instancia = {
        nome_instancia: dados["cmax_finais"]
        for nome_instancia, dados in resumo_experimentos.items()
    }

    diretorio_plots = config["caminhos"]["plots"]
    caminho_saida = os.path.join(diretorio_plots, "comparacao_instancias_boxplot.png")

    visualization.plotar_comparacao_boxplot(
        resultados_por_instancia,
        titulo="Comparação de Cmax final entre instâncias",
        caminho_saida=caminho_saida,
    )

    print(f"Gráfico comparativo salvo em: {caminho_saida}")


if __name__ == "__main__":
    main()