"""Pipeline LLM (M3): analyze → classify → simulate → validate → envelope.

Ranh giới cứng: LLM chỉ trích xuất, phân loại và điền CONFIG đầu vào.
Timeline/diễn biến/kết quả do engine tất định phía frontend sinh ra.
SimulationEnvelope hợp lệ CHỈ được phát hành sau server-side validation —
không bao giờ trả thẳng JSON của Gemini cho frontend (M3 §6).
"""

from __future__ import annotations

import json

from typing import TYPE_CHECKING

from app.ai.telemetry import stage_scope

if TYPE_CHECKING:  # tránh import vòng lúc chạy: contract kéo theo cả cây pydantic
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import SemanticRouteOutcome
from app.simulation.error_codes import ErrorCode

#: Trần lượt sửa của `stage_semantic_program`. HẰNG SỐ, không theo độ dài trace —
#: đó là điều giữ cho claim D1 (số lượt LLM chặn bởi call graph) còn đúng. Bằng
#: `stage_simulate` để hai đường không lệch nhau vô cớ.
MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3


def _emit(observer, event_type: str, **data) -> None:
    """M14 §F2 — phát event cho observer THỤ ĐỘNG (None → no-op, hành vi
    production không đổi một bit)."""
    if observer is not None:
        observer.emit(event_type, data)
from app.ai.gemini import call_gemini, load_skill

# ── Schema structured output ──────────────────────────────────
#
# `ANALYZE_SCHEMA` (schema `analyze` của miền Tin học, ~130 dòng) đã được gỡ
# cùng `stage_analyze`. Schema đang chạy của sản phẩm là schema `analyze` HÌNH
# HỌC, và nó sống ở `semantic_program/analyze_contract.analyze_schema_for` —
# nơi nó dẫn xuất từ chính taxonomy nghĩa vụ hình học.


async def _call_json(
    api_key: str,
    skill: str,
    user_text: str,
    schema: dict,
    temperature: float,
    retries: int,
    on_retry_note: str,
) -> dict:
    """Gọi Gemini + parse JSON, retry khi trả về không phải JSON hợp lệ."""
    prompt = user_text
    for attempt in range(retries + 1):
        # Nhãn stage cho telemetry token (spec §6.1). Dùng ContextVar thay vì
        # tham số của call_gemini: hàm đó có 13 test double, thêm tham số quan
        # trắc vào chữ ký làm gãy hết.
        with stage_scope(skill):
            raw = await call_gemini(api_key, load_skill(skill), prompt, schema, temperature)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        if attempt < retries:
            prompt = f"{user_text}\n\n{on_retry_note}"
    raise RuntimeError(f"Giai đoạn {skill} không trả về JSON hợp lệ sau {retries + 1} lần.")


# ── Các stage ─────────────────────────────────────────────────


async def stage_semantic_analyze(
    text: str, api_key: str, domain: str | None = None
) -> tuple["RequestContract | None", str | None]:
    """Đề bài → `RequestContract` ĐÃ ĐÓNG BĂNG (dữ liệu đề cho + nghĩa vụ).

    VÌ SAO TÁCH HẲN LƯỢT NÀY, không gộp vào lượt viết chương trình: gộp thì cùng
    một lượt sinh ra cả *nghĩa vụ* lẫn *chương trình*, nên mô hình chỉ việc khai
    nghĩa vụ nào mà chương trình nó vừa viết đã thoả. C₁a khi ấy còn đúng về mặt
    hình thức nhưng không còn kiểm được gì — nó tự đối chiếu một nguồn với chính
    nguồn ấy. Hai lượt tách rời tốn thêm một call và đổi lại giữ cho cổng phủ có
    thật sự là một cổng.

    Server ĐÓNG BĂNG, không chép nguyên lời LLM: `build_request_contract` loại
    nghĩa vụ ngoài taxonomy và mục dữ liệu thiếu `id` ngay tại biên.

    ─── `domain` (Wave 2, sau Phase 5) ──────────────────────────────────────

    `None` = miền Tin học, tức **hành vi trước Wave 2 nguyên vẹn**: cùng skill,
    cùng schema, cùng enum 19 nghĩa vụ. Truyền `hinh_hoc` thì đổi ĐỒNG BỘ ba
    thứ — skill đọc đề, enum nghĩa vụ trong schema, và bộ lọc phía server. Đổi
    thiếu một trong ba là đúng cái lỗ Phase 5 đo được: skill viết chương trình
    đã sang hình học từ lâu, còn skill đọc đề thì không, nên mô hình chọn nghĩa
    vụ Tin học cho bài hình học ở 3/6 ca hợp lệ.
    """
    from app.simulation.semantic_program.analyze_contract import (
        SEMANTIC_ANALYZE_SCHEMA,
        analyze_schema_for,
        build_request_contract,
    )
    from app.simulation.semantic_program.domain_profile import analyze_skill_for

    schema = analyze_schema_for(domain) if domain else SEMANTIC_ANALYZE_SCHEMA
    user = f'Đề bài:\n"""\n{text}\n"""'
    with stage_scope("semantic_analyze"):
        raw = await call_gemini(
            api_key,
            load_skill(analyze_skill_for(domain) if domain else "semantic_analyze"),
            user,
            schema,
            0.1,
        )

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        return None, f"SEMANTIC_ANALYZE_INVALID: JSON không parse được ({e})"
    if not isinstance(payload, dict):
        return None, (
            "SEMANTIC_ANALYZE_INVALID: đầu ra không phải một đối tượng JSON "
            f"(nhận {type(payload).__name__})"
        )
    # `text` đi kèm là bậc P1: `analyze` có thể bỏ trống ô giá trị dù đề ghi rõ
    # literal (đã quan sát: `values=null` cho đề chứa `{[()]}`). Có đề gốc thì
    # server tự neo được literal về span thay vì phụ thuộc model nhớ chép.
    return build_request_contract(payload, problem_text=text, domain=domain), None


