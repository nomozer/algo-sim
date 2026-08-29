# -*- coding: utf-8 -*-
"""Bằng chứng Phase 7B chính thức là BẤT BIẾN, và không được dùng làm dữ liệu
phát triển.

Hai luật khác nhau, hai lý do khác nhau.

**Bất biến** — con số của lượt đo chỉ có nghĩa khi chứng minh được là nó
không bị sửa sau khi người ta thấy nó. `BASELINE_LOCK.json` băm từng file
thô; sửa một byte là đỏ ở đây.

**Không làm dữ liệu phát triển** — cái này tinh vi hơn và là chỗ dễ mất
nhất. Wave sau sẽ sửa đúng những chỗ Phase 7B chỉ ra, và lối tiện nhất là
lấy luôn `problem_text`/`generated_program` của 20 bài ấy làm ca hồi quy.
Làm thế thì tập held-out biến thành tập DEV **một cách không thể hoàn tác**:
mọi lượt đo sau trên chính 20 bài ấy sẽ đo một hệ đã được vá theo chúng.
Taxonomy được phép dẫn đường (*"họ GÓC hỏng"*), nhưng bằng chứng sửa phải
đến từ DEV độc lập.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GEO = ROOT / "docs" / "evaluation" / "geometry"
RA = GEO / "phase7b-official"
LOCK = RA / "BASELINE_LOCK.json"


def _bam(f: Path) -> str:
    return hashlib.sha256(f.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@pytest.fixture(scope="module")
def khoa() -> dict:
    if not LOCK.exists():
        pytest.skip("chưa có BASELINE_LOCK.json")
    return json.loads(LOCK.read_text(encoding="utf-8"))


def test_moi_artifact_chinh_thuc_KHONG_DOI(khoa):
    lech = []
    for ten, b in khoa["bam_tung_file"].items():
        f = RA / ten
        if not f.exists():
            lech.append(f"{ten}: BỊ XOÁ")
        elif _bam(f) != b:
            lech.append(f"{ten}: nội dung ĐỔI")
    assert not lech, lech


def test_KHONG_them_bot_file_nao_trong_thu_muc_chinh_thuc(khoa):
    """Thêm file cũng là đổi bằng chứng: một `*-lan4.json` xuất hiện sau đó sẽ
    được bộ chấm đọc như một lượt của cùng lượt đo."""
    co = {f.name for f in RA.glob("*.json")} - {LOCK.name}
    assert co == set(khoa["bam_tung_file"]), {
        "thêm": sorted(co - set(khoa["bam_tung_file"])),
        "mất": sorted(set(khoa["bam_tung_file"]) - co)}


def test_bam_tong_khop_bam_tung_file(khoa):
    """Băm tổng phải DẪN từ bảng băm, không phải một chuỗi ghi tay cạnh nó."""
    assert khoa["bam_tong"] == hashlib.sha256(
        json.dumps(khoa["bam_tung_file"], sort_keys=True).encode("utf-8")
    ).hexdigest()


def test_co_SCORER_ERRATUM_va_no_khai_du_sau_muc():
    f = RA / "SCORER_ERRATUM.md"
    assert f.exists(), "sửa bộ chấm sau khi thấy số mà không có erratum"
    src = f.read_text(encoding="utf-8")
    for muc in ("Định nghĩa đã đăng ký", "Phép sửa", "Giá trị nào ĐỔI",
                "Giá trị nào KHÔNG ĐỔI", "Không lượt gọi model nào lặp lại"):
        assert muc in src, f"erratum thiếu mục {muc!r}"
    # Con số tầng A phải nằm nguyên trong erratum — đó là lời hứa kiểm được.
    for x in ("20/42", "6/33", "14/23", "32/42", "7/14"):
        assert x in src, f"erratum không nêu lại số tầng A {x}"


#: Thư mục/`glob` mà một ca hồi quy KHÔNG được trỏ tới.
_CAM = ("phase7b-official", "holdout/cases.json", "holdout/pool.json")


def test_KHONG_test_nao_doc_artifact_chinh_thuc_lam_du_lieu():
    """Test hồi quy đọc `phase7b-official/` là biến held-out thành DEV.

    File này tự loại mình: nó đọc thư mục ấy để KIỂM TÍNH BẤT BIẾN, không để
    lấy đề hay chương trình làm đầu vào.
    """
    minh = Path(__file__).name
    pham = []
    for f in (ROOT / "backend" / "tests").rglob("*.py"):
        if f.name == minh:
            continue
        src = f.read_text(encoding="utf-8", errors="replace")
        for x in _CAM:
            if x in src and "phase7b-official" in x:
                pham.append(f"{f.relative_to(ROOT)}: đọc {x}")
    assert not pham, pham


def test_ca_HOI_QUY_cua_wave_sau_dung_DEV_khong_dung_hp(khoa):
    """Không ca hồi quy nào được mang `problem_text` của 20 bài chính thức.

    So bằng ĐỀ, không bằng `case_id`: đổi tên id là việc của một dòng, còn
    đề thì mới là thứ làm hệ được vá theo tập đo.
    """
    cj = json.loads((GEO / "holdout" / "cases.json").read_text(encoding="utf-8"))
    de = {re.sub(r"\s+", " ", c["problem_text"]).strip().lower()
          for c in (cj["cases"] if isinstance(cj, dict) else cj)}
    dev = GEO / "dev" / "cases.json"
    d = json.loads(dev.read_text(encoding="utf-8"))
    trung = [c["case_id"] for c in d["cases"]
             if re.sub(r"\s+", " ", c["problem_text"]).strip().lower() in de]
    assert not trung, f"DEV mang đề của tập chính thức: {trung}"
