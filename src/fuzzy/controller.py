"""
Controlador fuzzy Mamdani — Seção 5 da Especificação Técnica.

2 entradas (progresso_qualidade, diversidade_estrutural), 2 saídas
(alpha, beta), FAM 5x3 = 15 regras (rules.py). Motor: Mamdani via
scikit-fuzzy (Seção 5.6), defuzzificação por centróide.
"""

from skfuzzy import control as ctrl

from . import membership
from . import rules


class ControladorFuzzy:
    """
    Encapsula o sistema Mamdani completo: antecedentes, consequentes,
    regras (a partir da FAM) e a simulação de inferência.

    Uso:
        controlador = ControladorFuzzy()
        alpha, beta = controlador.calcular(
            q=0.3, sigma_rel=0.1, diversidade_estrutural=0.6
        )
    """

    def __init__(self, limiares_progresso_qualidade=None, limiares_diversidade=None,
                 peso_q=0.8, peso_sigma_rel=0.2):
        """
        Parâmetros
        ----------
        limiares_progresso_qualidade, limiares_diversidade : list[float] ou None
            Repassados para membership.py. None = partição automática.
        peso_q, peso_sigma_rel : float
            Pesos da combinação de q e sigma_rel. O gap relativo recebe
            peso maior porque mede qualidade em relação ao melhor Cmax
            histórico; a dispersão atua como sinal secundário de espalhamento.
        """
        self.peso_q = peso_q
        self.peso_sigma_rel = peso_sigma_rel

        self.antecedente_progresso_qualidade = membership.construir_antecedente_progresso_qualidade(
            limiares=limiares_progresso_qualidade
        )
        self.antecedente_diversidade = membership.construir_antecedente_diversidade(
            limiares=limiares_diversidade
        )
        self.consequente_alpha = membership.construir_consequente_alpha()
        self.consequente_beta = membership.construir_consequente_beta()

        self._sistema_controle = self._construir_sistema_controle()
        self._simulacao = ctrl.ControlSystemSimulation(self._sistema_controle)

    def _construir_sistema_controle(self):
        """Constrói as 15 regras Mamdani a partir da FAM (rules.py)."""
        regras_fuzzy = []

        for termo_progresso, termo_diversidade, termo_alpha, termo_beta in rules.gerar_regras_fam():
            antecedente = (
                self.antecedente_progresso_qualidade[termo_progresso]
                & self.antecedente_diversidade[termo_diversidade]
            )
            consequente = [
                self.consequente_alpha[termo_alpha],
                self.consequente_beta[termo_beta],
            ]
            regras_fuzzy.append(ctrl.Rule(antecedente, consequente))

        return ctrl.ControlSystem(regras_fuzzy)

    def combinar_q_sigma_rel(self, q, sigma_rel):
        """
        Combina q e sigma_rel num único sinal 'progresso_qualidade'
        (Seção 5.2; decisão adotada aqui: média ponderada —
        config.yaml -> fuzzy.combinacao_q_sigma_rel).

        Ambos são clipados a [0, 1] antes da combinação, já que esse é
        o universo de discurso do antecedente fuzzy.
        """
        q_limitado = min(max(q, 0.0), 1.0)
        sigma_rel_limitado = min(max(sigma_rel, 0.0), 1.0)
        return self.peso_q * q_limitado + self.peso_sigma_rel * sigma_rel_limitado

    def calcular(self, q, sigma_rel, diversidade_estrutural):
        """
        Executa a inferência Mamdani completa: fuzzificação -> 15
        regras -> agregação -> defuzzificação (centroide) para alpha
        e beta.

        Parâmetros
        ----------
        q : float
            Gap relativo (utils/metrics.py -> calcular_gap_relativo).
        sigma_rel : float
            Dispersão relativa (utils/metrics.py ->
            calcular_dispersao_relativa).
        diversidade_estrutural : float
            Diversidade estrutural agregada (utils/metrics.py ->
            calcular_diversidade_estrutural_agregada). Clipada a [0, 1]
            aqui como salvaguarda — ver nota abaixo.

        Retorna
        -------
        tuple(float, float)
            (alpha, beta)
        """
        progresso_qualidade = self.combinar_q_sigma_rel(q, sigma_rel)
        diversidade_limitada = min(max(diversidade_estrutural, 0.0), 1.0)

        self._simulacao.input["progresso_qualidade"] = progresso_qualidade
        self._simulacao.input["diversidade_estrutural"] = diversidade_limitada

        self._simulacao.compute()

        alpha = self._simulacao.output["alpha"]
        beta = self._simulacao.output["beta"]

        return alpha, beta
