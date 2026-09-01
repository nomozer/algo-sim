# -*- coding: utf-8 -*-
"""M18 — LỚP HỌC, BÀI THỰC HÀNH, QUAN SÁT: UỶ QUYỀN KHOÁ Ở MÁY CHỦ.

File này là chỗ trả lời §36 (sáu ca phải bị TỪ CHỐI) và §38 (tiêm lỗi lớp học).
Mỗi ca đều đi qua HTTP thật với hai phiên trình duyệt độc lập — dùng chung một
client thì cookie của người đăng nhập sau đè lên người trước và bài kiểm mất
nghĩa.
"""

from __future__ import annotations

import json

import pytest

from tests.conftest_classroom import TEST_PASSWORD, api, login, new_client, register  # noqa: F401

# Envelope HỢP LỆ tối thiểu — đi qua đúng cổng của tuyến ngữ nghĩa.
#
# ⚠️ Trước `LEGACY_INFORMATICS_REMOVAL` fixture này là `logic.and_gate`, và nó
# đi qua `CATALOG[sim_id].validate`. Nhánh ấy đã gỡ: chỉ còn MỘT `simulation_id`
# giao được cho lớp — tuyến ngữ nghĩa, tức mọi bài hình học. Đổi fixture chứ
# không nới cổng: mọi phép kiểm về quyền, thành viên, kích thước, vòng đời
# phiên đều không phụ thuộc miền, nên chúng giữ nguyên hiệu lực.
GOOD_ENVELOPE = {
    "status": "ok",
    "simulation_id": "generic.semantic_program",
    "domain": "geometry",
    "visual_mode": "3d",
    "title": "Thiết diện hình chóp",
    "config": {
        "spec_version": "1.0",
        "title": "Thiết diện hình chóp",
        "frames": [
            {"step_index": 0, "narration": "Dựng đáy.",
             "objects": [], "highlighted_object_ids": []},
            {"step_index": 1, "narration": "Cắt bởi mặt phẳng.",
             "objects": [], "highlighted_object_ids": []},
        ],
        "view_steps": [{"frame_lo": 0, "frame_hi": 0},
                       {"frame_lo": 1, "frame_hi": 1}],
        "grouping_level": "step",
        "presentation_overflow": False,
        "execution_truncated": False,
    },
}


def make_teacher(client, *, email="co@lop.test", name="Cô Lan"):
    r = register(client, email=email, name=name, role="teacher",
                 teacher_code="MA-GIAO-VIEN-TEST")
    assert r.status_code == 200, r.text
    return r


def make_student(client, *, email="an@lop.test", name="An"):
    r = register(client, email=email, name=name)
    assert r.status_code == 200, r.text
    return r


