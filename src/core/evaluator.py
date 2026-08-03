"""
Avaliação de indivíduos: construção do grafo disjuntivo e cálculo do Cmax.

Segue a Seção 2 da Especificação Técnica: o makespan (Cmax) de uma
solução decodificada é o caminho crítico (caminho mais longo) do grafo
disjuntivo formado pelas arestas de precedência (fixas, da instância) e
pelas arestas disjuntivas (definidas pela ordem escolhida em cada
máquina).
"""

import networkx as nx


def construir_grafo_disjuntivo(instancia, ordens_por_maquina):
    """
    Constrói o grafo disjuntivo (DAG) de uma solução decodificada.

    Vértices: uma operação (i, k) por par job x máquina.
    Arestas de precedência: (i, k) -> (i, k+1), peso = p[i][k].
    Arestas disjuntivas: para cada máquina k, conectam jobs consecutivos
    na ordem decodificada daquela máquina.

    Parâmetros
    ----------
    instancia : Instancia
    ordens_por_maquina : list[np.ndarray]
        Saída de Individuo.decodificar(): ordens_por_maquina[k] é o
        array de índices de jobs, na ordem de execução na máquina k.

    Retorna
    -------
    networkx.DiGraph
    """
    grafo = nx.DiGraph()
    tempos_processamento = instancia.tempos_processamento

    # vértices + arestas de precedência (dentro do mesmo job, entre máquinas)
    for indice_job in range(instancia.numero_jobs):
        for indice_maquina in range(instancia.numero_maquinas):
            grafo.add_node((indice_job, indice_maquina))

        for indice_maquina in range(instancia.numero_maquinas - 1):
            peso = tempos_processamento[indice_job, indice_maquina]
            grafo.add_edge(
                (indice_job, indice_maquina),
                (indice_job, indice_maquina + 1),
                weight=peso,
            )

    # arestas disjuntivas (ordem escolhida dentro de cada máquina)
    for indice_maquina in range(instancia.numero_maquinas):
        ordem_jobs_na_maquina = ordens_por_maquina[indice_maquina]

        for posicao in range(len(ordem_jobs_na_maquina) - 1):
            job_atual = ordem_jobs_na_maquina[posicao]
            proximo_job = ordem_jobs_na_maquina[posicao + 1]
            peso = tempos_processamento[job_atual, indice_maquina]
            grafo.add_edge(
                (job_atual, indice_maquina),
                (proximo_job, indice_maquina),
                weight=peso,
            )

    return grafo


def calcular_cmax(instancia, ordens_por_maquina):
    """
    Calcula o Cmax (makespan) de uma solução decodificada.

    Cmax = comprimento do caminho mais longo (caminho crítico) do DAG
    formado pelo grafo disjuntivo (Seção 2).

    Parâmetros
    ----------
    instancia : Instancia
    ordens_por_maquina : list[np.ndarray]

    Retorna
    -------
    float
    """
    grafo = construir_grafo_disjuntivo(instancia, ordens_por_maquina)
    return nx.dag_longest_path_length(grafo, weight="weight")


def avaliar_individuo(instancia, individuo):
    """
    Decodifica (se necessário) e avalia um Individuo, preenchendo seu
    atributo cmax.

    Parâmetros
    ----------
    instancia : Instancia
    individuo : Individuo

    Retorna
    -------
    Individuo
        O mesmo objeto recebido, com individuo.cmax preenchido.
    """
    if individuo.ordens_por_maquina is None:
        individuo.decodificar()

    individuo.cmax = calcular_cmax(instancia, individuo.ordens_por_maquina)
    return individuo


def avaliar_populacao(instancia, populacao):
    """
    Avalia uma lista de indivíduos in-place.

    Parâmetros
    ----------
    instancia : Instancia
    populacao : list[Individuo]

    Retorna
    -------
    list[Individuo]
        A mesma lista recebida, com cada indivíduo avaliado.
    """
    for individuo in populacao:
        avaliar_individuo(instancia, individuo)
    return populacao