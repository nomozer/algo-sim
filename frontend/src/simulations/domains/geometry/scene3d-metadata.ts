/**
 * scene3d-metadata.ts — Helper siêu nhẹ không phụ thuộc `three` cho metadata, ngữ cảnh đề bài,
 * chuẩn hoá tiêu đề khối tròn xoay và đại số hữu tỉ Q^3 trên Scene3D.
 *
 * Tách khỏi `scene3d-semantic-policy.ts` để lịch sử học (`history.ts`), danh mục (`offline-catalog.ts`)
 * và trình nạp mẫu (`sample-loader.ts`) không kéo Three.js (568 KB) vào bundle khởi động.
 */
import {
  derivedSceneParentOf,
  exactSceneOriginOf,
  isSceneWorldTransformed,
  type Exact,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";

export type Frac = readonly [bigint, bigint];
export type FracVec3 = readonly [Frac, Frac, Frac];

function gcdBig(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    const r = x % y;
    x = y;
    y = r;
  }
  return x === 0n ? 1n : x;
}

export function normFrac(num: bigint, den: bigint): Frac {
  if (den === 0n) return [0n, 1n];
  const sign = den < 0n ? -1n : 1n;
  const n = num * sign;
  const d = den * sign;
  if (n === 0n) return [0n, 1n];
  const g = gcdBig(n, d);
  return [n / g, d / g];
}

export function parseExactFrac(s: Exact): Frac {
  const m = /^(-?\d+)(?:\/(\d+))?$/.exec(String(s).trim());
  if (!m) return [0n, 1n];
  return normFrac(BigInt(m[1]), m[2] === undefined ? 1n : BigInt(m[2]));
}

export function fAdd(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[1] + b[0] * a[1], a[1] * b[1]);
}
export function fSub(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[1] - b[0] * a[1], a[1] * b[1]);
}
export function fMul(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[0], a[1] * b[1]);
}
export function fDiv(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[1], a[1] * b[0]);
}
export function fEq(a: Frac, b: Frac): boolean {
  return a[0] === b[0] && a[1] === b[1];
}
export function fIsZero(a: Frac): boolean {
  return a[0] === 0n;
}

export function parseFracVec3(v: ExactVec3): FracVec3 {
  return [parseExactFrac(v[0]), parseExactFrac(v[1]), parseExactFrac(v[2])];
}
export function vSub(a: FracVec3, b: FracVec3): FracVec3 {
  return [fSub(a[0], b[0]), fSub(a[1], b[1]), fSub(a[2], b[2])];
}
export function vAdd(a: FracVec3, b: FracVec3): FracVec3 {
  return [fAdd(a[0], b[0]), fAdd(a[1], b[1]), fAdd(a[2], b[2])];
}
export function vIsZero(v: FracVec3): boolean {
  return fIsZero(v[0]) && fIsZero(v[1]) && fIsZero(v[2]);
}
export function vCross(a: FracVec3, b: FracVec3): FracVec3 {
  return [
    fSub(fMul(a[1], b[2]), fMul(a[2], b[1])),
    fSub(fMul(a[2], b[0]), fMul(a[0], b[2])),
    fSub(fMul(a[0], b[1]), fMul(a[1], b[0])),
  ];
}
export function vScaleFrac(s: Frac, v: FracVec3): FracVec3 {
  return [fMul(s, v[0]), fMul(s, v[1]), fMul(s, v[2])];
}
export function vParallel(a: FracVec3, b: FracVec3): boolean {
  return !vIsZero(a) && !vIsZero(b) && vIsZero(vCross(a, b));
}

export function metricDot(u: FracVec3, v: FracVec3, chartMetric?: Exact[][]): Frac {
  if (!chartMetric || chartMetric.length !== 3) {
    return fAdd(fAdd(fMul(u[0], v[0]), fMul(u[1], v[1])), fMul(u[2], v[2]));
  }
  let acc: Frac = [0n, 1n];
  for (let i = 0; i < 3; i += 1) {
    for (let j = 0; j < 3; j += 1) {
      const gij = parseExactFrac(chartMetric[i]?.[j] ?? "0");
      acc = fAdd(acc, fMul(fMul(u[i], gij), v[j]));
    }
  }
  return acc;
}

export const UNCERTIFIED_SOURCE_TOKENS = new Set([
  "LAYOUT_DERIVED",
  "ILLUSTRATIVE_CONFIGURATION",
  "ILLUSTRATIVE_CHOICE",
  "MODEL_ASSUMPTION",
  "UNVERIFIED",
]);

