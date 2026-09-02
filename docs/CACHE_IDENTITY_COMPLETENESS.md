# CACHE_IDENTITY_COMPLETENESS — đóng C1

> Thực hiện **2026-09-03**. **0 lượt gọi model · 0 đổi hình học · 0 đổi giao
> diện · 0 dependency mới.**
>
> Đây là **kỷ luật phiên bản được máy cưỡng chế**, **không phải** cache địa chỉ
> theo nội dung. Khoá cache runtime không đổi một dòng.

---

## 1. Lỗ

Khoá cache là *text đã chuẩn hoá + `CACHE_VERSION`*. `CACHE_VERSION` là một con
số **người phải nhớ tăng**.

Đổi một prompt, một lược đồ gửi cho mô hình, hay một chữ ký IR mà quên bump ⇒
đề đã phân tích tiếp tục được phục vụ bằng envelope sinh từ **một phiên bản hệ
không còn tồn tại**, và **không gì phát hiện**.

Nó **không** làm hình học sai — kernel vẫn tính đúng. Nó bẻ **phép đo**: chạy
lại sau khi sửa prompt sẽ đo phải bản cũ ở mọi đề đã cache.

⚠️ Kho này đã dùng đúng lập luận *"một bảng phải nhớ cập nhật là một bảng sẽ
quên"* để gỡ `TU_PHEP_DUNG`. Lập luận ấy áp vào một **con số** phải nhớ tăng thì
không yếu hơn.

---

## 2. Bản vá — một cổng, không phải một khoá cache mới

### 2.1 Vân tay môi trường sinh, ở **chính** thẩm quyền đã có

`runtime_identity` xuất thêm `semantic_environment_fingerprint()` +
`semantic_environment_hash()`. **Không dựng vân tay thứ hai** — `skill_fingerprint()`
đã sở hữu câu *"prompt nào đang chạy"*, và hàm mới dùng lại nó.

| thành phần | nguồn | vì sao có mặt |
|---|---|---|
| `prompts` | `skill_fingerprint()["tong"]` — mọi `skills/*.md` qua `gemini.SKILLS_DIR` | văn bản gửi thẳng cho mô hình |
| `grammar_card` | `skill_fingerprint()["grammar_card"]` | thẻ ghép vào user message |
| `synthesis_schema` | `generate_json_schema()` | `responseSchema` lượt tổng hợp |
| `analyze_schema` | `SEMANTIC_ANALYZE_SCHEMA` + `analyze_schema_for("hinh_hoc")` | `responseSchema` lượt đọc đề |
| `capability` | `stable_capability_hash()` | chữ ký IR + tập checker — quyết định chương trình nào được nhận |

**Không băm cùng một sự thật hai lần.** `manh_hop_dong` (mảnh hợp đồng gửi kèm
lượt sửa) chọn **các dòng của chính thẻ**, nên `grammar_card` đã phủ nó.

**Không băm `pipeline.py` nguyên tệp.** 794 dòng, gần hết là luồng điều khiển;
băm cả tệp thì mọi lần sửa logic không liên quan đều làm cổng đỏ — và một báo
động giả là cách nhanh nhất để một cổng bị tắt.

**Dẫn từ `SKILLS_DIR`, không từ một danh sách viết tay.** Nhờ vậy một file prompt
**mới** mà runtime dùng thì không thể nằm ngoài vân tay: cả hai đọc cùng một
chỗ. Có ca riêng chứng minh (`test_TIEM_them_file_prompt_MOI_*`).

### 2.2 Khoá — một cặp, không hơn

`backend/cache_identity.lock.json` ghi `cache_version` + `semantic_environment_hash`
+ từng thành phần. `scripts/lock_cache_identity.py`: không cờ ⇒ ghi lại,
`--verify` ⇒ thoát != 0 khi lệch. Cùng khuôn sync-lock kho đã dùng cho lược đồ
(`test_schema_sync`) và bảng loại vẽ (`test_scene3d_ts_sync`).

⚠️ **Đặt NGOÀI `app/` có chủ đích.** `MEASURED_SYSTEM_PATHS` gồm `backend/app`;
để khoá trong đó thì mỗi lần làm mới lại làm **candidate đánh giá** hết hiệu
lực — trộn hai cơ chế không liên quan, và biến một lượt vá prompt thành một lượt
đóng băng lại.

⚠️ **Script KHÔNG tự bump `CACHE_VERSION`.** Quyết định *"envelope cũ còn dùng
được không"* là của người: bump thừa thì vứt cache của cả kho, bump thiếu thì
phục vụ kết quả cũ. Script đoán hộ sẽ đoán sai đúng lúc đắt nhất.

### 2.3 Quy trình

```
sửa nguồn  →  test ĐỎ  →  người xem lại
           →  còn dùng được?  ⇒ chạy lại script
           →  không còn?      ⇒ bump CACHE_VERSION (ba cổng) rồi chạy script
           →  xanh
```

