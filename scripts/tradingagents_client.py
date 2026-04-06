#!/usr/bin/env python3
"""TradingAgentsCN skill helper.

跨平台处理：
- 读取环境变量
- 复用缓存 Token
- 用 /auth/me 校验 Token
- 没有有效 Token 时自动登录
- 发起认证后的 API 请求
- 401 时自动重登一次
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib import error, parse, request

class TradingAgentsError(RuntimeError):
    """Skill runtime error."""


@dataclass
class Config:
    base_url: str
    username: Optional[str]
    password: Optional[str]
    bearer_token: Optional[str]
    cache_path: Path
    timeout: int = 30


def _default_cache_path() -> Path:
    custom = os.getenv("TRADINGAGENTS_TOKEN_CACHE")
    if custom:
        return Path(custom).expanduser()

    if os.name == "nt":
        localappdata = os.getenv("LOCALAPPDATA")
        root = Path(localappdata) if localappdata else Path.home() / "AppData" / "Local"
        return root / "OpenClaw" / "tradingagents-cn" / "session.json"

    xdg_cache = os.getenv("XDG_CACHE_HOME")
    root = Path(xdg_cache) if xdg_cache else Path.home() / ".cache"
    return root / "openclaw" / "tradingagents-cn" / "session.json"


def load_config() -> Config:
    timeout_raw = os.getenv("TRADINGAGENTS_TIMEOUT")
    base_url = (os.getenv("TRADINGAGENTS_BASE_URL") or "").strip()
    if not base_url:
        raise TradingAgentsError(
            "缺少 TRADINGAGENTS_BASE_URL，请先通过环境变量提供 TradingAgentsCN 实例地址。"
        )

    return Config(
        base_url=base_url.rstrip("/"),
        username=(os.getenv("TRADINGAGENTS_USERNAME") or "").strip() or None,
        password=(os.getenv("TRADINGAGENTS_PASSWORD") or "").strip() or None,
        bearer_token=(os.getenv("TRADINGAGENTS_BEARER_TOKEN") or "").strip() or None,
        cache_path=_default_cache_path(),
        timeout=int(timeout_raw) if timeout_raw else 30,
    )


def _read_cache(config: Config) -> Optional[Dict[str, Any]]:
    if not config.cache_path.exists():
        return None
    try:
        return json.loads(config.cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(config: Config, payload: Dict[str, Any]) -> None:
    config.cache_path.parent.mkdir(parents=True, exist_ok=True)
    config.cache_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_cache(config: Config) -> None:
    try:
        if config.cache_path.exists():
            config.cache_path.unlink()
    except OSError:
        pass


def print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _json_request(
    url: str,
    *,
    method: str,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Tuple[int, Dict[str, str], Any]:
    req_headers = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")

    req = request.Request(url=url, data=data, headers=req_headers, method=method.upper())
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            resp_headers = dict(resp.info())
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        status = exc.code
        resp_headers = dict(exc.headers)
        raw = exc.read().decode("utf-8", errors="replace")
    except error.URLError as exc:
        raise TradingAgentsError(f"网络请求失败: {exc}") from exc

    try:
        data_obj = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        data_obj = raw
    return status, resp_headers, data_obj


def validate_token(config: Config, token: str) -> bool:
    status, _, payload = _json_request(
        f"{config.base_url}/auth/me",
        method="GET",
        headers={"Authorization": f"Bearer {token}"},
        timeout=config.timeout,
    )
    return status == 200 and isinstance(payload, dict)


def _login(config: Config) -> Dict[str, Any]:
    if not config.username or not config.password:
        raise TradingAgentsError(
            "缺少用户名或密码，请设置 TRADINGAGENTS_USERNAME 和 TRADINGAGENTS_PASSWORD。"
        )

    status, _, payload = _json_request(
        f"{config.base_url}/auth/login",
        method="POST",
        body={"username": config.username, "password": config.password},
        timeout=config.timeout,
    )
    if status != 200:
        raise TradingAgentsError(f"登录失败，HTTP {status}: {json.dumps(payload, ensure_ascii=False)}")
    if not isinstance(payload, dict):
        raise TradingAgentsError("登录失败，返回不是 JSON 对象。")

    data = payload.get("data") or {}
    token = data.get("access_token")
    if not token:
        raise TradingAgentsError("登录失败，返回中缺少 data.access_token。")

    session = {
        "base_url": config.base_url,
        "access_token": token,
        "refresh_token": data.get("refresh_token"),
        "expires_in": data.get("expires_in"),
        "fetched_at": int(time.time()),
        "user": data.get("user"),
    }
    _write_cache(config, session)
    return session


def ensure_session(config: Optional[Config] = None, *, force_login: bool = False) -> Dict[str, Any]:
    config = config or load_config()

    if not force_login and config.bearer_token and validate_token(config, config.bearer_token):
        session = {
            "base_url": config.base_url,
            "access_token": config.bearer_token,
            "source": "env",
        }
        _write_cache(config, session)
        return session

    cached = None if force_login else _read_cache(config)
    if cached and cached.get("base_url") == config.base_url:
        token = cached.get("access_token")
        if token and validate_token(config, token):
            cached["source"] = "cache"
            return cached

    session = _login(config)
    session["source"] = "login"
    return session


def api_request(
    path: str,
    *,
    method: str = "GET",
    body: Optional[Dict[str, Any]] = None,
    query: Optional[Dict[str, Any]] = None,
    require_auth: bool = True,
    config: Optional[Config] = None,
    retry_on_401: bool = True,
) -> Dict[str, Any]:
    config = config or load_config()
    if not path.startswith("/"):
        path = "/" + path

    url = f"{config.base_url}{path}"
    if query:
        query_string = parse.urlencode({k: v for k, v in query.items() if v is not None}, doseq=True)
        if query_string:
            url = f"{url}?{query_string}"

    headers: Dict[str, str] = {}
    if require_auth:
        session = ensure_session(config)
        headers["Authorization"] = f"Bearer {session['access_token']}"

    status, resp_headers, payload = _json_request(
        url,
        method=method,
        headers=headers,
        body=body,
        timeout=config.timeout,
    )

    if status == 401 and require_auth and retry_on_401:
        clear_cache(config)
        session = ensure_session(config, force_login=True)
        headers["Authorization"] = f"Bearer {session['access_token']}"
        status, resp_headers, payload = _json_request(
            url,
            method=method,
            headers=headers,
            body=body,
            timeout=config.timeout,
        )

    return {
        "ok": 200 <= status < 300,
        "status": status,
        "url": url,
        "headers": resp_headers,
        "data": payload,
    }
