# autoresearch

A lightweight harness for AI-driven code experiments. Pair it with a coding agent (Claude Code, Codex, etc.) — the agent handles the intelligence, the harness handles evaluation, state, and git.

## How it works

```
  Coding Agent                          Harness
  ───────────                           ───────
  reads AUTORESEARCH.md (goals + rules)
  explores code, plans experiment
  makes ONE focused change
  runs `autoresearch eval -m "..."` ──→ runs eval commands
                                        compares to previous best
                                        keeps or discards (mechanical)
                                        git commit / revert
  reads output ←────────────────────── prints results
  repeats
```

The agent does the thinking. The harness does the bookkeeping.

## Quick start

```bash
# 1. Install (once)
uv tool install path/to/autoresearch

# 2. Go to your project
cd ~/code/my-project

# 3. Create AUTORESEARCH.md (copy and edit the example)
cp path/to/autoresearch/AUTORESEARCH.example.md AUTORESEARCH.md

# 4. Initialize — creates git branch and runs baseline
autoresearch init

# 5. Start your coding agent
#    It reads AUTORESEARCH.md and knows what to do.
```

## The file

`AUTORESEARCH.md` is one file that serves two purposes:

1. **YAML frontmatter** (between `---` markers) — the structured bits the harness needs: what commands to run, which direction is better, budget.
2. **Markdown body** — free-text instructions you write for the agent: goals, workflow, rules, whatever context helps.

```markdown
---
evals:
  - name: latency
    run: python bench.py
    direction: lower_is_better
  - name: tests
    run: pytest -q
budget:
  max_experiments: 20
---

# Goal

Make the API faster. All tests must pass.

# Workflow

1. Run `autoresearch status` to see history
2. Make one change
3. Run `autoresearch eval -m "what you tried"`
4. Repeat
```

### Eval types (inferred from the fields you provide)

- `run` + `direction` → numeric metric (the harness extracts the number automatically)
- `run` only → pass/fail (exit code 0 = pass)

## CLI

```
autoresearch init [file]            Create branch, run baseline
autoresearch eval [file]            Run evals, compare, keep/discard
autoresearch eval -m "hypothesis"   Same, with a description
autoresearch status [file]          Show history and best scores
```

File defaults to `AUTORESEARCH.md` in the current directory.

## What lives where

```
~/code/autoresearch/           ← the tool (install once)

~/code/my-project/             ← your project
    ├── src/
    ├── tests/
    ├── AUTORESEARCH.md        ← goals, evals, instructions (you write this)
    └── experiments.jsonl      ← experiment log (created by harness)
```

## Architecture

```
autoresearch/
├── __main__.py     # CLI: init, eval, status
├── config.py       # Parse YAML frontmatter from markdown
├── evaluators.py   # Run eval commands, extract metrics
├── judge.py        # Mechanical keep/discard comparison
├── state.py        # Experiment log (experiments.jsonl)
└── git.py          # Branch, commit, revert, diff
```

No LLM client, no agent loop, no API keys. The coding agent you already pay for does the work.
