"""Parse YAML frontmatter from a markdown file."""

from __future__ import annotations

import os

import yaml


def load(path: str) -> dict:
    """Read a markdown file with YAML frontmatter and return the parsed config.

    Format:
        ---
        evals:
          - name: latency
            run: python bench.py
            direction: lower_is_better
        ---

        # Free-text instructions for the agent ...
    """
    with open(path) as f:
        text = f.read()

    if not text.startswith("---"):
        return {}

    end = text.find("---", 3)
    if end == -1:
        return {}

    frontmatter = text[3:end].strip()
    config = yaml.safe_load(frontmatter) or {}

    # Workspace is always the directory containing the config file
    config["_workspace"] = os.path.dirname(os.path.abspath(path)) or os.getcwd()
    config["_file"] = os.path.abspath(path)

    # Infer project name from directory if not set
    config.setdefault("name", os.path.basename(config["_workspace"]))

    return config
