"""Testes do cliente — sem chamadas de rede reais (requests.Session.get mockado)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from lummios import LummiosAuthError, LummiosClient, LummiosQuotaError, LummiosAPIError


def _fake_response(status_code=200, json_body=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.json.side_effect = None if json_body is not None else ValueError("no json")
    resp.json.return_value = json_body
    return resp


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("LUMMIOS_API_KEY", raising=False)
    with pytest.raises(LummiosAuthError):
        LummiosClient()


def test_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("LUMMIOS_API_KEY", "from-env")
    client = LummiosClient()
    assert client.api_key == "from-env"


def test_explicit_api_key_wins_over_env(monkeypatch):
    monkeypatch.setenv("LUMMIOS_API_KEY", "from-env")
    client = LummiosClient(api_key="explicit")
    assert client.api_key == "explicit"


def test_successful_get_returns_json():
    client = LummiosClient(api_key="k")
    with patch.object(client._session, "get", return_value=_fake_response(200, {"ticker": "PETR4"})):
        assert client.get("/v1/tickers/PETR4") == {"ticker": "PETR4"}


def test_fundamentals_hits_expected_path():
    client = LummiosClient(api_key="k")
    with patch.object(client._session, "get", return_value=_fake_response(200, {"p_l": 5.2})) as mocked:
        result = client.fundamentals("PETR4")
        assert result == {"p_l": 5.2}
        called_url = mocked.call_args[0][0]
        assert called_url.endswith("/v1/tickers/PETR4/fundamentals")


def test_401_raises_auth_error():
    client = LummiosClient(api_key="k")
    with patch.object(client._session, "get", return_value=_fake_response(401, {"detail": "no"})):
        with pytest.raises(LummiosAuthError):
            client.get("/v1/tickers/PETR4")


def test_429_raises_quota_error_with_daily_quota():
    client = LummiosClient(api_key="k")
    body = {"detail": "Cota diária do seu plano atingida (1.000 requisições/dia).", "daily_quota": 1000}
    with patch.object(client._session, "get", return_value=_fake_response(429, body)):
        with pytest.raises(LummiosQuotaError) as exc_info:
            client.get("/v1/tickers/PETR4")
        assert exc_info.value.daily_quota == 1000


def test_500_raises_api_error_with_status_code():
    client = LummiosClient(api_key="k")
    with patch.object(client._session, "get", return_value=_fake_response(500, {"detail": "boom"})):
        with pytest.raises(LummiosAPIError) as exc_info:
            client.get("/v1/tickers/PETR4")
        assert exc_info.value.status_code == 500


def test_get_strips_leading_slash_consistently():
    client = LummiosClient(api_key="k", base_url="https://example.com")
    with patch.object(client._session, "get", return_value=_fake_response(200, {})) as mocked:
        client.get("v1/tickers/PETR4")
        assert mocked.call_args[0][0] == "https://example.com/v1/tickers/PETR4"


def test_none_params_are_dropped():
    client = LummiosClient(api_key="k")
    with patch.object(client._session, "get", return_value=_fake_response(200, {})) as mocked:
        client.get("/v1/screener", roe_min=15, setor=None)
        assert mocked.call_args.kwargs["params"] == {"roe_min": 15}
