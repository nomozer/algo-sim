import { GEOMETRY_SAMPLES, geometrySampleById, type GeometrySample } from "../../data/geometry-samples";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { historyStore } from "../../state/history";
import { useAppStore } from "../../state/store";

export type Vec3Tuple = readonly [number, number, number];

export interface LandingPointSpec {
  readonly id: string;
  readonly label: string;
  readonly role: "vertex" | "base_center" | "seed" | "intersection";
  readonly domainXyz: Vec3Tuple;
  readonly pos: Vec3Tuple;
}

export interface LandingEdgeSpec {
  readonly from: string;
  readonly to: string;
  readonly kind: "solid_edge" | "altitude" | "section_edge" | "guide";
}

export interface LandingStageMilestone {
  readonly id: string;
  readonly stepNumber: string;
  readonly tag: string;
  readonly title: string;
  readonly summary: string;
  readonly mathFact: string;
  readonly v14StepLabel?: string;
  readonly v14ShortTab?: string;
  readonly v14Title?: string;
  readonly v14Guide?: string;
  readonly v14Focus?: string;
  readonly visiblePoints: readonly string[];
  readonly activePoints: readonly string[];
  readonly visibleSolidEdges: readonly string[];
  readonly showGuideEdges: boolean;
  readonly planeOpacity: number;
  readonly sectionProgress: number;
  readonly sectionFillOpacity: number;
  readonly cameraPos: Vec3Tuple;
  readonly lookAt: Vec3Tuple;
  readonly v14CameraPos?: Vec3Tuple;
  readonly v14LookAt?: Vec3Tuple;
}

export interface LandingMetricChip {
  readonly label: string;
  readonly value: string;
}

export interface LandingSampleSpec {
  readonly id: string;
  readonly shortName: string;
  readonly categoryLabel: string;
  readonly title: string;
  readonly problemText: string;
  readonly v14Premise?: string;
  readonly equationText: string;
  readonly answerBadge: string;
  readonly verifiedMetrics: readonly LandingMetricChip[];
  readonly points: readonly LandingPointSpec[];
  readonly pointMap: Readonly<Record<string, LandingPointSpec>>;
  readonly solidEdges: readonly LandingEdgeSpec[];
  readonly guideEdges: readonly LandingEdgeSpec[];
  readonly solidFaces: readonly (readonly string[])[];
  readonly sectionLoop: readonly string[];
  readonly planeQuad: readonly Vec3Tuple[];
  readonly basePolygon: readonly string[];
  readonly altitudePair?: readonly [string, string];
  readonly radiusBound: number;
  readonly defaultCamera: Vec3Tuple;
  readonly defaultLookAt: Vec3Tuple;
  readonly milestones: readonly LandingStageMilestone[];
}

