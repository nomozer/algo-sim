# TEST_TIERS.md — bốn tầng kiểm thử, và **nhãn nào được nói gì**

> Hợp đồng ràng buộc. Khoá bởi `frontend/src/test-tiers.test.ts` (ngữ nghĩa
> nhãn) và `frontend/scripts/impact.mjs` (bộ chọn). Số sống → `CURRENT_STATE.md`.

## Vì sao có file này

Đo ở HEAD `b7ca150`: `pytest` đầy đủ **57s**, `vitest` + build **14–25s**. Sửa
một dòng CSS rồi chờ một phút rưỡi là cách chắc chắn nhất để người sửa **thôi
chạy test** — và một bộ test không ai chạy thì bằng không.

Nhưng đi nhanh bằng cách chạy ít test hơn là tự lừa. Nên bốn tầng dưới đây khác
nhau ở **phạm vi được bảo vệ**, và mỗi tầng chỉ được phát đúng nhãn của mình.

## Bốn tầng

| Tầng | Mục đích | Lệnh | Nhãn phát ra |
|---|---|---|---|
| **T0** IMPACT | phản hồi khi đang sửa | `node frontend/scripts/impact.mjs` | `IMPACT_GATE_PASS` |
| **T1** DOMAIN | xong một lát cắt miền | `npm run test:domain:<miền>` | `DOMAIN_GATE_PASS` |
| **T2** WAVE | trước khi đóng một wave | `npm run test:wave` | `WAVE_GATE_PASS` |
| **T3** FULL | mốc/phát hành | `npm run test:full` | `FULL_PRODUCT_GATE_PASS` |

> **Đã sửa (2026-10-08, run `repo-cleanup`):** script T1 nay là `test:domain:geometry`, `test:domain:semantic`,
> `test:domain:shared-ui`, `test:domain:classroom`; `impact.mjs` sở hữu miền hình học theo thư mục
> (`ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE` RESOLVED). Ghi chú cũ giữ dưới đây làm lịch sử.
>
> **Thực trạng (2026-10-05, `cuboid-final-review`).** 8/10 script `test:domain:*` của `frontend/package.json`
> (`algorithm`, `binary`, `logic`, `network`, `database`, `web`, `generic`, `tree`) trỏ vào thư mục miền Tin học đã
> gỡ; chỉ `shared-ui` và `classroom` còn chọn được test. Miền hình học chưa có script T1 và chưa có chủ sở hữu trong
> `frontend/scripts/impact.mjs`: sửa `src/simulations/domains/geometry/**` thì T0 báo `IMPACT_MAPPING_MISSING` và leo
> thang lên toàn bộ `src/` + pytest. Kiểm nhanh miền hình học bằng tay:
> `cd frontend && npx vitest run src/simulations/domains/geometry/`. Việc sửa script ghi ở `OPEN_ISSUES.md`
> (`ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE`).

### Luật nhãn — **không tầng nhỏ nào được nói giọng tầng lớn**

`IMPACT_GATE_PASS` nghĩa là *"những gì tôi chọn đều xanh"*, **không** nghĩa là
sản phẩm đúng. Chỉ T3 được phát `FULL_PRODUCT_GATE_PASS`. Đây không phải chuyện
chữ nghĩa: một tập con 2 giây được báo cáo như một lượt xác nhận đầy đủ chính là
cách một wave đóng sai.

## Khi nào chạy tầng nào

- **T0** — sau mỗi lần sửa có nghĩa. Vài giây. Tất định, offline.
- **T1** — khi kết thúc một lát cắt trong một miền (vd xong renderer web).
- **T2** — trước khi commit đóng wave. Gồm typecheck + build + guard kiến trúc.
- **T3** — trước khi tuyên bố một mốc, hoặc khi đụng hợp đồng dùng chung.

## Ba nguồn chọn test (T0)

Không nguồn nào tự giải quyết hết; bộ chọn ghép cả ba và **in ra lý do**:

1. **Sở hữu theo thư mục** — `domains/web/**` → miền `web`.
2. **Sổ chủ sở hữu dùng chung** — `SimulationControls`, `store.ts`,
   `global.css`, `transport-policy.ts`… đổi một chỗ, ảnh hưởng nhiều miền.
3. **Leo thang bảo thủ** — file sản phẩm không tra ra chủ ⇒ `IMPACT_MAPPING_MISSING`
   và **leo lên tầng rộng hơn**, không bao giờ trả về "0 test, xanh".

## Luật không-được-vi-phạm

- **Thay đổi mã sản phẩm không bao giờ được chọn 0 test.** Không tra ra chủ thì
  leo thang. Một lượt chạy rỗng màu xanh là điều tệ nhất bộ chọn có thể làm —
  và repo này đã bị đúng kiểu "khớp 0 mục nhưng báo thành công" nhiều lần.
