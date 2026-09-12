/**
 * Scene3D — kiểu dữ liệu + phép chiếu THUẦN cho renderer hình học không gian.
 *
 *   Semantic Program → Interpreter → SimulationState → Scene3D → **đây** → three.js
 *
 * File này KHÔNG import `three`. Đó là chủ đích: mọi thứ quyết định *cái gì hiện
 * ra ở bước nào* đều kiểm được mà không cần WebGL, và tầng vẽ chỉ còn lại việc
 * đặt mesh. Cùng khuôn `encap-ui3d.tsx` đã chứng minh (`layerDepth`/`sideX` là
 * hàm thuần, tách khỏi `Encap3DWorkspace`).
 *
 * ─── HAI RANH GIỚI, VÀ CHÚNG LÀ LÝ DO FILE NÀY TỒN TẠI ────────────────────
 *
 * ① KHÔNG TÍNH HÌNH HỌC. Không tích có hướng, không giao điểm, không suy quan
 *    hệ. Mọi toạ độ/pháp tuyến/vector chỉ phương đến từ kernel hữu tỉ ở backend.
 *    Renderer chỉ ĐẶT và ĐỊNH HƯỚNG những thứ đã được tính.
 *
 * ② `toNumber` là chỗ DUY NHẤT số hoá float trong toàn chuỗi. Backend giữ chuỗi
 *    phân số (`"1/2"`) tới tận đây vì kernel so **bằng đúng**, không epsilon —
 *    hoá float sớm là vứt bỏ đúng thứ phân biệt hệ này với một bộ vẽ hình.
 *    GPU cần float, nên phép ấy phải xảy ra; nó chỉ không được xảy ra sớm hơn.
 */

/** Toạ độ chính xác: chuỗi phân số như `"0"`, `"2"`, `"1/2"`, `"-3/4"`. */
export type Exact = string;
export type ExactVec3 = [Exact, Exact, Exact];
export type Vec3 = [number, number, number];

/**
 * Loại hình vẽ — **ĐỒNG BỘ CỨNG** với `scene3d.RENDER_HINT` ở backend.
 *
 * Khoá bằng `tests/geometry/test_scene3d_ts_sync.py`: thêm một loại ở Python mà
 * quên nhánh ở đây thì renderer sẽ **im lặng bỏ qua** đối tượng — đúng chế độ
 * hỏng của bất biến #33 (đã xảy ra thật với `bar_chart`).
 */
/**
 * Kiểm hình dạng `Scene3D` tại BIÊN NHẬN. Không tin dữ liệu qua mạng.
 *
 * `envelope.scene3d` đến từ backend, và `SimulationEnvelope.config` cũng khai
 * `unknown` với cùng lý do: qua mạng thì không có gì bảo đảm hình dạng ngoài
 * việc **kiểm tại chỗ nhận**. FAIL-CLOSED: hình dạng lạ ⇒ shell rơi về đường
 * 2D cũ thay vì dựng một khung 3D rỗng. Bày một khung rỗng là mời người học
 * đi tìm thứ không có.
 *
 * Ở cạnh định nghĩa `Scene3D` chứ không ở component, vì đây là phép kiểm của
 * KIỂU — component nào nhận cảnh cũng cần nó, và trước 2026-08-30 nó nằm trong
 * `Scene3DSection.tsx` nên `SimulationWorkspace` phải import một component chỉ
 * để mượn một type guard.
 */
export function hopLeScene3D(x: unknown): x is Scene3D {
  if (!x || typeof x !== "object") return false;
  const s = x as Partial<Scene3D>;
  return (
    Array.isArray(s.objects) &&
    s.objects.length > 0 &&
    Array.isArray(s.events) &&
    s.events.length > 0 &&
    Array.isArray(s.free_objects)
  );
}

export const RENDER_KINDS = [
  "point_marker",
  "line",
  "surface",
  "mesh",
  "polygon",
  "readout",
  /**
   * ĐƯỜNG TRÒN trong không gian — tâm, pháp tuyến, **bình phương** bán kính.
   *
   * Payload chở `radius_sq` chứ không chở `radius`: bán kính có thể vô tỉ,
   * bình phương thì không, nên số chính xác đi hết đường dây rồi mới lấy căn ở
   * biên hiển thị. Cùng quy ước `distance_sq` đã dùng từ đầu.
   */
  "circle",
  /**
   * ELIP trong không gian — tâm, pháp tuyến, **hai** phương trục và **bình
   * phương** hai bán trục.
   *
   * Loại vẽ RIÊNG, không mượn `circle`, và khác biệt ấy là ngữ nghĩa chứ không
   * phải trang trí: một đường tròn vẽ được từ MỘT bán kính, một elip cần hai
   * bán trục **và** biết nó xoay thế nào trong mặt phẳng của nó. Cho elip đi
   * dưới lốt `circle` thì renderer vẽ một vòng tròn cho một hình không tròn —
   * đúng lớp lỗi mà `vector3` đã mắc khi đi dưới lốt `point3`.
   *
   * `major_dir`/`minor_dir` tới đây **chưa chuẩn hoá độ dài**: chuẩn hoá đá
   * chúng ra khỏi ℚ³, nên backend giữ nguyên và việc ấy làm ở biên hiển thị —
   * cùng chỗ lấy căn của `semi_*_sq`.
   */
  "ellipse",
  /**
   * KHỐI CONG — **một** loại vẽ cho cả cầu, trụ và nón.
   *
   * Không `sphere`/`cylinder`/`cone` riêng: hình nào là **dữ liệu**
   * (`curved_kind`), không phải ba nhánh vẽ. Ba loại vẽ ở đây nghĩa là ba
   * nhánh phía TS đối diện ba nhánh phía Python, và chúng sẽ trôi khỏi nhau —
   * `test_scene3d_ts_sync.py` chỉ khoá được tập TÊN, không khoá được ý nghĩa.
   *
   * Payload cố ý **không có `vertices` lẫn `faces`**: renderer chia lưới để
   * vẽ, nhưng lưới ấy không có đường nào đi ngược lên phép đo hay checker.
   */
  "curved_solid",
  /**
   * CÓ TRONG CẢNH, KHÔNG VẼ LÊN KHUNG — hiện chỉ `vector3`.
   *
   * Không phải "chưa hỗ trợ": backend nói thẳng rằng vật này không có hình
   * biểu diễn đúng trên khung 3D. Một vectơ tự do **không có vị trí**, nên vẽ
   * nó ở bất kỳ đâu là renderer tự quyết một dữ kiện hình học.
   *
   * Vật vẫn đi trọn pipeline: cây thành phần, ô soi và phép chọn đều thấy nó.
   * Trước bản này nó đi qua dưới lốt `point3` và phía này phải đọc `producer`
   * để lọc ra — tầng trình bày suy lại ngữ nghĩa, đúng thứ R0 cấm.
   */
  "non_visual",
] as const;
export type RenderKind = (typeof RENDER_KINDS)[number];

