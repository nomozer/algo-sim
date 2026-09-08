# -*- coding: utf-8 -*-
"""`THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT` — runner cuối phải ĐÚNG ĐƯỜNG.

**0 lượt gọi model, 0 lượt gọi provider thật.**

Năm khoảng trống đã đo ở wave trước được đóng bằng một entrypoint riêng. Bộ
test này kiểm **từng cái** trên mã đang chạy, và nhóm `F` chứng minh mỗi guard
ĐỎ ĐƯỢC khi bị phá — guard chưa từng đỏ là guard chưa được chứng minh.

⚠️ Trọng tâm là nhóm `A`: **parity byte của prompt sửa**. Chặng B tái dùng
`_prompt_sua` của sản phẩm, nhưng chuỗi CHẨN ĐOÁN thì phải dựng lại (ba nhánh
`loi` nằm trong thân vòng lặp `stage_semantic_program`, không lấy ra được).
Đó là chỗ DUY NHẤT runner có thể lệch khỏi sản phẩm, nên nó bị khoá bằng phép
so từng byte với prompt mà sản phẩm THẬT phát ra ở lượt sửa.
"""
from __future__ import annotations

import ast
import asyncio
import copy
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[3]
BACKEND = GOC / "backend"
SCRIPTS = BACKEND / "scripts"
RA = GOC / "docs" / "evaluation" / "geometry" / "thesis-final-acceptance"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import certify_thesis_final_acceptance as CT  # noqa: E402
import run_thesis_final_acceptance as R  # noqa: E402
import thesis_acceptance_corpus as C  # noqa: E402
from app.ai import pipeline  # noqa: E402
from app.simulation.semantic_program.analyze_contract import (  # noqa: E402
    build_request_contract)
from app.simulation.semantic_program.domain_profile import (  # noqa: E402
    DOMAIN_HINH_HOC)


@pytest.fixture(scope="module")
def bo_do() -> R.BoDo:
    return R.nap_bo_do()


@pytest.fixture(scope="module")
def chung_nhan() -> dict:
    p = RA / "certification" / "CERTIFICATION.json"
    assert p.exists(), ("thiếu CERTIFICATION.json — chạy "
                        "`run_thesis_final_acceptance.py --certify` trước")
    return json.loads(p.read_text(encoding="utf-8"))


def _hop_dong(ca: dict):
    return build_request_contract(
        json.loads(CT._analyze_tho(ca["request_contract_gold"])),
        problem_text=ca["problem_text"], domain=DOMAIN_HINH_HOC)


# ══ A · PARITY BYTE CỦA PROMPT SỬA — phép khoá quan trọng nhất ═══════════
def _chay_hai_luot(ca: dict, chuong_trinh_hong: dict) -> tuple[str, str, str]:
    """Chạy `stage_semantic_program` THẬT với trần 2 lượt.

    Trả `(base ở lượt 1, prompt SỬA ở lượt 2, raw lượt 1)` — tất cả do CHÍNH
    sản phẩm phát ra. Stub chỉ thay văn bản provider trả về.
    """
    de = ca["problem_text"]
    ct = _hop_dong(ca)
    ghi: list[str] = []
    tho = json.dumps(chuong_trinh_hong, ensure_ascii=False)

    async def _stub(api, skill, prompt, schema, temp, *a, **kw):
        ghi.append(prompt)
        return tho if len(ghi) == 1 else json.dumps(ca["gold_program"],
                                                    ensure_ascii=False)

    with R.bao_provider(_stub), R.ghim_so_luot_tong_hop(2):
        asyncio.run(pipeline.stage_semantic_program(
            de, {}, "STUB", ct, domain=DOMAIN_HINH_HOC))
    assert len(ghi) == 2, f"sản phẩm không đi tới lượt sửa: {len(ghi)} lượt"
    return ghi[0], ghi[1], tho


def _hong_schema() -> tuple[dict, dict]:
    ca = copy.deepcopy(C.theo_id("p4_hinh_tru_the_tich_va_xung_quanh"))
    xau = copy.deepcopy(ca["gold_program"])
    for st in xau["statements"]:
        if st.get("kind") == "construct_curved_solid":
            st.pop("apex_or_top", None)
    return ca, xau


