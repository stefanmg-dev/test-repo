#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def request(base_url, path, *, headers=None, timeout=10):
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    request_object = urllib.request.Request(
        url,
        headers={"Accept": "application/json", **(headers or {})},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request_object, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body) if body else None
        except json.JSONDecodeError:
            payload = None
        return exc.code, payload


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def build_auth_headers(api_key=None, bearer_token=None):
    require(
        not (api_key and bearer_token),
        "Use either SMOKE_API_KEY or SMOKE_BEARER_TOKEN, not both",
    )
    if api_key:
        return {"X-API-Key": api_key}
    if bearer_token:
        return {"Authorization": f"Bearer {bearer_token}"}
    return {}


def run_smoke(base_url, *, api_key=None, bearer_token=None, timeout=10):
    require(base_url.startswith("https://"), "SMOKE_BASE_URL must use HTTPS")
    headers = build_auth_headers(api_key, bearer_token)

    health_status, health = request(base_url, "/health", timeout=timeout)
    require(health_status == 200, "/health did not return HTTP 200")
    require(health == {"status": "ok"}, "/health response contract mismatch")
    print("PASS /health")

    ready_status, ready = request(base_url, "/ready", timeout=timeout)
    require(ready_status == 200, "/ready did not return HTTP 200")
    require(ready.get("status") == "ready", "/ready status is not ready")
    require(ready.get("database") == "connected", "/ready database is not connected")
    require(ready.get("migrations") == "current", "/ready migrations are not current")
    require(bool(ready.get("revision")), "/ready revision is missing")
    print("PASS /ready")

    auth_status, auth = request(base_url, "/api/v1/auth/config", timeout=timeout)
    require(auth_status == 200, "/api/v1/auth/config did not return HTTP 200")
    require(isinstance(auth, dict), "auth config is not a JSON object")
    require(isinstance(auth.get("enabled"), bool), "auth config enabled flag is missing")
    print("PASS /api/v1/auth/config")

    history_status, history = request(
        base_url,
        "/api/v1/processing-runs?offset=0&limit=1",
        headers=headers,
        timeout=timeout,
    )
    if headers:
        require(history_status == 200, "authenticated processing history did not return HTTP 200")
        require(isinstance(history, dict), "processing history is not a JSON object")
        require(isinstance(history.get("items"), list), "processing history items are missing")
        print("PASS authenticated processing history")
    else:
        require(history_status == 401, "protected processing history did not return HTTP 401")
        print("PASS anonymous access rejected")

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only production deployment smoke test")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key")
    parser.add_argument("--bearer-token")
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        return run_smoke(
            args.base_url,
            api_key=args.api_key,
            bearer_token=args.bearer_token,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