def make_class(teacher_client, name="10A1") -> dict:
    r = teacher_client.post("/api/classes", json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()


# ── LỚP ──────────────────────────────────────────────────────────────────────

class TestLop:
    def test_giao_vien_tao_lop_va_nhan_ma(self, api):
        make_teacher(api)
        c = make_class(api)
        assert c["name"] == "10A1"
        assert len(c["joinCode"]) == 6 and c["codeActive"] is True

    def test_ma_lop_KHONG_chua_ky_tu_de_nham(self, api):
        """0/O/1/I/L bị loại vì học sinh gõ tay mã này trên bảng."""
        make_teacher(api)
        for i in range(8):
            code = make_class(api, name=f"L{i}")["joinCode"]
            assert not (set(code) & set("O0I1L")), code

    def test_HOC_SINH_goi_endpoint_tao_lop_thi_BI_TU_CHOI(self, api):
        """§36.1"""
        make_student(api)
        r = api.post("/api/classes", json={"name": "Lớp giả"})
        assert r.status_code == 403

    def test_KHACH_goi_endpoint_tao_lop_thi_BI_TU_CHOI(self, api):
        r = api.post("/api/classes", json={"name": "Lớp giả"})
        assert r.status_code == 401

    def test_hoc_sinh_vao_lop_bang_ma(self, api):
        make_teacher(api)
        code = make_class(api)["joinCode"]
        s = new_client(api)
        make_student(s)
        r = s.post("/api/classes/join", json={"code": code})
        assert r.status_code == 200 and r.json()["alreadyMember"] is False
        assert [c["name"] for c in s.get("/api/classes").json()["classes"]] == ["10A1"]

    def test_ma_lop_khong_phan_biet_hoa_thuong_va_khoang_trang(self, api):
        make_teacher(api)
        code = make_class(api)["joinCode"]
        s = new_client(api)
        make_student(s)
        messy = f" {code.lower()[:3]} {code.lower()[3:]} "
        assert s.post("/api/classes/join", json={"code": messy}).status_code == 200

    def test_ma_sai_thi_KHONG_tao_tu_cach_thanh_vien(self, api):
        """§36.6"""
        s = new_client(api)
        make_student(s)
        r = s.post("/api/classes/join", json={"code": "SAIMA9"})
        assert r.status_code == 404
        assert s.get("/api/classes").json()["classes"] == []

    def test_ma_da_THU_HOI_thi_khong_vao_duoc_nua(self, api):
        """§36.6 — thu hồi phải có hiệu lực ngay."""
        make_teacher(api)
        c = make_class(api)
        api.delete(f"/api/classes/{c['id']}/code")
        s = new_client(api)
        make_student(s)
        r = s.post("/api/classes/join", json={"code": c["joinCode"]})
        assert r.status_code == 410
        assert s.get("/api/classes").json()["classes"] == []

    def test_sinh_lai_ma_thi_ma_CU_chet(self, api):
        make_teacher(api)
        c = make_class(api)
        old = c["joinCode"]
        new = api.post(f"/api/classes/{c['id']}/code").json()["joinCode"]
        assert new != old
        s = new_client(api)
        make_student(s)
        assert s.post("/api/classes/join", json={"code": old}).status_code == 404
        assert s.post("/api/classes/join", json={"code": new}).status_code == 200

    def test_vao_lop_HAI_LAN_khong_phai_loi_va_khong_tao_hai_dong(self, api):
        make_teacher(api)
        code = make_class(api)["joinCode"]
        s = new_client(api)
        make_student(s)
        s.post("/api/classes/join", json={"code": code})
        r = s.post("/api/classes/join", json={"code": code})
        assert r.status_code == 200 and r.json()["alreadyMember"] is True
        assert len(s.get("/api/classes").json()["classes"]) == 1

    def test_hoc_sinh_KHONG_thay_ma_lop(self, api):
        """Mã là LỜI MỜI để giáo viên phát tiếp, không phải thông tin lớp."""
        make_teacher(api)
        code = make_class(api)["joinCode"]
        s = new_client(api)
        make_student(s)
        s.post("/api/classes/join", json={"code": code})
        body = s.get("/api/classes").text
        assert code not in body and "joinCode" not in body

    def test_giao_vien_KHAC_khong_xem_duoc_danh_sach_lop_khong_phai_cua_minh(self, api):
        """§36.3"""
        make_teacher(api)
        c = make_class(api)
        other = new_client(api)
        make_teacher(other, email="thay@lop.test", name="Thầy Nam")
        assert other.get(f"/api/classes/{c['id']}/members").status_code == 403
        assert other.get("/api/classes").json()["classes"] == []


# ── BÀI THỰC HÀNH ────────────────────────────────────────────────────────────

class TestBaiThucHanh:
    def _setup(self, api):
        make_teacher(api)
        c = make_class(api)
        s = new_client(api)
        make_student(s)
        s.post("/api/classes/join", json={"code": c["joinCode"]})
        return c, s

    def test_giao_bai_roi_hoc_sinh_thay(self, api):
        c, s = self._setup(api)
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Cổng AND",
            "instruction": "Bật/tắt hai đầu vào rồi ghi lại bảng chân trị.",
            "envelope": GOOD_ENVELOPE})
        assert r.status_code == 200, r.text
        items = s.get("/api/assignments").json()["assignments"]
        assert [a["title"] for a in items] == ["Cổng AND"]
        assert items[0]["myPractice"] is None

    def test_ENVELOPE_KHONG_HOP_LE_bi_chan_o_cong_giao_bai(self, api):
        """§38.4 — chữ/cấu hình của giáo viên KHÔNG thành sự thật runtime.
        Nếu cổng này mất, lỗi sẽ nổ trên màn hình học sinh giữa tiết."""
        c, _ = self._setup(api)
        bad = {**GOOD_ENVELOPE, "config": {"inputA": 5, "inputB": 0}}
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Hỏng", "envelope": bad})
        assert r.status_code == 400
        assert "không hợp lệ" in r.json()["detail"]

    # ── TUYẾN NGỮ NGHĨA (MỌI BÀI HÌNH HỌC) ──────────────────────────────
    #
    # Bốn ca dưới đây tồn tại vì cổng giao bài TỪNG từ chối thẳng mọi envelope
    # hình học: nó chỉ hỏi `CATALOG`, mà tuyến ngữ nghĩa không nằm trong
    # `CATALOG`. Hệ quả không phải một lỗi nhỏ — giáo viên không giao được đúng
    # miền mà đề tài nói về, và tầng lớp học chỉ dùng được cho danh mục Tin học
    # cũ. Nghiệm thu ba trình duyệt bắt được (400 ở bước giao bài).

    @staticmethod
    def _envelope_hinh_hoc(**doi):
        """Envelope tuyến ngữ nghĩa tối thiểu: hai khung, hai bước xem phủ kín."""
        e = {
            "status": "ok",
            "simulation_id": "generic.semantic_program",
            "domain": "geometry",
            "visual_mode": "3d",
            "title": "Thiết diện hình chóp",
            "config": {
                "spec_version": "1.0",
                "title": "Thiết diện hình chóp",
                "frames": [
                    {"step_index": 0, "narration": "Dựng đáy.",
                     "objects": [], "highlighted_object_ids": []},
                    {"step_index": 1, "narration": "Cắt bởi mặt phẳng.",
                     "objects": [], "highlighted_object_ids": []},
                ],
                "view_steps": [{"frame_lo": 0, "frame_hi": 0},
                               {"frame_lo": 1, "frame_hi": 1}],
                "grouping_level": "step",
                "presentation_overflow": False,
                "execution_truncated": False,
            },
        }
        e["config"].update(doi)
        return e

    def test_GIAO_DUOC_bai_hinh_hoc_tuyen_ngu_nghia(self, api):
        c, s = self._setup(api)
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Thiết diện S.ABCD",
            "instruction": "Dựng thiết diện qua M song song với (SBD).",
            "envelope": self._envelope_hinh_hoc()})
        assert r.status_code == 200, r.text
        items = s.get("/api/assignments").json()["assignments"]
        assert [a["title"] for a in items] == ["Thiết diện S.ABCD"]

    def test_bai_hinh_hoc_THIEU_KHUNG_van_bi_chan(self, api):
        """Cổng mới phải TỪ CHỐI được — mở rộng danh mục không phải bỏ cổng."""
        c, _ = self._setup(api)
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Hỏng",
            "envelope": self._envelope_hinh_hoc(frames=[])})
        assert r.status_code == 400
        assert "không hợp lệ" in r.json()["detail"]

    def test_bai_hinh_hoc_BUOC_XEM_BO_SOT_KHUNG_bi_chan(self, api):
        """Ca hiểm: khung có đủ, nhưng bước xem bỏ sót khung cuối.

        Đây mới là ca đáng sợ — nó qua được mọi phép kiểm "có dữ liệu không",
        rồi học sinh gặp một bước trắng ở giữa tiết.
        """
        c, _ = self._setup(api)
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Hỏng",
            "envelope": self._envelope_hinh_hoc(
                view_steps=[{"frame_lo": 0, "frame_hi": 0}])})
        assert r.status_code == 400
        assert "phủ hết" in r.json()["detail"]

    def test_bai_hinh_hoc_BUOC_XEM_CHONG_LAN_bi_chan(self, api):
        c, _ = self._setup(api)
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Hỏng",
            "envelope": self._envelope_hinh_hoc(
                view_steps=[{"frame_lo": 0, "frame_hi": 1},
                            {"frame_lo": 0, "frame_hi": 1}])})
        assert r.status_code == 400

    def test_target_ngoai_danh_muc_bi_chan(self, api):
        c, _ = self._setup(api)
        bad = {**GOOD_ENVELOPE, "simulation_id": "khong.co.that"}
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Hỏng", "envelope": bad})
        assert r.status_code == 400

    def test_envelope_chua_phan_tich_xong_khong_giao_duoc(self, api):
        c, _ = self._setup(api)
        bad = {**GOOD_ENVELOPE, "status": "unsupported_to_verify"}
        r = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Hỏng", "envelope": bad})
        assert r.status_code == 400

    def test_giao_vien_KHONG_giao_duoc_cho_lop_khong_phai_cua_minh(self, api):
        c, _ = self._setup(api)
        other = new_client(api)
        make_teacher(other, email="thay@lop.test", name="Thầy Nam")
        r = other.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Chen ngang", "envelope": GOOD_ENVELOPE})
        assert r.status_code == 404

    def test_HOC_SINH_NGOAI_LOP_khong_thay_va_khong_mo_duoc_bai(self, api):
        """§36.2 + §38.5 — đoán đúng id cũng không mở được."""
        c, _ = self._setup(api)
        aid = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Cổng AND", "envelope": GOOD_ENVELOPE}).json()["id"]
        outsider = new_client(api)
        make_student(outsider, email="ngoai@lop.test", name="Ngoài")
        assert outsider.get("/api/assignments").json()["assignments"] == []
        assert outsider.get(f"/api/assignments/{aid}").status_code == 404
        assert outsider.post(f"/api/assignments/{aid}/progress",
                             json={"cursor": 1, "stepCount": 4}).status_code == 404

    def test_KHACH_khong_doc_duoc_bai(self, api):
        """§36.4"""
        c, _ = self._setup(api)
        aid = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Cổng AND", "envelope": GOOD_ENVELOPE}).json()["id"]
        guest = new_client(api)
        assert guest.get(f"/api/assignments/{aid}").status_code == 401
        assert guest.get("/api/assignments").status_code == 401

    def test_mo_bai_tra_ENVELOPE_DA_VALIDATE_khong_goi_LLM(self, api):
        """Ba mươi học sinh mở ra ĐÚNG một mô phỏng, không phải ba mươi cái."""
        c, s = self._setup(api)
        aid = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Cổng AND", "envelope": GOOD_ENVELOPE}).json()["id"]
        a = s.get(f"/api/assignments/{aid}").json()
        b = new_client(api)
        make_student(b, email="binh@lop.test", name="Bình")
        b.post("/api/classes/join", json={"code": c["joinCode"]})
        assert b.get(f"/api/assignments/{aid}").json()["envelope"] == a["envelope"]
        # Config đi qua cổng mà KHÔNG bị đổi — envelope tuyến ngữ nghĩa là
        # artifact đã biên dịch, không có bước chuẩn hoá nào được phép chạm vào.
        assert a["envelope"]["config"]["frames"] == GOOD_ENVELOPE["config"]["frames"]