export interface SceneObject {
  id: string;
  /**
   * TÊN ĐỌC ĐƯỢC do tầng ngữ nghĩa backend đặt (`display_names.ten_hien_thi`).
   *
   * ⚠️ **KHÔNG BAO GIỜ là `id`.** Trước 2026-09-02 trường này rơi về `id` khi
   * mô hình không đặt nhãn, nên học sinh đọc `khoang_cach_hs` trên màn hình.
   * Nay backend luôn trả một câu — cùng lắm là *"Điểm"* — nên phía này không
   * cần, và không được, tự chế một tên thay thế.
   */
  label: string;
  /**
   * KÝ HIỆU NGẮN in cạnh vật trên khung (`M`, `A′`, `(MNP)`, `d(H, (SBC))`).
   *
   * `null`/vắng là câu trả lời HỢP LỆ: vật ấy không có ký hiệu toán nào dẫn ra
   * được, và khung **không in gì** cho nó. Đừng thay bằng `label` (câu dài sẽ
   * phủ kín hình) và đừng dựng từ `id` — đọc ngược định danh chính là thứ bản
   * này gỡ bỏ.
   */
  notation?: string | null;
  /**
   * CÁCH GỌI NGẮN khi vật này bị nhắc **trong câu của vật khác**, hoặc trong
   * một danh sách (*"Dựa trên"*, *"Thuộc"*).
   *
   * Luôn có, và **không bao giờ là một câu dài**: backend dựng nó bằng ký
   * hiệu của toán hạng, hoặc bằng danh từ theo kiểu — nên đệ quy dừng ở một
   * tầng. Dùng `label` ở những chỗ ấy thì câu lồng câu và không tách được đâu
   * là hết toán hạng.
   */
  reference?: string;
  /**
   * *"Vật này LÀ GÌ"* — một dòng dưới tên trong ô soi.
   *
   * ⚠️ Do **backend** quyết (`display_names.py`). Trước 2026-09-03 phía này tự
   * dựng nó từ một bảng `producer → tiếng Việt`, tức một thẩm quyền đặt tên
   * thứ hai; bảng ấy đã gỡ. Đừng dựng lại nó dưới tên khác.
   */
  role?: string;
  type: string;
  render: RenderKind;
  origin: "free" | "derived";
  producer: string | null;
  depends: string[];
  /**
   * BỐN TRƯỜNG TƯƠNG TÁC — dữ liệu TRÌNH BÀY, không đi vào phép tính nào.
   *
   * `parent` — chứa đựng cấu trúc, tối đa MỘT, và nó không thay `depends`:
   *   `M = midpoint(A,B)` phụ thuộc A, B nhưng không NẰM TRONG A hay B.
   *   `null`/vắng là câu trả lời hợp lệ; cây phân rã treo vật ấy vào nhóm.
   * `display_group` — nhiều nhóm, do backend dẫn xuất từ vai trò.
   * `visual_transform` — chỉ không gian TRÌNH BÀY. Backend luôn phát đồng nhất
   *   thức; bung hình là thao tác của người xem và sống ở `InteractionState`.
   * `source` — đủ để trả lời *"vật này ở đâu ra"* khi soi, không hơn.
   *
   * Cùng khai `?` vì envelope cũ (lưu trước wave này) không có chúng.
   */
  parent?: string | null;
  display_group?: string[];
  visual_transform?: VisualTransform;
  source?: SceneSource;
  xyz?: ExactVec3;
  point?: ExactVec3;
  direction?: ExactVec3;
  normal?: ExactVec3;
  vertices?: ExactVec3[];
  /**
   * Id ĐIỂM NGỮ NGHĨA theo ĐÚNG VỊ TRÍ của `vertices` — `faces[i][j]` là chỉ
   * số vào đây. `depends` không thay được: nó đã bị sắp theo thứ tự chữ.
   */
  vertex_ids?: string[];
  faces?: number[][];
  polygon?: ExactVec3[];
  closed?: boolean;
  /**
   * HÌNH CONG — tham số ngữ nghĩa, **không phải lưới**.
   *
   * `curved_kind` là hình nào (`ball` · `cylinder` · `cone`); `anchor` là tâm
   * (cầu) hay tâm đáy; `apex_or_top` là đỉnh nón / tâm đáy kia và **vắng với
   * khối cầu**; `rim_point` là một điểm trên mặt hoặc trên vành đáy.
   *
   * ⚠️ Cố ý **không có `vertices`/`faces`** ở nhóm này. Renderer chia lưới để
   * VẼ, và lưới ấy không có ô nào để đi ngược lên phép đo hay checker — bảo
   * đảm bằng CẤU TRÚC chứ không bằng một lời dặn. Bán kính đến dưới dạng
   * `radius_sq` (chuỗi phân số) để số chính xác không mất mát trên đường dây.
   */
  curved_kind?: string;
  anchor?: ExactVec3;
  apex_or_top?: ExactVec3 | null;
  rim_point?: ExactVec3;
  center?: ExactVec3;
  radius_sq?: Exact;
  height_sq?: Exact;
  /**
   * ELIP — hai PHƯƠNG trục và **bình phương** hai bán trục.
   *
   * Hai phương tới đây **chưa chuẩn hoá độ dài**: chuẩn hoá đá chúng ra khỏi
   * ℚ³, nên backend giữ nguyên vectơ hữu tỉ và việc ấy làm ở đây, cùng chỗ lấy
   * căn của `semi_*_sq`. Không có chúng thì renderer phải đoán elip xoay thế
   * nào trong mặt phẳng của nó — tức tự quyết một dữ kiện hình học.
   */
  major_dir?: ExactVec3;
  minor_dir?: ExactVec3;
  semi_major_sq?: Exact;
  semi_minor_sq?: Exact;
  /**
   * THIẾT DIỆN — mỗi bước là một CẠNH, kèm chỉ số mặt của khối sinh ra nó.
   *
   * Backend phát sẵn (`_TRUONG["section"]`); phía này bỏ quên mất suốt vì
   * `polygon` một mình đã đủ vẽ. Nhưng `face_index` là thứ trả lời *"cạnh này
   * nằm trên mặt nào"* — đúng câu học sinh phải trả lời khi dựng trên giấy —
   * và suy lại nó ở đây thì phải làm hình học, thứ tầng nhìn không được làm.
   */
  steps?: { face_index: number; a: ExactVec3; b: ExactVec3 }[];
  /**
   * ĐẠI LƯỢNG ĐO — chuỗi ĐÃ ĐỊNH DẠNG cho người đọc (`"√2"`, `"3√2/5"`).
   *
   * ⚠️ KHÔNG còn luôn là một phân số. Từ 2026-08-31 khoảng cách vô tỉ trả căn
   * thức, nên đừng bao giờ đẩy trường này qua `toNumber` — nó sẽ ném, và một
   * lần ném ở đây làm sập cả khung 3D (đúng sự cố `visual_transform` §128).
   * Cần con số thì đọc `exact`, cần vẽ thì đây không phải nguồn.
   */
  value?: Exact;
  /**
   * CẤU TRÚC của đại lượng — nguồn, còn `value` là dẫn xuất.
   *
   * Có nó thì phía này định dạng lại được theo ngữ cảnh (đáp số nổi trên hình
   * vs. dòng "Chi tiết" trong ô soi) mà không phải đọc ngược một chuỗi có ký
   * tự toán học. Khai `?` vì envelope lưu trước wave này không có.
   */
  exact?: ExactNumberJson;
}