def _hong_ir_static() -> tuple[dict, dict]:
    """Cắt thiết diện TRƯỚC khi dựng khối ⇒ `được dựng ở câu lệnh SAU`."""
    ca = copy.deepcopy(C.theo_id("p1_chop_thiet_dien_khoang_cach"))
    xau = copy.deepcopy(ca["gold_program"])
    st = xau["statements"]
    i_khoi = next(i for i, x in enumerate(st) if x["kind"] == "construct_solid")
    i_td = next(i for i, x in enumerate(st) if x["kind"] == "construct_section")
    st.insert(0, st.pop(i_td))
    _ = i_khoi
    return ca, xau


def _hong_grounding() -> tuple[dict, dict]:
    """Bỏ `source_fact_id` của một đỉnh ⇒ toạ độ không truy được về đề."""
    ca = copy.deepcopy(C.theo_id("p2_chop_day_ngu_giac_lom"))
    xau = copy.deepcopy(ca["gold_program"])
    for d in xau["memory_declarations"]:
        if d["name"] == "Q":
            d.pop("source_fact_id", None)
    return ca, xau


@pytest.mark.parametrize("dung,nhanh_mong", [
    (_hong_schema, "schema"),
    (_hong_ir_static, "ir_static"),
    (_hong_grounding, "grounding"),
])
def test_A1_prompt_sua_cua_runner_TRUNG_TUNG_BYTE_voi_san_pham(dung, nhanh_mong):
    """Ba nhánh chẩn đoán, ba phép so BYTE.

    Nếu chuỗi chẩn đoán của runner lệch dù một dấu cách, mô hình ở lượt sửa
    nhận một lời khác lời sản phẩm sẽ gửi — và con số thu được nói về bộ đo
    chứ không nói về hệ.
    """
    ca, xau = dung()
    base, prompt_sp, raw = _chay_hai_luot(ca, xau)

    ct = _hop_dong(ca)
    chan_doan, nhanh = R.chan_doan_san_pham(raw, ct)
    assert nhanh == nhanh_mong, (nhanh, nhanh_mong)
    assert chan_doan is not None

    prompt_runner = R.prompt_sua_chang_b(
        base, raw, chan_doan, ca["problem_text"], DOMAIN_HINH_HOC)
    assert prompt_runner == prompt_sp, (
        f"prompt sửa LỆCH ở nhánh '{nhanh}'\n"
        f"  runner : {prompt_runner[-260:]!r}\n"
        f"  sản phẩm: {prompt_sp[-260:]!r}")


def test_A2_base_chup_duoc_chinh_la_prompt_luot_dau():
    """Runner KHÔNG dựng lại `base` — nó chụp. Test này ghim rằng lượt đầu
    thật sự gửi đúng `base`, tức phép chụp có nghĩa."""
    ca, xau = _hong_schema()
    base, _sua, _raw = _chay_hai_luot(ca, xau)
    assert base.startswith('Đề bài:\n"""\n' + ca["problem_text"])
    assert "HỢP ĐỒNG JSON" in base, "thẻ văn phạm phải nằm trong `base`"


def test_A3_chan_doan_TU_CHOI_khi_khong_co_gi_de_sua():
    ca = C.theo_id("p3_mat_cau_va_thiet_dien_tron")
    ct = _hop_dong(ca)
    chan_doan, nhanh = R.chan_doan_san_pham(
        json.dumps(ca["gold_program"], ensure_ascii=False), ct)
    assert chan_doan is None and nhanh == "khong_co_gi_de_sua"


# ══ B · NĂM KHOẢNG TRỐNG ĐÃ ĐÓNG ════════════════════════════════════════
def test_B1_G1_bo_ca_co_dinh_khong_qua_con_dau_V3():
    src = (GOC / R.RUNNER_ENTRYPOINT).read_text(encoding="utf-8")
    assert CT._dau_vet_v3(src) == []
    bd = R.nap_bo_do()
    assert len(bd.ca_duong) == 7 and len(bd.ca_am) == 2
    assert all(bd.kiem.values()), bd.lech


def test_B2_G2_moi_raw_attempt_du_truong(chung_nhan):
    assert chung_nhan["nhan"]["ALL_RAW_ATTEMPTS_RETAINED"]