# ── QUAN SÁT ─────────────────────────────────────────────────────────────────

class TestQuanSat:
    def _class_with_practice(self, api):
        make_teacher(api)
        c = make_class(api)
        aid = api.post("/api/assignments", json={
            "classroomId": c["id"], "title": "Cổng AND", "envelope": GOOD_ENVELOPE}).json()["id"]
        s = new_client(api)
        make_student(s)
        s.post("/api/classes/join", json={"code": c["joinCode"]})
        return c, aid, s

    def test_chua_bat_dau_la_mot_trang_thai_THAT(self, api):
        c, aid, _ = self._class_with_practice(api)
        rows = api.get(f"/api/classes/{c['id']}/observe").json()["rows"]
        assert len(rows) == 1
        assert rows[0]["status"] == "not_started" and rows[0]["cursor"] is None

    def test_hoc_sinh_bao_tien_do_thi_giao_vien_thay(self, api):
        c, aid, s = self._class_with_practice(api)
        s.post(f"/api/assignments/{aid}/progress", json={
            "cursor": 3, "stepCount": 8, "exploreOpen": True, "actionCount": 5})
        row = api.get(f"/api/classes/{c['id']}/observe").json()["rows"][0]
        assert row["status"] == "practicing"
        assert (row["cursor"], row["stepCount"]) == (3, 8)
        assert row["exploreOpen"] is True and row["actionCount"] == 5

    def test_con_so_bi_KEP_ve_mien_hop_le_chu_khong_tin_client(self, api):
        """Trình duyệt bị sửa gửi cursor 999999 thì bảng của giáo viên KHÔNG
        được hiện một con số mà timeline không có."""
        c, aid, s = self._class_with_practice(api)
        s.post(f"/api/assignments/{aid}/progress", json={
            "cursor": 999_999, "stepCount": 8, "actionCount": -5})
        row = api.get(f"/api/classes/{c['id']}/observe").json()["rows"][0]
        assert row["cursor"] == 8 and row["actionCount"] == 0

    def test_dem_chi_TANG_de_tai_lai_trang_khong_xoa_bang_chung(self, api):
        c, aid, s = self._class_with_practice(api)
        s.post(f"/api/assignments/{aid}/progress", json={"stepCount": 8, "actionCount": 9})
        s.post(f"/api/assignments/{aid}/progress", json={"stepCount": 8, "actionCount": 0})
        row = api.get(f"/api/classes/{c['id']}/observe").json()["rows"][0]
        assert row["actionCount"] == 9

    def test_GIAO_VIEN_KHAC_khong_quan_sat_duoc(self, api):
        """§36.3"""
        c, _, _ = self._class_with_practice(api)
        other = new_client(api)
        make_teacher(other, email="thay@lop.test", name="Thầy Nam")
        assert other.get(f"/api/classes/{c['id']}/observe").status_code == 403

    def test_HOC_SINH_khong_quan_sat_duoc_lop_cua_chinh_minh(self, api):
        """§36.2 — kể cả là thành viên."""
        c, _, s = self._class_with_practice(api)
        assert s.get(f"/api/classes/{c['id']}/observe").status_code == 403

    def test_KHACH_khong_quan_sat_duoc(self, api):
        c, _, _ = self._class_with_practice(api)
        assert new_client(api).get(f"/api/classes/{c['id']}/observe").status_code == 401

    def test_quan_sat_KHONG_ro_du_lieu_ngoai_lop(self, api):
        """§38.7 — bảng quan sát chỉ chứa bài CỦA LỚP NÀY.

        Học sinh cũng học ở một lớp khác của một giáo viên khác; không dòng nào
        của lớp kia được lọt sang.
        """
        c, aid, s = self._class_with_practice(api)
        s.post(f"/api/assignments/{aid}/progress", json={"cursor": 1, "stepCount": 8})

        other_teacher = new_client(api)
        make_teacher(other_teacher, email="thay@lop.test", name="Thầy Nam")
        c2 = make_class(other_teacher, name="11B2")
        aid2 = other_teacher.post("/api/assignments", json={
            "classroomId": c2["id"], "title": "BÍ MẬT LỚP KIA",
            "envelope": GOOD_ENVELOPE}).json()["id"]
        s.post("/api/classes/join", json={"code": c2["joinCode"]})
        s.post(f"/api/assignments/{aid2}/progress", json={"cursor": 7, "stepCount": 8})

        body = api.get(f"/api/classes/{c['id']}/observe").text
        assert "BÍ MẬT LỚP KIA" not in body
        rows = json.loads(body)["rows"]
        assert {r["assignmentId"] for r in rows} == {aid}

    def test_bang_quan_sat_KHONG_chua_truong_dung_sai(self, api):
        """Bất biến #27 — tầng lớp học không phán học sinh đúng hay chưa.
        Engine tất định là nơi duy nhất có quyền đó."""
        c, aid, s = self._class_with_practice(api)
        s.post(f"/api/assignments/{aid}/progress", json={
            "cursor": 8, "stepCount": 8, "commitmentCount": 3, "completed": True})
        body = api.get(f"/api/classes/{c['id']}/observe").text.lower()
        for banned in ["correct", "incorrect", "verdict", "score", "diem", "grade"]:
            assert banned not in body, banned

    def test_bang_quan_sat_KHONG_chua_anh_man_hinh_hay_DOM(self, api):
        """§38.8 — quan sát bằng trạng thái CÓ CẤU TRÚC, không phải luồng màn hình."""
        c, aid, s = self._class_with_practice(api)
        s.post(f"/api/assignments/{aid}/progress", json={"cursor": 2, "stepCount": 8})
        body = api.get(f"/api/classes/{c['id']}/observe").text.lower()
        for banned in ["screenshot", "<div", "outerhtml", "innerhtml", "data:image"]:
            assert banned not in body, banned
