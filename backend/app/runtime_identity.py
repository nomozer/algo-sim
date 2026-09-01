# -*- coding: utf-8 -*-
"""M17-RC1 §A — DANH TÍNH RUNTIME máy-đọc (chống "container chạy code cũ").

Vì sao cần: container backend từng chạy CACHE_VERSION "7" (thời M10) suốt nhiều
milestone mà KHÔNG gì báo — người dùng chỉ phát hiện khi thử một đề duyệt cây và
nó rơi xuống generic. Không có cách nào biết "runtime ≠ source" ngoài việc đọc
lỗi lạ. Module này phơi bày danh tính runtime để `runtime_doctor` so khớp.

Nguyên tắc: MỌI giá trị DẪN XUẤT từ registry sống — KHÔNG hard-code target/
family nào (thêm target thứ 20 tự vào hash, không phải sửa file này).
"""

from __future__ import annotations

import hashlib
import json
import os

def capability_fingerprint() -> dict:
    """Ảnh chụp NĂNG LỰC ĐANG CHẠY dùng để băm — ổn định, không phụ thuộc thứ
    tự dict hay chi tiết trình bày.

    ─── ĐỔI CHỦ THỂ, KHÔNG ĐỔI MỤC ĐÍCH (LEGACY_INFORMATICS_REMOVAL) ───────

    Bản trước băm `CATALOG` — 24 target Tin học, family, selector, menu LLM.
    Danh mục ấy đã gỡ, và băm một thứ không còn tồn tại thì `runtime_doctor`
    mất đúng khả năng nó sinh ra để có: phát hiện *"container đang chạy mã
    cũ"*.

    Thứ tương đương cho sản phẩm hiện tại là **thẩm quyền của IR hình học** —
    tập phép dựng, toán hạng, phép đo và kiểu bộ nhớ. Thêm một primitive, đổi
    một chữ ký, hẹp một kiểu toán hạng: hash đổi. Đó đúng là lớp thay đổi mà
    một container cũ sẽ im lặng bỏ qua.

    Nguyên tắc cũ giữ nguyên: MỌI giá trị DẪN XUẤT từ bảng sống, không
    hard-code tên phép nào.
    """
    import typing

    from app.simulation.semantic_program.contract import MemoryType
    from app.simulation.semantic_program.ir_static_check import (
        _CHU_KY, _KIEU_DUNG, _KIEU_DO, _TOAN_HANG_LENH,
    )
    from app.simulation.semantic_program.geometry_obligations import (
        GEOMETRY_CHECKERS,
    )

    return {
        "domain": "hinh_hoc",
        "bieu_thuc": {
            k: {"tham_so": [[t, sorted(kieu)] for t, kieu in ts], "tra_ve": ra}
            for k, (ts, ra) in sorted(_CHU_KY.items())
        },
        "cau_lenh_dung": dict(sorted(_KIEU_DUNG.items())),
        "toan_hang_lenh": {
            k: [[t, sorted(kieu), ds] for t, kieu, ds in ts]
            for k, ts in sorted(_TOAN_HANG_LENH.items())
        },
        "phep_do": {
            q: [sorted(of), sorted(wrt) if wrt else None]
            for q, (of, wrt) in sorted(_KIEU_DO.items())
        },
        "kieu_bo_nho": sorted(typing.get_args(MemoryType)),
        # Nghĩa vụ CÓ CHECKER — tức thứ hệ thật sự kiểm chứng được, không phải
        # thứ taxonomy khai là tồn tại.
        "nghia_vu": sorted(GEOMETRY_CHECKERS),
    }


