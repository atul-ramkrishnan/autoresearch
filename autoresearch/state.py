"""Experiment state: structured JSONL log that acts as long-term memory."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


class StateManager:
    """Manages the experiments.jsonl log and provides history for prompts."""

    def __init__(self, log_path: str):
        self.log_path = log_path
        self.experiments: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.log_path):
            return
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.experiments.append(json.loads(line))

    def add_experiment(self, experiment: dict[str, Any]) -> None:
        experiment.setdefault(
            "timestamp", datetime.now(timezone.utc).isoformat()
        )
        experiment.setdefault("id", len(self.experiments))
        self.experiments.append(experiment)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(experiment) + "\n")

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------

    def get_history_summary(self, max_entries: int = 30) -> str:
        if not self.experiments:
            return "No experiments run yet."

        recent = self.experiments[-max_entries:]
        lines: list[str] = []
        for exp in recent:
            status = exp.get("decision", "?")
            hyp = exp.get("hypothesis", "N/A")
            evals = exp.get("eval_results", {})
            eval_str = ", ".join(f"{k}={v}" for k, v in evals.items())
            lines.append(f"  #{exp['id']} [{status}] {hyp}")
            if eval_str:
                lines.append(f"      evals: {eval_str}")
            reason = exp.get("reasoning", "")
            if reason:
                lines.append(f"      reason: {reason}")
        return "\n".join(lines)

    def get_best_scores(self, eval_configs: list[dict]) -> dict[str, float]:
        best: dict[str, float] = {}
        for exp in self.experiments:
            if exp.get("decision") != "keep":
                continue
            for key, val in exp.get("eval_results", {}).items():
                if not isinstance(val, (int, float)):
                    continue
                cfg = next((e for e in eval_configs if e["name"] == key), None)
                if cfg is None:
                    continue
                direction = cfg.get("direction", "lower_is_better")
                if key not in best:
                    best[key] = val
                elif direction == "lower_is_better" and val < best[key]:
                    best[key] = val
                elif direction == "higher_is_better" and val > best[key]:
                    best[key] = val
        return best

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        return len(self.experiments)

    @property
    def last(self) -> dict[str, Any] | None:
        return self.experiments[-1] if self.experiments else None
