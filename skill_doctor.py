#!/usr/bin/env python3
"""Check local tool availability against tools mentioned in agent-skill files."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


DOC_NAMES = {
    "readme.md", "skill.md", "install.md", "requirements.txt",
    "pyproject.toml", "package.json", "environment.yml", "environment.yaml",
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "target"}
MAX_FILE_BYTES = 1_000_000

# These checks only report that a tool name appeared in a selected project file.
# They do not establish that the tool is required or run any downloaded code.
TOOLS: dict[str, tuple[re.Pattern[str], tuple[str, ...]]] = {
    "ffmpeg": (re.compile(r"(?<![\w-])ffmpeg(?:\.exe)?(?![\w-])", re.I), ("ffmpeg",)),
    "ffprobe": (re.compile(r"(?<![\w-])ffprobe(?:\.exe)?(?![\w-])", re.I), ("ffprobe",)),
    "python": (re.compile(r"(?<![\w-])python(?:3(?:\.\d+)?)?(?:\.exe)?(?![\w-])", re.I), ("python3", "python")),
    "node": (re.compile(r"(?<![\w-])node(?:\.js|\.exe)?(?![\w-])", re.I), ("node",)),
    "npm": (re.compile(r"(?<![\w-])npm(?:\.cmd)?(?![\w-])", re.I), ("npm",)),
    "npx": (re.compile(r"(?<![\w-])npx(?![\w-])", re.I), ("npx",)),
    "uv": (re.compile(r"(?<![\w-])uv(?![\w-])", re.I), ("uv",)),
    "docker": (re.compile(r"(?<![\w-])docker(?![\w-])", re.I), ("docker",)),
    "yt-dlp": (re.compile(r"(?<![\w-])yt-dlp(?:\.exe)?(?![\w-])", re.I), ("yt-dlp",)),
}


def project_files(root: Path) -> list[Path]:
    """Find a small set of common skill docs and dependency manifests."""
    if root.is_file():
        return [root] if root.name.lower() in DOC_NAMES else []
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.lower() in DOC_NAMES:
            found.append(path)
    return sorted(found)


def inspect_root(root: Path) -> dict[str, Any]:
    files = project_files(root)
    mentions: dict[str, list[str]] = {name: [] for name in TOOLS}
    unreadable: list[str] = []
    for file in files:
        try:
            if file.stat().st_size > MAX_FILE_BYTES:
                unreadable.append(f"{file}: skipped (larger than 1 MB)")
                continue
            lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            unreadable.append(f"{file}: could not read")
            continue
        for line_number, line in enumerate(lines, start=1):
            for tool, (pattern, _) in TOOLS.items():
                if pattern.search(line):
                    location = f"{file}:{line_number}"
                    if location not in mentions[tool]:
                        mentions[tool].append(location)

    checks = []
    for tool, (_, commands) in TOOLS.items():
        locations = mentions[tool]
        if not locations:
            continue
        executable = next((command for command in commands if shutil.which(command)), None)
        checks.append({
            "tool": tool,
            "status": "found" if executable else "not_found",
            "executable": executable,
            "mentioned_at": locations[:5],
            "note": (
                "Found on PATH; check the skill docs for version requirements."
                if executable else
                "Not found on PATH. Check the cited docs to see whether it is required or optional."
            ),
        })

    return {
        "path": str(root),
        "files_reviewed": [str(file) for file in files],
        "checks": checks,
        "notes": unreadable,
    }


def render_report(report: dict[str, Any]) -> str:
    lines = [f"Video Skill Doctor — {report['path']}"]
    if not report["files_reviewed"]:
        lines.append("No recognized skill docs or dependency manifests found.")
    elif not report["checks"]:
        lines.append(f"Reviewed {len(report['files_reviewed'])} file(s); no known tool names found.")
    else:
        lines.append(f"Reviewed {len(report['files_reviewed'])} file(s). Tools mentioned:")
        for check in report["checks"]:
            state = "FOUND" if check["status"] == "found" else "NOT FOUND"
            lines.append(f"  {state:9} {check['tool']}")
            lines.append(f"             {check['note']}")
            lines.extend(f"             mentioned in {location}" for location in check["mentioned_at"])
    if report["notes"]:
        lines.append("Notes:")
        lines.extend(f"  {note}" for note in report["notes"])
    lines.extend([
        "",
        "This is a text-based preflight, not a full dependency resolver or security audit.",
        "It does not run skill code, install tools, or decide whether a mention is mandatory.",
    ])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether common tools mentioned in local agent-skill docs are on PATH."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Skill folders or recognized skill documentation files")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    reports = []
    missing_paths = []
    for root in args.paths:
        if not root.exists():
            missing_paths.append(str(root))
            continue
        reports.append(inspect_root(root))
    if args.json:
        print(json.dumps({"reports": reports, "missing_paths": missing_paths}, indent=2))
    else:
        print("\n\n".join(render_report(report) for report in reports))
        for path in missing_paths:
            print(f"\nPath not found: {path}")
    return 2 if missing_paths else 0


if __name__ == "__main__":
    raise SystemExit(main())
