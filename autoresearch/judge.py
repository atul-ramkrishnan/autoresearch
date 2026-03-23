"""Mechanical keep/discard logic — no LLM needed."""

from __future__ import annotations

from typing import Any


def decide(
    eval_results: dict[str, Any],
    best_scores: dict[str, Any],
    eval_configs: list[dict],
    threshold: str = "any_improves_none_regress",
) -> tuple[str, str]:
    """Compare eval results to previous best and return (decision, reasoning).

    Returns ("keep", "...") or ("discard", "...").
    """
    improved: list[str] = []
    regressed: list[str] = []
    unchanged: list[str] = []
    errors: list[str] = []

    for cfg in eval_configs:
        name = cfg["name"]
        current = eval_results.get(name)

        if current is None or current == "timeout":
            errors.append(name)
            continue

        previous = best_scores.get(name)

        # First ever measurement — nothing to compare
        if previous is None:
            unchanged.append(name)
            continue

        # Pass/fail
        if isinstance(current, str) and current in ("pass", "fail"):
            if current == "pass" and previous == "fail":
                improved.append(name)
            elif current == "fail" and previous == "pass":
                regressed.append(name)
            else:
                unchanged.append(name)
            continue

        # Numeric
        if isinstance(current, (int, float)) and isinstance(previous, (int, float)):
            direction = cfg.get("direction", "lower_is_better")
            if direction == "lower_is_better":
                delta = previous - current
            else:
                delta = current - previous

            if delta > 0:
                improved.append(name)
            elif delta < 0:
                regressed.append(name)
            else:
                unchanged.append(name)
            continue

        unchanged.append(name)

    # Decision
    if errors:
        return "discard", f"eval errors: {', '.join(errors)}"

    if threshold == "any_improves_none_regress":
        if regressed:
            return "discard", f"regressed: {', '.join(regressed)}"
        if improved:
            return "keep", f"improved: {', '.join(improved)}"
        return "discard", "no improvement"

    if threshold == "all_improve":
        if regressed:
            return "discard", f"regressed: {', '.join(regressed)}"
        non_improved = [n for n in unchanged if n not in errors]
        if non_improved:
            return "discard", f"did not improve: {', '.join(non_improved)}"
        if improved:
            return "keep", f"all improved: {', '.join(improved)}"
        return "discard", "no improvement"

    if threshold == "any_improves":
        if improved:
            return "keep", f"improved: {', '.join(improved)}"
        return "discard", "no improvement"

    # Unknown threshold — default to strict
    if regressed:
        return "discard", f"regressed: {', '.join(regressed)}"
    if improved:
        return "keep", f"improved: {', '.join(improved)}"
    return "discard", "no improvement"


def format_comparison(
    eval_results: dict[str, Any],
    best_scores: dict[str, Any],
    eval_configs: list[dict],
) -> str:
    """Human-readable comparison table for the agent to read."""
    lines: list[str] = []
    for cfg in eval_configs:
        name = cfg["name"]
        current = eval_results.get(name, "N/A")
        previous = best_scores.get(name)
        direction = cfg.get("direction")

        if previous is None:
            lines.append(f"  {name}: {current} (first measurement)")
            continue

        arrow = ""
        if isinstance(current, (int, float)) and isinstance(previous, (int, float)):
            if direction == "lower_is_better":
                arrow = " ↓ better" if current < previous else " ↑ worse" if current > previous else " = same"
            elif direction == "higher_is_better":
                arrow = " ↑ better" if current > previous else " ↓ worse" if current < previous else " = same"
        elif isinstance(current, str) and current in ("pass", "fail"):
            if current == "pass" and previous == "fail":
                arrow = " ✓ fixed"
            elif current == "fail" and previous == "pass":
                arrow = " ✗ broke"
            else:
                arrow = " = same"

        lines.append(f"  {name}: {current} (was {previous}{arrow})")

    return "\n".join(lines)
