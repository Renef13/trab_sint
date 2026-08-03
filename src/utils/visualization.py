"""
Funções de plotagem para acompanhar a evolução do PBIL-Fuzzy.

Gera gráficos de convergência do Cmax, evolução de alpha/beta e
evolução da diversidade estrutural ao longo das gerações. Usado
principalmente pelos notebooks (Fase de análise) e por
scripts/generate_plots.py (Fase 7).
"""

import os
import matplotlib.pyplot as plt


def plotar_convergencia_cmax(historico_cmax_best, titulo="Convergência do Cmax",
                              caminho_saida=None):
    """
    Plota a evolução do Cmax_best ao longo das gerações.

    Parâmetros
    ----------
    historico_cmax_best : list[float]
        Cmax_best registrado a cada geração.
    caminho_saida : str, opcional
        Se fornecido, salva o gráfico em vez de exibir.
    """
    geracoes = range(1, len(historico_cmax_best) + 1)

    figura, eixo = plt.subplots(figsize=(8, 5))
    eixo.plot(geracoes, historico_cmax_best, linewidth=2, color="#1f77b4")
    eixo.set_xlabel("Geração")
    eixo.set_ylabel("Cmax_best")
    eixo.set_title(titulo)
    eixo.grid(True, linestyle="--", alpha=0.5)

    _salvar_ou_exibir(figura, caminho_saida)


def plotar_evolucao_alpha_beta(historico_alpha, historico_beta,
                                titulo="Evolução de α e β", caminho_saida=None):
    """
    Plota a evolução dos hiperparâmetros de saída do fuzzy (alpha e beta)
    ao longo das gerações, permitindo visualizar o comportamento do
    controlador Mamdani.
    """
    geracoes = range(1, len(historico_alpha) + 1)

    figura, eixo = plt.subplots(figsize=(8, 5))
    eixo.plot(geracoes, historico_alpha, label="α (atualização Hebbiana)",
              color="#d62728")
    eixo.plot(geracoes, historico_beta, label="β (proporção elite/sub-elite)",
              color="#2ca02c")
    eixo.set_xlabel("Geração")
    eixo.set_ylabel("Valor")
    eixo.set_title(titulo)
    eixo.legend()
    eixo.grid(True, linestyle="--", alpha=0.5)

    _salvar_ou_exibir(figura, caminho_saida)


def plotar_diversidade_estrutural(historico_diversidade,
                                   titulo="Diversidade estrutural (Kendall Tau)",
                                   caminho_saida=None):
    """
    Plota a evolução da diversidade estrutural agregada da população
    (segunda entrada do controlador fuzzy) ao longo das gerações.
    """
    geracoes = range(1, len(historico_diversidade) + 1)

    figura, eixo = plt.subplots(figsize=(8, 5))
    eixo.plot(geracoes, historico_diversidade, color="#9467bd", linewidth=2)
    eixo.set_xlabel("Geração")
    eixo.set_ylabel("Diversidade estrutural")
    eixo.set_title(titulo)
    eixo.grid(True, linestyle="--", alpha=0.5)

    _salvar_ou_exibir(figura, caminho_saida)


def plotar_comparacao_boxplot(resultados_por_instancia, titulo="Comparação de resultados",
                               caminho_saida=None):
    """
    Boxplot comparando a distribuição de Cmax final entre diferentes
    instâncias ou configurações (usado em scripts/compare_results.py).

    Parâmetros
    ----------
    resultados_por_instancia : dict[str, list[float]]
        Chave = nome da instância/configuração, valor = lista de Cmax
        finais (uma por execução independente).
    """
    rotulos = list(resultados_por_instancia.keys())
    dados = list(resultados_por_instancia.values())

    figura, eixo = plt.subplots(figsize=(max(8, len(rotulos) * 1.2), 5))
    eixo.boxplot(dados, tick_labels=rotulos)
    eixo.set_ylabel("Cmax final")
    eixo.set_title(titulo)
    eixo.grid(True, linestyle="--", alpha=0.5, axis="y")
    plt.xticks(rotation=45, ha="right")
    figura.tight_layout()

    _salvar_ou_exibir(figura, caminho_saida)


def _salvar_ou_exibir(figura, caminho_saida):
    """Função interna: salva a figura em disco ou exibe na tela."""
    if caminho_saida is not None:
        os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
        figura.savefig(caminho_saida, dpi=150, bbox_inches="tight")
        plt.close(figura)
    else:
        plt.show()