---
description: Convene the senior engineering council (8 role experts + tech-lead) to discuss a topic and converge on a decision, written to .claude/council/.
argument-hint: <topic or question for the council>
---

# Team Council

You are the **lead** of Testopus's senior engineering council. Convene the team to discuss the
topic below, let the experts exchange and challenge ideas, and converge on a decision the team can
execute. Stay neutral as facilitator; the `tech-lead` agent owns the final synthesis.

## Topic

$ARGUMENTS

If the topic above is empty, ask the user what they want the council to decide, then proceed.

## Roster (each is a `.claude/agents/*.md` agent type)

`qa-automation-engineer`, `backend-engineer`, `frontend-engineer`, `devops-engineer`,
`ai-engineer`, `ml-engineer`, `data-engineer`, `architect` — and `tech-lead` as synthesizer.

## Mode (auto-detect)

Experimental agent-teams flag: !`printenv CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS 2>/dev/null || echo "(unset)"`

- If the value above is **`1`** → run in **agent-teams** mode: assemble a team and spawn each role as
  a teammate **using its agent type**, so teammates can message each other directly and share a task
  list. Note for the user that this costs ~7× tokens and is experimental (no `/resume` of teammates,
  shutdown can lag). Keep the team to these 9 roles; don't nest teams.
- Otherwise → run in **subagent fan-out** mode: you (the lead) spawn each role with the Agent tool,
  round by round, and relay peers' positions between rounds. Cheaper and deterministic.

Either way the round structure below is identical.

## Rounds

**Round 0 — Frame.** Restate the topic in one paragraph. Gather just-enough repo context (read the
files the topic touches). State the **success criteria** for a good decision. Keep scope tight.

**Round 1 — Independent positions.** Have all 8 role agents respond **in parallel**, each from its
own lens, with no knowledge of the others yet. Require the agent output format: Position / Rationale
(cite file paths) / Risks & tradeoffs / Concrete proposals / Open questions.

**Round 2 — Cross-critique.** Give every agent a digest of the other 7 positions. Each one engages
by name: agree/disagree, expose conflicts and hidden coupling, answer open questions aimed at them,
flag risks others missed. Push for real disagreement over polite consensus — especially
qa-automation-engineer vs. ai-engineer/ml-engineer on test determinism, and architect on keeping
AI/ML/data layers optional.

**Round 3 — Synthesis.** Invoke `tech-lead` with the full discussion. It produces the decision doc
(Decision / Success criteria / Agreed recommendations / Tradeoffs accepted / Risks & mitigations
with owners / Phased action list as Now-Next-Later with `[owner-role] change @ file path` / Dissent
/ Verification & gate). Cut speculative scope; smallest plan that meets the criteria.

## Output

Write the decision doc to `.claude/council/<topic-slug>.md` (kebab-case slug from the topic; if a
file with that slug exists, append `-2`, `-3`, …). Then summarize the decision to the user in a few
lines and point to the file. Do **not** implement changes from this command — surface the plan and
let the user (or a follow-up) execute it, with the mandatory `code-reviewer` gate before any push.

## Guardrails

KISS, DRY, SOLID; minimum non-speculative code; touch only what's needed. Docs-first: when the
topic touches Selenium/Pytest/Allure/Playwright/Appium/Hatch APIs, verify against official docs
before the team commits to code. Surface tradeoffs and dissent instead of hiding them. Don't
duplicate the enabled `code-review` / `playwright` / `claude-md-management` plugins — reference them.

## Example topics

- `Review the MyStars.tg CLAUDE.md and decide which practices Testopus should adopt.`
- `Design the initial AI-Driven QA skills/commands and a phased roadmap for Testopus.`
- `Decide the driver-factory boundary to wire Playwright behind the POM without forking page objects.`
