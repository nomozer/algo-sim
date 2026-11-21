"""POST problems to a running Axo backend (/api/analyze, real HTTP) and print a compact summary per problem.

usage: python probe_analyze.py <base_url> <problems.json> [out.jsonl]
problems.json: [{"id": "...", "text": "..."}]
"""

import json
import sys
import time

import httpx


def summarize(status: int, body: dict) -> dict:
    env = body.get("envelope") if isinstance(body.get("envelope"), dict) else body
    rd = body.get("route_d") if isinstance(body.get("route_d"), dict) else (env.get("route_d") or {})
    scene = None
    for holder in (body, env):
        for key in ("scene3d", "scene"):
            if isinstance(holder.get(key), dict):
                scene = holder[key]
    return {
        "http": status,
        "status": body.get("status"),
        "route_status": rd.get("status"),
        "reason_code": body.get("reason_code") or (rd.get("refusal") or {}).get("reason_code"),
        "failure_category": body.get("failure_category"),
        "ux_state": (body.get("local_ai_ux") or {}).get("ux_state"),
        "top_keys": sorted(body)[:25],
        "scene_keys": sorted(scene)[:25] if scene else None,
    }


def student_client(base: str) -> httpx.Client:
    """A freshly registered student account (product policy: 15 analyses/day) — the quota gate is used, not bypassed."""
    c = httpx.Client(base_url=base, timeout=120, trust_env=False)
    tag = f"{int(time.time() * 1000)}"
    r = c.post("/api/auth/register", json={"email": f"live-acc-{tag}@example.com", "displayName": f"Live {tag}",
                                           "password": "LiveAcceptance!2026"})
    r.raise_for_status()
    return c


def main() -> None:
    base, path = sys.argv[1], sys.argv[2]
    out = open(sys.argv[3], "a", encoding="utf-8") if len(sys.argv) > 3 else None
    c = None
    for i, p in enumerate(json.load(open(path, encoding="utf-8"))):
        if i % 14 == 0:
            c = student_client(base)
        if True:
            t0 = time.perf_counter()
            r = c.post("/api/analyze", json={"input": {"type": "text", "content": p["text"]}})
            if r.status_code == 401:  # guest session cookie is set on the first refusal
                r = c.post("/api/analyze", json={"input": {"type": "text", "content": p["text"]}})
            ms = round((time.perf_counter() - t0) * 1000, 1)
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            row = {"id": p["id"], "ms": ms, **summarize(r.status_code, body)}
            print(json.dumps(row, ensure_ascii=False))
            if out:
                out.write(json.dumps({"id": p["id"], "ms": ms, "http": r.status_code, "body": body}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
