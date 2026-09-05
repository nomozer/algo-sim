# CURVED_OBLIGATION_SURFACE_ALIGNMENT

> 2026-09-05. **`APPLICATION_LLM_CALLS = 0`** · `V3_REEXECUTED = NO` ·
> `V3_SOURCE_ARTIFACTS_CHANGED = NO` · `PRODUCT_CAPABILITY_CHANGED = NO`.
>
> Chạm `backend/app` ⇒ candidate `93c47d9a…` → **`e0e2a6bd…`**,
> `CACHE_VERSION` **79 → 80**.

## 1. ROOT_CAUSE

Một lệch **từ vựng**, không phải thiếu năng lực hình học.

`analyze` phát nghĩa vụ `area` cho *"diện tích mặt cầu"* — đúng theo cách SGK
nói. Nhưng `BANG_PHEP_DO["area"].kieu_of` là `polygon3|section|circle3`; mặt
cong là `lateral_area`. Cổng phủ hỏi `accepts_container_type("area",
"curved_solid")` → `False` → bác.

⇒ Ca cầu **đơn giản nhất** chết ở `structural_coverage` /
`requested_operation_uncovered`, dù dựng · tĩnh · xuất xứ đều qua và kernel
tính đúng `972π` · `324π`.

Đây là khoảng trống mà `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` §10① đã định
vị: nó **chắn trước** mọi thứ hai wave trước vừa mở.

## 2. Tương đương toán học, và giới hạn của nó

Với **khối cầu** — và chỉ khối cầu — hai câu là một số:

```
diện tích mặt cầu        = 4πR²
diện tích mặt cong của S = 4πR²
```

Vì mặt cầu **không có đáy**: toàn bộ bề mặt chính là mặt cong.

Với trụ và nón thì `S_tp = S_xq + S_đáy` — hai số khác nhau, và gộp chúng là
nói dối về hình học. Nên `area` và `lateral_area` ở đó **vẫn là hai nghĩa**.

## 3. Thẩm quyền

**Một cột của bảng họ**, không phải một danh sách song song:

```python
KhoiCong.nghia_vu_area_la          # app/simulation/geometry/curved.py
  ball     → "lateral_area"
  cylinder → None
  cone     → None
```

**Một helper dẫn xuất**, đặt cạnh thẩm quyền từ vựng nghĩa vụ:

```python
measure_contract.nghia_vu_chinh_tac(nghia_vu, kieu_chu_the, ho_cong) -> str
```

| đầu vào | ra |
|---|---|
| `(area, curved_solid, ball)` | **`lateral_area`** |
| `(area, curved_solid, cylinder)` | `area` |
| `(area, curved_solid, cone)` | `area` |
| `(area, polygon3 / section / circle3, —)` | `area` |
| `(volume / radius / lateral_area, curved_solid, ball)` | *không đổi* |

`NEW_AUTHORITIES = 0` (mở rộng `KHOI_CONG` thêm **một cột**) ·
`NEW_IR_OPERATIONS = 0`.

## 4. Hợp đồng an toàn

**① Theo HỌ, không theo `MemoryType`.** Cầu, trụ và nón dùng chung
`curved_solid`; quyết định bằng kiểu bộ nhớ một mình sẽ kéo cả trụ lẫn nón vào
theo. Coverage lấy họ từ chính câu lệnh dựng (`construct_curved_solid.
curved_kind`); postconditions lấy từ `CurvedSolid.kind` trong snapshot.

**② Quy đổi từng nghĩa vụ ĐỘC LẬP.** Một hợp đồng có `volume(S)` + `area(S)` +
`radius(S)` trên cùng quả cầu chỉ đổi `area`; hai nghĩa vụ anh em giữ nguyên
(`test_E4`).

**③ Tầng NGHĨA VỤ, không phải tầng toán hạng.** `BANG_PHEP_DO["area"].kieu_of`
**vẫn không** nhận `curved_solid`, nên `measure(quantity="area", of=<khối>)`
vẫn bị hợp đồng tĩnh chặn y như trước (`test_G10`). Chương trình vẫn phát
`measure(quantity="lateral_area", of="S")`.

