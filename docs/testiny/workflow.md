# Testiny-driven test authoring workflow

This document describes the end-to-end flow for turning a human-language test case written in
[Testiny](https://app.testiny.io) into a committed, deterministic Pytest suite in Testopus.

For the architectural rationale and rejected alternatives see
[ADR-0002](../../.claude/adr/0002-testiny-nl-authoring.md).

## Overview

```
QA writes case in Testiny
        |
        v
python -m tools.testiny pull  →  specs/<app>/tc-<id>-<slug>.md
        |
        v
Review spec (locators / page exist?)
        |
        v
testopus-nl-test skill  →  tests/ui_tests/web/<app>/test_<name>.py
        |
        v
code-reviewer (Opus 4.8, effort max)  +  human review
        |
        v
testopus-run skill  (pytest --collect-only, then hatch run ui:web or hatch run api:run)
        |
        v
commit
```

The LLM (Claude Code) is in the **authoring** step only. The committed output is plain Pytest that
runs deterministically with no AI dependency at test-execution time.

## Prerequisites

### Install the tools extra

The pull tool depends on `requests`, which lives in the `[tools]` optional extra:

```bash
pip install -e .[tools]
```

When using Hatch the `test` env already includes this extra (`features = ["test", "tools"]`).

### Set `TESTINY_API_KEY`

Copy `.env.example` to `.env` (gitignored) and fill in your Testiny REST API key:

```bash
cp .env.example .env
# edit .env: set TESTINY_API_KEY=<your key>
```

The key is read from `TESTINY_API_KEY` in the environment or the local `.env`; it is never
written to logs or spec files (debug output is masked by `utils.redact.redact_mapping`).
In CI, set it as a repository secret.

### Confirm your custom field keys

The tool maps two Testiny custom fields to spec metadata:

| CLI flag | Default | Purpose |
|---|---|---|
| `--app-field` | `cf__app` | Testiny custom field holding the app name |
| `--page-field` | `cf__page` | Testiny custom field holding the page name |

Custom-field keys are **tenant-specific** in Testiny. Verify the exact key names in your Testiny
project's Settings → Custom Fields and supply `--app-field`/`--page-field` if they differ from
the defaults.

## Step 1 — Pull cases from Testiny

```
python -m tools.testiny pull <selector> [options]
```

Exactly one selector is required:

| Flag | Description |
|---|---|
| `--case-id N[,N,…]` | Fetch one or more cases by id |
| `--folder ID` | Fetch every case in a Testiny folder |
| `--query '<JSON>'` | Pass a raw Testiny filter object (you own the scope) |

### Common options

| Flag | Default | Description |
|---|---|---|
| `--base-url URL` | `https://app.testiny.io/api/v1` | Testiny API base URL |
| `--project-id ID` | — | Scope `--folder`/`--query` to a project |
| `--app-field KEY` | `cf__app` | Custom field for the app name |
| `--page-field KEY` | `cf__page` | Custom field for the page name |
| `--default-app NAME` | — | Fallback app when the custom field is absent |
| `--default-page NAME` | — | Fallback page when the custom field is absent |
| `--out DIR` | `specs` | Output root directory |
| `--verbose` | off | Enable debug logging (key stays masked) |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | All fetched cases written successfully |
| 1 | Network / HTTP error from Testiny |
| 2 | `TESTINY_API_KEY` not set |

### Examples

```bash
# Pull a single case
python -m tools.testiny pull --case-id 1

# Pull several cases at once
python -m tools.testiny pull --case-id 1,2,7

# Pull an entire folder (scoped to project 42)
python -m tools.testiny pull --folder 9 --project-id 42

# Pull with a custom filter; fall back to toolshop/login when custom fields are absent
python -m tools.testiny pull \
    --query '{"priority": {"op": "eq", "value": "high"}}' \
    --default-app toolshop --default-page login

# Use non-default custom field keys
python -m tools.testiny pull \
    --case-id 5 \
    --app-field cf__application \
    --page-field cf__screen

# Verbose mode (the API key is masked in output)
python -m tools.testiny pull --case-id 1 --verbose
```

## Step 2 — Review the spec

Each pulled case is written to `specs/<app>/tc-<id>-<slug>.md`. Open the file and verify:

- The `app` and `page` values map to a real Page Object (`core/pom/web/<app>/<page>_page.py`).
- The precondition, steps, and expected result are complete and unambiguous.
- The `priority`/`severity` mapping looks correct for your project.

If the Page Object for `app`/`page` does not yet exist, create it first with the
`testopus-page-object` skill before proceeding.

## Spec format reference

A pulled spec is YAML front-matter followed by a three-section Markdown body:

```markdown
---
testiny_id: 1
testiny_etag: 'W/"abc123"'
project_id: 42
title: Login rejects invalid credentials
app: toolshop
page: login
priority: high
severity: critical
status: draft
source: testiny
pulled_at: 2026-06-16T10:30:00Z
---

# Login rejects invalid credentials

## Precondition

The user is on the Toolshop login page (`LoginPage`, path `auth/login`).

## Steps

1. Enter an e-mail address and a password that do not match any account.
2. Submit the login form.

## Expected Result

An authentication error message containing "Invalid email or password" is shown
(`LoginPage.TEXT_LOGIN_ERROR_KEY_PHRASE`) and the user remains on the login page.
```

### Front-matter field mapping

| Spec field | Testiny source |
|---|---|
| `testiny_id` | `id` |
| `testiny_etag` | `_etag` |
| `project_id` | `project_id` |
| `title` | `title` |
| `app` | `cf__app` (or `--default-app`) |
| `page` | `cf__page` (or `--default-page`) |
| `priority` | `priority` |
| `severity` | derived from `priority` (see table below) |
| `status` | always `draft` |
| `source` | always `testiny` |
| `pulled_at` | UTC timestamp of the pull run |

Optional fields (`testiny_etag`, `project_id`, `priority`, `pulled_at`) are omitted from the
front-matter when the Testiny case does not supply them, so the file stays clean.

### Priority → severity mapping

The severity is written to the spec front-matter and becomes the `@pytest.mark.severity` value
in the generated test. Mapping is case-insensitive; unknown or missing priority values map to
`normal`.

| Testiny priority | Allure severity |
|---|---|
| highest | blocker |
| high | critical |
| medium / normal | normal |
| low | minor |
| lowest | trivial |
| unknown / missing | normal |

### Body sections

| Section | Testiny field |
|---|---|
| `## Precondition` | `precondition_text` |
| `## Steps` | `steps_text` |
| `## Expected Result` | `expected_result_text` |

All three sections are always present; when Testiny leaves a field blank the section body is
`_None specified._` so the skill can flag the gap rather than mis-parsing the document.

Only `template: "TEXT"` cases are supported. Step-table templates are out of scope.

## Step 3 — Generate the pytest suite

With a reviewed spec in place, invoke the **`testopus-nl-test`** skill:

```
/testopus-nl-test specs/toolshop/tc-1-login.md
```

The skill:

1. Reads the spec front-matter to resolve `app`/`page` → `core/pom/web/<app>/<page>_page.py`.
2. Reads the Page Object and builds the allowed vocabulary (locator constants, `TEXT_*` copy
   constants, snake_case action methods).
3. Maps `## Steps` to page-object action calls and `## Expected Result` to assertions, using
   only symbols that actually exist in the Page Object.
4. Generates `tests/ui_tests/web/<app>/test_<name>.py` with a provenance docstring linking
   the test back to its spec and Testiny case id.

If the spec requires a locator or action method that does not yet exist on the Page Object,
the skill either extends the Page Object via the `testopus-page-object` skill first, or emits
a `# BLOCKED: needs <PageClass>.<X>` marker for the human reviewer to resolve.

## Step 4 — Review and run

Before committing the generated test, run the mandatory "Before push" gate in order:

1. **Code review** — `code-reviewer` agent (Opus 4.8, effort `max`). A fabricated locator or
   invented method name will fail pytest collection, making grounding violations mechanically
   detectable.
2. **Run** — `testopus-run` skill: `pytest --collect-only` first (catches marker/import errors
   cheaply), then `hatch run ui:web`.
3. **Commit** after both pass.

## Out of scope

The following are explicitly not part of this workflow:

- Pushing test **results** back to Testiny (the TestRun API) — a future follow-up.
- An `anthropic`-SDK generation pipeline at authoring time — roadmap (ADR-0002).
- Runtime or agentic test execution where an LLM selects or drives tests — the verdict is
  always owned by the deterministic pytest path.
- Locator self-healing at test-execution time — roadmap.
