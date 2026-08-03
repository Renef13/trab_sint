"""
Seleção de elite e sub-elite — mecanismo de diversidade do PBIL-Fuzzy.

Segue a Seção 4 da Especificação Técnica. Este mecanismo SUBSTITUI
completamente a mutação aleatória do PBIL clássico: não existe matriz Q,
a sub-elite é injetada diretamente na próxima geração (sem ruído, sem
jitter, sem síntese estatística).
"""

import math

from .diversity import calcular_distancias_elegiveis


def selecionar_elite(populacao_ordenada, pct_elite):
    """
    elite = top pct_elite% da população, por menor Cmax (Seção 4.1, passo 4).

    Parâmetros
    ----------
    populacao_ordenada : list[Individuo]
        Já ordenada por Cmax crescente.
    pct_elite : float
        Fração em (0, 1], ex.: 0.10 para 10%.

    Retorna
    -------
    list[Individuo]
    """
    tamanho_elite = max(1, math.ceil(len(populacao_ordenada) * pct_elite))
    return populacao_ordenada[:tamanho_elite]


def selecionar_elegiveis(populacao_ordenada, elite, cmax_best, delta):
    """
    elegiveis = { s : Cmax(s) <= Cmax_best * (1 + delta) }, excluindo a elite
    (Seção 4.1, passo 5).

    Parâmetros
    ----------
    populacao_ordenada : list[Individuo]
    elite : list[Individuo]
        Já selecionada por selecionar_elite(), para exclusão.
    cmax_best : float
        Melhor Cmax histórico (não só desta geração).
    delta : float
        Teto máximo de 0.20 (Seção 7).

    Retorna
    -------
    list[Individuo]
    """
    limite_cmax = cmax_best * (1.0 + delta)
    ids_elite = {id(membro) for membro in elite}

    return [
        individuo for individuo in populacao_ordenada
        if individuo.cmax <= limite_cmax and id(individuo) not in ids_elite
    ]


def selecionar_subelite(elegiveis, elite, pct_subelite):
    """
    subelite = top pct_subelite% de `elegiveis`, por MAIOR distância
    estrutural (Kendall Tau) até a elite (Seção 4.1, passos 6-7).

    pct_subelite é aplicado sobre `elegiveis`, não sobre a população
    total (Seção 7).

    Parâmetros
    ----------
    elegiveis : list[Individuo]
        Já decodificados.
    elite : list[Individuo]
        Já decodificada.
    pct_subelite : float
        Fração em (0, 1].

    Retorna
    -------
    list[Individuo]
    """
    if len(elegiveis) == 0:
        return []

    distancias = calcular_distancias_elegiveis(elegiveis, elite)

    elegiveis_com_distancia = list(zip(elegiveis, distancias))
    elegiveis_com_distancia.sort(key=lambda par: par[1], reverse=True)

    tamanho_subelite = max(1, math.ceil(len(elegiveis) * pct_subelite))
    subelite_com_distancia = elegiveis_com_distancia[:tamanho_subelite]

    return [individuo for individuo, _distancia in subelite_com_distancia]


def calcular_diversidade_estrutural_da_populacao(elegiveis, elite):
    """
    Retorna as distâncias de Kendall Tau de todos os elegíveis até a
    elite, para agregação posterior (ex.: em utils/metrics.py ->
    calcular_diversidade_estrutural_agregada) como segunda entrada do
    controlador fuzzy (Seção 5.3).

    Parâmetros
    ----------
    elegiveis : list[Individuo]
    elite : list[Individuo]

    Retorna
    -------
    list[float]
    """
    return calcular_distancias_elegiveis(elegiveis, elite)


def montar_elite_e_subelite(populacao_ordenada, cmax_best, pct_elite, pct_subelite, delta):
    """
    Função de conveniência: executa os passos 4 a 7 da Seção 4.1 de uma
    vez, retornando elite, subelite e as distâncias estruturais (para o
    fuzzy). Requer que todos os indivíduos já estejam decodificados.

    Parâmetros
    ----------
    populacao_ordenada : list[Individuo]
        Já ordenada por Cmax crescente (passo 3).
    cmax_best : float
    pct_elite : float
    pct_subelite : float
    delta : float

    Retorna
    -------
    dict
        {"elite": ..., "elegiveis": ..., "subelite": ..., "distancias_elegiveis": ...}
    """
    elite = selecionar_elite(populacao_ordenada, pct_elite)
    elegiveis = selecionar_elegiveis(populacao_ordenada, elite, cmax_best, delta)
    distancias_elegiveis = calcular_diversidade_estrutural_da_populacao(elegiveis, elite)
    subelite = selecionar_subelite(elegiveis, elite, pct_subelite)

    return {
        "elite": elite,
        "elegiveis": elegiveis,
        "subelite": subelite,
        "distancias_elegiveis": distancias_elegiveis,
    }