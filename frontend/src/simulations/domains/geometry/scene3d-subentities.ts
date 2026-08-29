/**
 * THỰC THỂ CON THỊ GIÁC — mặt và cạnh của một khối, dựng từ TOPOLOGY.
 *
 * ─── VÌ SAO CẦN ─────────────────────────────────────────────────────────
 *
 * `solid` là **một** đối tượng mang `faces` là bảng chỉ số. Học sinh nhìn thấy
 * bốn mặt của hình chóp nhưng không bấm được vào mặt nào: với hệ, chúng không
 * tồn tại như những vật riêng. File này sinh ra chúng — **cho việc nhìn**.
 *
 * ─── ĐÂY KHÔNG PHẢI `GeometryState` MỚI ────────────────────────────────
 *
 * Không một toạ độ nào được TÍNH ở đây. Mặt lấy đỉnh từ `vertices` đã có,
 * theo `faces` đã có; cạnh lấy từ các cặp đỉnh liền nhau của mặt. Không
 * `cross`, không pháp tuyến, không diện tích — nếu một ngày cần pháp tuyến
 * thật thì nó phải đến từ kernel, không từ đây.
 *
 * `vertices` của mặt là **id ĐIỂM NGỮ NGHĨA**, không phải bản sao toạ độ: sự
 * thật chỉ có một chỗ, và một bản sao toạ độ ở tầng nhìn là chỗ nó sẽ lệch.
 *
 * ─── VÌ SAO CẦN `vertex_ids` ───────────────────────────────────────────
 *
 * `faces[i][j]` là chỉ số vào `vertices`. `depends` KHÔNG dùng thay được: nó
 * đã bị sắp theo thứ tự chữ, nên vị trí thứ `k` của nó không còn là đỉnh thứ
 * `k` của khối. Backend phát thêm `vertex_ids` theo đúng vị trí; thiếu nó thì
 * mặt không nói được nó gồm những điểm nào, và hàm này trả về rỗng thay vì
 * đoán.
 */