/**
 * Số chính xác do backend phát — mirror của `geometry/radical.to_json`.
 *
 * Hai nhánh, không hơn: hữu tỉ và `hệ·√căn`. Miền số cố ý hẹp (không tổng nhiều
 * căn), nên kiểu ở đây cũng hẹp — một `kind` thứ ba xuất hiện nghĩa là backend
 * đã mở miền mà phía này chưa biết, và `hienSo` sẽ nói thẳng thay vì đoán.
 */
export type ExactNumberJson =
  | { kind: "rational"; value: string }
  | {
      kind: "radical";
      coefficient: string;
      radicand: number;
      /**
       * Số mũ của π — `0` hoặc `1` (`radical.PI_EXPONENT_DOMAIN`).
       *
       * **VẮNG ⇒ 0, và mặc định ấy do BACKEND quy ước**, không phải phía này
       * tự nghĩ ra: `radical.to_json` cố ý bỏ trường khi `mu === 0` để mọi
       * payload sinh trước 2026-09-03 giữ nguyên **từng byte**. Phía đọc chỉ
       * lặp lại hợp đồng đã viết ở `from_json`.
       */
      pi?: number;
    };

/**
 * Định dạng số chính xác theo cách viết SGK: `√2`, `3√2`, `3√2/5`, `-√3/2`,
 * và từ 2026-09-03 thêm `π`, `2π`, `π√5`, `4π√3/3`.
 *
 * Đọc CẤU TRÚC, không đọc chuỗi backend đã dựng — hai bên định dạng độc lập là
 * cách duy nhất phát hiện khi chúng lệch nhau. `duPhong` dùng cho envelope cũ
 * (chưa có `exact`) và cho `kind` lạ: nói thẳng thứ nhận được, không đoán.
 *
 * ⚠️ `√căn` bị **ẩn** khi `radicand === 1`. Trước khi có π điều ấy không xảy ra
 * được — backend trả `Fraction` cho mọi giá trị hữu tỉ — nhưng `2π` có
 * `radicand === 1` mà vẫn là căn thức, và in `2π√1` là in một thứ không ai
 * viết. Cùng luật với `radical.display`, hai bên dựng độc lập.
 */
