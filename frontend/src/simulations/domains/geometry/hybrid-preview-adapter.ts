/**
 * Biên vận chuyển DUY NHẤT của phản hồi Hybrid Route D Preview → envelope Scene3D
 * (HYBRID_PREVIEW_FRONTEND_CONTRACT §2–§4; ISSUE-ARCH-HYBRID-FRONTEND-OFFLINE-INTEGRATION F3/F4).
 *
 * Phản hồi preview là `{schema_version, envelope, route_d}` — `route_d` cố ý nằm NGOÀI envelope. Trước biên này
 * `SimulationWorkspace` đọc `envelope.route_d` (không bao giờ có), nên trên đường sản phẩm không quan sát/đáp số ký hiệu
 * nào tới được cảnh. Ở đây KHÔNG chép mù `route_d` vào envelope: chỉ những gì kiểm được với chính cảnh mới thành một
 * `HybridPreviewView` (khoá `hybrid_preview`), và module `generic.semantic_program` kiểm lại view ấy ở `validateEnvelope`
 * trước khi store nhận (store vẫn không biết miền — M2 #7). Phản hồi lệch hợp đồng ⇒ từ chối cả phản hồi.
 *
 * Không có lời gọi mạng nào ở đây: frontend KHÔNG gọi `/api/preview/hybrid` (operator-only); biên này chỉ dùng cho
 * fixture/harness offline và cho một tích hợp tương lai đã được duyệt riêng.
 */
import type { Scene3D } from "./scene3d-model";

export const HYBRID_PREVIEW_SCHEMA = "hybrid-route-d-preview/1";
export const HYBRID_PREVIEW_ADAPTER = "hybrid-preview-adapter/2";
export const HYBRID_SIMULATION_SCHEMA = "hybrid-route-d-simulation/4";
export const HYBRID_SIMULATION_ADAPTER = "hybrid-simulation-adapter/4";
/** Khoá của view đã kiểm trong envelope (do frontend tạo, không phải trường của backend). */
export const KHOA_HYBRID_VIEW = "hybrid_preview";

/** Đáp số tổng quát của một đại lượng kết quả: `answers[id]` ↔ đại lượng cảnh `kq_<id>` (engine.py `kq_{c.id}`). */
export interface HybridAnswerView {
  quantity_id: string;
  /** Đáp số dạng chữ của backend, vd `a³√3/3`. */
  symbolic: string;
  /** Bậc theo đơn vị ký hiệu (0 ⇒ không thứ nguyên / đề dùng số). */
  dim: number;
  unit: string | null;
}

export type HybridEvidenceState = "TRUE_ON_CONFIGURATION" | "FALSE_ON_CONFIGURATION" | "UNVERIFIABLE";

/** Một quan sát trên hình dựng (KHÔNG phải chứng minh): loại quan hệ + trạng thái + bước neo. */
export interface HybridObservationView {
  check_id: string;
  group: "goal" | "negated";
  /** Tên LOẠI quan hệ (tiếng Việt) từ `planner.trace[].fn`. Vật cụ thể (vd BC, (SAB)) KHÔNG có trong adapter `/2`. */
  relation: string;
  evidence_state: HybridEvidenceState;
  /** Bước timeline mà từ đó quan sát được hiện: bước cuối — mệnh đề được kiểm trên hình đã dựng XONG. */
  anchor_step: number;
}

export interface HybridPreviewView {
  adapter_version: typeof HYBRID_PREVIEW_ADAPTER | typeof HYBRID_SIMULATION_ADAPTER;
  answers: HybridAnswerView[];
  observations: HybridObservationView[];
  /** Adapter /4 certificates and provenance, never promoted to source givens. */
  sections?: HybridSectionView[];
}

export interface HybridSectionView {
  section_id: string;
  boundary: string[] | null;
  vertices: { label: string; edge: string[]; provenance: string; stated: boolean }[];
  closure_certificate: { boundary: string[]; verified: boolean; rule: string } | null;
}

