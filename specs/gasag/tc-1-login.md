---
# Sample spec checked in as a grounding example (not a live Testiny pull).
# `python -m tools.testiny pull` writes files in exactly this shape; see
# docs/testiny/workflow.md and the testopus-nl-test skill.
testiny_id: 1
project_id: 42
title: Login rejects invalid credentials
app: gasag
page: login
priority: high
severity: critical
status: draft
source: testiny
---

# Login rejects invalid credentials

## Precondition

The user is on the GASAG online-service login page (`LoginPage`).

## Steps

1. Enter an e-mail address and a password that do not match any account.
2. Submit the login form.

## Expected Result

An authentication error is shown (the "no matching login" key phrase) and the user remains
on the login page.