**④ Không đọc chữ trong đề.** Helper nhận `(nghia_vu, kieu, ho)` — không có
`problem_text`. Nhận diện cầu bằng từ khoá là rửa năng lực; `test_G8` quét AST
để cấm.

## 5. Parity coverage ↔ postconditions

Bất biến: **hai consumer phải gọi cùng một helper.** Nếu cổng phủ dùng bản quy
đổi còn checker dùng `ob.kind` thô (hoặc ngược lại), hai cổng sẽ nói hai điều
khác nhau về cùng một nghĩa vụ — một bên cho qua, một bên không tìm ra checker.

`test_F_hai_consumer_cung_goi_MOT_helper` quét AST của `coverage_gate.py` và
**`postconditions.py`** — nơi *chọn* checker, chứ không phải
`geometry_obligations.py` nơi chỉ *định nghĩa* checker.
`test_F_parity_tren_ca_THAT` kiểm trên ca thật: qua cổng phủ **và** qua hậu
điều kiện.

## 6. `c1a` — replay tất định

Contract hậu-V3 (`volume(S)` + `area(S)`), chương trình dùng pose canonical:

```
construction   PASS
grounding      PASS
coverage       PASS        ← trước wave này: FAIL
runtime        PASS
volume         972π
area           324π        ← qua `lateral_area`
postconditions PASS
servable       True
```

## 7. Controls và tiêm lỗi

| control | kết quả |
|---|---|
| ball `area` + witness `lateral_area` | **PASS** |
| ball `lateral_area` + witness `lateral_area` | PASS |
| cylinder `area` | **FAIL** (`requested_operation_uncovered`) |
| cone `area` | **FAIL** |
| cylinder / cone `lateral_area` | PASS |
| polygon3 / section / circle3 `area` | giữ `area` |
| `area` trên `point3` | vẫn bị chặn |
| container không có producer | vẫn bị chặn |

| # | tiêm | test đỏ |
|---|---|---|
| ① | bỏ equivalence của ball | `test_B` · `test_E1` · `test_E3_ball_*` |
| ②③ | ánh xạ cylinder/cone `area` → `lateral_area` | `test_E3_tru_va_non_area_obligation_VAN_bi_chan` |
| ④ | quyết định chỉ bằng `MemoryType` | `test_G4` — quy đổi phải cho **2** giá trị khác nhau trên 3 họ |
| ⑤⑥ | một consumer dùng kind gốc | `test_F_*` (quét AST + ca thật) |
| ⑦ | quy đổi cả sibling | `test_E4` |
| ⑧ | đọc từ khoá trong đề | `test_G8` (quét AST) |
| ⑨ | alias sai họ / sai kiểu | `test_E5_*` |
| ⑩ | mở `measure.area` cho curved_solid | `test_G10` |

**Nền ĐỎ trước sửa: 21 failed / 9 passed.** Chín xanh sẵn là control — chúng
khẳng định thứ đã đúng (trụ/nón bị chặn, `lateral_area` chạy được, binding, IR
surface). Nếu chúng cũng đỏ thì bộ test đang đo sai chỗ.

## 8. Model-facing và identity

```
ANALYZE_SCHEMA_CHANGED            NO   515001b503af5c7c…
SYNTHESIS_SCHEMA_CHANGED          NO   8c57c9de49824d61…
GRAMMAR_CARD_CHANGED              NO   e0fbbc8456da57ae…
PROMPT_CHANGED                    NO   55ac1ca6a6df92ce…
STABLE_CAPABILITY_HASH            85bd316781b86576… → 85bd316781b86576…   KHÔNG đổi
SEMANTIC_ENVIRONMENT_HASH         f7def6207f5741d9… → f7def6207f5741d9…   KHÔNG đổi

COVERAGE_BEHAVIOR_CHANGED         YES
CHECKER_BEHAVIOR_CHANGED          YES
CACHE_VERSION                     79 → 80
CANDIDATE_HASH                    93c47d9a4ff9ffd2… → e0e2a6bd… (đo ở §10)
```

Bề mặt mô hình **không đổi một byte** — mô hình vẫn phát
`measure(quantity="lateral_area")` như trước. Thứ đổi là cách **hệ đọc nghĩa vụ
của đề**.

### ⚠️ Kiểm cache cho kết quả NGƯỢC với dự đoán thường gặp

