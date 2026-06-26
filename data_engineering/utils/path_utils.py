from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def relative_path(path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = resolve_project_path(path)
    if resolved is None:
        return None
    try:
        return resolved.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.resolve().as_posix()


def ensure_parent(path: str | Path) -> Path:
    resolved = resolve_project_path(path)
    if resolved is None:
        raise ValueError("Path cannot be None")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