export function hienSo(x: ExactNumberJson | undefined, duPhong = ""): string {
  if (!x) return duPhong;
  if (x.kind === "rational") return x.value;
  if (x.kind !== "radical") return duPhong;
  const [tuRaw, mauRaw] = x.coefficient.split("/");
  const tu = Number(tuRaw);
  const mau = mauRaw === undefined ? 1 : Number(mauRaw);
  if (!Number.isFinite(tu) || !Number.isFinite(mau)) return duPhong;
  const mu = x.pi ?? 0;
  // Miền số mũ đóng ở `{0, 1}`. Giá trị khác nghĩa là backend đã mở miền mà
  // phía này chưa biết — nói thẳng thay vì in một công thức sai.
  if (mu !== 0 && mu !== 1) return duPhong;
  const dau = tu < 0 ? "-" : "";
  const heSo = Math.abs(tu) === 1 ? "" : String(Math.abs(tu));
  const pi = mu === 1 ? "π" : "";
  const can = x.radicand === 1 ? "" : `√${x.radicand}`;
  const goc = `${dau}${heSo}${pi}${can}`;
  return mau === 1 ? goc : `${goc}/${mau}`;
}

/**
 * `VisualVec3` — KHÔNG GIAN TRÌNH BÀY, tách hẳn khỏi `ExactVec3`.
 *
 * ─── VÌ SAO PHẢI LÀ HAI KIỂU, KHÔNG PHẢI MỘT ────────────────────────────
 *
 * Bản đầu khai `visual_transform.translate` là `ExactVec3` — chuỗi phân số —
 * "cho đồng bộ". Demo trong Chrome thật cho thấy cái giá: `visualTransformOf`
 * sinh `"0.244949"`, `toNumber` ném đúng như nó phải ném, và **cả khung 3D
 * sập**. 1674 test vitest không bắt được, vì chúng chỉ so các
 * `visual_transform` với NHAU, chưa lần nào đẩy một cái qua `toNumber`.
 *
 * Bài học không phải "ép số thập phân thành phân số". Hai không gian này khác
 * nhau về BẢN CHẤT:
 *
 *   `ExactVec3`  toạ độ TOÁN HỌC — `GeometryState`, kernel, checker, phép đo.
 *                Phải chính xác tuyệt đối: đó là thứ phân biệt hệ này với một
 *                bộ vẽ hình.
 *   `VisualVec3` khoảng dịch TRÌNH BÀY — bung hình, lệch hiển thị. `0.244949`
 *                hoàn toàn hợp lệ ở đây; làm tròn nó không sai một mệnh đề
 *                toán nào, vì nó chưa bao giờ là một mệnh đề toán.
 *
 * ⚠️ `VisualVec3` **không được đi vào** kernel, checker, hay phép đo. Ranh
 * giới ấy là lý do tồn tại của kiểu này.
 */
export type VisualVec3 = [number, number, number];

export interface VisualTransform {
  translate: VisualVec3;
  scale: number;
}

