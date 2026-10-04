# -*- coding: utf-8 -*-
"""M17-Lite W0 — ánh xạ từ chối/lỗi pipeline sang thông điệp HỌC SINH.

Lớp TRÌNH BÀY sống ở biên API (main.py), KHÔNG nằm trong run_pipeline:
- ``reason`` kỹ thuật của pipeline GIỮ NGUYÊN (nó dạy LLM retry, nuôi
  harness/diagnostics — đổi nó là đổi hợp đồng M13/M14/M15);
- học sinh chỉ thấy ``learner_reason``: tiếng Việt thân thiện, KHÔNG token
  kỹ thuật (không snake_case id, không JSON path, không schema error, không
  message exception thô) — yêu cầu M17 W0 "structured error mapping";
- bất biến #22 không bị chạm: evaluation quan sát envelope pipeline TRƯỚC
  lớp này (attach chỉ chạy ở endpoint).

Test lock: tests/test_learner_messages.py (BE) + learner-error.test.tsx (FE).
"""

from __future__ import annotations

import re

# Thông điệp ĐÓNG — chọn theo failure_category/error_code CÓ CẤU TRÚC,
# tuyệt đối không string-match message kỹ thuật.
_MSG_CAPABILITY_GAP = (
    "Bài này cần một cơ chế mà AlgoSim chưa mô phỏng chính xác được, nên hệ "
    "thống từ chối trung thực thay vì dựng một mô phỏng gần đúng. Bạn có thể "
    "thử một bài thuộc các chủ đề đang hỗ trợ: tìm kiếm, sắp xếp, quét dãy, "
    "số nhị phân, cổng logic, định tuyến gói tin, đóng gói dữ liệu qua các "
    "tầng mạng."
)
_MSG_NOT_IN_CATALOG = (
    "Bài này chưa có mô phỏng phù hợp trong danh mục hiện tại. Danh mục sẽ "
    "được mở rộng dần — bạn có thể thử một bài khác trong các chủ đề đang "
    "hỗ trợ."
)
_MSG_INSUFFICIENT = (
    "Đề chưa cung cấp đủ dữ kiện để mô phỏng (ví dụ: cấu trúc cụ thể của cây — "
    "các nút và quan hệ con trái/con phải). Hãy mô tả rõ hơn rồi thử lại — hệ "
    "không tự bịa dữ liệu thay bạn."
)
_MSG_INCOMPLETE = (
    "Đề đang hỏi nhiều thao tác cùng lúc, nhưng mỗi lần mô phỏng chỉ trình bày "
    "được một. Em hãy tách thành từng lần hỏi (giữ nguyên dữ liệu, mỗi lần chọn "
    "một thao tác) để xem đầy đủ từng bước."
)
# 2026-08-31 — dọn phạm vi sản phẩm. Bản cũ mời học sinh "thử một bài Tin học"
# và liệt kê sáu miền của đề cũ; đó là quảng bá một sản phẩm không còn là sản
# phẩm. Nói "TẬP TRUNG" chứ không nói "chỉ": các miền cũ vẫn chạy được ở runtime
# (Lịch sử, bài giáo viên đã giao), nên tuyên bố "chỉ hình học" sẽ là nói dối
# theo hướng ngược lại.
_MSG_OUT_OF_SCOPE = (
    "Bài này thuộc môn học khác, không nằm trong phần AlgoSim mô phỏng. Hệ "
    "thống nói thẳng thay vì dựng một hình vẽ trông giống mô phỏng nhưng không "
    "dựa trên cơ chế nào. AlgoSim tập trung vào hình học không gian — bạn thử "
    "một bài về giao tuyến, thiết diện, quan hệ song song – vuông góc, khoảng "
    "cách hoặc thể tích nhé."
)
# TÁCH KHỎI `_MSG_NOT_IN_CATALOG` có chủ đích: chủ đề này CÓ trong chương trình,
# chỉ là nó không có cơ chế để mô phỏng. Nói "chưa có trong danh mục" ở đây làm
# học sinh tưởng hệ chưa hỗ trợ chủ đề và chờ nó được thêm vào — một lời hứa
# không bao giờ tới, vì chẳng có gì để thêm.
_MSG_NOT_SIMULATION_SUITABLE = (
    "Nội dung này đúng chủ đề, nhưng nó không có cơ chế nào để "
    "mô phỏng — đọc và hiểu là đủ, dựng cảnh chỉ thành hình trang trí. Nếu bạn "
    "muốn thấy một quá trình diễn ra từng bước, hãy thử một bài có dữ liệu và "
    "có thao tác trên dữ liệu đó."
)
_MSG_PIPELINE_FAILED = (
    "AI chưa tạo được mô phỏng hợp lệ cho đề này sau nhiều lần thử. Bạn hãy "
    "diễn đạt lại đề rõ ràng hơn — nêu rõ dữ liệu vào và kết quả cần tìm — "
    "rồi thử lại."
)


