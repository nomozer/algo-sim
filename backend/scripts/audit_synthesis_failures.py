# -*- coding: utf-8 -*-
"""AUDIT MA SÁT TỔNG HỢP — gom mọi lượt hỏng đã lưu, xếp theo BỆNH. 0 API call.

─── CÂU HỎI ───────────────────────────────────────────────────────────────

Ba tuyến đo (dihedral probes · declaration-merge · generalization matrix) đã
tiêu tổng cộng hơn 400 nghìn token. Mỗi tuyến kết luận riêng lẻ. Câu chưa ai
hỏi: **cùng một bệnh lặp lại bao nhiêu lần qua cả ba tuyến** — và trong đó bao
nhiêu phần là lỗi MÔ HÌNH, bao nhiêu là lỗi PROMPT của ta.

Phân biệt ấy quyết định việc phải làm. Lỗi mô hình thì chờ mô hình khá lên; lỗi
prompt thì sửa được ngay và rẻ. Trộn hai thứ vào một con số "tỉ lệ hỏng" là cách
chắc chắn nhất để sửa nhầm phía.

─── VÌ SAO KHỚP THÔNG ĐIỆP, KHÔNG KHỚP MÃ LỖI ─────────────────────────────

Bộ đo cũ chỉ ghi `gate` (`schema` · `ir_static` · `grounding`) — đủ để biết
lượt hỏng ở tầng nào, KHÔNG đủ để biết vì sao. Bốn ca "SCHEMA" có thể là bốn
bệnh khác hẳn. Thông điệp từ chối là chỗ duy nhất còn giữ nguyên bệnh, nên khớp
ở đó, và mỗi khuôn khớp phải đọc được thành một câu người hiểu.

─── QUY KẾT: SYSTEM · MODEL · PROMPT ──────────────────────────────────────

  PROMPT — ta nói sai hoặc nói thiếu, mô hình làm theo. Sửa được ngay.
  MODEL  — hợp đồng nói rõ, mô hình vẫn làm khác. Chờ mô hình, hoặc thu hẹp
           không gian chọn.
  SYSTEM — hệ ta hỏng (serialize, gate sai). Bug, sửa.

Quy kết ghi CỨNG theo từng khuôn, có lý do viết ra, để lần sau ai đó đọc còn
cãi được. Một bảng tự sinh không có lý do thì không ai cãi, nên cũng không ai
kiểm.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
GEO = GOC / "docs" / "evaluation" / "geometry"

#: (khoá, nhãn người đọc, khuôn khớp thông điệp, quy kết, vì sao)
#:
#: Thứ tự CÓ NGHĨA — khuôn đầu tiên khớp thì thắng. Xếp bệnh HẸP lên trước bệnh
#: RỘNG, vì `angle_cos` trên `line3` cũng khớp "sai kiểu" nếu để bệnh rộng lên
#: trước, và lúc ấy bảng sẽ nói ta có một bệnh chung chung thay vì một thiên
#: lệch prompt cụ thể sửa được.
KHUON: list[tuple[str, str, str, str, str]] = [
    ("angle_cos_tren_line3", "`angle_cos` dùng trên line3",
     r"angle_cos.{0,40}(VECTƠ CÓ HƯỚNG|cần VECTƠ)", "PROMPT",
     "thẻ chỉ liệt kê `quantity(distance|angle_cos_sq|angle_cos|volume)` — "
     "không kiểu toán hạng, không ngữ nghĩa. Mô hình chọn theo TÊN, và tên "
     "chứa sẵn 'cos'. ⚠️ KHÔNG quy cho bảng 'nhị diện' trong prompt hình "
     "học: hai tuyến đo này chạy với `domain=\"geometry\"` nên nhận PROMPT "
     "TIN HỌC, chưa bao giờ thấy bảng ấy (xem FRESH_PROBE_REPORT §0)"),
    ("dung_truoc_khi_dung", "dùng biến trước khi dựng",
     r"IR_USE_BEFORE_CONSTRUCTION", "MODEL",
     "hợp đồng nói rõ thứ tự; đây là lỗi lập kế hoạch của mô hình"),
    ("thieu_source_fact_id", "khai toạ độ mà thiếu xuất xứ",
     r"thiếu source_fact_id|không truy được về đề bài", "PROMPT",
     "prompt dạy 'toạ độ tự chọn khai model_assumption' nhưng không nói phải "
     "khai cho MỌI đỉnh; mô hình khai hai đỉnh đầu rồi quên phần còn lại"),
    ("rua_nang_luc", "rửa năng lực / thực thể tự bịa",
     r"UNANCHORED_DERIVED_ASSUMPTION|DERIVED_ENTITY_WITHOUT_PRODUCER|"
     r"không có trong đề bài", "MODEL",
     "mô hình tự giải rồi giấu kết luận vào toạ độ — vi phạm R0, không phải "
     "hiểu nhầm hợp đồng"),
    ("toa_do_cho_dan_xuat", "toạ độ thô cho đối tượng dựng ra",
     r"construct_point.{0,60}(toạ độ|coordinates)|"
     r"tu_choi_toa_do_trong_construct_point", "PROMPT",
     "thẻ văn phạm từng dán nhãn '[x,y,z]' cho `construct_plane.through` — "
     "trường nhận TÊN ĐIỂM; nhãn sai của ta đẻ ra lỗi của nó"),
    ("khai_bao_trung", "khai báo trùng tên",
     r"[Kk]hai báo trùng|duplicate declaration|trùng tên", "SYSTEM",
     "nâng `declare_point` từng đẻ khai báo thứ hai thay vì gộp — đã sửa"),
    ("enum_sai", "giá trị enum sai",
     r"Input should be '|không thuộc tập|phải là một trong", "PROMPT",
     "thẻ liệt kê enum nhưng operand type thì không; mô hình chọn đúng chỗ, "
     "sai giá trị"),
    ("hinh_dang_wire", "hình dạng wire sai (chỉ số ↔ tên)",
     r"valid integer|should be a valid|Input should be a", "PROMPT",
     "`faces: list[list[int]]` dùng chỉ số vị trí — thân thiện với máy, thù "
     "địch với người; mô hình dùng ký hiệu điểm ở mọi chỗ"),
    ("bieu_thuc_sai_cho", "biểu thức đặt vào chỗ cần giá trị thô",
     r"kind.{0,10}(literal|var).{0,40}(không phải|thay vì)|"
     r"giá trị \['literal'\]", "PROMPT",
     "thẻ gọi mọi chỗ là 'biểu thức'; trường nhận JSON thô không được nói rõ"),
    ("construct_point_diem_goc", "`construct_point` cho ĐIỂM GỐC",
     r"construct_point.{0,80}chỉ dành cho điểm DỰNG RA", "PROMPT",
     "IR từng KHÔNG có cách nói 'khai một điểm gốc' — mô hình dùng cửa duy "
     "nhất nó thấy; `declare_point` thêm sau, các lượt này có trước nó"),
    ("construct_point_arith", "`construct_point` nhận biểu thức số học",
     r"construct_point\.expr.{0,120}(union_tag_invalid|does not match any)",
     "PROMPT",
     "thẻ gọi `expr` là 'biểu thức' như mọi chỗ khác, nên mô hình tưởng chỗ "
     "ấy nhận `arith`; nhãn 'phép dựng ĐIỂM' thêm sau mới tách được"),
    ("operand_sai_kieu", "toán hạng sai kiểu cho phép đo",
     r"IR_OPERAND_TYPE|GEOMETRY_OPERAND_TYPE", "PROMPT",
     "thẻ liệt kê enum `quantity` nhưng KHÔNG nói mỗi lượng đo nhận kiểu "
     "nào — `distance` nhận điểm/đường/mặt, mô hình đưa `vector3` vào"),
    ("thieu_toan_hang", "phép đo thiếu toán hạng thứ hai",
     r"cần hai đối tượng|thiếu `?wrt`?", "PROMPT",
     "arity của từng lượng đo không có trong thẻ; `wrt?` gắn dấu hỏi làm nó "
     "trông như tuỳ chọn với MỌI lượng đo"),
    ("khong_do_duoc", "phép đo không áp được lên toán hạng",
     r"KHONG_DO_DUOC|không đo được", "MODEL",
     "chọn sai phép đo cho hình đã dựng"),
    ("ngoai_nang_luc", "khái niệm ngoài IR (mặt cầu/nón/trụ)",
     r"mặt cầu|mặt nón|mặt trụ|unsupported|UNSUPPORTED", "SYSTEM",
     "IR thật sự không biểu diễn được — fail-closed là ĐÚNG, không phải lỗi"),
    ("vuot_ngan_sach", "hết ngân sách lượt",
     r"vượt ngân sách", "SYSTEM",
     "hệ quả của các bệnh trên, không phải bệnh riêng — đếm để đối chiếu"),
]


def _bam(msg: str) -> tuple[str, str, str, str] | None:
    for khoa, nhan, mau, quy_ket, vi_sao in KHUON:
        if re.search(mau, msg or "", re.IGNORECASE):
            return khoa, nhan, quy_ket, vi_sao
    return None


def _luot(thu_muc_hoac_file: Path):
    """Sinh `(nguon, case_id, attempt_index, thông điệp, token của ca)`.

    Hai khuôn artifact khác nhau và cả hai đều phải đọc được: probe dùng
    `attempt_log`, matrix dùng `attempts_log`. Chuẩn hoá ở đây thay vì bắt nơi
    gọi nhớ — nơi gọi sẽ quên đúng một khuôn.
    """
    d = json.loads(thu_muc_hoac_file.read_text(encoding="utf-8"))
    nguon = thu_muc_hoac_file.parent.name
    for c in d.get("cases", []):
        cid = c.get("case_id") or (c.get("problem") or "?")[:40]
        tok = c.get("tokens") or c.get("total_tokens") or 0
        log = c.get("attempt_log") or c.get("attempts_log") or []
        for a in log:
            msg = a.get("error") or a.get("error_message") or ""
            if msg:
                yield nguon, cid, a.get("attempt_index", 0), msg, tok
        if not log and not c.get("ok", True) and c.get("error"):
            yield nguon, cid, 0, c["error"], tok


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path, help="ghi kết quả ra file")
    a = p.parse_args()

    files = sorted(GEO.glob("dihedral-probe*/dihedral-probe.json")) + \
        [GEO / "generalization-matrix" / "matrix.json"]
    files = [f for f in files if f.exists()]

    benh: dict[str, dict] = {}
    tong_luot = chua_xep = 0
    chua_xep_vi_du: list[str] = []

    for f in files:
        for nguon, cid, idx, msg, tok in _luot(f):
            tong_luot += 1
            hit = _bam(msg)
            if hit is None:
                chua_xep += 1
                if len(chua_xep_vi_du) < 6:
                    chua_xep_vi_du.append(msg[:110])
                continue
            khoa, nhan, quy_ket, vi_sao = hit
            b = benh.setdefault(khoa, {
                "nhan": nhan, "quy_ket": quy_ket, "vi_sao": vi_sao,
                "count": 0, "first_attempt": 0, "repair": 0,
                "token_cost": 0, "nguon": set(), "cases": set()})
            b["count"] += 1
            b["first_attempt" if idx == 0 else "repair"] += 1
            b["nguon"].add(nguon)
            if (nguon, cid) not in b["cases"]:
                b["cases"].add((nguon, cid))
                b["token_cost"] += tok

    xep = sorted(benh.items(), key=lambda kv: -kv[1]["count"])
    print(f"━━ AUDIT MA SÁT TỔNG HỢP — {len(files)} artifact, "
          f"{tong_luot} lượt hỏng ━━\n")
    print(f"{'bệnh':40s} {'n':>3s} {'lượt1':>5s} {'sửa':>4s} "
          f"{'token':>8s}  quy kết")
    print("─" * 92)
    for khoa, b in xep:
        print(f"{b['nhan'][:40]:40s} {b['count']:3d} {b['first_attempt']:5d} "
              f"{b['repair']:4d} {b['token_cost']:8d}  {b['quy_ket']}")
    print("─" * 92)
    for nhom in ("PROMPT", "MODEL", "SYSTEM"):
        n = sum(b["count"] for _, b in xep if b["quy_ket"] == nhom)
        print(f"{nhom:8s} {n:3d} lượt "
              f"({n * 100 // max(tong_luot, 1)}% số lượt hỏng đã xếp)")
    print(f"\nCHƯA XẾP: {chua_xep} lượt")
    for v in chua_xep_vi_du:
        print(f"  · {v}")

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps({
            "khai": "Audit ma sát tổng hợp — gom lượt hỏng của mọi artifact "
                    "đã lưu, xếp theo BỆNH chứ không theo tầng cổng. "
                    "0 API call.",
            "artifacts": [str(f.relative_to(GOC)) for f in files],
            "tong_luot_hong": tong_luot,
            "chua_xep": chua_xep,
            "benh": {k: {**{x: y for x, y in b.items()
                            if x not in ("nguon", "cases")},
                         "nguon": sorted(b["nguon"]),
                         "so_ca": len(b["cases"])}
                     for k, b in xep},
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"\n→ {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
