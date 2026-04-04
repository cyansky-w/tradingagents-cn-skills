#!/usr/bin/env python3
"""Ensure TradingAgentsCN token is ready."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tradingagents_client import TradingAgentsError, ensure_session, load_config, print_json


def _mask_token(token: str) -> str:
    if len(token) <= 10:
        return "***"
    return f"{token[:6]}...{token[-4:]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="确保 TradingAgentsCN Token 可用。")
    parser.add_argument("--force-login", action="store_true", help="忽略缓存并强制重新登录。")
    parser.add_argument("--show-token", action="store_true", help="输出脱敏后的 token 信息。")
    args = parser.parse_args()

    try:
        config = load_config()
        session = ensure_session(config, force_login=args.force_login)
        payload = {
            "ok": True,
            "base_url": config.base_url,
            "source": session.get("source"),
            "cache_path": str(config.cache_path),
        }
        token = session.get("access_token")
        if args.show_token and token:
            payload["token_preview"] = _mask_token(token)
            payload["token_sha1"] = hashlib.sha1(token.encode("utf-8")).hexdigest()
        print_json(payload)
        return 0
    except TradingAgentsError as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