#: W17 §15.3: lời CHUNG cho nguyên nhân chưa rõ (`UNKNOWN`) — không có căn cứ nào nói đề sai, nên
#: không bảo học sinh viết lại đề (bản trước khuyên "diễn đạt lại đề gọn hơn" cho mọi lỗi sinh).
_MSG_GEOMETRY_GENERATION_FAILED = (
    "AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương "
    "trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng. "
    "Hệ thống không hiển thị hình chưa được kiểm — thà không có mô phỏng còn hơn "
    "một hình sai mà em tin theo. Em có thể gửi lại để hệ dựng lại; nếu vẫn "
    "chưa được, bài này có thể nằm ngoài những gì hệ đang kiểm chứng được."
)


#: NGOÀI BAO ĐÓNG ≠ VIẾT ĐỀ CHƯA GỌN — và đây là một bản sửa lỗi nói sai.
#:
#: `requested_operation_uncovered` nghĩa là cổng phủ đã soát hết bảng phép dựng
#: và **không có phép nào** tạo ra thứ đề yêu cầu (khối tròn xoay tổng quát,
#: khối ghép/bù cần boolean). Trước bản này nó rơi vào câu chung của
#: `geometry_generation_failed`, tức khuyên học sinh *"diễn đạt lại đề gọn
#: hơn"* — một lời khuyên vô hại nghe thì lịch sự, nhưng nó hứa rằng viết lại
#: sẽ ăn thua. Không lần nào ăn thua cả: thiếu ở đây là một PHÉP DỰNG chưa tồn
#: tại trong hệ, không phải một câu văn chưa rõ. Đo được ở `n2` của lượt đánh
#: giá cuối, và cùng lớp lỗi với `out_of_scope` vs `not_simulation_suitable`.
_MSG_REQUESTED_OPERATION_UNCOVERED = (
    "Yêu cầu của đề này nằm ngoài các phép dựng mà AlgoSim đang có, nên hệ "
    "thống nói thẳng thay vì dựng một hình gần đúng rồi để em tin theo. Hệ "
    "dựng và kiểm chứng được thiết diện, giao tuyến, khoảng cách, góc và thể "
    "tích trên khối đa diện, hình cầu, hình trụ, hình nón — em thử một bài "
    "thuộc các dạng ấy nhé."
)

#: `error_code` → thông điệp. Tra bảng này TRƯỚC `failure_category` vì mã lỗi
#: chi tiết hơn loại: nhiều mã cùng rơi về một `failure_category`, và lời
#: khuyên đúng cho mã này là lời hứa sai cho mã kia.
_MSG_THEO_MA: dict[str, str] = {
    "requested_operation_uncovered": _MSG_REQUESTED_OPERATION_UNCOVERED,
}

