# -*- coding: utf-8 -*-
"""W17 §15.4 — SỐ ĐO TRÊN HÌNH: mỗi đại lượng hiển thị gắn với CHỦ THỂ hình học của nó.

Backend sở hữu nghĩa; frontend chỉ chiếu, đặt nhãn và bật/tắt — không suy chủ thể từ tên biến,
không tự tính giá trị. Hai nguồn gắn, cả hai tất định:
- đại lượng ĐO: toán hạng IR của `measure` — diện tích → đa giác/thiết diện (`region`), thể tích →
  khối đa diện (`solid`), khoảng cách có một toán hạng là ĐIỂM → cặp (`pair`; hai ĐIỂM ⇒ độ dài đoạn,
  `segment`); góc chưa có điểm neo (xem `_DO`);
- độ dài ĐỀ CHO: đoạn mà bộ đọc đề của server đọc ngay trước span bằng chứng GIVEN (cùng thẩm quyền
  `grounding_gate`), VÀ khoảng cách CHÍNH XÁC giữa hai điểm trong bộ nhớ cuối bằng đúng giá trị.
Không gắn được ⇒ không có nhãn, chẩn đoán `ANNOTATION_UNBOUND <id>: <lý do>`; đại lượng vẫn ở bảng
chi tiết. `category` (`measurement`/`result`) và `role` do `scene3d` quyết: chúng cần nhóm `target`
và bí danh.

W18 (§16.6–16.7): cùng chủ thể ⇒ `same_as` (một nhãn, một dòng — không còn bỏ gắn); khoảng cách điểm →
đường/mặt phẳng mang `witness` — chân CHÍNH XÁC do kernel tính, neo nhãn ở trung điểm đoạn tới chân.
Đăng ký: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §15.4, §16.6, §16.7.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from ..geometry import kernel as K
from ..geometry.exact import Line3, Plane3, Vec3
from ..geometry.predicates import collinear
from ..geometry.radical import square
from .display_names import ky_hieu_dai_luong
from .grounding_gate import _bang_chung_do_dai, _cung_doan
from .segment_relation import cac_doan_truoc
from .shape_constraint import che_muc_tieu
from .source_entities import dinh_danh_thuc_the, ky_hieu_toan

#: `measure.quantity` → (kind, anchor, kiểu được phép của toán hạng `of` — None: mọi kiểu).
#: Điểm neo phải đặt được ở phía trình bày CHỈ bằng trung bình toạ độ (frontend cấm suy luận hình
#: học, kể cả chân đường vuông góc): khoảng cách cần một toán hạng là ĐIỂM (neo ở điểm ấy; hai
#: điểm ⇒ đoạn); góc giữa hai đường/mặt và vật cong (đường tròn, elip, khối tròn xoay) chưa có
#: điểm neo đăng ký ⇒ không gắn.
_DO: dict[str, tuple[str, str, frozenset[str] | None]] = {
    "area": ("area", "region", frozenset({"polygon3", "section"})),
    "volume": ("volume", "solid", frozenset({"solid"})),
    "distance": ("distance", "pair", None),
}


def gan_so_do(spec: Any, final_memory: dict[str, Any], contract: Any,
              objects: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """→ ({id đại lượng: {kind, subject_ids, anchor, unit}}, chẩn đoán) cho mọi vật `quantity`."""
    loai = {o["id"]: o["type"] for o in objects}
    dinh_nghia = {getattr(s, "target_var", None): s for s in spec.statements}
    khai = {d.name: d for d in spec.memory_declarations}
    de = che_muc_tieu(getattr(contract, "problem_text", "") or "")
    doan = {frozenset(o.get("endpoint_ids") or ()) for o in objects
            if o["type"] == "segment3" and len(o.get("endpoint_ids") or ()) == 2}
    gan: dict[str, dict[str, Any]] = {}
    chan_doan: list[str] = []
    for o in objects:
        if o["type"] != "quantity":
            continue
        kq = _gan_mot(o["id"], dinh_nghia.get(o["id"]), khai.get(o["id"]), loai, final_memory, de)
        if isinstance(kq, dict) and kq.get("anchor") == "witness":
            kq = _bam_doan_da_dung(kq, loai, final_memory, doan)
        if isinstance(kq, dict):
            gan[o["id"]] = kq
        else:
            chan_doan.append(f"ANNOTATION_UNBOUND {o['id']}: {kq}")
    # Một chủ thể, một nhãn: độ dài đề cho AA′ và chiều cao đo được AA′ (hình hộp) là cùng một phép
    # đo trên cùng một đoạn. Nhãn thuộc DỮ KIỆN (không có câu lệnh định nghĩa), rồi theo thứ tự cảnh;
    # vật sau trỏ `same_as` về nó (W18 §16.6). Tiêu chí là chủ thể — KHÔNG BAO GIỜ là giá trị.
    da_co: dict[tuple, str] = {}
    for q in sorted(gan, key=lambda q: dinh_nghia.get(q) is not None):
        k = (gan[q]["kind"], gan[q]["anchor"], frozenset(gan[q]["subject_ids"]))
        if k in da_co:
            chan_doan.append(f"ANNOTATION_SAME_AS {q}: {da_co[k]}")
            gan[q]["same_as"] = da_co[k]
        else:
            da_co[k] = q
    return gan, chan_doan


def _bam_doan_da_dung(kq: dict[str, Any], loai: dict[str, str], mem: dict[str, Any],
                      doan: set[frozenset]) -> dict[str, Any]:
    """regular-square-pyramid-w02: chân của nhân chứng TRÙNG một điểm của cảnh (cùng toạ độ chính xác) và đoạn từ
    điểm đo tới điểm ấy đã được DỰNG (vd đường cao SO) ⇒ đại lượng là độ dài của đoạn ấy: nhãn bám đoạn, không vẽ
    thêm nét đứt chồng lên một đoạn đã có. Không có đoạn đã dựng ⇒ giữ nhân chứng."""
    w = kq["witness"]
    chan = Vec3.of(*w["foot"])
    for p, kieu in loai.items():
        if (kieu == "point3" and p != w["from"] and isinstance(mem.get(p), Vec3) and mem[p] == chan
                and frozenset((w["from"], p)) in doan):
            return {"kind": "length", "subject_ids": [w["from"], p], "anchor": "segment", "unit": kq.get("unit")}
    return kq


def _xau(v: Vec3) -> list[str]:
    return [str(v.x), str(v.y), str(v.z)]


def _nhan_chung(diem: str, nhan: str, mem: dict[str, Any]) -> dict[str, Any] | None:
    """W18 §16.7 — chân đường vuông góc CHÍNH XÁC từ `diem` tới đường/mặt phẳng `nhan` (kernel), và hai
    phương của ký hiệu vuông góc tại chân: `u` dọc vật nhận, `v` từ chân tới điểm. Vật nhận khác (đa
    giác, khối…) hay khoảng cách 0 ⇒ không có nhân chứng."""
    p, r = mem.get(diem), mem.get(nhan)
    if isinstance(r, Line3):
        chan, u = K.project_point_onto_line(p, r), r.direction
    elif isinstance(r, Plane3):
        chan = K.project_point_onto_plane(p, r)
        u = r.point - chan
        if u.is_zero():
            u = next(w for w in (r.normal.cross(Vec3.of(*e)) for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
                     if not w.is_zero())
    else:
        return None
    v = p - chan
    if v.is_zero():
        return None
    return {"from": diem, "foot": _xau(chan), "on": nhan, "marker": {"u": _xau(u), "v": _xau(v)}}


def _gan_mot(q: str, st: Any, decl: Any, loai: dict[str, str], mem: dict[str, Any],
             de: str) -> dict[str, Any] | str:
    expr = getattr(st, "expr", None)
    if getattr(expr, "kind", None) == "measure":
        kind, anchor, cho_phep = _DO.get(expr.quantity, (None, None, None))
        chu_the = [x for x in (expr.of, expr.wrt) if x]
        if kind is None:
            return f"measure {expr.quantity} has no registered anchor"
        if any(x not in loai for x in chu_the):
            return "a measured operand is not a scene object"
        if cho_phep is not None and loai[expr.of] not in cho_phep:
            return f"{expr.quantity} of a {loai[expr.of]} has no registered anchor"
        nhan_chung = None
        if expr.quantity == "distance":
            if all(loai[x] == "point3" for x in chu_the):
                kind, anchor = "length", "segment"
            elif not any(loai[x] == "point3" for x in chu_the):
                return "distance between two non-point objects has no registered anchor"
            else:
                diem = next(x for x in chu_the if loai[x] == "point3")
                nhan_chung = _nhan_chung(diem, next(x for x in chu_the if x != diem), mem)
        if nhan_chung is not None:
            return {"kind": kind, "subject_ids": chu_the, "anchor": "witness", "unit": None, "witness": nhan_chung}
        return {"kind": kind, "subject_ids": chu_the, "anchor": anchor, "unit": None}
    if getattr(expr, "kind", None) == "var":
        return f"copy of {expr.name} — shares its identity"
    if st is None and decl is not None and decl.initial_value is not None:
        return _do_dai_de_cho(q, loai, mem, de)
    return "computed by a statement that measures no single subject"


def _do_dai_de_cho(q: str, loai: dict[str, str], mem: dict[str, Any], de: str) -> dict[str, Any] | str:
    """Độ dài ĐỀ CHO: đoạn đề gọi tên ngay trước con số bằng chứng, kiểm bằng khoảng cách chính xác."""
    v = mem.get(q)
    try:
        so: Fraction | str = Fraction(str(v))
    except (ValueError, ZeroDivisionError):
        so = str(v)
    ma, bc, _ = _bang_chung_do_dai(de, q, so, None) if de else ("NO_TEXT", None, "")
    if ma or not bc or not bc.get("span"):
        return "no GIVEN evidence span in the text"
    # Bằng chứng của `q` đứng sau đúng đoạn của nó (một thành viên của chuỗi `SA = SB = 3`), hoặc sau số trơn.
    doan = next((d for d in cac_doan_truoc(de[:bc["span"][0]]) if _cung_doan(q, d)), None)
    if doan is None:
        return "the text gives the number without naming a segment"
    p, r = (dinh_danh_thuc_the(t)[0] for t in doan)
    if loai.get(p) != "point3" or loai.get(r) != "point3":
        return "the named segment's endpoints are not scene points"
    d = mem[r] - mem[p]
    try:                                       # §18.3: độ dài đề cho có thể là căn
        bang = d.dot(d) == square(v)
    except (TypeError, ValueError):
        bang = False
    if not bang:
        return f"the figure's {p}{r} is not {v}"
    return {"kind": "length", "subject_ids": [p, r], "anchor": "segment", "unit": bc.get("unit")}


def _doan_cua_ten(name: str, vertices: list[str]) -> tuple[str, str] | None:
    """Đoạn mà TÊN đại lượng độ dài gọi giữa hai đỉnh khai — cùng luật với `simulation_state._length_joins_vertices`."""
    symbol = ky_hieu_dai_luong(name)
    labels = [(v, (ky_hieu_toan(v) or "").replace("'", "′")) for v in vertices]
    cap = [(a, b) for i, (a, la) in enumerate(labels) for b, lb in labels[i + 1:]
           if la and lb and symbol in (la + lb, lb + la)]
    return cap[0] if symbol and len(cap) == 1 else None


def doan_tren_canh(objects: list[dict[str, Any]], memory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """regular-square-pyramid-w04 — đoạn mà HAI đầu mút nằm trên một cạnh khối (SM, M trung điểm SA) nhưng không trùng
    tên hai đầu cạnh: `{id đoạn: {solid, edge: [u, w], t0, t1}}`, kiểm CHÍNH XÁC (thẳng hàng + tham số trong [0, 1]).
    `edge` theo thứ tự chỉ số đỉnh của khối (cùng chiều cạnh chuẩn của tầng cảnh); `t` đo từ `u`. Tầng cảnh chỉ chép
    nó để cạnh chuẩn là owner nét duy nhất — không phép hình học nào ở đó."""
    khoi = [(o["id"], o["vertex_ids"], o.get("faces") or []) for o in objects
            if o.get("type") == "solid" and o.get("vertex_ids")]
    ra: dict[str, dict[str, Any]] = {}
    for s in objects:
        ten = s.get("endpoint_ids") or []
        if s.get("type") != "segment3" or len(ten) != 2:
            continue
        p = [memory.get(x) for x in ten]
        if not all(isinstance(x, Vec3) for x in p):
            continue
        for sid, vids, faces in khoi:
            canh = {tuple(sorted((f[i], f[(i + 1) % len(f)]))) for f in faces for i in range(len(f))}
            for i, j in sorted(canh):
                u, w = vids[i], vids[j]
                a, b = memory.get(u), memory.get(w)
                if {u, w} == set(ten) or not (isinstance(a, Vec3) and isinstance(b, Vec3)):
                    continue
                d = b - a
                if d.is_zero() or not all(collinear(a, b, x) for x in p):
                    continue
                t = [(x - a).dot(d) / d.dot(d) for x in p]
                if all(0 <= x <= 1 for x in t) and t[0] != t[1]:
                    ra[s["id"]] = {"solid": sid, "edge": [u, w], "t0": float(min(t)), "t1": float(max(t))}
    return ra


def chieu_cao_the_tich(objects: list[dict[str, Any]], memory: dict[str, Any],
                       so_do: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """regular-square-pyramid-w02 — CHIỀU CAO của công thức thể tích, chọn bằng QUAN HỆ HÌNH HỌC kiểm chính xác.

    Ứng viên là các nguồn số của thể tích (ngoài diện tích đáy). Một ứng viên là chiều cao khi đoạn nó đo — đoạn
    gắn nhãn của tầng số đo, hoặc đoạn tên nó gọi giữa hai đỉnh khối — có độ dài đúng bằng giá trị (chỉ là kiểm
    NHẤT QUÁN), cùng phương pháp tuyến mặt đáy, một đầu trên mặt đáy và đầu kia ngoài; hoặc khi nó đo khoảng cách
    từ một điểm tới một mặt phẳng trùng mặt đáy. Giá trị bằng nhau KHÔNG BAO GIỜ là lý do (W1 `98e2b8f7` chọn theo
    giá trị và in `× DF` cho một cạnh đáy trên tình cờ bằng chiều cao). Nhiều chiều cao thật: ưu tiên dữ kiện đề
    cho; còn hơn một ⇒ không chọn (không in còn hơn in mơ hồ).

    → {id thể tích: {"height": id, "symbol": ký hiệu đoạn đã DỰNG khi chiều cao là khoảng cách đo bám đoạn ấy}}.
    """
    by_id = {o["id"]: o for o in objects}
    ra: dict[str, dict[str, Any]] = {}
    for v in objects:
        if v.get("type") != "quantity" or v.get("producer") != "measure.volume":
            continue
        nguon = [by_id[x] for x in v.get("sources") or () if x in by_id]
        dt = next((x for x in nguon if x.get("producer") == "measure.area"), None)
        khoi = next((x for x in nguon if x.get("type") == "solid"), None)
        da_giac = by_id.get(next(iter((so_do.get(dt["id"]) or {}).get("subject_ids") or ()), "")) if dt else None
        day = [memory.get(p) for p in (da_giac or {}).get("vertex_ids") or ()]
        if not khoi or len(day) < 3 or not all(isinstance(p, Vec3) for p in day):
            continue
        n = (day[1] - day[0]).cross(day[2] - day[0])
        if n.is_zero():
            continue
        tren_day = lambda p: n.dot(p - day[0]) == 0  # noqa: E731
        cao: list[dict[str, Any]] = []
        for c in nguon:
            if c is dt or c.get("type") != "quantity":
                continue
            g = so_do.get(c["id"]) or {}
            cap = (tuple(g["subject_ids"]) if g.get("anchor") == "segment" and len(g.get("subject_ids") or ()) == 2
                   else _doan_cua_ten(c["id"], list(khoi.get("vertex_ids") or ())))
            gt = memory.get(c["id"])
            if cap and all(isinstance(memory.get(p), Vec3) for p in cap):
                p, q = memory[cap[0]], memory[cap[1]]
                try:                           # §18.3: giá trị có thể là căn (√3) — so bình phương chính xác
                    nhat_quan = (p - q).dot(p - q) == square(gt)
                except (TypeError, ValueError):
                    nhat_quan = False
                if nhat_quan and (p - q).cross(n).is_zero() and tren_day(p) != tren_day(q):
                    cao.append(c)
            elif g.get("anchor") == "witness":
                mat = memory.get((g.get("witness") or {}).get("on"))
                if isinstance(mat, Plane3) and mat.normal.cross(n).is_zero() and tren_day(mat.point):
                    cao.append(c)
        de_cho = [c for c in cao if c.get("origin") == "free"]
        chon = de_cho if de_cho else cao
        if len(chon) != 1:
            continue
        h = chon[0]
        g = so_do.get(h["id"]) or {}
        doan = next((o for o in objects if o.get("type") == "segment3"
                     and set(o.get("endpoint_ids") or ()) == set(g.get("subject_ids") or ())), None)
        ky = doan.get("notation") if (doan and h.get("producer") == "measure.distance") else None
        ra[v["id"]] = {"height": h["id"], "symbol": ky}
    return ra
