"""Exceções do cliente Lummios."""

from __future__ import annotations


class LummiosError(Exception):
    """Erro base do cliente Lummios."""


class LummiosAuthError(LummiosError):
    """Chave de API ausente, inválida ou desativada (HTTP 401/403)."""


class LummiosQuotaError(LummiosError):
    """Cota diária do plano atingida (HTTP 429).

    Attributes:
        daily_quota: limite diário do plano, quando informado pela API.
    """

    def __init__(self, message: str, daily_quota: int | None = None):
        super().__init__(message)
        self.daily_quota = daily_quota


class LummiosAPIError(LummiosError):
    """Erro retornado pela API (4xx/5xx não coberto pelas exceções acima).

    Attributes:
        status_code: código HTTP retornado (0 se a falha foi de conexão).
        payload: corpo JSON da resposta de erro, quando disponível.
    """

    def __init__(self, message: str, status_code: int, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