- **Chủ sở hữu dùng chung mở rộng bán kính**, không thu hẹp về một test trực tiếp.
- **Guard kiến trúc** (`code-index-sync`, `tokens`, `ui-hygiene`) không import
  file bị đổi, nên đồ thị import không chọn được chúng — chúng phải được khai
  theo sở hữu.
- **Live AI không bao giờ nằm trong T0/T1/T2.** Nó là tầng riêng, opt-in, có
  ngân sách (`docs/CORRECTNESS.md §7`).
- **Ảnh của lượt đo trình duyệt: chụp để kiểm, LƯU có chọn** (yêu cầu người dùng, run
  `regular-triangular-pyramid-w01`; W5 lưu 768 ảnh). Bộ đo vẫn chụp mọi trạng thái nó kiểm (nhiều phép kiểm
  đọc điểm ảnh); sau bộ dựng bằng chứng, `backend/scripts/prune_evidence_images.py` chỉ giữ ảnh bộ dựng ĐỌC
  (`results/EVIDENCE_IMAGE_INPUTS.json` — oracle thị giác, crop cạnh khuất, sheet), ảnh nó SINH, ảnh trong tập
  duyệt chọn TRƯỚC khi đo (`inputs/REVIEW_SET.json`, mỗi mục một yêu cầu/lỗi) và MỌI ảnh của một họ có lượt
  thất bại; ảnh bỏ vẫn ghi sha256 ở `results/IMAGE_POLICY.json`. Ngưỡng và mục tiêu kiểm không đổi. Không chụp
  mặc định mọi họ × bước × lựa chọn × khổ để duyệt; ảnh trước/sau cùng fixture, khổ và góc nhìn.
- **Từ run `exact-dimensions`: quyết TRƯỚC khi chụp, không chụp rồi xoá.** Phép kiểm điểm ảnh đọc khung trong
  bộ nhớ (`canvasFrame`), không đọc PNG — nên mọi bộ đo hỏi `frontend/scripts/capture-policy.mjs` trước mỗi lần ghi
  tệp (`capture`, `captureElement`). Mặc định `--anh-che-do toi-thieu`: ảnh oracle (`neutral_final`,
  `rotated_neutral` của suite), ảnh khớp `--review-set`, ảnh tại trạng thái lỗi; `day-du` khi cần tìm lỗi tiến trình
  dựng. Mỗi JSON bằng chứng ghi `capture_policy` (lượt gọi · ảnh tạo · bỏ qua · ảnh lỗi); số ảnh không chụp không
  bao giờ trình bày như số ảnh đã xoá. Lỗi tách ba lớp ENVIRONMENT / HARNESS / PRODUCT_ASSERTION; lỗi môi trường
  không giữ cả họ. Bước trình duyệt chạy tuần tự, có `timeout` hữu hạn, in tiến độ; chỉ chạy lại bước đỏ. Tỉa sau đo
  (`prune_evidence_images.py`) chỉ còn cho run cũ / chế độ đầy đủ.
- **Từ run `browser-temp-lifecycle`: tài nguyên tạm có chủ và có hạn.** Hồ sơ Chrome của bộ đo nằm dưới
  `D:/tmp/algosim-browser` (hoặc `ALGOSIM_BROWSER_TMP`; thiếu D: thì `%TEMP%/algosim-browser`), xoá khi phiên đóng hoặc
  hỏng; bị giết cứng thì lượt sau tự dọn theo `owner.json` (`frontend/scripts/browser-runner.mjs`). Không đặt `TEMP`/`TMP`
  toàn hệ thống, không diệt `chrome.exe` theo tên, không đụng hồ sơ trình duyệt cá nhân. Ảnh không phải bằng chứng
  (`--anh`/`--screenshots` của bước không cần lưu) ghi vào thư mục tạm của lượt đo và XOÁ khi lượt đo xong; chỉ ảnh
  oracle, tập duyệt chọn trước và ảnh lỗi vào thư mục run. Cảnh đã duyệt mà thành phần liên quan không đổi thì dùng
  lại bằng chứng cũ (đối chiếu `git diff` của product commit), không chụp lại.

## Chi phí đã đo và đã sửa

| Chỗ | Trước | Sau | Cách |
|---|---|---|---|
| `pytest` đầy đủ | 57s | **15,6s** | hạ số vòng PBKDF2 trong test (xem dưới) |

`test_classroom_api` + `test_auth_api` + `test_guest_trial` chiếm **40s/50s**,
và nguyên nhân là 365ms mỗi lần băm mật khẩu (600.000 vòng theo OWASP) nhân với
mỗi lượt đăng ký/đăng nhập trong fixture. 600.000 vòng **đúng cho production và
không đổi**; trong test nó là chi phí fixture. An toàn vì số vòng được ghi vào
chính chuỗi lưu và `verify_password` đọc lại từ đó. Mức production khoá riêng ở
`tests/test_kdf_cost.py`, file duy nhất mang marker `real_kdf_cost` nên không đi
qua fixture hạ chi phí.
