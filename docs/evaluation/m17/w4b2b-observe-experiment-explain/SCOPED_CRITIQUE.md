# SCOPED IMPECCABLE CRITIQUE — bề mặt pilot W4B-2B

⚠️ **DEGRADED: single-context (session cấm gọi AgentTool khi user không yêu cầu)**

Playbook `critique` đòi hai sub-agent cô lập (Assessment A / B). Chỉ thị phiên làm
việc cấm gọi AgentTool nếu user không yêu cầu tường minh, nên hai đánh giá chạy
tuần tự trong cùng ngữ cảnh. Banner này là bắt buộc theo chính playbook — không
được ẩn đi.

**Phạm vi:** `find_max` Quan sát/Thí nghiệm/Giải thích · `insertion_sort`
Quan sát/Thí nghiệm · tổ hợp Thí nghiệm+Giải thích. **Không** soát phần còn lại
của sản phẩm. Chế độ: **Operate** (học sinh đang làm một việc, không phải đang
được thuyết phục).

## Assessment B — máy dò

```
node .claude/skills/impeccable/scripts/detect.mjs --json \
  algorithm/ui.tsx ScanActionZone.tsx SortActionZone.tsx \
  SimulationInspector.tsx AnalysisCard.tsx
→ []   (exit 0)
```

**0 finding** trên bề mặt pilot. ~40 finding token drift đã biết nằm ở
`styles/global.css` — **ngoài phạm vi**, không sửa không ẩn không phân loại lại
(`POST-W4B2B_DESIGN_TOKEN_AUDIT`).

## Assessment A — trả lời 14 câu của §10

| # | Câu hỏi | Phán quyết |
|---|---|---|
| 1 | Mô phỏng có là thứ nổi bật nhất? | **Có.** Sân khấu chiếm phần trên, rộng nhất; mọi thứ khác xếp dưới hoặc sang phải |
| 2 | Thí nghiệm có dễ tìm? | **Có.** Teaser cụ thể + nút có icon, đứng ngay dưới vùng nội dung, không chìm vào chrome |
| 3 | Mở rồi Thí nghiệm mới thành chính? | **Có.** Vùng cam kết xuất hiện với hai nút viền rõ, chiếm hàng riêng |
| 4 | Giải thích có ra dáng tuỳ chọn? | **Có.** Đóng mặc định; mở ra là cột phải hẹp, chữ nhỏ, tông trầm |
| 5 | Dòng thời gian có ở vai phụ? | **Có.** Dán đáy, nền riêng, không tranh chú ý |
| 6 | Có chữ lặp không? | **Không đạt — xem MAJOR-1** |
| 7 | Vùng cam kết có lấn mô phỏng? | **Không.** Nó nằm dưới sân khấu, không đè, không thu nhỏ hình |
| 8 | Phản hồi có gắn rõ với hành động? | **Có, và đây là chỗ mạnh nhất.** Nút đã chọn giữ viền đậm + nhãn "✓ em đã chọn", câu phản hồi nằm ngay dưới đúng nút đó |
| 9 | Các lựa chọn có dễ hiểu? | **Có.** "Đặt 9 làm max mới" / "Giữ max = 7,5" nói bằng ngôn ngữ cơ chế, mang số thật, không phải Có/Không |
| 10 | Quan sát có lỡ trông như bài kiểm tra? | **Không.** Ở Quan sát chỉ có dải quan hệ + lời mời; không nút cam kết, không câu hỏi |
| 11 | Có thẻ khổng lồ thường trực? | **Không** |
| 12 | Có tương tác bị che/khuất ở viewport bắt buộc? | **Không** — 22 target × 6 viewport PASS, 0 failure |
| 13 | Mở Giải thích có làm dày quá? | **Không ở 1920/1536.** Sân khấu co theo đúng hành vi W4B-2A đã đóng băng |
| 14 | Teaser hữu ích hay ồn? | **Hữu ích.** Nó nêu đúng bất biến sắp bị thử ("không bao giờ nhìn lại vùng đã duyệt") mà không lộ hệ quả |

## Findings

