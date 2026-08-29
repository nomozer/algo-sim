/**
 * `InteractionState` — CÁCH NHÌN, không phải toán học.
 *
 * ─── RANH GIỚI, và nó là luật chứ không phải quy ước ────────────────────
 *
 * `GeometryState` (backend, `Fraction` chính xác) là **sự thật**. `Scene3D` là
 * phép chiếu của sự thật ấy. Mọi thứ trong file này chỉ đổi *người xem đang
 * nhìn thấy gì* — chọn, ẩn, cô lập, bung, tô sáng, tua bước.
 *
 *     THAO TÁC NHÌN   → đổi `InteractionState`, KHÔNG đổi `Scene3D`
 *     THAO TÁC HÌNH   → phải đi qua kernel + mọi cổng. CHƯA có ở wave này.
 *
 * Hệ quả cụ thể, và là thứ test khoá: **bung hình không đổi một con số nào**.
 * `explode` sinh `visual_transform`, và `visual_transform` không có mặt trong
 * bất kỳ phép đo, checker hay bất biến nào. Toạ độ trong `Scene3D.objects`
 * nguyên vẹn sau khi bung — nếu không thì "mô phỏng" đã nói dối về hình.
 *
 * Mọi hàm ở đây THUẦN: cùng đầu vào cho cùng đầu ra, không đọc `window`,
 * không giữ trạng thái ẩn. Nhờ vậy một phiên tương tác **tuần tự hoá được**
 * và **phát lại được** — và cả hai đều là điều kiện để lượt đo sau đọc lại
 * được người dùng đã làm gì.
 *
 * KHÔNG có lời gọi LLM nào trong file này, và không thể có: nó không nhận
 * `fetch`, không nhận client, không import gì ngoài mô hình cảnh thuần.
 */
import {
  BIEN_DOI_DONG_NHAT,
  type Exact,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
  type VisualTransform,
  clampStep,
  toNumber,
} from "./scene3d-model";

export interface InteractionState {
  /** Vật đang chọn. `null` ⇔ không chọn gì. */
  selected_id: string | null;
  /** Ẩn TƯỜNG MINH do người dùng bấm. Khác hẳn "bị mờ vì đang cô lập". */
  hidden_ids: string[];
  /** Rỗng ⇔ không cô lập. Khác `[]` với `null` là có chủ đích: xem `isVisible`. */
  isolated_ids: string[];
  /** Nhóm đang bung, theo tên `display_group`. */
  exploded_groups: string[];
  transparent_ids: string[];
  current_step: number;
}

export const TRANG_THAI_DAU: InteractionState = {
  selected_id: null,
  hidden_ids: [],
  isolated_ids: [],
  exploded_groups: [],
  transparent_ids: [],
  current_step: 0,
};

export function taoTrangThai(): InteractionState {
  return { ...TRANG_THAI_DAU };
}

/** Về đúng trạng thái đầu. Không giữ lại một mẩu nào của phiên trước. */
export function reset(): InteractionState {
  return taoTrangThai();
}

// ── CHỌN ─────────────────────────────────────────────────────────────────
export function select(s: InteractionState, id: string | null): InteractionState {
  return { ...s, selected_id: id };
}

/** Bấm lại đúng vật đang chọn ⇒ bỏ chọn. Cách thoát mà không cần nút riêng. */
export function toggleSelect(s: InteractionState, id: string): InteractionState {
  return select(s, s.selected_id === id ? null : id);
}

// ── ẨN / HIỆN / CÔ LẬP ───────────────────────────────────────────────────
export function hide(s: InteractionState, id: string): InteractionState {
  return s.hidden_ids.includes(id)
    ? s
    : { ...s, hidden_ids: [...s.hidden_ids, id].sort() };
}

export function show(s: InteractionState, id: string): InteractionState {
  return { ...s, hidden_ids: s.hidden_ids.filter((x) => x !== id) };
}

export function showAll(s: InteractionState): InteractionState {
  return { ...s, hidden_ids: [], isolated_ids: [] };
}

/**
 * Cô lập một tập vật — mọi thứ ngoài tập ấy thôi hiển thị.
 *
 * `isolate` KHÔNG ghi vào `hidden_ids`: hai thứ khác nhau về ý định và về
 * cách thoát. Gộp chúng thì bỏ cô lập sẽ hiện lại cả những vật người dùng đã
 * chủ động ẩn trước đó — một sự "giúp đỡ" mà người dùng không yêu cầu.
 */
export function isolate(s: InteractionState, ids: string[]): InteractionState {
  return { ...s, isolated_ids: [...new Set(ids)].sort() };
}

