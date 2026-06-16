import os
import subprocess


def resolve_branch() -> str:
    """Resolve the current git branch from CI env vars, falling back to git.

    Order: GITHUB_HEAD_REF (pull requests) → GITHUB_REF (pushes) → `git rev-parse`.

    :return: The branch name, or "unknown" if it cannot be determined.
    """
    branch = os.environ.get("GITHUB_HEAD_REF", "")  # pull requests
    if not branch:
        ref = os.environ.get("GITHUB_REF", "")  # direct pushes
        if ref.startswith("refs/heads/"):
            branch = ref.replace("refs/heads/", "")
    if not branch:
        try:
            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8")
                .strip()
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            branch = "unknown"
    return branch or "unknown"


def resolve_provenance() -> dict:
    """Return CI run provenance from the environment (fail-open; empty strings if absent).

    Gives test telemetry a stable join key to a commit and CI run.

    :return: dict with keys commit, run_id, run_attempt, ci_url.
    """
    commit = os.environ.get("GITHUB_SHA", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    ci_url = f"{server}/{repo}/actions/runs/{run_id}" if (repo and run_id) else ""
    return {
        "commit": commit,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "ci_url": ci_url,
    }
