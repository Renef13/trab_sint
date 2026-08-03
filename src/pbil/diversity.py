"""
Diversidade estrutural entre indivíduos, via distância de Kendall Tau.

Segue a Seção 4.1 (passo 6) da Especificação Técnica: a distância entre
um candidato e a elite é calculada sobre as PERMUTAÇÕES decodificadas
(ordem dos jobs por máquina), nunca sobre as chaves reais cruas — chaves
diferentes podem decodificar na mesma permutação.
"""

import numpy as np
from scipy.stats import kendalltau


def distancia_kendall_tau_uma_maquina(ordem_a, ordem_b):
    """
    Distância de Kendall Tau entre duas permutações de uma única máquina.

    Usa a correlação tau de Kendall (scipy) e converte para distância em
    [0, 1]: 0 = permutações idênticas, 1 = permutações totalmente opostas.

    distancia = (1 - tau) / 2

    Parâmetros
    ----------
    ordem_a, ordem_b : np.ndarray
        Arrays de índices de jobs, na ordem de execução (saída de
        Individuo.decodificar()[k]).

    Retorna
    -------
    float
    """
    tau, _p_valor = kendalltau(ordem_a, ordem_b)

    # tau pode ser nan se uma das permutações for constante (não deve
    # acontecer em permutações válidas com mais de 1 job, mas protege)
    if np.isnan(tau):
        return 0.0

    return (1.0 - tau) / 2.0


def distancia_estrutural_soma_maquinas(ordens_por_maquina_a, ordens_por_maquina_b):
    """
    Σ_k KendallTau(ordem_k(a), ordem_k(b))

    Soma, sobre todas as máquinas, da distância de Kendall Tau entre as
    permutações de dois indivíduos decodificados (Seção 4.1, passo 6).

    Parâmetros
    ----------
    ordens_por_maquina_a, ordens_por_maquina_b : list[np.ndarray]

    Retorna
    -------
    float
    """
    numero_maquinas = len(ordens_por_maquina_a)
    soma = 0.0
    for indice_maquina in range(numero_maquinas):
        soma += distancia_kendall_tau_uma_maquina(
            ordens_por_maquina_a[indice_maquina],
            ordens_por_maquina_b[indice_maquina],
        )
    return soma


def distancia_candidato_para_elite(individuo_candidato, elite):
    """
    dist(s) = média, sobre e em elite, de Σ_k KendallTau(ordem_k(s), ordem_k(e))

    Distância estrutural de um candidato em relação ao conjunto elite
    (Seção 4.1, passo 6). Sempre candidato-vs-conjunto, nunca
    candidato-vs-"elite média" (não existe média bem definida de
    permutações).

    Parâmetros
    ----------
    individuo_candidato : Individuo
        Já decodificado (ordens_por_maquina preenchido).
    elite : list[Individuo]
        Já decodificados.

    Retorna
    -------
    float
    """
    distancias = [
        distancia_estrutural_soma_maquinas(
            individuo_candidato.ordens_por_maquina, membro_elite.ordens_por_maquina
        )
        for membro_elite in elite
    ]
    return float(np.mean(distancias))


def calcular_distancias_elegiveis(elegiveis, elite):
    """
    Calcula dist(s) para cada candidato em `elegiveis`.

    Parâmetros
    ----------
    elegiveis : list[Individuo]
    elite : list[Individuo]

    Retorna
    -------
    list[float]
        Uma distância por candidato em `elegiveis`, na mesma ordem.
    """
    return [distancia_candidato_para_elite(candidato, elite) for candidato in elegiveis]