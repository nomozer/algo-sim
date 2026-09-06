# POINT_INITIALIZATION_REPAIR_EFFICACY

> 2026-09-07. **Đúng 1 logical application LLM call** — bằng trần đăng ký.
> `MEASUREMENT_CLASS = DEVELOPMENT_REPAIR_PROBE` · `HELD_OUT_CLAIM = NO` ·
> `INITIAL_SYNTHESIS_CALLS_THIS_WAVE = 0`. **Không đụng một dòng mã sản phẩm
> nào**; thẻ giữ **A** suốt lượt.
>
> ```
> POINT_INITIALIZATION_DIAGNOSTIC_DISCOVERABLE = YES
> ONE_REPAIR_RECOVERS_CORRECT_SIMULATION       = YES
> PERMANENT_SLOT_INSTRUCTION_NEEDED            = NOT_PROVED
> RECOMMENDED_NEXT_ACTION = MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION
> ```

## 1. Trạng thái đầu — khớp bàn giao

HEAD `38dc75f` · `CACHE_VERSION` **85** · candidate `36e81713…`
(`--verify` exit 0, 90 file) · `PRODUCT_VARIANT` **A**.

Sáu băm model-facing đo lại **sau** wave: `prompts 55ac1ca6…` ·
`grammar_card e0fbbc84…` · `synthesis_schema 8c57c9de…` ·
`analyze_schema 515001b5…` · `capability 85bd3167…` ·
`semantic_environment f7def620…` — **giống từng byte** với bảng ở
`PROVENANCE_AFFORDANCE_AB_4_LUOT §1`. Đó là bằng chứng máy cho câu *"bề mặt
model-facing không nhúc nhích"*, không phải lời hứa.

## 2. Câu hỏi

Wave trước để lại **đúng một** lỗi trên lượt P1/RATIO: mô hình đặt toạ độ vào
ô `at` **của `memory_declarations[]`**, trong khi `at` là trường của câu lệnh
`declare_point`. Mọi thứ khác của lượt ấy đã đúng — `ratio 2/5`, `C` khai
`model_assumption`, `D` khai `source_fact_id`, `N` dựng bằng `divide_segment`.

Câu hỏi wave này **không** phải *"có nên thêm hướng dẫn về ô chứa toạ độ
không"*. Nó là câu hỏi đứng **trước** câu đó:

> Vòng sửa **đã có sẵn** của sản phẩm có tự đóng được lỗi này không?

Vì nếu có, thì một dòng hướng dẫn thường trực là **chi phí không cần thiết**
gắn vĩnh viễn vào mọi lượt sinh.

## 3. Tiền kiểm — 0 lượt gọi

**`PREFLIGHT.json`** (chạy trước, không tốn call): gold đi trọn `served` với
**`ND = 6`**, và **3 phản ví dụ** đều bị chặn **đúng tầng** — không có tầng nào
"đỏ nhờ tầng khác".

**`backend/tests/geometry/test_repair_probe_integrity.py` — 12 pass, 0 lượt
gọi.** Các test này chạy **chính** `probe_point_init_repair.main_async`, tức đi
qua `pipeline.stage_semantic_program` và `_prompt_sua` của **sản phẩm**, chỉ
thay provider bằng stub. Tiền lệ bắt buộc phải làm vậy nằm ngay trong kho:
`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL` — một certifier xanh vì nó gọi
tắt, chưa bao giờ chạy đường thật.

Bốn thứ bộ kiểm ràng: đếm đúng **một** lượt sửa (lượt 0 do probe trả raw lịch
sử, không tốn call) · payload sửa **có đủ ba thứ** (chương trình hỏng, chẩn
đoán validator, đề/hợp đồng) · candidate được **lưu trước khi chấm** · và bộ
chấm phân biệt được ba kiểu hỏng khác nhau (sai slot / đúng slot–hỏng ratio /
đúng slot–mất provenance).

## 4. Kết quả — `repair-20260906T212731Z`