export function clearIsolate(s: InteractionState): InteractionState {
  return { ...s, isolated_ids: [] };
}

/** Cô lập theo NHÓM hiển thị — `base`, `section`, `target`… */
export function isolateGroup(
  s: InteractionState,
  scene: Scene3D,
  group: string,
): InteractionState {
  return isolate(
    s,
    scene.objects
      .filter((o) => (o.display_group ?? []).includes(group))
      .map((o) => o.id),
  );
}

/**
 * Vật này có được vẽ ở bước hiện tại không?
 *
 * Ba điều kiện, và thứ tự không quan trọng vì cả ba đều phải đúng:
 * chưa bị ẩn tường minh · nằm trong tập cô lập (nếu đang cô lập) · đã tồn tại
 * tại bước đang xem. Điều kiện thứ ba mượn `objectsAt` chứ không tự tính lại.
 */
export function isVisible(
  s: InteractionState,
  id: string,
  daTonTai: ReadonlySet<string>,
): boolean {
  if (s.hidden_ids.includes(id)) return false;
  if (s.isolated_ids.length > 0 && !s.isolated_ids.includes(id)) return false;
  return daTonTai.has(id);
}

// ── PHỤ THUỘC ────────────────────────────────────────────────────────────
/**
 * Phụ thuộc TRỰC TIẾP — đọc `depends` do backend gửi, không dựng lại từ tên.
 *
 * `M = midpoint(A,B)` ⇒ `["A", "B"]`. Dựng lại đồ thị này ở frontend bằng
 * cách bóc chuỗi `producer` là dựng nguồn sự thật thứ hai, và nó sẽ lệch ngay
 * lần thêm primitive tiếp theo.
 */
export function directDependencies(scene: Scene3D, id: string): string[] {
  return scene.objects.find((o) => o.id === id)?.depends ?? [];
}

/**
 * Bao đóng phụ thuộc — mọi thứ vật này dựa vào, dù gián tiếp.
 *
 * Duyệt có `đã thăm`, nên **đồ thị có chu trình cũng dừng**. Chu trình không
 * nên tồn tại (chương trình dựng theo thứ tự), nhưng một vòng lặp vô hạn ở
 * tầng UI thì treo cả tab — và "không nên tồn tại" chưa bao giờ là một phép
 * bảo vệ.
 */
export function dependencyClosure(scene: Scene3D, id: string): string[] {
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const daTham = new Set<string>();
  const hangDoi = [...(theoId.get(id)?.depends ?? [])];
  while (hangDoi.length > 0) {
    const x = hangDoi.shift()!;
    if (daTham.has(x) || x === id) continue;
    daTham.add(x);
    hangDoi.push(...(theoId.get(x)?.depends ?? []));
  }
  return [...daTham].sort();
}

/** Tập cần tô sáng khi chọn `id`: chính nó + phụ thuộc trực tiếp. */
export function highlightSet(scene: Scene3D, id: string, sau = false): string[] {
  const d = sau ? dependencyClosure(scene, id) : directDependencies(scene, id);
  return [...new Set([id, ...d])].sort();
}

// ── BUNG / GỘP ───────────────────────────────────────────────────────────
/** Khoảng cách bung, đơn vị TRÌNH BÀY. Đổi nó không đổi mệnh đề toán nào. */
export const EXPLODE_DISTANCE = 0.6;

export function explode(s: InteractionState, group: string): InteractionState {
  return s.exploded_groups.includes(group)
    ? s
    : { ...s, exploded_groups: [...s.exploded_groups, group].sort() };
}

export function collapse(s: InteractionState, group: string): InteractionState {
  return { ...s, exploded_groups: s.exploded_groups.filter((g) => g !== group) };
}

export function collapseAll(s: InteractionState): InteractionState {
  return { ...s, exploded_groups: [] };
}

/** Tâm hiển thị của một vật — trung bình các đỉnh nó có. Chỉ để BUNG. */
function _tam(o: SceneObject): [number, number, number] {
  const dinh: ExactVec3[] =
    o.vertices ?? o.polygon ?? (o.xyz ? [o.xyz] : o.point ? [o.point] : []);
  if (dinh.length === 0) return [0, 0, 0];
  const t: [number, number, number] = [0, 0, 0];
  for (const v of dinh) {
    t[0] += toNumber(v[0]);
    t[1] += toNumber(v[1]);
    t[2] += toNumber(v[2]);
  }
  return [t[0] / dinh.length, t[1] / dinh.length, t[2] / dinh.length];
}

function _soChuoi(x: number): Exact {
  return String(Math.round(x * 1e6) / 1e6);
}

