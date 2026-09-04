# -*- coding: utf-8 -*-
"""CHÍNH SÁCH ĐO — nạp, chuẩn hoá và BĂM ngưỡng + rubric. **0 lượt gọi model.**

    `V3_THRESHOLD_AND_RUN_IDENTITY_POLICY`, 2026-09-04.

Bộ đo, ở `scripts/` — ngoài `MEASURED_SYSTEM_PATHS`. Nó không đọc và không sửa
gì trong `app/`.

─── VÌ SAO MỘT AUTHORITY RIÊNG ────────────────────────────────────────────

Ngưỡng phải **khoá trước khi biết kết quả**, nếu không nó chỉ mô tả lại kết quả.
Khoá được nghĩa là **băm được**, và băm được nghĩa là có một dạng CHÍNH TẮC —
không phụ thuộc thụt lề, xuống dòng hay thứ tự khoá trong file. Đặt phép chuẩn
hoá ấy cạnh scorer, không nhét vào scorer: scorer trả lời *"ca này thuộc lớp
nào"*, file này trả lời *"ngưỡng và rubric là gì, và có bị đổi không"*.

─── DẠNG CHÍNH TẮC ────────────────────────────────────────────────────────

`json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",",":"))`.

Reformat file (thêm thụt lề, đổi thứ tự khoá) **không** đổi băm; đổi một CON SỐ
thì đổi. Đó đúng là ranh giới cần: hình thức tự do, nội dung bất biến.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

__all__ = [
    "CHINH_SACH_NGUONG",
    "RUBRIC_QUY_TRACH_NHIEM",
    "bam_chinh_tac",
    "doc_chinh_sach",
    "nap_nguong",
    "nap_rubric",
    "kiem_chinh_sach",
    "kiem_danh_tinh_model",
    "cau_hinh_model_hien_tai",
    "san_sang_live_tu_cau_hinh",
    "kiem_bang_chung_quy_trach_nhiem",
    "TRUONG_DECODING",
]

THU_MUC = Path(__file__).resolve().parent / "policies"
CHINH_SACH_NGUONG = THU_MUC / "curved_v3_threshold_policy.json"
RUBRIC_QUY_TRACH_NHIEM = THU_MUC / "curved_v3_attribution_rubric.json"


def bam_chinh_tac(obj: Any) -> str:
    """Băm DẠNG CHÍNH TẮC — bất biến với thụt lề và thứ tự khoá."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def doc_chinh_sach(duong: Path) -> tuple[dict, str]:
    """Trả `(nội dung, băm chính tắc)`. Thiếu file ⇒ NÉM, không im lặng."""
    if not duong.exists():
        raise FileNotFoundError(
            f"thiếu chính sách đo: {duong}\nNgưỡng phải tồn tại TRƯỚC lượt "
            f"chạy — không có thì mọi con số sau đó đều có thể được chọn "
            f"ngưỡng cho vừa.")
    d = json.loads(duong.read_text(encoding="utf-8"))
    return d, bam_chinh_tac(d)


def nap_nguong() -> tuple[dict, str]:
    return doc_chinh_sach(CHINH_SACH_NGUONG)


def nap_rubric() -> tuple[dict, str]:
    return doc_chinh_sach(RUBRIC_QUY_TRACH_NHIEM)


#: Trường BẮT BUỘC của chính sách ngưỡng. Thiếu một cái là chính sách không
#: nói đủ để chấm, và một chính sách nói thiếu sẽ được "diễn giải" sau khi
#: thấy kết quả — đúng thứ việc khoá trước sinh ra để chặn.
TRUONG_BAT_BUOC = (
    "policy_id", "policy_version", "created_before_live_run",
    "candidate_hash", "pool_hash", "sample_design", "run_validity",
    "family_thresholds", "feature_thresholds", "negative_thresholds",
    "error_accounting", "attribution_policy", "model_identity_policy",
    "hash_algorithm",
)


