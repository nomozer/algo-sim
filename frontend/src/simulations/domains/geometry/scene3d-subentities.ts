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
  type: "face" | "edge" | "point3";
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

// ── THIẾT DIỆN ────────────────────────────────────────────────────────────
export function sectionVertexId(secId: string, i: number): string {
  return `${secId}${NGAN_CACH}vertex:${i}`;
}
export function sectionEdgeId(secId: string, i: number): string {
  return `${secId}${NGAN_CACH}edge:${i}`;
}
export function sectionFaceId(secId: string): string {
  return `${secId}${NGAN_CACH}face:0`;
}

function _khoaToa(v: ExactVec3): string {
  return v.join("|");
}

/**
 * Đỉnh thiết diện có TRÙNG một điểm ngữ nghĩa nào không — theo TOẠ ĐỘ CHÍNH XÁC.
 *
 * Đây **không phải suy đoán**. Toạ độ tới đây là chuỗi phân số đã tối giản do
 * kernel phát, nên `"1/2" === "1/2"` là một mệnh đề đúng-hoặc-sai, không phải
 * một phép so gần đúng. Trùng thì thiết diện gọi được tên học sinh đã đặt
 * (*"thiết diện MNPQ"*); không trùng thì gọi theo vị trí (*"đỉnh 1"*) — và
 * không bao giờ bịa một cái tên.
 *
 * Hai điểm ngữ nghĩa cùng toạ độ ⇒ **bỏ**, không chọn bừa một cái: một cái tên
 * sai còn tệ hơn không tên.
 */
function _banDoDiem(scene: Scene3D): Map<string, SceneObject | null> {
  const m = new Map<string, SceneObject | null>();
  for (const o of scene.objects) {
    // BỎ QUA thực thể con. Đỉnh thiết diện cũng là `point3` và cũng mang
    // đúng toạ độ ấy, nên tính cả chúng thì MỌI đỉnh đều "có hai điểm trùng"
    // và luật khử nhập nhằng sẽ xoá sạch mọi cái tên. Đã xảy ra thật ngay
    // lượt chạy đầu: `sectionDetails` trên cảnh ĐÃ dẫn xuất trả về
    // "Đỉnh 1..4" trong khi trên cảnh gốc trả về "P2, P1, …".
    if (isSubEntity(o.id)) continue;
    if (o.type !== "point3" || !o.xyz) continue;
    const k = _khoaToa(o.xyz);
    m.set(k, m.has(k) ? null : o);
  }
  return m;
}

/**
 * Đỉnh · cạnh · mặt của mọi THIẾT DIỆN trong cảnh, TẤT ĐỊNH.
 *
 * ─── VÌ SAO THIẾT DIỆN CẦN RIÊNG, KHÔNG DÙNG CHUNG VỚI KHỐI ─────────────
 *
 * Khối có `faces` là bảng CHỈ SỐ vào `vertex_ids` — mặt của nó gồm những điểm
 * ĐÃ CÓ TÊN. Thiết diện thì khác về bản chất: đỉnh của nó là **giao điểm mới
 * do kernel tính ra**, thường không trùng đỉnh nào của khối và không có tên
 * trong chương trình. Nên ở đây không có `vertex_ids` để đọc — có `polygon`
 * (dãy toạ độ đã sắp) và `steps` (mỗi cạnh kèm mặt sinh ra nó).
 *
 * ─── THỨ TỰ ĐẾN TỪ KERNEL, KHÔNG TỪ ĐÂY ────────────────────────────────
 *
 * Cạnh đi theo `steps` khi có, vì `steps` mang thêm `face_index` — thứ trả lời
 * *"cạnh này nằm trên mặt nào của khối"*, tức đúng câu học sinh phải trả lời
 * khi dựng trên giấy. Không có `steps` thì nối vòng theo `polygon`. Cả hai
 * đường đều **đọc lại** thứ tự kernel đã quyết; không có phép sắp xếp nào ở
 * đây, và sắp lại quanh trọng tâm chính là cách bản ngây thơ đánh mất thứ tự
 * dựng.
 */
