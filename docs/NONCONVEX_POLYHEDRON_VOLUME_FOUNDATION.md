# NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION

> 2026-09-07 · `APPLICATION_LLM_CALLS = 0` · `NEW_PER_PROBLEM_MODULES = 0`
> `NEW_IR_OPERATIONS = 0` · `NEW_MEMORY_TYPES = 0`
>
> ```
> SYSTEM_EXPRESSIBLE        = YES   (construct_solid đã có, không thêm phép nào)
> DETERMINISTICALLY_CORRECT = YES   (3 oracle độc lập · 20, không phải 28)
> MODEL_DISCOVERABLE        = NOT_MEASURED   (0 lượt gọi model theo chỉ thị)
> STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
>
> MODEL_FACING_CONTRACT_CHANGED = NO   (sáu băm đứng yên TỪNG BYTE)
> CACHE_VERSION 91 → 92                (lần bump đầu tiên KHÔNG vì bề mặt mô hình)
> nonconvex_polyhedron: (không có dòng) → foundation_only
> ```
>
> Wave này bắt đầu bằng một câu hỏi về **năng lực** và kết thúc bằng một phát
> hiện về **tính đúng**: hệ không hề từ chối khối lõm — nó **phục vụ** khối lõm
> với một con số sai, và sai im lặng.

## 1. Bệnh: một thẩm quyền duy nhất bảo vệ NHẤT QUÁN, không bảo vệ ĐÚNG

`volume_polyhedron` là nguồn sự thật duy nhất, dùng chung bởi `measure` (phép
đo của IR) và `check_volume` (cổng C₂). Kho này đã đi dọn ba lần để có được
điều đó, và nó đúng — nhưng nó chỉ đảm bảo runtime và checker **nói cùng một
câu**. Nếu câu ấy sai thì cả hai cùng sai, và không cổng nào thấy.

Bản cũ cộng `volume_tetrahedron`, tức lấy `abs` cho **từng** tứ diện, kèm một
chú thích khoe rằng nhờ vậy *"bảng `faces` viết thuận hay nghịch kim đồng hồ
đều ra cùng số"*. Với khối LỒI câu ấy đúng và vô hại. Với khối LÕM nó là lỗi:
phần lõm phải đóng góp **âm** để trừ đi, `abs` biến nó thành cộng.

Ca chuẩn của wave — chóp đáy ngũ giác lõm:

```
A(0,0,0)  B(4,0,0)  C(4,4,0)  D(2,1,0)  E(0,4,0)     S(2, ½, 6)
```

| Nguồn | Thể tích |
|---|---|
| shoelace đáy × h/3 (tay) | **20** |
| chia đáy thành `ABC` + `ACE` − `CDE` (tay) | **20** |
| oracle custodian, thuật toán KHÁC kernel | **20** |
| **`volume_polyhedron` bản cũ** | **28** ❌ |

Và `28` không dừng ở kernel. Đo ở mức route
(`test_nonconvex_polyhedron_volume.py::test_30_TIEM_7`):

```
servable = True   ·   envelope.status = "ok"   ·   V = 28
```

## 2. Chữa: tổng có dấu trên mặt biên, `abs` ĐÚNG MỘT LẦN ở cuối

```
V = | 1/6 · Σ_mặt Σ_i det(p₀ − g, pᵢ − g, pᵢ₊₁ − g) |
```

Thẩm quyền mới: `geometry/section.py::the_tich_da_dien`. `geometry_exec.
volume_polyhedron` uỷ quyền cho nó — **vẫn một thẩm quyền**, không đẻ cái thứ
hai.

`g` là đỉnh 0; chọn điểm nào cũng ra cùng kết quả vì tổng có dấu trên một mặt
biên KÍN bất biến với phép tịnh tiến gốc.

### 2b. Tự định hướng lại, thay vì đòi mô hình khai đúng chiều

Một phép tính **có dấu** cần các mặt định hướng nhất quán. Hợp đồng hiện hành
**không** đòi điều đó, và đó không phải sơ suất — `abs` từng tứ diện làm cho
chiều khai trở nên vô nghĩa. Đo được: tứ diện, hình hộp và chóp đáy vuông
trong test hiện tại **đều KHÔNG** định hướng nhất quán.

Nên đòi mô hình khai đúng chiều sẽ làm sai **mọi** chương trình đang chạy, và
sai theo hướng tệ nhất: số nhỏ đi, im lặng. `dinh_huong_bien` định hướng lại
bằng BFS trên đồ thị kề mặt — tất định, chỉ cần biên kín, không cần một byte
nào từ mô hình. **Hợp đồng khai mặt không đổi một byte.**

## 3. Fail-closed: năm mã lỗi MỚI, ba tổ hợp + hai hình học

