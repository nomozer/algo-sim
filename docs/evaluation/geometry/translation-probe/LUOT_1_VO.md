# LƯỢT 1 VỠ — ghi trước khi chạy lại

Lượt live đầu của `FRESH_TRANSLATION_COMPOSITION_PROBE` **vỡ giữa chừng** vì
lỗi của bộ đo, không của hệ. **5/12 lượt provider đã tiêu, artifact KHÔNG được
ghi.**

## Nó vỡ ở đâu, và vì sao chỗ ấy đáng chú ý

`_dang_tinh_tien` giả định toán hạng `vector` của `translate` là một **chuỗi**:

```python
if e.get("kind") == "translate" and e.get("vector") in ra["vector_producers"]:
    #                               ^^^^^^^^^^^^^^^^ dict → TypeError
```

Ở `t3`, mô hình viết nó là một **biểu thức lồng**:

```json
{"kind": "translate", "point": "B",
 "vector": {"kind": "vector_from_points", "from_point": "A", "to_point": "D"}}
```

Đó là thứ kiến trúc cấm — `test_R0_bieu_thuc_hinh_hoc_chi_nhan_TEN` đòi mọi
trường của biểu thức hình học là TÊN, vì nhận cấu trúc ở đó là mở đường cho
toạ độ đi thẳng từ LLM vào.

⇒ Bộ đo **vỡ ngay trên một quan sát có ý nghĩa** thay vì ghi nó lại. Nay nó
đếm riêng `vector_operand_nested`.

## Điều tôi đã thấy trước khi chạy lại

Toàn bộ output còn đọc được. Ghi ra vì lượt 2 chạy **sau khi tôi đã thấy nó**:

| đề | lớp | `translate` |
|---|---|---|
| `t1_binh_hanh_dinh_thu_tu` | ONE_SHOT_CORRECT | `['C']` |
| `t2_lang_tru_dinh_tang_tren` | ONE_SHOT_CORRECT | `['B_prime', 'C_prime']` |
| `t3_hop_tinh_tien_day_chuyen` | *(vỡ giữa lượt)* | lồng biểu thức vào `vector` |
| `t4_mat_xich_trong_chuoi_sau` | *(chưa chạy)* | — |

Không thấy: token từng đề, hợp đồng, payload, kết quả cổng, mọi số của §20.

## Vì sao chạy lại cả bốn thay vì chỉ t3/t4

Chạy tiếp t3/t4 giữ được trần 12, nhưng để t1/t2 chỉ tồn tại trong console —
**không artifact, không chạy lại được**. Đó đúng là lỗ hổng đã chặn wave
`SYNTHESIS_STABILITY_K3` phải dừng trước API, và lặp lại nó ở đây là không học
được gì từ nó.

Quyết định do người vận hành: chạy lại cả bốn, chấp nhận vượt trần §9, đổi lấy
một artifact đầy đủ và bốn ca cùng một điều kiện.

Điều KHÔNG đổi giữa hai lượt: bộ đề, oracle, prompt, thẻ, hợp đồng. Chỉ
`_dang_tinh_tien` đổi — một hàm ĐẾM của bộ đo, không nằm trên đường sinh
chương trình.
