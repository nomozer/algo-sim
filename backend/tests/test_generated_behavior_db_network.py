"""Spot check hành vi cho hai họ còn lại: DATABASE và NETWORK.

─── VÌ SAO KHÔNG DÙNG PROVIDER DẪN-TỪ-SCHEMA ─────────────────────────────

`canonical_config` dựng ứng viên từ schema, và với hai họ này nó không dựng nổi
cấu trúc NHẤT QUÁN THAM CHIẾU: cạnh phải trỏ tới nút có thật, cột phải khai kiểu
thuộc tập đóng. Đó là giới hạn của bộ sinh, không phải của hợp đồng.

Nên nền cấu trúc lấy từ MẪU CÔNG KHAI đang chạy (`frontend/src/data/sim-samples.ts`)
— thứ đã được production dùng — rồi mới đổi MỘT trường có nghĩa để tạo ứng viên
AI-shaped. Validator production vẫn là oracle.

⚠️ Config nền chép từ mẫu công khai nên nó là BẢN SAO. Nếu mẫu đổi mà chỗ này
quên đổi, `test_nen_van_khop_hop_dong` sẽ đỏ vì validator từ chối — đó là cách
bản sao này tự báo mình đã cũ, thay vì trôi im lặng.
"""
from __future__ import annotations

import copy

import pytest

from app.simulation.catalog import CATALOG

DB_BASE = {
    "specVersion": "table-1.0",
    "schema": [
        {"name": "ten", "type": "text", "label": "Họ tên"},
        {"name": "diem", "type": "number", "label": "Điểm"},
        {"name": "to", "type": "number", "label": "Tổ"},
    ],
    "rows": [
        {"ten": "An", "diem": 7.5, "to": 1},
        {"ten": "Bình", "diem": 9, "to": 2},
        {"ten": "Chi", "diem": 6.5, "to": 1},
        {"ten": "Dũng", "diem": 8, "to": 2},
        {"ten": "Em", "diem": 8.5, "to": 1},
    ],
    "filter": {"kind": "compare", "column": "diem", "op": ">=", "value": 8},
    "projection": ["ten", "diem"],
    "sort": {"column": "diem", "direction": "desc"},
    "limit": None,
    "aggregate": None,
    "normalizations": [],
    "notes": None,
}

NET_BASE = {
    "nodes": [
        {"id": "client", "label": "Máy khách", "role": "client"},
        {"id": "router", "label": "Router", "role": "router"},
        {"id": "isp", "label": "ISP", "role": "isp"},
        {"id": "server", "label": "Máy chủ", "role": "server"},
    ],
    "links": [["client", "router"], ["router", "isp"], ["isp", "server"]],
    "source": "client",
    "destination": "server",
    "notes": None,
}


def test_nen_van_khop_hop_dong():
    """Nền chép từ mẫu công khai — nếu mẫu đã đổi thì dòng này đỏ, không trôi."""
    db, err = CATALOG["database.relational_table_query"].validate(copy.deepcopy(DB_BASE))
    assert err is None, f"nền DATABASE đã lệch hợp đồng: {err}"
    assert db, "CONTRACT_SOURCE_EMPTY: validator trả rỗng"
    net, err = CATALOG["network.packet_routing"].validate(copy.deepcopy(NET_BASE))
    assert err is None, f"nền NETWORK đã lệch hợp đồng: {err}"
    assert net, "CONTRACT_SOURCE_EMPTY: validator trả rỗng"


def _rows_passing(cfg: dict) -> list[str]:
    """Kết quả học sinh NHÌN THẤY, tính bằng chính ngữ nghĩa lọc đã validate."""
    f = cfg["filter"]
    col, op, val = f["column"], f["op"], f["value"]
    keep = []
    for r in cfg["rows"]:
        v = r[col]
        if (op == ">=" and v >= val) or (op == ">" and v > val) or (op == "<=" and v <= val):
            keep.append(r["ten"])
    return keep


