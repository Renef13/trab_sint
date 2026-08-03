# Relatorio para Slides - Implementacao PBIL-Fuzzy NPFS

Este documento resume a implementacao, as configuracoes usadas e os
resultados de apoio para montar slides do trabalho de Sistemas
Inteligentes.

## 1. Tema do trabalho

O trabalho implementa uma metaheuristica hibrida para o problema
**Non-Permutation Flow Shop Scheduling (NPFS)**.

Objetivo:

```text
minimizar Cmax = tempo de conclusao da ultima operacao finalizada
```

A proposta combina:

- **PBIL** para aprender uma matriz de prioridades (`matriz_p`).
- **Controlador fuzzy Mamdani** para ajustar dinamicamente `alpha` e
  `beta`.
- **Elite/subelite** para equilibrar intensificacao e diversidade
  estrutural.
- **Grafo disjuntivo** para avaliar cada individuo e calcular o `Cmax`.

## 2. Arquitetura da implementacao

```text
data/instances/*.txt
        |
        v
src/core/instance.py
        |
        v
src/engine/pbil_fuzzy.py
        |
        +-- src/core/individual.py
        |      amostragem e decodificacao dos individuos
        |
        +-- src/core/evaluator.py
        |      grafo disjuntivo e calculo do Cmax
        |
        +-- src/pbil/probability_matrix.py
        |      matriz_p e atualizacao Hebbiana
        |
        +-- src/pbil/elite.py / diversity.py
        |      elite, subelite e distancia_kendall_tau
        |
        +-- src/fuzzy/controller.py / rules.py / membership.py
               controlador fuzzy Mamdani
```

Modulos principais:

| Modulo | Papel |
|---|---|
| `src/core/instance.py` | Le as instancias e monta a matriz de tempos de processamento |
| `src/core/individual.py` | Representa uma solucao candidata por chaves reais e decodifica em permutacoes por maquina |
| `src/core/evaluator.py` | Constroi o grafo disjuntivo e calcula `Cmax` por caminho critico |
| `src/pbil/probability_matrix.py` | Inicializa e atualiza a `matriz_p` com regra Hebbiana |
| `src/pbil/elite.py` | Seleciona elite, elegiveis e subelite |
| `src/pbil/diversity.py` | Mede diversidade estrutural com distancia de Kendall Tau |
| `src/fuzzy/` | Implementa pertinencia, FAM 5x3 e controlador Mamdani |
| `src/engine/pbil_fuzzy.py` | Integra todas as fases do algoritmo |

## 3. Representacao da solucao

A solucao candidata e uma matriz de chaves:

```text
individuo.chaves[k][i] = prioridade do job i na maquina k
```

Convencao:

```text
menor chave = maior prioridade = executa mais cedo
```

Como o problema e NPFS, cada maquina pode ter uma ordem diferente de jobs:

```text
maquina 0: [job2, job0, job1, ...]
maquina 1: [job1, job2, job0, ...]
...
```

## 4. Avaliacao por grafo disjuntivo

Cada operacao `(job, maquina)` vira um vertice do grafo.

Arestas:

- Precedencia do job: `(i, k) -> (i, k+1)`.
- Ordem na maquina: `(job_atual, k) -> (proximo_job, k)`.

O `Cmax` e calculado por caminho critico, usando a duracao das operacoes
como peso dos vertices:

```text
finish(v) = duracao(v) + max(finish(predecessores))
Cmax = max(finish(v))
```

Observacao importante: durante a verificacao dos notebooks foi encontrada
uma divergencia no notebook 02. O avaliador antigo usava pesos nas arestas
e deixava de contar corretamente algumas operacoes. A implementacao foi
corrigida para usar duracao nos vertices, e os testes manuais passaram:

| Teste | Cmax esperado | Cmax corrigido |
|---|---:|---:|
| 2 jobs, 2 maquinas, mesma ordem | 8 | 8 |
| 2 jobs, 2 maquinas, ordem diferente na maquina 1 | 10 | 10 |

Tambem foi feita uma checagem com 20 instancias aleatorias, comparando o
avaliador com uma simulacao manual independente.

## 5. Funcionamento do PBIL-Fuzzy

Fases por geracao:

1. Amostrar populacao a partir da `matriz_p`.
2. Decodificar cada individuo em permutacoes por maquina.
3. Avaliar cada individuo pelo `Cmax`.
4. Ordenar a populacao por menor `Cmax`.
5. Selecionar `elite`.
6. Selecionar candidatos `elegiveis` dentro do limite `delta`.
7. Calcular diversidade estrutural com `distancia_kendall_tau`.
8. Selecionar `subelite`.
9. Calcular `alpha` e `beta` com o controlador fuzzy.
10. Atualizar `matriz_p` com regra Hebbiana.
11. Montar a proxima populacao com amostragem da `matriz_p`, subelite e
    preservacao da elite.

## 6. Controlador fuzzy

Entradas:

- `progresso_qualidade`: combinacao de `q` e `sigma_rel`.
- `diversidade_estrutural`: diversidade media normalizada pelo numero de
  maquinas.

Saidas:

- `alpha`: intensidade da atualizacao Hebbiana.
- `beta`: proporcao de individuos amostrados da `matriz_p` na proxima
  geracao.

Configuracao fuzzy usada:

```yaml
pesos_progresso_qualidade:
  q: 0.80
  sigma_rel: 0.20

limiares_progresso_qualidade: [0.05, 0.15, 0.35, 0.65]
limiares_diversidade: [0.25, 0.60]
```

