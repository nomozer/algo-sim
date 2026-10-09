# real-model-e2e-readiness — khảo sát sẵn sàng đo Gemini thật

LOCAL, Windows, 2026-10-10. `main` = `origin/main` = `28ac1d61`, candidate `93077b51…` (102 file), `CACHE_VERSION` 125,
`LLM_ONLY` mặc định, compiler opt-in. **0 lượt gọi model**, không sửa mã sản phẩm, không đóng băng, không bump cache.
Kết luận: **CHƯA chạy pilot ngay được — cần sửa CÔNG CỤ đo (chỉ `backend/scripts/`), không sửa sản phẩm.**

## 1. Hai loại "thành công" — không được trộn

| | đã có | câu hỏi |
|---|---|---|
| **Foundation** (`foundation_only`) | T8, T11, T12 phục vụ đúng trên chương trình **viết tay kiểu mô hình** (31 + 17 + 25 hàng ghi trước, oracle độc lập, kiểm LOCAL bằng metric riêng) | engine tất định có NHẬN và tính đúng chương trình như thế không |
| **Gemini thật** | chưa có lượt nào cho T8/T11/T12 | từ đề tự nhiên, Gemini có TỰ VIẾT được chương trình mà các cổng nhận không |

Pilot dưới đây chỉ trả lời câu hỏi thứ hai, trên corpus **đã được nhìn** khi xây T8/T11/T12, `k = 1` ⇒ là phép đo
phát triển, không phải held-out, không phải ước lượng độ ổn định.

## 2. Harness có sẵn — kiểm từng cái

| runner | đường chạy | dùng cho pilot được không |
|---|---|---|
| `run_thesis_final_acceptance.py` (`--certify`/`--live`) | stage A/B + `_dung_scene3d`, cổng 8 băm trước ca đầu | **Không.** Bộ ca cố định của lượt đo cuối; kiểm băm 0 call hôm nay: `CANDIDATE_HASH`, `CACHE_VERSION`, `MODEL_FACING_HASHES` TRÔI (93077b51 ≠ d72db7c3; 125 ≠ 94) ⇒ runner từ chối — đúng thiết kế (artifact đo cuối bất biến) |
| `run_geometry_dev_evaluation.py --cases <tệp> --out-dir <thư mục>` | `stage_semantic_analyze` → `stage_semantic_program` (≤3 lần thử, có vòng sửa) → `verify_and_compile` (CÓ metric khung, `route.py:285`) | **Một phần.** Có chế độ thăm dò, trần theo số bài (6 logic / 8 HTTP mỗi bài), ghi token/chi phí (`api_usage_log`). Nhưng BỎ QUA `run_pipeline`: không cổng phạm vi `co_duong_thuc_thi`, không Scene3D, không cổng nghĩa vụ trực quan; không chấm bài phải từ chối; **bộ chấm không so được căn thức** (§4 G1) |
| `measure_geometry_stability.mot_luot` (dùng bởi `run_holdout_pilot.py`, `run_holdout_official.py`) | **`run_pipeline` thật** (miền → phạm vi → route → Scene3D → cổng trực quan → envelope), proxy chỉ ĐỌC hợp đồng/chương trình, `ApiBudget` mỗi lượt (8 logic / 12 HTTP), token theo stage, ghi `{case}-lan{n}.json` ngay sau mỗi lượt (tiếp tục ≠ chạy lại) | **Có — làm lõi.** Bộ đề, thư mục ra và oracle là hằng cấp module (oracle theo TÊN, vd `the_tich_12`); `run_holdout_pilot.py` đã có tiền lệ thay chúng. Thiếu: oracle căn thức, chấm từ chối, lưu envelope |
| `run_multicase_benchmark.py` | lượt completion của 12 ca đóng băng | Không — chỉ cho bộ ca lịch sử |
| `run_photo_problem_live.py` | đường ẢNH | Không — tuyến A; nhưng là mẫu tốt về che khoá (`BoKhuBiMat`, tắt log `httpx`) |

Kiểm 0 call: 19 tệp test của các runner này (`test_geometry_dev_runner`, `test_thesis_runner_alignment`,
`test_acceptance_runner_integrity`, …) — **1061 passed** trên `28ac1d61`.

## 3. Cấu hình provider (đọc mã, không đọc giá trị khoá)

- Model: `GEMINI_MODEL` hoặc mặc định `gemini-2.5-flash` (`app/ai/gemini.py:30`); `backend/.env` có `GEMINI_API_KEY`
  (khác rỗng, bị gitignore), KHÔNG đặt `GEMINI_MODEL`, `ALLOW_LIVE_AI`, `GEOMETRY_COMPILER_MODE` ⇒ flash + `LLM_ONLY`.