def _facts_for_prompt(contract: "RequestContract") -> str:
    """Danh mục dữ liệu đề cho, kèm ĐÚNG `id` mà IR phải ghim vào.

    Không có khối này thì `source_fact_id` là bất khả thi chứ không phải khó:
    lượt viết chương trình chưa từng nhìn thấy hợp đồng, nên không có id nào để
    trích dẫn, và P2 sẽ từ chối 100% chương trình — kể cả chương trình đúng.
    """
    if not contract.input_facts:
        return "Đề không cho dữ liệu cụ thể nào."

    def _hien(f) -> str:
        """Cách VIẾT của một mục dữ liệu, cho MẮT ĐỌC.

        ─── BẪY ĐÃ CẮN, ĐO ĐƯỢC TRÊN LƯỢT LIVE 2026-08-24 ──────────────────
        `f.values` là biểu diễn dành cho GROUNDING: một chuỗi được mở thành
        *toàn bộ + từng ký tự* (`gia_tri_kem_ky_tu`) để chương trình khai đầu
        vào dạng mảng ký tự vẫn qua được P2. Đem nguyên biểu diễn ấy nối bằng
        dấu phẩy thì mục `{[()]}` hiện ra thành:

            Chuỗi đóng mở ngoặc: {[()]}, {, [, (, ), ], }

        — dấu phẩy vừa là ký tự phân cách vừa nằm cạnh toàn dấu ngoặc. Mô hình
        đọc mớ đó rồi khai `['{', '<', '(', ')', '>']`: **bịa ra dấu ngoặc
        nhọn**. Cổng grounding bắt đúng và từ chối, nhưng thứ bị hỏng là CÁCH
        HỎI, không phải mô hình.

        `source_text` là literal ĐÚNG NHƯ NÓ NẰM TRONG ĐỀ, do extractor tất
        định cắt ra kèm span. Có nó thì hiển thị nó — không có cách viết nào
        trung thực hơn thế.
        """
        # CHUẨN HOÁ THANG THẮNG `source_text`. Mục đã viết lại thì `source_text`
        # còn giữ nguyên văn (`4a/5`) — chính là thứ mô hình KHÔNG được dùng
        # nữa. Hiện nó ra thì mô hình lại đi tìm một giá trị cho `a`, tức đúng
        # bế tắc mà phép chuẩn hoá sinh ra để gỡ.
        if f.scale_symbol:
            goc = ", ".join(str(v) for v in f.original_values)
            return f": {', '.join(str(v) for v in f.values)}  (đề viết: {goc})"
        if f.source_text:
            return f': "{f.source_text}"'
        if f.values:
            return f": {', '.join(str(v) for v in f.values)}"
        return " (đề chưa cho giá trị)"

    dong = [f"- id `{f.fact_id}` — {f.label}{_hien(f)}" for f in contract.input_facts]
    dau = ""
    if contract.scale_binding is not None:
        # Nói THẲNG rằng thang đã được chốt, và chốt bởi ai. Không có dòng này
        # thì mô hình thấy `AB = 1` mà vẫn tưởng mình được chọn lại thang.
        b = contract.scale_binding
        dau = (
            f"Đề dùng ký hiệu tỉ lệ tự do `{b.symbol}`. Hệ ĐÃ CHỐT "
            f"`{b.symbol} = {b.canonical_value}` và viết lại các số dưới đây "
            f"theo thang ấy. Dùng đúng những số này; KHÔNG tự chọn giá trị "
            f"khác cho `{b.symbol}`, KHÔNG khai lại `{b.symbol}` như một biến.\n"
        )
    return (dau + "Dữ liệu đề cho (ghim `source_fact_id` về đúng id dưới đây):\n"
            + "\n".join(dong))


def _obligations_for_prompt(contract: "RequestContract") -> str:
    """Danh xưng CHUNG cho hai lượt LLM — container và witness của từng nghĩa vụ.

    VÌ SAO CẦN (đo được ở lượt pilot 3): hai lượt được tách rời có chủ đích, nên
    chúng không dùng chung không gian tên. `semantic_analyze` khai
    `extremum(container='day_so_hoc', witness='so_lon_nhat_nho_hon_100')`, còn
    `semantic_program` đặt tên biến hoàn toàn khác, và C₁a báo đúng là "container
    chưa khai báo". 12/40 case trượt vì đúng khe hở này.

    Việc này KHÔNG làm C₁a rỗng nghĩa. C₁a hỏi *chương trình có SINH RA witness
    không*, không hỏi *nó đặt tên thế nào*. Tính độc lập cần giữ là "hợp đồng
    nêu yêu cầu TRƯỚC khi chương trình được viết", và điều đó vẫn nguyên vẹn:
    nghĩa vụ đã đóng băng xong mới tới lượt viết chương trình.
    """
    if not contract.obligations:
        return "Đề không đòi kết quả cụ thể nào."
    dong = [
        f"- {ob.kind}: dữ liệu bị hỏi nằm trong biến `{ob.container}`, "
        f"kết quả nằm trong biến `{ob.witness}`"
        for ob in contract.obligations
        if ob.witness
    ]
    if not dong:
        return "Đề không đòi kết quả cụ thể nào."
    return (
        "Nghĩa vụ của đề. CẢ HAI tên dưới đây đều phải có mặt trong "
        "`memory_declarations`, đúng từng chữ:\n"
        + "\n".join(dong)
        + "\n(Dãy do đề mô tả mà không liệt kê sẵn thì vẫn phải dựng thành một "
        "biến chứa dữ liệu — mô phỏng cần hiện dãy đó lên, không chỉ tính ra "
        "đáp số.)"
    )


