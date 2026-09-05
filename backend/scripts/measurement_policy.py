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
    "chinh_sach_da_tieu",
    "kiem_chinh_sach",
    "kiem_danh_tinh_model",
    "cau_hinh_model_hien_tai",
    "san_sang_live_tu_cau_hinh",
    "kiem_bang_chung_quy_trach_nhiem",
    "kiem_tham_so_giai_ma",
    "tham_so",
    "derive_application_call_budget",
    "CHE_DO_THAM_SO",
    "RESPONSE_MODEL_VERSION",
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


#: Ba trạng thái của một tham số giải mã. Trước 2026-09-05 chỉ có hai — "có
#: số" và "None" — và hai thì không đủ: `None` gộp *"không gửi"* với *"provider
#: có mặc định nhưng ta không quan sát được"*. Hai điều đó khác nhau ở đúng chỗ
#: quan trọng: cái đầu ta biết hết, cái sau ta biết là mình không biết.
CHE_DO_THAM_SO = ("explicit", "not_sent", "provider_default_unobserved")


def tham_so(che_do: str, gia_tri: Any = None) -> dict[str, Any]:
    """Dựng một tham số giải mã CÓ KIỂU."""
    return {"mode": che_do, "value": gia_tri}


def kiem_tham_so_giai_ma(ts: Any, nguong: dict) -> list[str]:
    """Hợp đồng typed cho tham số giải mã. Trả danh sách lỗi — rỗng là đạt.

    Luật, và mỗi luật chặn đúng một cách nói dối:

    - `explicit` phải kèm **số** — `bool` không tính (`True` là `int` trong
      Python, nên `temperature=True` lọt mọi phép kiểm `isinstance(int)`).
    - `not_sent` phải kèm `value = null`. Điền một con số cho tham số **không
      được gửi** là bịa lại lịch sử của lượt đo: nó khiến người đọc sau tưởng
      request mang giá trị ấy.
    - `provider_default_unobserved` chỉ hợp lệ trong chế độ LIMITED. Ngoài chế
      độ ấy, "provider có mặc định nào đó" là một câu chưa đo được, và một
      phép đo không được xây trên câu chưa đo được.
    - **Chuỗi văn xuôi không thay được giá trị có kiểu** — đây là lỗ đã đóng ở
      wave trước ở mức "số hay không phải số"; ở đây đóng thêm một tầng, vì
      `{"mode": ...}` là chỗ tiếp theo văn xuôi sẽ lẻn vào.
    """
    lm = nguong.get("model_identity_policy", {}).get(
        "limited_reproducibility_allowed") is True
    loi = []
    if not isinstance(ts, dict):
        return [f"`decoding_parameters` phải là bảng có kiểu, nhận {type(ts).__name__}"]
    for ten, v in ts.items():
        if not isinstance(v, dict) or "mode" not in v:
            loi.append(f"`{ten}` không phải giá trị CÓ KIỂU ({v!r}) — cần "
                       f"{{'mode': …, 'value': …}}")
            continue
        m, gt = v.get("mode"), v.get("value")
        if m not in CHE_DO_THAM_SO:
            loi.append(f"`{ten}` có `mode` lạ: {m!r}")
        elif m == "explicit" and not _la_so(gt):
            loi.append(f"`{ten}` khai `explicit` nhưng `value` không phải số "
                       f"({gt!r})")
        elif m == "not_sent" and gt is not None:
            loi.append(f"`{ten}` khai `not_sent` nhưng `value` = {gt!r} — "
                       f"tham số KHÔNG gửi thì manifest không được mang giá trị")
        elif m == "provider_default_unobserved" and not lm:
            loi.append(f"`{ten}` khai `provider_default_unobserved` nhưng "
                       f"chính sách CHƯA cho phép LIMITED")
    return loi


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
      `LIMITED_ACCEPTED`        — alias, nhưng chính sách ĐÃ cho phép LIMITED
                                  và mọi thứ ghi lại được đều đã ghi
      `MODEL_IDENTITY_UNPINNED` — alias trôi, chính sách CHƯA cho phép LIMITED
      `DECODING_INCOMPLETE`     — thiếu tham số giải mã cụ thể

    ⚠️ `LIMITED_ACCEPTED` **không** phải `PINNED` đổi tên. Danh sách `thiếu`
    vẫn khai alias là alias — quyết định học thuật cho phép **ghi nhận** một
    lượt đo kèm giới hạn, nó không xoá giới hạn ấy đi.

    Không gọi provider: câu hỏi *"alias này trỏ snapshot nào"* chỉ provider trả
    lời được, và một lượt gọi để hỏi cũng là một lượt gọi.
    """
    mip = nguong.get("model_identity_policy", {})
    lm = mip.get("limited_reproducibility_allowed") is True
    thieu = []
    ten = model.get("model_name")
    ban = model.get("model_version_or_snapshot")
    if not ten:
        thieu.append("thiếu `model_name`")
    if not ban:
        thieu.append(
            f"`model_version_or_snapshot` trống — `{ten}` là ALIAS TRÔI, "
            f"không phải snapshot bất biến")

    ts = model.get("decoding_parameters")
    if ts is not None:                       # hợp đồng typed (manifest ≥ 1.2)
        thieu += [f"tham số giải mã: {x}" for x in
                  kiem_tham_so_giai_ma(ts, nguong)]
        if not _la_so(model.get("repair_limit")):
            thieu.append("tham số giải mã `repair_limit` chưa phải một số")
    else:                                    # đường phẳng cũ (manifest 1.1)
        for t in TRUONG_DECODING:
            v = model.get(t)
            if v is None:
                thieu.append(f"tham số giải mã `{t}` chưa có giá trị cụ thể")
            elif not _la_so(v):
                thieu.append(
                    f"tham số giải mã `{t}` ghi bằng VĂN XUÔI ({v!r}) chứ "
                    f"không bằng số — lượt sau không tái lập được")

    # Thứ tự có ý nghĩa. Alias KHI CHƯA cho phép LIMITED là khiếm khuyết cơ
    # bản hơn: chưa biết đo model nào thì tham số giải mã của nó là câu hỏi
    # sau. Nhưng khi LIMITED đã được chấp nhận, tham số giải mã lại phải chặn
    # được — không thì `LIMITED_ACCEPTED` sẽ cấp phép cho một manifest mà
    # chính tham số gửi đi cũng không khai nổi.
    thieu_gm = any("tham số giải mã" in x for x in thieu)
    if mip.get("require_immutable_snapshot") and not ban and not lm:
        return "MODEL_IDENTITY_UNPINNED", thieu
    if thieu_gm:
        return "DECODING_INCOMPLETE", thieu
    if mip.get("require_immutable_snapshot") and not ban:
        return "LIMITED_ACCEPTED", thieu
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
    from app.ai.gemini import (
        BACKOFF_BASE_SECONDS,
        MAX_ATTEMPTS,
        MODEL,
        TRANSIENT_STATUS,
    )
    from app.ai.pipeline import MAX_SEMANTIC_PROGRAM_ATTEMPTS

    return {
        "provider": "gemini",
        "model_name": MODEL,
        # Alias trôi: `GEMINI_MODEL` không cấp snapshot bất biến, và response
        # `modelVersion` hiện KHÔNG được ghi lại (ghi lại được thì phải sửa
        # `app/ai/gemini.py` — trong `MEASURED_SYSTEM_PATHS`, tức phá đóng
        # băng candidate). Đó là ràng buộc thật, không phải thiếu sót ở đây.
        "model_version_or_snapshot": None,
        "response_model_version": RESPONSE_MODEL_VERSION,
        "sdk": _sdk_httpx(),
        "api_endpoint_class": ENDPOINT,
        # Ba trạng thái, đọc từ `call_gemini`: `temperature` ĐƯỢC gửi (mặc
        # định 0.2); `top_p` và `max_output_tokens` **không có mặt** trong
        # `generationConfig` — nên chúng là `not_sent`, không phải "null".
        "decoding_parameters": {
            "temperature": tham_so("explicit", 0.2),
            "top_p": tham_so("not_sent"),
            "max_output_tokens": tham_so("not_sent"),
        },
        "repair_limit": MAX_SEMANTIC_PROGRAM_ATTEMPTS,
        "transport_retry_policy": {
            "max_attempts": MAX_ATTEMPTS,
            "backoff_base_seconds": BACKOFF_BASE_SECONDS,
            "retry_on_status": sorted(TRANSIENT_STATUS),
            "khai": "retry TRANSPORT (HTTP) — KHÔNG đụng vòng sửa ngữ nghĩa",
        },
    }


#: `call_gemini` trả về **đúng một chuỗi text**. `body["modelVersion"]`,
#: `finishReason`, request-id đều bị bỏ ngay tại chỗ parse — caller không có
#: đường nào chạm tới. Ghi thành hằng số thay vì để trống, vì "không có" và
#: "chưa điền" đọc giống nhau trong artifact mà nghĩa thì khác hẳn.
RESPONSE_MODEL_VERSION = "UNAVAILABLE_TO_RUNNER"
ENDPOINT = "generativelanguage.googleapis.com/v1beta/models/:generateContent"


def _sdk_httpx() -> dict[str, str]:
    """Không có SDK Gemini — kho gọi REST thẳng bằng `httpx`."""
    import httpx

    return {"package": "httpx", "version": httpx.__version__,
            "khai": "gọi REST trực tiếp, KHÔNG qua SDK google-genai"}


def derive_application_call_budget(*, selected_cases: int,
                                   analyze_calls_per_case: int,
                                   synthesis_attempt_limit: int,
                                   calls_per_attempt: int) -> int:
    """Trần CỨNG số lượt gọi logic cho MỘT chặng đo.

        trần = số_ca × (analyze_mỗi_ca + attempt_tối_đa × call_mỗi_attempt)

    Dẫn từ **call graph**, không từ số đã dùng ở V1/V2 — một trần suy từ lượt
    trước là một trần đã biết kết quả, và nó sẽ vừa khít với thứ đã xảy ra
    thay vì với thứ có thể xảy ra.

    Đối chiếu với `app/ai/pipeline.py`: đường hình học có **đúng hai** chỗ gọi
    provider — `stage_semantic_analyze` (1 lượt) và `stage_semantic_program`
    (1 lượt mỗi attempt, tối đa `MAX_SEMANTIC_PROGRAM_ATTEMPTS`). Khoá bởi
    `test_D4` bằng AST, nên thêm một chỗ gọi thứ ba ở `app/` sẽ làm test đỏ
    chứ không lặng lẽ làm trần hụt.
    """
    for ten, v in (("selected_cases", selected_cases),
                   ("analyze_calls_per_case", analyze_calls_per_case),
                   ("synthesis_attempt_limit", synthesis_attempt_limit),
                   ("calls_per_attempt", calls_per_attempt)):
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ValueError(f"`{ten}` phải là số nguyên ≥ 0, nhận {v!r}")
    return selected_cases * (
        analyze_calls_per_case + synthesis_attempt_limit * calls_per_attempt)


def san_sang_live_tu_cau_hinh(nguong: dict) -> tuple[list[str], list[str]]:
    """`(chặn, giới hạn đã khai)` — hai danh sách, cố ý không gộp.

    Gộp chúng là lỗi đã mắc ở bản trước: alias trôi bị đếm như một **chặn**,
    nên sau khi người hướng dẫn chấp nhận `LIMITED` thì readiness vẫn đứng ở
    `CONDITIONAL` mà không nói được còn thiếu gì. Alias vẫn là alias — nhưng
    dưới `LIMITED_ACCEPTED` nó là một **giới hạn đã khai trước**, không phải
    một việc chưa làm. Khai nó là bắt buộc; nó chặn thì không.
    """
    mip = nguong.get("model_identity_policy", {})
    lm = mip.get("limited_reproducibility_allowed")
    v, thieu = kiem_danh_tinh_model(cau_hinh_model_hien_tai(), nguong)
    if lm is None:
        return ([
            "`limited_reproducibility_allowed` còn NULL — quyết định 'khoá "
            "luận có chấp nhận LIMITED không' là quyết định học thuật của "
            "người hướng dẫn, bộ đo không tự đặt hộ"], thieu)
    if v == "LIMITED_ACCEPTED":
        return [], thieu + [
            f"tái lập ở mức {v}: không tuyên bố bit-for-bit; alias, thời "
            f"điểm, tham số gửi và raw output đều phải ghi đủ"]
    return (thieu, []) if v != "PINNED" else ([], [])


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


def chinh_sach_da_tieu(nguong: dict, *, candidate_hash: str) -> bool:
    """Chính sách này thuộc về một lượt đo ĐÃ XONG hay một lượt sắp chạy?

    Hai điều kiện, và cần **cả hai** — một mình mỗi cái đều nói sai:

        pool đã rút          `da_rut` khác `null` trong con dấu nó trỏ tới
        candidate đã đổi     hệ hiện tại khác hệ nó niêm phong

    Chỉ "candidate đổi" thì đó là **lỗi thật**: ai đó sửa mã sản phẩm giữa lúc
    một lượt đo đang chờ chạy. Chỉ "pool đã rút" thì lượt đo vừa xong trên đúng
    hệ ấy, và chính sách vẫn mô tả hệ đang chạy. Cả hai cùng lúc mới là *"lượt
    đo này đã khép, tài liệu của nó nay là bằng chứng lịch sử"*.

    ⚠️ Vì sao KHÔNG sửa file chính sách cho khớp candidate mới: băm của nó
    (`460e0ce5…` với V3) đã nằm trong manifest của lượt đã chạy, và toàn bộ giá
    trị của nó nằm ở chỗ **khoá TRƯỚC kết quả**. Sửa nó bây giờ là hồi tố đúng
    thứ nó tồn tại để chặn. Lượt đo sau cần một chính sách MỚI của riêng nó.
    """
    from pathlib import Path as _P

    if nguong.get("candidate_hash") == candidate_hash:
        return False
    dau = (_P(__file__).resolve().parents[2] / "docs" / "evaluation"
           / "geometry" / "curved-v3" / "V3_SEAL.json")
    if not dau.exists():
        return False
    try:
        d = json.loads(dau.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(d.get("da_rut")) and d.get("pool_hash") == nguong.get("pool_hash")


def kiem_chinh_sach(nguong: dict, *, candidate_hash: str,
                    pool_hash: str) -> list[str]:
    """Chính sách có đủ trường và có trỏ đúng hệ đang đo không?

    Trả danh sách lỗi — rỗng là đạt. KHÔNG ném: người gọi (certifier, readiness
    guard) quyết định làm gì với danh sách ấy.

    Chính sách của một lượt đo **đã tiêu** được miễn hai phép so danh tính —
    xem `chinh_sach_da_tieu`. Nó vẫn phải đủ trường: một tài liệu lịch sử thiếu
    trường thì không đọc lại được, và đọc lại được là toàn bộ công dụng còn lại
    của nó.
    """
    loi = []
    da_tieu = chinh_sach_da_tieu(nguong, candidate_hash=candidate_hash)
    for t in TRUONG_BAT_BUOC:
        if t not in nguong:
            loi.append(f"thiếu trường bắt buộc: {t}")
    if nguong.get("created_before_live_run") is not True:
        loi.append("`created_before_live_run` phải là true")
    if not da_tieu:
        if nguong.get("candidate_hash") != candidate_hash:
            loi.append(
                f"chính sách trỏ candidate "
                f"{str(nguong.get('candidate_hash'))[:16]}… nhưng hệ hiện tại "
                f"là {candidate_hash[:16]}…")
        if nguong.get("pool_hash") != pool_hash:
            loi.append(
                f"chính sách trỏ pool {str(nguong.get('pool_hash'))[:16]}… "
                f"nhưng pool hiện tại là {pool_hash[:16]}…")
    return loi