- Timeout 120 s/lượt; retry chỉ cho 429/5xx/lỗi mạng, tối đa 4 lần thử, backoff 1–2–4 s; 4xx khác không retry.
- `ApiBudget` chặn theo lượt LOGIC và lần thử HTTP (`BudgetExceeded` dừng sạch); `temperature = 0.2` ⇒ không tất định,
  tái lập bằng ghi lại đầu ra (hợp đồng + chương trình), không bằng gọi lại.
- Token: `record_usage` ghi `usageMetadata` TRƯỚC khi parse (lượt rỗng vẫn tính); chi phí ước tính chặn trên
  `api_usage_log` với bảng giá tra tay 2026-08-25 (flash: 0,30 / 2,50 USD mỗi triệu token vào / ra; token suy luận tính
  giá ra) — phải tra lại trước khi trích số USD.
- Khoá đi trong query `?key=` của URL. Lỗi HTTP chỉ in thân phản hồi (`res.text[:300]`), không in URL; logger `httpx` ở
  mức INFO sẽ in URL — `mot_luot` không tắt nó (runner ảnh thì tắt). Audit tài liệu có cổng "Secret leaks: 0" quét artifact
  trước commit.

## 4. Lỗ của công cụ — phải sửa trước lượt live

| # | lỗ | bằng chứng | sửa (chỉ `backend/scripts/` + test, không chạm `MEASURED_SYSTEM_PATHS` ⇒ không đóng băng lại) |
|---|---|---|---|
| G1 | **Bộ chấm không so được căn thức**: `cham_oracle` dùng `Fraction(str(...))`; `final_memory` giữ `Radical` chính xác | 0 call, chương trình corpus phục vụ ĐÚNG: X1 `Radical(18, 3)` vs `"18√3"`, T1, X5 ⇒ cả ba **FAIL** "không so được" — sẽ đổ lỗi cho mô hình | so bằng số chính xác (`Radical`/bình phương hữu tỉ), không so chuỗi; test có ca căn, phân số, nguyên |
| G2 | dev runner không đi `run_pipeline` | đọc mã (§2) | dùng `mot_luot` làm lõi (đường sản phẩm thật) |
| G3 | không chấm "phải từ chối" | `cham_oracle` chỉ PASS/FAIL/UNGRADED/NO_RESULT; oracle `mot_luot` theo tên | kỳ vọng `served:<giá trị>` \| `refused`; từ chối đúng = không đáp số, không Scene3D; ghi riêng "đúng kết cục, khác lý do" |
| G4 | artifact không giữ Scene3D | `mot_luot` chỉ ghi `co_scene3d` + số vật | dựng lại cảnh OFFLINE từ hợp đồng + chương trình đã lưu (`_dung_scene3d`, 0 call) rồi kiểm cấu trúc + biến đổi renderer như `runs/regular-prisms/diagnostics/local_verification/` |
| G5 | khoá có thể lọt qua log `httpx` | §3 | tắt `httpx`/`httpcore` về WARNING như runner ảnh; quét artifact trước commit |

Hình dạng tối thiểu: MỘT runner mỏng kiểu `run_holdout_pilot.py` (nạp `measure_geometry_stability`, thay bộ đề + bộ chấm),
bộ đề pilot ghi trước ở thư mục run, và chứng nhận provider giả 0 call trước lượt thật. Không máy đo thứ hai.

## 5. Pilot đề xuất — 16 bài, `k = 1`, chỉ văn bản (nhãn và oracle đã có, không viết nhãn mới)

| # | hàng (nguồn) | họ | đề tóm tắt | kỳ vọng |
|---|---|---|---|---|
| 1 | X1 (`regular-prisms`) | T12 lục giác | cạnh 2, cao 3 | 18√3 |
| 2 | X4 | T12 lục giác | cạnh √3, cao 2 | 9√3 |
| 3 | X6 | T12 lục giác | "lăng trụ đứng … đáy là lục giác đều cạnh 2", cao 3 | 18√3 |
| 4 | T2 | T12 tam giác | cạnh 2, cạnh bên 3 | 3√3 |
| 5 | T5 | T12 tam giác | cạnh 2/3, cao 9 | √3 |
| 6 | H1 (`regular-hexagonal-pyramid`) | T11 | cạnh 2, cao 3 | 6√3 |
| 7 | H2 | T11 | cạnh 2, cạnh bên 4 | 12 |
| 8 | H8 | T11 | cạnh 1/2, cao 6 | 3√3/4 |
| 9 | P09 (`exact-dimensions`) | T8 chóp tam giác đều | cạnh 6, cạnh bên 5 | 3√39 |
| 10 | P06 | T8 tứ diện đều | cạnh 6 | 18√2 |
| 11 | NX1 | T12 biên | thiếu chiều cao | từ chối |
| 12 | NT2 | T12 biên | cao 3 ≠ cạnh bên 4 | từ chối |
| 13 | NT4 | T12 biên | lăng trụ xiên đáy tam giác đều | từ chối |
| 14 | NX7 | ngoài miền | lăng trụ ngũ giác đều | từ chối |
| 15 | N8 | T11 biên | phủ định "không phải là hình chóp lục giác đều" | từ chối |
| 16 | N02 | T8 biên | cạnh bên, chiều cao mâu thuẫn | từ chối |

