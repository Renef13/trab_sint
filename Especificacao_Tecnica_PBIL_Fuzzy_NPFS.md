# Especificação Técnica de Implementação — PBIL-Fuzzy para o NPFS

Documento de especificação, não de fundamentação. Contém apenas as estruturas de dados, fórmulas e algoritmos já decididos, no nível de detalhe necessário para implementar diretamente. Onde algo ainda está em aberto (Seção 8), está marcado como `TODO(aluno)` — o resto é especificação fechada.

---

## 1. Entrada e estruturas de dados

**Instância:** `n` jobs, `m` máquinas, matriz de tempos `p[i][k]` (job *i*, máquina *k*), lida de um `.txt`.

**Matriz de probabilidades (estado persistente do PBIL):**
```
P : matriz m × n, valores em [0,1]
P[k][i] = centro da chave de prioridade do job i na máquina k
```
`P[k][i]` **não** é probabilidade de o par (job, máquina) existir — em flow shop todo job passa por toda máquina, isso é fixo. `P[k][i]` só tem significado relativo às outras entradas da mesma linha `k`.

**Convenção de decodificação:** menor chave = maior prioridade = executa mais cedo na fila daquela máquina.

**Indivíduo (solução candidata):**
```
X : matriz m × n, amostrada a partir de P
X[k][i] ~ dist(centro = P[k][i], dispersão = σ), truncada/clipada em [0,1]
```
`dist` = uniforme ou normal truncada — `TODO(aluno)`, ver Seção 8.

**Decodificação (X → permutações por máquina):**
```
para cada máquina k:
    ordem[k] = jobs ordenados por X[k][:] crescente
```
Resultado: `m` permutações independentes → solução NPFS válida por construção (nunca gera ciclo, ver Seção 2).

---

## 2. Avaliação — grafo disjuntivo → Cmax

**Vértices:** uma operação `(i, k)` por par job×máquina.

**Arestas de precedência** (fixas, da instância): `(i,k) → (i,k+1)`, peso = `p[i][k]`.

**Arestas disjuntivas** (da solução candidata): para cada máquina `k`, conectam jobs consecutivos na `ordem[k]` decodificada.

**Cálculo:**
```
Start(i,k) = max( Finish(i,k-1),           # precedência dentro do job
                   Finish(job_anterior,k)  # ordem escolhida na máquina
                 )
Finish(i,k) = Start(i,k) + p[i][k]
Cmax = max sobre todas as operações de Finish(i,k)
     = comprimento do caminho mais longo (caminho crítico) do DAG
```

**Implementação:** montar o grafo (`networkx.DiGraph`), pesos = tempos de processamento, e chamar `networkx.dag_longest_path_length()`.

**Por que caminho mais longo:** `Start` é sempre o `max` das duas dependências (a operação só começa quando ambas terminaram), e esse `max` recursivo propagado pela cadeia de dependências é, por definição, o caminho mais longo ponderado do DAG.

---

## 3. Regra de atualização Hebbiana (elite → P)

```
P[k][i] ← P[k][i]·(1 − α) + α · X*[k][i]
```

- `X*[k][i]` = valor da chave, na posição `(k,i)`, do(s) indivíduo(s) da **elite** daquela geração (Seção 4). Se `|elite| > 1`, `X*[k][i]` = média das chaves da elite nessa posição.
- Equivalente algébrico (mostra que a direção do ajuste é automática): `P_novo = P_antigo + α·(X* − P_antigo)`.
- Propriedade garantida: como `P_antigo, X* ∈ [0,1]` e os pesos somam 1, `P_novo ∈ [0,1]` sempre — não precisa de clipping adicional neste passo.

---

## 4. Mecanismo de diversidade — Elite / Sub-elite / Injeção direta

**Substitui completamente** a mutação aleatória do vetor de probabilidades do PBIL clássico. Não existe matriz `Q`; a sub-elite é injetada diretamente.

### 4.1 Passo a passo, por geração