/** Hàm loại `fact` của Registry (`geometry_functions/registry.py` — mệnh đề kiểm được trên hình) → tên cho học sinh.
 *  Ngoài bảng ⇒ tên chung (an toàn: không bịa quan hệ). */
const TEN_QUAN_HE: Record<string, string> = {
  perpendicular_line_plane: "quan hệ vuông góc giữa đường thẳng và mặt phẳng",
  perpendicular_lines: "quan hệ vuông góc giữa hai đường thẳng",
  face_perpendicular_base: "quan hệ vuông góc giữa mặt bên và mặt đáy",
  right_angle: "góc vuông",
  equal_length: "hai đoạn bằng nhau",
  segment_length: "độ dài đoạn thẳng",
  altitude: "đường cao",
  height: "chiều cao",
  orthogonal_projection: "hình chiếu vuông góc",
  rectangle: "hình chữ nhật",
  regular_polygon: "đa giác đều",
};
const TEN_QUAN_HE_CHUNG = "mệnh đề của đề";
const TEN_HOP_LE = new Set<string>([...Object.values(TEN_QUAN_HE), TEN_QUAN_HE_CHUNG]);

const TRANG_THAI = new Set<string>(["TRUE_ON_CONFIGURATION", "FALSE_ON_CONFIGURATION", "UNVERIFIABLE"]);

export type KetQuaPhanHoiHybrid =
  | { ok: true; envelope: Record<string, unknown> }
  | { ok: false; reason: string };

const laDoiTuong = (x: unknown): x is Record<string, unknown> => !!x && typeof x === "object" && !Array.isArray(x);
const gon = (s: unknown) => String(s ?? "").replace(/\s+/g, "");

/** Compare backend identities/coordinates only; no intersection, area or volume calculation in the consumer. */
function cungChuTrinh(a: unknown[], b: unknown[]): boolean {
  return a.length === b.length && [b, [...b].reverse()].some((cycle) =>
    cycle.some((_, offset) => a.every((x, i) => JSON.stringify(x) === JSON.stringify(cycle[(i + offset) % cycle.length]))));
}