#: Mã lỗi KHÔNG BAO GIỜ được gửi đi sửa (§9, §10).
#:
#: Hai mã trung thực năng lực nói *"mô hình đã tự giải rồi giấu kết luận vào
#: toạ độ"*. Một lượt sửa ở đây không phải cho nó cơ hội sửa — nó là cho nó cơ
#: hội **giấu khéo hơn**, và ta trả tiền cho lượt ấy.
#:
#: Chúng cũng chính là tín hiệu tất định gần nhất cho *"đề này ngoài IR"*:
#: `gm_10` là bài mặt cầu, và nó lộ ra đúng ở đây. Nên §9 và §10 gộp về một
#: tập, không phải vì tiện mà vì cùng một phán quyết.
KHONG_DUOC_SUA = frozenset({
    "UNANCHORED_DERIVED_ASSUMPTION",
    "DERIVED_ENTITY_WITHOUT_PRODUCER",
})


def _prompt_sua(
    base: str,
    chuong_trinh: str | None,
    loi: str,
    *,
    de: str | None = None,
    domain: str | None = None,
) -> str:
    """Prompt SỬA — gửi lại chính chương trình vừa hỏng.

    ─── LỖI CỦA BẢN CŨ, ĐO ĐƯỢC Ở PROBE 2026-08-31 ────────────────────────

    Bản trước chỉ gửi `base + lỗi` rồi bảo *"sửa ĐÚNG chỗ đó và giữ nguyên
    phần còn lại"* — một câu mô hình **không thể theo**, vì nó không có
    chương trình cũ trong ngữ cảnh. Nó sinh lại từ đầu, và lượt hai vấp một
    lỗi KHÁC lượt một. Bản ghi từng lượt cho thấy đúng hình ấy ở cả bốn ca:
    lượt 0 hỏng vì `construct_point`+toạ độ, lượt 1 hỏng vì `angle_cos` trên
    `line3` — hai lỗi ĐỘC LẬP, không phải một lỗi chưa sửa xong.

    Gửi lại chương trình TỐN thêm input token, đổi lấy việc lượt sửa thật sự
    là một lượt SỬA. Đó là phép đổi đúng: một lượt sửa vô hiệu tốn cả output
    token lẫn một ca hỏng.

    Cắt ở 6000 ký tự và NÓI RÕ đã cắt — cắt câm thì mô hình sửa một chương
    trình khác chương trình nó viết.

    ─── NGỮ CẢNH HẸP LẠI (§8, 2026-08-31) ─────────────────────────────────

    `de` + `domain` cho phép thay `base` — đề bài + dữ kiện + nghĩa vụ + **cả
    thẻ văn phạm** — bằng đề bài cộng đúng MẢNH hợp đồng mà lời từ chối nói
    tới. Với đề hình học `base` nặng ~8 KB, gần hết là thẻ, và gửi lại cả thẻ
    là mời mô hình cân nhắc lại cả thẻ: bản ghi bốn ca probe cho thấy lượt sửa
    vấp một lỗi KHÁC lượt đầu, tức nó viết lại chứ không sửa.

    Không khớp được mảnh nào ⇒ **quay về `base`**, không gửi một prompt cụt.
    Thà tốn token còn hơn bảo mô hình sửa mà không cho nó hợp đồng.
    """
    duoi_cung = "Hãy sửa ĐÚNG chỗ đó và giữ nguyên phần còn lại."
    goc = base
    if de is not None:
        from app.simulation.semantic_program.grammar_card import manh_hop_dong

        manh = manh_hop_dong(loi, domain)
        if manh:
            goc = (f'Đề bài:\n"""\n{de}\n"""\n\n'
                   f"Phần hợp đồng liên quan tới lỗi này:\n{manh}")
    if not chuong_trinh:
        return f"{goc}\n\nLần trước bị từ chối vì: {loi}\n{duoi_cung}"
    cat = chuong_trinh[:6000]
    duoi = f"\n… (đã cắt bớt)" if len(chuong_trinh) > 6000 else ""
    return (f"{goc}\n\nChương trình bạn vừa viết:\n{cat}{duoi}"
            f"\n\nNó bị từ chối vì: {loi}\n{duoi_cung}")


