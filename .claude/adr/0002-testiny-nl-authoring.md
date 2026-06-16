# ADR-0002: Testiny-driven natural-language test authoring

- **Status:** Accepted
- **Date:** 2026-06-16
- **Deciders:** tech-lead, qa-automation-engineer, ai-engineer, backend-engineer

## Context

The team writes test cases in **Testiny** (a web-based test-management platform) as human-language
descriptions: a precondition, numbered steps, and an expected result. Turning those into executable
Pytest suites today requires a manual re-typing step that is error-prone and duplicates effort —
the case exists in two places (Testiny and the Python repo) and drifts over time.

We needed a repeatable, auditable path from a Testiny case to a committed pytest suite that:

1. Does not add a large new runtime dependency to the test framework.
2. Keeps the framework's layering invariant intact: `core/` must not import AI or LLM libraries.
3. Produces a deterministic, committed test — not an agentic test runner that calls an LLM at
   test-execution time.
4. Reuses the existing Page Object and skill infrastructure rather than duplicating it.
5. Is traceably linked from the committed test back to the Testiny source case.

## Decision

Implement a two-stage **authoring-time** pipeline:

### Stage 1 — Pull (`tools/testiny`)

A standalone `tools/` package (`python -m tools.testiny pull`) fetches cases from the Testiny
REST API and normalizes each into a **Markdown + YAML front-matter spec file** under `specs/<app>/`.
The tool is authoring-time tooling only:

- It lives in `tools/`, outside `core/`, and is **not included in the wheel** (`packages` in
  `pyproject.toml` lists only `fixtures`, `tests`, `utils`, `core`, `config`).
- Its only new runtime dependency is `requests`, isolated in a dedicated `[tools]` optional extra
  so the framework's core install stays light.
- `TESTINY_API_KEY` is read from the environment (or a local `.env`); it is never logged — the
  debug path routes through `utils.redact.redact_mapping`, which masks the key.
- The spec format is a strict 1-to-1 projection of the Testiny data model: front-matter fields map
  directly to Testiny REST fields (`id`, `_etag`, `project_id`, `title`, `priority`, plus the
  `cf__app`/`cf__page` custom fields), and the body preserves `precondition_text`, `steps_text`,
  and `expected_result_text` verbatim as Markdown sections. Only `template: "TEXT"` cases are
  supported.

### Stage 2 — Generate (`testopus-nl-test` skill)

A Claude Code skill (`.claude/skills/testopus-nl-test/SKILL.md`) reads a spec file **and** the
Page Object it references, grounds every locator/method/`TEXT_*` constant on the real file (never
inventing selectors), and produces a class-based pytest suite following the `testopus-web-test`
conventions.

The skill is **Claude Code as the generator**: it uses the same `code-reviewer` → human → `testopus-run`
gate that governs every other code change. No `anthropic` SDK is added; the Anthropic SDK remains
a roadmap item (CLAUDE.md "Toward an AI-Driven QA Framework") for when the first **runtime** AI
feature lands. The model is in the authoring loop only — the committed output is plain Pytest that
runs deterministically forever.

### Invariant

**The LLM is in the authoring loop only; it never owns the test verdict.** The deterministic test
path (Selenium → Page Object → pytest) runs with no AI dependency at all.

## Consequences

- **New files:** `tools/testiny/{__main__,cli,client,normalize}.py`, `specs/<app>/tc-*.md`,
  `.claude/skills/testopus-nl-test/SKILL.md`.
- **Dependency change:** `requests>=2.34.2` added to `[project.optional-dependencies].tools`.
  The `test` Hatch env gains `features = ["test", "tools"]` so the tool's tests (which import
  `tools.testiny`) have the dependency available.
- **Layering guard unchanged:** `tests/internal_tests/test_layering.py` scans only `core/`;
  `tools/` is authoring-time infrastructure, outside the guarded perimeter.
- **Traceability:** every generated suite carries a docstring linking it to its spec file and
  Testiny case id, and the spec front-matter carries `source: testiny` + `pulled_at` + `testiny_etag`
  for provenance.
- **Custom-field dependency:** `cf__app` and `cf__page` are tenant-specific Testiny field keys.
  Teams must confirm their own field names and set `--app-field`/`--page-field` accordingly.

## Rejected alternatives

**An `anthropic`-SDK generation pipeline now** — would add a heavy optional dep, require an
`ANTHROPIC_API_KEY` for authoring, and risk the layering invariant if any AI import leaked into
`core/`. The SDK is already called out in CLAUDE.md as a roadmap item tied to the *first runtime AI
feature*. Claude Code (already the development environment) is a simpler, zero-dep generator for
the authoring step.

**BDD / Gherkin / pytest-bdd** — a third convention layer (Testiny → Gherkin → step definitions →
test) with its own learning curve and maintenance surface. The existing class-based pytest
convention is already the project standard; the spec → test mapping is a strict projection,
not a behavior-framework with ambiguous step matching.

**Runtime / agentic execution** — having the LLM select and run tests at runtime violates the
"AI never owns the verdict" invariant and requires always-on API access in CI. Deterministic
committed tests are the correct model.

**Placing the tool in `core/` or `utils/`** — `core/` is the guarded, wheel-shipped framework;
putting authoring tooling there blurs the boundary and would pull `requests` into the core
install. `utils/` holds thin framework helpers (`helpers.py`, `redact.py`); a multi-module CLI
package belongs in a top-level `tools/` namespace.
