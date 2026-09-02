# PRODUCT_INTEGRATION_HARDENING — soát hành trình người dùng xuyên tầng

> Lượt soát ngày **2026-09-02**. Mục tiêu: tìm lỗi **giữa các tầng** — chỗ mà mỗi
> tầng đều đúng phần của mình nhưng ghép lại thì sai.
>
> **0 API call.** Mọi lượt đo dùng envelope đã niêm phong hoặc catalog bài mẫu
> chạy phía client. Không thêm năng lực hình học, không đổi kiến trúc.

---

## 1. Cách soát

Ba kịch bản Chrome thật (CDP), tất cả cần `npm run dev`, tất cả **0 mạng ra ngoài**:

| kịch bản | đi đường nào | kết quả |
|---|---|---|
| `frontend/scripts/certify-journey-integration.mjs` | nạp envelope thẳng vào store — cô lập tầng | **13/13**, 0 lỗi bảng điều khiển |
| `frontend/scripts/certify-offline-journey.mjs` | đúng đường người dùng: trang chủ → thẻ bài mẫu → xưởng → bài thứ hai | **11/11**, 0 lỗi bảng điều khiển |
| `frontend/scripts/certify-refusal-surface.mjs` | 5 hạng từ chối + 4 envelope hỏng | **21/21**, 0 lỗi bảng điều khiển |

Artifact: `docs/evaluation/integration/{journey,offline-journey,refusal-surface}.json`.

Hai kịch bản đầu **cố ý chồng nhau một phần**. Kịch bản nạp store trực tiếp bắt
được lỗi trạng thái; kịch bản đi đường thật bắt được lỗi điều hướng. Không cái nào
thay được cái kia — lỗi §2.2 dưới đây chỉ hiện ở cái sau.

---

## 2. Hai lỗi tích hợp tìm được, đều đã sửa

Cả hai thuộc loại **A** theo §15 của chỉ thị (trình bày / tích hợp), nên sửa tại
chỗ ở đúng owner hiện tại. **Không** lỗi nào chạm ngữ nghĩa hay hình học.

### 2.1 Trạng thái tương tác rớt sang bài mới — hiện ra "Bước 10/6"

**Đo được trước bản vá** (`certify-journey-integration.mjs`, nhóm D):

```
[bẩn]     {"buoc":"Bước 10/12","chon":"Trung điểm N của AD","bung":"Ráp lại"}
[bài mới] {"buoc":"Bước 10/6", "chon":"N",                  "bung":"Ráp lại","scrub":5}
✗ D1 bài mới bắt đầu ở bước 1     | thuc=Bước 10/6
✗ D2 bài mới không giữ vật đang chọn của bài cũ | coSoi=true ten="N"
✗ D3 bài mới không mở sẵn trạng thái tách khối  | thuc=Ráp lại
```

**Vì sao.** `SimulationWorkspace` dựng `Scene3DExplorer` ở **cùng vị trí cây** cho
mọi bài, nên React dùng lại instance thay vì dựng mới; `InteractionState` khởi
tạo bằng `useState(taoTrangThai)` nên chỉ chạy một lần trong đời component.

Ba triệu chứng, một nguyên nhân — và triệu chứng nặng nhất là **"Bước 10/6"**: một
bước **không tồn tại**. Nó không chỉ xấu, nó nói dối về dữ liệu.

**Sửa** (`Scene3DExplorer.tsx`, hai chỗ, đều thuộc tầng trình bày):

```ts
useEffect(() => { setTt(taoTrangThai()); setNgan(null); }, [scene]);
```

và kẹp phòng thủ ở dòng chữ:

```tsx
{`Bước ${clampStep(day, tt.current_step) + 1}/${stepCount(day)}`}
```

`clampStep` đã tồn tại trong `scene3d-model.ts` — không viết hàm mới.

