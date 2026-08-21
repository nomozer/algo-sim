# -*- coding: utf-8 -*-
"""Kiểm HÌNH DẠNG của tập SEALED — CUSTODIAN chạy, TRƯỚC khi niêm phong.

VÌ SAO TÁCH KHỎI RUNNER: `run_sealed_evaluation.py` chạy ĐÚNG MỘT LẦN. Phát
hiện một trường viết sai chính tả ở case thứ 31 khi đang chạy live là mất luôn
lượt duy nhất ấy. Script này nhận đúng cú đánh đó thay cho runner, và nó chạy
được bao nhiêu lần cũng được vì **không gọi API, không đụng hệ đang bị đo**.

NÓ KHÔNG PHẢI, và không được dùng như, một bộ chấm:

- Không kiểm đề bài có ĐÚNG phạm vi không — đó là `eligibility_audit`, việc của
  người, và người phải chịu trách nhiệm bằng chữ ký của mình.
- Không kiểm ground truth có ĐÚNG không — nếu máy kiểm được thì nó đã không còn
  là ground truth độc lập nữa.
- **Không** dùng năng lực hiện tại của IR để loại case. Bài thoả rubric mà IR
  không diễn đạt được thì **ở lại** và thành `capability_gap` — đó là phát hiện
  phải báo cáo. Lọc nó ra là tự nâng tỉ lệ A của mình.

Nó chỉ trả lời một câu: **runner có đọc được tập này không.**

    cd backend && .venv/Scripts/python.exe scripts/validate_sealed_submission.py \\
        ../docs/evaluation/semantic-benchmark/sealed/cases.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

#: Guard CỨNG — cả ba đều nói về NHIỄM DỮ LIỆU: bài đã được hệ phục vụ sẵn,
#: hoặc đã lọt vào prompt. Thiếu một cái là tập mất tính held-out.
METADATA_GUARDS = (
    "no_specialized_module",
    "no_target_template",
    "not_prompt_example",
)

#: MÔ TẢ, không phải guard — và đây là một sửa có chủ đích (2026-08-22).
#:
#: `expressible_in_ir` từng nằm trong nhóm trên và bị bắt phải `true`. Làm thế là
#: dùng NĂNG LỰC HIỆN TẠI CỦA IR làm điều kiện loại case — tức lọc bỏ trước đúng
#: những bài đáng lẽ phải ở lại để thành `capability_gap` trung thực, và làm tỉ
#: lệ A cao lên một cách giả tạo. Rubric §7.2 vốn đã nói ngược lại: *thoả rubric
#: nhưng IR không diễn đạt được ⇒ VẪN Ở TRONG benchmark*.
#:
#: Nay nó chỉ là ghi chú của custodian. `false` KHÔNG phải lỗi, và KHÔNG BAO GIỜ
#: là lý do bỏ một case ra khỏi tập.
METADATA_MO_TA = ("expressible_in_ir",)

ELIGIBILITY_CO = (
    "discrete",
    "finite_input",
    "deterministic_bounded_procedure",
    "in_scope",
)

N_MONG_DOI = 40


def _loi(ds: list[str], case_id, msg: str) -> None:
    ds.append(f"[{case_id}] {msg}")


def kiem(payload: dict) -> tuple[list[str], list[str]]:
    """Trả `(lỗi, cảnh báo)`. Lỗi ⇒ runner sẽ vỡ hoặc chấm sai."""
    from app.simulation.semantic_program.obligations import (
        OBLIGATION_KINDS,
        SEMANTIC_PRESCRIBED_PROCEDURES,
    )

    loi: list[str] = []
    canh_bao: list[str] = []

    cases = payload.get("cases")
    if not isinstance(cases, list):
        return ["File phải là object có khoá `cases` là mảng."], []

    if len(cases) != N_MONG_DOI:
        canh_bao.append(
            f"Có {len(cases)} case, protocol khoá N_planned = {N_MONG_DOI}. "
            "Chạy thiếu ⇒ `evaluation_complete: false` và A/B không được công "
            "bố như kết quả chính."
        )

    da_thay: set[str] = set()
    so_cham_duoc = 0

    for i, c in enumerate(cases):
        cid = (c or {}).get("case_id", f"#{i}")
        if not isinstance(c, dict):
            _loi(loi, cid, "case không phải object")
            continue

        if not isinstance(c.get("case_id"), str) or not c["case_id"]:
            _loi(loi, cid, "thiếu `case_id`")
        elif c["case_id"] in da_thay:
            _loi(loi, cid, "`case_id` TRÙNG — báo cáo sẽ lẫn hai case làm một")
        else:
            da_thay.add(c["case_id"])

        if not isinstance(c.get("problem_text"), str) or not c["problem_text"].strip():
            _loi(loi, cid, "thiếu `problem_text` (runner không có gì để gửi)")

        src = c.get("source")
        if not isinstance(src, dict) or not src.get("book"):
            canh_bao.append(f"[{cid}] thiếu `source.book` — không truy được nguồn đề")

        # ── eligibility: người phán, máy chỉ kiểm ĐÃ PHÁN CHƯA ──
        el = c.get("eligibility_audit")
        if not isinstance(el, dict):
            _loi(loi, cid, "thiếu `eligibility_audit` — chưa ai audit case này")
        else:
            thieu = [k for k in ELIGIBILITY_CO if k not in el]
            if thieu:
                _loi(loi, cid, f"`eligibility_audit` thiếu: {', '.join(thieu)}")
            if el.get("in_scope") is False:
                _loi(loi, cid, "`in_scope: false` — case ngoài phạm vi không được "
                               "nằm trong tập đo")

        # ── metadata guard: thiếu MỘT cái là benchmark mất tính held-out ──
        md = c.get("metadata")
        if not isinstance(md, dict):
            _loi(loi, cid, "thiếu `metadata` (3 guard held-out)")
        else:
            for g in METADATA_GUARDS:
                if g not in md:
                    _loi(loi, cid, f"metadata thiếu guard `{g}`")
                elif md[g] is not True:
                    _loi(loi, cid, f"metadata `{g}` = {md[g]!r}, phải là true — "
                                   "case này làm hỏng tính held-out")
            # MÔ TẢ, không phải guard. `false` là hợp lệ và ĐÁNG GIÁ: nó báo
            # trước một `capability_gap` mà benchmark sẽ đo được thật.
            if md.get("expressible_in_ir") is False:
                canh_bao.append(
                    f"[{cid}] `expressible_in_ir: false` — case này VẪN Ở LẠI "
                    "trong tập và dự kiến cho `capability_gap`. Đó là phát hiện "
                    "phải báo cáo, không phải lý do loại case (rubric §7.2)."
                )

        pp = c.get("prescribed_procedure")
        if pp is not None and pp not in SEMANTIC_PRESCRIBED_PROCEDURES:
            _loi(loi, cid, f"`prescribed_procedure` = {pp!r} ngoài tập đóng")

        # ── ground truth ──
        gt = c.get("ground_truth")
        if not isinstance(gt, dict):
            _loi(loi, cid, "thiếu `ground_truth`")
            continue
        if not gt.get("kind"):
            _loi(loi, cid, "`ground_truth.kind` trống — không biết ai/cái gì dựng")
        if not gt.get("provenance"):
            canh_bao.append(f"[{cid}] `ground_truth.provenance` trống")

        exp = gt.get("expected")
        if exp is None or (isinstance(exp, list) and not exp):
            canh_bao.append(
                f"[{cid}] `expected` rỗng ⇒ case này sẽ được đếm UNGRADED, không "
                "vào tử số lẫn mẫu số. Cố ý thì bỏ qua."
            )
            continue
        if isinstance(exp, dict):
            _loi(loi, cid, "`expected` là object ánh xạ TÊN BIẾN → giá trị. Dạng "
                           "này bị bỏ: tên biến do LLM đặt, custodian không được "
                           "phép đoán. Dùng [{obligation_kind, value}].")
            continue
        if not isinstance(exp, list):
            _loi(loi, cid, f"`expected` phải là mảng, nhận {type(exp).__name__}")
            continue

        dem_kind: dict[str, int] = {}
        for m in exp:
            if not isinstance(m, dict):
                _loi(loi, cid, f"mục expected không phải object: {m!r}")
                continue
            k = m.get("obligation_kind")
            if k not in OBLIGATION_KINDS:
                _loi(loi, cid, f"`obligation_kind` = {k!r} ngoài taxonomy "
                               f"({len(OBLIGATION_KINDS)} giá trị hợp lệ)")
                continue
            if "value" not in m:
                _loi(loi, cid, f"{k}: thiếu `value`")
            dem_kind[k] = dem_kind.get(k, 0) + 1

        for k, n in dem_kind.items():
            if n > 1 and any(
                isinstance(m, dict) and m.get("obligation_kind") == k
                and not isinstance(m.get("index"), int)
                for m in exp
            ):
                _loi(loi, cid, f"{k}: có {n} mục cùng loại nhưng thiếu `index` — "
                               "runner sẽ trả UNGRADED chứ không đoán")
        so_cham_duoc += 1

    if so_cham_duoc == 0 and cases:
        loi.append(
            "KHÔNG case nào chấm được bằng oracle độc lập — báo cáo sẽ chỉ có "
            "phán quyết nội bộ, tức không kiểm chứng được gì từ bên ngoài."
        )
    elif cases and so_cham_duoc < len(cases) * 0.5:
        canh_bao.append(
            f"Chỉ {so_cham_duoc}/{len(cases)} case có ground truth chấm được. "
            "Tỉ lệ correctness sẽ dựa trên mẫu nhỏ."
        )

    return loi, canh_bao


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    duong = Path(sys.argv[1])
    if not duong.exists():
        print(f"Không có file: {duong}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(duong.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"JSON không parse được: {e}", file=sys.stderr)
        return 2

    loi, canh_bao = kiem(payload)

    for c in canh_bao:
        print(f"  ⚠ {c}")
    for l in loi:
        print(f"  ✗ {l}")

    n = len(payload.get("cases") or [])
    print(f"\n{n} case · {len(loi)} lỗi · {len(canh_bao)} cảnh báo")
    if loi:
        print("\nSỬA HẾT LỖI RỒI MỚI NIÊM PHONG. Runner chỉ chạy một lần.")
        return 1
    print("\nHình dạng hợp lệ. Niêm phong bằng scripts/seal_benchmark.py.")
    print("Nhắc: script này KHÔNG kiểm đề có đúng phạm vi hay ground truth có "
          "đúng không — hai việc đó thuộc về người.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
