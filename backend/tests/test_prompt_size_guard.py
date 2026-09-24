# -*- coding: utf-8 -*-
"""Cổng TĨNH chặn prompt phình — hard-fail build (spec §6.4).

Vì sao cổng nằm ở tầng tĩnh chứ không ở số live: số live nhiễu và tốn tiền, để
nó gác cổng mặc định là vừa đắt vừa hay đỏ oan. Live token regression chỉ BÁO
CÁO. Còn kích thước prompt thì tất định, không tốn call, và đo đúng thứ đang
trôi: mỗi lần vá lỗi bằng cách nhồi thêm một dòng vào prompt.

Chi phí thật của một bản vá prompt gồm HAI phần: prompt to hơn vĩnh viễn, CỘNG
một đợt gọi lại toàn bộ vì sửa `skills/*.md` buộc bump `CACHE_VERSION` (xoá sạch
exact-cache). Cổng này chặn phần thứ nhất.

NGƯỠNG: chốt 2026-08-20 ở mức ~5% trên kích thước hiện tại. Hạ được thì hạ.
TĂNG ngưỡng phải kèm lý do trong commit message — và trước khi tăng, hãy hỏi
luật vừa thêm có mã hoá được xuống schema/validator không (spec §6.3.1).
"""
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[1] / "app" / "ai" / "skills"

