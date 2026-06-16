"""CLI for pulling Testiny test cases into spec files (``python -m tools.testiny``).

Authoring-time tooling — NOT part of the runtime test path. Fetches cases via the
Testiny REST API, normalizes each into the Markdown + front-matter spec format, and
writes them under ``specs/<app>/``. The API key comes from ``TESTINY_API_KEY``
(environment or a local ``.env``) and is never logged. After pulling, generate the
pytest suite from a spec with the ``testopus-nl-test`` skill (which grounds the test
on the real Page Object).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from tools.testiny.client import DEFAULT_BASE_URL, TestinyClient
from tools.testiny.normalize import (
    SpecValidationError,
    resolve_app,
    spec_filename,
    testiny_case_to_spec,
)
from utils.redact import redact_mapping

logger = logging.getLogger("tools.testiny")

API_KEY_ENV = "TESTINY_API_KEY"


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m tools.testiny",
        description="Pull Testiny test cases into local Markdown spec files.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    pull = subcommands.add_parser(
        "pull", help="Fetch test case(s) and write specs/<app>/tc-*.md"
    )
    selector = pull.add_mutually_exclusive_group(required=True)
    selector.add_argument("--case-id", help="Comma-separated Testiny test-case id(s).")
    selector.add_argument("--folder", help="Pull every case in a Testiny folder id.")
    selector.add_argument(
        "--query",
        help="Raw Testiny filter as JSON (you scope it; --project-id is ignored).",
    )
    pull.add_argument("--base-url", default=DEFAULT_BASE_URL)
    pull.add_argument(
        "--project-id", help="Testiny project id (scopes --folder / --query)."
    )
    pull.add_argument(
        "--app-field", default="cf__app", help="Custom field holding the app name."
    )
    pull.add_argument(
        "--page-field", default="cf__page", help="Custom field holding the page name."
    )
    pull.add_argument("--default-app", help="App used when --app-field is absent.")
    pull.add_argument("--default-page", help="Page used when --page-field is absent.")
    pull.add_argument(
        "--out", default="specs", help="Output root directory (default: specs/)."
    )
    pull.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging (the key stays masked).",
    )
    return parser


def _as_int(value):
    """Best-effort int coercion; leave non-numeric values untouched."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _fetch_cases(client, args):
    """Resolve the selector flags into a list of Testiny case dicts."""
    if args.case_id:
        ids = [part.strip() for part in args.case_id.split(",") if part.strip()]
        return [client.get_testcase(case_id) for case_id in ids]
    if args.folder:
        filter_obj = {"folder_id": {"op": "eq", "value": _as_int(args.folder)}}
        if args.project_id:
            filter_obj["project_id"] = {"op": "eq", "value": _as_int(args.project_id)}
        return client.find(filter_obj)
    return client.find(json.loads(args.query))


def main(argv=None):
    """Entry point. Returns an exit code (0 ok, 1 fetch error, 2 missing key)."""
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    load_dotenv()
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        logger.error("%s not set — see .env.example", API_KEY_ENV)
        return 2

    # Effective config is safe to log: redact_mapping() masks the api_key value (the
    # "api_key" hint is in utils.redact._SECRET_KEY_HINTS) — one shared helper so
    # secret handling never diverges.
    logger.debug(
        "Testiny pull config: %s",
        redact_mapping(
            {
                "base_url": args.base_url,
                "project_id": args.project_id,
                "api_key": api_key,
                "app_field": args.app_field,
                "page_field": args.page_field,
                "out": args.out,
            }
        ),
    )

    client = TestinyClient(api_key, args.base_url)
    try:
        cases = _fetch_cases(client, args)
    except (requests.RequestException, ValueError) as exc:
        # Surface the failure without leaking the key (it lives in headers, not exc).
        logger.error("Failed to fetch from Testiny: %s", exc)
        return 1

    pulled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_root = Path(args.out)
    written = 0
    for case in cases:
        try:
            spec = testiny_case_to_spec(
                case,
                app_field=args.app_field,
                page_field=args.page_field,
                default_app=args.default_app,
                default_page=args.default_page,
                pulled_at=pulled_at,
            )
        except SpecValidationError as exc:
            logger.warning("Skipping case %s: %s", case.get("id"), exc)
            continue
        app = resolve_app(case, args.app_field, args.default_app)
        destination = out_root / app / spec_filename(case)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(spec, encoding="utf-8")
        written += 1
        logger.info("Wrote %s", destination)

    logger.info("Done: %d spec(s) written under %s/", written, out_root)
    return 0


if __name__ == "__main__":  # pragma: no cover - module-level convenience
    sys.exit(main())
