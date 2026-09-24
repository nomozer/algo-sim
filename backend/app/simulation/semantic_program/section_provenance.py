# -*- coding: utf-8 -*-
"""CHUẨN HOÁ XUẤT XỨ THIẾT DIỆN — `polygon3` thành `section` CHỈ KHI có bằng chứng.

`SECTION_PROVENANCE_NORMALIZATION` (2026-09-20).

─── HAI TẦNG ĐANG TRẢ LỜI KHÁC NHAU, VÀ CẢ HAI ĐỀU ĐÚNG ────────────────────

`OBLIGATION_KINDS['section_matches'] = {section, polygon3}`, và `check_section_matches`
nhận cả một dãy `Vec3` làm chủ thể — tầng nghĩa vụ công nhận thiết diện theo **quan hệ
semantic đã kiểm chứng**: dựng lại `cross_section(solid, plane)` rồi so chu trình.

`_than_hinh_hoc` phân loại theo **lớp runtime**, và frontend
(`scene3d-subentities.ts`) nhận đúng `type === "section"` — tầng cảnh công nhận theo
**phép dựng**.

Hệ quả đo được: một chương trình dựng đa giác bằng `construct_polygon` với ĐÚNG các đỉnh
thiết diện, kèm nghĩa vụ `section_matches` đã qua C₂, vẫn ra cảnh là `polygon3`. Frontend
không vẽ thiết diện, và cổng trực quan (863c912) từ chối đúng
`VISUAL_OBJECT_TYPE_MISMATCH`.

─── ĐƯỜNG DUY NHẤT SINH RA MỘT `polygon3` LÀ THIẾT DIỆN ────────────────────

`exec_construct_section` LUÔN trả `Section`; không nhánh nào trả dãy đỉnh trần. Nên
KHÔNG có `polygon3` nào "sinh trực tiếp từ `construct_section`". Đường duy nhất là
`construct_polygon` + một nghĩa vụ `section_matches` trỏ vào nó. Vì vậy bằng chứng
plane–solid nằm ở **quan hệ semantic**, không ở phép dựng — và module này phải đọc
`contract.obligations`.

─── VÌ SAO LÀ MỘT LƯỢT SAU, KHÔNG PHẢI SỬA `build_scene` ───────────────────

`build_scene(spec, final_memory)` KHÔNG nhận `contract`. Cho nó nhận `contract` là trộn
hai câu hỏi khác nhau (lớp runtime ↔ quan hệ semantic) vào một chỗ. `route` thì bị cấm
biết tới cảnh. Nên chuẩn hoá chạy trong `pipeline._dung_scene3d`, ngay sau
`build_scene3d` và trước khi cảnh vào `outcome.scene3d` — tức **trước** cổng trực quan.

─── KHÔNG BAO GIỜ DÙNG LÀM BẰNG CHỨNG ──────────────────────────────────────

tên chứa "section"/"thiết diện" · ID có tiền tố · đúng ba đỉnh · đồng phẳng · đáp số
diện tích đúng · vật tự khai `type = "section"` mà không nghĩa vụ nào cho nó nguồn.

KHÔNG LƯU trong chẩn đoán: đề, chương trình, cảnh, tên vật, toạ độ, giá trị bộ nhớ.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: Loại vật cảnh chính tắc của một thiết diện. Phải trùng `scene3d.RENDER_HINT`.
CANONICAL_SECTION_KIND = "section"

NORMALIZATION_VERSION = "section-provenance/1"

#: Nghĩa vụ mang quan hệ *"chủ thể này là thiết diện của khối K với mặt phẳng P"*.
NGHIA_VU_THIET_DIEN = "section_matches"

TRANG_THAI: tuple[str, ...] = ("ALREADY_CANONICAL", "NORMALIZED", "NOT_NORMALIZED")

MA_LY_DO: tuple[str, ...] = (
    "ALREADY_SECTION",
    "NORMALIZED_FROM_PLANE_SOLID_INTERSECTION",
    #: Chủ thể không phải một đa giác (không có dãy đỉnh đọc được).
    "SUBJECT_NOT_POLYGONAL",
    "SOURCE_SOLID_UNRESOLVED",
    "SOURCE_PLANE_UNRESOLVED",
    #: Mặt phẳng của nghĩa vụ không cắt được khối (kernel báo suy biến).
    "SECTION_DEGENERATE",
    "CYCLE_MISMATCH",
    #: Nhiều nghĩa vụ cùng chủ thể khai nguồn KHÁC NHAU ⇒ không đoán.
    "AMBIGUOUS_SECTION_SOURCE",
)


@dataclass(frozen=True)
class HangChuanHoa:
    """Một dòng chẩn đoán — theo NGHĨA VỤ, không theo vật. Không chở tên."""

    obligation_id: str
    status: str
    reason_code: str
    normalized_object_count: int


@dataclass(frozen=True)
class KetQuaChuanHoa:
    scene: dict[str, Any]
    hang: tuple[HangChuanHoa, ...]
    normalized_count: int
    #: Tra cứu theo id vật — CHỈ dùng trong test/bộ đo, KHÔNG đi vào chẩn đoán.
    hang_theo_id: dict[str, HangChuanHoa]


def _dinh_cua(o: dict) -> list | None:
    """Dãy đỉnh của một vật cảnh, bất kể nó đang mang tên trường nào."""
    for truong in ("polygon", "vertices"):
        v = o.get(truong)
        if isinstance(v, (list, tuple)) and v:
            return list(v)
    return None


def _diem_cua(gt: Any) -> list | None:
    """Giá trị bộ nhớ → dãy `Vec3`, hoặc `None` nếu không phải đa giác."""
    from app.simulation.geometry.exact import Vec3
    from app.simulation.geometry.section import Section

    if isinstance(gt, Section):
        return list(gt.polygon)
    if isinstance(gt, (list, tuple)) and gt and all(isinstance(p, Vec3) for p in gt):
        return list(gt)
    return None


def _nguon_thiet_dien(contract: Any) -> dict[str, Any]:
    """`tên chủ thể → (solid, plane)` hoặc `AMBIGUOUS`, từ các nghĩa vụ `section_matches`.

    Hai nghĩa vụ cùng chủ thể mà khai nguồn khác nhau ⇒ `AMBIGUOUS`, KHÔNG phải
    "ai đến trước thắng" — nếu không, đảo thứ tự nghĩa vụ sẽ đổi kết quả.
    """
    ra: dict[str, Any] = {}
    for ob in (getattr(contract, "obligations", None) or ()):
        if ob.kind != NGHIA_VU_THIET_DIEN or not ob.container:
            continue
        cap = (ob.params.get("solid"), ob.params.get("plane"))
        if ob.container in ra and ra[ob.container] != cap:
            ra[ob.container] = "AMBIGUOUS"
        elif ra.get(ob.container) != "AMBIGUOUS":
            ra[ob.container] = cap
    return ra


def _phan_xu(dinh_ct: list, solid_ten, plane_ten, memory: dict) -> str:
    """Chu trình của chủ thể có ĐÚNG là thiết diện `solid ∩ plane` không. Trả MÃ LÝ DO.

    Thẩm quyền hình học là `cross_section` + `same_section_cycle` — ĐÚNG hai hàm
    `check_section_matches` dùng. Không có bản cài thứ hai ở đây.
    """
    from app.simulation.geometry.exact import GeometryError, Plane3
    from app.simulation.geometry.section import (
        Polyhedron,
        cross_section,
        same_section_cycle,
    )

    sol = memory.get(solid_ten) if isinstance(solid_ten, str) else None
    pl = memory.get(plane_ten) if isinstance(plane_ten, str) else None
    if not isinstance(sol, Polyhedron):
        return "SOURCE_SOLID_UNRESOLVED"
    if not isinstance(pl, Plane3):
        return "SOURCE_PLANE_UNRESOLVED"
    try:
        chuan = cross_section(sol, pl)
    except GeometryError:
        return "SECTION_DEGENERATE"
    if not same_section_cycle(dinh_ct, chuan.polygon):
        return "CYCLE_MISMATCH"
    return "NORMALIZED_FROM_PLANE_SOLID_INTERSECTION"


def _thanh_section(o: dict, solid_ten: str, plane_ten: str) -> dict:
    """Vật `polygon3` → vật `section` chính tắc. Vật MỚI, không sửa vật cũ.

    GIỮ NGUYÊN `producer`/`depends`/`sources`/`origin`: chương trình ấy dựng bằng
    `construct_polygon`, và nói khác đi là nói dối về cách vật được tạo ra. Nguồn
    plane–solid đi ở trường RIÊNG `section_source`.

    KHÔNG có `steps` — frontend đã có nhánh dự phòng (`scene3d-subentities.ts:258`),
    và bịa bước dựng là bịa một thao tác chương trình chưa từng làm.
    """
    dinh = _dinh_cua(o) or []
    moi = {k: v for k, v in o.items() if k != "vertices"}
    moi["type"] = CANONICAL_SECTION_KIND
    moi["polygon"] = dinh
    moi["closed"] = True
    moi["section_source"] = {"solid": solid_ten, "plane": plane_ten,
                             "evidence": "SECTION_MATCHES_OBLIGATION"}
    return moi


def normalize_section_provenance(scene: dict | None, memory: dict | None,
                                 contract: Any) -> KetQuaChuanHoa:
    """Chuẩn hoá thiết diện trong một cảnh đã dựng. TẤT ĐỊNH · IDEMPOTENT · immutable.

    Trả cảnh MỚI; `scene` đầu vào không bị sửa một byte.
    """
    doi: dict[str, tuple[str, str]] = {}
    hang: list[HangChuanHoa] = []
    theo_id: dict[str, HangChuanHoa] = {}
    objs = list((scene or {}).get("objects", ()))
    mem = memory or {}

    for i, (ten, nguon) in enumerate(sorted(_nguon_thiet_dien(contract).items())):
        vat = next((o for o in objs if o.get("id") == ten), None)
        oid = f"{NGHIA_VU_THIET_DIEN}#{i}"

        if vat is not None and vat.get("type") == CANONICAL_SECTION_KIND:
            h = HangChuanHoa(oid, "ALREADY_CANONICAL", "ALREADY_SECTION", 0)
        elif nguon == "AMBIGUOUS":
            h = HangChuanHoa(oid, "NOT_NORMALIZED", "AMBIGUOUS_SECTION_SOURCE", 0)
        else:
            dinh = _diem_cua(mem.get(ten))
            if dinh is None or len(dinh) < 3:
                h = HangChuanHoa(oid, "NOT_NORMALIZED", "SUBJECT_NOT_POLYGONAL", 0)
            else:
                ma = _phan_xu(dinh, nguon[0], nguon[1], mem)
                if ma != "NORMALIZED_FROM_PLANE_SOLID_INTERSECTION":
                    h = HangChuanHoa(oid, "NOT_NORMALIZED", ma, 0)
                else:
                    # BÍ DANH: mọi vật giữ CÙNG GIÁ TRỊ đều là cùng một hình, nên
                    # được chuẩn hoá cùng lúc — ở MỌI độ sâu `assign`, không phải
                    # đoán đâu là "chuỗi bí danh" từ `depends`.
                    cung = [o["id"] for o in objs
                            if o.get("type") == "polygon3"
                            and _diem_cua(mem.get(o.get("id"))) == dinh]
                    for cid in cung:
                        doi[cid] = (nguon[0], nguon[1])
                    h = HangChuanHoa(oid, "NORMALIZED", ma, len(cung))
        hang.append(h)
        if vat is not None:
            theo_id[ten] = h

    moi = [_thanh_section(o, *doi[o["id"]]) if o.get("id") in doi else o for o in objs]
    return KetQuaChuanHoa(
        scene={**(scene or {}), "objects": moi},
        hang=tuple(hang),
        normalized_count=len(doi),
        hang_theo_id=theo_id,
    )


def chan_doan_chuan_hoa(kq: KetQuaChuanHoa) -> dict[str, Any]:
    """Chẩn đoán máy đọc được — TỪ VỰNG ĐÓNG, không tên, không toạ độ, không giá trị."""
    return {
        "normalization_version": NORMALIZATION_VERSION,
        "canonical_section_kind": CANONICAL_SECTION_KIND,
        "requested_count": len(kq.hang),
        "normalized_object_count": kq.normalized_count,
        "obligations": [
            {
                "obligation_id": h.obligation_id,
                "status": h.status,
                "reason_code": h.reason_code,
                "normalized_object_count": h.normalized_object_count,
            }
            for h in kq.hang
        ],
    }