/** Số dùng được cho trình bày: hữu hạn. `NaN`/`Infinity` thì KHÔNG. */
export function laSoTrinhBayHopLe(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

/** Xuất xứ NGẮN cho ô soi. Không chở prompt, không chở lời giải. */
export interface SceneSource {
  fact_id?: string;
  assumption?: string;
  instruction?: string;
}

export const BIEN_DOI_DONG_NHAT: VisualTransform = {
  translate: [0, 0, 0],
  scale: 1,
};

export type EventAction = "INIT" | "CREATE" | "EXTEND" | "MEASURE" | "STEP";

export interface SceneEvent {
  step_index: number;
  action: EventAction;
  object: string | null;
  depends: string[];
  explanation: string;
}

export interface Scene3D {
  objects: SceneObject[];
  events: SceneEvent[];
  free_objects: string[];
}

/**
 * Chuỗi phân số → `number`. **Chỗ duy nhất** float xuất hiện.
 *
 * `"1/2"` → `0.5`, `"-3/4"` → `-0.75`, `"2"` → `2`. Không dùng `eval` cũng
 * không `Number("1/2")` (trả `NaN`) — tách tử/mẫu tường minh.
 *
 * Chuỗi hỏng ném lỗi thay vì trả `NaN`: một `NaN` lọt vào buffer của three.js
 * làm cả mesh biến mất **không báo gì**, và truy ngược từ một khung hình trống
 * về một chuỗi sai là chỗ tốn nhiều giờ nhất.
 */
export function toNumber(s: Exact): number {
  const t = String(s).trim();
  const m = /^(-?\d+)(?:\/(\d+))?$/.exec(t);
  if (!m) throw new Error(`Toạ độ không phải phân số hợp lệ: ${JSON.stringify(s)}`);
  const tu = Number(m[1]);
  const mau = m[2] === undefined ? 1 : Number(m[2]);
  if (mau === 0) throw new Error(`Mẫu số bằng 0: ${JSON.stringify(s)}`);
  return tu / mau;
}

export function toVec3(v: ExactVec3): Vec3 {
  return [toNumber(v[0]), toNumber(v[1]), toNumber(v[2])];
}

/** Số bước của mô phỏng. `0` khi cảnh chưa có sự kiện nào. */
export function stepCount(scene: Scene3D): number {
  return scene.events.length;
}

export function clampStep(scene: Scene3D, step: number): number {
  const n = stepCount(scene);
  if (n === 0) return 0;
  return Math.min(Math.max(Math.trunc(step), 0), n - 1);
}

/**
 * Những đối tượng ĐÃ TỒN TẠI tại bước `step`.
 *
 * ─── VÌ SAO TÍNH TỪ `events`, KHÔNG TỪ `objects` ────────────────────────
 *
 * `objects` là trạng thái CUỐI — mọi thứ đã dựng xong. Chiếu thẳng nó ra màn
 * hình thì học sinh thấy ngay hình hoàn chỉnh, và toàn bộ mục tiêu sư phạm
 * (*"một hình được hình thành như thế nào"*) biến mất.
 *
 * `events` mang thứ tự dựng thật, một sự kiện cho đúng một bước (bất biến #31).
 * Nên tập hiện ra ở bước `k` = mọi đối tượng có sự kiện tạo nó ở bước ≤ `k`,
 * cộng các đối tượng TỰ DO (điểm gốc của hệ trục) vốn có mặt từ bước `INIT`.
 */
export function objectsAt(scene: Scene3D, step: number): SceneObject[] {
  const k = clampStep(scene, step);
  const hien = new Set(scene.free_objects);
  for (const e of scene.events) {
    if (e.step_index > k) break;
    if (e.object) hien.add(e.object);
  }
  return scene.objects.filter((o) => hien.has(o.id));
}

/**
 * Tiến trình DỰNG của một vật tại một bước.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * `objectsAt` quy mọi sự kiện về một câu hỏi nhị phân: *"vật này đã xuất hiện
 * chưa"*. Với thiết diện thì câu hỏi ấy thiếu một nửa. Trace của ca
 * `S.ABCD ∩ (MNP)` có **bốn** sự kiện `EXTEND` — mỗi sự kiện nối thêm một
 * cạnh, kèm cả `face_index` trong `object.steps` — rồi mới tới sự kiện `STEP`
 * đóng hình. Renderer trước bản này dựng trọn `polygon` ngay từ sự kiện đầu,
 * nên **năm bước cuối cho năm khung hình trùng khít nhau** (đo được: cùng băm
 * ảnh, cùng 4186 điểm mực), trong khi lời dẫn vẫn đang kể từng cạnh một.
 *
 * `EventAction` đã khai `"EXTEND"` từ đầu và **không dòng mã nào đọc nó**. Đây
 * là chỗ đọc.
 *
 * ⚠️ `soCanh === null` nghĩa là vật KHÔNG dựng luỹ tiến (không có sự kiện
 * `EXTEND` nào) ⇒ nơi gọi giữ nguyên hành vi cũ. Không suy ra "0 cạnh".
 */
export interface TienTrinhDung {
  /** Số cạnh đã được nối tính tới bước này; `null` khi vật không dựng luỹ tiến. */
  soCanh: number | null;
  /** Sự kiện ĐÓNG HÌNH đã xảy ra chưa — mảng tô chỉ xuất hiện từ đó. */
  daDong: boolean;
}

export function tienTrinhDung(
  scene: Scene3D, id: string, step: number,
): TienTrinhDung {
  const k = clampStep(scene, step);
  let soCanh: number | null = null;
  let daDong = false;
  for (const e of scene.events) {
    if (e.object !== id) continue;
    if (e.step_index > k) break;
    if (e.action === "EXTEND") soCanh = (soCanh ?? 0) + 1;
    else if (e.action === "STEP" && soCanh !== null) daDong = true;
  }
  /* Vật có `EXTEND` ở bước SAU bước đang xem vẫn là vật dựng luỹ tiến — nếu
   * không khai điều đó, bước 6/11 (mặt phẳng vừa dựng, thiết diện chưa có
   * cạnh nào) sẽ rơi về hành vi cũ và vẽ trọn miếng cắt. */
  if (soCanh === null && scene.events.some((e) => e.object === id && e.action === "EXTEND")) {
    soCanh = 0;
  }
  return { soCanh, daDong };
}

/** Đối tượng vừa được tạo/kéo dài ở bước này — dùng để làm nổi bật. */
export function highlightedAt(scene: Scene3D, step: number): string[] {
  const k = clampStep(scene, step);
  const e = scene.events.find((x) => x.step_index === k);
  if (!e || !e.object) return [];
  return [e.object, ...e.depends];
}

/** Lời kể của bước hiện tại — Tier 1, do engine sinh từ trạng thái thật. */
export function narrationAt(scene: Scene3D, step: number): string {
  const e = scene.events.find((x) => x.step_index === clampStep(scene, step));
  return e ? e.explanation : "";
}

/**
 * Kích thước hiển thị của mặt phẳng và độ dài nửa đoạn của đường thẳng.
 *
 * `plane3` và `line3` là **VÔ HẠN** — backend cố ý không gửi biên, vì cắt chúng
 * là quyết định TRÌNH BÀY. Hai hằng dưới đây là quyết định ấy, và chúng thuộc
 * renderer: đổi chúng không đổi một mệnh đề toán học nào.
 */
export const PLANE_DISPLAY_SIZE = 6;

/**
 * Lề quanh vùng hình học liên quan khi cắt một mặt phẳng vô hạn thành miếng.
 *
 * Miếng phải **phủ hết** vùng đáng nhìn rồi thừa ra một chút, để mắt đọc được
 * "mặt phẳng cắt qua khối" chứ không phải "một tấm ván dựng cạnh khối".
 */
export const PLANE_PATCH_MARGIN = 1.15;

/** Cạnh tối thiểu của miếng mặt phẳng — chặn ca cảnh suy biến về một điểm. */
export const PLANE_PATCH_MIN_SIZE = 2;

/**
 * BỀ DÀY NÉT của thiết diện cong, theo tỉ lệ đường kính cảnh.
 *
 * ⚠️ Vì sao không để `THREE.Line` mặc định: WebGL bỏ qua `linewidth`, nên mọi
 * đường luôn dày đúng **một** điểm ảnh. Đo được: đường tròn thiết diện của
 * `p3` chiếm **6 điểm ảnh có màu** trên cả khung 1318×545 — về mặt kỹ thuật
 * "có vẽ", về mặt người học là không nhìn thấy. Thiết diện là *câu trả lời của
 * bài*, nên nó phải là thứ đập vào mắt trước tiên.
 *
 * Bề dày tính theo cảnh chứ không theo điểm ảnh: cùng một hình, phóng to hay
 * thu nhỏ thì nét vẫn cân đối với hình, và không phụ thuộc độ phân giải.
 */
export const SECTION_STROKE_RATIO = 0.014;

/** Đường kính cảnh, dùng để suy các cỡ trình bày. `0` khi không có điểm nào. */
export function duongKinhCanh(diem: Vec3[]): number {
  if (diem.length === 0) return 0;
  const lo: Vec3 = [Infinity, Infinity, Infinity];
  const hi: Vec3 = [-Infinity, -Infinity, -Infinity];
  for (const p of diem) {
    for (let i = 0; i < 3; i++) {
      if (!Number.isFinite(p[i])) return 0;
      if (p[i] < lo[i]) lo[i] = p[i];
      if (p[i] > hi[i]) hi[i] = p[i];
    }
  }
  return Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]);
}

