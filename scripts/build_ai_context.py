#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_CONTEXT_FILES: tuple[str, ...] = (
    "README.md",
    "docker-compose.yml",
    "web/requirements.txt",
    "bot/requirements.txt",
    "web/Dockerfile",
    "bot/Dockerfile",
    "web/app/main.py",
    "web/app/database.py",
    "web/app/models.py",
    "web/app/schemas.py",
    "web/app/crud.py",
    "web/app/routers/users.py",
    "web/app/routers/wagers.py",
    "web/app/routers/catalog.py",
    "bot/main.py",
)

IGNORED_TREE_ENTRIES = {
    ".git",
    "__pycache__",
    "ai_context",
}


def build_tree(root: Path, max_depth: int = 2, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if max_depth <= 0:
        return lines
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.name in IGNORED_TREE_ENTRIES or entry.name.startswith(".venv"):
            continue
        marker = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{entry.name}{marker}")
        if entry.is_dir():
            lines.extend(build_tree(entry, max_depth=max_depth - 1, prefix=prefix + "  "))
    return lines


def load_issue(issue_path: Path) -> dict:
    with issue_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def serialize_issue(issue: dict) -> str:
    lines = [
        f"# Issue #{issue.get('number')} – {issue.get('title', '').strip()}",
        "",
        issue.get("body", "").strip(),
        "",
    ]
    raw_comments = issue.get("comments") or []
    if isinstance(raw_comments, dict):
        comments = raw_comments.get("nodes") or []
    else:
        comments = raw_comments
    if comments:
        lines.append("## Comments")
        for comment in comments:
            author = (comment.get("author") or {}).get("login", "unknown")
            body = (comment.get("body") or "").strip()
            lines.append(f"- **{author}**: {body}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def read_file(root: Path, relative_path: str) -> tuple[str, str] | None:
    target = root / relative_path
    if not target.exists() or not target.is_file():
        return None
    contents = target.read_text(encoding="utf-8")
    return relative_path, contents


def build_context(
    repo_root: Path,
    files: Sequence[str],
    issue: dict,
    tree_depth: int,
) -> tuple[str, list[str]]:
    now = dt.datetime.utcnow().isoformat()
    sections: list[str] = [
        f"Context generated at {now} UTC",
        "",
        serialize_issue(issue),
        "## Repository Tree Snapshot",
        "```\n" + "\n".join(build_tree(repo_root, max_depth=tree_depth)) + "\n```",
        "",
    ]
    included_files: list[str] = []
    for relative_path in files:
        result = read_file(repo_root, relative_path)
        if result is None:
            continue
        rel, contents = result
        included_files.append(rel)
        sections.append(f"## File: {rel}")
        sections.append("```")
        sections.append(contents.rstrip())
        sections.append("```")
        sections.append("")
    return "\n".join(sections).strip() + "\n", included_files


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build AI context pack from issue JSON.")
    parser.add_argument("--issue-json", required=True, help="Path to gh issue view JSON output.")
    parser.add_argument("--output", required=True, help="Where to write the assembled context markdown.")
    parser.add_argument(
        "--files-output",
        default=None,
        help="Optional path to write newline-delimited file list used for aider.",
    )
    parser.add_argument(
        "--extra-file",
        action="append",
        default=[],
        help="Additional repo-relative files to include.",
    )
    parser.add_argument("--tree-depth", type=int, default=2, help="Depth for repository tree snapshot.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(__file__).resolve().parents[1]
    issue_path = Path(args.issue_json)
    output_path = Path(args.output)
    files_output_path = Path(args.files_output) if args.files_output else None

    files = list(dict.fromkeys([*DEFAULT_CONTEXT_FILES, *args.extra_file]))
    issue = load_issue(issue_path)
    context, included_files = build_context(repo_root, files, issue, args.tree_depth)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(context, encoding="utf-8")

    if files_output_path:
        files_output_path.parent.mkdir(parents=True, exist_ok=True)
        files_output_path.write_text("\n".join(included_files) + "\n", encoding="utf-8")

    print(f"[context] wrote {output_path}")
    if files_output_path:
        print(f"[context] wrote {files_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
