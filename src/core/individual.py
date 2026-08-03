"""
Representação do indivíduo (solução candidata) e sua decodificação.

Um indivíduo é uma matriz X de chaves de prioridade reais, amostrada a
partir da matriz de probabilidades P do PBIL. A decodificação converte
X em m permutações (uma por máquina) — Seção 1 da Especificação Técnica.
"""

import numpy as np


class Individuo:
    """
    Representa um indivíduo (solução candidata) do PBIL-Fuzzy.

    Atributos
    ---------
    chaves : np.ndarray
        Matriz X, shape (numero_maquinas, numero_jobs), valores em [0, 1].
        chaves[k][i] = chave de prioridade do job i na máquina k.
    ordens_por_maquina : list[np.ndarray] ou None
        Preenchido por decodificar(). ordens_por_maquina[k] é o array de
        índices de jobs ordenados por prioridade crescente na máquina k.
    cmax : float ou None
        Preenchido após avaliação (Fase core/evaluator.py).
    """

    def __init__(self, chaves):
        self.chaves = np.asarray(chaves, dtype=float)
        self.ordens_por_maquina = None
        self.cmax = None

    @property
    def numero_maquinas(self):
        return self.chaves.shape[0]

    @property
    def numero_jobs(self):
        return self.chaves.shape[1]

    def decodificar(self):
        """
        Converte a matriz de chaves em m permutações independentes.

        Convenção (Seção 1): menor chave = maior prioridade = executa
        mais cedo na fila daquela máquina.

        Retorna
        -------
        list[np.ndarray]
            Uma lista com m arrays; cada array é a ordem de execução dos
            jobs (índices) naquela máquina, já ordenada por prioridade.
        """
        ordens_por_maquina = []
        for indice_maquina in range(self.numero_maquinas):
            ordem = np.argsort(self.chaves[indice_maquina, :], kind="stable")
            ordens_por_maquina.append(ordem)

        self.ordens_por_maquina = ordens_por_maquina
        return ordens_por_maquina

    def __repr__(self):
        return (f"Individuo(numero_maquinas={self.numero_maquinas}, "
                f"numero_jobs={self.numero_jobs}, cmax={self.cmax})")


def amostrar_individuo(matriz_p, sigma, distribuicao="normal_truncada",
                        gerador_aleatorio=None):
    """
    Amostra um novo indivíduo X a partir da matriz de probabilidades P.

    X[k][i] ~ dist(centro = P[k][i], dispersão = sigma), truncado em [0, 1]
    (Seção 1 da Especificação Técnica).

    Parâmetros
    ----------
    matriz_p : np.ndarray
        Matriz P, shape (numero_maquinas, numero_jobs).
    sigma : float
        Dispersão da amostragem (config.yaml -> pbil.sigma_amostragem).
    distribuicao : str
        "normal_truncada" ou "uniforme" (config.yaml -> pbil.distribuicao_amostragem).
    gerador_aleatorio : np.random.Generator, opcional
        Gerador com seed controlada; se None, usa o gerador global do numpy.

    Retorna
    -------
    Individuo
    """
    rng = gerador_aleatorio if gerador_aleatorio is not None else np.random.default_rng()

    if distribuicao == "normal_truncada":
        chaves = rng.normal(loc=matriz_p, scale=sigma)
    elif distribuicao == "uniforme":
        limite_inferior = matriz_p - sigma
        limite_superior = matriz_p + sigma
        chaves = rng.uniform(low=limite_inferior, high=limite_superior)
    else:
        raise ValueError(
            f"Distribuição de amostragem desconhecida: {distribuicao!r}. "
            f"Use 'normal_truncada' ou 'uniforme'."
        )

    chaves = np.clip(chaves, 0.0, 1.0)

    return Individuo(chaves)


def amostrar_populacao(matriz_p, n_pop, sigma, distribuicao="normal_truncada",
                        gerador_aleatorio=None):
    """
    Amostra uma população de n_pop indivíduos a partir de P (Seção 1).

    Retorna
    -------
    list[Individuo]
    """
    return [
        amostrar_individuo(matriz_p, sigma, distribuicao, gerador_aleatorio)
        for _ in range(n_pop)
    ]