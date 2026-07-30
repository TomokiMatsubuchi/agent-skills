#!/usr/bin/env python3
"""Run one delegated Codex turn through `codex app-server --stdio`.

The script is intentionally conservative: read-only sandbox and approvalPolicy=never
are the defaults, so a delegated investigation cannot modify files or block on
interactive approval prompts.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


CLIENT_INFO = {
    "name": "codex_delegate_skill",
    "title": "Codex Delegate Skill",
    "version": "0.1.0",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delegate a single prompt to a child Codex app-server process."
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to send to the child Codex.")
    parser.add_argument(
        "--prompt-file",
        help="Read the child prompt from a UTF-8 text file instead of argv.",
    )
    parser.add_argument("--codex-bin", default="codex", help="Codex executable path.")
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for child Codex.")
    parser.add_argument("--model", help="Model override for child Codex.")
    parser.add_argument(
        "--sandbox",
        default="read-only",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Child Codex sandbox policy.",
    )
    parser.add_argument(
        "--approval",
        default="never",
        choices=["never", "on-request", "untrusted", "on-failure"],
        help="Child Codex approval policy.",
    )
    parser.add_argument(
        "--developer-instructions",
        help="Optional child-only developer instructions for the thread.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1800.0,
        help="Maximum seconds to wait for the delegated turn.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of plain assistant text.",
    )
    parser.add_argument(
        "--raw-log",
        help="Write raw JSON-RPC messages and stderr lines to this JSONL file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the JSON-RPC messages that would be sent; do not spawn Codex.",
    )
    return parser.parse_args()


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    data = sys.stdin.read()
    if data.strip():
        return data
    raise SystemExit("prompt, --prompt-file, or stdin is required")


def reader_thread(stream: Any, out: queue.Queue[tuple[str, str]]) -> None:
    try:
        for line in iter(stream.readline, ""):
            out.put(("line", line.rstrip("\n")))
    finally:
        out.put(("eof", ""))


def stderr_thread(stream: Any, out: queue.Queue[tuple[str, str]]) -> None:
    try:
        for line in iter(stream.readline, ""):
            out.put(("stderr", line.rstrip("\n")))
    finally:
        out.put(("stderr_eof", ""))


def write_raw(raw: Any, direction: str, payload: Any) -> None:
    if not raw:
        return
    raw.write(json.dumps({"direction": direction, "payload": payload}, ensure_ascii=False) + "\n")
    raw.flush()


def make_messages(args: argparse.Namespace, prompt: str, thread_id: str | None = None) -> list[dict[str, Any]]:
    thread_params: dict[str, Any] = {
        "cwd": str(Path(args.cwd).expanduser().resolve()),
        "ephemeral": True,
        "sandbox": args.sandbox,
        "approvalPolicy": args.approval,
    }
    if args.model:
        thread_params["model"] = args.model
    if args.developer_instructions:
        thread_params["developerInstructions"] = args.developer_instructions

    messages: list[dict[str, Any]] = [
        {
            "method": "initialize",
            "id": 0,
            "params": {
                "clientInfo": CLIENT_INFO,
                "capabilities": {"experimentalApi": True},
            },
        },
        {"method": "initialized", "params": {}},
        {"method": "thread/start", "id": 1, "params": thread_params},
    ]
    if thread_id:
        messages.append(
            {
                "method": "turn/start",
                "id": 2,
                "params": {
                    "threadId": thread_id,
                    "cwd": str(Path(args.cwd).expanduser().resolve()),
                    "approvalPolicy": args.approval,
                    "input": [{"type": "text", "text": prompt}],
                },
            }
        )
    return messages


def main() -> int:
    args = parse_args()
    prompt = load_prompt(args)

    if args.dry_run:
        for message in make_messages(args, prompt, thread_id="THREAD_ID_FROM_THREAD_START"):
            print(json.dumps(message, ensure_ascii=False))
        return 0

    raw = open(args.raw_log, "w", encoding="utf-8") if args.raw_log else None
    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            [args.codex_bin, "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        raise SystemExit(f"Codex executable not found: {args.codex_bin!r}")

    assert proc.stdin and proc.stdout and proc.stderr
    events: queue.Queue[tuple[str, str]] = queue.Queue()
    threading.Thread(target=reader_thread, args=(proc.stdout, events), daemon=True).start()
    threading.Thread(target=stderr_thread, args=(proc.stderr, events), daemon=True).start()

    def send(message: dict[str, Any]) -> None:
        write_raw(raw, "client", message)
        proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        proc.stdin.flush()

    for message in make_messages(args, prompt):
        send(message)

    deadline = time.monotonic() + args.timeout
    thread_id: str | None = None
    turn_id: str | None = None
    final_turn: dict[str, Any] | None = None
    assistant_chunks: list[str] = []
    warnings: list[str] = []
    errors: list[Any] = []
    stderr_lines: list[str] = []

    try:
        while time.monotonic() < deadline:
            if proc.poll() is not None and events.empty():
                break
            try:
                kind, line = events.get(timeout=0.2)
            except queue.Empty:
                continue

            if kind == "stderr" and line:
                stderr_lines.append(line)
                write_raw(raw, "stderr", line)
                continue
            if kind != "line" or not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                warnings.append(f"non-JSON stdout line: {line}")
                write_raw(raw, "server_non_json", line)
                continue

            write_raw(raw, "server", message)

            # JSON-RPC request from server. This simple client cannot safely service
            # approvals, dynamic tools, or user-input requests, so reject them instead
            # of leaving the child turn hanging.
            if "id" in message and "method" in message and "params" in message:
                send(
                    {
                        "id": message["id"],
                        "error": {
                            "code": -32000,
                            "message": "codex-delegate does not service server-side requests; retry with a narrower read-only prompt.",
                        },
                    }
                )
                continue

            if message.get("id") == 1:
                if "error" in message:
                    errors.append(message["error"])
                    break
                thread_id = message.get("result", {}).get("thread", {}).get("id")
                if not thread_id:
                    errors.append({"message": "thread/start response did not contain thread.id"})
                    break
                send(make_messages(args, prompt, thread_id=thread_id)[-1])
                continue

            if message.get("id") == 2:
                if "error" in message:
                    errors.append(message["error"])
                    break
                turn_id = message.get("result", {}).get("turn", {}).get("id")
                continue

            method = message.get("method")
            params = message.get("params", {})
            if method == "item/agentMessage/delta":
                assistant_chunks.append(params.get("delta", ""))
            elif method == "warning":
                warnings.append(params.get("message", "warning"))
            elif method == "error":
                errors.append(params.get("error", params))
                if not params.get("willRetry", False):
                    break
            elif method == "turn/completed":
                final_turn = params.get("turn", {})
                turn_id = turn_id or final_turn.get("id")
                break

        else:
            errors.append({"message": f"timed out after {args.timeout} seconds"})

    finally:
        if proc and proc.poll() is None:
            try:
                proc.send_signal(signal.SIGINT)
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        if raw:
            raw.close()

    returncode = proc.poll() if proc else None
    if final_turn is None and not errors:
        errors.append(
            {
                "message": "codex app-server exited before turn/completed"
                if returncode is not None
                else "turn/completed was not received",
                "returncode": returncode,
            }
        )

    text = "".join(assistant_chunks).strip()
    status = final_turn.get("status") if final_turn else None
    result = {
        "ok": not errors and final_turn is not None and status not in {"failed", "cancelled"},
        "thread_id": thread_id,
        "turn_id": turn_id,
        "status": status,
        "text": text,
        "warnings": warnings,
        "errors": errors,
        "stderr": stderr_lines[-20:],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if text:
            print(text)
        if warnings:
            print("\n[Warnings]", file=sys.stderr)
            for warning in warnings:
                print(f"- {warning}", file=sys.stderr)
        if errors:
            print("\n[Errors]", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