| Mã | Điều kiện | Tầng |
|---|---|---|
| `POLYHEDRON_BOUNDARY_OPEN` | có cạnh không thuộc đúng hai mặt · hoặc các mặt không liên thông (hai vỏ rời) | tổ hợp |
| `POLYHEDRON_NON_ORIENTABLE` | biên kín nhưng không ghép thành một vỏ có trong/ngoài | tổ hợp |
| `POLYHEDRON_DEGENERATE` | thể tích bằng 0 — mọi đỉnh đồng phẳng | tổ hợp |
| `POLYHEDRON_FACE_NOT_PLANAR` | một MẶT không nằm trọn trong một mặt phẳng | hình học |
| `POLYHEDRON_FACE_NOT_SIMPLE` | biên của một MẶT tự cắt chính nó · hoặc lặp đỉnh · hoặc gập ngược | hình học |

Hai mã cuối thêm **giữa wave**, sau một lần đo hụt — xem §7.

⚠️ **Vẫn KHÔNG kiểm được, và phải nói ra**: hai MẶT KHÁC NHAU xuyên qua nhau
trong không gian. Đó là điều kiện toàn cục; năm mã trên soát bảng mặt và soát
**từng mặt một**. Bao đóng v1 vì thế khai theo đường DỰNG.

## 4. Nửa kia: renderer từng LẤP phần lõm

Sửa thể tích mà để renderer lấp phần lõm là chữa nửa bệnh — con số đúng, thứ
học sinh **nhìn thấy** vẫn sai.

Đo được: `scene3d-view.tsx` dùng **quạt tam giác** ở CẢ HAI nhánh dựng mặt
(`render === "mesh"` và `type === "face"`). Quạt chỉ đúng với mặt LỒI.

Thay bằng `polygon-triangulate.ts` — cắt tai trên một hệ trục 2D cục bộ. Nó
**không phải một thẩm quyền hình học thứ hai**: thứ tự đỉnh quanh mặt do kernel
quyết, module chỉ **nối** chúng lại, và mọi tam giác trả về là ba **chỉ số** vào
chính mảng đầu vào — không toạ độ nào do frontend sinh ra.

Đo trên buffer THẬT mà `buildObject3D` phát ra:

```
RENDERED_PROJECTED_AREA      = 10      (đúng bằng diện tích đáy)
NOTCH_REMAINS_EMPTY          = YES     (không tam giác nào chứa (2, 5/3))
TRIANGLE_OVERLAP_OUTSIDE_FACE = 0      (mọi trọng tâm nằm TRONG đáy)
```

Phép tiêm ⑤ — trả `scene3d-view.tsx` về quạt: **3 ô đỏ**, đáy phủ **22** thay
vì 10.

> ⚠️ **Hai con số, cùng một lỗi.** `polygon-triangulate.test.ts` ghi quạt phủ
> **14**; `scene3d.test.tsx` ghi **22**. Cả hai đúng: `14` là quạt từ `A`
> (thứ tự mảng của module), `22` là quạt từ `E` — mặt đáy của khối khai theo
> chiều `(4,3,2,1,0)` nên gốc quạt là `E`. Ghi cả hai để lần sau không ai
> tưởng một trong hai là số sai.

Fail-closed ở đây cũng có: `chiaTamGiac` trả `[]` cho đa giác suy biến hoặc tự
cắt — người gọi không vẽ gì, thay vì vẽ một thứ vô nghĩa.

## 5. Gold đi trọn chuỗi (§10) — `NEW_IR_OPERATIONS = 0` đo được ở đây

Bảng mặt là **cấu trúc tổ hợp**, và một ngũ giác lõm không cần từ vựng nào mà
một ngũ giác lồi không cần. Gold dùng đúng `construct_solid` đã có.

```
SYSTEM_EXPRESSIBLE = YES   servable = True · V = 20 · weak_kinds = []
TRACE_PASS         = YES   0 init · 1 construct_solid(chop) · 2 assign(V)
                           "Dựng khối S.ABCDE từ 6 đỉnh và 6 mặt."
DEPENDENCY_PASS    = YES   V → [chop] · chop → [A,B,C,D,E,S]
SCENE3D_PASS       = YES   6 đỉnh · đáy giữ NGUYÊN 5 chỉ số theo thứ tự vòng
                           quanh · đúng MỘT đỉnh phản xạ (1 dương / 4 âm)
```

`weak_kinds = []` là ô quan trọng: `servable` chỉ có nghĩa nếu checker thể tích
**thật sự chạy** trên ca này. Nghĩa vụ ở mức yếu thì `servable` là lời hứa suông.

## 6. Bề mặt mô hình (§14) — đo trước/sau bằng worktree tại HEAD

