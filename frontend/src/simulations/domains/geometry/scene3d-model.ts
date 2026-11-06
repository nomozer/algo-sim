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

const EPS_CHART_SPD = 1e-12;

export function hopLeChartMetric(chart_metric: unknown): boolean {
  if (chart_metric == null) return true;
  if (
    !Array.isArray(chart_metric) ||
    chart_metric.length !== 3 ||
    chart_metric.some((row) => !Array.isArray(row) || row.length !== 3)
  ) {
    return false;
  }
  const G: number[][] = [];
  for (const r of chart_metric) {
    const row: number[] = [];
    for (const cell of r) {
      if (typeof cell !== "string" || cell.trim() === "") return false;
      try {
        const val = toNumber(cell);
        if (!Number.isFinite(val)) return false;
        row.push(val);
      } catch {
        return false;
      }
    }
    G.push(row);
  }
  for (let i = 0; i < 3; i++) {
    for (let j = i + 1; j < 3; j++) {
      if (Math.abs(G[i][j] - G[j][i]) > EPS_CHART_SPD) return false;
    }
  }
  const d0 = G[0][0];
  if (!(d0 > EPS_CHART_SPD)) return false;
  const l00 = Math.sqrt(d0);
  const l10 = G[1][0] / l00;
  const l20 = G[2][0] / l00;
  const d1 = G[1][1] - l10 * l10;
  if (!(d1 > EPS_CHART_SPD)) return false;
  const l11 = Math.sqrt(d1);
  const l21 = (G[2][1] - l20 * l10) / l11;
  const d2 = G[2][2] - l20 * l20 - l21 * l21;
  return d2 > EPS_CHART_SPD;
}

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
 * việc **kiểm tại chỗ nhận**. Module dùng guard này trước khi chấp nhận
 * envelope; shell dùng lại để chọn bố cục. Cảnh đã gửi nhưng hỏng không
 * được nhận như một mô phỏng 2D hợp lệ.
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
    Array.isArray(s.free_objects) &&
    hopLeChartMetric(s.chart_metric)
  );
}

