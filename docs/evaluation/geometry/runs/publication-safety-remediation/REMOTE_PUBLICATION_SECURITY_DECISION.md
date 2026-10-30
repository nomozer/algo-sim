# Remote publication: trạng thái bảo mật

**Hiệu lực hiện tại:** quyết định Owner ngày 2026-10-30 tại §4 cho phép push có điều kiện **chỉ lần tích hợp W3-F2**. §1–§3 giữ nguyên làm lịch sử; điều kiện §3.3 được thay thế trong phạm vi đó. Ngoài phạm vi này, chính sách cũ vẫn hiệu lực.

**Phân loại lịch sử: `REMOTE_SECURITY_BLOCKED`.** Owner quyết `REMOTE_PUSH = NO-GO`; không push nào được thực hiện ở thời điểm báo cáo gốc.

## 1. Vì sao vẫn chặn

Gate `backend/scripts/check_publication_safety.py` chạy trên đối tượng Git ở `76c6795c` (log metadata-only:
`gate-runs/` của run này):

| chế độ | quét | vi phạm | đều thuộc miễn trừ `PENDING` | vi phạm mới ngoài danh sách | verdict |
|---|---|---|---|---|---|
| `--head` | 16,076 blob tracked | 105 dòng / 26 blob | 105 | **0** | BLOCKED |
| `--range origin/main..HEAD` | 459 blob mới + 48 commit message | 5 dòng / 1 blob (`8a515fef`) | 5 | **0** | BLOCKED |

Chặn chỉ vì 27 entry miễn trừ đều `PENDING_OWNER_DECISION`. Không có rò rỉ nào mới phát sinh từ Session 5 hay từ việc sửa này.

## 2. Đã làm (cục bộ, không rewrite)

1. Bản bảo toàn offline của 47 commit chưa công bố và của blob gốc, có SHA-256 (hồ sơ ngoại lệ §8). Nằm cùng SSD, nên
   không chống được hỏng ổ.
2. Commit tiến `76c6795c` gỡ `geometry-dir-first-run-before-fixes.log` khỏi tip. Bytes còn ở `77f7aaf7` và trong bản
   offline; `suite-receipts.json` vẫn giữ SHA-256 và summary. Chuỗi đính chính trong `EVIDENCE_INDEX.md`
   (`PUBLICATION_SAFETY_REMEDIATION`).
3. Gate có test cơ chế (12 test) và 3 phép tiêm lỗi đều làm test đỏ (`POST_MAIN_REGRESSION_REPORT.md`).
4. Hồ sơ ngoại lệ: [`HISTORICAL_TRACEBACK_EXCEPTION_PROPOSAL.md`](HISTORICAL_TRACEBACK_EXCEPTION_PROPOSAL.md).

## 3. Điều kiện để đổi sang `REMOTE_READY_FOR_OWNER_PUSH_REVIEW`

1. Owner tự ghi `APPROVED_BY_USER` cho các entry chấp nhận (hoặc xử lý các entry từ chối theo §7 của hồ sơ).
2. Owner sửa AGENTS.md §4 hoặc ghi diễn giải chính thức (đề xuất văn bản ở hồ sơ §5).
3. Hai lệnh sau exit 0 trên HEAD định push (chạy từ `backend/`):
   `check_publication_safety.py --head` và `check_publication_safety.py --range origin/main..HEAD`.
4. Nhánh `research/publication-safety-remediation` được Owner cho merge vào `main` (hiện chưa merge).
5. Owner cấp GO push riêng. Chỉ push fast-forward, không force.

Không điều kiện nào ở trên được agent tự đánh dấu.

## 4. Owner supersession — W3-F2 only (2026-10-30)

Nguồn thẩm quyền: yêu cầu trực tiếp của Owner, “OWNER DECISION — ALGOSIM AUTONOMOUS INTEGRATION POLICY”, nhận ngày
2026-10-30. Agent ghi lại quyết định được cấp; không tự phê duyệt ngoại lệ. Phạm vi là lần xuất bản W3-F2 từ remote
main `996f114b3480efe1b0d075dd4342530aaa12ddae`, đã tích hợp local tại `15a8e1ac327e7ec5197ebe5d08330afb444b9571`,
cộng các commit tài liệu/chứng cứ cần thiết cho lần đóng tích hợp này. Không áp dụng cho nhiệm vụ tương lai.

| Chính sách cũ | Quyết định thay thế của Owner cho lần tích hợp này |
|---|---|
| §3.1: phải xử lý các ngoại lệ pending trước push | Không tự phê duyệt 104 legacy exception findings; giữ nguyên registry, chỉ hai ngoại lệ đã được Owner ghi trước đó có hiệu lực |
| §3.2: cần diễn giải chính thức của Owner | §4 này ghi nhận diễn giải có giới hạn từ yêu cầu Owner; không giảm bảo mật toàn cục |
| §3.3: cả head và range phải exit 0 | Range `origin/main..HEAD` bắt buộc PASS; head bắt buộc chạy và báo đúng BLOCKED do historical baseline debt |
| §3.4: cần GO merge | Owner xác nhận local main đã fast-forward `996f114b` → `15a8e1ac`; không cần merge lại |
| §3.5: GO push riêng, fast-forward | Owner cấp GO có điều kiện cho non-force push main và xác minh SHA remote, sau khi mọi điều kiện dưới đạt |

Điều kiện bắt buộc trước push:

1. Đọc remote thực tế; remote main vẫn đúng baseline trên, không đổi hay diverge. Working tree sạch.
2. Candidate `4e7fe91d`, product `dd17fbfb`, Full T3 và bằng chứng review còn hợp lệ; xác minh product không đổi.
3. Commit chính sách này và hồ sơ đối chiếu trước push. Chạy scanner nguyên vẹn trên chính HEAD định push.
4. `--range origin/main..HEAD` PASS. `--head` vẫn BLOCKED do historical baseline debt và phải được báo trung thực.
5. So sánh chính xác từng finding (rule, path, blob, line, exception) trên HEAD với remote baseline; không có finding
   mới chưa được phê duyệt. Xác minh GOOGLE_API_KEY cũ là test vector bằng blob/provenance và luồng sử dụng; nếu
   không xác minh an toàn được thì STOP. Không có credential/token/secret thật chưa xử lý trong nội dung mới.
6. Không sửa scanner, làm giả PASS hay thay trạng thái Owner trong registry. Chạy các test bị ảnh hưởng.
7. Nếu remote đổi hoặc có secret/rủi ro mới: STOP. Không force-push, reset, rebase hay rewrite lịch sử.
8. Sau non-force push: đọc SHA remote thực tế và đối chiếu local main. Chỉ sau đó mới dọn worktree W3-F2 có kiểm kê
   tracked/untracked/ignored, evidence và junction node_modules; chỉ Git worktree remove không force. Không chắc
   thì giữ lại, không chặn các bước còn lại; giữ backups, historical receipts và baseline evidence còn consumer.

Phân biệt `TECHNICAL_READY`, `PUBLICATION_READY` (theo chính sách có phạm vi này) và `REMOTE_VERIFIED`.
Head BLOCKED không được đổi tên thành scanner PASS. Hết lần tích hợp này, §4 không cấp quyền cho lần push khác.
Hồ sơ: `docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/integration/`.