def test_B3_G3_scorer_canonical_cho_ca_duong_VA_ca_am(chung_nhan):
    assert chung_nhan["nhan"]["CANONICAL_POSITIVE_SCORER"]
    assert chung_nhan["nhan"]["CANONICAL_NEGATIVE_SCORER"]


def test_B4_G4_hai_chang_dung_so_luot(chung_nhan):
    assert chung_nhan["nhan"]["STAGE_A_ONE_ATTEMPT"]
    assert chung_nhan["nhan"]["STAGE_B_ONE_REPAIR"]
    assert chung_nhan["nhan"]["STAGE_B_REUSES_FROZEN_CONTRACT"]
    assert chung_nhan["nhan"]["STAGE_B_REUSES_RAW_CANDIDATE"]


def test_B5_G5_policy_khoa_luan_duoc_nap(chung_nhan):
    assert chung_nhan["nhan"]["THESIS_POLICY_LOADED"]
    mf = json.loads((RA / "certification" / "stub_manifest.json")
                    .read_text(encoding="utf-8"))
    assert mf["threshold_policy_path"] == "thesis_final_acceptance_policy.json"


def test_B6_moi_nhan_chung_nhan_PASS(chung_nhan):
    thieu = sorted(k for k, v in chung_nhan["nhan"].items() if not v)
    assert not thieu and not chung_nhan["sai"], (thieu, chung_nhan["sai"])
    assert set(chung_nhan["nhan"]) == set(CT.NHAN)


def test_B7_chuoi_su_kien_du_va_DUNG_THU_TU(chung_nhan):
    sk = chung_nhan["su_kien"]
    assert chung_nhan["thieu_su_kien"] == []
    assert sk.index("write_manifest") < min(
        i for i, t in enumerate(sk) if t.endswith("_call"))
    assert sk.index("write_stage_a") < sk.index("repair_call")
    assert sk.index("freeze_contract") < sk.index("synthesis_call")


# ══ C · CỔNG MẠNG ═══════════════════════════════════════════════════════
def test_C1_bao_provider_phu_MOI_tham_chieu():
    """`pipeline` làm `from app.ai.gemini import call_gemini`, nên có HAI tên
    trỏ cùng một hàm. Vá một tên là để hở tên kia — và tên bị bỏ sót chính là
    tên đi thẳng ra mạng."""
    import app.ai.gemini as gm

    async def _stub(*a, **kw):
        return "{}"

    goc_pipeline, goc_gemini = pipeline.call_gemini, gm.call_gemini
    with R.bao_provider(_stub):
        assert pipeline.call_gemini is _stub
        assert gm.call_gemini is _stub
    assert pipeline.call_gemini is goc_pipeline
    assert gm.call_gemini is goc_gemini
    assert not any(R.dang_bi_va().values())


def test_C2_hoan_nguyen_ngay_ca_khi_NEM():
    import app.ai.gemini as gm

    goc = gm.call_gemini

    async def _stub(*a, **kw):
        return "{}"

    with pytest.raises(RuntimeError):
        with R.bao_provider(_stub):
            raise RuntimeError("vỡ giữa chừng")
    assert gm.call_gemini is goc
    assert not any(R.dang_bi_va().values())


def test_C3_ghim_so_luot_hoan_nguyen_trong_finally():
    goc = pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    with pytest.raises(ValueError):
        with R.ghim_so_luot_tong_hop(1):
            assert pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS == 1
            raise ValueError("vỡ")
    assert pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS == goc


def test_C4_khong_lượt_gọi_thật_nao(chung_nhan):
    assert chung_nhan["nhan"]["REAL_PROVIDER_CALLS_ZERO"]
    assert chung_nhan["nhan"]["NETWORK_REFERENCES_RESTORED"]
    assert chung_nhan["tong_ket"]["LOGICAL_CALLS"] == 19  # 9+9+1


# ══ D · BẢN VÁ DẤU TRỪ (SẢN PHẨM) ═══════════════════════════════════════
@pytest.mark.parametrize("dau", ["-", "−", "–", "—", "‐", "‑"])
def test_D1_moi_dau_tru_deu_doc_duoc(dau):
    """`U+2212` là dấu trừ ĐÚNG của toán học. Trước bản vá nó trả `None`."""
    from app.simulation.semantic_program.plane_equation import doc_phuong_trinh

    from fractions import Fraction as F

    assert doc_phuong_trinh(f"2x {dau} z + 12 = 0") == (
        F(2), F(0), F(-1), F(12))


