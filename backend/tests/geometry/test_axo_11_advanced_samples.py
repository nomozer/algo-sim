"""Kiểm thử toán học chính xác (Fraction / Radical) và bất biến hình học
cho 11 bài toán hình học không gian THPT nâng cao trong Thư viện Axo."""

from __future__ import annotations

from fractions import Fraction
import pytest

from app.simulation.geometry import (
    ERR_KHONG_NGOAI_TIEP,
    ERR_SONG_SONG,
    GeometryError,
    Line3,
    Plane3,
    Point3,
    Vec3,
    circumscribed_sphere,
    kernel as K,
)
from app.simulation.geometry.radical import sqrt_rational
from app.simulation.semantic_program.interpreter import (
    SemanticExecutionError,
    SemanticProgramInterpreter,
)
from scripts.build_advanced_geometry_samples import (
    BAI_MAU_NANG_CAO,
    build_all_advanced_samples,
)


def test_11_advanced_samples_catalog_completeness_and_schema() -> None:
    samples = build_all_advanced_samples()
    assert len(samples) == 11
    expected_ids = [ma for ma, _, _ in BAI_MAU_NANG_CAO]
    assert [s["id"] for s in samples] == expected_ids

    expected_formation_steps_by_id = {
        "chop-thiet-dien-ba-diem": 23,
        "lap-phuong-thiet-dien-bat-ky": 25,
        "khoang-cach-diem-mat-phang-nghieng": 16,
        "goc-nhi-dien-hai-mat-phang": 19,
        "khoang-cach-hai-duong-cheo-nhau": 18,
        "lang-tru-tam-giac-thiet-dien": 21,
        "mat-cau-cat-mat-phang": 14,
        "oxyz-giao-diem-duong-mat": 15,
        "mat-phang-tiep-xuc-mat-cau": 14,
        "hinh-non-cat-song-song-day": 21,
        "chop-mat-cau-ngoai-tiep": 26,
    }

    for sample in samples:
        sid = sample["id"]
        env = sample["envelope"]
        assert env["simulation_id"] == "generic.semantic_program"
        assert env["domain"] == "geometry"
        assert env["source"] == "geometry_sample"
        assert len(env["description"]) > 40

        scene3d = env["scene3d"]
        steps = scene3d["formation"]["steps"]
        assert len(steps) == expected_formation_steps_by_id[sid]
        assert len(scene3d["events"]) == expected_formation_steps_by_id[sid]

        # Mỗi sample đều có chứng chỉ hình học (certificates) hoặc đối tượng kết quả đã kiểm chứng
        certificates = scene3d.get("certificates", {})
        assert isinstance(certificates, dict)
        assert len(scene3d["objects"]) >= 5


def test_circumscribed_sphere_exact_and_metamorphic() -> None:
    # Hình chóp S.ABCD có SA ⊥ (ABCD), đáy ABCD hình vuông cạnh a = 4, SA = 4
    S = Vec3.of(0, 0, 4)
    A = Vec3.of(0, 0, 0)
    B = Vec3.of(4, 0, 0)
    C = Vec3.of(4, 4, 0)
    D = Vec3.of(0, 4, 0)

    center, r_sq = circumscribed_sphere([S, A, B, C, D])
    assert center == Vec3.of(2, 2, 2)
    assert r_sq == Fraction(12, 1)
    rad = sqrt_rational(r_sq)
    assert (rad.he, rad.can, rad.mu) == (Fraction(2, 1), 3, 0)

    # Metamorphic scaling: nhân đôi cạnh a -> 8, tâm dịch thành (4, 4, 4), R^2 nhân 4 thành 48
    scale = Fraction(2, 1)
    scaled_pts = [p.scale(scale) for p in (S, A, B, C, D)]
    center_scaled, r_sq_scaled = circumscribed_sphere(scaled_pts)
    assert center_scaled == Vec3.of(4, 4, 4)
    assert r_sq_scaled == r_sq * (scale * scale)


def test_circumscribed_sphere_fail_closed_degenerate_cases() -> None:
    A = Vec3.of(0, 0, 0)
    B = Vec3.of(4, 0, 0)
    C = Vec3.of(4, 4, 0)
    D = Vec3.of(0, 4, 0)
    S = Vec3.of(0, 0, 4)

    # 1. 4 điểm đồng phẳng không xác định mặt cầu ngoại tiếp duy nhất
    with pytest.raises(GeometryError) as exc_coplanar:
        circumscribed_sphere([A, B, C, D])
    assert exc_coplanar.value.code == ERR_KHONG_NGOAI_TIEP

    # 2. Điểm thứ 5 không nằm trên mặt cầu ngoại tiếp của 4 điểm đầu -> từ chối fail-closed
    D_skew = Vec3.of(0, 5, 0)
    with pytest.raises(GeometryError) as exc_non_cospherical:
        circumscribed_sphere([S, A, B, C, D_skew])
    assert exc_non_cospherical.value.code == ERR_KHONG_NGOAI_TIEP


def test_sphere_plane_projection_and_tangent_invariants() -> None:
    I = Vec3.of(0, 0, 0)

    # 1. Mặt phẳng cắt z = 3: hình chiếu của tâm I(0,0,0) là H(0,0,3), d^2 = 9 < R^2 = 25 -> r^2 = 16
    p_sec = Plane3(Vec3.of(0, 0, 3), Vec3.of(0, 0, 1))
    H_sec = K.project_point_onto_plane(I, p_sec)
    assert H_sec == Vec3.of(0, 0, 3)
    d_sq_sec = (H_sec - I).dot(H_sec - I)
    assert d_sq_sec == Fraction(9, 1)
    assert Fraction(25, 1) - d_sq_sec == Fraction(16, 1)

    # 2. Mặt phẳng tiếp xúc tại A(3, 0, 4): 3x + 4z - 25 = 0 -> hình chiếu của I lên (P) trùng A và d^2 = 25 = R^2
    A_tan = Vec3.of(3, 0, 4)
    p_tan = Plane3(A_tan, Vec3.of(3, 0, 4))
    H_tan = K.project_point_onto_plane(I, p_tan)
    assert H_tan == A_tan
    d_sq_tan = (H_tan - I).dot(H_tan - I)
    assert d_sq_tan == Fraction(25, 1)


def test_oxyz_line_plane_intersection_and_parallel_fail_closed() -> None:
    plane = Plane3.through(
        Vec3.of(6, 0, 0),
        Vec3.of(0, 6, 0),
        Vec3.of(0, 0, 6),
    )
    E = Vec3.of(3, 3, 6)
    line_d = Line3(E, Vec3.of(1, 1, 3))

    M = K.intersect_line_plane(line_d, plane)
    assert M == Vec3(Fraction(9, 5), Fraction(9, 5), Fraction(12, 5))
    assert M.x + M.y + M.z - Fraction(6, 1) == Fraction(0, 1)

    # Đường thẳng song song với mặt phẳng x + y + z - 6 = 0 (vector chỉ phương (1, -1, 0)) -> fail-closed
    line_par = Line3(E, Vec3.of(1, -1, 0))
    with pytest.raises(GeometryError) as exc_par:
        K.intersect_line_plane(line_par, plane)
    assert exc_par.value.code == ERR_SONG_SONG
