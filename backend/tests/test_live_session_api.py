# -*- coding: utf-8 -*-
"""PHIÊN DẠY TRỰC TIẾP — điều phối lớp, thẩm quyền khoá ở máy chủ.

Mỗi vai một PHIÊN TRÌNH DUYỆT RIÊNG. Dùng chung một client thì cookie của người
đăng nhập sau đè lên người trước, và mọi bài kiểm uỷ quyền mất nghĩa — đó là
cùng lý do `test_classroom_api.py` đã dựng `new_client`.

Bốn cơ chế được kiểm ở đây, và mỗi cái chặn một lỗi ĐÃ QUAN SÁT ĐƯỢC ở một sản
phẩm dạy học thật:

  `cmd_id`    — không có thì mỗi nhịp hỏi lại kéo học sinh về chỗ giáo viên.
  `round_id`  — không có thì tab mở từ tiết trước vẫn điều khiển được lớp.
  `serverNow` — không có thì "em này chờ bao lâu" mỗi máy ra một con số.
  `sync` tách khỏi `mode` — không tách thì gọi cả lớp về một lần là khoá luôn
                            quyền tự khám phá, và giáo viên phải nhớ bật lại.
"""

from __future__ import annotations

import pytest

from tests.conftest_classroom import TEST_PASSWORD, api, login, new_client, register  # noqa: F401
from tests.test_classroom_api import (  # noqa: F401
    GOOD_ENVELOPE,
    make_class,
    make_student,
    make_teacher,
)


def _lop_co_hoc_sinh(api, *, so_hs=1):
    """Giáo viên + lớp + `so_hs` học sinh đã vào lớp + một bài đã giao.

    Trả `(gv, lop, bai, [hs…])`, mỗi người một client riêng.
    """
    gv = api
    make_teacher(gv)
    lop = make_class(gv)
    r = gv.post("/api/assignments", json={
        "classroomId": lop["id"], "title": "Thiết diện S.ABCD",
        "instruction": "Dựng thiết diện", "envelope": GOOD_ENVELOPE})
    assert r.status_code == 200, r.text
    bai = r.json()

    hs = []
    for i in range(so_hs):
        c = new_client(api)
        make_student(c, email=f"hs{i}@lop.test", name=f"Học sinh {i}")
        assert c.post("/api/classes/join",
                      json={"code": lop["joinCode"]}).status_code == 200
        hs.append(c)
    return gv, lop, bai, hs


def _start(gv, lop, bai=None, mode="follow"):
    r = gv.post(f"/api/classes/{lop['id']}/session",
                json={"assignmentId": bai["id"] if bai else None, "mode": mode})
    assert r.status_code == 200, r.text
    return r.json()["session"]


def _cmd(gv, lop, phien, **kw):
    body = {"roundId": phien["roundId"], **kw}
    return gv.post(f"/api/classes/{lop['id']}/session/command", json=body)


# ══ A · KHỞI TẠO PHIÊN ══════════════════════════════════════════════════════
class TestKhoiTao:
    def test_A_giao_vien_bat_dau_phien(self, api):
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        assert s["mode"] == "follow"
        assert s["cmdId"] == 0
        assert s["assignmentId"] == bai["id"]
        assert len(s["roundId"]) >= 8

    def test_G_moi_response_mang_gio_MAY_CHU(self, api):
        """Máy phòng tin hay sai giờ. Không có mốc chung thì mỗi em đếm một kiểu."""
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        _start(gv, lop, bai)
        for r in (gv.get(f"/api/classes/{lop['id']}/session"),
                  hs[0].get(f"/api/classes/{lop['id']}/session"),
                  gv.get(f"/api/classes/{lop['id']}/monitor")):
            assert r.status_code == 200
            assert r.json()["serverNow"], "thiếu serverNow"

    def test_MOT_phien_moi_lop_bat_dau_lai_thi_DOI_ROUND(self, api):
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        a = _start(gv, lop, bai)
        b = _start(gv, lop, bai)
        assert b["roundId"] != a["roundId"]
        assert b["sessionId"] == a["sessionId"], "không được đẻ phiên thứ hai"
        assert b["cmdId"] == 0, "round mới thì đếm lệnh lại từ đầu"