function kiemSections(sections: unknown, scene: Scene3D): string | null {
  if (!Array.isArray(sections)) return "thiếu provenance thiết diện";
  const ids = new Set<string>();
  const diem = (name: string) => scene.objects.filter((o) => o.type === "point3"
    && (o.id === name || o.notation?.replace(/[′’]/g, "'") === name.replace(/[′’]/g, "'")));
  const nguon = new Set(["THROUGH_POINT_REUSE", "SOURCE_NAMED", "STATED_UNNAMED", "REUSED_INTERSECTION", "DERIVED_FRESH"]);
  for (const s of sections) {
    if (!laDoiTuong(s) || typeof s.section_id !== "string" || ids.has(s.section_id) || !Array.isArray(s.vertices)) return "thiết diện sai dạng";
    ids.add(s.section_id);
    const obj = scene.objects.find((o) => o.id === `td_${s.section_id}` && o.type === "section");
    if (!obj || !obj.polygon) return "thiết diện không thuộc cảnh";
    const polygon = obj.polygon;
    const solid = scene.objects.find((o) => obj.depends.includes(o.id) && o.type === "solid");
    if (!solid?.vertex_ids || s.vertices.length !== polygon.length) return "đỉnh thiết diện lệch cảnh";
    const labels = new Set<string>();
    for (const v of s.vertices) {
      if (!laDoiTuong(v) || typeof v.label !== "string" || labels.has(v.label) || !nguon.has(String(v.provenance))
        || typeof v.stated !== "boolean" || (v.provenance === "DERIVED_FRESH" && v.stated)
        || !Array.isArray(v.edge) || v.edge.length !== 2 || !v.edge.every((id) => typeof id === "string" && diem(id).length === 1)
        || !scene.objects.some((o) => o.id === v.label && o.type === "point3" && (v.provenance !== "DERIVED_FRESH" || o.origin === "derived"))) return "provenance đỉnh thiết diện sai";
      labels.add(v.label);
      const point = scene.objects.find((o) => o.id === v.label && o.type === "point3");
      if (!point) return "thiếu điểm thiết diện";
      if (v.provenance === "DERIVED_FRESH" && (point.notation != null || point.role !== "Điểm dựng phụ"
        || point.display_group?.includes("given"))) return "điểm suy diễn không được giả làm dữ kiện";
      const ordinal = polygon.findIndex((p) => JSON.stringify(p) === JSON.stringify(point?.xyz));
      const source = obj.vertex_sources?.[ordinal];
      const edge = v.edge.map((name: string) => diem(name)[0].id);
      const indices = source?.solid_edge_vertex_indices;
      if (ordinal < 0 || !source || (indices
        ? !cungChuTrinh(edge, indices.map((i) => solid.vertex_ids![i]))
        : source.solid_vertex_index == null || !edge.includes(solid.vertex_ids[source.solid_vertex_index]))) return "cạnh nguồn thiết diện lệch cảnh";
    }
    // Plane-only sections have no derived-solid closure certificate in /4; preserve this absence honestly.
    if (s.boundary === null && s.closure_certificate === null) {
      if (scene.objects.some((o) => o.type === "solid" && o.id !== solid.id
        && [...labels].every((id) => o.vertex_ids?.includes(id)))) return "khối dẫn xuất thiếu chứng chỉ khép kín";
      continue;
    }
    if (!Array.isArray(s.boundary) || s.boundary.length < 3 || new Set(s.boundary).size !== s.boundary.length
      || s.boundary.length !== labels.size || !s.boundary.every((id) => labels.has(id))
      || !laDoiTuong(s.closure_certificate) || s.closure_certificate.verified !== true
      || typeof s.closure_certificate.rule !== "string" || !Array.isArray(s.closure_certificate.boundary)
      || !cungChuTrinh(s.boundary, s.closure_certificate.boundary)) return "chứng chỉ chu trình thiết diện lệch";
    const points = s.boundary.map((id) => scene.objects.find((o) => o.id === id)?.xyz);
    if (points.some((p) => !p) || !cungChuTrinh(points, obj.polygon)) return "chu trình thiết diện lệch cảnh";
  }
  if (scene.objects.filter((o) => o.type === "section").length !== ids.size) return "thiếu thiết diện";
  return null;
}

function nhomKiem(group: unknown): [string, Record<string, unknown>][] | null {
  if (group == null) return [];
  if (!laDoiTuong(group)) return null;
  const ra: [string, Record<string, unknown>][] = [];
  for (const [id, v] of Object.entries(group)) {
    if (!laDoiTuong(v)) return null;
    ra.push([id, v]);
  }
  return ra;
}

/** Giá trị số của đại lượng cảnh, dạng chữ backend phát (`value`) — để đối chiếu với hệ số `answer_exact.coef`. */
function giaTriCanh(scene: Scene3D, id: string): string | null {
  const o = scene.objects.find((x) => x.id === id);
  return o && o.type === "quantity" && o.value != null ? gon(o.value) : null;
}

/**
 * Dựng view từ `route_d` của một envelope PHỤC VỤ; `null` + lý do khi lệch hợp đồng. Mọi đáp số phải nối được với đúng
 * một đại lượng cảnh và khớp giá trị dựng (hệ số tại a = 1); mọi quan sát phải là quan sát (không chứng minh).
 */
