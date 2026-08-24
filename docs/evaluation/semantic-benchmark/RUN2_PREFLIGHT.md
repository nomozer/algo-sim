# PREFLIGHT LƯỢT ĐO #2 — chạy 2026-08-24, TRƯỚC khi có seed

> Mọi mục dưới đây **chạy được lại**. Lệnh nằm ngay cạnh kết quả để người khác
> kiểm chứ không phải tin. Preflight này **không** tiêu một call API nào.

HEAD lúc chạy: `1bd0437` · candidate đóng băng: `b407af0` (cây sạch: **true**)

## 1. Cổng cơ học — 5/5 XANH

| # | Kiểm | Lệnh | Kết quả |
|---|---|---|---|
| 1 | Candidate không trôi khỏi bản đóng băng | `python backend/scripts/freeze_evaluation_candidate.py --verify` | ✅ khớp, mã sản phẩm 130 file · `61b12f71…` |
| 2 | Runner + ngân sách khoá đúng | `pytest tests/semantic_program/test_sealed_runner.py -q` | ✅ **39 passed** |
| 3 | Suite backend không hồi quy | `pytest -q` | ✅ **2033 passed · 18 skipped** |
| 4 | Tập loại trừ đúng vân tay | `MEASURED_RUN1_IDS_FINGERPRINT.txt` | ✅ `e2ebcf79…` khớp §4 |
| 5 | Phép chọn còn tái lập, giao rỗng | `select_by_seed.py --seed <giả> --exclude-measured` | ✅ chọn 40/49 · **giao với 40 bài đã đo = 0** |

Chi tiết mục 5 (seed giả `PREFLIGHT_KHONG_PHAI_SEED_THAT`, **không** ghi file):

```
selection_count             40
effective_pool_size         49
excluded_measured_count     40
excluded_fingerprint        e2ebcf79d52372f700da916066f2fe28942f4d98fa29e8d96ad751a172eeae94
selection_pool_fingerprint  34d11adc5084047f92b290ac906fc6177c8aa3d23b9b0323dd8b325d48d50808
giao với tập đã đo          0
```

Vân tay pool `34d11adc…` khớp mắt xích thứ hai trong chuỗi provenance bốn tầng
của lượt #1 — pool **không** bị dựng lại giữa hai lượt.

## 2. Hai khối telemetry MỚI, chỉ đọc được từ lượt #2

Lượt #1 không có chúng. Đây là lý do đáng đo lại ngoài chuyện A/B.

- **`token_dau_ra_theo_route`** — token ĐẦU RA (`candidates` **+** `thoughts`),
  tách route sinh ↔ route module. Bỏ `thoughts` là báo thấp đi gần ba lần: ở
  stage `semantic_program` nó lớn hơn `candidates` **2,6×**.
- **`coercion_rate`** — bốn biên chuẩn hoá của `contract.py` phải ra tay bao
  nhiêu lần, tách theo lớp. Cao và dai dẳng **không** phải tin tốt: nó nghĩa là
  mô hình đã thành thói quen viết khác hợp đồng, và chỗ phải sửa là bề mặt sinh
  chứ không phải thêm lớp gộp thứ năm.

Số của lượt #1 tính ngược được từ `sealed_cases.json[].token` (đã ghi đủ năm
trường ngay từ đầu), dùng làm mốc so:

| | token đầu ra/ca | prompt |
|---|---:|---:|
| Route sinh | **4.085** | 79.247 |
| Route module | 7.481 | 407.453 |

⚠️ Đây là **telemetry hỗ trợ, KHÔNG phải D2** — hai route chạy trên hai
population khác nhau. D2 chỉ đọc trên `D2_matched_subset`.

## 3. Kỳ vọng phải chốt TRƯỚC, để không tự lừa mình sau

Chẩn đoán trên SEALED `7e5df014…` (ghi trong `12085d5`): trong 40 ca, **LLM chỉ
sai thuật toán thật ở 3 ca**. Phân bố nguyên nhân của 37 ca còn lại:

| nguyên nhân | ca | đã vá sau lượt #1? |
|---|---:|---|
| `spec_version` float vs `"1.0"` | 21 | ✅ |
| `str` làm visual container | 3 | ✅ |
| `for_range.step` bọc `literal` | 2 | ✅ |
| `if` nhận thẳng biến bool | 1 | ✅ |
| taxonomy không nhận chủ thể vô hướng | 5 | ✅ (xem §7b — có sai lệch) |
| chết ở cổng phạm vi / grounding | 4 | — (đúng, ngoài môn) |
| C₁a không có đường tạo thứ đề hỏi | 1 | ❌ |

**Phát biểu đúng về kỳ vọng**: sau vá, **tối đa ~36/40 sẽ CHẠM TỚI interpreter**
thay vì 9. Đó **không** phải dự đoán về A. Qua thẩm định ≠ chạy đúng ≠ thoả
nghĩa vụ, và các cổng sau (`interpreter → C₁a → C₁b → C₂`) tới giờ mới nhìn thấy
**9 chương trình**, rụng còn 3 rồi còn 1. Ngoại suy từ n=9 là không có cơ sở.

Vòng sửa `stage_semantic_program` ≤3 lượt **chưa từng chạy** trong lượt #1: đo
được 37/37 ca gọi đúng 1 lượt, vì vòng sửa mới có ở `d6b7b30` — **6,5 giờ sau**
lượt đo. Lượt #2 là lần đầu tiên nó được đo.

**Không đặt pass mark.** `freeze_protocol.md` cấm, và §8 của protocol không hứa
A sẽ cao hơn.

### 3b. Bốn bản vá đáng giá bao nhiêu — CHẨN ĐOÁN CƠ HỌC, 0 API call

