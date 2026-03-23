"""Script-based evaluation runners. No LLM dependency."""

from __future__ import annotations

import re
import subprocess
from typing import Any


def run_evals(
    eval_configs: list[dict],
    workspace: str,
) -> dict[str, Any]:
    """Run every configured evaluator and return {name: result}."""
    results: dict[str, Any] = {}
    for cfg in eval_configs:
        if "run" not in cfg:
            continue
        results[cfg["name"]] = _run(cfg, workspace)
    return results


def _run(cfg: dict, workspace: str) -> Any:
    """Run an eval command and interpret its output."""
    timeout = cfg.get("timeout", 120)
    try:
        result = subprocess.run(
            cfg["run"],
            shell=True,
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timeout"

    # No direction → pass/fail based on exit code
    if "direction" not in cfg:
        return "pass" if result.returncode == 0 else "fail"

    # Has direction → extract a number from the output
    return _extract_metric(cfg["name"], result.stdout, result.stderr)


def _extract_metric(name: str, stdout: str, stderr: str) -> Any:
    """Pull a number from command output using simple heuristics."""
    combined = stdout + "\n" + stderr

    # 1. Look for "name: <number>" or "name=<number>"
    pattern = re.compile(
        rf"{re.escape(name)}\s*[:=]\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE
    )
    match = pattern.search(combined)
    if match:
        return float(match.group(1))

    # 2. Last non-empty line is a bare number
    for line in reversed(combined.strip().splitlines()):
        line = line.strip()
        if line:
            try:
                return float(line)
            except ValueError:
                break

    # 3. Single standalone number in the output
    numbers = re.findall(r"(?<!\w)-?\d+(?:\.\d+)?(?!\w)", combined)
    if len(numbers) == 1:
        return float(numbers[0])

    return f"could not extract metric '{name}' from output"
