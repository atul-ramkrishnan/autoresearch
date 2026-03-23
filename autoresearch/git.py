"""Git helpers — branch, commit, revert, diff."""

from __future__ import annotations

import subprocess
from datetime import datetime


def run(*args: str, cwd: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return (result.stdout + result.stderr).strip()


def current_branch(cwd: str) -> str:
    return run("branch", "--show-current", cwd=cwd)


def setup_branch(name: str, cwd: str) -> str:
    """Create an autoresearch branch if not already on one. Returns branch name."""
    current = current_branch(cwd)
    if current.startswith("autoresearch/"):
        return current

    ts = datetime.now().strftime("%Y%m%d-%H%M")
    branch = f"autoresearch/{name}-{ts}"
    run("checkout", "-b", branch, cwd=cwd)
    return branch


def commit(message: str, cwd: str) -> str | None:
    """Stage everything and commit. Returns short hash or None."""
    run("add", "-A", cwd=cwd)
    result = run("commit", "-m", message, cwd=cwd)
    if "nothing to commit" in result:
        return None
    return run("rev-parse", "--short", "HEAD", cwd=cwd) or None


def revert(cwd: str) -> None:
    """Discard all uncommitted changes."""
    run("reset", "HEAD", ".", cwd=cwd)
    run("checkout", ".", cwd=cwd)
    run("clean", "-fd", cwd=cwd)


def diff(cwd: str) -> str:
    """Return combined staged + unstaged diff."""
    staged = run("diff", "--cached", cwd=cwd)
    unstaged = run("diff", cwd=cwd)
    return (staged + "\n" + unstaged).strip()


def has_changes(cwd: str) -> bool:
    """Check if there are any uncommitted changes."""
    status = run("status", "--porcelain", cwd=cwd)
    return bool(status.strip())
