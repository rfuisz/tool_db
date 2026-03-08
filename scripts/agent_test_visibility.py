#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURSORIGNORE = ROOT / ".cursorignore"
HIDE_RULES = ["tests/"]


def _read_lines() -> list[str]:
    if not CURSORIGNORE.exists():
        return []
    return CURSORIGNORE.read_text(encoding="utf-8").splitlines()


def _write_lines(lines: list[str]) -> None:
    content = "\n".join(lines).rstrip()
    if content:
        content += "\n"
    CURSORIGNORE.write_text(content, encoding="utf-8")


def hide() -> None:
    lines = _read_lines()
    existing = set(lines)
    changed = False
    for rule in HIDE_RULES:
        if rule not in existing:
            lines.append(rule)
            changed = True
    if changed:
        _write_lines(lines)
    print("agent test visibility: hidden")


def show() -> None:
    lines = _read_lines()
    filtered = [line for line in lines if line not in HIDE_RULES]
    if filtered != lines:
        _write_lines(filtered)
    print("agent test visibility: visible")


def status() -> None:
    lines = set(_read_lines())
    hidden = all(rule in lines for rule in HIDE_RULES)
    print("hidden" if hidden else "visible")


def main() -> int:
    if len(sys.argv) == 1:
        status()
        return 0

    command = sys.argv[1]
    if command == "hide":
        hide()
        return 0
    if command == "show":
        show()
        return 0
    if command == "status":
        status()
        return 0

    print("usage: python scripts/agent_test_visibility.py [hide|show|status]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
