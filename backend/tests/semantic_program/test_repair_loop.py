# -*- coding: utf-8 -*-
"""VÒNG SỬA của `stage_semantic_program` — chứng minh nó THẬT SỰ chạy.

VÌ SAO FILE NÀY TỒN TẠI: `MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3` và vòng lặp có
trong mã từ `d6b7b30`, nhưng **không test nào chứng minh nó quay lần thứ hai**.
Sáu test ở `test_stage_synthesis.py` đều là một-lượt: hợp lệ → trả spec, hỏng →
trả lỗi. Cả hai nhánh ấy xanh y hệt nhau dù vòng lặp có chạy hay `range()` bị
đổi thành `range(1)`.

Đây đúng loại lỗ đã cắn kho này một lần: `stage_semantic_program` từng **không
có một ai gọi** trong khi mọi unit test đều xanh — *test xanh không chứng minh
đường orchestration tồn tại*. Lần đó phát hiện được là nhờ đọc mã, không nhờ CI.

Rủi ro cụ thể lúc này: lượt SEALED #1 đo được **37/37 case gọi đúng 1 lượt**.
Ta biết lý do là vòng sửa chưa ra đời lúc ấy (`d6b7b30` đổ xuống 6,5 giờ SAU
lượt đo) — nhưng ta biết bằng **git log**, không bằng test. Nếu vòng lặp hỏng
lặng lẽ thì lượt #2 sẽ tiêu 520 lượt LLM để phát hiện lại một lỗi tất định, và
`test_mocked_production_e2e.py` đã ghi rõ đó là thứ đã xảy ra **ba lượt liên
tiếp** trong wave này.

Vòng sửa cũng là cơ chế được đo độc lập bên ngoài: ALGOGEN (arXiv 2605.12159)
báo cáo *"up to 3 error-guided repair attempts"* nâng Pass@1 từ 91,0 % lên
99,5 % — cùng hằng số, cùng loại phản hồi.

0 API call: thay `call_gemini` ở biên module, đúng khuôn `test_stage_synthesis`.
"""
from __future__ import annotations

import asyncio
import copy
import json

from app.ai import pipeline
from app.ai.pipeline import MAX_SEMANTIC_PROGRAM_ATTEMPTS

# Chương trình hợp lệ tối thiểu — dùng lại hình dạng đã được
# `test_stage_synthesis.py` chứng minh là qua được validator.
_HOP_LE: dict = {
    "spec_version": "1.0",
    "title": "Tìm giá trị lớn nhất",
    "description": "Quét dãy, giữ lại giá trị lớn nhất đã gặp.",
    "pedagogical_intent": "Thấy biến tích luỹ đổi giá trị qua từng bước.",
    "memory_declarations": [
        {"name": "a", "type": "array", "element_type": "int", "initial_value": [3, 9, 2]},
        {"name": "m", "type": "int", "initial_value": 0},
    ],
    "statements": [
        {
            "kind": "assign",
            "target_var": "m",
            "expr": {"kind": "index", "container": "a", "index": {"kind": "literal", "value": 0}},
        }
    ],
    "visual_bindings": {
        "containers": [{"semantic_id": "a", "primitive": "array_strip", "label": "Dãy"}],
        "pointers": [],
        "value_boxes": [{"box_id": "box_m", "var_ref": "m", "label": "Lớn nhất"}],
    },
}


