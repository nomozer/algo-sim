"""AXO HYBRID /12 (P5): Compositional Source Gate revalidation & adversarial counterexample tests."""
from __future__ import annotations

import ast
from pathlib import Path
import pytest

from app.simulation.geometry_functions import registry as R


def _kiem(text: str, raw_calls: list[dict], *, read_quotes: tuple[str, ...] = ()) -> dict[str, str | None]:
    calls = R.doc_ke_hoach({"calls": raw_calls})
    return R.kiem_nguon(calls, text, read_quotes=read_quotes)


def test_registry_version_and_zero_app_ai_imports() -> None:
    assert R.REGISTRY_VERSION == "geometry-functions/33"
    src = Path(R.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "app.ai" not in alias.name, f"forbidden import in registry.py: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert "app.ai" not in mod, f"forbidden from-import in registry.py: {mod}"
            assert not (node.level >= 2 and mod.startswith("ai")), f"forbidden relative import in registry.py: {mod}"


@pytest.mark.parametrize(
    "case_id,text,raw_calls",
    [
        (
            "S11",
            "Cho hình lập phương ABCD.EFGH có cạnh 4. Hãy dựng hình 3D của hình lập phương này.",
            [
                {"id": "c1", "fn": "prism", "args": {"base": ["A", "B", "C", "D"], "top": ["E", "F", "G", "H"], "right": True}, "source": {"quotes": ["Cho hình lập phương ABCD.EFGH có cạnh 4"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "4"}, "source": {"quotes": ["Cho hình lập phương ABCD.EFGH có cạnh 4"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "E"], "value": "4"}, "source": {"quotes": ["Cho hình lập phương ABCD.EFGH có cạnh 4"]}},
            ],
        ),
        (
            "S13",
            "Cho khối lăng trụ tam giác đều ABC.A'B'C' có tất cả các cạnh bằng a. Biểu diễn khối lăng trụ đã cho.",
            [
                {"id": "c1", "fn": "prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"], "right": True}, "source": {"quotes": ["Cho khối lăng trụ tam giác đều ABC.A'B'C'"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "a"}, "source": {"quotes": ["Cho khối lăng trụ tam giác đều ABC.A'B'C' có tất cả các cạnh bằng a"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "a"}, "source": {"quotes": ["Cho khối lăng trụ tam giác đều ABC.A'B'C' có tất cả các cạnh bằng a"]}},
            ],
        ),
        (
            "S28",
            "Hình chóp S.ABCD có ABCD là hình vuông cạnh 4, SA vuông góc mặt đáy, SA = 4; điểm N nằm trên cạnh SD với SN = 3ND. Hãy vẽ hình chóp và điểm N.",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Hình chóp S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "4"}, "source": {"quotes": ["ABCD là hình vuông cạnh 4"]}},
                {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc mặt đáy"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "4"}, "source": {"quotes": ["SA = 4"]}},
                {"id": "c5", "fn": "divide_segment", "args": {"point": "N", "segment": ["S", "D"], "ratio": "3/4"}, "source": {"quotes": ["điểm N nằm trên cạnh SD với SN = 3ND"]}},
            ],
        ),
        (
            "S34",
            "Hãy mô phỏng khối hộp chữ nhật ABCD.A'B'C'D' biết AB = a, AD = a√2, AA' = a√3.",
            [
                {"id": "c1", "fn": "prism", "args": {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"], "right": True}, "source": {"quotes": ["Hãy mô phỏng khối hộp chữ nhật ABCD.A'B'C'D'"]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": ["A", "B", "C", "D"]}, "source": {"quotes": ["khối hộp chữ nhật ABCD.A'B'C'D'"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "source": {"quotes": ["AB = a"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "sqrt(2)*a"}, "source": {"quotes": ["AD = a√2"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "sqrt(3)*a"}, "source": {"quotes": ["AA' = a√3"]}},
            ],
        ),
        (
            "Q04",
            "Mô phỏng hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với đáy, SA = a và tính góc giữa SC với mặt phẳng (ABCD).",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Mô phỏng hình chóp S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["hình chóp S.ABCD có đáy là hình vuông cạnh a"]}},
                {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
                {"id": "c5", "fn": "ask_angle_line_plane", "args": {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["tính góc giữa SC với mặt phẳng (ABCD)"]}},
            ],
        ),
        (
            "Q05",
            "Hãy vẽ hình chóp tứ giác đều S.ABCD có cạnh đáy 2 và cạnh bên √6, sau đó tính chiều cao của hình chóp.",
            [
                {"id": "c1", "fn": "regular_pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Hãy vẽ hình chóp tứ giác đều S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "source": {"quotes": ["hình chóp tứ giác đều S.ABCD có cạnh đáy 2"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "sqrt(6)"}, "source": {"quotes": ["cạnh bên √6"]}},
                {"id": "c4", "fn": "ask_distance_point_plane", "args": {"point": "S", "plane": ["A", "B", "C"]}, "source": {"quotes": ["tính chiều cao của hình chóp"]}},
            ],
        ),
        (
            "Q06",
            "Biểu diễn tứ diện OABC với OA, OB, OC đôi một vuông góc, OA = 1, OB = 2, OC = 2 và tính thể tích khối tứ diện.",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "O", "base": ["A", "B", "C"]}, "source": {"quotes": ["Biểu diễn tứ diện OABC"]}},
                {"id": "c2", "fn": "perpendicular_lines", "args": {"line1": ["O", "A"], "line2": ["O", "B"]}, "source": {"quotes": ["OA, OB, OC đôi một vuông góc"]}},
                {"id": "c3", "fn": "perpendicular_lines", "args": {"line1": ["O", "A"], "line2": ["O", "C"]}, "source": {"quotes": ["OA, OB, OC đôi một vuông góc"]}},
                {"id": "c4", "fn": "perpendicular_lines", "args": {"line1": ["O", "B"], "line2": ["O", "C"]}, "source": {"quotes": ["OA, OB, OC đôi một vuông góc"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["O", "A"], "value": "1"}, "source": {"quotes": ["OA = 1"]}},
                {"id": "c6", "fn": "segment_length", "args": {"segment": ["O", "B"], "value": "2"}, "source": {"quotes": ["OB = 2"]}},
                {"id": "c7", "fn": "segment_length", "args": {"segment": ["O", "C"], "value": "2"}, "source": {"quotes": ["OC = 2"]}},
                {"id": "c8", "fn": "ask_volume", "args": {"solid": "O.ABC"}, "source": {"quotes": ["tính thể tích khối tứ diện"]}},
            ],
        ),
        (
            "Q08",
            "Hãy mô phỏng hình chóp S.ABCD đáy là hình chữ nhật, AB = 3, AD = 4, SA vuông góc với đáy, SA = 5 và tính độ dài SC.",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Hãy mô phỏng hình chóp S.ABCD"]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": ["A", "B", "C", "D"]}, "source": {"quotes": ["hình chóp S.ABCD đáy là hình chữ nhật"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "source": {"quotes": ["AB = 3"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "4"}, "source": {"quotes": ["AD = 4"]}},
                {"id": "c5", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
                {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "5"}, "source": {"quotes": ["SA = 5"]}},
                {"id": "c7", "fn": "ask_length", "args": {"segment": ["S", "C"]}, "source": {"quotes": ["tính độ dài SC"]}},
            ],
        ),
        (
            "Q09",
            "Vẽ hình chóp S.ABC có SA, AB, AC đôi một vuông góc, SA = AB = AC = 3 và tính khoảng cách từ A đến mặt phẳng (SBC).",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Vẽ hình chóp S.ABC"]}},
                {"id": "c2", "fn": "perpendicular_lines", "args": {"line1": ["S", "A"], "line2": ["A", "B"]}, "source": {"quotes": ["SA, AB, AC đôi một vuông góc"]}},
                {"id": "c3", "fn": "perpendicular_lines", "args": {"line1": ["S", "A"], "line2": ["A", "C"]}, "source": {"quotes": ["SA, AB, AC đôi một vuông góc"]}},
                {"id": "c4", "fn": "perpendicular_lines", "args": {"line1": ["A", "B"], "line2": ["A", "C"]}, "source": {"quotes": ["SA, AB, AC đôi một vuông góc"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "source": {"quotes": ["SA = AB = AC = 3"]}},
                {"id": "c6", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "source": {"quotes": ["SA = AB = AC = 3"]}},
                {"id": "c7", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "3"}, "source": {"quotes": ["SA = AB = AC = 3"]}},
                {"id": "c8", "fn": "ask_distance_point_plane", "args": {"point": "A", "plane": ["S", "B", "C"]}, "source": {"quotes": ["tính khoảng cách từ A đến mặt phẳng (SBC)"]}},
            ],
        ),
        (
            "Q10",
            "Mô phỏng hình lập phương ABCD.A'B'C'D' cạnh a và tính góc giữa hai mặt phẳng (A'BD) và (ABCD).",
            [
                {"id": "c1", "fn": "prism", "args": {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"], "right": True}, "source": {"quotes": ["Mô phỏng hình lập phương ABCD.A'B'C'D'"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["Mô phỏng hình lập phương ABCD.A'B'C'D' cạnh a"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "a"}, "source": {"quotes": ["Mô phỏng hình lập phương ABCD.A'B'C'D' cạnh a"]}},
                {"id": "c4", "fn": "ask_angle_plane_plane", "args": {"plane1": ["A'", "B", "D"], "plane2": ["A", "B", "C", "D"]}, "source": {"quotes": ["tính góc giữa hai mặt phẳng (A'BD) và (ABCD)"]}},
            ],
        ),
        (
            "Q12",
            "Hãy mô phỏng tứ diện đều ABCD cạnh a và tính khoảng cách từ A đến mặt phẳng (BCD).",
            [
                {"id": "c1", "fn": "regular_pyramid", "args": {"apex": "A", "base": ["B", "C", "D"]}, "source": {"quotes": ["Hãy mô phỏng tứ diện đều ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["B", "C", "D"], "side": "a"}, "source": {"quotes": ["tứ diện đều ABCD cạnh a"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "source": {"quotes": ["tứ diện đều ABCD cạnh a"]}},
                {"id": "c4", "fn": "ask_distance_point_plane", "args": {"point": "A", "plane": ["B", "C", "D"]}, "source": {"quotes": ["tính khoảng cách từ A đến mặt phẳng (BCD)"]}},
            ],
        ),
        (
            "Q13",
            "Vẽ hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với đáy, SA = 2√2; tính góc giữa đường thẳng SC và mặt phẳng đáy.",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Vẽ hình chóp S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "source": {"quotes": ["đáy ABCD là hình vuông cạnh 2"]}},
                {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "2*sqrt(2)"}, "source": {"quotes": ["SA = 2√2"]}},
                {"id": "c5", "fn": "ask_angle_line_plane", "args": {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["tính góc giữa đường thẳng SC và mặt phẳng đáy"]}},
            ],
        ),
        (
            "Q14",
            "Mô phỏng hình hộp chữ nhật ABCD.A'B'C'D' với AB = 3, AD = 4, AA' = 12 và tính độ dài đường chéo BD'.",
            [
                {"id": "c1", "fn": "prism", "args": {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"], "right": True}, "source": {"quotes": ["Mô phỏng hình hộp chữ nhật ABCD.A'B'C'D'"]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": ["A", "B", "C", "D"]}, "source": {"quotes": ["hình hộp chữ nhật ABCD.A'B'C'D'"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "source": {"quotes": ["AB = 3"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "4"}, "source": {"quotes": ["AD = 4"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "12"}, "source": {"quotes": ["AA' = 12"]}},
                {"id": "c6", "fn": "ask_length", "args": {"segment": ["B", "D'"]}, "source": {"quotes": ["tính độ dài đường chéo BD'"]}},
            ],
        ),
        (
            "EXAM_EXCL_META",
            "Câu 2 (2 điểm). Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy, SA = a! Chỉ cần vẽ hình, không cần tính gì thêm!",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["đáy ABCD là hình vuông cạnh a"]}},
                {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
            ],
        ),
        (
            "MUON_XEM",
            "Em muốn xem hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc đáy và SA = a.",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["hình chóp S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["hình chóp S.ABCD có đáy là hình vuông cạnh a"]}},
                {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc đáy"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
            ],
        ),
        (
            "ASCII_VALID",
            "Cho hinh chop S.ABCD co day la hinh vuong canh a, SA vuong goc voi day, SA = a. Tinh the tich khoi chop S.ABCD.",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hinh chop S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["hinh chop S.ABCD co day la hinh vuong canh a"]}},
                {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuong goc voi day"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
                {"id": "c5", "fn": "ask_volume", "args": {"solid": "S.ABCD"}, "source": {"quotes": ["Tinh the tich khoi chop S.ABCD"]}},
            ],
        ),
    ],
)
def test_compositional_source_gate_accepts_closed_patterns(case_id: str, text: str, raw_calls: list[dict]) -> None:
    out = _kiem(text, raw_calls)
    assert isinstance(out, dict), f"{case_id} should pass Source Gate"


def test_adversarial_1_ungrounded_number_rejected() -> None:
    text = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy, SA = a."
    with pytest.raises(R.TuChoi) as exc:
        _kiem(text, [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["đáy ABCD là hình vuông cạnh a"]}},
            {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
            {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "99"}, "source": {"quotes": ["SA = a"]}},
        ])
    assert exc.value.code == "UNGROUNDED_VALUE"


def test_adversarial_2_swapped_ask_operand_rejected() -> None:
    text = "Vẽ hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy, SA = a và tính độ dài SC."
    with pytest.raises(R.TuChoi) as exc:
        _kiem(text, [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Vẽ hình chóp S.ABCD"]}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["đáy ABCD là hình vuông cạnh a"]}},
            {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
            {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
            {"id": "c5", "fn": "ask_length", "args": {"segment": ["S", "B"]}, "source": {"quotes": ["tính độ dài SC"]}},
        ])
    assert exc.value.code == "SOURCE_OBJECT_MISMATCH"


def test_adversarial_3_negated_premise_rejected() -> None:
    text = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA không vuông góc với đáy."
    with pytest.raises(R.TuChoi) as exc:
        _kiem(text, [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["hình chóp S.ABCD có đáy là hình vuông cạnh a"]}},
            {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA không vuông góc với đáy"]}},
        ])
    assert exc.value.code == "NEGATED_CLAUSE"


def test_adversarial_4_conditional_premise_rejected() -> None:
    text = "Nếu SA = 2a thì tính thể tích hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với đáy."
    with pytest.raises(R.TuChoi) as exc:
        _kiem(text, [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["hình chóp S.ABCD"]}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["hình chóp S.ABCD có đáy là hình vuông cạnh a"]}},
            {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
            {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "2*a"}, "source": {"quotes": ["SA = 2a"]}},
            {"id": "c5", "fn": "ask_volume", "args": {"solid": "S.ABCD"}, "source": {"quotes": ["tính thể tích hình chóp S.ABCD"]}},
        ])
    assert exc.value.code == "CONDITIONAL_CLAUSE"


