---
name: flaky-triage
description: This skill should be used when the user wants to diagnose flaky or failing Testopus tests, analyze an Allure result/trend set, or get root-cause classification and concrete fix proposals for red/unstable tests (e.g. "why is this test flaky", "triage the last allure run", "these tests keep failing intermittently"). It reads existing Allure JSON results, trend history, and failure screenshots — no new dependencies.
version: 0.1.0
---

# Testopus — AI-driven flaky / failure triage

The framework already emits rich failure signal; this skill turns it into a root-cause classification
plus concrete, convention-respecting fixes. It is **read-and-recommend** — it does not rewrite tests
on its own; it proposes diffs for human review (and the `code-reviewer` gate).

**Data prerequisite:** Allure JSON exists only when a run passed `--alluredir` (CI does; locally pass
it explicitly — `pytest.ini` sets no default `addopts`). Genuine flakiness (`retry-to-pass`) is only
observable if `@retry`'s `on_retry` callback records each retry — today `@retry`
(`core/pom/web/base_page.py`) swallows the caught exception, so instrument `on_retry` to emit a
structured `retry_event` before trusting flake counts. See the roadmap in
`.claude/council/ai-driven-qa-and-claude-md-adoption.md`.

## Inputs (read these; don't assume the schema — inspect the actual files)

- **Allure results**: `reports/allure-results/*-result.json` — per-test `name`, `status`
  (`passed`/`failed`/`broken`/`skipped`), `statusDetails.message` + `.trace`, timing (`start`/`stop`),
  `labels`, and `attachments` (failure screenshots). Written only when a run used `--alluredir`.
- **Trend / history**: `reports/allure-results/history/` (CI preserves ~90 days via
  `ci/scripts/customize_allure_report.py`) — pass/fail flip-flops and duration drift over time.
- **Failure screenshots**: attached by `fixtures/allure.py` on test failure (also under
  `reports/screenshots/`). Use them to judge locator vs. app-state failures.
- **The test + page object**: the failing `tests/ui_tests/web/<app>/test_*.py` and its
  `core/pom/web/<app>/*_page.py`.

## Procedure

1. **Gather**: parse the result JSONs for the run; group by test; pull `status`, message/trace, and
   duration. Cross-reference history for flip-flop rate and duration variance.
2. **Classify** each failing/unstable test into one bucket:
   - **locator-stale** — `NoSuchElement`/`Timeout` on a specific locator; screenshot shows the page
     loaded but the element moved/renamed → fix the locator in the page object (prefer stable
     `data-testid`/ARIA/semantic CSS).
   - **timing-flaky** — passes on retry, intermittent `Timeout`, duration spikes → replace implicit
     waits/sleeps with the right BasePage wait (`wait_for_element_visible`/`_clickable`,
     `wait_until_page_is_fully_loaded`, `wait_for_url_change`); tune `@retry` only as a backstop.
   - **app-bug** — consistent failure, screenshot shows a real error/wrong state → it's a found
     defect, not a test problem; report it, don't silence it.
   - **env** — driver/Chrome/network/Docker (`DOCKER_ENV`, `CHROME_BIN`, `CHROMEDRIVER_PATH`),
     auth/credentials → fix the environment, not the test.
3. **Propose fixes** that respect conventions: locators stay class constants; reuse BasePage helpers;
   `@retry(retries=3, delay=2, on_retry=log_retry)` absorbs *genuine* flake only. **Never** propose
   widening tolerances or adding retries to hide a reproducible `app-bug`.
4. **Report** a table: `test | bucket | evidence (message/trace/screenshot) | proposed fix @ file`.
   Flag tests where confidence is low and a human should look.

## Guardrails

A test that's green for the wrong reason is worse than a red one. Distinguish *mitigating* flake
(legitimate waits/retries) from *hiding* a real failure (never). If AI/model assistance is used to
read screenshots or classify, it advises — the verdict stays with the test result and the reviewer.
This skill uses only existing data and the `anthropic` SDK if a model call is wired later; it adds
no new runtime dependency to the suite.
