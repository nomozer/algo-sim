# M17 W3-LIVE-C1 — sửa cổng cơ chế cho `binary.character_encoding`

**Kết luận: root cause GIẢ ĐỊNH của checkpoint là SAI; root cause THẬT đã được
ĐO và sửa ở đúng chỗ hỏng.** Cổng cơ chế **không** bị nới; fail-closed nguyên vẹn.

## 1. Đo trước, sửa sau (§2)

Checkpoint giả định analyze phát `positional_representation.non_binary_base` —
mắt xích downstream của một "chuỗi đã khai". Probe live (3 HTTP, chỉ tới
`stage_analyze`, temperature 0.1) bác bỏ điều đó:

| Case | `prescribed_procedure` đo được |
|---|---|
| LIVE-ENC-1 | `null` |
| LIVE-ENC-2 | `null` |
| LIVE-ENC-3 | **`positional_representation.binary_positional_weights`** |

```json
{
  "analyze_exposed_positional": [
    "positional_representation.binary_positional_weights",
    "positional_representation.non_binary_base"
  ],
  "w3_owned_mechanisms": ["positional_representation.character_code_mapping"]
}
```

Hai hệ quả:

- **Thiết kế "chain-aware gate" (§3/§4) tự vô hiệu.** Nó chỉ mở
  `non_binary_base`, trong khi giá trị THẬT SỰ chặn W3 là
  `binary_positional_weights` — mà §5 test 4 của chính checkpoint lại **yêu cầu
  giá trị đó phải FAIL**. Làm đủ 14 test vẫn không gỡ được W3.
- **Root cause thật nằm ở chỗ khác**: `character_code_mapping` — cơ chế DUY NHẤT
  `binary.character_encoding` sở hữu — **chưa bao giờ có trong enum analyze**.

## 2. Root cause thật: tái phát anti-pattern #1

`ANALYZE_SCHEMA.prescribed_procedure` là enum ĐÓNG dẫn xuất từ
`mechanisms.analyze_exposed_values()`. Trong hàm đó, họ `tree_traversal` và
`bounded_control_flow` được **splat** từ `FAMILY_MECHANISMS`, còn họ positional
lại được **liệt kê bằng hai string VIẾT TAY**. Khi W3 thêm
`character_code_mapping` vào `FAMILY_MECHANISMS`, danh sách viết tay **không đi
theo**.

Đây đúng là anti-pattern #1 trong `ARCHITECTURE_MAP §8`, với tiền lệ đã gây bug
thật: *`_GENERIC_SCHEMA` từng thiếu `drag` → Gemini **không thể** phát ra dù
prompt cho phép.* Lần này hậu quả là:

```
analyze không thể phát character_code_mapping
  → nhánh direct-ownership của check_mechanism_consistency_for_target
    KHÔNG BAO GIỜ thoả mãn được cho W3
  → target chỉ lọt khi analyze tình cờ trả "none" (nhánh permissive)
  → khi analyze ÉP cơ chế, nó chọn hàng xóm gần nhất còn lại
    (binary_positional_weights) → capability_gap
```

Điều này giải thích khớp dữ liệu baseline: 5/6 lượt bị chặn, lượt PASS duy nhất
là lượt analyze trả `none`.

## 3. Cách sửa — nối cơ chế vào enum, KHÔNG nới cổng

`mechanisms.analyze_exposed_values()` nay splat thẳng từ taxonomy:

```python
*FAMILY_MECHANISMS[FamilyId.POSITIONAL_REPRESENTATION],
```

thay cho hai string viết tay. Diff hành vi: enum có thêm **đúng một** giá trị,
`positional_representation.character_code_mapping`; hai giá trị cũ giữ nguyên vị
trí và thứ tự.

**Không làm** (và có test khoá): thêm `non_binary_base` hay
`binary_positional_weights` vào `owned_mechanisms` của W3; hard-code target id
trong cổng; cho qua mọi cơ chế cùng họ; sửa `analyze.md` / `classify.md` /
`CharacterEncodingSpec` / validator; thêm chain metadata mới.

`mechanism_gate.py` **không đổi một dòng nào** — cổng vẫn là phép thử sở hữu đơn,
fail-closed.

## 4. Ranh giới giữ nguyên (bằng chứng negative)

| Prescribed | Target | Kết quả | Vì sao |
|---|---|---|---|
| `character_code_mapping` | `binary.character_encoding` | **PASS** | sở hữu trực tiếp |
| `binary_positional_weights` | `binary.character_encoding` | **GAP** | thuộc `decimal_to_binary`, chặn cứng 0–255/8 bit ⇒ **không chở nổi BMP tới 65535** |
| `non_binary_base` | `binary.character_encoding` | **GAP** | không cấp ownership giả |
| `character_code_mapping` | `binary.decimal_to_binary` | **GAP** | không nuốt cơ chế hàng xóm |
| `row_predicate_filter` · `reveal_sequence` · `tree_traversal.preorder` | W3 | **FAMILY_MISMATCH** | khác họ |
| cơ chế không tồn tại / rỗng | W3 | **fail-closed** | |
| `non_binary_base` · `binary_positional_weights` | `binary.base_conversion` | PASS | không đổi hành vi target cũ |
| `bounded_control_flow.bounded_loop` | `algorithm.bounded_control_flow` | PASS | như trên |
| `row_predicate_filter` | `database.relational_table_query` | PASS | như trên |

Thêm hai lock chống trôi:

- `test_analyze_exposed_phu_DU_co_che_positional_chong_troi_w3_live_c1` — enum
  analyze phải PHỦ ĐỦ `FAMILY_MECHANISMS[POSITIONAL_REPRESENTATION]`; thêm cơ chế
  positional mới mà quên nối là **ĐỎ**.
- `test_gate_khong_hard_code_target_id` — quét mã nguồn cổng, cấm mọi literal
  tên target/tiền tố.

## 5. Cache (§6)

`CACHE_VERSION` **23 → 24**. Bằng chứng đường gọi: lookup nằm TRƯỚC pipeline và
`main.py` **chỉ cache `status == "ok"`** ([main.py:254-256](../../../../backend/app/main.py)),
nên refusal cũ không thể bị phát lại. Vẫn bump vì **chính sách định tuyến đổi**:
analyze nay phát được một cơ chế mới ⇒ envelope OK sinh dưới enum cũ có thể mang
target kém phù hợp (mã hoá ký tự trước đây chỉ lọt khi analyze tình cờ trả
`none`). Đúng tiền lệ đã ghi trong `test_api.py`: W2C bump 20→21 cũng vì "enum
analyze mới ⇒ chính sách classify đổi".

`HISTORY_SCHEMA_VERSION` giữ **2** — envelope persist không đổi hình.
`family_count` **11**, `target_count` **22** — không thêm family/target.

## 6. Giới hạn còn lại

Sửa này **không** giải quyết LIVE-ENC-3. Đề *"Mô phỏng Unicode code point của ký
tự ế **và chuyển mã đó sang nhị phân**"* khiến analyze đặt cơ chế chính là
`binary_positional_weights` (bước đổi cơ số) thay vì `character_code_mapping`
(bước tra bảng mã) ⇒ cổng chặn ĐÚNG LUẬT, vì cơ chế đó thật sự không chở nổi
BMP. Sửa tiếp sẽ phải chạm `analyze.md` hoặc ngữ nghĩa cổng — **cả hai đều nằm
trong stop condition §20**, nên checkpoint dừng và báo.