def test_adversarial_5_fabricated_accented_quote_on_ascii_rejected() -> None:
    text = "Cho hinh chop S.ABCD co day la hinh vuong canh a, SA vuong goc voi day, SA = a."
    with pytest.raises(R.TuChoi) as exc:
        _kiem(text, [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["hinh chop S.ABCD co day la hinh vuong canh a"]}},
        ])
    assert exc.value.code == "QUOTE_NOT_IN_SOURCE"


def test_adversarial_6_polysemous_decoy_ascii_never_projected() -> None:
    assert not R._du_dieu_kien_bu_dau_nguon("Tinh toc do canh quat OABC.")
    assert not R._du_dieu_kien_bu_dau_nguon("Tim thuat toan dijkstra tren do thi ABCD.")
    assert not R._du_dieu_kien_bu_dau_nguon("Kiem tra ket qua dung cua so duong AB.")
    with pytest.raises(R.TuChoi):
        _kiem("Tinh toc do canh quat OABC.", [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "O", "base": ["A", "B", "C"]}, "source": {"quotes": ["canh quat OABC"]}},
        ])


def test_adversarial_7_bare_object_list_and_unread_local_mod_rejected() -> None:
    with pytest.raises(R.TuChoi):
        _kiem("Cho mình xem hình chóp S.ABCD và đường thẳng SC.", [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["hình chóp S.ABCD"]}},
        ])
    with pytest.raises(R.TuChoi) as exc:
        _kiem(
            "Vẽ hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy, SA = a và tính độ dài SC với SA = 2a.",
            [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Vẽ hình chóp S.ABCD"]}},
                {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quotes": ["đáy ABCD là hình vuông cạnh a"]}},
                {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
                {"id": "c5", "fn": "ask_length", "args": {"segment": ["S", "C"]}, "source": {"quotes": ["tính độ dài SC"]}},
            ],
        )
    assert exc.value.code == "QUESTION_LOCAL_GIVEN_CONFLICT"
