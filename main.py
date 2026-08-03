"""
Ponto de entrada principal do PBIL-Fuzzy para o NPFS.

Executa uma única run do algoritmo sobre uma instância, salvando logs,
resultados e (opcionalmente) gráficos de acompanhamento.

Uso:
    python main.py --config config.yaml --instancia data/instances/Small/I_2_10_2_1.txt
"""

import argparse
import json
import os

import yaml

from src.core.instance import carregar_instancia
from src.engine.pbil_fuzzy import PBILFuzzy
from src.utils.logger import configurar_logger
from src.utils import visualization


def carregar_config(caminho_config):
    """Lê o arquivo config.yaml e retorna um dicionário."""
    with open(caminho_config, "r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def parse_argumentos():
    parser = argparse.ArgumentParser(description="PBIL-Fuzzy para o NPFS")
    parser.add_argument("--config", type=str, default="config.yaml",
                         help="Caminho para o arquivo de configuração.")
    parser.add_argument("--instancia", type=str, required=True,
                         help="Caminho para o arquivo .txt da instância.")
    parser.add_argument("--geracoes", type=int, default=None,
                         help="Sobrescreve criterio_parada.max_geracoes do config.yaml.")
    parser.add_argument("--seed", type=int, default=None,
                         help="Sobrescreve execucao.seed do config.yaml.")
    return parser.parse_args()


def montar_resultado_serializavel(resultado, instancia):
    """Converte um ResultadoExecucao em um dicionário serializável em JSON."""
    return {
        "instancia": instancia.nome,
        "numero_jobs": instancia.numero_jobs,
        "numero_maquinas": instancia.numero_maquinas,
        "cmax_best": resultado.cmax_best,
        "numero_geracoes": len(resultado.historico_cmax_best),
        "historico_cmax_best": resultado.historico_cmax_best,
        "historico_alpha": resultado.historico_alpha,
        "historico_beta": resultado.historico_beta,
        "historico_diversidade_estrutural": resultado.historico_diversidade_estrutural,
    }


def salvar_resultado_json(resultado_serializavel, diretorio_outputs, nome_instancia):
    os.makedirs(diretorio_outputs, exist_ok=True)
    caminho_arquivo = os.path.join(diretorio_outputs, f"{nome_instancia}.json")
    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(resultado_serializavel, arquivo, indent=2, ensure_ascii=False)
    return caminho_arquivo


def gerar_plots_execucao(resultado, diretorio_plots, nome_instancia):
    os.makedirs(diretorio_plots, exist_ok=True)

    visualization.plotar_convergencia_cmax(
        resultado.historico_cmax_best,
        titulo=f"Convergência do Cmax — {nome_instancia}",
        caminho_saida=os.path.join(diretorio_plots, f"{nome_instancia}_convergencia.png"),
    )
    visualization.plotar_evolucao_alpha_beta(
        resultado.historico_alpha, resultado.historico_beta,
        titulo=f"Evolução de α e β — {nome_instancia}",
        caminho_saida=os.path.join(diretorio_plots, f"{nome_instancia}_alpha_beta.png"),
    )
    visualization.plotar_diversidade_estrutural(
        resultado.historico_diversidade_estrutural,
        titulo=f"Diversidade estrutural — {nome_instancia}",
        caminho_saida=os.path.join(diretorio_plots, f"{nome_instancia}_diversidade.png"),
    )


def main():
    argumentos = parse_argumentos()
    config = carregar_config(argumentos.config)

    if argumentos.geracoes is not None:
        config["criterio_parada"]["max_geracoes"] = argumentos.geracoes
    if argumentos.seed is not None:
        config["execucao"]["seed"] = argumentos.seed

    logger = configurar_logger(
        nome="pbil_fuzzy.main",
        diretorio_logs=config["caminhos"]["logs"],
        salvar_em_arquivo=config["execucao"]["salvar_logs"],
    )

    logger.info("Carregando instância: %s", argumentos.instancia)
    instancia = carregar_instancia(argumentos.instancia)
    logger.info("Instância carregada: %s", instancia)

    motor = PBILFuzzy(instancia, config, logger=logger)

    logger.info("Iniciando execução do PBIL-Fuzzy...")
    resultado = motor.executar()
    logger.info("Execução finalizada. Cmax_best = %.2f", resultado.cmax_best)

    resultado_serializavel = montar_resultado_serializavel(resultado, instancia)
    caminho_json = salvar_resultado_json(
        resultado_serializavel, config["caminhos"]["outputs"], instancia.nome
    )
    logger.info("Resultado salvo em: %s", caminho_json)

    if config["execucao"]["salvar_plots"]:
        gerar_plots_execucao(resultado, config["caminhos"]["plots"], instancia.nome)
        logger.info("Gráficos salvos em: %s", config["caminhos"]["plots"])

    print(f"\nInstância: {instancia.nome}")
    print(f"Cmax_best: {resultado.cmax_best:.2f}")
    print(f"Gerações executadas: {len(resultado.historico_cmax_best)}")


if __name__ == "__main__":
    main()