"""Check a running same-origin Compose deployment without changing data.

Run from the repository root with the same private --env-file used by Compose.
Requires Python 3.10+ and Docker CLI. No third-party Python packages required.
"""

import argparse
import json
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SECURITY_HEADERS = ("Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options")


def request(base, path, method="GET", body=None):
    try:
        response = urlopen(Request(base + path, data=body, method=method), timeout=15)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def check(base, project, env_file, overlays=()):
    checks = []
    status, headers, index = request(base, "/")
    assert status == 200 and b'<div id="root">' in index, "Frontend shell unavailable"
    assert all(headers.get(name) for name in SECURITY_HEADERS), "Missing security headers"
    assert "no-cache" in headers.get("Cache-Control", ""), "HTML shell must revalidate"
    status, deep_headers, deep = request(base, "/transfer-lab")
    assert status == 200 and deep == index, "SPA deep links do not return the application shell"
    assert all(deep_headers.get(name) for name in SECURITY_HEADERS)
    checks.append("frontend shell, SPA deep link, revalidation and security headers")
    status, theme_headers, _ = request(base, "/theme-init.js")
    assert status == 200 and "no-cache" in theme_headers.get("Cache-Control", "")
    checks.append("theme initializer revalidation")
    status, _, health = request(base, "/healthz")
    assert status == 200 and json.loads(health)["status"] == "ready", "Frontend readiness failed"
    checks.append("frontend readiness proxy")
    status, api_headers, quality = request(base, "/api/data-quality")
    assert status == 200 and "warnings" in json.loads(quality), "Data-quality API unavailable"
    assert api_headers.get("Cache-Control") == "no-store" and api_headers.get("X-Request-ID")
    checks.append("API proxy, no-store responses and request references")
    status, disabled_headers, _ = request(
        base, "/api/fixtures/1/sync-player-stats", method="POST", body=b""
    )
    assert status == 404 and disabled_headers.get("X-Request-ID")
    checks.append("public fixture-stat sync route disabled with request reference")
    asset = re.search(rb'(?:src|href)="(/assets/[^\"]+)"', index)
    assert asset, "No built content-hashed asset found"
    status, asset_headers, _ = request(base, asset[1].decode())
    assert status == 200 and "max-age=31536000" in asset_headers.get("Cache-Control", "")
    assert all(asset_headers.get(name) for name in SECURITY_HEADERS)
    checks.append("hashed asset caching retains security headers")
    status, _, _ = request(base, "/api/squads/validate", method="POST", body=b"x" * 65537)
    assert status == 413, "Oversized requests were not rejected"
    checks.append("64KB request-size boundary")
    probe = """
import json
from urllib.error import HTTPError
from urllib.request import Request,urlopen
checks=[]
for path,method,expected in [('/health/live','GET',200),('/health/ready','GET',200),
('/docs','GET',404),('/openapi.json','GET',404),('/sync/teams','POST',404),
('/sync/players','POST',404),('/sync/fixtures','POST',404),('/sync/player-fixture-stats/batch','POST',404),
('/api/fixtures/1/sync-player-stats','POST',404)]:
    try: r=urlopen(Request('http://127.0.0.1:8000'+path,method=method),timeout=10)
    except HTTPError as error: r=error
    assert r.status==expected,(path,r.status,expected)
    r.close()
    checks.append(path)
try: r=urlopen(Request('http://127.0.0.1:8000/health/live',headers={'Host':'untrusted.invalid'}),timeout=10)
except HTTPError as error: r=error
assert r.status==400,r.status
r.close()
print(json.dumps(checks))
"""
    compose = ["docker", "compose", "--env-file", env_file, "-f", "compose.yml"]
    for overlay in overlays:
        compose.extend(["-f", overlay])
    subprocess.run(
        compose
        + [
            "-p",
            project,
            "exec",
            "-T",
            "backend",
            "python",
            "-c",
            probe,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    checks.append(
        "backend liveness/readiness, production docs disabled, all admin routes disabled, host rejection"
    )
    print(json.dumps({"base_url": base, "passed": checks}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--project", default="fpl-forge")
    parser.add_argument(
        "--env-file",
        required=True,
        help="Private Compose variable file; contents are never printed",
    )
    parser.add_argument(
        "--compose-file",
        action="append",
        default=[],
        help="Additional Compose overlay after compose.yml; repeat for multiple overlays",
    )
    args = parser.parse_args()
    check(args.base_url.rstrip("/"), args.project, args.env_file, args.compose_file)