export function deriveSectionSubEntities(scene: Scene3D): SubEntity[] {
  const diem = _banDoDiem(scene);
  const ra: SubEntity[] = [];

  for (const o of scene.objects) {
    if (o.type !== "section" || !o.polygon || o.polygon.length < 3) continue;
    const poly = o.polygon;
    const goc = o.producer ?? "construct_section";
    const ten = poly.map((v) => diem.get(_khoaToa(v)) ?? null);

    poly.forEach((v, i) => {
      const trung = ten[i];
      ra.push({
        id: sectionVertexId(o.id, i),
        label: trung?.label ?? `Đỉnh ${i + 1}`,
        type: "point3",
        render: "point_marker",
        origin: "derived",
        producer: `${goc}.vertex[${i}]`,
        // TRÙNG TOẠ ĐỘ là một quan hệ có thật và đáng nói; nó KHÔNG phải quan
        // hệ "được dựng ra từ". Ô soi nói đúng chừng ấy, không hơn.
        depends: trung ? [trung.id] : [],
        vertex_ids: trung ? [trung.id] : [],
        polygon: [v],
        xyz: v,
        parent: o.id,
        display_group: ["section_component", "vertex"],
        visual_transform: { ...BIEN_DOI_DONG_NHAT },
        source: {
          instruction: trung
            ? `đỉnh thứ ${i + 1} của ${o.label}, trùng điểm ${trung.label}`
            : `đỉnh thứ ${i + 1} của ${o.label} — giao điểm do kernel tính`,
        },
      });
    });

    const canh: { a: ExactVec3; b: ExactVec3; mat: number | null }[] =
      o.steps && o.steps.length > 0
        ? o.steps.map((s) => ({ a: s.a, b: s.b, mat: s.face_index }))
        : poly.map((v, i) => ({ a: v, b: poly[(i + 1) % poly.length], mat: null }));

    canh.forEach((c, i) => {
      const nA = diem.get(_khoaToa(c.a));
      const nB = diem.get(_khoaToa(c.b));
      ra.push({
        id: sectionEdgeId(o.id, i),
        label: nA && nB ? `${nA.label}${nB.label}` : `Cạnh ${i + 1}`,
        type: "edge",
        render: "line",
        origin: "derived",
        producer: `${goc}.edge[${i}]`,
        depends: [nA?.id, nB?.id].filter((x): x is string => !!x),
        vertex_ids: [nA?.id, nB?.id].filter((x): x is string => !!x),
        polygon: [c.a, c.b],
        parent: o.id,
        display_group: ["section_component", "edge"],
        visual_transform: { ...BIEN_DOI_DONG_NHAT },
        source: {
          instruction: c.mat === null
            ? `cạnh thứ ${i + 1} của ${o.label}`
            : `cạnh thứ ${i + 1} của ${o.label}, nằm trên mặt thứ ${c.mat + 1} của khối`,
        },
      });
    });

    // MẶT TÔ — vật `section` gốc chỉ vẽ ĐƯỜNG VIỀN (`render: "polygon"`), nên
    // "xem thiết diện" không có gì để nhìn ngoài bốn đoạn thẳng. Mảng tô này
    // là thứ làm thiết diện trông như một mặt cắt thật.
    ra.push({
      id: sectionFaceId(o.id),
      label: o.label,
      type: "face",
      render: "polygon",
      origin: "derived",
      producer: `${goc}.face`,
      depends: ten.filter((t): t is SceneObject => !!t).map((t) => t.id),
      vertex_ids: ten.filter((t): t is SceneObject => !!t).map((t) => t.id),
      polygon: [...poly],
      parent: o.id,
      display_group: ["section_component", "face"],
      visual_transform: { ...BIEN_DOI_DONG_NHAT },
      source: { instruction: `mặt cắt của ${o.label}` },
    });
  }
  return ra;
}

/**
 * Nhãn chu trình của một thiết diện — `"MNPQ"` khi mọi đỉnh gọi được tên.
 *
 * Trả `null` khi còn một đỉnh chưa có tên. **Không** ghép nửa tên nửa số:
 * `"MN-đỉnh 3-Q"` không phải cách ai gọi một thiết diện, và một cái tên gọi
 * được một nửa dễ bị đọc như cái tên đầy đủ.
 */
