"""
FAM (Fuzzy Associative Memory) 5x3 — Seção 5.5 da Especificação Técnica.

Mapeia cada combinação (progresso_qualidade, diversidade_estrutural)
para um par de termos de saída (alpha, beta).

As regras abaixo implementam uma política inicial de intensificação e
diversificação: quando a população está longe do melhor valor histórico,
alpha tende a subir para acelerar a aprendizagem da matriz P; quando a
diversidade estrutural está baixa, beta tende a cair para injetar mais
subelite diversa na próxima geração.

A linha "muito próximo do ótimo + estagnado" (Seção 5.5) NÃO faz parte
desta FAM 5x3: estagnação não é um dos 5 termos de Progresso/Qualidade
(que mede nível, não tendência). Por decisão de projeto
(config.yaml -> fuzzy.tratamento_estagnacao = "fora_do_fuzzy"), esse
caso é tratado como verificação separada, fora do sistema fuzzy — ver
verificar_estagnacao() e aplicar_override_estagnacao() abaixo.
"""

TERMOS_PROGRESSO_QUALIDADE = [
    "muito_proximo", "proximo", "moderado", "distante", "muito_distante",
]
TERMOS_DIVERSIDADE = ["baixa", "media", "alta"]


# FAM[termo_progresso][termo_diversidade] = (termo_alpha, termo_beta)
FAM = {
    "muito_proximo": {
        "baixa": ("baixo", "baixo"),
        "media": ("baixo", "medio"),
        "alta": ("medio", "medio"),
    },
    "proximo": {
        "baixa": ("baixo", "baixo"),
        "media": ("medio", "medio"),
        "alta": ("medio", "alto"),
    },
    "moderado": {
        "baixa": ("medio", "baixo"),
        "media": ("medio", "medio"),
        "alta": ("alto", "alto"),
    },
    "distante": {
        "baixa": ("medio", "baixo"),
        "media": ("alto", "medio"),
        "alta": ("alto", "alto"),
    },
    "muito_distante": {
        "baixa": ("alto", "baixo"),
        "media": ("alto", "medio"),
        "alta": ("alto", "alto"),
    },
}


def gerar_regras_fam():
    """
    Achata a FAM num formato de lista, conveniente para o
    controller.py construir as 15 regras skfuzzy.control.Rule.

    Retorna
    -------
    list[tuple]
        Cada item: (termo_progresso, termo_diversidade, termo_alpha, termo_beta)
    """
    regras = []
    for termo_progresso in TERMOS_PROGRESSO_QUALIDADE:
        for termo_diversidade in TERMOS_DIVERSIDADE:
            termo_alpha, termo_beta = FAM[termo_progresso][termo_diversidade]
            regras.append((termo_progresso, termo_diversidade, termo_alpha, termo_beta))
    return regras


def verificar_estagnacao(historico_cmax_best, geracoes_estagnacao_limite):
    """
    Verifica estagnação fora do fuzzy (Seção 5.5, tratamento_estagnacao
    = "fora_do_fuzzy"): True se Cmax_best não melhorou nas últimas
    `geracoes_estagnacao_limite` gerações.

    Parâmetros
    ----------
    historico_cmax_best : list[float]
        Cmax_best registrado a cada geração, em ordem cronológica.
    geracoes_estagnacao_limite : int

    Retorna
    -------
    bool
    """
    if len(historico_cmax_best) < geracoes_estagnacao_limite:
        return False

    janela = historico_cmax_best[-geracoes_estagnacao_limite:]
    return janela[0] == janela[-1]


def esta_muito_proximo_do_otimo(q, limiar_muito_proximo):
    """
    Auxiliar para aplicar_override_estagnacao(): verifica se o gap
    relativo q está na faixa do termo 'muito_proximo' (Seção 5.5).

    Parâmetros
    ----------
    limiar_muito_proximo : float
        Mesmo primeiro limiar usado na fuzzificação de progresso_qualidade.
    """
    return q <= limiar_muito_proximo


def aplicar_override_estagnacao(alpha, beta, estagnado, muito_proximo_do_otimo):
    """
    Override decidido (Seção 5.5, célula destacada): se a população
    está muito próxima do ótimo E estagnada, "manter comportamento" —
    ou seja, não deixar o fuzzy alterar alpha/beta nessa geração.
    Implementado aqui como: se as duas condições forem verdadeiras,
    sinaliza pro engine (Fase 6) reutilizar alpha/beta da geração
    anterior em vez dos calculados pelo fuzzy.

    Parâmetros
    ----------
    alpha, beta : float
        Saída normal do controlador fuzzy nesta geração.
    estagnado : bool
        Saída de verificar_estagnacao().
    muito_proximo_do_otimo : bool
        Saída de esta_muito_proximo_do_otimo().

    Retorna
    -------
    tuple(float | None, float | None, bool)
        (alpha_final, beta_final, override_aplicado). Se
        override_aplicado for True, alpha_final/beta_final vêm None —
        o engine deve usar os valores da geração anterior.
    """
    if estagnado and muito_proximo_do_otimo:
        return None, None, True

    return alpha, beta, False