Đề bài nêu *"cached envelope có thể đổi từ rejected sang served"*. Đã kiểm, và
tiền đề ấy **không đúng với kho này**: `main.py:691` chỉ cache khi
`status == "ok"`, kèm chú thích *"KHÔNG cache unsupported để tránh kẹt kết quả
cũ khi năng lực được cải thiện (chống stale)"*. Bản **từ chối chưa bao giờ được
cache**, nên **không envelope nào hoá sai**.

Bump vẫn thực hiện, nhưng theo **luật** chứ không phải để dọn rác: policy định
tuyến đổi — cổng phủ nay nhận một nghĩa vụ nó từng bác (`CLAUDE.md §3`). Ghi lý
do vào cả ba chỗ để lần sau không ai phải suy lại phân tích này.

Bump là **bốn chỗ trong một commit**: `app/main.py` · assert ở
`tests/test_api.py` · bảng danh tính `docs/CURRENT_STATE.md` ·
`tests/semantic_program/test_evaluation_candidate.py` (dẫn từ nguồn), cộng
`lock_cache_identity.py`.

## 9. V3 — trạng thái lịch sử

```
V3_POOL_HASH             36c2153ecefd2dbf…   không đổi
V3_CASE_SET_HASH         eb1c402a71517553…   không đổi
V3_SEED                  5324284654432805119 không đổi
V3_SOURCE_ARTIFACTS      4/4 byte-identical
V3_REEXECUTED            NO
```

Lượt V3 vẫn là bằng chứng của **candidate cũ** `a696200e…`; wave này không chạy
lại gì. Nhưng nó đã trả lời một câu mà báo cáo V3 để mở: `c1a` — ca duy nhất
được kiểm — nay **đi trọn** trên candidate mới. Đó là bằng chứng về **năng lực
hệ**, không phải về `MODEL_DISCOVERABLE`: câu ấy cần một lượt live trên pool mới.

## 10. Gates

| | |
|---|---|
| `tests/geometry/test_curved_obligation_surface.py` (MỚI) | **30 passed** |
| full backend pytest | **3652 passed** · 1 skipped · 1 deselected, exit 0 (cây sạch) |
| `replay_demo_cases.py` | **5/5** · reduced-chain 1/1 |
| `audit_demo_crash_surface.py` | biên **6/6** · ném ra ngoài **0** |
| `certify_acceptance_runner.py` | exit 0 · 4 nhãn PASS · 2 readiness YES |
| candidate verification | exit **0** |
| cache identity | **15 passed** |
| frontend vitest | exit 0 (không file frontend nào đổi) |
| `git diff --check` | exit **0** |

## 11. Giới hạn

**① Chỉ khối cầu.** Trụ và nón vẫn không có nghĩa vụ `area`. Nếu SGK hỏi *"diện
tích toàn phần hình nón"* thì hệ vẫn từ chối — đúng, vì `S_tp` của nón có hai
căn thức khác nhau và miền số **cố ý** từ chối tổng ấy (`dien_tich_mat_cong`
docstring). Đó là giới hạn đã khai, không phải thiếu sót mới.

**② `MODEL_DISCOVERABLE` chưa đo.** Wave này chứng minh đường **đi được**; nó
không chứng minh mô hình sẽ phát đúng cặp (nghĩa vụ `area`, witness
`lateral_area`). Chỉ một lượt live trả lời được.

**③ Khoảng trống khác giữ nguyên trạng thái**: `distance` witness của `c7a` ·
`radius` của `circle3` sinh từ thiết diện · product promotion · V4.

**④ Postconditions nhận diện họ bằng `snap.get(container)`** — nếu container
chưa được dựng thì không có họ, và nghĩa vụ giữ kind gốc. Đúng: một vật chưa
dựng thì cổng phủ đã chặn trước rồi.

## 12. RECOMMENDED_NEXT_ACTION

```
CURVED_DISTANCE_WITNESS_VERIFICATION
```

Lỗ chứng thực `distance` trên `curved_solid` — thứ làm `c7a` **đúng cả ba đáp
số mà vẫn không servable** (`V3_PRODUCT_PATH_PARITY_CORRECTION`). Nó là lỗi HỆ
đang mở duy nhất còn chặn một ca đã chứng minh được là đúng.