async def stage_semantic_program(
    text: str,
    analysis: dict,
    api_key: str,
    contract: "RequestContract | None" = None,
    observer=None,
    domain: str | None = None,
) -> tuple["SemanticProgramSpec | None", str | None]:
    """LLM tổng hợp `SemanticProgramSpec` — ≤3 lượt, lỗi validator gửi ngược.

    Trả `(spec, None)` khi hợp lệ, `(None, lý_do)` khi hỏng.

    R0 nguyên vẹn: LLM viết CHƯƠNG TRÌNH, không quyết kết quả — interpreter tất
    định mới là authority (luật cứng #11).

    ĐỔI TỪ MỘT LƯỢT → ≤3 (2026-08-23). Bản cũ ghi *"retry ở đây chỉ để cứu lỗi
    parse, không phải để dò dần cho đúng"* — vế sau vẫn đúng và vẫn được giữ,
    nhưng vế đầu hoá ra bao trùm hơn ta tưởng. Tám lượt probe E2E liên tiếp trên
    một đề (ghép ngoặc bằng ngăn xếp, route `serve`, API thật) chết ở TÁM lỗi
    hình dạng KHÁC NHAU, mỗi lần một chỗ: `container` nhận biểu thức, rồi nhận
    literal, `pop` viết như biểu thức, rồi `peek` viết như câu lệnh, biến bool
    dùng thẳng làm điều kiện… Không lỗi nào là hiểu sai đề — chương trình dựng
    đúng nghĩa vụ, đúng cấu trúc dữ liệu, chỉ sai CÁCH VIẾT. Và mỗi lỗi ấy đều
    đã có sẵn một thông báo Pydantic nói đúng chỗ sai.

    Vá từng lớp bằng luật prompt là đuổi theo một biến ngẫu nhiên: sửa xong lớp
    này thì lượt sau model rơi vào lớp khác (`RULES §3c` gọi đây là
    DEEP_HARDENING). Đưa lỗi ngược cho chính nó sửa thì cả LỚP biến mất một lần
    — đúng khuôn `stage_simulate` đã dùng từ M3.

    Trần là HẰNG SỐ, nên claim D1 không suy suyển: số lượt LLM vẫn bị chặn bởi
    call graph chứ không đi theo độ dài trace. Chương trình đúng thì interpreter
    vẫn tự sinh toàn bộ bước mà không tiêu thêm một token nào.

    Cấu trúc và enum do `responseSchema` cưỡng chế (constrained decoding). Nhưng
    đó KHÔNG phải đảm bảo tuyệt đối — Flash có ghi nhận rơi vào vòng lặp lặp
    token trong literal số cho tới `MAX_TOKENS` rồi trả JSON cụt; nên nhánh lỗi
    parse dưới đây là đường sống, không phải phòng thủ thừa.

    ─── `domain` ────────────────────────────────────────────────────────────

    `None` = miền Tin học, tức **hành vi trước đó nguyên vẹn**. Trước bản này
    tên skill viết CỨNG là `"semantic_program"`, nên `geometry_program_generator.md`
    không có một người gọi nào trong `app/` — chỉ harness đo mới với tới nó bằng
    cách bọc `load_skill` từ ngoài. Hệ quả: đề hình học đi qua sản phẩm được
    **viết chương trình bằng prompt Tin học**, và trượt ở chỗ trông như mô hình
    kém trong khi thật ra ta đưa nhầm đề bài cho nó.
    """
    from app.simulation.semantic_program.contract import generate_json_schema
    from app.simulation.semantic_program.domain_profile import program_skill_for
    from app.simulation.semantic_program.validator import validate_semantic_program

    from app.simulation.semantic_program.grammar_card import grammar_card

    skill = program_skill_for(domain) if domain else "semantic_program"

    base = f'Đề bài:\n"""\n{text}\n"""'
    if contract is not None:
        base = f"{base}\n\n{_facts_for_prompt(contract)}"
        base = f"{base}\n\n{_obligations_for_prompt(contract)}"
    # Hợp đồng IR phải đi kèm, vì Gemini KHÔNG nhận được schema của nó (xem
    # `grammar_card.py`). Thiếu nó, mô hình tự đặt tên trường và 38/40 case
    # trượt thẩm định — đo được ở lượt pilot thứ hai.
    # Thẻ theo MIỀN: đề hình học nhận bản thu hẹp (không IR Tin học, không
    # `visual_bindings`). `domain=None` ⇒ bản đầy đủ, tức hành vi Tin học
    # nguyên vẹn — cùng khuôn fail-safe với chính `skill` ở dòng trên.
    base = f"{base}\n\n{grammar_card(domain)}"

    prompt = base
    loi_cuoi = "không rõ"

    for lan in range(MAX_SEMANTIC_PROGRAM_ATTEMPTS):
        with stage_scope("semantic_program"):
            raw = await call_gemini(
                api_key,
                load_skill(skill),
                prompt,
                generate_json_schema(),
                0.1,
            )

        loi: str | None = None
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            loi = f"JSON không parse được ({e})"
        else:
            if not isinstance(payload, dict):
                loi = (
                    "đầu ra không phải một đối tượng JSON "
                    f"(nhận {type(payload).__name__})"
                )
            else:
                val = validate_semantic_program(payload)
                if val.ok:
                    # ─── XUẤT XỨ CŨNG PHẢI GỬI NGƯỢC ────────────────────────
                    #
                    # Vòng sửa này trước đây chỉ gửi lại lỗi SCHEMA. Cổng
                    # grounding thì chạy SAU, ở `route.py`, nên lời từ chối
                    # của nó **không bao giờ tới được mô hình**: chương trình
                    # được sinh đúng một lần rồi bị giết ở hạ nguồn.
                    #
                    # Đo được ở CONFIRMATION_V2: 6/10 chi tiết grounding là
                    # *"có initial_value nhưng thiếu source_fact_id"* trên các
                    # đỉnh dẫn xuất (`C`, `D`, `B'`, `C'`, `D'`, `S`). Mô hình
                    # khai `model_assumption` cho hai đỉnh đầu rồi quên phần
                    # còn lại — một lỗi nó tự sửa được nếu biết mình đã sai.
                    #
                    # ⚠️ KHÔNG nới cổng. Cùng `check_grounding`, cùng phán
                    # quyết, cùng trần 3 lượt; chỉ thêm ĐƯỜNG PHẢN HỒI. Và
                    # cùng khuôn với lỗi schema: gửi lại LỜI TỪ CHỐI, không
                    # gợi ý cách sửa — gợi ý là ta đang viết chương trình hộ.
                    #
                    # Vì sao không nhồi luật này vào prompt: `test_prompt_size_
                    # guard` chặn ở 4800 byte với đúng lý do ấy — *"luật trong
                    # prompt là GỢI Ý, luật trong validator là RÀNG BUỘC"*.
                    # ─── THẨM ĐỊNH TĨNH CŨNG PHẢI GỬI NGƯỢC (V3 §5) ────────
                    #
                    # Cùng lý do với grounding, và cùng khuôn. Chạy TRƯỚC
                    # grounding vì nó rẻ hơn và bệnh nặng hơn: một chương trình
                    # tham chiếu điểm chưa dựng thì mọi câu hỏi về xuất xứ đều
                    # nói về một chương trình không chạy nổi.
                    #
                    # Thông điệp NGẮN và máy đọc được — `mã · vị trí · vật ·
                    # mong đợi · thực tế`. Không thêm văn xuôi vào prompt chính.
                    from app.simulation.semantic_program.ir_static_check import (
                        kiem_tinh,
                    )
                    t = kiem_tinh(val.spec)
                    if not t.ok and lan < MAX_SEMANTIC_PROGRAM_ATTEMPTS - 1:
                        loi = "chương trình không thực thi được — " + t.phan_hoi()
                        _emit(observer, "semantic_program_attempt",
                              n=lan, ok=False, message=loi, gate="ir_static")
                        prompt = _prompt_sua(base, raw, loi,
                                             de=text, domain=domain)
                        continue
                    if contract is not None:
                        from app.simulation.semantic_program.grounding_gate import (
                            check_grounding,
                        )
                        g = check_grounding(contract, val.spec)
                        # ─── DỪNG HẲN, KHÔNG SỬA (§9/§10) ──────────────────
                        #
                        # Lỗi trung thực năng lực không phải một sai sót mô
                        # hình sửa được: nó nói mô hình đã tự giải rồi giấu kết
                        # luận vào toạ độ. Gửi đi sửa là trả tiền cho một lượt
                        # giấu khéo hơn. Và nó là tín hiệu gần nhất cho "đề này
                        # ngoài IR" — `gm_10` là bài mặt cầu.
                        if not g.ok and g.error_code in KHONG_DUOC_SUA:
                            loi = (f"[{g.error_code}] "
                                   + "; ".join(g.unresolved[:4]))
                            _emit(observer, "semantic_program_attempt",
                                  n=lan, ok=False, message=loi,
                                  gate="grounding", repairable=False)
                            return None, f"SEMANTIC_PROGRAM_INVALID: {loi}"
                        if not g.ok and lan < MAX_SEMANTIC_PROGRAM_ATTEMPTS - 1:
                            loi = ("xuất xứ dữ liệu chưa đủ — "
                                   + "; ".join(g.unresolved[:4]))
                            _emit(observer, "semantic_program_attempt",
                                  n=lan, ok=False, message=loi, gate="grounding")
                            prompt = _prompt_sua(base, raw, loi,
                                                 de=text, domain=domain)
                            continue
                    return val.spec, None
                loi = val.error

        loi_cuoi = loi
        _emit(observer, "semantic_program_attempt", n=lan, ok=False, message=loi)
        # Cùng khuôn với `stage_simulate` — lỗi validator là thứ DUY NHẤT gửi
        # ngược. Không gợi ý cách sửa: gợi ý là ta đang viết chương trình hộ.
        prompt = _prompt_sua(base, raw, loi, de=text, domain=domain)

    return None, f"SEMANTIC_PROGRAM_INVALID: {loi_cuoi}"


