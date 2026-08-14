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
