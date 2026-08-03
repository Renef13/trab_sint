# Arquitetura do Projeto - PBIL-Fuzzy para NPFS

Este documento descreve como o projeto esta organizado e como os modulos
conversam entre si. A especificacao matematica do algoritmo fica em
`docs/ESPECIFICACAO_TECNICA.md`; aqui o foco e a arquitetura de software.

## Visao geral

O projeto implementa uma metaheuristica hibrida para o problema
**Non-Permutation Flow Shop Scheduling (NPFS)**. A busca e conduzida por
PBIL, representado por uma `matriz_p`, e adaptada por um
`controlador_fuzzy` Mamdani, que ajusta `alpha` e `beta` a cada geracao.

O fluxo principal e:

```text
arquivo .txt da instancia
        |
        v
carregar_instancia()
        |
        v
PBILFuzzy.executar()
        |
        +--> amostrar_populacao() e decodificar individuos
        +--> calcular_cmax() via grafo_disjuntivo
        +--> selecionar elite/subelite por Cmax e distancia_kendall_tau
        +--> controlador_fuzzy calcula alpha/beta
        +--> atualizacao_hebbiana da matriz_p
        |
        v
ResultadoExecucao com historicos e melhor Cmax
```

## Estrutura de diretorios

```text
.
+-- config.yaml
+-- main.py
+-- data/
|   +-- instances/
|   |   +-- Small/
|   |   +-- Large/
|   +-- results/
|       +-- logs/
|       +-- outputs/
|       +-- plots/
+-- docs/
+-- notebooks/
+-- scripts/
+-- src/
|   +-- core/
|   +-- pbil/
|   +-- fuzzy/
|   +-- engine/
|   +-- utils/
+-- tests/
```

## Camadas do sistema

### `src/core`

Contem a base do problema NPFS.

- `instance.py`: le arquivos `.txt`, cria uma `Instancia` com
  `numero_jobs`, `numero_maquinas` e `tempos_processamento`.
- `individual.py`: define `Individuo`, sua matriz de chaves e a
  decodificacao em uma permutacao por maquina.
- `evaluator.py`: constroi o `grafo_disjuntivo` e calcula `Cmax` pelo
  caminho critico do DAG, usando a duracao das operacoes como peso dos nos.

Essa camada nao conhece PBIL, fuzzy, elite ou subelite. Ela so sabe
representar e avaliar solucoes.

### `src/pbil`

Contem os operadores de aprendizado incremental e diversidade estrutural.

- `probability_matrix.py`: inicializa a `matriz_p`, calcula a chave media
  da elite e aplica a `atualizacao_hebbiana`.
- `diversity.py`: calcula `distancia_kendall_tau` entre permutacoes e a
  distancia estrutural de candidatos ate a elite.
- `elite.py`: seleciona `elite`, `elegiveis` e `subelite`.

A decisao importante desta arquitetura e que a diversidade nao muta a
`matriz_p`. A subelite e reinjetada diretamente na proxima populacao.

### `src/fuzzy`

Contem o controlador fuzzy Mamdani.

- `membership.py`: cria as funcoes de pertinencia para
  `progresso_qualidade`, `diversidade_estrutural`, `alpha` e `beta`.
- `rules.py`: declara a FAM 5x3 com politica inicial de intensificacao e
  diversificacao.
- `controller.py`: combina `q` e `sigma_rel`, executa a inferencia fuzzy e
  retorna `(alpha, beta)`.

O fuzzy recebe sinais calculados pela engine e devolve hiperparametros de
controle. Ele nao avalia individuos diretamente.

### `src/engine`

Contem o ciclo completo do algoritmo.

- `pbil_fuzzy.py`: define `PBILFuzzy` e `ResultadoExecucao`.

`PBILFuzzy` e a camada que integra todas as outras: instancia, individuos,
avaliador, matriz P, elite/subelite, metricas e controlador fuzzy.

### `src/utils`

Contem infraestrutura de apoio.