def _sai_hop_dong() -> str:
    """JSON đúng cú pháp nhưng SAI hợp đồng — `push` vào container chưa khai.

    Hai cái bẫy khi chọn payload này, cả hai đều làm test xanh vì lý do sai:

    (1) **Không dùng bốn lớp đã có biên chuẩn hoá.** `spec_version` sai kiểu,
        `container` viết dạng `{"kind":"var"}`, `step` bọc literal, biến bool
        làm điều kiện — cả bốn nay được GỘP chứ không bị từ chối, nên chúng
        không còn kích hoạt được vòng sửa.
    (2) **Không dùng thứ validator thật ra vẫn cho qua.** Đã thử: `statements`
        rỗng → `ok=True`; gán vào biến chưa khai → `ok=True`; `value_box` trỏ
        biến lạ → `ok=True`. Ba cái đó tưởng hỏng mà không hỏng.

    `push` vào container chưa khai thì validator từ chối dứt khoát, kèm thông
    báo nêu đúng tên — nên nó cũng là mẫu tốt để kiểm lỗi có được gửi ngược.
    """
    xau = copy.deepcopy(_HOP_LE)
    xau["statements"] = [
        {"kind": "push", "container": "KHO_KHONG_TON_TAI",
         "val": {"kind": "literal", "value": 1}}
    ]
    return json.dumps(xau, ensure_ascii=False)


def _json_cut() -> str:
    """Đầu ra bị cắt giữa chừng — Flash lặp token tới `MAX_TOKENS`.

    Không phải ca giả tưởng: hai case của SEALED #1 hỏng đúng kiểu này.
    """
    return '{"spec_version": "1.0", "title": "Tìm ma'


class _GhiLuot:
    """Thay `call_gemini`, phát lần lượt các đáp án và ghi lại prompt từng lượt."""

    def __init__(self, monkeypatch, *dap_an: str):
        self.dap_an = list(dap_an)
        self.prompts: list[str] = []
        self.so_lan = 0

        async def fake(api_key, system_prompt, user_text,
                       response_schema=None, temperature=0.2, image=None):
            self.prompts.append(user_text)
            i = self.so_lan
            self.so_lan += 1
            # Hết đáp án thì lặp lại cái cuối — để test "dừng ở trần" không phụ
            # thuộc vào việc ta đoán đúng số lượt.
            return self.dap_an[i] if i < len(self.dap_an) else self.dap_an[-1]

        monkeypatch.setattr(pipeline, "call_gemini", fake)


class _Thu:
    """Observer thụ động — chỉ ghi, không can thiệp."""

    def __init__(self) -> None:
        self.su_kien: list[tuple[str, dict]] = []

    def emit(self, event_type: str, data: dict) -> None:
        self.su_kien.append((event_type, data))


def _chay(g: _GhiLuot | None = None, observer=None):
    return asyncio.run(
        pipeline.stage_semantic_program("Tìm max của 3, 9, 2", {}, "k", observer=observer)
    )


# ── 1. Vòng lặp có quay thật không ─────────────────────────────────────────
def test_luot_1_hong_luot_2_sua_duoc_thi_TRA_VE_SPEC(monkeypatch):
    """Đây là khẳng định trung tâm: hỏng KHÔNG còn là kết thúc."""
    g = _GhiLuot(monkeypatch, _sai_hop_dong(), json.dumps(_HOP_LE, ensure_ascii=False))
    spec, err = _chay(g)
    assert err is None, err
    assert spec is not None and spec.title == "Tìm giá trị lớn nhất"
    assert g.so_lan == 2, f"phải gọi đúng 2 lượt, gọi {g.so_lan}"


def test_thanh_cong_ngay_luot_1_thi_KHONG_goi_them(monkeypatch):
    """Chặn hồi quy ngược: vòng sửa không được biến mọi ca thành 3 lượt."""
    g = _GhiLuot(monkeypatch, json.dumps(_HOP_LE, ensure_ascii=False))
    spec, err = _chay(g)
    assert err is None and spec is not None
    assert g.so_lan == 1, f"chỉ được gọi 1 lượt, gọi {g.so_lan}"


def test_json_cut_cung_kich_hoat_vong_sua(monkeypatch):
    """Lỗi parse là đường sống, không phải phòng thủ thừa (2 ca ở SEALED #1)."""
    g = _GhiLuot(monkeypatch, _json_cut(), json.dumps(_HOP_LE, ensure_ascii=False))
    spec, err = _chay(g)
    assert err is None, err
    assert spec is not None
    assert g.so_lan == 2