Hàng nhãn phụ thuộc CHƯƠNG TRÌNH (NX3, NX4, NT3, N4, N5, P02/P03/P18, N11) bị loại: ở lượt thật mô hình tự chọn bố cục.
Giả thuyết cần pilot trả lời (không phải kết luận): lục giác đều cần một khung affine HỮU TỈ; nếu Gemini cố viết toạ độ
Euclid (√3 xấp xỉ thập phân) thì T11/T12 sẽ từ chối ⇒ từ chối sai — prompt chưa đổi (bề mặt mô hình không đổi).

## 6. Chỉ số — mỗi chỉ số báo tử / mẫu, không chỉ tỉ lệ

1. **Chương trình hợp lệ**: hợp đồng `analyze` + chương trình qua lược đồ/thẩm định tĩnh (kèm số lần thử sinh, 1–3).
2. **Đúng theo oracle** (10 bài dương): phục vụ và giá trị chính xác = nhãn.
3. **Scene3D đúng** (bài phục vụ): dựng lại offline — số đỉnh/mặt/cạnh, Euler, có `chart_metric`, biến đổi renderer ra
   đa giác đều đúng cạnh/cao.
4. **Từ chối**: đúng (6 biên bị từ chối, không đáp số, không cảnh) · sai (bài dương bị từ chối, kèm chặng/mã) ·
   **phục vụ sai** (biên được phục vụ, hoặc dương phục vụ sai giá trị) — mục tiêu an toàn = 0.
5. **Chi phí**: lượt logic, lần thử HTTP, retry, token theo stage (vào / ra / suy luận / cache), USD ước tính chặn trên.

## 7. Ngân sách dự kiến (căn cứ đo, không đoán)

Lượt sống gần nhất cùng đường văn bản (`thesis-final-20260908T160224Z`, 9 đề): 19 lượt logic, 0 retry, 97 869 token
(vào 49 481 + cache 1 859, ra 14 390, suy luận 33 998) ⇒ ~2,1 lượt và ~5,7k token vào + ~5,4k ra/suy luận mỗi đề.

| | dự kiến (16 đề) | trần đề xuất |
|---|---|---|
| lượt logic | ~34 | 64 (1 analyze + ≤3 sinh mỗi đề) |
| lần thử HTTP | ~34 | 96 |
| token | ~175 000 | 400 000 |
| USD (bảng giá 2026-08-25, chặn trên) | ~0,25 | ≤ 1,00 (400k token tính toàn bộ ở giá ra) |

Luật dừng: `BudgetExceeded`; hai lỗi provider không tạm thời liên tiếp; phát hiện khoá trong bất kỳ artifact/log nào.

## 8. Cần người dùng phê duyệt

1. Sửa công cụ G1–G5 (chỉ `backend/scripts/` + test; không đổi sản phẩm, candidate, cache) và chứng nhận provider giả 0 call.
2. Ngân sách live: `gemini-2.5-flash`, 16 đề × `k = 1`, trần 64 logic / 96 HTTP / 400k token (≈ ≤ 1 USD, giá phải tra lại).
3. Khai đo: `MEASUREMENT_CLASS = DEVELOPMENT_G05_REAL_MODEL_PILOT` · `HELD_OUT_CLAIM = NO` (corpus đã nhìn khi xây
   T8/T11/T12) · `EVALUATOR_INDEPENDENCE = PARTIAL` (nhãn + oracle ghi trước sửa sản phẩm, kiểm metric LOCAL độc lập;
   cùng nhóm tác giả) hoặc `OPERATOR_WAIVED`.
4. Bật `ALLOW_LIVE_AI=1` cho đúng một phiên; khoá giữ trong `backend/.env`.
5. Trong lượt pilot không sửa sản phẩm; kết quả xấu ⇒ wave mới có tiền đăng ký riêng.

Không tuyên bố từ báo cáo này: năng lực Gemini thật, giảm token, hay tỉ lệ nào của pilot chưa chạy.