import {
  BIEN_DOI_DONG_NHAT,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";

/** Ngăn cách id khối với phần con. Không xuất hiện trong tên biến chương trình. */
export const NGAN_CACH = "::";

export interface SubEntity extends SceneObject {
  type: "face" | "edge";
  /** Id ĐIỂM NGỮ NGHĨA, theo thứ tự topology. Không phải bản sao toạ độ. */
  vertex_ids: string[];
  /** Toạ độ đọc lại từ khối — để vẽ, không phải nguồn sự thật. */
  polygon: ExactVec3[];
}

export function faceId(solidId: string, i: number): string {
  return `${solidId}${NGAN_CACH}face:${i}`;
}

export function edgeId(solidId: string, a: string, b: string): string {
  const [x, y] = a <= b ? [a, b] : [b, a];
  return `${solidId}${NGAN_CACH}edge:${x}-${y}`;
}

/** Id khối cha của một thực thể con, hoặc `null` nếu đây là vật ngữ nghĩa. */
export function parentSolidOf(id: string): string | null {
  const i = id.indexOf(NGAN_CACH);
  return i > 0 ? id.slice(0, i) : null;
}

export function isSubEntity(id: string): boolean {
  return id.includes(NGAN_CACH);
}

/**
 * Nhãn của một mặt: ghép nhãn các đỉnh — `"ABC"`, `"SAB"`.
 *
 * Không suy vai trò toán học nào từ nhãn. `"ABC"` chỉ nói *mặt đi qua A, B,
 * C*; nó **không** nói đó là đáy. Vai trò ấy hệ chưa biết, và đoán nó ở tầng
 * nhìn là dựng một kết luận hình học từ một chuỗi ký tự.
 */
export function faceLabel(ids: string[], nhan: Map<string, string>): string {
  const ten = ids.map((i) => nhan.get(i) ?? i);
  return ten.every((t) => t.length <= 3) ? ten.join("") : ten.join("–");
}

function _diemCuaKhoi(o: SceneObject): { ids: string[]; toa: ExactVec3[] } {
  const toa = o.vertices ?? [];
  const ids = (o as SceneObject & { vertex_ids?: string[] }).vertex_ids ?? [];
  return { ids, toa };
}

/**
 * Mọi mặt và cạnh của mọi khối trong cảnh, TẤT ĐỊNH.
 *
 * Cùng cảnh ⇒ cùng danh sách, cùng thứ tự: mặt theo chỉ số của `faces`, cạnh
 * theo thứ tự gặp và khử trùng theo cặp **không hướng** (cạnh AB của mặt này
 * và cạnh BA của mặt kia là MỘT cạnh).
 *
 * Khối thiếu `vertex_ids`, hoặc `faces` trỏ ra ngoài biên ⇒ **bỏ qua khối
 * ấy**, không sinh một phần. Một cây phân rã thiếu vài mặt còn đọc được;
 * một cây có mặt gồm những điểm sai thì nói dối về hình.
 */
export function deriveVisualSubEntities(scene: Scene3D): SubEntity[] {
  const nhan = new Map(scene.objects.map((o) => [o.id, o.label]));
  const ra: SubEntity[] = [];

  for (const o of scene.objects) {
    if (o.type !== "solid" || !o.faces) continue;
    const { ids, toa } = _diemCuaKhoi(o);
    if (ids.length === 0 || ids.length !== toa.length) continue;
    const hopLe = o.faces.every((f) =>
      f.length >= 3 && f.every((k) => Number.isInteger(k) && k >= 0 && k < ids.length),
    );
    if (!hopLe) continue;

    const daCoCanh = new Set<string>();
    o.faces.forEach((f, i) => {
      const dinhId = f.map((k) => ids[k]);
      ra.push({
        id: faceId(o.id, i),
        label: faceLabel(dinhId, nhan),
        type: "face",
        render: "polygon",
        origin: "derived",
        producer: `${o.producer ?? "construct_solid"}.face[${i}]`,
        // PHỤ THUỘC ở đây là THÀNH VIÊN TOPOLOGY, không phải phụ thuộc ngữ
        // nghĩa: mặt "gồm" các đỉnh ấy, chứ không được "dựng ra từ" chúng bởi
        // một phép dựng nào. Ô soi phải nói đúng điều đó.
        depends: dinhId,
        vertex_ids: dinhId,
        polygon: f.map((k) => toa[k]),
        parent: o.id,
        display_group: ["solid_component", "face"],
        visual_transform: { ...BIEN_DOI_DONG_NHAT },
        source: { instruction: `topology faces[${i}] của ${o.label}` },
      });

      for (let j = 0; j < f.length; j++) {
        const a = ids[f[j]];
        const b = ids[f[(j + 1) % f.length]];
        const eid = edgeId(o.id, a, b);
        if (daCoCanh.has(eid)) continue;
        daCoCanh.add(eid);
        ra.push({
          id: eid,
          label: faceLabel([a, b], nhan),
          type: "edge",
          render: "line",
          origin: "derived",
          producer: `${o.producer ?? "construct_solid"}.edge`,
          depends: [a, b],
          vertex_ids: [a, b],
          polygon: [toa[f[j]], toa[f[(j + 1) % f.length]]],
          parent: o.id,
          display_group: ["solid_component", "edge"],
          visual_transform: { ...BIEN_DOI_DONG_NHAT },
          source: { instruction: `topology cạnh của ${o.label}` },
        });
      }
    });
  }
  return ra;
}

/**
 * Cảnh kèm thực thể con — **một** danh sách để mọi tầng sau dùng chung.
 *
 * Trả một `Scene3D` mới; `scene` gốc không bị chạm. Hai danh sách song song
 * là chỗ chọn-ở-cây và chọn-ở-khung-nhìn sẽ tra hai bảng khác nhau rồi lệch.
 */
export function withSubEntities(scene: Scene3D): Scene3D {
  const con = deriveVisualSubEntities(scene);
  return con.length === 0
    ? scene
    : { ...scene, objects: [...scene.objects, ...con] };
}


/**
 * Id nào ĐÃ TỒN TẠI ở bước `step`, kể cả thực thể con.
 *
 * Mặt và cạnh **không có sự kiện riêng** trong timeline — chúng là topology
 * của khối, không phải một bước dựng. Nên chúng có mặt đúng lúc khối cha có
 * mặt. Bịa cho mỗi mặt một sự kiện là dựng timeline THỨ HAI, và §10 cấm.
 *
 * Tách khỏi component để kiểm được mà không cần DOM: đây là toàn bộ phần
 * "quyết định" của việc *"nút này trong cây có bấm được chưa"*.
 */
export function entitiesPresentAt(
  scene: Scene3D,
  step: number,
  objectsAt: (s: Scene3D, k: number) => SceneObject[],
): Set<string> {
  const co = new Set(objectsAt(scene, step).map((o) => o.id));
  for (const o of scene.objects) {
    const cha = parentSolidOf(o.id);
    if (cha && co.has(cha)) co.add(o.id);
  }
  return co;
}
