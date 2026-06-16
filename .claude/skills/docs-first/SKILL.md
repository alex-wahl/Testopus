---
name: docs-first
description: This skill should be used BEFORE planning, implementing, changing, or fixing any code that touches Selenium, Pytest, pytest-check, Allure, Playwright, Appium, Hatch, or the Anthropic SDK in Testopus. It enforces a documentation-first discipline — fetch the official docs and verify the current API surface, method signatures, and constraints rather than relying on cached/training knowledge.
version: 0.1.0
---

# Testopus — docs-first lookup (MANDATORY before implementation)

Adopted from the MyStars.tg "Official Documentation MANDATORY lookup" rule. Before you write or
change code against any library below, **fetch the relevant page, read the current API surface, and
only then write code**. Do not rely on cached training knowledge when docs are available — APIs
drift (pinned versions in `pyproject.toml` may differ from your assumptions).

## When this is required

Any plan / analysis / implementation / change / fix involving: web automation (Selenium, Playwright),
test running/fixtures (Pytest, pytest-check), reporting (Allure), mobile (Appium), environments
(Hatch), or AI features (Anthropic SDK). For new/uncertain API calls, fetch first.

## Curated official docs

| Area | Source |
|---|---|
| Selenium (WebDriver, `By`, waits, expected_conditions) | https://www.selenium.dev/documentation/ |
| Pytest (fixtures, marks, CLI, config) | https://docs.pytest.org/en/stable/ |
| pytest-check (soft assertions) | https://github.com/okken/pytest-check |
| Allure (pytest adapter, results schema, CLI) | https://allurereport.org/docs/ |
| Playwright for Python | https://playwright.dev/python/docs/intro |
| Appium | https://appium.io/docs/en/latest/ |
| Hatch (envs, scripts, build) | https://hatch.pypa.io/latest/ |
| Anthropic SDK + Claude models (for AI features) | https://docs.claude.com/ |

## Procedure

1. Identify the library and its version constraint in `pyproject.toml` (the single source of truth).
2. Fetch the matching doc page (use WebFetch/WebSearch); confirm method signatures, parameters,
   return types, and constraints for the version in use.
3. Note any deprecations or version-specific behavior in your plan or PR description.
4. Then implement, preferring the framework's existing helpers (e.g. BasePage waits) over raw API
   calls. For AI features, add the official `anthropic` SDK + latest Claude models (Opus 4.8 /
   Sonnet 4.6 / Haiku 4.5) when the first AI feature lands (`pydantic-ai` / `langchain` were removed
   as unused).

## Why

Cheaper than debugging a wrong assumption. The cost of one doc fetch is far less than shipping code
against an API that changed — and it keeps the framework's behavior aligned with what the libraries
actually guarantee.
