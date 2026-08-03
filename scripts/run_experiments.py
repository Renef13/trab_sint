"""
Execução em lote do PBIL-Fuzzy sobre um conjunto de instâncias.

Roda `execucao.n_execucoes_por_instancia` execuções independentes (com
seeds diferentes) para cada instância de um diretório, e salva um
resumo agregado (Cmax final por execução) em JSON.

Uso:
    python scripts/run_experiments.py --config config.yaml --diretorio data/instances/Small
"""

import argparse
import json
import os
import sys

import numpy as np
import yaml
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.instance import carregar_instancia, listar_instancias
from src.engine.pbil_fuzzy import PBILFuzzy
from src.utils.logger import configurar_logger


def parse_argumentos():
    parser = argparse.ArgumentParser(description="Execução em lote do PBIL-Fuzzy")
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--diretorio", type=str, required=True,
                         help="Diretório com arquivos .txt de instâncias.")
    parser.add_argument("--execucoes", type=int, default=None,
                         help="Sobrescreve execucao.n_execucoes_por_instancia.")
    return parser.parse_args()


def carregar_config(caminho_config):
    with open(caminho_config, "r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def rodar_execucoes_para_instancia(instancia, config, n_execucoes, logger, seed_base):
    """
    Roda n_execucoes independentes do PBIL-Fuzzy para uma instância,
    cada uma com uma seed derivada de seed_base, e retorna a lista de
    Cmax finais.
    """
    cmax_finais = []

    for indice_execucao in range(n_execucoes):
        gerador_aleatorio = np.random.default_rng(seed_base + indice_execucao)
        motor = PBILFuzzy(instancia, config, logger=logger, gerador_aleatorio=gerador_aleatorio)
        resultado = motor.executar()
        cmax_finais.append(resultado.cmax_best)

    return cmax_finais


def main():
    argumentos = parse_argumentos()
    config = carregar_config(argumentos.config)

    n_execucoes = argumentos.execucoes or config["execucao"]["n_execucoes_por_instancia"]
    seed_base = config["execucao"]["seed"]

    logger = configurar_logger(
        nome="pbil_fuzzy.run_experiments",
        diretorio_logs=config["caminhos"]["logs"],
        salvar_em_arquivo=config["execucao"]["salvar_logs"],
    )

    caminhos_instancias = listar_instancias(argumentos.diretorio)
    logger.info("Encontradas %d instâncias em %s", len(caminhos_instancias), argumentos.diretorio)

    resumo_experimentos = {}

    for caminho_instancia in tqdm(caminhos_instancias, desc="Instâncias"):
        instancia = carregar_instancia(caminho_instancia)

        cmax_finais = rodar_execucoes_para_instancia(
            instancia, config, n_execucoes, logger, seed_base
        )

        resumo_experimentos[instancia.nome] = {
            "cmax_finais": cmax_finais,
            "cmax_medio": float(np.mean(cmax_finais)),
            "cmax_desvio_padrao": float(np.std(cmax_finais)),
            "cmax_melhor": float(np.min(cmax_finais)),
            "cmax_pior": float(np.max(cmax_finais)),
        }

        logger.info(
            "Instância %s: cmax_medio=%.2f, cmax_desvio_padrao=%.2f",
            instancia.nome, resumo_experimentos[instancia.nome]["cmax_medio"],
            resumo_experimentos[instancia.nome]["cmax_desvio_padrao"],
        )

    diretorio_outputs = config["caminhos"]["outputs"]
    os.makedirs(diretorio_outputs, exist_ok=True)
    caminho_resumo = os.path.join(diretorio_outputs, "resumo_experimentos.json")

    with open(caminho_resumo, "w", encoding="utf-8") as arquivo:
        json.dump(resumo_experimentos, arquivo, indent=2, ensure_ascii=False)

    logger.info("Resumo dos experimentos salvo em: %s", caminho_resumo)
    print(f"\nResumo salvo em: {caminho_resumo}")


if __name__ == "__main__":
    main()