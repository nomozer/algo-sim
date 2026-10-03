# -*- coding: utf-8 -*-
"""Scene3D — dữ liệu cảnh cho renderer. **0 API call, 0 phép hình học.**

    SimulationState → **Scene3D** → Renderer 3D (Phase 5D)

─── RANH GIỚI MẠNH NHẤT TRONG CẢ CHUỖI, VÀ NÓ CƯỠNG CHẾ ĐƯỢC ────────────────

Module này **không import gì từ tầng hình học**: không kernel, không validator,
không oracle, không cả `contract`. Nó nhận một `dict` và trả một `dict`.

Đó không phải khổ hạnh. Ở `simulation_state.py` tôi phải viết test quét `ast` để
cấm gọi `cross`/`dot`/`intersect_*`, vì module ấy **buộc** phải biết `Vec3` để
đọc bộ nhớ. Ở đây thì không cần biết gì cả — nên ranh giới trở thành *"danh sách
import phải rỗng"*, một mệnh đề máy kiểm được trong một dòng.

Hệ quả: không có cách nào để một phép hình học lẻn vào tầng này, kể cả khi ai đó
rất muốn.

─── VÌ SAO KHÔNG TÁI DÙNG TÊN `VisualTraceAdapter` ─────────────────────────

`visual_adapter.VisualTraceAdapter` **đã tồn tại** và làm việc khác hẳn: nó biến
trace thành `VisualFrame[]` cho **chín nguyên thuỷ 2D** (`array_strip`,
`stack_view`…) qua `visual_bindings`. Đặt trùng tên là mời người sau đọc nhầm
hai đường hoàn toàn khác nhau.

─── ĐIỀU TẦNG NÀY *KHÔNG* LÀM, và phải nói rõ ─────────────────────────────

`Scene3D` đi **vòng qua** đường `visual_bindings` → `envelope`. Nên nó **KHÔNG
mở khoá `B` (servable)**: `learner_surface` vẫn đòi mọi container biến động có
binding trong tập chín nguyên thuỷ đã đóng băng, và một `solid` vẫn không binding
nổi. Đó là một quyết định kiến trúc riêng, chưa được ra — xem báo cáo 5C.
"""
from __future__ import annotations

from typing import Any

#: Loại đối tượng ngữ nghĩa → **loại hình vẽ**. Chỉ nói *vẽ bằng hình gì*, không
#: nói kích thước/màu/độ trong — những thứ ấy renderer sở hữu.
#:
#: Bảng ĐÓNG. Không có `cylinder`, `sphere`, `curve`: chúng chưa có trong hợp
#: đồng ngữ nghĩa, và thêm ở đây là để tầng trình bày đẻ ra năng lực mà tầng
#: sinh không có — renderer sẽ vẽ được thứ mà không chương trình nào tạo ra nổi.
RENDER_HINT: dict[str, str] = {
    "point3": "point_marker",
    "line3": "line",
    "segment3": "segment",
    "plane3": "surface",
    "solid": "mesh",
    "polygon3": "polygon",
    "section": "polygon",
    # ── HÌNH CONG: MỘT loại vẽ cho BA hình ──────────────────────────────────
    #
    # Không `sphere`/`cylinder`/`cone` riêng. Renderer nhận `curved_kind` như
    # DỮ LIỆU rồi tra bảng trình bày của nó — cùng khuôn mà `curved_kind` dùng ở
    # backend. Ba loại vẽ nghĩa là ba nhánh ở phía TS, và chúng sẽ trôi khỏi ba
    # nhánh ở phía Python.
    "circle3": "circle",
    # ELIP — loại vẽ RIÊNG, không mượn `circle`. Một đường tròn vẽ được từ MỘT
    # bán kính; một elip cần hai bán trục và hai phương. Cho nó đi dưới lốt
    # `circle` thì renderer vẽ một vòng tròn cho một hình không tròn — đúng lớp
    # lỗi mà `vector3` đã mắc khi đi dưới lốt `point3`.
    "ellipse3": "ellipse",
    "curved_solid": "curved_solid",
    # ── VECTƠ: CÓ MẶT TRONG CẢNH, KHÔNG VẼ LÊN KHUNG ────────────────────────
    #
    # `non_visual` là một **quyết định kiến trúc được nói ra**, không phải một ô
    # bỏ trống. Trước bản này `vector3` không có ô nào ở đây, nên nó đi qua cảnh
    # dưới lốt `point3` (hai kiểu cùng là `Vec3` ở runtime) và hiện thành một
    # chấm ở toạ độ bằng **thành phần** của vectơ — một vật không tồn tại trong
    # bài. Frontend phải đọc `producer` để đoán ngược và lọc nó ra, tức tầng
    # trình bày suy lại ngữ nghĩa.
    #
    # Vì sao KHÔNG vẽ thành mũi tên: một vectơ tự do **không có vị trí** trong
    # không gian. Chọn một điểm đặt cho nó — gốc toạ độ, hay điểm đầu suy từ
    # `depends` — là renderer tự quyết một dữ kiện hình học. Thà không vẽ.
    #
    # Vật vẫn ở trong cảnh: cây thành phần và ô soi đọc được nó, `angle_cos` đo
    # nó, và ô soi hiện `xyz` là các THÀNH PHẦN. Chỉ khung 3D không vẽ.
    "vector3": "non_visual",
    # Đại lượng đo được KHÔNG vẽ được, nhưng phải HIỆN LÊN: nó là câu trả lời
    # của bài. Bỏ nó khỏi cảnh thì mô phỏng chạy xong mà học sinh không thấy
    # đáp số — đúng điều `learner_surface` sinh ra để chặn.
    "quantity": "readout",
}

