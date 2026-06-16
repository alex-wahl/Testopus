# Council decision — AI-Driven QA direction & CLAUDE.md adoption

> **Date:** 2026-06-16 · **Convened by:** `/team-council` · **Mode:** subagent fan-out (Round 1
> independent positions → Round 2 cross-critique → Round 3 `tech-lead` synthesis). This run was
> driven by an automated orchestrator, so it took the deterministic subagent-fan-out path even
> though `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set; an **interactive** `/team-council` with the
> flag on uses the experimental agent-teams peer-to-peer mode instead.
> **Participants:** `tech-lead` (synthesis) + `qa-automation-engineer`, `backend-engineer`,
> `frontend-engineer`, `devops-engineer`, `ai-engineer`, `ml-engineer`, `data-engineer`, `architect`.
> **Topic:** G1 — which MyStars.tg CLAUDE.md practices to adopt; G2 — the AI-Driven QA skills/commands
> set + phased roadmap.

---

## Decision

Adopt the drafted `.claude/` toolkit and CLAUDE.md practices, **trimmed to KISS**, and evolve Testopus into an AI-Driven QA framework along a **read-and-recommend-first, never-touch-the-verdict** path. Ship a neutral **driver seam** with Selenium behind it now; build **one telemetry pipeline** before any ML/LLM; make `flaky-triage` the first AI feature. AI/ML are strictly optional layers that depend on `core/`, never the reverse — enforced by a self-test. Effort scales to blast radius: heavyweight gates on `core/` and `main`, light touch elsewhere.

## Success criteria

- The existing **gasag suite passes unchanged** after the driver seam lands (regression gate for the refactor).
- `core/` imports neither `core/ai|ml|telemetry` nor any AI SDK — proven by a green import-guard self-test.
- `@retry` retry-to-pass emits a `retry_event`; `flaky-triage` lists flaky tests (final-pass + ≥1 retry) from telemetry, reading **telemetry, never raw Allure**.
- Committed credential is **rotated**; no secret reaches an Allure attachment (`redact()` runs before attach).
- `hatch run lint/typecheck/format` execute against real packages; advisory lint/secret CI job + pre-commit are green.
- Verdict path is provably AI-free: `fixtures/allure.py::pytest_runtest_makereport:69` still returns pytest's untouched `outcome.get_result()`.

## Agreed recommendations

1. **5-skill foundation** ships as-is; add `LOCATOR_PRIORITY` ladder (data-testid → ARIA role/name → semantic CSS → id → XPath) to `testopus-page-object`.
2. **Driver seam** `core/drivers/{base,factory,selenium}.py`: `BaseDriver`/`ElementHandle` as `@runtime_checkable typing.Protocol`; `ElementHandle` owns resilient click/fill/text/select_option/hover; `execute_script` is a Selenium-only escape hatch (Playwright → `NotImplementedError`).
3. **Telemetry first** — one pipeline `core/telemetry/extract.py` (off hot path, idempotent on `run_id`, fail-open), Pydantic v2 models `core/telemetry/models.py` (`schema_version`, NDJSON) for `run`/`result`/`trend_point`. Source = JUnit `reports/junit/report_*.xml` enriched by Allure; DuckDB queries; `telemetry/trend.ndjson` committed under Pages dir.
4. **ai/ml boundary**: ml = unsupervised TF-IDF/cosine clustering; ai = LLM cluster *labeling* (human-confirmed candidates). Supervised models Later, gated on ≥50–100 labels across ≥2 apps + frozen eval set.
5. **New artifacts**: `ai-eval` skill (precision gate = sole authority promoting a classifier to CI), read-only `testopus-locator-audit`, `.claude/adr/` (ADR-0001 = driver seam), import-guard self-test, `--report` local flag.
6. **Security/hygiene**: rotate creds, `${ENV_VAR}` interpolation, gitignore `override.yaml`, shared `redact()`, fix Hatch scripts, advisory lint/secret CI + pre-commit, drop `langchain`/`pydantic-ai`/`pyviztest`.

## Tradeoffs accepted

- **[architect]** A neutral Protocol seam adds indirection over raw Selenium — accepted to make Playwright/Appium pluggable and AI layers mockable.
- **[qa-automation]** `/code-review` & TDD are proportional, not blanket — accepted; culture is set by the `core/`+`main` gate, not ceremony on docs.
- **[data]** Committing only aggregated `trend_point` (raw rows live in the 90-day artifact) trades deep history for a clean `reporting` branch (`force_orphan`/`keep_files:false`).
- **[ai]** LLM labels are candidates requiring human confirmation — slower labeling, but avoids a circular train/eval set.

## Risks & mitigations

- **AI greens a real bug** (self-healing/healed locator). → **[ai]** Self-healing is authoring-time suggest-only; HARD RULE AI never enters verdict path; fail-open. Owner: ai.
- **Secret leaks into vision-model ingestion.** → **[devops]** `redact()` before every attach; gitleaks pre-commit + CI. Owner: devops.
- **Driver refactor breaks gasag.** → **[qa-automation]** gasag suite green is the gate; migrate JS fallbacks to native handle methods incrementally. Owner: qa-automation.
- **Telemetry on hot path slows tests.** → **[ml]** Extraction post-run, idempotent, fail-open; `on_retry` emit is append-only. Owner: ml.
- **Schema drift in telemetry.** → **[backend]** `schema_version` on every model; readers tolerate unknown fields. Owner: backend.

## Phased action list

### Now
- **[devops]** Rotate the committed credential and replace it with `${ENV_VAR}` interpolation in `load_config` @ `core/config/config_loader.py` / `config/yaml_configs/default.yaml:4-5`; add `override.yaml` to `.gitignore`.
- **[devops]** Fix scripts to `core fixtures utils config tests` @ `pyproject.toml:57-59`; drop `langchain`/`pydantic-ai`/`pyviztest` @ `pyproject.toml`; add advisory (`continue-on-error: true`) lint/type CI job + `.pre-commit-config.yaml` (ruff+black+ruff-format+gitleaks).
- **[backend/architect]** Create `core/drivers/{base,factory,selenium}.py` (Protocols); migrate JS fallbacks @ `core/pom/web/base_page.py:154,211,229` to native handle methods; write ADR-0001 @ `.claude/adr/0001-driver-seam.md`.
- **[qa-automation]** Add import-guard self-test @ `tests/internal_tests/test_layering.py`; confirm gasag suite passes.
- **[ml]** Wire `on_retry` to emit `retry_event` @ `core/pom/web/base_page.py:559-583`.
- **[devops]** Add `redact()` (denylist + email regex) and call before `allure.attach` @ `fixtures/allure.py`.

### Next
- **[backend]** `core/telemetry/{models,extract}.py` (Pydantic v2, NDJSON); commit `trend_point` aggregates under Pages dir; DuckDB query helper.
- **[qa-automation]** `--ai`/`--framework` config wiring mirroring the override pattern @ `core/config/config_loader.py` (`getoption` → resolved flags); add `--report` flag (no `pytest.ini` addopts).
- **[ai]** Ship `flaky-triage` v1 (read-only over telemetry); add `testopus-locator-audit` skill + `LOCATOR_PRIORITY`.
- **[architect]** Add Playwright impl behind the seam (`to_have_screenshot()` for visual).

### Later
- **[ml]** TF-IDF/cosine failure clustering; flip-flop-on-SHA flaky signal.
- **[ai]** LLM cluster labeling + `ai-eval` precision gate; SSIM/pixel visual diff with masks.
- **[ml]** Supervised classifier (gated: ≥50–100 labels, ≥2 apps, frozen eval, baseline); Appium behind the seam.

## Dissent

**[qa-automation]** held a soft dissent that TDD and `/code-review` should remain **blanket** to set engineering culture. Resolved in favor of **proportional / blast-radius-scaled** gating (mandatory on `core/` + `main`, advisory on docs/skills). Recorded; revisit if quality regresses outside `core/`.

## Verification & gate

1. `hatch run test:internal` — import-guard self-test green (layering invariant holds).
2. `hatch run ui:web` — gasag suite passes unchanged (driver-seam regression gate).
3. `hatch run lint` + `hatch run typecheck` against real packages; gitleaks pre-commit clean; grep confirms no secret in any `reports/` attachment.
4. Confirm `fixtures/allure.py:69` verdict path is untouched and a forced retry-to-pass produces a `retry_event` surfaced by `flaky-triage`.
5. **`/code-review` (high effort) is the mandatory merge gate** for all `core/` changes and any push to `main`; advisory for docs/skills. No classifier enters CI except through the `ai-eval` precision threshold.
