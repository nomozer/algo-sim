# -*- coding: utf-8 -*-
"""PHÉP ĐO NĂNG LỰC CONG — 9 ca, MỚI, không phải chạy lại benchmark lịch sử.

    cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \\
        .venv/Scripts/python.exe scripts/run_curved_acceptance.py --out-dir <thư mục>

⚠️ **TIÊU QUOTA THẬT.** Xem `docs/PHASE_3_CURVED_PRODUCT_INTEGRATION.md`.

─── CHÍNH SÁCH TIẾT KIỆM, VÀ VÌ SAO NÓ TÁCH LÀM HAI CHẶNG ─────────────────

**8A — MỘT lượt tổng hợp mỗi ca, KHÔNG sửa.** Hạ `MAX_SEMANTIC_PROGRAM_ATTEMPTS`
xuống `1`; đó là **hằng số của sản phẩm**, không phải một runner riêng — mọi
cổng, mọi phán quyết, mọi thông điệp giữ nguyên. Kết quả one-shot được ghi
**TRƯỚC** khi có bất kỳ lượt sửa nào, nên con số one-shot không bao giờ bị một
lượt sửa về sau làm đẹp lên.

**8B — chỉ sửa những ca mà ĐƯỜNG SẢN PHẨM thật sự gửi lỗi ngược.** Đọc thẳng
`pipeline._sinh_chuong_trinh`: chỉ ba lớp lỗi đi vào `_prompt_sua` —

    schema (`validate_semantic_program`) · ir_static (`kiem_tinh`) ·
    grounding (khi mã lỗi KHÔNG thuộc `KHONG_DUOC_SUA`)

Lỗi **runtime** (interpreter, `GeometryError`) xảy ra ở `verify_and_compile`,
**ngoài** vòng sửa, nên nó KHÔNG repair-eligible. Cho một ca runtime đi sửa là
dựng một hành vi mà sản phẩm không có — và con số thu được sẽ nói về runner chứ
không nói về hệ.

─── ĐIỀU RUNNER NÀY TỰ CẤM ────────────────────────────────────────────────

Không k=3/k=5. Không đổi prompt giữa các ca. Không chạy lại ca đã ĐẠT. Không
sửa mã nguồn khi phép đo đang chạy — gặp lỗi nền THẬT thì **DỪNG** và báo, vì
vá giữa chừng làm mọi con số phía trước nói về một hệ khác con số phía sau.

Artifact **từ chối ghi đè** thư mục đã có, cùng lệ mọi bộ đo hình học.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))


# ══ BỘ CA CỐ ĐỊNH — khoá bằng băm, không sửa giữa chừng ══════════════════
#
# Đề viết MỚI, không lấy từ ví dụ trong prompt và không lấy từ tập DEV/holdout.
# `mong` là đáp số tính TAY; runner so chuỗi hiển thị của đại lượng.
CA: list[dict[str, Any]] = [
    {
        "id": "ball_1", "hinh": "ball", "loai": "duong",
        "de": "Cho mặt cầu (S) có tâm I và đi qua điểm A, biết IA = 6. "
              "Tính bán kính và thể tích khối cầu (S).",
        "mong": {"6", "288π"},
    },
    {
        "id": "ball_2", "hinh": "ball", "loai": "duong",
        "de": "Cho mặt cầu tâm O bán kính bằng 13. Một mặt phẳng (P) cách tâm "
              "O một khoảng bằng 5 và cắt mặt cầu theo một đường tròn (C). "
              "Tính bán kính của (C) và diện tích hình tròn (C).",
        "mong": {"12", "144π"},
    },
    {
        "id": "cylinder_1", "hinh": "cylinder", "loai": "duong",
        "de": "Một hình trụ có hai đáy tâm O và O′ với OO′ = 7, bán kính đáy "
              "bằng 4. Tính thể tích khối trụ và diện tích xung quanh của "
              "hình trụ.",
        "mong": {"112π", "56π"},
    },
    {
        "id": "cylinder_2", "hinh": "cylinder", "loai": "duong",
        "de": "Cho hình trụ có hai đáy tâm O và O′, bán kính đáy bằng 5 và "
              "chiều cao OO′ = 8. Mặt phẳng vuông góc với trục tại trung điểm "
              "của OO′ cắt hình trụ theo đường tròn (C). Tính bán kính của (C).",
        "mong": {"5"},
    },
    {
        "id": "cone_1", "hinh": "cone", "loai": "duong",
        "de": "Cho hình nón đỉnh S, tâm đáy O, chiều cao SO = 8 và bán kính "
              "đáy bằng 6. Tính độ dài đường sinh, thể tích khối nón và diện "
              "tích xung quanh của hình nón.",
        "mong": {"10", "96π", "60π"},
    },
    {
        "id": "cone_2", "hinh": "cone", "loai": "duong",
        "de": "Cho hình nón đỉnh S, tâm đáy O, chiều cao bằng 9 và bán kính "
              "đáy bằng 4. Một mặt phẳng đi qua trục của hình nón cắt hình nón "
              "theo một tam giác cân. Tính diện tích tam giác đó.",
        "mong": {"36"},
    },
    {
        # LỚP `gm_10`, viết mới. Tâm PHẢI được DỰNG, không được khai toạ độ.
        "id": "circumsphere", "hinh": "ball", "loai": "duong",
        "de": "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và "
              "OA = OB = OC = 2. Tính bán kính mặt cầu ngoại tiếp tứ diện OABC.",
        "mong": {"√3"},
    },
    {
        "id": "refuse_oblique", "hinh": "cylinder", "loai": "am",
        "de": "Cho hình trụ có bán kính đáy bằng 3 và chiều cao bằng 10. Một "
              "mặt phẳng cắt hình trụ theo một đường elip (mặt phẳng này không "
              "vuông góc với trục và không chứa trục). Hãy dựng elip đó và "
              "tính diện tích hình elip.",
        "mong": set(),
    },
    {
        "id": "refuse_line_curved", "hinh": "ball", "loai": "am",
        "de": "Cho mặt cầu tâm I bán kính bằng 5 và một đường thẳng d cắt mặt "
              "cầu tại hai điểm P và Q. Hãy dựng hai giao điểm P, Q của d với "
              "mặt cầu rồi tính độ dài đoạn PQ.",
        "mong": set(),
    },
]

#: Băm bộ ca — vào artifact. Đổi một chữ trong đề ⇒ băm đổi ⇒ không so được
#: với lượt trước, và đó là điều ĐÚNG.
CA_HASH = hashlib.sha256(
    json.dumps([{k: (sorted(v) if isinstance(v, set) else v)
                 for k, v in c.items()} for c in CA],
               ensure_ascii=False, sort_keys=True).encode()
).hexdigest()

#: Ba lớp lỗi mà `pipeline._sinh_chuong_trinh` THẬT SỰ gửi ngược cho mô hình.
#: Đọc từ mã, không đoán. Runtime KHÔNG có trong này.
LOP_SUA_DUOC = ("schema", "ir_static", "grounding")


def cham_ca_theo_duong_san_pham(ca: dict, contract, spec, outcome, *,
                                schema_ok: bool) -> dict[str, Any]:
    """Chấm MỘT ca bằng đúng ba thẩm quyền của sản phẩm.

    ─── VÌ SAO HÀM NÀY TỒN TẠI ────────────────────────────────────────────

    Bản trước runner tự dựng phép chiếu riêng: đọc đại lượng từ
    `outcome.envelope["scene3d"]` rồi so với `mong`. Nhưng `route` **cố ý**
    không dựng `scene3d` — hướng phụ thuộc một chiều, `test_scene3d.py` cấm mọi
    module dưới `app/simulation` import nó, và người ghép cảnh là
    `pipeline._dung_scene3d` chạy SAU route. Nên phép chiếu ấy trả **rỗng cho
    mọi ca**, và `dap_so_khop` không bao giờ True được — kể cả với một chương
    trình đúng tuyệt đối. `c7a` của V3 là ca đã trả giá:
    `l=13 · V=100π · Sxq=65π`, đúng trọn vẹn, bị chấm là lỗi MÔ HÌNH.

    Thẩm quyền đúng vốn đã có sẵn trong scorer — runner chỉ không gọi. Chính
    docstring của `trich_ket_qua` đã nói trước: *"KHÔNG chạm `scene3d`: ở đó
    đại lượng chỉ xuất hiện khi ca đã servable, nên đọc nó là trộn câu hỏi
    'kết quả là gì' với 'hệ có dám phát không'."*

    ─── BỐN CỘT, VÀ VÌ SAO KHÔNG ĐƯỢC GỘP ─────────────────────────────────

        runtime_executable   interpreter chạy được
        exact_answer_match   đáp số ĐÚNG          ← `final_memory`
        scene3d_pass         cảnh dựng được       ← `_dung_scene3d`
        postconditions_pass  hệ CHỨNG THỰC được
        servable             hệ dám phát

    `c7a` đúng ba cột đầu và hỏng hai cột sau. Gộp bất kỳ cặp nào cũng xoá mất
    đúng thông tin ấy — và thông tin ấy nói rằng lỗi thuộc về **HỆ**, không
    thuộc về mô hình.

    ─── PHÂN LỚP: CANONICAL vs LEGACY ─────────────────────────────────────

    `acceptance_verdict.phan_loai` (13 lớp) sở hữu phán quyết. `phan_lop` của
    runner (7 lớp) **không đọc `servable`** nên nó mù với `verification_gap`;
    giữ lại dưới `legacy` để chẩn đoán, và nó KHÔNG tham gia ngưỡng.
    """
    import acceptance_verdict as AV
    from app.ai import pipeline

    gd = AV.co_giai_doan(outcome, schema_ok=schema_ok)
    kq = AV.trich_ket_qua(outcome)
    dai_luong = kq.get("dai_luong") or {}

    # CẢNH — gọi đúng hàm mà pipeline sản phẩm dùng, không dựng bản thứ hai.
    canh = pipeline._dung_scene3d(spec, contract) if gd["runtime_executable"] \
        else None
    canh_dl = [o.get("value") for o in (canh or {}).get("objects", [])
               if o.get("type") == "quantity"]

    mong = set(ca.get("mong") or ())
    khop = bool(mong) and mong <= set(dai_luong.values())

    legacy = phan_lop({
        "loai": ca.get("loai", "duong"), "executable": gd["runtime_executable"],
        "dai_luong": sorted(dai_luong.values()),
        "dap_so_khop": (khop if mong else None),
        "lop_loi": ("khong" if gd["runtime_executable"]
                    else _phan_lop_loi(getattr(outcome, "reason", None))),
        "loi": getattr(outcome, "reason", None)})
    return {
        "execution": {
            "runtime_executable": gd["runtime_executable"],
            "postconditions_pass": gd["postconditions_pass"],
            "servable": gd["servable"],
            "stage_reached": gd["stage_reached"],
            "failure_category": getattr(outcome, "failure_category", None),
            "error_code": getattr(outcome, "error_code", None),
        },
        "results": {
            "final_memory": dai_luong,
            "exact_result_authority": kq.get("nguon"),
            "exact_answer_match": khop,
            "scene3d_pass": bool(canh_dl),
            "scene_quantities": sorted(canh_dl),
            "expected": sorted(mong),
        },
        "classification": {
            "canonical": str(AV.phan_loai(
                outcome, schema_ok=schema_ok,
                la_ca_am=(ca.get("loai") == "am"))),
            "legacy": legacy,
        },
    }


def _moi_truong(case_set_hash: str) -> dict[str, Any]:
    """Wrapper MỎNG quanh thẩm quyền chung — không dựng bảng thứ hai.

    Bản trước tự đọc `CACHE_VERSION` + ba hàm băm và ráp bảng riêng. Bảng thứ
    hai luôn trôi khỏi bản gốc, và cái trôi sẽ là cái không ai nhìn: thêm một
    thành phần danh tính ở `acceptance_integrity` thì bảng ở đây vẫn xanh và
    vẫn thiếu. Nay chỉ thêm đúng thứ runner này sở hữu — băm bộ ca.

    ⚠️ `case_set_hash` là **tham số**, không phải hằng số module. Bản trước
    nhét thẳng `CA_HASH` vào đây, nên mọi artifact của lượt live đều mang băm
    của **corpus phát triển** — kể cả khi bộ ca chạy là pool V3. Một băm sai
    trong artifact không đỏ ở đâu cả; nó chỉ làm hai lượt khác nhau trông như
    cùng một bộ ca.
    """
    from acceptance_integrity import moi_truong_hien_tai

    return {**moi_truong_hien_tai(), "case_set_hash": case_set_hash}


# ══ NGUỒN BỘ CA — POOL V3 ĐÃ RÚT, KHÔNG PHẢI CORPUS PHÁT TRIỂN ═══════════
#
# `CA` ở trên là corpus V1/V2: 9 đề tôi tự viết, đã chạy, artifact đã công bố.
# Nó là **dữ liệu phát triển**. Dùng nó ở chỗ đáng lẽ là pool V3 sẽ cho ra một
# con số trông như nghiệm thu held-out mà thật ra là chấm trên bài đã biết —
# hỏng im lặng, và hỏng theo chiều luôn đẹp lên.
def kiem_bo_ca_la_pool_v3(ca: list[dict]) -> None:
    """Bộ ca này có phải POOL V3 không? Không phải ⇒ NÉM.

    Nhận diện bằng **id**, không bằng số lượng: corpus V1/V2 mang id do tôi
    đặt (`ball_1`, `circumsphere`…), pool V3 mang id ô (`C1`–`C9`, `N1`–`N4`)
    do con dấu quy định.
    """
    from acceptance_integrity import IntegrityError

    ids = {c.get("id") for c in ca}
    la = ids & {c["id"] for c in CA}
    if la:
        raise IntegrityError(
            f"CORPUS PHÁT TRIỂN lọt vào chỗ pool V3: {sorted(la)}\n"
            f"`CA` là bộ V1/V2 đã chạy và đã công bố — chấm trên nó không "
            f"phải phép đo held-out.")


def nap_ca_v3() -> tuple[list[dict], list[dict], str]:
    """Đọc ĐÚNG những ca con dấu đã rút. Chưa rút ⇒ NÉM.

    Trả **ba** thứ, và ba vì mỗi thứ có đúng một việc:

    - `ca_chuan` — để **CHẠY**. `mong` đã chuẩn hoá thành `set`, vì
      `_chay_mot` chấm đáp số bằng phép tập con `mong <= set(dai_luong)`, và
      `list <= set` ném `TypeError`. Pool lưu `list` (JSON không có set), nên
      nếu không quy đổi ở đây thì mỗi ca dương sẽ nổ **sau** khi đã tiêu lượt
      analyze và lượt tổng hợp của nó.
    - `ca_tho` — để **NIÊM PHONG**. `seal_bo_ca` băm bằng `json.dumps`, mà
      `set` không JSON-hoá được. Giữ nguyên bản đọc từ pool cũng là thứ làm
      băm khớp con dấu byte-đối-byte.
    - `case_set_hash` — thẩm quyền băm bộ ca, lấy từ **con dấu**, không tự
      tính lại theo một đường khác.

    ⚠️ Hàm này **đọc nội dung ca** — nên chỉ evaluator độc lập được gọi nó, và
    chỉ sau khi seed đã ghi bất biến vào con dấu. Trước lúc đó `da_rut` là
    `null` và nó dừng ngay ở dòng đầu.
    """
    import copy
    import seal_curved_v3 as SC
    from acceptance_integrity import IntegrityError

    if not SC.DAU.exists():
        raise IntegrityError("CHƯA NIÊM PHONG pool V3")
    dau = json.loads(SC.DAU.read_text(encoding="utf-8"))
    if not dau.get("da_rut"):
        raise IntegrityError(
            "V3 CHƯA RÚT — `da_rut` còn null. Rút bằng seed từ NGƯỜI NGOÀI: "
            "`python scripts/seal_curved_v3.py --rut --seed <SỐ>`. Không có "
            "tập đo thì không lượt nào được phép bắt đầu.")
    bai = json.loads(SC.POOL.read_text(encoding="utf-8"))["bai"]
    if SC._bam(bai) != dau["pool_hash"]:
        raise IntegrityError("pool ĐÃ TRÔI khỏi con dấu — băm lệch")
    chon = set(dau["da_rut"])
    ra = [b for b in bai if b["id"] in chon]
    if len(ra) != len(chon):
        raise IntegrityError(
            f"con dấu rút {len(chon)} ca nhưng pool chỉ có {len(ra)}")
    if SC._bam(ra) != dau.get("case_set_hash"):
        raise IntegrityError("`case_set_hash` lệch — tập đo đã bị sửa sau rút")
    # Băm TRƯỚC khi chuẩn hoá: băm là của bản đọc từ pool, không của bản đã
    # quy đổi kiểu. Và chuẩn hoá trên BẢN SAO SÂU — sửa tại chỗ sẽ làm bản
    # thô lẫn băm ở trên nói về một thứ khác với thứ ta đang cầm.
    tho = copy.deepcopy(ra)
    chuan = copy.deepcopy(ra)
    for c in chuan:
        c["mong"] = set(c.get("mong") or ())
    return chuan, tho, dau["case_set_hash"]


# ══ TRẦN LƯỢT GỌI — DẪN TỪ CALL GRAPH, KHÔNG TỪ LƯỢT TRƯỚC ══════════════
def tran_luot_goi_v3(so_ca: int) -> int:
    """Trần CỨNG cho cả lượt V3, gồm **cả hai** chặng 8A và 8B.

        8A  — mỗi ca: 1 analyze + 1 tổng hợp (`MAX_…_ATTEMPTS` ghim xuống 1)
        8B  — worst case MỌI ca repair-eligible: 1 analyze + 3 tổng hợp

    Trần của một chặng là một cái phanh hụt: bản trước ghi
    `max_logical_calls = 3n + 5` — một con số có `+5` mà không ai giải thích
    được `5` từ đâu ra, và với n = 13 nó **thấp hơn** worst case thật.
    """
    import measurement_policy as MP

    tam = MP.derive_application_call_budget(
        selected_cases=so_ca, analyze_calls_per_case=1,
        synthesis_attempt_limit=1, calls_per_attempt=1)          # 8A
    sua = MP.derive_application_call_budget(
        selected_cases=so_ca, analyze_calls_per_case=1,
        synthesis_attempt_limit=_TRAN_SUA, calls_per_attempt=1)  # 8B
    return tam + sua


def _tran_sua() -> int:
    from app.ai.pipeline import MAX_SEMANTIC_PROGRAM_ATTEMPTS

    return MAX_SEMANTIC_PROGRAM_ATTEMPTS


_TRAN_SUA = 3          # = MAX_SEMANTIC_PROGRAM_ATTEMPTS, khoá bởi test_D4


# ══ TIỀN KIỂM TRƯỚC LƯỢT GỌI ĐẦU TIÊN ═══════════════════════════════════
def quet_bi_mat(tho: str) -> list[str]:
    """Artifact có mang khoá không. Chưa từng rò — và cách giữ nguyên như thế
    là có một guard, không phải có một thói quen."""
    import re

    mau = (r"AIza[0-9A-Za-z_\-]{35}",              # Google API key
           r"(?i)\b(api[_-]?key|authorization|bearer)\b\s*[:=]\s*['\"][^'\"]{8,}")
    return [m if isinstance(m, str) else m[0]
            for p in mau for m in re.findall(p, tho)]


def mo_luot_do_v3(thu_muc, *, run_id: str, ca: list[dict],
                  bo_qua_dirty: bool = False, gia_lap: bool = False):
    """Mọi thứ phải xong TRƯỚC lượt gọi provider đầu tiên. Mười bước, đúng thứ tự.

    Thứ tự không tuỳ tiện: manifest phải nằm trên đĩa **trước** lượt gọi đầu,
    nếu không nó là ảnh chụp của một hệ đã bị lượt gọi ấy chạm vào. Và nó phải
    được **đọc lại từ đĩa** rồi mới kiểm — kiểm bản trong bộ nhớ là kiểm thứ
    vừa tự tính ra, một phép so luôn đúng.
    """
    import measurement_policy as MP
    from acceptance_integrity import IntegrityError, mo_run

    thu_muc = Path(thu_muc)
    nguong, _bn = MP.nap_nguong()

    # ① + ② — con dấu, candidate, và tập đo đã rút hợp lệ chưa.
    #
    # `gia_lap` chỉ miễn **một** phép kiểm: "bộ ca có phải pool V3 không" —
    # một lượt diễn tập không có pool đã rút thì đúng là không có. Mọi phép
    # kiểm còn lại (con dấu, candidate, bốn băm, danh tính model, trần) chạy
    # y hệt lượt thật; miễn thêm cái nào nữa thì diễn tập không còn chứng minh
    # được gì về lượt thật.
    if not gia_lap:
        kiem_bo_ca_la_pool_v3(ca)
    _kiem_con_dau_va_candidate()
    # ③ + ④ + ⑤ — thư mục MỚI, `mo_run` ghi manifest nguyên khối
    mf = mo_run(
        thu_muc, run_id=run_id,
        muc_dich=("DIỄN TẬP TỔNG HỢP — KHÔNG phải phép đo" if gia_lap else
                  "CURVED_V3_LIVE_ACCEPTANCE — nghiệm thu hình cong, held-out"),
        runner=str(Path(__file__).resolve()), ca=ca,
        model=MP.cau_hinh_model_hien_tai(),
        chinh_sach_sua="acceptance_verdict.sua_duoc — đọc luật sản phẩm",
        ngan_sach_goi=tran_luot_goi_v3(len(ca)), bo_qua_dirty=bo_qua_dirty)

    # ⑥ + ⑦ + ⑧ + ⑨ — đọc LẠI từ đĩa rồi mới kiểm
    canh_gac_truoc_luot_goi(thu_muc, con_lai=mf.application_call_budget,
                            lan_dau=True)
    if mf.model_reproducibility not in ("PINNED", "LIMITED_ACCEPTED"):
        raise IntegrityError(
            f"danh tính model chưa đủ để chạy: {mf.model_reproducibility}\n  "
            + "\n  ".join(MP.san_sang_live_tu_cau_hinh(nguong)))
    return mf


def _kiem_con_dau_va_candidate() -> None:
    import freeze_evaluation_candidate as F
    import seal_curved_v3 as SC
    from acceptance_integrity import IntegrityError

    dau = json.loads(SC.DAU.read_text(encoding="utf-8"))
    he, _n = F.measured_system_hash()
    if he != dau["measured_system_hash"]:
        raise IntegrityError(
            f"hệ đã đổi sau khi niêm phong: {he[:16]}… ≠ "
            f"{dau['measured_system_hash'][:16]}… — niêm phong lại trước")


def canh_gac_truoc_luot_goi(thu_muc, *, con_lai: int,
                            lan_dau: bool = False) -> dict:
    """Chạy TRƯỚC **mỗi** lượt analyze/tổng hợp/sửa. Trôi ⇒ NÉM.

    Đọc lại manifest từ đĩa mỗi lượt, không cache: thứ ta canh là **file trên
    đĩa đổi giữa hai lượt gọi**, nên đọc một lần rồi giữ trong bộ nhớ là bỏ
    đúng thứ cần canh.

    KHÔNG tự cập nhật manifest cho khớp file mới. Manifest là ảnh chụp trước
    kết quả; sửa nó cho khớp hiện tại là xoá đúng bằng chứng của việc trôi.
    """
    import measurement_policy as MP
    from acceptance_integrity import (
        IntegrityError,
        doc_artifact,
        kiem_ghim_bo_do,
        kiem_manifest_du_truong,
        kiem_moi_truong,
    )

    thu_muc = Path(thu_muc)
    duong = thu_muc / "manifest.json"
    if not duong.exists():
        raise IntegrityError(
            f"chưa có manifest ở {duong} — không lượt gọi nào được phép đi "
            f"trước ảnh chụp danh tính")
    d = doc_artifact(duong)

    nguong, _bn = MP.nap_nguong()
    loi = kiem_manifest_du_truong(d) + kiem_ghim_bo_do(d)
    loi += [f"tham số giải mã: {x}" for x in
            MP.kiem_tham_so_giai_ma(d.get("decoding_parameters"), nguong)]
    tran = d.get("application_call_budget")
    if tran != tran_luot_goi_v3(len(d.get("seal", {}).get("ids", []))):
        loi.append(
            f"`application_call_budget` {tran} lệch trần dẫn xuất — trần "
            f"đổi SAU khi mở lượt đo là nới quota giữa chừng")
    if loi:
        _ghi_chan_doan(thu_muc, loi)
        raise IntegrityError("DANH TÍNH BỘ ĐO ĐÃ TRÔI:\n  " + "\n  ".join(loi))
    # `lan_dau` = lúc MỞ lượt đo, chưa có lượt gọi nào. "Còn 0" ở đó không
    # phải hết quota — nó chỉ có nghĩa khi ta sắp gọi. Kiểm ở đây sẽ chặn một
    # lượt diễn tập 0 ca vì một lý do không đúng.
    if not lan_dau:
        if con_lai <= 0:
            _ghi_chan_doan(thu_muc, ["hết trần lượt gọi"])
            raise IntegrityError(
                f"HẾT TRẦN lượt gọi (trần {tran}) — dừng để không đốt thêm "
                f"quota")
        kiem_moi_truong(d["moi_truong"], nhan="trước lượt gọi")
    return d


def _ghi_chan_doan(thu_muc: Path, loi: list[str]) -> None:
    """Trôi thì để lại artifact chẩn đoán, và **giữ nguyên** thứ đã ghi."""
    from acceptance_integrity import ARTIFACT_SCHEMA_VERSION, ghi_artifact

    p = Path(thu_muc) / "integrity_stop.json"
    if p.exists():                 # lần dừng đầu là lần đáng tin nhất
        return
    ghi_artifact(p, {"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                     "DUNG_VI": loi})


def ghi_bang_chung_quy_trach_nhiem(thu_muc, bc: dict) -> Path:
    """Đường lưu canonical cho artifact attribution (§H).

    Wave này chỉ **lắp đường**; chưa rút nên chưa có ca nào để phán. Ghi thêm
    `rubric_hash` vào chính artifact: bằng chứng phải mang theo bản rubric đã
    dùng, không trỏ suông sang "rubric hiện hành" — rubric hiện hành sẽ đổi.
    """
    import measurement_policy as MP
    from acceptance_integrity import (
        ARTIFACT_SCHEMA_VERSION,
        IntegrityError,
        ghi_artifact,
    )

    rubric, bam = MP.nap_rubric()
    if loi := MP.kiem_bang_chung_quy_trach_nhiem(bc, rubric):
        raise IntegrityError(
            "bằng chứng attribution KHÔNG đúng lược đồ:\n  " + "\n  ".join(loi))
    if not bc.get("evaluator"):
        raise IntegrityError("thiếu `evaluator` — adjudication phải có người")
    thu_muc = Path(thu_muc) / "attribution"
    thu_muc.mkdir(parents=True, exist_ok=True)
    p = thu_muc / f"{bc['case_id']}.json"
    n = 1
    while p.exists():              # sửa ⇒ VERSION MỚI, bản đầu giữ nguyên
        n += 1
        p = thu_muc / f"{bc['case_id']}.v{n}.json"
    ghi_artifact(p, {"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                     **bc, "rubric_hash": bam, "version": n})
    return p


def _phan_lop_loi(err: str | None) -> str:
    """Lỗi one-shot thuộc lớp nào — quyết định ca có repair-eligible không."""
    if not err:
        return "khong"
    h = err
    if "validation error" in h and "SemanticProgramSpec" in h:
        return "schema"
    if "không thực thi được" in h:
        return "ir_static"
    if "xuất xứ dữ liệu chưa đủ" in h:
        return "grounding"
    # Mã trong `KHONG_DUOC_SUA` — cố ý KHÔNG sửa.
    if "[" in h and "]" in h:
        return "grounding_khong_sua"
    return "khac"


async def _chay_mot(c: dict, api_key: str) -> dict[str, Any]:
    """Một ca đi ĐÚNG đường sản phẩm: analyze → tổng hợp → verify_and_compile."""
    from app.ai import pipeline
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
    from app.simulation.semantic_program.route import verify_and_compile

    ra: dict[str, Any] = {
        "id": c["id"], "hinh": c["hinh"], "loai": c["loai"], "de": c["de"],
        "contract_ok": False, "schema_ok": False, "executable": False,
        "dai_luong": [], "mong": sorted(c["mong"]), "dap_so_khop": None,
        "tu_choi": None, "loi": None, "lop_loi": "khong",
        "chuong_trinh": None, "dung_phep_cong": [],
        # QUAN TRẮC THUẦN — không tầng chấm nào đọc. Thiếu nó ở V1 là lý do
        # `cylinder_1` không tái dựng được để chứng nhận đường đầy đủ.
        "request_contract": None,
    }
    contract, err = await pipeline.stage_semantic_analyze(
        c["de"], api_key, domain=DOMAIN_HINH_HOC)
    if contract is None:
        ra.update(loi=err, lop_loi="analyze")
        return ra
    ra["contract_ok"] = True
    ra["request_contract"] = {
        "problem_text": contract.problem_text,
        "input_facts": [f.model_dump(mode="json") for f in contract.input_facts],
        "obligations": [o.model_dump(mode="json") for o in contract.obligations],
    }

    spec, serr = await pipeline.stage_semantic_program(
        c["de"], {}, api_key, contract, domain=DOMAIN_HINH_HOC)
    if spec is None:
        ra.update(loi=serr, lop_loi=_phan_lop_loi(serr))
        return ra
    ra["schema_ok"] = True
    ra["chuong_trinh"] = spec.model_dump(mode="json")
    ra["dung_phep_cong"] = sorted({
        st.get("curved_kind") for st in ra["chuong_trinh"].get("statements", [])
        if st.get("kind") == "construct_curved_solid"} - {None})

    outcome = verify_and_compile(contract, spec)
    ra["executable"] = bool(outcome.executable)

    # ══ CHẤM THEO ĐÚNG BA THẨM QUYỀN CỦA SẢN PHẨM ═══════════════════════
    #
    # Bản trước đọc đại lượng từ `outcome.envelope["scene3d"]` — một phép
    # chiếu LUÔN RỖNG, vì `route` cố ý không dựng cảnh. Xem
    # `cham_ca_theo_duong_san_pham` và `docs/V3_PRODUCT_PATH_PARITY_CORRECTION.md`.
    cham = cham_ca_theo_duong_san_pham(c, contract, spec, outcome,
                                       schema_ok=True)
    ra["cham"] = cham
    ra["dai_luong"] = sorted(cham["results"]["final_memory"].values())
    ra["canh_dai_luong"] = cham["results"]["scene_quantities"]
    ra["postconditions_pass"] = cham["execution"]["postconditions_pass"]
    ra["servable"] = cham["execution"]["servable"]
    ra["scene3d_pass"] = cham["results"]["scene3d_pass"]
    ra["canonical_verdict"] = cham["classification"]["canonical"]
    ra["legacy_runner_classification"] = cham["classification"]["legacy"]

    if not outcome.executable:
        ra.update(loi=getattr(outcome, "reason", None) or "không thực thi được",
                  lop_loi="runtime")
        return ra
    if c["mong"]:
        ra["dap_so_khop"] = cham["results"]["exact_answer_match"]
    return ra


#: Bảy lớp kết cục, đúng phân loại wave V2 đòi. Quy trách nhiệm cho ĐÚNG cột:
#: gộp một lỗi hệ vào cột mô hình là nói dối về khả năng của mô hình.
def phan_lop(r: dict) -> str:
    if r["loai"] == "am":
        return "HONEST_REFUSAL" if _cham_am(r)[0] else "FAKE_CONSTRUCTION"
    if r["executable"] and r["dap_so_khop"]:
        return "CORRECT_EXECUTABLE_IR"
    l = r["lop_loi"]
    if l == "schema":
        return "MODEL_SCHEMA_FAILURE"
    if l in ("grounding", "grounding_khong_sua"):
        return "MODEL_GROUNDING_FAILURE"
    if l == "ir_static":
        # `AMBIGUOUS_FIRST_BINDING` là một lớp riêng: nó nói mô hình ràng buộc
        # một tên bằng biểu thức không suy ra kiểu, khác hẳn "tham chiếu vật
        # chưa dựng".
        return ("MODEL_FIRST_BINDING_FAILURE"
                if "AMBIGUOUS_FIRST_BINDING" in (r["loi"] or "")
                else "MODEL_COMPOSITION_FAILURE")
    if l == "runtime":
        # Cổng phủ / cổng xuất xứ ở `verify_and_compile` là HỆ; lỗi kernel là
        # mô hình dựng sai hình.
        h = r["loi"] or ""
        if "không có đường tạo ra" in h:
            return "SYSTEM_FAILURE"
        if "không truy được về đề bài" in h:
            return "MODEL_GROUNDING_FAILURE"
        return "MODEL_COMPOSITION_FAILURE"
    if l == "analyze":
        return "SYSTEM_FAILURE"
    return "MODEL_COMPOSITION_FAILURE"


#: Mã lỗi CHẠM ĐÚNG ranh giới cong. Từ chối vì một lý do khác (vd điểm bịa)
#: vẫn là fail-closed, nhưng **không** phải bằng chứng cho ranh giới ấy.
_MA_RANH_GIOI_CONG = (
    "CURVED_SECTION_OUTSIDE_V1_CLOSURE", "CURVED_PLANE_TANGENT",
    "CURVED_PLANE_DOES_NOT_CUT", "intersect_line_curved",
    "does not match any of the",
)


def _cham_am(r: dict) -> tuple[bool, str]:
    """Ca ÂM đạt khi hệ TỪ CHỐI, không phải khi nó dựng gần đúng.

    Ba đường từ chối đều hợp lệ: mô hình tự nói không diễn đạt được (không sinh
    chương trình), cổng tĩnh/xuất xứ chặn, hoặc runtime từ chối bằng mã cong.
    Đường KHÔNG hợp lệ: một envelope chạy được kèm đáp số — nghĩa là hệ đã dựng
    một thứ nó không biểu diễn nổi.
    """
    if r["executable"]:
        if r["dai_luong"]:
            return False, f"DỰNG GẦN ĐÚNG — trả đại lượng {r['dai_luong']}"
        return False, "envelope chạy được cho một đề ngoài bao đóng"
    return True, f"từ chối ở lớp '{r['lop_loi']}'"


def cham_ranh_gioi(r: dict) -> bool:
    """Lời từ chối có CHẠM ĐÚNG ranh giới cong không?

    V1 cho thấy vì sao phải tách: `refuse_oblique` chết ở `UNANCHORED_DERIVED_
    ASSUMPTION` — fail-closed đúng, nhưng nó chưa bao giờ tới được chỗ hệ phải
    nói *"elip, không biểu diễn được"*. Tính nó là bằng chứng cho ranh giới
    conic sẽ là tự khen.
    """
    if r["executable"]:
        return False
    return any(m in (r["loi"] or "") for m in _MA_RANH_GIOI_CONG)


async def main_async(args) -> int:
    from app.ai import gemini, telemetry

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not api_key:
        print("DỪNG: cần ALLOW_LIVE_AI=1 và GEMINI_API_KEY", file=sys.stderr)
        return 2
    out = Path(args.out_dir)
    if out.exists() and any(out.iterdir()):
        print(f"DỪNG: {out} đã có nội dung — bộ đo KHÔNG ghi đè lượt cũ",
              file=sys.stderr)
        return 2

    # ══ NGUỒN BỘ CA — MỘT thẩm quyền duy nhất ═══════════════════════════
    #
    # `CA` (corpus phát triển V1/V2) KHÔNG còn với tới được từ đây. Bản trước
    # gán `chay = CA` và mọi consumer bên dưới đọc theo, nên lượt "nghiệm thu
    # held-out" thật ra chấm trên 9 đề đã công bố — hỏng im lặng, và hỏng theo
    # chiều luôn đẹp lên.
    ca_v3, ca_tho, case_set_hash = nap_ca_v3()
    kiem_bo_ca_la_pool_v3(ca_v3)
    theo_id = {c["id"]: c for c in ca_v3}

    # Lọc ca KHÔNG đụng bộ đầy đủ lẫn băm của nó: băm vẫn của BỘ ĐÃ RÚT, và
    # artifact ghi riêng tập con đã chạy. Nếu lọc mà băm cũng đổi theo thì mỗi
    # lượt probe lại sinh một "bộ ca" mới trông như hợp lệ, và không còn so
    # được lượt nào với lượt nào — đúng thứ `CASE_SET_HASH` sinh ra để chặn.
    chay = ca_v3
    if args.ca:
        muon = [x.strip() for x in args.ca.split(",") if x.strip()]
        if la := [x for x in muon if x not in theo_id]:
            print(f"DỪNG: id không có trong bộ ca đã rút: {la}", file=sys.stderr)
            return 2
        chay = [c for c in ca_v3 if c["id"] in muon]

    mt = _moi_truong(case_set_hash)
    print(f"MÔI TRƯỜNG  cache {mt['cache_version']} · "
          f"env {mt['semantic_environment_hash'][:16]}… · "
          f"capability {mt['stable_capability_hash'][:16]}…")
    print(f"BỘ CA       {len(ca_v3)} ca (pool V3 đã rút) · "
          f"băm {case_set_hash[:16]}…")
    la_probe = len(chay) != len(ca_v3)
    if la_probe:
        print(f"TẬP CON     {len(chay)}/{len(ca_v3)} · "
              f"{', '.join(c['id'] for c in chay)}  ← PROBE, không phải nghiệm thu")
    print()

    from app.ai import pipeline

    # ══ MỞ LƯỢT ĐO — manifest xuống đĩa TRƯỚC lượt gọi đầu tiên ═════════
    #
    # Trần đọc từ `tran_luot_goi_v3`, KHÔNG từ manifest: nếu `mo_luot_do_v3`
    # bị bỏ qua thì phải là **cổng canh** báo thiếu manifest, chứ không phải
    # một `AttributeError` đọc như lỗi hạ tầng.
    tran = tran_luot_goi_v3(len(chay))
    mo_luot_do_v3(out, run_id=out.name,
                  ca=[c for c in ca_tho if c["id"] in {x["id"] for x in chay}])

    telemetry.reset_usage()
    # Trần CỨNG, dẫn từ call graph (8A + 8B), không từ một công thức `3n+5`
    # không ai giải thích được. Một application call = một lượt `call_gemini`
    # ⇒ nó vào `max_logical_calls`. `max_api_calls` đếm request HTTP, tức đã
    # gồm retry transport, nên trần của nó là trần logic × `MAX_ATTEMPTS`.
    gemini.set_budget(gemini.ApiBudget(
        max_api_calls=tran * gemini.MAX_ATTEMPTS, max_logical_calls=tran))

    # ══ CỔNG CANH ĐÚNG RANH GIỚI APPLICATION CALL ═══════════════════════
    #
    # `_chay_mot` KHÔNG có đúng một lượt gọi: nó gọi analyze một lượt rồi
    # `stage_semantic_program`, mà hàm ấy lặp tới `MAX_SEMANTIC_PROGRAM_ATTEMPTS`
    # lượt bên trong. Đặt cổng trước `_chay_mot` sẽ bỏ sót mọi lượt sửa. Ranh
    # giới thật là `call_gemini` — một lượt gọi hàm ấy = một application call,
    # đúng thứ `ApiBudget.note_call` đếm. Bọc ở `scripts/`, KHÔNG đụng `app/`.
    con_lai = {"n": tran}

    async def _chay_co_canh_gac(c: dict) -> dict[str, Any]:
        """Bọc `call_gemini` quanh ĐÚNG một ca, rồi trả nguyên trạng.

        Tự khôi phục trong `finally` thay vì vá toàn cục một lần: một bản vá
        toàn cục sống sót qua ngoại lệ sẽ rò sang lượt sau, và thứ rò ra là
        một cổng canh trỏ vào thư mục của lượt đã kết thúc.
        """
        goc_call = pipeline.call_gemini

        async def _co_canh_gac(*a, **kw):
            canh_gac_truoc_luot_goi(out, con_lai=con_lai["n"])
            con_lai["n"] -= 1
            return await goc_call(*a, **kw)

        pipeline.call_gemini = _co_canh_gac
        try:
            return await _chay_mot(c, api_key)
        finally:
            pipeline.call_gemini = goc_call

    # ══ 8A — MỘT lượt, KHÔNG sửa ════════════════════════════════════════
    goc_tran = pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS = 1
    mot_luot: list[dict] = []
    dung_som = None
    try:
        for i, c in enumerate(chay, 1):
            print(f"[8A {i}/{len(chay)}] {c['id']}", flush=True)
            mot_luot.append(await _chay_co_canh_gac(c))
    except gemini.BudgetExceeded as e:
        dung_som = f"BUDGET_EXHAUSTED: {e}"
        print(dung_som)
    finally:
        pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS = goc_tran

    token_8a = telemetry.usage_report()
    # GHI NGAY, trước mọi lượt sửa. Con số one-shot không được phép đẹp lên.
    out.mkdir(parents=True, exist_ok=True)
    (out / "stage_8a_one_shot.json").write_text(json.dumps(
        {"moi_truong": mt, "dung_som": dung_som, "token": token_8a,
         "case_set_hash": case_set_hash,
         "tap_con": [c["id"] for c in chay] if la_probe else None,
         "ca": mot_luot}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n→ {out / 'stage_8a_one_shot.json'} (ghi TRƯỚC mọi lượt sửa)\n")

    # ══ 8B — chỉ sửa ca mà ĐƯỜNG SẢN PHẨM gửi lỗi ngược ═════════════════
    can_sua = [r for r in mot_luot
               if not r["executable"] and r["lop_loi"] in LOP_SUA_DUOC
               and r["loai"] == "duong"]
    print(f"REPAIR_ELIGIBLE_FAILURES {len(can_sua)}"
          + (f" — {[r['id'] for r in can_sua]}" if can_sua else ""))
    sua: list[dict] = []
    if can_sua and not args.chi_8a:
        for i, r in enumerate(can_sua, 1):
            # Tra trong TẬP V3 đã rút. Bản trước tra trong `CA`, và với id ô
            # (`C1`…`N4`) thì `next()` ném `StopIteration` — tức nhánh sửa
            # chết ngay ca đầu, SAU khi 8A đã tiêu hết lượt của nó.
            c = theo_id[r["id"]]
            print(f"[8B {i}/{len(can_sua)}] {c['id']}", flush=True)
            try:
                sua.append(await _chay_co_canh_gac(c))
            except gemini.BudgetExceeded as e:
                dung_som = f"BUDGET_EXHAUSTED (8B): {e}"
                print(dung_som)
                break
    gemini.set_budget(None)

    cuoi = {r["id"]: r for r in mot_luot}
    for r in sua:
        cuoi[r["id"]] = r

    def _dat(r: dict) -> bool:
        if r["loai"] == "am":
            return _cham_am(r)[0]
        return bool(r["executable"]) and r["dap_so_khop"] is True

    tk = telemetry.usage_report()
    # Telemetry dùng tên của Gemini (`prompt_tokens`/`candidates_tokens`/
    # `thoughts_tokens`). Bản V1 đọc `input`/`output` nên in ra 0 — lỗi BÁO
    # CÁO, không phải lỗi đo; tổng vẫn đúng. Sửa trước khi chạy V2.
    tong_in = sum(v.get("prompt_tokens", 0) for v in tk.values())
    tong_out = sum(v.get("candidates_tokens", 0) for v in tk.values())
    tong_nghi = sum(v.get("thoughts_tokens", 0) for v in tk.values())
    tong_goi = sum(v.get("calls", 0) for v in tk.values())
    dung_ok = [r for r in cuoi.values() if _dat(r) and r["loai"] == "duong"]
    bao = {
        "moi_truong": mt,
        # Mẫu số là SỐ CA THỰC CHẠY. Để `len(CA)` ở đây thì một probe 4 ca đọc
        # ra "4/9" và trông y hệt một lượt nghiệm thu hỏng 5 ca.
        "MODEL_CASES_TOTAL": len(chay),
        "CASE_SET_HASH": case_set_hash,
        "PROBE_SUBSET": [c["id"] for c in chay] if la_probe else None,
        "ONE_SHOT_CORRECT": sum(1 for r in mot_luot if _dat(r)),
        "ONE_SHOT_EXECUTABLE_IR": sum(1 for r in mot_luot if r["executable"]),
        "ONE_SHOT_HONEST_REFUSALS": sum(
            1 for r in mot_luot if r["loai"] == "am" and _cham_am(r)[0]),
        "REPAIR_ELIGIBLE_FAILURES": len(can_sua),
        "REPAIR_CALLS": len(sua),
        "FINAL_CORRECT_AFTER_REPAIR": sum(1 for r in cuoi.values() if _dat(r)),
        "TOTAL_APPLICATION_LLM_CALLS": tong_goi,
        "TOTAL_INPUT_TOKENS": tong_in,
        "TOTAL_OUTPUT_TOKENS": tong_out,
        "TOTAL_THOUGHT_TOKENS": tong_nghi,
        "TOTAL_TOKENS": telemetry.total_tokens(),
        "TOKENS_PER_CORRECT_EXECUTABLE_IR": (
            round(telemetry.total_tokens() / len(dung_ok)) if dung_ok else None),
        "theo_hinh": {
            h: {
                "duong_dat": sum(1 for r in cuoi.values()
                                 if r["hinh"] == h and r["loai"] == "duong"
                                 and _dat(r)),
                "duong_tong": sum(1 for r in chay
                                  if r["hinh"] == h and r["loai"] == "duong"),
            } for h in ("ball", "cylinder", "cone")
        },
        "FINAL_EXECUTABLE_IR": sum(1 for r in cuoi.values() if r["executable"]),
        "phan_lop": {r["id"]: phan_lop(r) for r in cuoi.values()},
        "am": {r["id"]: {"fail_closed": _cham_am(r)[0],
                         "cham_dung_ranh_gioi": cham_ranh_gioi(r),
                         "ly_do": _cham_am(r)[1]}
               for r in cuoi.values() if r["loai"] == "am"},
        "dung_som": dung_som,
        "token_theo_stage": tk,
    }
    (out / "curved_acceptance.json").write_text(json.dumps(
        {"tom_tat": bao, "one_shot": mot_luot, "sau_sua": sua,
         "cuoi": list(cuoi.values())}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print("\n── KẾT QUẢ ──")
    for k in ("MODEL_CASES_TOTAL", "ONE_SHOT_CORRECT", "ONE_SHOT_EXECUTABLE_IR",
              "ONE_SHOT_HONEST_REFUSALS", "REPAIR_ELIGIBLE_FAILURES",
              "REPAIR_CALLS", "FINAL_CORRECT_AFTER_REPAIR",
              "FINAL_EXECUTABLE_IR", "TOTAL_APPLICATION_LLM_CALLS",
              "TOTAL_INPUT_TOKENS", "TOTAL_OUTPUT_TOKENS",
              "TOTAL_THOUGHT_TOKENS", "TOTAL_TOKENS",
              "TOKENS_PER_CORRECT_EXECUTABLE_IR"):
        print(f"  {k:34} {bao[k]}")
    for h, v in bao["theo_hinh"].items():
        print(f"  {h:34} {v['duong_dat']}/{v['duong_tong']}")
    print("  ── phân lớp từng ca ──")
    for i, k in bao["phan_lop"].items():
        print(f"  {i:34} {k}")
    for i, m in bao["am"].items():
        print(f"  {i:34} fail_closed={m['fail_closed']} "
              f"chạm_ranh_giới={m['cham_dung_ranh_gioi']} · {m['ly_do']}")
    print(f"\n→ {out / 'curved_acceptance.json'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--chi-8a", action="store_true",
                   help="chỉ chạy one-shot, không sửa")
    p.add_argument("--ca", default=None,
                   help="chạy TẬP CON id (phẩy ngăn) — probe phát triển, "
                        "KHÔNG phải nghiệm thu; băm bộ ca giữ nguyên")
    # Khoá nằm ở `backend/.env` (bị gitignore) — cùng lối
    # `run_geometry_dev_evaluation.py` nạp nó.
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