```
REPAIR_LOGICAL_CALLS = 1/1     PHYSICAL_ATTEMPTS = 2     TOKENS = 3123
```

`PHYSICAL_ATTEMPTS = 2` **không** phải hai lượt gọi model: lượt 0 là raw
candidate lịch sử do probe trả thẳng, chỉ lượt 1 ra mạng.

| chiều | kết quả |
|---|---|
| `SLOT_REPAIRED` | **PASS** |
| `PROVENANCE_PRESERVED` | **PASS** |
| `RATIO_PRESERVED` | **PASS** (`T_WRITTEN = 2/5`, `OPERAND_ORDER = C->D`) |
| `GROUNDING` · `SOURCE_INVARIANTS` · `RUNTIME` · `POSTCONDITIONS` | **PASS** |
| `EXACT_ANSWER` | **PASS** — `ANSWER_OBSERVED = 6` |
| `TRACE_CONSTRUCTION` | **PASS** — producer `construct_point.divide_segment`, `depends = [C, D]` |
| `SCENE3D` · `SERVABLE` | **PASS** · `STAGE = served` |

**Một lượt sửa, trọn đường tới `served`.**

## 5. Bản sửa — delta đúng bằng chỗ hỏng

Mô hình chọn **`initial_value`**, không dựng thêm câu lệnh `declare_point`:

```diff
  { "name": "C", "type": "point3",
-   "at": [0,0,0],
+   "initial_value": [0,0,0],
    "model_assumption": "Đặt điểm C tại gốc tọa độ." }
  { "name": "D", "type": "point3",
-   "at": [10,0,0],
+   "initial_value": [10,0,0],
    "source_fact_id": "do_dai_doan", "model_assumption": … }
```

Hai biểu diễn ấy **tương đương chính tắc** theo tiêu chí đăng ký trước lượt
gọi (`registration.tieu_chi_thanh_cong.slot`) — ghi trước, nên không phải nới
tiêu chí sau khi thấy kết quả.

Phần còn lại **không xê dịch**: `N` vẫn không có toạ độ, vẫn được sinh bởi
`construct_point.divide_segment(C, D, 2/5)`; `C` giữ `model_assumption`; `D`
giữ `source_fact_id`; `model_assumption` **không** lan sang `N`. Đây là chỗ đắt
nhất của phép đo — một vòng sửa "đúng đáp số" mà **đánh mất provenance** hoặc
**bẻ ratio** thì đã là hồi quy, và bộ chấm có test riêng cho từng kiểu (`B3`,
`B4`).

Chẩn đoán mà validator gửi đi trỏ đích danh vị trí và **nói ra ô đúng**:
*"`memory_declarations[0].at`: khoá này không có trong `memory_declarations[]`
— `at` là trường của `declare_point`, chuyển giá trị ấy sang `initial_value`"*,
kèm danh sách trường hợp lệ. Nó có từ `4ab25e9` (wave trước), và lượt này là
lần đầu nó được **đo hiệu lực** thay vì chỉ được kiểm bằng test tổng hợp.

## 6. Token — ba số, không trộn

```
CURRENT_WAVE_REPAIR_TOKENS          = 3123   (prompt 2466 · candidates 501 · thoughts 156 · cached 0)
HISTORICAL_INITIAL_SYNTHESIS_TOKENS = 5023   (lượt P1/RATIO wave trước)
COMBINED_OBSERVED_RECOVERY_TOKENS   = 8146
```

Chỉ số **thứ nhất** thuộc ngân sách wave này. Số thứ ba là **chi phí quan sát
được của cả đường phục hồi**, không phải chi phí của một lượt sinh. Chưa có
đơn giá provider ⇒ **không** kết luận gì về tiền.

## 7. Một lỗi BỘ ĐO, tìm bằng stub — và nó ở file test, không ở runner

Đăng ký nói: *"Sửa runner hoặc scorer chỉ khi stub chứng minh lỗi bộ đo."* Stub
đã chứng minh đúng một lỗi như vậy, nhưng **không** nằm ở runner:

`test_offline_guard::test_pipeline_quen_mock_cung_bi_chan` **xanh khi chạy một
mình**, **đỏ khi chạy sau** `test_repair_probe_integrity.py`. Tức chốt chặn
mạng offline — thứ bảo chứng cho câu *"pytest = 0 API call thật"* — mất tác
dụng **trong im lặng** cho mọi test chạy sau.

Nguyên nhân, một dòng: probe lưu `goc_call = G.call_gemini` rồi ở `finally` ghi
nó ngược vào **cả** `G` **lẫn** `PL`. Bản đầu của fixture chỉ vá `G`, nên
`goc_call` **chính là stub**, và `PL.call_gemini` ở lại = stub **vĩnh viễn** —
bộ gỡ vá không biết về `PL` để hoàn nguyên.

**Runner giữ nguyên từng byte**, có chủ đích. Cách khôi phục của nó **đúng cho
lượt chạy thật**: `pipeline.py` viết `from app.ai.gemini import call_gemini`,
nên hai thuộc tính là **một** đối tượng. Và `runner_sha256 dad902f0…` đã nằm
trong artifact live **bất biến** — sửa runner bây giờ là làm hỏng danh tính của
chính con số vừa đo. Nên tiền đề im lặng ấy được **khoá bằng test** thay vì
được sửa:

- `test_A2b_tien_de_cua_probe_hai_module_TRO_CUNG_MOT_ham` — khẳng định
  `PL.call_gemini is G.call_gemini`. Đổi `pipeline.py` sang `import gemini as G`
  sẽ làm test này đỏ **trước khi** probe kịp ghi đè thứ nó không hề mượn.
- `test_A2c_provider_KHONG_RO_RI_sang_pipeline_sau_khi_chay` — sau lượt chạy,
  cả hai thuộc tính phải trở lại đúng hàm ban đầu.

Fixture cũng đổi sang `pytest.MonkeyPatch.context()` riêng thay vì fixture
`monkeypatch` dùng chung: `monkeypatch` chỉ hoàn nguyên lúc **teardown**, tức
sau khi thân test chạy xong, nên **không thể** viết trong thân test một khẳng
định về trạng thái *sau khi đã gỡ vá*. Không có thay đổi đó thì `A2c` không
quan sát được thứ nó cần quan sát.

**Tiêm lỗi để chứng minh bộ khoá đỏ được** — bỏ đúng dòng vá `PL`:

```
FAILED test_repair_probe_integrity.py::test_A2b_tien_de_cua_probe_hai_module_TRO_CUNG_MOT_ham
FAILED test_repair_probe_integrity.py::test_A2c_provider_KHONG_RO_RI_sang_pipeline_sau_khi_chay
FAILED test_offline_guard.py::test_pipeline_quen_mock_cung_bi_chan
3 failed, 14 passed
```

Dòng thứ ba là **triệu chứng gốc**, tái hiện đúng. Trả dòng vá về: **17 pass**.

### 7b. Lỗ thứ hai, có sẵn từ trước, cùng họ

Cũng trong lượt này lộ ra một điểm yếu **không do wave sinh ra**: fixture
`block_real_network` gỡ `GEMINI_API_KEY`, nhưng `app/persistence/db.py` gọi
`load_dotenv` **lúc import** và **điền lại** biến vừa bị xoá. Nếu một test là
test **đầu tiên** chạm `app.*`, thứ tự thành *xoá key → import `app.main` →
`load_dotenv` nạp lại*. Trước đây ẩn vì suite luôn có test khác import `app`
sớm hơn — tức phép kiểm phụ thuộc **thứ tự thu thập**, thứ đổi mỗi lần thêm
file test. Xác nhận là **có sẵn từ trước** bằng `git stash` (đỏ y hệt khi không
có file của wave này). Sửa ở `backend/conftest.py`: import `app.persistence.db`
cho `load_dotenv` chạy **xong** rồi mới gỡ key — biến phép gỡ thành vô điều
kiện.