# ── Orchestrator ──────────────────────────────────────────────

def _dung_scene3d(spec, contract=None) -> dict | None:
    """`SemanticProgramSpec` → cảnh 3D, hoặc `None` nếu bài không phải hình học.

    ─── VÌ SAO NGƯỜI GHÉP NẰM Ở ĐÂY, KHÔNG Ở `route.py` ────────────────────

    Hướng phụ thuộc một chiều: engine (kernel · validator · interpreter · các
    cổng) KHÔNG được biết tới tầng trình bày, vì khi ấy một thay đổi thẩm mỹ sẽ
    đụng vào thứ đang gác cửa. `test_scene3d.py` giữ luật đó bằng cách cấm **mọi**
    module dưới `app/simulation` import `scene3d`.

    `pipeline` là người GỌI route, không phải một tầng của nó — nên ghép ở đây
    thoả cả hai: cảnh 3D vẫn tới được envelope, mà ranh giới không phải nới một
    milimét nào. `SemanticRouteOutcome.scene3d` chỉ là một Ô TRỐNG kiểu `dict`.

    ─── VÌ SAO CHẠY LẠI INTERPRETER ───────────────────────────────────────

    `verify_and_compile` trả `final_memory` nhưng không trả `trace`, mà timeline
    cần trace đầy đủ. Interpreter tất định và không đọc trạng thái ngoài, nên
    chạy lại cho **đúng kết quả cũ**; `compile_semantic_program_to_envelope`
    trong route cũng đã chạy lại vì cùng lý do, và ghi rõ tiền lệ ấy.

    Bài Tin học trả `None` — cảnh rỗng cũng là `None`: một khung 3D trống không
    nói được gì, và bày nó ra là mời người học đi tìm thứ không có.
    """
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import (
        build_simulation_state,
    )

    try:
        ket = SemanticProgramInterpreter().execute(spec)
        canh = build_scene3d(build_simulation_state(spec, ket, contract))
    except Exception:  # noqa: BLE001 — trình bày hỏng KHÔNG được giết phép đo
        # Một lỗi ở tầng cảnh không được làm hỏng một chương trình đã qua mọi
        # cổng. Mất hình còn hơn mất cả kết quả đã kiểm chứng.
        return None
    return canh if canh["objects"] else None


