"""
Ciclo completo do PBIL-Fuzzy para o NPFS — Seção 6 da Especificação Técnica.

Junta core (instância, indivíduo, avaliador), pbil (matriz P, elite,
sub-elite, diversidade) e fuzzy (controlador Mamdani) num único laço de
gerações.
"""

import numpy as np

from src.core.individual import amostrar_populacao
from src.core.evaluator import avaliar_populacao
from src.pbil.probability_matrix import inicializar_matriz_p, atualizar_matriz_p
from src.pbil.elite import montar_elite_e_subelite
from src.fuzzy.controller import ControladorFuzzy
from src.fuzzy.rules import (
    verificar_estagnacao,
    esta_muito_proximo_do_otimo,
    aplicar_override_estagnacao,
)
from src.utils.metrics import (
    calcular_meta_features,
    atualizar_cmax_best,
    calcular_diversidade_estrutural_agregada,
)


class ResultadoExecucao:
    """
    Armazena o histórico completo de uma execução do PBIL-Fuzzy, para
    uso posterior em plots (utils/visualization.py) e scripts de
    experimentos (Fase 7).
    """

    def __init__(self):
        self.historico_cmax_best = []
        self.historico_alpha = []
        self.historico_beta = []
        self.historico_diversidade_estrutural = []
        self.melhor_individuo = None
        self.cmax_best = float("inf")

    def registrar_geracao(self, cmax_best, alpha, beta, diversidade_estrutural):
        self.historico_cmax_best.append(cmax_best)
        self.historico_alpha.append(alpha)
        self.historico_beta.append(beta)
        self.historico_diversidade_estrutural.append(diversidade_estrutural)


