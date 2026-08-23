# REPOSITORY MAP — cái gì nằm ở đâu

Bản đồ **vị trí**, không phải tài liệu kiến trúc. Muốn biết hệ hoạt động ra sao
thì đọc `ARCHITECTURE_MAP.md`; muốn biết hiện đang ở đâu thì đọc
`CURRENT_STATE.md`. File này chỉ trả lời đúng một câu: *thứ này thuộc về ai.*

## Quy tắc một dòng

**Mỗi file có đúng một chủ.** Không có `misc/`, `temp/`, `old/`. Nếu không biết
đặt một file mới ở đâu, nó thuộc về một trong tám ô dưới đây — hoặc nó chưa được
định nghĩa rõ và đó là vấn đề cần giải trước khi tạo file.

| Đường dẫn | Chủ sở hữu | Nội dung |
|---|---|---|
| `backend/app/**` | **mã sản phẩm** (backend) | pipeline, DSL, semantic program, validator, persistence |
| `frontend/src/**` | **mã sản phẩm** (frontend) | store, module mô phỏng, renderer, component |
| `frontend/public/` | **asset runtime** | *chỉ* thứ trình duyệt production thật sự fetch. Hiện **rỗng** — và guard giữ nó đúng như vậy |
| `frontend/tests/fixtures/` | **fixture test frontend** | `semantic/` · `live-ai/` — envelope đã chụp, script đọc bằng `fs` |
| `backend/tests/fixtures/` | **fixture test backend** | envelope, holdout, fault, refusal, seal manifest |
| `docs/evaluation/**` | **bằng chứng nghiên cứu** | benchmark, provenance, ảnh chụp, báo cáo wave |
| `frontend/scripts/` · `backend/scripts/` | **tooling chạy được** | theo dependency thật, không theo chủ đề |
| `data/` | **cache sinh ra tại máy** | nguồn SGK + cache OCR. **Gitignore**, 357 MB, vắng mặt là ĐÚNG |

## Ba cái bẫy tên gọi

**`frontend/src/data/` KHÔNG phải `data/`.** Cái đầu là **mã sản phẩm** (catalog
offline, sample — chạy client-side, không đụng `/api`). Cái sau là cache cục bộ
bị gitignore. `.gitignore` phải neo `/data/` vào gốc chính vì chuyện này.

**`frontend/tests/` KHÔNG phải `backend/tests/`.** Chỉ cái sau nằm trong
`SOURCE_PATHS` của dấu vân tay bằng chứng (xem dưới).

**`docs/evaluation/` có ba tầng bằng chứng, đừng trích lẫn nhau** — tầng thấp
không được nói giọng tầng cao:

| Tầng | Ở đâu | Là gì |
|---|---|---|
| **CHÍNH THỨC** | `semantic-benchmark/results/`, `sealed/` | SEALED, custodian độc lập, seed ngoài. **Chỉ số ở đây mới trích được vào luận văn** |
| **PILOT** | `semantic-benchmark/pilot*`, `dev/` | nội bộ, không held-out |
| **KỸ THUẬT** | `tier2-live-pilot/`, `m1x/`, `semantic-vnext/`, các `*-audit/` | ảnh chụp, faultcheck, bằng chứng wave |

## `docs/evaluation/semantic-vnext/` — wave đang mở

```
reports/           báo cáo đọc được
browser-evidence/  ảnh trình duyệt thật + phép chiếu ngữ nghĩa từ DOM
e2e/               lượt chạy qua đường HTTP sản phẩm, MỖI LƯỢT MỘT THƯ MỤC
    run-<ISO>/     (tên theo mốc chạy — trước đây hai lượt trùng tên file)
```

## Ràng buộc phải biết trước khi di chuyển bất cứ thứ gì

`frontend/scripts/evidence.mjs` băm `git ls-files -s` của **bốn** đường dẫn:

```
frontend/src   frontend/scripts   backend/app   backend/tests
```

`git ls-files -s` in kèm **đường dẫn**, nên **đổi tên hay di chuyển một file
trong bốn thư mục đó làm đổi `sourceFingerprint`** — mọi artifact bằng chứng đã
commit lập tức thành `STALE_SOURCE`, kể cả khi nội dung không đổi một byte.

Hệ quả vận hành: sắp xếp lại `docs/evaluation/`, `frontend/tests/`,
`frontend/public/` thì **an toàn**; đổi chỗ script hay fixture backend thì **phải
sinh lại toàn bộ bằng chứng**. Đó là lý do đợt dọn dẹp này không đụng tới chúng.

## Bản sao có chủ đích — đừng "dọn"

| Artifact | Nguồn canonical | Bản sao | Vì sao giữ |
|---|---|---|---|
| `semantic_program.schema.json` | `backend/app/simulation/semantic_program/contract.py` (Pydantic) | `docs/schemas/` + `frontend/src/simulations/domains/generic/` | cả hai đều **sinh ra**, khoá byte-đối-byte bởi `test_schema_sync.py`. Bỏ bản nào cũng đỏ |
| ảnh bằng chứng trùng byte giữa các wave | — | nhiều `docs/evaluation/*/` | mỗi wave phải **tự chứa**. Gộp lại là biến lịch sử đánh giá thành mạng tham chiếu, một thư mục đổi chỗ là hỏng cả chuỗi |

Sinh lại artifact: `scripts/export_semantic_program_schema.py` ghi **hai** bản —
chạy thiếu là `test_schema_sync.py` đỏ.