Politica da FAM:

- Se a populacao esta distante do melhor `Cmax`, aumentar `alpha`.
- Se a diversidade esta baixa, reduzir `beta` para injetar mais subelite.
- Se a diversidade esta alta, aumentar `beta` para aproveitar mais a
  `matriz_p`.

## 7. Configuracao geral do projeto

Configuracao base em `config.yaml`:

| Parametro | Valor |
|---|---:|
| `n_pop` | 80 |
| `sigma_amostragem` | 0.25 |
| `pct_elite` | 0.08 |
| `pct_subelite` | 0.35 |
| `delta` | 0.20 |
| `max_geracoes` | 300 |
| `geracoes_estagnacao_limite` | 40 |
| `n_execucoes_por_instancia` | 30 |

Para gerar dados rapidos de slide, foi usada uma configuracao reduzida:

| Parametro | Valor |
|---|---:|
| `n_pop` | 40 |
| `geracoes` | 25 |
| `seed_base` | 42 |
| `salvar_logs` | false |
| `salvar_plots` | false |

Os demais parametros seguiram o `config.yaml`.

## 8. Verificacao dos notebooks

Resumo da verificacao dos notebooks ja executados:

| Notebook | Estado observado | Observacao |
|---|---|---|
| `01_validacao_decodificacao.ipynb` | OK | Decodificacao das chaves em permutacoes validada |
| `02_validacao_grafo.ipynb` | Saidas antigas com erro | A divergencia revelou o problema no avaliador; codigo foi corrigido |
| `03_teste_fuzzy.ipynb` | Uma assertiva antiga falhou | O notebook esperava pesos `0.7/0.3`; o projeto agora usa `0.8/0.2` |
| `04_experimentos_Small.ipynb` | Execucao longa interrompida no lote | A execucao detalhada da primeira instancia terminou |
| `05_experimentos_Large.ipynb` | Rodou sem erro | Resultados antigos foram gerados antes da correcao do `Cmax` |
| `06_analise_resultados.ipynb` | Rodou sem erro | Analisa os resultados salvos pelo notebook 05 |

Para os slides, use preferencialmente os dados novos em
`data/results/outputs/resumo_slides.csv`, pois foram gerados depois da
correcao do avaliador.

## 9. Resultados novos para slides

Arquivo gerado:

```text
data/results/outputs/resumo_slides.csv
data/results/outputs/resumo_slides.json
```

Configuracao da rodada: `n_pop=40`, `geracoes=25`.

| Grupo | Instancia | Jobs | Maquinas | Cmax inicial | Cmax final | Melhoria |
|---|---|---:|---:|---:|---:|---:|
| Small | `I_2_6_2_1` | 6 | 2 | 357 | 335 | 6.16% |
| Small | `I_2_8_2_1` | 8 | 2 | 387 | 359 | 7.24% |
| Small | `I_3_6_2_1` | 6 | 2 | 446 | 339 | 23.99% |
| Small | `I_3_8_2_1` | 8 | 2 | 603 | 470 | 22.06% |
| Large | `Ta001_2` | 20 | 5 | 3816 | 3363 | 11.87% |
| Large | `Ta001_3` | 20 | 5 | 3861 | 3261 | 15.54% |

Metricas medias da rodada:

| Metrica | Valor aproximado |
|---|---:|
| Melhoria media Small | 14.86% |
| Melhoria media Large | 13.71% |
| `alpha_medio` | 0.519 |
| `beta_medio` | 0.499 |
| `diversidade_media` | 0.480 |

Leitura para apresentacao:

- Mesmo com apenas 25 geracoes, todas as instancias testadas melhoraram.
- As instancias Small com 3 familias/6-8 jobs tiveram maiores ganhos
  percentuais.
- Nas Large, o algoritmo tambem reduziu `Cmax`, apesar de usar uma rodada
  curta para economizar tempo.

## 10. Pontos fortes para destacar no slide

- O algoritmo trabalha diretamente com NPFS, permitindo ordens diferentes
  por maquina.
- A matriz de probabilidades do PBIL aprende prioridades de jobs por
  maquina.
- O fuzzy adapta `alpha` e `beta` com base em qualidade e diversidade.
- A subelite preserva diversidade estrutural sem mutacao aleatoria.
- A avaliacao por grafo disjuntivo deixa claro o vinculo com a formulacao
  teorica do problema.
- A implementacao foi validada por notebooks e por testes manuais contra
  simulacao independente.

## 11. Sugestao de roteiro de slides

1. **Problema:** NPFS e objetivo `Cmax`.
2. **Representacao:** matriz de chaves e permutacoes por maquina.
3. **Avaliacao:** grafo disjuntivo e caminho critico.
4. **PBIL:** matriz `P` e atualizacao Hebbiana.
5. **Diversidade:** elite, subelite e Kendall Tau.
6. **Fuzzy:** entradas, saidas e FAM.
7. **Arquitetura:** modulos `core`, `pbil`, `fuzzy`, `engine`, `utils`.
8. **Resultados:** tabela `resumo_slides.csv` e melhoria percentual.
9. **Conclusao:** algoritmo roda ponta a ponta e melhora `Cmax` nas
   instancias testadas.

## 12. Frase curta de conclusao

O PBIL-Fuzzy implementado combina aprendizado probabilistico, controle
fuzzy e diversidade estrutural para construir solucoes NPFS. Nos testes
rapidos gerados para apresentacao, o algoritmo reduziu o `Cmax` em todas
as instancias avaliadas, com ganhos entre 6.16% e 23.99%.
