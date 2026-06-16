"""Architecture guard: `core/` must not depend on the optional AI/ML/data layers.

CLAUDE.md rule — keep AI/ML/data as optional layers that depend on `core`, never the reverse —
so the deterministic test path runs with them absent. This statically scans every module under
`core/` for imports of those layers (or the Anthropic SDK), resolving relative imports to absolute
names so a `from ..ml import x` can't slip past, and fails if any leaks in.
"""

import ast
from pathlib import Path

from utils.helpers import get_project_root

# Optional layers / heavy SDKs that core must never import (depend on core, not vice versa).
FORBIDDEN_PREFIXES = (
    "core.ai",
    "core.ml",
    "core.telemetry",
    "core.data",
    "anthropic",
)


def _imported_modules(path: Path, project_root: Path):
    """Yield absolute module names imported by a file, resolving relative imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    # Package parts of THIS file: core/pom/web/base_page.py -> ["core", "pom", "web"].
    package_parts = list(path.relative_to(project_root).with_suffix("").parts[:-1])

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    yield node.module
            else:
                # Resolve a relative import against this file's package.
                base = package_parts[: len(package_parts) - (node.level - 1)]
                if node.module:
                    yield ".".join([*base, *node.module.split(".")])
                else:
                    for alias in node.names:  # e.g. `from . import ml`
                        yield ".".join([*base, alias.name])


def test_core_does_not_import_optional_layers():
    project_root = Path(get_project_root())
    core_dir = project_root / "core"
    offenders = []
    for py_file in core_dir.rglob("*.py"):
        for module in _imported_modules(py_file, project_root):
            if any(
                module == prefix or module.startswith(prefix + ".")
                for prefix in FORBIDDEN_PREFIXES
            ):
                offenders.append(
                    f"{py_file.relative_to(project_root)} imports '{module}'"
                )

    assert not offenders, (
        "core/ must not import the optional AI/ML/data layers (they depend on core, "
        "never the reverse):\n" + "\n".join(offenders)
    )