⚠️ Hiệu ứng **không** reset `chiTiet`: mức chi tiết muốn đọc là sở thích người
dùng, không gắn với bài nào. Reset nó là bắt bật lại sau mỗi bài. Có ca khoá
điều này để lần sau không ai "dọn dẹp" thêm vào.

**Sau bản vá:** `ĐẠT 13/13`; qua đường UI thật `§4 bài thứ hai mở sạch: Bước 1/5
chon="" bung=Tách khối`.

### 2.2 Chip "Menu" chết với người dùng khách

**Đo được trước bản vá** (`certify-offline-journey.mjs`):

```
✗ §9 chip Menu mở được cột điều hướng | bam=ok muc=[]
```

Bấm được, không mở được gì. `AppSidebar.tsx` trả `null` khi chưa đăng nhập, còn
xưởng 3D không biết điều đó nên vẫn hiện lối ra.

**Sửa** (`SimulationWorkspace.tsx`): chỉ truyền lối ra khi có cột để mở.

```ts
const coNguoiDung = !!useAuthStore((s) => s.user);
…
onMoMenu={coNguoiDung ? openNav : undefined}
```

Xưởng vốn đã tự ẩn chip khi không nhận `onMoMenu`. Khách vẫn có lối về qua dấu
hiệu sản phẩm ở thanh trên (`✓ §9 wordmark đưa về màn nhập đề`).

⚠️ Ca guard `canvas-first-shell.test.tsx` **phải sửa theo**: nó đang khoá chữ
viết `onMoMenu={openNav}` trong khi chính nó, ở ca ngay trên, khẳng định
`{user && <AppSidebar />}`. Guard nay khoá **bất biến** — chip xuất hiện *đúng khi*
có cột để mở — chứ không khoá một cách viết.

---

## 3. Điều đã soát và KHÔNG có lỗi

| soát | kết luận |
|---|---|
| Thẩm quyền kết quả | `hienSo()` in cấu trúc `exact` (`kind: rational｜radical`) do backend gửi; **không** hàm nào ở frontend tính lại số từ toạ độ. `RESULT_AUTHORITY = DETERMINISTIC` |
| Không bịa vật thấy được | `buildObject3D` khoá mọi nhánh theo **cả** loại vẽ **và** trường dữ liệu bắt buộc; thiếu là trả `null`. Không có nhánh nào dựng hình từ suy đoán |
| Song ánh khung ⇔ bước | tua bằng thanh trượt và bằng nút cho cùng một bước ⇒ cùng một khung; kéo quá cuối bị kẹp, không ra bước không tồn tại |
| Bề mặt từ chối | 5/5 hạng đúng nhãn, 0 canvas, 0 mã kỹ thuật lọt UI, đều còn đường đi tiếp |
| Envelope hỏng | 4 dạng hỏng (`{}`, thiếu `simulation_id`, `scene3d` sai kiểu, vắng `scene3d`) — không ném lỗi, không trắng màn |
| Ba khổ màn hình | 1600×900 · 1440×900 · 1366×768 × 4 bài × ô soi đóng/mở: 0 tràn ngang, 0 đè lên nhau, khung vẽ và nhãn ổn định |

---

## 4. Một điều đáng ghi, KHÔNG sửa trong lượt này

**Kho không có React error boundary nào.** Đã kiểm: không `componentDidCatch`,
không `ErrorBoundary`, không `react-error-boundary`.

Hiện tại điều đó **chưa gây hại đo được** — bốn dạng envelope hỏng ở §3 đều đi
qua êm, vì `buildObject3D` fail-closed và các bộ đọc đều phòng thủ. Nhưng nó có
nghĩa là **một lần ném ở bất kỳ đâu trong cây là mất cả trang**, không phải mất
một khối.

Không sửa vì: thêm error boundary là **thêm một tầng kiến trúc**, đúng thứ §15
của chỉ thị dặn không biến wave thành refactor. Ghi lại ở đây để quyết riêng.