- `metrics.py`: calcula media, desvio padrao, gap relativo,
  dispersao relativa, `cmax_best` e diversidade agregada.
- `visualization.py`: gera graficos de convergencia, alpha/beta,
  diversidade e boxplot comparativo.
- `logger.py`: configura logs para execucoes via scripts e `main.py`.

## Entradas e saidas

### Entradas

- `config.yaml`: hiperparametros do PBIL, diversidade, fuzzy, criterio de
  parada e caminhos de saida.
- `data/instances/Small/*.txt`: instancias pequenas.
- `data/instances/Large/*.txt`: instancias grandes.

O formato de instancia contem `n`, `m`, linhas com pares
`maquina tempo`, e uma secao `Duedate` ignorada nesta implementacao,
porque a funcao objetivo e `Cmax`.

### Saidas

`main.py` salva:

- JSON da execucao em `data/results/outputs/<instancia>.json`.
- Graficos em `data/results/plots/`, quando `execucao.salvar_plots` esta
  habilitado.
- Logs em `data/results/logs/`, quando `execucao.salvar_logs` esta
  habilitado.

`scripts/run_experiments.py` salva:

- `data/results/outputs/resumo_experimentos.json`, com estatisticas por
  instancia.

Os notebooks 04, 05 e 06 tambem podem gerar tabelas e arquivos de resumo
para analise exploratoria.

## Contratos entre modulos

### Instancia

`Instancia` deve expor:

- `numero_jobs`
- `numero_maquinas`
- `tempos_processamento`
- `nome`

O shape de `tempos_processamento` e sempre:

```text
(numero_jobs, numero_maquinas)
```

### Individuo

`Individuo` deve expor:

- `chaves`: matriz real `(numero_maquinas, numero_jobs)`.
- `ordens_por_maquina`: lista preenchida por `decodificar()`.
- `cmax`: preenchido por `avaliar_individuo()`.

A convencao de decodificacao e fixa: menor chave significa maior
prioridade na maquina.

### ResultadoExecucao

`ResultadoExecucao` guarda os historicos usados por notebooks, plots e
relatorios:

- `historico_cmax_best`
- `historico_alpha`
- `historico_beta`
- `historico_diversidade_estrutural`
- `melhor_individuo`
- `cmax_best`

## Decisoes arquiteturais

1. O avaliador usa `networkx.DiGraph` e caminho critico com duracao nos
   vertices para manter a implementacao alinhada com a formulacao por
   grafo disjuntivo.
2. A `matriz_p` representa centros de chaves de prioridade, nao
   probabilidades discretas de alocacao.
3. A diversidade e medida nas permutacoes decodificadas, nao nas chaves
   reais, porque chaves diferentes podem gerar a mesma ordem.
4. A subelite entra por injecao direta na proxima geracao, substituindo a
   mutacao aleatoria do PBIL classico.
5. O controlador fuzzy esta isolado em `src/fuzzy`, permitindo trocar
   limiares, pertinencias e FAM sem mexer no avaliador ou no PBIL.
6. O criterio de parada efetivamente implementado na engine e o numero de
   geracoes. A estagnacao hoje atua apenas como override de alpha/beta.

## Estado atual

O projeto ja executa ponta a ponta com uma configuracao inicial completa:

- A FAM em `src/fuzzy/rules.py` diferencia cenarios de proximidade e
  diversidade, ajustando `alpha` e `beta`.
- As funcoes de pertinencia usam limiares triangulares definidos em
  `config.yaml`.
- `q` e `sigma_rel` sao combinados por media ponderada com pesos 0.80 e
  0.20.
- A diversidade estrutural e normalizada pelo numero de maquinas antes de
  entrar no fuzzy.
- `scripts/compare_results.py` compara dois ou mais resumos de
  experimentos por `cmax_medio`, `cmax_melhor`, desvio e gap percentual.

Esses valores sao uma calibracao heuristica inicial. Eles tornam o sistema
executavel sem lacunas, mas ainda podem ser refinados por comparacao
experimental no relatorio.