#: NGUỒN KHÔNG CHỨNG MINH ĐƯỢC (W12) — không phải "diễn đạt lại đề": đề thiếu
#: số liệu, hoặc số liệu mâu thuẫn với chính câu chữ của đề. Hứa rằng viết lại
#: gọn hơn sẽ ăn thua là hứa sai; nói đúng thứ đang thiếu thì học sinh sửa được.
_MSG_NGUON_THIEU = (
    "Để dựng hình, chương trình cần {doan} nhưng đề bài không ghi số liệu này. "
    "AlgoSim không tự thêm dữ kiện thay em, nên không dựng hình cho đề này. Em "
    "kiểm tra lại đề đã ghi đủ các số liệu cần thiết chưa rồi gửi lại nhé."
)
#: W17 §15.3 (đính chính Task 1): đề là thẩm quyền — số liệu HỆ dùng lệch câu chữ của đề là lỗi
#: đọc đề của hệ (`CONSTRUCTION`), không phải lỗi của đề.
_DUOI_LOI_HE = " Đây là lỗi dựng hình của hệ, đề không cần sửa — em có thể gửi lại để hệ dựng lại."
_MSG_NGUON_MAU_THUAN = (
    "Số liệu hệ dùng để dựng hình ({doan}) không khớp với chính câu chữ của đề — "
    "khác giá trị, khác đoạn thẳng hoặc khác đơn vị. AlgoSim dừng lại thay vì "
    "dựng một hình có thể sai." + _DUOI_LOI_HE
)
#: W17 §15.2: giá trị chỉ có trong yêu cầu chứng minh — đề nêu nó như điều phải chứng minh.
_MSG_CHI_TRONG_MUC_TIEU = (
    "Đề bài chỉ nêu {doan} trong yêu cầu chứng minh, chứ không cho nó như một dữ kiện. "
    "AlgoSim không dùng điều cần chứng minh làm dữ kiện, nên không dựng hình cho đề này. "
    "Nếu đó là dữ kiện, em ghi nó vào phần giả thiết của đề rồi gửi lại nhé."
)
#: W17 §15.3: cùng một mã, hai nguyên nhân — đề GHI giá trị gây lỗi (SOURCE), hay hệ tự đặt nó
#: trên một đề hợp lệ (CONSTRUCTION). Chỉ nguyên nhân SOURCE mới mời học sinh xem lại đề.
_MSG_THEO_NGUYEN_NHAN: dict[str, dict[str, str]] = {
    "NON_POSITIVE_LENGTH": {
        "SOURCE": ("Đề bài cho {doan} bằng 0 hoặc âm, nên hình suy biến: không có khối nào như vậy để "
                   "dựng hay tính. Em kiểm tra lại số liệu này trong đề rồi gửi lại nhé."),
        "CONSTRUCTION": ("Khâu dựng hình của AlgoSim đã dùng {doan} không dương, trong khi đề bài không "
                         "cho số liệu như vậy." + _DUOI_LOI_HE),
    },
    "PLANE_DOES_NOT_CUT": {
        "SOURCE": ("Mặt phẳng{mp} mà đề bài cho không cắt khối, nên không có thiết diện để dựng hay "
                   "tính. Em kiểm tra lại phương trình của mặt phẳng này trong đề rồi gửi lại nhé."),
        "CONSTRUCTION": ("Mặt phẳng mà khâu dựng hình của AlgoSim dùng để cắt không cắt khối, nên không có "
                         "thiết diện — trong khi đề bài không cho mặt phẳng ấy." + _DUOI_LOI_HE),
    },
}
#: W14 5a — hợp đồng tới route mà không mang đề. Tuyến sản phẩm luôn gửi đề, nên lời
#: này lẽ ra không tới học sinh; nếu tới, nó nói đúng điều đã xảy ra, không đổ cho đề.
_MSG_THIEU_DE = (
    "AlgoSim không nhận được nội dung đề bài đi kèm, nên không đối chiếu được dữ kiện "
    "với đề và không dựng hình. Em gửi lại đề bài nhé."
)
#: W15 — đáp số phụ thuộc một kích thước đề không cho (chứng chỉ giả định tìm được một
#: hình khác cũng khớp mọi điều đề nói mà đáp số đổi). Nói đúng số liệu đang thiếu.
_MSG_GIA_DINH_QUYET_DINH = (
    "Đề bài chưa cho {doan}, mà đáp số lại phụ thuộc vào số liệu này: hình vẫn khớp mọi "
    "điều đề nói khi số liệu ấy đổi, còn đáp số thì đổi theo. AlgoSim không tự chọn một "
    "giá trị thay em, nên không đưa ra đáp số cho đề này. Em kiểm tra lại đề xem có thiếu "
    "số liệu đó không rồi gửi lại nhé."
)
#: W15 — chưa chứng minh được đáp số chỉ phụ thuộc dữ kiện đề cho.
_MSG_GIA_DINH_CHUA_CHUNG_MINH = (
    "AlgoSim chưa chứng minh được đáp số chỉ phụ thuộc vào các dữ kiện đề bài cho: có thể "
    "hình dựng đã tự chọn một số liệu đề không nêu, hoặc đề nêu quan hệ theo cách hệ chưa "
    "đọc được. Hệ dừng lại thay vì đưa ra một đáp số chưa kiểm chứng. Em thử ghi rõ các "
    "quan hệ trong đề (ví dụ \"SA vuông góc với đáy\", \"đáy ABCD là hình chữ nhật\") và đủ "
    "các số liệu rồi gửi lại nhé."
)
_MSG_THEO_MA_CHI_TIET: dict[str, str] = {
    "GIVEN_VALUE_NOT_IN_SOURCE": _MSG_NGUON_THIEU,
    "SOURCE_SPAN_MISMATCH": _MSG_NGUON_MAU_THUAN,
    "SOURCE_EVIDENCE_CONFLICT": _MSG_NGUON_MAU_THUAN,
    "SOURCE_TEXT_MISSING": _MSG_THIEU_DE,
    "ASSUMPTION_DETERMINES_ANSWER": _MSG_GIA_DINH_QUYET_DINH,
    "ASSUMPTION_INVARIANCE_UNPROVEN": _MSG_GIA_DINH_CHUA_CHUNG_MINH,
    "GIVEN_ONLY_IN_GOAL_CLAUSE": _MSG_CHI_TRONG_MUC_TIEU,
}


