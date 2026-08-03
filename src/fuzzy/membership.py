"""
Funções de pertinência (membership functions) do controlador fuzzy.

Baseado na Seção 5 da Especificação Técnica. Quando os limiares vêm do
config.yaml, são usadas funções triangulares calibradas; se não vierem,
o sistema usa uma partição automática uniforme como fallback.
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# ordem CRESCENTE no universo de discurso (0 -> 1). Note que essa ordem
# é a INVERSA da tabela de apresentação da Seção 5.2 (que lista do "mais
# distante" pro "mais próximo") — q baixo = perto do ótimo, q alto =
# longe do ótimo, e o automf/trimf espera ordem crescente de valor.
NOMES_PROGRESSO_QUALIDADE_CRESCENTE = [
    "muito_proximo", "proximo", "moderado", "distante", "muito_distante",
]

NOMES_DIVERSIDADE_CRESCENTE = ["baixa", "media", "alta"]


def construir_antecedente_progresso_qualidade(faixa=(0.0, 1.0, 0.001),
                                                limiares=None):
    """
    Cria o antecedente fuzzy 'progresso_qualidade' — sinal único
    resultante da combinação de q (gap relativo) e sigma_rel (dispersão
    relativa), ver ControladorFuzzy.combinar_q_sigma_rel() em
    controller.py.

    Parâmetros
    ----------
    faixa : tuple(float, float, float)
        (inicio, fim, passo) do universo de discurso.
    limiares : list[float] ou None
        4 cortes internos definindo as fronteiras dos 5 termos
        linguísticos, em ordem crescente. Se None, usa distribuição
        automática uniforme.

    Retorna
    -------
    skfuzzy.control.Antecedent
    """
    universo = np.arange(*faixa)
    antecedente = ctrl.Antecedent(universo, "progresso_qualidade")

    if limiares is None:
        antecedente.automf(5, names=NOMES_PROGRESSO_QUALIDADE_CRESCENTE)
    else:
        _aplicar_triangulos_por_limiares(
            antecedente, universo, NOMES_PROGRESSO_QUALIDADE_CRESCENTE, limiares
        )

    return antecedente


def construir_antecedente_diversidade(faixa=(0.0, 1.0, 0.001), limiares=None):
    """
    Cria o antecedente fuzzy 'diversidade_estrutural' (Seção 5.3),
    3 termos: baixa / média / alta.

    Parâmetros
    ----------
    faixa : tuple(float, float, float)
    limiares : list[float] ou None
        2 cortes internos. Se None, distribuição automática uniforme.

    Retorna
    -------
    skfuzzy.control.Antecedent
    """
    universo = np.arange(*faixa)
    antecedente = ctrl.Antecedent(universo, "diversidade_estrutural")

    if limiares is None:
        antecedente.automf(3, names=NOMES_DIVERSIDADE_CRESCENTE)
    else:
        _aplicar_triangulos_por_limiares(
            antecedente, universo, NOMES_DIVERSIDADE_CRESCENTE, limiares
        )

    return antecedente


def construir_consequente_alpha(faixa=(0.0, 1.0, 0.001)):
    """
    Cria o consequente fuzzy 'alpha' (intensidade da atualização
    Hebbiana, Seção 5.4). 3 termos: baixo / medio / alto — suficiente
    para as setas ↓ / → / ↑ da FAM (Seção 5.5).

    Retorna
    -------
    skfuzzy.control.Consequent
    """
    universo = np.arange(*faixa)
    consequente = ctrl.Consequent(universo, "alpha")
    consequente.automf(3, names=["baixo", "medio", "alto"])
    return consequente


def construir_consequente_beta(faixa=(0.0, 1.0, 0.001)):
    """
    Cria o consequente fuzzy 'beta' (proporção elite/sub-elite na
    próxima geração, Seção 5.4). 3 termos: baixo / medio / alto.

    Retorna
    -------
    skfuzzy.control.Consequent
    """
    universo = np.arange(*faixa)
    consequente = ctrl.Consequent(universo, "beta")
    consequente.automf(3, names=["baixo", "medio", "alto"])
    return consequente


def _aplicar_triangulos_por_limiares(variavel_fuzzy, universo, nomes, limiares):
    """
    Função interna: constrói funções de pertinência triangulares a
    partir de uma lista de pontos centrais/limiares internos.

    O primeiro e o último termo viram "ombros" (patamar no extremo do
    universo); os termos intermediários são triângulos centrados em
    cada limiar.

    Parâmetros
    ----------
    variavel_fuzzy : ctrl.Antecedent ou ctrl.Consequent
    universo : np.ndarray
    nomes : list[str]
        Nomes dos termos, em ordem crescente no universo.
    limiares : list[float]
        len(nomes) - 1 cortes internos, em ordem crescente.
    """
    if len(limiares) != len(nomes) - 1:
        raise ValueError(
            f"Esperado {len(nomes) - 1} limiares para {len(nomes)} termos, "
            f"recebido {len(limiares)}."
        )

    pontos = [float(universo[0])] + list(limiares) + [float(universo[-1])]
    numero_termos = len(nomes)

    for indice_termo, nome_termo in enumerate(nomes):
        if indice_termo == 0:
            a, b, c = pontos[0], pontos[0], pontos[1]
        elif indice_termo == numero_termos - 1:
            a, b, c = pontos[-2], pontos[-1], pontos[-1]
        else:
            a, b, c = pontos[indice_termo - 1], pontos[indice_termo], pontos[indice_termo + 1]

        variavel_fuzzy[nome_termo] = fuzz.trimf(universo, [a, b, c])