Cả hai lỗ đều thuộc **bộ đo**, ngoài `MEASURED_SYSTEM_PATHS`; candidate
`36e81713…` không đổi.

## 8. Kết luận — theo đúng nhánh đã đăng ký trước lượt gọi

`registration.quy_tac_ket_luan.thanh_cong_tron_duong`:

```
POINT_INITIALIZATION_DIAGNOSTIC_DISCOVERABLE = YES
ONE_REPAIR_RECOVERS_CORRECT_SIMULATION       = YES
PERMANENT_SLOT_INSTRUCTION_NEEDED            = NOT_PROVED
RECOMMENDED_NEXT_ACTION = MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION
```

`PERMANENT_SLOT_INSTRUCTION_NEEDED = NOT_PROVED` là kết luận **có sức nặng
nhất** ở đây, và nó là kết luận **phủ định**: wave trước bàn giao đề xuất
*"thêm một dòng hướng dẫn về ô chứa toạ độ"*, phép đo này cho thấy **chưa
chứng minh được là cần**. Vòng sửa sẵn có đã đóng lỗ, tốn 3123 token, không
cần một dòng gắn vĩnh viễn vào mọi lượt sinh.

Nó **không** nói ngược lại: chưa chứng minh cần ≠ chứng minh không cần.
`n = 1`.

## 9. `CACHE_VERSION` — không bump

Giữ **85**. Luật bump là **served → refusal** mới cần bump. Wave này không sửa
prompt, không sửa policy, không sửa mã sản phẩm; sáu băm model-facing giống
từng byte (§1). Không có đường nào để một đề từng `served` trở thành từ chối.

## 10. Cổng đã chạy

pytest đầy đủ **4031 pass · 1 skip · 1 deselect**, đỏ duy nhất là
`test_holdout_readiness_7b::test_bao_cao_da_sinh_va_KHONG_TROI` với lý do máy
in ra `CÂY LÀM VIỆC BẨN — niêm phong đòi cây sạch` (`cay_sach: False`) — đó là
khoá **cây sạch**, tự xanh sau commit, không phải hỏng hóc.

`replay_demo_cases` **5/5** (+ `REDUCED_CHAIN_CASES 1/1`) ·
`audit_demo_crash_surface` **biên đúng kỳ vọng 6/6, ném ra ngoài 0** ·
`freeze_evaluation_candidate --verify` **exit 0** · `git diff --check` sạch.

## 11. Giới hạn bằng chứng

- **`n = 1` ca, một lượt sửa.** `DEVELOPMENT_SIGNAL`, không phải ước lượng tổng
  thể. `CAUSAL_ATTRIBUTION = LIMITED`.
- **Bắt đầu từ raw candidate lịch sử**, không phải từ một lượt sinh mới ⇒ phép
  đo nói về **vòng sửa**, **không** nói gì về tỉ lệ sinh đúng ngay lượt đầu.
- `gemini-2.5-flash` là **alias, không phải snapshot** ⇒ `reproducibility =
  LIMITED`; lượt sau có thể gặp trọng số khác.
- Ba mức bằng chứng **không trộn**: *"đáp số đúng"* · *"có bước dựng đúng"* ·
  *"AI tự sinh ổn định"*. `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`.
- Token so ở **mức quan sát**; không kết luận về tiền.

**Việc kế tiếp: `MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`.** Hai wave
liên tiếp đã đo xong hai mảnh rời — hướng dẫn provenance **đạt** mục tiêu của
nó (2/2), và lỗ `at` **tự đóng được** bằng vòng sửa. Bước hợp lý là gộp phần
tối thiểu đã có bằng chứng vào thẻ, rồi **xác nhận trên ca mới** (fresh), chứ
không phải thêm tiếp một dòng hướng dẫn chưa chứng minh được là cần.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