export function sectionCycleLabel(
  scene: Scene3D, sectionId: string,
): string | null {
  const sec = scene.objects.find((o) => o.id === sectionId);
  if (!sec?.polygon || sec.polygon.length < 3) return null;
  const diem = _banDoDiem(scene);
  const ten = sec.polygon.map((v) => diem.get(_khoaToa(v))?.label);
  return ten.every((t): t is string => !!t) ? ten.join("") : null;
}

export interface SectionDetails {
  /** Nhãn chu trình `"MNPQ"`, hoặc `null` khi còn đỉnh chưa có tên. */
  cycleLabel: string | null;
  vertexCount: number;
  /** Tên từng đỉnh theo CHU TRÌNH — có tên thì dùng tên, không thì "Đỉnh k". */
  vertexNames: string[];
  /** Id khối bị cắt, đọc theo KIỂU chứ không theo vị trí trong `depends`. */
  solidId: string | null;
  planeId: string | null;
}

/**
 * Dữ liệu ô soi của một thiết diện. `null` nếu `id` không phải thiết diện.
 *
 * ⚠️ Khối và mặt phẳng tra theo **KIỂU** của vật trong `depends`, không theo
 * thứ tự. `depends` đi qua `dependency_graph` phía server và bị sắp theo thứ
 * tự chữ ở đó, nên `depends[0]` là khối chỉ do may mắn về tên — `"chop"` đứng
 * trước `"mp"`, nhưng `"td"` cắt bởi `"alpha"` thì đảo ngay.
 */
export function sectionDetails(
  scene: Scene3D, id: string,
): SectionDetails | null {
  const sec = scene.objects.find((o) => o.id === id);
  if (sec?.type !== "section" || !sec.polygon) return null;
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const diem = _banDoDiem(scene);
  const cua = (loai: string) =>
    sec.depends.find((d) => theoId.get(d)?.type === loai) ?? null;
  return {
    cycleLabel: sectionCycleLabel(scene, id),
    vertexCount: sec.polygon.length,
    vertexNames: sec.polygon.map(
      (v, i) => diem.get(_khoaToa(v))?.label ?? `Đỉnh ${i + 1}`,
    ),
    solidId: sec.parent ?? cua("solid"),
    planeId: cua("plane3"),
  };
}

/**
 * Id cần giữ lại khi học sinh bấm «Xem thiết diện».
 *
 * Gồm thiết diện, mọi thực thể con của nó, **và khối bị cắt**. Giữ khối lại là
 * có chủ đích: khối vẽ ở độ mờ 0.22, nên nó thành cái vỏ trong suốt cho thấy
 * mặt cắt nằm ĐÂU trong hình — bỏ nó đi thì còn một đa giác lơ lửng, và đúng
 * thứ bài toán hỏi (*"thiết diện cắt khối ở chỗ nào"*) biến mất.
 *
 * Không giữ mặt phẳng cắt: nó vô hạn, và tấm mặt phẳng che mất chính thiết
 * diện nằm trên nó.
 */
export function sectionViewIds(scene: Scene3D, id: string): string[] {
  const sec = scene.objects.find((o) => o.id === id);
  if (sec?.type !== "section") return [];
  const con = scene.objects
    .filter((o) => o.parent === id)
    .map((o) => o.id);
  const ct = sectionDetails(scene, id);
  return [...new Set([id, ...con, ...(ct?.solidId ? [ct.solidId] : [])])].sort();
}

/**
 * Cảnh kèm thực thể con — **một** danh sách để mọi tầng sau dùng chung.
 *
 * Trả một `Scene3D` mới; `scene` gốc không bị chạm. Hai danh sách song song
 * là chỗ chọn-ở-cây và chọn-ở-khung-nhìn sẽ tra hai bảng khác nhau rồi lệch.
 */
export function withSubEntities(scene: Scene3D): Scene3D {
  const con = [...deriveVisualSubEntities(scene), ...deriveSectionSubEntities(scene)];
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
