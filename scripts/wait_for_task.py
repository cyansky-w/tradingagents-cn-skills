#!/usr/bin/env python3
"""Wait for an async TradingAgentsCN task with conservative polling."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tradingagents_client import TradingAgentsError, api_request, print_json


DEPTH_DEFAULTS = {
    "快速": {"first_wait": 30, "interval": 30, "timeout": 360},
    "基础": {"first_wait": 30, "interval": 30, "timeout": 360},
    "标准": {"first_wait": 30, "interval": 45, "timeout": 720},
    "深度": {"first_wait": 45, "interval": 60, "timeout": 1080},
    "全面": {"first_wait": 45, "interval": 60, "timeout": 1800},
}


def _normalize_depth(depth: str) -> str:
    return depth if depth in DEPTH_DEFAULTS else "标准"


def _sleep(seconds: int, quiet: bool) -> None:
    if not quiet:
        print_json({"ok": True, "state": "waiting", "sleep_seconds": seconds})
    time.sleep(seconds)


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
    parser = argparse.ArgumentParser(description="等待 TradingAgentsCN 异步任务完成。")
    parser.add_argument("--task-id", required=True, help="任务 ID。")
    parser.add_argument("--depth", default="标准", help="分析深度，用于选择默认轮询节奏。")
    parser.add_argument("--first-wait", type=int, help="首次轮询前等待秒数。")
    parser.add_argument("--interval", type=int, help="后续轮询间隔秒数。")
    parser.add_argument("--timeout", type=int, help="最长等待秒数。")
    parser.add_argument("--status-path", help="自定义状态接口路径，默认 /analysis/tasks/{task_id}/status")
    parser.add_argument("--result-path", help="自定义结果接口路径，默认 /analysis/tasks/{task_id}/result")
    parser.add_argument("--skip-result", action="store_true", help="任务完成后不自动拉取结果。")
    parser.add_argument("--quiet", action="store_true", help="等待期间不输出 waiting 状态。")
    args = parser.parse_args()

    depth = _normalize_depth(args.depth)
    defaults = DEPTH_DEFAULTS[depth]
    first_wait = args.first_wait if args.first_wait is not None else defaults["first_wait"]
    interval = args.interval if args.interval is not None else defaults["interval"]
    timeout = args.timeout if args.timeout is not None else defaults["timeout"]

    if first_wait < 30:
        first_wait = 30
    if interval < 30:
        interval = 30

    status_path = args.status_path or f"/analysis/tasks/{args.task_id}/status"
    result_path = args.result_path or f"/analysis/tasks/{args.task_id}/result"

    start = time.time()

    try:
        _sleep(first_wait, args.quiet)
        while True:
            status_resp = api_request(status_path, method="GET")
            status_value = _extract_status(status_resp)
            elapsed = int(time.time() - start)

            output = {
                "ok": status_resp.get("ok", False),
                "task_id": args.task_id,
                "elapsed_seconds": elapsed,
                "status_response": status_resp,
            }

            if status_value in {"completed"}:
                if args.skip_result:
                    print_json(output)
                    return 0
                result_resp = api_request(result_path, method="GET")
                output["result_response"] = result_resp
                print_json(output)
                return 0 if result_resp.get("ok") else 1

            if status_value in {"failed", "error", "cancelled"}:
                print_json(output)
                return 1

            if elapsed >= timeout:
                output["timed_out"] = True
                output["message"] = "任务仍在后台运行，请稍后继续用 task_id 查询。"
                print_json(output)
                return 2

            print_json(output)
            _sleep(interval, args.quiet)

    except TradingAgentsError as exc:
        print_json({"ok": False, "task_id": args.task_id, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
