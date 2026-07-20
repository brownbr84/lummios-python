# lummios

Cliente Python para a **[Lummios Developer](https://developers.lummios.com.br)** — API de
dados fundamentalistas da B3/CVM: fundamentos linha a linha desde 2010, cotações ajustadas
por eventos societários, indicadores, dividendos, dados prudenciais de bancos (Basileia/CET1
via Banco Central) e análises de IA com explicabilidade.

[![tests](https://github.com/brownbr84/lummios-python/actions/workflows/test.yml/badge.svg)](https://github.com/brownbr84/lummios-python/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/lummios.svg)](https://pypi.org/project/lummios/)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Instalação

```bash
pip install lummios
```

> Se o pacote ainda não estiver publicado no PyPI, instale direto do GitHub:
> `pip install git+https://github.com/brownbr84/lummios-python.git`

## Chave de API

Gere uma chave gratuita (1.000 requisições/dia) em
**[developers.lummios.com.br](https://developers.lummios.com.br)** — leva 30 segundos, sem
cartão de crédito.

## Uso rápido

```python
from lummios import LummiosClient

client = LummiosClient(api_key="sua_chave")

# ou, definindo a variável de ambiente LUMMIOS_API_KEY:
# client = LummiosClient()

fund = client.fundamentals("PETR4")
print(fund["p_l"], fund["roe"], fund["dividend_yield"])
```

### Screener fundamentalista

```python
resultado = client.screener(roe_min=15, div_liq_ebitda_max=3, setor="Petróleo, Gás e Biocombustíveis")
for ativo in resultado:
    print(ativo["ticker_ref"], ativo["pl_ratio"], ativo["dividend_yield"])
```

### Histórico ajustado (split + total return) para backtest

```python
historico = client.historico_ajustado("WEGE3")
for ponto in historico:
    print(ponto["date"], ponto["adj_close_tr"])  # ajustado por splits + proventos
```

### Índice de Basileia de um banco

```python
banco = client.bank_indicators("ITUB4")
print(banco["basileia_valor"], banco["indice_eficiencia"], banco["roaa"])
```

### Checks factuais (estilo "fato + fonte", CVM-safe)

```python
checks = client.checks("VALE3")
for nome, resumo in checks["dimensoes"].items():
    print(nome, f"{resumo['atende']}/{resumo['total']} atende")

for c in checks["checks"]:
    print(c["dimensao"], "-", c["pergunta"], "->", c["atende"], f"(valor={c['valor']}, referência={c['referencia']})")
```

### Qualquer endpoint da API (escape hatch)

O cliente cobre os métodos de uso mais comum, mas a API tem 50+ rotas
([referência completa](https://developers.lummios.com.br/docs.html)). Para qualquer
endpoint sem atalho dedicado, use `.get()` diretamente:

```python
client.get("/v1/tickers/PETR4/governance")
client.get("/v1/tickers/PETR4/esg")
client.get("/v1/mercado/breadth")
```

## Tratamento de erros

```python
from lummios import LummiosAuthError, LummiosQuotaError, LummiosAPIError

try:
    client.fundamentals("PETR4")
except LummiosAuthError:
    print("chave inválida ou ausente")
except LummiosQuotaError as e:
    print(f"cota diária ({e.daily_quota}) atingida — faça upgrade do plano")
except LummiosAPIError as e:
    print(f"erro da API: {e.status_code}")
```

## Cobertura de métodos

| Método | Endpoint |
|---|---|
| `ticker(t)` | `/v1/tickers/{t}` |
| `fundamentals(t)` | `/v1/tickers/{t}/fundamentals` |
| `historico(t, **params)` | `/v1/tickers/{t}/historico` |
| `historico_ajustado(t, **params)` | `/v1/tickers/{t}/historico-ajustado` |
| `multiplos_historico(t, **params)` | `/v1/tickers/{t}/multiplos-historico` |
| `dividends(t)` | `/v1/tickers/{t}/dividends` |
| `corporate_actions(t)` | `/v1/tickers/{t}/corporate-actions` |
| `dfp_completo(t, **params)` | `/v1/tickers/{t}/dfp-completo` |
| `checks(t)` | `/v1/tickers/{t}/checks` |
| `bank_indicators(t)` | `/v1/tickers/{t}/bank-indicators` |
| `peers(t)` | `/v1/tickers/{t}/peers` |
| `ai_explicabilidade(t)` | `/v1/tickers/{t}/ai-explicabilidade` |
| `valor_intrinseco(t)` | `/v1/tickers/{t}/valor-intrinseco` |
| `info(t)` | `/v1/tickers/{t}/info` |
| `mercado_resumo()` | `/v1/mercado/resumo` |
| `maiores_altas()` / `maiores_baixas()` / `maior_volume()` | `/v1/mercado/...` |
| `screener(**params)` | `/v1/screener` |
| `classificacao()` | `/v1/classificacao` |
| `comparar(tickers, **params)` | `/v1/comparar` |
| `macro()` | `/v1/macro` |
| `dataset_info()` | `/v1/info` |
| `get(path, **params)` | qualquer rota (referência completa nos docs) |

## Sobre os dados

- **Fundamentos CVM**: DFP/ITR linha a linha, FY2010 → presente.
- **Cotações B3**: histórico completo, ajustadas por splits/proventos, point-in-time.
- **Dados bancários**: Basileia/CET1/Tier1 de instituições financeiras (BCB IFData).
- **Conformidade**: scores e narrativas de IA são leituras estatísticas descritivas de
  dados públicos — nunca recomendação de investimento (Res. CVM 20/2021).

Detalhes completos de cobertura e metodologia:
[Data Sheet](https://developers.lummios.com.br/dataset.html).

## Desenvolvimento

```bash
git clone https://github.com/brownbr84/lummios-python.git
cd lummios-python
pip install -e ".[dev]"
pytest
```

## Licença

MIT — veja [LICENSE](LICENSE).