def test_database_doi_nguong_loc_doi_ket_qua_nhin_thay():
    target = "database.relational_table_query"
    base, err = CATALOG[target].validate(copy.deepcopy(DB_BASE))
    assert err is None

    truoc = base["filter"]["value"]
    tiem = 6.5
    assert tiem != truoc, f"PROBE_NO_OP: giá trị tiêm bằng mặc định ({truoc})"

    ung_vien = copy.deepcopy(DB_BASE)
    ung_vien["filter"]["value"] = tiem
    assert ung_vien["filter"]["value"] != DB_BASE["filter"]["value"] or True

    sau, err = CATALOG[target].validate(ung_vien)
    assert err is None, f"ứng viên AI-shaped bị từ chối: {err}"
    assert sau["filter"]["value"] == tiem, "giá trị tiêm không sống sót qua validate"

    # HẬU QUẢ NHÌN THẤY ĐƯỢC — không chỉ là một trường đổi trong config.
    ket_qua_truoc = _rows_passing(base)
    ket_qua_sau = _rows_passing(sau)
    assert ket_qua_sau != ket_qua_truoc, (
        f"đổi ngưỡng lọc mà kết quả không đổi ({ket_qua_truoc}) ⇒ không chứng minh được gì"
    )
    assert len(ket_qua_sau) > len(ket_qua_truoc), "hạ ngưỡng mà số dòng qua lọc không tăng"


def test_database_doi_chieu_sap_xep():
    target = "database.relational_table_query"
    base, _ = CATALOG[target].validate(copy.deepcopy(DB_BASE))
    truoc = base["sort"]["direction"]
    tiem = "asc" if truoc == "desc" else "desc"
    assert tiem != truoc, "PROBE_NO_OP: chiều sắp xếp tiêm bằng mặc định"

    ung_vien = copy.deepcopy(DB_BASE)
    ung_vien["sort"]["direction"] = tiem
    sau, err = CATALOG[target].validate(ung_vien)
    assert err is None, f"bị từ chối: {err}"
    assert sau["sort"]["direction"] == tiem, "chiều sắp xếp không sống sót"


def test_network_validator_tu_choi_topo_khong_co_duong_di():
    """PHÁT HIỆN của lượt này, giữ lại vì nó là hành vi ĐÚNG cần khoá.

    Bản đầu của phép thử dưới cắt một liên kết để chứng minh "đích không còn tới
    được". Validator TỪ CHỐI ngay lúc validate: một đề mà nguồn không nối tới
    đích thì không phải bài học hợp lệ, nên nó không được phép tồn tại dưới dạng
    ĐẶC TẢ. Việc cắt liên kết là hành động LÚC CHẠY (`net_disconnect`), nơi
    engine tính lại và trả trạng thái không-tới-được — đã chứng minh trên trình
    duyệt, không phải ở tầng sinh đặc tả.
    """
    ung_vien = copy.deepcopy(NET_BASE)
    ung_vien["links"] = [l for l in ung_vien["links"] if l != ["client", "router"]]
    _, err = CATALOG["network.packet_routing"].validate(ung_vien)
    assert err is not None, "tôpô không có đường đi vẫn lọt qua validate"
    assert "đường đi" in err, f"từ chối vì lý do khác dự kiến: {err}"


def test_network_doi_dich_den_doi_tuyen_nhin_thay():
    """Biến đổi AI-shaped HỢP LỆ: đổi đích ⇒ tuyến ngắn lại, quan sát được."""
    target = "network.packet_routing"
    base, err = CATALOG[target].validate(copy.deepcopy(NET_BASE))
    assert err is None

    truoc = base["destination"]
    tiem = "isp"
    assert tiem != truoc, f"PROBE_NO_OP: đích tiêm bằng mặc định ({truoc})"

    ung_vien = copy.deepcopy(NET_BASE)
    ung_vien["destination"] = tiem
    sau, err = CATALOG[target].validate(ung_vien)
    assert err is None, f"ứng viên AI-shaped bị từ chối: {err}"
    assert sau["destination"] == tiem, "đích tiêm không sống sót qua validate"

    def do_dai_tuyen(cfg):
        canh = {tuple(sorted(map(str, l))) for l in cfg["links"]}
        from collections import deque
        d = {cfg["source"]: 0}
        q = deque([cfg["source"]])
        while q:
            cur = q.popleft()
            for a, b in canh:
                for x, y in ((a, b), (b, a)):
                    if x == cur and y not in d:
                        d[y] = d[cur] + 1
                        q.append(y)
        return d.get(cfg["destination"])

    assert do_dai_tuyen(sau) is not None, "đích mới không tới được"
    assert do_dai_tuyen(sau) < do_dai_tuyen(base), (
        "đổi đích mà độ dài tuyến không đổi ⇒ hậu quả không quan sát được"
    )


@pytest.mark.parametrize("target", ["database.relational_table_query", "network.packet_routing"])
def test_nguon_khong_rong(target):
    """Cổng khớp-rỗng: nền rỗng làm mọi khẳng định trên vô nghĩa."""
    base = DB_BASE if target.startswith("database") else NET_BASE
    assert base, "CONTRACT_SOURCE_EMPTY"
    assert len(base.get("rows") or base.get("nodes") or []) >= 3, "nền quá nhỏ để kết luận"
