# Remote publication: trạng thái bảo mật

**Phân loại: `REMOTE_SECURITY_BLOCKED`.** Owner quyết `REMOTE_PUSH = NO-GO`; không push nào được thực hiện.

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