`sealed_cases.json` giữ **nguyên văn** khối lỗi Pydantic của từng ca, và khối ấy
liệt kê ĐỦ mọi lỗi của chương trình. Nên phân loại từng lỗi là đủ để biết ca nào
nay qua được tầng cú pháp — không phải tiêu một lượt LLM nào.

Công cụ: `backend/scripts/classify_run1_failures.py` (chạy lại được, `--json`).

```
27 ca trượt thẩm định ở lượt #1
├── 22  mọi lỗi đã được gộp  → NAY QUA tầng Pydantic
├──  3  còn lỗi ngoài bốn biên → vẫn trượt
└──  2  lỗi parse (JSON cụt)  → không kết luận được
```

Đếm theo **lỗi** (một ca có thể nhiều lỗi): `spec_version` 21 · `container_var` 4
· `step_literal` 2 · `condition_bool` 1.

Phễu thẩm định vì thế đổi từ **9/36** lên **31/36** chương trình chạm tới
interpreter — nhưng đọc cho đúng:

> ⚠️ **Qua Pydantic mới là CHẠM cổng kế, không phải chạy đúng.** Sau đó còn
> `validate_semantic_program` (tầng ngữ nghĩa) → interpreter → C₁a → C₁b → C₂.
> Ở lượt #1, 9 chương trình qua được cú pháp rụng còn 3 chạy được, còn 1 phát
> được. Các cổng sau **chưa bao giờ nhìn thấy quá 9 chương trình**.
>
> ⚠️ Con số này chạy trên **40 ca ĐÃ LỘ**, nên nó là **chẩn đoán**, tuyệt đối
> không được trình bày như kết quả held-out.

### 3c. DỰ ĐOÁN TIỀN ĐĂNG KÝ — chốt trước khi có seed

Ghi ở đây để lượt #2 có thể **bác bỏ** được. Dự đoán viết sau khi thấy số thì
không phải dự đoán.

Ba lớp lỗi dưới đây **chưa được vá và cố ý không vá** (đóng băng mã §2 đang có
hiệu lực; vá chúng lúc này là vá theo ca đã lộ). Chúng ta dự đoán chúng **sẽ
xuất hiện lại ở lượt #2**:

| lớp | lượt #1 | bản chất |
|---|---:|---|
| `kind` bịa ra (`function_call`, `array`) | 3 lỗi / 2 ca | LLM tự chế kind biểu thức ngoài union đóng |
| `field` ngoài `{left,right,val,data}` | 5 lỗi / 1 ca | IR **không có kiểu bản ghi**; LLM cần `.diem` của một học sinh |
| JSON cụt / parse hỏng | 2 ca | Flash rơi vào lặp token tới `MAX_TOKENS` |

Lớp thứ hai là **giới hạn IR thật**, không phải lỗi ký pháp: gộp nó đòi thêm
kiểu bản ghi, tức mở ngữ nghĩa chứ không phải gộp cách viết. Nếu lượt #2 cho
thấy nó phổ biến thì đó là **kết luận có giá trị của luận văn** về ranh giới của
bounded IR — không phải một bug cần vá gấp.

Nếu ba lớp này **không** xuất hiện ở lượt #2 thì dự đoán sai, và điều đó cũng
phải được ghi đúng như thế.

## 4. CHẶN — hai thứ preflight không tự giải được

### (a) Quyết định về sai lệch taxonomy — GVHD, trước khi cấp seed

Xem **§7b** của `RUN2_PROTOCOL.md`. Tóm tắt: protocol tiền đăng ký chốt 9 nghĩa
vụ và chốt rằng *đề cần `predicate_verdict` vẫn phải trượt*; hệ hiện tại có 11
nghĩa vụ, gồm `predicate_verdict`. Lập luận bênh (lỗ hổng cấu trúc, tập đóng) và
lập luận chống (nghĩ ra sau khi thấy kết quả) đều đã ghi ở đó.

Hai lối đi, phải chọn **trước** khi có seed:

| | Hệ quả |
|---|---|
| **Giữ 11** | mang theo lời khai §7b; tập đề vẫn held-out nguyên vẹn, nhưng taxonomy không còn tư cách tiền đăng ký |
| **Hoàn về 9** | lượt #2 sạch tiền đăng ký, đổi lại bỏ một bản vá cấu trúc có thật và ~5 ca sẽ trượt vì lý do đã biết trước |

### (b) Seed #2 — chỉ GVHD cấp được

Tính độc lập của phép chọn nằm ở chỗ seed **không** đến từ người viết mã và
**không** được chọn sau khi đã thấy kết quả. Seed #1 là `23082026`.

## 5. Sau khi có seed — trình tự, không đảo

```bash
python backend/scripts/freeze_evaluation_candidate.py --verify        # phải xanh

cd docs/evaluation/semantic-benchmark/custodian
python select_by_seed.py --seed <SEED_GVHD> --exclude-measured --write
python sealed_ground_truth.py          # Python thuần, 0 import mã sản phẩm

cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
  .venv/Scripts/python.exe scripts/run_sealed_evaluation.py           # MỘT LẦN
```

Ngân sách chốt cứng: **520 lượt logic · 620 lần thử HTTP** (13 × 40, dẫn từ call
graph). Vượt trần ⇒ `BUDGET_EXHAUSTED`, `evaluation_complete = false`, **không
chạy bù**.

⚠️ **49 bài cho N=40 là rất sát.** Custodian loại bất kỳ bài nào lúc dựng ground
truth thì phải hoặc hạ `N`, hoặc mở rộng SOURCE UNIVERSE — quyết **trước** khi
chọn, không phải sau.
