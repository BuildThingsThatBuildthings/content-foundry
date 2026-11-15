#!/usr/bin/env python3
"""Repository-local skill package validator used on clean CI hosts."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    skill = Path(sys.argv[1] if len(sys.argv) > 1 else "skill/content-foundry")
    source = skill / "SKILL.md"
    problems = []
    if not source.exists():
        problems.append("SKILL.md is missing")
    else:
        body = source.read_text()
        match = re.match(r"^---\n(.*?)\n---\n", body, re.DOTALL)
        if not match:
            problems.append("SKILL.md frontmatter is invalid")
        else:
            frontmatter = match.group(1)
            name = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.MULTILINE)
            description = re.search(
                r"^description:\s*(?:[>|]-?\s*)?([^\n]*)$",
                frontmatter,
                re.MULTILINE,
            )
            if not name or name.group(1).strip("\"' ") != "content-foundry":
                problems.append("frontmatter name must be content-foundry")
            if not description:
                problems.append("frontmatter description is required")
        if len(body.splitlines()) > 500:
            problems.append("SKILL.md exceeds 500 lines")
        if "/Users/" in body or "\\Users\\" in body:
            problems.append("SKILL.md contains a private absolute path")
        for ref in set(re.findall(r"`(references/[^`]+\.md)`", body)):
            if not (skill / ref).exists():
                problems.append(f"missing referenced file: {ref}")
    if not (skill / "agents" / "openai.yaml").exists():
        problems.append("agents/openai.yaml is missing")
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1
    print("Content Foundry skill package is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
