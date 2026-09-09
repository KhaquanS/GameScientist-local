from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from gamescientist.core.identity import validate_identifier


def _contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def safe_pack_file(pack_root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() != relative:
        raise ValueError(f"pack path must be normalized and relative: {relative!r}")
    resolved = (pack_root / relative).resolve()
    if not _contained(resolved, pack_root.resolve()) or not resolved.is_file():
        raise ValueError(f"pack file is missing or escapes the pack: {relative}")
    return resolved


@dataclass(frozen=True)
class BenchmarkManifest:
    schema_version: int
    pack_id: str
    plugin: str
    catalog: str

    @classmethod
    def load(cls, path: Path) -> "BenchmarkManifest":
        resolved = path.resolve()
        value = json.loads(resolved.read_text(encoding="utf-8"))
        expected = {"schema_version", "pack_id", "plugin", "catalog"}
        if set(value) != expected:
            raise ValueError("benchmark manifest has unknown or missing fields")
        manifest = cls(**value)
        if manifest.schema_version != 1:
            raise ValueError("unsupported benchmark schema version")
        validate_identifier(manifest.pack_id, "pack_id")
        validate_identifier(manifest.plugin, "plugin_id")
        safe_pack_file(resolved.parent, manifest.catalog)
        return manifest


def discover_manifest_paths(search_roots: tuple[Path, ...]) -> tuple[Path, ...]:
    found: set[Path] = set()
    for configured in search_roots:
        root = configured.expanduser().resolve()
        if not root.is_dir():
            continue
        for candidate in root.rglob("benchmark.json"):
            if candidate.is_symlink():
                continue
            resolved = candidate.resolve()
            if _contained(resolved, root) and resolved.is_file():
                found.add(resolved)
    return tuple(sorted(found))