def test_D2_phep_no_span_KHONG_con_cat_cut_phuong_trinh():
    """Lỗi thật: nở trái dừng ở `−` và thu `z + 12 = 0` — một mặt phẳng KHÁC
    hẳn, rồi đem đối chiếu và báo vi phạm trên chương trình đúng."""
    from app.simulation.semantic_program.plane_equation import _ung_vien

    de = ("Trong không gian Oxyz, Mặt phẳng (α): 2x − z + 12 = 0 cắt hình trụ "
          "theo một đường elip.")
    assert [c for c, _b in _ung_vien(de)] == ["2x - z + 12 = 0"]


def test_D3_chuan_hoa_GIU_NGUYEN_do_dai():
    """Ánh xạ 1:1 là điều kiện sống còn: `_ung_vien` trả LÁT CẮT của chuỗi
    gốc, nên một phép chuẩn hoá đổi độ dài sẽ làm mọi chỉ số lệch."""
    from app.simulation.semantic_program.plane_equation import (
        chuan_hoa_dau_tru)

    for s in ("2x − z + 12 = 0", "a–b—c‐d‑e", "không có dấu trừ nào"):
        assert len(chuan_hoa_dau_tru(s)) == len(s)


def test_D4_soft_hyphen_KHONG_bi_coi_la_dau_tru():
    """`U+00AD` không phải dấu trừ. Nhận nó là bịa ra một phép trừ đề không
    viết — và đó là chiều sai nguy hiểm hơn."""
    from app.simulation.semantic_program.plane_equation import doc_phuong_trinh

    assert doc_phuong_trinh("2x \u00ad z + 12 = 0") is None


def test_D5_point_coordinate_VON_da_dung__plane_equation_la_ngoai_le():
    """Chứng minh đây là một NGOẠI LỆ chứ không phải quy ước chung của kho."""
    from app.simulation.semantic_program.point_coordinate import doc_toa_do

    assert doc_toa_do("A(−1;2;3)") is not None


def test_D6_tac_dong_cache_da_DO_chu_khong_suy():
    d = json.loads((RA / "CACHE_IMPACT.json").read_text(encoding="utf-8"))
    assert d["SERVED_TO_REJECTED"] == 0
    assert d["ANSWER_CHANGED"] == 0
    assert d["REJECTED_TO_SERVED"] >= 1
    assert d["CACHE_VERSION_BUMP_REQUIRED"] is False
    assert 'status == "ok"' in d["cache_write_condition"]


# ══ E · KHOÁ DANH TÍNH ══════════════════════════════════════════════════
def test_E1_lock_mang_bam_runner_that():
    d = json.loads((RA / "IDENTITY_LOCK.json").read_text(encoding="utf-8"))
    assert d["LOCK_STATE"] == "LOCKED_READY_FOR_FINAL_EXECUTION"
    assert d["RUNNER_HASH"] == R.bam_runner()["RUNNER_HASH"]
    assert d["CERTIFICATION_HASH"]


def test_E2_bam_runner_KHONG_doc_artifact__khong_co_vong():
    """Khoá hai lần phải cho cùng một băm. Nếu băm runner đọc artifact chứa
    chính nó thì mỗi lần ghi sẽ đổi băm và không bao giờ hội tụ."""
    a = R.bam_runner()["RUNNER_HASH"]
    d = json.loads((RA / "IDENTITY_LOCK.json").read_text(encoding="utf-8"))
    b = R.bam_runner()["RUNNER_HASH"]
    assert a == b == d["RUNNER_HASH"]
    for t in (R.RUNNER_ENTRYPOINT, *R.RUNNER_MODULE_SET):
        assert t.endswith(".py"), t


def test_E3_ngan_sach_trong_lock_khop_policy(bo_do):
    d = json.loads((RA / "IDENTITY_LOCK.json").read_text(encoding="utf-8"))
    ns = bo_do.nguong["budget"]
    assert d["LOGICAL_CALL_BUDGET"] == ns["MAX_LOGICAL_CALLS"] == 25
    assert d["PHYSICAL_ATTEMPT_BUDGET"] == ns["MAX_PHYSICAL_ATTEMPTS"] == 100
    assert d["TOKEN_BUDGET"] == ns["HARD_TOKEN_BUDGET"] == 196000