#: Tham số decoding PHẢI có giá trị cụ thể trước draw. `None` được phép TỒN TẠI
#: trong manifest (khai thật rằng provider dùng mặc định chưa xác định), nhưng
#: readiness guard vẫn đỏ — vì một mặc định không ghi lại thì lượt sau không
#: tái lập được, và "không biết" khác "đã chọn".
TRUONG_DECODING = ("temperature", "top_p", "max_output_tokens", "repair_limit")


def _la_so(v: Any) -> bool:
    """Giá trị có TÁI LẬP được không — tức có phải một SỐ.

    Không phải câu hỏi thừa. `run_curved_ergonomics_v2.py:297` ghi thật
    `"repair_attempts": "mặc định sản phẩm"` — một chuỗi văn xuôi lọt qua mọi
    phép kiểm `is not None`, đọc như đã khai, và **không** cho lượt sau biết
    con số nào đã dùng. Một guard nói chuyện được bằng văn xuôi là guard
    thuyết phục được.
    """
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def kiem_danh_tinh_model(model: dict, nguong: dict) -> tuple[str, list[str]]:
    """`(verdict, [thiếu gì])` cho danh tính model + tham số giải mã.

    Verdict:
      `PINNED`                  — có snapshot bất biến, mọi tham số đã ghi
      `MODEL_IDENTITY_UNPINNED` — chỉ có alias trôi
      `DECODING_INCOMPLETE`     — thiếu tham số giải mã cụ thể

    Không gọi provider: câu hỏi *"alias này trỏ snapshot nào"* chỉ provider trả
    lời được, và một lượt gọi để hỏi cũng là một lượt gọi.
    """
    thieu = []
    ten = model.get("model_name")
    ban = model.get("model_version_or_snapshot")
    if not ten:
        thieu.append("thiếu `model_name`")
    if not ban:
        thieu.append(
            f"`model_version_or_snapshot` trống — `{ten}` là ALIAS TRÔI, "
            f"không phải snapshot bất biến")
    for t in TRUONG_DECODING:
        v = model.get(t)
        if v is None:
            thieu.append(f"tham số giải mã `{t}` chưa có giá trị cụ thể")
        elif not _la_so(v):
            thieu.append(
                f"tham số giải mã `{t}` ghi bằng VĂN XUÔI ({v!r}) chứ không "
                f"bằng số — lượt sau không tái lập được")
    if nguong.get("model_identity_policy", {}).get("require_immutable_snapshot") \
            and not ban:
        return "MODEL_IDENTITY_UNPINNED", thieu
    if any("giải mã" in x for x in thieu):
        return "DECODING_INCOMPLETE", thieu
    return ("PINNED" if not thieu else "MODEL_IDENTITY_UNPINNED"), thieu


def cau_hinh_model_hien_tai() -> dict[str, Any]:
    """Danh tính model mà kho SẼ dùng nếu lượt live chạy ngay bây giờ.

    Đọc từ mã sản phẩm, **không gọi provider**: câu hỏi *"alias này trỏ
    snapshot nào"* chỉ provider trả lời được, và một lượt gọi để hỏi cũng là
    một lượt gọi. `None` ở đâu là *thật sự chưa ghim* ở đó.
    """
    import sys
    from pathlib import Path as _P

    goc = _P(__file__).resolve().parents[1]
    if str(goc) not in sys.path:
        sys.path.insert(0, str(goc))
    from app.ai.gemini import MODEL
    from app.ai.pipeline import MAX_SEMANTIC_PROGRAM_ATTEMPTS

    return {
        "provider": "gemini",
        "model_name": MODEL,
        # Alias trôi: `GEMINI_MODEL` không cấp snapshot bất biến, và response
        # `modelVersion` hiện KHÔNG được ghi lại (ghi lại được thì phải sửa
        # `app/ai/gemini.py` — trong `MEASURED_SYSTEM_PATHS`, tức phá đóng
        # băng candidate). Đó là ràng buộc thật, không phải thiếu sót ở đây.
        "model_version_or_snapshot": None,
        "temperature": 0.2,          # mặc định của `call_gemini`
        "top_p": None,               # KHÔNG gửi ⇒ mặc định provider, không ghi
        "max_output_tokens": None,   # KHÔNG gửi ⇒ như trên
        "repair_limit": MAX_SEMANTIC_PROGRAM_ATTEMPTS,
    }


