---
evals:
  - name: response_time
    run: python bench.py
    direction: lower_is_better
  - name: correctness
    run: pytest tests/ -q
budget:
  max_experiments: 20
  max_consecutive_failures: 5
---

# Goal

Make the API response time under 50ms for the /search endpoint.
Maintain correctness — all existing tests must pass.

# Workflow

For each experiment:

1. Run `autoresearch status` to see past experiments and current best scores.
2. Based on what worked and what didn't, form a hypothesis for your next change.
3. Explore the code, understand the current state, then implement ONE focused change.
4. Run `autoresearch eval -m "your hypothesis here"` to evaluate.
5. Read the output — it tells you whether the change was kept or discarded and why.
6. Repeat from step 1.

# Rules

- One change per experiment. Don't combine unrelated modifications.
- Learn from history. Don't repeat discarded approaches. Build on what worked.
- Keep code clean. Unnecessary complexity is a reason to discard.
- Never stop. Keep experimenting until you are interrupted.
- Don't modify AUTORESEARCH.md or experiments.jsonl.
