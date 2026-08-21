# Bàn giao cho custodian — chuẩn bị và niêm phong SEALED 40

> Tài liệu này viết cho **người giữ tập đánh giá**, không phải cho agent. Nếu
> bạn đang đọc nó với tư cách người chuẩn bị 40 đề: bạn là mắt xích duy nhất
> đứng ngoài hệ, và giá trị của toàn bộ phần đánh giá nằm ở chỗ bạn đứng ngoài.

## Vì sao phải là bạn, không phải phía phát triển

Phía phát triển đã đóng: hệ được đóng băng tại commit `36bae92`, và từ mốc đó
không ai được sửa prompt, schema, taxonomy, primitive, route, checker, runner
hay ngân sách nữa.

Nếu người viết hệ nhìn thấy 40 đề trước khi niêm phong thì con dấu **vỡ ngay
lúc ấy**. Không phải vì họ gian, mà vì sau đó mọi lựa chọn — thêm một checker,
nới một miền kiểu, sửa một câu prompt — đều có thể đã bị dẫn dắt bởi thứ họ
thấy, và **không ai chứng minh được là không**. Một benchmark chỉ có giá trị
đúng bằng mức nó không thể bị nắn.

Bạn giao lại **đúng hai thứ**: đường dẫn tới file đã niêm phong, và fingerprint.
Không gửi nội dung đề, không gửi đáp án, không trao đổi trước về "đề này chắc
hệ làm được không".

## Sáu bước

```
1. Chọn 40 đề          →  2. Audit phạm vi     →  3. Dựng ground truth
                                                        ↓
6. Giao đường dẫn      ←  5. Niêm phong        ←  4. Kiểm hình dạng
   + fingerprint
```

### 1. Chọn 40 đề

Từ nguồn thật (sách giáo khoa, đề kiểm tra, tài liệu ôn tập). Ghi lại `source`
đủ để người khác tra lại được: tên sách + vị trí.

Ba điều kiện **held-out**, mỗi đề phải thoả cả ba. Cả ba đều nói về **nhiễm dữ
liệu** — bài đã được hệ phục vụ sẵn, hoặc đã lọt vào prompt:

| guard | nghĩa |
|---|---|
| `no_specialized_module` | hệ **chưa có** module chuyên biệt cho dạng bài này |
| `no_target_template` | không có template/target catalog nào khớp sẵn |
| `not_prompt_example` | đề **không** xuất hiện trong bất kỳ prompt nào của hệ |

Thiếu **một** guard là đề ấy làm hỏng tính held-out của **cả tập**, không chỉ
của chính nó.

> **KHÔNG có guard nào về năng lực của hệ, và đó là cố ý.** Đừng loại một đề vì
> nghĩ "cái này chắc hệ chưa làm được". Bài **thoả rubric mà IR hiện tại không
> diễn đạt được** phải **ở lại trong tập** và trở thành `capability_gap` — đó là
> một **phát hiện phải báo cáo**, không phải sự cố cần tránh.
>
> Lọc những bài ấy ra chính là tự chọn một population có lợi cho hệ, và con số
> "tỉ lệ sinh được" thu về sẽ cao lên một cách giả tạo. Trường
> `expressible_in_ir` nếu bạn muốn ghi thì chỉ là **ghi chú mô tả**: `false`
> hoàn toàn hợp lệ, và bộ kiểm hình dạng sẽ chỉ nhắc lại rằng case đó ở lại.

### 2. Audit phạm vi

Đây là phán quyết của **người**, máy không làm thay được. Với mỗi đề, trả lời và
ghi vào `eligibility_audit`:

- `discrete` — dữ liệu rời rạc, không liên tục?
- `finite_input` — đầu vào hữu hạn và biết trước?
- `deterministic_bounded_procedure` — có thủ tục tất định, số bước có biên?
- `in_scope` — kết luận cuối: đề này thuộc phạm vi đo?

`in_scope: false` thì **bỏ đề đó ra**, đừng để trong tập rồi trông chờ hệ từ
chối — như thế là đo lời từ chối chứ không đo năng lực sinh.

**Ranh giới phải phân biệt cho đúng**, vì hai thứ này dễ lẫn:

| tình huống | làm gì |
|---|---|
| Không thoả rubric (liên tục, vô hạn, không có thủ tục tất định…) | **ngoài population** — bỏ ra |
| Thoả rubric **nhưng IR hiện tại chịu thua** | **giữ lại** — kết quả `capability_gap`, và đó là số liệu thật |

Câu hỏi ở bước này là *"đề này có thuộc lớp bài mà luận văn nhận đo không"*,
**không** phải *"hệ có làm được không"*. Câu thứ hai là thứ benchmark sinh ra để
trả lời — hỏi trước nó là tự trả lời hộ.

### 3. Dựng ground truth ĐỘC LẬP

**Điều kiện tuyệt đối: đáp án không được đến từ hệ đang bị đo.** Lấy
`SemanticProgramInterpreter` làm thước đo chính nó thì mọi con số thu được đều
rỗng nghĩa. Giải tay, dùng một công cụ khác, hoặc dùng đáp án in sẵn trong sách
— ghi rõ bằng cách nào vào `provenance`.