# ══ B·C · THẨM QUYỀN ════════════════════════════════════════════════════════
class TestThamQuyen:
    def test_B_hoc_sinh_KHONG_sua_duoc_trang_thai_lop(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        for body in ({"kind": "SET_MODE", "roundId": s["roundId"], "mode": "free"},
                     {"kind": "STATE_UPDATE", "roundId": s["roundId"], "currentStep": 5},
                     {"kind": "SYNC_CLASS", "roundId": s["roundId"]}):
            r = hs[0].post(f"/api/classes/{lop['id']}/session/command", json=body)
            assert r.status_code == 403, body["kind"]

    def test_B2_hoc_sinh_KHONG_bat_dau_hay_ket_thuc_duoc_phien(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        assert hs[0].post(f"/api/classes/{lop['id']}/session",
                          json={"assignmentId": bai["id"]}).status_code == 403
        assert hs[0].delete(f"/api/classes/{lop['id']}/session").status_code == 403

    def test_C_giao_vien_LOP_KHAC_khong_dieu_khien_duoc(self, api):
        """"Là giáo viên" KHÔNG đủ — phải là giáo viên CỦA LỚP NÀY."""
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        gv2 = new_client(api)
        make_teacher(gv2, email="co2@lop.test", name="Cô Hai")
        r = gv2.post(f"/api/classes/{lop['id']}/session/command",
                     json={"kind": "SET_MODE", "roundId": s["roundId"], "mode": "free"})
        assert r.status_code == 403
        assert gv2.get(f"/api/classes/{lop['id']}/monitor").status_code == 403

    def test_NGUOI_NGOAI_lop_khong_doc_duoc_phien(self, api):
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        _start(gv, lop, bai)
        la = new_client(api)
        make_student(la, email="la@lop.test", name="Người lạ")
        # 404 chứ không 403: người ngoài không cần biết lớp ấy có tồn tại.
        assert la.get(f"/api/classes/{lop['id']}/session").status_code == 404

    def test_hoc_sinh_TRONG_lop_doc_duoc_phien(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        _start(gv, lop, bai)
        r = hs[0].get(f"/api/classes/{lop['id']}/session")
        assert r.status_code == 200 and r.json()["session"] is not None


# ══ D·E·F · LỆNH ════════════════════════════════════════════════════════════
class TestLenh:
    def test_D_cmd_id_TANG_DON_DIEU(self, api):
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        truoc = s["cmdId"]
        for i in range(1, 4):
            r = _cmd(gv, lop, s, kind="STATE_UPDATE", currentStep=i)
            assert r.status_code == 200
            assert r.json()["session"]["cmdId"] == truoc + i

    def test_F_lenh_ROUND_CU_bi_tu_choi(self, api):
        """Tab mở từ tiết trước không được kéo lớp về bài hôm qua."""
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        cu = _start(gv, lop, bai)
        _start(gv, lop, bai)                      # tiết mới
        r = _cmd(gv, lop, cu, kind="STATE_UPDATE", currentStep=9)
        assert r.status_code == 409

    def test_lenh_LA_bi_tu_choi(self, api):
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        assert _cmd(gv, lop, s, kind="REMOTE_CONTROL").status_code == 400
        assert _cmd(gv, lop, s, kind="SET_MODE", mode="nua-nua").status_code == 400

    def test_lenh_khi_KHONG_co_phien_thi_409(self, api):
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        r = gv.post(f"/api/classes/{lop['id']}/session/command",
                    json={"kind": "STATE_UPDATE", "roundId": "khong-co", "currentStep": 1})
        assert r.status_code == 409

    def test_E_client_LOC_lenh_cu_bang_cmd_id(self, api):
        """Hợp đồng phía client: giữ `lastSeenCmdId`, chỉ áp lệnh MỚI.

        Máy chủ KHÔNG nhớ hộ từng học sinh đã thấy tới đâu — nhớ hộ là dựng một
        hàng đợi cho mỗi em. Nó phát một con số tăng đơn điệu, và đó đã đủ để
        mỗi client tự quyết định idempotent.
        """
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        _cmd(gv, lop, s, kind="STATE_UPDATE", currentStep=3)
        a = hs[0].get(f"/api/classes/{lop['id']}/session").json()["session"]
        b = hs[0].get(f"/api/classes/{lop['id']}/session").json()["session"]
        assert a["cmdId"] == b["cmdId"], "đọc lại KHÔNG được sinh lệnh mới"


# ══ H·I·J · FOLLOW / FREE / SYNC ════════════════════════════════════════════
class TestCheDo:
    def test_H_follow_doc_duoc_trang_thai_giao_vien(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai, mode="follow")
        _cmd(gv, lop, s, kind="STATE_UPDATE", currentStep=4,
             selectedId="chop::face:1", isolatedIds=["chop", "td"],
             explodedGroups=["face"])
        got = hs[0].get(f"/api/classes/{lop['id']}/session").json()["session"]
        assert got["mode"] == "follow"
        assert got["currentStep"] == 4
        assert got["selectedId"] == "chop::face:1"
        assert got["isolatedIds"] == ["chop", "td"]
        assert got["explodedGroups"] == ["face"]

    def test_I_doi_sang_FREE_van_giu_trang_thai_giao_vien(self, api):
        """Trạng thái giáo viên KHÔNG mất khi thả lớp ra tự do — nó là thứ
        `SYNC_CLASS` gọi cả lớp về, nên phải còn đó."""
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        _cmd(gv, lop, s, kind="STATE_UPDATE", currentStep=6, selectedId="M")
        _cmd(gv, lop, s, kind="SET_MODE", mode="free")
        got = hs[0].get(f"/api/classes/{lop['id']}/session").json()["session"]
        assert got["mode"] == "free"
        assert got["currentStep"] == 6 and got["selectedId"] == "M"

    def test_J_SYNC_CLASS_khong_doi_mode(self, api):
        """Gọi cả lớp về MỘT LẦN rồi trả lại quyền tự khám phá.

        Ép đổi mode để sync là buộc giáo viên nhớ bật lại — và quên bật lại thì
        cả lớp bị khoá mà không ai hiểu vì sao.
        """
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai, mode="free")
        r = _cmd(gv, lop, s, kind="SYNC_CLASS", currentStep=2, selectedId="SA")
        assert r.status_code == 200
        got = r.json()["session"]
        assert got["mode"] == "free", "SYNC không được đổi chế độ lớp"
        assert got["syncCmdId"] == got["cmdId"]
        hs_thay = hs[0].get(f"/api/classes/{lop['id']}/session").json()["session"]
        assert hs_thay["syncCmdId"] == got["cmdId"]

    def test_J2_SYNC_moi_lan_cho_mot_moc_MOI(self, api):
        """Client áp mỗi mốc đúng một lần — hai lần sync là hai mốc khác nhau."""
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai, mode="free")
        m1 = _cmd(gv, lop, s, kind="SYNC_CLASS", currentStep=1).json()["session"]["syncCmdId"]
        m2 = _cmd(gv, lop, s, kind="SYNC_CLASS", currentStep=2).json()["session"]["syncCmdId"]
        assert m2 > m1

    def test_bo_chon_gui_null_LA_HOP_LE(self, api):
        gv, lop, bai, _ = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        _cmd(gv, lop, s, kind="STATE_UPDATE", selectedId="M")
        r = _cmd(gv, lop, s, kind="STATE_UPDATE", selectedId=None)
        assert r.json()["session"]["selectedId"] is None


# ══ K · TÁCH TRẠNG THÁI HỌC SINH ════════════════════════════════════════════
class TestTachTrangThai:
    def test_K_hai_hoc_sinh_KHONG_lay_nhiem_trang_thai(self, api):
        """A cô lập một mặt, B chọn một điểm. Không ai thấy trạng thái của ai."""
        gv, lop, bai, hs = _lop_co_hoc_sinh(api, so_hs=2)
        _start(gv, lop, bai, mode="free")
        a, b = hs
        a.post(f"/api/assignments/{bai['id']}/progress",
               json={"cursor": 2, "stepCount": 8, "selectedId": "chop::face:1",
                     "lastAction": "ISOLATE_ENTITY"})
        b.post(f"/api/assignments/{bai['id']}/progress",
               json={"cursor": 5, "stepCount": 8, "selectedId": "M",
                     "lastAction": "SELECT_ENTITY"})
        rows = {r["studentName"]: r for r in
                gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"]}
        assert rows["Học sinh 0"]["selectedId"] == "chop::face:1"
        assert rows["Học sinh 0"]["currentStep"] == 2
        assert rows["Học sinh 1"]["selectedId"] == "M"
        assert rows["Học sinh 1"]["currentStep"] == 5

    def test_hoc_sinh_KHONG_ghi_duoc_tien_do_cua_em_khac(self, api):
        """Danh tính lấy từ PHIÊN ĐĂNG NHẬP, không từ body — không có trường
        `studentId` nào để mượn."""
        gv, lop, bai, hs = _lop_co_hoc_sinh(api, so_hs=2)
        a, b = hs
        a.post(f"/api/assignments/{bai['id']}/progress",
               json={"cursor": 1, "stepCount": 8, "selectedId": "A",
                     "studentId": 999})
        rows = {r["studentName"]: r for r in
                gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"]}
        assert rows["Học sinh 1"]["selectedId"] is None, "ghi lấn sang em khác"

    def test_O_hanh_dong_NGOAI_ENUM_bi_bo(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        hs[0].post(f"/api/assignments/{bai['id']}/progress",
                   json={"cursor": 1, "stepCount": 8, "lastAction": "SELECT_ENTITY"})
        hs[0].post(f"/api/assignments/{bai['id']}/progress",
                   json={"cursor": 1, "stepCount": 8, "lastAction": "<script>"})
        row = gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"][0]
        assert row["lastAction"] == "SELECT_ENTITY", "chuỗi tự do lọt vào bảng GV"

    def test_O2_id_ngu_nghia_QUA_DAI_bi_bo_khong_lam_sap_phien(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        r = hs[0].post(f"/api/assignments/{bai['id']}/progress",
                       json={"cursor": 1, "stepCount": 8, "selectedId": "x" * 5000})
        assert r.status_code == 200, "fail-safe, không sập"
        row = gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"][0]
        assert row["selectedId"] is None


# ══ L·M·N · TRỢ GIÚP ════════════════════════════════════════════════════════
class TestTroGiup:
    def test_L_hoc_sinh_gio_tay_CHO_CHINH_MINH(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api, so_hs=2)
        r = hs[0].post(f"/api/assignments/{bai['id']}/help", json={"requested": True})
        assert r.status_code == 200 and r.json()["helpRequested"] is True
        assert r.json()["helpRequestedAt"], "thời điểm do MÁY CHỦ đặt"
        rows = {x["studentName"]: x for x in
                gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"]}
        assert rows["Học sinh 0"]["helpRequested"] is True
        assert rows["Học sinh 1"]["helpRequested"] is False

    def test_gio_tay_HAI_LAN_khong_lam_moi_dong_ho_cho(self, api):
        """Làm mới thì em bấm nhiều lần luôn đứng cuối hàng đợi — phạt đúng em
        đang sốt ruột."""
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        t1 = hs[0].post(f"/api/assignments/{bai['id']}/help",
                        json={"requested": True}).json()["helpRequestedAt"]
        t2 = hs[0].post(f"/api/assignments/{bai['id']}/help",
                        json={"requested": True}).json()["helpRequestedAt"]
        assert t1 == t2

    def test_M_giao_vien_thay_thoi_gian_cho(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        hs[0].post(f"/api/assignments/{bai['id']}/help", json={"requested": True})
        row = gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"][0]
        assert row["helpRequested"] is True
        assert isinstance(row["helpWaitingSeconds"], int) and row["helpWaitingSeconds"] >= 0

    def test_N_giao_vien_danh_dau_DA_HO_TRO(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        hs[0].post(f"/api/assignments/{bai['id']}/help", json={"requested": True})
        me = hs[0].get("/api/auth/me").json()
        sid = me["user"]["id"] if "user" in me else me["id"]
        r = gv.post(f"/api/classes/{lop['id']}/help/{sid}/clear")
        assert r.status_code == 200 and r.json()["cleared"] == 1
        row = gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"][0]
        assert row["helpRequested"] is False
        assert row["helpWaitingSeconds"] is None

    def test_hoc_sinh_TU_HA_TAY_duoc(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        hs[0].post(f"/api/assignments/{bai['id']}/help", json={"requested": True})
        r = hs[0].post(f"/api/assignments/{bai['id']}/help", json={"requested": False})
        assert r.json()["helpRequested"] is False

    def test_hoc_sinh_KHONG_danh_dau_ho_tro_ho_ai_duoc(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api, so_hs=2)
        hs[0].post(f"/api/assignments/{bai['id']}/help", json={"requested": True})
        r = hs[1].post(f"/api/classes/{lop['id']}/help/1/clear")
        assert r.status_code == 403

    def test_ROUND_MOI_don_sach_tay_da_gio(self, api):
        """Một cánh tay giơ từ tiết trước không phải một cánh tay đang giơ."""
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        _start(gv, lop, bai)
        hs[0].post(f"/api/assignments/{bai['id']}/help", json={"requested": True})
        _start(gv, lop, bai)
        row = gv.get(f"/api/classes/{lop['id']}/monitor").json()["rows"][0]
        assert row["helpRequested"] is False


# ══ P·Q·R · RANH GIỚI ═══════════════════════════════════════════════════════
class TestRanhGioi:
    def test_ket_thuc_tiet_thi_phien_HET_HIEU_LUC(self, api):
        gv, lop, bai, hs = _lop_co_hoc_sinh(api)
        s = _start(gv, lop, bai)
        assert gv.delete(f"/api/classes/{lop['id']}/session").status_code == 200
        assert hs[0].get(f"/api/classes/{lop['id']}/session").json()["session"] is None
        # …và lệnh của round đã đóng không sống dậy được.
        assert _cmd(gv, lop, s, kind="STATE_UPDATE", currentStep=1).status_code == 409

    def test_P_mo_bai_da_giao_dung_ENVELOPE_DA_VALIDATE(self, api):
        """30 em mở cùng một bài không tạo 30 lượt phân tích."""
        gv, lop, bai, hs = _lop_co_hoc_sinh(api, so_hs=2)
        for c in hs:
            r = c.get(f"/api/assignments/{bai['id']}")
            assert r.status_code == 200
            assert r.json()["envelope"]["simulation_id"] == GOOD_ENVELOPE["simulation_id"]

    def test_Q_khong_endpoint_nao_o_day_goi_LLM(self):
        """Guard mạng của `conftest` đã gỡ khoá API, nên một lời gọi thật sẽ
        nổ. Nhưng kiểm bằng NGUỒN mạnh hơn: tầng điều phối không được có một
        đường nào tới model, kể cả đường chưa ai đi."""
        from pathlib import Path

        src = Path(__file__).resolve().parents[1] / "app" / "accounts"
        for f in ("session_router.py", "classroom_router.py"):
            noi_dung = (src / f).read_text(encoding="utf-8")
            for cam in ("call_gemini", "load_skill", "GEMINI", "openai", "anthropic"):
                assert cam not in noi_dung, f"{f} có đường tới model: {cam}"

    def test_R_tang_dieu_phoi_KHONG_dung_toi_hinh_hoc(self):
        """Ranh giới cứng: phiên lớp chở ID và số bước. Nó không được import
        kernel, không được đọc `GeometryState`, không được tính lại gì."""
        from pathlib import Path

        import ast

        f = (Path(__file__).resolve().parents[1] / "app" / "accounts"
             / "session_router.py")
        cay = ast.parse(f.read_text(encoding="utf-8"))
        # SOI MÃ, KHÔNG SOI LỜI. Docstring của file nói RÕ rằng nó KHÔNG chạm
        # `GeometryState` — và bản đầu của guard này ĐỎ vì chính câu ấy. Guard
        # khoá chính tả thay vì khoá ý định thì nói dối theo cả hai chiều.
        #
        # Duyệt AST và chỉ lấy IMPORT + THAM CHIẾU TÊN: đó là toàn bộ cách một
        # module Python chạm tới module khác.
        ma = " ".join(
            ast.unparse(n) for n in ast.walk(cay)
            if isinstance(n, (ast.Import, ast.ImportFrom, ast.Attribute, ast.Name)))
        for cam in ("geometry", "Vec3", "GeometryState", "kernel",
                    "cross_section", "scene3d"):
            assert cam not in ma, f"tầng điều phối chạm hình học: {cam}"
        # Rỗng-là-hỏng: nếu `ma` rỗng thì mọi khẳng định trên xanh vô nghĩa.
        assert "PracticeSession" in ma and len(ma) > 500

    def test_KHONG_co_duong_chieu_man_hinh_hay_chup_DOM(self):
        from pathlib import Path

        src = (Path(__file__).resolve().parents[1] / "app" / "accounts"
               / "session_router.py").read_text(encoding="utf-8")
        # Ở đây quét CẢ chú thích là ĐÚNG: một nguyên thuỷ chiếu màn hình không
        # có lý do gì để được nhắc tới, kể cả trong lời bàn.
        for cam in ("screenshot", "screen_share", "innerHTML", "dom_snapshot",
                    "canvas_data", "remote_control", "mouse"):
            assert cam.lower() not in src.lower(), f"có nguyên thuỷ cấm: {cam}"