#: Trường hình học được chở nguyên si sang, theo từng loại.
#:
#: `line3`/`plane3` cố ý **không có** trường biên. Chúng vô hạn, và cắt chúng
#: thành đoạn/hình chữ nhật là quyết định TRÌNH BÀY — renderer làm, dựa trên
#: `depends` (tên các điểm sinh ra) mà toạ độ đã có sẵn trong cùng cảnh.
_TRUONG: dict[str, tuple[str, ...]] = {
    "point3": ("xyz",),
    # Cùng ba số như `point3`, nhưng chúng là **THÀNH PHẦN** của vectơ chứ không
    # phải toạ độ một điểm. Khác biệt ấy nay nằm ở `type`, nơi nó thuộc về —
    # không còn ở việc đoán `producer`.
    "vector3": ("xyz",),
    "line3": ("point", "direction"),
    "segment3": ("point_a", "point_b", "endpoints", "endpoint_ids"),
    "plane3": ("point", "normal"),
    # `shape_class` + `formation_requirements`: lớp hình và vai trò bắt buộc, do
    # PRODUCER (`simulation_state` ← `formation`) gắn — tầng này chỉ chở (W14).
    "solid": ("vertices", "vertex_ids", "faces", "shape_class", "formation_requirements"),
    "polygon3": ("vertices", "vertex_ids"),
    "section": ("polygon", "closed", "steps", "vertex_sources", "shape_class",
                "formation_requirements"),
    # ⚠️ **KHÔNG `vertices`, KHÔNG `faces`** — và sự vắng mặt ấy LÀ cơ chế giữ
    # lưới ra khỏi ngữ nghĩa, không phải một lời dặn. Renderer chia lưới để vẽ,
    # nhưng không có ô nào để một đỉnh nội suy đi ngược lên checker hay phép đo.
    "circle3": ("center", "normal", "radius_sq"),
    # Hai bán trục dưới dạng BÌNH PHƯƠNG + hai phương trục CHƯA chuẩn hoá — cả
    # bốn ở ℚ. Renderer lấy căn và chuẩn hoá ở biên hiển thị, không sớm hơn.
    "ellipse3": ("center", "normal", "major_dir", "minor_dir",
                 "semi_major_sq", "semi_minor_sq"),
    "curved_solid": ("curved_kind", "anchor", "apex_or_top", "rim_point",
                     "radius_sq", "height_sq"),
    # `exact` đi CÙNG `value`, không thay nó: `value` là chuỗi cho người đọc,
    # `exact` là cấu trúc cho máy. Bỏ `exact` khỏi bảng này thì nó dừng lại ở
    # `SimulationState` và **không bao giờ tới renderer** — frontend buộc phải
    # đọc ngược chuỗi `"3√2/5"`, đúng thứ cấu trúc sinh ra để khỏi phải làm.
    "quantity": ("value", "exact"),
}


#: Phép biến đổi TRÌNH BÀY mặc định — đồng nhất thức.
#:
#: **SỐ thường, không phải chuỗi phân số**, và khác biệt ấy là có chủ đích.
#:
#: Bản đầu dùng chuỗi phân số "cho đồng bộ với toạ độ". Demo trong Chrome thật
#: cho thấy cái giá: phía frontend sinh `"0.244949"` cho khoảng dịch bung
#: hình, `toNumber` ném vì nó không phải phân số, và cả khung 3D sập.
#:
#: Hai không gian này khác nhau về BẢN CHẤT. Toạ độ hình học phải chính xác
#: tuyệt đối — đó là thứ phân biệt hệ này với một bộ vẽ hình. Khoảng dịch
#: trình bày thì không: làm tròn nó không sai một mệnh đề toán nào, vì nó chưa
#: bao giờ là một mệnh đề toán. Dùng chung một cách viết cho hai thứ ấy là mời
#: chúng đi lẫn vào nhau.
BIEN_DOI_DONG_NHAT: dict[str, Any] = {"translate": [0, 0, 0], "scale": 1}


def _canonical_edge_id(
    solid_id: str, vertex_ids: list[str], ia: int, ib: int
) -> str:
    """Machine edge id ordered by the solid's stable vertex ordinal."""
    a, b = (ia, ib) if ia <= ib else (ib, ia)
    return f"{solid_id}::edge:{vertex_ids[a]}-{vertex_ids[b]}"


def _coordinate_hash(coordinate: list[str]) -> str:
    """Stable hash of exact rational spellings, used only by legacy payloads."""
    value = 1469598103934665603
    for byte in "|".join(coordinate).encode("utf-8"):
        value ^= byte
        value = (value * 1099511628211) & ((1 << 64) - 1)
    return f"{value:016x}"


