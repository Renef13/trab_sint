"""
Leitura e representação da instância do problema NPFS.

Uma instância é definida por n jobs, m máquinas e uma matriz de tempos
de processamento p[i][k] (job i, máquina k) — Seção 1 da Especificação
Técnica.

Formato real de entrada (ex.: I_2_10_2_1.txt):

    n  m
    m                              <- linha extra (redundante), ignorada
        maq0  t0  maq1  t1  ...    <- n linhas, pares (id_maquina, tempo)
    Duedate
        d0
        d1
        ...

Due dates são deliberadamente IGNORADOS nesta implementação: o objetivo
do trabalho é Cmax, não métricas relacionadas a prazo (Tardiness, etc.).
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
    Lê uma instância NPFS a partir de um arquivo .txt no formato real
    do dataset (pares máquina-tempo por job + seção Duedate ignorada).

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

    indice_linha = 1

    # linha extra (ex.: repetição do número de máquinas) — presente em
    # alguns arquivos do dataset. Se a próxima linha não tiver a
    # quantidade de tokens esperada para uma linha de job, é a linha
    # extra: pula.
    tokens_esperados_por_job = 2 * numero_maquinas
    if len(linhas[indice_linha].split()) != tokens_esperados_por_job:
        indice_linha += 1

    tempos_processamento = np.zeros((numero_jobs, numero_maquinas))

    for indice_job in range(numero_jobs):
        valores = linhas[indice_linha].split()
        indice_linha += 1

        if len(valores) != tokens_esperados_por_job:
            raise ValueError(
                f"Linha de job malformada em {caminho_arquivo} (job {indice_job}): "
                f"esperado {tokens_esperados_por_job} valores (pares máquina-tempo), "
                f"encontrado {len(valores)}."
            )

        # pares (id_maquina, tempo) — indexa pela máquina informada, não
        # pela posição, para ser robusto a qualquer ordem no arquivo
        for posicao_par in range(numero_maquinas):
            indice_maquina = int(valores[2 * posicao_par])
            tempo = float(valores[2 * posicao_par + 1])
            tempos_processamento[indice_job, indice_maquina] = tempo

    # a partir daqui (seção "Duedate" e valores de prazo) é ignorado
    # deliberadamente — não faz parte do escopo do trabalho (Cmax)

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