export function dungHybridView(routeD: unknown, scene: Scene3D): { view: HybridPreviewView } | { reason: string } {
  if (!laDoiTuong(routeD)) return { reason: "route_d không phải đối tượng" };
  const v4 = routeD.schema_version === HYBRID_SIMULATION_SCHEMA;
  const id = routeD.runtime_identity;
  if (v4) {
    if (routeD.adapter_version !== HYBRID_SIMULATION_ADAPTER || routeD.contract_version !== "typed-fact-next/2"
      || routeD.status !== "SERVED" || routeD.refusal !== null || !laDoiTuong(routeD.source_verification)
      || routeD.source_verification.authority !== "registry.kiem_nguon") return { reason: "authority Adapter /4 không hợp lệ" };
    const error = kiemSections(routeD.sections, scene);
    if (error) return { reason: error };
  } else if (!laDoiTuong(id) || id.adapter_version !== HYBRID_PREVIEW_ADAPTER) return { reason: "adapter_version không được hỗ trợ" };

  // §4 — length_unit của route_d phải đúng là length_unit của cảnh (một nguồn).
  if (JSON.stringify(routeD.length_unit ?? null) !== JSON.stringify((v4 ? scene.length_unit?.symbol : scene.length_unit) ?? null)) {
    return { reason: "length_unit của route_d lệch cảnh" };
  }
  const donVi = scene.length_unit?.symbol ?? null;

  const answers: HybridAnswerView[] = [];
  const ans = routeD.answers ?? {};
  const exact = routeD.answer_exact ?? {};
  if (!laDoiTuong(ans) || !laDoiTuong(exact)) return { reason: "answers/answer_exact sai dạng" };
  if (v4 && JSON.stringify(Object.keys(ans).sort()) !== JSON.stringify(Object.keys(exact).sort())) return { reason: "answers/answer_exact lệch" };
  for (const [k, sym] of Object.entries(ans)) {
    const ex = exact[k];
    if (typeof sym !== "string" || !sym.trim() || !laDoiTuong(ex)) return { reason: `đáp số ${k} thiếu dạng chính xác` };
    const dim = ex.dim;
    if (ex.unit != null && typeof ex.unit !== "string") return { reason: `đáp số ${k}: đơn vị sai dạng` };
    const unit: string | null = ex.unit ?? null;
    if (typeof dim !== "number" || !Number.isInteger(dim) || dim < 0) return { reason: `đáp số ${k}: bậc không hợp lệ` };
    if (dim > 0 ? unit !== donVi || donVi == null : unit !== null && unit !== donVi) {
      return { reason: `đáp số ${k}: đơn vị lệch length_unit` };
    }
    const qid = `kq_${k}`;
    const giaTri = giaTriCanh(scene, qid);
    // Hình dựng ở a = 1 ⇒ giá trị trên cảnh = hệ số. Lệch ⇒ đáp số không thuộc cảnh này.
    if (giaTri == null || giaTri !== gon(ex.coef)) return { reason: `đáp số ${k} không khớp đại lượng ${qid} của cảnh` };
    answers.push({ quantity_id: qid, symbolic: sym, dim, unit });
  }

  const planner = routeD.planner;
  if (!laDoiTuong(planner)) return { reason: "planner thiếu" };
  const trace = Array.isArray(planner.trace) ? planner.trace : [];
  const fnCua = (k: string): string | null => {
    const t = trace.find((x) => laDoiTuong(x) && x.call === k);
    return t && laDoiTuong(t) && typeof t.fn === "string" ? t.fn : null;
  };
  const buocCuoi = Math.max(0, ...scene.events.map((e) => e.step_index));
  const observations: HybridObservationView[] = [];
  for (const [group, khoa] of [["goal", "goal_checks"], ["negated", "negated_checks"]] as const) {
    const nhom = nhomKiem(planner[khoa]);
    if (nhom == null) return { reason: `${khoa} sai dạng` };
    for (const [k, c] of nhom) {
      // §3: phiên bản này không có chứng minh — mọi giá trị khác là lệch hợp đồng, không phải "đã chứng minh".
      if (c.can_present_as_proven !== false || c.proof_status !== "UNVERIFIABLE") {
        return { reason: `quan sát ${k} tự xưng chứng minh` };
      }
      if (typeof c.evidence_state !== "string" || !TRANG_THAI.has(c.evidence_state)) {
        return { reason: `quan sát ${k}: evidence_state lạ` };
      }
      const fn = fnCua(k);
      observations.push({
        check_id: k, group,
        relation: (fn && TEN_QUAN_HE[fn]) ?? TEN_QUAN_HE_CHUNG,
        evidence_state: c.evidence_state as HybridEvidenceState,
        anchor_step: buocCuoi,
      });
    }
  }
  return { view: { adapter_version: v4 ? HYBRID_SIMULATION_ADAPTER : HYBRID_PREVIEW_ADAPTER, answers, observations,
    ...(v4 ? { sections: structuredClone(routeD.sections) as HybridSectionView[] } : {}) } };
}

