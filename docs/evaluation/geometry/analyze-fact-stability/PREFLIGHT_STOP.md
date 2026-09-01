# ANALYZE_SOURCE_FACT_STABILITY — DỪNG Ở CỔNG §1, **0 lượt provider**

> Không gọi analyze để vá dữ liệu thiếu (§1). Không đề nào bị thay. Không sửa
> mã bộ đo.

## 1. Cổng §1 hỏi gì, và câu trả lời

Trước bất kỳ lượt gọi nào, phải chứng minh **tái tạo được CHÍNH XÁC model input
đã dùng cho analyze R1**, và §3 đòi một phép so trước mỗi lượt:

    CURRENT_ANALYZE_INPUT_HASH == R1_ANALYZE_INPUT_HASH

Artifact `name-contract-probe/probe.json` lưu, dưới mỗi ca, khoá `analyze`:

    raw_request_contract · request_contract_hash · roundtrip_ok
    input_facts · obligations

Tất cả là **ĐẦU RA**. `request_contract_hash` băm hợp đồng analyze *phát ra*,
không băm thứ *gửi đi*. Không có `payload`, không có `model_input_hash`.

    ANALYZE_R1_REPLAYABLE = NO

## 2. Vì sao "dựng lại được" không cứu được cổng này

Payload analyze **là tất định** từ dữ liệu đã lưu + mã ở commit đóng băng:
prompt = `analyze_skill_for("hinh_hoc")`, user = `Đề bài:\n"""…"""` từ
`problem_text`, schema = `analyze_schema_for("hinh_hoc")`, nhiệt độ 0.1. Dựng
lại thử cho cả bốn ca ra bốn hash phân biệt:

| ca | dựng lại | đối chiếu với |
|---|---|---|
| `n1_thoi_dinh_thu_tu` | `9801bd03518a7038` | **không có** |
| `n2_lang_tru_xien_hai_vecto` | `e6fa66e9b2485e5c` | **không có** |
| `n3_mat_qua_diem_dan_xuat` | `1d4f10e0789fb4cc` | **không có** |
| `n4_giao_duong_mat_roi_do` | `dc4e128eec30956f` | **không có** |

Bốn hash ấy **không chứng minh gì**. Cổng §3 là một phép so hai vế; ở đây chỉ
có một vế, nên "assert" biến thành so một bản dựng lại với chính nó — đúng thứ
phép tự-khẳng-định mà `test_probe_artifact_replayable.py` được viết ra để cấm
(*"không đọc cờ artifact tự ghi"*).

§1 nói rõ điều kiện thay thế: chỉ được dùng R1 nếu có **bằng chứng tất định từ
artifact bất biến rằng payload analyze đã được lưu ĐẦY ĐỦ**. Nó chưa bao giờ
được lưu — không đầy đủ, không một phần. Điều kiện sai dứt khoát.

## 3. Lỗ hổng này BẤT ĐỐI XỨNG, và đó là chỗ đáng nói

Cùng artifact, cùng ca, tầng tổng hợp có đủ:

    synthesis_input: canonical_domain · selected_skill · skill_hash
                     model_card_hash · payload · model_input_hash

và nó **kiểm được thật**: `TU_KIEM` của lượt chạy báo `tự chứa 4/4, dựng lại
4/4`. Nên đây không phải giới hạn định dạng artifact, cũng không phải chuyện
analyze khó chụp hơn. Đây là **một nhánh bị bỏ sót trong chính bộ đo tôi viết**:
hàm bao `bao()` gọi `payload_chuan_tac` trong nhánh `SYNTHESIS` và chỉ chuyển
tiếp ở nhánh `ANALYZE`.

⚠️ Và nó là **lần thứ hai của cùng một lớp lỗi**. `CLEAN_BASELINE_V2_SYNTHESIS_
STABILITY` đã phải DỪNG trước API vì đúng lý do này ở tầng **tổng hợp** (hợp
đồng chỉ lưu dạng tóm tắt). Bản vá khi ấy — chụp payload + hash + guard trong
suite — được làm cho tầng tổng hợp và **không kéo xuống tầng analyze**. Tôi
dựng lưới ở một tầng rồi để nguyên tầng dưới.

## 4. Điều KHÔNG làm

- **Không gọi analyze để "vá"** (§1). 0 lượt provider.
- **Không** hạ cổng §3 xuống thành *"cùng problem_text là đủ"*. Nới nó thì mọi
  con số k=3 sau đó không còn nghĩa: chúng sẽ đo cả biến thiên của mô hình lẫn
  biến thiên của đầu vào mà không tách được hai thứ.
- **Không** thay hay loại đề nào (§6 chỉ mở khi đã qua §1).
- **Không** sửa prompt/parser/schema/runner (§23).

## 5. Câu hỏi của wave vẫn còn nguyên giá trị

Quan sát đã có từ `NAME_ONLY_CONTRACT_LIVE_PROBE` không mất đi: `analyze` trích
dữ kiện toạ độ ở `n1` (3 fact) và `n2` (4 fact), **không trích ở `n3` và `n4`**,
trên bốn đề nêu toạ độ cùng một kiểu. Đó vẫn là nguyên nhân gần của thất bại
grounding duy nhất, và vẫn đáng đo.

Cái thiếu không phải câu hỏi — là **hạt giống chạy lại được** để đo nó cho ra
nghĩa.

    PROVIDER_CALLS_USED = 0 / 8
    NEXT_ACTION = REPLAYABLE_ANALYZE_SEED
