# -*- coding: utf-8 -*-
"""Sinh BÀI MẪU HÌNH HỌC chạy offline — **0 API call**.

VÌ SAO CẦN: toàn bộ đường *không-cần-AI* của sản phẩm nằm ở `SAMPLES` (17 bài
Tin học). Hình học có **0 bài**, nên mở app mà không có khoá API thì không có
một bài hình học nào để chạy — kể cả để soát giao diện. Đó cũng là lý do
`CLAUDE.md` dặn "task UI/CSS chọn bài mẫu, không cần backend": lối ấy hiện chỉ
tồn tại cho miền đã bị thay.

RANH GIỚI R0 KHÔNG ĐỔI. Chương trình dưới đây do NGƯỜI viết, đúng như
`oracle_result` của tập DEV do người tính tay — nhưng **không một toạ độ kết
quả nào** được viết tay: trung điểm, giao tuyến, thiết diện, thể tích đều do
kernel tính. Người viết *các bước dựng*, engine dựng. Đó chính là việc LLM làm
ở đường sinh, nên bài mẫu và bài sinh ra cho cùng một hình dạng envelope.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/build_geometry_samples.py

Ghi ra `frontend/src/data/geometry-samples.json`. Khoá bởi
`frontend/src/data/geometry-samples.test.ts` — sửa chương trình mà quên chạy
lại script là ĐỎ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

RA = ROOT / "frontend" / "src" / "data" / "geometry-samples.json"


def _diem(ten: str, xyz: list[int | str]) -> dict[str, Any]:
    return {"name": ten, "type": "point3", "initial_value": xyz,
            "model_assumption": "hệ trục do đề chọn"}


def _khai(ten: str, kieu: str) -> dict[str, Any]:
    return {"name": ten, "type": kieu}


#: Đáy vuông cạnh 2 trong `z = 0`, đỉnh S trên trục z — quy ước hình của tập
#: DEV (`hinh_quy_uoc`). Giữ cùng quy ước để bài mẫu và bài đo nói cùng thứ.
DAY = {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0]}
MAT_CHOP = [["A", "B", "C", "D"], ["A", "B", "S"], ["B", "C", "S"],
            ["C", "D", "S"], ["D", "A", "S"]]


def chuong_trinh_thiet_dien() -> dict[str, Any]:
    """Thiết diện song song đáy — dạng bài tần suất cao nhất của chương này."""
    return {
        "spec_version": "1.0",
        "title": "Thiết diện của hình chóp cắt bởi mặt phẳng qua ba trung điểm",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Gọi M, N, P lần lượt là trung "
            "điểm của SA, SB, SC. Hãy dựng thiết diện của hình chóp khi cắt "
            "bởi mặt phẳng (MNP)."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("M", "point3"), _khai("N", "point3"), _khai("P", "point3"),
            _khai("chop", "solid"), _khai("mp", "plane3"),
            _khai("thiet_dien", "section"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP},
            {"kind": "construct_point", "target_var": "M", "label": "M",
             "expr": {"kind": "midpoint", "a": "S", "b": "A"}},
            {"kind": "construct_point", "target_var": "N", "label": "N",
             "expr": {"kind": "midpoint", "a": "S", "b": "B"}},
            {"kind": "construct_point", "target_var": "P", "label": "P",
             "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
            {"kind": "construct_plane", "target_var": "mp", "label": "(MNP)",
             "through": ["M", "N", "P"]},
            {"kind": "construct_section", "target_var": "thiet_dien",
             "label": "thiết diện", "solid": "chop", "plane": "mp"},
        ],
        "visual_bindings": {},
    }


def chuong_trinh_vuong_goc() -> dict[str, Any]:
    """Quan hệ vuông góc — trả `sin² = 1`, tức BC ⊥ (SAB)."""
    return {
        "spec_version": "1.0",
        "title": "Đường thẳng vuông góc với mặt phẳng trong hình chóp",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Xét đường thẳng BC và mặt phẳng "
            "(SAB): hãy dựng hình rồi cho biết góc giữa chúng."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("chop", "solid"), _khai("sab", "plane3"),
            _khai("bc", "line3"), _khai("goc", "float"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP},
            {"kind": "construct_plane", "target_var": "sab", "label": "(SAB)",
             "through": ["S", "A", "B"]},
            {"kind": "construct_line", "target_var": "bc", "label": "BC",
             "through_a": "B", "through_b": "C"},
            {"kind": "assign", "target_var": "goc",
             "expr": {"kind": "measure", "quantity": "angle_cos_sq",
                      "of": "bc", "wrt": "sab"}},
        ],
        "visual_bindings": {},
    }


def chuong_trinh_the_tich() -> dict[str, Any]:
    """Thể tích + khoảng cách — hai đại lượng, cùng một hình."""
    return {
        "spec_version": "1.0",
        "title": "Thể tích khối chóp và khoảng cách từ đỉnh đến đáy",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Tính thể tích khối chóp và "
            "khoảng cách từ S đến mặt phẳng đáy."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("chop", "solid"), _khai("day", "plane3"),
            _khai("V", "float"), _khai("d", "float"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP},
            {"kind": "construct_plane", "target_var": "day", "label": "(ABCD)",
             "through": ["A", "B", "C"]},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
            {"kind": "assign", "target_var": "d",
             "expr": {"kind": "measure", "quantity": "distance",
                      "of": "S", "wrt": "day"}},
        ],
        "visual_bindings": {},
    }


def chuong_trinh_mat_cheo() -> dict[str, Any]:
    """Thiết diện theo MẶT CHÉO (SAC) — mặt phẳng chứa hai cạnh của khối.

    ─── VÌ SAO BÀI NÀY CÓ MẶT ────────────────────────────────────────────────

    Nó là dạng phổ biến bậc nhất của chương, và cho tới 2026-09-02 hệ **không
    dựng nổi**: mặt phẳng (SAC) chứa trọn hai cạnh `SA` và `SC`, mỗi cạnh được
    hai mặt kề cùng báo, và vòng nối vấp bản sao rồi đổ lỗi cho bảng mặt
    (`SECTION_COPLANAR_EDGE_GAP`).

    Đặt nó vào tập bài mẫu là cách giữ cho lỗ ấy không lặng lẽ mở lại: một bản
    hồi quy trong `tests/geometry/` chứng minh kernel đúng, còn bài mẫu này
    chứng minh **cả chuỗi** đúng — và nó chạy trong trình duyệt thật, không cần
    khoá API.
    """
    return {
        "spec_version": "1.0",
        "title": "Thiết diện của hình chóp theo mặt phẳng chéo (SAC)",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Hãy dựng thiết diện của hình "
            "chóp khi cắt bởi mặt phẳng (SAC)."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("chop", "solid"), _khai("sac", "plane3"),
            _khai("thiet_dien", "section"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP,
             "label": "S.ABCD"},
            {"kind": "construct_plane", "target_var": "sac",
             "through": ["S", "A", "C"], "label": "(SAC)"},
            {"kind": "construct_section", "target_var": "thiet_dien",
             "solid": "chop", "plane": "sac",
             "label": "thiết diện theo mặt phẳng (SAC)"},
        ],
        "visual_bindings": {},
    }


def chuong_trinh_mp_vuong_goc() -> dict[str, Any]:
    """Mặt phẳng qua một điểm, VUÔNG GÓC với một đường thẳng.

    ─── VÌ SAO BÀI NÀY CÓ MẶT ────────────────────────────────────────────────

    Nó là phép dựng DUY NHẤT trong nhóm *"qua một điểm, song song/vuông góc
    với …"* mà IR không diễn đạt được trước 2026-09-02: mọi phép sinh điểm của
    IR bảo toàn bao affine của các điểm đã khai, còn mặt phẳng này nằm ngoài
    bao ấy, nên ba điểm lấy được luôn thẳng hàng
    (`G4_CONSTRUCTION_EXPRESSIVENESS_BRIDGE`).

    Ba phép còn lại **không** có bài mẫu riêng, và đó là có chủ đích: chúng đã
    diễn đạt được bằng IR cũ, nên một bài mẫu cho chúng chỉ là trang trí.

    Bài dừng ở *dựng rồi đo*, không đi tiếp tới giao tuyến — chuỗi dài hơn đã
    có ở `tests/geometry/test_construction_bridge_g4.py::test_D_chuoi_dai_*`.
    Lý do là NHÃN: một vật do `assign` sinh ra không có ô nhãn trong IR, nên tên
    của nó do formatter dựng; lồng câu ấy vào câu sau cho ra *"Giao tuyến của
    Mặt phẳng qua B và vuông góc với SC và (ABCD)"* — đúng ngữ nghĩa mà mơ hồ
    khi đọc. Bài mẫu là bề mặt học sinh nên nó dừng trước chỗ đó; test thì
    không cần đọc đẹp.
    """
    return {
        "spec_version": "1.0",
        "title": "Mặt phẳng qua một điểm và vuông góc với đường thẳng cho trước",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Dựng mặt phẳng qua B và vuông "
            "góc với đường thẳng SC, rồi tính khoảng cách từ S đến mặt phẳng "
            "vừa dựng."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("chop", "solid"), _khai("sc", "line3"),
            _khai("day", "plane3"), _khai("mpb", "plane3"),
            _khai("kc", "float"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP,
             "label": "S.ABCD"},
            # Cạnh bên XIÊN, có chủ đích: mặt phẳng qua B vuông góc với cạnh
            # ĐỨNG `SA` lại chính là mặt đáy, và giao của nó với đáy là cả một
            # mặt phẳng — một ca suy biến, không phải một bài.
            {"kind": "construct_line", "target_var": "sc",
             "through_a": "S", "through_b": "C", "label": "SC"},
            {"kind": "assign", "target_var": "mpb",
             "expr": {"kind": "plane_perpendicular_to_line",
                      "point": "B", "line": "sc"}},
            {"kind": "construct_plane", "target_var": "day",
             "through": ["A", "B", "C"], "label": "(ABCD)"},
            {"kind": "assign", "target_var": "kc",
             "expr": {"kind": "measure", "quantity": "distance",
                      "of": "S", "wrt": "mpb"}},
        ],
        "visual_bindings": {},
    }


#: `id` là khoá ỔN ĐỊNH của bài mẫu — nó đi vào URL và vào lịch sử học, nên
#: đổi nó là làm mất tiến độ của học sinh. Thêm bài thì thêm khoá mới.
# ── KHỐI CONG (2026-09-03, Phase 3) ──────────────────────────────────────
#
# Sáu bài, và không bài nào có **mã riêng theo hình**: cả sáu dùng cùng một câu
# lệnh `construct_curved_solid` với `curved_kind` khác nhau, cùng các phép đo
# chung, cùng lối hợp thành. Nếu một hình nào đó cần một hàm dựng riêng ở đây
# thì nền đã sai — đó chính là phép thử mà `NEW SHAPE ≠ NEW MODULE` nói tới.
_CONG = "Khối cong · cầu, trụ, nón"


def _khoi_cong(ten: str, loai: str, neo: str, dinh: str | None,
               vanh: str, nhan: str) -> dict[str, Any]:
    st: dict[str, Any] = {
        "kind": "construct_curved_solid", "target_var": ten,
        "curved_kind": loai, "anchor": neo, "rim_point": vanh, "label": nhan,
    }
    if dinh:
        st["apex_or_top"] = dinh
    return st


def _do(ten: str, q: str, of: str, wrt: str | None = None) -> dict[str, Any]:
    e: dict[str, Any] = {"kind": "measure", "quantity": q, "of": of}
    if wrt:
        e["wrt"] = wrt
    return {"kind": "assign", "target_var": ten, "expr": e}


def chuong_trinh_cau_the_tich() -> dict[str, Any]:
    """Khối cầu: bán kính và thể tích. `R² = 9 ⇒ R = 3, V = 36π`."""
    return {
        "spec_version": "1.0",
        "title": "Bán kính và thể tích khối cầu",
        "description": (
            "Cho mặt cầu tâm I đi qua điểm A với IA = 3. Tính bán kính và thể "
            "tích khối cầu."
        ),
        "memory_declarations": [
            _diem("I", [0, 0, 0]), _diem("A", [3, 0, 0]),
            _khai("cau", "curved_solid"),
            _khai("R", "float"), _khai("V", "float"),
        ],
        "statements": [
            _khoi_cong("cau", "ball", "I", None, "A", "(S)"),
            _do("R", "radius", "cau"), _do("V", "volume", "cau"),
        ],
        "visual_bindings": {},
    }


def chuong_trinh_cau_cat_mp() -> dict[str, Any]:
    """Mặt phẳng cắt mặt cầu theo đường tròn. `r² = 25 − 9 = 16 ⇒ r = 4`."""
    return {
        "spec_version": "1.0",
        "title": "Đường tròn giao của mặt phẳng và mặt cầu",
        "description": (
            "Cho mặt cầu tâm I bán kính 5. Mặt phẳng (P) cách tâm I một khoảng "
            "bằng 3 cắt mặt cầu theo một đường tròn. Tính bán kính và diện "
            "tích hình tròn đó."
        ),
        "memory_declarations": [
            _diem("I", [0, 0, 0]), _diem("A", [5, 0, 0]),
            _diem("H", [0, 0, 3]), _diem("U", [1, 0, 3]), _diem("W", [0, 1, 3]),
            _khai("cau", "curved_solid"), _khai("P", "plane3"),
            _khai("C", "circle3"), _khai("r", "float"), _khai("S", "float"),
        ],
        "statements": [
            _khoi_cong("cau", "ball", "I", None, "A", "(S)"),
            {"kind": "construct_plane", "target_var": "P", "label": "(P)",
             "through": ["H", "U", "W"]},
            {"kind": "assign", "target_var": "C", "label": "(C)",
             "expr": {"kind": "intersect_plane_curved", "solid": "cau",
                      "plane": "P"}},
            _do("r", "radius", "C"), _do("S", "area", "C"),
        ],
        "visual_bindings": {},
    }


def chuong_trinh_tru_truc_xien() -> dict[str, Any]:
    """Hình trụ TRỤC XIÊN — bằng chứng rằng nền không giả định hình dựng đứng.

    Trục `(1,2,2)`, điểm vành `(2,−1,0)` vuông góc trục ⇒ `r = √5` **vô tỉ**,
    `h = 3`, `V = 15π`, `S_xq = 6π√5`. Mọi TOẠ ĐỘ vẫn hữu tỉ.
    """
    return {
        "spec_version": "1.0",
        "title": "Hình trụ có trục xiên",
        "description": (
            "Cho hình trụ có hai tâm đáy là O và O′ với OO′ = 3, và một điểm A "
            "trên đường tròn đáy sao cho OA vuông góc với OO′. Tính thể tích "
            "và diện tích xung quanh của hình trụ."
        ),
        "memory_declarations": [
            _diem("O", [0, 0, 0]), _diem("O_prime", [1, 2, 2]), _diem("A", [2, -1, 0]),
            _khai("tru", "curved_solid"), _khai("V", "float"),
            _khai("Sxq", "float"), _khai("h", "float"),
        ],
        "statements": [
            _khoi_cong("tru", "cylinder", "O", "O_prime", "A", "hình trụ"),
            _do("V", "volume", "tru"), _do("Sxq", "lateral_area", "tru"),
            # Chiều cao KHÔNG có lượng đo riêng — nó là khoảng cách giữa hai
            # điểm CÓ TÊN, và `distance` đã nói được.
            _do("h", "distance", "O", "O_prime"),
        ],
        "visual_bindings": {},
    }


def chuong_trinh_tru_thiet_dien_tron() -> dict[str, Any]:
    """Mặt phẳng vuông góc trục cắt trụ theo đường tròn bán kính đáy."""
    return {
        "spec_version": "1.0",
        "title": "Thiết diện vuông góc trục của hình trụ",
        "description": (
            "Cho hình trụ có tâm hai đáy là O và O′, bán kính đáy bằng 2. Mặt "
            "phẳng đi qua trung điểm của OO′ và vuông góc với trục cắt hình "
            "trụ theo một đường tròn. Tính bán kính đường tròn ấy."
        ),
        "memory_declarations": [
            _diem("O", [0, 0, 0]), _diem("O_prime", [0, 0, 4]), _diem("A", [2, 0, 0]),
            _khai("tru", "curved_solid"), _khai("M", "point3"),
            _khai("truc", "line3"), _khai("P", "plane3"),
            _khai("C", "circle3"), _khai("r", "float"),
        ],
        "statements": [
            _khoi_cong("tru", "cylinder", "O", "O_prime", "A", "hình trụ"),
            {"kind": "construct_point", "target_var": "M",
             "expr": {"kind": "midpoint", "a": "O", "b": "O_prime"}},
            {"kind": "construct_line", "target_var": "truc", "label": "OO′",
             "through_a": "O", "through_b": "O_prime"},
            {"kind": "assign", "target_var": "P", "label": "(P)",
             "expr": {"kind": "plane_perpendicular_to_line", "point": "M",
                      "line": "truc"}},
            {"kind": "assign", "target_var": "C", "label": "(C)",
             "expr": {"kind": "intersect_plane_curved", "solid": "tru",
                      "plane": "P"}},
            _do("r", "radius", "C"),
        ],
        "visual_bindings": {},
    }


def chuong_trinh_non_duong_sinh() -> dict[str, Any]:
    """Nón `r = 3, h = 4` ⇒ `l = 5`, `V = 12π`, `S_xq = 15π`. Kiểm tay."""
    return {
        "spec_version": "1.0",
        "title": "Đường sinh, thể tích và diện tích xung quanh hình nón",
        "description": (
            "Cho hình nón có tâm đáy O, đỉnh S với SO = 4, và một điểm A trên "
            "đường tròn đáy với OA = 3. Tính độ dài đường sinh, thể tích và "
            "diện tích xung quanh của hình nón."
        ),
        "memory_declarations": [
            _diem("O", [0, 0, 0]), _diem("S", [0, 0, 4]), _diem("A", [3, 0, 0]),
            _khai("non", "curved_solid"), _khai("l", "float"),
            _khai("V", "float"), _khai("Sxq", "float"),
        ],
        "statements": [
            _khoi_cong("non", "cone", "O", "S", "A", "hình nón"),
            # Đường sinh = khoảng cách đỉnh → điểm vành. Không có `slant`.
            _do("l", "distance", "S", "A"),
            _do("V", "volume", "non"), _do("Sxq", "lateral_area", "non"),
        ],
        "visual_bindings": {},
    }


def chuong_trinh_non_thiet_dien_truc() -> dict[str, Any]:
    """Thiết diện QUA TRỤC — bằng HỢP THÀNH, không phép dựng mới.

    `B = 2O − A` qua `divide_segment(ratio="2")`, nối bằng `construct_polygon`,
    đo bằng `area` của Phase 1. Đáy `AB = 6`, cao `SO = 4` ⇒ `S = 12`.
    """
    return {
        "spec_version": "1.0",
        "title": "Thiết diện qua trục của hình nón",
        "description": (
            "Cho hình nón đỉnh S, tâm đáy O với SO = 4 và bán kính đáy bằng 3. "
            "Mặt phẳng đi qua trục cắt hình nón theo một tam giác. Tính diện "
            "tích thiết diện đó."
        ),
        "memory_declarations": [
            _diem("O", [0, 0, 0]), _diem("S", [0, 0, 4]), _diem("A", [3, 0, 0]),
            _khai("non", "curved_solid"), _khai("B", "point3"),
            _khai("td", "polygon3"), _khai("Std", "float"),
        ],
        "statements": [
            _khoi_cong("non", "cone", "O", "S", "A", "hình nón"),
            {"kind": "construct_point", "target_var": "B",
             "expr": {"kind": "divide_segment", "a": "A", "b": "O",
                      "ratio": "2"}},
            {"kind": "construct_polygon", "target_var": "td", "label": "SAB",
             "vertices": ["S", "A", "B"]},
            _do("Std", "area", "td"),
        ],
        "visual_bindings": {},
    }


BAI_MAU = [
    ("thiet-dien-chop", "Dựng hình · thiết diện", chuong_trinh_thiet_dien),
    ("mat-cheo-sac", "Dựng hình · thiết diện", chuong_trinh_mat_cheo),
    ("vuong-goc-chop", "Quan hệ song song – vuông góc", chuong_trinh_vuong_goc),
    ("mp-vuong-goc-duong", "Quan hệ song song – vuông góc", chuong_trinh_mp_vuong_goc),
    ("the-tich-chop", "Khoảng cách · thể tích · góc", chuong_trinh_the_tich),
    ("cau-the-tich", _CONG, chuong_trinh_cau_the_tich),
    ("cau-cat-mat-phang", _CONG, chuong_trinh_cau_cat_mp),
    ("tru-truc-xien", _CONG, chuong_trinh_tru_truc_xien),
    ("tru-thiet-dien-tron", _CONG, chuong_trinh_tru_thiet_dien_tron),
    ("non-duong-sinh", _CONG, chuong_trinh_non_duong_sinh),
    ("non-thiet-dien-truc", _CONG, chuong_trinh_non_thiet_dien_truc),
]


def main() -> int:
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )
    from app.simulation.semantic_program.pipeline_adapter import (
        compile_semantic_program_to_envelope,
    )
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import (
        build_simulation_state,
    )

    ra: list[dict[str, Any]] = []
    for ma, nhom, dung in BAI_MAU:
        spec = SemanticProgramSpec.model_validate(dung())
        env = compile_semantic_program_to_envelope(spec)
        # Cảnh 3D dựng đúng đường sản phẩm dựng (`pipeline._dung_scene3d`):
        # interpreter → simulation_state → scene3d. Không có đường tắt nào ở
        # đây, nếu không bài mẫu sẽ khác bài sinh ra ở một chỗ không ai ngờ.
        ket = SemanticProgramInterpreter().execute(spec)
        # `limit_reached` = cắt giữa chừng. Một bài mẫu cắt giữa chừng là bài
        # mẫu dạy sai, nên DỪNG chứ không ghi ra.
        if ket.status != "completed":
            print(f"DỪNG: {ma} không chạy trọn — {ket.status}", file=sys.stderr)
            return 2
        canh = build_scene3d(build_simulation_state(spec, ket))
        if not canh["objects"]:
            print(f"DỪNG: {ma} không dựng ra cảnh 3D nào", file=sys.stderr)
            return 2
        env["scene3d"] = canh
        # Cùng một luật với `pipeline._envelope_tu_route_sinh`: có cảnh 3D ⇒
        # envelope khai miền HÌNH HỌC. Lặp lại ở đây chứ không gọi lại hàm kia
        # vì hàm kia nhận `SemanticRouteOutcome` của đường LLM; nhưng nếu hai
        # chỗ lệch nhau thì bài mẫu hiện nhãn khác bài sinh ra —
        # `geometry-samples.test.ts` khoá cho chúng không lệch.
        env["domain"] = "geometry"
        env["source"] = "geometry_sample"
        ra.append({"id": ma, "group": nhom,
                   "problemText": spec.description or spec.title,
                   "envelope": env})
        so_do = sum(1 for o in canh["objects"] if o["type"] == "quantity")
        print(f"  {ma:20} {len(canh['objects']):3} vật · "
              f"{len(env['config']['frames']):3} khung · {so_do} số đo")

    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(
        json.dumps({
            "khai": ("Bài mẫu hình học SINH RA, không viết tay. Sửa "
                     "`backend/scripts/build_geometry_samples.py` rồi chạy lại; "
                     "sửa thẳng file này sẽ bị ghi đè."),
            "samples": ra,
        }, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    print(f"\n→ {RA.relative_to(ROOT)} · {len(ra)} bài")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
