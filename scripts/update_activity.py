"""Update only the marked README section using public project commits."""

import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

OWNER = "romario-anchaise"
PROJECTS = ("Happy_Dog", "parqueo-inteligente", "AmzartOne")
ROOT = Path(__file__).resolve().parents[1]
START, END = "<!-- ACTIVITY:START -->", "<!-- ACTIVITY:END -->"


def get_json(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-activity"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urlopen(Request("https://api.github.com/" + path, headers=headers), timeout=30) as response:
        return json.load(response)


def safe_text(value):
    # Treat commit titles as text, never as README markup or embedded HTML.
    return re.sub(r"[&<>|`\[\]*_\\]", lambda match: "&#" + str(ord(match[0])) + ";", value)


def main():
    entries = []
    for project in PROJECTS:
        commits = get_json(f"repos/{OWNER}/{project}/commits?per_page=1")
        if not commits:
            continue
        latest = commits[0]
        sha = latest["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Unexpected commit identifier")
        commit = latest["commit"]
        date = commit["committer"]["date"]
        title = commit["message"].splitlines()[0]
        if len(title) > 90:
            title = title[:87].rstrip() + "…"
        url = f"https://github.com/{OWNER}/{project}/commit/{sha}"
        row = f"| {date[:10]} | [{safe_text(project)}](https://github.com/{OWNER}/{project}) | [{safe_text(title)}]({url}) |"
        entries.append((date, row))
    if not entries:
        raise RuntimeError("No public activity found; preserving README")
    rows = ["| Fecha (UTC) | Proyecto | Último commit |", "| :--- | :--- | :--- |"]
    rows.extend(row for _, row in sorted(entries, reverse=True))
    readme = ROOT / "README.md"
    current = readme.read_text(encoding="utf-8")
    if current.count(START) != 1 or current.count(END) != 1:
        raise ValueError("README must have exactly one pair of activity markers")
    before, rest = current.split(START)
    _, after = rest.split(END)
    updated = before + START + "\n" + "\n".join(rows) + "\n" + END + after
    if updated != current:
        readme.write_text(updated, encoding="utf-8", newline="\n")
        print("Updated project activity")
    else:
        print("Project activity is unchanged")


if __name__ == "__main__":
    main()
