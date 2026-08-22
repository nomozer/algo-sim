# -*- coding: utf-8 -*-
"""GROUND TRUTH ĐỘC LẬP cho SEALED — dựng `sealed/cases.json` từ 40 ID đã chốt.

ĐỘC LẬP VỚI HỆ ĐANG BỊ ĐO, kiểm được bằng mắt: file này không `import` một dòng
nào từ `backend/app`, không đụng `SemanticProgramInterpreter`, không đụng
checker/route/renderer của production. Chỉ có thư viện chuẩn Python.

Vì sao tính bằng máy chứ không tính tay: 40 đáp án tính tay là 40 cơ hội sai số
học, và một đáp án sai sẽ âm thầm chấm hệ là SAI trong khi nó ĐÚNG.

HAI LOẠI CASE, khai rõ để kiểm toán được:

  ĐỀ CÓ DỮ LIỆU  — sách cho sẵn số liệu; ground truth tính thẳng.
  ĐỀ TRỪU TƯỢNG  — sách viết "nhập từ bàn phím"; custodian CỤ THỂ HOÁ dữ liệu.
                   Mỗi trường hợp ghi rõ trong `provenance`.

Case nào **không có nghĩa vụ nào trong taxonomy 9 loại diễn đạt được** thì
`expected` để RỖNG và ghi lý do. Đó là câu trả lời trung thực: bịa một nghĩa vụ
gần đúng rồi chấm theo nó thì con số thu về không còn nghĩa. Runner đếm chúng là
`UNGRADED`, tách hẳn khỏi tử số lẫn mẫu số.

    python sealed_ground_truth.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEALED = HERE.parent / "sealed"

PY = "tính bằng Python thuần trong sealed_ground_truth.py; không dùng hệ đang được đánh giá"
SACH = "dữ liệu và/hoặc đáp án in sẵn trong SGK"
CUTHE = "đề gốc nhận dữ liệu từ bàn phím; custodian cụ thể hoá dữ liệu; " + PY

# ── lời giải độc lập ─────────────────────────────────────────────
def _uoc(n):            return [d for d in range(1, n) if n % d == 0]
def _uoc_ke_n(n):       return [d for d in range(1, n + 1) if n % d == 0]
def _nt(n):
    if n < 2: return False
    d = 2
    while d * d <= n:
        if n % d == 0: return False
        d += 1
    return True
def _merge(s1, s2):
    S, l = "", min(len(s1), len(s2))
    for i in range(l): S += s1[i] + s2[i]
    return S + (s2[l:] if len(s1) < len(s2) else s1[l:])


#: id → (kind|None, giá trị, provenance, [đề đã cụ thể hoá], [ghi chú])
GT: dict[str, tuple] = {
    "T10-C5-006": ("total_mapping", {"a": 5, "b": -1}, PY, None, None),
    "T10-C5-008": ("derived_sequence", ["010", "1" + "0" * 6], PY, None, None),
    "T10-C5-010": ("total_mapping",
                   {"chu_vi": round(2 * 3.14 * 4.5, 4),
                    "dien_tich": round(3.14 * 4.5 ** 2, 4)},
                   "bán kính R = 4.5 và pi = 3.14 lấy từ chương trình mẫu "
                   "trang 96 của SGK; " + PY, None, None),
    "T10-C5-013": ("total_mapping", {"x": 7, "y": 10}, PY, None, None),
    "T10-C5-020": (None, None,
                   "đề yêu cầu một PHÁN QUYẾT (chẵn/lẻ). Taxonomy 9 nghĩa vụ "
                   "cố ý không có `predicate_verdict`, nên không nghĩa vụ nào "
                   "diễn đạt được kết quả này.", None,
                   "UNGRADED — phán quyết nhị phân"),
    "T10-C5-024": (None, None,
                   "đề yêu cầu một PHÁN QUYẾT (có phải năm nhuận không). Xem "
                   "T10-C5-020.", None, "UNGRADED — phán quyết nhị phân"),
    "T10-C5-025": ("aggregate_matching", sum(range(10)), SACH + "; " + PY,
                   None, None),
    "T10-C5-026": ("aggregate_matching", sum(range(1, 11)),
                   "đề để n tự do; custodian chọn n = 10; " + PY,
                   "Cho n = 10. Thực hiện đoạn chương trình sau rồi cho biết "
                   "giá trị của S: S = 0 ; for k in range(1, n+1): S = S + k",
                   None),
    "T10-C5-027": ("derived_sequence", _uoc_ke_n(10),
                   "đề nêu sẵn ví dụ n = 10 với kết quả 1, 2, 5, 10; " + PY,
                   "Cho số tự nhiên n = 10. Hãy liệt kê các ước số của n theo "
                   "thứ tự tăng dần.", None),
    "T10-C5-033": ("aggregate_matching", sum(range(2, 101, 2)), PY, None, None),
    "T10-C5-037": ("derived_sequence", list(range(1, 101)),
                   "đề in 1..100 thành 10 hàng mỗi hàng 10 số; ground truth là "
                   "dãy giá trị, không phải cách trình bày; " + PY, None, None),
    "T10-C5-038": ("derived_sequence", [1, "One", False],
                   "ba ý a, b, c của đề. Ý d) A[len(A)] cố ý vượt chỉ số và "
                   "sinh lỗi, không phải một giá trị nên không đưa vào ground "
                   "truth; " + PY, None,
                   "ý d) là trường hợp lỗi, đã loại khỏi expected"),
    "T10-C5-039": ("derived_sequence", [x for x in [3, 8, 1, 10, 7, 4] if x % 2 == 0],
                   CUTHE,
                   "Cho dãy các số nguyên A: 3 8 1 10 7 4. Hãy liệt kê các số "
                   "chẵn của A theo thứ tự xuất hiện.", None),
    "T10-C5-045": ("derived_sequence", list(reversed(["An", "Binh", "Cuong", "Dung"])),
                   CUTHE,
                   "Cho danh sách tên học sinh theo thứ tự đã nhập: An, Binh, "
                   "Cuong, Dung. Hãy in danh sách các tên này theo thứ tự "
                   "ngược lại với thứ tự đã nhập.", None),
    "T10-C5-052": ("derived_sequence",
                   [len("123&*()+-ABC"), len("1010110&0101001"), len("Tây Nguyên")],
                   SACH + "; " + PY, None, None),
    "T10-C5-062": ("first_match_index", "abababab".find("ab", 4), SACH + "; " + PY,
                   None, None),
    "T10-C5-064": ("aggregate_matching", len([12, 7, 25, 9, 18]), CUTHE,
                   "Nhập vào dãy số nguyên: 12 7 25 9 18. Hãy cho biết đã nhập "
                   "bao nhiêu số.", None),
    "T10-C5-065": ("derived_sequence", "Hoc   sinh  lop   10".split(), CUTHE,
                   'Cho xâu kí tự S = "Hoc   sinh  lop   10", giữa các từ có '
                   "thể có nhiều dấu cách. Hãy tách S thành danh sách các từ, "
                   "bỏ hết dấu cách thừa.", None),
    "T10-C5-071": (None, None,
                   "đề yêu cầu một PHÁN QUYẾT (n có là số nguyên tố không). "
                   "Xem T10-C5-020.", None, "UNGRADED — phán quyết nhị phân"),
    "T10-C5-076": ("derived_sequence", [x for x in range(11, 30) if _nt(x)],
                   "đề để m, n tự do; custodian chọn m = 10, n = 30; " + PY,
                   "Cho hai số tự nhiên m = 10 và n = 30. Hãy liệt kê các số "
                   "nguyên tố nằm trong khoảng từ m đến n theo thứ tự tăng dần.",
                   None),
    "T10-C5-079": ("derived_sequence", list(_merge("1111", "0000")),
                   SACH + " (ví dụ s1 = \"1111\", s2 = \"0000\" cho kết quả "
                   "\"10101010\"); " + PY, None, None),
    "T10-C5-080": (None, None,
                   "đề định nghĩa một HÀM số học (a+b) mũ c. Không nghĩa vụ nào "
                   "trong taxonomy 9 loại diễn đạt được một phép tính vô hướng "
                   "thuần tuý như vậy.", None,
                   "UNGRADED — số học vô hướng, ngoài taxonomy"),
    "T10-C5-084": ("total_mapping", {"a": 1, "b": 2},
                   "hàm f gán lại a, b ở PHẠM VI CỤC BỘ nên a, b ở chương trình "
                   "chính không đổi — đó chính là điểm bài học của Bài 28; " + PY,
                   None, "đáp án phụ thuộc quy tắc phạm vi biến, đã ghi rõ"),
    "T10-C5-085": ("aggregate_matching", 2 * (1 + 2) + 10, SACH + "; " + PY,
                   None, None),
    "T10-C5-086": ("derived_sequence", [x for x in [1, 7, 3, 10, 5] if x >= 5],
                   CUTHE,
                   "Cho danh sách A: 1 7 3 10 5 và số x = 5. Hãy lập danh sách "
                   "B gồm các phần tử của A lớn hơn hoặc bằng x, giữ nguyên thứ "
                   "tự.", None),
    "T10-C5-088": ("derived_sequence", [x for x in [3, -5, 8, 0, -2, 7] if x > 0],
                   CUTHE,
                   "Cho dãy số nguyên A: 3 -5 8 0 -2 7. Hãy lập danh sách B "
                   "gồm các phần tử lớn hơn 0 của A, giữ nguyên thứ tự.", None),
    "T10-C5-089": ("derived_sequence", [s[0] for s in ["Hoa", "Lan", "Cuc", "Mai"]],
                   CUTHE,
                   "Cho danh sách sList gồm các xâu kí tự: Hoa, Lan, Cuc, Mai. "
                   "Hãy lập danh sách cList gồm kí tự đầu tiên của mỗi xâu "
                   "tương ứng trong sList.", None),
    "T10-C5-094": ("total_mapping", {"tong": 17 + 5, "hieu": 17 - 5,
                                     "thuong": round(17 / 5, 4)}, CUTHE,
                   "Cho hai số nguyên m = 17 và n = 5. Hãy tính tổng, hiệu và "
                   "thương của hai số này.", None),
    "T10-C5-099": (None, None,
                   "đề tìm NGHIỆM của phương trình bậc hai và phải xét đủ các "
                   "trường hợp (vô nghiệm / nghiệm kép / hai nghiệm). Không "
                   "nghĩa vụ nào trong taxonomy diễn đạt được một tập nghiệm "
                   "phân nhánh như vậy.", None,
                   "UNGRADED — tập nghiệm phân nhánh, ngoài taxonomy"),
    "T10-C5-103": ("total_mapping",
                   {"ho": "Nguyễn", "dem": "Thị Mai", "ten": "Hương"},
                   SACH + " (ví dụ \"Nguyễn Thị Mai Hương\"); " + PY, None, None),
    "T10-C5-104": ("aggregate_matching", round(600 * 1.62 / 9.8, 3),
                   "công thức P = P0 × g / 9.8 và bảng gravities in ở trang 154; "
                   "custodian chọn P0 = 600 N và hành tinh Mặt Trăng "
                   "(g = 1.62); " + PY,
                   "Trọng lượng của một người trên Trái Đất là 600 N. Biết gia "
                   "tốc trọng trường trên Trái Đất là 9,8 m/s² và trên Mặt "
                   "Trăng là 1,62 m/s². Hãy tính trọng lượng của người đó trên "
                   "Mặt Trăng.", None),
    "T11CS-C6-027": ("derived_sequence", ["Huyền", "Nam"],
                     "dữ liệu điểm thi in ở trang 98 của SGK (Sơn 5.6, Huyền "
                     "7.4, Nam 7.8, Hùng 8.4, Hương 8.9, Hà 9.5); custodian "
                     "chọn khoảng điểm 6–8 đúng như ví dụ trong đề; " + PY,
                     "Cho danh sách điểm thi: Sơn 5.6, Huyền 7.4, Nam 7.8, "
                     "Hùng 8.4, Hương 8.9, Hà 9.5. Hãy liệt kê tên các học "
                     "sinh có điểm nằm trong khoảng từ 6 đến 8, theo thứ tự "
                     "điểm tăng dần.", None),
    "T11CS-C6-041": ("aggregate_matching", sum(range(6)),
                     "chương trình trong đề dùng range(n+1) nên tổng đúng bằng "
                     "1+2+...+n; custodian chọn n = 5; " + PY,
                     "Cho n = 5. Chương trình sau tính tổng: S = 0 ; "
                     "for i in range(n+1): S = S + i. Hãy cho biết giá trị của "
                     "S sau khi chương trình chạy xong.", None),
    "T11CS-C6-053": (None, None,
                     "đề yêu cầu một PHÁN QUYẾT (CÓ/KHÔNG là số nguyên tố). "
                     "Xem T10-C5-020.", None, "UNGRADED — phán quyết nhị phân"),
    "T11CS-C6-056": (None, None,
                     "đề yêu cầu một PHÁN QUYẾT (dãy có là hoán vị của 1..n "
                     "không). Xem T10-C5-020.", None,
                     "UNGRADED — phán quyết nhị phân"),
    "T11CS-C6-057": (None, None,
                     "đề yêu cầu một PHÁN QUYẾT (có hai phần tử trùng nhau "
                     "không). Xem T10-C5-020.", None,
                     "UNGRADED — phán quyết nhị phân"),
    "T11CS-C6-058": (None, None,
                     "đề yêu cầu một PHÁN QUYẾT (xâu có đối xứng không). Xem "
                     "T10-C5-020.", None, "UNGRADED — phán quyết nhị phân"),
    "T11CS-C6-068": ("derived_sequence", ["Hà", "Hoa", "Bình"],
                     "hàm insert() của thư viện LinkedList trong SGK chèn vào "
                     "ĐẦU danh sách, nên duyệt từ head ra thứ tự ngược với thứ "
                     "tự chèn; " + PY, None,
                     "đáp án phụ thuộc ngữ nghĩa insert-at-head của thư viện "
                     "LinkedList định nghĩa ở Bài 30, đã ghi rõ"),
    "T11CS-C6-070": ("derived_sequence", [5, 2],
                     "danh sách liên kết minh hoạ trong Bài 30 là 5 → 2 → 8; "
                     "xoá phần tử cuối còn 5 → 2; " + PY,
                     "Cho danh sách liên kết L gồm các phần tử theo thứ tự từ "
                     "đầu danh sách: 5, 2, 8. Hãy xoá phần tử cuối cùng của L "
                     "và cho biết danh sách thu được.", None),
    "T11ICT-003": ("aggregate_matching", (5 - 1) * 5,
                   "GIMP chèn số khung hình trung gian vào GIỮA mỗi cặp lớp "
                   "liền kề: 5 lớp có 4 khoảng, mỗi khoảng 5 khung ⇒ 20; " + PY,
                   None,
                   "đáp án phụ thuộc ngữ nghĩa hiệu ứng Blend của GIMP, đã ghi rõ"),
}


def main() -> int:
    sel = json.loads((HERE / "EXTERNAL_SELECTION.json").read_text(encoding="utf-8"))
    uni = {r["source_id"]: r for r in json.loads(
        (HERE / "source_universe.json").read_text(encoding="utf-8"))["records"]}

    thieu = [i for i in sel["source_ids"] if i not in GT]
    if thieu:
        print("Thiếu ground truth cho:", thieu, file=sys.stderr)
        return 1

    cases = []
    for sid in sel["source_ids"]:
        r = uni[sid]
        kind, val, prov, de_moi, note = GT[sid]
        exp = [{"obligation_kind": kind, "value": val}] if kind else []
        c = {
            "case_id": sid,
            "source": {
                "book": r["book"],
                "location": f"trang {r['page']}, {r['exercise_number_or_position']}",
                "section_or_chapter": r["section_or_chapter"],
                "page": r["page"],
                "exercise_number_or_position": r["exercise_number_or_position"],
                "source_id": sid,
            },
            "problem_text": de_moi or r["problem_text"],
            "eligibility_audit": {
                "discrete": True, "finite_input": True,
                "deterministic_bounded_procedure": True, "in_scope": True,
            },
            "metadata": {
                "no_specialized_module": True, "no_target_template": True,
                "not_prompt_example": True, "expressible_in_ir": True,
            },
            "prescribed_procedure": None,
            "ground_truth": {
                "kind": "independent_solver",
                "provenance": prov,
                "expected": exp,
            },
        }
        if de_moi:
            c["source"]["problem_text_goc"] = r["problem_text"]
        if r.get("context_text"):
            c["context_text"] = r["context_text"]
        if note:
            c["custodian_note"] = note
        cases.append(c)

    payload = {
        "provenance_chain": {
            "source_universe_fingerprint": sel["source_universe_fingerprint"],
            "selection_pool_fingerprint": sel["selection_pool_fingerprint"],
            "external_selection_fingerprint": hashlib.sha256(
                (HERE / "EXTERNAL_SELECTION.json").read_bytes()).hexdigest(),
            "external_seed": sel["seed"],
            "selector_role": sel["selector_role"],
            "selection_method": sel["selection_method"],
        },
        "ground_truth": {
            "solver": "docs/evaluation/semantic-benchmark/custodian/"
                      "sealed_ground_truth.py",
            "khai": "Python thuần, không import mã sản phẩm nào. Case không có "
                    "nghĩa vụ nào trong taxonomy diễn đạt được thì `expected` "
                    "RỖNG và runner đếm là UNGRADED.",
        },
        "cases": cases,
    }
    SEALED.mkdir(parents=True, exist_ok=True)
    (SEALED / "cases.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cham = sum(1 for c in cases if c["ground_truth"]["expected"])
    print(f"cases: {len(cases)} · có expected: {cham} · UNGRADED: {len(cases)-cham}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