def _attach_topology(objects: list[dict[str, Any]]) -> None:
    """Attach renderer topology without performing geometric inference.

    Faces already contain the authoritative cyclic vertex indices.  This pass
    only normalises that topology into named edge and surface records.
    """
    solids: dict[str, dict[str, Any]] = {}
    edge_ids_by_solid: dict[str, dict[frozenset[str], str]] = {}
    for obj in objects:
        if obj.get("type") != "solid":
            continue
        vertex_ids = obj.get("vertex_ids") or []
        vertices = obj.get("vertices") or []
        faces = obj.get("faces") or []
        if len(vertex_ids) != len(vertices):
            continue
        ownership: dict[tuple[int, int], dict[str, Any]] = {}
        surfaces: list[dict[str, Any]] = []
        for face_index, face in enumerate(faces):
            if len(face) < 3 or any(
                not isinstance(index, int) or index < 0 or index >= len(vertex_ids)
                for index in face
            ):
                continue
            boundary: list[str] = []
            surface_id = f"{obj['id']}::face:{face_index}"
            for index, ia in enumerate(face):
                ib = face[(index + 1) % len(face)]
                key = (ia, ib) if ia <= ib else (ib, ia)
                edge_id = _canonical_edge_id(obj["id"], vertex_ids, ia, ib)
                boundary.append(edge_id)
                edge = ownership.setdefault(key, {
                    "edge_id": edge_id,
                    "endpoint_ids": [vertex_ids[key[0]], vertex_ids[key[1]]],
                    "adjacent_surface_ids": [],
                })
                edge["adjacent_surface_ids"].append(surface_id)
            surfaces.append({
                "surface_id": surface_id,
                "vertex_indices": list(face),
                "boundary_edge_ids": boundary,
                "surface_role": "SOLID_FACE",
                "occludes_edges": True,
            })
        obj["edge_ownership"] = list(ownership.values())
        obj["surfaces"] = surfaces
        solids[obj["id"]] = obj
        edge_ids_by_solid[obj["id"]] = {
            frozenset(edge["endpoint_ids"]): edge["edge_id"]
            for edge in ownership.values()
        }

    for obj in objects:
        kind = obj.get("type")
        if kind == "solid":
            continue
        obj["occludes_edges"] = False
        if kind == "plane3":
            obj["surface_role"] = "CUTTING_PLANE"
        elif kind == "section":
            obj["surface_role"] = "SECTION_REGION"
            polygon = obj.get("polygon") or []
            sources = obj.get("vertex_sources") or []
            parent = solids.get(obj.get("parent"))
            vertex_ids = (parent or {}).get("vertex_ids") or []
            edge_map = edge_ids_by_solid.get(obj.get("parent"), {})
            endpoints: list[dict[str, Any]] = []
            diagnostics: list[str] = []
            for ordinal, coordinate in enumerate(polygon):
                source = sources[ordinal] if ordinal < len(sources) else {}
                entity_id = None
                if source.get("kind") == "SOLID_VERTEX":
                    index = source.get("solid_vertex_index")
                    if isinstance(index, int) and 0 <= index < len(vertex_ids):
                        entity_id = vertex_ids[index]
                elif source.get("kind") == "SOLID_EDGE_INTERSECTION":
                    indices = source.get("solid_edge_vertex_indices") or []
                    if len(indices) == 2 and all(
                        isinstance(index, int) and 0 <= index < len(vertex_ids)
                        for index in indices
                    ):
                        solid_edge_id = edge_map.get(frozenset((
                            vertex_ids[indices[0]], vertex_ids[indices[1]],
                        )))
                        if solid_edge_id:
                            entity_id = f"section:{obj['id']}:point:on:{solid_edge_id}"
                fallback = entity_id is None
                coordinate_hash = _coordinate_hash(coordinate)
                if fallback:
                    entity_id = f"section:{obj['id']}:anonymous:{coordinate_hash}"
                    diagnostics.append("ANONYMOUS_SECTION_ENDPOINT_ID_FALLBACK")
                endpoints.append({
                    "entity_id": entity_id,
                    "section_vertex_ordinal": ordinal,
                    "provenance_kind": source.get("kind") or "LEGACY_COORDINATE",
                    "coordinate_hash": coordinate_hash,
                    "anonymous_coordinate_fallback": fallback,
                })
            obj["endpoint_entities"] = endpoints
            obj["identity_diagnostics"] = sorted(set(diagnostics))
            boundary: list[str] = []
            edge_hashes: dict[str, str] = {}
            for ordinal in range(len(endpoints)):
                other = (ordinal + 1) % len(endpoints)
                first, second = (ordinal, other) if ordinal <= other else (other, ordinal)
                edge_id = (
                    f"section:{obj['id']}:edge:"
                    f"{endpoints[first]['entity_id']}:{endpoints[second]['entity_id']}"
                )
                coordinate_hash = ":".join(sorted((
                    endpoints[first]["coordinate_hash"],
                    endpoints[second]["coordinate_hash"],
                )))
                if edge_id in edge_hashes and edge_hashes[edge_id] != coordinate_hash:
                    raise ValueError("SECTION_EDGE_IDENTITY_DRIFT")
                edge_hashes[edge_id] = coordinate_hash
                boundary.append(edge_id)
            obj["boundary_edge_ids"] = boundary
            obj["section_edge_coordinate_hashes"] = edge_hashes
        elif kind == "polygon3":
            parent = obj.get("parent")
            vertex_ids = obj.get("vertex_ids") or []
            edge_map = edge_ids_by_solid.get(parent, {})
            boundary = []
            if len(vertex_ids) >= 3:
                boundary = [
                    edge_map.get(frozenset((vertex_ids[i], vertex_ids[(i + 1) % len(vertex_ids)])))
                    for i in range(len(vertex_ids))
                ]
            if boundary and all(boundary):
                obj["surface_role"] = "BASE_REGION"
                obj["boundary_edge_ids"] = boundary
            else:
                obj["surface_role"] = "AUXILIARY_SURFACE"
        elif kind == "segment3":
            # Đoạn trùng cạnh khối (theo TÊN đầu mút): cạnh chuẩn của khối là
            # owner nét vẽ, đoạn chỉ trỏ về nó — một cạnh, một nét.
            key = frozenset(obj.get("endpoint_ids") or ())
            owned = [edges[key] for edges in edge_ids_by_solid.values() if key in edges]
            if len(key) == 2 and owned:
                obj["boundary_edge_ids"] = owned


def _cha(objs: list[dict[str, Any]]) -> dict[str, str]:
    """`id → id của vật CHỨA nó về mặt cấu trúc`. Nhiều cha ⇒ KHÔNG có cha.

    ─── `parent` KHÔNG PHẢI `depends` ──────────────────────────────────────

    `depends` là *"tôi được dựng TỪ cái gì"* — một đồ thị nhiều-nhiều, và nó
    đã có sẵn. `parent` là *"tôi NẰM TRONG cái gì"* — quan hệ chứa đựng, tối
    đa một, và nó chỉ tồn tại để cây phân rã (`isolate`, `explode`) có chỗ
    treo. Hai thứ khác nhau: `M = midpoint(A,B)` phụ thuộc A, B nhưng KHÔNG
    nằm trong A hay B.

    Suy theo TÊN, không theo toạ độ: khối khai `vertices` bằng tên điểm, nên
    `sources` của nó chính là các đỉnh. So toạ độ thì một điểm trùng chỗ với
    đỉnh khối sẽ bị nhận nhầm là đỉnh — mà trùng chỗ là chuyện thường trong
    hình học (chân đường cao, trung điểm).

    Hai khối cùng nhận một đỉnh ⇒ trả **không cha**, và điểm ấy về nhóm hiển
    thị thay vì bị gán bừa vào một trong hai.
    """
    loai = {o["id"]: o["type"] for o in objs}
    ung: dict[str, list[str]] = {}
    for o in objs:
        if o["type"] != "solid":
            continue
        dinh = {s for s in o.get("depends", []) if loai.get(s) == "point3"}
        for ten in dinh:
            ung.setdefault(ten, []).append(o["id"])
        # Thiết diện / đa giác dựng TỪ khối này, hoặc từ chính các đỉnh của nó.
        for k in objs:
            if k["type"] not in ("section", "polygon3"):
                continue
            pt = set(k.get("depends", []))
            if o["id"] in pt or (pt and pt <= dinh):
                ung.setdefault(k["id"], []).append(o["id"])
    return {k: v[0] for k, v in ung.items() if len(set(v)) == 1}