#: ⚠️ Mọi số dưới đây là **byte LF** (xem `_byte_lf`). Chúng được quy đổi
#: 2026-09-03 từ số `st_size` cũ, GIỮ NGUYÊN khoảng dôi mà từng tác giả đã
#: định — không nới cho ai một byte nào. Trước đó cổng đo `st_size`, và một số
#: file trên đĩa dùng CRLF còn số khác dùng LF, nên cổng so những thứ không
#: cùng đơn vị: `geometry_program_generator.md` đọc 5612 ở một nơi và 5707 ở
#: nơi khác, cùng một commit.
BUDGET_BYTES: dict[str, int] = {
    "adapt.md": 1500,
    # MIỀN HÌNH HỌC KHÔNG GIAN (2026-08-24). Ngân sách LỚN HƠN
    # `semantic_program.md` (2500) có lý do, không phải vì viết dài tay:
    #
    #   1. Đề hình học **không cho toạ độ**. Prompt phải dạy cách ĐẶT HỆ TOẠ ĐỘ
    #      — thứ không mã hoá được vào schema, và không có nó thì mô hình chọn
    #      hệ tuỳ tiện rồi ra số vô tỉ mà `Fraction` không nhận.
    #   2. Ranh giới R0 ở miền này cần VÍ DỤ ĐỐI CHIẾU đúng/sai, vì cám dỗ tự
    #      điền toạ độ kết quả mạnh hơn hẳn miền thuật toán: model *biết* giao
    #      tuyến là gì và rất muốn nói ra.
    #   3. Bảng "đề hỏi gì → nghĩa vụ nào" cho 8 nghĩa vụ.
    #
    # ⚠️ Ngân sách này KHÔNG phải chỗ để thêm luật mỗi lần một ca hỏng. Luật nào
    # mã hoá được thì để validator/kernel giữ — đó là bài học `RULES §3c`
    # (DEEP_HARDENING) và bằng chứng lượt SEALED #1: 30/40 thất bại là do hợp
    # đồng cứng nhắc, KHÔNG phải do prompt.
    # 4800 → 5700 (2026-09-03, PHASE_3_CURVED_PRODUCT_INTEGRATION): 4794 →
    # 5612, tức **+818**, cho việc mở HỌ HÌNH CONG và thu hẹp lời từ chối cũ.
    #
    # ⚠️ Ba khoản đều rơi vào ngoại lệ mà chính ngân sách này thừa nhận —
    # **luật KHÔNG mã hoá được thành RÀNG BUỘC HỮU ÍCH** — và lý do là một tính
    # chất kiến trúc, không phải sự tiện tay:
    #
    #   `construct_curved_solid` thẩm định ở RUNTIME (`CurvedSolid.__post_init__`
    #   kiểm vành ⊥ trục), còn vòng sửa ≤3 lượt đóng ở tầng TĨNH. Nên một lỗi
    #   chọn hệ trục **giết cả ca, không có lượt sửa nào**. Với những luật ấy,
    #   "để validator giữ" không phải một lựa chọn rẻ hơn — nó là mất ca.
    #
    #   1. vành ⊥ trục, phải đúng NGAY LÚC CHỌN HỆ TOẠ ĐỘ  (~180 byte)
    #   2. thiết diện qua trục = đa giác, không có `kind` riêng  (~200 byte)
    #      Không nói thì mô hình từ chối một bài nó LÀM ĐƯỢC, và lời từ chối
    #      của runtime không bao giờ nổ để dạy lại.
    #   3. ranh giới còn lại (xiên · đường–cong · cong–cong · tròn xoay · quỹ
    #      tích) thay cho một câu từ chối rộng đã sai  (~440 byte)
    #
    # Khoản 3 phần lớn là VIẾT LẠI, không phải thêm: câu cũ *"đề cần mặt cầu…
    # nói thẳng là không diễn đạt được"* nay mâu thuẫn với thẻ văn phạm.
    # ⚠️ Quy đổi cơ học cho ra 5605 và **âm 7 byte dôi** — vì trần 5700 của
    # Phase 3 vốn đặt từ một số ĐO BẰNG LF (5612), rồi cổng lại so bằng
    # `st_size` (5707). Tức trần ấy đã bị vượt ngay từ lúc đặt, và không ai
    # thấy vì hai bên đo hai đơn vị. 5700 là con số tác giả THẬT SỰ định; giữ
    # nó, và đây là sửa một lỗi cũ chứ không phải nới thêm.
    "geometry_program_generator.md": 5700,
    # Bề mặt `analyze` của MIỀN HÌNH HỌC (Wave 2, 2026-08-24). Tách khỏi
    # `semantic_analyze.md` vì cùng lý do `semantic_analyze.md` tách khỏi
    # `analyze.md`: trộn vào thì mọi đề Tin học phải trả tiền cho bảng dịch
    # "câu hỏi hình học → nghĩa vụ nào", và mọi đề hình học phải đọc luật
    # `cmp`/`transform`/`prescribed_procedure` mà nó không bao giờ dùng.
    #
    # LỚN HƠN `semantic_analyze.md` (2200) vì ba thứ không mã hoá được:
    #   1. Dữ kiện hình học có HAI DẠNG — số đo và quan hệ (`SA ⊥ (ABCD)`).
    #      Bảng kiểu không diễn đạt được "một mệnh đề quan hệ".
    #   2. Bảng dịch 8 nghĩa vụ, kèm cột `witness` — vì witness của nhóm quan
    #      hệ là ĐỐI TƯỢNG còn của nhóm đại lượng là CON SỐ. Đây chính là chỗ
    #      Phase 5 đo được `obligation_match` 3/6.
    #   3. Luật "hệ toạ độ KHÔNG phải dữ kiện" — nếu không nói, `analyze` khai
    #      `A = (0,0,0)` thành một `input_fact`, và cả chuỗi provenance phía
    #      sau ghim vào một dữ kiện không có trong đề.
    # 4200 → 4600 (2026-09-03, RADIUS_OBLIGATION_COVERAGE): 4196 → 4517 TRÊN
    # ĐĨA, tức **+321**, cho ĐÚNG MỘT khái niệm nghĩa vụ — `radius`.
    #
    # ⚠️ Con số ở đây là `st_size`, tức ĐÃ TÍNH CRLF — file nằm trên bind mount
    # từ Windows. Đo bằng `len(text.encode())` sẽ ra 4442 và lệch 75 byte so
    # với thứ cổng thật sự so; ghi rõ để lần sau không ai trừ nhầm.
    #
    # Vì sao không để validator giữ: `analyze` chọn nghĩa vụ từ một enum, và
    # enum một mình **không nói được** khi nào dùng cái nào. `CURVED_MODEL_
    # ACCEPTANCE_V2` đo được cái giá của sự im lặng ấy bằng quota thật: hai ca
    # (`ball_1`, `circumsphere`) sinh chương trình ĐÚNG rồi chết ở cổng phủ, vì
    # mô hình ép *"tính bán kính"* vào `distance` — nghĩa vụ gần nhất mà nó có
    # từ để gọi.
    #
    #   dòng bảng dịch        ~75 byte
    #   câu phân biệt         ~170 byte — và nó nói bằng **số toán hạng**
    #                         (một vật ↔ hai vật), không bằng chữ trong đề.
    #                         Dạy theo chữ là đúng cái bẫy `measure_contract`
    #                         §② đã phải đi dọn với `angle_cos`.
    # 4525 → 5350 (2026-09-21, `FACT_GRAPH_CONTRACT_EXTENSION`): +786 byte cho
    # mục `## geometric_relations`, và câu hỏi bắt buộc của ngân sách này —
    # *"mã hoá xuống schema được không"* — đã được hỏi TRƯỚC, không phải sau:
    #
    #   · tập loại quan hệ            → `enum` của `kind`
    #   · đường 2 đỉnh, mặt 3 đỉnh     → `minItems`/`maxItems`
    #   · phải ghim về một mục dữ kiện → `required: [..., source_fact_id]`
    #   · đổi thứ tự đỉnh không sao    → `description` của từng ô
    #
    # Bản đầu của mục này dài 1263 byte vì nó chép lại cả bốn điều trên; cắt
    # xuống còn ĐÚNG ba điều schema không nói được — `source_fact_id` trỏ đi
    # đâu, nghĩa vận hành của `model_assumption`, và *"đừng liệt kê hệ quả"*.
    # Điều thứ ba là thứ đắt nhất nếu im lặng: mô hình liệt kê quan hệ suy ra
    # thì chúng vào graph dưới nhãn `GIVEN`, và một hệ quả hoá thành dữ kiện.
    #
    # +70 byte so với con số 5300 đặt lúc đầu wave: `test_V` đòi prompt NÊU TÊN
    # hai `kind`, và đòi đúng — `enum` chỉ tới mô hình qua lược đồ, còn câu
    # *"dùng cái nào khi nào"* thì không. Ghi ra con số thật thay vì gọt văn cho
    # vừa một trần đã lỡ công bố. Dôi thực tế: 39 byte.
    # 5350 → 5700 (2026-09-21, `ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX`):
    # +361 byte cho MỘT gạch đầu dòng — lớp `DEFINITIONAL_NORMALIZATION`. Câu
    # hỏi bắt buộc của ngân sách này đã được hỏi TRƯỚC, và câu trả lời là KHÔNG,
    # vì một lý do KIẾN TRÚC chứ không phải sự tiện tay:
    #
    #   · **Schema không nói được.** Lược đồ ràng buộc HÌNH DẠNG của thứ mô hình
    #     viết ra (`enum` của `kind`, arity đường/mặt, `required: source_fact_id`).
    #     Nó không có chỗ nào diễn đạt *"gặp cách viết này thì phát quan hệ kia"* —
    #     đó là một ánh xạ từ NGỮ NGHĨA câu văn sang ô có cấu trúc.
    #   · **Validator càng không.** Muốn cưỡng chế thì validator phải đọc
    #     `problem_text` tìm chữ *"vuông tại"*. Nhưng `contract_adapter/2` vừa GỠ
    #     HẲN bộ đọc từ vựng văn bản, có chủ đích: *"thiếu quan hệ có cấu trúc thì
    #     từ chối, kể cả khi `problem_text` nói rõ"*. Thêm lại một text parser để
    #     giữ đúng luật này là phá chính bất biến mà `FACT_GRAPH_CONTRACT_EXTENSION`
    #     dựng lên — và là điều đặc tả wave này cấm thẳng.
    #
    # Tức khoản này rơi đúng vào ngoại lệ mà ngân sách tự thừa nhận: **luật KHÔNG
    # mã hoá được thành ràng buộc hữu ích**.
    #
    # Không gọt văn cho vừa trần: khối luật là bản ĐÃ ĐĂNG KÝ ở artifact của
    # `ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS`, và năm mệnh đề của nó đều
    # chở một điều lược đồ không nói được — lớp ngữ nghĩa mới · ánh xạ cách viết
    # → quan hệ · khi nào `model_assumption` là `false` · câu *"không phải bạn tự
    # suy"* (thứ vô hiệu hoá luật L34/L36 vốn sẽ nuốt mất nó) · và dạng *"góc …
    # bằng 90°"*. Bỏ mệnh đề nào cũng mất một ca trong ma trận 13 cách viết.
    #
    # ⚠️ Cổng này bắt được wave: tập test đã chạy trước khi commit KHÔNG có nó,
    # và chỉ lượt full backend trong worktree sạch mới làm nó đỏ. Ghi lại để lần
    # sau ai sửa `skills/*.md` thì chạy `tests/test_prompt_size_guard.py` ngay.
    # 5700 → 6350 (2026-09-22, PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE):
    # thêm mục solid_topology cho lăng trụ đứng (+608 byte: 5700 → 6308 / 6350).
    "geometry_analyze.md": 6350,
    "analyze.md": 6900,
    "classify.md": 4520,
    "edit.md": 3550,
    "explain.md": 1550,
    # Bề mặt `analyze` RIÊNG của route ngữ nghĩa (2026-08-21). Tách khỏi
    # `analyze.md` có chủ đích — trộn vào đó thì mọi đề đi đường module cũng
    # phải trả tiền cho từ vựng nghĩa vụ mà chúng không dùng.
    # 1950 → 2200 (2026-08-23): luật "tham số phân biệt BẮT BUỘC". Đo được trên
    # DEV `dev_01` (tìm max): nghĩa vụ `extremum` phát ra KHÔNG có `cmp`, checker
    # âm thầm hiểu thành `min` rồi báo *"witness = 35, đúng phải là 27"* — kết
    # tội một chương trình ĐÚNG. `cmp` vốn đã có trong schema (nullable) nhưng
    # prompt chưa bao giờ nhắc, nên model không có lý do gì để điền.
    "semantic_analyze.md": 2161,
    # HẠ 2100 → 1800 (2026-08-20). Bản viết lại bỏ phần schema đã cưỡng chế
    # (danh sách statement/expression/primitive) và còn 1.675B, nhỏ hơn bản gốc
    # 1.998B. Ghi lại vì bản nháp đầu của chính lượt này lại PHÌNH lên 2.131B —
    # gỡ enum xong rồi nhồi thêm văn xuôi. Cổng này bắt được, nên nó có ích.
    # NÂNG 1800 → 2500 (2026-08-23). KHÔNG phải nới để nhồi văn xuôi — đúng thứ
    # comment trên cảnh báo. Bốn lượt probe E2E trên đề "kiểm tra chuỗi ngoặc
    # bằng ngăn xếp" (route `serve`, API thật) đo được mỗi luật gỡ đúng một lớp
    # lỗi, số lỗi cú pháp đi 4 → 2 → 1 → 0:
    #   · `container` là TÊN đã khai (literal đặt thẳng ⇒ trỏ vùng nhớ không có)
    #   · `pop`/`dequeue` là CÂU LỆNH có `dest_var`; chỉ `peek` là biểu thức
    #   · chuỗi ĐƯỢC DUYỆT khai `array` ký tự, không khai `str`
    # Đã thử chỗ rẻ hơn trước: thẻ văn phạm (`grammar_card`) VỐN ĐÃ in
    # `pop: container:tên dest_var?:tên` và `container:tên` — tức dữ kiện dẫn
    # xuất có sẵn mà model vẫn viết sai. Thiếu là GỢI Ý CÁCH DÙNG, thứ docstring
    # của chính thẻ xếp về `skills/*.md`. Nên trần đổi, không phải chỗ đặt đổi.
    # 2500 → 2850 (cùng lượt): luật thứ tư — `visual_bindings` phải phủ container
    # BIẾN ĐỘNG và witness của mỗi nghĩa vụ. Đề "đảo dãy bằng ngăn xếp" chạy
    # được (executable, 8 bước) rồi bị `learner_surface` chặn với đúng câu
    # "mô phỏng chạy xong mà học sinh không thấy đáp án". Đây là luật SƯ PHẠM,
    # không mã hoá thành canonicalization được: cổng biết đòi gì, nhưng model
    # chỉ biết sau khi đã trượt.
    "semantic_program.md": 2804,
    "simulate.md": 1450,
    # 1050 → 1970 (2026-09-13, PHOTO_PROBLEM_TO_SCENE_END_TO_END): 1874 byte.
    # NHIỆM VỤ ĐỔI, không phải vá: từ "chép thành văn bản tự do" (đề Tin học)
    # sang BẢN GHI CÓ CẤU TRÚC cho hình học không gian. Ba nhóm luật thêm vào
    # KHÔNG mã hoá được xuống lược đồ — lược đồ chỉ giữ được HÌNH DẠNG bản ghi:
    #   1. ký tự dễ nhầm (O/0 · S/5 · I/l/1) phải được KHAI, không tự chọn im lặng;
    #   2. hình minh hoạ không được dùng để ước lượng toạ độ/độ dài/góc;
    #   3. chữ trong ảnh là DỮ LIỆU, không phải chỉ dẫn (chống tiêm prompt qua ảnh).
    # Phán quyết từ chối thì KHÔNG nằm trong prompt: `assess_extraction` giữ nó.
    "transcribe.md": 1970,
}