/**
 * ĐIỂM CÓ BIÊN của cảnh — bỏ mọi vật VÔ HẠN.
 *
 * ⚠️ Vì sao cần: `plane3` và `line3` không có biên, nên thứ renderer vẽ cho
 * chúng là một **miếng đại diện** do tầng trình bày tự chọn cỡ. Đưa miếng ấy
 * vào phép tính khung nhìn là để một quyết định trình bày tự khuếch đại chính
 * nó: mặt phẳng to ra ⇒ hộp bao to ra ⇒ camera lùi ⇒ khối thật bé lại.
 *
 * `plane3.point` cũng bị bỏ, và đó là điểm tinh: nó là **một điểm bất kỳ** trên
 * mặt phẳng, không phải một điểm của hình. Ở `p7` nó nằm ở `(9,0,0)` — ngoài
 * hẳn hình nón bán kính 6.
 */
/** Hai phương đơn vị vuông góc với `u` (và với nhau). `u` phải đã chuẩn hoá. */
function truc_vuong_goc(u: Vec3): Vec3[] {
  // Chọn trục toạ độ ÍT song song với `u` nhất để tích có hướng không suy biến.
  const t: Vec3 = Math.abs(u[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
  const a: Vec3 = [
    u[1] * t[2] - u[2] * t[1], u[2] * t[0] - u[0] * t[2], u[0] * t[1] - u[1] * t[0],
  ];
  const da = Math.hypot(...a) || 1;
  const a1: Vec3 = [a[0] / da, a[1] / da, a[2] / da];
  const b: Vec3 = [
    u[1] * a1[2] - u[2] * a1[1], u[2] * a1[0] - u[0] * a1[2],
    u[0] * a1[1] - u[1] * a1[0],
  ];
  return [a1, b];
}

export function diemHuuHan(objects: SceneObject[]): Vec3[] {
  const ra: Vec3[] = [];
  const them = (v?: ExactVec3 | null) => { if (v) ra.push(toVec3(v)); };
  for (const o of objects) {
    if (o.render === "surface" || o.render === "line") continue;
    them(o.xyz); them(o.center); them(o.anchor); them(o.apex_or_top);
    them(o.rim_point);
    for (const v of o.vertices ?? []) them(v);
    for (const v of o.polygon ?? []) them(v);
    // Khối cong: bán kính nở ra theo hai phương ⟂ TRỤC. Chỉ có `rim_point` thì
    // hộp bao chỉ ôm được một phía của khối.
    //
    // ⚠️ Nở theo cả ba trục toạ độ là SAI, và sai đo được: với hình nón cao 12
    // bán kính 5, nó thêm ±5 **dọc trục** nên hộp bao cao 22 thay vì 12, và
    // camera lùi ra tới mức hình chỉ còn chiếm 21% khung. Bán kính vuông góc
    // với trục, nên phép nở cũng phải vuông góc với trục.
    if (o.radius_sq && o.anchor) {
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
      const c = toVec3(o.anchor);
      const dinh = o.apex_or_top ? toVec3(o.apex_or_top) : c;
      const truc: Vec3 = [dinh[0] - c[0], dinh[1] - c[1], dinh[2] - c[2]];
      const dai = Math.hypot(...truc);
      // Khối cầu (`apex_or_top` vắng) không có trục ⇒ nở đều theo ba trục.
      const phuong: Vec3[] = dai === 0
        ? [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        : truc_vuong_goc([truc[0] / dai, truc[1] / dai, truc[2] / dai]);
      for (const t of [c, dinh]) {
        for (const u of phuong) {
          ra.push([t[0] + u[0] * r, t[1] + u[1] * r, t[2] + u[2] * r]);
          ra.push([t[0] - u[0] * r, t[1] - u[1] * r, t[2] - u[2] * r]);
        }
      }
    }
    // Elip: hai bán trục, mỗi phương hai đầu.
    if (o.center && o.major_dir && o.minor_dir && o.semi_major_sq && o.semi_minor_sq) {
      const c = toVec3(o.center);
      for (const [d, sq] of [[o.major_dir, o.semi_major_sq],
        [o.minor_dir, o.semi_minor_sq]] as const) {
        const v = toVec3(d);
        const len = Math.hypot(v[0], v[1], v[2]) || 1;
        const k = Math.sqrt(Math.max(0, toNumber(sq))) / len;
        ra.push([c[0] + v[0] * k, c[1] + v[1] * k, c[2] + v[2] * k]);
        ra.push([c[0] - v[0] * k, c[1] - v[1] * k, c[2] - v[2] * k]);
      }
    }
  }
  return ra;
}

/**
 * MIẾNG MẶT PHẲNG đặt và định cỡ quanh vùng hình học liên quan.
 *
 * ─── LỖI ĐƯỢC SỬA, ĐO ĐƯỢC ────────────────────────────────────────────
 *
 * Trước bản này miếng là một ô vuông `PLANE_DISPLAY_SIZE` **cố định**, đặt tại
 * `plane3.point`. Ở `p7`, `point = (9,0,0)` còn thiết diện elip ở `(1,0,8)` —
 * cách nhau **11,3** đơn vị trong khi nửa đường chéo miếng chỉ **4,24**. Miếng
 * không chạm tới thiết diện, và ảnh trình duyệt đọc ra đúng như vậy: một tấm
 * vuông trôi bên cạnh hình nón, không liên quan gì tới elip.
 *
 * Toán học vẫn đúng — `point` đúng là một điểm trên mặt phẳng, `normal` đúng.
 * Sai ở chỗ **chọn phần nào của một mặt phẳng vô hạn để vẽ**, và đó là quyết
 * định của tầng trình bày.
 *
 * ─── QUY TẮC, DÙNG CHUNG CHO MỌI CA ───────────────────────────────────
 *
 * Chiếu mọi điểm có biên của cảnh xuống mặt phẳng, lấy tâm là tâm của hình
 * chiếu, cạnh là đường kính hình chiếu nhân lề. Không ca nào được nêu tên.
 *
 * Trả `null` khi cảnh không có điểm hữu hạn nào — nơi gọi rơi về cỡ cố định.
 */
export function khungMatPhang(
  diemMp: Vec3, phapTuyen: Vec3, diem: Vec3[],
): { tam: Vec3; canh: number } | null {
  const n = Math.hypot(...phapTuyen);
  if (!Number.isFinite(n) || n === 0 || diem.length === 0) return null;
  const u: Vec3 = [phapTuyen[0] / n, phapTuyen[1] / n, phapTuyen[2] / n];

  const chieu = diem.map((p): Vec3 => {
    const t = (p[0] - diemMp[0]) * u[0] + (p[1] - diemMp[1]) * u[1]
      + (p[2] - diemMp[2]) * u[2];
    return [p[0] - t * u[0], p[1] - t * u[1], p[2] - t * u[2]];
  });

  const lo: Vec3 = [Infinity, Infinity, Infinity];
  const hi: Vec3 = [-Infinity, -Infinity, -Infinity];
  for (const p of chieu) {
    for (let i = 0; i < 3; i++) {
      if (!Number.isFinite(p[i])) return null;
      if (p[i] < lo[i]) lo[i] = p[i];
      if (p[i] > hi[i]) hi[i] = p[i];
    }
  }
  const tam: Vec3 = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2];
  /* ⚠️ BỀ RỘNG LẤY TỪ HÌNH CHIẾU, KHÔNG TỪ BÁN KÍNH NGOẠI TIẾP — cùng bài học
   * đã học ở camera (`scene3d-camera.ts`).
   *
   * Bản trước lấy `banKinh` = khoảng cách xa nhất từ tâm tới một điểm chiếu,
   * rồi đặt CẠNH ô vuông bằng `2·banKinh·lề`. Nhưng một ô vuông cạnh `S` có
   * nửa đường chéo `0,71·S`, nên bốn góc miếng vươn tới `1,63·` bề rộng thật
   * của cụm điểm — trong khi camera chỉ khớp khung cho chính cụm điểm ấy. Kết
   * quả đo được ở p7: miếng mặt phẳng **chạy khỏi mép dưới canvas**.
   *
   * Nay cạnh lấy từ bề rộng hình chiếu lớn nhất: ô vuông vẫn phủ trọn cụm điểm
   * (cạnh ≥ mỗi bề rộng) nhưng không phình theo đường chéo. */
  const beRong = Math.max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]);
  const canh = Math.max(PLANE_PATCH_MIN_SIZE, beRong * PLANE_PATCH_MARGIN);
  return Number.isFinite(canh) ? { tam, canh } : null;
}