def _nhom(o: dict[str, Any], muc_tieu: set[str]) -> list[str]:
    """Nhóm hiển thị, DẪN XUẤT từ vai trò — không hard-code theo bài.

    Chỉ phát những nhóm **suy được từ dữ liệu đang có**. Ví dụ của chỉ thị có
    `base` và `lateral_faces`; hệ hiện **không** có thực thể mặt riêng (một
    khối là MỘT đối tượng mang `faces` là chỉ số), nên hai nhóm ấy không suy
    được và **không được bịa ra** — một nhóm rỗng tên đẹp còn tệ hơn không có
    nhóm, vì UI sẽ dựng nút bấm cho nó.
    """
    ra = ["given" if o["origin"] == "free" else "construction"]
    theo_loai = {"solid": "solid", "section": "section",
                 "polygon3": "face", "quantity": "measurement"}
    if (g := theo_loai.get(o["type"])):
        ra.append(g)
    if o["id"] in muc_tieu:
        ra.append("target")
    # ─── VẬT DO HỆ DỰNG, KHÔNG DO ĐỀ HAY MÔ HÌNH ĐẶT TÊN ───────────────────
    #
    # `hoisting` sinh các ràng buộc trung gian khi mô hình lồng một phép dựng
    # vào một ô TÊN. Chúng là một phần THẬT của chuỗi dựng — `depends` và
    # `producer` đi qua chúng, và xoá chúng khỏi cảnh là nói dối về xuất xứ.
    #
    # Nhưng chúng cũng KHÔNG phải thứ học sinh cần đọc: tên `_tam_1` là định
    # danh kỹ thuật, và định danh kỹ thuật lọt lên bề mặt học sinh là một bug
    # đã ship hai lần ở kho này. Nên: giữ trong đồ thị, ĐÁNH DẤU cho tầng trình
    # bày gộp lại. Đồ thị nội bộ thấy; màn hình học sinh không nhất thiết.
    # Cờ ĐỌC từ state, không tự suy từ tên: module này không được biết quy ước
    # đặt tên của bất kỳ tầng nào (`test_scene3d_KHONG_nhap_gi_tu_tang_hinh_hoc`).
    if o.get("synthetic"):
        ra.append("internal")
    return ra


def build_scene3d(state: dict[str, Any]) -> dict[str, Any]:
    """`SimulationState` → `Scene3D`.

    Giữ nguyên **ba** thứ, và mỗi thứ mất đi là mất một năng lực:

      · **toạ độ chính xác** — chuỗi phân số, không float. Mất là mất khả năng
        so bằng đúng, tức mất thứ phân biệt hệ này với một bộ vẽ hình.
      · **`producer`** — phép dựng sinh ra đối tượng. Mất là cảnh chỉ còn nói
        *hình trông thế nào*, thôi nói *hình được tạo ra thế nào* — tức mất đúng
        đóng góp của đề tài.
      · **`depends`** — mất là không mô phỏng thay đổi được, và Phase 5E không
        biết kéo cái gì thì hợp lệ.
    """
    phu_thuoc = state.get("dependencies", {})
    typed_dependencies = state.get("dependency_edges", {})
    muc_tieu = set(state.get("targets", []))
    xuat_xu = state.get("provenance", {})
    tho = [o for o in state.get("scene", {}).get("objects", [])
           if o["type"] in RENDER_HINT]
    # Tính cha trên TOÀN BỘ danh sách trước khi lọc từng cái: một khối bị bỏ
    # qua ở vòng dưới vẫn phải cho các đỉnh của nó biết chúng nằm trong đâu.
    cha = _cha([{**o, "depends": phu_thuoc.get(o["id"], o.get("sources", []))}
                for o in tho])
    ra: list[dict[str, Any]] = []

    for o in tho:
        loai = o["type"]
        if loai not in RENDER_HINT:
            # Loại lạ ⇒ BỎ QUA có ghi, không đoán một hình để vẽ. Vẽ bừa là
            # dựng một đối tượng mà chương trình không hề tạo ra.
            continue
        v: dict[str, Any] = {
            "id": o["id"],
            # ── HAI VAI, HAI TRƯỜNG ────────────────────────────────────────
            #
            # `label` là CÂU đọc được (*"Khoảng cách giữa H và (SBC)"*),
            # `notation` là KÝ HIỆU ngắn in cạnh vật (*"d(H, (SBC))"*, `M`,
            # `A′`). Cả hai do `display_names` quyết ở tầng ngữ nghĩa; tầng này
            # chỉ chở. `notation` có thể `None` — khung không in gì cho vật ấy.
            #
            # Trước bản này chỉ có `label`, và nó rơi về `id` khi mô hình không
            # đặt tên. Hệ quả: học sinh đọc `khoang_cach_hs`, còn renderer phải
            # tự cắt gọt `id` để có ký hiệu.
            "label": o["label"],
            "notation": o.get("notation"),
            # `reference` — cách gọi vật này khi nó bị nhắc TRONG câu của vật
            # khác, và trong danh sách phụ thuộc. Luôn có, không bao giờ là
            # một câu dài.
            # `role` — *"vật này là gì"*, một dòng dưới tên trong ô soi.
            "reference": o.get("reference"),
            "role": o.get("role"),
            "display_label": o["label"],
            "type": loai,
            "render": RENDER_HINT[loai],
            "display_role": (
                "measurement" if RENDER_HINT[loai] == "readout"
                else "non_visual" if RENDER_HINT[loai] == "non_visual"
                else "visual_owner"
            ),
            # PROVENANCE — không được phẳng hoá. `M = [1,2,3]` mất đúng thứ làm
            # nó mô phỏng được.
            "origin": o["origin"],
            "producer": o.get("producer"),
            "depends": phu_thuoc.get(o["id"], o.get("sources", [])),
            "dependency_edges": list(typed_dependencies.get(o["id"], [])),
            # ── BỐN TRƯỜNG TƯƠNG TÁC ────────────────────────────────────────
            #
            # Cả bốn đều là DỮ LIỆU TRÌNH BÀY. Không cái nào đi vào phép tính:
            # kernel, checker và mọi cổng đọc `GeometryState`, không đọc cảnh.
            #
            # `parent` — chứa đựng cấu trúc, tối đa một. `None` là câu trả lời
            #   hợp lệ và thường gặp; UI treo vật ấy vào nhóm hiển thị.
            # `display_group` — NHIỀU nhóm, dẫn xuất từ vai trò.
            # `visual_transform` — đồng nhất thức cho tới khi người dùng bung
            #   hình. Server KHÔNG bao giờ phát một giá trị khác: bung hình là
            #   thao tác của người xem, và trạng thái ấy sống ở `InteractionState`.
            # `source` — đủ để trả lời *"vật này ở đâu ra"* khi soi, không hơn.
            "parent": cha.get(o["id"]),
            "display_group": _nhom(o, muc_tieu),
            "visual_transform": dict(BIEN_DOI_DONG_NHAT),
            "source": xuat_xu.get(o["id"]) or {},
            # Vai trò dựng hình của VẬT (W14) — gắn ở producer, chở nguyên.
            "formation_roles": list(o.get("formation_roles") or []),
        }
        for f in _TRUONG[loai]:
            if f in o:
                v[f] = o[f]
        ra.append(v)

    _attach_topology(ra)
    _attach_formulas(ra)
    _danh_dau_bi_danh(ra)
    _gan_so_do(ra, state.get("annotations") or {})
    events = build_scene_events(state)
    _ke_lai(events, ra)
    formation = _build_formation(ra, events, state.get("free_objects", []))

    return {
        "objects": ra,
        "events": events,
        "formation": formation,
        "free_objects": list(state.get("free_objects", [])),
        # W17 §15.4: đại lượng không gắn được chủ thể (`ANNOTATION_UNBOUND …`) — cho người phát
        # triển; học sinh vẫn đọc giá trị ở bảng chi tiết.
        "diagnostics": list(state.get("annotation_diagnostics") or []),
        "khai": "Dữ liệu CẢNH cho renderer. Mọi số là chuỗi phân số CHÍNH XÁC; "
                "hoá float là việc của renderer, ở bước cuối trước GPU. Mặt "
                "phẳng và đường thẳng KHÔNG có biên — renderer tự quyết kích "
                "thước dựa trên `depends`.",
    }


