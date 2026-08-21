# Benchmark của route sinh ngữ nghĩa — DEV, SEALED, và danh tính bản được đo

## Hai hash, đọc kỹ kẻo hiểu nhầm

```
evaluation candidate source commit  = 9898d13
freeze / manifest commit            = 5506027
```

`EVALUATION_CANDIDATE.json` ghi `commit = 9898d13`, **không phải** `5506027`.
Đó là **đúng**, không phải trỏ nhầm:

- `9898d13` là trạng thái mã **được đem đo** — taxonomy, tập primitive, schema,
  prompt đều ở đúng bản này. Manifest được sinh **trên cây sạch** tại đó
  (`cay_lam_viec_sach: true`).
- `5506027` chỉ **chứa** manifest ấy cộng test khoá nó. Nó là cha–con trực tiếp
  của `9898d13` (`git rev-parse 5506027^` → `9898d13`), và **không đụng** một
  dòng nào của hệ được đo.

Nói cách khác: một hash trả lời *"đo bản nào"*, hash kia trả lời *"bản ghi nằm ở
đâu"*. Kiểm bất cứ lúc nào bằng:

```bash
cd backend && .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
```

## Ba tập dữ liệu, ba vai trò khác hẳn nhau

| | Ai soạn | Được nhìn? | Đổi được cái gì |
|---|---|---|---|
| **DEV** (20 case) | agent phát triển | có | **hệ** — IR, schema, prompt, taxonomy |
| **SEALED** (40 case) | **custodian độc lập** | **không**, tới Task 12 | **kết luận của luận văn** |
| **EVALUATION_CANDIDATE** | sinh từ nguồn | có | không đổi gì — nó là ảnh chụp danh tính |

Luật con dấu (spec §7.4), viết gọn:

> **DEV được phép làm thay đổi HỆ. SEALED chỉ được phép làm thay đổi KẾT LUẬN.**

## SEALED phải được chuẩn bị NGOÀI development context

Đây không phải hình thức. Nếu agent viết hệ đọc SEALED trước khi niêm phong thì
con dấu **đã vỡ ngay lúc ấy**: mọi lựa chọn sau đó — thêm một checker, nới một
miền kiểu, sửa một câu prompt — đều có thể bị dẫn dắt bởi thứ đã thấy, và không
ai chứng minh được là không.

Quy trình đúng:

```
CUSTODIAN ĐỘC LẬP
  40 case text
  → audit eligibility theo rubric §7.2
  → dựng ground truth ĐỘC LẬP
  → kiểm 4 metadata guard
  → seal + fingerprint
  → giao cho phía phát triển ĐÚNG hai thứ: đường dẫn + fingerprint

                 ↓ khi Task 12 bắt đầu

PHÍA PHÁT TRIỂN
  candidate đã đóng băng
  → mở SEALED ĐÚNG MỘT LẦN
  → chạy evaluation
  → TUYỆT ĐỐI không sửa hệ
  → báo A · B · D1 · D2
```

> Sau khi mở SEALED, case nào hỏng vì thiếu checker / thiếu primitive / IR không
> diễn đạt được thì **ghi đúng cái hỏng đó**. Không vá rồi chạy lại. Một lần vá
> là con dấu mất hiệu lực và phải niêm phong tập mới.

## Dạng dữ liệu SEALED

`docs/evaluation/semantic-benchmark/sealed/cases.json` — một object, khoá `cases`
là mảng:

```json
{
  "case_id": "sealed_001",
  "source": { "book": "tin-hoc-11-cs.pdf", "location": "trang 62, bài 3" },
  "problem_text": "…đề bài nguyên văn, tiếng Việt…",
  "eligibility_audit": {
    "discrete": true,
    "finite_input": true,
    "deterministic_bounded_procedure": true,
    "allowed_state_family": ["array", "int"],
    "allowed_operation_family": ["gán", "so sánh", "duyệt"],
    "in_scope": true
  },
  "metadata": {
    "no_specialized_module": true,
    "no_target_template": true,
    "not_prompt_example": true,
    "expressible_in_ir": true
  },
  "prescribed_procedure": null,
  "ground_truth": {
    "kind": "human | independent_solver | property_oracle",
    "provenance": "…dựng bằng gì, ai dựng…",
    "expected": {}
  },
  "expected_obligations": []
}
```

Hai điều bắt buộc:

- `ground_truth.kind` **không bao giờ** được là hệ đang bị kiểm. Lấy
  `SemanticProgramInterpreter` làm thước đo chính nó thì mọi con số thu được đều
  rỗng nghĩa.
- `expected_obligations` **chỉ điền nếu custodian tự xác lập trước khi seal**.
  Để hệ hiện tại sinh trường đó rồi dùng lại làm ground truth là tự chấm bằng
  chính đầu ra của mình — bỏ trống còn hơn.

`prescribed_procedure`: `null` khi đề **không ép** thủ tục. Có ép thì dùng giá
trị trong `SEMANTIC_PRESCRIBED_PROCEDURES`, và oracle sẽ so **canonical
mechanism events** chứ không so raw trace 1:1 (spec §5.5).

## Niêm phong

```bash
cd backend && .venv/Scripts/python.exe scripts/seal_benchmark.py
```

Lần đầu ghi `sealed/FINGERPRINT.txt`; các lần sau **kiểm** và thoát != 0 khi
lệch. `tests/semantic_program/test_benchmark_seal.py` chạy cùng suite mặc định:
hiện nó SKIP vì `sealed/cases.json` chưa tồn tại, và sẽ tự bật khi có.

## Ngân sách Task 12 — đã duyệt, không nâng sau khi thấy số

```
N = 40  ·  ≤ 4 lượt LLM logic/case  ·  trần logic 160  ·  trần HTTP 200
```

Bốn lượt là: `analyze` · `classify` · `semantic_analyze` · `semantic_program`.
Con số này sửa từ 3 lên 4 ngày 2026-08-21, **trước khi chạy case SEALED nào** —
lý do đầy đủ ở `freeze_protocol.md §2`.

Vượt trần ⇒ dừng và ghi `BUDGET_EXHAUSTED`. Trần HTTP rộng hơn trần logic **chỉ
để chịu lỗi tạm thời**, không phải để dò tìm kết quả tốt hơn.

D2 dùng đúng matched-subset rule đã khoá ở `freeze_protocol.md`: tối đa 12 case,
chọn tất định theo `case_id`, **không chọn lại sau khi biết kết quả**.