```
1. Amostrar população de N_pop indivíduos a partir de P (Seção 1)
2. Decodificar e avaliar todos (Cmax via Seção 2)
3. Ordenar por Cmax crescente

4. ELITE:
   elite = top pct_elite% da população, por menor Cmax
   → usar elite para calcular X* e atualizar P (Seção 3)

5. GRUPO ELEGÍVEL PARA SUB-ELITE:
   Cmax_best = menor Cmax já encontrado (histórico, não só desta geração)
   elegiveis = { s ∈ população : Cmax(s) ≤ Cmax_best · (1 + δ) }
                 excluindo os já selecionados como elite

6. DISTÂNCIA ESTRUTURAL (só para quem está em `elegiveis`):
   para cada candidato s em elegiveis:
       dist(s) = média sobre e em elite de
                   Σ_k  KendallTau( ordem_k(s), ordem_k(e) )
   # soma da distância de Kendall Tau entre as permutações de cada
   # máquina, depois média sobre os membros da elite

7. SUB-ELITE:
   subelite = top pct_subelite% de `elegiveis`, por maior dist(s)

8. PRÓXIMA GERAÇÃO:
   β · N_pop indivíduos → amostrados a partir de P (atualizado no passo 4)
   (1-β) · N_pop indivíduos → cópias diretas dos indivíduos de `subelite`
                                (sem ruído, sem jitter, sem síntese estatística)
   # se |subelite| < (1-β)·N_pop, decisão de preenchimento do resto
   # é TODO(aluno) — ver Seção 8
```

### 4.2 Por que essa ordem de critérios (não outra)

- Cmax filtra **qualidade** (passo 5); Kendall Tau filtra **estrutura** (passo 6) — nunca se usa Cmax como proxy de diversidade, nem se mede distância sobre as chaves reais cruas (redundância: chaves diferentes podem decodificar na mesma permutação).
- A distância é sempre candidato-vs-conjunto-elite, nunca candidato-vs-"elite média" (não existe média bem definida de permutações).

---

## 5. Controlador Fuzzy — especificação exata

### 5.1 Arquitetura

```
                 ┌────────────────────┐
Progresso/       │                    │
Qualidade ──────►│    MAMDANI         │────► α
                 │                    │
Diversidade ────►│                    │────► β
                 └────────────────────┘
```

Um único sistema Mamdani, 2 entradas, 2 saídas, FAM 5×3 = 15 regras (cada célula produz um par `(α, β)`).

### 5.2 Entrada 1 — Progresso/Qualidade

```
μ = média dos Cmax da população atual
σ = desvio padrão dos Cmax da população atual
Cmax_best = melhor Cmax já encontrado (histórico)

q      = (μ − Cmax_best) / Cmax_best     # gap relativo; menor = melhor
σ_rel  = σ / μ                           # dispersão relativa
```

5 termos linguísticos (nível de proximidade ao ótimo, não tendência entre gerações):

| Termo | Sentido |
|---|---|
| Muito distante do ótimo | q alto |
| Distante | |
| Moderado | |
| Próximo | |
| Muito próximo do ótimo | q baixo |

Como combinar `q` e `σ_rel` num único valor fuzzificado (ou tratá-los como sub-componentes da mesma variável) — `TODO(aluno)`, Seção 8.

> **Nota de viés conhecida:** `Cmax_best` só melhora/mantém ao longo da busca, então `q` tende a cair estruturalmente com o tempo — o controlador pode "achar" que a população está sempre se aproximando do ótimo mesmo sem mudança real de comportamento. Registrado, não resolvido nesta versão.

### 5.3 Entrada 2 — Diversidade estrutural

Valor calculado no passo 6 da Seção 4.1 (distância de Kendall Tau agregada), 3 termos: **baixa / média / alta**.

### 5.4 Saídas

| Saída | Significado | Efeito |
|---|---|---|
| α | intensidade da atualização Hebbiana (Seção 3) | alto = confia mais na elite atual; baixo = preserva conhecimento acumulado em P |
| β | proporção elite (via P) vs. sub-elite (injeção direta) na próxima geração (Seção 4.1, passo 8) | alto = mais intensificação; baixo = mais exploração |

### 5.5 Esqueleto da FAM (5×3)

Preencher com `↑ / → / ↓` para α e β em cada célula — só a primeira linha abaixo já está decidida:

| Progresso/Qualidade \ Diversidade | Baixa | Média | Alta |
|---|---|---|---|
| Muito próximo do ótimo **+ estagnado** | — | — | **α → , β →** *(manter comportamento — decidido)* |
| Muito próximo do ótimo | `TODO` | `TODO` | `TODO` |
| Próximo | `TODO` | `TODO` | `TODO` |
| Moderado | `TODO` | `TODO` | `TODO` |
| Distante | `TODO` | `TODO` | `TODO` |
| Muito distante do ótimo | `TODO` | `TODO` | `TODO` |

> A linha "Muito próximo do ótimo + estagnado" foi destacada à parte porque "estagnado" não é, tecnicamente, um dos 5 termos de Progresso/Qualidade (que mede nível, não tendência) — é preciso decidir, junto com o preenchimento da FAM, se estagnação entra como parte da fuzzificação de Progresso/Qualidade ou se é tratada por fora (ver Seção 8).

### 5.6 Motor de inferência

