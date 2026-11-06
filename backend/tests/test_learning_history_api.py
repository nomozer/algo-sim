# -*- coding: utf-8 -*-
"""Kiểm chứng API lịch sử tự học gắn với tài khoản (`learning_history_entries`)."""

from __future__ import annotations

from tests.conftest_classroom import api, new_client, register  # noqa: F401


def _sample_payload(history_id: str = "generic.semantic_program::abc12345", title: str = "Thiết diện hình chóp S.ABCD") -> dict:
    return {
        "id": history_id,
        "sampleId": "thiet-dien-chop",
        "title": title,
        "simulationId": "generic.semantic_program",
        "domain": "geometry",
        "envelope": {
            "status": "ok",
            "simulation_id": "generic.semantic_program",
            "title": title,
            "config": {"spec_version": "1.0", "title": title, "frames": [], "view_steps": []},
        },
        "originalInput": "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.",
        "lastCursor": 1,
        "stepCount": 5,
        "visualMode": "3d",
    }


def test_history_requires_authentication(api):  # noqa: F811
    assert api.get("/api/history").status_code == 401
    assert api.post("/api/history", json=_sample_payload()).status_code == 401
    assert api.patch("/api/history/abc", json={"lastCursor": 2}).status_code == 401
    assert api.delete("/api/history/abc").status_code == 401
    assert api.delete("/api/history").status_code == 401


def test_history_crud_and_step_progress_persistence(api):  # noqa: F811
    res = register(api, email="hs1@algosim.edu.vn", name="Học sinh 1")
    assert res.status_code == 200

    # Ban đầu rỗng
    empty = api.get("/api/history")
    assert empty.status_code == 200
    assert empty.json()["items"] == []

    # Ghi mục thứ nhất
    p1 = _sample_payload("generic.semantic_program::item1", "Bài 1: Thiết diện hình chóp")
    c1 = api.post("/api/history", json=p1)
    assert c1.status_code == 200
    item1 = c1.json()["item"]
    assert item1["id"] == "generic.semantic_program::item1"
    assert item1["sampleId"] == "thiet-dien-chop"
    assert item1["lastCursor"] == 1
    assert item1["stepCount"] == 5

    # Ghi mục thứ hai
    p2 = _sample_payload("generic.semantic_program::item2", "Bài 2: Giao của mặt phẳng và mặt cầu")
    p2["sampleId"] = "cau-cat-mat-phang"
    c2 = api.post("/api/history", json=p2)
    assert c2.status_code == 200

    # Danh sách sắp theo mới xem gần nhất trước (item2 đứng đầu)
    listed = api.get("/api/history").json()["items"]
    assert [x["id"] for x in listed] == [
        "generic.semantic_program::item2",
        "generic.semantic_program::item1",
    ]

    # Cập nhật bước dựng cho item1 → nhảy lên đầu danh sách và lưu lastCursor = 3
    patched = api.patch(
        "/api/history/generic.semantic_program::item1",
        json={"lastCursor": 3, "stepCount": 5, "visualMode": "3d"},
    )
    assert patched.status_code == 200
    assert patched.json()["item"]["lastCursor"] == 3

    listed_after_patch = api.get("/api/history").json()["items"]
    assert listed_after_patch[0]["id"] == "generic.semantic_program::item1"
    assert listed_after_patch[0]["lastCursor"] == 3

    # Mở lại cùng id không nhân bản bản ghi
    reopen = api.post("/api/history", json={**p1, "lastCursor": 4})
    assert reopen.status_code == 200
    assert len(api.get("/api/history").json()["items"]) == 2
    assert api.get("/api/history").json()["items"][0]["lastCursor"] == 4

    # Xóa 1 mục
    del_one = api.delete("/api/history/generic.semantic_program::item1")
    assert del_one.status_code == 200
    remaining = api.get("/api/history").json()["items"]
    assert [x["id"] for x in remaining] == ["generic.semantic_program::item2"]

    # Xóa toàn bộ
    del_all = api.delete("/api/history")
    assert del_all.status_code == 200
    assert del_all.json()["deleted"] == 1
    assert api.get("/api/history").json()["items"] == []