def _la_hinh_hoc(text: str) -> bool:
    """Đề này có thuộc miền hình học không — TẤT ĐỊNH, không hỏi LLM."""
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC,
        detect_domain,
    )

    return detect_domain(text) == DOMAIN_HINH_HOC


def _that_bai_hinh_hoc(outcome, analysis: dict, plan: dict, observer) -> dict:
    """Envelope cho đề HÌNH HỌC mà route sinh không phục vụ được.

    Nói đúng thứ đã xảy ra: *hệ hiểu đây là hình học, đã thử dựng, và chương
    trình chưa qua kiểm chứng* — thay vì đổ cho đề bài là "môn khác".

    `outcome` có thể `None`: route dừng trước khi dựng nổi IR. Khi ấy vẫn là
    thất bại của việc SINH, không phải của phạm vi.
    """
    category = "geometry_generation_failed"
    ly_do = getattr(outcome, "reason", None) if outcome is not None else None
    _emit(observer, "envelope", status="unsupported", simulation_id=None,
          failure_category=category)
    return {
        "status": "unsupported",
        # `reason` KỸ THUẬT giữ nguyên — nó nuôi harness và diagnostics. Học
        # sinh đọc `learner_reason`, gắn ở biên API (`learner_messages`).
        "reason": ly_do or "Chưa dựng được chương trình hình học cho đề này.",
        "failure_category": category,
        "error_code": getattr(outcome, "error_code", None) if outcome else None,
        "stage_reached": getattr(outcome, "stage_reached", None) if outcome else None,
        "representation_plan": plan,
        "analysis": analysis,
    }


def _envelope_tu_route_sinh(outcome, analysis: dict, plan: dict, observer) -> dict:
    """Envelope phát từ route sinh — MỘT chỗ dựng, hai chỗ gọi.

    Hai lối vào (nhánh phát bình thường, và nhánh classifier lệch) phải dựng ra
    envelope GIỐNG HỆT nhau. Chép thành hai bản là cách chắc chắn để `source`
    hoặc `representation_plan` thiếu ở đúng một lối vào — thứ chỉ lộ ra khi đọc
    artifact nhiều tuần sau.
    """
    env = dict(outcome.envelope or {})
    env["analysis"] = analysis
    env["representation_plan"] = plan
    env["source"] = "semantic_program"
    # Cảnh 3D đi kèm envelope, KHÔNG thay nó: đường 2D cũ nguyên vẹn, và bài
    # Tin học không có khoá này. Gắn ở đây vì đây là MỘT chỗ dựng envelope duy
    # nhất — hai lối vào phải ra cùng một hình dạng.
    if outcome.scene3d:
        env["scene3d"] = outcome.scene3d
        # …và envelope nói đúng MIỀN của nó. `compile_semantic_program_to_
        # envelope` khai cứng `"generic"` vì route sinh vốn dựng cho miền Tin
        # học; hệ quả là một bài thiết diện hiện lên bề mặt học sinh dưới nhãn
        # "Tổng quát". `domain` chỉ nuôi nhãn và màu ở danh mục — module vẫn
        # tra bằng `simulation_id` (`store.loadEnvelope`), nên đổi nó không
        # đụng đường phân giải module.
        env["domain"] = "geometry"
    _emit(observer, "envelope", status="ok",
          simulation_id=env.get("simulation_id"), source="semantic_program")
    return env


