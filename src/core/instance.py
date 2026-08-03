"""
Leitura e representação da instância do problema NPFS.

Uma instância é definida por n jobs, m máquinas e uma matriz de tempos
de processamento p[i][k] (job i, máquina k) — Seção 1 da Especificação
Técnica.
"""

import os
import numpy as np


class Instancia:
    """
    Representa uma instância do NPFS.

    Atributos
    ---------
    numero_jobs : int
        Quantidade de jobs (n).
    numero_maquinas : int
        Quantidade de máquinas (m).
    tempos_processamento : np.ndarray
        Matriz p[i][k], shape (numero_jobs, numero_maquinas).
    nome : str
        Nome/identificador da instância (geralmente o nome do arquivo).
    """

    def __init__(self, numero_jobs, numero_maquinas, tempos_processamento, nome=""):
        self.numero_jobs = numero_jobs
        self.numero_maquinas = numero_maquinas
        self.tempos_processamento = np.asarray(tempos_processamento, dtype=float)
        self.nome = nome

        self._validar()

    def _validar(self):
        formato_esperado = (self.numero_jobs, self.numero_maquinas)
        if self.tempos_processamento.shape != formato_esperado:
            raise ValueError(
                f"Matriz de tempos com shape {self.tempos_processamento.shape}, "
                f"esperado {formato_esperado} (numero_jobs x numero_maquinas)."
            )
        if np.any(self.tempos_processamento < 0):
            raise ValueError("Matriz de tempos de processamento contém valores negativos.")

    def __repr__(self):
        return (f"Instancia(nome={self.nome!r}, numero_jobs={self.numero_jobs}, "
                f"numero_maquinas={self.numero_maquinas})")


def carregar_instancia(caminho_arquivo):
    """
    Lê uma instância NPFS a partir de um arquivo .txt.

    Formato esperado (Taillard-like):
        linha 1: n m
        linhas seguintes: n linhas com m tempos de processamento cada,
                          separados por espaço (uma linha por job).

    Ex.:
        3 2
        5 3
        2 4
        6 1

    TODO(aluno): confirmar se as instâncias reais em data/instances/
    seguem exatamente este formato; ajustar o parser se necessário.

    Parâmetros
    ----------
    caminho_arquivo : str

    Retorna
    -------
    Instancia
    """
    if not os.path.isfile(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo de instância não encontrado: {caminho_arquivo}")

    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        linhas = [linha.strip() for linha in arquivo if linha.strip() != ""]

    if len(linhas) < 1:
        raise ValueError(f"Arquivo de instância vazio: {caminho_arquivo}")

    numero_jobs, numero_maquinas = map(int, linhas[0].split())

    linhas_de_dados = linhas[1:1 + numero_jobs]
    if len(linhas_de_dados) != numero_jobs:
        raise ValueError(
            f"Esperado {numero_jobs} linhas de tempos de processamento, "
            f"encontrado {len(linhas_de_dados)} em {caminho_arquivo}."
        )

    tempos_processamento = np.array(
        [[float(valor) for valor in linha.split()] for linha in linhas_de_dados]
    )

    nome = os.path.splitext(os.path.basename(caminho_arquivo))[0]

    return Instancia(numero_jobs, numero_maquinas, tempos_processamento, nome=nome)


def listar_instancias(diretorio):
    """
    Lista os caminhos de todos os arquivos .txt de instância em um diretório.
    Usado por scripts/run_experiments.py (Fase 7) para rodar em lote.
    """
    if not os.path.isdir(diretorio):
        raise NotADirectoryError(f"Diretório não encontrado: {diretorio}")

    arquivos = sorted(
        os.path.join(diretorio, nome_arquivo)
        for nome_arquivo in os.listdir(diretorio)
        if nome_arquivo.endswith(".txt")
    )
    return arquivos