---

## 3. Cổng đỏ được — chứng minh, không chỉ tuyên bố

Bốn ca **TIÊM** trong `tests/test_cache_identity.py`, tiêm bằng cách vá chính
thư mục/hàm runtime dùng, trong `tmp_path` hoặc `monkeypatch` — cây sản phẩm
không bẩn một byte:

| ca | tiêm gì | kết quả |
|---|---|---|
| `TIEM_prompt_doi` | sửa nội dung một `skills/*.md` | vân tay đổi |
| `TIEM_them_file_prompt_MOI` | thêm một prompt chưa từng có | vân tay đổi |
| `TIEM_chu_ky_IR_doi` | thêm một mục vào `_CHU_KY` | băm năng lực đổi ⇒ vân tay đổi |
| `TIEM_hop_dong_model_facing_doi` | đổi lược đồ gửi cho mô hình (chỉ `title`) | vân tay đổi |
| `TIEM_chi_bump_VERSION` | bump version, không làm mới khoá | cặp lệch ⇒ đỏ |

Và **trên cây thật**, không qua monkeypatch: thêm một dòng vào
`geometry_program_generator.md` ⇒ cổng ĐỎ và nêu đúng thành phần:

```
MÔI TRƯỜNG SINH NGỮ NGHĨA ĐÃ ĐỔI.
  khoá:  version 63 · f545293124e52891…
  hiện:  version 63 · 72c5dec5bab177d2…
  thành phần đổi: ['prompts']
```

Khôi phục ⇒ 15/15 xanh.

⚠️ Thông điệp cố ý **nêu tên thành phần**, không chỉ in hai chuỗi hex. Một lời
từ chối bắt người đọc tự đi tìm sẽ được xử lý bằng cách bump cho xong.

---

## 4. Hành vi cache **không** đổi

`_cache_key` vẫn băm *text đã chuẩn hoá*; `_cache_lookup` vẫn so `policy_version`
với `CACHE_VERSION`. `test_KHOA_CACHE_san_pham_KHONG_doi` quét **mã nguồn** của
hai hàm ấy để chắc không vân tay nào lọt vào đường chạy thật — lọt là mọi hàng
cache hiện có mất hiệu lực trong im lặng.

```
PRODUCTION_CACHE_KEY_CHANGED    NO
CACHE_STORAGE_FORMAT_CHANGED    NO
CACHE_RUNTIME_BEHAVIOR_CHANGED  NO
CONTENT_ADDRESSED_CACHE         NO
```

---

## 5. Giới hạn còn lại, khai chính xác

Vài **câu bọc tiếng Việt** nằm trong `pipeline.py` — *"Hãy sửa ĐÚNG chỗ đó và
giữ nguyên phần còn lại."*, tiêu đề khối dữ kiện/nghĩa vụ, dòng *"Lần trước bị
từ chối vì:"* — **không** nằm trong vân tay. Chúng có tới mô hình, nên sửa chúng
vẫn cần bump theo quy ước; chỉ là chưa có máy canh.

Không phủ chúng vì lý do ở §2.1: cách duy nhất rẻ là băm cả tệp, và cái giá là
một cổng đỏ theo mọi lần sửa logic. Muốn phủ nốt thì mở rộng **chính**
`semantic_environment_fingerprint()`, đừng dựng vân tay thứ hai.

Câu đúng sau bản vá này:

> **Đầu vào tĩnh mang nghĩa không thể đổi mà không làm cổng danh tính cache đỏ.**

**Không** phải *"cache tự vô hiệu hoá"* — runtime vẫn dựa vào `CACHE_VERSION`.

---

## 6. Phiên bản

```
CACHE_VERSION            63 → 63   (không đầu vào ngữ nghĩa nào đổi; chỉ thêm cổng)
STABLE_CAPABILITY_HASH   803722ff59dfbdf6…  KHÔNG đổi
thẻ văn phạm             4431 / 3316 byte   KHÔNG đổi
lược đồ model-facing     KHÔNG đổi          prompt KHÔNG đổi
```

`backend/app/runtime_identity.py` nằm trong `MEASURED_SYSTEM_PATHS`, nên
**candidate đánh giá đổi** và được đóng băng lại theo đúng quy trình. Baseline
nghiên cứu đã niêm phong (`a075e9f5…`) **không đổi, không chạy lại**.

---

## 7. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **2846 passed**, 1 skipped (+15 ca mới) |
| `vitest` | **685 passed** (50 tệp) — frontend không đổi một dòng |
| `npm run build` | PASS |
| `replay_demo_cases` · `audit_demo_crash_surface` | 5/5 · 1/1 · 6/6, ném 0 |
| `lock_cache_identity.py --verify` | exit 0 |