**Bạn KHÔNG cần biết hệ đặt tên biến là gì.** Đây là điều quan trọng nhất trong
cả tài liệu này. Tên biến do LLM tự đặt; bắt bạn đoán nó là bắt đoán sai. Một
chương trình hoàn toàn đúng gọi biến `ket_qua` trong khi bạn ghi `max_value` sẽ
bị chấm **sai oan**, và cái sai oan ấy đi thẳng vào con số chính của luận văn.

Nên bạn khai **nghĩa vụ + giá trị đúng**:

```json
"ground_truth": {
  "kind": "human",
  "provenance": "giáo viên giải tay, đối chiếu đáp án trang 180",
  "expected": [
    { "obligation_kind": "extremum", "value": 89 }
  ]
}
```

`obligation_kind` chọn trong đúng 9 giá trị:

| kind | đề hỏi gì |
|---|---|
| `extremum` | lớn nhất / nhỏ nhất |
| `aggregate_matching` | đếm / tổng / tích / max / min theo điều kiện |
| `ordering` | dãy sau khi sắp xếp |
| `membership` | có mặt hay không |
| `first_match_index` | **vị trí đầu tiên** thoả điều kiện |
| `total_mapping` | ánh xạ đầy đủ khoá → giá trị |
| `derived_sequence` | dãy dẫn xuất (đảo, lọc, khử trùng…) |
| `reachability` | đỉnh nào tới được trên đồ thị |
| `structural_traversal` | thứ tự duyệt cây |

Đề hỏi **nhiều thứ cùng loại** thì thêm `"index": 0`, `"index": 1`… theo thứ tự
bạn liệt kê. Thiếu `index` khi nhập nhằng thì hệ trả `UNGRADED` — không đoán.

Đề **không đòi kết quả cụ thể** (chỉ yêu cầu quan sát diễn biến) thì để
`expected` là mảng rỗng. Case ấy được đếm riêng, không vào tử số lẫn mẫu số.

> Một lưu ý về `structural_traversal`: hệ hiện **chưa có** cách kiểm chứng độc
> lập cho nghĩa vụ này. Đề duyệt cây vẫn chạy được nhưng sẽ được xếp vào
> `verification_gap`. Đó là hạn chế đã biết và đã khai, không phải lỗi phát sinh
> — cứ đưa đề vào nếu nó hợp phạm vi.

### 4. Kiểm hình dạng — chạy bao nhiêu lần cũng được

```bash
cd backend
.venv/Scripts/python.exe scripts/validate_sealed_submission.py \
    ../docs/evaluation/semantic-benchmark/sealed/cases.json
```

Script này **không gọi API, không đụng hệ đang bị đo**, nên bạn chạy thoải mái.
Nó bắt các lỗi khiến lượt chạy live duy nhất bị mất: thiếu trường, `case_id`
trùng, `obligation_kind` sai chính tả, guard bị bỏ quên, dùng nhầm dạng
`{tên_biến: giá_trị}` cũ.

Nó **không** kiểm đề có đúng phạm vi không, **không** kiểm đáp án có đúng không,
và **không** loại case vì IR chịu thua. Ba việc đó lần lượt là: của bạn · của
bạn · và của chính benchmark.

Sửa hết lỗi rồi mới sang bước 5.

### 5. Niêm phong

```bash
cd backend && .venv/Scripts/python.exe scripts/seal_benchmark.py
```

Lần đầu ghi `sealed/FINGERPRINT.txt`. Từ đó trở đi, **mọi thay đổi trong
`cases.json` đều bị phát hiện** — runner so lại vân tay trước khi chạy và từ
chối nếu lệch.

### 6. Giao lại

Gửi cho phía phát triển đúng hai dòng:

```
đường dẫn:   docs/evaluation/semantic-benchmark/sealed/cases.json
fingerprint: <64 ký tự hex trong FINGERPRINT.txt>
```

Không gửi nội dung. Không gửi đáp án.

## Sau khi bạn giao — chuyện gì xảy ra

Task 12 chạy **một lệnh, một lần**. Runner tự từ chối nếu hệ đã lệch khỏi bản
đóng băng, nếu chưa có vân tay, hoặc nếu `cases.json` bị sửa sau khi niêm phong.

Nếu có đề fail vì hệ thiếu checker, thiếu primitive, hoặc IR không diễn đạt
được, thì **failure đó được ghi đúng như nó là**. Không ai được vá rồi chạy lại
để số đẹp hơn — một lần vá là con dấu mất hiệu lực và phải niêm phong tập mới.

Điều này có nghĩa: bạn không cần chọn đề "dễ cho hệ". Đề khó mà hệ trượt là một
kết quả **có giá trị khoa học**, và nó chính là thứ luận văn phải nói thật.

## Ngân sách — để bạn biết vì sao có thể chạy thiếu

```
N = 40  ·  trần lượt LLM logic = 440  ·  trần lần thử HTTP = 520
```

440 = 11 × 40, với 11 là số lượt tối đa một đề có thể tiêu (dẫn từ sơ đồ gọi
hàm thật, không phải ước lượng). Nếu vượt trần thì lượt chạy dừng và báo cáo ghi
`evaluation_complete: false` — khi đó A/B **không được công bố như kết quả
chính**. Trần không được nâng sau khi mở SEALED.