def test_history_isolated_between_users(api):  # noqa: F811
    client_a = new_client(api)
    client_b = new_client(api)

    assert register(client_a, email="usera@algosim.edu.vn", name="User A").status_code == 200
    assert register(client_b, email="userb@algosim.edu.vn", name="User B").status_code == 200

    payload_a = _sample_payload("generic.semantic_program::sharedkey", "Bài của User A")
    assert client_a.post("/api/history", json=payload_a).status_code == 200

    # User B không nhìn thấy lịch sử của User A
    assert client_b.get("/api/history").json()["items"] == []

    # User B không sửa hoặc xóa được mục của User A
    assert (
        client_b.patch(
            "/api/history/generic.semantic_program::sharedkey",
            json={"lastCursor": 4},
        ).status_code
        == 404
    )
    assert (
        client_b.delete("/api/history/generic.semantic_program::sharedkey").status_code
        == 404
    )

    # User B xóa toàn bộ lịch sử của mình không làm mất lịch sử của User A
    assert client_b.delete("/api/history").status_code == 200
    items_a = client_a.get("/api/history").json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["title"] == "Bài của User A"


def test_history_order_holds_when_writes_share_one_clock_tick(api, monkeypatch):  # noqa: F811
    """Windows' clock ticks every ~15.6 ms: several writes can read the same `now`. The most recently viewed entry must
    still list first (and overflow pruning, which uses the same order, must drop the oldest)."""
    import app.accounts.router as router_mod
    from datetime import datetime as real_dt, timezone as tz

    frozen = real_dt(2026, 11, 6, 12, 0, 0, tzinfo=tz.utc)

    class _Frozen(real_dt):
        @classmethod
        def now(cls, tz=None):  # noqa: ARG003
            return frozen

    monkeypatch.setattr(router_mod, "datetime", _Frozen)
    assert register(api, email="tick@algosim.edu.vn", name="Tick").status_code == 200
    for k in ("k1", "k2", "k3"):
        assert api.post("/api/history", json=_sample_payload(f"generic.semantic_program::{k}", k)).status_code == 200
    assert api.patch("/api/history/generic.semantic_program::k1", json={"lastCursor": 2}).status_code == 200
    ids = [x["id"].split("::")[1] for x in api.get("/api/history").json()["items"]]
    assert ids == ["k1", "k3", "k2"]


def test_history_keeps_hybrid_answer_evidence_and_attempt_identity_verbatim(api):  # noqa: F811
    """Server history is a verbatim store: the exact scene, primed labels, the frontend `hybrid_preview` binding
    (answers + coefficient), the stamped statement and the attempt ID come back unchanged on create and on update."""
    import json
    from pathlib import Path

    layers = Path(__file__).resolve().parents[2] / (
        "docs/evaluation/geometry/runs/axo-end-to-end-authority-scene3d-usability/inputs/prism-layers.json")
    response = json.loads(layers.read_text(encoding="utf-8"))["rows"]["reference"]["response"]
    envelope = {**response["envelope"], "problem_statement": response["envelope"]["title"],
                "hybrid_preview": {"answers": [{"quantity_id": "kq_q", "coefficient": "30", "symbolic": "30",
                                                "dim": 0, "unit": None}],
                                   "source_provenance": response["route_d"]["source_provenance"]}}
    assert register(api, email="hs-evidence@algosim.edu.vn", name="HS").status_code == 200
    attempt = "a" + "0123456789abcdef" * 2
    statement = "Cho hình lăng trụ đứng A′B′C′.DEF — √41, ½"
    payload = {"id": attempt, "sampleId": None, "title": "Lăng trụ", "simulationId": envelope["simulation_id"],
               "domain": "geometry", "envelope": envelope, "originalInput": statement, "lastCursor": 3,
               "stepCount": 4, "visualMode": "3d"}
    for _ in range(2):                                   # create, then the update path
        assert api.post("/api/history", json=payload).status_code == 200
        (item,) = api.get("/api/history").json()["items"]
        assert item["envelope"] == envelope
        assert (item["id"], item["originalInput"], item["sampleId"]) == (attempt, statement, None)