# ── 2. Lỗi có ĐƯỢC GỬI NGƯỢC không, hay chỉ thử lại mù ─────────────────────
def test_loi_validator_di_vao_prompt_luot_sau(monkeypatch):
    """Thử lại mù ≠ vòng sửa. Nghiên cứu về self-repair chỉ ra grounded
    feedback là ĐIỀU KIỆN để sửa có tác dụng — nên phải kiểm lỗi thật sự tới nơi.
    """
    g = _GhiLuot(monkeypatch, _sai_hop_dong(), json.dumps(_HOP_LE, ensure_ascii=False))
    _chay(g)
    assert len(g.prompts) == 2
    assert "bị từ chối vì" in g.prompts[1]
    # Không chỉ là câu dẫn — nội dung lỗi thật phải có mặt.
    assert g.prompts[1] != g.prompts[0]
    assert len(g.prompts[1]) > len(g.prompts[0])


def test_prompt_luot_sau_van_giu_de_bai_va_the_van_pham(monkeypatch):
    """Gửi lỗi mà đánh rơi ngữ cảnh thì lượt 2 sửa trong bóng tối.

    Prompt được dựng lại từ `base`, nên đề bài và thẻ văn phạm phải còn nguyên.
    """
    g = _GhiLuot(monkeypatch, _sai_hop_dong(), json.dumps(_HOP_LE, ensure_ascii=False))
    _chay(g)
    assert len(g.prompts) >= 2, "vòng sửa không quay — không có prompt lượt 2 để soi"
    dau, sau = g.prompts[0], g.prompts[1]
    assert "Tìm max của 3, 9, 2" in sau, "đề bài bị đánh rơi ở lượt sửa"
    # Thẻ văn phạm là phần dài nhất của prompt đầu; lấy một mốc ổn định trong đó.
    assert "spec_version" in dau and "spec_version" in sau, \
        "thẻ văn phạm bị đánh rơi ở lượt sửa — mô hình sẽ tự đặt lại tên trường"


def test_khong_goi_y_cach_sua(monkeypatch):
    """R0: gửi lỗi thì được, mách nước thì thành ta viết chương trình hộ.

    ─── ĐIỀU ĐỔI 2026-08-31, VÀ ĐIỀU KHÔNG ĐỔI ─────────────────────────────

    Bản cũ đo bằng SỐ DÒNG (`< 6`) — một biến thay cho ý *"phần thêm vào không
    phình"*. Nay prompt sửa gửi kèm **chính chương trình vừa hỏng**, nên số
    dòng tăng, và tăng có chủ đích: không có nó thì câu *"sửa đúng chỗ đó"* là
    lệnh mô hình KHÔNG THỂ THEO — nó không có chương trình cũ trong ngữ cảnh,
    nên sinh lại từ đầu rồi vấp một lỗi KHÁC. Đo được ở cả bốn ca probe: lượt 0
    hỏng vì `construct_point`+toạ độ, lượt 1 hỏng vì `angle_cos` trên `line3`.

    Điều KHÔNG đổi, và là thứ test này thật sự canh: phần thêm vào chỉ được
    chứa **lỗi là gì** và **chương trình cũ**. Không một chữ nào mách cách sửa.
    """
    g = _GhiLuot(monkeypatch, _sai_hop_dong(), json.dumps(_HOP_LE, ensure_ascii=False))
    _chay(g)
    assert len(g.prompts) >= 2, "vòng sửa không quay — không có prompt lượt 2 để soi"
    them = g.prompts[1][len(g.prompts[0]):]
    assert "Hãy sửa ĐÚNG chỗ đó và giữ nguyên phần còn lại." in them
    assert "Chương trình bạn vừa viết" in them, "lượt sửa không có gì để sửa"

    # KHÔNG MÁCH NƯỚC. Danh sách này là chỗ luật sống, thay cho phép đếm dòng:
    # đếm dòng chỉ là một biến thay, và nó vỡ ngay khi phần thêm vào đổi hình.
    for cam in ["thay vì", "nên dùng", "ví dụ:", "gợi ý", "thử dùng"]:
        assert cam not in them.lower(), f"prompt sửa mách nước: {cam!r}"

    # Văn xuôi TA thêm vẫn phải ngắn — đo riêng nó, không đo chương trình mà
    # mô hình đã tự viết.
    # Bóc đúng khối chương trình ra, không cố dựng lại payload: đo văn xuôi mà
    # TA viết, chứ không đo thứ mô hình viết.
    dau = them.index("Chương trình bạn vừa viết:")
    cuoi = them.index("Nó bị từ chối vì:")
    van_xuoi = them[:dau] + them[cuoi:]
    assert len(van_xuoi) < 400, f"văn xuôi ta thêm phình ra: {van_xuoi[:200]!r}"