| Thành phần | Trước | Sau |
|---|---|---|
| `prompts` | `55ac1ca6a6df92ce` | `55ac1ca6a6df92ce` |
| `grammar_card` | `cc105e4f1da84d23` | `cc105e4f1da84d23` |
| `synthesis_schema` | `6ccef3230c003d61` | `6ccef3230c003d61` |
| `analyze_schema` | `515001b503af5c7c` | `515001b503af5c7c` |
| `capability` | `72edf39f6c10220d` | `72edf39f6c10220d` |
| `semantic_environment` | `a483ced9fd7546df` | `a483ced9fd7546df` |

`MODEL_FACING_CONTRACT_CHANGED = NO`. Bất biến nguồn và grounding **không bị
đụng**: `git diff -- backend/app` khớp 0 lần với `_NGUON_CUA_PHEP_DUNG`,
`grounding`, `SourceInvariant`, `_MANH_MOI_NGHIA_VU`, `BANG_PHEP_DO`,
`_TOAN_HANG_LENH`, `_CHU_KY`, `_KIEU_DUNG`.

## 7. Cache (§15): bump 92 — **lần đầu tiên KHÔNG vì "đầu vào của mô hình đổi"**

Mọi bump từ 68 tới 91 đều vì bề mặt mô hình đổi. Lần này bề mặt đứng yên từng
byte (§6). Lý do là chiều nặng hơn:

| Chiều | Có? | Bằng chứng |
|---|:---:|---|
| phục vụ số **SAI** → phục vụ số **ĐÚNG** | ✅ | `test_30_TIEM_7`: bản cũ trả `status="ok"`, `V = 28` |
| **served → rejected** | ✅ | mặt tự cắt từng được phục vụ với `V = 4` |
| rejected → served | — | (chiều duy nhất của bump 87/88/90/91) |

`main.py` cache **cả** `envelope_json`, nên một row sinh trước bản vá đọc to
`28` dưới cùng `CACHE_VERSION` và không cổng nào chặn nó. Row cũ **PHẢI** miss.

Bốn cổng bump trả đủ trong một commit, cộng `cache_identity.lock.json` sinh lại.
**Cổng thứ năm không có trong `CLAUDE.md §3`, phát hiện khi chạy**: hai test
ghim danh tính của lượt đo live cũ (`test_oblique_ellipse_final_rerun.py`,
`test_oblique_ellipse_e2e_rerun_preflight.py`). Sửa **test**, KHÔNG sửa
artifact — và sửa theo hướng tách bạch: artifact giữ `91` (số đo đông cứng),
hệ ở `92`, còn thứ test thật sự bảo vệ — **năm băm model-facing** — vẫn được
ghim y nguyên. Ghim hai `cache_version` bằng nhau sẽ biến mọi bump ở tầng kernel
thành một lượt đo mất giá trị, mà nó không hề mất.

## 8. Đính chính trong chính wave này

Kho này coi đính chính là việc bình thường; luật là **giữ nguyên số gốc, viết
đính chính bên trên**. Wave này có ba, và cả ba đều là *tôi tự bác mình*:

**(a) `TIEM_2` — hộp hở mà vẫn ra số đúng.** Ô này định khẳng định "bỏ phép
kiểm biên kín thì hộp hở lọt qua với số sai". Đo: bỏ mặt cuối `3-0-4-7` cho ra
**30**, đúng bằng hộp kín. Nguyên nhân: mặt bị bỏ **chứa đỉnh 0** — gốc quạt —
nên mọi tứ diện của nó suy biến và đóng góp 0. Đổi sang bỏ mặt `4-5-6-7` →
**20 ≠ 30**.

**(b) `TIEM_3` — phép đo BÁC chính tuyên bố của tôi.** Ô này định khẳng định
"bỏ định hướng lại thì khối lồi ra sai". Đo: **cả bốn** fixture vẫn ra đúng dù
đếm cạnh có hướng gọi chúng là "không nhất quán". Phải đo từng mặt: lật mặt 0,
1, 5 (chứa đỉnh 0) → 20 **không đổi**; mặt 2 → 12; mặt 3 → **28**; mặt 4 → 4.
Dùng mặt 3. Cùng cái bẫy "mặt chứa gốc quạt đóng góp 0" đã đánh trúng hai lần.

**(c) "Đáy tự cắt mà hệ vẫn phục vụ 24" — SAI TIỀN ĐỀ.** Lượt đầu tôi ghi chu
trình `A→B→D→C→E` là đáy tự cắt và định coi `V = 24` là một lỗ. Đo lại:
chu trình ấy **không** tự cắt — nó là một ngũ giác lõm **khác**, shoelace `12`,
nên `24` là đáp số **đúng** cho hình ấy. Hệ không sai chỗ nào.

