"""Cliente HTTP fino para a API Lummios Developer.

Documentação completa: https://developers.lummios.com.br/docs.html
Gere sua chave gratuita em: https://developers.lummios.com.br
"""

from __future__ import annotations

import os
from typing import Any

import requests

from .exceptions import LummiosAPIError, LummiosAuthError, LummiosQuotaError

DEFAULT_BASE_URL = "https://developers.lummios.com.br"


class LummiosClient:
    """Cliente para a API Lummios Developer — fundamentos B3/CVM, cotações,
    indicadores, dividendos, dados bancários e análises de IA.

    As leituras de score/IA são estatísticas descritivas sobre dados públicos;
    não constituem recomendação de investimento (Res. CVM 20/2021).

    Exemplo:
        >>> from lummios import LummiosClient
        >>> client = LummiosClient(api_key="sua_chave")
        >>> client.fundamentals("PETR4")["p_l"]

    A chave também pode vir da variável de ambiente ``LUMMIOS_API_KEY``:
        >>> client = LummiosClient()  # lê LUMMIOS_API_KEY
    """

    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL, timeout: int = 30):
        self.api_key = api_key or os.getenv("LUMMIOS_API_KEY")
        if not self.api_key:
            raise LummiosAuthError(
                "Nenhuma chave de API informada. Passe api_key=... ou defina a "
                "variável de ambiente LUMMIOS_API_KEY. Gere uma chave gratuita em "
                "https://developers.lummios.com.br"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"X-Api-Key": self.api_key})

    # ── núcleo ────────────────────────────────────────────────────────────
    def get(self, path: str, **params: Any) -> Any:
        """Chamada genérica a qualquer endpoint da API — cobre toda a
        referência (https://developers.lummios.com.br/docs.html), inclusive
        rotas sem método dedicado abaixo.

        ``path`` pode vir com ou sem a barra inicial:
            client.get("/v1/tickers/PETR4") == client.get("v1/tickers/PETR4")
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        clean_params = {k: v for k, v in params.items() if v is not None}
        try:
            resp = self._session.get(url, params=clean_params, timeout=self.timeout)
        except requests.RequestException as e:
            raise LummiosAPIError(f"Falha de conexão: {e}", status_code=0) from e

        if resp.status_code in (401, 403):
            raise LummiosAuthError(f"Chave de API inválida, ausente ou desativada (HTTP {resp.status_code}).")
        if resp.status_code == 429:
            body = _safe_json(resp) or {}
            raise LummiosQuotaError(
                body.get("detail", "Cota diária do plano atingida."),
                daily_quota=body.get("daily_quota"),
            )
        if resp.status_code >= 400:
            body = _safe_json(resp) or {}
            msg = body.get("detail", resp.text[:200])
            raise LummiosAPIError(f"Erro da API (HTTP {resp.status_code}): {msg}", status_code=resp.status_code, payload=body)
        return _safe_json(resp)

    # ── tickers ───────────────────────────────────────────────────────────
    def ticker(self, ticker: str) -> dict:
        """Cotação atual, variação do dia e estatísticas de 52 semanas."""
        return self.get(f"/v1/tickers/{ticker}")

    def fundamentals(self, ticker: str) -> dict:
        """Indicadores fundamentalistas: P/L, P/VP, ROE, ROIC, margens, CAGR..."""
        return self.get(f"/v1/tickers/{ticker}/fundamentals")

    def historico(self, ticker: str, **params: Any) -> dict:
        """Série histórica de cotações (OHLCV)."""
        return self.get(f"/v1/tickers/{ticker}/historico", **params)

    def historico_ajustado(self, ticker: str, **params: Any) -> dict:
        """Série ajustada por splits e proventos (total return)."""
        return self.get(f"/v1/tickers/{ticker}/historico-ajustado", **params)

    def multiplos_historico(self, ticker: str, **params: Any) -> dict:
        """Série histórica de múltiplos (P/L, P/VP, EV/EBITDA...)."""
        return self.get(f"/v1/tickers/{ticker}/multiplos-historico", **params)

    def dividends(self, ticker: str) -> dict:
        """Histórico de dividendos e JCP (conciliado IPE/CVM)."""
        return self.get(f"/v1/tickers/{ticker}/dividends")

    def corporate_actions(self, ticker: str) -> dict:
        """Eventos corporativos: splits, grupamentos, bonificações."""
        return self.get(f"/v1/tickers/{ticker}/corporate-actions")

    def dfp_completo(self, ticker: str, **params: Any) -> dict:
        """DFP/ITR linha a linha (DRE, BPA, BPP, DFC, DVA)."""
        return self.get(f"/v1/tickers/{ticker}/dfp-completo", **params)

    def checks(self, ticker: str) -> dict:
        """Checks factuais por dimensão (rentabilidade, solidez, crescimento,
        dividendos, múltiplos) — cada um com o dado que o comprova."""
        return self.get(f"/v1/tickers/{ticker}/checks")

    def bank_indicators(self, ticker: str) -> dict:
        """Indicadores prudenciais (Basileia, CET1, Tier1, PDD) — só bancos."""
        return self.get(f"/v1/tickers/{ticker}/bank-indicators")

    def peers(self, ticker: str) -> dict:
        """Comparativo com pares do mesmo segmento/setor."""
        return self.get(f"/v1/tickers/{ticker}/peers")

    def ai_explicabilidade(self, ticker: str) -> dict:
        """Score de ML com explicabilidade SHAP e narrativa. Leitura estatística
        descritiva; não constitui recomendação de investimento (Res. CVM 20/2021)."""
        return self.get(f"/v1/tickers/{ticker}/ai-explicabilidade")

    def valor_intrinseco(self, ticker: str) -> dict:
        """Estimativas de valor intrínseco (Graham, EPV, DCF)."""
        return self.get(f"/v1/tickers/{ticker}/valor-intrinseco")

    def info(self, ticker: str) -> dict:
        """Cadastro: CNPJ, setor B3/CVM, tipo de ação, free float."""
        return self.get(f"/v1/tickers/{ticker}/info")

    # ── mercado ───────────────────────────────────────────────────────────
    def mercado_resumo(self) -> dict:
        """Resumo do pregão: ativos, altas/baixas, volume total."""
        return self.get("/v1/mercado/resumo")

    def maiores_altas(self) -> dict:
        return self.get("/v1/mercado/maiores-altas")

    def maiores_baixas(self) -> dict:
        return self.get("/v1/mercado/maiores-baixas")

    def maior_volume(self) -> dict:
        return self.get("/v1/mercado/maior-volume")

    # ── screener ──────────────────────────────────────────────────────────
    def screener(self, **params: Any) -> dict:
        """Screener fundamentalista com filtros (ex.: roe_min, pl_max, dy_min,
        setor, margem_min, div_liq_ebitda_max)."""
        return self.get("/v1/screener", **params)

    # ── classificação / comparação ───────────────────────────────────────
    def classificacao(self) -> dict:
        """Árvore setor→subsetor→segmento da B3."""
        return self.get("/v1/classificacao")

    def comparar(self, tickers: list[str], **params: Any) -> dict:
        """Compara séries de preços normalizadas de múltiplos tickers."""
        return self.get("/v1/comparar", tickers=",".join(tickers), **params)

    # ── macro ─────────────────────────────────────────────────────────────
    def macro(self) -> dict:
        """Séries do Banco Central: SELIC, CDI, IPCA, PIB, USD/BRL."""
        return self.get("/v1/macro")

    # ── metadados ─────────────────────────────────────────────────────────
    def dataset_info(self) -> dict:
        """Resumo do dataset: total de registros, tickers, cobertura temporal."""
        return self.get("/v1/info")


def _safe_json(resp: requests.Response):
    try:
        return resp.json()
    except ValueError:
        return None
