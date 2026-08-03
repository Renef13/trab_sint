# Guia de Experimentos - PBIL-Fuzzy para NPFS

Este guia explica como preparar, executar e analisar experimentos do
PBIL-Fuzzy. Ele considera a estrutura atual do projeto e os arquivos em
`src`, `notebooks`, `scripts`, `data` e `config.yaml`.

## 1. Preparacao do ambiente

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Para validar que os imports principais estao funcionando:

```bash
python main.py --config config.yaml --instancia data/instances/Small/I_2_4_2_1.txt --geracoes 5
```

Essa execucao curta serve apenas como teste funcional.

## 2. Antes de rodar experimentos

Confira `config.yaml`, principalmente:

```yaml
pbil:
  n_pop: 80
  distribuicao_amostragem: "normal_truncada"
  sigma_amostragem: 0.25

diversidade:
  pct_elite: 0.08
  pct_subelite: 0.35
  delta: 0.20

fuzzy:
  pesos_progresso_qualidade:
    q: 0.80
    sigma_rel: 0.20

criterio_parada:
  max_geracoes: 300

execucao:
  seed: 42
  n_execucoes_por_instancia: 30
```

A FAM fuzzy inicial ja esta definida em `src/fuzzy/rules.py`. Ela usa
uma politica de intensificacao quando a populacao esta distante do melhor
Cmax historico e de diversificacao quando a diversidade estrutural esta
baixa.

## 3. Execucao unica

Use `main.py` quando quiser estudar uma instancia especifica.

Exemplo com instancia Small:

```bash
python main.py --config config.yaml --instancia data/instances/Small/I_2_4_2_1.txt
```

Exemplo com menos geracoes:

```bash
python main.py --config config.yaml --instancia data/instances/Small/I_2_4_2_1.txt --geracoes 50
```

Exemplo mudando a seed:

```bash
python main.py --config config.yaml --instancia data/instances/Small/I_2_4_2_1.txt --seed 123
```

Saidas esperadas:

- `data/results/outputs/<nome_instancia>.json`
- `data/results/plots/<nome_instancia>_convergencia.png`
- `data/results/plots/<nome_instancia>_alpha_beta.png`
- `data/results/plots/<nome_instancia>_diversidade.png`
- logs em `data/results/logs/`, se habilitados

## 4. Experimentos em lote

Use `scripts/run_experiments.py` para rodar varias instancias.

Small:

```bash
python scripts/run_experiments.py --config config.yaml --diretorio data/instances/Small
```

Large:

```bash
python scripts/run_experiments.py --config config.yaml --diretorio data/instances/Large
```

Sobrescrevendo o numero de execucoes por instancia:

```bash
python scripts/run_experiments.py --config config.yaml --diretorio data/instances/Small --execucoes 5
```

O script salva:

```text
data/results/outputs/resumo_experimentos.json
```

Formato do resumo:

```json
{
  "nome_instancia": {
    "cmax_finais": [1234.0, 1250.0],
    "cmax_medio": 1242.0,
    "cmax_desvio_padrao": 8.0,
    "cmax_melhor": 1234.0,
    "cmax_pior": 1250.0
  }
}
```

## 5. Geracao de graficos

Depois de rodar `scripts/run_experiments.py`, gere o boxplot comparativo:

```bash
python scripts/generate_plots.py --config config.yaml
```

Saida:

```text
data/results/plots/comparacao_instancias_boxplot.png
```

Tambem e possivel informar manualmente um arquivo de resumo:

```bash
python scripts/generate_plots.py --config config.yaml --resumo data/results/outputs/resumo_experimentos.json
```

## 6. Uso dos notebooks

Os notebooks devem ser executados na ordem, porque cada um valida uma fase
do projeto:

1. `notebooks/01_validacao_decodificacao.ipynb`
2. `notebooks/02_validacao_grafo.ipynb`
3. `notebooks/03_teste_fuzzy.ipynb`
4. `notebooks/04_experimentos_Small.ipynb`
5. `notebooks/05_experimentos_Large.ipynb`
6. `notebooks/06_analise_resultados.ipynb`

### Notebook 04

Valida o ciclo completo em instancias Small:

- Carrega `config.yaml`.
- Lista arquivos em `data/instances/Small`.
- Executa uma instancia em detalhe.
- Plota convergencia, alpha/beta e diversidade.
- Monta tabela comparativa de execucao unica.

### Notebook 05

Deve executar as instancias Large em uma amostra controlada. Como Large
pode demorar, recomenda-se configurar:

```python
max_instancias_large = 10
n_execucoes_por_instancia = 3
max_geracoes_large = 100
n_pop_large = 40
```

Para resultados finais, aumente esses valores de forma planejada.

### Notebook 06

Deve carregar os resultados produzidos pelo notebook 05 ou pelos scripts,
calcular estatisticas agregadas e montar graficos de comparacao.

Metricas recomendadas:

- `cmax_melhor`
- `cmax_medio`
- `cmax_desvio_padrao`
- `cmax_pior`
- `tempo_medio_segundos`
- `alpha_medio`
- `beta_medio`
- `diversidade_media`

## 7. Protocolo recomendado para relatorio

Para cada conjunto de instancias:

1. Fixar `seed` base em `config.yaml`.
2. Definir `n_execucoes_por_instancia`.
3. Usar o mesmo `n_pop`, `sigma_amostragem`, `pct_elite`,
   `pct_subelite`, `delta` e `max_geracoes` em todas as instancias do
   mesmo experimento.
4. Rodar todas as instancias do conjunto.
5. Reportar media, desvio padrao, melhor, pior e tempo medio.
6. Guardar os arquivos JSON e CSV usados para gerar tabelas e graficos.
7. Registrar no texto do relatorio os parametros usados na configuracao.

## 8. Interpretacao dos resultados

Use `cmax_melhor` para indicar a melhor solucao encontrada.

Use `cmax_medio` e `cmax_desvio_padrao` para discutir estabilidade. Um
desvio alto indica sensibilidade a seed ou exploracao instavel.

Use `tempo_medio_segundos` para comparar custo computacional.

Use `historico_cmax_best` para verificar convergencia. Uma curva plana
muito cedo pode indicar estagnacao.

Use `historico_alpha`, `historico_beta` e diversidade para discutir o
comportamento do controlador fuzzy.

## 9. Cuidados praticos

- Instancias Large podem demorar bastante. Comece com poucas instancias e
  poucas geracoes.
- Nao misture resultados de configuracoes diferentes no mesmo resumo sem
  registrar os hiperparametros.
- Ao comparar configuracoes, salve cada resumo com nome proprio, por
  exemplo `resumo_large_npop40_ger100.json`.
- Se mudar a FAM ou os limiares fuzzy, rode novamente os experimentos; os
  resultados antigos nao sao comparaveis diretamente.
- `scripts/compare_results.py` compara dois ou mais arquivos
  `resumo_experimentos.json`, gerando tabela com medias, desvios e gap
  percentual por instancia.

## 10. Checklist final de experimento

Antes de usar resultados no relatorio:

- [ ] Configuracao registrada.
- [ ] Instancias usadas registradas.
- [ ] Numero de execucoes por instancia registrado.
- [ ] Seeds registradas ou reprodutiveis.
- [ ] FAM fuzzy e limiares descritos.
- [ ] JSON/CSV de resultados salvo.
- [ ] Graficos gerados a partir dos mesmos dados da tabela.
- [ ] Limitacoes da implementacao explicitadas.
