# PBIL-Fuzzy NPFS

Metaheurística híbrida que combina **PBIL (Population-Based Incremental
Learning)** com um **controlador fuzzy Mamdani** para resolver o
**Non-Permutation Flow Shop Scheduling (NPFS)**.

Projeto desenvolvido para a disciplina de Sistemas Inteligentes — UFMA.

---

## Visão geral do algoritmo

| Componente | Papel |
|---|---|
| Matriz de probabilidades `P` | Estado persistente do PBIL; cada `P[k][i]` é o centro da chave de prioridade do job `i` na máquina `k` |
| Indivíduo `X` | Solução candidata, amostrada a partir de `P`; decodificada em `m` permutações (uma por máquina) |
| Avaliador | Constrói um grafo disjuntivo a partir de `X` e calcula `Cmax` via caminho crítico (caminho mais longo do DAG) |
| Elite / Sub-elite | Mantém diversidade estrutural via distância de Kendall Tau entre permutações — substitui a mutação aleatória do PBIL clássico |
| Controlador fuzzy | Sistema Mamdani com 2 entradas (progresso/qualidade, diversidade estrutural) e 2 saídas (`α`, `β`), que ajusta a intensidade da atualização Hebbiana de `P` e a proporção elite/sub-elite a cada geração |

## Estrutura do projeto

```
PBIL_Fuzzy_NPFS/
├── README.md
├── requirements.txt
├── config.yaml
├── main.py
├── data/
│   ├── instances/          # instâncias de entrada (Small, Large, custom)
│   └── results/             # logs, outputs e plots gerados
├── src/
│   ├── core/                 # instância, indivíduo, avaliador (grafo disjuntivo)
│   ├── pbil/                 # matriz P, elite/sub-elite, diversidade (Kendall Tau)
│   ├── fuzzy/                 # pertinência, regras (FAM 5x3), controlador Mamdani
│   ├── engine/                # ciclo completo do algoritmo
│   └── utils/                 # logging, métricas, visualização
├── notebooks/                 # validação e experimentos exploratórios
├── scripts/                   # execução em lote, geração de gráficos
└── tests/                     # testes unitários
```

## Status do projeto

Em desenvolvimento. Vários hiperparâmetros e detalhes da fuzzificação ainda
estão em aberto — ver `docs/ESPECIFICACAO_TECNICA.md` (Seção 8) e os
comentários `# TODO` em `config.yaml`.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso (placeholder — `main.py` ainda será implementado)

```bash
python main.py --config config.yaml --instancia data/instances/Small/exemplo.txt
```

## Documentação

- Especificação técnica de implementação: `docs/ESPECIFICACAO_TECNICA.md`
- Fundamentação teórica e arquitetura: `docs/ARQUITETURA.md`