#: Hành động của một bước, dẫn từ `action` của trace.
#:
#: `MEASURE` tách khỏi `CREATE` vì hai thứ khác nhau về sư phạm: dựng ra một đối
#: tượng mới, và đọc một số từ đối tượng đã có. Animation của chúng cũng khác.
_HANH_DONG: dict[str, str] = {
    "init": "INIT",
    "construct_point": "CREATE",
    "construct_line": "CREATE",
    "construct_segment": "CREATE",
    "construct_plane": "CREATE",
    "construct_polygon": "CREATE",
    "construct_solid": "CREATE",
    "section_edge": "EXTEND",
    "assign": "MEASURE",
}


def build_scene_events(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Timeline → dãy sự kiện cảnh, để Phase 5D phát từng bước.

    MỘT sự kiện cho ĐÚNG một bước — bất biến #31 (`frame k ⇔ trace[k]`) áp
    thẳng, không gộp, không cắt.

    `section_edge` thành `EXTEND` chứ không `CREATE`: kernel sinh **một bước cho
    mỗi cạnh** của thiết diện, và đó là dãy thao tác học sinh làm trên giấy —
    nối dần từng cạnh, không phải hiện ra cả đa giác một lúc.
    """
    scene_objects = state.get("scene", {}).get("objects", [])
    co_that = {o["id"] for o in scene_objects}
    labels = {o["id"]: o.get("label") or o.get("reference")
              for o in scene_objects}
    events = []
    for b in state.get("timeline", []):
        details = b.get("details", {})
        sub_objs = [o for o in (details.get("objects") or []) if o in co_that]
        if b.get("action") == "init":
            main_obj = None
        elif b.get("created") in co_that:
            main_obj = b["created"]
        else:
            main_obj = b.get("created") or (sub_objs[0] if sub_objs else None)
        # W17: đích của câu lệnh NHÓM (`canh_ben`) không phải vật của cảnh — tên hành động là nhãn
        # của CHÍNH câu lệnh ("Các cạnh bên AD, BE, CF", do bước bổ sung dựng hình đặt), không phải
        # câu chung; nhãn mang `_` là tên máy và không bao giờ lên bề mặt học sinh.
        nhan_lenh = details.get("label")
        nhan_lenh = nhan_lenh if isinstance(nhan_lenh, str) and nhan_lenh.strip() and "_" not in nhan_lenh else None
        evt: dict[str, Any] = {
            "step_index": b["step_index"],
            "action": _HANH_DONG.get(b["action"], "STEP"),
            "object": main_obj,
            "depends": list(b.get("depends_on", [])),
            "explanation": b.get("explanation", ""),
            "display_label": labels.get(main_obj) or nhan_lenh or "Bước dựng hình",
            "semantic_kind": b.get("semantic_kind") or "LEGACY_UNTYPED_EVENT",
            "details": dict(details),
        }
        if not b.get("semantic_kind"):
            evt["diagnostics"] = ["LEGACY_UNTYPED_EVENT"]
        evt["learner_text"] = _learner_text(
            b.get("learner_text") or b.get("explanation") or "",
            co_that,
            evt["action"],
            evt["display_label"],
        )
        if sub_objs:
            evt["objects"] = sub_objs
        events.append(evt)
    return events


def _contains_identifier(text: str, identifier: str) -> bool:
    """So khớp token máy với biên từ, không cần regex hay đọc ngược id."""
    if not identifier:
        return False
    start = 0
    while True:
        index = text.find(identifier, start)
        if index < 0:
            return False
        before = text[index - 1] if index > 0 else ""
        end = index + len(identifier)
        after = text[end] if end < len(text) else ""
        if not (before.isalnum() or before == "_") and not (
            after.isalnum() or after == "_"
        ):
            return True
        start = index + 1


def _learner_text(
    candidate: str,
    internal_ids: set[str],
    action: str,
    display_label: str,
) -> str:
    """Chỉ cho learner text qua khi nó không lộ id/snake_case động."""
    unsafe = any(
        "_" in identifier and _contains_identifier(candidate, identifier)
        for identifier in internal_ids
    )
    # Chặn cả token snake_case mới chưa có trong ``objects`` (enum hoặc id bị
    # lọc khỏi cảnh), thay vì duy trì một denylist theo fixture.
    words = candidate.replace(".", " ").replace(",", " ").split()
    unsafe = unsafe or any("_" in word for word in words)
    if candidate.strip() and not unsafe:
        return candidate.strip()
    if action == "INIT":
        return "Khởi tạo các dữ kiện và điểm đã cho."
    if action == "CREATE":
        return f"Dựng {display_label}."
    if action == "EXTEND":
        return f"Tiếp tục dựng {display_label}."
    if action == "MEASURE":
        return f"Tính {display_label}."
    return "Tiếp tục lời giải hình học."


def _formula_symbol(obj: dict[str, Any]) -> str:
    """Ký hiệu learner-facing; tuyệt đối không lùi về internal id."""
    return str(
        obj.get("notation")
        or obj.get("reference")
        or obj.get("display_label")
        or obj.get("label")
        or "đại lượng"
    )


def _attach_formulas(objects: list[dict[str, Any]]) -> None:
    """Gắn formula có references tới entity thật; thiếu nguồn thì ẩn.

    `references` = ĐÚNG các vật chữ công thức nhắc tới, theo thứ tự trong chữ
    (w11). Bản w10 gắn mọi nguồn số vào cả `S(ABCD) = 12`, nên frontend thấy
    không nhất quán và ẩn thẻ; nguồn số vẫn nằm nguyên ở `dependency_edges`.
    """
    by_id = {obj["id"]: obj for obj in objects}

    def ref(o: dict[str, Any]) -> dict[str, Any]:
        return {"entity_id": o["id"], "display_label": _formula_symbol(o),
                "relation": "numerical"}

    for obj in objects:
        if obj.get("type") != "quantity":
            continue
        numerical = [
            edge["source_id"]
            for edge in obj.get("dependency_edges", [])
            if edge.get("relation") == "numerical"
            and edge.get("source_id") in by_id
        ]
        producer = obj.get("producer")
        value = obj.get("value")
        if producer == "measure.volume":
            area = next(
                (by_id[source_id] for source_id in numerical
                 if by_id[source_id].get("producer") == "measure.area"),
                None,
            )
            # ĐÚNG MỘT ứng viên chiều cao. Hai độ dài cùng qua được luật tên
            # (`SA` và cạnh bên `SB`) thì chọn cái đầu là in một công thức có
            # thể sai — không in còn hơn in sai.
            cao = [by_id[source_id] for source_id in numerical
                   if source_id != (area or {}).get("id")]
            height = cao[0] if len(cao) == 1 else None
            solid = next(
                (by_id[edge["source_id"]]
                 for edge in obj.get("dependency_edges", [])
                 if edge.get("relation") == "structural"
                 and edge.get("source_id") in by_id
                 and by_id[edge["source_id"]].get("type") == "solid"),
                None,
            )
            if area is None or height is None or solid is None:
                continue
            is_pyramid = len(solid.get("faces") or []) == len(
                solid.get("vertices") or []
            )
            prefix = "1/3 × " if is_pyramid else ""
            text = (
                f"V = {prefix}{_formula_symbol(area)} × "
                f"{_formula_symbol(height)}"
            )
            if value is not None:
                text += f" = {value}"
            obj["formula"] = {"text": text, "references": [ref(area), ref(height)]}
        elif value is not None:
            obj["formula"] = {"text": f"{_formula_symbol(obj)} = {value}", "references": []}


_TEN_DA_GIAC = {3: "tam giác", 4: "tứ giác", 5: "ngũ giác", 6: "lục giác"}


def _giua_cau(t: str) -> str:
    """Danh từ chung mở đầu nhãn viết thường giữa câu; ký hiệu giữ nguyên.

    *"Đáy ABCD"* ⇒ *"đáy ABCD"*; *"S.ABCD"*, *"(α)"*, *"AB"* không đổi.
    """
    return t[:1].lower() + t[1:] if t[:1].isupper() and t[1:2].islower() else t


def _sua_cau(t: str) -> str:
    """Hai lỗi chép nhãn vào câu kể: hoa giữa câu, và danh từ lặp đôi.

    Thuần chuỗi — module này không nhập gì ngoài `typing` (test khoá).
    """
    for dong_tu in ("Dựng ", "Tính "):
        if t.startswith(dong_tu):
            t = dong_tu + _giua_cau(t[len(dong_tu):])
    for danh_tu in ("mặt phẳng", "đường thẳng", "đoạn thẳng", "điểm"):
        for lap in (f"{danh_tu} {danh_tu.capitalize()}", f"{danh_tu} {danh_tu}"):
            t = t.replace(lap, danh_tu)
    return t


def _danh_dau_bi_danh(objects: list[dict[str, Any]]) -> None:
    """Đại lượng chép NGUYÊN một đại lượng khác mang `alias_of`.

    Bí danh là ĐÁP SỐ của đề (nhóm `target`) thì không hiện thành dòng số đo
    thứ hai (`V(S.ABCD) = 24` và `v = 24`) — vật vẫn nằm trong cảnh, vì cổng
    nghĩa vụ trực quan tra nó theo tên. Bí danh chỉ là một phép suy (cạnh lập
    phương bằng nhau) thì vẫn hiện: đó là một dữ kiện học sinh cần đọc.
    """
    by_id = {o["id"]: o for o in objects}
    for o in objects:
        nguon = o.get("depends") or []
        if (o["type"] != "quantity" or o.get("producer") != "assign" or len(nguon) != 1
                or by_id.get(nguon[0], {}).get("type") != "quantity"):
            continue
        o["alias_of"] = nguon[0]
        if "target" in (o.get("display_group") or []):
            o.update(render="non_visual", display_role="non_visual", role="Kết quả cuối")


def _gan_so_do(objects: list[dict[str, Any]], gan: dict[str, dict[str, Any]]) -> None:
    """W17 §15.4: chở gắn kết của tầng ngữ nghĩa lên vật `quantity` và quyết `category` — `result`
    khi đại lượng là đích của đề hoặc được một đích `alias_of`, còn lại `measurement`. Bí danh
    dùng CHUNG danh tính với nguồn: không có nhãn thứ hai."""
    dich = {o["id"] for o in objects if "target" in (o.get("display_group") or [])}
    ket_qua = dich | {o["alias_of"] for o in objects if o.get("alias_of") and o["id"] in dich}
    for o in objects:
        g = gan.get(o["id"])
        if g is not None and o["type"] == "quantity" and not o.get("alias_of"):
            o["annotation"] = {**g, "category": "result" if o["id"] in ket_qua else "measurement"}


def _ten_diem_khoi(solid: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> list[str]:
    return [by_id.get(v, {}).get("notation") or by_id.get(v, {}).get("label") or "?"
            for v in solid.get("vertex_ids") or []]


def _cau_canh_thiet_dien(e: dict[str, Any], sec: dict[str, Any],
                         by_id: dict[str, dict[str, Any]]) -> str:
    """Một cạnh thiết diện kể bằng ĐỈNH/CẠNH của khối, không bằng toạ độ."""
    k = (e.get("details") or {}).get("canh")
    buoc = sec.get("steps") or []
    poly = sec.get("polygon") or []
    nguon = sec.get("vertex_sources") or []
    solid = next((by_id[d] for d in sec.get("depends") or []
                  if by_id.get(d, {}).get("type") == "solid"), None)
    if not isinstance(k, int) or k >= len(buoc) or solid is None or len(nguon) != len(poly):
        return f"Nối thêm một cạnh của {_giua_cau(sec['label'])}."
    ten = _ten_diem_khoi(solid, by_id)

    def diem(xyz: Any) -> str:
        i = next((j for j, p in enumerate(poly) if list(p) == list(xyz)), None)
        s = nguon[i] if i is not None else {}
        if s.get("kind") == "SOLID_VERTEX" and s.get("solid_vertex_index") is not None:
            return f"đỉnh {ten[s['solid_vertex_index']]}"
        canh = s.get("solid_edge_vertex_indices") or []
        return f"giao điểm thuộc cạnh {''.join(ten[j] for j in canh)}" if len(canh) == 2 else "một giao điểm"

    mat = buoc[k].get("face_index")
    mat_ten = ("".join(ten[j] for j in solid["faces"][mat])
               if isinstance(mat, int) and mat < len(solid.get("faces") or []) else None)
    noi = f"nối {diem(buoc[k]['a'])} với {diem(buoc[k]['b'])}."
    return f"Trên mặt {mat_ten}, {noi}" if mat_ten else noi[:1].upper() + noi[1:]


def _cau_thiet_dien(sec: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> str:
    n = len(sec.get("polygon") or [])
    hinh = _TEN_DA_GIAC.get(n, f"đa giác {n} đỉnh")
    loai = {by_id.get(d, {}).get("type"): by_id.get(d) for d in sec.get("depends") or []}
    solid, plane = loai.get("solid"), loai.get("plane3")
    if solid and plane:
        return (f"Thiết diện khép lại thành {hinh}: "
                f"{plane.get('reference') or _giua_cau(plane['label'])} cắt {_giua_cau(solid['label'])}.")
    return f"Thiết diện khép lại thành {hinh}."


def _cau_do(o: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> str:
    """Bước tính một đại lượng: công thức một lần, không "Ghi nhận …"."""
    gia_tri = o.get("value")
    goc = by_id.get(o.get("alias_of") or "")
    if goc is not None:
        return (f"Suy ra {o.get('notation') or _giua_cau(o['label'])} = "
                f"{goc.get('notation') or _giua_cau(goc['label'])} = {gia_tri}.")
    cong_thuc = (o.get("formula") or {}).get("text")
    if o.get("notation") and cong_thuc:
        return f"Tính {_giua_cau(o['label'])}: {cong_thuc}."
    return f"{o['label']} bằng {gia_tri}."


def _ke_lai(events: list[dict[str, Any]], objects: list[dict[str, Any]]) -> None:
    """Kiểu ngữ nghĩa + lời kể của từng bước, dựng từ cảnh CÓ CẤU TRÚC.

    Một bước ⇔ một sự kiện (bất biến #31) — chỉ đổi lời và kiểu, không thêm
    bớt bước. KẾT LUẬN (`FINAL_RESULT`) là bước ghi đáp số của đề: bí danh-đáp
    số nếu chương trình có, không thì bước đo một đại lượng mục tiêu; không có
    mục tiêu nào thì bước đo cuối cùng.
    """
    by_id = {o["id"]: o for o in objects}
    bi_danh_dap_so = {o["id"]: o["alias_of"] for o in objects
                      if o.get("alias_of") and o.get("render") == "non_visual"}
    co_bi_danh = any(e.get("object") in bi_danh_dap_so for e in events)
    muc_tieu = {o["id"] for o in objects if o["type"] == "quantity"
                and o.get("render") == "readout" and "target" in (o.get("display_group") or [])}
    buoc_do = [e for e in events if by_id.get(e.get("object") or "", {}).get("type") == "quantity"]
    cho = [o for o in objects if o["type"] == "quantity" and o.get("origin") == "free"
           and o.get("render") == "readout" and o.get("value") is not None]
    for e in events:
        oid = e.get("object")
        o = by_id.get(oid or "")
        if oid in bi_danh_dap_so:
            goc = by_id[bi_danh_dap_so[oid]]
            # Tiêu điểm là dòng đáp số HỌC SINH THẤY; bí danh của trace vẫn ghi lại.
            # Mang ĐÚNG phụ thuộc của nguồn: giữ `[nguồn]` của bí danh thì nguồn
            # tự phụ thuộc chính nó và mâu thuẫn với sự kiện đo của nó.
            do_goc = next((x for x in events if x is not e and x.get("object") == goc["id"]), None)
            e["depends"] = list(do_goc["depends"] if do_goc else goc.get("depends", []))
            e.update(object=goc["id"], alias_object=oid, display_label=goc["label"],
                     semantic_kind="FINAL_RESULT",
                     learner_text=f"Kết luận: {_giua_cau(goc['label'])} bằng {goc.get('value')}.")
        elif o is not None and o["type"] == "quantity":
            la_ket_luan = not co_bi_danh and (oid in muc_tieu or (not muc_tieu and e is buoc_do[-1]))
            e.update(semantic_kind="FINAL_RESULT" if la_ket_luan else "MEASUREMENT",
                     learner_text=_cau_do(o, by_id))
        elif e.get("action") == "INIT":
            e["learner_text"] = ("Dữ kiện đề cho: " + ", ".join(
                f"{c.get('notation') or c['label']} = {c['value']}" for c in cho) + "."
                if cho else "Đặt các điểm đề cho vào không gian.")
        elif o is not None and o["type"] == "section":
            e["learner_text"] = (_cau_canh_thiet_dien(e, o, by_id) if e.get("action") == "EXTEND"
                                 else _cau_thiet_dien(o, by_id))
        elif o is not None and e.get("action") == "CREATE":
            e["learner_text"] = (
                f"Dựng {_giua_cau(o['label'])} ({len(o.get('vertices') or [])} đỉnh, "
                f"{len(o.get('faces') or [])} mặt)." if o["type"] == "solid"
                else f"Dựng {_giua_cau(o['label'])}.")
        else:
            e["learner_text"] = _sua_cau(e.get("learner_text") or "")


def _build_formation(
    objects: list[dict[str, Any]],
    events: list[dict[str, Any]],
    free_objects: list[str],
) -> dict[str, Any]:
    """Explicit visibility snapshots, độc lập với playback state của UI."""
    by_id = {obj["id"]: obj for obj in objects}
    visible = {object_id for object_id in free_objects if object_id in by_id}
    section_edges = {
        object_id: list(obj.get("boundary_edge_ids") or [])
        for object_id, obj in by_id.items()
        if obj.get("type") == "section"
    }
    section_counts: dict[str, int] = {}
    # Mặt thiết diện TÔ ở bước hoàn tất (bước không phải EXTEND); nối cạnh cuối
    # chỉ khép viền. Không có bước hoàn tất nào thì tô ngay khi viền khép.
    completes = {
        event.get("object") for event in events
        if event.get("object") in section_edges and event.get("action") != "EXTEND"
    }
    completed: set[str] = set()
    steps: list[dict[str, Any]] = []
    for event in events:
        focus = [
            object_id
            for object_id in [event.get("object"), *(event.get("objects") or [])]
            if object_id in by_id
        ]
        visible.update(focus)
        for retired in event.get("retires") or []:
            visible.discard(retired)
        section_id = event.get("object")
        if section_id in section_edges:
            if event.get("action") == "EXTEND":
                ordinal = event.get("details", {}).get("canh")
                if isinstance(ordinal, int):
                    section_counts[section_id] = max(
                        section_counts.get(section_id, 0), ordinal + 1
                    )
            else:
                # Mọi bước KHÁC nối cạnh (hoàn tất thiết diện, hay một thiết diện
                # hiện ra một lần) ⇒ đủ cạnh. Theo cấu trúc, không theo nhãn kiểu.
                section_counts[section_id] = len(section_edges[section_id])
                completed.add(section_id)
        progress = []
        for object_id, count in sorted(section_counts.items()):
            ordered = section_edges[object_id][:count]
            closed = bool(ordered) and count == len(section_edges[object_id])
            progress.append({
                "object_id": object_id,
                "visible_edge_ids": ordered,
                "ordered_construction_ids": ordered,
                "closed": closed,
                "fill_visible": closed and (object_id in completed or object_id not in completes),
            })
        # Vai trò của BƯỚC = hợp vai trò các vật trọng tâm + ba vai theo sự kiện
        # (khai báo · giao · khép thiết diện). Bước đo và kết luận không dựng gì.
        vai = {r for object_id in focus for r in by_id[object_id].get("formation_roles") or ()}
        if event.get("action") == "INIT":
            vai.add("DECLARE_ENTITIES")
        if section_id in section_edges:
            vai.add("CONSTRUCT_INTERSECTION" if event.get("action") == "EXTEND" else "CLOSE_SECTION")
        if event["semantic_kind"] in ("MEASUREMENT", "FINAL_RESULT"):
            vai = set()
        steps.append({
            "step_index": event["step_index"],
            "visible_ids": sorted(visible),
            "focus_ids": sorted(set(focus)),
            "readout_ids": sorted(
                object_id for object_id in visible
                if by_id[object_id].get("render") == "readout"
            ),
            "learner_text": event["learner_text"],
            "semantic_kind": event["semantic_kind"],
            "geometry_progress": progress,
            "formation_roles": sorted(vai),
        })
    if steps:
        # Vật topology không có event riêng vẫn phải hiện ở ảnh kết thúc; chỉ
        # snapshot cuối được phép bổ sung chúng, nên không thể rò ra tương lai.
        steps[-1]["visible_ids"] = sorted(by_id)
        steps[-1]["readout_ids"] = sorted(
            object_id for object_id, obj in by_id.items()
            if obj.get("render") == "readout"
        )
    return {"steps": steps}
