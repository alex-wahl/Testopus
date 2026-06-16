"""Pure logic: convert a Testiny test-case dict into a Testopus spec-Markdown string.

No network or filesystem here (those live in ``tools/testiny/client.py`` and
``cli.py``) so this module is unit-tested in isolation. The output is the
"Markdown + front-matter" spec format consumed by the ``testopus-nl-test`` skill;
the fields map 1:1 onto the Testiny REST data model (``title`` /
``precondition_text`` / ``steps_text`` / ``expected_result_text`` / ``priority`` +
custom fields). See ``docs/testiny/workflow.md`` and
``.claude/adr/0002-testiny-nl-authoring.md``.
"""

import re
import unicodedata

import yaml

# Testiny priority -> Allure severity (the set pytest.ini registers: blocker/critical/
# normal/minor/trivial). Best-effort and case-insensitive; unknown/missing -> "normal".
# NOTE: confirm the exact priority vocabulary of your Testiny project and adjust here;
# this table is the single source of truth shared by the tool and the skill.
_PRIORITY_TO_SEVERITY = {
    "highest": "blocker",
    "high": "critical",
    "medium": "normal",
    "normal": "normal",
    "low": "minor",
    "lowest": "trivial",
}
_DEFAULT_SEVERITY = "normal"

# Placeholder so every spec keeps a stable three-section body even when Testiny leaves
# a field blank — the skill can then flag the gap instead of mis-parsing a section.
_EMPTY_SECTION = "_None specified._"

_SLUG_MAX_LEN = 50


class SpecValidationError(ValueError):
    """Raised when a Testiny case cannot become a valid spec — a missing required
    field, an unsupported (non-TEXT) template, or an app/page that cannot be
    resolved."""


def priority_to_severity(priority):
    """Map a Testiny priority to an Allure severity (unknown/None -> ``normal``)."""
    if priority is None:
        return _DEFAULT_SEVERITY
    return _PRIORITY_TO_SEVERITY.get(str(priority).strip().lower(), _DEFAULT_SEVERITY)


def _slugify(text):
    """Lowercase ASCII slug: accent-folded, non-alphanumerics collapsed to hyphens."""
    folded = (
        unicodedata.normalize("NFKD", str(text))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = "-".join(re.findall(r"[a-z0-9]+", folded))
    if len(slug) > _SLUG_MAX_LEN:
        slug = slug[:_SLUG_MAX_LEN].rstrip("-")
    return slug or "case"


def spec_filename(case):
    """Deterministic ``tc-<id>-<slug>.md`` filename for a Testiny case."""
    case_id = case.get("id")
    if case_id is None:
        raise SpecValidationError("Testiny case is missing required field 'id'.")
    return f"tc-{case_id}-{_slugify(case.get('title', ''))}.md"


def _require(case, field):
    """Return ``case[field]`` or raise if absent/blank."""
    value = case.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise SpecValidationError(f"Testiny case is missing required field '{field}'.")
    return value


def _section(text):
    """Section body verbatim, or a placeholder when Testiny left the field empty."""
    if text is None:
        return _EMPTY_SECTION
    return str(text).strip() or _EMPTY_SECTION


def _drop_none(mapping):
    """Drop keys whose value is ``None`` (keeps the front-matter clean and ordered)."""
    return {key: value for key, value in mapping.items() if value is not None}


def resolve_app(case, app_field="cf__app", default_app=None):
    """Resolve the app name from the case's custom field, falling back to a default.

    Shared by the normalizer and the CLI so the spec's ``app`` front-matter and the
    ``specs/<app>/`` destination path can never drift.
    """
    return case.get(app_field) or default_app


def testiny_case_to_spec(
    case,
    *,
    app_field="cf__app",
    page_field="cf__page",
    default_app=None,
    default_page=None,
    pulled_at=None,
):
    """Render a Testiny test-case dict as a spec-Markdown string.

    :param case: A Testiny test-case object (as returned by ``GET /testcase/:id``).
    :param app_field: Custom-field key holding the app name (default ``cf__app``).
    :param page_field: Custom-field key holding the page name (default ``cf__page``).
    :param default_app: Fallback app when the custom field is absent.
    :param default_page: Fallback page when the custom field is absent.
    :param pulled_at: Optional ISO timestamp written to the front-matter (provenance).
    :return: The spec as Markdown (YAML front-matter + Precondition/Steps/Expected).
    :raises SpecValidationError: On a missing required field, a non-TEXT template, or an
        unresolved app/page.
    """
    template = case.get("template", "TEXT")
    if str(template).upper() != "TEXT":
        raise SpecValidationError(
            f"Unsupported Testiny template '{template}'; only TEXT cases are supported "
            "(step-table templates are out of scope)."
        )

    case_id = _require(case, "id")
    title = _require(case, "title")
    app = resolve_app(case, app_field, default_app)
    page = case.get(page_field) or default_page
    if not app:
        raise SpecValidationError(
            f"Cannot resolve app: custom field '{app_field}' is absent and no "
            "--default-app was given."
        )
    if not page:
        raise SpecValidationError(
            f"Cannot resolve page: custom field '{page_field}' is absent and no "
            "--default-page was given."
        )

    priority = case.get("priority")
    front = _drop_none(
        {
            "testiny_id": case_id,
            "testiny_etag": case.get("_etag"),
            "project_id": case.get("project_id"),
            "title": title,
            "app": app,
            "page": page,
            "priority": priority,
            "severity": priority_to_severity(priority),
            "status": "draft",
            "source": "testiny",
            "pulled_at": pulled_at or None,
        }
    )
    front_matter = yaml.safe_dump(
        front, sort_keys=False, allow_unicode=True, width=4096
    )

    body = (
        f"# {title}\n\n"
        f"## Precondition\n\n{_section(case.get('precondition_text'))}\n\n"
        f"## Steps\n\n{_section(case.get('steps_text'))}\n\n"
        f"## Expected Result\n\n{_section(case.get('expected_result_text'))}\n"
    )
    return f"---\n{front_matter}---\n\n{body}"