export function hasUncertifiedObjectSource(obj: SceneObject | undefined): boolean {
  const src = obj?.source as Record<string, unknown> | undefined;
  if (!src) return false;
  if (src.is_given === false) return true;
  if (src.binding === "AUXILIARY" || src.provenance === "DISPLAY_ONLY") return true;
  if (typeof src.provenance === "string" && UNCERTIFIED_SOURCE_TOKENS.has(src.provenance.trim())) return true;
  if (typeof src.assumption === "string" && UNCERTIFIED_SOURCE_TOKENS.has(src.assumption.trim())) return true;
  if (
    typeof src.assumption === "string"
    && src.assumption.trim().length > 0
    && src.assumption.trim() !== "hệ trục do đề chọn"
  ) {
    return true;
  }
  return false;
}

const _problemContextByScene = new WeakMap<object, { title?: string | null; statement?: string | null }>();

export function attachProblemContextToScene(
  scene: Pick<Scene3D, "objects">,
  ctx: { title?: string | null; statement?: string | null },
): void {
  if (!scene || typeof scene !== "object") return;
  if (!ctx.title && !ctx.statement) return;
  _problemContextByScene.set(scene as object, ctx);
}

export function problemContextOfScene(
  scene: Pick<Scene3D, "objects">,
): { title?: string | null; statement?: string | null } | undefined {
  let cur: Pick<Scene3D, "objects"> | undefined = scene;
  const seen = new Set<object>();
  while (cur && !seen.has(cur as object)) {
    seen.add(cur as object);
    const direct = _problemContextByScene.get(cur as object);
    if (direct) return direct;
    const ex = exactSceneOriginOf(cur);
    if (ex !== cur) {
      const exHit = _problemContextByScene.get(ex as object);
      if (exHit) return exHit;
      const exParent = derivedSceneParentOf(ex);
      if (exParent && !seen.has(exParent as object)) {
        cur = exParent;
        continue;
      }
    }
    cur = derivedSceneParentOf(cur);
  }
  return undefined;
}

export interface AxialCurvedOrthogonality {
  isRightCertified: boolean;
  isOblique: boolean;
  isTiltedAxisInSpace: boolean;
  baseNormal: FracVec3 | null;
  isIllustrativeBasePlane?: boolean;
}

/**
 * Kiểm chứng chính xác trên ℚ³ xem khối có trục (`cylinder` / `cone`) là khối tròn xoay trục vuông góc mặt đáy
 * hay khối trụ xiên (`OO′` không vuông góc mặt đáy).
 */
