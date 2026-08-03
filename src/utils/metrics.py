"""
Funções de métricas usadas pelo PBIL-Fuzzy.

Inclui estatísticas descritivas da população (média, desvio padrão) e
os sinais derivados que alimentam o controlador fuzzy (Seção 5.2 da
Especificação Técnica): gap relativo `q` e dispersão relativa `sigma_rel`.
"""

import numpy as np


def calcular_media_cmax(lista_cmax):
    """Média (mu) dos valores de Cmax de uma população."""
    return float(np.mean(lista_cmax))


def calcular_desvio_padrao_cmax(lista_cmax):
    """Desvio padrão (sigma) dos valores de Cmax de uma população."""
    return float(np.std(lista_cmax))


def calcular_gap_relativo(media_cmax, cmax_best):
    """
    q = (mu - Cmax_best) / Cmax_best

    Gap relativo entre a média da população atual e o melhor Cmax
    já encontrado. Quanto menor, mais perto do ótimo (Seção 5.2).
    """
    if cmax_best == 0:
        return 0.0
    return (media_cmax - cmax_best) / cmax_best


def calcular_dispersao_relativa(desvio_padrao_cmax, media_cmax):
    """
    sigma_rel = sigma / mu

    Dispersão relativa da população atual (Seção 5.2).
    """
    if media_cmax == 0:
        return 0.0
    return desvio_padrao_cmax / media_cmax


def calcular_meta_features(lista_cmax, cmax_best):
    """
    Calcula de uma vez as meta-features usadas como entrada do fuzzy:
    media, desvio_padrao, gap_relativo (q) e dispersao_relativa (sigma_rel).

    Retorna um dicionário para facilitar o uso no engine (Fase 6).
    """
    media_cmax = calcular_media_cmax(lista_cmax)
    desvio_padrao_cmax = calcular_desvio_padrao_cmax(lista_cmax)
    q = calcular_gap_relativo(media_cmax, cmax_best)
    sigma_rel = calcular_dispersao_relativa(desvio_padrao_cmax, media_cmax)

    return {
        "media_cmax": media_cmax,
        "desvio_padrao_cmax": desvio_padrao_cmax,
        "gap_relativo": q,
        "dispersao_relativa": sigma_rel,
    }


def atualizar_cmax_best(cmax_best_atual, lista_cmax_geracao):
    """
    Cmax_best = min(Cmax_best, min(Cmax da população))

    Atualização histórica do melhor Cmax encontrado (nunca piora).
    """
    melhor_da_geracao = min(lista_cmax_geracao)
    return min(cmax_best_atual, melhor_da_geracao)


def calcular_diversidade_estrutural_agregada(distancias_kendall_tau, numero_maquinas=None):
    """
    Agrega as distâncias de Kendall Tau individuais (uma por candidato
    elegível, calculadas na Fase 4 - pbil/diversity.py) num único valor
    escalar de diversidade estrutural da população, usado como segunda
    entrada do controlador fuzzy (Seção 5.3).

    Como a distância de cada candidato é uma soma das distâncias de
    Kendall Tau sobre as máquinas, a normalização divide a média pelo
    número de máquinas. Assim a entrada do fuzzy permanece em [0, 1]:
    0 indica estrutura igual à elite e 1 indica estrutura oposta em todas
    as máquinas.
    """
    if len(distancias_kendall_tau) == 0:
        return 0.0

    diversidade_media = float(np.mean(distancias_kendall_tau))

    if numero_maquinas is not None and numero_maquinas > 0:
        diversidade_media /= numero_maquinas

    return float(np.clip(diversidade_media, 0.0, 1.0))
