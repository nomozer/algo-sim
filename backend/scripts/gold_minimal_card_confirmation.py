# -*- coding: utf-8 -*-
"""Hai đề MỚI + hợp đồng cố định + gold cho
`MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`.

Câu hỏi đo: **thẻ hợp nhất (C) có giữ được cả hai thứ đã có bằng chứng rời —
`ratio` đúng và xuất xứ đúng — trên đề CHƯA TỪNG đo không?**

─── VÌ SAO LÀ MODULE RIÊNG, KHÔNG THÊM VÀO `gold_ratio_ab.CORPUS` ─────────

`gold_ratio_ab` công bố `CORPUS_HASH`, `CONTRACT_HASH`, `ORACLE_HASH`,
`GOLD_HASH`, và **bốn giá trị ấy đã nằm trong artifact BẤT BIẾN** của ba wave
trước. Thêm một ca vào `CORPUS` là làm mọi băm đó tính ra khác đi — tức phá
danh tính của những lượt đo đã đóng. Nên corpus mới ở file riêng, **tái dùng**
builder `_ca`/`_facts`/`_gold` chứ không chép lại chúng.

─── HAI ĐỀ, HAI LỚP QUAN HỆ KHÁC NHAU ────────────────────────────────────

    F1  AB = 18 · AM:MB = 5:4  ⇒ t(A→B) = 5/9 · MB = 8       (tỉ số trực tiếp)
    F2  GH = 14 · KH = 2·GK    ⇒ t(G→H) = 1/3 · KH = 28/3    (bội số đảo hướng)

`F2` cố ý có đáp số **hữu tỉ không nguyên**: nếu ở đâu đó trên đường đo còn
một phép làm tròn hay một lần đi qua `float`, ca này sẽ lộ ra, còn ca đáp số
nguyên thì không. `F1` cố ý là lớp mà thẻ A **đã sai hai lần** (`2/3` cho
`2:3`, `1/4` cho `4·`) — nó hỏi lại đúng chỗ delta `ratio` nhắm tới.

Cả hai đề **không cho toạ độ** và đều hỏi một ĐỘ DÀI, giữ đúng tính chất của
corpus gốc: đáp số **bất biến với hệ trục** mà mô hình tự chọn, nên oracle
không phụ thuộc quy ước đặt hình nào.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gold_ratio_ab import _bam, _ca  # noqa: E402  (TÁI DÙNG, không chép)

RA = (BACKEND.parent / "docs" / "evaluation" / "geometry"
      / "minimal-card-fresh-confirmation")

#: Hai đề, chưa xuất hiện trong bất kỳ phép đo A/B nào trước đây.
CORPUS = [
    _ca("f1", "ti_so_chia_doan_truc_tiep",
        "Cho đoạn thẳng AB có độ dài 18. Điểm M nằm trên đoạn AB sao cho "
        "AM : MB = 5 : 4. Tính độ dài MB.",
        "A", "B", 18, "M", "M thuộc AB và AM:MB = 5:4",
        "5/9", "4/9", "do_dai_mb", "B", "8"),
    _ca("f2", "boi_so_dao_huong",
        "Cho đoạn thẳng GH có độ dài 14. Điểm K nằm trên đoạn GH sao cho "
        "KH = 2·GK. Tính độ dài KH.",
        "G", "H", 14, "K", "K thuộc GH và KH = 2·GK",
        "1/3", "2/3", "do_dai_kh", "H", "28/3"),
]

CA_MOI = ("f1", "f2")

CORPUS_HASH = _bam([{k: c[k] for k in ("case_id", "feature", "problem_text")}
                    for c in CORPUS])
CONTRACT_HASH = _bam([c["request_contract"] for c in CORPUS])
ORACLE_HASH = _bam([{k: c[k] for k in
                     ("case_id", "t_theo_thu_tu", "exact_expected_results",
                      "diem_duoc_hoi", "moc_do")} for c in CORPUS])
GOLD_HASH = _bam([c["gold"] for c in CORPUS])

#: Lý do chọn gốc toạ độ — dùng cho gold, KHÔNG gửi cho mô hình.
LY_DO_GOC = ("Đặt hệ trục: chọn điểm này làm gốc toạ độ vì đề không cho toạ "
             "độ; trục Ox dọc theo đoạn thẳng đã cho.")

#: `case_id -> (gốc, đầu kia, điểm dẫn xuất, t thuận, witness, đáp số)`
BO = {
    "f1": ("A", "B", "M", "5/9", "do_dai_mb", "8"),
    "f2": ("G", "H", "K", "1/3", "do_dai_kh", "28/3"),
}