# ── 3. Trần — ngân sách 520 lượt của lượt #2 DẪN TỪ hằng số này ────────────
def test_dung_dung_o_tran_khong_goi_qua(monkeypatch):
    """Vượt trần là vỡ ngân sách giữa lượt đo chính thức, không phải phiền nhỏ."""
    g = _GhiLuot(monkeypatch, _sai_hop_dong())
    spec, err = _chay(g)
    assert spec is None and err is not None
    assert g.so_lan == MAX_SEMANTIC_PROGRAM_ATTEMPTS, (
        f"gọi {g.so_lan} lượt, trần là {MAX_SEMANTIC_PROGRAM_ATTEMPTS}. "
        "Ngân sách 520 của RUN2_PROTOCOL §3 dẫn từ hằng số này (13 × 40)."
    )


def test_hong_het_thi_bao_loi_cua_luot_CUOI(monkeypatch):
    """`loi_cuoi` phải là lỗi mới nhất — báo lỗi lượt đầu là chẩn đoán sai chỗ."""
    g = _GhiLuot(monkeypatch, _json_cut(), _json_cut(), _sai_hop_dong())
    spec, err = _chay(g)
    assert spec is None
    assert err is not None and err.startswith("SEMANTIC_PROGRAM_INVALID:")
    assert "JSON không parse được" not in err, \
        "báo lỗi parse của lượt 1 trong khi lượt 3 hỏng vì hợp đồng"


# ── 4. Quan trắc — mỗi lượt hỏng phải để lại dấu ───────────────────────────
def test_moi_luot_hong_phat_mot_su_kien_danh_so(monkeypatch):
    """Không có sự kiện thì runner không đếm được vòng sửa đã chạy bao nhiêu —
    và ta lại rơi vào đúng tình trạng của lượt #1: chỉ biết bằng git log."""
    g = _GhiLuot(monkeypatch, _sai_hop_dong(), _sai_hop_dong(), _sai_hop_dong())
    thu = _Thu()
    _chay(g, observer=thu)
    lan = [d for t, d in thu.su_kien if t == "semantic_program_attempt"]
    assert len(lan) == MAX_SEMANTIC_PROGRAM_ATTEMPTS
    assert [d["n"] for d in lan] == list(range(MAX_SEMANTIC_PROGRAM_ATTEMPTS))
    assert all(d["ok"] is False for d in lan)
    assert all(d["message"] for d in lan), "sự kiện không mang nội dung lỗi"


def test_luot_thanh_cong_KHONG_phat_su_kien_hong(monkeypatch):
    g = _GhiLuot(monkeypatch, json.dumps(_HOP_LE, ensure_ascii=False))
    thu = _Thu()
    _chay(g, observer=thu)
    assert [t for t, _ in thu.su_kien if t == "semantic_program_attempt"] == []


def test_observer_None_khong_lam_vo_gi(monkeypatch):
    """Production chạy không observer — đường đó phải y hệt."""
    g = _GhiLuot(monkeypatch, _sai_hop_dong(), json.dumps(_HOP_LE, ensure_ascii=False))
    spec, err = _chay(g, observer=None)
    assert err is None and spec is not None