/**
 * Số cạnh khi CHIA LƯỚI một mặt cong để vẽ.
 *
 * ⚠️ Đây là con số của TRÌNH BÀY, và nó không mang một mệnh đề toán học nào:
 * đổi nó không đổi một phép đo, một checker hay một kết quả nào. Ngữ nghĩa của
 * khối cong là ba điểm neo mà backend gửi; lưới chỉ là cách nhìn thấy chúng.
 *
 * Đặt cạnh `PLANE_DISPLAY_SIZE` — cùng loại hằng số, cùng lý do tồn tại.
 */
export const VONG_CHIA = 48;
export const LINE_DISPLAY_HALF_LENGTH = 6;

/**
 * ĐOẠN ĐẠI DIỆN của một đường thẳng vô hạn, cắt quanh vùng hình học liên quan.
 *
 * Cùng một lẽ với `khungMatPhang`: `line3` **vô hạn**, hai đầu mút là quyết
 * định TRÌNH BÀY chứ không phải một mệnh đề toán học. Trước bản này nửa chiều
 * dài là hằng `LINE_DISPLAY_HALF_LENGTH = 6` cho mọi cảnh, nên ở `p1` đường
 * `BD` **chạy thẳng ra ngoài khung** — ảnh sản phẩm đọc được đúng thế: một nét
 * xám đi khỏi mép dưới canvas mà không dẫn tới đâu. Cảnh to hơn thì ngược lại,
 * đoạn ngắn quá và đường không chạm tới vật nó đi qua.
 *
 * Quy tắc, dùng chung mọi ca: chiếu điểm có biên của cảnh lên đường thẳng, lấy
 * tâm là giữa khoảng tham số và nửa chiều dài là nửa khoảng ấy nhân lề. Không
 * ca nào được nêu tên.
 *
 * Trả `null` khi cảnh không có điểm hữu hạn nào — nơi gọi rơi về hằng cũ.
 */
