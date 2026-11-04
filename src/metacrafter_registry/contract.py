"""Check the public URL contract against a deployed (or locally served) site.

The contract is what metacrafter and stored catalog metadata depend on:
``/datatype/<id>``, ``/datatype/<id>.json``, ``/registry.json``,
``/tools.json``, ``/tool/<id>``, ``/tool``.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class CheckResult:
    path: str
    ok: bool
    detail: str

    def __str__(self) -> str:
        return f"{'PASS' if self.ok else 'FAIL'} {self.path}: {self.detail}"


def _fetch(url: str, timeout: float) -> tuple[int, str, bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "metacrafter-registry-contract"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return (
                response.status,
                response.headers.get("Content-Type", ""),
                response.read(),
                response.geturl(),
            )
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read(), url


def _html_mentions(token: str) -> Callable[[bytes], str | None]:
    def check(body: bytes) -> str | None:
        return None if token.encode() in body else f"HTML does not mention '{token}'"

    return check


def _json_check(predicate: Callable[[object], bool], what: str) -> Callable[[bytes], str | None]:
    def check(body: bytes) -> str | None:
        try:
            data = json.loads(body)
        except ValueError as exc:
            return f"invalid JSON: {exc}"
        return None if predicate(data) else f"JSON check failed: {what}"

    return check


CHECKS: list[tuple[str, str, Callable[[bytes], str | None]]] = [
    ("/", "text/html", _html_mentions("Metacrafter Registry")),
    ("/datatype/", "text/html", _html_mentions("/datatype/email")),
    ("/datatype/email", "text/html", _html_mentions("email")),
    (
        "/api/v1/datatypes/email.json",
        "application/json",
        _json_check(
            lambda d: d.get("id") == "email" and d.get("kind") == "datatype",
            "id == email, kind == datatype",
        ),
    ),
    (
        "/api/v1/openapi.json",
        "application/json",
        _json_check(lambda d: str(d.get("openapi", "")).startswith("3.1"), "OpenAPI 3.1"),
    ),
    ("/sitemap.xml", "xml", _html_mentions("/datatype/email")),
    ("/llms.txt", "text/plain", _html_mentions("# Metacrafter Registry")),
    ("/identify", "text/html", _html_mentions("identify-form")),
    (
        "/api/v1/coverage.json",
        "application/json",
        _json_check(lambda d: "orphan_rule_keys" in d, "coverage report"),
    ),
    ("/datatype/email.md", "text/markdown", _html_mentions('id: "email"')),
    (
        "/datatype/email.json",
        "application/json",
        _json_check(
            lambda d: (
                d.get("id") == "email"
                and d.get("type") == "datatype"
                and isinstance(d.get("is_pii"), bool)
            ),
            "id == email, type == datatype, is_pii is boolean",
        ),
    ),
    (
        "/registry.json",
        "application/json",
        _json_check(
            lambda d: isinstance(d, dict) and "email" in d and len(d) > 500,
            "object keyed by id with > 500 records incl. email",
        ),
    ),
    (
        "/tools.json",
        "application/json",
        _json_check(lambda d: isinstance(d, dict) and "presidio" in d, "object with presidio"),
    ),
    ("/tool/presidio", "text/html", _html_mentions("presidio")),
    (
        "/tool/presidio.json",
        "application/json",
        _json_check(lambda d: d.get("id") == "presidio", "id == presidio"),
    ),
    ("/tool", "text/html", _html_mentions("presidio")),
    (
        "/api/v1/index.json",
        "application/json",
        _json_check(lambda d: "datatype_url_template" in d, "manifest has datatype_url_template"),
    ),
]


def check_contract(
    base_url: str,
    *,
    expect_sha: str | None = None,
    timeout: float = 20.0,
    retries: int = 0,
    retry_delay: float = 10.0,
) -> list[CheckResult]:
    """Run all contract checks; retry the whole set to absorb CDN propagation."""
    base = base_url.rstrip("/")
    for attempt in range(retries + 1):
        results = []
        for path, expected_type, body_check in CHECKS:
            try:
                status, ctype, body, final_url = _fetch(base + path, timeout)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                results.append(CheckResult(path, False, f"request failed: {exc}"))
                continue
            problems = []
            if status != 200:
                problems.append(f"status {status}")
            if expected_type not in ctype:
                problems.append(f"content-type '{ctype}' (expected {expected_type})")
            if status == 200:
                problem = body_check(body)
                if problem:
                    problems.append(problem)
            detail = "; ".join(problems) if problems else f"200 {ctype}"
            if final_url != base + path and not problems:
                detail += f" (via {final_url})"
            results.append(CheckResult(path, not problems, detail))
        if expect_sha:
            try:
                _, _, body, _ = _fetch(base + "/api/v1/index.json", timeout)
                deployed = json.loads(body).get("git_sha")
            except (ValueError, urllib.error.URLError, OSError) as exc:
                deployed = f"unavailable ({exc})"
            results.append(
                CheckResult(
                    "/api/v1/index.json#git_sha",
                    deployed == expect_sha,
                    f"deployed {deployed}, expected {expect_sha}",
                )
            )
        if all(r.ok for r in results) or attempt == retries:
            return results
        time.sleep(retry_delay)
    return results