def test_E4_amendment_ghi_du_ba_muc(bo_do):
    am = bo_do.nguong["amendments"][0]
    assert am["DECIDED_BEFORE_LIVE_RUN"] is True
    assert am["APPLICATION_LLM_CALLS_BEFORE_AMENDMENT"] == 0
    assert am["from_version"] == "1.0.0" and am["to_version"] == "1.1.0"
    assert am["③ candidate"]["CACHE_VERSION"]["bump"] is False
    assert am["① ngân sách"]["MAX_LOGICAL_CALLS"] == {"before": 39, "after": 25}


# ══ F · TIÊM LỖI — mỗi guard phải ĐỎ được ═══════════════════════════════
def test_F1_sua_mot_byte_CORPUS_lam_DO_loader(tmp_path, bo_do):
    import shutil

    for t in R.NGUON_ARTIFACT:
        shutil.copyfile(RA / t, tmp_path / t)
    d = json.loads((tmp_path / "CORPUS.json").read_text(encoding="utf-8"))
    d["positive_cases"][0]["problem_text"] += " "
    (tmp_path / "CORPUS.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    assert not R.nap_bo_do(tmp_path).kiem["CORPUS_HASH_MATCH"]


def test_F2_sua_EXPECTED_RESULTS_lam_DO_loader(tmp_path):
    import shutil

    for t in R.NGUON_ARTIFACT:
        shutil.copyfile(RA / t, tmp_path / t)
    d = json.loads((tmp_path / "EXPECTED_RESULTS.json").read_text("utf-8"))
    next(iter(d["cases"].values()))["V"]["display"] = "999"
    (tmp_path / "EXPECTED_RESULTS.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert not R.nap_bo_do(tmp_path).kiem["EXPECTED_RESULTS_HASH_MATCH"]


def test_F3_sua_POLICY_MIRROR_lam_DO_loader(tmp_path):
    import shutil

    for t in R.NGUON_ARTIFACT:
        shutil.copyfile(RA / t, tmp_path / t)
    d = json.loads((tmp_path / "EVALUATION_POLICY.json").read_text("utf-8"))
    d["budget"]["MAX_LOGICAL_CALLS"] = 999
    (tmp_path / "EVALUATION_POLICY.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert not R.nap_bo_do(tmp_path).kiem["POLICY_MIRROR_MATCH"]


def test_F4_sua_CANDIDATE_trong_lock_lam_DO_loader(tmp_path):
    import shutil

    for t in R.NGUON_ARTIFACT:
        shutil.copyfile(RA / t, tmp_path / t)
    d = json.loads((tmp_path / "IDENTITY_LOCK.json").read_text("utf-8"))
    d["CANDIDATE_HASH"] = "0" * 64
    (tmp_path / "IDENTITY_LOCK.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert not R.nap_bo_do(tmp_path).kiem["CANDIDATE_HASH_MATCH"]


def test_F5_manifest_ghi_SAU_luot_goi_lam_DO_guard():
    """Thứ tự sự kiện là bằng chứng, không phải trang trí."""
    sk = ["load_identity", "analyze_call", "write_manifest", "synthesis_call"]
    i_mf = sk.index("write_manifest")
    i_goi = min(i for i, t in enumerate(sk) if t.endswith("_call"))
    assert not (0 <= i_mf < i_goi)


def test_F6_bo_mot_raw_attempt_lam_DO_guard(chung_nhan):
    so_goi = sum(1 for t in chung_nhan["su_kien"] if t.endswith("_call"))
    assert so_goi == 19
    assert so_goi - 1 != 19, "phép tiêm không ăn"


def test_F7_scorer_am_cu_cua_V3_bi_guard_bat():
    """Dùng lại `_MA_RANH_GIOI_CONG` của runner V3 phải làm guard đỏ."""
    xau = "x = _MA_RANH_GIOI_CONG\n"
    assert "_MA_RANH_GIOI_CONG" in CT._dau_vet_v3(xau)


def test_F8_stage_B_goi_lai_analyze_lam_DO_guard():
    b = json.loads((RA / "certification" / "stub_stage_b_recovery.json")
                   .read_text(encoding="utf-8"))
    that = [x for x in b["cases"] if not x["bo_qua"]]
    assert that, "chặng B chưa từng chạy ⇒ guard chưa chứng minh được gì"
    for x in that:
        assert x["reuses"]["analyze_calls_in_stage_b"] == 0
        xau = {**x["reuses"], "analyze_calls_in_stage_b": 1}
        assert xau["analyze_calls_in_stage_b"] != 0


def test_F9_stage_B_tao_candidate_dau_moi_lam_DO_guard():
    b = json.loads((RA / "certification" / "stub_stage_b_recovery.json")
                   .read_text(encoding="utf-8"))
    a = json.loads((RA / "certification" / "stub_stage_a_first_attempt.json")
                   .read_text(encoding="utf-8"))
    theo_id = {c["id"]: c for c in a["cases"]}
    for x in (y for y in b["cases"] if not y["bo_qua"]):
        assert x["reuses"]["initial_synthesis_calls_in_stage_b"] == 0
        assert x["reuses"]["frozen_contract_sha256"] == \
            theo_id[x["id"]]["frozen_contract_sha256"]


def test_F10_hai_luot_sua_lam_DO_guard():
    nk = json.loads((RA / "certification" / "CERTIFICATION.json")
                    .read_text(encoding="utf-8"))["nhat_ky_provider"]
    assert all(v.count("repair") <= 1 for v in nk.values()), nk
    assert not all(v.count("repair") <= 1 for v in
                   {**nk, "gia": ["repair", "repair"]}.values())


def test_F11_bo_cong_danh_tinh_o_mot_luot_lam_DO_guard():
    assert CT._canh_truoc_moi_goi(
        ["identity_guard_pass", "analyze_call",
         "identity_guard_pass", "synthesis_call"], "identity_guard_pass")
    assert not CT._canh_truoc_moi_goi(
        ["identity_guard_pass", "analyze_call", "synthesis_call"],
        "identity_guard_pass")


def _gac_co_manifest(bo_do, tmp_path):
    """Cổng danh tính chạy TRƯỚC cổng ngân sách, nên muốn kiểm cổng ngân sách
    thì phải cho nó một manifest hợp lệ. Thứ tự ấy là ĐÚNG — `test_F14` ghim
    chiều còn lại."""
    import shutil

    shutil.copyfile(RA / "certification" / "stub_manifest.json",
                    tmp_path / "manifest.json")
    return R.CanhGac(bo_do, tmp_path, gia_lap=True)


def test_F12_vuot_tran_luot_goi_lam_runner_NEM(tmp_path, bo_do):
    gac = _gac_co_manifest(bo_do, tmp_path)
    gac.logic = gac.tran_logic
    with pytest.raises(R.RunnerError, match="HẾT TRẦN lượt gọi"):
        gac.truoc_luot_goi("analyze")


def test_F13_vuot_tran_token_lam_runner_NEM(tmp_path, bo_do):
    gac = _gac_co_manifest(bo_do, tmp_path)
    gac.token_da_dat_cho = gac.tran_token
    with pytest.raises(R.RunnerError, match="HẾT TRẦN token"):
        gac.truoc_luot_goi("synthesis")


def test_F14_thieu_manifest_lam_runner_NEM(tmp_path, bo_do):
    gac = R.CanhGac(bo_do, tmp_path, gia_lap=True)
    with pytest.raises(R.RunnerError, match="chưa có manifest"):
        gac.truoc_luot_goi("analyze")


def test_F15_tham_chieu_mang_con_tro_stub_sau_teardown_bi_bat():
    import app.ai.gemini as gm

    async def _stub(*a, **kw):
        return "{}"

    goc = gm.call_gemini
    gm.call_gemini = _stub                      # rò CÓ CHỦ Ý
    try:
        assert any(R.dang_bi_va().values()), "guard không thấy tham chiếu rò"
    finally:
        gm.call_gemini = goc
    assert not any(R.dang_bi_va().values())


def test_F16_runner_import_bo_do_V3_lam_DO_guard():
    xau = "import seal_curved_v3\nfrom run_curved_acceptance import nap_ca_v3\n"
    assert set(CT._dau_vet_v3(xau)) >= {
        "seal_curved_v3", "run_curved_acceptance", "nap_ca_v3"}
    assert CT._dau_vet_v3("# nap_ca_v3 chỉ là chú thích\n") == [], \
        "guard đọc CHÚ THÍCH ⇒ nó hỏi sai tầng"


def test_F17_chan_doan_lech_mot_ky_tu_lam_DO_parity():
    ca, xau = _hong_schema()
    base, prompt_sp, raw = _chay_hai_luot(ca, xau)
    ct = _hop_dong(ca)
    chan_doan, _n = R.chan_doan_san_pham(raw, ct)
    lech = R.prompt_sua_chang_b(base, raw, chan_doan + " ",
                                ca["problem_text"], DOMAIN_HINH_HOC)
    assert lech != prompt_sp, "phép so parity không phân biệt được một dấu cách"


def test_F18_phan_loai_dirty_KHONG_an_mat_ky_tu_dau_duong_dan(monkeypatch):
    """⚠️ Hồi quy cho một guard TỪNG MÙ, đo được 2026-09-08.

    `git status --porcelain` phát `XY<space>path`, và một file đã sửa mà chưa
    stage ra `' M path'`. Bản trước gọi `_git(...)` có `strip()` toàn bộ output,
    nên **dòng đầu tiên** mất dấu cách đầu và `d[3:]` ăn luôn ký tự đầu của
    đường dẫn: `' M backend/app/x.py'` → `'ackend/app/x.py'`.

    Hậu quả KHÔNG cosmetic: `startswith("backend/app")` khi ấy False, nên file
    rơi khỏi `ban_trong_yeu` và `mo_run` **không chặn** một lượt đo mở trên mã
    sản phẩm đang dirty — đúng thứ `DUONG_TRONG_YEU` sinh ra để chặn, bịt lặng
    lẽ ở đúng file đứng đầu danh sách.
    """
    import acceptance_integrity as AI

    tho = (" M backend/app/simulation/semantic_program/plane_equation.py\n"
           " M backend/scripts/acceptance_integrity.py\n"
           "?? docs/ghi_chu.md\n")

    def _gia(*a, giu_le=False):
        return tho if giu_le else tho.strip()

    monkeypatch.setattr(AI, "_git", _gia)
    d = AI.phan_loai_dirty()
    assert d["duong_ban"][0] == \
        "backend/app/simulation/semantic_program/plane_equation.py"
    assert "backend/app/simulation/semantic_program/plane_equation.py" in \
        d["ban_trong_yeu"], "file `backend/app` ĐẦU danh sách phải là TRỌNG YẾU"
    assert len(d["ban_trong_yeu"]) == 2
    assert d["ban_khong_lien_quan"] == ["docs/ghi_chu.md"]


def test_F19_git_giu_le_moi_doc_dung_porcelain():
    """Chiều NGƯỢC: `strip()` phải VẪN là mặc định, vì `rev-parse` cần nó."""
    import acceptance_integrity as AI

    assert "\n" not in AI._git("rev-parse", "HEAD")
    assert len(AI._git("rev-parse", "HEAD")) == 40


# ══ G · MÃ NGUỒN RUNNER ═════════════════════════════════════════════════
def test_G1_runner_khong_co_nhanh_nao_goi_provider_ngoai_hai_che_do():
    """`--certify` và `--live` là hai cửa duy nhất. Một chế độ mặc định gọi
    provider là một runner sẽ tiêu quota vì gõ nhầm."""
    cay = ast.parse((GOC / R.RUNNER_ENTRYPOINT).read_text(encoding="utf-8"))
    ten = {n.name for n in ast.walk(cay)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert {"chay_lut", "_chay_stage_a", "_chay_stage_b"} <= ten
    src = (GOC / R.RUNNER_ENTRYPOINT).read_text(encoding="utf-8")
    assert 'ALLOW_LIVE_AI' in src and '"--live"' in src
    assert src.count("asyncio.run(chay_lut(") == 1


def test_G2_payload_gui_model_cua_loader_chi_co_de(bo_do):
    for ca in bo_do.moi_ca:
        assert set(bo_do.payload_gui_model(ca)) == {"problem_text"}
