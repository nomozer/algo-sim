# -*- coding: utf-8 -*-
"""KHOÁ DANH TÍNH CACHE — gắn `CACHE_VERSION` vào môi trường sinh ngữ nghĩa.

    cd backend && .venv/Scripts/python.exe scripts/lock_cache_identity.py --verify
    cd backend && .venv/Scripts/python.exe scripts/lock_cache_identity.py

Không cờ ⇒ **ghi lại** khoá theo trạng thái hiện tại. `--verify` ⇒ thoát != 0
khi lệch. **0 lượt gọi model.**

─── VÌ SAO TỒN TẠI ──────────────────────────────────────────────────────────

Khoá cache runtime là *text đã chuẩn hoá + `CACHE_VERSION`* — và nó **không
đổi**. Nhưng `CACHE_VERSION` là một con số người phải nhớ tăng: đổi một prompt,
một lược đồ gửi cho mô hình, hay một chữ ký IR mà quên bump thì đề đã phân tích
tiếp tục được phục vụ bằng envelope sinh từ một phiên bản hệ không còn tồn tại,
và không gì phát hiện (`CURRENT_ARCHITECTURE_GAP_AUDIT §12`).

Khoá này chỉ ghi lại **một cặp**: phiên bản nào đi với môi trường nào. Test đọc
nó và đỏ khi cặp ấy lệch. Kho đã dùng đúng khuôn này cho lược đồ
(`test_schema_sync`) và cho bảng loại vẽ (`test_scene3d_ts_sync`).

─── VÌ SAO ĐẶT NGOÀI `app/` ────────────────────────────────────────────────

`MEASURED_SYSTEM_PATHS` gồm `backend/app`. Để khoá trong đó thì mỗi lần làm mới
nó lại làm **candidate đánh giá** hết hiệu lực — trộn hai cơ chế không liên
quan, và biến một lượt vá prompt thành một lượt đóng băng lại. Khoá là **vật
canh**, cùng hạng với `tests/`, nên nó sống ở `backend/`.

─── ĐIỀU NÓ KHÔNG LÀM ──────────────────────────────────────────────────────

Không tự bump `CACHE_VERSION`. Quyết định *"envelope cũ còn dùng được không"* là
quyết định của người, và một script đoán hộ sẽ đoán sai đúng vào lúc đắt nhất:
bump thừa thì vứt cache của cả kho, bump thiếu thì phục vụ kết quả cũ.

Quy trình đúng: sửa nguồn → test đỏ → **người xem lại** → bump nếu envelope cũ
mất hiệu lực → chạy script này → xanh.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

KHOA = BACKEND / "cache_identity.lock.json"


def anh_chup() -> dict:
    from app.main import CACHE_VERSION
    from app.runtime_identity import (
        semantic_environment_fingerprint,
        semantic_environment_hash,
    )

    return {
        "khai": "Cặp (CACHE_VERSION ↔ môi trường sinh ngữ nghĩa). Sinh bởi "
                "`scripts/lock_cache_identity.py`; đừng sửa tay. Khoá bởi "
                "`tests/test_cache_identity.py`.",
        "cache_version": CACHE_VERSION,
        "semantic_environment_hash": semantic_environment_hash(),
        # Từng thành phần — để lời từ chối nói được *cái nào* đổi, không chỉ
        # "băm lệch". Một thông điệp chỉ in hai chuỗi hex bắt người đọc tự đi
        # tìm, và họ sẽ bump cho xong.
        "components": semantic_environment_fingerprint(),
    }


def doc() -> dict | None:
    if not KHOA.exists():
        return None
    return json.loads(KHOA.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true",
                   help="chỉ kiểm, thoát != 0 khi lệch")
    a = p.parse_args()

    nay = anh_chup()
    cu = doc()

    if a.verify:
        if cu is None:
            print("✗ chưa có khoá — chạy script không cờ để tạo")
            return 1
        if (cu.get("cache_version") == nay["cache_version"]
                and cu.get("semantic_environment_hash")
                == nay["semantic_environment_hash"]):
            print(f"Khoá khớp · CACHE_VERSION {nay['cache_version']} · "
                  f"môi trường {nay['semantic_environment_hash'][:16]}…")
            return 0
        print("✗ LỆCH")
        print(f"    khoá:  version {cu.get('cache_version')} · "
              f"{str(cu.get('semantic_environment_hash'))[:16]}…")
        print(f"    hiện:  version {nay['cache_version']} · "
              f"{nay['semantic_environment_hash'][:16]}…")
        for k, v in nay["components"].items():
            truoc = (cu.get("components") or {}).get(k)
            if truoc != v:
                print(f"    đổi:   {k}  {str(truoc)[:16]}… → {v[:16]}…")
        return 1

    KHOA.write_text(json.dumps(nay, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"→ {KHOA.relative_to(BACKEND.parent)}")
    print(f"  CACHE_VERSION {nay['cache_version']}")
    print(f"  môi trường    {nay['semantic_environment_hash'][:16]}…")
    for k, v in nay["components"].items():
        print(f"    {k:20} {v[:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
