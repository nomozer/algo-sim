# -*- coding: utf-8 -*-
"""Cổng TRƯỚC khi tiêu quota cho Phase 5 lần hai. **0 API call.**

Ba câu hỏi, và mỗi câu đều đã có một lần trả lời sai phải trả giá:

  §1 Prompt có nói hộ đáp án của tập DEV không?
     — Tìm thấy MỘT rò rỉ thật khi viết file này: `geometry_analyze.md` lấy
       *"biết rằng thể tích bằng 2/3"* làm ví dụ, mà `2/3` đúng là đáp án
       `geo_09`. Không cổng nào bắt được nó, và nó sẽ đi thẳng vào lượt đo.

  §2 Bộ ghi chi phí có làm đổi pipeline không?
     — Nếu có thì thứ đo được là *pipeline có bộ ghi*, không phải pipeline.

  §3 Artifact có đủ trường trên MỌI đường thoát không?
     — Artifact PHASE 5 thiếu `obligation_match` ở 4 bài trượt sớm, vì
       `return ra` trong `try` nhảy qua phần hậu xử lý. `tong_ket` dùng `.get()`
       nên che mất, và không ai biết cho tới khi đọc lại JSON bằng mắt.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

_BE = Path(__file__).resolve().parents[2]
_GOC = _BE.parent
_SKILLS = _BE / "app" / "ai" / "skills"
_DEV = _GOC / "docs" / "evaluation" / "geometry" / "dev" / "cases.json"
_R = _BE / "scripts" / "run_geometry_dev_evaluation.py"

_CASES = json.loads(_DEV.read_text(encoding="utf-8"))["cases"]
_PROMPTS = {p.name: p.read_text(encoding="utf-8")
            for p in _SKILLS.glob("geometry*.md")}


@pytest.fixture(scope="module")
def rn():
    spec = importlib.util.spec_from_file_location("run_geometry_dev", _R)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_geometry_dev"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def AU(rn):
    """`rn` là phụ thuộc THẬT, không phải trang trí: nạp runner mới đưa
    `backend/scripts` vào `sys.path`, và `api_usage_log` sống ở đó."""
    import api_usage_log

    return api_usage_log


# ══ §1. PROMPT KHÔNG ĐƯỢC NÓI HỘ ĐÁP ÁN ═══════════════════════════════════
def test_co_it_nhat_hai_prompt_hinh_hoc_de_quet():
    """Bảo hiểm cho chính §1: đổi tên file mà quên sửa glob thì mọi test dưới
    đây quét một tập RỖNG và xanh vô nghĩa."""
    assert set(_PROMPTS) == {"geometry_analyze.md", "geometry_program_generator.md"}


@pytest.mark.parametrize("ten", sorted(_PROMPTS))
def test_prompt_khong_chua_case_id(ten):
    lo = [c["case_id"] for c in _CASES if c["case_id"] in _PROMPTS[ten]]
    assert not lo, f"{ten} nhắc tới case DEV: {lo}"


@pytest.mark.parametrize("ten", sorted(_PROMPTS))
def test_prompt_khong_chep_de_bai_DEV(ten):
    """Cửa sổ 40 ký tự: đủ dài để không trùng ngẫu nhiên với văn phong SGK,
    đủ ngắn để bắt được một câu chép lại có sửa vài chữ."""
    t = _PROMPTS[ten]
    for c in _CASES:
        pt = c["problem_text"]
        trung = [pt[i:i + 40] for i in range(0, max(1, len(pt) - 40), 10)
                 if pt[i:i + 40] in t]
        assert not trung, f"{ten} chép đề {c['case_id']}: {trung}"


@pytest.mark.parametrize("ten", sorted(_PROMPTS))
def test_prompt_khong_chep_ghi_chu_giai_tay(ten):
    """`ghi_chu_kiem_tay` là LỜI GIẢI do custodian viết. Lọt vào prompt là đưa
    thẳng cách làm cho mô hình."""
    t = _PROMPTS[ten]
    for c in _CASES:
        g = c.get("ghi_chu_kiem_tay", "")
        trung = [g[i:i + 40] for i in range(0, max(1, len(g) - 40), 10)
                 if g[i:i + 40] in t]
        assert not trung, f"{ten} chép ghi chú {c['case_id']}: {trung}"


def _dap_an_phan_so() -> set[str]:
    """Đáp án DẠNG PHÂN SỐ của tập DEV — thứ đặc trưng nhất để dò rò rỉ.

    Chỉ lấy phân số, KHÔNG lấy số trần: `2` và `4` xuất hiện trong prompt như
    số đánh mục và như quy ước tỉ lệ, nên cấm chúng là dựng một guard kêu oan —
    và một guard kêu oan là một guard sẽ bị tắt. Cũng KHÔNG lấy chuỗi văn xuôi:
    `"điểm A"` khớp bên trong *"trung điểm AB"*, một dương tính giả thuần tuý.
    """
    ra: set[str] = set()
    for c in _CASES:
        for v in c["oracle_result"].values():
            if isinstance(v, str) and re.fullmatch(r"\d+/\d+", v.strip()):
                ra.add(v.strip())
    return ra


def test_tap_DEV_co_dap_an_phan_so_de_ma_do():
    """Nếu tập DEV không còn phân số nào thì test dưới đây xanh mà chưa đo gì."""
    assert _dap_an_phan_so(), "không còn đáp án phân số — sửa lại phép dò"


@pytest.mark.parametrize("ten", sorted(_PROMPTS))
def test_prompt_khong_chua_DAP_AN_phan_so_cua_DEV(ten):
    """RÒ RỈ THẬT ĐÃ BẮT ĐƯỢC Ở ĐÂY (2026-08-25).

    `geometry_analyze.md` viết *"biết rằng thể tích bằng 2/3"* làm ví dụ cho
    trường `params.value`. `2/3` là đáp án `geo_09` **và** `geo_10`. Ví dụ ấy
    nằm ngay cạnh câu dạy mô hình khi nào được điền đáp số — chỗ tệ nhất có thể
    đặt nó. Đã đổi sang `7/12`, một giá trị không bài DEV nào có.
    """
    lo = sorted(v for v in _dap_an_phan_so() if v in _PROMPTS[ten])
    assert not lo, (
        f"{ten} chứa đáp án phân số của tập DEV: {lo}. Đổi ví dụ sang một giá "
        f"trị không bài nào dùng."
    )


def test_moi_phan_so_trong_prompt_deu_KHONG_phai_dap_an():
    """Chiều ngược lại — quét mọi phân số CÓ trong prompt rồi đối chiếu.

    Cần cả hai chiều: test trên hỏi *"đáp án có lọt vào prompt không"*, test này
    hỏi *"ví dụ trong prompt có tình cờ là đáp án không"*. Một ví dụ mới viết
    thêm sau này sẽ bị chiều này bắt trước.
    """
    dap_an = _dap_an_phan_so()
    for ten, t in _PROMPTS.items():
        for ps in sorted(set(re.findall(r"\b\d+/\d+\b", t))):
            assert ps not in dap_an, f"{ten}: ví dụ {ps} trùng đáp án DEV"


def test_moi_DAI_LUONG_duoc_cham_deu_co_SO_trong_de():
    """Chặn một dạng rò rỉ TINH VI hơn: prompt đặt quy ước tỉ lệ mặc định
    (*"số đo không cho cụ thể thì lấy 1, hoặc 2 cho chiều cao"*), và quy ước ấy
    trùng đúng kích thước tập DEV dùng.

    Quy ước đó CHỈ vô hại khi mọi đại lượng được chấm đều có số nêu trong đề —
    khi ấy tỉ lệ đến từ đề chứ không từ prompt. Bài chỉ chấm quan hệ (đúng/sai)
    thì bất biến theo tỉ lệ nên không cần điều kiện này.

    Test sẽ ĐỎ nếu ai đó thêm một bài kiểu *"hình vuông ABCD, tính thể tích"*
    không nêu cạnh — bài ấy chấm được **chỉ vì** prompt đã chọn hộ tỉ lệ.
    """
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    thieu = []
    for c in _CASES:
        # Chỉ khoá theo nghĩa vụ: khoá văn xuôi (`so_canh_thiet_dien`,
        # `hinh_chieu_la`) là ghi chú cho người đọc, không dùng để chấm.
        dai_luong = [k for k, v in c["oracle_result"].items()
                     if k in OBLIGATION_KINDS and not isinstance(v, bool)]
        if dai_luong and not re.search(r"\d", c["problem_text"]):
            thieu.append((c["case_id"], dai_luong))
    assert not thieu, (
        f"bài chấm ĐẠI LƯỢNG mà đề không nêu số nào: {thieu} — tỉ lệ khi ấy "
        f"đến từ quy ước trong prompt, tức prompt đang chấm hộ."
    )


# ══ §2. BỘ GHI KHÔNG ĐƯỢC ĐỔI PIPELINE ════════════════════════════════════
def test_boc_tra_ve_DUNG_gia_tri_goc(AU):
    ghi = AU.GhiNhanApi()

    async def goc(*a, **kw):
        return '{"ok": true}'

    assert asyncio.run(ghi.boc(goc)()) == '{"ok": true}'
    assert len(ghi.luot) == 1


def test_boc_truyen_nguyen_THAM_SO(AU):
    """Bọc mà nuốt mất một tham số thì pipeline chạy bằng cấu hình khác — và
    lượt đo nói về cấu hình đó chứ không nói về sản phẩm."""
    ghi = AU.GhiNhanApi()
    thay: dict = {}

    async def goc(*a, **kw):
        thay["a"], thay["kw"] = a, kw
        return "x"

    asyncio.run(ghi.boc(goc)("key", "skill", "prompt", {"s": 1}, 0.1, extra=9))
    assert thay["a"] == ("key", "skill", "prompt", {"s": 1}, 0.1)
    assert thay["kw"] == {"extra": 9}


def test_boc_KHONG_nuot_ngoai_le_va_VAN_ghi(AU):
    """Lượt hỏng vẫn tốn tiền và vẫn tốn giờ. Không ghi nó là báo thiếu chi phí
    đúng ở những lượt đắt nhất (timeout, 429)."""
    ghi = AU.GhiNhanApi()

    async def goc(*a, **kw):
        raise RuntimeError("429 quá tải")

    with pytest.raises(RuntimeError, match="429"):
        asyncio.run(ghi.boc(goc)())
    assert len(ghi.luot) == 1
    assert ghi.luot[0]["raw"] is None and "429" in ghi.luot[0]["loi"]


def test_boc_ghi_dung_STAGE(AU):
    from app.ai.telemetry import stage_scope

    ghi = AU.GhiNhanApi()

    async def goc(*a, **kw):
        return "x"

    async def chay():
        with stage_scope("semantic_program"):
            await ghi.boc(goc)()

    asyncio.run(chay())
    assert ghi.luot[0]["stage"] == "semantic_program"


def test_tho_cuoi_tra_ve_LAN_CUOI_khong_phai_lan_dau(AU):
    """Vòng sửa chạy tới 3 lượt. Thứ bị từ chối sau cùng mới là thứ cần soi."""
    from app.ai.telemetry import stage_scope

    ghi = AU.GhiNhanApi()
    dap = iter(['{"lan":1}', '{"lan":2}', '{"lan":3}'])

    async def goc(*a, **kw):
        return next(dap)

    async def chay():
        with stage_scope("semantic_program"):
            for _ in range(3):
                await ghi.boc(goc)()

    asyncio.run(chay())
    assert ghi.tho_cuoi("semantic_program") == '{"lan":3}'
    assert ghi.tho_cuoi("semantic_analyze") is None


def test_tho_bi_CAT_de_artifact_con_doc_duoc(AU):
    ghi = AU.GhiNhanApi()

    async def goc(*a, **kw):
        return "x" * 50_000

    asyncio.run(ghi.boc(goc)())
    assert len(ghi.luot[0]["raw"]) == AU.GhiNhanApi.GIOI_HAN_THO


def test_runner_KHOI_PHUC_call_gemini_sau_moi_case(rn, monkeypatch):
    """Bỏ sót `finally` thì case thứ hai chạy qua một `call_gemini` bọc chồng —
    và mỗi lớp bọc lại đếm thêm một lần, nên chi phí báo cao gấp bội."""
    from app.ai import pipeline

    goc = pipeline.call_gemini

    async def _analyze(*a, **kw):
        return None, "hỏng"

    monkeypatch.setattr(pipeline, "stage_semantic_analyze", _analyze)
    for _ in range(3):
        asyncio.run(rn.chay_mot_case(_CASES[0], "khoa-gia"))
        assert pipeline.call_gemini is goc, "call_gemini chưa được trả lại"


# ══ §2b. ƯỚC TÍNH CHI PHÍ — tái lập được hoặc không có ════════════════════
def test_model_ngoai_bang_gia_thi_KHONG_UOC_TINH_DUOC(AU):
    """"Không biết giá" và "miễn phí" là hai điều khác hẳn nhau. Trả `0.0` cho
    model lạ là bịa ra một con số rồi để người khác trích nó."""
    kq = AU._tien("model-chua-tung-co", {"prompt_tokens": 10_000})
    assert kq["uoc_tinh_duoc"] is False
    assert "usd" not in kq


def test_uoc_tinh_la_MOT_PHEP_TINH_tai_lap_duoc(AU):
    """Artifact phải mang ĐƠN GIÁ + NGÀY + NGUỒN, nếu không con số USD nằm
    trong `docs/evaluation/` sẽ không ai kiểm lại được nó tính theo giá nào."""
    tok = {"prompt_tokens": 1_000_000, "candidates_tokens": 1_000_000}
    kq = AU._tien("gemini-2.5-flash", tok)
    gia = AU.BANG_GIA_USD["gemini-2.5-flash"]
    assert kq["usd"] == pytest.approx(gia["input"] + gia["output"])
    for k in ("don_gia_usd_moi_trieu", "ngay_tra_gia", "nguon_gia", "khai"):
        assert k in kq


def test_thoughts_tinh_theo_gia_OUTPUT(AU):
    """Token suy luận của model thinking được tính như token sinh ra. Bỏ quên
    nó là báo thiếu ở đúng phần đắt nhất."""
    a = AU._tien("gemini-2.5-flash", {"candidates_tokens": 2_000_000})
    b = AU._tien("gemini-2.5-flash",
                 {"candidates_tokens": 1_000_000, "thoughts_tokens": 1_000_000})
    assert a["usd"] == b["usd"]


def test_cached_tinh_DAY_GIA_input_va_khai_ro_la_chan_tren(AU):
    kq = AU._tien("gemini-2.5-flash", {"cached_content_tokens": 1_000_000})
    assert kq["usd"] == pytest.approx(AU.BANG_GIA_USD["gemini-2.5-flash"]["input"])
    assert "CHẶN TRÊN" in kq["khai"]


def test_khong_co_budget_thi_KHONG_DO_DUOC_chu_khong_phai_ZERO(AU):
    kq = AU.bao_cao("gemini-2.5-flash", None)
    assert kq["do_duoc"] is False and "luot_logic" not in kq


def test_bao_cao_gom_du_BON_truc_yeu_cau(AU):
    """model · api_calls · tokens · latency · cost — bốn trục của mục 2."""
    from app.ai import telemetry

    class _B:
        logical_calls, http_requests, retry_requests, transient_hits = 6, 8, 2, 1
        max_logical_calls, max_api_calls = 60, 80

    telemetry.reset_usage()
    telemetry.record_usage("semantic_program", {
        "promptTokenCount": 100, "candidatesTokenCount": 50, "totalTokenCount": 150,
    })
    ghi = AU.GhiNhanApi()
    ghi.luot.append({"stage": "semantic_program", "giay": 1.5, "loi": None, "raw": "x"})

    kq = AU.bao_cao("gemini-2.5-flash", _B(), ghi)
    assert kq["model"] == "gemini-2.5-flash"
    assert kq["luot_logic"] == 6 and kq["request_http"] == 8
    assert kq["tong_token"] == 150
    assert kq["token_gop"]["prompt_tokens"] == 100
    assert kq["do_tre"]["tong_giay"] == 1.5
    assert kq["uoc_tinh_chi_phi"]["uoc_tinh_duoc"] is True
    telemetry.reset_usage()


# ══ §3. HÌNH DẠNG ARTIFACT ỔN ĐỊNH TRÊN MỌI ĐƯỜNG THOÁT ═══════════════════
#: Trường mà bộ chấm downstream đọc. Thiếu MỘT là nó phải phòng thủ từng khoá,
#: và phòng thủ từng khoá là cách một bài trượt trở thành một bài "không đo".
KHOA_BAT_BUOC = (
    "case_id", "problem", "expected_obligations",
    "generated_program", "generated_raw", "obligations_declared",
    "schema_pass", "semantic_pass", "executable", "oracle_pass",
    "obligation_match", "failure_layer", "failure_code", "failure_reason",
    "do_tre",
)


def _chay(rn, monkeypatch, analyze, program=None):
    from app.ai import pipeline

    monkeypatch.setattr(pipeline, "stage_semantic_analyze", analyze)
    if program is not None:
        monkeypatch.setattr(pipeline, "stage_semantic_program", program)
    return asyncio.run(rn.chay_mot_case(_CASES[8], "khoa-gia"))  # geo_09


def test_artifact_du_khoa_khi_ANALYZE_hong(rn, monkeypatch):
    async def a(*x, **k):
        return None, "SEMANTIC_ANALYZE_INVALID: JSON không parse được"

    ra = _chay(rn, monkeypatch, a)
    thieu = [k for k in KHOA_BAT_BUOC if k not in ra]
    assert not thieu, f"thiếu {thieu} khi analyze hỏng"
    assert ra["failure_layer"] == 0


def test_artifact_du_khoa_khi_SCHEMA_hong(rn, monkeypatch):
    """ĐÂY là đường đã hỏng ở PHASE 5: 4/10 bài đi lối này và mất
    `obligation_match`."""
    from app.simulation.semantic_program.request_contract import RequestContract

    async def a(*x, **k):
        return RequestContract(), None

    async def p(*x, **k):
        return None, "1 validation error for SemanticProgramSpec\ntype: volume"

    ra = _chay(rn, monkeypatch, a, p)
    thieu = [k for k in KHOA_BAT_BUOC if k not in ra]
    assert not thieu, f"thiếu {thieu} khi schema hỏng"
    assert ra["obligation_match"] is not None
    assert ra["schema_pass"] is False and ra["failure_layer"] == 2


def test_artifact_du_khoa_khi_NEM_NGOAI_LE(rn, monkeypatch):
    async def a(*x, **k):
        raise ValueError("mạng đứt")

    ra = _chay(rn, monkeypatch, a)
    thieu = [k for k in KHOA_BAT_BUOC if k not in ra]
    assert not thieu, f"thiếu {thieu} khi ném ngoại lệ"
    assert ra["failure_layer"] == 1 and ra["failure_code"] == "ValueError"


def test_artifact_du_khoa_khi_DI_TRON_DUONG(rn, monkeypatch):
    """Dùng lại đúng chương trình `geo_09` viết tay của `test_geometry_wave2` —
    một nguồn sự thật cho "chương trình hình học đúng trông thế nào"."""
    from test_geometry_wave2 import _chuong_trinh_geo_09, _hop_dong_geo_09

    from app.simulation.semantic_program.contract import SemanticProgramSpec

    async def a(*x, **k):
        return _hop_dong_geo_09(), None

    async def p(*x, **k):
        return SemanticProgramSpec.model_validate(_chuong_trinh_geo_09()), None

    ra = _chay(rn, monkeypatch, a, p)
    thieu = [k for k in KHOA_BAT_BUOC if k not in ra]
    assert not thieu, f"thiếu {thieu} khi đi trọn đường"
    assert ra["schema_pass"] and ra["semantic_pass"] and ra["executable"]
    assert ra["generated_program"] is not None
    assert ra["oracle"]["verdict"] == "PASS", ra["oracle"]
    assert ra["oracle_pass"] is True


def test_artifact_GIU_DUOC_dau_ra_tho_khi_truot_schema(rn, monkeypatch):
    """PHASE 5 phải dựng lại *"mô hình bịa construct_plane"* từ chuỗi lỗi
    Pydantic — đọc dấu vết thay vì đọc vật chứng. Bốn bài trượt G1 và không bài
    nào để lại thứ mô hình thật sự viết."""
    from app.ai import pipeline
    from app.simulation.semantic_program.request_contract import RequestContract

    async def a(*x, **k):
        return RequestContract(), None

    from app.ai.telemetry import stage_scope

    async def gia_call(*x, **k):
        return '{"memory_declarations": [{"name": "V", "type": "volume"}]}'

    async def p(*x, **k):
        # `stage_scope` là thứ gắn NHÃN STAGE cho lượt gọi, và bộ ghi tra theo
        # nhãn ấy. Giả lập thiếu nó thì lượt rơi vào stage "unknown" và
        # `tho_cuoi("semantic_program")` trả None — đúng như sản phẩm sẽ hành xử
        # nếu ai đó gỡ `stage_scope` khỏi pipeline.
        with stage_scope("semantic_program"):
            await pipeline.call_gemini("k", "s", "p", {}, 0.1)
        return None, "1 validation error for SemanticProgramSpec"

    monkeypatch.setattr(pipeline, "call_gemini", gia_call)
    monkeypatch.setattr(pipeline, "stage_semantic_program", p)
    ra = _chay(rn, monkeypatch, a)
    assert ra["generated_raw"] is not None
    assert '"type": "volume"' in ra["generated_raw"]


# ══ §4. ARTIFACT PHẢI TỰ NEO VÀO MỘT BẢN MÃ ══════════════════════════════
def test_artifact_tu_khai_COMMIT_va_TRANG_THAI_BAN(rn):
    """Không có khối này thì điểm số không buộc được vào commit nào — người đọc
    sau ba tháng không tái lập được, và không biết cây có bẩn lúc chạy không."""
    neo = rn.neo_kho_ma()
    for k in ("commit", "commit_ngan", "nhanh", "cache_version",
              "measured_system_hash", "measured_system_so_file",
              "dirty_toan_kho", "dirty_he_duoc_do",
              "sach_toan_kho", "sach_he_duoc_do"):
        assert k in neo, f"thiếu {k}"
    assert len(neo["commit"]) == 40
    assert re.fullmatch(r"[0-9a-f]{64}", neo["measured_system_hash"])
    assert neo["measured_system_so_file"] > 100
    assert neo["cache_version"] == "40"


def test_hai_pham_vi_ban_KHONG_bi_gop_lam_mot(rn):
    """`bẩn` có hai nghĩa không trùng nhau, và gộp chúng là mất thông tin quyết
    định: cây bẩn NGOÀI hệ được đo vẫn tái lập được, bẩn TRONG thì không.

    Runner cố ý không chọn phe — nó ghi cả hai và để người đọc phán.
    """
    neo = rn.neo_kho_ma()
    assert set(neo["dirty_he_duoc_do"]) <= set(neo["dirty_toan_kho"])
    assert neo["sach_he_duoc_do"] == (not neo["dirty_he_duoc_do"])
    assert neo["sach_toan_kho"] == (not neo["dirty_toan_kho"])
    # Sạch toàn kho thì tất yếu sạch hệ được đo; chiều ngược lại KHÔNG đúng.
    if neo["sach_toan_kho"]:
        assert neo["sach_he_duoc_do"]


def test_neo_dung_DUNG_pham_vi_cua_freeze(rn):
    """Runner không được tự chép một danh sách đường dẫn thứ hai: hai bản rời
    nhau sẽ lệch, và lệch câm."""
    import inspect

    import freeze_evaluation_candidate as FZ

    src = inspect.getsource(rn.neo_kho_ma)
    assert "FZ.MEASURED_SYSTEM_PATHS" in src
    assert "backend/app" in FZ.MEASURED_SYSTEM_PATHS


def test_measured_system_hash_KHONG_doi_theo_file_ngoai_pham_vi(rn, tmp_path):
    """Bằng chứng cho câu khẳng định ở `neo.khai`. Không có test này thì đó chỉ
    là một lời tuyên bố trong JSON."""
    import freeze_evaluation_candidate as FZ

    truoc, _ = FZ.measured_system_hash()
    ngoai = _GOC / "docs" / "_tam_kiem_pham_vi.md"
    ngoai.write_text("file rác ngoài hệ được đo\n", encoding="utf-8")
    try:
        sau, _ = FZ.measured_system_hash()
    finally:
        ngoai.unlink()
    assert truoc == sau, "file ngoài MEASURED_SYSTEM_PATHS làm đổi hash hệ đo"


def test_tong_ket_du_khoa_va_co_CHI_PHI(rn):
    class _B:
        logical_calls, http_requests, retry_requests, transient_hits = 3, 3, 0, 0
        max_logical_calls, max_api_calls = 60, 80

    bao = rn.tong_ket([], 10, None, "gemini-2.5-flash", _B())
    for k in ("G1_schema", "G2_semantic", "A_executable", "O_oracle",
              "obligation_match", "phan_bo_that_bai", "N", "hoan_tat",
              "chi_phi", "model"):
        assert k in bao, f"thiếu {k}"
    assert bao["chi_phi"]["do_duoc"] is True
    assert bao["chi_phi"]["uoc_tinh_chi_phi"]["uoc_tinh_duoc"] is True