- Tipo: **Mamdani** (único suportado nativamente por `scikit-fuzzy`).
- Fuzzificação → aplicação das 15 regras → agregação → defuzzificação (ex.: centróide) para cada uma das duas saídas, α e β, independentemente, a partir do mesmo conjunto de regras/antecedentes.

---

## 6. Pseudocódigo do ciclo completo

```
ler instância → n, m, p[i][k]
inicializar P (m × n), todos os valores em 0.5 (ou outro ponto neutro)
Cmax_best ← +infinito

para geração = 1 até critério_de_parada:

    # 1. Amostragem e avaliação
    população ← amostrar N_pop indivíduos X a partir de P (Seção 1)
    para cada X em população:
        ordens ← decodificar(X)                       # Seção 1
        Cmax(X) ← avaliar_grafo_disjuntivo(ordens, p)  # Seção 2
    ordenar população por Cmax crescente
    Cmax_best ← min(Cmax_best, min(Cmax da população))

    # 2. Meta-features (entradas do fuzzy)
    μ, σ ← média e desvio padrão dos Cmax da população
    q ← (μ − Cmax_best) / Cmax_best
    σ_rel ← σ / μ

    elite ← top pct_elite% da população                     # Seção 4.1
    elegiveis ← { Cmax(s) ≤ Cmax_best·(1+δ) } \ elite
    dist(s) ← distância de Kendall Tau média até a elite, ∀s ∈ elegiveis
    subelite ← top pct_subelite% de elegiveis por dist(s)
    diversidade_estrutural ← agregado de dist(s) sobre a população (ex.: média)

    # 3. Controlador fuzzy
    (α, β) ← fuzzy_mamdani(entrada_progresso = (q, σ_rel),
                            entrada_diversidade = diversidade_estrutural)  # Seção 5

    # 4. Atualização de P (Hebbiana)
    X* ← média das chaves da elite, posição a posição
    P ← P·(1−α) + α·X*                                        # Seção 3

    # 5. Composição da próxima geração
    próxima_população ← concat(
        amostrar β·N_pop indivíduos a partir do P atualizado,
        copiar diretamente (1−β)·N_pop indivíduos de subelite   # sem ruído
    )

retornar melhor solução encontrada (Cmax_best, ordens correspondentes)
```

---

## 7. Hiperparâmetros — lista fechada

| Hiperparâmetro | Controlado por | Observação |
|---|---|---|
| α | Fuzzy (saída) | Seção 5.4 |
| β | Fuzzy (saída) | Seção 5.4 |
| δ | Fixo/experimental | teto de 20%, valor exato = `TODO(aluno)` |
| pct_elite | Fixo/experimental | `TODO(aluno)` |
| pct_subelite | Fixo/experimental | `TODO(aluno)` — aplicado sobre `elegiveis`, não sobre a população total |
| σ (dispersão da amostragem de X) | Fixo/experimental | `TODO(aluno)` |
| N_pop (tamanho da população) | Fixo/experimental | `TODO(aluno)` |
| Critério de parada | Fixo/experimental | `TODO(aluno)` (nº gerações / estagnação / combinação) |
| Funções de pertinência (todas as variáveis fuzzy) | Fixo/experimental | `TODO(aluno)` |
| Regras da FAM (14 das 15 células) | Fixo/experimental | `TODO(aluno)`, Seção 5.5 |

**Removido do escopo:** força de mutação/decaimento do vetor de probabilidades — não existe mais; substituída pelo mecanismo da Seção 4.

---

## 8. `TODO(aluno)` — decisões que faltam para fechar a especificação

1. Distribuição de amostragem de `X[k][i]` em torno de `P[k][i]`: uniforme ou normal truncada, e valor de σ.
2. Preenchimento das 14 células restantes da FAM (Seção 5.5).
3. Funções de pertinência (formato — triangular, trapezoidal — e limiares) de todas as variáveis fuzzy, incluindo os cortes de `q` e `σ_rel` que definem cada termo de Progresso/Qualidade.
4. Se "estagnação" é tratada como parte da fuzzificação de Progresso/Qualidade, ou como uma verificação separada por fora do fuzzy (ver nota da Seção 5.5).
5. Como combinar `q` e `σ_rel` num único sinal de entrada (ou mantê-los como dois sub-componentes fuzzificados separadamente dentro da mesma variável linguística).
6. Regra de preenchimento caso `|subelite| < (1−β)·N_pop` (repetir indivíduos? completar com amostragem extra de P? reduzir N_pop efetivo nessa geração?).
7. `pct_elite`, `pct_subelite`, `δ`, `N_pop`, critério de parada — valores numéricos exatos.

Tudo o mais neste documento é especificação fechada, pronta para implementar.
