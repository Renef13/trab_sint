"""
Matriz de probabilidades P do PBIL e sua atualização Hebbiana.

Segue as Seções 1 e 3 da Especificação Técnica.
"""

import numpy as np


def inicializar_matriz_p(numero_maquinas, numero_jobs, valor_inicial=0.5):
    """
    Inicializa a matriz P (m x n) com um valor neutro em todas as células.

    Decisão de projeto: todas as células começam em 0.5
    (config.yaml -> pbil.valor_inicial_matriz_p).

    Retorna
    -------
    np.ndarray
        Shape (numero_maquinas, numero_jobs).
    """
    return np.full((numero_maquinas, numero_jobs), valor_inicial, dtype=float)


def calcular_chave_media_elite(elite):
    """
    X*[k][i] = média das chaves da elite, posição a posição.

    Se |elite| == 1, X* é simplesmente a matriz de chaves desse único
    indivíduo (Seção 3).

    Parâmetros
    ----------
    elite : list[Individuo]

    Retorna
    -------
    np.ndarray
        Shape (numero_maquinas, numero_jobs).
    """
    if len(elite) == 0:
        raise ValueError("Elite vazia: não é possível calcular a chave média.")

    matrizes_de_chaves = np.stack([membro.chaves for membro in elite], axis=0)
    return np.mean(matrizes_de_chaves, axis=0)


def atualizar_matriz_p(matriz_p, elite, alpha):
    """
    Regra de atualização Hebbiana (Seção 3):

        P[k][i] <- P[k][i] * (1 - alpha) + alpha * X*[k][i]

    Equivalente a: P_novo = P_antigo + alpha * (X* - P_antigo)

    Propriedade garantida: como P_antigo, X* ∈ [0,1] e os pesos somam 1,
    P_novo ∈ [0,1] sempre — não precisa de clipping adicional aqui.

    Parâmetros
    ----------
    matriz_p : np.ndarray
        Matriz P atual, shape (numero_maquinas, numero_jobs).
    elite : list[Individuo]
        Elite da geração atual.
    alpha : float
        Saída do controlador fuzzy — intensidade da atualização.

    Retorna
    -------
    np.ndarray
        Nova matriz P (não modifica matriz_p in-place).
    """
    chave_media_elite = calcular_chave_media_elite(elite)
    return matriz_p * (1.0 - alpha) + alpha * chave_media_elite