/**
 * Phản hồi preview → envelope cho `store.loadEnvelope`. Envelope phục vụ mang thêm `hybrid_preview` (view đã kiểm);
 * envelope từ chối giữ nguyên (lời từ chối không mang quan sát — §5). Phản hồi cổng HTTP (không envelope) ⇒ lỗi.
 */
export function docPhanHoiHybrid(raw: unknown): KetQuaPhanHoiHybrid {
  if (!laDoiTuong(raw) || (raw.schema_version !== HYBRID_PREVIEW_SCHEMA && raw.schema_version !== HYBRID_SIMULATION_SCHEMA)) return { ok: false, reason: "schema_version lạ" };
  const v4 = raw.schema_version === HYBRID_SIMULATION_SCHEMA;
  if (!v4 && laDoiTuong(raw.route_d) && raw.route_d.schema_version === HYBRID_SIMULATION_SCHEMA) return { ok: false, reason: "wrapper/route_d khác phiên bản" };
  if (v4 && (!laDoiTuong(raw.route_d) || raw.route_d.schema_version !== HYBRID_SIMULATION_SCHEMA
    || raw.route_d.adapter_version !== HYBRID_SIMULATION_ADAPTER || raw.route_d.contract_version !== "typed-fact-next/2")) return { ok: false, reason: "identity Adapter /4 lệch" };
  const envelope = raw.envelope;
  if (!laDoiTuong(envelope)) return { ok: false, reason: "phản hồi không có envelope (phản hồi cổng operator)" };
  if (KHOA_HYBRID_VIEW in envelope) return { ok: false, reason: "envelope backend không được tự mang hybrid_preview" };
  if (envelope.status !== "ok") {
    if (v4 && (!laDoiTuong(raw.route_d) || raw.route_d.status !== "REFUSED" || !laDoiTuong(raw.route_d.refusal)
      || typeof raw.route_d.refusal.code !== "string" || raw.route_d.refusal.code !== envelope.reason_code
      || envelope.scene3d != null || envelope.simulation_id != null)) return { ok: false, reason: "từ chối Adapter /4 lệch" };
    return { ok: true, envelope: { ...envelope } };
  }
  const scene = envelope.scene3d as Scene3D | undefined;
  if (!laDoiTuong(scene) || !Array.isArray(scene.objects) || !Array.isArray(scene.events)) {
    return { ok: false, reason: "envelope phục vụ thiếu scene3d" };
  }
  if (scene.objects.some((o) => !laDoiTuong(o)) || scene.events.some((e) => !laDoiTuong(e))) {
    return { ok: false, reason: "scene3d có đối tượng hoặc sự kiện sai dạng" };
  }
  const r = dungHybridView(raw.route_d, scene);
  if ("reason" in r) return { ok: false, reason: r.reason };
  return { ok: true, envelope: { ...envelope, [KHOA_HYBRID_VIEW]: r.view } };
}

/**
 * Kiểm lại view ở biên module (`validateEnvelope`): view chỉ được trỏ vào vật/bước CÓ trong chính cảnh. `null` = hợp lệ.
 * Không dựng lại từ `route_d` (đã bỏ ở biên vận chuyển) — chỉ kiểm tính nhất quán với cảnh.
 */
