# Audit implementation status

> **Snapshot:** `docs/audit/` vs the code on branch **`fix/antipatterns-audit`** (2026-06-16).
> **Legend:** ✅ done · ⚠️ partial / manual step pending · ⬜ pending (roadmap).
> **Source of truth** is the branch diff — `git diff main...fix/antipatterns-audit` once committed (work
> is currently uncommitted; use `git status`). This file is the human-readable view.
> **Companion docs:** [antipatterns.md](antipatterns.md) · [roadmap.md](roadmap.md) ·
> [best-practices.md](best-practices.md).

## Headline

- **Antipatterns — 26 / 26 fixed in code** (2 carry a manual/CI residual: AP-01, AP-08; 1 partial: AP-14).
- **Roadmap — Now: all ✅ · Next: ✅ except telemetry pipeline + flaky-triage · Later: ⬜ (intentional).**
- **Best practices — all now-actionable items adopted; the AI/ML section stays roadmap.**
- **Verification:** `ruff` / `black` / `mypy` pass; 36 internal tests pass; 48 tests collect. Live gasag
  UI suite (`hatch run ui:web`) not run locally (no browser) → must pass in CI before merge.
- **Historical note:** The gasag suite was later replaced by the public Toolshop demo target;
  see ADR-0003.

## Antipatterns ([antipatterns.md](antipatterns.md)) — 26/26

| ID | Status | Note |
|----|--------|------|
| AP-01 credentials committed/printed | ✅ ⚠️ | code: env interpolation + placeholders + prints removed + `override.yaml` untracked. **Manual: rotate the live GASAG credential.** |
| AP-02 `@retry` masks failures | ✅ | default `(WebDriverException,)` + fail-open `retry_event`. |
| AP-03 `merge_configs` aliasing | ✅ | `copy.deepcopy` + self-test. |
| AP-04 no CI lint/type/collect gate | ✅ | advisory `lint` job added. |
| AP-05 actions on mutable tags | ✅ | SHA-pinned. |
| AP-06 mislabeled redirect test | ✅ | → `test_login_page_loads` (asserts form). |
| AP-07 `js_input` f-string | ✅ | parameterized `arguments[1]`. |
| AP-08 driver hardcoded / no seam | ✅ ⚠️ | `core/drivers/` Protocol seam + ADR-0001. **CI: live `ui:web` regression must pass.** |
| AP-09 dead Allure markers | ✅ | registered + `--strict-markers` + suite decorated. |
| AP-10 sleep-loop polling | ✅ | `WebDriverWait(ignored_exceptions=…)`. |
| AP-11 dead `--framework/--ai/--config` | ✅ | `--framework` wired (fail-loud), `--config` threaded; `--ai` reserved. |
| AP-12 dead/invalid locators | ✅ | removed + valid CSS + POM method. |
| AP-13 inline selectors in tests | ✅ | moved into `LoginPage.get_social_legal_text`. |
| AP-14 Docker unpinned | ⚠️ | base image digest-pinned; exact Chromium apt-pin deferred (documented). |
| AP-15 cache key never hits | ✅ | `hashFiles(Dockerfile, pyproject.toml)`. |
| AP-16 unused heavy deps | ✅ | Appium/Playwright → `[frameworks]`, requests/Faker → `[test]`, `responses` removed. |
| AP-17 `override.yaml` tracked | ✅ | `git rm --cached` + gitignored. |
| AP-18 no telemetry provenance | ✅ | `Commit/RunId/RunAttempt/CiUrl` in `environment.properties`. |
| AP-19 PII in screenshots | ✅ | password inputs blanked before capture. |
| AP-20 timestamp regex on JSON | ✅ | scoped away from history/widgets + literal ISO separators. |
| AP-21 duplicated `sys.path.insert` | ✅ | removed both. |
| AP-22 `DEFAULT_TIMEOUT`/magic 3 | ✅ | unified on `DEFAULT_TIMEOUT`. |
| AP-23 near-empty `internal_tests/` | ✅ | config/helpers/redact/drivers/retry/layering/schema suites. |
| AP-24 duplicated branch detection | ✅ | one `utils/ci_env.resolve_branch()`. |
| AP-25 docs/reality drift | ✅ | description fixed; `api` script/option pruned; skill `src/` wording refreshed. |
| AP-26 `chmod -R 777` | ✅ | host-UID via compose `user:`. |

## Roadmap ([roadmap.md](roadmap.md))

**Now — ✅ all done:** secret remediation (⚠️ manual rotation) · CI quality gate · SHA-pin actions ·
`@retry` narrowing + `retry_event` · `merge_configs` deep-merge + internal tests · Allure markers ·
quick correctness sweep.

**Next:**

| Item | Status |
|------|--------|
| Driver-factory seam + ADR-0001 | ✅ (⚠️ live `ui:web` regression gate) |
| One telemetry pipeline (`core/telemetry/`) | ⬜ pending (prereqs AP-18/AP-20 ✅) |
| Wire `--framework` / `--config` | ✅ ( `--ai` ⬜ reserved) |
| Dependency & docs honesty pass | ✅ |
| `LOCATOR_PRIORITY` ladder | ✅ |
| `redact()` + screenshot scrub | ✅ |
| flaky-triage v1 | ⬜ pending (gated on telemetry) |
| Docker reproducibility | ⚠️ partial (Chromium apt-pin deferred) |

**Later — ⬜ all pending (intentional):** ml clustering + flaky score · ai LLM labeling / self-healing /
visual diff · supervised classifier · `customize_allure_report.py` refactor · `tests/api_tests/` build
(its dangling references were ✅ pruned).

## Best practices ([best-practices.md](best-practices.md))

| Area | Status |
|------|--------|
| Testing & Pytest (waits, parameterized JS, markers, `@retry`, stable substrings, TDD) | ✅ |
| Locators & frontend (priority ladder) | ✅ — `data-testid` request to app team is ⚠️ external |
| CI / DevOps (collect+lint, SHA-pin, secrets, cache keys, non-root UID) | ✅ — base-image/Chromium pin ⚠️ partial |
| Architecture (driver interface, ADRs, optional-layer extras + import-guard, one import path, fail-loud flags) | ✅ |
| Config & backend (deep merge + Pydantic validation) | ✅ |
| AI / ML / data (anthropic client + tiering, token budgeting, eval sets, perceptual diff, telemetry pipeline) | ⬜ roadmap — no AI/ML feature exists to attach to yet |

## Remaining work (what's left to build)

1. **AI/ML layer (roadmap):** telemetry pipeline → flaky-triage v1 → ml clustering / ai labeling /
   self-healing / visual diff → supervised classifier. Sequenced and gated in [roadmap.md](roadmap.md).
2. **Deferred maintenance:** refactor `customize_allure_report.py`; build `tests/api_tests/` when needed.
3. **Manual / CI (not code):** rotate the live GASAG credential; run the live `hatch run ui:web`
   regression in CI; (optionally) exact-pin Chromium via a Debian snapshot source.

## How to verify

```bash
# everything implemented for the audit lives on this branch:
git diff main...fix/antipatterns-audit            # full change set (after commit)
git status --short                                # while still uncommitted

# re-run the local gates:
hatch run lint && hatch run typecheck             # ruff + mypy
hatch run test:internal                           # 36 pure-logic tests
pytest --collect-only tests                       # 48 tests collect under --strict-markers
```