export function inspectAxialCurvedOrthogonality(
  scene: Pick<Scene3D, "objects" | "chart_metric">,
  cs: SceneObject,
): AxialCurvedOrthogonality {
  const exactScene = exactSceneOriginOf(scene);
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  const s = exactById.get(cs.id) ?? cs;
  const sApexOrTop = s.apex_or_top ?? (s as SceneObject & { apex?: ExactVec3 | null }).apex ?? undefined;
  if (
    s.type !== "curved_solid"
    || (s.curved_kind !== "cylinder" && s.curved_kind !== "cone")
    || !s.anchor
    || !sApexOrTop
  ) {
    return { isRightCertified: false, isOblique: false, isTiltedAxisInSpace: false, baseNormal: null };
  }
  const A = parseFracVec3(s.anchor);
  const T = parseFracVec3(sApexOrTop);
  const ax = vSub(T, A);
  if (vIsZero(ax)) {
    return { isRightCertified: false, isOblique: false, isTiltedAxisInSpace: false, baseNormal: null };
  }
  const zAxis: FracVec3 = [
    [0n, 1n],
    [0n, 1n],
    [1n, 1n],
  ];
  const isTiltedAxisInSpace = !vParallel(ax, zAxis);

  let isOblique = false;
  let hasCapCircleNormal = false;
  let hasAuthoritativeCapCircleNormal = false;
  let baseNormal: FracVec3 = ax;
  let sampleRimVec: FracVec3 | null = null;

  for (const c of exactScene.objects) {
    if (c.type !== "circle3" || !c.center || !c.normal) continue;
    const isBaseCap =
      c.surface_role === "BASE_REGION"
      || ((c.depends ?? []).includes(s.id) && (vIsZero(vSub(parseFracVec3(c.center), A)) || vIsZero(vSub(parseFracVec3(c.center), T))));
    if (!isBaseCap) continue;
    const cCenter = parseFracVec3(c.center);
    if (!vIsZero(vSub(cCenter, A)) && !vIsZero(vSub(cCenter, T))) continue;
    const nCap = parseFracVec3(c.normal);
    if (!vIsZero(nCap)) {
      hasCapCircleNormal = true;
      if (c.authoritative !== false && !hasUncertifiedObjectSource(c)) {
        hasAuthoritativeCapCircleNormal = true;
      }
      baseNormal = nCap;
      if (!vParallel(nCap, ax)) {
        isOblique = true;
      }
    }
  }

  const gMetric = isSceneWorldTransformed(exactScene) ? undefined : exactScene.chart_metric;
  if (s.rim_point) {
    const P = parseFracVec3(s.rim_point);
    if (!vIsZero(vSub(P, A)) && !vIsZero(vSub(P, T))) {
      const rBase = vSub(P, A);
      const rTop = vSub(P, T);
      const orthoBase = fIsZero(metricDot(rBase, ax, gMetric));
      const orthoTop = s.curved_kind === "cylinder" && fIsZero(metricDot(rTop, ax, gMetric));
      if (!sampleRimVec && !vIsZero(vCross(rBase, ax))) sampleRimVec = rBase;
      if (!orthoBase && !orthoTop) {
        isOblique = true;
      }
    }
  }

  for (const depId of s.depends ?? []) {
    const pt = exactById.get(depId);
    if (!pt || pt.type !== "point3" || !pt.xyz) continue;
    const P = parseFracVec3(pt.xyz);
    if (vIsZero(vSub(P, A)) || vIsZero(vSub(P, T))) continue;
    const rBase = vSub(P, A);
    const rTop = vSub(P, T);
    const orthoBase = fIsZero(metricDot(rBase, ax, gMetric));
    const orthoTop = s.curved_kind === "cylinder" && fIsZero(metricDot(rTop, ax, gMetric));
    if (!sampleRimVec && !vIsZero(vCross(rBase, ax))) sampleRimVec = rBase;
    if (!orthoBase && !orthoTop) {
      isOblique = true;
    }
  }

  const textTag = `${s.label ?? ""} ${s.role ?? ""}`;
  const declaredObliqueText =
    (/\b(trụ|nón)\s+xiên\b/iu.test(textTag) && !/\btrục\s+xiên\b/iu.test(textTag))
    || /\bkhông\s+vuông\s+góc\b/iu.test(textTag)
    || /không\s*⊥/u.test(textTag);
  const sSrc = s.source as Record<string, unknown> | undefined;
  const declaredIllustrative =
    sSrc?.is_given === false
    || sSrc?.assumption === "ILLUSTRATIVE_CONFIGURATION"
    || sSrc?.assumption === "LAYOUT_DERIVED"
    || sSrc?.provenance === "LAYOUT_DERIVED";

  if (declaredObliqueText || declaredIllustrative) {
    isOblique = true;
  }

  let isIllustrativeBasePlane = false;
  if (isOblique && !hasAuthoritativeCapCircleNormal) {
    isIllustrativeBasePlane = true;
    if (!hasCapCircleNormal && sampleRimVec && !vIsZero(vCross(sampleRimVec, ax))) {
      const perpInPlane = vCross(vCross(sampleRimVec, ax), sampleRimVec);
      if (!vIsZero(perpInPlane) && !vParallel(perpInPlane, ax)) {
        baseNormal = perpInPlane;
      } else {
        const tiltedAroundRim = vAdd(ax, vCross(sampleRimVec, ax));
        if (!vIsZero(tiltedAroundRim) && !vParallel(tiltedAroundRim, ax)) {
          baseNormal = tiltedAroundRim;
        }
      }
    }
  }

  return {
    isRightCertified: !isOblique,
    isOblique,
    isTiltedAxisInSpace,
    baseNormal,
    ...(isIllustrativeBasePlane ? { isIllustrativeBasePlane: true } : {}),
  };
}

export function normalizeCylinderEnvelopeTitle(
  rawTitle: string | null | undefined,
  scene?: Scene3D | null,
): string {
  const title = rawTitle ?? "";
  if (scene && /hình\s+trụ\s+(?:có\s+)?trục\s+xiên|hình\s+trụ\s+xiên/iu.test(title)) {
    const cyl = scene.objects?.find((o) => o.type === "curved_solid" && o.curved_kind === "cylinder");
    if (cyl) {
      const ortho = inspectAxialCurvedOrthogonality(scene, cyl);
      if (ortho.isRightCertified && !ortho.isOblique) {
        return "Hình trụ tròn xoay có trục đặt nghiêng";
      }
    }
  }
  return title;
}