async def _semantic_route_attempt(
    text: str, analysis: dict, api_key: str, observer, domain: str | None = None
) -> "SemanticRouteOutcome | None":
    """Hai lượt LLM + toàn bộ cổng tất định. Trả `None` khi chưa dựng nổi IR.

    Mọi thất bại đều được EMIT chứ không nuốt: benchmark cần biết bài hỏng ở
    khâu nào, và "hỏng ở khâu nào" mới là dữ liệu, còn "hỏng" thì không.

    `domain` đi xuống **cả hai** lượt LLM. Đổi một lượt mà quên lượt kia là đúng
    lỗi Phase 5 đo được: skill viết chương trình đã sang hình học, skill đọc đề
    thì không, nên mô hình khai nghĩa vụ Tin học cho bài hình học ở 3/6 ca.
    """
    from app.simulation.semantic_program.route import verify_and_compile

    contract, cerr = await stage_semantic_analyze(text, api_key, domain)
    if contract is None:
        _emit(observer, "semantic_route", stage_reached="semantic_analyze",
              executable=False, servable=False,
              error_code=ErrorCode.SEMANTIC_PROGRAM_INVALID.value, reason=cerr)
        return None

    # Phát KÈM witness của từng nghĩa vụ. Ground truth độc lập không được phép
    # đoán tên biến mà LLM tự đặt — custodian chỉ khai nghĩa vụ và giá trị
    # đúng, còn ánh xạ nghĩa-vụ → tên-biến thì đọc từ contract này.
    _emit(observer, "semantic_contract",
          so_fact=len(contract.input_facts),
          so_nghia_vu=len(contract.obligations),
          kinds=sorted({ob.kind for ob in contract.obligations}),
          obligations=[
              {"kind": ob.kind, "container": ob.container, "witness": ob.witness}
              for ob in contract.obligations
          ])

    spec, serr = await stage_semantic_program(
        text, analysis, api_key, contract, observer=observer, domain=domain
    )
    if spec is None:
        _emit(observer, "semantic_route", stage_reached="semantic_program",
              executable=False, servable=False,
              error_code=ErrorCode.SEMANTIC_PROGRAM_INVALID.value, reason=serr)
        return None

    outcome = verify_and_compile(contract, spec)
    # Cảnh 3D CHỈ dựng khi chương trình đã chạy trọn. Chương trình không qua
    # thẩm định thì không có hình — đó là toàn bộ luận điểm của đề tài, và nếu
    # nới ở đây thì renderer sẽ bày ra thứ chưa ai kiểm.
    if outcome.executable:
        outcome = outcome.model_copy(
            update={"scene3d": _dung_scene3d(spec, contract)})
    _emit(observer, "semantic_route",
          stage_reached=outcome.stage_reached,
          executable=outcome.executable,
          servable=outcome.servable,
          error_code=outcome.error_code,
          failure_category=outcome.failure_category,
          reason=outcome.reason,
          weak_kinds=outcome.weak_kinds,
          details=outcome.details,
          total_steps=outcome.total_steps,
          frame_count=outcome.frame_count,
          # Trạng thái cuối là thứ DUY NHẤT đem so được với ground truth độc
          # lập. Thiếu nó ở đây thì benchmark chấm được đúng 0 case — và chấm
          # sai theo hướng im lặng, sau khi đã tiêu hết quota.
          final_memory=outcome.final_memory,
          # §7 — ba con số của SCALE NORMALIZATION. Phát cùng chỗ với mọi quan
          # trắc khác: một lượt đo không giữ được chúng thì tỉ lệ literal có
          # căn cứ phải suy ngược từ `details`, và suy ngược là chỗ hai định
          # nghĩa "biện minh" bắt đầu trôi khỏi nhau.
          justified_literals=outcome.justified_literals,
          unjustified_literals=outcome.unjustified_literals,
          constraints_checked=outcome.constraints_checked,
          constraints_verified=outcome.constraints_verified,
          # THẨM QUYỀN VỀ TÊN cho bộ đo — xem `SemanticRouteOutcome`. Không
          # phát ra đây thì bộ đo buộc phải hoà giải lần thứ tám.
          resolved_names=outcome.resolved_names,
          source_invariant_stats=outcome.source_invariant_stats)
    return outcome


async def _chay_duong_hinh_hoc(text: str, api_key: str, observer) -> dict:
    """ĐƯỜNG SẢN PHẨM của miền hình học — hai lượt LLM, không một lượt thừa.

        đề → geometry_analyze → RequestContract → tổng hợp Semantic Program
           → chuẩn hoá → thẩm định tĩnh → grounding + trung thực năng lực
           → interpreter tất định → checker → transport → envelope + Scene3D

    ─── CÁI GÌ BIẾN MẤT SO VỚI ĐƯỜNG CŨ, VÀ VÌ SAO KHÔNG MẤT GÌ ────────────

    Không còn: `stage_analyze` (Tin học) · `build_representation_plan` ·
    `stage_classify` · `check_scope_and_simulatability` ·
    `check_execution_authority`.

    Không cổng nào trong số ấy **phán quyết được** về một đề hình học: enum của
    `analyze.md` không có giá trị nào cho miền này, nên bốn nhãn nó cho ra đều
    sai như nhau, và mã cũ phải dựng một khối miễn trừ để hình học lọt qua
    chính chúng. Bỏ một cổng chỉ biết nói sai không phải là nới cổng.

    Mọi cổng THẬT SỰ gác hình học vẫn nguyên và vẫn chạy trong
    `_semantic_route_attempt` → `verify_and_compile`: lược đồ, thẩm định tĩnh,
    grounding, trung thực năng lực, hậu điều kiện, phủ, bề mặt học sinh,
    transport. `servable` vẫn là thứ duy nhất quyết định có phát hay không.

    `analysis = {}` là ĐÚNG chứ không phải chỗ trống chờ lấp: `stage_semantic_
    program` không đọc trường nào của nó cho miền hình học — bốn wave đo đều
    gọi thẳng với `{}` và cho cùng kết quả.
    """
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC,
        co_duong_thuc_thi,
    )

    # ─── CỔNG SƯ PHẠM, NAY LÀ THẨM QUYỀN CỦA CHÍNH MIỀN ─────────────────────
    #
    # Đường cũ hỏi `check_scope_and_simulatability`, tức hỏi một enum Tin học
    # (`REQUIRES_SIMULATION` = INTERACTIVE_MODEL · INTERACTIVE_ARTIFACT ·
    # MEANINGFUL_TRACE) — không nhãn nào tả được một bài hình học tĩnh. Bỏ nó mà
    # không thay gì là NUỐT một lời từ chối đáng nói, nên nó được thay chứ không
    # bị xoá.
    #
    # `co_duong_thuc_thi` là phép kiểm TẤT ĐỊNH của chính miền hình học: đề có
    # ánh xạ được tới một nghĩa vụ CÓ CHECKER không. Fail-closed ở cả ba chỗ
    # (sai miền · không manh mối · manh mối trỏ nghĩa vụ không checker), và 0
    # lượt gọi. Nó trả lời đúng câu mà cổng cũ chỉ giả vờ trả lời.
    if not co_duong_thuc_thi(text, DOMAIN_HINH_HOC):
        # ⚠️ KHÔNG dùng lại `_that_bai_hinh_hoc`: nó nói *"chưa dựng được
        # chương trình"* (`geometry_generation_failed`), mà ở đây chưa hề có
        # lượt dựng nào. Lời từ chối phải nói ĐÚNG thứ đã xảy ra — đề là hình
        # học thật, nhưng nó không hỏi một đại lượng nào hệ kiểm chứng được.
        ma = ErrorCode.GATE_NOT_SIMULATION_SUITABLE
        _emit(observer, "semantic_route", stage_reached="scope",
              executable=False, servable=False, error_code=ma.value,
              reason="không ánh xạ tới nghĩa vụ nào hệ thực thi được")
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="not_simulation_suitable")
        return {
            "status": "unsupported",
            "reason": "Đề thuộc hình học không gian nhưng không hỏi một đại "
                      "lượng nào hệ dựng và kiểm chứng được (khoảng cách, góc, "
                      "thể tích, thiết diện, quan hệ song song/vuông góc).",
            "failure_category": "not_simulation_suitable",
            "error_code": ma.value,
            "stage_reached": "scope",
            "representation_plan": {},
            "analysis": {},
        }

    outcome = await _semantic_route_attempt(text, {}, api_key, observer,
                                            DOMAIN_HINH_HOC)
    if outcome is not None and outcome.servable:
        return _envelope_tu_route_sinh(outcome, {}, {}, observer)
    # Thất bại phải nói ĐÚNG thứ đã xảy ra — *hệ hiểu đây là hình học, đã thử
    # dựng, chương trình chưa qua kiểm chứng* — chứ không đổ cho đề là môn khác.
    return _that_bai_hinh_hoc(outcome, {}, {}, observer)


