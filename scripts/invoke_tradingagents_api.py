#!/usr/bin/env python3
"""Invoke TradingAgentsCN API with automatic auth handling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tradingagents_client import TradingAgentsError, api_request, print_json


def main() -> int:
    parser = argparse.ArgumentParser(description="调用 TradingAgentsCN API。")
    parser.add_argument("--method", default="GET", help="HTTP 方法，默认 GET。")
    parser.add_argument("--path", required=True, help="接口路径，例如 /analysis/single")
    parser.add_argument("--body", help="JSON 字符串形式的请求体。")
    parser.add_argument("--body-file", help="请求体 JSON 文件路径。")
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="查询参数，格式 key=value，可重复传入。",
    )
    parser.add_argument("--no-auth", action="store_true", help="调用无需认证的接口。")
    args = parser.parse_args()

    if args.body and args.body_file:
        print_json({"ok": False, "error": "--body 和 --body-file 只能二选一。"})
        return 1

    body = None
    if args.body:
        body = json.loads(args.body)
    elif args.body_file:
        body = json.loads(Path(args.body_file).read_text(encoding="utf-8"))

    query = {}
    for item in args.query:
        if "=" not in item:
            print_json({"ok": False, "error": f"无效的 --query 参数: {item}"})
            return 1
        key, value = item.split("=", 1)
        query[key] = value

    try:
        result = api_request(
            args.path,
            method=args.method.upper(),
            body=body,
            query=query or None,
            require_auth=not args.no_auth,
        )
        print_json(result)
        return 0 if result.get("ok") else 1
    except (TradingAgentsError, json.JSONDecodeError) as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
