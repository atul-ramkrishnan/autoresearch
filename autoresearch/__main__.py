"""CLI entry point: autoresearch init|eval|status"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from . import config as cfg
from . import git
from .evaluators import run_evals
from .judge import decide, format_comparison
from .state import StateManager

DEFAULT_FILE = "AUTORESEARCH.md"


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="autoresearch",
        description="Lightweight harness for AI-driven code experiments",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Set up branch and run baseline")
    p_init.add_argument("file", nargs="?", default=DEFAULT_FILE)

    p_eval = sub.add_parser("eval", help="Run evals, compare, keep or discard")
    p_eval.add_argument("file", nargs="?", default=DEFAULT_FILE)
    p_eval.add_argument("-m", "--message", default=None, help="Experiment hypothesis")

    p_status = sub.add_parser("status", help="Show experiment history and best scores")
    p_status.add_argument("file", nargs="?", default=DEFAULT_FILE)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.file):
        print(f"Not found: {args.file}")
        print(f"Create an {DEFAULT_FILE} with YAML frontmatter. See the README for the format.")
        sys.exit(1)

    config = cfg.load(args.file)

    if args.command == "init":
        cmd_init(config)
    elif args.command == "eval":
        cmd_eval(config, args.message)
    elif args.command == "status":
        cmd_status(config)


# ======================================================================
# Commands
# ======================================================================

def cmd_init(config: dict) -> None:
    workspace = config["_workspace"]
    state = _state(config)
    evals = config.get("evals", [])

    branch = git.setup_branch(config["name"], cwd=workspace)
    print(f"Branch: {branch}")

    if state.count == 0:
        print("\nRunning baseline evals...")
        results = run_evals(evals, workspace)
        _print_results(results)

        commit_hash = git.commit("autoresearch: baseline", cwd=workspace)
        state.add_experiment({
            "hypothesis": "Baseline — no changes",
            "git_commit": commit_hash,
            "eval_results": results,
            "decision": "keep",
            "reasoning": "Baseline measurement",
        })
        print(f"Baseline recorded (commit {commit_hash}).\n")
    else:
        print(f"Resuming — {state.count} experiments already logged.\n")

    print("Ready. Start your coding agent in this directory.")


def cmd_eval(config: dict, hypothesis: str | None) -> None:
    workspace = config["_workspace"]
    state = _state(config)
    evals = config.get("evals", [])
    threshold = config.get("keep_threshold", "any_improves_none_regress")

    if not git.has_changes(cwd=workspace):
        print("No changes detected. Make some code changes first.")
        return

    print("Running evals...")
    results = run_evals(evals, workspace)

    best = state.get_best_scores(evals)
    comparison = format_comparison(results, best, evals)
    print(f"\nResults:\n{comparison}")

    decision, reasoning = decide(results, best, evals, threshold)

    exp_num = state.count
    commit_hash = None
    if decision == "keep":
        msg = hypothesis or f"experiment #{exp_num}"
        commit_hash = git.commit(f"experiment #{exp_num}: {msg}", cwd=workspace)
        print(f"\n✓ KEEP — {reasoning}")
        print(f"  Committed: {commit_hash}")
    else:
        git.revert(cwd=workspace)
        print(f"\n✗ DISCARD — {reasoning}")
        print("  Changes reverted.")

    state.add_experiment({
        "hypothesis": hypothesis or "(no description)",
        "git_commit": commit_hash,
        "eval_results": results,
        "decision": decision,
        "reasoning": reasoning,
    })

    # Budget warnings
    budget = config.get("budget", {})
    max_exp = budget.get("max_experiments")
    if max_exp and state.count >= max_exp:
        print(f"\n⚠ Budget reached: {state.count}/{max_exp} experiments.")

    max_fail = budget.get("max_consecutive_failures", 5)
    consecutive = _count_consecutive_failures(state)
    if consecutive >= max_fail:
        print(f"\n⚠ {consecutive} consecutive failures — consider a different approach.")

    print(f"\nExperiment #{exp_num} complete. Run `autoresearch status` to see history.")


def cmd_status(config: dict) -> None:
    state = _state(config)
    evals = config.get("evals", [])
    best = state.get_best_scores(evals)

    print(f"Experiments: {state.count}")

    if best:
        print("\nBest scores:")
        for name, val in best.items():
            print(f"  {name}: {val}")

    if state.experiments:
        kept = sum(1 for e in state.experiments if e.get("decision") == "keep")
        print(f"\nKept: {kept}  Discarded: {state.count - kept}")

        print("\nHistory (recent first):")
        for exp in reversed(state.experiments[-20:]):
            tag = "✓" if exp.get("decision") == "keep" else "✗"
            hyp = exp.get("hypothesis", "?")
            evals_str = ", ".join(
                f"{k}={v}" for k, v in exp.get("eval_results", {}).items()
            )
            print(f"  {tag} #{exp.get('id', '?')} {hyp}")
            if evals_str:
                print(f"      {evals_str}")
            reason = exp.get("reasoning", "")
            if reason:
                print(f"      → {reason}")
    else:
        print("\nNo experiments yet. Run `autoresearch init` first.")


# ======================================================================
# Helpers
# ======================================================================

def _state(config: dict) -> StateManager:
    workspace = config["_workspace"]
    log_file = config.get("log_file", "experiments.jsonl")
    return StateManager(os.path.join(workspace, log_file))


def _print_results(results: dict) -> None:
    for name, val in results.items():
        print(f"  {name}: {val}")


def _count_consecutive_failures(state: StateManager) -> int:
    count = 0
    for exp in reversed(state.experiments):
        if exp.get("decision") == "keep":
            break
        count += 1
    return count


if __name__ == "__main__":
    main()