export function kiemHybridView(view: unknown, scene: Scene3D | undefined): string | null {
  if (!laDoiTuong(view) || (view.adapter_version !== HYBRID_PREVIEW_ADAPTER && view.adapter_version !== HYBRID_SIMULATION_ADAPTER)) return "hybrid_preview lạ";
  if (!scene) return "hybrid_preview cần scene3d";
  if (view.adapter_version === HYBRID_SIMULATION_ADAPTER) {
    const error = kiemSections(view.sections, scene);
    if (error) return error;
  }
  if (!Array.isArray(view.answers) || !Array.isArray(view.observations)) return "hybrid_preview sai dạng";
  const daCo = new Set<string>();
  for (const a of view.answers) {
    // Cùng ràng buộc như lúc dựng (`dungHybridView`): không tin một view tự đến (review của run, M3).
    if (!laDoiTuong(a) || typeof a.symbolic !== "string" || !a.symbolic.trim()
      || typeof a.dim !== "number" || !Number.isInteger(a.dim) || a.dim < 0
      || (a.dim > 0 ? a.unit !== (scene.length_unit?.symbol ?? null) || a.unit == null : a.unit !== null && a.unit !== scene.length_unit?.symbol)
      || daCo.has(String(a.quantity_id)) || giaTriCanh(scene, String(a.quantity_id)) == null) {
      return "đáp số trỏ vào đại lượng không có trong cảnh hoặc sai dạng";
    }
    daCo.add(String(a.quantity_id));
  }
  const buocCuoi = Math.max(0, ...scene.events.map((e) => e.step_index));
  for (const o of view.observations) {
    if (!laDoiTuong(o) || !TRANG_THAI.has(String(o.evidence_state)) || o.anchor_step !== buocCuoi
      || (o.group !== "goal" && o.group !== "negated") || !TEN_HOP_LE.has(String(o.relation))) {
      return "quan sát neo vào bước không có trong cảnh hoặc sai dạng";
    }
  }
  return null;
}

/** View đã kiểm của envelope đang hoạt động, hoặc `null` (envelope LLM_ONLY không bao giờ có). */
export function hybridViewCua(envelope: unknown): HybridPreviewView | null {
  const v = laDoiTuong(envelope) ? envelope[KHOA_HYBRID_VIEW] : null;
  return laDoiTuong(v) && (v.adapter_version === HYBRID_PREVIEW_ADAPTER || v.adapter_version === HYBRID_SIMULATION_ADAPTER) ? (v as unknown as HybridPreviewView) : null;
}

/**
 * Thứ được hiện ở bước `buoc` — MỘT luật cho timeline: đáp số từ bước đo đại lượng của nó, quan sát từ bước neo.
 * Không kết luận nào đứng trước bước chống đỡ nó.
 */
export function hybridTaiBuoc(
  view: HybridPreviewView | null | undefined, scene: Pick<Scene3D, "events">, buoc: number,
): { answers: HybridAnswerView[]; observations: HybridObservationView[] } {
  if (!view) return { answers: [], observations: [] };
  return {
    answers: view.answers.filter((a) => scene.events.some((e) => e.object === a.quantity_id && e.step_index <= buoc)),
    observations: view.observations.filter((o) => buoc >= o.anchor_step),
  };
}

/** Giá trị của đáp số dạng chữ — `answers` của góc đã mang ký hiệu ("cos²=1/4"): bỏ vế trái để không lặp ký hiệu
 *  của đại lượng ("cos²(SA, (ABC)) = 1/4", không phải "… = cos²=1/4"; review của run, M1). */
export function giaTriDapSo(a: HybridAnswerView): string {
  return a.symbolic.includes("=") ? a.symbolic.slice(a.symbolic.lastIndexOf("=") + 1).trim() : a.symbolic;
}

/** Câu trình bày MỘT quan sát (§3): luôn nói đây là quan sát trên một hình, không phải chứng minh tổng quát. */
export function cauQuanSat(o: HybridObservationView): string {
  const tt = o.evidence_state === "TRUE_ON_CONFIGURATION" ? "trên hình đã dựng, điều này đúng"
    : o.evidence_state === "FALSE_ON_CONFIGURATION" ? "trên hình đã dựng, điều này không đúng"
    : "chưa kiểm được trên hình đã dựng";
  const dau = o.relation.charAt(0).toUpperCase() + o.relation.slice(1);
  return `${dau} (${o.group === "goal" ? "điều đề yêu cầu" : "mệnh đề phủ định của đề"}): ${tt} — đây là quan sát trên một hình, không phải chứng minh tổng quát.`;
}
