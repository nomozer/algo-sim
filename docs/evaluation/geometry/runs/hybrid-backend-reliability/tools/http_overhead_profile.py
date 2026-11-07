"""Where the fixed per-request cost of `POST /api/analyze` goes (cProfile, staging-replay, offline).

Posts N cache HITs of one served text (no route work at all), then N cache MISSes of distinct served texts, under
cProfile, and prints the top cumulative functions plus the number of SQL COMMITs per request (SQLAlchemy event).
Usage (from backend/): PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this> <fresh out.txt> [N]
"""
from __future__ import annotations

import cProfile
import io
import pstats
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5] / "backend"))
import http_e2e_replay as H  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    corpus = H.collect()
    client = H.make_client(corpus)
    from sqlalchemy import event

    from app.persistence import db as db_module

    commits = [0]
    event.listen(db_module.engine, "commit", lambda conn: commits.__setitem__(0, commits[0] + 1))
    served = []
    for t in corpus:
        r = client.post("/api/analyze", json={"input": {"type": "text", "content": t}})
        if (r.json().get("route_d") or {}).get("status") == "SERVED":
            served.append(t)
        if len(served) > n:
            break
    lines = []
    for label, texts in (("HIT", [served[0]] * n), ("MISS", None)):
        if texts is None:
            client = H.make_client(corpus)        # fresh DB: the first post of each text misses
            from app.persistence import db as db2
            event.listen(db2.engine, "commit", lambda conn: commits.__setitem__(0, commits[0] + 1))
            texts = served[1:n + 1]
        commits[0] = 0
        prof = cProfile.Profile()
        t0 = time.perf_counter()
        prof.enable()
        for t in texts:
            client.post("/api/analyze", json={"input": {"type": "text", "content": t}})
        prof.disable()
        wall = (time.perf_counter() - t0) / len(texts)
        s = io.StringIO()
        pstats.Stats(prof, stream=s).sort_stats("cumulative").print_stats(45)
        lines.append(f"===== {label}: {len(texts)} requests, {wall * 1000:.1f} ms/request under cProfile, "
                     f"{commits[0] / len(texts):.2f} SQL commits/request\n{s.getvalue()}")
    with out.open("x", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(line.split("\n")[0] for line in lines))


if __name__ == "__main__":
    main()