/**
 * Biến đổi TRÌNH BÀY của một vật dưới trạng thái hiện tại.
 *
 * Quy tắc bung: TẤT ĐỊNH, dựa trên tâm — vật dịch ra xa tâm của cha nó (hoặc
 * gốc toạ độ nếu không có cha) một khoảng cố định. Không dùng LLM, không dùng
 * ngẫu nhiên, nên hai lần bung cùng một cảnh cho cùng một kết quả.
 *
 * ⚠️ Trả về một `visual_transform` MỚI. Không sửa `scene`, và không có đường
 * nào từ đây về toạ độ hình học — đó là toàn bộ điểm của việc tách hai thứ.
 */
export function visualTransformOf(
  s: InteractionState,
  scene: Scene3D,
  id: string,
): VisualTransform {
  const o = scene.objects.find((x) => x.id === id);
  if (!o) return BIEN_DOI_DONG_NHAT;
  const bung = (o.display_group ?? []).some((g) => s.exploded_groups.includes(g));
  if (!bung) return BIEN_DOI_DONG_NHAT;

  const cha = o.parent ? scene.objects.find((x) => x.id === o.parent) : undefined;
  const goc = cha ? _tam(cha) : ([0, 0, 0] as [number, number, number]);
  const t = _tam(o);
  const d: [number, number, number] = [t[0] - goc[0], t[1] - goc[1], t[2] - goc[2]];
  const n = Math.hypot(d[0], d[1], d[2]);
  if (n === 0) return BIEN_DOI_DONG_NHAT;
  const k = EXPLODE_DISTANCE / n;
  return {
    translate: [_soChuoi(d[0] * k), _soChuoi(d[1] * k), _soChuoi(d[2] * k)],
    scale: "1",
  };
}

// ── TUA BƯỚC ─────────────────────────────────────────────────────────────
export function setStep(
  s: InteractionState,
  scene: Scene3D,
  step: number,
): InteractionState {
  return { ...s, current_step: clampStep(scene, step) };
}

// ── CÂY PHÂN RÃ NGỮ NGHĨA ────────────────────────────────────────────────
export interface TreeNode {
  id: string;
  label: string;
  type: string;
  children: TreeNode[];
}

/**
 * Cây phân rã, dựng từ `parent` — KHÔNG hard-code theo loại bài.
 *
 * Vật không có cha thành nút gốc, xếp theo NHÓM HIỂN THỊ thay vì bị đoán một
 * cái cha. Đoán cha là chỗ cây sẽ nói sai về cấu trúc hình, và học sinh đọc
 * cây để hiểu hình chứ không phải để trang trí.
 */
export function semanticTree(scene: Scene3D): TreeNode[] {
  const nut = new Map<string, TreeNode>(
    scene.objects.map((o) => [
      o.id,
      { id: o.id, label: o.label, type: o.type, children: [] },
    ]),
  );
  const goc: TreeNode[] = [];
  const nhomGoc = new Map<string, TreeNode>();
  for (const o of scene.objects) {
    const n = nut.get(o.id)!;
    const cha = o.parent ? nut.get(o.parent) : undefined;
    if (cha && cha !== n) {
      cha.children.push(n);
      continue;
    }
    const ten = (o.display_group ?? [])[0] ?? "other";
    let g = nhomGoc.get(ten);
    if (!g) {
      g = { id: `group:${ten}`, label: ten, type: "group", children: [] };
      nhomGoc.set(ten, g);
      goc.push(g);
    }
    g.children.push(n);
  }
  return goc;
}

// ── TUẦN TỰ HOÁ ──────────────────────────────────────────────────────────
export function serialize(s: InteractionState): string {
  return JSON.stringify(s);
}

/**
 * Đọc lại một phiên. Thiếu trường ⇒ lấy mặc định; **không ném**.
 *
 * Một phiên lưu bằng bản cũ phải mở được bằng bản mới, nếu không thì lịch sử
 * thao tác của học sinh mất mỗi lần triển khai.
 */
export function deserialize(raw: string): InteractionState {
  let x: Partial<InteractionState> = {};
  try {
    x = JSON.parse(raw) as Partial<InteractionState>;
  } catch {
    return taoTrangThai();
  }
  const mang = (v: unknown): string[] =>
    Array.isArray(v) ? v.filter((z): z is string => typeof z === "string") : [];
  return {
    selected_id: typeof x.selected_id === "string" ? x.selected_id : null,
    hidden_ids: mang(x.hidden_ids),
    isolated_ids: mang(x.isolated_ids),
    exploded_groups: mang(x.exploded_groups),
    transparent_ids: mang(x.transparent_ids),
    current_step: typeof x.current_step === "number" ? x.current_step : 0,
  };
}
