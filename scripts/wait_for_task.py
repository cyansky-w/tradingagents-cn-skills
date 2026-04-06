#!/usr/bin/env python3
"""Legacy helper kept for one-shot status checks.

This script no longer blocks and should not be used for long polling.
Prefer passing `openclaw_notify` when creating the task.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tradingagents_client import TradingAgentsError, api_request, print_json

def _extract_status(payload: dict) -> str | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    nested = data.get("data")
    if isinstance(nested, dict):
        status = nested.get("status")
        if isinstance(status, str):
            return status
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="单次查询 TradingAgentsCN 异步任务状态。")
    parser.add_argument("--task-id", required=True, help="任务 ID。")
    parser.add_argument("--status-path", help="自定义状态接口路径，默认 /analysis/tasks/{task_id}/status")
    parser.add_argument("--result-path", help="自定义结果接口路径，默认 /analysis/tasks/{task_id}/result")
    parser.add_argument("--skip-result", action="store_true", help="任务完成后不自动拉取结果。")
    args = parser.parse_args()

    status_path = args.status_path or f"/analysis/tasks/{args.task_id}/status"
    result_path = args.result_path or f"/analysis/tasks/{args.task_id}/result"

    try:
        status_resp = api_request(status_path, method="GET")
        status_value = _extract_status(status_resp)
        output = {
            "ok": status_resp.get("ok", False),
            "task_id": args.task_id,
            "status_response": status_resp,
            "non_blocking": True,
            "message": "此脚本已改为单次状态查询。长任务请优先使用 openclaw_notify。",
        }
        if status_value in {"completed"} and not args.skip_result:
            output["result_response"] = api_request(result_path, method="GET")
        print_json(output)
        if status_value in {"completed"}:
            return 0
        if status_value in {"failed", "error", "cancelled"}:
            return 1
        return 2
    except TradingAgentsError as exc:
        print_json({"ok": False, "task_id": args.task_id, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