def stable_capability_hash() -> str:
    payload = json.dumps(capability_fingerprint(), ensure_ascii=False,
                         sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _bam(x: str) -> str:
    """Băm nội dung, chuẩn hoá CRLF→LF.

    Bắt buộc: file skill nằm trên bind mount từ host Windows, nên Git đổi cách
    xuống dòng khi chạm file. Không chuẩn hoá thì vân tay lệch giữa host và
    container **mà nội dung không đổi một chữ** — một báo động giả, và báo động
    giả là cách nhanh nhất để một cổng bị tắt.
    """
    return hashlib.sha256(
        x.replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def skill_fingerprint() -> dict:
    """Vân tay prompt — ĐO THỨ TIẾN TRÌNH ĐANG GIỮ, không phải thứ trên đĩa.

    ─── VÌ SAO PHÂN BIỆT NÀY LÀ TOÀN BỘ GIÁ TRỊ CỦA HÀM ────────────────────

    `gemini.load_skill()` cache nội dung `.md` **trong tiến trình**. Sửa một
    prompt rồi gửi đề mà quên restart thì backend vẫn gửi cho LLM bản CŨ, và
    không gì báo. `runtime_doctor` trước bản này chỉ *cảnh báo bằng lời* về ca
    ấy — nó so `git_sha`, `CACHE_VERSION`, catalog hash, và cả ba đều KHỚP khi
    prompt cũ đang được dùng, vì cả ba đều không đọc file `.md` nào.

    Nếu hàm này đọc lại file trên đĩa để băm, nó sẽ báo "khớp" trong đúng cái ca
    nó sinh ra để bắt. Nên:

        tren_dia    băm MỌI file `skills/*.md` hiện có
        da_nap      băm nội dung `_skill_cache` — thứ THẬT SỰ gửi đi
        cu          skill nào đã nạp mà khác đĩa  ⇒ CẦN RESTART

    `da_nap` rỗng ở một tiến trình vừa khởi động là ĐÚNG, không phải lỗi: chưa
    lượt nào chạy thì chưa prompt nào bị giữ, và khi ấy không có gì cũ được.

    `grammar_card` đi kèm vì nó cũng là bề mặt prompt: nó SINH TỪ `contract.py`
    và ghép vào user message, nên đổi một model Pydantic là đổi thứ LLM đọc —
    mà không file `.md` nào bị sửa. Đó là ca dễ quên nhất.
    """
    from app.ai import gemini

    tren_dia = {
        f.stem: _bam(f.read_text(encoding="utf-8"))
        for f in sorted(gemini.SKILLS_DIR.glob("*.md"))
    }
    da_nap = {ten: _bam(noi_dung)
              for ten, noi_dung in sorted(gemini._skill_cache.items())}
    cu = sorted(t for t, h in da_nap.items() if tren_dia.get(t) != h)

    try:
        from app.simulation.semantic_program.grammar_card import grammar_card

        the = _bam(grammar_card())
    except Exception:  # noqa: BLE001 — chẩn đoán không được giết tiến trình
        the = "unavailable"

    return {
        "tren_dia": tren_dia,
        "da_nap": da_nap,
        "cu": cu,
        "grammar_card": the,
        # Một con số để so nhanh. KHÔNG dùng nó thay `cu`: hai vân tay tổng thể
        # khớp nhau vẫn có thể che một skill đã nạp bị cũ, vì `da_nap` là tập con.
        "tong": _bam(json.dumps(tren_dia, sort_keys=True)),
    }


def runtime_identity() -> dict:
    """Danh tính runtime máy-đọc. `git_sha`/`build_timestamp` được BAKE lúc build
    image (build-arg → env); ngoài Docker thì báo "unknown" trung thực thay vì
    đoán — doctor sẽ xử lý riêng trường hợp đó."""
    # Nhập muộn: main.py import module này, tránh vòng import.
    from app.main import CACHE_VERSION, semantic_route_mode

    kn = capability_fingerprint()
    return {
        "git_sha": os.getenv("ALGOSIM_GIT_SHA", "unknown"),
        "build_timestamp": os.getenv("ALGOSIM_BUILD_TIME", "unknown"),
        "cache_version": CACHE_VERSION,
        # ─── ĐẾM NĂNG LỰC HÌNH HỌC, thay cho đếm target Tin học ────────────
        #
        # `family_count`/`target_count`/`registered_*_ids` cũ đếm 24 target của
        # danh mục đã gỡ. Giữ những khoá ấy mà cho chúng giá trị 0 là để lại một
        # con số đọc như "hệ mất hết năng lực"; bỏ hẳn và đếm đúng thứ đang chạy
        # thì `runtime_doctor` mới nói được điều nó sinh ra để nói.
        "domain": "hinh_hoc",
        "expression_count": len(kn["bieu_thuc"]),
        "construct_statement_count": len(kn["cau_lenh_dung"]),
        "measure_count": len(kn["phep_do"]),
        "obligation_count": len(kn["nghia_vu"]),
        "stable_capability_hash": stable_capability_hash(),
        # Vân tay PROMPT. Ba trường trước đó (`git_sha`, `cache_version`,
        # `stable_capability_hash`) đều KHỚP khi một prompt cũ đang được gửi đi,
        # vì không trường nào trong chúng đọc một file `.md`.
        "skills": skill_fingerprint(),
        # ─── CỜ VẬN HÀNH — KHÔNG phải danh tính mã, nhưng quyết định HÀNH VI ──
        #
        # `runtime_doctor` từng báo PASS trọn vẹn trong khi `SEMANTIC_ROUTE_MODE`
        # là `off`, tức route sinh KHÔNG CHẠY và mọi đề hình học rơi xuống
        # classifier. Mã khớp từng bit, hành vi thì khác hẳn — và "PASS" đọc
        # thành "mọi thứ đúng".
        #
        # Đo được 2026-08-25: một lượt `docker compose up -d --build` không kèm
        # env kéo cờ về mặc định `off` mà không gì báo. Chúng phải HIỆN RA.
        # Doctor không phán chúng đúng/sai — `off` là lựa chọn hợp lệ cho bản
        # chạy thật — nhưng người đọc phải thấy, và `--doi-mode` cho phép khai
        # kỳ vọng khi lượt này là một lượt ĐO.
        "semantic_route_mode": semantic_route_mode(),
        "semantic_telemetry": os.getenv("SEMANTIC_TELEMETRY", "0"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "dev_reload": os.getenv("DEV_RELOAD", "0"),
        # `simulation_id` DUY NHẤT sản phẩm phát ra. Không còn danh mục target,
        # nên không còn `registered_target_ids`/`family_ids`/`selector_tokens`.
        "simulation_id": "generic.semantic_program",
        "expressions": sorted(kn["bieu_thuc"]),
        "construct_statements": sorted(kn["cau_lenh_dung"]),
        "measures": sorted(kn["phep_do"]),
    }