class PBILFuzzy:
    """
    Motor principal do algoritmo. Encapsula o estado persistente
    (matriz P, Cmax_best, controlador fuzzy) e executa o laço de
    gerações descrito na Seção 6.

    Uso:
        motor = PBILFuzzy(instancia, config)
        resultado = motor.executar(max_geracoes=200)
    """

    def __init__(self, instancia, config, logger=None, gerador_aleatorio=None):
        """
        Parâmetros
        ----------
        instancia : Instancia
        config : dict
            Conteúdo carregado de config.yaml.
        logger : logging.Logger, opcional
        gerador_aleatorio : np.random.Generator, opcional
            Se None, cria um novo a partir de config["execucao"]["seed"].
        """
        self.instancia = instancia
        self.config = config
        self.logger = logger

        seed = config.get("execucao", {}).get("seed", None)
        self.gerador_aleatorio = gerador_aleatorio or np.random.default_rng(seed)

        self.matriz_p = inicializar_matriz_p(
            numero_maquinas=instancia.numero_maquinas,
            numero_jobs=instancia.numero_jobs,
            valor_inicial=config["pbil"]["valor_inicial_matriz_p"],
        )

        self.controlador_fuzzy = ControladorFuzzy()

        self.cmax_best = float("inf")
        self.resultado = ResultadoExecucao()

        self._alpha_anterior = None
        self._beta_anterior = None

    def _amostrar_e_avaliar_populacao(self):
        n_pop = self.config["pbil"]["n_pop"]
        sigma = self.config["pbil"]["sigma_amostragem"]
        distribuicao = self.config["pbil"]["distribuicao_amostragem"]

        populacao = amostrar_populacao(
            self.matriz_p, n_pop, sigma, distribuicao, self.gerador_aleatorio
        )

        for individuo in populacao:
            individuo.decodificar()

        avaliar_populacao(self.instancia, populacao)
        populacao.sort(key=lambda individuo: individuo.cmax)

        return populacao

    def _calcular_alpha_beta(self, meta_features, diversidade_estrutural_agregada):
        """
        Chama o controlador fuzzy e aplica o override de estagnação
        (Seção 5.5) se necessário.
        """
        alpha_fuzzy, beta_fuzzy = self.controlador_fuzzy.calcular(
            q=meta_features["gap_relativo"],
            sigma_rel=meta_features["dispersao_relativa"],
            diversidade_estrutural=diversidade_estrutural_agregada,
        )

        geracoes_estagnacao_limite = self.config["criterio_parada"]["geracoes_estagnacao_limite"]
        limiar_muito_proximo = self.config.get("fuzzy", {}).get(
            "limiar_muito_proximo_override", 0.05
        )  # TODO(aluno): calibrar junto com os limiares da Seção 8

        estagnado = verificar_estagnacao(
            self.resultado.historico_cmax_best, geracoes_estagnacao_limite
        )
        muito_proximo = esta_muito_proximo_do_otimo(
            meta_features["gap_relativo"], limiar_muito_proximo
        )

        alpha, beta, override_aplicado = aplicar_override_estagnacao(
            alpha_fuzzy, beta_fuzzy, estagnado, muito_proximo
        )

        if override_aplicado:
            # "manter comportamento" (Seção 5.5): reusa alpha/beta da
            # geração anterior; na primeira geração cai pro valor do fuzzy
            alpha = self._alpha_anterior if self._alpha_anterior is not None else alpha_fuzzy
            beta = self._beta_anterior if self._beta_anterior is not None else beta_fuzzy

        self._alpha_anterior = alpha
        self._beta_anterior = beta

        return alpha, beta

    def _compor_proxima_populacao(self, subelite, beta):
        """
        Passo 8 da Seção 4.1: beta*N_pop amostrados de P (atualizada),
        (1-beta)*N_pop cópias diretas da sub-elite.

        TODO(aluno): regra de preenchimento se |subelite| for menor que
        (1-beta)*N_pop — atualmente completa amostrando extra de P
        (config.yaml -> diversidade.preenchimento_insuficiente).
        """
        n_pop = self.config["pbil"]["n_pop"]
        sigma = self.config["pbil"]["sigma_amostragem"]
        distribuicao = self.config["pbil"]["distribuicao_amostragem"]

        tamanho_amostrado = round(beta * n_pop)
        tamanho_subelite_desejado = n_pop - tamanho_amostrado

        proxima_populacao = amostrar_populacao(
            self.matriz_p, tamanho_amostrado, sigma, distribuicao, self.gerador_aleatorio
        )

        copias_subelite = list(subelite[:tamanho_subelite_desejado])

        deficit = tamanho_subelite_desejado - len(copias_subelite)
        if deficit > 0:
            preenchimento_extra = amostrar_populacao(
                self.matriz_p, deficit, sigma, distribuicao, self.gerador_aleatorio
            )
            copias_subelite.extend(preenchimento_extra)

        proxima_populacao.extend(copias_subelite)

        for individuo in proxima_populacao:
            individuo.decodificar()

        return proxima_populacao

    def executar(self, max_geracoes=None):
        """
        Executa o laço principal do PBIL-Fuzzy (Seção 6).

        Parâmetros
        ----------
        max_geracoes : int, opcional
            Sobrescreve config["criterio_parada"]["max_geracoes"].

        Retorna
        -------
        ResultadoExecucao
        """
        max_geracoes = max_geracoes or self.config["criterio_parada"]["max_geracoes"]

        pct_elite = self.config["diversidade"]["pct_elite"]
        pct_subelite = self.config["diversidade"]["pct_subelite"]
        delta = self.config["diversidade"]["delta"]

        populacao = self._amostrar_e_avaliar_populacao()

        for numero_geracao in range(1, max_geracoes + 1):
            lista_cmax = [individuo.cmax for individuo in populacao]
            self.cmax_best = atualizar_cmax_best(self.cmax_best, lista_cmax)

            meta_features = calcular_meta_features(lista_cmax, self.cmax_best)

            selecao = montar_elite_e_subelite(
                populacao, self.cmax_best, pct_elite, pct_subelite, delta
            )
            elite = selecao["elite"]
            subelite = selecao["subelite"]
            diversidade_estrutural_agregada = calcular_diversidade_estrutural_agregada(
                selecao["distancias_elegiveis"]
            )

            alpha, beta = self._calcular_alpha_beta(
                meta_features, diversidade_estrutural_agregada
            )

            self.matriz_p = atualizar_matriz_p(self.matriz_p, elite, alpha)

            self.resultado.registrar_geracao(
                self.cmax_best, alpha, beta, diversidade_estrutural_agregada
            )

            if self.logger is not None:
                from src.utils.logger import registrar_geracao
                registrar_geracao(
                    self.logger, numero_geracao, min(lista_cmax), self.cmax_best,
                    alpha, beta, diversidade_estrutural_agregada,
                )

            populacao = self._compor_proxima_populacao(subelite, beta)
            avaliar_populacao(self.instancia, populacao)
            populacao.sort(key=lambda individuo: individuo.cmax)

        melhor_final = min(populacao, key=lambda individuo: individuo.cmax)
        self.resultado.cmax_best = min(self.cmax_best, melhor_final.cmax)
        self.resultado.melhor_individuo = melhor_final

        return self.resultado