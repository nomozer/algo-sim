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
    "plane3": "surface",
    "solid": "mesh",
    "polygon3": "polygon",
    "section": "polygon",
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
    "line3": ("point", "direction"),
    "plane3": ("point", "normal"),
    "solid": ("vertices", "faces"),
    "polygon3": ("vertices",),
    "section": ("polygon", "closed", "steps"),
    "quantity": ("value",),
}


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
    ra: list[dict[str, Any]] = []

    for o in state.get("scene", {}).get("objects", []):
        loai = o["type"]
        if loai not in RENDER_HINT:
            # Loại lạ ⇒ BỎ QUA có ghi, không đoán một hình để vẽ. Vẽ bừa là
            # dựng một đối tượng mà chương trình không hề tạo ra.
            continue
        v: dict[str, Any] = {
            "id": o["id"],
            "label": o["label"],
            "type": loai,
            "render": RENDER_HINT[loai],
            # PROVENANCE — không được phẳng hoá. `M = [1,2,3]` mất đúng thứ làm
            # nó mô phỏng được.
            "origin": o["origin"],
            "producer": o.get("producer"),
            "depends": phu_thuoc.get(o["id"], o.get("sources", [])),
        }
        for f in _TRUONG[loai]:
            if f in o:
                v[f] = o[f]
        ra.append(v)

    return {
        "objects": ra,
        "events": build_scene_events(state),
        "free_objects": list(state.get("free_objects", [])),
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
    "construct_plane": "CREATE",
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
    return [
        {
            "step_index": b["step_index"],
            "action": _HANH_DONG.get(b["action"], "STEP"),
            "object": b.get("created"),
            "depends": list(b.get("depends_on", [])),
            "explanation": b.get("explanation", ""),
        }
        for b in state.get("timeline", [])
    ]