#: W17 §15.1 — đề đủ và đúng, phép dựng thiết diện của hệ dùng thực thể khác thực thể đề nêu.
#: Nguyên nhân CONSTRUCTION: không bảo học sinh sửa đề.
_DUOI_LECH_PHEP_DUNG = (
    " AlgoSim dừng lại thay vì đưa ra một đáp số tính trên một hình khác với hình đề nói." + _DUOI_LOI_HE
)


def _msg_lech_phep_dung(envelope: dict) -> str:
    """`reason_subjects` = [thực thể đề nêu, thực thể chương trình dùng]: mặt phẳng `(β)` /
    `z = 3`, hoặc khối `S.ABCD`."""
    ten = [f"khối {s}" if "." in s and "=" not in s else f"mặt phẳng {s}"
           for s in envelope.get("reason_subjects") or [] if isinstance(s, str) and s and "_" not in s]
    if len(ten) >= 2 and ten[0].split()[0] == ten[1].split()[0]:
        cau = f"Đề bài nêu {ten[0]}, nhưng phép dựng thiết diện của AlgoSim lại dùng {ten[1]}."
    elif ten:
        cau = f"Phép dựng thiết diện của AlgoSim không dùng đúng {ten[0]} mà đề bài nêu."
    else:
        cau = "Phép dựng thiết diện của AlgoSim không khớp với câu cắt trong đề bài."
    return cau + _DUOI_LECH_PHEP_DUNG


def _msg_lech_phep_dung_diem(envelope: dict) -> str:
    """W18 §16.4 — `reason_subjects` = các cặp [quan hệ đề nêu, quan hệ chương trình dựng], viết theo
    ký hiệu học sinh (`M là trung điểm của SA`). Nguyên nhân CONSTRUCTION: không bảo sửa đề."""
    s = [x for x in envelope.get("reason_subjects") or [] if isinstance(x, str)]
    cap = [(a, b) for a, b in zip(s[0::2], s[1::2]) if a and b and "_" not in a + b]
    if cap:
        def noi(xs):
            return " và ".join(f"\"{x}\"" for x in dict.fromkeys(xs))
        cau = (f"Đề bài nêu {noi(a for a, _ in cap)}, nhưng phép dựng của AlgoSim lại dựng "
               f"{noi(b for _, b in cap)}.")
    else:
        cau = "Phép dựng điểm của AlgoSim không khớp với câu của đề bài."
    return cau + _DUOI_LECH_PHEP_DUNG