### MAJOR-1 — khung thí nghiệm và gợi ý kéo nói gần như cùng một câu, xếp chồng

Khi mở Thí nghiệm ở `find_max`, hai dòng đứng liền nhau:

> *"Thuật toán chỉ nhớ giá trị tốt nhất ĐÃ GẶP và không bao giờ quay lại vùng đã
> duyệt. Hãy đổi một phần tử chưa duyệt vào vùng đã duyệt rồi xem kết quả cuối."*
> *"Kéo một cột chưa duyệt thả vào vùng đã duyệt (các cột xám) — kết quả cuối có
> còn đúng với dãy mới không?"*

`framing` và `hint` là hai trường khác nhau nhưng đang chở cùng một chỉ dẫn. Đây
đúng lớp trùng lặp mà UI-CLARITY W1 đã gỡ một lần ở chỗ khác.
**→ BACKLOG** (không chặn milestone; sửa là việc của lớp copy, không phải kiến trúc).

### MAJOR-2 — hai cách đếm vị trí trên cùng một màn hình

Panel Giải thích in `vị trí 0` (chỉ số 0-based lấy thẳng từ biến `vt`), trong khi
vùng cam kết ngay bên trái nói `Bình — vị trí 2` (1-based). Học sinh đọc hai con
số khác nhau cho cùng một phần tử.

Kho mã ĐÃ từng vấp đúng lỗi này (`core/algorithms.ts` có chú thích *"hai cách đếm
cạnh nhau trong một câu"*). Chủ sở hữu là `VarsView`/`VAR_LABELS`, không phải mã
của wave này — lỗi **có sẵn**, nay lộ ra vì Giải thích và Thí nghiệm lần đầu đứng
cạnh nhau. **→ BACKLOG**, ưu tiên cao nhất trong danh sách backlog.

### MINOR-1 — biến hiện tại và câu phản hồi lệch pha một bước

Ở bước 2/10: panel ghi `max 7,5`, phản hồi ghi *"max được cập nhật: 7,5 → 9"*.
Cả hai **đều đúng** (phép gán thuộc bước kế tiếp), nhưng đặt cạnh nhau thì đọc như
mâu thuẫn. Không sửa bằng cách nói dối state; nếu sửa thì sửa ở lớp chữ.
**→ BACKLOG**.

### Không có BLOCKER

Đối chiếu đúng danh sách BLOCKER của §11: học sinh tìm được Thí nghiệm ✓ · vùng
cam kết không che cơ chế ✓ · phản hồi gắn rõ với hành động ✓ · đường bàn phím
thông ✓ · không rò đáp án ✓ · không cắt nội dung ở mọi viewport bắt buộc ✓ ·
đóng/mở Giải thích·Thí nghiệm không đụng canonical state ✓.

## Hai điểm mạnh đáng giữ khi mở rộng họ

1. **Nhãn hành động nói bằng cơ chế, mang số thật** — "Đặt 9 làm max mới" chứ
   không phải "Có/Không". Nó biến một câu hỏi trắc nghiệm thành *làm đúng việc mà
   thuật toán làm*. Giữ nguyên nguyên tắc này cho `count_if`/`sum_if`.
2. **Vết chọn không biến mất sau khi chấm** — nút đã chọn giữ viền + "✓ em đã
   chọn". Nửa sau của vòng học (đối chiếu cam kết với phán quyết) chỉ tồn tại nhờ
   chi tiết đó.

## Câu hỏi để ngỏ cho wave sau

Ở `find_max`, Thí nghiệm hiện gộp **hai** việc rất khác nhau: *cam kết* (làm đúng
bước thuật toán) và *phá bất biến* (kéo cột để đánh lừa). Cùng một cổng, hai ý
định. Mở rộng sang `count_if`/`sum_if` — vốn `mode: "hidden"`, không có kéo — sẽ
cho ra một cổng chỉ mang **một** việc. Nếu cổng ở hai bài mang nghĩa khác nhau thì
tên "Thí nghiệm" bắt đầu phải gánh hai nghĩa; đáng kiểm tra bằng người dùng thật
trước khi trải ra bảy target còn lại.
