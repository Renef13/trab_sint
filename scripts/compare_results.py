"""
Comparacao de resumos de experimentos do PBIL-Fuzzy.

Recebe dois ou mais arquivos JSON no formato gerado por
scripts/run_experiments.py e monta uma tabela comparativa por instancia.

Uso:
    python scripts/compare_results.py --resumos saida_a.json saida_b.json
"""

import argparse
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def parse_argumentos():
    parser = argparse.ArgumentParser(description="Comparacao de resultados PBIL-Fuzzy")
    parser.add_argument(
        "--resumos",
        nargs="+",
        required=True,
        help="Arquivos JSON gerados por scripts/run_experiments.py.",
    )
    parser.add_argument(
        "--rotulos",
        nargs="*",
        default=None,
        help="Rotulos opcionais para identificar cada resumo.",
    )
    parser.add_argument(
        "--saida",
        default=None,
        help="Caminho CSV opcional para salvar a tabela comparativa.",
    )
    return parser.parse_args()


def carregar_resumo(caminho_resumo):
    with open(caminho_resumo, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def montar_linhas_resumo(resumo_experimentos, rotulo_configuracao):
    linhas = []
    for nome_instancia, dados in resumo_experimentos.items():
        linhas.append({
            "configuracao": rotulo_configuracao,
            "instancia": nome_instancia,
            "cmax_medio": dados["cmax_medio"],
            "cmax_desvio_padrao": dados["cmax_desvio_padrao"],
            "cmax_melhor": dados["cmax_melhor"],
            "cmax_pior": dados["cmax_pior"],
            "numero_execucoes": len(dados["cmax_finais"]),
        })
    return linhas


def calcular_melhor_por_instancia(tabela_comparativa):
    melhores = tabela_comparativa.groupby("instancia")["cmax_medio"].transform("min")
    tabela_comparativa["gap_medio_percentual"] = (
        100.0 * (tabela_comparativa["cmax_medio"] - melhores) / melhores
    )
    return tabela_comparativa


def main():
    argumentos = parse_argumentos()

    if argumentos.rotulos is not None and len(argumentos.rotulos) > 0:
        if len(argumentos.rotulos) != len(argumentos.resumos):
            raise ValueError("A quantidade de rotulos deve ser igual a quantidade de resumos.")
        rotulos = argumentos.rotulos
    else:
        rotulos = [
            os.path.splitext(os.path.basename(caminho_resumo))[0]
            for caminho_resumo in argumentos.resumos
        ]

    linhas = []
    for caminho_resumo, rotulo in zip(argumentos.resumos, rotulos):
        resumo = carregar_resumo(caminho_resumo)
        linhas.extend(montar_linhas_resumo(resumo, rotulo))

    tabela_comparativa = pd.DataFrame(linhas)
    tabela_comparativa = calcular_melhor_por_instancia(tabela_comparativa)
    tabela_comparativa = tabela_comparativa.sort_values(
        ["instancia", "gap_medio_percentual", "cmax_medio"]
    )

    print(tabela_comparativa.to_string(index=False))

    if argumentos.saida is not None:
        diretorio_saida = os.path.dirname(argumentos.saida)
        if diretorio_saida:
            os.makedirs(diretorio_saida, exist_ok=True)
        tabela_comparativa.to_csv(argumentos.saida, index=False, encoding="utf-8")
        print(f"\nTabela comparativa salva em: {argumentos.saida}")


if __name__ == "__main__":
    main()
