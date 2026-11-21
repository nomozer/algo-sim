"""Runtime fault scenarios against a RUNNING backend (real llama-server, real GGUF). Problems are NOT from the
acceptance manifest (no cache hits, SLM path forced by wording the deterministic parser leaves to the model).

usage: python runtime_fault_scenarios.py <base_url> <scenario> <out.jsonl>
  scenario: kill      — kill llama-server between two SLM requests (U14)
            saturate  — 8 concurrent SLM requests vs max_queue=4, then one more (U15)
            probe     — health + one deterministic + one SLM request (used for U11/U12/rollback restarts)
"""

import concurrent.futures as cf
import json
import subprocess
import sys
import time

import httpx

DETERMINISTIC = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3a, SA vuông góc với (ABCD), SA = 4a. Tính thể tích khối chóp S.ABCD."
SLM = [f"Cho hình hộp chữ nhật MNPQ.M'N'P'Q' có MN = {k}, MQ = {k + 1}, MM' = {k + 3}. Hãy mô phỏng hình hộp chữ nhật." for k in range(2, 12)]


def client(base):
    c = httpx.Client(base_url=base, timeout=200, trust_env=False)
    t = f"{time.time_ns()}"
    c.post("/api/auth/register", json={"email": f"fault-{t}@example.com", "displayName": "f", "password": "LiveAcceptance!2026"}).raise_for_status()
    return c


def ask(c, text, label):
    t0 = time.perf_counter()
    r = c.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    rd = body.get("route_d") or {}
    return {"label": label, "http": r.status_code, "ms": round((time.perf_counter() - t0) * 1000, 1),
            "route_status": rd.get("status"), "extraction_mode": rd.get("extraction_mode"),
            "reason_code": body.get("reason_code") or (rd.get("refusal") or {}).get("code"),
            "ux_state": (body.get("local_ai_ux") or {}).get("ux_state"), "learner_error": body.get("error"),
            "slm_model": (rd.get("adaptive_telemetry") or {}).get("slm_model_key") or rd.get("local_slm_model_key")}


def llama_pids():
    out = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-Process llama-server -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True).stdout.split()
    return [int(x) for x in out if x.isdigit()]


def main():
    base, scen, outp = sys.argv[1:4]
    rows = []
    if scen == "kill":
        c = client(base)
        rows.append(ask(c, SLM[0], "warm_slm_request"))
        pids = llama_pids()
        for p in pids:
            subprocess.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {p} -Force"], check=False)
        time.sleep(1)
        rows.append({"label": "killed_llama_server", "pids": pids, "alive_after": llama_pids()})
        rows.append(ask(c, SLM[1], "first_slm_request_after_kill"))
        rows.append(ask(c, SLM[2], "second_slm_request_after_kill"))
        rows.append({"label": "llama_server_after", "pids": llama_pids()})
    elif scen == "saturate":
        cs = [client(base) for _ in range(8)]
        t0 = time.perf_counter()
        with cf.ThreadPoolExecutor(8) as ex:
            futs = [ex.submit(ask, cs[i], SLM[2 + i], f"concurrent_{i}") for i in range(8)]
            rows += [f.result() for f in futs]
        rows.append({"label": "burst_wall_ms", "ms": round((time.perf_counter() - t0) * 1000, 1)})
        rows.append(ask(client(base), DETERMINISTIC.replace("3a", "5a"), "deterministic_after_burst"))
        rows.append(ask(client(base), SLM[0].replace("MN = 2", "MN = 7"), "slm_after_burst"))
    elif scen == "probe":
        c = client(base)
        h = c.get("/api/health").json()
        rows.append({"label": "health", **{k: h.get(k) for k in ("hasKey", "routeMode", "localOnlyMode", "localSlmReady", "localSlmModel", "aiAvailable")},
                     "ux_state": (h.get("local_ai_ux") or {}).get("ux_state")})
        rows.append(ask(c, DETERMINISTIC, "deterministic"))
        rows.append(ask(c, SLM[9], "slm"))
    with open(outp, "a", encoding="utf-8") as f:
        for r in rows:
            r["scenario"] = scen
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(json.dumps(r, ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
