# -*- coding: utf-8 -*-
"""Trích **phản hồi SẢN PHẨM** của 9 ca lượt đo cuối. 0 lượt gọi model.

─── VÌ SAO PHẢI DỰNG LẠI, KHÔNG CHỈ CHÉP ────────────────────────────────────

Artifact lượt đo giữ `chuong_trinh` (đầu ra mô hình) và `cham` (điểm số) —
**không** giữ envelope. Envelope là thứ tầng TẤT ĐỊNH dựng ra *sau* mô hình, nên
nó dựng lại được từ chương trình đã đóng băng mà không tốn một lượt gọi nào.

Đường dựng ở đây là **đúng đường sản phẩm**, gọi đúng những hàm `main.py` gọi:

    RequestContract (đóng băng)  +  SemanticProgramSpec (đóng băng)
      → route.verify_and_compile          ← toàn bộ cổng thẩm định
      → pipeline._dung_scene3d            ← cảnh CHỈ dựng khi chương trình chạy trọn
      → pipeline._envelope_tu_route_sinh  ← phục vụ được
        · pipeline._that_bai_hinh_hoc     ← không phục vụ được
      → learner_messages.attach_learner_reason   ← biên API

⚠️ **Không dựng envelope bằng `compile_semantic_program_to_envelope` một mình.**
Hàm ấy khai cứng `domain: "generic"` và không gắn `scene3d`, nên nó cho ra một
envelope **2D hợp lệ nhưng sai miền** — `build_baseline_spot_envelopes.py` đã
trả giá cho lỗi ấy bằng một lượt spot-check đỏ 6/8 với 0 lỗi console.

─── PHÉP ĐỐI CHỨNG, VÀ VÌ SAO NÓ LÀ TOÀN BỘ GIÁ TRỊ CỦA SCRIPT NÀY ─────────

Một bản dựng lại chỉ đáng tin khi nó **khớp với điểm đã chấm**. Mỗi ca được so
lại với `cham` đóng băng ở bốn chỗ: `SERVABLE` · tập `scene3d_kinds` ·
`quantities` (từng ký tự) · lớp phán quyết. Lệch một chỗ là **NÉM**, không phải
cảnh báo — vì một fixture trôi khỏi lượt đo thì mọi ảnh chụp sau đó chứng minh
nhầm hệ.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
sys.path.insert(0, str(BE / "scripts"))
GOC = BE.parent

RUN_MAC_DINH = (GOC / "docs" / "evaluation" / "geometry" / "thesis-final-acceptance"
                / "thesis-final-20260908T160224Z")
OUT_MAC_DINH = (GOC / "docs" / "evaluation" / "geometry" / "product-ui-result-rendering")


class FixtureError(RuntimeError):
    """Bản dựng lại lệch khỏi lượt đo — dừng, không ghi."""


def _bam_chuoi(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _bam_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _tuong_doi(p: Path) -> str:
    """Đường dẫn ghi vào fixture luôn tương đối gốc kho — tuyệt đối thì fixture
    chỉ đọc được trên đúng máy đã sinh ra nó."""
    return p.resolve().relative_to(GOC).as_posix()


# ══════════════════════════════════════════════════════════════════════════
# §1 · CHỌN LƯỢT CUỐI CỦA MỖI CA
# ══════════════════════════════════════════════════════════════════════════
def lan_cuoi_cua_moi_ca(thu_muc: Path) -> dict[str, dict[str, Any]]:
    """`{case_id: bản ghi của lần THỬ CUỐI}` — chặng B đè chặng A khi có.

    Đây là điều luận văn báo cáo (`FINAL_SERVABLE 7/7`), khác với con số
    one-shot (`FIRST_ATTEMPT 6/7`). Trộn hai chặng là cách làm đẹp số một cách
    im lặng, nên hàm này ghi rõ ca nào tới từ chặng nào.
    """
    a = json.loads((thu_muc / "stage_a_first_attempt.json").read_text(encoding="utf-8"))
    b = json.loads((thu_muc / "stage_b_recovery.json").read_text(encoding="utf-8"))
    ra: dict[str, dict[str, Any]] = {}
    for c in a["cases"]:
        ra[c["id"]] = {**c, "chang": "A", "nguon_file": "stage_a_first_attempt.json"}
    for c in b.get("cases", []):
        cu = ra.get(c["id"], {})
        # Chặng B là một lượt TIẾP TỤC: nó không phân tích lại đề, nên hợp đồng
        # phải lấy từ chặng A. Chép đè nguyên bản ghi B sẽ mất `request_contract`.
        ra[c["id"]] = {**cu, **c, "chang": "B",
                       "nguon_file": "stage_b_recovery.json",
                       "request_contract": c.get("request_contract")
                       or cu.get("request_contract")}
    return ra


# ══════════════════════════════════════════════════════════════════════════
# §2 · DỰNG LẠI PHẢN HỒI SẢN PHẨM — 0 lượt gọi
# ══════════════════════════════════════════════════════════════════════════
def dung_phan_hoi(ban_ghi: dict[str, Any]) -> dict[str, Any]:
    """Chạy đúng đường sản phẩm sau mô hình và trả **phản hồi API** đầy đủ."""
    from app.ai import pipeline
    from app.learner_messages import attach_learner_reason
    from app.simulation.error_codes import ErrorCode
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import (
        hong_truoc_khi_dung_ir,
        verify_and_compile,
    )
    from app.simulation.semantic_program.validator import validate_semantic_program

    hd_json = ban_ghi.get("request_contract")
    if hd_json is None:
        raise FixtureError(f"{ban_ghi['id']}: artifact không có request_contract")
    contract = RequestContract.model_validate(hd_json)

    spec = None
    ct = ban_ghi.get("chuong_trinh")
    if ct is not None:
        v = validate_semantic_program(ct)
        if not v.ok:
            raise FixtureError(f"{ban_ghi['id']}: chương trình đóng băng không "
                               f"qua được validator hiện hành: {v.error}")
        spec = v.spec

    if spec is not None:
        outcome = verify_and_compile(contract, spec)
    else:
        # ⚠️ KHÔNG để `outcome = None` ở đây, và đây là một bản sửa lỗi TRÔI.
        #
        # Đường sản phẩm (`pipeline._semantic_route_attempt`) khi không dựng nổi
        # IR nay trả một PHÁN QUYẾT — `stage_reached="semantic_program"`,
        # `error_code="semantic_program_invalid"` — chứ không trả `None`. Script
        # này dựng lại đường ấy, nên `None` biến nó thành bản dựng lại của một
        # hệ đã không còn tồn tại: fixture `n1` giữ `stage_reached=null` trong
        # khi sản phẩm thật đã giao đủ hai trường. Một fixture như thế khiến ảnh
        # chụp trình duyệt chứng minh cho hệ CŨ.
        #
        # Lý do lấy từ `synthesis_error` của chính artifact — đã đối chiếu bằng
        # máy là khớp từng ký tự với `reason` mà route phát ra khi phát lại.
        outcome = hong_truoc_khi_dung_ir(
            "semantic_program", ErrorCode.SEMANTIC_PROGRAM_INVALID,
            ban_ghi.get("synthesis_error"))
    if outcome is not None and outcome.executable:
        # `SemanticRouteOutcome.scene3d` là một Ô TRỐNG — route KHÔNG dựng cảnh
        # (hướng phụ thuộc một chiều). `pipeline._dung_scene3d` là người đổ.
        outcome = outcome.model_copy(
            update={"scene3d": pipeline._dung_scene3d(spec, contract)})

    if outcome is not None and outcome.servable:
        env = pipeline._envelope_tu_route_sinh(outcome, {}, {}, None)
    else:
        env = pipeline._that_bai_hinh_hoc(outcome, {}, {}, None)
    return attach_learner_reason(env)


# ══════════════════════════════════════════════════════════════════════════
# §3 · ĐỐI CHỨNG VỚI ĐIỂM ĐÃ ĐÓNG BĂNG
# ══════════════════════════════════════════════════════════════════════════
def doi_chung(ban_ghi: dict[str, Any], env: dict[str, Any]) -> None:
    """Ném khi bản dựng lại lệch khỏi `cham` của lượt đo.

    Bốn chỗ, cố ý không gộp: một envelope có thể phục vụ được mà thiếu đại
    lượng, hoặc đủ đại lượng mà thiếu loại vật trong cảnh — hai kiểu hỏng khác
    nhau, và gộp lại thì chỉ còn một bit thông tin.
    """
    ch = ban_ghi.get("cham") or {}
    cid = ban_ghi["id"]
    lech: list[str] = []

    phuc_vu = env.get("status") == "ok"
    if phuc_vu != bool(ch.get("SERVABLE")):
        lech.append(f"SERVABLE: artifact {ch.get('SERVABLE')} · dựng lại {phuc_vu}")

    if phuc_vu:
        canh = env.get("scene3d") or {}
        # ⚠️ `cham["scene3d_kinds"]` là kiểu NGỮ NGHĨA (`type`: point3, solid,
        # quantity…), KHÔNG phải loại vẽ (`render`: point_marker, mesh,
        # readout…). Hai bảng tên khác nhau cho hai tầng khác nhau, và so nhầm
        # bảng thì mọi ca đều "lệch" — đã mắc một lần khi viết script này.
        kieu = sorted({o.get("type") for o in canh.get("objects", [])})
        mong = sorted(ch.get("scene3d_kinds") or [])
        if kieu != mong:
            lech.append(f"scene3d_kinds: artifact {mong} · dựng lại {kieu}")

        # Đáp số đọc từ CẢNH (thứ người học thật sự nhìn thấy), so với
        # `expected_display` — kỳ vọng GOLD đóng băng trước lượt chạy.
        #
        # ⚠️ Cố ý KHÔNG so với `actual_display` của artifact thô: đó chính là
        # trường mà lỗi bộ chấm làm rỗng ở 6/7 ca (`SCORING_CORRECTION.json`).
        # So với một trường đã biết là hỏng thì phép đối chứng này sẽ đỏ trên
        # một hệ hoàn toàn đúng — đúng cái bẫy wave trước đã gỡ.
        doc = {o["label"]: o.get("value")
               for o in canh.get("objects", []) if o.get("render") == "readout"}
        mong_dap = [q.get("expected_display")
                    for q in (ch.get("quantities") or {}).values()]
        thieu = [g for g in mong_dap if g not in doc.values()]
        if thieu:
            lech.append(f"đáp số vắng mặt trên CẢNH: {thieu} · cảnh có {doc}")

    if lech:
        raise FixtureError(f"{cid}: bản dựng lại LỆCH khỏi lượt đo — "
                           + " | ".join(lech))


# ══════════════════════════════════════════════════════════════════════════
# §4 · FIXTURE
# ══════════════════════════════════════════════════════════════════════════
def dung_fixture(ban_ghi: dict[str, Any], env: dict[str, Any],
                 thu_muc: Path) -> dict[str, Any]:
    ch = ban_ghi.get("cham") or {}
    canh = env.get("scene3d") or {}
    objs = canh.get("objects", [])
    am = ban_ghi["loai"] == "am"

    if am:
        # Ranh giới ghi ĐÚNG thứ quan sát được, kể cả khi nó `None`: `n1` bị
        # chặn TRƯỚC khi có mã lỗi nào để so, và ghi một mã cho đẹp ở đây là
        # hồi tố sửa kỳ vọng — đúng thứ pre-registration tồn tại để chặn.
        ranh = (ch.get("ACTUAL_BOUNDARY") or {})
        that_bai = {"stage": ranh.get("stage"), "code": ranh.get("code"),
                    "envelope_error_code": env.get("error_code"),
                    "envelope_stage_reached": env.get("stage_reached"),
                    "failure_category": env.get("failure_category"),
                    "verdict": ch.get("CANONICAL_VERDICT")}
    else:
        that_bai = None

    return {
        "case_id": ban_ghi["id"],
        "positive_or_negative": "negative" if am else "positive",
        "source_artifact_path": _tuong_doi(thu_muc / ban_ghi["nguon_file"]),
        "source_sha256": _bam_file(thu_muc / ban_ghi["nguon_file"]),
        "served_from_stage": ban_ghi["chang"],
        "status": env.get("status"),
        "expected_exact_display": sorted(
            o.get("value") for o in objs if o.get("render") == "readout"),
        "expected_scene_object_count": len(objs),
        # ⚠️ HAI bảng tên cho HAI tầng, và chúng không thay nhau được:
        # `type` là kiểu NGỮ NGHĨA (`point3`, `solid`, `ellipse3`) — cùng bảng
        # `cham["scene3d_kinds"]` của lượt đo dùng; `render` là LOẠI VẼ
        # (`point_marker`, `mesh`, `readout`). Ghi cả hai vì phép đối chứng cần
        # bảng thứ nhất còn phía renderer đọc bảng thứ hai.
        "expected_scene_kinds": sorted({o.get("type") for o in objs}),
        "expected_render_kinds": sorted({o.get("render") for o in objs}),
        "expected_trace_event_count": len(canh.get("events", [])),
        "expected_failure_stage_or_code": that_bai,
        "problem_text": (ban_ghi.get("request_contract") or {}).get("problem_text"),
        "envelope": env,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, default=RUN_MAC_DINH)
    p.add_argument("--out", type=Path, default=OUT_MAC_DINH)
    p.add_argument("--bo-qua-kiem-bam", action="store_true",
                   help="CHỈ để chẩn đoán; lượt sinh fixture thật phải kiểm")
    a = p.parse_args()

    print("TRÍCH FIXTURE PHẢN HỒI SẢN PHẨM — 0 lượt gọi model\n")

    # ── ① Artifact nguồn phải còn nguyên byte ────────────────────────────
    if not a.bo_qua_kiem_bam:
        from doi_chieu_ket_qua_cuoi import kiem_bam
        kb = kiem_bam(a.run)
        if not kb["ARTIFACT_HASH_VERIFICATION"]:
            print(f"  ✗ ARTIFACT_HASH_VERIFICATION FAIL: {kb}")
            return 2
        print(f"  ✓ ARTIFACT_HASH_VERIFICATION  {kb['SO_ARTIFACT']} file · "
              f"{kb['SO_FILE_RAW']} raw")

    fixtures_dir = a.out / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    cuoi = lan_cuoi_cua_moi_ca(a.run)
    ra: list[dict[str, Any]] = []
    for cid in sorted(cuoi):
        bg = cuoi[cid]
        env = dung_phan_hoi(bg)
        doi_chung(bg, env)
        fx = dung_fixture(bg, env, a.run)
        (fixtures_dir / f"{cid}.json").write_text(
            json.dumps(fx, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        ra.append(fx)
        print(f"  ✓ {cid:<36} chặng {fx['served_from_stage']} · "
              f"{fx['status']:<11} · {fx['expected_scene_object_count']:>3} vật · "
              f"{fx['expected_trace_event_count']:>2} bước · "
              f"{fx['expected_exact_display']}")

    # ── ② Bảng băm: fixture nối về artifact nguồn bằng SHA-256 ───────────
    bang = {
        "khai": "Fixture DẪN XUẤT từ lượt đo cuối. Không phải artifact lượt "
                "đo — artifact ấy bất biến và nằm ở thư mục khác. Mỗi dòng nối "
                "ngược về file nguồn bằng SHA-256.",
        "run_id": a.run.name,
        "application_llm_calls": 0,
        "real_provider_calls": 0,
        "fixtures": {
            fx["case_id"]: {
                "fixture_sha256": _bam_file(fixtures_dir / f"{fx['case_id']}.json"),
                "source_artifact_path": fx["source_artifact_path"],
                "source_sha256": fx["source_sha256"],
                "envelope_sha256": _bam_chuoi(
                    json.dumps(fx["envelope"], sort_keys=True, ensure_ascii=False)),
            }
            for fx in ra
        },
    }
    (a.out / "FIXTURE_HASHES.json").write_text(
        json.dumps(bang, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    duong = sum(1 for x in ra if x["positive_or_negative"] == "positive")
    print(f"\n  {len(ra)} fixture ({duong} dương · {len(ra) - duong} âm) → "
          f"{_tuong_doi(fixtures_dir)}")
    print(f"  bảng băm → {_tuong_doi(a.out / 'FIXTURE_HASHES.json')}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FixtureError as e:
        print(f"\n✗ {e}")
        sys.exit(3)