def san_sang_live_tu_cau_hinh(nguong: dict) -> list[str]:
    """Cấu hình THẬT còn thiếu gì trước khi được phép rút và chạy live."""
    _v, thieu = kiem_danh_tinh_model(cau_hinh_model_hien_tai(), nguong)
    if nguong.get("model_identity_policy", {}).get(
            "limited_reproducibility_allowed") is None:
        thieu.append(
            "`limited_reproducibility_allowed` còn NULL — quyết định 'khoá "
            "luận có chấp nhận LIMITED không' là quyết định học thuật của "
            "người hướng dẫn, bộ đo không tự đặt hộ")
    return thieu


def kiem_bang_chung_quy_trach_nhiem(bc: dict, rubric: dict) -> list[str]:
    """Một artifact attribution có đủ tư cách để scorer NHẬN không?

    Danh sách trường đọc TỪ RUBRIC, không chép lại ở đây: chép là tạo bản thứ
    hai, và bản thứ hai sẽ trôi. Rubric đã băm và ghim vào manifest, nên đọc
    từ nó là đọc từ thứ đã khoá trước kết quả.

    Chặn đúng chỗ dễ trượt nhất: một `verdict` không kèm `reason` và
    `authority_hashes` là một lời phán không truy được về đâu — và
    `SYSTEM_EXPRESSIVENESS_GAP` là lời phán tốn kém nhất trong bộ này.
    """
    can = rubric.get("post_draw_adjudication", {}).get(
        "required_evidence_fields", [])
    loi = [f"bằng chứng attribution thiếu `{t}`"
           for t in can if bc.get(t) in (None, "", [], {})]
    vd = bc.get("verdict")
    if vd == "SYSTEM_EXPRESSIVENESS_GAP" and not bc.get("valid_path_proof"):
        loi.append("kết luận SYSTEM_EXPRESSIVENESS_GAP mà KHÔNG có "
                   "`valid_path_proof` — đó là quy trách nhiệm cho hệ bằng "
                   "suy đoán")
    if vd and vd not in _MOI_VERDICT(rubric):
        loi.append(f"`verdict` {vd!r} không nằm trong rubric đã khoá")
    return loi


def _MOI_VERDICT(rubric: dict) -> set[str]:
    """Tập verdict rubric CHO PHÉP — cũng dẫn từ rubric, không liệt tay."""
    ra = {rubric["valid_path_no"]["verdict"],
          rubric["valid_path_unknown"]["verdict"]}
    ra |= set(rubric["valid_path_yes"]["stage_to_class"].values())
    return ra


def kiem_chinh_sach(nguong: dict, *, candidate_hash: str,
                    pool_hash: str) -> list[str]:
    """Chính sách có đủ trường và có trỏ đúng hệ đang đo không?

    Trả danh sách lỗi — rỗng là đạt. KHÔNG ném: người gọi (certifier, readiness
    guard) quyết định làm gì với danh sách ấy.
    """
    loi = []
    for t in TRUONG_BAT_BUOC:
        if t not in nguong:
            loi.append(f"thiếu trường bắt buộc: {t}")
    if nguong.get("created_before_live_run") is not True:
        loi.append("`created_before_live_run` phải là true")
    if nguong.get("candidate_hash") != candidate_hash:
        loi.append(
            f"chính sách trỏ candidate {str(nguong.get('candidate_hash'))[:16]}…"
            f" nhưng hệ hiện tại là {candidate_hash[:16]}…")
    if nguong.get("pool_hash") != pool_hash:
        loi.append(
            f"chính sách trỏ pool {str(nguong.get('pool_hash'))[:16]}… nhưng "
            f"pool hiện tại là {pool_hash[:16]}…")
    return loi
