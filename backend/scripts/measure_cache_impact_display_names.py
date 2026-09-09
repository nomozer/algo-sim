# -*- coding: utf-8 -*-
"""ĐO tác động cache của bản vá TÊN HIỂN THỊ, bằng ROW THẬT. 0 lượt gọi model.

─── VÌ SAO WAVE NÀY KHÁC HẲN WAVE TRƯỚC ────────────────────────────────────

`PRODUCT_RESPONSE_CONTRACT_ALIGNMENT` chỉ đổi nội dung phản hồi **từ chối**, và
`main.py` chỉ ghi cache khi `status == "ok"` — nên ở đó không tồn tại row nào để
trả lại, và kết luận *"không bump"* là hiển nhiên.

Ở đây thì ngược: nhãn hiển thị nằm **bên trong** `scene3d.objects[].label` của
một envelope `status = "ok"` — đúng loại envelope ĐƯỢC cache. Một row ghi trước
bản vá mang nhãn `Diện tích «đối tượng»`; nếu route trả thẳng row ấy thì học
sinh vẫn đọc nhãn cũ trên mã mới, và không cổng nào kêu.

Nên câu hỏi phải trả lời bằng một row thật, không bằng suy luận:

    ① ghi được một row `status="ok"` cho ca elip không?
    ② row ấy có CHỨA nhãn hiển thị không?
    ③ tra cứu lần sau có trả thẳng row ấy, bỏ qua mã mới, không?

`③` là câu quyết định. Trả lời **có** ⇒ phải bump `CACHE_VERSION`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
sys.path.insert(0, str(BE / "scripts"))
GOC = BE.parent

FIXTURES = (GOC / "docs" / "evaluation" / "geometry"
            / "product-ui-result-rendering" / "fixtures")
CA = "p6_thiet_dien_elip_cua_hinh_tru"
NHAN_CU = "Diện tích «đối tượng»"


def do() -> dict:
    import app.main as M
    from app.persistence.db import SessionLocal, SimulationCache

    fx = json.loads((FIXTURES / f"{CA}.json").read_text(encoding="utf-8"))
    de = fx["problem_text"]
    env_moi = fx["envelope"]

    src = (BE / "app" / "main.py").read_text(encoding="utf-8")
    dieu_kien = [d.strip() for d in src.splitlines()
                 if 'envelope.get("status") == "ok"' in d]

    ket: dict = {
        "khai": "Đo bằng ROW THẬT trong bảng `SimulationCache`.",
        "wave": "DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH",
        "case_id": CA,
        "CACHE_WRITE_CONDITION": dieu_kien,
        "CACHE_VERSION": M.CACHE_VERSION,
    }

    # ── ① + ② dựng một row Y HỆT row mà bản TRƯỚC bản vá sẽ ghi ───────────
    #
    # Không cần chạy lại mã cũ: envelope trước bản vá đã có trong git, và điều
    # duy nhất cần chứng minh là *row có chở nhãn hay không*.
    import subprocess

    cu = subprocess.run(
        ["git", "show",
         f"HEAD:{(FIXTURES / f'{CA}.json').relative_to(GOC).as_posix()}"],
        cwd=GOC, capture_output=True, text=True, encoding="utf-8")
    env_cu = json.loads(cu.stdout)["envelope"] if cu.returncode == 0 else None

    def _nhan(env) -> list[str]:
        return [str(o.get("label")) for o in
                (env.get("scene3d") or {}).get("objects", [])
                if o.get("render") == "readout"]

    ket["nhan_trong_envelope_TRUOC_va"] = _nhan(env_cu) if env_cu else None
    ket["nhan_trong_envelope_SAU_va"] = _nhan(env_moi)
    ket["ROW_CO_CHUA_NHAN_HIEN_THI"] = bool(
        env_cu and any(NHAN_CU in n for n in _nhan(env_cu)))

    key = M._cache_key(de)
    ket["cache_key"] = key[:16]

    # ── ③ Ghi row CŨ rồi hỏi lại: route có trả thẳng nó không? ────────────
    from fastapi.testclient import TestClient

    from app.ai import pipeline

    async def _khong_duoc_goi(*a, **k):
        raise AssertionError(
            "provider bị gọi — nghĩa là cache KHÔNG trả row, phép đo sai giả thiết")

    goi_that = {"n": 0}
    cu_call = pipeline.call_gemini
    pipeline.call_gemini = _khong_duoc_goi
    try:
        with TestClient(M.app) as c:
            # Dọn mọi row của đề này để phép đo bắt đầu từ trạng thái đã biết.
            with SessionLocal() as s:
                for r in s.query(SimulationCache).filter_by(problem_text=de).all():
                    s.delete(r)
                s.commit()
                s.add(SimulationCache(
                    key=key,
                    problem_text=de, simulation_id="generic.semantic_program",
                    envelope_json=json.dumps(env_cu or env_moi, ensure_ascii=False),
                    dsl_version=M.DSL_VERSION, policy_version=M.CACHE_VERSION))
                s.commit()

            r = c.post("/api/analyze",
                       json={"input": {"type": "text", "content": de}})
            body = r.json()
    except AssertionError as e:
        body = {"_loi": str(e)}
        goi_that["n"] = 1
    finally:
        pipeline.call_gemini = cu_call
        with SessionLocal() as s:
            for row in s.query(SimulationCache).filter_by(problem_text=de).all():
                s.delete(row)
            s.commit()

    nhan_tra_ve = _nhan(body) if isinstance(body, dict) and body.get("scene3d") else []
    ket["nhan_route_TRA_VE_khi_co_row_cu"] = nhan_tra_ve
    ket["ROW_CU_DUOC_TRA_THANG"] = bool(
        nhan_tra_ve and any(NHAN_CU in n for n in nhan_tra_ve))
    ket["provider_bi_goi"] = goi_that["n"]

    ket["CACHE_VERSION_BUMP_REQUIRED"] = ket["ROW_CU_DUOC_TRA_THANG"]
    ket["ket_luan"] = (
        "PHẢI BUMP: row cache ghi trước bản vá CHỞ nhãn hiển thị cũ, và route "
        "trả thẳng row ấy — học sinh đọc nhãn cũ trên mã mới, không cổng nào kêu."
        if ket["ROW_CU_DUOC_TRA_THANG"] else
        "KHÔNG bump: row cũ không được trả về nguyên trạng cho đường sinh cảnh; "
        "xem `nhan_route_TRA_VE_khi_co_row_cu`.")
    return ket


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(
        GOC / "docs" / "evaluation" / "geometry" / "display-name-final-polish"
        / "CACHE_IMPACT.json"))
    a = ap.parse_args()
    kq = do()
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in kq.items() if k != "CACHE_WRITE_CONDITION"},
                     ensure_ascii=False, indent=1)[:1400])
    print("\nBUMP_REQUIRED =", kq["CACHE_VERSION_BUMP_REQUIRED"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