function parseExactNumber(raw: string | number): number {
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : 0;
  const trimmed = raw.trim();
  if (trimmed.includes("/")) {
    const [num, den] = trimmed.split("/");
    const n = Number(num);
    const d = Number(den);
    if (Number.isFinite(n) && Number.isFinite(d) && Math.abs(d) > 1e-12) {
      return n / d;
    }
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : 0;
}

function toThreeVec(xyz: Vec3Tuple, center: Vec3Tuple): Vec3Tuple {
  return [
    Number((xyz[0] - center[0]).toFixed(5)),
    Number((xyz[2] - center[2]).toFixed(5)),
    Number((-(xyz[1] - center[1])).toFixed(5)),
  ];
}

interface RawSceneObject {
  id: string;
  notation?: string;
  type?: string;
  xyz?: readonly (string | number)[];
  value?: string;
}

export function extractPointsFromSample(
  sample: GeometrySample | undefined,
  fallbackPoints: readonly { id: string; label: string; xyz: Vec3Tuple }[],
): readonly { id: string; label: string; xyz: Vec3Tuple }[] {
  const objects = (
    sample?.envelope as { scene3d?: { objects?: readonly RawSceneObject[] } } | undefined
  )?.scene3d?.objects;

  if (!Array.isArray(objects)) return fallbackPoints;

  const extracted: { id: string; label: string; xyz: Vec3Tuple }[] = [];
  const seenIds = new Set<string>();
  for (const obj of objects) {
    if (obj.type === "point3" && Array.isArray(obj.xyz) && obj.xyz.length === 3) {
      const normalizedId = obj.id.trim();
      if (!normalizedId || seenIds.has(normalizedId)) continue;
      seenIds.add(normalizedId);
      extracted.push({
        id: normalizedId,
        label: obj.notation || normalizedId,
        xyz: [
          parseExactNumber(obj.xyz[0]),
          parseExactNumber(obj.xyz[1]),
          parseExactNumber(obj.xyz[2]),
        ],
      });
    }
  }
  return extracted.length >= fallbackPoints.length ? extracted : fallbackPoints;
}

export function computeBoundedPlaneQuad(
  sectionWorldPts: readonly Vec3Tuple[],
  normal: Vec3Tuple,
  margin = 0.72,
): readonly Vec3Tuple[] {
  let cx = 0;
  let cy = 0;
  let cz = 0;
  for (const p of sectionWorldPts) {
    cx += p[0];
    cy += p[1];
    cz += p[2];
  }
  const count = Math.max(1, sectionWorldPts.length);
  cx /= count;
  cy /= count;
  cz /= count;

  const nLen = Math.hypot(normal[0], normal[1], normal[2]) || 1;
  const nx = normal[0] / nLen;
  const ny = normal[1] / nLen;
  const nz = normal[2] / nLen;

  // Pick a stable orthonormal tangent frame (u, v) in the plane
  const seed: Vec3Tuple = Math.abs(ny) < 0.85 ? [0, 1, 0] : [1, 0, 0];
  let ux = ny * seed[2] - nz * seed[1];
  let uy = nz * seed[0] - nx * seed[2];
  let uz = nx * seed[1] - ny * seed[0];
  const uLen = Math.hypot(ux, uy, uz) || 1;
  ux /= uLen;
  uy /= uLen;
  uz /= uLen;

  const vx = ny * uz - nz * uy;
  const vy = nz * ux - nx * uz;
  const vz = nx * uy - ny * ux;

  let minU = Infinity;
  let maxU = -Infinity;
  let minV = Infinity;
  let maxV = -Infinity;
  for (const p of sectionWorldPts) {
    const dx = p[0] - cx;
    const dy = p[1] - cy;
    const dz = p[2] - cz;
    const pu = dx * ux + dy * uy + dz * uz;
    const pv = dx * vx + dy * vy + dz * vz;
    if (pu < minU) minU = pu;
    if (pu > maxU) maxU = pu;
    if (pv < minV) minV = pv;
    if (pv > maxV) maxV = pv;
  }

  minU -= margin;
  maxU += margin;
  minV -= margin * 0.88;
  maxV += margin * 0.88;

  const corner = (u: number, v: number): Vec3Tuple => [
    cx + ux * u + vx * v,
    cy + uy * u + vy * v,
    cz + uz * u + vz * v,
  ];

  return [
    corner(minU, minV),
    corner(maxU, minV),
    corner(maxU, maxV),
    corner(minU, maxV),
  ];
}

function buildPyramidSample(): LandingSampleSpec {
  const sampleId = "chop-thiet-dien-ba-diem";
  const rawSample = geometrySampleById(sampleId);
  const center: Vec3Tuple = [2, 2, 2.65];

  const rawPoints = extractPointsFromSample(rawSample, [
    { id: "A", label: "A", xyz: [0, 0, 0] },
    { id: "B", label: "B", xyz: [4, 0, 0] },
    { id: "C", label: "C", xyz: [4, 4, 0] },
    { id: "D", label: "D", xyz: [0, 4, 0] },
    { id: "S", label: "S", xyz: [0, 0, 6] },
    { id: "O", label: "O", xyz: [2, 2, 0] },
    { id: "M", label: "M", xyz: [0, 0, 3] },
    { id: "N", label: "N", xyz: [4, 2, 0] },
    { id: "P", label: "P", xyz: [2, 4, 0] },
    { id: "E", label: "E", xyz: [3, 0, 1.5] },
    { id: "F", label: "F", xyz: [0, 3, 1.5] },
  ]);

  const roleMap: Record<string, LandingPointSpec["role"]> = {
    A: "vertex",
    B: "vertex",
    C: "vertex",
    D: "vertex",
    S: "vertex",
    O: "base_center",
    M: "seed",
    N: "seed",
    P: "seed",
    E: "intersection",
    F: "intersection",
  };

  const points: LandingPointSpec[] = rawPoints.map((p) => ({
    id: p.id,
    label: p.label,
    role: roleMap[p.id] ?? "vertex",
    domainXyz: p.xyz,
    pos: toThreeVec(p.xyz, center),
  }));

  const pointMap = Object.fromEntries(points.map((p) => [p.id, p]));
  const sectionLoop = ["M", "E", "N", "P", "F"] as const;
  const sectionWorld = sectionLoop.map((id) => pointMap[id].pos);
  // Domain plane x + y + 2z = 6 => normal in domain = (1, 1, 2) => Three.js (1, 2, -1)
  const planeQuad = computeBoundedPlaneQuad(sectionWorld, [1, 2, -1], 0.4);

  const solidEdges: readonly LandingEdgeSpec[] = [
    { from: "A", to: "B", kind: "solid_edge" },
    { from: "B", to: "C", kind: "solid_edge" },
    { from: "C", to: "D", kind: "solid_edge" },
    { from: "D", to: "A", kind: "solid_edge" },
    { from: "S", to: "A", kind: "altitude" },
    { from: "S", to: "B", kind: "solid_edge" },
    { from: "S", to: "C", kind: "solid_edge" },
    { from: "S", to: "D", kind: "solid_edge" },
  ];

  const guideEdges: readonly LandingEdgeSpec[] = [
    { from: "A", to: "C", kind: "guide" },
    { from: "B", to: "D", kind: "guide" },
  ];

  return {
    id: sampleId,
    shortName: "Hình chóp S.ABCD",
    categoryLabel: "Thiết diện phẳng",
    title:
      (rawSample?.envelope?.title as string | undefined) ||
      "Thiết diện hình chóp S.ABCD cắt bởi mặt phẳng (MNP)",
    problemText:
      rawSample?.problemText ||
      "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh bằng 4, cạnh bên SA vuông góc với đáy (ABCD) và SA = 6. M, N, P lần lượt là trung điểm của SA, BC và CD. Mặt phẳng (MNP) cắt SB tại E, SD tại F tạo thành thiết diện MENPF.",
    v14Premise:
      "Đáy ABCD là hình vuông cạnh a = 4, đường cao SA = 6 ⊥ (ABCD); M, N, P là trung điểm SA, BC, CD.",
    equationText: "x + y + 2z = 6",
    answerBadge: "S(MENPF) = 6√6",
    verifiedMetrics: [
      { label: "Thiết diện", value: "S(MENPF) = 6√6" },
      { label: "Thể tích khối chóp", value: "V(S.ABCD) = 32" },
    ],
    points,
    pointMap,
    solidEdges,
    guideEdges,
    solidFaces: [
      ["A", "B", "C", "D"],
      ["S", "A", "B"],
      ["S", "B", "C"],
      ["S", "C", "D"],
      ["S", "D", "A"],
    ],
    sectionLoop,
    planeQuad,
    basePolygon: ["A", "B", "C", "D"],
    altitudePair: ["S", "A"],
    radiusBound: 4.5,
    defaultCamera: [13.5, 7.6, -7.5],
    defaultLookAt: [0, 0.05, 0],
    milestones: [
      {
        id: "stage-problem",
        stepNumber: "01",
        tag: "Đề bài & khối chóp",
        title: "Biến câu chữ thành tọa độ xác thực",
        summary:
          "Khởi tạo hình chóp S.ABCD với đáy hình vuông cạnh 4 tâm O, đường cao SA = 6 vuông góc đáy và ba trung điểm gốc M, N, P.",
        mathFact: "S(0; 0; 6) · SA ⊥ (ABCD) · M(0; 0; 3), N(4; 2; 0), P(2; 4; 0)",
        visiblePoints: ["A", "B", "C", "D", "S", "O", "M", "N", "P"],
        activePoints: ["S", "A", "M", "N", "P"],
        visibleSolidEdges: ["AB", "BC", "CD", "DA", "SA", "SB", "SC", "SD"],
        showGuideEdges: true,
        planeOpacity: 0,
        sectionProgress: 0,
        sectionFillOpacity: 0,
        cameraPos: [12.4, 7.2, -6.2],
        lookAt: [0, 0.25, 0],
        v14StepLabel: "Bước 1 · Khối gốc",
        v14ShortTab: "1. Khối chóp",
        v14Title: "Dựng khối chóp và ba điểm gốc",
        v14Guide:
          "Quan sát khối chóp đáy vuông, đường cao hạ từ đỉnh xuống đáy cùng ba trung điểm xuất phát trên các cạnh.",
        v14Focus:
          "Điểm cần chú ý: Đường cao SA vuông góc với mặt đáy ABCD và vị trí M, N, P.",
        v14CameraPos: [11.5, 6.6, -6.2],
        v14LookAt: [0, 0.16, 0],
      },
      {
        id: "stage-structure",
        stepNumber: "02",
        tag: "Hình thành cấu trúc",
        title: "Xác lập mặt phẳng cắt (MNP)",
        summary:
          "Từ ba điểm không thẳng hàng M, N, P, hệ dựng mặt phẳng chuẩn x + y + 2z = 6 với khung giới hạn gọn quanh hình chóp.",
        mathFact: "Mặt phẳng (MNP): x + y + 2z = 6 · Vectơ pháp tuyến n = (1; 1; 2)",
        visiblePoints: ["A", "B", "C", "D", "S", "O", "M", "N", "P"],
        activePoints: ["M", "N", "P"],
        visibleSolidEdges: ["AB", "BC", "CD", "DA", "SA", "SB", "SC", "SD"],
        showGuideEdges: false,
        planeOpacity: 0.72,
        sectionProgress: 0.2,
        sectionFillOpacity: 0,
        cameraPos: [11.2, 7.8, -7.6],
        lookAt: [0, 0.22, 0],
        v14StepLabel: "Bước 2 · Mặt phẳng cắt",
        v14ShortTab: "2. Mặt (MNP)",
        v14Title: "Xác lập mặt phẳng (MNP)",
        v14Guide:
          "Mặt phẳng cắt đi qua ba điểm M, N, P nằm nghiêng qua lòng khối chóp và mở ra khung quan sát.",
        v14Focus:
          "Điểm cần chú ý: Giao tuyến NP nằm hoàn toàn trên mặt đáy ABCD.",
        v14CameraPos: [10.5, 7.0, -7.2],
        v14LookAt: [0, 0.16, 0],
      },
      {
        id: "stage-relations",
        stepNumber: "03",
        tag: "Khám phá quan hệ",
        title: "Giao tuyến cắt cạnh bên tại E và F",
        summary:
          "Giao (MNP) với các mặt bên tạo thành các đoạn NP, PF, FM, ME, EN, xác định đúng hai giao điểm E trên SB và F trên SD.",
        mathFact: "E = (MNP) ∩ SB = (3; 0; 3/2) · F = (MNP) ∩ SD = (0; 3; 3/2)",
        visiblePoints: ["A", "B", "C", "D", "S", "O", "M", "N", "P", "E", "F"],
        activePoints: ["E", "F"],
        visibleSolidEdges: ["AB", "BC", "CD", "DA", "SA", "SB", "SC", "SD"],
        showGuideEdges: false,
        planeOpacity: 0.78,
        sectionProgress: 0.85,
        sectionFillOpacity: 0.22,
        cameraPos: [12.6, 6.5, -5.4],
        lookAt: [0, 0.22, 0],
        v14StepLabel: "Bước 3 · Điểm cắt cạnh bên",
        v14ShortTab: "3. Giao điểm",
        v14Title: "Xác định các giao điểm mới",
        v14Guide:
          "Khi mặt phẳng cắt gặp các mặt bên, giao tuyến kéo dài từ mặt đáy sẽ cắt thêm hai cạnh bên của khối chóp.",
        v14Focus:
          "Điểm cần chú ý: Cách mặt phẳng tìm ra hai giao điểm E trên SB và F trên SD.",
        v14CameraPos: [11.5, 6.1, -5.5],
        v14LookAt: [0, 0.16, 0],
      },
      {
        id: "stage-result",
        stepNumber: "04",
        tag: "Kết quả trực quan",
        title: "Thiết diện ngũ giác MENPF khép kín",
        summary:
          "Toàn bộ thiết diện ngũ giác hiện rõ cả hình khối lẫn đại lượng chính xác, sẵn sàng để xoay tự do hoặc mở vào Xưởng 3D.",
        mathFact: "Ngũ giác phẳng MENPF thuộc mặt phẳng (MNP): x + y + 2z = 6",
        visiblePoints: ["A", "B", "C", "D", "S", "O", "M", "N", "P", "E", "F"],
        activePoints: ["M", "E", "N", "P", "F"],
        visibleSolidEdges: ["AB", "BC", "CD", "DA", "SA", "SB", "SC", "SD"],
        showGuideEdges: false,
        planeOpacity: 0.56,
        sectionProgress: 1,
        sectionFillOpacity: 0.88,
        cameraPos: [11.9, 7.1, -6.9],
        lookAt: [0, 0.25, 0],
        v14StepLabel: "Bước 4 · Thiết diện hoàn chỉnh",
        v14ShortTab: "4. Thiết diện",
        v14Title: "Khép kín ngũ giác thiết diện",
        v14Guide:
          "Năm đoạn giao tuyến khép kín thành đa giác phẳng nằm trên mặt cắt. Xoay khối 3D để kiểm tra từng cạnh.",
        v14Focus:
          "Gợi ý quan sát: Thử xoay nhìn từ trên xuống để thấy rõ ngũ giác cắt qua năm mặt.",
        v14CameraPos: [11.1, 6.5, -6.5],
        v14LookAt: [0, 0.16, 0],
      },
    ],
  };
}

function buildCubeSample(): LandingSampleSpec {
  const sampleId = "lap-phuong-thiet-dien-bat-ky";
  const rawSample = geometrySampleById(sampleId);
  const center: Vec3Tuple = [2, 2, 2];

  const rawPoints = extractPointsFromSample(rawSample, [
    { id: "A", label: "A", xyz: [0, 0, 0] },
    { id: "B", label: "B", xyz: [4, 0, 0] },
    { id: "C", label: "C", xyz: [4, 4, 0] },
    { id: "D", label: "D", xyz: [0, 4, 0] },
    { id: "A_prime", label: "A′", xyz: [0, 0, 4] },
    { id: "B_prime", label: "B′", xyz: [4, 0, 4] },
    { id: "C_prime", label: "C′", xyz: [4, 4, 4] },
    { id: "D_prime", label: "D′", xyz: [0, 4, 4] },
    { id: "M", label: "M", xyz: [0, 2, 0] },
    { id: "N", label: "N", xyz: [2, 4, 0] },
    { id: "P", label: "P", xyz: [4, 2, 4] },
    { id: "E", label: "E", xyz: [4, 4, 2] },
    { id: "F", label: "F", xyz: [2, 0, 4] },
    { id: "Q", label: "Q", xyz: [0, 0, 2] },
  ]);

  const roleMap: Record<string, LandingPointSpec["role"]> = {
    M: "seed",
    N: "seed",
    P: "seed",
    E: "intersection",
    F: "intersection",
    Q: "intersection",
  };

  const points: LandingPointSpec[] = rawPoints.map((p) => ({
    id: p.id,
    label: p.label,
    role: roleMap[p.id] ?? "vertex",
    domainXyz: p.xyz,
    pos: toThreeVec(p.xyz, center),
  }));

  const pointMap = Object.fromEntries(points.map((p) => [p.id, p]));
  const sectionLoop = ["M", "N", "E", "P", "F", "Q"] as const;
  const sectionWorld = sectionLoop.map((id) => pointMap[id].pos);
  // Domain plane -x + y + z = 2 => normal (-1, 1, 1) => Three.js (-1, 1, -1)
  const planeQuad = computeBoundedPlaneQuad(sectionWorld, [-1, 1, -1], 0.26);

  const solidEdges: readonly LandingEdgeSpec[] = [
    { from: "A", to: "B", kind: "solid_edge" },
    { from: "B", to: "C", kind: "solid_edge" },
    { from: "C", to: "D", kind: "solid_edge" },
    { from: "D", to: "A", kind: "solid_edge" },
    { from: "A_prime", to: "B_prime", kind: "solid_edge" },
    { from: "B_prime", to: "C_prime", kind: "solid_edge" },
    { from: "C_prime", to: "D_prime", kind: "solid_edge" },
    { from: "D_prime", to: "A_prime", kind: "solid_edge" },
    { from: "A", to: "A_prime", kind: "solid_edge" },
    { from: "B", to: "B_prime", kind: "solid_edge" },
    { from: "C", to: "C_prime", kind: "solid_edge" },
    { from: "D", to: "D_prime", kind: "solid_edge" },
  ];

  const allEdgeKeys = solidEdges.map((e) => `${e.from}-${e.to}`);

  return {
    id: sampleId,
    shortName: "Lập phương ABCD.A′B′C′D′",
    categoryLabel: "Lục giác đều",
    title:
      (rawSample?.envelope?.title as string | undefined) ||
      "Thiết diện lục giác đều của hình lập phương ABCD.A′B′C′D′",
    problemText:
      rawSample?.problemText ||
      "Cho hình lập phương ABCD.A′B′C′D′ có cạnh bằng 4. M, N, P là trung điểm AD, CD và B′C′. Mặt phẳng (MNP) cắt CC′, A′B′, AA′ tại E, F, Q tạo thành thiết diện lục giác đều MNEPFQ.",
    v14Premise:
      "Hình lập phương ABCD.A′B′C′D′ cạnh a = 4; M, N, P là trung điểm AD, CD và B′C′.",
    equationText: "-x + y + z = 2",
    answerBadge: "S(MNEPFQ) = 12√3",
    verifiedMetrics: [
      { label: "Thiết diện lục giác", value: "S(MNEPFQ) = 12√3" },
      { label: "Cạnh thiết diện", value: "MN = 2√2" },
    ],
    points,
    pointMap,
    solidEdges,
    guideEdges: [],
    solidFaces: [
      ["A", "B", "C", "D"],
      ["A_prime", "B_prime", "C_prime", "D_prime"],
      ["A", "B", "B_prime", "A_prime"],
      ["B", "C", "C_prime", "B_prime"],
      ["C", "D", "D_prime", "C_prime"],
      ["D", "A", "A_prime", "D_prime"],
    ],
    sectionLoop,
    planeQuad,
    basePolygon: ["A", "B", "C", "D"],
    radiusBound: 4.1,
    defaultCamera: [9.6, 6.1, -6.8],
    defaultLookAt: [0, 0, 0],
    milestones: [
      {
        id: "cube-1",
        stepNumber: "01",
        tag: "Khối lập phương",
        title: "Khởi tạo hình lập phương cạnh 4",
        summary:
          "Đặt hai đáy ABCD, A′B′C′D′ cùng ba trung điểm gốc M ∈ AD, N ∈ CD, P ∈ B′C′.",
        mathFact: "Cạnh a = 4 · M(0; 2; 0), N(2; 4; 0), P(4; 2; 4)",
        visiblePoints: [
          "A",
          "B",
          "C",
          "D",
          "A_prime",
          "B_prime",
          "C_prime",
          "D_prime",
          "M",
          "N",
          "P",
        ],
        activePoints: ["M", "N", "P"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: false,
        planeOpacity: 0,
        sectionProgress: 0,
        sectionFillOpacity: 0,
        cameraPos: [9.9, 6.3, -6.2],
        lookAt: [0, 0, 0],
        v14StepLabel: "Bước 1 · Khối gốc",
        v14ShortTab: "1. Lập phương",
        v14Title: "Dựng hình lập phương và ba trung điểm",
        v14Guide:
          "Hai đáy đối diện và bốn cạnh bên song song tạo thành khung đối xứng quanh tâm, với ba điểm xuất phát M, N, P.",
        v14Focus:
          "Điểm cần chú ý: M, N thuộc mặt đáy dưới và P nằm ở mặt đáy trên.",
        v14CameraPos: [9.4, 6.1, -6.3],
        v14LookAt: [0, 0.02, 0],
      },
      {
        id: "cube-2",
        stepNumber: "02",
        tag: "Mặt cắt phẳng",
        title: "Xác định mặt phẳng (MNP)",
        summary:
          "Mặt phẳng đi qua ba trung điểm đối xứng có phương trình -x + y + z = 2, cắt sáu cạnh lập phương.",
        mathFact: "(MNP): -x + y + z = 2",
        visiblePoints: [
          "A",
          "B",
          "C",
          "D",
          "A_prime",
          "B_prime",
          "C_prime",
          "D_prime",
          "M",
          "N",
          "P",
        ],
        activePoints: ["M", "N", "P"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: false,
        planeOpacity: 0.72,
        sectionProgress: 0.17,
        sectionFillOpacity: 0,
        cameraPos: [9.1, 6.8, -7.2],
        lookAt: [0, 0, 0],
        v14StepLabel: "Bước 2 · Mặt phẳng cắt",
        v14ShortTab: "2. Mặt (MNP)",
        v14Title: "Đặt mặt phẳng chéo qua hình lập phương",
        v14Guide:
          "Mặt phẳng (MNP) đi nghiêng qua tâm hình lập phương, cắt qua cả hai mặt đáy trên dưới và các mặt xung quanh.",
        v14Focus:
          "Điểm cần chú ý: Hướng song song giữa các cặp mặt đối diện của lập phương.",
        v14CameraPos: [8.8, 6.5, -7.0],
        v14LookAt: [0, 0.02, 0],
      },
      {
        id: "cube-3",
        stepNumber: "03",
        tag: "Sáu giao điểm",
        title: "Tìm E ∈ CC′, F ∈ A′B′, Q ∈ AA′",
        summary:
          "Các giao điểm lần lượt nằm đúng tại trung điểm ba cạnh còn lại, chia mỗi cặp cạnh song song thành các đoạn bằng nhau 2√2.",
        mathFact: "E(4; 4; 2) · F(2; 0; 4) · Q(0; 0; 2)",
        visiblePoints: points.map((p) => p.id),
        activePoints: ["E", "F", "Q"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: false,
        planeOpacity: 0.75,
        sectionProgress: 0.83,
        sectionFillOpacity: 0.25,
        cameraPos: [10.1, 5.7, -5.8],
        lookAt: [0, 0, 0],
        v14StepLabel: "Bước 3 · Mở rộng giao tuyến",
        v14ShortTab: "3. Giao điểm",
        v14Title: "Tìm thêm giao điểm trên ba cạnh còn lại",
        v14Guide:
          "Lần theo từng cặp mặt song song, mặt phẳng cắt tuần tự xác định thêm ba điểm E, F, Q trên các cạnh bên và đáy trên.",
        v14Focus:
          "Điểm cần chú ý: Các cặp giao tuyến trên mặt đối diện luôn giữ hướng song song.",
        v14CameraPos: [9.5, 5.8, -5.9],
        v14LookAt: [0, 0.02, 0],
      },
      {
        id: "cube-4",
        stepNumber: "04",
        tag: "Lục giác đều",
        title: "Khép kín thiết diện MNEPFQ",
        summary:
          "Sáu cạnh đều bằng 2√2 tạo thành lục giác đều hoàn chỉnh có diện tích 12√3.",
        mathFact: "Lục giác đều 6 cạnh bằng nhau thuộc mặt phẳng (MNP): -x + y + z = 2",
        visiblePoints: points.map((p) => p.id),
        activePoints: ["M", "N", "E", "P", "F", "Q"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: false,
        planeOpacity: 0.56,
        sectionProgress: 1,
        sectionFillOpacity: 0.88,
        cameraPos: [9.6, 6.1, -6.8],
        lookAt: [0, 0, 0],
        v14StepLabel: "Bước 4 · Thiết diện lục giác",
        v14ShortTab: "4. Lục giác đều",
        v14Title: "Khép kín lục giác thiết diện đối xứng",
        v14Guide:
          "Sáu đoạn giao tuyến trên sáu mặt của hình lập phương nối kín với nhau. Xoay trực tiếp để nhìn chính diện mặt cắt.",
        v14Focus:
          "Gợi ý quan sát: Đặt góc nhìn trực diện vào mặt phẳng cắt để thấy hình lục giác cân đối.",
        v14CameraPos: [9.2, 6.0, -6.7],
        v14LookAt: [0, 0.02, 0],
      },
    ],
  };
}

function buildStoryPrismSpec(): LandingSampleSpec {
  const s3 = Math.sqrt(3);
  const center: Vec3Tuple = [2, (2 * s3) / 3, 2];
  const rawPoints: readonly { id: string; label: string; role: LandingPointSpec["role"]; xyz: Vec3Tuple }[] = [
    { id: "A", label: "A", role: "vertex", xyz: [0, 0, 0] },
    { id: "B", label: "B", role: "vertex", xyz: [4, 0, 0] },
    { id: "C", label: "C", role: "vertex", xyz: [2, 2 * s3, 0] },
    { id: "A_prime", label: "A′", role: "vertex", xyz: [0, 0, 4] },
    { id: "B_prime", label: "B′", role: "vertex", xyz: [4, 0, 4] },
    { id: "C_prime", label: "C′", role: "vertex", xyz: [2, 2 * s3, 4] },
    { id: "M", label: "M", role: "seed", xyz: [2, 0, 0] },
    { id: "N", label: "N", role: "seed", xyz: [1, s3, 0] },
    { id: "P", label: "P", role: "seed", xyz: [2, 2 * s3, 2] },
    { id: "Q", label: "Q", role: "intersection", xyz: [4, 0, 2] },
  ];

  const points: LandingPointSpec[] = rawPoints.map((p) => ({
    id: p.id,
    label: p.label,
    role: p.role,
    domainXyz: p.xyz,
    pos: toThreeVec(p.xyz, center),
  }));

  const pointMap = Object.fromEntries(points.map((p) => [p.id, p]));
  const sectionLoop = ["M", "N", "P", "Q"] as const;
  const sectionWorld = sectionLoop.map((id) => pointMap[id].pos);
  // Domain plane √3x + y - √3z = 2√3 -> Three.js normal (√3, -√3, -1)
  const planeQuad = computeBoundedPlaneQuad(sectionWorld, [s3, -s3, -1], 0.44);

  const solidEdges: readonly LandingEdgeSpec[] = [
    { from: "A", to: "B", kind: "solid_edge" },
    { from: "B", to: "C", kind: "solid_edge" },
    { from: "C", to: "A", kind: "solid_edge" },
    { from: "A_prime", to: "B_prime", kind: "solid_edge" },
    { from: "B_prime", to: "C_prime", kind: "solid_edge" },
    { from: "C_prime", to: "A_prime", kind: "solid_edge" },
    { from: "A", to: "A_prime", kind: "solid_edge" },
    { from: "B", to: "B_prime", kind: "solid_edge" },
    { from: "C", to: "C_prime", kind: "solid_edge" },
  ];
  const allEdgeKeys = solidEdges.map((e) => `${e.from}-${e.to}`);

  return {
    id: "lang-tru-tam-giac-thiet-dien",
    shortName: "Lăng trụ ABC.A′B′C′",
    categoryLabel: "Thiết diện hình thang cân",
    title: "Thiết diện hình thang cân của lăng trụ tam giác đều ABC.A′B′C′",
    problemText:
      "Cho lăng trụ tam giác đều ABC.A′B′C′ có tất cả các cạnh bằng 4. M, N, P lần lượt là trung điểm của AB, AC và CC′. Mặt phẳng (MNP) cắt BB′ tại Q tạo thành thiết diện hình thang cân MNPQ.",
    equationText: "√3x + y − √3z = 2√3",
    answerBadge: "S(MNPQ) = 3√7",
    verifiedMetrics: [
      { label: "Thiết diện", value: "Hình thang cân MNPQ" },
      { label: "Độ dài đáy", value: "MN = 2 · PQ = 4" },
      { label: "Diện tích", value: "S(MNPQ) = 3√7" },
    ],
    points,
    pointMap,
    solidEdges,
    guideEdges: [{ from: "B", to: "C", kind: "guide" }],
    solidFaces: [
      ["A", "C", "B"],
      ["A_prime", "B_prime", "C_prime"],
      ["A", "B", "B_prime", "A_prime"],
      ["B", "C", "C_prime", "B_prime"],
      ["C", "A", "A_prime", "C_prime"],
    ],
    sectionLoop,
    planeQuad,
    basePolygon: ["A", "B", "C"],
    radiusBound: 4.1,
    defaultCamera: [1.8, 4.4, 9.8],
    defaultLookAt: [0, 0.05, 0],
    milestones: [
      {
        id: "story-1",
        stepNumber: "01",
        tag: "Đề bài",
        title: "Từ đề bài tiếng Việt dựng khối ABC.A′B′C′",
        summary:
          "Axo trích xuất giả thiết lăng trụ tam giác đều cạnh 4 và ghim đúng ba trung điểm gốc M ∈ AB, N ∈ AC, P ∈ CC′.",
        mathFact: "A(0;0;0), B(4;0;0), C(2;2√3;0) · Ba điểm gốc M, N, P",
        visiblePoints: ["A", "B", "C", "A_prime", "B_prime", "C_prime", "M", "N", "P"],
        activePoints: ["M", "N", "P"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: false,
        planeOpacity: 0,
        sectionProgress: 0,
        sectionFillOpacity: 0,
        cameraPos: [1.8, 4.4, 9.8],
        lookAt: [0, 0.05, 0],
      },
      {
        id: "story-2",
        stepNumber: "02",
        tag: "Phân tích",
        title: "Nhận ra quan hệ song song MN // BC",
        summary:
          "Trong đáy (ABC), đường trung bình MN song song với BC; vì BC nằm trong mặt bên (BCC′B′), giao tuyến qua P cũng phải song song với BC.",
        mathFact: "MN // BC (MN = ½ BC = 2) · Mặt phẳng (MNP): √3x + y − √3z = 2√3",
        visiblePoints: ["A", "B", "C", "A_prime", "B_prime", "C_prime", "M", "N", "P"],
        activePoints: ["M", "N", "P"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: true,
        planeOpacity: 0.72,
        sectionProgress: 0.25,
        sectionFillOpacity: 0,
        cameraPos: [1.8, 4.4, 9.8],
        lookAt: [0, 0.05, 0],
      },
      {
        id: "story-3",
        stepNumber: "03",
        tag: "Dựng hình",
        title: "Vạch giao tuyến xác định Q ∈ BB′",
        summary:
          "Từ P ∈ CC′ kẻ tia song song BC trong mặt bên (BCC′B′), cắt cạnh BB′ đúng tại trung điểm Q và nối khép kín bốn đoạn M–N–P–Q.",
        mathFact: "Q = (MNP) ∩ BB′ = (4; 0; 2) · Hai cạnh bên MQ = NP = 2√2",
        visiblePoints: ["A", "B", "C", "A_prime", "B_prime", "C_prime", "M", "N", "P", "Q"],
        activePoints: ["Q"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: true,
        planeOpacity: 0.82,
        sectionProgress: 0.9,
        sectionFillOpacity: 0.2,
        cameraPos: [1.8, 4.4, 9.8],
        lookAt: [0, 0.05, 0],
      },
      {
        id: "story-4",
        stepNumber: "04",
        tag: "Khám phá",
        title: "Kiểm chứng hình thang cân MNPQ",
        summary:
          "Thiết diện MNPQ lộ rõ với hai đáy song song MN = 2, PQ = 4, hai cạnh bên bằng nhau 2√2 và diện tích chính xác 3√7.",
        mathFact: "Chiều cao hình thang h = √7 · Diện tích S(MNPQ) = 3√7",
        visiblePoints: ["A", "B", "C", "A_prime", "B_prime", "C_prime", "M", "N", "P", "Q"],
        activePoints: ["M", "N", "P", "Q"],
        visibleSolidEdges: allEdgeKeys,
        showGuideEdges: false,
        planeOpacity: 0.56,
        sectionProgress: 1,
        sectionFillOpacity: 0.9,
        cameraPos: [1.8, 4.4, 9.8],
        lookAt: [0, 0.05, 0],
      },
    ],
  };
}

export const LANDING_PYRAMID_SAMPLE: LandingSampleSpec = buildPyramidSample();
export const LANDING_CUBE_SAMPLE: LandingSampleSpec = buildCubeSample();
export const LANDING_PRISM_STORY_SPEC: LandingSampleSpec = buildStoryPrismSpec();
export const LANDING_SHOWCASE_SAMPLES: readonly LandingSampleSpec[] = [
  LANDING_PYRAMID_SAMPLE,
  LANDING_CUBE_SAMPLE,
];

export function landingSampleById(id: string): LandingSampleSpec {
  return LANDING_SHOWCASE_SAMPLES.find((s) => s.id === id) ?? LANDING_PYRAMID_SAMPLE;
}

export const AXO_INTENDED_DESTINATION_KEY = "axo_intended_destination_v1";
const INTENDED_DESTINATION_TTL_MS = 30 * 60 * 1000;

export type IntendedDestinationKind = "home" | "workspace" | "library" | "sample" | "admin";

export interface IntendedDestination {
  readonly kind: IntendedDestinationKind;
  readonly sampleId?: string;
  readonly preferActive?: boolean;
  readonly createdAt: number;
}

let memoryIntendedDestination: IntendedDestination | null = null;

function isValidIntendedDestination(raw: unknown): raw is IntendedDestination {
  if (!raw || typeof raw !== "object") return false;
  const candidate = raw as Partial<IntendedDestination>;
  if (
    candidate.kind !== "home" &&
    candidate.kind !== "workspace" &&
    candidate.kind !== "library" &&
    candidate.kind !== "sample" &&
    candidate.kind !== "admin"
  ) {
    return false;
  }
  if (typeof candidate.createdAt !== "number" || !Number.isFinite(candidate.createdAt)) {
    return false;
  }
  if (Date.now() - candidate.createdAt > INTENDED_DESTINATION_TTL_MS) {
    return false;
  }
  return true;
}

export function saveIntendedDestination(dest: Omit<IntendedDestination, "createdAt"> & { createdAt?: number }): IntendedDestination {
  const normalized: IntendedDestination = {
    kind: dest.kind,
    ...(dest.sampleId ? { sampleId: dest.sampleId } : {}),
    ...(dest.preferActive !== undefined ? { preferActive: dest.preferActive } : {}),
    createdAt: typeof dest.createdAt === "number" ? dest.createdAt : Date.now(),
  };
  memoryIntendedDestination = normalized;
  if (typeof window !== "undefined") {
    try {
      window.sessionStorage?.setItem(AXO_INTENDED_DESTINATION_KEY, JSON.stringify(normalized));
    } catch {
      /* ignore sessionStorage restriction */
    }
  }
  return normalized;
}

export function peekIntendedDestination(): IntendedDestination | null {
  if (typeof window !== "undefined") {
    try {
      const raw = window.sessionStorage?.getItem(AXO_INTENDED_DESTINATION_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as unknown;
        if (isValidIntendedDestination(parsed)) {
          memoryIntendedDestination = parsed;
          return parsed;
        }
        window.sessionStorage?.removeItem(AXO_INTENDED_DESTINATION_KEY);
      }
    } catch {
      /* fallback to memory copy */
    }
  }
  if (isValidIntendedDestination(memoryIntendedDestination)) {
    return memoryIntendedDestination;
  }
  memoryIntendedDestination = null;
  return null;
}

export function clearIntendedDestination(): void {
  memoryIntendedDestination = null;
  if (typeof window !== "undefined") {
    try {
      window.sessionStorage?.removeItem(AXO_INTENDED_DESTINATION_KEY);
    } catch {
      /* ignore sessionStorage restriction */
    }
  }
}

export function consumeIntendedDestination(): IntendedDestination | null {
  const dest = peekIntendedDestination();
  clearIntendedDestination();
  return dest;
}

export function resetIntendedDestinationForTests(): void {
  clearIntendedDestination();
}

/**
 * Restore the persisted composer draft into store.problemText after a cold page load
 * whenever entering Workspace Home with an empty in-memory draft.
 */
export function restoreSavedDraftIfEmpty(): void {
  const store = useAppStore.getState();
  if (store.problemText.trim().length > 0) return;
  const saved = historyStore.readDraftText();
  if (saved.trim().length > 0) {
    useAppStore.setState({ problemText: saved });
  }
}

/**
 * Restore the exact task destination after successful login/register without creating
 * a redirect loop or losing draft problemText.
 */
export function applyIntendedDestination(dest: IntendedDestination, user: AuthUser | null): boolean {
  if (!user) return false;
  const store = useAppStore.getState();
  store.setGuestEnteredApp(true);

  if (user.role === "admin" || dest.kind === "admin") {
    if (user.role === "admin") {
      store.setView("admin");
      return true;
    }
  }

  if (dest.kind === "sample" && dest.sampleId) {
    const sample = geometrySampleById(dest.sampleId);
    if (sample) {
      store.loadEnvelope(sample.envelope, sample.id, sample.problemText);
      return true;
    }
    store.openLibrary();
    return true;
  }

  if (dest.kind === "library") {
    store.openLibrary();
    return true;
  }

  if (dest.kind === "workspace" && dest.preferActive && store.active !== null) {
    store.setView("workspace");
    return true;
  }

  store.goHome();
  restoreSavedDraftIfEmpty();
  return true;
}

export interface EnterWorkspaceOptions {
  readonly requireAuth?: boolean;
}

export function enterAxoWorkspaceWithOptions(options?: EnterWorkspaceOptions): void {
  const auth = useAuthStore.getState();
  const store = useAppStore.getState();
  store.setGuestEnteredApp(true);

  if (auth.user !== null) {
    clearIntendedDestination();
    if (auth.user.role === "admin") {
      store.setView("admin");
      return;
    }
    if (store.active !== null) {
      store.setView("workspace");
    } else {
      store.goHome();
      restoreSavedDraftIfEmpty();
    }
    return;
  }

  const target: IntendedDestination =
    store.active !== null
      ? {
          kind: "workspace",
          preferActive: true,
          sampleId: store.activeSampleId ?? undefined,
          createdAt: Date.now(),
        }
      : { kind: "home", createdAt: Date.now() };

  const requiresAuth =
    Boolean(options?.requireAuth) ||
    (auth.resolved && auth.entitlement.canRunSimulation === false);

  if (requiresAuth) {
    saveIntendedDestination(target);
    store.setView("login");
    return;
  }

  if (store.active !== null) {
    store.setView("workspace");
  } else {
    store.goHome();
    restoreSavedDraftIfEmpty();
  }
}

export function enterAxoWorkspace(): void {
  enterAxoWorkspaceWithOptions();
}

export function openLibraryFromLanding(): void {
  const store = useAppStore.getState();
  store.setGuestEnteredApp(true);
  store.openLibrary();
}

export function openSampleInWorkspace(sampleId: string): void {
  const store = useAppStore.getState();
  store.setGuestEnteredApp(true);
  const sample = geometrySampleById(sampleId) ?? GEOMETRY_SAMPLES[0];
  if (sample) {
    store.loadEnvelope(sample.envelope, sample.id, sample.problemText);
  } else {
    store.openLibrary();
  }
}
