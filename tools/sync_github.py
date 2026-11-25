"""Audit the editorial catalogue against GitHub's public repository API.

Read-only: report differences, never publish content or create commits.
"""
import argparse
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch_json(url, token=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Rufus-Terminal-catalogue-check",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def public_repositories(owner, token=None):
    """Paginate and exclude nonpublic data and the special profile repository."""
    result = []
    page = 1
    while True:
        batch = fetch_json(
            f"https://api.github.com/users/{owner}/repos"
            f"?type=owner&sort=full_name&per_page=100&page={page}", token
        )
        if not isinstance(batch, list):
            raise ValueError("Unexpected repository response")
        for repo in batch:
            if (
                repo.get("owner", {}).get("login", "").casefold() == owner.casefold()
                and repo.get("private") is False
                and repo.get("visibility", "public") == "public"
                and repo["name"].casefold() != owner.casefold()
            ):
                result.append(repo)
        if len(batch) < 100:
            return result
        page += 1


def compare(projects, repositories):
    """Compare case-insensitively without modifying editorial descriptions."""
    catalogue = {project["repo"].casefold(): project for project in projects}
    public = {repo["name"].casefold(): repo for repo in repositories}
    missing = []
    matched = []
    for key, repo in sorted(public.items()):
        entry = {
            "repo": repo["name"],
            "url": repo["html_url"],
            "description": repo.get("description"),
            "language": repo.get("language"),
            "pushed_at": repo.get("pushed_at"),
            "archived": bool(repo.get("archived")),
            "fork": bool(repo.get("fork")),
        }
        (matched if key in catalogue else missing).append(entry)
    return {
        "public_count_excluding_profile": len(public),
        "catalogue_count": len(catalogue),
        "new_public_repositories": missing,
        "catalogue_entries_not_in_public_listing": [
            catalogue[key]["repo"] for key in sorted(catalogue.keys() - public.keys())
        ],
        "matched_public_repositories": matched,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "github-catalogue-report.json")
    args = parser.parse_args()
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    projects = json.loads((ROOT / "src/projects.json").read_text(encoding="utf-8"))
    profile = urlparse(site["github"])
    owner = profile.path.strip("/")
    if (profile.scheme != "https" or profile.netloc != "github.com"
            or not re.fullmatch(r"[A-Za-z0-9-]+", owner)):
        parser.error("site.json github must be a GitHub user profile URL")
    try:
        report = compare(projects, public_repositories(owner, os.getenv("GITHUB_TOKEN")))
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
        parser.exit(1, f"GitHub catalogue check failed: {error}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Public projects: {report['public_count_excluding_profile']}; catalogue: {report['catalogue_count']}")
    for repo in report["new_public_repositories"]:
        print(f"New public repository: {repo['repo']}")
    for name in report["catalogue_entries_not_in_public_listing"]:
        print(f"Review availability of catalogue entry: {name}")
    print(f"Report: {args.output}")
    return 2 if report["new_public_repositories"] or report["catalogue_entries_not_in_public_listing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