export function khungDuongThang(
  diemDt: Vec3, huong: Vec3, diem: Vec3[],
): { tam: Vec3; nua: number } | null {
  const n = Math.hypot(...huong);
  if (!Number.isFinite(n) || n === 0 || diem.length === 0) return null;
  const u: Vec3 = [huong[0] / n, huong[1] / n, huong[2] / n];

  let lo = Infinity, hi = -Infinity;
  for (const p of diem) {
    const t = (p[0] - diemDt[0]) * u[0] + (p[1] - diemDt[1]) * u[1]
      + (p[2] - diemDt[2]) * u[2];
    if (!Number.isFinite(t)) return null;
    if (t < lo) lo = t;
    if (t > hi) hi = t;
  }
  const giua = (lo + hi) / 2;
  const nua = Math.max(LINE_PATCH_MIN_HALF, ((hi - lo) / 2) * LINE_PATCH_MARGIN);
  if (!Number.isFinite(nua)) return null;
  return {
    tam: [diemDt[0] + giua * u[0], diemDt[1] + giua * u[1], diemDt[2] + giua * u[2]],
    nua,
  };
}

/** Lề quanh khoảng chiếu, để đường thẳng nhô ra khỏi vật nó đi qua. */
const LINE_PATCH_MARGIN = 1.15;
/** Nửa chiều dài tối thiểu — cảnh suy biến về một điểm vẫn phải thấy đường. */
const LINE_PATCH_MIN_HALF = 1.5;

/* ══ PHÁT LẠI — hàm THUẦN, không React, không three ══════════════════════
 *
 * Người học điều khiển **thời gian quan sát** và **góc nhìn**. Không điều khiển
 * nội dung toán học. Nên toàn bộ "tương tác" của Phase 5E rút gọn thành: đổi
 * MỘT SỐ NGUYÊN `step`.
 *
 * Đó là lý do nhóm hàm này thuần và nhỏ: nếu playback cần biết gì về hình học
 * thì thiết kế đã sai chỗ nào đó.
 */

export function isFirstStep(scene: Scene3D, step: number): boolean {
  return clampStep(scene, step) <= 0;
}

export function isLastStep(scene: Scene3D, step: number): boolean {
  const n = stepCount(scene);
  return n === 0 || clampStep(scene, step) >= n - 1;
}

export function nextStep(scene: Scene3D, step: number): number {
  return clampStep(scene, clampStep(scene, step) + 1);
}

export function prevStep(scene: Scene3D, step: number): number {
  return clampStep(scene, clampStep(scene, step) - 1);
}

/** Đối tượng đang được dựng ở bước này, và những thứ nó phụ thuộc. */
export function focusAt(
  scene: Scene3D,
  step: number,
): { created: string | null; depends: string[] } {
  const e = scene.events.find((x) => x.step_index === clampStep(scene, step));
  return { created: e?.object ?? null, depends: e ? [...e.depends] : [] };
}

/**
 * Người dùng đã bật "giảm chuyển động" ở hệ điều hành chưa?
 *
 * ─── VÌ SAO CẦN Ở TẦNG JS, DÙ W13-A11Y ĐÃ LÀM Ở CSS ────────────────────
 *
 * Khối `@media (prefers-reduced-motion: reduce)` trong `global.css` tắt được
 * `animation`/`transition` — tức hoạt cảnh do **CSS** phát. Tự động chạy các
 * bước dựng là hoạt cảnh do **JavaScript** phát: nó đổi nội dung khung hình
 * theo nhịp, và không luật CSS nào chạm tới được.
 *
 * Bỏ qua chỗ này thì người bật giảm-chuyển-động vẫn nhận đúng thứ họ đã tắt,
 * chỉ khác đường đi.
 *
 * SSR-an toàn: không có `window`/`matchMedia` ⇒ trả `false` (không tự suy diễn
 * sở thích của một người chưa có mặt).
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/** Nhịp phát mặc định (ms/bước). Đủ chậm để đọc được lời kể của bước. */
export const PLAYBACK_INTERVAL_MS = 1400;
