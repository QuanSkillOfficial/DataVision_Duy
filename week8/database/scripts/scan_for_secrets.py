import re
import subprocess
import sys


def run_git(args):
    """Run a git command, return stdout as a list of lines (empty list on
    non-zero exit, e.g. not a git repo yet)."""
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        print("ERROR: git is not on PATH.", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def section(title, lines, empty_message="  none found"):
    print(f"=== {title} ===")
    if lines:
        for line in lines:
            print(f"  {line}")
    else:
        print(empty_message)
    print()


def main():
    tracked_files = run_git(["ls-files"])

    env_templates = [
        f for f in tracked_files
        if re.search(r"(^|/)\.env(\..*)?\.example$|(^|/)\.env\.example$", f)
    ]
    env_files = [
        f for f in tracked_files
        if re.search(r"(^|/)\.env(\..*)?$", f) and f not in env_templates
    ]
    section("1. Tracked environment templates (allowed)", env_templates)
    section("2. Tracked non-template .env files", env_files)

    dump_files = [
        f for f in tracked_files
        if re.search(r"\.dump$|\.sql\.gz$|\.pgdump$", f)
    ]
    section("3. Tracked database dump files", dump_files)

    pycache_files = [
        f for f in tracked_files
        if re.search(r"__pycache__/|\.py[cod]$", f)
    ]
    section("4. Tracked __pycache__ / .pyc files", pycache_files)

    credential_pattern = re.compile(
        r'(DB_PASSWORD|PGPASSWORD|api[_-]?key|secret|token)\s*[:=]\s*'
        r'["\'][^"\']{6,}',
        re.IGNORECASE,
    )
    grep_hits = []
    for f in tracked_files:
        if f.endswith(".md") or f.endswith(".lock"):
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if credential_pattern.search(line) and not re.search(
                        r"your[-_ ]?(password|secret|token)|example|placeholder|dummy|unit-test",
                        line,
                        re.IGNORECASE,
                    ):
                        grep_hits.append(f"{f}:{lineno}: {line.strip()}")
        except (IsADirectoryError, PermissionError, FileNotFoundError):
            continue
    section("5. Likely hard-coded credentials in tracked files", grep_hits)

    history_files = run_git(
        ["log", "--all", "--diff-filter=A", "--name-only", "--pretty=format:"]
    )
    history_hits = sorted(set(
        f for f in history_files
        if (
            re.search(r"(^|/)\.env(\..*)?$|\.dump$|\.pgdump$", f)
            and not re.search(r"\.env(\..*)?\.example$|\.env\.example$", f)
        )
    ))
    section(
        "6. Non-template .env / dump files anywhere in git history",
        history_hits,
        empty_message="  none found in history",
    )

    print("Scan complete. Any hits above must be reviewed manually before")
    print("deciding on rotation and/or history remediation — this script")
    print("makes no changes.")

    any_hits = bool(env_files or dump_files or pycache_files or grep_hits or history_hits)
    return 1 if any_hits else 0


if __name__ == "__main__":
    sys.exit(main())