Bow-tie thật là `A→C→B→D→E` (cạnh `A-C` cắt cạnh `D-E` tại `(8/5, 8/5)`), và
**ở đó lỗ là thật**: biên vẫn kín, vẫn định hướng được, ba điều kiện tổ hợp cho
nó đi qua, hệ phục vụ `V = 4`. Hai mã `FACE_NOT_SIMPLE` / `FACE_NOT_PLANAR`
sinh ra từ lần đo lại này — tức **một tiền đề sai vẫn dẫn tới một bản vá
đúng, nhưng chỉ sau khi chịu đo lại**.

Ô `test_24` giữ lại cả hai chu trình lõm để khoá một điều thật: hai bảng mặt
khác nhau trên cùng sáu điểm phải cho hai khối khác nhau (20 và 24). Nếu cả hai
cùng ra 20 thì `faces` đang bị bỏ qua.

## 9. Test và nền đỏ

```
tests/geometry/test_nonconvex_polyhedron_volume.py   34 hàm → 39 ca (parametrize)
  §5   ba oracle độc lập                              1
  §12  ca bắt buộc (lõm · shift · đảo · tịnh tiến · scale · hồi quy lồi)  6 → 11
  §7   topology fail-closed                           6
  §12.13 runtime ↔ checker                            2
  §13  tiêm lỗi kernel                                4
  §10  gold + hình dạng fail-closed + tiêm ⑥⑦        15
frontend  polygon-triangulate.test.ts                15 pass
          scene3d.test.tsx khối (5D-lõm)              5 pass
```

**Bảy phép tiêm, cả bảy ĐO ĐƯỢC là lật đúng ô nó nhắm:**

| # | Tiêm | Kết quả đo |
|---|---|---|
| ① | `abs` từng tứ diện | `20 → 28` |
| ② | bỏ kiểm biên kín (bỏ mặt `4-5-6-7`) | `30 → 20`, lọt qua |
| ③ | bỏ định hướng lại + lật mặt 3 | `20 → 28` |
| ④ | đảo hướng **từng** mặt, cả 6 | BFS lật về, `20` mọi lần |
| ⑤ | trả renderer về quạt tam giác | 3 ô đỏ, đáy phủ `22` |
| ⑥ | bỏ `kiem_mat_phang_don` | bow-tie được phục vụ, `V = 4` |
| ⑦ | bản cũ ở mức **route** | `envelope.status = "ok"`, `V = 28` |

Ngoài ra `test_oracle_independence.py` phải đổi điểm tiêm: bản vá
`volume_pyramid_fan` gỡ mất lời gọi `volume_tetrahedron` nên phép tiêm cũ hoá
**cùn** (kernel khớp oracle, `!=` xanh giả). Chuyển sang tiêm `M.det3`, sau khi
kiểm module oracle chỉ nhập `fractions`/`typing` — nó vẫn độc lập.

## 10. Năng lực (§16)

```
nonconvex_polyhedron : (bảng KHÔNG có dòng nào) → foundation_only
```

Im lặng trước đó đọc như *"chưa nghĩ tới"*, trong khi sự thật tệ hơn: hệ
**phục vụ** khối lõm với số sai. Một dòng `unsupported` cũng đã tốt hơn im lặng.

`foundation_only`, **không** `supported` — cùng luật đang áp cho
ball/cylinder/cone: hệ diễn đạt và tính đúng, nhưng **chưa ai đo** mô hình có
tự viết nổi bảng mặt của một đáy lõm từ đề hay không. `MODEL_DISCOVERABLE` để
`NOT_MEASURED` vì chỉ thị wave ghi `APPLICATION_LLM_CALLS = 0`.

**Tên phạm vi đã chứng minh** — hẹp, và nói thẳng:

> khối đa diện có **biên KÍN, một vỏ**, và **mọi MẶT phẳng + đơn**.

Không phải *"mọi đa diện không lồi"*. Hai mặt khác nhau xuyên qua nhau vẫn nằm
ngoài bao đóng v1.

## 11. Cổng (§17)

```
pytest            4477 collected · 4476 chạy · 4476 pass  (cây sạch)
vitest            52 file · 717 pass
npm run build     ✔ tsc -b + vite build
replay_demo       DEMO_REPLAY_PASS 5/5 · REDUCED_CHAIN 1/1
crash_surface     BIÊN ĐÚNG KỲ VỌNG 6/6 · NÉM RA NGOÀI 0
cache identity    lock sinh lại, CACHE_VERSION 92
freeze --verify   xanh sau commit đóng băng lại
git diff --check  sạch
```

`RECOMMENDED_NEXT_ACTION` — xem `docs/CURRENT_STATE.md`.
