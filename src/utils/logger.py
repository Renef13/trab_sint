"""
Utilitário de logging do projeto PBIL-Fuzzy NPFS.

Centraliza a configuração de logs para console e arquivo, usada por
todos os outros módulos (core, pbil, fuzzy, engine, scripts).
"""

import logging
import os
from datetime import datetime


FORMATO_PADRAO = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
FORMATO_DATA = "%Y-%m-%d %H:%M:%S"


def configurar_logger(nome, diretorio_logs=None, nivel=logging.INFO,
                       salvar_em_arquivo=True, nome_arquivo=None):
    """
    Cria e configura um logger nomeado.

    Parâmetros
    ----------
    nome : str
        Nome do logger (geralmente __name__ do módulo chamador).
    diretorio_logs : str, opcional
        Diretório onde o arquivo de log será salvo (ex.: data/results/logs).
    nivel : int
        Nível de log (logging.DEBUG, logging.INFO, etc.).
    salvar_em_arquivo : bool
        Se True, além do console, grava em arquivo .log.
    nome_arquivo : str, opcional
        Nome customizado do arquivo de log. Se None, usa timestamp.

    Retorna
    -------
    logging.Logger
    """
    logger = logging.getLogger(nome)
    logger.setLevel(nivel)

    # evita adicionar handlers duplicados se o logger já foi configurado antes
    if logger.handlers:
        return logger

    formatador = logging.Formatter(FORMATO_PADRAO, datefmt=FORMATO_DATA)

    handler_console = logging.StreamHandler()
    handler_console.setFormatter(formatador)
    logger.addHandler(handler_console)

    if salvar_em_arquivo and diretorio_logs is not None:
        os.makedirs(diretorio_logs, exist_ok=True)

        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"execucao_{timestamp}.log"

        caminho_arquivo = os.path.join(diretorio_logs, nome_arquivo)
        handler_arquivo = logging.FileHandler(caminho_arquivo, encoding="utf-8")
        handler_arquivo.setFormatter(formatador)
        logger.addHandler(handler_arquivo)

    return logger


def registrar_geracao(logger, numero_geracao, cmax_melhor_geracao,
                       cmax_best_historico, alpha, beta,
                       diversidade_estrutural):
    """
    Log padronizado do estado do algoritmo ao final de cada geração.
    Usado pelo engine (Fase 6) dentro do laço principal.
    """
    logger.info(
        "geracao=%d | cmax_melhor_geracao=%.2f | cmax_best_historico=%.2f | "
        "alpha=%.3f | beta=%.3f | diversidade_estrutural=%.4f",
        numero_geracao, cmax_melhor_geracao, cmax_best_historico,
        alpha, beta, diversidade_estrutural,
    )