export const RENDER_KINDS = [
  "point_marker",
  "line",
  "segment",
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
  /** Nhãn learner-facing lặp lại tường minh tại biên transport. */
  display_label?: string;
  /** Chủ sở hữu nét thật, proxy bắt chuột, measurement hoặc non-visual. */
  /** `presentation_reference`: frontend-only (the sphere's reference equator, `sphere_reference:*`) — never sent by the
   *  backend; drawn as an auxiliary curve, lighter and thinner than real rims. */
  display_role?: "visual_owner" | "hit_proxy" | "measurement" | "non_visual" | "presentation_reference";
  type: string;
  render: RenderKind;
  origin: "free" | "derived";
  producer: string | null;
  depends: string[];
  dependency_edges?: DependencyEdge[];
  formula?: LearnerFormula;
  /** Canonical machine topology. Learner notation never appears in these ids. */
  edge_ownership?: LogicalEdgeOwnership[];
  surfaces?: CanonicalSurface[];
  boundary_edge_ids?: string[];
  /** regular-square-pyramid-w04: đoạn CON nằm trên cạnh chuẩn (backend kiểm chính xác) — khúc [t0, t1] từ `edge.a`. */
  edge_span?: { edge_id: string; t0: number; t1: number };
  /** Vai trò dựng hình của vật (formation W14, backend) — W2 · D đọc `CONSTRUCT_AUXILIARY_GEOMETRY`. */
  formation_roles?: string[];
  /** Lớp hình của khối (backend `formation.lop_khoi`): `PYRAMID_LIKE` · `PRISM_LIKE` · `SECTION`. */
  shape_class?: string;
  surface_role?: SurfaceRole;
  /** Vai trò ngữ nghĩa toán học tường minh (tương thích ngược: vắng mặt sẽ xác định tất định từ dữ liệu hình học đã xác minh). */
  semantic_role?:
    | "SOLID_SHELL"
    | "BOUNDARY_AND_INTERSECTION"
    | "HIDDEN_EDGE"
    | "RESULT_SECTION"
    | "GEOMETRIC_PLANE"
    | "INSCRIBED_CIRCLE"
    | "CIRCUMSCRIBED_CIRCLE"
    | "INSCRIBED_SPHERE"
    | "CIRCUMSCRIBED_SPHERE"
    | "STANDALONE_SPHERE"
    | "REFERENCE_EQUATOR"
    | "REFERENCE_GREAT_CIRCLE"
    | "CERTIFIED_RELATION_MARKER"
    | "AUXILIARY_CONSTRUCTION";
  /** `false` khi vật chỉ là tham chiếu/phụ trợ giải thích ở tầng trình bày, không phải dữ kiện đề cho hay vật thẩm quyền của Kernel. */
  authoritative?: boolean;
  occludes_edges?: boolean;
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
  point_a?: ExactVec3;
  point_b?: ExactVec3;
  endpoints?: ExactVec3[];
  endpoint_ids?: string[];
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
  /** Tầng trình bày chép từ `geometry_progress`: viền đã khép nhưng mặt chưa tô. */
  fill_visible?: boolean;
  /** Bí danh của đáp số (backend `_danh_dau_bi_danh`): MỘT kết luận với nguồn này. */
  alias_of?: string;
  /**
   * W17 §15.4 — CHỦ THỂ của một đại lượng, do backend gắn (`quantity_annotations`). Vắng ⇒
   * đại lượng không có nhãn trên hình (vẫn ở bảng lời giải). Phía này không bao giờ suy chủ thể
   * từ tên biến (`AB_length`) và không tự tính giá trị.
   */
  annotation?: QuantityAnnotation;
  /** Review I1 — điểm dựng bằng hình chiếu vuông góc: đoạn vuông góc PHỤ từ `from` tới chân (= chính điểm này) +
   *  hai phương ký hiệu vuông góc, do backend tính (cùng dạng `QuantityAnnotation.witness`). Không phải cạnh khối. */
  perpendicular_witness?: QuantityAnnotation["witness"];
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
  steps?: {
    face_index: number | null;
    a: ExactVec3;
    b: ExactVec3;
    parallel_face_edge?: [number, number] | number[] | null;
  }[];
  vertex_sources?: SectionVertexSource[];
  endpoint_entities?: SectionEndpointEntity[];
  identity_diagnostics?: string[];
  section_edge_coordinate_hashes?: Record<string, string>;
  /**
   * ĐẠI LƯỢNG ĐO — chuỗi ĐÃ ĐỊNH DẠNG cho người đọc (`"√2"`, `"3√2/5"`).
   *
   * ⚠️ KHÔNG còn luôn là một phân số. Từ 2026-08-31 khoảng cách vô tỉ trả căn
   * thức, nên đừng bao giờ đẩy trường này qua `toNumber` — nó sẽ ném, và một
   * lần ném ở đây làm sập cả khung 3D (đúng sự cố `visual_transform` §128).
   * Cần con số thì đọc `exact`, cần vẽ thì đây không phải nguồn.
   */
  value?: Exact;
  /** Biểu thức ký hiệu gốc của đề bài khi hình dựng dùng độ dài chuẩn hóa (vd `"2a"`, `"4a"`, `"2a + b"`). */
  symbolic?: string | null;
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

const GIA_TRI_DAI_LUONG_CHUA_BIET = new Set([
  "",
  "?",
  "unknown",
  "UNKNOWN",
  "undefined",
  "null",
  "NaN",
  "Infinity",
  "-Infinity",
]);

/** Kiểm tra đại lượng mang giá trị rỗng hoặc ký hiệu giữ chỗ chưa biết (`"?"`, `"unknown"`, `"NaN"`...). */
export function laGiaTriDaiLuongChuaBiet(raw: string | null | undefined): boolean {
  if (typeof raw !== "string") return true;
  const t = raw.trim();
  return t.length === 0 || GIA_TRI_DAI_LUONG_CHUA_BIET.has(t);
}

/**
 * Định dạng biểu thức có thẩm quyền của một đối tượng `quantity` mà không tính toán lại:
 * ưu tiên `symbolic` (biểu thức chứa tham số đề cho), kế đến cấu trúc chính xác `exact` (`hienSo`),
 * cuối cùng là `value`. Trả về `null` nếu thiếu giá trị hoặc là placeholder chưa biết.
 */
export function hienBieuThucDaiLuong(
  o: Pick<SceneObject, "symbolic" | "exact" | "value">,
): string | null {
  if (typeof o.symbolic === "string" && !laGiaTriDaiLuongChuaBiet(o.symbolic)) {
    return o.symbolic.trim();
  }
  if (o.exact) {
    const ex = hienSo(o.exact, typeof o.value === "string" ? o.value : "");
    return laGiaTriDaiLuongChuaBiet(ex) ? null : ex.trim();
  }
  if (typeof o.value === "string" && !laGiaTriDaiLuongChuaBiet(o.value)) {
    return o.value.trim();
  }
  return null;
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
export type FormationSemanticKind =
  | "GEOMETRY_CONSTRUCTION"
  | "MEASUREMENT"
  | "EXPLANATION"
  | "FINAL_RESULT"
  | "LEGACY_UNTYPED_EVENT";

export type DependencyRelation = "numerical" | "structural" | "topological" | "layout";

export interface DependencyEdge {
  source_id: string;
  relation: DependencyRelation;
}

export interface SectionVertexSource {
  kind: "SOLID_VERTEX" | "SOLID_EDGE_INTERSECTION" | string;
  solid_vertex_index?: number | null;
  solid_edge_vertex_indices?: number[] | null;
}

export interface SectionEndpointEntity {
  entity_id: string;
  section_vertex_ordinal: number;
  provenance_kind: string;
  coordinate_hash: string;
  anonymous_coordinate_fallback: boolean;
  display_label?: string;
}

export type SurfaceRole =
  | "SOLID_FACE"
  | "BASE_REGION"
  | "SECTION_REGION"
  | "CUTTING_PLANE"
  | "AUXILIARY_SURFACE";

export interface LogicalEdgeOwnership {
  edge_id: string;
  endpoint_ids: [string, string] | string[];
  adjacent_surface_ids: string[];
}

export interface CanonicalSurface {
  surface_id: string;
  vertex_indices: number[];
  boundary_edge_ids: string[];
  surface_role: SurfaceRole;
  occludes_edges: boolean;
}

export interface FormulaReference {
  entity_id: string;
  display_label: string;
  relation: "numerical";
}

export interface LearnerFormula {
  text: string;
  references: FormulaReference[];
}

export interface SceneEvent {
  step_index: number;
  action: EventAction;
  object: string | null;
  alias_object?: string | null;
  objects?: string[];
  retires?: string[];
  depends: string[];
  explanation: string;
  learner_text?: string;
  /** W4 · Vì sao của bước, chỉ khi backend KIỂM CHÍNH XÁC được quan hệ nó nêu (`details.justification`). */
  justification_text?: string | null;
  display_label?: string;
  details?: Record<string, unknown>;
  semantic_kind?: FormationSemanticKind;
  diagnostics?: string[];
}

export interface GeometryProgress {
  object_id: string;
  visible_edge_ids: string[];
  ordered_construction_ids: string[];
  closed: boolean;
  fill_visible: boolean;
}

export interface FormationStep {
  step_index: number;
  visible_ids: string[];
  focus_ids: string[];
  readout_ids: string[];
  learner_text: string;
  justification_text?: string | null;
  details?: Record<string, unknown>;
  semantic_kind?: FormationSemanticKind;
  geometry_progress?: GeometryProgress[];
}

export interface SceneFormation {
  steps: FormationStep[];
}

/** W17 §15.4 — gắn kết đại lượng ↔ chủ thể hình học (backend sở hữu nghĩa). */
export interface QuantityAnnotation {
  /** `angle` (2026-10-26): CHỈ góc đo được bằng 90°, neo bằng nhân chứng góc vuông backend (`_goc_vuong`). */
  kind: "length" | "area" | "volume" | "distance" | "angle";
  /** `result` = đích của đề (hoặc thứ một đích trỏ tới); còn lại `measurement`. */
  category: "measurement" | "result";
  /** W18 §16.5 — dữ kiện đề cho / trung gian / đáp số. Vắng (envelope v109) ⇒ suy từ `category` + `origin`. */
  role?: "given" | "intermediate" | "result";
  /** Id vật/điểm CÓ trong cảnh. */
  subject_ids: string[];
  anchor: "segment" | "region" | "solid" | "pair" | "witness";
  /** Chỉ khi payload có đơn vị. */
  unit?: string | null;
  /** W18 §16.6 — CÙNG một phép đo với đại lượng này (cùng chủ thể): không nhãn thứ hai, không dòng thứ hai. */
  same_as?: string;
  /** W18 §16.7 — nhân chứng khoảng cách điểm → đường/mặt phẳng: chân CHÍNH XÁC do backend tính, `u` dọc vật
   *  nhận, `v` từ chân tới điểm. Phía này chỉ vẽ — không bao giờ tự dựng chân đường vuông góc. */
  witness?: {
    from: string;
    foot: ExactVec3;
    on: string;
    /** `u_to` (Owner 2026-10-26): điểm CÓ TÊN trên vật nhận mà `u` chĩa tới — renderer vẽ đoạn chứng minh chân → điểm. */
    marker: { u: ExactVec3; v: ExactVec3; u_to?: string };
    certificate?: string | null;
    relation?: string;
    status?: string;
    rule?: string;
    foot_id?: string;
    can_present_as_proven?: boolean;
    /** Chứng chỉ đường ⊥ mặt (`exact-gram-line-plane-orthogonality/1`): hai phương độc lập của mặt phẳng. */
    plane_directions?: ExactVec3[];
    /** `relation: "common_perpendicular"` (khoảng cách hai đường chéo nhau): đầu kia của đoạn vuông góc chung không
     *  phải điểm có tên ⇒ toạ độ chính xác ở đây (`from` là id đường kia), và `second` là dấu vuông góc ở chân ấy. */
    from_point?: ExactVec3;
    second?: { foot: ExactVec3; on: string; foot_id?: string; marker: { u: ExactVec3; v: ExactVec3; u_to?: string } };
  };
}

export interface SceneLengthUnit {
  symbol: string;
  display_scale: string;
  is_given: boolean;
}

export interface Scene3D {
  objects: SceneObject[];
  events: SceneEvent[];
  free_objects: string[];
  formation?: SceneFormation;
  /** W17: chẩn đoán cho người phát triển (`ANNOTATION_UNBOUND …`) — không hiện cho học sinh. */
  diagnostics?: string[];
  /** exact-dimensions: metric KHUNG G (3×3 phân số) khi bố cục là khung affine — vắng ⇒ Euclid. `scene3d-chart`. */
  chart_metric?: Exact[][];
  /** HYBRID_PREVIEW_FRONTEND_CONTRACT §4: tỉ lệ dựng hình khi chuẩn hoá theo đơn vị độ dài ký hiệu (vd `a = 1 đơn vị dựng`). */
  length_unit?: SceneLengthUnit | null;
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
  return scene.formation?.steps.length ?? scene.events.length;
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
  const snapshot = scene.formation?.steps[k];
  if (snapshot) {
    const visible = new Set(snapshot.visible_ids);
    return scene.objects.filter((o) => visible.has(o.id));
  }
  const hien = new Set(scene.free_objects);
  for (const e of scene.events) {
    if (e.step_index > k) break;
    if (e.object) hien.add(e.object);
    if (Array.isArray(e.objects)) {
      for (const obj of e.objects) hien.add(obj);
    }
    if (Array.isArray(e.retires)) {
      for (const obj of e.retires) hien.delete(obj);
    }
  }
  return scene.objects.filter((o) => hien.has(o.id));
}

/** Đối tượng vừa được tạo/kéo dài ở bước này — dùng để làm nổi bật. */
export function highlightedAt(scene: Scene3D, step: number): string[] {
  const k = clampStep(scene, step);
  const snapshot = scene.formation?.steps[k];
  if (snapshot) return [...new Set(snapshot.focus_ids)];
  const e = scene.events.find((x) => x.step_index === k);
  if (!e) return [];
  const objs = [
    ...(e.object ? [e.object] : []),
    ...(Array.isArray(e.objects) ? e.objects : []),
  ];
  if (objs.length === 0) return [];
  return [...objs, ...e.depends];
}

/**
 * F3 (ISSUE-ARCH-HYBRID-FRONTEND-OFFLINE-INTEGRATION) — cảnh dựng ở tỉ lệ KÝ HIỆU (`length_unit.is_given === false`,
 * vd "a = 1 đơn vị dựng"): mọi giá trị số trên cảnh là của MỘT hình tại a = 1, không phải đáp số tổng quát (`a³√3/3`).
 * MỘT chỗ sinh lời chú thích cho mọi nơi hiện giá trị (nhãn số đo, ô soi, lời kể bước đo). Cảnh không có
 * `length_unit` (mọi cảnh LLM_ONLY) ⇒ chuỗi rỗng, hành vi cũ giữ nguyên.
 */
export function ghiChuGiaTriDung(
  scene: Pick<Scene3D, "length_unit">,
  valueText?: string | null,
  kind?: QuantityAnnotation["kind"],
): string {
  const lu = scene.length_unit;
  if (!lu || lu.is_given !== false) return "";
  if (kind === "angle") return "";
  if (typeof valueText === "string") {
    const trimmed = valueText.trim();
    if (/°|\brad\b/iu.test(trimmed)) return "";
    if (!laGiaTriDaiLuongChuaBiet(trimmed) && /[A-Za-z]/u.test(trimmed.replace(/\brad\b/giu, ""))) {
      return "";
    }
  }
  if (lu.display_scale && lu.display_scale.trim()) {
    return ` (trên hình dựng, ${lu.display_scale.trim()})`;
  }
  const sym = lu.symbol?.trim();
  return sym ? ` (trên hình dựng chuẩn hóa ${sym} = 1)` : "";
}

/** Lời kể của bước hiện tại — Tier 1, do engine sinh từ trạng thái thật. */
export function narrationAt(scene: Scene3D, step: number): string {
  const k = clampStep(scene, step);
  const e = scene.events.find((x) => x.step_index === k);
  // F3: lời kể của bước ĐO đọc ra giá trị của hình dựng — kèm tỉ lệ dựng khi cảnh dựng theo ký hiệu.
  const chu = e?.action === "MEASURE" ? ghiChuGiaTriDung(scene) : "";
  const goc = narrationGoc(scene, k, e);
  return goc && chu ? `${goc.replace(/\.\s*$/, "")}${chu}.` : goc;
}

function narrationGoc(scene: Scene3D, k: number, e: SceneEvent | undefined): string {
  const snapshot = scene.formation?.steps[k];
  if (snapshot?.learner_text && learnerTextIsSafe(scene, snapshot.learner_text)) {
    return snapshot.learner_text;
  }
  if (!e) return "";
  const candidate = e.learner_text ?? e.explanation;
  if (candidate && learnerTextIsSafe(scene, candidate)) return candidate;
  const obj = e.object ? scene.objects.find((o) => o.id === e.object) : undefined;
  const label = obj?.display_label?.trim() || obj?.label?.trim() || "đối tượng hình học";
  if (e.action === "INIT") return "Khởi tạo các dữ kiện và điểm đã cho.";
  if (e.action === "CREATE") return `Dựng ${label}.`;
  if (e.action === "EXTEND") return `Tiếp tục dựng ${label}.`;
  if (e.action === "MEASURE") return `Tính ${label}.`;
  return "Tiếp tục lời giải hình học.";
}

/** Kiểm leakage theo chính payload, không theo denylist case cố định. */
export function learnerTextIsSafe(scene: Scene3D, text: string): boolean {
  if (/^\s*Gán\s+\S+\s*=/u.test(text)) return false;
  if (/\b[\p{L}\p{N}]+_[\p{L}\p{N}_]+\b/u.test(text)) return false;
  const tokens = new Set<string>();
  for (const obj of scene.objects) {
    for (const value of [obj.id, obj.type, obj.render]) {
      if (typeof value === "string" && value.includes("_")) tokens.add(value);
    }
  }
  for (const token of tokens) {
    const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (new RegExp(`(^|[^\\p{L}\\p{N}_])${escaped}($|[^\\p{L}\\p{N}_])`, "u").test(text)) {
      return false;
    }
  }
  return true;
}

/** Formula chỉ được hiện khi mọi reference trỏ tới entity learner-facing thật. */
export function coherentFormula(
  scene: Scene3D,
  object: SceneObject,
): LearnerFormula | null {
  const formula = object.formula;
  if (!formula || !formula.text.trim() || !Array.isArray(formula.references)) return null;
  const ids = new Set(scene.objects.map((candidate) => candidate.id));
  const coherent = formula.references.every((reference) =>
    ids.has(reference.entity_id)
    && reference.display_label.trim().length > 0
    && formula.text.includes(reference.display_label));
  return coherent ? formula : null;
}

/**
 * "Dựa trên" của một vật (w11, review W10-H3): ĐÚNG các nguồn SỐ trực tiếp —
 * theo thứ tự chữ công thức khi có công thức nhất quán, không thì theo cạnh
 * `numerical` backend gõ loại. Rỗng ⇒ vật không có nguồn số; nơi gọi giữ phụ
 * thuộc hình học. Không tính gì — chỉ đọc provenance có cấu trúc.
 */
export function numericalBasis(scene: Scene3D, object: SceneObject | null | undefined): string[] {
  if (!object) return [];
  const refs = coherentFormula(scene, object)?.references ?? [];
  if (refs.length > 0) return refs.map((r) => r.entity_id);
  const ids = new Set(scene.objects.map((o) => o.id));
  return (object.dependency_edges ?? [])
    .filter((e) => e.relation === "numerical" && ids.has(e.source_id))
    .map((e) => e.source_id);
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
    them(o.rim_point); them(o.annotation?.witness?.foot); them(o.annotation?.witness?.from_point);
    them(o.perpendicular_witness?.foot);
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
      const h = o.curved_kind && o.curved_kind !== "ball" && o.height_sq
        ? Math.sqrt(Math.max(0, toNumber(o.height_sq)))
        : 0;
      const dinh: Vec3 = o.apex_or_top
        ? toVec3(o.apex_or_top)
        : h > 0
          ? [c[0], c[1], c[2] + h]
          : c;
      const truc: Vec3 = [dinh[0] - c[0], dinh[1] - c[1], dinh[2] - c[2]];
      const dai = Math.hypot(...truc);
      // Khối cầu (`apex_or_top` vắng) không có trục ⇒ nở đều theo ba trục.
      const phuong: Vec3[] = dai === 0
        ? [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        : truc_vuong_goc([truc[0] / dai, truc[1] / dai, truc[2] / dai]);
      const tamNo = o.curved_kind === "cone" ? [c] : [c, dinh];
      if (o.curved_kind === "cone") ra.push(dinh);
      for (const t of tamNo) {
        // True surface boundary points on axial directions (exact radius r from center/axis).
        for (const u of phuong) {
          ra.push([t[0] + u[0] * r, t[1] + u[1] * r, t[2] + u[2] * r]);
          ra.push([t[0] - u[0] * r, t[1] - u[1] * r, t[2] - u[2] * r]);
        }
        // Normalized diagonal surface points keep diagonal camera views on the true radius-r surface
        // without inflating the bounding box to r*sqrt(2) or r*sqrt(3).
        const rCheo = (r / Math.sqrt(Math.max(1, phuong.length))) * (1 + 1e-12);
        for (let mask = 0; mask < 1 << phuong.length; mask++) {
          const p: Vec3 = [...t];
          phuong.forEach((u, i) => {
            const sign = mask & (1 << i) ? 1 : -1;
            for (let j = 0; j < 3; j++) p[j] += sign * u[j] * rCheo;
          });
          ra.push(p);
        }
      }
    }
    if (o.render === "circle" && o.center && o.normal && o.radius_sq) {
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
      const c = toVec3(o.center);
      const n = toVec3(o.normal);
      const dai = Math.hypot(...n);
      if (dai > 0 && r > 0) {
        for (const u of truc_vuong_goc([n[0] / dai, n[1] / dai, n[2] / dai])) {
          ra.push([c[0] + u[0] * r, c[1] + u[1] * r, c[2] + u[2] * r]);
          ra.push([c[0] - u[0] * r, c[1] - u[1] * r, c[2] - u[2] * r]);
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
 * Đỉnh / cạnh / mặt của cảnh cho bộ chọn góc nhìn (`scene3d-camera.ts`) —
 * đọc TOPOLOGY đã có (`faces` của khối, đa giác), không suy hình học. Đỉnh trùng
 * chỗ gộp một; điểm lẻ (trung điểm, chân đường cao) vào như đỉnh không cạnh.
 */
export function cauTrucGocNhin(objects: SceneObject[]) {
  const diem: Vec3[] = [];
  const canh: [number, number][] = [];
  const mat: number[][] = [];
  const chiSo = new Map<string, number>();
  const daCo = new Set<string>();
  const dinhSo = (p: Vec3) => {
    const k = p.map((x) => x.toFixed(9)).join(",");
    if (!chiSo.has(k)) { chiSo.set(k, diem.length); diem.push(p); }
    return chiSo.get(k)!;
  };
  const dinh = (v: ExactVec3) => dinhSo(toVec3(v));
  const themCanh = (a: number, b: number) => {
    const [x, y] = a < b ? [a, b] : [b, a];
    if (x !== y && !daCo.has(`${x}-${y}`)) { daCo.add(`${x}-${y}`); canh.push([x, y]); }
  };
  const vong = (ds: number[]) => {
    mat.push(ds);
    ds.forEach((a, i) => {
      const b = ds[(i + 1) % ds.length];
      themCanh(a, b);
    });
  };
  for (const o of objects) {
    if (o.render === "surface" || o.render === "line") continue;
    if (o.type === "solid" && o.vertices && o.faces) {
      const g = o.vertices.map(dinh);
      for (const f of o.faces) vong(f.map((i) => g[i]));
    } else if (o.type === "curved_solid" && o.anchor) {
      const tam = toVec3(o.anchor);
      const iTam = dinhSo(tam);
      const rSq = o.radius_sq ? toNumber(o.radius_sq) : 0;
      const r = rSq > 0
        ? Math.sqrt(rSq)
        : o.rim_point
          ? Math.hypot(...toVec3(o.rim_point).map((v, k) => v - tam[k]))
          : 0;
      const hSq = o.height_sq ? toNumber(o.height_sq) : 0;
      const h = hSq > 0 ? Math.sqrt(hSq) : 0;
      const dinhTren: Vec3 | null = o.apex_or_top
        ? toVec3(o.apex_or_top)
        : o.curved_kind !== "ball" && h > 0
          ? [tam[0], tam[1], tam[2] + h]
          : null;
      if (o.curved_kind !== "ball" && dinhTren && r > 1e-6) {
        const truc: Vec3 = [dinhTren[0] - tam[0], dinhTren[1] - tam[1], dinhTren[2] - tam[2]];
        const lenTruc = Math.hypot(...truc);
        if (lenTruc > 1e-6) {
          const iTren = dinhSo(dinhTren);
          themCanh(iTam, iTren);
          const u: Vec3 = [truc[0] / lenTruc, truc[1] / lenTruc, truc[2] / lenTruc];
          const [e1, e2] = truc_vuong_goc(u);
          const dayPts: Vec3[] = [
            [tam[0] + r * e1[0], tam[1] + r * e1[1], tam[2] + r * e1[2]],
            [tam[0] + r * e2[0], tam[1] + r * e2[1], tam[2] + r * e2[2]],
            [tam[0] - r * e1[0], tam[1] - r * e1[1], tam[2] - r * e1[2]],
            [tam[0] - r * e2[0], tam[1] - r * e2[1], tam[2] - r * e2[2]],
          ];
          const gDay = dayPts.map(dinhSo);
          vong(gDay);
          if (o.curved_kind === "cylinder") {
            const napPts: Vec3[] = [
              [dinhTren[0] + r * e1[0], dinhTren[1] + r * e1[1], dinhTren[2] + r * e1[2]],
              [dinhTren[0] + r * e2[0], dinhTren[1] + r * e2[1], dinhTren[2] + r * e2[2]],
              [dinhTren[0] - r * e1[0], dinhTren[1] - r * e1[1], dinhTren[2] - r * e1[2]],
              [dinhTren[0] - r * e2[0], dinhTren[1] - r * e2[1], dinhTren[2] - r * e2[2]],
            ];
            const gNap = napPts.map(dinhSo);
            vong(gNap);
            themCanh(gDay[0], gNap[0]);
            themCanh(gDay[2], gNap[2]);
          } else {
            themCanh(gDay[0], iTren);
            themCanh(gDay[2], iTren);
          }
        }
      }
    } else if (o.polygon && o.polygon.length >= 3) {
      vong(o.polygon.map(dinh));
    } else if (o.xyz) {
      dinh(o.xyz);
    }
    if (o.perpendicular_witness?.foot) dinh(o.perpendicular_witness.foot);
    if (o.annotation?.witness?.foot) dinh(o.annotation.witness.foot);
  }
  for (const o of objects) {
    if (o.render !== "surface" || !o.point || !o.normal || diem.length < 3) continue;
    const p0 = toVec3(o.point);
    const n = toVec3(o.normal);
    const dn = Math.hypot(...n);
    if (!Number.isFinite(dn) || dn === 0) continue;
    const tren: number[] = [];
    for (let i = 0; i < diem.length; i++) {
      const p = diem[i];
      const h = ((p[0] - p0[0]) * n[0] + (p[1] - p0[1]) * n[1] + (p[2] - p0[2]) * n[2]) / dn;
      if (Math.abs(h) <= 1e-3) tren.push(i);
    }
    const tapTren = new Set(tren);
    if (tren.length >= 3 && !mat.some((f) => f.length >= 3 && f.every((idx) => tapTren.has(idx)))) {
      for (let j = 2; j < tren.length; j++) {
        const a = diem[tren[0]], b = diem[tren[1]], c = diem[tren[j]];
        const cx = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]);
        const cy = (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]);
        const cz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
        if (Math.hypot(cx, cy, cz) > 1e-5) {
          mat.push([tren[0], tren[1], tren[j]]);
          break;
        }
      }
    }
  }
  return { diem, canh, mat };
}

/**
 * ĐÁY và ĐỈNH của khối CHÓP duy nhất (regular-triangular-pyramid-w01) — ĐỌC dữ liệu backend, không tính: đáy là đa giác
 * mang vai `CONSTRUCT_BASE` (formation), đỉnh là đỉnh duy nhất của khối `PYRAMID_LIKE` ngoài đáy. `null` khi cảnh không
 * có đúng một chóp có đáy. Dùng cho hướng lên TRÌNH BÀY (`scene3d-camera.huongLenHienThi`).
 */
export function dayVaDinhChop(objects: SceneObject[]): { day: Vec3[]; dinh: Vec3 } | null {
  const chop = objects.filter((o) => o.type === "solid" && o.shape_class === "PYRAMID_LIKE"
    && o.vertices && o.vertex_ids && o.vertices.length === o.vertex_ids.length);
  if (chop.length !== 1) return null;
  const toaDo = new Map(chop[0].vertex_ids!.map((id, i) => [id, toVec3(chop[0].vertices![i])]));
  const day = objects.find((o) => o.type === "polygon3" && (o.formation_roles ?? []).includes("CONSTRUCT_BASE")
    && (o.vertex_ids ?? []).length >= 3 && o.vertex_ids!.every((id) => toaDo.has(id)));
  const dinh = day ? [...toaDo.keys()].filter((id) => !day.vertex_ids!.includes(id)) : [];
  if (!day || dinh.length !== 1) return null;
  return { day: day.vertex_ids!.map((id) => toaDo.get(id)!), dinh: toaDo.get(dinh[0])! };
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
  const banKinh = Math.max(
    ...chieu.map((p) => Math.hypot(p[0] - tam[0], p[1] - tam[1], p[2] - tam[2])));
  const canh = banKinh > 0 ? 2 * banKinh * PLANE_PATCH_MARGIN : PLANE_PATCH_MIN_SIZE;
  return Number.isFinite(canh) ? { tam, canh } : null;
}

/**
 * Bao lồi phẳng của các điểm trong `diem` thực sự nằm trên mặt phẳng `(diemMp, phapTuyen)`.
 * Khi mặt phẳng đi qua ≥ 3 điểm không thẳng hàng của hình (vd `(SAB)`, `(SAC)`, `(A'BD)`),
 * trả về các đỉnh đa giác theo thứ tự ngược chiều kim đồng hồ để vẽ đúng miền phẳng của hình
 * thay vì một tấm vuông lệch trục thò ra dưới đáy. Không đủ 3 điểm không thẳng hàng ⇒ `null`.
 */
export function daGiacMatPhang(
  diemMp: Vec3, phapTuyen: Vec3, diem: Vec3[],
): Vec3[] | null {
  const n = Math.hypot(...phapTuyen);
  if (!Number.isFinite(n) || n === 0 || diem.length < 3) return null;
  const u: Vec3 = [phapTuyen[0] / n, phapTuyen[1] / n, phapTuyen[2] / n];
  const [e1, e2] = truc_vuong_goc(u);
  const dk = duongKinhCanh(diem);
  const dungSaiMp = Math.max(dk * 1e-4, 1e-9);
  const dungSaiTrung = Math.max(dk * 1e-6, 1e-11);
  const dungSaiDienTich = Math.max(dk * dk * 1e-7, 1e-16);
  const trenMp: { p: Vec3; x: number; y: number }[] = [];
  for (const p of diem) {
    if (!p.every(Number.isFinite)) continue;
    const vx = p[0] - diemMp[0], vy = p[1] - diemMp[1], vz = p[2] - diemMp[2];
    const h = vx * u[0] + vy * u[1] + vz * u[2];
    if (Math.abs(h) > dungSaiMp) continue;
    const x = vx * e1[0] + vy * e1[1] + vz * e1[2];
    const y = vx * e2[0] + vy * e2[1] + vz * e2[2];
    if (trenMp.some((q) => Math.hypot(q.x - x, q.y - y) <= dungSaiTrung)) continue;
    trenMp.push({ p: [p[0] - h * u[0], p[1] - h * u[1], p[2] - h * u[2]], x, y });
  }
  if (trenMp.length < 3) return null;
  trenMp.sort((a, b) => a.x - b.x || a.y - b.y);
  const re = (o: { x: number; y: number }, a: { x: number; y: number }, b: { x: number; y: number }) =>
    (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const duoi: typeof trenMp = [];
  for (const pt of trenMp) {
    while (duoi.length >= 2 && re(duoi[duoi.length - 2], duoi[duoi.length - 1], pt) <= dungSaiDienTich) duoi.pop();
    duoi.push(pt);
  }
  const tren: typeof trenMp = [];
  for (let i = trenMp.length - 1; i >= 0; i--) {
    const pt = trenMp[i];
    while (tren.length >= 2 && re(tren[tren.length - 2], tren[tren.length - 1], pt) <= dungSaiDienTich) tren.pop();
    tren.push(pt);
  }
  duoi.pop();
  tren.pop();
  const bao = [...duoi, ...tren];
  if (bao.length < 3) return null;
  let dienTich2 = 0;
  for (let i = 0; i < bao.length; i++) {
    const a = bao[i], b = bao[(i + 1) % bao.length];
    dienTich2 += a.x * b.y - b.x * a.y;
  }
  return Math.abs(dienTich2) > dungSaiDienTich * 10 ? bao.map((b) => b.p) : null;
}

/** Cắt đa giác lồi trong mặt phẳng theo nửa không gian `z >= zMin` (Sutherland–Hodgman). */
function catDaGiacTheoDay(daGiac: Vec3[], zMin: number): Vec3[] {
  if (daGiac.length < 3 || !Number.isFinite(zMin)) return daGiac;
  const span = Math.max(...daGiac.map((p) => Math.hypot(p[0], p[1], p[2])), Math.abs(zMin), 1e-6);
  const eps = 1e-6 * span;
  if (daGiac.every((p) => p[2] >= zMin - eps)) return daGiac;
  const ra: Vec3[] = [];
  for (let i = 0; i < daGiac.length; i++) {
    const a = daGiac[i];
    const b = daGiac[(i + 1) % daGiac.length];
    const da = a[2] - zMin;
    const db = b[2] - zMin;
    const aTrong = da >= -eps;
    const bTrong = db >= -eps;
    if (aTrong && bTrong) {
      ra.push(b);
    } else if (aTrong && !bTrong) {
      const t = da / (da - db);
      ra.push([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), zMin]);
    } else if (!aTrong && bTrong) {
      const t = da / (da - db);
      ra.push([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), zMin]);
      ra.push(b);
    }
  }
  return ra.length >= 3 ? ra : daGiac;
}

/**
 * Miền phẳng mở rộng hữu hạn của một mặt phẳng toán học (`plane3`):
 * - Khi mặt phẳng đi qua ≥ 3 điểm của hình (`daGiac`), mở rộng bao lồi ra ngoài một lề vừa phải
 *   trong đúng mặt phẳng đó (và giữ `z >= zMin` khi mặt phẳng không nằm ngang) để mặt phẳng
 *   không bị mặt bên/mặt đáy của khối đặc nuốt mất.
 * - Khi mặt phẳng đi qua < 3 điểm của hình (vd mặt phẳng qua B vuông góc với SC), tạo miền phẳng
 *   từ `khungMatPhang` và cắt theo `z >= zMin` để không thò góc nhọn xuống dưới đáy.
 */
export function moRongDaGiacMatPhang(
  diemMp: Vec3, phapTuyen: Vec3, diem: Vec3[], daGiac?: Vec3[] | null,
): Vec3[] | null {
  const n = Math.hypot(...phapTuyen);
  if (!Number.isFinite(n) || n === 0 || diem.length === 0) return null;
  const u: Vec3 = [phapTuyen[0] / n, phapTuyen[1] / n, phapTuyen[2] / n];
  const dk = duongKinhCanh(diem);
  const dungSaiMp = Math.max(dk * 1e-4, 1e-9);
  const co = dk > 0 ? dk * 0.10 : 0.5;
  const zMin = Math.min(...diem.map((p) => p[2]));
  const zMax = Math.max(...diem.map((p) => p[2]));
  const ngang = Math.abs(u[2]) > 0.98;
  const goc = daGiac !== undefined ? daGiac : daGiacMatPhang(diemMp, phapTuyen, diem);
  if (goc && goc.length >= 3) {
    const coDiemNgoaiMp = diem.some((p) =>
      p.every(Number.isFinite)
      && Math.abs((p[0] - diemMp[0]) * u[0] + (p[1] - diemMp[1]) * u[1] + (p[2] - diemMp[2]) * u[2]) > dungSaiMp,
    );
    if (!coDiemNgoaiMp) return null;
  }
  if (ngang) {
    // Xây dựng cơ sở trực chuẩn (e1, e2) nằm ĐÚNG trong mặt phẳng vuông góc với u (dot(e1, u) = 0, dot(e2, u) = 0),
    // không bao giờ ép mặt phẳng gần ngang (0.98 < |u_z| < 1) thành mặt phẳng XY (z = const).
    const e1Raw: Vec3 = [1 - u[0] * u[0], -u[0] * u[1], -u[0] * u[2]];
    const ne1 = Math.hypot(...e1Raw) || 1;
    const e1: Vec3 = [e1Raw[0] / ne1, e1Raw[1] / ne1, e1Raw[2] / ne1];
    const e2Raw: Vec3 = [
      u[1] * e1[2] - u[2] * e1[1],
      u[2] * e1[0] - u[0] * e1[2],
      u[0] * e1[1] - u[1] * e1[0],
    ];
    const e2: Vec3 = e2Raw[1] >= 0 ? e2Raw : [-e2Raw[0], -e2Raw[1], -e2Raw[2]];
    const nguon = goc && goc.length >= 3 ? goc : diem;
    const sList = nguon.map((p) => (p[0] - diemMp[0]) * e1[0] + (p[1] - diemMp[1]) * e1[1] + (p[2] - diemMp[2]) * e1[2]);
    const tList = nguon.map((p) => (p[0] - diemMp[0]) * e2[0] + (p[1] - diemMp[1]) * e2[1] + (p[2] - diemMp[2]) * e2[2]);
    const sMin = Math.min(...sList);
    const sMax = Math.max(...sList);
    const tMin = Math.min(...tList);
    const tMax = Math.max(...tList);
    const spanS = Math.max(sMax - sMin, co);
    const spanT = Math.max(tMax - tMin, co);
    const heSoLe = goc && goc.length === 3 ? 0.45 : 0.42;
    const padS = Math.max(spanS * heSoLe, co * 1.15);
    const padT = Math.max(spanT * heSoLe, co * 1.15);
    const s0 = sMin - padS;
    const s1 = sMax + padS;
    const t0 = tMin - padT;
    const t1 = tMax + padT;
    return [
      [s0, t0],
      [s1, t0],
      [s1, t1],
      [s0, t1],
    ].map(([s, t]): Vec3 => [
      diemMp[0] + s * e1[0] + t * e2[0],
      diemMp[1] + s * e1[1] + t * e2[1],
      diemMp[2] + s * e1[2] + t * e2[2],
    ]);
  }
  const nh = Math.hypot(u[0], u[1]) || 1;
  const e1: Vec3 = [-u[1] / nh, u[0] / nh, 0];
  const e2Raw: Vec3 = [
    u[1] * e1[2] - u[2] * e1[1],
    u[2] * e1[0] - u[0] * e1[2],
    u[0] * e1[1] - u[1] * e1[0],
  ];
  const e2: Vec3 = e2Raw[2] >= 0 ? e2Raw : [-e2Raw[0], -e2Raw[1], -e2Raw[2]];
  const tFloor = e2[2] > 1e-6 ? (zMin - diemMp[2]) / e2[2] : -Infinity;
  if (goc && goc.length >= 3) {
    const sList = goc.map((p) => (p[0] - diemMp[0]) * e1[0] + (p[1] - diemMp[1]) * e1[1] + (p[2] - diemMp[2]) * e1[2]);
    const tList = goc.map((p) => (p[0] - diemMp[0]) * e2[0] + (p[1] - diemMp[1]) * e2[1] + (p[2] - diemMp[2]) * e2[2]);
    const sMin = Math.min(...sList);
    const sMax = Math.max(...sList);
    const tMin = Math.min(...tList);
    const tMax = Math.max(...tList);
    const spanS = Math.max(sMax - sMin, co);
    const spanT = Math.max(tMax - tMin, co);
    const padS = Math.max(spanS * (goc.length === 3 ? 0.30 : 0.22), co * 0.82);
    const padT = Math.max(spanT * (goc.length === 3 ? 0.24 : 0.16), co * 0.68);
    const s0 = sMin - padS;
    const s1 = sMax + padS;
    const t0 = Math.max(tFloor, tMin - padT);
    const t1 = tMax + padT;
    const hop: Vec3[] = [
      [s0, t0],
      [s1, t0],
      [s1, t1],
      [s0, t1],
    ].map(([s, t]): Vec3 => [
      diemMp[0] + s * e1[0] + t * e2[0],
      diemMp[1] + s * e1[1] + t * e2[1],
      diemMp[2] + s * e1[2] + t * e2[2],
    ]);
    return catDaGiacTheoDay(hop, zMin);
  }
  const sList = diem.map((p) => (p[0] - diemMp[0]) * e1[0] + (p[1] - diemMp[1]) * e1[1] + (p[2] - diemMp[2]) * e1[2]);
  const tList = diem.map((p) => (p[0] - diemMp[0]) * e2[0] + (p[1] - diemMp[1]) * e2[1] + (p[2] - diemMp[2]) * e2[2]);
  if (!sList.every(Number.isFinite) || !tList.every(Number.isFinite)) return null;
  const sMin = Math.min(...sList);
  const sMax = Math.max(...sList);
  const tMin = Math.min(...tList);
  const tMax = Math.max(...tList);
  const coMin = dk > 0 ? dk * 0.4 : PLANE_PATCH_MIN_SIZE;
  const spanS = Math.max(sMax - sMin, coMin);
  const spanT = Math.max(tMax - tMin, coMin * 0.6);
  const tCeil = e2[2] > 1e-6 && zMax > zMin + dungSaiMp ? (zMax - diemMp[2]) / e2[2] : Infinity;
  const padS = spanS * 0.08;
  const s0 = sMin - padS;
  const s1 = sMax + padS;
  const t0 = Math.max(tFloor, tMin - spanT * 0.10);
  const t1 = Math.min(tCeil, Math.max(tMax + spanT * 0.30, t0 + spanS * 0.95));
  const hop: Vec3[] = [
    [s0, t0],
    [s1, t0],
    [s1, t1],
    [s0, t1],
  ].map(([s, t]): Vec3 => [
    diemMp[0] + s * e1[0] + t * e2[0],
    diemMp[1] + s * e1[1] + t * e2[1],
    diemMp[2] + s * e1[2] + t * e2[2],
  ]);
  return catDaGiacTheoDay(hop, zMin);
}

/**
 * Điểm neo trên lề mở rộng của mặt phẳng toán học để gắn nhãn ký hiệu (vd `(SAB)`, `(MNP)`),
 * chọn vị trí cách xa các đỉnh của hình nhất để không đè lên chấm đỉnh và tên đỉnh.
 */
export function diemNeoNhanMatPhang(
  diemMp: Vec3, phapTuyen: Vec3, diem: Vec3[],
): Vec3 | null {
  const goc = daGiacMatPhang(diemMp, phapTuyen, diem);
  const moRieng = moRongDaGiacMatPhang(diemMp, phapTuyen, diem, goc); const mo = moRieng ?? goc;
  if (!mo || mo.length < 3) return null;
  const m = mo.length;
  const tam: Vec3 = [
    mo.reduce((s, p) => s + p[0], 0) / m,
    mo.reduce((s, p) => s + p[1], 0) / m,
    mo.reduce((s, p) => s + p[2], 0) / m,
  ];
  const diemTranh: Vec3[] = moRieng ? [...diem] : [tam];
  if (goc && goc.length >= 3) {
    const gLen = goc.length;
    const tamGoc: Vec3 = [
      goc.reduce((s, p) => s + p[0], 0) / gLen,
      goc.reduce((s, p) => s + p[1], 0) / gLen,
      goc.reduce((s, p) => s + p[2], 0) / gLen,
    ];
    diemTranh.push(tamGoc);
    for (let i = 0; moRieng && i < gLen; i++) {
      const a = goc[i];
      const b = goc[(i + 1) % gLen];
      diemTranh.push(a);
      diemTranh.push([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]);
      diemTranh.push([0.5 * a[0] + 0.5 * tamGoc[0], 0.5 * a[1] + 0.5 * tamGoc[1], 0.5 * a[2] + 0.5 * tamGoc[2]]);
    }
  }
  const ungVien: Vec3[] = [];
  for (let i = 0; i < m; i++) {
    const a = mo[i];
    const b = mo[(i + 1) % m];
    ungVien.push([0.90 * a[0] + 0.10 * tam[0], 0.90 * a[1] + 0.10 * tam[1], 0.90 * a[2] + 0.10 * tam[2]]);
    const mid: Vec3 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
    ungVien.push([0.92 * mid[0] + 0.08 * tam[0], 0.92 * mid[1] + 0.08 * tam[1], 0.92 * mid[2] + 0.08 * tam[2]]);
  }
  let tot: Vec3 = ungVien[0];
  let diemTot = -Infinity;
  for (const u of ungVien) {
    const kcMin = diemTranh.length > 0
      ? Math.min(...diemTranh.map((p) => Math.hypot(u[0] - p[0], u[1] - p[1], u[2] - p[2])))
      : 1;
    const diemSo = kcMin + 0.08 * (u[2] - tam[2]);
    if (diemSo > diemTot) {
      diemTot = diemSo;
      tot = u;
    }
  }
  return tot;
}

/** Điểm nền cho phần vẽ của đường `duongId`: điểm có biên của cảnh + chân (do kernel tính) của mọi nhân chứng vuông
 *  góc rơi trên đường ấy — chân thường không phải điểm của cảnh, nên thiếu nó thì chân ngoài cạnh nằm ngoài nét vẽ. */
export function diemChoDuong(objects: SceneObject[], duongId: string): Vec3[] {
  const chan = objects.flatMap((o) => [o.annotation?.witness, o.perpendicular_witness])
    .flatMap((w) => [
      ...(w?.on === duongId && w.foot ? [toVec3(w.foot)] : []),
      ...(w?.second?.on === duongId && w.second.foot ? [toVec3(w.second.foot)] : []),
    ]);
  return [...diemHuuHan(objects), ...chan];
}

/**
 * ĐOẠN ĐẠI DIỆN của một đường thẳng vô hạn — cùng quy tắc với `khungMatPhang`: chiếu mọi điểm có biên của cảnh lên
 * đường, lấy khoảng hình chiếu, nới theo `PLANE_PATCH_MARGIN`; dài tối thiểu bằng đường chéo hộp bao của cảnh.
 *
 * ─── LỖI ĐƯỢC SỬA, ĐO ĐƯỢC (run `hybrid-semantic-hardening`) ─────────────
 *
 * Trước bản này đoạn là `point ± LINE_DISPLAY_HALF_LENGTH` (±6) bất kể cỡ cảnh. Cảnh Hybrid cỡ ~1 đơn vị: giao tuyến
 * (SAB) ∩ (SCD) qua S chạy tới (6,0,1), sau lưng camera. SwiftShader bỏ trắng cả nét (0 điểm ảnh, kể cả khi tắt kiểm
 * chiều sâu); GPU thật vẽ một vệt loe tới mép khung. Toán học vẫn đúng — sai ở chỗ chọn PHẦN NÀO của đường để vẽ.
 *
 * Trả `null` khi cảnh không có điểm hữu hạn hoặc phương suy biến — nơi gọi rơi về độ dài cố định.
 */
export function doanDuongThang(diemDuong: Vec3, huong: Vec3, diem: Vec3[]): [Vec3, Vec3] | null {
  const n = Math.hypot(...huong);
  if (!Number.isFinite(n) || n === 0 || diem.length === 0) return null;
  const u: Vec3 = [huong[0] / n, huong[1] / n, huong[2] / n];
  const t = diem.map((p) => (p[0] - diemDuong[0]) * u[0] + (p[1] - diemDuong[1]) * u[1] + (p[2] - diemDuong[2]) * u[2]);
  if (!t.every(Number.isFinite)) return null;
  const lo = Math.min(...t), hi = Math.max(...t);
  const truc = [0, 1, 2].map((i) => Math.max(...diem.map((p) => p[i])) - Math.min(...diem.map((p) => p[i])));
  const cheo = Math.hypot(...truc);
  const tai = (s: number): Vec3 => [diemDuong[0] + s * u[0], diemDuong[1] + s * u[1], diemDuong[2] + s * u[2]];
  // Khi trên đường thẳng có ≥ 2 điểm của hình (vd hai đầu mút đoạn/cạnh hoặc đỉnh + chân vuông góc), lấy tâm và
  // khoảng cơ sở theo đúng các điểm nằm trên đường, nới đều hai đầu để phân biệt đường vô hạn với đoạn hữu hạn mà
  // không bị các đỉnh ngoài đường kéo lệch tâm.
  const dungSai = 1e-4 * Math.max(1, cheo);
  // Khoảng chỉ của các điểm NẰM TRÊN đường: điểm neo `diemDuong` (một điểm bất kỳ backend chọn) không phải điểm của hình.
  let onLo = Infinity, onHi = -Infinity;
  for (let i = 0; i < diem.length; i++) {
    const p = diem[i], ti = t[i];
    const lech = Math.hypot(
      p[0] - diemDuong[0] - ti * u[0],
      p[1] - diemDuong[1] - ti * u[1],
      p[2] - diemDuong[2] - ti * u[2],
    );
    if (lech <= dungSai) {
      if (ti < onLo) onLo = ti;
      if (ti > onHi) onHi = ti;
    }
  }
  const khoangTrenDuong = onHi - onLo;
  if (khoangTrenDuong > 1e-5) {
    const giuaOn = (onLo + onHi) / 2;
    const duoi = Math.max(khoangTrenDuong * 0.14, cheo * 0.055);
    const nuaOn = khoangTrenDuong / 2 + duoi;
    return [tai(giuaOn - nuaOn), tai(giuaOn + nuaOn)];
  }
  const giua = (lo + hi) / 2;
  // Tối thiểu theo TỈ LỆ cảnh (nửa đường chéo hộp bao), không cố định: cảnh 0,05 không nhận đường dài 2 (lại đâm qua
  // camera), cảnh 100 không nhận một mẩu dài 2 (review S2). Cảnh một điểm ⇒ rơi về `PLANE_PATCH_MIN_SIZE`.
  const nua = Math.max(cheo > 0 ? cheo / 2 : PLANE_PATCH_MIN_SIZE / 2, ((hi - lo) / 2) * PLANE_PATCH_MARGIN);
  return [tai(giua - nua), tai(giua + nua)];
}

/**
 * Hướng cạnh góc vuông `u` tại `chan`: giữ nguyên phương `u` do backend phát,
 * nhưng nếu `chan` nằm ở đầu mút của các điểm thuộc đường `(chan, u)` khiến `+u`
 * chĩa ra ngoài đoạn còn `-u` hướng vào phần trong của đoạn (như khi chân H trùng
 * đỉnh B' trên đường BB'), lật sang `-u` để ký hiệu góc vuông nằm gọn trong hình.
 * Với khoảng cách điểm–mặt phẳng (`v` là pháp tuyến MH), nếu `chan` thực sự nằm
 * ở phần trong của một đoạn nối hai điểm của hình thuộc mặt phẳng vuông góc với `v`
 * (như chân H nằm trên cạnh A'B' của mặt (ABB')), ưu tiên hướng dọc theo cạnh đó.
 */
export function huongChanVuongGoc(chan: Vec3, u: Vec3, diem: Vec3[], v?: Vec3): Vec3 {
  const d = Math.hypot(u[0], u[1], u[2]);
  if (!Number.isFinite(d) || d < 1e-9 || diem.length === 0) return u;
  const ux = u[0] / d, uy = u[1] / d, uz = u[2] / d;
  let tMin = 0, tMax = 0;
  for (const p of diem) {
    const dx = p[0] - chan[0], dy = p[1] - chan[1], dz = p[2] - chan[2];
    const t = dx * ux + dy * uy + dz * uz;
    const px = dx - t * ux, py = dy - t * uy, pz = dz - t * uz;
    if (Math.hypot(px, py, pz) <= 1e-4) {
      if (t < tMin) tMin = t;
      if (t > tMax) tMax = t;
    }
  }
  if (tMax - tMin > 1e-4 && tMax < -tMin * 0.25) {
    return [-u[0], -u[1], -u[2]];
  }
  if (!(tMin < -1e-4 && tMax > 1e-4) && v) {
    const dv = Math.hypot(v[0], v[1], v[2]);
    if (Number.isFinite(dv) && dv > 1e-9) {
      const vx = v[0] / dv, vy = v[1] / dv, vz = v[2] / dv;
      const trenMp: { dx: number; dy: number; dz: number; kc: number }[] = [];
      for (const p of diem) {
        const dx = p[0] - chan[0], dy = p[1] - chan[1], dz = p[2] - chan[2];
        const kc = Math.hypot(dx, dy, dz);
        if (kc > 1e-4 && Math.abs(dx * vx + dy * vy + dz * vz) <= 1e-4 * Math.max(1, kc)) {
          trenMp.push({ dx, dy, dz, kc });
        }
      }
      for (let i = 0; i < trenMp.length; i++) {
        const a = trenMp[i];
        for (let j = i + 1; j < trenMp.length; j++) {
          const b = trenMp[j];
          const cung = (a.dx * b.dx + a.dy * b.dy + a.dz * b.dz) / (a.kc * b.kc);
          if (cung < -1 + 1e-5) {
            return a.kc >= b.kc ? [a.dx, a.dy, a.dz] : [b.dx, b.dy, b.dz];
          }
        }
      }
    }
  }
  return u;
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
export const VONG_CHIA = 72;
export const LINE_DISPLAY_HALF_LENGTH = 6;

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

/* ══ DÒNG THỜI GIAN HÌNH HỌC (W12) — tách bước DỰNG khỏi bước TÍNH ════════
 *
 * Review người (W12, NEEDS_CHANGES): thanh bước đi qua cả những sự kiện chỉ
 * tính một con số hay ghi kết luận — chỉ số tăng mà hình đứng yên, nên mô
 * phỏng đọc như một slideshow lời giải.
 *
 * Bước dựng là một PHÂN HOẠCH của dãy sự kiện (cùng khuôn `pacer`, bất biến
 * #32): mỗi bước là một đoạn LIÊN TIẾP, các đoạn phủ đủ, không chồng lấn,
 * không sinh sự kiện mới. Khung hiển thị của một bước là `trace[anchor]` với
 * `anchor` = sự kiện CUỐI của đoạn — bất biến #31 (`frame k ⇔ trace[k]`) giữ
 * nguyên, chỉ không dừng ở những `k` không đổi hình.
 *
 * Một bước MỚI mở ở sự kiện `GEOMETRY_CONSTRUCTION` làm đổi HÌNH (tập vật vẽ
 * được hoặc tiến độ thiết diện). Bước đo, lời giải thích, kết luận nhập vào
 * bước đang mở và lên lớp LỜI GIẢI. Loại sự kiện đọc từ `semantic_kind` có
 * cấu trúc; cảnh cũ không gõ loại thì mỗi sự kiện một bước như trước — không
 * đoán từ lời kể, tiêu đề, hành động hay định danh máy. */

export interface GeometryStep {
  index: number;
  /** Sự kiện đầu và cuối của đoạn (chỉ số `step_index`). */
  start: number;
  end: number;
  /** Khung hiển thị của bước — luôn là sự kiện cuối của đoạn. */
  anchor: number;
  /** Sự kiện dựng hình (và `INIT` ở bước 0). */
  construction: number[];
  /** Bước đo và lời giải thích — lên lớp lời giải, không lên thanh bước. */
  solution: number[];
  /** Kết luận của đề (`FINAL_RESULT`). */
  results: number[];
}

const _dongThoiGian = new WeakMap<Scene3D, GeometryStep[]>();

function _loaiSuKien(scene: Scene3D, k: number): string | undefined {
  return scene.formation?.steps[k]?.semantic_kind
    ?? scene.events.find((e) => e.step_index === k)?.semantic_kind;
}

const _chiDeDo = new WeakMap<Scene3D, Set<string>>();

/**
 * regular-square-pyramid-w03 · H-W2-4 — MẶT PHẲNG PHỤ CHỈ ĐỂ ĐO: `plane3` dẫn xuất, đúng một vai
 * `CONSTRUCT_AUXILIARY_GEOMETRY`, không phải dữ kiện/mục tiêu, và mọi vật dựa trên nó là đại lượng (vd mặt phẳng qua
 * A, B, C chỉ để đo chiều cao). Cảnh trung tính không vẽ nó (`scene3d-auxiliary`), nên nó không phải thay đổi HÌNH:
 * sự kiện chỉ dựng nó không mở bước dựng — dù công tắc «Hình phụ» bật hay tắt (dòng thời gian không phụ thuộc công tắc).
 */
export function measurementOnlyPlanes(scene: Scene3D): Set<string> {
  const co = _chiDeDo.get(scene);
  if (co) return co;
  // Chỉ mặt phẳng ĐI QUA CÁC ĐIỂM của khối đã vẽ (mặt/mặt chéo, vd (ABC) để đo chiều cao) mới là "chỉ để đo": nó trùng
  // thứ đã thấy. Mặt phẳng dựng mới (vd qua B ⊥ SC, phụ thuộc một đường) là hình đề yêu cầu dựng — không ẩn (Owner
  // 2026-10-26).
  const diemKhoi = new Set(scene.objects.flatMap((o) =>
    (o.type === "solid" || o.type === "curved_solid") ? [...(o.depends ?? []), ...(o.vertex_ids ?? [])] : []));
  const ra = new Set(scene.objects.filter((o) => {
    const vai = o.formation_roles ?? [];
    const nhom = o.display_group ?? [];
    const con = scene.objects.filter((x) => x.depends?.includes(o.id));
    return o.type === "plane3" && o.origin === "derived" && vai.length === 1
      && vai[0] === "CONSTRUCT_AUXILIARY_GEOMETRY" && !nhom.includes("given") && !nhom.includes("target")
      && con.length > 0 && con.every((x) => x.type === "quantity")
      && (o.depends ?? []).length >= 3 && (o.depends ?? []).every((id) => diemKhoi.has(id));
  }).map((o) => o.id));
  _chiDeDo.set(scene, ra);
  return ra;
}

/** Chữ ký HÌNH ở sự kiện `k`: vật vẽ được đang hiện (trừ mặt phẳng phụ chỉ để đo) + tiến độ thiết diện. */
function _chuKyHinh(scene: Scene3D, k: number): string {
  const chiDeDo = measurementOnlyPlanes(scene);
  const ve = new Set(scene.objects
    .filter((o) => o.render !== "readout" && o.render !== "non_visual" && !chiDeDo.has(o.id)).map((o) => o.id));
  const s = scene.formation?.steps[k];
  const hien = (s ? s.visible_ids : objectsAt(scene, k).map((o) => o.id))
    .filter((id) => ve.has(id)).sort();
  const tienDo = (s?.geometry_progress ?? [])
    .map((p) => [p.object_id, p.visible_edge_ids.length, p.closed, p.fill_visible]);
  return JSON.stringify([hien, tienDo]);
}

export function geometryTimeline(scene: Scene3D): GeometryStep[] {
  const daCo = _dongThoiGian.get(scene);
  if (daCo) return daCo;
  const n = stepCount(scene);
  const coLoai = n > 0 && Array.from({ length: n }, (_, k) => _loaiSuKien(scene, k))
    .every((l) => !!l && l !== "LEGACY_UNTYPED_EVENT");
  const ra: GeometryStep[] = [];
  for (let k = 0; k < n; k += 1) {
    const loai = _loaiSuKien(scene, k);
    const moBuoc = k === 0 || !coLoai
      || (loai === "GEOMETRY_CONSTRUCTION" && _chuKyHinh(scene, k) !== _chuKyHinh(scene, k - 1));
    if (moBuoc) {
      ra.push({ index: ra.length, start: k, end: k, anchor: k,
        construction: [], solution: [], results: [] });
    }
    const g = ra[ra.length - 1];
    g.end = k;
    g.anchor = k;
    if (k === g.start || loai === "GEOMETRY_CONSTRUCTION") g.construction.push(k);
    else if (loai === "FINAL_RESULT") g.results.push(k);
    else g.solution.push(k);
  }
  _dongThoiGian.set(scene, ra);
  return ra;
}

export function geometryStepCount(scene: Scene3D): number {
  return geometryTimeline(scene).length;
}

/** Bước dựng chứa sự kiện `step`. */
export function geometryStepOf(scene: Scene3D, step: number): number {
  const k = clampStep(scene, step);
  return Math.max(0, geometryTimeline(scene).findIndex((g) => k >= g.start && k <= g.end));
}

/** Khung hiển thị của bước dựng thứ `g` (kẹp vào miền hợp lệ). */
export function anchorOfGeometryStep(scene: Scene3D, g: number): number {
  const t = geometryTimeline(scene);
  if (t.length === 0) return 0;
  return t[Math.min(Math.max(Math.trunc(g), 0), t.length - 1)].anchor;
}

/** Sự kiện `step` bất kỳ → khung của bước dựng chứa nó. */
export function geometryAnchor(scene: Scene3D, step: number): number {
  return anchorOfGeometryStep(scene, geometryStepOf(scene, step));
}

export function nextGeometryStep(scene: Scene3D, step: number): number {
  return anchorOfGeometryStep(scene, geometryStepOf(scene, step) + 1);
}

export function prevGeometryStep(scene: Scene3D, step: number): number {
  return anchorOfGeometryStep(scene, geometryStepOf(scene, step) - 1);
}

export function isFirstGeometryStep(scene: Scene3D, step: number): boolean {
  return geometryStepOf(scene, step) <= 0;
}

export function isLastGeometryStep(scene: Scene3D, step: number): boolean {
  const n = geometryStepCount(scene);
  return n === 0 || geometryStepOf(scene, step) >= n - 1;
}

/** "Đang dựng / Dựa trên" của bước dựng — sự kiện dựng đầu đoạn. */
export function geometryFocusAt(
  scene: Scene3D,
  step: number,
): { created: string | null; depends: string[] } {
  const t = geometryTimeline(scene);
  const dau = t[geometryStepOf(scene, step)]?.construction[0] ?? clampStep(scene, step);
  return focusAt(scene, dau);
}

/**
 * W17 · TÊN HÀNH ĐỘNG của bước dựng chứa `step` — `display_label` backend phát cho sự kiện dựng
 * đầu đoạn. Cần khi đích của bước không phải vật của cảnh (câu lệnh NHÓM "Các cạnh bên AD, BE,
 * CF"). `null` ở bước INIT: tên hành động tách khỏi XUẤT XỨ — chỉ INIT là "dữ kiện đề cho".
 */
export function geometryActionLabelAt(scene: Scene3D, step: number): string | null {
  const k = geometryTimeline(scene)[geometryStepOf(scene, step)]?.construction[0] ?? clampStep(scene, step);
  const e = scene.events.find((x) => x.step_index === k);
  return e && e.action !== "INIT" ? e.display_label ?? null : null;
}

/**
 * Vật TÔ SÁNG của bước dựng: mọi vật các sự kiện dựng của đoạn đưa lên khung.
 * Bước dựng CUỐI không tô gì — hình đã đủ, khung cuối là khung trung tính.
 */
export function geometryHighlightedAt(scene: Scene3D, step: number): string[] {
  if (isLastGeometryStep(scene, step)) return [];
  const g = geometryTimeline(scene)[geometryStepOf(scene, step)];
  return [...new Set((g?.construction ?? []).flatMap((k) => highlightedAt(scene, k)))];
}

/** W4 · Các lý do đã kiểm chứng của bước dựng chứa `step` (mọi sự kiện của đoạn), không trùng, qua cùng bộ lọc rò
 *  định danh với lời kể. Rỗng khi backend không chứng nhận được quan hệ nào — không bao giờ tự suy ra ở frontend. */
export function geometryJustificationsAt(scene: Scene3D, step: number): string[] {
  const g = geometryTimeline(scene)[geometryStepOf(scene, step)];
  if (!g) return [];
  const ra = scene.events
    .filter((e) => e.step_index >= g.start && e.step_index <= g.end)
    .map((e) => e.justification_text?.trim() ?? "")
    .filter((t) => t && learnerTextIsSafe(scene, t));
  return [...new Set(ra)];
}

/** Lời kể của bước dựng — lời của sự kiện dựng đầu đoạn. */
export function geometryNarrationAt(scene: Scene3D, step: number): string {
  const t = geometryTimeline(scene);
  return narrationAt(scene, t[geometryStepOf(scene, step)]?.construction[0] ?? step);
}

/** Một dòng của lớp lời giải. `id` luôn là một vật THẬT của cảnh (bấm được). */
export interface SolutionItem {
  id: string;
  /** Sự kiện sinh ra dòng này (0 với dữ kiện đề cho). */
  event: number;
  /** Lời kể của sự kiện — rỗng với dữ kiện đề cho. */
  text: string;
  /** Công thức có tham chiếu nhất quán; `null` khi không có công thức thật. */
  formula: string | null;
  /** Nguồn SỐ trực tiếp (`numericalBasis`). */
  basis: string[];
  /** Dòng mới xuất hiện ở bước dựng đang xem. */
  isNew: boolean;
}

export interface SolutionLayer {
  givens: SolutionItem[];
  steps: SolutionItem[];
  results: SolutionItem[];
}

/**
 * LỚP LỜI GIẢI đồng bộ với bước dựng chứa `step` (W12): dữ kiện đề cho, các
 * bước tính (công thức, nguồn số), kết quả. Mỗi đại lượng MỘT dòng: đáp số
 * nằm ở `results` và không lặp ở `steps`.
 */
export function solutionAt(scene: Scene3D, step: number): SolutionLayer {
  const t = geometryTimeline(scene);
  if (t.length === 0) return { givens: [], steps: [], results: [] };
  const g = t[geometryStepOf(scene, step)];
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const suKien = (k: number) => scene.events.find((e) => e.step_index === k);
  const dong = (id: string, k: number, text: string): SolutionItem => {
    const o = byId.get(id)!;
    const f = coherentFormula(scene, o);
    return {
      id, event: k, text,
      formula: f && f.references.length > 0 ? f.text : null,
      basis: numericalBasis(scene, o),
      isNew: k >= g.start && k <= g.end,
    };
  };
  const ketQua = new Set<string>();
  const results: SolutionItem[] = [];
  for (let k = 0; k <= g.anchor; k += 1) {
    const sk = suKien(k);
    const id = sk?.object;
    const o = id ? byId.get(id) : undefined;
    const loai = _loaiSuKien(scene, k);
    const laDuKienDeCho = Boolean(
      o
      && classifyQuantityProvenance(o, scene) === "GIVEN"
      && o.annotation?.role !== "result"
      && o.annotation?.category !== "result",
    );
    const laKetQua = loai === "FINAL_RESULT"
      || (!loai && sk?.action === "MEASURE" && !laDuKienDeCho && Boolean(o && (o.type === "quantity" || o.value !== undefined) && (o.render === "readout" || o.render === "non_visual")));
    if (!laKetQua || !id || !o || ketQua.has(id)) continue;
    ketQua.add(id);
    results.push(dong(id, k, narrationAt(scene, k)));
  }
  const hien = new Set(objectsAt(scene, g.anchor).map((o) => o.id));
  const givens = scene.objects
    .filter((o) => o.type === "quantity" && o.render === "readout" && classifyQuantityProvenance(o, scene) === "GIVEN"
      && hien.has(o.id) && !ketQua.has(o.id))
    .map((o) => dong(o.id, 0, ""));
  const daCo = new Set([...ketQua, ...givens.map((x) => x.id)]);
  const steps: SolutionItem[] = [];
  for (let k = 1; k <= g.anchor; k += 1) {
    const id = suKien(k)?.object;
    const o = id ? byId.get(id) : undefined;
    if (_loaiSuKien(scene, k) !== "MEASUREMENT" || !o || o.type !== "quantity"
        || o.render !== "readout" || daCo.has(o.id)) continue;
    daCo.add(o.id);
    steps.push(dong(o.id, k, narrationAt(scene, k)));
  }
  return { givens, steps, results };
}

/**
 * Danh sách «Các bước dựng» (ROADMAP §0.1-3): MỘT mục mỗi bước DỰNG — cùng phân hoạch với thanh bước, nên chọn
 * một mục là đặt đúng neo mà thanh bước và phát lại đang dùng (#31/#35). Nhãn: hành động backend phát cho bước,
 * hoặc lời kể của nó; bước 0 là dữ kiện đề cho.
 */
export function geometryStepList(scene: Scene3D): { index: number; anchor: number; label: string }[] {
  return geometryTimeline(scene).map((g, index) => ({
    index,
    anchor: g.anchor,
    label: geometryActionLabelAt(scene, g.anchor) || geometryNarrationAt(scene, g.anchor) || "Dữ kiện đề cho",
  }));
}

/**
 * Đại lượng chọn được ở bước đang xem (ROADMAP §0.1-2): kết quả trước, rồi đại lượng trung gian, rồi dữ kiện —
 * cùng ba mục của lớp lời giải, nên một đại lượng chỉ có một mục; `same_as` trỏ về dòng gốc không lặp.
 */
export function quantityChoices(scene: Scene3D, step: number): { results: string[]; steps: string[]; givens: string[] } {
  const lg = solutionAt(scene, step);
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const co = new Set([...lg.givens, ...lg.steps, ...lg.results].map((x) => x.id));
  const rieng = (xs: SolutionItem[]) => xs.map((x) => x.id).filter((id) => {
    const s = byId.get(id)?.annotation?.same_as;
    return !(s && co.has(s));
  });
  return { results: rieng(lg.results), steps: rieng(lg.steps), givens: rieng(lg.givens) };
}

/**
 * SIMULATION-FIRST UX (P1): Tập id các ĐẠI LƯỢNG KẾT QUẢ CUỐI của bài toán (cùng bí danh `same_as` hai chiều).
 *
 * Phân biệt rõ đại lượng dựng hình/quan sát (`given`, `intermediate` / `MEASUREMENT`) với kết quả cuối của đề
 * (`status=result` / `role="result"` / `category="result"` / `FINAL_RESULT` / `hybrid.answers`). Các hàm model
 * thuần (`solutionAt`, `quantityChoices`, `annotationsAt`) giữ nguyên dữ liệu gốc; giao diện mô phỏng học sinh
 * dùng tập này để không lộ đáp số cuối ở bất kỳ bước nào trong khi vẫn giữ chứng chỉ vuông góc và đoạn nhân chứng 3D.
 */
export function tapKetQuaCuoi(
  scene: Scene3D,
  hybrid?: { answers?: readonly { quantity_id: string }[] } | null,
): ReadonlySet<string> {
  const ra = new Set<string>();
  for (const a of hybrid?.answers ?? []) {
    if (a?.quantity_id) ra.add(a.quantity_id);
  }
  const cuoi = Math.max(0, stepCount(scene) - 1);
  for (const r of solutionAt(scene, cuoi).results) {
    ra.add(r.id);
  }
  for (const e of scene.events) {
    if (e.semantic_kind === "FINAL_RESULT") {
      if (e.object) ra.add(e.object);
      if (e.alias_object) ra.add(e.alias_object);
    }
  }
  for (const o of scene.objects) {
    if (o.type !== "quantity") continue;
    if (
      o.annotation?.role === "result"
      || o.annotation?.category === "result"
      || o.formation_roles?.includes("FINAL_RESULT")
      || o.display_group?.includes("target")
      || o.id.startsWith("kq_vcert")
    ) {
      ra.add(o.id);
    }
  }
  const byId = new Map(scene.objects.map((x) => [x.id, x]));
  const laDuKienDeCho = (x?: SceneObject): boolean =>
    Boolean(
      x
      && classifyQuantityProvenance(x, scene) === "GIVEN"
      && x.annotation?.role !== "result"
      && x.annotation?.category !== "result",
    );
  let doi = true;
  while (doi) {
    doi = false;
    for (const o of scene.objects) {
      for (const s of [o.annotation?.same_as, o.alias_of]) {
        if (!s) continue;
        if (ra.has(o.id) && !ra.has(s) && !laDuKienDeCho(byId.get(s))) {
          ra.add(s);
          doi = true;
        } else if (ra.has(s) && !ra.has(o.id) && !laDuKienDeCho(o)) {
          ra.add(o.id);
          doi = true;
        }
      }
    }
  }
  return ra;
}

/**
 * P7 — Phân loại ngữ nghĩa của thông tin trong xưởng mô phỏng (8 vai trò chuẩn).
 * Chỉ đọc cấu trúc có sẵn trong `Scene3D` / `hybrid` / `routeDSimulation`, không dò chuỗi văn xuôi.
 */
export type LoaiThongTin =
  | "GIVEN_DIMENSION"
  | "GIVEN_RELATION"
  | "DERIVED_MEASUREMENT"
  | "CONSTRUCTION_STEP"
  | "GEOMETRY_IDENTITY"
  | "REQUESTED_RESULT"
  | "MATHEMATICAL_CERTIFICATE"
  | "ERROR_OR_REFUSAL";

export interface RouteDMathGoalView {
  goal_id: string;
  kind: string;
  goal_type?: string | null;
  call_id?: string | null;
  value_display: string;
  numerator_solid?: string | null;
  denominator_solid?: string | null;
  parent_solid?: string | null;
  cut_solid?: string | null;
  complement_ratio?: string | null;
  exact?: { coef: string; dim: number; unit: string | null } | null;
  certificate?: Record<string, unknown> | null;
}

export interface RouteDSimulationSummary {
  length_unit?: string | null;
  solids?: readonly { solid_id: string; scene_object_id?: string | null }[];
  math_goals?: readonly RouteDMathGoalView[] | null;
  answers?: Readonly<Record<string, string>> | null;
  answer_exact?: Readonly<Record<string, { coef: string; dim: number; unit: string | null }>> | null;
  verified_relations?: readonly {
    relation_id: string;
    kind: string;
    verified: boolean;
    details?: Record<string, unknown> | null;
  }[] | null;
}

export interface MucPhanTichToan {
  id: string;
  category: LoaiThongTin;
  label: string;
  notation: string | null;
  valueDisplay: string | null;
  formula: string | null;
  basisLabels: string[];
  entityId: string | null;
  certificateRule: string | null;
  provenance?: CanonicalMathProvenance;
}

export interface BangPhanTichToan {
  lengthUnit: string | null;
  givenDimensions: MucPhanTichToan[];
  givenRelations: MucPhanTichToan[];
  derivedMeasurements: MucPhanTichToan[];
  requestedResults: MucPhanTichToan[];
  certificates: MucPhanTichToan[];
}

/** Phân loại một thực thể trong `Scene3D` theo đúng vai trò ngữ nghĩa P7. */
export function phanLoaiVat(
  scene: Scene3D,
  object: SceneObject,
  ketQuaCuoi?: ReadonlySet<string>,
): LoaiThongTin {
  const kq = ketQuaCuoi ?? tapKetQuaCuoi(scene);
  if (object.type === "quantity" || object.value !== undefined) {
    if (kq.has(object.id) && !object.id.startsWith("kq_vcert")) {
      return "REQUESTED_RESULT";
    }
    if (classifyQuantityProvenance(object, scene) === "GIVEN") {
      return "GIVEN_DIMENSION";
    }
    return "DERIVED_MEASUREMENT";
  }
  if (object.perpendicular_witness?.can_present_as_proven) {
    return "MATHEMATICAL_CERTIFICATE";
  }
  if (
    object.perpendicular_witness?.status === "GIVEN"
    || Boolean(object.perpendicular_witness?.certificate)
    || object.source?.assumption
  ) {
    return "GIVEN_RELATION";
  }
  return "GEOMETRY_IDENTITY";
}

/**
 * P6/P7 — Tổng hợp thông tin cho Chế độ B («Phân tích toán học») từ `Scene3D` đã kiểm chứng,
 * `HybridPreviewView` (nếu có) và `RouteDSimulationSummary` (nếu có).
 * Không tính lại hình học, không chế lời giải văn xuôi, không dùng heuristic chuỗi.
 */
export function phanTichToanHocCuaCanh(
  scene: Scene3D,
  hybrid?: {
    answers?: readonly { quantity_id: string; symbolic: string; dim: number; unit: string | null }[];
    observations?: readonly { check_id: string; group: "goal" | "negated"; relation: string; evidence_state: string }[];
  } | null,
  routeD?: RouteDSimulationSummary | null,
): BangPhanTichToan {
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const tenNgan = (id: string) => {
    const linked = routeD?.solids?.find((s) => s.solid_id === id)?.scene_object_id;
    const o = byId.get(linked ?? id);
    return [o?.reference, o?.display_label, o?.label, o?.notation]
      .find((s) => s?.trim() && learnerTextIsSafe(scene, s)) ?? "đối tượng hình học";
  };
  const ketQua = tapKetQuaCuoi(scene, hybrid);
  const cuoi = Math.max(0, stepCount(scene) - 1);
  const lg = solutionAt(scene, cuoi);

  const hybridAnsById = new Map(
    (hybrid?.answers ?? []).map((a) => [a.quantity_id, a.symbolic]),
  );
  const routeGoalByKernelVar = new Map<string, RouteDMathGoalView>();
  for (const g of routeD?.math_goals ?? []) {
    const kv = typeof g.certificate?.kernel_var === "string" ? g.certificate.kernel_var : null;
    if (kv) routeGoalByKernelVar.set(kv, g);
    routeGoalByKernelVar.set(`kq_${g.goal_id}`, g);
    if (g.call_id) routeGoalByKernelVar.set(`kq_${g.call_id}`, g);
  }

  const hienGiaTri = (o: SceneObject): string => {
    const rg = routeGoalByKernelVar.get(o.id);
    if (rg?.value_display) return rg.value_display;
    const ha = hybridAnsById.get(o.id);
    if (ha) return ha.includes("=") ? ha.slice(ha.lastIndexOf("=") + 1).trim() : ha;
    const dv = o.annotation?.unit ? ` ${o.annotation.unit}` : "";
    const expr = hienBieuThucDaiLuong(o) ?? hienSo(o.exact, o.value);
    return `${expr}${dv}${ghiChuGiaTriDung(scene, expr, o.annotation?.kind)}`;
  };

  const givenDimensions: MucPhanTichToan[] = [];
  const daGomGiven = new Set<string>();
  const daGomCanhGiven = new Set<string>();
  const khoaCapGiven = (a: string, b: string) => (a < b ? `${a}\u0000${b}` : `${b}\u0000${a}`);
  for (const o of scene.objects) {
    if (o.type !== "quantity" || (o.value == null && !hienBieuThucDaiLuong(o))) continue;
    if (o.authoritative === false) continue;
    if (classifyQuantityProvenance(o, scene) !== "GIVEN") continue;
    if (ketQua.has(o.id)) continue;
    const goc = o.annotation?.same_as ?? o.alias_of ?? o.id;
    if (daGomGiven.has(goc)) continue;
    daGomGiven.add(goc);
    if (o.annotation?.anchor === "segment" && o.annotation.subject_ids.length === 2) {
      daGomCanhGiven.add(khoaCapGiven(o.annotation.subject_ids[0], o.annotation.subject_ids[1]));
    }
    givenDimensions.push({
      id: o.id,
      category: "GIVEN_DIMENSION",
      label: o.label,
      notation: o.notation ?? o.label,
      valueDisplay: hienGiaTri(o),
      formula: null,
      basisLabels: [],
      entityId: o.id,
      certificateRule: null,
    });
  }
  for (const hd of certifiedHybridGivenDimensions(scene)) {
    const capKey = khoaCapGiven(hd.subjectIds[0], hd.subjectIds[1]);
    if (daGomCanhGiven.has(capKey) || daGomGiven.has(hd.id)) continue;
    daGomCanhGiven.add(capKey);
    daGomGiven.add(hd.id);
    givenDimensions.push({
      id: hd.id,
      category: "GIVEN_DIMENSION",
      label: hd.label,
      notation: hd.notation,
      valueDisplay: `${hd.valueDisplay}${ghiChuGiaTriDung(scene, hd.valueDisplay, "length")}`,
      formula: null,
      basisLabels: [],
      entityId: null,
      certificateRule: "registry.kiem_nguon",
    });
  }
  if (scene.length_unit?.display_scale && scene.length_unit.is_given === true && givenDimensions.length === 0) {
    givenDimensions.push({
      id: "length_unit",
      category: "GIVEN_DIMENSION",
      label: "Tỉ lệ dựng",
      notation: scene.length_unit.symbol,
      valueDisplay: scene.length_unit.display_scale,
      formula: null,
      basisLabels: [],
      entityId: null,
      certificateRule: null,
    });
  }

  const derivedMeasurements: MucPhanTichToan[] = [];
  const daGomStep = new Set<string>(daGomGiven);
  const ungVienTrungGian = [
    ...lg.steps.map((s) => byId.get(s.id)).filter((o): o is SceneObject => !!o),
    ...scene.objects.filter(
      (o) => o.type === "quantity" && o.value != null && o.origin === "derived"
        && (!ketQua.has(o.id) || o.id.startsWith("kq_vcert")),
    ),
  ];
  for (const o of ungVienTrungGian) {
    const goc = o.annotation?.same_as ?? o.alias_of ?? o.id;
    if (daGomStep.has(goc) || daGomStep.has(o.id)) continue;
    if (ketQua.has(o.id) && !o.id.startsWith("kq_vcert")) continue;
    const prov = classifySceneEntityProvenance(scene, o);
    if (prov === "INVALID" || prov === "ILLUSTRATIVE") continue;
    daGomStep.add(goc);
    daGomStep.add(o.id);
    const isUnder = prov === "UNDERDETERMINED";
    const cf = isUnder ? null : coherentFormula(scene, o);
    derivedMeasurements.push({
      id: o.id,
      category: "DERIVED_MEASUREMENT",
      label: o.label,
      notation: o.notation ?? null,
      valueDisplay: isUnder ? "Chưa đủ dữ kiện xác định duy nhất" : hienGiaTri(o),
      formula: cf && cf.references.length > 0 ? cf.text : null,
      basisLabels: numericalBasis(scene, o).map(tenNgan),
      entityId: o.id,
      certificateRule: null,
      provenance: prov,
    });
  }

  const requestedResults: MucPhanTichToan[] = [];
  const daGomKq = new Set<string>();
  const ungVienKq = [
    ...lg.results.map((r) => byId.get(r.id)).filter((o): o is SceneObject => !!o),
    ...scene.objects.filter((o) => o.type === "quantity" && o.value != null && ketQua.has(o.id)),
  ];
  for (const o of ungVienKq) {
    if (o.id.startsWith("kq_vcert")) continue;
    const goc = o.annotation?.same_as ?? o.alias_of ?? o.id;
    if (daGomKq.has(goc) || daGomKq.has(o.id)) continue;
    const rg = routeGoalByKernelVar.get(o.id);
    const certRule = typeof rg?.certificate?.rule === "string" ? rg.certificate.rule : null;
    const prov: CanonicalMathProvenance = certRule ? "DERIVED_VERIFIED" : classifySceneEntityProvenance(scene, o);
    if (prov === "INVALID" || prov === "ILLUSTRATIVE") continue;
    daGomKq.add(goc);
    daGomKq.add(o.id);
    const isUnder = prov === "UNDERDETERMINED";
    const cf = isUnder ? null : coherentFormula(scene, o);
    requestedResults.push({
      id: o.id,
      category: "REQUESTED_RESULT",
      label: o.label,
      notation: o.notation ?? null,
      valueDisplay: isUnder ? "Chưa đủ dữ kiện xác định duy nhất" : hienGiaTri(o),
      formula: cf && cf.references.length > 0 ? cf.text : null,
      basisLabels: numericalBasis(scene, o).map(tenNgan),
      entityId: o.id,
      certificateRule: certRule,
      provenance: prov,
    });
  }

  for (const g of routeD?.math_goals ?? []) {
    const kv = typeof g.certificate?.kernel_var === "string" ? g.certificate.kernel_var : null;
    if (kv && byId.has(kv)) continue;
    if (byId.has(`kq_${g.goal_id}`) || (g.call_id && byId.has(`kq_${g.call_id}`))) continue;
    if (g.kind === "volume_ratio") {
      const num = g.numerator_solid ? tenNgan(g.numerator_solid) : "khối con";
      const den = g.denominator_solid ? tenNgan(g.denominator_solid) : "khối gốc";
      requestedResults.push({
        id: `goal:${g.goal_id}`,
        category: "REQUESTED_RESULT",
        label: `Tỉ số thể tích ${num} và ${den}`,
        notation: `V(${num}) / V(${den})`,
        valueDisplay: g.value_display,
        formula: null,
        basisLabels: [num, den],
        entityId: null,
        certificateRule: typeof g.certificate?.rule === "string" ? g.certificate.rule : null,
      });
    } else if (g.kind === "residual_volume") {
      const par = g.parent_solid ? tenNgan(g.parent_solid) : "khối gốc";
      const cut = g.cut_solid ? tenNgan(g.cut_solid) : "khối cắt";
      requestedResults.push({
        id: `goal:${g.goal_id}`,
        category: "REQUESTED_RESULT",
        label: `Thể tích phần còn lại (${par} trừ ${cut})`,
        notation: `V(${par}) − V(${cut})`,
        valueDisplay: g.value_display,
        formula: g.complement_ratio ? `Tỉ số phần còn lại = ${g.complement_ratio}` : null,
        basisLabels: [par, cut],
        entityId: null,
        certificateRule: typeof g.certificate?.rule === "string" ? g.certificate.rule : null,
      });
    } else {
      requestedResults.push({
        id: `goal:${g.goal_id}`,
        category: "REQUESTED_RESULT",
        label: "Kết quả đã kiểm chứng",
        notation: null,
        valueDisplay: g.value_display,
        formula: null,
        basisLabels: [],
        entityId: null,
        certificateRule: typeof g.certificate?.rule === "string" ? g.certificate.rule : null,
      });
    }
  }

  const givenRelations: MucPhanTichToan[] = [];
  const certificates: MucPhanTichToan[] = [];
  // Nhiều điểm cùng MỘT giả định (vd mọi đỉnh "hệ trục …") ⇒ một dòng, không lặp từng điểm; giả định riêng giữ dòng của điểm.
  const diemTheoGiaDinh = new Map<string, SceneObject[]>();
  for (const o of scene.objects) {
    if (o.authoritative !== false && o.type === "point3" && o.source?.assumption) {
      diemTheoGiaDinh.set(o.source.assumption, [...(diemTheoGiaDinh.get(o.source.assumption) ?? []), o]);
    }
  }
  const giaDinhDaGhi = new Set<string>();
  for (const o of scene.objects) {
    if (o.authoritative === false) continue;
    if (o.perpendicular_witness?.can_present_as_proven) {
      certificates.push({
        id: `cert:perp:${o.id}`,
        category: "MATHEMATICAL_CERTIFICATE",
        label: o.label,
        notation: o.notation ?? null,
        valueDisplay: o.role ?? "Quan hệ vuông góc đã kiểm chứng",
        formula: null,
        basisLabels: (o.depends ?? []).map(tenNgan),
        entityId: o.id,
        certificateRule: o.perpendicular_witness.certificate ?? null,
      });
    } else if (
      o.perpendicular_witness
      && (o.perpendicular_witness.status === "GIVEN" || Boolean(o.perpendicular_witness.certificate))
    ) {
      const w = o.perpendicular_witness;
      const fromObj = w.from ? byId.get(w.from) : undefined;
      const onObj = w.on ? byId.get(w.on) : undefined;
      const footObj = w.foot_id ? byId.get(w.foot_id) : undefined;
      const segSym =
        o.notation?.trim()
        || (fromObj?.notation && footObj?.notation ? `${fromObj.notation}${footObj.notation}` : o.label);
      const onSym = onObj?.notation?.trim()
        ? (onObj.type === "polygon3" || onObj.type === "plane3"
            ? `(${onObj.notation.replace(/^\(|\)$/gu, "")})`
            : onObj.notation)
        : (onObj ? tenNgan(onObj.id) : "");
      const footSuffix = footObj?.notation ? ` tại ${footObj.notation}` : "";
      const perpDisplay = onSym ? `${segSym} ⊥ ${onSym}${footSuffix}` : (o.role ?? "Quan hệ vuông góc từ giả thiết");
      givenRelations.push({
        id: `rel:perp:${o.id}`,
        category: "GIVEN_RELATION",
        label: o.label,
        notation: o.notation ?? null,
        valueDisplay: perpDisplay,
        formula: null,
        basisLabels: (o.depends ?? []).map(tenNgan),
        entityId: o.id,
        certificateRule: w.certificate ?? null,
      });
    } else if (o.type === "section" || o.surface_role === "SECTION_REGION") {
      certificates.push({
        id: `cert:sec:${o.id}`,
        category: "MATHEMATICAL_CERTIFICATE",
        label: o.label,
        notation: o.notation ?? null,
        valueDisplay: o.role ?? "Thiết diện phẳng đã kiểm chứng",
        formula: null,
        basisLabels: (o.depends ?? []).map(tenNgan),
        entityId: o.id,
        certificateRule: "verified_plane_section",
      });
    } else if (o.source?.assumption && (diemTheoGiaDinh.get(o.source.assumption)?.length ?? 0) > 1 && o.type === "point3") {
      if (giaDinhDaGhi.has(o.source.assumption)) continue;
      giaDinhDaGhi.add(o.source.assumption);
      const ds = diemTheoGiaDinh.get(o.source.assumption)!;
      givenRelations.push({
        id: `rel:assump:${ds.map((x) => x.id).join(",")}`,
        category: "GIVEN_RELATION",
        label: `Điểm ${ds.map((x) => x.notation ?? x.id).join(", ")}`,
        notation: null,
        valueDisplay: o.source.assumption,
        formula: null,
        basisLabels: [],
        entityId: null,
        certificateRule: null,
      });
    } else if (o.source?.assumption) {
      givenRelations.push({
        id: `rel:assump:${o.id}`,
        category: "GIVEN_RELATION",
        label: o.label,
        notation: o.notation ?? null,
        valueDisplay: o.source.assumption,
        formula: null,
        basisLabels: [],
        entityId: o.id,
        certificateRule: null,
      });
    }
  }
  for (const rel of routeD?.verified_relations ?? []) {
    if (!rel.verified) continue;
    givenRelations.push({
      id: `rel:${rel.relation_id}`,
      category: "GIVEN_RELATION",
      label: rel.kind === "shared_faces" ? "Chung mặt đa diện" : "Chung đỉnh đa diện",
      notation: null,
      valueDisplay: "Đã kiểm chứng khớp toạ độ giữa hai khối",
      formula: null,
      basisLabels: [],
      entityId: null,
      certificateRule: rel.kind,
    });
  }
  for (const g of routeD?.math_goals ?? []) {
    const rule = typeof g.certificate?.rule === "string" ? g.certificate.rule : null;
    if (!rule) continue;
    if (g.kind === "volume_ratio" || g.kind === "residual_volume") {
      certificates.push({
        id: `cert:goal:${g.goal_id}`,
        category: "MATHEMATICAL_CERTIFICATE",
        label: g.kind === "volume_ratio" ? "Chứng chỉ tỉ số thể tích" : "Chứng chỉ thể tích phần còn lại",
        notation: g.value_display,
        valueDisplay: g.complement_ratio ? `Tỉ số bù = ${g.complement_ratio}` : `Tỉ số = ${g.value_display}`,
        formula: null,
        basisLabels: [],
        entityId: null,
        certificateRule: rule,
      });
    }
  }

  for (const cd of certifiedCuttingPlaneDistanceGivens(scene)) {
    if (daGomGiven.has(cd.id)) continue;
    daGomGiven.add(cd.id);
    givenDimensions.push({
      id: cd.id,
      category: "GIVEN_DIMENSION",
      label: cd.label,
      notation: cd.notation,
      valueDisplay: `${cd.valueDisplay}${ghiChuGiaTriDung(scene, cd.valueDisplay, "distance")}`,
      formula: null,
      basisLabels: [],
      entityId: null,
      certificateRule: "exact_plane_distance",
      provenance: "GIVEN",
    });
  }

  for (const item of givenDimensions) {
    item.provenance ??= "GIVEN";
  }
  for (const item of certificates) {
    item.provenance ??= "DERIVED_VERIFIED";
  }
  for (const item of givenRelations) {
    item.provenance ??= item.id.startsWith("rel:assump:") ? "ILLUSTRATIVE" : "GIVEN";
  }
  for (const item of [...derivedMeasurements, ...requestedResults]) {
    const qObj = item.entityId ? byId.get(item.entityId) : undefined;
    item.provenance ??= qObj ? classifySceneEntityProvenance(scene, qObj) : "DERIVED_VERIFIED";
  }

  // Unknown internal names remain available through entity ids, never as learner labels.
  for (const item of [...givenDimensions, ...givenRelations, ...derivedMeasurements, ...requestedResults, ...certificates]) {
    if (!learnerTextIsSafe(scene, item.label)) item.label = "Đại lượng hoặc quan hệ đã kiểm chứng";
    if (item.notation && !learnerTextIsSafe(scene, item.notation)) item.notation = null;
    if (item.formula && !learnerTextIsSafe(scene, item.formula)) item.formula = null;
    item.basisLabels = item.basisLabels.map((s) => learnerTextIsSafe(scene, s) ? s : "đối tượng hình học");
  }
  return {
    lengthUnit: routeD?.length_unit ?? scene.length_unit?.symbol ?? null,
    givenDimensions,
    givenRelations,
    derivedMeasurements,
    requestedResults,
    certificates,
  };
}



export interface AttachedHybridSceneMetadata {
  adapter_version?: string;
  /** Source-bound exact answers (`HybridPreviewView.answers`): quantity ID + coefficient checked against the scene. */
  answers?: readonly { quantity_id: string; coefficient?: string }[];
  source_provenance?: readonly {
    id?: string | null;
    fn?: string;
    args?: Record<string, unknown> | null;
    quotes?: readonly string[];
    origin?: string | null;
    fact_id?: string | null;
    kind?: string;
    verified?: boolean;
    polygon?: readonly string[];
    edge?: readonly string[];
    points?: readonly string[];
    vertex?: string;
    rays?: readonly (readonly string[])[];
    line?: string;
    plane?: readonly string[];
    value_display?: string | null;
  }[];
  relation_certificates?: readonly {
    relation_id?: string | null;
    kind?: string;
    verified?: boolean;
    schema?: string;
    SOURCE_GROUNDING_PROOF?: { verified: boolean; [k: string]: unknown } | null;
    GEOMETRIC_RELATION_PROOF?: { verified: boolean; [k: string]: unknown } | null;
    KERNEL_EXECUTION_PROOF?: { verified: boolean; [k: string]: unknown } | null;
    RESULT_CERTIFICATE?: { verified: boolean; [k: string]: unknown } | null;
    rule?: string | null;
    details?: Record<string, unknown> | null;
  }[];
}

const _exactSceneOrigin = new WeakMap<object, Scene3D>();
const _worldTransformedScenes = new WeakSet<object>();
const _hybridViewByScene = new WeakMap<object, AttachedHybridSceneMetadata>();

/**
 * Đính kèm metadata `HybridPreviewView` đã kiểm chứng vào một cảnh mà KHÔNG sửa đổi (`mutate`) payload `envelope.scene3d`.
 * Tự động kế thừa qua `registerExactSceneOrigin` và `propagateSceneLineage`.
 */
export function attachHybridViewToScene<T extends AttachedHybridSceneMetadata>(
  scene: Pick<Scene3D, "objects"> | null | undefined,
  view: T | null | undefined,
): void {
  if (!scene || typeof scene !== "object") return;
  if (!view) {
    _hybridViewByScene.delete(scene as object);
    return;
  }
  _hybridViewByScene.set(scene as object, view);
  const exact = _exactSceneOrigin.get(scene as object);
  if (exact && exact !== scene) {
    _hybridViewByScene.set(exact as object, view);
  }
}

export function hybridViewOfScene<T extends AttachedHybridSceneMetadata = AttachedHybridSceneMetadata>(
  scene: Pick<Scene3D, "objects"> | null | undefined,
): T | null {
  if (!scene || typeof scene !== "object") return null;
  const direct = _hybridViewByScene.get(scene as object);
  if (direct) return direct as T;
  const orig = _exactSceneOrigin.get(scene as object);
  if (orig && orig !== scene) {
    return (_hybridViewByScene.get(orig as object) as T | undefined) ?? null;
  }
  return null;
}

/**
 * Liên kết cảnh hiển thị (đã qua Cholesky `veKhongGian` làm tròn 1e-9 sang thế giới Euclid)
 * với cảnh hữu tỉ gốc trên khung affine `Q^3` + `chart_metric`, đảm bảo mọi phép kiểm chứng
 * đại số và suy dẫn kết luận toán học luôn chạy trên tọa độ phân số chính xác tuyệt đối.
 */
export function registerExactSceneOrigin(displayScene: Scene3D, exactScene: Scene3D): Scene3D {
  if (displayScene !== exactScene) {
    const rootExact = exactSceneOriginOf(exactScene);
    _exactSceneOrigin.set(displayScene, rootExact);
    const hv = _hybridViewByScene.get(exactScene as object) ?? _hybridViewByScene.get(rootExact as object);
    if (hv) {
      _hybridViewByScene.set(displayScene as object, hv);
    }
  }
  return displayScene;
}

export function exactSceneOriginOf<T extends Pick<Scene3D, "objects">>(scene: T): T {
  return (_exactSceneOrigin.get(scene as object) as unknown as T | undefined) ?? scene;
}

export function markSceneWorldTransformed(scene: Scene3D): Scene3D {
  _worldTransformedScenes.add(scene);
  return scene;
}

const _derivedSceneParent = new WeakMap<object, Scene3D>();

export function registerDerivedSceneParent(nextScene: Scene3D, prevScene: Scene3D): Scene3D {
  if (nextScene !== prevScene) {
    _derivedSceneParent.set(nextScene, prevScene);
  }
  return nextScene;
}

export function derivedSceneParentOf(scene: Pick<Scene3D, "objects">): Scene3D | undefined {
  return _derivedSceneParent.get(scene as object);
}

export function isSceneWorldTransformed(scene: Pick<Scene3D, "objects">): boolean {
  return _worldTransformedScenes.has(scene as object);
}

export function propagateSceneLineage(nextScene: Scene3D, prevScene: Scene3D, exactNextOverride?: Scene3D): Scene3D {
  registerDerivedSceneParent(nextScene, prevScene);
  if (nextScene === prevScene) return nextScene;
  if (isSceneWorldTransformed(prevScene)) {
    markSceneWorldTransformed(nextScene);
  }
  const prevHv = hybridViewOfScene(prevScene);
  if (prevHv) {
    _hybridViewByScene.set(nextScene as object, prevHv);
    if (exactNextOverride) {
      _hybridViewByScene.set(exactNextOverride as object, prevHv);
    }
  }
  if (exactNextOverride) {
    registerExactSceneOrigin(nextScene, exactNextOverride);
  } else {
    const orig = exactSceneOriginOf(prevScene);
    if (orig !== prevScene) {
      registerExactSceneOrigin(nextScene, orig);
    }
  }
  return nextScene;
}

/**
 * Kiểm tra cấu trúc và tính hợp lệ phân số (`Exact`) sâu của `Scene3D` trước khi đưa vào sequencer / renderer.
 * Dùng `toNumber` làm thẩm quyền duy nhất kiểm tra chuỗi tọa độ (tuyệt đối không dùng float parser phụ).
 */
export function inspectScene3DPayloadIntegrity(
  raw: unknown,
): { valid: true } | { valid: false; reason: string } {
  if (!raw || typeof raw !== "object") {
    return { valid: false, reason: "Dữ liệu Scene3D không phải đối tượng hợp lệ." };
  }
  const s = raw as Record<string, unknown>;
  if (!Array.isArray(s.objects) || !Array.isArray(s.events) || !Array.isArray(s.free_objects)) {
    return { valid: false, reason: "Dữ liệu Scene3D thiếu danh sách đối tượng hoặc sự kiện dựng hình." };
  }
  if (s.free_objects.some((id) => typeof id !== "string" || !id.trim())) {
    return { valid: false, reason: "Danh sách đối tượng tự do chứa định danh không hợp lệ." };
  }

  const hopLeExact = (v: unknown): boolean => {
    if (typeof v !== "string" && (typeof v !== "number" || !Number.isFinite(v))) return false;
    try {
      toNumber(v as Exact);
      return true;
    } catch {
      return false;
    }
  };
  const hopLeVec3 = (v: unknown): boolean =>
    Array.isArray(v) && v.length === 3 && v.every(hopLeExact);

  if (s.chart_metric !== undefined && s.chart_metric !== null) {
    if (
      !Array.isArray(s.chart_metric)
      || s.chart_metric.length !== 3
      || s.chart_metric.some((row) => !Array.isArray(row) || row.length !== 3 || row.some((c) => !hopLeExact(c)))
    ) {
      return { valid: false, reason: "Ma trận chart_metric của Scene3D sai cấu trúc phân số." };
    }
  }

  const singleVecKeys = ["xyz", "point", "normal", "direction", "point_a", "point_b", "center", "axis"] as const;
  const listVecKeys = ["vertices", "polygon"] as const;

  for (const obj of s.objects) {
    if (!obj || typeof obj !== "object") {
      return { valid: false, reason: "Scene3D chứa phần tử đối tượng rỗng hoặc sai kiểu." };
    }
    const rec = obj as Record<string, unknown>;
    if (typeof rec.id !== "string" || !rec.id.trim() || typeof rec.type !== "string" || !rec.type.trim()) {
      return { valid: false, reason: "Đối tượng trong Scene3D thiếu mã định danh hoặc kiểu hình học." };
    }
    if (rec.depends !== undefined && (!Array.isArray(rec.depends) || rec.depends.some((d) => typeof d !== "string"))) {
      return { valid: false, reason: `Đối tượng ${rec.id} có danh sách phụ thuộc sai kiểu.` };
    }
    if (rec.type === "point3" && rec.render !== "non_visual" && !hopLeVec3(rec.xyz)) {
      return { valid: false, reason: `Điểm ${rec.id} thiếu hoặc sai tọa độ không gian 3 chiều.` };
    }
    for (const k of singleVecKeys) {
      if (rec[k] !== undefined && rec[k] !== null && !hopLeVec3(rec[k])) {
        return { valid: false, reason: `Trường tọa độ ${k} của ${rec.id} không phải bộ ba phân số hợp lệ.` };
      }
    }
    for (const k of listVecKeys) {
      if (rec[k] !== undefined && rec[k] !== null) {
        if (!Array.isArray(rec[k]) || (rec[k] as unknown[]).some((pt) => !hopLeVec3(pt))) {
          return { valid: false, reason: `Danh sách tọa độ ${k} của ${rec.id} không hợp lệ.` };
        }
      }
    }
    for (const scalarKey of ["radius_sq", "height_sq", "semi_major_sq", "semi_minor_sq"] as const) {
      if (rec[scalarKey] !== undefined && rec[scalarKey] !== null && !hopLeExact(rec[scalarKey])) {
        return { valid: false, reason: `Tham số ${scalarKey} của ${rec.id} không phải phân số hợp lệ.` };
      }
    }
  }

  for (const ev of s.events) {
    if (!ev || typeof ev !== "object") {
      return { valid: false, reason: "Sự kiện dựng hình trong Scene3D sai cấu trúc." };
    }
    const rec = ev as Record<string, unknown>;
    if (typeof rec.step_index !== "number" || !Number.isInteger(rec.step_index) || typeof rec.action !== "string") {
      return { valid: false, reason: "Sự kiện dựng hình thiếu chỉ số bước hoặc hành động hợp lệ." };
    }
  }

  return { valid: true };
}

export type QuantityProvenance = "GIVEN" | "CERTIFIED_DERIVED" | "UNVERIFIED" | "DISPLAY_ONLY";

/**
 * Phân loại nguồn gốc nhận thức (epistemic provenance) của một đại lượng trong `Scene3D`:
 * - `GIVEN`: dữ kiện trực tiếp được chứng thực từ đề bài (`origin === "free"` và không bị hạ bậc bởi `source`,
 *   đồng thời nằm trong `scene.free_objects` khi không có khóa `source` xác thực riêng).
 * - `CERTIFIED_DERIVED`: đại lượng suy ra hoặc đáp số do Kernel chứng nhận (`origin === "derived"` / `role: "intermediate" | "result"`).
 * - `UNVERIFIED`: đại lượng giả định bố cục / minh họa hoặc chưa đủ chứng thực.
 * - `DISPLAY_ONLY`: đối tượng trình bày không mang thẩm quyền toán học.
 */
export function classifyQuantityProvenance(
  o: SceneObject,
  scene?: Partial<Pick<Scene3D, "free_objects" | "objects">> | null,
): QuantityProvenance {
  const src = o.source as Record<string, unknown> | undefined;
  if (o.authoritative === false || src?.provenance === "DISPLAY_ONLY") {
    return "DISPLAY_ONLY";
  }
  const explicitRole = o.annotation?.role as string | undefined;
  const explicitCat = o.annotation?.category as string | undefined;
  const hasDerivedMarkers =
    o.origin === "derived"
    || o.producer != null
    || Boolean(src?.instruction);
  const sourceClaimsExplicitGiven =
    src?.provenance === "GIVEN"
    || src?.is_given === true
    || Boolean(src?.fact_id);
  const claimsExplicitGiven =
    sourceClaimsExplicitGiven
    || explicitRole === "given";
  if (hasDerivedMarkers && claimsExplicitGiven) {
    return "UNVERIFIED";
  }
  if (
    src?.is_given === false
    || src?.provenance === "MODEL_ASSUMPTION"
    || src?.assumption === "LAYOUT_DERIVED"
    || src?.provenance === "LAYOUT_DERIVED"
    || src?.assumption === "ILLUSTRATIVE_CONFIGURATION"
    || src?.provenance === "ILLUSTRATIVE_CONFIGURATION"
    || src?.assumption === "ILLUSTRATIVE_CHOICE"
    || src?.provenance === "ILLUSTRATIVE_CHOICE"
    || src?.provenance === "UNVERIFIED"
    || src?.assumption === "UNVERIFIED"
    || src?.binding === "AUXILIARY"
    || (typeof src?.assumption === "string" && src.assumption.trim().length > 0)
  ) {
    return "UNVERIFIED";
  }
  const hasExplicitSourceKeys = Boolean(src && Object.keys(src).length > 0);
  const inFreeObjects = scene && Array.isArray(scene.free_objects)
    ? scene.free_objects.includes(o.id)
    : true;
  const sourceConfirmsGiven =
    sourceClaimsExplicitGiven
    || (!hasExplicitSourceKeys && inFreeObjects);
  if (
    o.origin === "free"
    && !hasDerivedMarkers
    && explicitRole !== "intermediate"
    && explicitRole !== "result"
    && explicitRole !== "answer"
    && explicitCat !== "result"
    && explicitCat !== "answer"
    && sourceConfirmsGiven
  ) {
    return "GIVEN";
  }
  if (
    o.origin === "derived"
    && o.producer === null
    && !src?.instruction
    && o.exact == null
    && !(o.dependency_edges && o.dependency_edges.length > 0)
    && !o.formula
    && !o.annotation?.witness
  ) {
    return "UNVERIFIED";
  }
  if (
    hasDerivedMarkers
    || explicitRole === "intermediate"
    || explicitRole === "result"
    || explicitRole === "answer"
    || explicitCat === "result"
    || explicitCat === "answer"
  ) {
    return "CERTIFIED_DERIVED";
  }
  return "UNVERIFIED";
}

export interface CertifiedHybridGivenDimension {
  id: string;
  subjectIds: [string, string];
  notation: string;
  label: string;
  valueDisplay: string;
}

const chuanKyHieuDiem = (s: string): string => s.replace(/″/g, "''").replace(/[′’]/g, "'").trim();

/**
 * Đọc các kích thước đề cho (`segment_length`, `regular_polygon.side`) đã được `registry.kiem_nguon`
 * chứng thực trong `HybridPreviewView.source_provenance` (Adapter /4) mà KHÔNG sửa đổi `scene.objects`.
 */
export function certifiedHybridGivenDimensions(
  scene: Pick<Scene3D, "objects">,
): CertifiedHybridGivenDimension[] {
  const hv = hybridViewOfScene(scene);
  const provList = hv?.source_provenance;
  if (!Array.isArray(provList) || provList.length === 0) return [];

  const timDiem = (rawName: unknown): SceneObject | null => {
    if (typeof rawName !== "string" || !rawName.trim()) return null;
    const norm = chuanKyHieuDiem(rawName);
    const hits = scene.objects.filter(
      (o) =>
        o.type === "point3"
        && Boolean(o.xyz)
        && (o.id === rawName || (typeof o.notation === "string" && chuanKyHieuDiem(o.notation) === norm)),
    );
    return hits.length === 1 ? hits[0]! : null;
  };
  const kyHieuDiemNgan = (pt: SceneObject): string => pt.notation?.trim() || pt.label?.trim() || pt.id;
  const khoaCapDiem = (a: string, b: string) => (a < b ? `${a}\u0000${b}` : `${b}\u0000${a}`);

  const out: CertifiedHybridGivenDimension[] = [];
  const seenSeg = new Set<string>();

  for (let i = 0; i < provList.length; i += 1) {
    const sp = provList[i];
    if (!sp || sp.verified === false) continue;
    const hasQuotes = Array.isArray(sp.quotes) && sp.quotes.some((q: unknown) => typeof q === "string" && q.trim().length > 0);
    if (sp.verified !== true && !hasQuotes) continue;

    const fn = sp.fn ?? sp.kind ?? "";
    const args = sp.args && typeof sp.args === "object" ? sp.args : null;

    if (fn === "segment_length") {
      const segRaw = Array.isArray(args?.segment)
        ? args.segment
        : Array.isArray(sp.edge)
          ? sp.edge
          : null;
      const valRaw = typeof args?.value === "string" ? args.value : sp.value_display;
      if (!segRaw || segRaw.length !== 2 || typeof valRaw !== "string" || !valRaw.trim()) continue;
      const ptA = timDiem(segRaw[0]);
      const ptB = timDiem(segRaw[1]);
      if (!ptA || !ptB || ptA.id === ptB.id) continue;
      const key = khoaCapDiem(ptA.id, ptB.id);
      if (seenSeg.has(key)) continue;
      seenSeg.add(key);
      const notation = `${kyHieuDiemNgan(ptA)}${kyHieuDiemNgan(ptB)}`;
      out.push({
        id: `hybrid_given:${sp.id ?? sp.fact_id ?? i}:${ptA.id}-${ptB.id}`,
        subjectIds: [ptA.id, ptB.id],
        notation,
        label: `Độ dài ${notation}`,
        valueDisplay: valRaw.trim(),
      });
    } else if (fn === "regular_polygon") {
      const vertsRaw = Array.isArray(args?.vertices)
        ? args.vertices
        : Array.isArray(sp.polygon)
          ? sp.polygon
          : null;
      const sideRaw = typeof args?.side === "string" ? args.side : sp.value_display;
      if (!vertsRaw || vertsRaw.length < 3 || typeof sideRaw !== "string" || !sideRaw.trim()) continue;
      const pt0 = timDiem(vertsRaw[0]);
      const pt1 = timDiem(vertsRaw[1]);
      if (!pt0 || !pt1 || pt0.id === pt1.id) continue;
      const key = khoaCapDiem(pt0.id, pt1.id);
      if (seenSeg.has(key)) continue;
      seenSeg.add(key);
      const notation = `${kyHieuDiemNgan(pt0)}${kyHieuDiemNgan(pt1)}`;
      out.push({
        id: `hybrid_given:${sp.id ?? sp.fact_id ?? i}:${pt0.id}-${pt1.id}`,
        subjectIds: [pt0.id, pt1.id],
        notation,
        label: `Cạnh đáy ${notation}`,
        valueDisplay: sideRaw.trim(),
      });
    }
  }
  return out;
}

export type CanonicalMathProvenance =
  | "GIVEN"
  | "DERIVED_VERIFIED"
  | "ILLUSTRATIVE"
  | "UNDERDETERMINED"
  | "INVALID";

export interface CertifiedCuttingPlaneDistanceGiven {
  id: string;
  centerId: string;
  planeId: string;
  circleId: string;
  segmentSubjectIds: [string, string] | null;
  notation: string;
  label: string;
  valueDisplay: string;
}

interface ExactBigFrac {
  num: bigint;
  den: bigint;
}

function gcdBigIntModel(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    const t = x % y;
    x = y;
    y = t;
  }
  return x === 0n ? 1n : x;
}

function normBigFrac(num: bigint, den: bigint): ExactBigFrac | null {
  if (den === 0n) return null;
  const s = den < 0n ? -1n : 1n;
  const n = num * s;
  const d = den * s;
  const g = gcdBigIntModel(n, d);
  return { num: n / g, den: d / g };
}

function parseExactBigFrac(v: unknown): ExactBigFrac | null {
  if (typeof v === "number" && Number.isInteger(v)) {
    return { num: BigInt(v), den: 1n };
  }
  if (typeof v !== "string") return null;
  const m = /^\s*(-?\d+)(?:\/(\d+))?\s*$/.exec(v);
  if (!m) return null;
  return normBigFrac(BigInt(m[1]), m[2] !== undefined ? BigInt(m[2]) : 1n);
}

function addBigFrac(a: ExactBigFrac, b: ExactBigFrac): ExactBigFrac {
  return normBigFrac(a.num * b.den + b.num * a.den, a.den * b.den)!;
}

function subBigFrac(a: ExactBigFrac, b: ExactBigFrac): ExactBigFrac {
  return normBigFrac(a.num * b.den - b.num * a.den, a.den * b.den)!;
}

function mulBigFrac(a: ExactBigFrac, b: ExactBigFrac): ExactBigFrac {
  return normBigFrac(a.num * b.num, a.den * b.den)!;
}

function bigIntFloorSqrt(n: bigint): bigint {
  if (n <= 0n) return 0n;
  if (n < 4n) return 1n;
  let x = 1n << BigInt((n.toString(2).length + 1) >> 1);
  while (true) {
    const nx = (x + n / x) >> 1n;
    if (nx >= x) return x;
    x = nx;
  }
}

function formatExactSqrtBigFrac(sq: ExactBigFrac): string | null {
  if (sq.num < 0n || sq.den <= 0n) return null;
  if (sq.num === 0n) return "0";
  const prod = sq.num * sq.den;
  const root = bigIntFloorSqrt(prod);
  if (root * root === prod) {
    const exactRat = normBigFrac(root, sq.den);
    if (!exactRat) return null;
    return exactRat.den === 1n ? exactRat.num.toString() : `${exactRat.num}/${exactRat.den}`;
  }
  if (prod > 100_000_000n) {
    return null;
  }
  let k = 1n;
  let rem = prod;
  for (let d = 2n; d * d <= rem; d += d === 2n ? 1n : 2n) {
    while (rem % (d * d) === 0n) {
      k *= d;
      rem /= d * d;
    }
  }
  const reduced = normBigFrac(k, sq.den);
  if (!reduced) return null;
  if (rem === 1n) {
    return reduced.den === 1n ? reduced.num.toString() : `${reduced.num}/${reduced.den}`;
  }
  const rad = `${reduced.num === 1n ? "" : reduced.num.toString()}√${rem}`;
  return reduced.den === 1n ? rad : `${rad}/${reduced.den}`;
}

function exactGramDistanceSquared(
  exactScene: Pick<Scene3D, "chart_metric">,
  a: readonly [unknown, unknown, unknown],
  b: readonly [unknown, unknown, unknown],
): ExactBigFrac | null {
  const pa = [parseExactBigFrac(a[0]), parseExactBigFrac(a[1]), parseExactBigFrac(a[2])];
  const pb = [parseExactBigFrac(b[0]), parseExactBigFrac(b[1]), parseExactBigFrac(b[2])];
  if (pa.some((x) => !x) || pb.some((x) => !x)) return null;
  const dv = [
    subBigFrac(pa[0]!, pb[0]!),
    subBigFrac(pa[1]!, pb[1]!),
    subBigFrac(pa[2]!, pb[2]!),
  ];
  const rawG = !isSceneWorldTransformed(exactScene as Pick<Scene3D, "objects">) ? exactScene.chart_metric : undefined;
  let sum: ExactBigFrac = { num: 0n, den: 1n };
  for (let i = 0; i < 3; i += 1) {
    for (let j = 0; j < 3; j += 1) {
      const gij = rawG ? parseExactBigFrac(rawG[i]?.[j]) : { num: i === j ? 1n : 0n, den: 1n };
      if (!gij) return null;
      sum = addBigFrac(sum, mulBigFrac(gij, mulBigFrac(dv[i], dv[j])));
    }
  }
  return sum;
}

/**
 * Suy xuất khoảng cách đề cho `d(I, (P))` bằng số học phân số chính xác trên `exactSceneOriginOf(scene)`
 * khi mặt cầu tâm `I` (bán kính `GIVEN`) bị cắt bởi mặt phẳng phương trình độc lập `(P)` (`depends === []`)
 * ngoài hệ trục Oxyz (tương ứng `construct_plane_from_equation`). Không sửa payload `scene.objects`.
 */
export function certifiedCuttingPlaneDistanceGivens(
  scene: Pick<Scene3D, "objects" | "free_objects" | "chart_metric">,
): CertifiedCuttingPlaneDistanceGiven[] {
  const exact = exactSceneOriginOf(scene);
  const hasOxyz = exact.objects.some(
    (o) => (o.type === "line3" || o.type === "vector3") && /^(?:Ox|Oy|Oz)$/u.test((o.notation ?? o.label ?? o.id).trim()),
  );
  if (hasOxyz) return [];
  const exactById = new Map(exact.objects.map((o) => [o.id, o]));
  const dispById = new Map(scene.objects.map((o) => [o.id, o]));
  const out: CertifiedCuttingPlaneDistanceGiven[] = [];

  for (const circ of exact.objects) {
    if (circ.type !== "circle3" || !circ.center || circ.center.length !== 3) continue;
    const deps = circ.depends ?? [];
    const ball = deps.map((id) => exactById.get(id)).find((o) => o?.type === "curved_solid" && o.curved_kind === "ball");
    const plane = deps.map((id) => exactById.get(id)).find((o) => o?.type === "plane3" && o.origin === "derived" && (o.depends ?? []).length === 0);
    if (!ball || !plane) continue;
    const centerPt = (ball.depends ?? []).map((id) => exactById.get(id)).find((o) => o?.type === "point3" && Boolean(o.xyz));
    const hasGivenRad =
      (ball.depends ?? []).some((id) => {
        const q = exactById.get(id);
        return Boolean(q && q.type === "quantity" && classifyQuantityProvenance(q, exact) === "GIVEN");
      })
      || (ball.dependency_edges ?? []).some((e) => {
        const q = exactById.get(e.source_id);
        return Boolean(e.relation === "numerical" && q && q.type === "quantity" && classifyQuantityProvenance(q, exact) === "GIVEN");
      });
    if (!centerPt?.xyz || !hasGivenRad) continue;

    // Không nhân đôi nếu cảnh đã có quantity GIVEN đo khoảng cách I -> (P)
    const alreadyExplicit = exact.objects.some(
      (q) =>
        q.type === "quantity"
        && classifyQuantityProvenance(q, exact) === "GIVEN"
        && (q.depends ?? []).includes(centerPt.id)
        && (q.depends ?? []).includes(plane.id),
    );
    if (alreadyExplicit) continue;

    const dSq = exactGramDistanceSquared(exact, circ.center as [unknown, unknown, unknown], centerPt.xyz as [unknown, unknown, unknown]);
    if (!dSq || dSq.num <= 0n) continue;
    const valStr = formatExactSqrtBigFrac(dSq);
    if (!valStr) continue;

    const cSym = centerPt.notation?.trim() || centerPt.id;
    const rawPlaneSym = (plane.notation?.trim() || plane.label?.replace(/^Mặt\s+phẳng\s+/iu, "").trim() || plane.id);
    const pSym = rawPlaneSym.startsWith("(") && rawPlaneSym.endsWith(")") ? rawPlaneSym : `(${rawPlaneSym})`;
    const notation = `d(${cSym}, ${pSym})`;
    let footPtId: string | null = null;
    for (const cand of dispById.values()) {
      if (cand.type === "point3" && cand.id !== centerPt.id && Boolean(cand.xyz)) {
        if (cand.perpendicular_witness?.from === centerPt.id && cand.perpendicular_witness?.on === plane.id) {
          footPtId = cand.id;
          break;
        }
        const candXyz = (exactById.get(cand.id)?.xyz ?? cand.xyz) as [unknown, unknown, unknown];
        const zeroDist = exactGramDistanceSquared(exact, circ.center as [unknown, unknown, unknown], candXyz);
        if (zeroDist && zeroDist.num === 0n) {
          footPtId = cand.id;
        }
      } else if (cand.type === "segment3" && cand.perpendicular_witness?.on === plane.id && cand.endpoint_ids?.length === 2) {
        const [u, v] = cand.endpoint_ids;
        if (u === centerPt.id && dispById.get(v)?.type === "point3") { footPtId = v; break; }
        if (v === centerPt.id && dispById.get(u)?.type === "point3") { footPtId = u; break; }
      }
    }
    const segIds: [string, string] | null = footPtId ? [centerPt.id, footPtId] : null;
    out.push({
      id: `plane_dist_given:${ball.id}:${plane.id}`,
      centerId: centerPt.id,
      planeId: plane.id,
      circleId: circ.id,
      segmentSubjectIds: segIds,
      notation,
      label: `Khoảng cách từ ${cSym} đến ${pSym}`,
      valueDisplay: valStr,
    });
  }
  return out;
}

function isRigidGaugeAssumptionText(text: unknown): boolean {
  if (typeof text !== "string") return false;
  const s = text.trim();
  return (
    /^hệ\s+trục\s+(?:do\s+đề\s+chọn|đã\s+chọn)$/iu.test(s)
    || /^chọn\s+(?:tâm|đỉnh|điểm)\s+\S+\s+làm\s+gốc\s+to[ạa]\s+độ$/iu.test(s)
    || /^đặt\s+.+(?:tại\s+gốc\s+to[ạa]\s+độ|làm\s+gốc\s+to[ạa]\s+độ|dọc\s+trục\s+.+|trên\s+pháp\s+tuyến\s+.+)$/iu.test(s)
  );
}

function hasNonRigidMetricSource(o: SceneObject | undefined): boolean {
  if (!o) return false;
  const src = o.source as Record<string, unknown> | undefined;
  if (!src) return false;
  if (src.is_given === false) return true;
  const prov = typeof src.provenance === "string" ? src.provenance.trim().toUpperCase() : "";
  const assumpRaw = typeof src.assumption === "string" ? src.assumption.trim() : "";
  const assumpUpper = assumpRaw.toUpperCase();
  const nonRigidTokens = new Set([
    "UNDERDETERMINED",
    "UNKNOWN",
    "UNVERIFIED",
    "ILLUSTRATIVE",
    "ILLUSTRATIVE_CHOICE",
    "ILLUSTRATIVE_CONFIGURATION",
  ]);
  if (nonRigidTokens.has(prov) || nonRigidTokens.has(assumpUpper)) return true;
  if (prov === "LAYOUT_DERIVED" || assumpUpper === "LAYOUT_DERIVED") {
    return o.type === "quantity" || assumpUpper === "LAYOUT_DERIVED";
  }
  if (prov === "MODEL_ASSUMPTION" && !isRigidGaugeAssumptionText(assumpRaw || src.model_assumption)) {
    return true;
  }
  if (assumpRaw && !isRigidGaugeAssumptionText(assumpRaw)) {
    return true;
  }
  return false;
}

interface SceneMetricRigidityAnalysis {
  illustrativePolyIds: Set<string>;
  unpinnedPointIds: Set<string>;
}

const _rigidityCache = new WeakMap<object, SceneMetricRigidityAnalysis>();

function analyzeSceneMetricRigidity(
  scene: Pick<Scene3D, "objects" | "free_objects" | "chart_metric">,
): SceneMetricRigidityAnalysis {
  const exact = exactSceneOriginOf(scene);
  const cached = _rigidityCache.get(exact as object);
  if (cached) return cached;

  const empty: SceneMetricRigidityAnalysis = {
    illustrativePolyIds: new Set<string>(),
    unpinnedPointIds: new Set<string>(),
  };
  const hasOxyz = exact.objects.some(
    (o) => (o.type === "line3" || o.type === "vector3") && /^(?:Ox|Oy|Oz)$/u.test((o.notation ?? o.label ?? o.id).trim()),
  );
  if (hasOxyz) {
    _rigidityCache.set(exact as object, empty);
    return empty;
  }

  // Nếu chart_metric khác ma trận đơn vị, metric đã được compiler nhúng trực tiếp vào Gram matrix.
  if (!isSceneWorldTransformed(exact) && Array.isArray(exact.chart_metric) && exact.chart_metric.length === 3) {
    let isIdentity = true;
    for (let i = 0; i < 3; i += 1) {
      for (let j = 0; j < 3; j += 1) {
        const f = parseExactBigFrac(exact.chart_metric[i]?.[j]);
        const target = i === j ? 1n : 0n;
        if (!f || f.den !== 1n || f.num !== target) {
          isIdentity = false;
        }
      }
    }
    if (!isIdentity) {
      _rigidityCache.set(exact as object, empty);
      return empty;
    }
  }

  const givenQuantities = exact.objects.filter(
    (o) => o.type === "quantity" && !o.annotation?.same_as && classifyQuantityProvenance(o, exact) === "GIVEN",
  );
  const hybridGivenDims = certifiedHybridGivenDimensions(scene);
  if (givenQuantities.length === 0 && hybridGivenDims.length === 0) {
    _rigidityCache.set(exact as object, empty);
    return empty;
  }

  const byId = new Map(exact.objects.map((o) => [o.id, o]));
  const illustrativePolyIds = new Set<string>();
  const unpinnedPointIds = new Set<string>();
  const pairKey = (a: string, b: string) => (a < b ? `${a}\u0000${b}` : `${b}\u0000${a}`);

  const hybridMeta = hybridViewOfScene(scene) ?? hybridViewOfScene(exact);
  const provList = hybridMeta?.source_provenance ?? [];

  const entityPointsIfContainedInBase = (
    objId: string,
    basePolyId: string,
    vertSet: ReadonlySet<string>,
  ): string[] | null => {
    if (objId === basePolyId) return [...vertSet];
    const ent = byId.get(objId);
    if (!ent) return null;
    if (ent.type === "point3") {
      return vertSet.has(ent.id) ? [ent.id] : null;
    }
    if (ent.type === "segment3" || ent.type === "line3" || ent.type === "vector3") {
      const pts = [...new Set([...(ent.endpoint_ids ?? []), ...(ent.depends ?? [])])].filter(
        (id) => byId.get(id)?.type === "point3",
      );
      return pts.length > 0 && pts.every((p) => vertSet.has(p)) ? pts : null;
    }
    if (ent.type === "polygon3" || ent.type === "plane3") {
      const pts = [...new Set([...(ent.vertex_ids ?? []), ...(ent.depends ?? [])])].filter(
        (id) => byId.get(id)?.type === "point3",
      );
      return pts.length >= 3 && pts.every((p) => vertSet.has(p)) ? pts : null;
    }
    return null;
  };

  const entityTransitivePoints = (rootId: string): Set<string> => {
    const out = new Set<string>();
    const vis = new Set<string>();
    const qIds = [rootId];
    while (qIds.length > 0) {
      const cid = qIds.shift()!;
      if (vis.has(cid)) continue;
      vis.add(cid);
      const ent = byId.get(cid);
      if (!ent) continue;
      if (ent.type === "point3") out.add(ent.id);
      for (const nx of [...(ent.vertex_ids ?? []), ...(ent.endpoint_ids ?? []), ...(ent.depends ?? [])]) {
        if (!vis.has(nx)) qIds.push(nx);
      }
    }
    return out;
  };

  const rawSubjectIdsOfGiven = (q: SceneObject): string[] => {
    const subs = q.annotation?.subject_ids?.length ? q.annotation.subject_ids : (q.depends ?? []);
    return subs.filter((id): id is string => typeof id === "string" && id.trim().length > 0);
  };
  const detachedGivenScalarIds = givenQuantities
    .filter((q) => rawSubjectIdsOfGiven(q).length === 0)
    .map((q) => q.id);

  // Gom các đa giác đáy theo khối đa diện chủ quản để nhận diện cặp đáy tịnh tiến của lăng trụ / hình hộp
  const basePolys = exact.objects.filter(
    (o) =>
      o.type === "polygon3"
      && !o.id.includes("__")
      && (o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE"))
      && !(o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE"),
  );
  const primaryBaseIdsBySolid = new Map<string, string>();
  for (const bp of basePolys) {
    const vIds = [...new Set([...(bp.vertex_ids ?? []), ...(bp.depends ?? [])])].filter(
      (id) => byId.get(id)?.type === "point3",
    );
    const hs = exact.objects.find(
      (o) => o.type === "solid" && vIds.length >= 3 && vIds.every((v) => (o.vertex_ids ?? o.depends ?? []).includes(v)),
    );
    if (hs && !primaryBaseIdsBySolid.has(hs.id)) {
      primaryBaseIdsBySolid.set(hs.id, bp.id);
    }
  }

  for (const basePoly of basePolys) {
    const vertIds = [...new Set([...(basePoly.vertex_ids ?? []), ...(basePoly.depends ?? [])])].filter(
      (id) => byId.get(id)?.type === "point3",
    );
    const m = vertIds.length;
    if (m < 3) continue;
    if (
      vertIds.every((id) => {
        const p = byId.get(id);
        return p?.origin === "derived" && Boolean(p.producer) && !hasNonRigidMetricSource(p);
      })
    ) {
      // Đa giác đáy của khối con dẫn xuất (vd S.MI1I2I3 với M, I1, I2, I3 là trung điểm/giao điểm đã chứng minh)
      // kế thừa độ cứng từ các đỉnh gốc qua đồ thị phụ thuộc thay vì đòi dữ kiện cạnh riêng.
      continue;
    }
    const vertSet = new Set(vertIds);
    const polySyms = new Set(
      vertIds.map((id) => (byId.get(id)?.notation ?? id).trim()).filter(Boolean),
    );

    const hostSolid = exact.objects.find(
      (o) => o.type === "solid" && vertIds.every((v) => (o.vertex_ids ?? o.depends ?? []).includes(v)),
    );
    // Nếu đây là mặt đáy thứ hai của cùng một hình hộp / lăng trụ (vd day_A'B'C'D' khi day_ABCD đã là đáy gốc),
    // nó sẽ được xét cùng bậc tự do tịnh tiến của khối thay vì đòi lại một bộ cạnh đề cho trùng lặp trên nắp trên.
    if (hostSolid && primaryBaseIdsBySolid.get(hostSolid.id) && primaryBaseIdsBySolid.get(hostSolid.id) !== basePoly.id) {
      continue;
    }

    const textDecl = !hasNonRigidMetricSource(basePoly) && !hasNonRigidMetricSource(hostSolid)
      ? `${basePoly.label ?? ""} ${basePoly.role ?? ""} ${hostSolid?.label ?? ""} ${hostSolid?.role ?? ""}`
      : "";

    const genericDof = 2 * m - 3;
    let neededDof = genericDof;
    let isIsoscelesTriangle = m === 3 && /tam\s+giác\s+cân/iu.test(textDecl) && !/vuông\s+cân/iu.test(textDecl);
    let isRhombus = m === 4 && /hình\s+thoi/iu.test(textDecl);
    let isParallelogram = m === 4 && /hình\s+bình\s+hành/iu.test(textDecl);
    let isNonRightTrapezoid = m === 4 && /hình\s+thang/iu.test(textDecl) && !/hình\s+thang\s+vuông/iu.test(textDecl);

    if (/hình\s+vuông|hình\s+lập\s+phương|tứ\s+diện\s+đều|tam\s+giác\s+đều|ngũ\s+giác\s+đều|lục\s+giác\s+đều|đa\s+giác\s+đều|vuông\s+cân|(?:chóp|lăng\s+trụ)[^.,;]*\bđều\b/iu.test(textDecl)) {
      neededDof = 1;
    } else if (/hình\s+chữ\s+nhật|hình\s+hộp\s+chữ\s+nhật|hình\s+thoi|tam\s+giác\s+vuông|tam\s+giác\s+cân/iu.test(textDecl)) {
      neededDof = Math.min(neededDof, 2);
    } else if (/hình\s+bình\s+hành|hình\s+thang\s+vuông|hình\s+thang\s+cân/iu.test(textDecl)) {
      neededDof = Math.min(neededDof, 3);
    } else if (isNonRightTrapezoid) {
      neededDof = Math.min(neededDof, 4);
    }

    const hasVertNonRigid = vertIds.some((id) => hasNonRigidMetricSource(byId.get(id)));
    if (!hasVertNonRigid && !hasNonRigidMetricSource(basePoly) && !hasNonRigidMetricSource(hostSolid)) {
      const hasRightVertexGauge = vertIds.some((id) =>
        /đỉnh\s+vuông|cạnh\s+góc\s+vuông/iu.test(String(byId.get(id)?.source?.assumption ?? "")),
      );
      if (m === 3 && hasRightVertexGauge) {
        neededDof = Math.min(neededDof, 2);
      }
      if (!/hình\s+bình\s+hành|hình\s+thang|tứ\s+giác\s+lồi/iu.test(textDecl)) {
        const certifiedKernelArea = exact.objects.find((qo) => {
          if (
            qo.type !== "quantity"
            || qo.origin !== "derived"
            || qo.annotation?.kind !== "area"
            || qo.exact == null
            || hasNonRigidMetricSource(qo)
          ) {
            return false;
          }
          const structHitsBase =
            (qo.depends ?? []).includes(basePoly.id)
            || (qo.annotation?.subject_ids ?? []).includes(basePoly.id)
            || (qo.dependency_edges ?? []).some((e) => e.relation === "structural" && e.source_id === basePoly.id);
          if (!structHitsBase) return false;
          const numEdges = (qo.dependency_edges ?? []).filter((e) => e.relation === "numerical");
          if (numEdges.length < 2) return false;
          return numEdges.every((e) => {
            const sq = byId.get(e.source_id);
            return Boolean(sq && sq.type === "quantity" && classifyQuantityProvenance(sq, exact) === "GIVEN");
          });
        });
        if (certifiedKernelArea) {
          const numCount = (certifiedKernelArea.dependency_edges ?? []).filter((e) => e.relation === "numerical").length;
          neededDof = Math.min(neededDof, numCount);
        } else if (
          detachedGivenScalarIds.length >= 2
          && exact.objects.some(
            (qo) =>
              qo.type === "quantity"
              && qo.origin === "derived"
              && qo.annotation?.kind === "area"
              && qo.exact != null
              && !hasNonRigidMetricSource(qo)
              && ((qo.depends ?? []).includes(basePoly.id) || (qo.annotation?.subject_ids ?? []).includes(basePoly.id)),
          )
          && exact.objects.some(
            (ptO) =>
              ptO.type === "point3"
              && ptO.origin === "derived"
              && (ptO.depends ?? []).length === 2
              && (ptO.depends ?? []).every((did) => {
                const dobj = byId.get(did);
                return dobj?.type === "line3" || dobj?.type === "segment3";
              })
              && [...entityTransitivePoints(ptO.id)].filter((pid) => pid !== ptO.id).every((pid) => vertSet.has(pid)),
          )
        ) {
          // Chóp đều từ compiler chính tắc (tâm đáy O là giao hai đường chéo + biến vô hướng canh_day & chieu_cao)
          neededDof = 1;
        }
      }
    }

    const inPlaneRightVerts = new Set<string>();
    for (let spIdx = 0; spIdx < provList.length; spIdx++) {
      const sp = provList[spIdx];
      if (!sp || sp.verified === false) continue;
      const fn = (sp.fn ?? sp.kind ?? "").trim().toLowerCase();
      const argsRec = sp.args && typeof sp.args === "object" ? sp.args : {};
      const polyRaw = sp.polygon as unknown;
      const explicitPolyMatch =
        typeof polyRaw === "string"
        && (polyRaw.trim() === basePoly.id || polySyms.has(polyRaw.trim()));
      const rawVerts = [
        ...(Array.isArray(polyRaw) ? (polyRaw as unknown[]) : []),
        ...(Array.isArray(sp.points) ? sp.points : []),
        ...(Array.isArray(argsRec.vertices) ? (argsRec.vertices as unknown[]) : []),
      ];
      const matchesBase =
        explicitPolyMatch
        || (rawVerts.length > 0 && rawVerts.every((t) => typeof t === "string" && (vertSet.has(t.trim()) || polySyms.has(t.trim()))));
      if (!matchesBase) continue;
      if (fn === "regular_polygon" || fn === "square" || fn === "equilateral_triangle") {
        neededDof = 1;
      } else if (fn === "rectangle" || fn === "right_triangle") {
        neededDof = Math.min(neededDof, 2);
      } else if (fn === "rhombus") {
        isRhombus = true;
        neededDof = Math.min(neededDof, 2);
      } else if (fn === "isosceles_triangle") {
        isIsoscelesTriangle = true;
        neededDof = Math.min(neededDof, 2);
      } else if (fn === "parallelogram") {
        isParallelogram = true;
        neededDof = Math.min(neededDof, 3);
      } else if (fn === "trapezoid") {
        isNonRightTrapezoid = true;
        neededDof = Math.min(neededDof, 4);
      } else if (fn === "right_angle" || fn === "line_perp_line" || fn === "perpendicular_lines") {
        const vSym = typeof sp.vertex === "string" ? sp.vertex.trim() : "";
        const matchedVid = vSym
          ? vertIds.find((vid) => vid === vSym || (byId.get(vid)?.notation ?? "").trim() === vSym)
          : undefined;
        inPlaneRightVerts.add(matchedVid ?? `__prov_ra_${spIdx}`);
      }
    }

    // Nhân chứng vuông góc phẳng nằm trọn trong mặt đáy: giảm trên genericDof (tối đa m-1 góc vuông độc lập),
    // tuyệt đối không trừ lặp lần hai trên họ đã hàm chứa góc vuông (tam giác vuông / hình chữ nhật / hình thang vuông).
    for (const o of exact.objects) {
      if (hasNonRigidMetricSource(o)) continue;
      const w = o.perpendicular_witness ?? o.annotation?.witness;
      if (!w) continue;
      if (
        w.relation !== "line_perp_line"
        && w.relation !== "lines_perpendicular"
        && w.relation !== "perpendicular_lines"
      ) {
        continue;
      }
      if (!w.from || !w.on) continue;
      const fromInBase = entityPointsIfContainedInBase(w.from, basePoly.id, vertSet);
      const onInBase = entityPointsIfContainedInBase(w.on, basePoly.id, vertSet);
      if (!fromInBase || !onInBase) continue;
      const fId = w.foot_id ?? vertIds.find((vid) => {
        const vp = byId.get(vid);
        return Boolean(vp?.xyz && w.foot && vp.xyz.every((c, idx) => String(c) === String(w.foot![idx])));
      });
      if (fId && vertSet.has(fId)) {
        inPlaneRightVerts.add(fId);
      }
    }
    const maxIndependentRightAngles = m === 3 ? 1 : Math.max(0, m - 1);
    const rightAngleCount = Math.min(maxIndependentRightAngles, inPlaneRightVerts.size);
    if (rightAngleCount > 0) {
      neededDof = Math.min(neededDof, Math.max(1, genericDof - rightAngleCount));
      if (isIsoscelesTriangle || isRhombus) {
        neededDof = 1;
      } else if (isParallelogram) {
        neededDof = Math.min(neededDof, 2);
      } else if (isNonRightTrapezoid) {
        neededDof = Math.min(neededDof, 3);
      }
    }

    const givenBaseEdges = new Map<string, [string, string]>();
    let extraInPlaneConstraints = 0;

    for (const q of givenQuantities) {
      const rawSubs = rawSubjectIdsOfGiven(q);
      if (rawSubs.length === 0) continue;
      const resolvedPerSub = rawSubs.map((sid) => entityPointsIfContainedInBase(sid, basePoly.id, vertSet));
      if (resolvedPerSub.some((pts) => pts === null)) {
        // Có chủ thể nằm ngoài mặt đáy (vd góc giữa SB và đáy, khoảng cách đường chéo ngoài đáy...) -> không tính vào DoF đáy!
        continue;
      }
      if (
        rawSubs.length === 2
        && byId.get(rawSubs[0])?.type === "point3"
        && byId.get(rawSubs[1])?.type === "point3"
        && rawSubs[0] !== rawSubs[1]
      ) {
        givenBaseEdges.set(pairKey(rawSubs[0], rawSubs[1]), [rawSubs[0], rawSubs[1]]);
      } else if (
        rawSubs.length === 1
        && byId.get(rawSubs[0])?.type === "segment3"
        && resolvedPerSub[0]!.length === 2
        && resolvedPerSub[0]![0] !== resolvedPerSub[0]![1]
      ) {
        const [u, v] = resolvedPerSub[0]!;
        givenBaseEdges.set(pairKey(u, v), [u, v]);
      } else {
        extraInPlaneConstraints += 1;
      }
    }
    for (const hd of hybridGivenDims) {
      const [u, v] = hd.subjectIds;
      if (vertSet.has(u) && vertSet.has(v) && u !== v) {
        givenBaseEdges.set(pairKey(u, v), [u, v]);
      }
    }

    const detachedBaseContribution = givenBaseEdges.size === 0 && extraInPlaneConstraints === 0 && detachedGivenScalarIds.length > 0 ? 1 : 0;
    const inPlaneCount = givenBaseEdges.size + extraInPlaneConstraints + detachedBaseContribution;
    const siblingTopPolys = exact.objects.filter(
      (tp) =>
        tp.type === "polygon3"
        && tp.id !== basePoly.id
        && !tp.id.includes("__")
        && (
          (tp.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
          || (hostSolid && primaryBaseIdsBySolid.get(hostSolid.id) === basePoly.id && tp.surface_role === "BASE_REGION")
        ),
    );

    if (inPlaneCount < neededDof || hasVertNonRigid) {
      illustrativePolyIds.add(basePoly.id);
      const outPerpFootId =
        exact.objects
          .map((o) => o.perpendicular_witness)
          .find((w) => w && w.on === basePoly.id && w.foot_id && vertSet.has(w.foot_id))?.foot_id ?? null;

      const pinned = new Set<string>();
      const edgesList = [...givenBaseEdges.values()];
      if (edgesList.length > 0) {
        const anchorEdge =
          (outPerpFootId ? edgesList.find(([u, v]) => u === outPerpFootId || v === outPerpFootId) : undefined)
          ?? edgesList[0];
        if (!outPerpFootId || anchorEdge[0] === outPerpFootId || anchorEdge[1] === outPerpFootId) {
          pinned.add(anchorEdge[0]);
          pinned.add(anchorEdge[1]);
        } else {
          pinned.add(outPerpFootId);
        }
      } else {
        pinned.add(outPerpFootId ?? vertIds[0]);
      }

      for (const vid of vertIds) {
        if (!pinned.has(vid) || hasNonRigidMetricSource(byId.get(vid))) {
          unpinnedPointIds.add(vid);
        }
      }

      for (const topPoly of siblingTopPolys) {
        const topVerts = [...new Set([...(topPoly.vertex_ids ?? []), ...(topPoly.depends ?? [])])].filter(
          (id) => byId.get(id)?.type === "point3",
        );
        if (topVerts.length === vertIds.length) {
          illustrativePolyIds.add(topPoly.id);
          topVerts.forEach((tv, idx) => {
            if (unpinnedPointIds.has(vertIds[idx])) {
              unpinnedPointIds.add(tv);
            }
          });
        }
      }
    }

    // Kiểm tra bậc tự do chiều cao / cạnh bên ngoài mặt phẳng đáy cho khối chóp và khối lăng trụ
    if (hostSolid) {
      const solidVerts = [...new Set([...(hostSolid.vertex_ids ?? []), ...(hostSolid.depends ?? [])])].filter(
        (id) => byId.get(id)?.type === "point3",
      );
      const outOfPlaneVerts = solidVerts.filter((id) => !vertSet.has(id));
      if (outOfPlaneVerts.length > 0) {
        const outVertSet = new Set(outOfPlaneVerts);
        const isRegularAllEqualSolid =
          !illustrativePolyIds.has(basePoly.id)
          && !hasNonRigidMetricSource(hostSolid)
          && /hình\s+lập\s+phương|tứ\s+diện\s+đều|bát\s+diện\s+đều|khối\s+đa\s+diện\s+đều/iu.test(textDecl);

        const hasExplicitOutGiven =
          givenQuantities.some((q) => {
            const rSubs = rawSubjectIdsOfGiven(q);
            if (rSubs.length === 0) return false;
            return rSubs.some((sid) => {
              if (sid === hostSolid.id || outVertSet.has(sid)) return true;
              const pts = entityTransitivePoints(sid);
              return [...pts].some((pid) => outVertSet.has(pid));
            });
          })
          || hybridGivenDims.some((hd) => outVertSet.has(hd.subjectIds[0]) || outVertSet.has(hd.subjectIds[1]))
          || detachedGivenScalarIds.length >= 2
          || exact.objects.some((qo) => {
            if (
              qo.type !== "quantity"
              || qo.origin !== "derived"
              || qo.annotation?.kind !== "volume"
              || qo.exact == null
              || hasNonRigidMetricSource(qo)
            ) {
              return false;
            }
            const hitsSolid = (qo.depends ?? []).includes(hostSolid.id) || (qo.annotation?.subject_ids ?? []).includes(hostSolid.id);
            if (!hitsSolid) return false;
            return (qo.dependency_edges ?? []).some((e) => {
              if (e.relation !== "numerical") return false;
              const sq = byId.get(e.source_id);
              if (!sq || sq.type !== "quantity" || classifyQuantityProvenance(sq, exact) !== "GIVEN") return false;
              const rSubs = rawSubjectIdsOfGiven(sq);
              return rSubs.length === 0 || rSubs.some((sid) => entityPointsIfContainedInBase(sid, basePoly.id, vertSet) === null);
            });
          });

        if (!isRegularAllEqualSolid && !hasExplicitOutGiven) {
          for (const ov of outOfPlaneVerts) {
            unpinnedPointIds.add(ov);
          }
          for (const tp of siblingTopPolys) {
            illustrativePolyIds.add(tp.id);
          }
        }
      }
    }
  }

  // Kiểm tra bậc tự do bán kính & chiều cao trục cho khối tròn xoay (cylinder / cone)
  for (const cs of exact.objects) {
    if (cs.type !== "curved_solid" || (cs.curved_kind !== "cylinder" && cs.curved_kind !== "cone")) continue;
    const csPts = (cs.depends ?? []).filter((id) => byId.get(id)?.type === "point3");
    if (csPts.length < 2) continue;
    const baseCenterId =
      csPts.find((pid) => {
        const pt = byId.get(pid);
        const ref = cs.anchor ?? cs.center;
        return Boolean(pt?.xyz && ref && pt.xyz.every((c, idx) => String(c) === String(ref[idx])));
      }) ?? csPts[0]!;
    const rimOrOtherIds = csPts.filter((pid) => pid !== baseCenterId);
    const axisEndId =
      rimOrOtherIds.find((pid) => {
        const pt = byId.get(pid);
        return Boolean(pt?.xyz && cs.apex_or_top && pt.xyz.every((c, idx) => String(c) === String(cs.apex_or_top![idx])));
      }) ?? rimOrOtherIds[0]!;
    const rimIds = csPts.filter((pid) => pid !== baseCenterId && pid !== axisEndId);

    const directScalarGivensOnCs = new Set<string>(
      [
        ...(cs.depends ?? []),
        ...(cs.dependency_edges ?? []).filter((e) => e.relation === "numerical").map((e) => e.source_id),
      ].filter((id) => {
        const q = byId.get(id);
        return Boolean(q && q.type === "quantity" && classifyQuantityProvenance(q, exact) === "GIVEN");
      }),
    );

    const hasExplicitRimGeomGiven =
      givenQuantities.some((q) => {
        const rSubs = rawSubjectIdsOfGiven(q);
        return rimIds.some((rid) => rSubs.includes(rid) || rSubs.some((sid) => entityTransitivePoints(sid).has(rid)));
      })
      || hybridGivenDims.some((hd) => rimIds.includes(hd.subjectIds[0]) || rimIds.includes(hd.subjectIds[1]));

    const hasExplicitAxisGeomGiven =
      givenQuantities.some((q) => {
        if (directScalarGivensOnCs.has(q.id)) return false;
        const rSubs = rawSubjectIdsOfGiven(q);
        return rSubs.some((sid) => sid === axisEndId || entityTransitivePoints(sid).has(axisEndId));
      })
      || hybridGivenDims.some((hd) => hd.subjectIds[0] === axisEndId || hd.subjectIds[1] === axisEndId);

    const scalarPool = new Set<string>([...directScalarGivensOnCs, ...detachedGivenScalarIds]);
    const rimScalarConsumed = hasExplicitRimGeomGiven ? 0 : 1;
    const hasRimGiven = hasExplicitRimGeomGiven || scalarPool.size >= 1;
    const hasAxisGiven = hasExplicitAxisGeomGiven || scalarPool.size >= rimScalarConsumed + 1;

    if (!hasRimGiven) {
      for (const rid of rimIds) unpinnedPointIds.add(rid);
      if (rimIds.length === 0) unpinnedPointIds.add(baseCenterId);
    }
    if (!hasAxisGiven) {
      unpinnedPointIds.add(axisEndId);
    }
  }

  const res: SceneMetricRigidityAnalysis = { illustrativePolyIds, unpinnedPointIds };
  _rigidityCache.set(exact as object, res);
  return res;
}

/**
 * Kiểm tra xem một đại lượng suy dẫn `q` có bị thiếu bậc tự do xác định duy nhất (`UNDERDETERMINED`) hay không:
 * - Chặn đại lượng phụ thuộc nguồn `ILLUSTRATIVE_CHOICE` / `LAYOUT_DERIVED` / `is_given === false` / `UNVERIFIED`.
 * - Chặn diện tích/thể tích/độ dài phụ thuộc đỉnh đáy chưa ghim cứng khi đa giác đáy thiếu ràng buộc Euclid,
 *   nhưng giữ nguyên `DERIVED_VERIFIED` cho các bất biến thực sự đã ghim (như `SB = 2a√5`, `d(S, (ABC)) = 4a`).
 */
export function isDerivedQuantityMetricallyUnderdetermined(
  scene: Pick<Scene3D, "objects" | "free_objects" | "chart_metric">,
  q: SceneObject,
): boolean {
  if (q.type !== "quantity") return false;
  if (!hienBieuThucDaiLuong(q)) return true;

  const exact = exactSceneOriginOf(scene);
  const byId = new Map(exact.objects.map((o) => [o.id, o]));
  const exactQ = byId.get(q.id) ?? q;
  if (hasNonRigidMetricSource(exactQ)) return true;

  const { illustrativePolyIds, unpinnedPointIds } = analyzeSceneMetricRigidity(scene);

  // Bất biến khoảng cách từ đỉnh tới mặt phẳng đáy dọc theo đường cao đã chứng nhận (vd d(S, (ABC)) = SA = 4a)
  // độc lập với vị trí minh họa của đỉnh đáy thứ ba trong mặt phẳng đáy khi SA ⊥ (ABC) đã được chứng nhận.
  const ann = exactQ.annotation;
  const prod = exactQ.producer ?? (exactQ.source as Record<string, unknown> | undefined)?.instruction ?? "";
  const isDistanceMeasure = ann?.kind === "distance" || String(prod).includes("distance");
  if (isDistanceMeasure) {
    const depObjs = [...new Set([...(exactQ.depends ?? []), ...(ann?.subject_ids ?? [])])]
      .map((id) => byId.get(id))
      .filter((o): o is SceneObject => Boolean(o));
    const fromPt = depObjs.find((o) => o.type === "point3");
    const planeOrPoly = depObjs.find((o) => o.type === "polygon3" || o.type === "plane3");
    if (
      fromPt
      && planeOrPoly
      && !hasNonRigidMetricSource(fromPt)
      && !hasNonRigidMetricSource(planeOrPoly)
      && !unpinnedPointIds.has(fromPt.id)
    ) {
      const hasCertifiedPerpHeight = exact.objects.some((o) => {
        if (hasNonRigidMetricSource(o)) return false;
        const pw = o.perpendicular_witness;
        if (!pw || pw.from !== fromPt.id || pw.on !== planeOrPoly.id) return false;
        const footId = pw.foot_id ?? exact.objects.find(
          (p) => p.type === "point3" && p.xyz && pw.foot && p.xyz.every((c, idx) => String(c) === String(pw.foot![idx])),
        )?.id;
        const footPt = footId ? byId.get(footId) : undefined;
        if (!footId || !footPt || hasNonRigidMetricSource(footPt) || unpinnedPointIds.has(footId)) return false;
        return exact.objects.some((gq) => {
          if (gq.type !== "quantity" || hasNonRigidMetricSource(gq) || classifyQuantityProvenance(gq, exact) !== "GIVEN") {
            return false;
          }
          const gqSubs = [...(gq.depends ?? []), ...(gq.annotation?.subject_ids ?? [])];
          return gqSubs.includes(fromPt.id) && gqSubs.includes(footId);
        });
      });
      if (hasCertifiedPerpHeight) {
        return false;
      }
    }
  }

  // Bất biến thiết diện tròn vuông góc trục hình trụ: r = R và S = πR² độc lập với chiều cao OO′ khi bán kính R đã cho
  const isRadOrArea =
    ann?.kind === "length"
    || ann?.kind === "area"
    || String(prod).includes("radius")
    || String(prod).includes("area");
  if (isRadOrArea && (exactQ.depends ?? []).length === 1) {
    const secCirc = byId.get(exactQ.depends![0]!);
    if (secCirc?.type === "circle3" && !hasNonRigidMetricSource(secCirc)) {
      const cDeps = (secCirc.depends ?? []).map((id) => byId.get(id)).filter((o): o is SceneObject => Boolean(o));
      const cyl = cDeps.find((o) => o.type === "curved_solid" && o.curved_kind === "cylinder");
      const cutPlane = cDeps.find((o) => o.type === "plane3");
      if (cyl && cutPlane && !hasNonRigidMetricSource(cyl) && !hasNonRigidMetricSource(cutPlane)) {
        const cylHasGivenRad = [
          ...(cyl.depends ?? []),
          ...(cyl.dependency_edges ?? []).filter((e) => e.relation === "numerical").map((e) => e.source_id),
        ].some((id) => {
          const sq = byId.get(id);
          return Boolean(sq && sq.type === "quantity" && classifyQuantityProvenance(sq, exact) === "GIVEN");
        });
        const cylBase = cyl.anchor ?? cyl.center;
        const cylTop = cyl.apex_or_top;
        const planePerpAxis = Boolean(
          cutPlane.normal
            && cylBase
            && cylTop
            && (() => {
              const nx = parseExactBigFrac(cutPlane.normal[0]);
              const ny = parseExactBigFrac(cutPlane.normal[1]);
              const nz = parseExactBigFrac(cutPlane.normal[2]);
              const bx = parseExactBigFrac(cylBase[0]);
              const by = parseExactBigFrac(cylBase[1]);
              const bz = parseExactBigFrac(cylBase[2]);
              const tx = parseExactBigFrac(cylTop[0]);
              const ty = parseExactBigFrac(cylTop[1]);
              const tz = parseExactBigFrac(cylTop[2]);
              if (!nx || !ny || !nz || !bx || !by || !bz || !tx || !ty || !tz) return false;
              const ax = subBigFrac(tx, bx);
              const ay = subBigFrac(ty, by);
              const az = subBigFrac(tz, bz);
              const cx = subBigFrac(mulBigFrac(ny, az), mulBigFrac(nz, ay));
              const cy = subBigFrac(mulBigFrac(nz, ax), mulBigFrac(nx, az));
              const cz = subBigFrac(mulBigFrac(nx, ay), mulBigFrac(ny, ax));
              return cx.num === 0n && cy.num === 0n && cz.num === 0n && (ax.num !== 0n || ay.num !== 0n || az.num !== 0n);
            })(),
        );
        if (cylHasGivenRad && planePerpAxis) {
          return false;
        }
      }
    }
  }

  // 1. Kiểm tra lan truyền nguồn phi-bất-biến (minh họa / bố cục / chưa xác thực)
  const visitedSrc = new Set<string>();
  const srcQueue: SceneObject[] = [exactQ];
  while (srcQueue.length > 0) {
    const cur = srcQueue.shift()!;
    if (visitedSrc.has(cur.id)) continue;
    visitedSrc.add(cur.id);
    if (hasNonRigidMetricSource(cur)) return true;
    if (cur.id !== exactQ.id && cur.type === "quantity" && cur.origin === "free" && classifyQuantityProvenance(cur, exact) !== "GIVEN") {
      return true;
    }
    const nextIds = [
      ...(cur.depends ?? []),
      ...(cur.dependency_edges ?? []).map((e) => e.source_id),
      ...(cur.annotation?.subject_ids ?? []),
    ];
    for (const nid of nextIds) {
      const nextObj = byId.get(nid);
      if (nextObj && !visitedSrc.has(nextObj.id)) srcQueue.push(nextObj);
    }
  }

  // 2. Kiểm tra độ cứng Euclid trên mặt đáy đa giác (nếu cảnh có khai báo dữ kiện metric tường minh)
  if (illustrativePolyIds.size === 0 && unpinnedPointIds.size === 0) {
    return false;
  }

  const visitedGeo = new Set<string>();
  const geoQueue: SceneObject[] = [exactQ];
  while (geoQueue.length > 0) {
    const cur = geoQueue.shift()!;
    if (visitedGeo.has(cur.id)) continue;
    visitedGeo.add(cur.id);
    if (cur.id !== exactQ.id) {
      if (illustrativePolyIds.has(cur.id) || unpinnedPointIds.has(cur.id)) {
        return true;
      }
      if ((cur.vertex_ids ?? []).some((vid) => unpinnedPointIds.has(vid))) {
        return true;
      }
    }
    const nextIds = [
      ...(cur.depends ?? []),
      ...(cur.annotation?.subject_ids ?? []),
      ...(cur.dependency_edges ?? []).map((e) => e.source_id),
    ];
    for (const nid of nextIds) {
      const nextObj = byId.get(nid);
      if (nextObj && !visitedGeo.has(nextObj.id)) geoQueue.push(nextObj);
    }
  }

  return false;
}

/**
 * Ràng buộc đáp số Hybrid `/4` của một đại lượng: `MATCH` khi view đính kèm cảnh trỏ đáp số vào đại lượng này và hệ số
 * khớp giá trị cảnh chính xác (hệ số vắng ⇒ view đã qua `kiemHybridView` ở biên vào: giải mã, lịch sử); `MISMATCH` khi
 * hệ số lệch; `null` khi không có ràng buộc (bài mẫu, bản ghi cũ) — khi đó heuristic hình học vẫn áp dụng.
 */
function hybridAnswerBinding(
  scene: Pick<Scene3D, "objects">,
  q: SceneObject,
): "MATCH" | "MISMATCH" | null {
  const exact = exactSceneOriginOf(scene);
  const answer = (hybridViewOfScene(scene) ?? hybridViewOfScene(exact))?.answers?.find((a) => a.quantity_id === q.id);
  if (!answer) return null;
  if (answer.coefficient === undefined) return "MATCH";
  const value = (exact.objects.find((o) => o.id === q.id) ?? q).value;
  const gon = (s: unknown) => String(s ?? "").replace(/\s+/g, "");
  return value != null && gon(answer.coefficient) === gon(value) ? "MATCH" : "MISMATCH";
}

/**
 * Phân loại provenance chuẩn hóa xuyên suốt (`GIVEN`, `DERIVED_VERIFIED`, `ILLUSTRATIVE`, `UNDERDETERMINED`, `INVALID`)
 * cho mọi thực thể trong `Scene3D`.
 */
export function classifySceneEntityProvenance(
  scene: Pick<Scene3D, "objects" | "free_objects" | "chart_metric">,
  o: SceneObject,
): CanonicalMathProvenance {
  const src = o.source as Record<string, unknown> | undefined;
  const claimsGiven = src?.provenance === "GIVEN" || src?.is_given === true || Boolean(src?.fact_id);
  if ((o.origin === "derived" || o.producer != null) && claimsGiven) {
    return "INVALID";
  }
  if (claimsGiven && hasNonRigidMetricSource(o)) {
    return "INVALID";
  }

  if (o.type === "quantity") {
    const qp = classifyQuantityProvenance(o, scene);
    if (qp === "GIVEN") return "GIVEN";
    // A source-bound Hybrid /4 answer is certified by the backend (exact kernel + `certify_answer`); the display layer
    // never re-decides it. A binding that disagrees with the scene is inconsistent, not "insufficient data".
    const binding = qp === "CERTIFIED_DERIVED" ? hybridAnswerBinding(scene, o) : null;
    if (binding === "MATCH") return "DERIVED_VERIFIED";
    if (binding === "MISMATCH") return "INVALID";
    if (qp === "CERTIFIED_DERIVED") {
      return isDerivedQuantityMetricallyUnderdetermined(scene, o) ? "UNDERDETERMINED" : "DERIVED_VERIFIED";
    }
    if (qp === "DISPLAY_ONLY" || hasNonRigidMetricSource(o)) return "ILLUSTRATIVE";
    if (o.origin === "derived") return "INVALID";
    return "UNDERDETERMINED";
  }

  if (o.semantic_role === "AUXILIARY_CONSTRUCTION") {
    return "DERIVED_VERIFIED";
  }
  if (o.authoritative === false) {
    return o.perpendicular_witness?.status === "GIVEN" ? "GIVEN" : "ILLUSTRATIVE";
  }
  if (hasNonRigidMetricSource(o)) {
    return "ILLUSTRATIVE";
  }

  const { illustrativePolyIds, unpinnedPointIds } = analyzeSceneMetricRigidity(scene);
  if (illustrativePolyIds.has(o.id) || unpinnedPointIds.has(o.id)) {
    return "ILLUSTRATIVE";
  }
  if (o.type === "point3" && typeof src?.assumption === "string" && src.assumption.trim().length > 0) {
    return "ILLUSTRATIVE";
  }
  if (o.perpendicular_witness?.status === "GIVEN" || claimsGiven) {
    return "GIVEN";
  }
  if (o.origin === "free") {
    return (scene.free_objects ?? []).includes(o.id) ? "GIVEN" : "UNDERDETERMINED";
  }
  if (o.origin === "derived") {
    if (
      o.type === "solid"
      && [...(o.depends ?? []), ...(o.vertex_ids ?? [])].some(
        (id) => illustrativePolyIds.has(id) || unpinnedPointIds.has(id),
      )
    ) {
      return "ILLUSTRATIVE";
    }
    return "DERIVED_VERIFIED";
  }
  return "UNDERDETERMINED";
}
