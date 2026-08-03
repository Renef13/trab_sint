# Especificacao Tecnica - PBIL-Fuzzy para NPFS

Este documento especifica o algoritmo implementado no projeto. Ele deve
ser lido junto com `docs/ARQUITETURA.md`, que explica a organizacao dos
modulos, e `docs/GUIA_EXPERIMENTOS.md`, que explica como executar os
experimentos.

## 1. Problema

O problema tratado e o **Non-Permutation Flow Shop Scheduling (NPFS)**.
Ha `n` jobs e `m` maquinas. Todo job passa por todas as maquinas na mesma
ordem tecnologica, mas a ordem dos jobs pode ser diferente em cada
maquina.

O objetivo implementado e minimizar:

```text
Cmax = tempo de conclusao da ultima operacao terminada
```

Due dates presentes nos arquivos de instancia sao ignoradas, pois o
trabalho atual usa apenas `Cmax`.

## 2. Instancia

Uma instancia e representada por:

```text
n = numero_jobs
m = numero_maquinas
p[i][k] = tempo de processamento do job i na maquina k
```

No codigo:

- Classe: `src/core/instance.py::Instancia`
- Leitura: `src/core/instance.py::carregar_instancia`
- Lista de arquivos: `src/core/instance.py::listar_instancias`

O arquivo real possui:

```text
n m
m
maq0 tempo0 maq1 tempo1 ...
...
Duedate
...
```

A linha extra com `m` e a secao `Duedate` nao participam da avaliacao.

## 3. Matriz P e individuo

O PBIL mantem uma matriz persistente:

```text
matriz_p: matriz m x n, valores em [0, 1]
matriz_p[k][i] = centro da chave de prioridade do job i na maquina k
```

`matriz_p[k][i]` nao representa a probabilidade de o job existir na
maquina. Em flow shop, todo job passa por toda maquina. O valor e apenas
uma chave continua usada para ordenar jobs.

Um individuo e:

```text
individuo.chaves: matriz m x n, valores em [0, 1]
```

Amostragem:

```text
X[k][i] ~ distribuicao(centro = matriz_p[k][i], dispersao = sigma)
X[k][i] e limitado ao intervalo [0, 1]
```

Distribuicoes implementadas em `src/core/individual.py`:

- `normal_truncada`: usa normal e aplica `clip`.
- `uniforme`: amostra no intervalo `matriz_p +/- sigma` e aplica `clip`.

## 4. Decodificacao

Cada linha da matriz de chaves vira uma permutacao independente:

```text
para cada maquina k:
    ordem[k] = argsort(individuo.chaves[k])
```

Convencao:

```text
menor chave = maior prioridade = executa mais cedo
```

No codigo:

- Classe: `src/core/individual.py::Individuo`
- Metodo: `Individuo.decodificar`
- Amostragem: `amostrar_individuo` e `amostrar_populacao`

## 5. Avaliacao por grafo disjuntivo

A avaliacao constroi um `grafo_disjuntivo` com um vertice para cada
operacao:

```text
(i, k) = operacao do job i na maquina k
```

Arestas de precedencia do job:

```text
(i, k) -> (i, k + 1), peso = p[i][k]
```

Arestas disjuntivas da maquina:

```text
(job_atual, k) -> (proximo_job, k), peso = p[job_atual][k]
```

O `Cmax` e calculado como o comprimento do caminho mais longo no DAG:

```text
Cmax = dag_longest_path_length(grafo_disjuntivo, weight="weight")
```

No codigo:

- `src/core/evaluator.py::construir_grafo_disjuntivo`
- `src/core/evaluator.py::calcular_cmax`
- `src/core/evaluator.py::avaliar_individuo`
- `src/core/evaluator.py::avaliar_populacao`

## 6. Elite, elegiveis e subelite

A populacao e ordenada por menor `Cmax`.

Elite:

```text
elite = top ceil(pct_elite * N_pop)
```

Elegiveis:

```text
elegiveis = individuos com Cmax <= cmax_best * (1 + delta)
            excluindo membros da elite
```

Distancia estrutural de um candidato ate a elite:

```text
dist(s) = media, para cada e em elite, de:
          soma_k distancia_kendall_tau(ordem_k(s), ordem_k(e))
```

Subelite:

```text
subelite = top ceil(pct_subelite * len(elegiveis))
           ordenado por maior dist(s)
```

No codigo:

- `src/pbil/elite.py`
- `src/pbil/diversity.py`

Observacao importante: a distancia e calculada nas permutacoes
decodificadas, nao nas chaves reais.

## 7. Atualizacao Hebbiana da matriz P

A elite produz uma matriz media de chaves:

```text
chave_media_elite[k][i] = media das chaves[k][i] dos membros da elite
```

Atualizacao:

```text
matriz_p_nova = matriz_p * (1 - alpha) + alpha * chave_media_elite
```

Equivalente:

```text
matriz_p_nova = matriz_p + alpha * (chave_media_elite - matriz_p)
```

Como `matriz_p` e `chave_media_elite` estao em `[0, 1]`, a nova matriz
tambem permanece em `[0, 1]`.

No codigo:

- `src/pbil/probability_matrix.py::inicializar_matriz_p`
- `src/pbil/probability_matrix.py::calcular_chave_media_elite`
- `src/pbil/probability_matrix.py::atualizar_matriz_p`

## 8. Controlador fuzzy

O controlador fuzzy e Mamdani, com:

```text
entradas: progresso_qualidade, diversidade_estrutural
saidas: alpha, beta
FAM: 5 x 3 = 15 regras
```

### 8.1 Entrada progresso_qualidade

Primeiro sao calculadas as meta-features:

```text
media_cmax = media dos Cmax da populacao
desvio_padrao_cmax = desvio padrao dos Cmax da populacao
q = (media_cmax - cmax_best) / cmax_best
sigma_rel = desvio_padrao_cmax / media_cmax
```

Depois o controlador combina:

```text
progresso_qualidade = 0.7 * q + 0.3 * sigma_rel
```

Os valores sao limitados ao intervalo `[0, 1]`.

Termos linguisticos:

- `muito_proximo`
- `proximo`
- `moderado`
- `distante`
- `muito_distante`

### 8.2 Entrada diversidade_estrutural

A diversidade estrutural agregada e a media das distancias estruturais
dos elegiveis ate a elite.

Termos linguisticos:

- `baixa`
- `media`
- `alta`

O controlador tambem limita esse sinal a `[0, 1]`.

### 8.3 Saidas

`alpha` controla a intensidade da atualizacao Hebbiana:

```text
alpha alto  -> matriz_p se aproxima mais rapidamente da elite
alpha baixo -> matriz_p preserva mais memoria historica
```

`beta` controla a composicao da proxima populacao:

```text
beta alto  -> mais individuos amostrados da matriz_p
beta baixo -> mais copias diretas da subelite
```

### 8.4 FAM atual

A estrutura da FAM esta implementada em `src/fuzzy/rules.py`, mas as
regras ainda estao como placeholder:

```text
(alpha, beta) = ("medio", "medio")
```

Isso permite testar o pipeline completo, mas ainda nao representa uma
calibracao final do controlador fuzzy.

### 8.5 Estagnacao

A estagnacao e tratada fora da FAM.

```text
estagnado = cmax_best nao melhorou nas ultimas geracoes_estagnacao_limite
muito_proximo = q <= limiar_muito_proximo
```

Se as duas condicoes forem verdadeiras, a engine reutiliza `alpha` e
`beta` da geracao anterior.

No codigo:

- `src/fuzzy/rules.py::verificar_estagnacao`
- `src/fuzzy/rules.py::esta_muito_proximo_do_otimo`
- `src/fuzzy/rules.py::aplicar_override_estagnacao`

## 9. Ciclo completo do PBIL-Fuzzy

Pseudocodigo da implementacao em `src/engine/pbil_fuzzy.py`:

```text
ler instancia
inicializar matriz_p com valor_inicial_matriz_p
inicializar controlador_fuzzy
amostrar e avaliar populacao inicial

para numero_geracao = 1 ate max_geracoes:
    lista_cmax = Cmax de todos os individuos
    cmax_best = min(cmax_best, min(lista_cmax))

    meta_features = calcular media, desvio, q e sigma_rel

    elite, elegiveis, subelite = montar_elite_e_subelite(...)
    diversidade = media das distancias dos elegiveis ate a elite

    alpha, beta = controlador_fuzzy(q, sigma_rel, diversidade)
    aplicar override de estagnacao, se necessario

    matriz_p = atualizacao_hebbiana(matriz_p, elite, alpha)

    registrar historicos:
        cmax_best
        alpha
        beta
        diversidade

    proxima_populacao:
        round(beta * N_pop) individuos amostrados da matriz_p
        restante copiado da subelite
        se faltar subelite, completar amostrando da matriz_p

    avaliar e ordenar proxima_populacao

retornar ResultadoExecucao
```

## 10. Configuracao

Os hiperparametros ficam em `config.yaml`.

### PBIL

- `pbil.n_pop`
- `pbil.valor_inicial_matriz_p`
- `pbil.distribuicao_amostragem`
- `pbil.sigma_amostragem`

### Diversidade

- `diversidade.pct_elite`
- `diversidade.pct_subelite`
- `diversidade.delta`
- `diversidade.preenchimento_insuficiente`

### Fuzzy

- `fuzzy.motor_inferencia`
- `fuzzy.metodo_defuzzificacao`
- `fuzzy.combinacao_q_sigma_rel`
- `fuzzy.tratamento_estagnacao`
- termos linguisticos
- limiares de pertinencia

### Criterio de parada

- `criterio_parada.max_geracoes`
- `criterio_parada.geracoes_estagnacao_limite`

Atualmente a engine usa efetivamente `max_geracoes` como criterio de
parada principal.

## 11. Artefatos de execucao

`main.py` executa uma instancia e salva:

- JSON serializavel da execucao.
- Graficos de convergencia, alpha/beta e diversidade.
- Logs, se habilitados.

`scripts/run_experiments.py` executa varias instancias e salva:

- `resumo_experimentos.json`, com `cmax_finais`, media, desvio, melhor e
  pior Cmax por instancia.

`scripts/generate_plots.py` le esse resumo e gera boxplot comparativo.

## 12. Pontos pendentes

Para transformar a implementacao funcional em versao final de experimento,
faltam:

1. Calibrar as 15 celulas da FAM.
2. Definir limiares reais das funcoes de pertinencia.
3. Validar os pesos da combinacao `q` e `sigma_rel`.
4. Normalizar ou justificar a diversidade estrutural quando a soma por
   maquinas ultrapassar 1.
5. Definir protocolo estatistico final: numero de execucoes, instancias,
   comparacoes e metricas.
6. Implementar ou remover `scripts/compare_results.py`.