async def run_pipeline(
    text: str,
    api_key: str,
    pattern_store=None,
    observer=None,
    semantic_route: str = "off",
) -> dict:
    """Chạy trọn pipeline; trả ValidatedSimulationEnvelope hoặc unsupported.

    Ném RuntimeError khi stage simulate thất bại sau retry (API trả 422).

    M7.13B: `pattern_store` (inject, optional) bật pattern reuse — CHỈ sau
    classify và CHỈ cho generic.rule_scene (bảo vệ specialized selection).
    None → hành vi compose cũ nguyên vẹn.

    M14 §F2: `observer` (inject, optional) THỤ ĐỘNG — thu event có cấu trúc; None
    → hành vi production KHÔNG đổi một bit (evaluation dùng CHUNG orchestration
    này, bất biến #22).
    """
    # ─── ĐƯỜNG HÌNH HỌC LÀ ĐƯỜNG CHÍNH, KHÔNG PHẢI NHÁNH SHADOW ──────────
    #
    # Đề tài là mô phỏng 3D hình học không gian. Trước bản này một đề hình học
    # vẫn phải đi qua `stage_analyze` Tin học TRƯỚC, rồi mới tới nhánh sinh ngữ
    # nghĩa — tức tiêu một lượt LLM cho một bản phân tích mà chính mã này đã ghi
    # là KHÔNG MANG THÔNG TIN với hình học (`analyze.md` không có giá trị
    # `domain_scope` nào cho hình học, nên mô hình buộc phải chọn một nhãn sai).
    #
    # Hệ quả cũ, cả hai đều thật: một lượt gọi thừa mỗi đề, và ba cổng Tin học
    # (`scope`, `simulatability`, `execution_authority`) phán quyết trên nhãn
    # sai ấy — phải dựng khối miễn trừ riêng cho hình học để nó lọt qua.
    #
    # `detect_domain` chạy trên VĂN BẢN, ở server, 0 lượt gọi. Rẽ ở đây thì
    # hình học không còn phụ thuộc analyze/classify/catalog Tin học một dòng
    # nào, và khối miễn trừ kia thôi cần tồn tại cho đường sản phẩm.
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC as _DOMAIN_HH,
        detect_domain as _dò_miền,
    )

    if _dò_miền(text) == _DOMAIN_HH:
        return await _chay_duong_hinh_hoc(text, api_key, observer)

    # ─── NGOÀI MIỀN ⇒ FAIL CLOSED. Không còn nhánh Tin học nào ở đây ────────
    #
    # Nhánh ấy từng dài 460 dòng: analyze → plan → shadow → classify →
    # recovery → bốn cổng → selector/direct → pattern reuse → simulate. Nó đã
    # KHÔNG VỚI TỚI ĐƯỢC từ khi biên API đóng cửa cho mọi miền khác, và mã chết
    # thì phải xoá chứ không để nằm đó làm người đọc tưởng nó còn chạy.
    #
    # Đây là chỗ DUY NHẤT trả lời cho miền ngoài phạm vi, nên nó nói thẳng.
    _emit(observer, "envelope", status="unsupported", simulation_id=None,
          failure_category="out_of_scope")
    return {
        "status": "unsupported",
        "reason": "Hệ thống này mô phỏng HÌNH HỌC KHÔNG GIAN (Toán 11–12). "
                  "Đề bạn gửi không thuộc phạm vi ấy.",
        "failure_category": "out_of_scope",
        "error_code": ErrorCode.GATE_OUT_OF_SCOPE.value,
        "stage_reached": "domain",
    }


