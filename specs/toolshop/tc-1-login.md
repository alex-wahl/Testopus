---
testiny_id: 1
title: Login rejects invalid credentials
app: toolshop
page: login
severity: critical
status: draft
source: testiny
pulled_at: 2026-06-16T10:30:00Z
---

# Login rejects invalid credentials

## Precondition

The user is on the Toolshop login page (`LoginPage`, path `auth/login`).
No active session exists.

## Steps

1. Navigate to the login page (`f"{BASE_URL}/{LoginPage.PAGE_URL}"`).
2. Enter an e-mail address that does not match any account (e.g. `nobody@example.com`).
3. Enter any password (e.g. `wrong-password`).
4. Submit the login form by clicking the login button.

## Expected Result

An error message containing "Invalid email or password"
(`LoginPage.TEXT_LOGIN_ERROR_KEY_PHRASE`) is visible on the page
(locator: `LoginPage.LOGIN_ERROR`). The user remains on the login page — the URL does
not change away from `auth/login`.
