# -*- coding: utf-8 -*-
"""PHÉP THỬ NĂNG LỰC: AI có tự tìm ra phân rã góc nhị diện không?

    đề chưa từng thấy → Semantic Program → thẩm định
                      → thực thi tất định → chấm → trace → Scene3D

⚠️ **TIÊU QUOTA THẬT.** Cần `ALLOW_LIVE_AI=1` và `GEMINI_API_KEY`.

─── CÂU HỎI, VÀ VÌ SAO NÓ KHÔNG PHẢI "MÔ HÌNH GIỎI KHÔNG" ─────────────────

`test_dihedral_composition.py` đã chứng minh **bằng tay, 0 token**: IR hiện tại
đủ từ vựng để viết phép dựng góc nhị diện. Câu còn lại là câu của kiến trúc:

    một dạng bài MỚI có bắt buộc kéo theo CODE MỚI không?

Nếu mô hình tự tìm ra phân rã từ schema — mà prompt **không** hề nhắc tới nhị
diện, cũng không nhắc `project_onto` — thì câu trả lời là KHÔNG, và mỗi
primitive chuyên biệt thêm vào sau này phải tự biện minh chứ không được mặc
định.

─── ĐIỀU KHÔNG ĐƯỢC LÀM (§6) ──────────────────────────────────────────────

Không mớm phân rã. Không đưa đáp số. Không thêm ví dụ nhị diện vào prompt. Đề
gửi đi là đề THPT bình thường, đúng thứ một học sinh nhận được.

─── NGÂN SÁCH (§5) ────────────────────────────────────────────────────────

Tối đa **1 lượt tổng hợp + 1 lượt sửa**. Sản phẩm cho phép 3
(`MAX_SEMANTIC_PROGRAM_ATTEMPTS`); script này chặn ở 2 và ghi lại con số THẬT.
Chặn tại đây chứ không sửa hằng số sản phẩm: ngân sách là điều kiện của phép
đo, không phải một thay đổi hành vi.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import pipeline as PL  # noqa: E402
from app.ai.telemetry import reset_usage, total_tokens, usage_report  # noqa: E402
from app.simulation.semantic_program.geometry_obligations import (  # noqa: E402
    GEOMETRY_CHECKERS,
)
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.scene3d import build_scene3d  # noqa: E402
from app.simulation.semantic_program.simulation_state import (  # noqa: E402
    build_simulation_state,
)

#: Đề CHƯA TỪNG có trong dataset, template, hay ví dụ prompt nào.
#:
#: Cố ý chọn một cấu hình quen thuộc của SGK (chóp có cạnh bên vuông góc đáy) để
#: phép thử đo ĐÚNG thứ cần đo: không phải "mô hình có xử lý nổi hình lạ không",
#: mà "mô hình có tự nghĩ ra phép dựng đường đại diện không".
DE_BAI = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, cạnh bên SA vuông "
    "góc với mặt phẳng đáy và SA = a. Tính góc nhị diện tạo bởi mặt phẳng (SBC) "
    "và mặt phẳng đáy (ABCD) dọc theo cạnh chung BC."
)

BIEN_THE = [
    ("đổi tên đỉnh",
     "Cho hình chóp M.PQRT có đáy PQRT là hình vuông cạnh a, cạnh bên MP vuông "
     "góc với mặt phẳng đáy và MP = a. Tính góc nhị diện giữa mặt phẳng (MQR) "
     "và mặt phẳng đáy (PQRT) dọc cạnh chung QR."),
    ("đổi số liệu",
     "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với "
     "đáy và SA = 2a. Tính góc nhị diện giữa mặt phẳng (SBC) và mặt phẳng "
     "(ABCD) dọc cạnh chung BC."),
    ("đổi loại khối",
     "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B với "
     "AB = BC = a, cạnh bên AA' = a. Tính góc nhị diện giữa mặt phẳng (A'BC) và "
     "mặt phẳng đáy (ABC) dọc cạnh chung BC."),
]


def _no_dihedral_word(spec) -> bool:
    """Chương trình KHÔNG được chứa một từ vựng chuyên biệt nào cho nhị diện.

    Nếu có, nghĩa là ai đó đã lén thêm primitive — và toàn bộ phép thử vô nghĩa.
    """
    chuoi = json.dumps(spec.model_dump(), ensure_ascii=False).lower()
    return "dihedral" not in chuoi


def _kiem_phan_ra(spec, mem: dict) -> dict:
    """Chương trình mô hình viết ra CÓ THẬT SỰ là một phép dựng góc nhị diện?

    ─── VÌ SAO KHÔNG DÙNG `RequestContract.obligations` ────────────────────

    Nghĩa vụ do tầng **analyze** phát, không do LLM tổng hợp. Chạy analyze chỉ
    để có nghĩa vụ là tiêu thêm một lượt token cho một thứ phép thử này không
    hỏi. Nên bộ kiểm ở đây đọc thẳng **hình đã dựng** — đúng tinh thần §8: xác
    minh từ hình học, không từ lời khai.

    ─── ĐỊNH LÝ NÓ KIỂM, KHÔNG PHẢI HÌNH DẠNG CHƯƠNG TRÌNH ────────────────

    Không hỏi *"mô hình có gọi `project_onto` không"* — hỏi thế là chấm theo
    cách viết, và một lời giải đúng bằng đường khác sẽ bị đánh trượt oan. Hỏi
    tính chất TOÁN HỌC làm cho con số là góc nhị diện:

      ① có một đường `d` là giao tuyến hai mặt;
      ② có hai đường phân biệt cùng **vuông góc** với `d`;
      ③ mỗi đường **nằm trong** một trong hai mặt.

    Đủ ba điều ấy thì góc giữa chúng LÀ góc nhị diện, bất kể mô hình đi đường
    nào để dựng ra chúng.
    """
    from app.simulation.geometry import predicates as PR
    from app.simulation.geometry.exact import Line3, Plane3

    ra: dict = {"edge": None, "planes": [], "representatives": [],
                "verdict": "FAIL", "reason": None}

    # `d` = biến sinh bởi `intersect_plane_plane` (nếu có), nếu không thì mọi
    # `line3` đều là ứng viên — mô hình có thể dựng cạnh chung bằng đường khác.
    giao = [st.target_var for st in spec.statements
            if getattr(st, "kind", None) == "assign"
            and getattr(getattr(st, "expr", None), "kind", None) == "intersect_plane_plane"]
    duong = [k for k, v in mem.items() if isinstance(v, Line3)]
    mat = [k for k, v in mem.items() if isinstance(v, Plane3)]
    ra["planes"] = sorted(mat)

    ung_vien_d = giao or duong
    for d in ung_vien_d:
        vuong = [ln for ln in duong if ln != d
                 and PR.perpendicular_lines(mem[ln], mem[d])]
        if len(vuong) < 2:
            continue
        # ③ hai đường phải nằm trong HAI mặt KHÁC nhau.
        def _trong(ln: str, pl: str) -> bool:
            L = mem[ln]
            return (PR.point_on_plane(L.point, mem[pl])
                    and PR.point_on_plane(L.point + L.direction, mem[pl]))

        for i, x in enumerate(vuong):
            for y in vuong[i + 1:]:
                mx = [pl for pl in mat if _trong(x, pl)]
                my = [pl for pl in mat if _trong(y, pl)]
                if mx and my and set(mx) != set(my):
                    ra.update({"edge": d, "representatives": [x, y],
                               "in_planes": [sorted(mx), sorted(my)],
                               "verdict": "PASS"})
                    return ra
    ra["reason"] = ("không tìm được cạnh chung + hai đường vuông góc nằm trong "
                    "hai mặt khác nhau")
    return ra


async def _mot_de(text: str, api_key: str, ngan_sach: int) -> dict:
    """Chạy MỘT đề. Trả bản ghi đầy đủ, kể cả khi hỏng."""
    reset_usage()
    dem = {"http": 0, "attempted": 0}

    goc = PL.call_gemini

    async def dem_call(*a, **kw):
        # Đếm ĐỊNH THỬ và ĐÃ GỬI riêng ra. Lượt vượt trần bị chặn TRƯỚC khi
        # gửi, nên nó không tiêu token — gộp hai con số làm một là báo cáo
        # thổi phồng chi phí, và một báo cáo sai theo hướng nào cũng là sai.
        dem["attempted"] += 1
        if dem["attempted"] > ngan_sach:
            raise RuntimeError(
                f"vượt ngân sách {ngan_sach} lượt — dừng TRƯỚC khi gửi, "
                "lượt này không tiêu token"
            )
        dem["http"] += 1
        return await goc(*a, **kw)

    PL.call_gemini = dem_call
    ghi: dict = {"problem": text}
    # KHÔNG gọi `stage_analyze`: `stage_semantic_program` không đọc `analysis`
    # (chỉ dùng `text` + `contract` + thẻ văn phạm), nên một lượt analyze ở đây
    # là một lượt token tiêu cho không. Ngân sách §5 đếm lượt TỔNG HỢP, và phép
    # đo phải đo đúng thứ nó khai.
    try:
        spec, loi = await PL.stage_semantic_program(
            text, {}, api_key, domain="geometry")
    except RuntimeError as e:
        PL.call_gemini = goc
        return {**ghi, "ok": False, "stage": "BUDGET", "error": str(e),
                "http_calls": dem["http"], "attempts": dem["attempted"],
                "tokens": total_tokens()}
    finally:
        PL.call_gemini = goc

    ghi.update({"http_calls": dem["http"], "attempts": dem["attempted"],
                "tokens": total_tokens(),
                "usage": usage_report()})

    if spec is None:
        return {**ghi, "ok": False, "stage": "SYNTHESIS", "error": loi}

    ghi["no_dihedral_primitive"] = _no_dihedral_word(spec)
    ghi["statements"] = [s.kind for s in spec.statements]

    # ── THỰC THI TẤT ĐỊNH — 0 token từ đây trở đi ────────────────────────
    try:
        kq = SemanticProgramInterpreter().execute(spec)
    except Exception as e:  # noqa: BLE001
        return {**ghi, "ok": False, "stage": "RUNTIME", "error": f"{type(e).__name__}: {e}"}

    ghi["memory"] = {k: str(v) for k, v in kq.final_memory.items()}

    # ── CHẤM: xác minh TỪ HÌNH ĐÃ DỰNG, không đọc lời mô hình khai ───────
    ghi["verification"] = _kiem_phan_ra(spec, kq.final_memory)

    try:
        state = build_simulation_state(spec, kq)
        canh = build_scene3d(state)
        ghi["scene_objects"] = len(canh.get("objects", []))
        ghi["timeline_steps"] = len(state.get("timeline", []) or [])
        ghi["scene_json_ok"] = bool(json.dumps(canh, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        return {**ghi, "ok": False, "stage": "SCENE", "error": f"{type(e).__name__}: {e}"}

    # "Chạy được" KHÔNG phải "đúng". Lời giải ngây thơ — đo thẳng góc giữa hai
    # MẶT — chạy trót lọt và cho đúng con số ở nhiều cấu hình, nhưng nó không
    # phải một phép DỰNG góc nhị diện: không có cạnh chung, không có đường đại
    # diện, không có gì cho học sinh nhìn. Nên `ok` đòi cả bộ kiểm hình học.
    ghi["ok"] = ghi["verification"]["verdict"] == "PASS"
    ghi["stage"] = "DONE" if ghi["ok"] else "VERIFICATION"
    return ghi


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default="../docs/evaluation/geometry/dihedral-probe")
    p.add_argument("--budget", type=int, default=2,
                   help="trần lượt HTTP mỗi đề (1 tổng hợp + 1 sửa)")
    p.add_argument("--variations", action="store_true",
                   help="chạy thêm 3 biến thể (§11) — tiêu thêm quota")
    a = p.parse_args()

    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("✗ Cần ALLOW_LIVE_AI=1 — script này TIÊU QUOTA THẬT.")
        return 2
    # Nạp `backend/.env` như mọi runner khác — khoá KHÔNG viết trong mã, và
    # `dotenv` không đè biến môi trường đã có.
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except ImportError:
        pass
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("✗ Thiếu GEMINI_API_KEY trong môi trường/backend/.env")
        return 2

    ra = Path(a.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    dich = ra / "dihedral-probe.json"
    if dich.exists():
        print(f"✗ {dich} đã có — bộ đo TỪ CHỐI đè artifact lượt cũ.")
        return 3

    cases = [("bài chính", DE_BAI)]
    if a.variations:
        cases += BIEN_THE

    ket = []
    for ten, de in cases:
        print(f"\n━━ {ten} ━━")
        r = await _mot_de(de, key, a.budget)
        r["label"] = ten
        ket.append(r)
        print(f"  stage={r['stage']} http={r.get('http_calls')} "
              f"tokens={r.get('tokens')} ok={r.get('ok')}")
        if r.get("obligations"):
            for o in r["obligations"]:
                print(f"    · {o['kind']}: {o['verdict']}")

    chinh = ket[0]
    bao = {
        "khai": "Phép thử NĂNG LỰC: AI tự tìm phân rã góc nhị diện từ IR tổng "
                "quát. Prompt KHÔNG nhắc nhị diện, KHÔNG nhắc project_onto.",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "budget_per_case": a.budget,
        "one_shot": chinh.get("http_calls") == 1 and chinh.get("ok") is True,
        "repair_used": max(0, (chinh.get("http_calls") or 0) - 1),
        "total_tokens": sum(c.get("tokens") or 0 for c in ket),
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"\n→ {dich}")
    print(f"ONE_SHOT={'YES' if bao['one_shot'] else 'NO'} · "
          f"tokens={bao['total_tokens']}")
    return 0 if chinh.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
