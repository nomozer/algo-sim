# -*- coding: utf-8 -*-
"""Lớp TRẠNG THÁI MÔ PHỎNG — giữa interpreter và renderer. **0 API call.**

    Semantic Program → Interpreter → **Simulation State** → Renderer 3D

VÌ SAO TỒN TẠI: `memory_snapshot` chứa `Vec3`/`Plane3`/`Polyhedron` dưới dạng
**đối tượng Python**. Renderer không đọc được. File này chiếu chúng sang JSON.

─── LUẬT SỐ MỘT: CHIẾU, KHÔNG TÍNH ──────────────────────────────────────────

Không một dòng nào ở đây làm hình học. Không `cross`, không `dot`, không dựng
điểm. Mọi giá trị đến từ thứ kernel đã tính; file này chỉ **sắp lại**. Một phép
tính hình học lọt vào đây là dựng engine thứ hai — và hai engine thì sẽ lệch,
lệch câm.

Hệ quả cụ thể của luật ấy, và nó định hình toàn bộ thiết kế: `Line3` là đường
**vô hạn** (điểm + vector chỉ phương), `Plane3` là `n·x = d` — cũng **vô hạn**.
Muốn vẽ thì phải có biên hữu hạn, và biên ấy **không có trong kernel**.

Cách giải KHÔNG phải tính biên ở đây. Cách giải là **chở PROVENANCE**: đường
thẳng mang tên hai điểm sinh ra nó, mặt phẳng mang tên ba điểm sinh ra nó. Toạ
độ của những điểm ấy đã có sẵn trong cảnh, nên renderer dựng được biên mà lớp
này không phải tính gì.

Và đó cũng là điều đúng với đề tài: cảnh không mô tả *"hình trông thế nào"* mà
mô tả *"hình được tạo ra thế nào"*.

─── LUẬT SỐ HAI: KHÔNG FLOAT ────────────────────────────────────────────────

Toạ độ xuất dạng **chuỗi phân số** (`"1/2"`), không phải `0.5`. Kernel dựng bằng
`Fraction` để mọi vị ngữ so **bằng đúng**, không epsilon — đó là thứ làm hệ này
khác một bộ vẽ hình. Hoá float ở biên JSON là vứt bỏ đúng thứ ấy, ở đúng chỗ
không ai nhìn thấy.

Renderer hoá float ở **bước cuối cùng trước khi đặt vào buffer**, không sớm hơn.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from ..geometry import Line3, Plane3, Vec3
from ..geometry.radical import Radical, display, to_json
from ..geometry.section import Polyhedron, Section
from .contract import SemanticProgramSpec
from .geometry_exec import la_dai_luong_do, la_doi_tuong_hinh_hoc

#: Câu lệnh dựng → tên các trường mang TÊN đối tượng nó ĐỌC.
#:
#: Viết tay, cùng lý do `validator._BIEU_THUC_HINH_HOC` viết tay: đây là chỗ duy
#: nhất nói *"trường nào chở provenance"*, và dẫn xuất tự động sẽ nuốt luôn
#: `faces` (một bảng chỉ số, không phải tên).
_NGUON_CUA_PHEP_DUNG: dict[str, tuple[str, ...]] = {
    "construct_line": ("through_a", "through_b"),
    "construct_plane": ("through",),
    "construct_solid": ("vertices",),
    "construct_polygon": ("vertices",),
    "construct_section": ("solid", "plane"),
}


def _so(v: Any) -> str:
    """`Fraction` → chuỗi phân số. `"1/2"`, không phải `0.5`.

    `str(Fraction(2, 1))` cho `"2"`, `str(Fraction(1, 2))` cho `"1/2"` — cả hai
    đều đọc ngược lại được bằng `Fraction(s)`, nên chuỗi này là biểu diễn **không
    mất mát**, không phải một cách hiển thị.

    ⚠️ CHỈ dùng cho TOẠ ĐỘ, nơi giá trị luôn hữu tỉ (`Vec3` sống trong ℚ³). Đại
    lượng đo được có thể là căn thức và đi đường khác — `_dai_luong()`.
    """
    return str(v) if isinstance(v, Fraction) else str(Fraction(v))


def _dai_luong(v: Any) -> dict[str, Any]:
    """Đại lượng đo được → CẤU TRÚC máy đọc được, kèm chuỗi hiển thị.

    ─── VÌ SAO KHÔNG CHỈ MỘT CHUỖI ─────────────────────────────────────────

    `"3√2/5"` đọc được bằng mắt và **không** đọc được bằng máy: bộ chấm cần so
    bằng chính xác, frontend cần định dạng theo ngữ cảnh. Đọc ngược một chuỗi
    có ký tự toán học là mời sai sót vào đúng chỗ không được phép sai.

    Nên phát cả hai, và nói rõ cái nào là nguồn: `exact` là NGUỒN, `display` là
    DẪN XUẤT. Frontend cũ (envelope lưu trước wave này) chỉ đọc `value`, nên
    trường ấy giữ nguyên tên và vẫn là chuỗi — thêm trường, không đổi trường.
    """
    return {
        "value": display(v),
        "exact": to_json(v),
    }


def _xyz(p: Vec3) -> list[str]:
    return [_so(p.x), _so(p.y), _so(p.z)]


# ══ 1. ĐỒ THỊ PHỤ THUỘC — API mỏng, KHÔNG dùng để thẩm định ══════════════
def dependency_graph(spec: SemanticProgramSpec) -> dict[str, list[str]]:
    """Mỗi đối tượng phụ thuộc vào những đối tượng nào.

    ─── VÌ SAO CÓ HÀM NÀY ──────────────────────────────────────────────────

    `coverage_gate._phu_thuoc` **đã tính đồ thị này rồi VỨT ĐI** sau khi C₁a
    dùng xong. Không cần tính mới — cần thôi vứt.

    Nhưng `_phu_thuoc`/`_producers` là **chi tiết cài đặt private** của một cổng
    thẩm định. Gọi thẳng chúng từ tầng mô phỏng là buộc hai thứ không liên quan
    vào nhau: một bản vá C₁a sau này sẽ lặng lẽ đổi hình dạng cảnh 3D. Hàm mỏng
    này là chỗ ranh giới ấy được ghi ra.

    ⚠️ **KHÔNG dùng cho thẩm định.** C₁a có bản riêng và bản đó mới là cổng. Đồ
    thị ở đây phục vụ *tô sáng*, *mô phỏng thay đổi*, *tương tác* — nếu ai đó
    dùng nó để gác cửa thì tầng trình bày trở thành tầng thẩm định, và một thay
    đổi thẩm mỹ sẽ đổi được phán quyết.
    """
    from .coverage_gate import _phu_thuoc

    tho = _phu_thuoc(spec.statements, frozenset())
    khai = {d.name for d in spec.memory_declarations}
    return {
        ten: sorted(n for n in nguon if n in khai)
        for ten, nguon in sorted(tho.items())
    }


def _provenance(spec: SemanticProgramSpec) -> dict[str, dict[str, Any]]:
    """`target_var` → phép dựng sinh ra nó, kèm TÊN các đối tượng nguồn.

    Đi trên `statements`, không trên bộ nhớ: bộ nhớ chỉ có **giá trị cuối**, còn
    câu hỏi của đề tài là *"nó được tạo ra thế nào"*.
    """
    ra: dict[str, dict[str, Any]] = {}

    from .validator import _BIEU_THUC_HINH_HOC

    def di(stmts) -> None:
        for st in stmts or ():
            kind = getattr(st, "kind", None)
            tv = getattr(st, "target_var", None)
            if kind == "construct_point" and tv:
                # `construct_point` KHÔNG có trường tên ở câu lệnh — nguồn nằm
                # trong BIỂU THỨC (`midpoint.a/b`, `project_onto.point/target`…).
                # Bỏ sót nhánh này thì mọi điểm dựng ra đều `producer: null`, tức
                # cảnh mất đúng thứ đề tài muốn kể: *nó được tạo ra thế nào*.
                #
                # Bảng tên trường nhập từ `validator` — MỘT nguồn sự thật, và
                # bảng ấy cố ý không gồm `ratio` (một phân số, không phải tên).
                e = getattr(st, "expr", None)
                truong = _BIEU_THUC_HINH_HOC.get(getattr(e, "kind", None), ())
                nguon = [x for x in (getattr(e, f, None) for f in truong)
                         if isinstance(x, str)]
                ra[tv] = {"producer": f"construct_point.{getattr(e, 'kind', '?')}",
                          "sources": nguon, "label": getattr(st, "label", None)}
            elif kind in _NGUON_CUA_PHEP_DUNG and tv:
                nguon: list[str] = []
                for f in _NGUON_CUA_PHEP_DUNG[kind]:
                    v = getattr(st, f, None)
                    if isinstance(v, str):
                        nguon.append(v)
                    elif isinstance(v, list):
                        nguon += [x for x in v if isinstance(x, str)]
                ra[tv] = {"producer": kind, "sources": nguon,
                          "label": getattr(st, "label", None)}
            elif kind == "assign" and tv:
                e = getattr(st, "expr", None)
                if getattr(e, "kind", None) == "measure":
                    nguon = [x for x in (getattr(e, "of", None),
                                         getattr(e, "wrt", None))
                             if isinstance(x, str)]
                    ra[tv] = {"producer": f"measure.{e.quantity}",
                              "sources": nguon, "label": None}
            for attr in ("body", "then_body", "else_body"):
                sub = getattr(st, attr, None)
                if sub:
                    di(sub)

    di(spec.statements)
    return ra


# ══ 2. GEOMETRY SCENE — chiếu bộ nhớ ═════════════════════════════════════
def build_scene(
    spec: SemanticProgramSpec, memory: dict[str, Any]
) -> dict[str, Any]:
    """Bộ nhớ + chương trình → cảnh hình học JSON.

    Chỉ nhặt đối tượng HÌNH HỌC. Biến `int`/`array`/`map` của miền Tin học không
    thuộc cảnh 3D, và nhét chúng vào là mời renderer đoán xem phải vẽ gì.

    Đối tượng khai mà chưa dựng (`initial_value: null`, câu lệnh chưa chạy tới)
    có mặt trong `memory` với giá trị `None` — bỏ qua, không dựng một ô rỗng.
    """
    from .coverage_gate import _producers

    tao_ra = _producers(spec.statements)
    prov = _provenance(spec)
    kieu = {d.name: d.type for d in spec.memory_declarations}

    objects: list[dict[str, Any]] = []
    for ten, gt in memory.items():
        p = prov.get(ten, {})
        chung = {
            "id": ten,
            "label": p.get("label") or ten,
            # FREE vs DERIVED — DẪN XUẤT, không khai. Một cờ khai được là một cờ
            # khai sai được, và ở đây khai sai nghĩa là một điểm dẫn xuất tự
            # nhận mình tự do rồi được phép kéo.
            "origin": "derived" if ten in tao_ra else "free",
            "producer": p.get("producer"),
            "sources": p.get("sources", []),
        }
        if isinstance(gt, Vec3):
            objects.append({**chung, "type": "point3", "xyz": _xyz(gt)})
        elif isinstance(gt, Line3):
            # KHÔNG có `segment`: `Line3` vô hạn, và cắt nó thành một đoạn là
            # quyết định TRÌNH BÀY. `sources` đã chở tên hai điểm sinh ra nó,
            # nên renderer dựng đoạn được mà lớp này không tính gì.
            objects.append({**chung, "type": "line3",
                            "point": _xyz(gt.point),
                            "direction": _xyz(gt.direction)})
        elif isinstance(gt, Plane3):
            # Cùng lý do: không có `boundary`. `sources` chở ba điểm định nghĩa.
            objects.append({**chung, "type": "plane3",
                            "point": _xyz(gt.point),
                            "normal": _xyz(gt.normal)})
        elif isinstance(gt, Polyhedron):
            # `vertex_ids` THEO VỊ TRÍ, không sắp xếp — `faces` là bảng CHỈ SỐ
            # vào `vertices`, nên không có dãy tên cùng thứ tự thì mặt thứ `i`
            # không nói được nó gồm những ĐIỂM NÀO. `depends` không thay được:
            # `dependency_graph` sắp thứ tự chữ và làm mất đúng tính chất ấy.
            objects.append({**chung, "type": "solid",
                            "vertices": [_xyz(v) for v in gt.vertices],
                            "vertex_ids": list(p.get("sources", [])),
                            "faces": [list(f) for f in gt.faces]})
        elif isinstance(gt, Section):
            objects.append({**chung, "type": "section",
                            "polygon": [_xyz(v) for v in gt.polygon],
                            "closed": gt.is_closed,
                            "steps": [{"face_index": s.face_index,
                                       "a": _xyz(s.a), "b": _xyz(s.b)}
                                      for s in gt.steps]})
        elif la_doi_tuong_hinh_hoc(gt) and isinstance(gt, tuple):
            # `polygon3` sống dưới dạng tuple các đỉnh — không có lớp riêng.
            objects.append({**chung, "type": "polygon3",
                            "vertices": [_xyz(v) for v in gt],
                            "vertex_ids": list(p.get("sources", []))})
        elif la_dai_luong_do(gt, kieu.get(ten)):
            # ĐẠI LƯỢNG đo được (`measure`) — không vẽ được, nhưng phải HIỆN
            # LÊN: nó là câu trả lời của bài. Bỏ nó khỏi cảnh thì mô phỏng chạy
            # xong mà học sinh không thấy đáp số.
            objects.append({**chung, "type": "quantity", **_dai_luong(gt)})

    return {"objects": objects}


# ══ 3. TIMELINE — tận dụng trace, không dựng mới ═════════════════════════
def build_timeline(
    spec: SemanticProgramSpec, exec_result: Any
) -> list[dict[str, Any]]:
    """`SemanticTraceStep[]` → dãy bước mô phỏng.

    KHÔNG tạo timeline mới. `trace` đã mang `step_index`, `action`, `target`,
    `details`, `tier1_narration` — đủ cả năm thứ một bước cần.

    Bất biến #31 (`frame k ⇔ trace[k]`) áp thẳng: **một mục cho đúng một bước**,
    không gộp, không cắt. `construct_section` đã sinh một bước cho MỖI CẠNH kèm
    `face_index`, nên bài "dựng thiết diện" có timeline đúng như học sinh làm
    trên giấy mà không phải thêm gì.
    """
    prov = _provenance(spec)
    return [
        {
            "step_index": s.step_index,
            "action": s.action,
            "created": s.target,
            "depends_on": prov.get(s.target, {}).get("sources", []),
            "explanation": s.tier1_narration,
            "details": _json_an_toan(s.details),
        }
        for s in exec_result.trace
    ]


def _json_an_toan(x: Any) -> Any:
    """`Fraction` trong `details` → chuỗi phân số.

    ĐO ĐƯỢC khi viết test 5B: `assign` từ `measure` ghi `{"value": Fraction(2,3)}`
    vào `details`, và `json.dumps` VỠ — sau khi cả lượt đo đã chạy xong. Một
    artifact không ghi ra được là một lượt đo mất trắng.

    Chuyển sang chuỗi phân số chứ không sang float, cùng lý do với toạ độ: đó là
    biểu diễn **không mất mát**, đọc ngược lại được bằng `Fraction(s)`.
    """
    if isinstance(x, Radical):
        # CẤU TRÚC, không phải chuỗi: `details` là dữ liệu, và một `"3√2/5"`
        # trong đó không đọc ngược lại được.
        return to_json(x)
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _json_an_toan(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_an_toan(v) for v in x]
    return x


# ══ 4. SIMULATION STATE ══════════════════════════════════════════════════
def build_simulation_state(
    spec: SemanticProgramSpec, exec_result: Any, contract: Any = None
) -> dict[str, Any]:
    """Cảnh + đồ thị phụ thuộc + timeline. Đầu vào DUY NHẤT của renderer.

    `free_objects` là thứ Phase 5E sẽ cho kéo. Nó dẫn xuất từ `_producers`, nên
    một điểm dẫn xuất **không thể** tự nhận mình tự do — và luật *"kéo M thì bị
    từ chối vì M sinh ra từ A, B"* rơi ra từ dữ liệu, không phải từ một danh
    sách ai đó phải nhớ cập nhật.
    """
    scene = build_scene(spec, exec_result.final_memory)
    return {
        "scene": scene,
        "dependencies": dependency_graph(spec),
        "free_objects": sorted(
            o["id"] for o in scene["objects"] if o["origin"] == "free"
        ),
        "timeline": build_timeline(spec, exec_result),
        # ── DỮ LIỆU CHO TƯƠNG TÁC (đọc bởi `scene3d`) ────────────────────────
        #
        # Tính ở ĐÂY chứ không ở `scene3d` vì cả hai cần `spec`, mà `scene3d`
        # chỉ nhận `state` — và mở cửa cho nó nhận thêm `spec` là để tầng trình
        # bày nhìn thẳng vào chương trình, đúng hướng phụ thuộc không được đảo.
        #
        # `targets`: vật mà đề BẢO chứng minh/tính. Nhóm hiển thị `target` dẫn
        # xuất từ đây, nên học sinh phân biệt được *"cái phải chứng minh"* với
        # *"cái dựng ra để chứng minh"* — thứ nhìn hình vẽ phẳng không thấy.
        "targets": sorted(_muc_tieu(contract)),
        "provenance": _xuat_xu_hien_thi(spec),
        "khai": "Trạng thái TRUNG GIAN cho renderer. Mọi số là chuỗi phân số "
                "CHÍNH XÁC; hoá float là việc của renderer, ở bước cuối cùng.",
    }


def _muc_tieu(contract: Any) -> set[str]:
    """Tên vật mà NGHĨA VỤ CỦA ĐỀ nhắc tới.

    Đọc từ `RequestContract`, KHÔNG từ `SemanticProgramSpec` — spec không có
    trường `obligations`, và nếu có thì đó cũng là nghĩa vụ do chương trình tự
    khai. Nhóm `target` phải nói *"đề bảo chứng minh cái này"*, không phải
    *"chương trình tự nhận nó chứng minh cái này"*.

    `None` (đường gọi cũ, test dựng state bằng tay) ⇒ không có mục tiêu nào,
    và nhóm `target` đơn giản là vắng mặt. Không đoán.
    """
    ra: set[str] = set()
    for ob in (getattr(contract, "obligations", None) or ()):
        for t in (getattr(ob, "container", None), getattr(ob, "witness", None)):
            if isinstance(t, str) and t:
                ra.add(t)
        for v in (getattr(ob, "params", None) or {}).values():
            if isinstance(v, str) and v:
                ra.add(v)
    return ra


def _xuat_xu_hien_thi(spec: SemanticProgramSpec) -> dict[str, dict[str, Any]]:
    """`id → xuất xứ NGẮN` cho ô soi. Không chép prompt vào từng đối tượng.

    Ba mẩu, mỗi mẩu trả lời một câu học sinh thật sự hỏi:
    `fact_id` *"dữ kiện nào của đề"* · `assumption` *"chỗ này do ai chọn"* ·
    `instruction` *"câu lệnh nào dựng ra"*.
    """
    prov = _provenance(spec)
    ra: dict[str, dict[str, Any]] = {}
    for d in (spec.memory_declarations or ()):
        m = {"fact_id": getattr(d, "source_fact_id", None),
             "assumption": getattr(d, "model_assumption", None)}
        if any(m.values()):
            ra[d.name] = {k: v for k, v in m.items() if v}
    for ten, p in prov.items():
        ra.setdefault(ten, {})["instruction"] = p.get("producer")
    return ra