#: W18 §16.4 — CHƯA ĐỐI CHIẾU được, không phải đề sai: nói đúng giới hạn của hệ.
_MSG_CHUA_DOI_CHIEU = (
    "AlgoSim chưa đối chiếu được cách dựng {diem} với câu của đề bài: hệ mới đọc được một số cách "
    "viết như \"Gọi M là trung điểm của SA\" hay \"Gọi H là hình chiếu của S lên (ABCD)\". Đây là "
    "giới hạn của hệ, không phải lỗi của đề. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm "
    "chứng; nếu muốn, em có thể viết câu ấy theo một trong các cách trên rồi gửi lại."
)


def _msg_toa_do_thay_dung(envelope: dict) -> str:
    """W20 §17 — `reason_subjects` = các cặp [quan hệ đề nêu, việc chương trình đã làm] (`đặt H bằng toạ
    độ cho sẵn`, `lấy H trùng với điểm A`). Toạ độ có thể đúng: nói giới hạn KIỂM CHỨNG, không nói hình
    khác, không bảo sửa đề."""
    s = [x for x in envelope.get("reason_subjects") or [] if isinstance(x, str)]
    cap = [(a, b) for a, b in zip(s[0::2], s[1::2]) if a and b and "_" not in a + b]
    if cap:
        de = " và ".join(f"\"{a}\"" for a in dict.fromkeys(a for a, _ in cap))
        cau = (f"Đề bài nêu {de}, nhưng chương trình của AlgoSim {' và '.join(dict.fromkeys(b for _, b in cap))}"
               + (" thay vì dựng điểm này từ quan hệ ấy, nên hệ chưa kiểm chứng được nó" if len(cap) == 1
                  else " thay vì dựng các điểm này từ quan hệ ấy, nên hệ chưa kiểm chứng được chúng"))
    else:
        cau = ("Chương trình của AlgoSim đặt một điểm đề nêu bằng toạ độ thay vì dựng nó từ quan hệ đề nêu, "
               "nên hệ chưa kiểm chứng được nó")
    return cau + " đúng là điểm đề nói. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm chứng." + _DUOI_LOI_HE


def _msg_chua_doi_chieu(envelope: dict) -> str:
    ten = [x for x in envelope.get("reason_subjects") or [] if isinstance(x, str) and x and "_" not in x]
    return _MSG_CHUA_DOI_CHIEU.format(diem=("điểm " + ", ".join(ten)) if ten else "một điểm trong hình")


_KY_HIEU_DIEM = re.compile(r"[A-Z]\d*′?")


def _doan_hoc_sinh(envelope: dict) -> str:
    """Số liệu học sinh đọc được — `độ dài AD`, `toạ độ điểm S` — hoặc câu chung;
    không bao giờ in thứ gì mang `_` (tên máy)."""
    ten = [s for s in (envelope.get("reason_subjects") or [])
           if isinstance(s, str) and s and "_" not in s]
    diem = [s for s in ten if _KY_HIEU_DIEM.fullmatch(s)]
    doan = [s for s in ten if s not in diem]
    cum = ([f"độ dài {', '.join(doan)}"] if doan else []) \
        + ([f"toạ độ điểm {', '.join(diem)}"] if diem else [])
    return " và ".join(cum) if cum else "một số liệu"