def _byte_lf(name: str) -> int:
    """Kích thước prompt, CHUẨN HOÁ CRLF→LF.

    ⚠️ Bản trước dùng `stat().st_size`, và nó **phụ thuộc cách Git checkout
    xuống dòng**: file nằm trên bind mount từ Windows, nên cùng một commit cho
    ra 5612 byte ở nơi này và 5707 ở nơi khác. Cổng vì thế xanh hay đỏ tuỳ máy
    — và một cổng như thế còn tệ hơn không có cổng, vì nó dạy người ta rằng đỏ
    là chuyện của môi trường.

    Cùng lý do `runtime_identity._bam` chuẩn hoá: đo NỘI DUNG, không đo cách
    lưu. Mọi ngân sách dưới đây là **byte LF**.
    """
    return len((SKILLS / name).read_text(encoding="utf-8").encode("utf-8"))


@pytest.mark.parametrize("name,budget", sorted(BUDGET_BYTES.items()))
def test_prompt_khong_vuot_ngan_sach_byte(name, budget):
    actual = _byte_lf(name)
    assert actual <= budget, (
        f"{name} = {actual} byte, vượt ngân sách {budget}. "
        "Luật nào mã hoá được thì chuyển sang schema/validator, đừng nhồi prompt: "
        "luật trong prompt là GỢI Ý, luật trong validator là RÀNG BUỘC."
    )


def test_moi_skill_deu_co_ngan_sach():
    """Thêm skill mới mà quên khai ngân sách ⇒ nó phình tự do, không ai biết."""
    tren_dia = {p.name for p in SKILLS.glob("*.md")}
    thieu = tren_dia - set(BUDGET_BYTES)
    assert not thieu, f"Skill chưa khai ngân sách byte: {sorted(thieu)}"


def test_khong_khai_ngan_sach_cho_skill_da_bien_mat():
    tren_dia = {p.name for p in SKILLS.glob("*.md")}
    thua = set(BUDGET_BYTES) - tren_dia
    assert not thua, f"Ngân sách khai cho skill không còn tồn tại: {sorted(thua)}"
