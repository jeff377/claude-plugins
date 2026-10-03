#!/usr/bin/env python3
"""Audit or apply a GitHub organization's repository baseline.

The baseline is `repo-baseline.json` in the organization's `.github` repository (or a local file given with
--baseline). See SKILL.md for its format.

  org_baseline.py audit --org ORG [REPO ...]          List every difference; exit 1 when there is any.
  org_baseline.py apply --org ORG REPO                 Show what apply would change in REPO's settings and protection.
  org_baseline.py apply --org ORG REPO --confirm       Change them. Files (CODEOWNERS, CONTRIBUTING.md) are reported only:
                                                       they change through a commit, not through the API.

Needs the GitHub CLI (`gh`), signed in with admin rights on the repositories.
"""
import argparse
import base64
import json
import subprocess
import sys


def gh(*args, body=None, allow_404=False):
    result = subprocess.run(["gh", "api", *args] + (["--input", "-"] if body is not None else []),
                            input=json.dumps(body) if body is not None else None,
                            capture_output=True, text=True)
    if result.returncode != 0:
        if allow_404 and "404" in (result.stdout + result.stderr):
            return None
        sys.exit(f"gh api {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def file_text(org, repo, path):
    content = gh(f"repos/{org}/{repo}/contents/{path}", allow_404=True)
    return None if content is None else base64.b64decode(content["content"]).decode("utf-8")


def load_baseline(org, path):
    if path:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    text = file_text(org, ".github", "repo-baseline.json")
    if text is None:
        sys.exit(f"{org}/.github has no repo-baseline.json.")
    return json.loads(text)


def audit_repo(org, repo, baseline):
    """Returns a list of (kind, message) differences; kind is 'api' when apply can fix it, 'file' otherwise."""
    diffs = []
    meta = gh(f"repos/{org}/{repo}")
    for key, want in baseline["settings"].items():
        if meta.get(key) != want:
            diffs.append(("api", f"setting {key} is {meta.get(key)}, baseline {want}"))

    protection = gh(f"repos/{org}/{repo}/branches/{meta['default_branch']}/protection", allow_404=True)
    want_p = baseline["protection"]
    want_checks = sorted(baseline["repos"][repo].get("required_checks", []))
    if protection is None:
        diffs.append(("api", f"{meta['default_branch']} is not protected"))
    else:
        status = protection.get("required_status_checks") or {}
        reviews = protection.get("required_pull_request_reviews")
        actual = {
            "strict": status.get("strict"),
            "enforce_admins": protection.get("enforce_admins", {}).get("enabled"),
            "required_approving_review_count": None if reviews is None else reviews.get("required_approving_review_count"),
            "require_code_owner_reviews": None if reviews is None else reviews.get("require_code_owner_reviews"),
            "allow_force_pushes": protection.get("allow_force_pushes", {}).get("enabled"),
            "allow_deletions": protection.get("allow_deletions", {}).get("enabled"),
        }
        for key, want in want_p.items():
            if actual.get(key) != want:
                diffs.append(("api", f"protection {key} is {actual.get(key)}, baseline {want}"))
        if sorted(status.get("contexts", [])) != want_checks:
            diffs.append(("api", f"required checks are {sorted(status.get('contexts', []))}, baseline {want_checks}"))

    owners = next((t for t in (file_text(org, repo, p) for p in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")) if t), None)
    if owners is None or baseline["codeowners"] not in owners.splitlines():
        diffs.append(("file", f"CODEOWNERS lacks the line '{baseline['codeowners']}'"))

    contributing = file_text(org, repo, "CONTRIBUTING.md")
    shared = f"github.com/{org}/.github/blob/main/CONTRIBUTING.md"
    if contributing is not None and shared not in contributing:
        diffs.append(("file", f"CONTRIBUTING.md does not link to the shared guide ({shared})"))

    # A contributor's coding agent reads the repository's agent guide, not the maintainer's own configuration.
    guides = {path: file_text(org, repo, path) for path in (".claude/CLAUDE.md", "CLAUDE.md")}
    if not any(guides.values()):
        diffs.append(("file", "no agent guide (.claude/CLAUDE.md or CLAUDE.md) to point at the shared guide"))
    elif not any(shared in text for text in guides.values() if text):
        diffs.append(("file", f"the agent guide does not link to the shared guide ({shared})"))
    return diffs


def apply_repo(org, repo, baseline, confirm):
    meta = gh(f"repos/{org}/{repo}")
    branch = meta["default_branch"]
    want_p = baseline["protection"]
    body = {
        "required_status_checks": {"strict": want_p["strict"], "contexts": baseline["repos"][repo].get("required_checks", [])},
        "enforce_admins": want_p["enforce_admins"],
        "required_pull_request_reviews": {
            "required_approving_review_count": want_p["required_approving_review_count"],
            "require_code_owner_reviews": want_p["require_code_owner_reviews"],
            "dismiss_stale_reviews": False,
        },
        "restrictions": None,
        "allow_force_pushes": want_p["allow_force_pushes"],
        "allow_deletions": want_p["allow_deletions"],
    }
    print(f"PATCH repos/{org}/{repo} {json.dumps(baseline['settings'])}")
    print(f"PUT repos/{org}/{repo}/branches/{branch}/protection {json.dumps(body)}")
    if not confirm:
        print("Nothing changed. Run again with --confirm to apply.")
        return
    gh("-X", "PATCH", f"repos/{org}/{repo}", body=baseline["settings"])
    gh("-X", "PUT", f"repos/{org}/{repo}/branches/{branch}/protection", body=body)
    print("Applied. Files are not changed here; run audit for what is left.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["audit", "apply"])
    parser.add_argument("repos", nargs="*")
    parser.add_argument("--org", required=True)
    parser.add_argument("--baseline", help="A local baseline file instead of the one in the .github repository.")
    parser.add_argument("--confirm", action="store_true", help="apply: change the settings instead of only showing them.")
    args = parser.parse_args()
    baseline = load_baseline(args.org, args.baseline)

    if args.command == "apply":
        if len(args.repos) != 1:
            sys.exit("apply takes exactly one repository.")
        if args.repos[0] not in baseline["repos"]:
            sys.exit(f"{args.repos[0]} is not in the baseline; add it with its required checks first.")
        apply_repo(args.org, args.repos[0], baseline, args.confirm)
        return

    listed = gh("--paginate", f"orgs/{args.org}/repos?per_page=100")
    active = sorted(r["name"] for r in listed if not r["archived"])
    repos = args.repos or [r for r in active if r not in baseline.get("excluded", {})]
    found = False
    for repo in repos:
        if repo not in baseline["repos"]:
            print(f"{repo}: not in the baseline (add it with its required checks, or list it under excluded with a reason)")
            found = True
            continue
        for kind, message in audit_repo(args.org, repo, baseline):
            print(f"{repo}: [{'apply' if kind == 'api' else 'commit'}] {message}")
            found = True
    for repo in baseline["repos"]:
        if repo not in active:
            print(f"{repo}: in the baseline but not an active repository of {args.org}")
            found = True
    if not found:
        print("Every repository matches the baseline.")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