def learner_reason(envelope: dict) -> str:
    """Thông điệp học sinh cho envelope ``status="unsupported"`` — chọn theo
    ``reason_code``, ``error_code`` rồi tới ``failure_category`` (đều CÓ CẤU
    TRÚC), không bao giờ đọc text ``reason``."""
    ma = envelope.get("reason_code") or ""
    if ma == "CONSTRUCTION_NOT_TEXT_BOUND":
        # W18: cùng mã, chặng phân biệt — phép dựng ĐIỂM (§16) hay phép dựng thiết diện (§15.1).
        return (_msg_lech_phep_dung_diem(envelope) if envelope.get("stage_reached") == "construction_binding"
                else _msg_lech_phep_dung(envelope))
    if ma == "CONSTRUCTION_BINDING_UNVERIFIED":
        return _msg_chua_doi_chieu(envelope)
    if ma == "CONSTRUCTION_REPLACED_BY_COORDINATES":
        return _msg_toa_do_thay_dung(envelope)
    theo_nn = _MSG_THEO_NGUYEN_NHAN.get(ma, {}).get(envelope.get("refusal_cause") or "")
    if theo_nn is not None:
        mp = ", ".join(s for s in envelope.get("reason_subjects") or [] if isinstance(s, str) and "_" not in s)
        return theo_nn.format(doan=_doan_hoc_sinh(envelope), mp=f" {mp}" if mp else "")
    chi_tiet = _MSG_THEO_MA_CHI_TIET.get(ma)
    if chi_tiet is not None:
        return chi_tiet.format(doan=_doan_hoc_sinh(envelope))
    theo_ma = _MSG_THEO_MA.get(envelope.get("error_code") or "")
    if theo_ma is not None:
        return theo_ma
    if envelope.get("failure_category") == "capability_gap":
        return _MSG_CAPABILITY_GAP
    if envelope.get("failure_category") == "geometry_generation_failed":
        # KHÔNG dùng `_MSG_OUT_OF_SCOPE` ở đây, và đó là toàn bộ lý do nhánh này
        # tồn tại: nói "bài thuộc môn khác" cho một đề hình học mà hệ VỪA bỏ hai
        # phút để dựng là đổ lỗi cho đề bài cái sai của hệ.
        return _MSG_GEOMETRY_GENERATION_FAILED
    if envelope.get("failure_category") == "out_of_scope":
        return _MSG_OUT_OF_SCOPE
    if envelope.get("failure_category") == "not_simulation_suitable":
        return _MSG_NOT_SIMULATION_SUITABLE
    if envelope.get("failure_category") == "insufficient_specification":
        # M17-RC1 §C2: cổng đủ-dữ-kiện đã sinh thông điệp RIÊNG theo target
        # (`learner_prompt_template` — nêu đúng thứ đang thiếu: dãy số, số cần
        # đổi, cấu trúc cây…). Giữ nguyên vì nó hữu ích hơn câu chung; câu
        # chung chỉ dùng khi vì lý do nào đó không có.
        reason = envelope.get("reason")
        return reason if isinstance(reason, str) and reason else _MSG_INSUFFICIENT
    if envelope.get("failure_category") == "semantic_incomplete":
        # Thông điệp của gate ĐÃ thân thiện và nêu rõ cách tách đề — giữ nguyên
        # thay vì thay bằng câu chung chung kém hữu ích hơn.
        reason = envelope.get("reason")
        return reason if isinstance(reason, str) and reason else _MSG_INCOMPLETE
    return _MSG_NOT_IN_CATALOG


def attach_learner_reason(envelope: dict) -> dict:
    """Gắn ``learner_reason`` vào envelope unsupported (bản sao — không mutate
    envelope pipeline). Envelope ok đi qua NGUYÊN VẸN."""
    if not isinstance(envelope, dict) or envelope.get("status") != "unsupported":
        return envelope
    # W17 §15.3: mọi envelope từ chối mang nguyên nhân; nơi từ chối không phân xử ⇒ UNKNOWN.
    return {**envelope, "refusal_cause": envelope.get("refusal_cause") or "UNKNOWN",
            "learner_reason": learner_reason(envelope)}


def learner_error_message() -> str:
    """Thông điệp học sinh cho nhánh 422 (simulate thất bại sau retry) —
    CỐ ĐỊNH, không nhúng chi tiết validator (chi tiết kỹ thuật đi field
    ``error_detail`` riêng, FE không render)."""
    return _MSG_PIPELINE_FAILED
