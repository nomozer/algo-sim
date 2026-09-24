# -*- coding: utf-8 -*-
"""CỔNG PHỦ NGHĨA VỤ TRỰC QUAN — vật mà đề bảo VẼ có thật sự nằm trong cảnh không.

`SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE` (2026-09-20).

─── BỆNH ĐÃ ĐO ────────────────────────────────────────────────────────────

`B02_STRUCTURAL_COVERAGE_LIVE_REVALIDATION` (2026-09-15): synthesis được nhận ngay
lượt đầu, route trả `served`, `final_memory` và cả ba đáp số ĐÚNG — mà cảnh **không
có một vật `section` nào**. Học sinh nhận một lời giải tính đúng diện tích thiết
diện trên một hình không hề vẽ thiết diện. `SILENT_QUALITY_FAILURE`.

`SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS` tách đôi nguyên nhân:
  ① `COMPUTATION_ONLY_COVERAGE` — C₁a chỉ kiểm ĐƯỜNG PHÉP TÍNH: kiểu container được
     nhận + witness dẫn xuất từ container. Một đa giác đáy thay cho thiết diện vẫn
     qua, với đáp số đúng.
  ② `SCENE_TYPE_OR_PROVENANCE_MISMATCH` — tầng nghĩa vụ nhận `polygon3` là thiết
     diện (`OBLIGATION_KINDS['section_matches']`), cảnh và frontend thì chỉ nhận
     `type == "section"`.

Cổng này hỏi câu mà KHÔNG cổng nào đang hỏi: *chủ thể của nghĩa vụ có MẶT trong
cảnh, đúng một kiểu nghĩa vụ ấy nhận, có xuất xứ, và đúng topology không.*

─── VÌ SAO KHÔNG CÓ NHÁNH RIÊNG CHO B02 ───────────────────────────────────

Luật chạy trên TẬP KIỂU CHẤP NHẬN ĐƯỢC của từng nghĩa vụ (`OBLIGATION_KINDS`, vốn
DẪN XUẤT từ `measure_contract.BANG_PHEP_DO`), không trên một loại vật cố định. Đo
được từ manifest benchmark, và đây là dữ kiện đã CHẶN một thiết kế sai:

    B02  area(T)  → thiết diện ĐA GIÁC → vật cảnh đúng là `section`
    B03  area(C)  → thiết diện TRÒN    → vật cảnh đúng là `circle3`

Nên *"mọi nghĩa vụ `area` đều đòi một vật `section`"* là SAI và sẽ phá parity B03.

─── KHOẢNG TRỐNG HỢP ĐỒNG, KHAI THẲNG ─────────────────────────────────────

`RequestContract` KHÔNG phân biệt được "diện tích đa giác phẳng thường" với "diện
tích thiết diện" — cả hai khai đúng một `area(container)`. Khi nghĩa vụ nhận CẢ
`section` LẪN `polygon3`, vật quan sát được là `polygon3`, và không có
`section_matches` nào phân xử ⇒ `UNVERIFIABLE` ⇒ route TỪ CHỐI AN TOÀN.
KHÔNG đoán theo tên biến, KHÔNG dò chuỗi trên đề. Sửa khoảng trống ấy là đổi lược
đồ analyze ⇒ đổi BỀ MẶT MÔ HÌNH ⇒ phải đo lại; ngoài phạm vi wave này.

─── RANH GIỚI ─────────────────────────────────────────────────────────────

Module này **KHÔNG import `scene3d`**: `tests/geometry/test_scene3d.py::
test_KHONG_module_nao_o_TANG_DUOI_nhap_scene3d` quét AST và cấm mọi file dưới
`app/simulation` làm vậy. Cảnh đi vào đây dưới dạng `dict` THUẦN, do `pipeline`
đổ vào. Hướng phụ thuộc vì thế không phải nới một milimét nào.

Module này cũng **không tự làm hình học**: đồng phẳng hỏi
`geometry.predicates.coplanar`, toạ độ hỏi `geometry.exact.points_of` — cùng
thẩm quyền mà kernel dùng. Không có bản cài thứ hai.

KHÔNG LƯU: đề, chương trình, cảnh, tên vật, toạ độ, giá trị bộ nhớ, công thức,
prompt, output mô hình. Mọi chuỗi trong chẩn đoán thuộc TỪ VỰNG ĐÓNG dưới đây.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from app.simulation.error_codes import ErrorCode

from .obligations import OBLIGATION_KINDS

#: Phiên bản hợp đồng chẩn đoán. Đổi HÌNH DẠNG hàng ⇒ tăng số.
DIAGNOSTIC_VERSION = "visual-obligation-coverage/1"

#: Pha route ổn định. Runner dựng `ROUTE_{stage_reached.upper()}` nên KHÔNG có
#: bảng ánh xạ thứ hai ở đâu cả.
ROUTE_STAGE = "visual_coverage"

TRANG_THAI: tuple[str, ...] = ("COVERED", "UNCOVERED", "UNVERIFIABLE")

MA_LY_DO: tuple[str, ...] = (
    "COVERED",
    #: Nghĩa vụ không hứa một vật nào trên cảnh (quan hệ song song/vuông góc…).
    "NOT_A_VISUAL_OBLIGATION",
    "VISUAL_OBJECT_MISSING",
    "VISUAL_OBJECT_TYPE_MISMATCH",
    "VISUAL_PROVENANCE_MISSING",
    "VISUAL_TOPOLOGY_MISMATCH",
    "VISUAL_OBLIGATION_UNVERIFIABLE",
)

LOAI_TRUC_QUAN: tuple[str, ...] = ("SECTION_IDENTITY", "MEASURED_SUBJECT", "NONE")

#: Bảng ĐÓNG các kiểu vật tới được cảnh. Phải TRÙNG `scene3d.RENDER_HINT` — không
#: import được (ranh giới ở trên), nên `test_visual_obligation_gate.py` khoá đồng
#: bộ hai bảng. Một bảng trôi khỏi bảng kia là ĐỎ.
KIEU_CANH_HOP_LE: tuple[str, ...] = (
    "circle3", "curved_solid", "ellipse3", "line3", "plane3",
    "point3", "polygon3", "quantity", "section", "solid", "vector3",
)

#: Kiểu vật cảnh phải là ĐA GIÁC KHÉP KÍN đồng phẳng mới được tính là phủ.
KIEU_DOI_TOPOLOGY: frozenset[str] = frozenset({"section", "polygon3"})

#: Trường chở dãy đỉnh, theo kiểu vật. `section` dùng `polygon`, `polygon3` dùng
#: `vertices` — hai tên khác nhau ở `simulation_state._than_hinh_hoc`.
TRUONG_DINH: dict[str, str] = {"section": "polygon", "polygon3": "vertices"}

#: Nghĩa vụ đòi ĐÍCH DANH một thiết diện, bất kể tầng kiểu có nới hay không.
#:
#: `OBLIGATION_KINDS['section_matches']` nhận cả `polygon3` — CỐ Ý, để chương
#: trình sinh trước 2026-08-30 không rơi xuống mức yếu. Nhưng đó là câu hỏi về
#: KIỂU HỢP ĐỒNG; câu hỏi ở đây là về VẬT TRÊN MÀN HÌNH, và frontend
#: (`deriveSectionSubEntities`) chỉ nhận `type === "section"`. Hai câu hỏi khác
#: nhau được phép có hai câu trả lời khác nhau — đó là toàn bộ bệnh ②.
NGHIA_VU_DOI_SECTION: frozenset[str] = frozenset({"section_matches"})


def kieu_canh_yeu_cau(kind: str) -> tuple[str, ...]:
    """Nghĩa vụ này đòi chủ thể của nó hiện ra dưới những kiểu vật nào.

    DẪN XUẤT từ `OBLIGATION_KINDS` — mở một lượng đo cho kiểu mới là cổng này
    **tự** nhận kiểu ấy, không có bản sao nào để quên. Lọc qua
    `KIEU_CANH_HOP_LE` vì taxonomy còn chở kiểu Tin học (`array`, `graph`…)
    không bao giờ tới được cảnh.
    """
    if kind in NGHIA_VU_DOI_SECTION:
        return ("section",)
    thô = OBLIGATION_KINDS.get(kind) or frozenset()
    return tuple(sorted(k for k in thô if k in KIEU_CANH_HOP_LE))


@dataclass(frozen=True)
class NghiaVuTrucQuan:
    """Nghĩa vụ TRỰC QUAN suy từ một nghĩa vụ hợp đồng — có kiểu, không có tên."""

    obligation_id: str
    source_contract_pointer: str | None
    pointer_status: str
    visual_kind: str
    target_kind: str | None
    required_scene_kind: tuple[str, ...]
    provenance_requirement: str
    topology_requirement: str
    #: Tên chủ thể — CHỈ sống trong bộ nhớ để tra cảnh. KHÔNG bao giờ ra chẩn đoán.
    _container: str = field(default="", repr=False)


@dataclass(frozen=True)
class KetQuaNghiaVuTrucQuan:
    obligation_id: str
    source_contract_pointer: str | None
    pointer_status: str
    visual_kind: str
    target_kind: str | None
    required_scene_kind: tuple[str, ...]
    provenance_requirement: str
    topology_requirement: str
    status: str
    reason_code: str
    evidence_count: int
    evidence_kinds: tuple[str, ...]


@dataclass(frozen=True)
class KetQuaTrucQuan:
    verdict: str
    obligations: tuple[KetQuaNghiaVuTrucQuan, ...]
    requested_count: int
    covered_count: int
    uncovered_count: int
    unverifiable_count: int


def _van_tay(ob) -> str:
    """16 hex SHA-256 của nghĩa vụ — CHỈ để tự kiểm con trỏ, KHÔNG ghi ra."""
    tho = json.dumps(ob.model_dump(mode="json"), sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"))
    return hashlib.sha256(tho.encode("utf-8")).hexdigest()[:16]


def _con_tro(contract, chi_so: int, ob) -> tuple[str | None, str]:
    """Con trỏ RFC 6901 dựng từ chỉ số vòng lặp, rồi TỰ KIỂM bằng vân tay.

    Tên trường không được tin suông: lệch vân tay ⇒ `None` + `AMBIGUOUS`, không bịa.
    """
    try:
        tho = contract.model_dump(mode="json")["obligations"][chi_so]
    except (KeyError, IndexError, TypeError):
        return None, "AMBIGUOUS"
    cùng = json.dumps(tho, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if hashlib.sha256(cùng.encode("utf-8")).hexdigest()[:16] != _van_tay(ob):
        return None, "AMBIGUOUS"
    return f"/obligations/{chi_so}", "EXACT"


def suy_nghia_vu_truc_quan(contract) -> tuple[NghiaVuTrucQuan, ...]:
    """`RequestContract` → dãy nghĩa vụ trực quan, THỨ TỰ NGUỒN, không lọc, không sắp.

    Suy từ biểu diễn CÓ KIỂU (`kind` + `container`), không dò chuỗi trên đề.
    """
    ra: list[NghiaVuTrucQuan] = []
    for i, ob in enumerate(contract.obligations):
        ct, tt = _con_tro(contract, i, ob)
        yeu_cau = kieu_canh_yeu_cau(ob.kind)
        if ob.kind in NGHIA_VU_DOI_SECTION:
            loai = "SECTION_IDENTITY"
        elif yeu_cau:
            loai = "MEASURED_SUBJECT"
        else:
            loai = "NONE"
        ra.append(NghiaVuTrucQuan(
            obligation_id=f"{ob.kind}#{i}",
            source_contract_pointer=ct,
            pointer_status=tt,
            visual_kind=loai,
            target_kind=None,
            required_scene_kind=yeu_cau,
            provenance_requirement="PRODUCER_REQUIRED" if loai != "NONE" else "NONE",
            topology_requirement=("CLOSED_COPLANAR_POLYGON"
                                  if any(k in KIEU_DOI_TOPOLOGY for k in yeu_cau) else "NONE"),
            _container=ob.container or "",
        ))
    return tuple(ra)


def _vat_cua(scene: dict, container: str, resolved_names: dict) -> list[dict]:
    """Vật cảnh của một tên HỢP ĐỒNG, qua ĐÚNG thẩm quyền tên của C₁a.

    `resolved_names` là bản đồ *tên hợp đồng → tên chương trình* mà C₁a đã giải.
    Không hoà giải lần thứ tám ở đây (ERRATUM #4).
    """
    ten_ct = (resolved_names or {}).get(container, container)
    return [o for o in scene.get("objects", ()) if o.get("id") in (ten_ct, container)]


def _co_xuat_xu(o: dict) -> bool:
    """Vật này có truy được về phép dựng nào không.

    ⚠️ KHÔNG chỉ hỏi `producer`, và đây là một BẪY ĐÃ SẬP: bản đầu của cổng hỏi
    đúng `producer` và lập tức đánh trượt p4 (trụ) lẫn p5 (nón) — hai ca HỢP LỆ
    đang được phục vụ. Nguyên nhân: chương trình đặt BÍ DANH cho khối đã dựng
    (`assign hình trụ = khối trụ`), mà `assign` không phải phép dựng nên
    `_provenance` không gắn `producer`. Vật bí danh vẫn `origin="derived"` và vẫn
    `depends: ["khối trụ"]` — tức truy được hoàn toàn.

    Nên câu hỏi đúng là *"có truy được về đâu không"*, và `depends`/`sources` trả
    lời nó y như `producer`. Vật KHÔNG có cả ba mới là vật rơi từ trên trời xuống.

    ⚠️ BẪY THỨ HAI, cùng lớp, sập ngay sau bản vá thứ nhất: điểm do ĐỀ CHO
    (`declare_point`) mang `origin="free"`, `producer=None`, `depends=[]` — và nó
    ĐÚNG như thế. Nó không được DỰNG, nó được KHAI, và xuất xứ của nó là chính đề
    bài. Đòi `producer` ở đây đánh trượt mọi bài hỏi khoảng cách từ một điểm đề
    cho (`tests/test_mocked_production_e2e.py`). `origin` là thẩm quyền phân biệt
    "chương trình tạo ra" với "đề cho sẵn" — hỏi nó thay vì đoán.
    """
    if o.get("origin") == "free":
        return True
    return bool(o.get("producer") or o.get("depends") or o.get("sources"))


def _topology_dat(o: dict) -> bool:
    """Đa giác khép kín, ≥ 3 đỉnh phân biệt, và MỌI đỉnh đồng phẳng."""
    truong = TRUONG_DINH.get(o.get("type") or "")
    dinh = o.get(truong) if truong else None
    if not isinstance(dinh, (list, tuple)) or len(dinh) < 3:
        return False
    if o.get("type") == "section" and o.get("closed") is not True:
        return False
    try:
        from app.simulation.geometry.exact import points_of
        from app.simulation.geometry.predicates import coplanar

        p = points_of(dinh)
    except Exception:  # noqa: BLE001 — toạ độ không đọc được ⇒ KHÔNG khai là đạt
        return False
    if len({(v.x, v.y, v.z) for v in p}) < 3:
        return False
    return all(coplanar(p[0], p[1], p[2], p[k]) for k in range(3, len(p)))


def check_visual_obligations(contract, scene: dict | None,
                             resolved_names: dict | None = None) -> KetQuaTrucQuan:
    """Cảnh có mang đủ vật mà các nghĩa vụ đòi nhìn thấy không. TẤT ĐỊNH, chỉ ĐỌC.

    `scene is None` ⇒ không có cảnh để phán ⇒ mọi nghĩa vụ `UNVERIFIABLE`. Người
    GỌI quyết định điều đó có nghĩa gì (xem `ap_dung`: bài không phải hình học
    thì cổng không phán gì cả).
    """
    hang: list[KetQuaNghiaVuTrucQuan] = []
    for nv in suy_nghia_vu_truc_quan(contract):
        vat = _vat_cua(scene or {}, nv._container, resolved_names or {})
        kieu = tuple(sorted({o.get("type") for o in vat if o.get("type") in KIEU_CANH_HOP_LE}))
        hop = [o for o in vat if o.get("type") in nv.required_scene_kind]

        if nv.visual_kind == "NONE":
            tt, ma = "COVERED", "NOT_A_VISUAL_OBLIGATION"
        elif scene is None:
            tt, ma = "UNVERIFIABLE", "VISUAL_OBLIGATION_UNVERIFIABLE"
        elif not vat:
            tt, ma = "UNCOVERED", "VISUAL_OBJECT_MISSING"
        elif not hop:
            tt, ma = "UNCOVERED", "VISUAL_OBJECT_TYPE_MISMATCH"
        elif not any(_co_xuat_xu(o) for o in hop):
            tt, ma = "UNCOVERED", "VISUAL_PROVENANCE_MISSING"
        elif _mo_ho_section(nv, hop, contract):
            # Hợp đồng nhận cả `section` lẫn `polygon3`, vật là `polygon3`, và
            # KHÔNG nghĩa vụ nào phân xử ⇒ không biết đây là thiết diện bị bỏ sót
            # hay một đa giác hợp lệ. Từ chối AN TOÀN, không đoán.
            tt, ma = "UNVERIFIABLE", "VISUAL_OBLIGATION_UNVERIFIABLE"
        elif (nv.topology_requirement == "CLOSED_COPLANAR_POLYGON"
              and any(o.get("type") in KIEU_DOI_TOPOLOGY for o in hop)
              and not any(_topology_dat(o) for o in hop
                          if o.get("type") in KIEU_DOI_TOPOLOGY)):
            tt, ma = "UNCOVERED", "VISUAL_TOPOLOGY_MISMATCH"
        else:
            tt, ma = "COVERED", "COVERED"

        hang.append(KetQuaNghiaVuTrucQuan(
            obligation_id=nv.obligation_id,
            source_contract_pointer=nv.source_contract_pointer,
            pointer_status=nv.pointer_status,
            visual_kind=nv.visual_kind,
            target_kind=(kieu[0] if len(kieu) == 1 else None),
            required_scene_kind=nv.required_scene_kind,
            provenance_requirement=nv.provenance_requirement,
            topology_requirement=nv.topology_requirement,
            status=tt,
            reason_code=ma,
            evidence_count=len(hop),
            evidence_kinds=kieu,
        ))

    chua = sum(1 for r in hang if r.status == "UNCOVERED")
    kho = sum(1 for r in hang if r.status == "UNVERIFIABLE")
    return KetQuaTrucQuan(
        verdict=("COVERED" if not chua and not kho
                 else "UNCOVERED" if chua else "UNVERIFIABLE"),
        obligations=tuple(hang),
        requested_count=len(hang),
        covered_count=sum(1 for r in hang if r.status == "COVERED"),
        uncovered_count=chua,
        unverifiable_count=kho,
    )


def _mo_ho_section(nv: NghiaVuTrucQuan, hop: list[dict], contract) -> bool:
    """Vật là `polygon3` trong khi nghĩa vụ cũng nhận `section`, và không gì phân xử."""
    if nv.visual_kind != "MEASURED_SUBJECT":
        return False
    if "section" not in nv.required_scene_kind:
        return False
    if any(o.get("type") == "section" for o in hop):
        return False
    if not any(o.get("type") == "polygon3" for o in hop):
        return False
    # `section_matches` trên CÙNG chủ thể là lời phân xử có kiểu — có nó thì
    # nghĩa vụ ấy tự phán, hàng này không cần đoán nữa.
    return not any(ob.kind in NGHIA_VU_DOI_SECTION and ob.container == nv._container
                   for ob in contract.obligations)


def chan_doan_truc_quan(kq: KetQuaTrucQuan) -> dict[str, Any]:
    """Chẩn đoán máy đọc được — TỪ VỰNG ĐÓNG, không tên, không toạ độ, không giá trị."""
    return {
        "diagnostic_version": DIAGNOSTIC_VERSION,
        "verdict": kq.verdict,
        "requested_count": kq.requested_count,
        "covered_count": kq.covered_count,
        "uncovered_count": kq.uncovered_count,
        "unverifiable_count": kq.unverifiable_count,
        "obligations": [
            {
                "obligation_id": r.obligation_id,
                "source_contract_pointer": r.source_contract_pointer,
                "pointer_status": r.pointer_status,
                "visual_kind": r.visual_kind,
                "target_kind": r.target_kind,
                "required_scene_kind": list(r.required_scene_kind),
                "provenance_requirement": r.provenance_requirement,
                "topology_requirement": r.topology_requirement,
                "status": r.status,
                "reason_code": r.reason_code,
                "evidence_count": r.evidence_count,
                "evidence_kinds": list(r.evidence_kinds),
            }
            for r in kq.obligations
        ],
    }


#: Lời từ chối cho HỌC SINH — tiếng Việt, không định danh kĩ thuật (§2 bề mặt).
_LOI: dict[str, str] = {
    "VISUAL_OBJECT_MISSING": "hình chưa dựng ra vật mà đề yêu cầu nhìn thấy",
    "VISUAL_OBJECT_TYPE_MISMATCH": "vật đã dựng không đúng loại hình mà đề yêu cầu",
    "VISUAL_PROVENANCE_MISSING": "vật đã dựng không cho biết nó được tạo ra từ đâu",
    "VISUAL_TOPOLOGY_MISMATCH": "hình phẳng đã dựng chưa khép kín hoặc các đỉnh không cùng một mặt phẳng",
    "VISUAL_OBLIGATION_UNVERIFIABLE": "hệ chưa phân biệt được hình đã dựng có đúng là hình đề yêu cầu không",
}


def ap_dung(outcome, contract):
    """Hạ `servable` khi cảnh thiếu nghĩa vụ trực quan. Trả outcome MỚI, hoặc CHÍNH NÓ.

    Ba luật, mỗi luật đã có test riêng:
      · cổng chỉ HẠ, KHÔNG BAO GIỜ NÂNG — `servable=False` đi vào thì đi ra y nguyên;
      · không có cảnh (`scene3d is None`) thì KHÔNG phán gì — bài không phải hình
        học, hoặc chương trình chưa chạy nổi, và cả hai đã có phán quyết đúng rồi;
      · mọi nghĩa vụ được phủ ⇒ trả về CHÍNH đối tượng cũ, không `model_copy`, nên
        ca hợp lệ trùng từng byte.
    """
    if outcome is None or not getattr(outcome, "servable", False):
        return outcome
    if getattr(outcome, "scene3d", None) is None:
        return outcome

    kq = check_visual_obligations(contract, outcome.scene3d,
                                  getattr(outcome, "resolved_names", {}) or {})
    if kq.verdict == "COVERED":
        return outcome

    ma = ErrorCode.VISUAL_OBLIGATION_UNCOVERED
    thieu = [r for r in kq.obligations if r.status != "COVERED"]
    ly_do = sorted({_LOI[r.reason_code] for r in thieu if r.reason_code in _LOI})
    from app.simulation.error_codes import SEMANTIC_FAILURE_CATEGORY

    return outcome.model_copy(update={
        "stage_reached": ROUTE_STAGE,
        # `executable=True` GIỮ NGUYÊN, có chủ đích: hệ CHẠY ĐƯỢC bài này và đáp
        # số có thể đúng hoàn toàn. Cái thiếu là đường lên màn hình.
        "servable": False,
        "error_code": ma.value,
        "failure_category": SEMANTIC_FAILURE_CATEGORY[ma.value],
        "reason": "Mô phỏng chạy được nhưng hình chưa mang đủ thứ đề yêu cầu: "
                  + "; ".join(ly_do) + ".",
        "details": [r.reason_code for r in thieu],
        "visual_diagnostic": chan_doan_truc_quan(kq),
    })
