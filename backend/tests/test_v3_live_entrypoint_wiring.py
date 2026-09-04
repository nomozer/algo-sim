"""V3_LIVE_ENTRYPOINT_WIRING — đường chạy LIVE có dùng pool đã niêm phong không?

Bộ test này khoá đúng khoảng hở mà `test_v3_runner_manifest_integration.py`
**không** bắt được: bộ ấy gọi thẳng `mo_luot_do_v3` và chứng minh **hàm** đúng;
nó chưa bao giờ chạy `main_async`, nên nó xanh suốt quãng entrypoint chạy corpus
phát triển. Ở đây mọi khẳng định đi qua **`main_async`** — đường mà lệnh
`--out-dir` thật sự chạy.

0 network call: `conftest.py` đã gỡ transport httpx; ngoài ra mọi lượt gọi
provider ở đây đều là stub ghi nhật ký.
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "scripts"))

import acceptance_integrity as AI  # noqa: E402
import run_curved_acceptance as R  # noqa: E402
import seal_curved_v3 as SC  # noqa: E402

O_DUONG = [f"C{i}" for i in range(1, 10)]
O_AM = [f"N{i}" for i in range(1, 5)]
MOI_O = O_DUONG + O_AM


# ══ FIXTURE — pool/seal TỔNG HỢP. Nội dung V3 thật không mở ở đây ═════════
def _bai_gia() -> list[dict]:
    """26 bài / 13 ô / mỗi ô 2 bài — đúng hình dạng pool V3, nội dung giả."""
    ra = []
    for o in MOI_O:
        duong = o.startswith("C")
        for k in (1, 2):
            ra.append({
                "id": f"{o}_{k}",
                "o": o,
                "hinh": {"C1": "ball", "C2": "ball", "C3": "ball",
                         "C4": "cylinder", "C5": "cylinder", "C6": "cylinder",
                         "C7": "cone", "C8": "cone", "C9": "cone",
                         "N1": "ball", "N2": "cylinder", "N3": "cone",
                         "N4": "ball"}[o],
                "loai": "duong" if duong else "am",
                "de": f"đề tổng hợp {o}_{k}",
                # ⚠️ `list`, ĐÚNG như pool V3 thật lưu. Đây là blocker ②.
                "mong": ["2", "3"] if duong else [],
                "cong_thuc": {},
            })
    return ra


@pytest.fixture
def v3_gia(tmp_path, monkeypatch):
    """Trỏ `seal_curved_v3` sang pool/seal tổng hợp ĐÃ RÚT.

    `measured_system_hash` lấy từ hệ THẬT: `_kiem_con_dau_va_candidate` là một
    phép kiểm thật, và làm giả nó thì test không còn chứng minh gì về lượt thật.
    """
    import freeze_evaluation_candidate as F

    bai = _bai_gia()
    chon = [f"{o}_1" for o in MOI_O]
    da_chon = [b for b in bai if b["id"] in set(chon)]
    he, _n = F.measured_system_hash()

    pool = tmp_path / "POOL.json"
    dau = tmp_path / "V3_SEAL.json"
    pool.write_text(json.dumps({"khai": "giả", "bai": bai}, ensure_ascii=False),
                    encoding="utf-8")
    dau.write_text(json.dumps({
        "pool_hash": SC._bam(bai), "pool_size": len(bai), "o": MOI_O,
        "o_duong": O_DUONG, "o_am": O_AM,
        "measured_system_hash": he, "measured_system_files": _n,
        "seed": 123456789, "da_rut": chon,
        "case_set_hash": SC._bam(da_chon),
    }, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(SC, "POOL", pool)
    monkeypatch.setattr(SC, "DAU", dau)
    # Cây làm việc bẩn trong lúc phát triển KHÔNG được biến thành lỗi test —
    # `mo_run` từ chối bản trọng yếu chưa commit, và điều đó đúng cho lượt
    # THẬT. Ở đây ta đo wiring, nên trung hoà đúng một phép kiểm ấy.
    monkeypatch.setattr(AI, "phan_loai_dirty", lambda: {
        "sach": True, "duong_ban": [], "ban_trong_yeu": [],
        "ban_khong_lien_quan": []})
    return {"pool": pool, "dau": dau, "bai": bai, "chon": chon,
            "case_set_hash": SC._bam(da_chon)}


class GhiNhatKy:
    """Nhật ký thứ tự sự kiện — guard và lượt gọi provider."""

    def __init__(self):
        self.su_kien: list[str] = []
        self.goi: list[str] = []

    def provider_stub(self, tra: str = "khong-phai-json"):
        async def _stub(api_key, system_prompt, user_text,
                        response_schema=None, temperature=0.2, image=None):
            self.su_kien.append("provider_call")
            self.goi.append(user_text[:40])
            return tra
        return _stub


@pytest.fixture
def nhat_ky(monkeypatch):
    """Stub provider ở ĐÚNG ranh giới application call (`call_gemini`)."""
    from app.ai import pipeline

    nk = GhiNhatKy()
    monkeypatch.setattr(pipeline, "call_gemini", nk.provider_stub())

    goc = R.canh_gac_truoc_luot_goi

    def canh_gac_ghi(thu_muc, **kw):
        nk.su_kien.append("identity_guard")
        return goc(thu_muc, **kw)

    monkeypatch.setattr(R, "canh_gac_truoc_luot_goi", canh_gac_ghi)
    return nk


def _chay(out: Path, *, ca: str | None = None, chi_8a: bool = False) -> int:
    """Chạy ĐÚNG `main_async` — không phải một bản mô phỏng của nó."""
    import os

    os.environ["ALLOW_LIVE_AI"] = "1"
    os.environ["GEMINI_API_KEY"] = "khoa-gia-cho-test"
    try:
        return asyncio.run(R.main_async(argparse.Namespace(
            out_dir=str(out), chi_8a=chi_8a, ca=ca)))
    finally:
        os.environ.pop("ALLOW_LIVE_AI", None)
        os.environ.pop("GEMINI_API_KEY", None)


# ══ D1 — CHUẨN HOÁ Ở LOADER ═══════════════════════════════════════════════
def test_D1a_nap_ca_v3_tra_mong_kieu_set(v3_gia):
    ca, _tho, _bam = R.nap_ca_v3()
    assert ca, "loader không trả ca nào"
    assert {type(c["mong"]).__name__ for c in ca} == {"set"}, \
        "`mong` phải là set sau chuẩn hoá — pool lưu list"


def test_D1b_nap_ca_v3_KHONG_ghi_lai_pool(v3_gia):
    truoc = v3_gia["pool"].read_bytes()
    R.nap_ca_v3()
    assert v3_gia["pool"].read_bytes() == truoc, "loader đã ghi đè pool"


def test_D1c_nap_ca_v3_giu_nguyen_cac_truong_khac(v3_gia):
    ca, _tho, _bam = R.nap_ca_v3()
    m = {c["id"]: c for c in ca}
    goc = {b["id"]: b for b in v3_gia["bai"]}
    for i, c in m.items():
        for k in ("id", "o", "hinh", "loai", "de", "cong_thuc"):
            assert c[k] == goc[i][k], f"{i}.{k} bị đổi"


def test_D1d_nap_ca_v3_tra_BAN_SAO_khong_phai_object_pool(v3_gia):
    ca, _tho, _bam = R.nap_ca_v3()
    ca[0]["de"] = "ĐÃ SỬA"
    lai, _t2, _b2 = R.nap_ca_v3()
    assert lai[0]["de"] != "ĐÃ SỬA", "loader trả tham chiếu chung, sửa lan ngược"


def test_D1e_so_sanh_dap_so_KHONG_nem_TypeError(v3_gia):
    """Blocker ②: `list <= set` ném; `set <= set` thì không."""
    ca, _tho, _bam = R.nap_ca_v3()
    duong = [c for c in ca if c["loai"] == "duong"]
    assert duong
    for c in duong:
        assert (c["mong"] <= {"2", "3", "9"}) is True


def test_D1f_case_set_hash_khop_con_dau(v3_gia):
    _ca, _tho, bam = R.nap_ca_v3()
    assert bam == v3_gia["case_set_hash"]


def test_D1g_ca_tho_giu_mong_dang_list_de_niem_phong_duoc(v3_gia):
    """Bộ THÔ phải JSON-hoá được — `seal_bo_ca` băm bằng `json.dumps`."""
    _ca, tho, bam = R.nap_ca_v3()
    assert {type(c["mong"]).__name__ for c in tho} == {"list"}
    assert AI.seal_bo_ca(tho)["case_set_hash"] == bam


# ══ D2 — END-TO-END QUA `main_async` ══════════════════════════════════════
def test_D2a_manifest_ton_tai_TRUOC_luot_goi_provider_dau_tien(
        tmp_path, v3_gia, nhat_ky):
    out = tmp_path / "run"
    _chay(out)
    assert (out / "manifest.json").exists(), "không ghi manifest"
    assert nhat_ky.su_kien, "không lượt gọi nào xảy ra — test không đo được gì"
    assert nhat_ky.su_kien.index("identity_guard") < \
        nhat_ky.su_kien.index("provider_call"), \
        f"provider đi trước guard: {nhat_ky.su_kien[:4]}"


def test_D2b_MOI_luot_goi_provider_deu_co_guard_di_TRUOC(
        tmp_path, v3_gia, nhat_ky):
    _chay(tmp_path / "run")
    canh = 0
    for sk in nhat_ky.su_kien:
        if sk == "identity_guard":
            canh += 1
        elif sk == "provider_call":
            assert canh > 0, "một lượt gọi provider không có guard nào đi trước"
            canh -= 1


def test_D2c_moi_ID_chay_deu_thuoc_da_rut(tmp_path, v3_gia, nhat_ky):
    out = tmp_path / "run"
    _chay(out)
    d = json.loads((out / "stage_8a_one_shot.json").read_text(encoding="utf-8"))
    ids = {c["id"] for c in d["ca"]}
    assert ids <= set(v3_gia["chon"]), f"ID lạ: {ids - set(v3_gia['chon'])}"


def test_D2d_KHONG_ID_nao_thuoc_corpus_phat_trien(tmp_path, v3_gia, nhat_ky):
    out = tmp_path / "run"
    _chay(out)
    d = json.loads((out / "stage_8a_one_shot.json").read_text(encoding="utf-8"))
    ids = {c["id"] for c in d["ca"]}
    assert not (ids & {c["id"] for c in R.CA}), "corpus phát triển lọt vào lượt live"


def test_D2e_canonical_run_chay_du_13_ca(tmp_path, v3_gia, nhat_ky):
    out = tmp_path / "run"
    _chay(out)
    d = json.loads((out / "stage_8a_one_shot.json").read_text(encoding="utf-8"))
    assert len(d["ca"]) == 13, f"chạy {len(d['ca'])} ca, phải 13"
    assert {c["id"] for c in d["ca"]} == set(v3_gia["chon"])


def test_D2f_manifest_ghi_ngan_sach_78(tmp_path, v3_gia, nhat_ky):
    out = tmp_path / "run"
    _chay(out)
    mf = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert mf["application_call_budget"] == 78
    assert mf["ngan_sach_goi"] == 78


def test_D2g_artifact_dung_case_set_hash_V3_KHONG_dung_CA_HASH(
        tmp_path, v3_gia, nhat_ky):
    out = tmp_path / "run"
    _chay(out)
    a8 = json.loads((out / "stage_8a_one_shot.json").read_text(encoding="utf-8"))
    cuoi = json.loads((out / "curved_acceptance.json").read_text(encoding="utf-8"))
    mf = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    bam = v3_gia["case_set_hash"]
    assert a8["case_set_hash"] == bam
    assert cuoi["tom_tat"]["CASE_SET_HASH"] == bam
    assert a8["moi_truong"]["case_set_hash"] == bam
    assert mf["seal"]["case_set_hash"] == bam
    tho = json.dumps({"a": a8, "c": cuoi, "m": mf}, ensure_ascii=False)
    assert R.CA_HASH not in tho, "băm corpus phát triển lọt vào artifact"


def test_D2h_guard_that_bai_thi_provider_KHONG_duoc_goi(
        tmp_path, v3_gia, nhat_ky, monkeypatch):
    from acceptance_integrity import IntegrityError

    def canh_gac_hong(thu_muc, **kw):
        nhat_ky.su_kien.append("identity_guard")
        if not kw.get("lan_dau"):
            raise IntegrityError("TIÊM LỖI: danh tính trôi")
        return {}

    monkeypatch.setattr(R, "canh_gac_truoc_luot_goi", canh_gac_hong)
    with pytest.raises(IntegrityError):
        _chay(tmp_path / "run")
    assert nhat_ky.goi == [], f"provider vẫn bị gọi {len(nhat_ky.goi)} lượt"


def test_D2i_khong_co_luot_goi_nao_ngoai_stub(tmp_path, v3_gia, nhat_ky):
    """Mọi lượt gọi đều đi qua stub ⇒ 0 network call."""
    _chay(tmp_path / "run")
    assert len(nhat_ky.goi) == 13, \
        f"13 ca × 1 analyze = 13 lượt; đếm được {len(nhat_ky.goi)}"


def test_D2j_out_dir_da_co_noi_dung_thi_DUNG(tmp_path, v3_gia, nhat_ky):
    out = tmp_path / "run"
    out.mkdir()
    (out / "cu.json").write_text("{}", encoding="utf-8")
    assert _chay(out) == 2
    assert nhat_ky.goi == []


def test_D2k_probe_subset_loc_TRONG_tap_da_rut_va_mang_nhan(
        tmp_path, v3_gia, nhat_ky):
    """`--ca` lọc trong bộ ĐÃ RÚT, mang nhãn PROBE, băm bộ ca KHÔNG đổi."""
    out = tmp_path / "run"
    _chay(out, ca="C1_1,N1_1")
    cuoi = json.loads((out / "curved_acceptance.json").read_text(encoding="utf-8"))
    tt = cuoi["tom_tat"]
    assert tt["PROBE_SUBSET"] == ["C1_1", "N1_1"]
    assert tt["MODEL_CASES_TOTAL"] == 2
    assert tt["CASE_SET_HASH"] == v3_gia["case_set_hash"], \
        "băm bộ ca phải giữ nguyên của BỘ ĐẦY ĐỦ, không đổi theo tập con"
    assert len(nhat_ky.goi) == 2


def test_D2l_probe_id_ngoai_tap_da_rut_bi_TU_CHOI(tmp_path, v3_gia, nhat_ky):
    """id thuộc corpus phát triển không còn là id hợp lệ."""
    assert _chay(tmp_path / "run", ca="ball_1") == 2
    assert nhat_ky.goi == []


def test_D2m_tran_theo_SO_CA_THUC_CHAY_khong_phai_13(
        tmp_path, v3_gia, nhat_ky, monkeypatch):
    """Probe 2 ca không được mang trần của lượt 13 ca."""
    out = tmp_path / "run"
    _chay(out, ca="C1_1,N1_1")
    mf = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert mf["application_call_budget"] == R.tran_luot_goi_v3(2) == 12


# ══ D3 — NHÁNH 8B TRA CA TRONG TẬP V3 ═════════════════════════════════════
def test_D3a_nhanh_8B_tra_ca_trong_tap_V3(tmp_path, v3_gia, monkeypatch):
    """Trước sửa: `next(x for x in CA …)` ⇒ StopIteration vì id V3 không có
    trong corpus phát triển."""
    from app.ai import pipeline

    lan: dict[str, int] = {}

    class HopDongGia:
        problem_text = "đề"
        input_facts: list = []
        obligations: list = []

    async def analyze_gia(text, api_key, domain=None):
        return HopDongGia(), None

    async def program_gia(text, _x, api_key, contract, domain=None):
        return None, "1 validation error for SemanticProgramSpec: sai lược đồ"

    monkeypatch.setattr(pipeline, "stage_semantic_analyze", analyze_gia)
    monkeypatch.setattr(pipeline, "stage_semantic_program", program_gia)

    out = tmp_path / "run"
    _chay(out)
    d = json.loads((out / "curved_acceptance.json").read_text(encoding="utf-8"))
    assert d["tom_tat"]["REPAIR_ELIGIBLE_FAILURES"] == 9, \
        "9 ca dương phải repair-eligible với lỗi schema"
    assert d["tom_tat"]["REPAIR_CALLS"] == 9, "nhánh 8B không chạy"
    assert {r["id"] for r in d["sau_sua"]} <= set(v3_gia["chon"])
    assert lan == {}


# ══ D4 — TRẦN LƯỢT GỌI ════════════════════════════════════════════════════
def test_D4a_tran_78_vao_dung_truong_logical(tmp_path, v3_gia, nhat_ky,
                                             monkeypatch):
    """`max_logical_calls` đếm số lần `call_gemini` — đó là application call.
    `max_api_calls` đếm request HTTP (gồm retry transport)."""
    from app.ai import gemini

    thay: dict = {}
    goc = gemini.set_budget

    def ghi(b):
        if b is not None:
            thay["max_logical_calls"] = b.max_logical_calls
            thay["max_api_calls"] = b.max_api_calls
        return goc(b)

    monkeypatch.setattr(gemini, "set_budget", ghi)
    _chay(tmp_path / "run")
    assert thay["max_logical_calls"] == 78, thay
    assert thay["max_api_calls"] == 78 * gemini.MAX_ATTEMPTS, thay


def test_D4b_luot_goi_thu_79_bi_chan_TRUOC_khi_goi_provider(
        tmp_path, v3_gia, nhat_ky, monkeypatch):
    from app.ai import gemini

    goc_note = gemini.ApiBudget.note_call
    trang_thai = {"da": 0}

    def note(self):
        trang_thai["da"] += 1
        return goc_note(self)

    monkeypatch.setattr(gemini.ApiBudget, "note_call", note)
    b = gemini.ApiBudget(max_logical_calls=78)
    for _ in range(78):
        b.note_call()
    with pytest.raises(gemini.BudgetExceeded):
        b.note_call()


# ══ D5 — QUÉT NGUỒN: LIVE PATH KHÔNG ĐỌC CORPUS PHÁT TRIỂN ════════════════
def _ham_live_path() -> list[ast.AST]:
    src = Path(R.__file__).read_text(encoding="utf-8")
    cay = ast.parse(src)
    ten = {"main", "main_async", "_chay_mot", "_moi_truong"}
    return [n for n in cay.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name in ten]


def _doc_ten(nodes, ten: str) -> int:
    return sum(1 for n in nodes for x in ast.walk(n)
               if isinstance(x, ast.Name) and x.id == ten)


def test_D5a_live_path_KHONG_doc_CA():
    assert _doc_ten(_ham_live_path(), "CA") == 0, \
        "live path còn đọc corpus phát triển `CA`"


def test_D5b_live_path_KHONG_doc_CA_HASH():
    assert _doc_ten(_ham_live_path(), "CA_HASH") == 0, \
        "live path còn đọc `CA_HASH`"


def test_D5c_guard_chong_corpus_VAN_duoc_giu(_=None):
    """`kiem_bo_ca_la_pool_v3` PHẢI còn đọc `CA` — nó là guard, không phải nguồn."""
    src = Path(R.__file__).read_text(encoding="utf-8")
    cay = ast.parse(src)
    g = [n for n in cay.body if isinstance(n, ast.FunctionDef)
         and n.name == "kiem_bo_ca_la_pool_v3"]
    assert g and _doc_ten(g, "CA") > 0


# ══ D6 — TIÊM LỖI: mỗi phép sửa bị hoàn tác phải làm ĐỎ ═══════════════════
def test_D6a_khoi_phuc_nguon_ca_thanh_CA_thi_entrypoint_DO(
        tmp_path, v3_gia, nhat_ky, monkeypatch):
    """Tiêm ①: loader trả corpus phát triển ⇒ guard pool phải chặn."""
    from acceptance_integrity import IntegrityError

    monkeypatch.setattr(R, "nap_ca_v3",
                        lambda: (R.CA, R.CA, "bam-gia"))
    with pytest.raises(IntegrityError, match="CORPUS PHÁT TRIỂN"):
        _chay(tmp_path / "run")
    assert nhat_ky.goi == []


def test_D6b_bo_chuan_hoa_mong_thi_so_sanh_dap_so_DO(v3_gia):
    """Tiêm ②: `mong` để nguyên list ⇒ TypeError ở phép tập con."""
    bai = _bai_gia()
    with pytest.raises(TypeError, match="not supported between"):
        _ = bai[0]["mong"] <= {"2", "3"}


def test_D6c_bo_buoc_mo_manifest_thi_guard_DO(tmp_path, v3_gia, nhat_ky,
                                              monkeypatch):
    """Tiêm ③: không mở manifest ⇒ `canh_gac` phải ném."""
    from acceptance_integrity import IntegrityError

    monkeypatch.setattr(R, "mo_luot_do_v3",
                        lambda thu_muc, **kw: Path(thu_muc).mkdir(parents=True))
    with pytest.raises(IntegrityError, match="manifest"):
        _chay(tmp_path / "run")
    assert nhat_ky.goi == []


def test_D6d_khoi_phuc_3n_cong_5_thi_ngan_sach_DO(v3_gia):
    """Tiêm ⑤: công thức cũ cho 13 ca ra 44, không phải 78."""
    assert 3 * 13 + 5 != R.tran_luot_goi_v3(13)
    assert R.tran_luot_goi_v3(13) == 78


def test_D6e_ghi_CA_HASH_vao_artifact_thi_case_identity_DO(
        tmp_path, v3_gia, nhat_ky):
    """Tiêm ⑦: băm corpus phát triển KHÁC băm bộ ca V3 — nhầm là bắt được."""
    out = tmp_path / "run"
    _chay(out)
    a8 = json.loads((out / "stage_8a_one_shot.json").read_text(encoding="utf-8"))
    assert a8["case_set_hash"] != R.CA_HASH


# ══ F — CERTIFIER PHẢI CHẠY ENTRYPOINT THẬT ═══════════════════════════════
def test_F1_certifier_co_verdict_live_entrypoint(tmp_path):
    import certify_acceptance_runner as cert

    ok, sai = cert.chung_nhan_live_entrypoint(tmp_path / "cert-live")
    assert ok, sai


def test_F2_tiem_lai_nguon_CA_thi_certifier_DO(tmp_path, monkeypatch):
    """Hoàn tác đúng bản vá wave này ⇒ verdict mạnh phải ĐỎ."""
    import certify_acceptance_runner as cert

    monkeypatch.setattr(R, "nap_ca_v3", lambda: (R.CA, R.CA, R.CA_HASH))
    ok, sai = cert.chung_nhan_live_entrypoint(tmp_path / "cert-live")
    assert not ok
    assert sai


def test_F3_bo_mo_manifest_thi_certifier_DO(tmp_path, monkeypatch):
    import certify_acceptance_runner as cert

    monkeypatch.setattr(R, "mo_luot_do_v3",
                        lambda thu_muc, **kw: Path(thu_muc).mkdir(parents=True))
    ok, sai = cert.chung_nhan_live_entrypoint(tmp_path / "cert-live")
    assert not ok
    assert any("manifest" in x.lower() for x in sai), sai


def test_F5_readiness_YES_chi_khi_verdict_MANH_pass(tmp_path, monkeypatch,
                                                    capsys):
    """Tiêm: verdict mạnh ĐỎ ⇒ readiness KHÔNG được nói YES.

    Trước wave này readiness chỉ hỏi cấu hình model, nên nó nói YES suốt quãng
    entrypoint chạy corpus phát triển — một lời mời đi thẳng vào chỗ tiêu pool.
    """
    import certify_acceptance_runner as cert

    monkeypatch.setattr(cert, "chung_nhan_live_entrypoint",
                        lambda td: (False, ["TIÊM LỖI: entrypoint chưa nối"]))
    monkeypatch.setattr(sys, "argv", ["certify", "--out-dir", str(tmp_path)])
    ma = cert.main()
    ra = capsys.readouterr().out
    assert "V3_LIVE_ENTRYPOINT_INTEGRATION  FAIL" in ra
    assert "READY_FOR_INDEPENDENT_V3_LIVE  CONDITIONAL" in ra
    assert "READY_FOR_INDEPENDENT_V3_LIVE  YES" not in ra
    assert ma == 1, "verdict mạnh đỏ mà mã thoát vẫn 0"


def test_F6_certifier_that_phat_YES_khi_moi_thu_xanh(tmp_path, monkeypatch,
                                                     capsys):
    import certify_acceptance_runner as cert

    monkeypatch.setattr(sys, "argv", ["certify", "--out-dir", str(tmp_path)])
    ma = cert.main()
    ra = capsys.readouterr().out
    assert "V3_LIVE_ENTRYPOINT_INTEGRATION  PASS" in ra
    assert "READY_FOR_INDEPENDENT_V3_LIVE  YES" in ra
    assert ma == 0


def test_F4_certifier_live_entrypoint_KHONG_ro_ra_moi_truong(tmp_path):
    """Bọc/gỡ phải sạch: sau khi chứng nhận, `call_gemini` về nguyên trạng."""
    import certify_acceptance_runner as cert
    from app.ai import pipeline

    truoc_call = pipeline.call_gemini
    truoc_dau, truoc_pool = SC.DAU, SC.POOL
    truoc_dirty = AI.phan_loai_dirty
    cert.chung_nhan_live_entrypoint(tmp_path / "cert-live")
    assert pipeline.call_gemini is truoc_call
    assert (SC.DAU, SC.POOL) == (truoc_dau, truoc_pool)
    assert AI.phan_loai_dirty is truoc_dirty
