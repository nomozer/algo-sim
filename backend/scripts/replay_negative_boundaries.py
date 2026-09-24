# -*- coding: utf-8 -*-
"""Replay NGUYÊN BYTE hai ca âm qua ĐÚNG đường sản phẩm, chụp từng biên.

─── VÌ SAO KHÔNG ĐỌC JSON CUỐI RỒI ĐOÁN ─────────────────────────────────────

`n1` giao `stage_reached = null` và `error_code = null`. Nhìn envelope cuối thì
có đúng **một** bit thông tin: *thiếu*. Nó không phân biệt được ba giả thuyết
hoàn toàn khác nhau — tầng phát hiện chưa từng biết mã nào (nhánh A), tầng ấy
biết nhưng biên chuyển kết quả đánh rơi (nhánh B), hay hợp đồng không chở nổi
(nhánh C). Ba nhánh cần ba chỗ sửa khác nhau, nên phải nhìn thấy **giá trị tại
từng biên** chứ không suy ngược từ đầu ra.

Script này chụp bảy biên cho mỗi ca:

    domain → scope → analyze → semantic_program → verify/execute
      → envelope backend → product response adapter

Biên thứ tám (nội dung UI) không thuộc backend; nó do
`frontend/scripts/certify-refusal-contract.mjs` chụp trên trình duyệt thật.

─── 0 LƯỢT GỌI MODEL, VÀ ĐIỀU ĐÓ ĐƯỢC CHỨNG MINH CHỨ KHÔNG ĐƯỢC KHAI ───────

Hai lớp, cố ý chồng nhau:

* **Chặn ở biên mạng** — `httpx.AsyncClient.send` và `socket.socket.connect` bị
  thay bằng hàm ném. `--faultcheck` chứng minh lớp này CÓ RĂNG bằng cách thử
  gọi thật và đòi thấy ngoại lệ; guard chưa từng đỏ là guard chưa được chứng
  minh (`ARCHITECTURE_MAP §8` #14).
* **Phát lại đúng byte** — `call_gemini` trả `raw_text` của lượt live đã đóng
  băng, sau khi đối chiếu `raw_sha256`. Lệch một byte là NÉM: một bản phát lại
  trôi khỏi lượt đo thì mọi kết luận sau đó nói về một hệ khác.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
from pathlib import Path
from typing import Any

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
sys.path.insert(0, str(BE / "scripts"))
GOC = BE.parent

RUN = (GOC / "docs" / "evaluation" / "geometry" / "thesis-final-acceptance"
       / "thesis-final-20260908T160224Z")
OUT_MAC_DINH = (GOC / "docs" / "evaluation" / "geometry"
                / "product-response-contract-alignment")

CA_AM = ("n1_khoi_tron_xoay_tong_quat", "n2_khoi_ghep_bu_can_boolean")


class ReplayError(RuntimeError):
    """Bản phát lại lệch khỏi lượt đo, hoặc guard mạng không có răng."""


def _bam(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ══════════════════════════════════════════════════════════════════════════
# §1 · CHẶN MẠNG — hai tầng, và cả hai phải chứng minh được là có răng
# ══════════════════════════════════════════════════════════════════════════
class NetworkGuard:
    """Mọi lối ra mạng đều ném. Đếm số lần bị chạm để báo cáo."""

    def __init__(self) -> None:
        self.attempts: list[str] = []
        self._cu: dict[str, Any] = {}

    def _chan(self, ten: str):
        def f(*_a, **_k):
            self.attempts.append(ten)
            raise ReplayError(
                f"CHẶN MẠNG: {ten} bị gọi trong lượt phát lại — "
                "lượt này phải có 0 lượt gọi thật")
        return f

    def _chan_socket(self):
        """Chặn MỌI đích trừ loopback — và ngoại lệ ấy KHÔNG phải chỗ hở.

        `asyncio.ProactorEventLoop` trên Windows tự dựng một `socketpair()`
        loopback để đánh thức chính nó; chặn thẳng `socket.connect` thì script
        chết trước khi chạy được ca đầu tiên (đã xảy ra ở lần chạy đầu — guard
        có răng tới mức cắn cả chủ). Provider thật KHÔNG đi qua loopback: nó đi
        `httpx` tới `generativelanguage.googleapis.com`, và lớp `httpx` bị chặn
        VÔ ĐIỀU KIỆN ngay dưới đây. Phép tiêm ở `kiem_guard_co_rang` thử đúng
        một địa chỉ NGOÀI loopback để chứng minh ngoại lệ này không nới ra.
        """
        cu = self._cu["sock"]
        chan = self._chan("socket.connect")

        def f(sock, address, *a, **k):
            host = address[0] if isinstance(address, tuple) else address
            if host in ("127.0.0.1", "::1", "localhost"):
                return cu(sock, address, *a, **k)
            return chan(sock, address, *a, **k)
        return f

    def __enter__(self) -> "NetworkGuard":
        import httpx

        self._cu["httpx_send"] = httpx.AsyncClient.send
        self._cu["httpx_sync"] = httpx.Client.send
        self._cu["sock"] = socket.socket.connect
        httpx.AsyncClient.send = self._chan("httpx.AsyncClient.send")
        httpx.Client.send = self._chan("httpx.Client.send")
        socket.socket.connect = self._chan_socket()
        return self

    def __exit__(self, *_e) -> None:
        import httpx

        httpx.AsyncClient.send = self._cu["httpx_send"]
        httpx.Client.send = self._cu["httpx_sync"]
        socket.socket.connect = self._cu["sock"]


def kiem_guard_co_rang() -> dict[str, Any]:
    """TIÊM LỖI vào chính guard: thử một lượt ra mạng và ĐÒI thấy ngoại lệ.

    Không có phép thử này thì "0 lượt gọi" chỉ là một câu trong báo cáo.
    """
    ket: dict[str, Any] = {}
    with NetworkGuard() as g:
        for ten, thu in (
            # Địa chỉ NGOÀI loopback, dạng số nên không cần DNS: nếu ngoại lệ
            # loopback bị nới ra thành "chặn nửa vời" thì phép thử này đỏ.
            ("socket_ngoai", lambda: socket.socket().connect(("93.184.216.34", 80))),
            ("httpx_sync", _thu_httpx_sync),
        ):
            try:
                thu()
            except ReplayError:
                ket[ten] = "RAISED"
            except Exception as e:                     # pragma: no cover
                ket[ten] = f"RAISED_OTHER:{type(e).__name__}"
            else:
                ket[ten] = "NOT_RAISED"
        ket["touched"] = list(g.attempts)
    ket["PASS"] = all(ket.get(k) == "RAISED"
                      for k in ("socket_ngoai", "httpx_sync"))
    return ket


def _thu_httpx_sync() -> None:
    import httpx

    with httpx.Client() as c:
        c.get("http://127.0.0.1:9/")


# ══════════════════════════════════════════════════════════════════════════
# §2 · PHÁT LẠI ĐÚNG BYTE — provider trả `raw_text` đã đóng băng
# ══════════════════════════════════════════════════════════════════════════
def doc_raw(case_id: str) -> dict[str, dict[str, Any]]:
    """`{stage: bản ghi thô}`, đã đối chiếu `raw_sha256`."""
    thu_muc = RUN / "raw" / case_id
    ra: dict[str, dict[str, Any]] = {}
    for f in sorted(thu_muc.iterdir()):
        j = json.loads(f.read_text(encoding="utf-8"))
        thuc = _bam(j["raw_text"].encode("utf-8"))
        if thuc != j["raw_sha256"]:
            raise ReplayError(
                f"{case_id}/{f.name}: raw_text lệch băm đã khoá "
                f"({thuc[:16]}… ≠ {j['raw_sha256'][:16]}…)")
        ra.setdefault(j["stage"], j)
    return ra


#: HAI BẢNG TÊN cho cùng hai lượt gọi, và chúng KHÔNG thay nhau được.
#: `telemetry.current_stage()` khai theo tên hàm pipeline
#: (`semantic_analyze` · `semantic_program`); bộ đo lượt live ghi theo vai trò
#: của lượt gọi (`analyze` · `synthesis`). Ánh xạ tường minh ở đây thay vì khớp
#: tiền tố — khớp tiền tố là chỗ một tên mới sẽ lặng lẽ trượt qua.
TEN_CHANG_ARTIFACT = {
    "semantic_analyze": "analyze",
    "semantic_program": "synthesis",
}


class ProviderPhatLai:
    """Đứng đúng chỗ `call_gemini`. Trả byte đã đóng băng, đếm lượt."""

    def __init__(self, raw: dict[str, dict[str, Any]]) -> None:
        self.raw = raw
        self.calls: list[str] = []

    async def __call__(self, api_key, skill, user, schema, temperature=0.1,
                       *a, **k) -> str:
        # Chặng đang mở đọc từ CHÍNH telemetry của pipeline
        # (`stage_scope` → `current_stage`), không đoán theo thứ tự gọi: thứ tự
        # là giả định, còn `current_stage` là thứ pipeline thật sự khai.
        from app.ai.telemetry import current_stage

        stage = current_stage()
        self.calls.append(stage or "?")
        ban = self.raw.get(TEN_CHANG_ARTIFACT.get(stage, stage))
        if ban is None:
            raise ReplayError(
                f"lượt gọi ở chặng {stage!r} không có bản ghi thô — "
                f"artifact chỉ có {sorted(self.raw)}")
        return ban["raw_text"]


def doc_raw_theo_thu_tu(case_id: str) -> dict[str, list[str]]:
    """`{chặng pipeline: [raw_text theo THỨ TỰ lượt gọi]}` — KỂ CẢ lượt sửa.

    `doc_raw` giữ MỘT bản ghi mỗi chặng (`setdefault`), đủ cho hai ca âm mà nó
    sinh ra để phát lại. Ca được phục vụ SAU một lượt sửa (`p3` có `repair_1`)
    cần cả chuỗi: phát lại lượt sửa bằng byte của lượt đầu thì hỏng y như lượt
    đầu (`ir_static`), và trông giống hệt một hồi quy của sản phẩm — đo được ở
    `PHOTO_PROBLEM_TO_SCENE_END_TO_END` (2026-09-13).

    Chỉ số lượt đọc từ tên tệp (`synthesis_0`, `repair_1`); băm đối chiếu y như
    `doc_raw`.
    """
    hang: dict[str, list[tuple[int, str]]] = {"semantic_analyze": [], "semantic_program": []}
    for f in (RUN / "raw" / case_id).iterdir():
        j = json.loads(f.read_text(encoding="utf-8"))
        thuc = _bam(j["raw_text"].encode("utf-8"))
        if thuc != j["raw_sha256"]:
            raise ReplayError(
                f"{case_id}/{f.name}: raw_text lệch băm đã khoá "
                f"({thuc[:16]}… ≠ {j['raw_sha256'][:16]}…)")
        chang = "semantic_analyze" if j["stage"] == "analyze" else "semantic_program"
        hang[chang].append((int(f.stem.rsplit("_", 1)[1]), j["raw_text"]))
    return {k: [t for _, t in sorted(v)] for k, v in hang.items()}


class ProviderPhatLaiTheoThuTu:
    """Như `ProviderPhatLai`, nhưng trả byte theo đúng THỨ TỰ lượt gọi trong chặng.

    Hết bản ghi mà pipeline còn gọi ⇒ NÉM: pipeline đã đi lệch đường lượt đo.
    `con_lai()` khác 0 sau khi chạy ⇒ pipeline gọi ÍT hơn lượt đo — cũng là lệch.
    """

    def __init__(self, hang: dict[str, list[str]]) -> None:
        self.hang = {k: list(v) for k, v in hang.items()}
        self.calls: list[str] = []

    async def __call__(self, api_key, skill, user, schema=None, temperature=0.1,
                       *a, **k) -> str:
        from app.ai.telemetry import current_stage

        stage = current_stage()
        self.calls.append(stage or "?")
        ds = self.hang.get(stage)
        if not ds:
            raise ReplayError(
                f"lượt gọi thứ {len(self.calls)} ở chặng {stage!r} không còn "
                f"bản ghi thô — còn lại {self.con_lai()}")
        return ds.pop(0)

    def con_lai(self) -> dict[str, int]:
        return {k: len(v) for k, v in self.hang.items()}


# ══════════════════════════════════════════════════════════════════════════
# §3 · OBSERVER — biên 3..5 hiện ra ở đây, không phải suy từ envelope
# ══════════════════════════════════════════════════════════════════════════
class GhiBien:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, data: dict) -> None:
        self.events.append({"type": event_type, **_thuan_json(data)})

    def ket_thuc(self, envelope) -> None:
        self.events.append({"type": "ket_thuc",
                            "status": (envelope or {}).get("status")})


def _thuan_json(x: Any) -> Any:
    """Bỏ mọi thứ không serialize được, giữ hình dạng."""
    if isinstance(x, dict):
        return {str(k): _thuan_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_thuan_json(v) for v in x]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return repr(x)[:400]


# ══════════════════════════════════════════════════════════════════════════
# §4 · MỘT CA — bảy biên
# ══════════════════════════════════════════════════════════════════════════
def replay_case(case_id: str, text: str) -> dict[str, Any]:
    import asyncio

    from app.ai import pipeline
    from app.learner_messages import attach_learner_reason
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC, co_duong_thuc_thi, detect_domain,
    )

    raw = doc_raw(case_id)
    prov = ProviderPhatLai(raw)
    ghi = GhiBien()

    # ── biên 1–2: TẤT ĐỊNH, 0 lượt gọi, chạy được ngoài mọi stub ──────────
    bien1 = {"detect_domain": detect_domain(text)}
    bien2 = {"co_duong_thuc_thi": co_duong_thuc_thi(text, DOMAIN_HINH_HOC)}

    cu = pipeline.call_gemini
    pipeline.call_gemini = prov
    try:
        with NetworkGuard() as g:
            env = asyncio.run(pipeline.run_pipeline(
                text, "REPLAY_KHONG_PHAI_KEY", observer=ghi,
                semantic_route="serve"))
        cham_mang = list(g.attempts)
    finally:
        pipeline.call_gemini = cu

    phan_hoi = attach_learner_reason(env)

    def _ev(t: str) -> list[dict]:
        return [e for e in ghi.events if e["type"] == t]

    return {
        "case_id": case_id,
        "problem_sha256": _bam(text.encode("utf-8")),
        "provider_calls_replayed": prov.calls,
        "raw_stages_available": sorted(raw),
        "network_touch_attempts": cham_mang,
        "boundaries": {
            "1_domain": bien1,
            "2_scope": bien2,
            "3_semantic_analyze": _ev("semantic_contract"),
            "4_semantic_program": [e for e in _ev("semantic_route")
                                   if e.get("stage_reached") in
                                   ("semantic_analyze", "semantic_program")],
            "5_verify_execute": [e for e in _ev("semantic_route")
                                 if e.get("stage_reached") not in
                                 ("semantic_analyze", "semantic_program")],
            "6_envelope_backend": _thuan_json(env),
            "7_product_response_adapter": _thuan_json(phan_hoi),
        },
        "contract_fields": {
            "status": env.get("status"),
            "stage_reached": env.get("stage_reached"),
            "failure_category": env.get("failure_category"),
            "error_code": env.get("error_code"),
            "learner_reason_present": bool(phan_hoi.get("learner_reason")),
        },
        "event_log": ghi.events,
    }


# ══════════════════════════════════════════════════════════════════════════
# §5 · CLI
# ══════════════════════════════════════════════════════════════════════════
def doc_de_bai() -> dict[str, str]:
    corpus = json.loads(
        (RUN.parent / "CORPUS.json").read_text(encoding="utf-8"))
    ra = {}
    for c in corpus["negative_cases"] + corpus["positive_cases"]:
        ra[c["id"]] = c["problem_text"]
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(OUT_MAC_DINH))
    ap.add_argument("--label", default="before",
                    help="'before' hoặc 'after' — tên file kết quả")
    ap.add_argument("--faultcheck", action="store_true",
                    help="chứng minh guard mạng có răng trước khi phát lại")
    ap.add_argument("--cases", nargs="*", default=list(CA_AM))
    a = ap.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    guard = kiem_guard_co_rang() if a.faultcheck else {"SKIPPED": True}
    if a.faultcheck and not guard["PASS"]:
        print("GUARD MẠNG KHÔNG CÓ RĂNG:", json.dumps(guard, ensure_ascii=False))
        return 2

    de = doc_de_bai()
    ket: dict[str, Any] = {
        "label": a.label,
        "run_source": RUN.relative_to(GOC).as_posix(),
        "network_guard_faultcheck": guard,
        "cases": {},
    }
    for cid in a.cases:
        ket["cases"][cid] = replay_case(cid, de[cid])

    ket["APPLICATION_LLM_CALLS"] = 0
    ket["REAL_PROVIDER_CALLS"] = 0

    p = out / f"BOUNDARY_REPLAY_{a.label.upper()}.json"
    p.write_text(json.dumps(ket, ensure_ascii=False, indent=1),
                 encoding="utf-8")

    for cid, r in ket["cases"].items():
        cf = r["contract_fields"]
        print(f"{cid}")
        print(f"  status={cf['status']}  stage_reached={cf['stage_reached']}")
        print(f"  failure_category={cf['failure_category']}  "
              f"error_code={cf['error_code']}")
        print(f"  provider replay: {r['provider_calls_replayed']}  "
              f"network touches: {r['network_touch_attempts']}")
    print(f"\nghi: {p.relative_to(GOC).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
