import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { chiaTamGiac } from "./polygon-triangulate";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  LINE_DISPLAY_HALF_LENGTH,
  PLANE_DISPLAY_SIZE,
  VONG_CHIA,
  clampStep,
  SECTION_STROKE_RATIO,
  daGiacMatPhang,
  dayVaDinhChop,
  diemHuuHan,
  diemChoDuong,
  diemNeoNhanMatPhang,
  doanDuongThang,
  duongKinhCanh,
  geometryHighlightedAt,
  geometryNarrationAt,
  geometryStepCount,
  geometryStepOf,
  huongChanVuongGoc,
  isLastGeometryStep,
  khungMatPhang,
  measurementOnlyPlanes,
  moRongDaGiacMatPhang,
  objectsAt,
  toNumber,
  toVec3,
  type GeometryProgress,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import {
  type InteractionState,
  type TangNhanManh,
  TRANG_THAI_DAU,
  highlightSet,
  isVisible,
  tangNhanManh,
  visualTransformOf,
} from "./interaction-state";
import { diemTaiDinhThietDien, entitiesPresentAt, laDiemPhuDungMatPhang, parentSolidOf } from "./scene3d-subentities";
import {
  buildObliqueCylinderGeometry,
  canonicalEdgesOf,
  classifySolidEdgeVisibility,
  classifyWorldSegmentVisibility,
  createWorldPointOcclusionTest,
  curvedSurfaceTangentTurns,
  resolveObliqueCylinderCapBasis,
  updateCurvedSolidSilhouette,
  dongBoNetDayManHinh,
  taoGiuAmNetDay,
  type CurvedSolidVolumeMeta,
  type EdgeVisibilityAudit,
  type WorldSolidOccluder,
} from "./scene3d-edge-visibility";
export { classifySolidEdgeVisibility, dongBoNetDayManHinh } from "./scene3d-edge-visibility";
import {
  BAN_KINH_NHIN,
  KHOANG_CAM_MAC_DINH,
  banKinhBamDiem,
  banKinhBamPx,
  coDauDinhPx,
  donViMoiPx,
  hangCuThe,
  nguongBamCanh,
} from "./pick-target";
import {
  kyHieu,
  kyHieuDiem,
  locNhanChongNhau,
  uuTienNhan,
  veTrenKhung,
} from "./scene3d-presentation";
import {
  type KhungNhin, type LoaiKhoiTamXoay, type TamXoayOnDinh, type VungAnToanNdc,
  chonHuongNhin, hopBaoCuaDiem, huongLenHienThi, khungNhinQuanhTam,
  khungNhinSuPham, khungNhinVua, tiLeHinhChieu, tinhTamXoayTuKhoi, khoangGanToiThieu, khoangTuaTheoHuong,
} from "./scene3d-camera";
import { MAU_VAI_TRO, PHONG_CACH_SCENE3D, vaiTroKhoi, vaiTroMien, type VaiTroKhoi } from "./scene3d-roles";
import {
  type AnnotationView,
  type LabelRect,
  type LabelToPlace,
  type WitnessShown,
  DEFAULT_ANNOTATION_VIEW,
  annotationAnchor,
  annotationsAt,
  placeAnnotationLabels,
  projectionWitnessesAt,
  witnessesShown,
} from "./scene3d-annotations";
import { namTrenDoanDaVe, nhanChungDoanHopLe } from "./scene3d-witness-gate";
import { auxiliaryHiddenAt, auxiliaryObjects } from "./scene3d-auxiliary";
import { maTranKhung4 } from "./scene3d-chart";
import {
  buildContractReferenceGroup,
  buildVerifiedObjectTooltip,
  cauTrucSuPham,
  classifyCircleSemanticRole,
  classifyCurvedSegmentRole,
  classifySceneObjectSemantics,
  classifySphereSemanticRole,
  compactPlaneAnchorPoints,
  computeBoundedStudiedPlanePolygon,
  computeProjectedCircleOverlapFactor,
  computeStepHighlightTargets,
  isAuxiliaryExplanatoryPolygon,
  isIntersectionLineOrSegment,
  isPolyhedronOppositeTopBasePolygon,
  resolvePlanePerpendicularLineWitness,
  resolveSemanticObjectContract,
  resolveSolidFaceDuplicateCarrierPolygons,
  isPrimarySpatialLine,
  modulateSemanticColor,
  pedagogicalStepList,
  planeSolidEdgeIntersections,
  resolveLineDisplaySpan,
  resolvePlaneSectionVisibility,
  resolveSphereReferenceGreatCirclePolicy,
  resolveStepVisualRoles,
  resolveStudiedPlaneVisualStyle,
  shouldShowSphereReferenceEquator,
  ungroundedFreePointIdsAt,
  type InteractionVisualState,
} from "./scene3d-semantic-policy";

/**
 * Renderer 3D của miền hình học không gian — `display(scene, step)`.
 *
 * Cùng khuôn `network/encap-ui3d.tsx` đã chứng minh: KHÔNG engine 3D thứ hai,
 * KHÔNG tính lại, mọi mesh/camera/vật liệu là **renderer-owned** (ref/closure),
 * KHÔNG BAO GIỜ vào store.
 *
 * ─── ĐIỀU FILE NÀY TUYỆT ĐỐI KHÔNG LÀM ────────────────────────────────────
 *
 * Không tích có hướng, không giao điểm, không suy quan hệ vuông góc/song song.
 * Mọi `point`/`normal`/`direction`/`vertices` đến từ kernel hữu tỉ ở backend.
 *
 * Chỗ dễ nhầm nhất là mặt phẳng: `plane3` VÔ HẠN, không có biên. Renderer
 * **không tính** biên từ ba điểm định nghĩa — nó đặt một `PlaneGeometry` cỡ cố
 * định tại `point` rồi xoay nó theo `normal` bằng `setFromUnitVectors`. Pháp
 * tuyến là dữ liệu đã có; xoay theo nó là dùng thư viện, không phải suy luận.
 *
 * Cùng lẽ ấy với `line3`: kéo dài `direction` ra hai phía một khoảng cố định.
 *
 * ─── VÌ SAO KHÔNG PHẢI GEOGEBRA ───────────────────────────────────────────
 *
 * Không toolbar, không click-tạo-điểm, không kéo thả, không ô nhập lệnh. Hình
 * ở đây **không dựng được bằng chuột** — nó chỉ có thể đến từ một chương trình
 * đã qua thẩm định. Thứ người học điều khiển là **thời gian** (bước dựng) và
 * **góc nhìn**, không phải nội dung hình.
 */

export const GEOMETRY_WEBGL_FALLBACK =
  "Không khởi tạo được chế độ 3D trên thiết bị này (WebGL không khả dụng). " +
  "Các bước dựng vẫn đọc được đầy đủ trong ngăn Học tập.";

let _webglRendererFactoryOverride: (() => THREE.WebGLRenderer | null) | null = null;
let _sharedWebGLRenderer: THREE.WebGLRenderer | null = null;
let _sharedGetContextFn: unknown = null;
let _sharedWebGLRendererInUse = false;

function discardSharedWebGLRenderer(): void {
  if (_sharedWebGLRenderer) {
    try {
      _sharedWebGLRenderer.dispose();
    } catch {
      // Ignore disposal errors on already-lost contexts
    }
    _sharedWebGLRenderer = null;
    _sharedGetContextFn = null;
    _sharedWebGLRendererInUse = false;
  }
}

export function setWebGLRendererFactoryForTest(
  fn: (() => THREE.WebGLRenderer | null) | null,
): void {
  _webglRendererFactoryOverride = fn;
  discardSharedWebGLRenderer();
}

/** Tạo WebGLRenderer an toàn: thất bại → `null`, KHÔNG ném (export để test). */
export function tryCreateWebGLRenderer(): THREE.WebGLRenderer | null {
  try {
    if (_webglRendererFactoryOverride) {
      return _webglRendererFactoryOverride();
    }
    return new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch {
    return null;
  }
}

function acquireSceneWebGLRenderer(): { renderer: THREE.WebGLRenderer; pooled: boolean } | null {
  if (_webglRendererFactoryOverride) {
    const custom = tryCreateWebGLRenderer();
    return custom ? { renderer: custom, pooled: false } : null;
  }
  const curGetContext =
    typeof HTMLCanvasElement !== "undefined" ? HTMLCanvasElement.prototype.getContext : null;
  if (_sharedWebGLRenderer) {
    if (_sharedWebGLRendererInUse) {
      const unpooled = tryCreateWebGLRenderer();
      return unpooled ? { renderer: unpooled, pooled: false } : null;
    }
    const gl = _sharedWebGLRenderer.getContext?.();
    const isLost = Boolean(gl && typeof gl.isContextLost === "function" && gl.isContextLost());
    if (isLost || _sharedGetContextFn !== curGetContext) {
      discardSharedWebGLRenderer();
    } else {
      _sharedWebGLRendererInUse = true;
      try {
        _sharedWebGLRenderer.setScissorTest?.(false);
        _sharedWebGLRenderer.clear?.(true, true, true);
      } catch {
        // Ignore optional clear APIs on lightweight test doubles
      }
      return { renderer: _sharedWebGLRenderer, pooled: true };
    }
  }
  const fresh = tryCreateWebGLRenderer();
  if (!fresh) return null;
  _sharedWebGLRenderer = fresh;
  _sharedGetContextFn = curGetContext;
  _sharedWebGLRendererInUse = true;
  return { renderer: fresh, pooled: true };
}

function releaseSceneWebGLRenderer(
  renderer: THREE.WebGLRenderer,
  pooled: boolean,
  contextLost: boolean,
): void {
  try {
    renderer.renderLists?.dispose?.();
  } catch {
    // Ignore optional renderLists cleanup in lightweight test doubles
  }
  if (!pooled || contextLost) {
    if (_sharedWebGLRenderer === renderer) {
      _sharedWebGLRenderer = null;
      _sharedGetContextFn = null;
      _sharedWebGLRendererInUse = false;
    }
    renderer.dispose();
    return;
  }
  if (_sharedWebGLRenderer === renderer) {
    _sharedWebGLRendererInUse = false;
  }
}

const MAU = { ...PHONG_CACH_SCENE3D.colors, highlight: MAU_VAI_TRO.moi_dung };
const DO_DUC = PHONG_CACH_SCENE3D.opacity;
const NET = PHONG_CACH_SCENE3D.width;

const HE_SO_LAM_DIU = DO_DUC.fade;
/** Đường VÔ HẠN (đường phụ) không được nhấn: lùi xuống, không biến mất (w11). */
const HE_SO_DUONG_PHU = DO_DUC.auxiliary;

function lamDiuVatLieu(m: THREE.Material, k: number): void {
  if ((m as THREE.Material & { colorWrite?: boolean }).colorWrite === false) return;
  m.transparent = true;
  m.opacity *= k;
}

/** Làm dịu cả một vật — trừ cạnh chuẩn đang được tô qua vật khác trong chuỗi. */
export function lamDiu(obj: THREE.Object3D, k = HE_SO_LAM_DIU): void {
  const bo = new Set<THREE.Object3D>();
  const daDiu = new Set<THREE.Material>();
  obj.traverse((x) => {
    if (x.userData?.visualOwnerId && x.userData.highlighted === true) x.traverse((y) => bo.add(y));
  });
  obj.traverse((x) => {
    if (bo.has(x)) return;
    if (x.userData?.visualOwnerId) x.userData.lamDiu = k;
    if (x.userData?.nonCanonicalSegment || x.userData?.nonCanonicalLoop) {
      x.userData.lamDiu = ((x.userData.lamDiu as number | undefined) ?? 1) * k;
    }
    if (x.userData?.sang === true) return;   // khúc tô sáng của đoạn con nằm trên cạnh (W4)
    const m = (x as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
    for (const vl of Array.isArray(m) ? m : m ? [m] : []) {
      if (daDiu.has(vl)) continue;
      lamDiuVatLieu(vl, k);
      daDiu.add(vl);
    }
  });
}

/** A visual owner keeps its few semantic span styles while orbit only changes their geometry. */
function spanMaterial<T extends THREE.Material>(owner: THREE.Object3D, key: string, create: () => T): T {
  const pool: Map<string, THREE.Material> = owner.userData.spanMaterialPool ??= new Map();
  if (!pool.has(key)) {
    const material = create();
    material.userData.spanPooled = true;
    pool.set(key, material);
  }
  return pool.get(key) as T;
}

/** Release both attached resources and inactive pooled styles when the owner is rebuilt or unmounted. */
export function disposeScene3DObject(root: THREE.Object3D): void {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  root.traverse(node => {
    const renderable = node as THREE.Mesh | THREE.Line | THREE.Sprite;
    if ("geometry" in renderable && renderable.geometry) geometries.add(renderable.geometry);
    for (const g of (node.userData.spanGeoPool ?? []) as THREE.BufferGeometry[]) geometries.add(g);
    for (const m of (node.userData.spanMaterialPool as Map<string, THREE.Material> | undefined)?.values() ?? []) materials.add(m);
    for (const m of Array.isArray(renderable.material) ? renderable.material : renderable.material ? [renderable.material] : []) materials.add(m);
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) {
    const texMat = material as THREE.Material & {
      map?: THREE.Texture | null;
      alphaMap?: THREE.Texture | null;
    };
    texMat.map?.dispose?.();
    texMat.alphaMap?.dispose?.();
    material.dispose();
  }
}

/** Toạ độ cảnh → khung THẾ GIỚI qua phép xoay hiển thị (đồng nhất thức khi đáy ngang — trả lại chính các số). */
const DONG_NHAT = new THREE.Quaternion();

function xoay(p: Vec3, q: THREE.Quaternion): Vec3 {
  if (q.equals(DONG_NHAT)) return p;
  const w = new THREE.Vector3(...p).applyQuaternion(q);
  return [w.x, w.y, w.z];
}

/** Phép xoay hiển thị của cảnh (`huongLenHienThi`): đáy chóp nghiêng về nằm ngang; đáy ngang ⇒ đồng nhất thức. */
export function quayHienThi(objects: SceneObject[]): THREE.Quaternion {
  const dc = dayVaDinhChop(objects);
  const len = dc ? huongLenHienThi(dc.day, dc.dinh) : null;
  return len
    ? new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(...len), new THREE.Vector3(0, 0, 1))
    : new THREE.Quaternion();
}

/**
 * TỈ LỆ cao/rộng của HÌNH ở góc nhìn mặc định (mobile-canvas-fit, D5) — cùng điểm, cùng phép xoay hiển thị, cùng
 * hướng `chonHuongNhin` mà khung nhìn vừa (`vuaKhungRef`) dùng; chỉ phụ thuộc cảnh, nên không đổi theo bước, lựa
 * chọn, tách khối hay bảng. `null` khi cảnh không cạnh (khung cũ ôm mặt cầu bao — không có tỉ lệ hình chiếu).
 */
export function tiLeKhungHinh(objects: SceneObject[]): number | null {
  const q = quayHienThi(objects);
  const ct = cauTrucSuPham(objects, q);
  if (ct.canh.length === 0) return null;
  return tiLeHinhChieu(diemHuuHan(objects).map((p) => xoay(p, q)), chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon));
}

function v(o: THREE.Object3D, name: string): THREE.Object3D {
  o.name = name;
  return o;
}

/* ⚠️ `VAT_LIEU_THIET_DIEN = { depthTest: false }` ĐÃ GỠ (2026-09-09).
 *
 * Nó ra đời để đường tròn thiết diện của `p3` không bị mặt cầu nuốt mất — và
 * nó làm được, bằng cách vẽ thiết diện ĐÈ LÊN MỌI THỨ. Cái giá chỉ lộ ra khi
 * hỏi câu tiếp theo: khi mọi phần đều vẽ đè, phần THẤY và phần KHUẤT hiện y
 * hệt nhau, nên hình mất luôn khả năng trả lời *"đoạn này nằm trước hay sau
 * khối"*. Với hình học không gian thì đó không phải chi tiết trang trí — đó
 * là thông tin chính.
 *
 * Nay thiết diện đi qua đúng phép kiểm chiều sâu như mọi đường khác, và phần
 * khuất vẫn đọc được vì nó **vẫn được vẽ**, chỉ ở dạng ngắt quãng và nhạt hơn.
 */

/** Vẽ sau mọi vật khác. Số lớn = vẽ sau, theo quy ước của three.js. */
export const THU_TU_VE_THIET_DIEN = 10;

/**
 * Thứ tự vẽ PHẦN TÔ thiết diện (W16, ASSUMPTION_CERTIFICATE_AMENDMENT §14.4): sau mặt khối
 * và mặt cắt (0), TRƯỚC mọi nét (`THU_TU_DUONG`). Ở 10 (W15) phần tô — không kiểm chiều sâu —
 * phủ hổ phách lên cạnh khối đi qua vùng thiết diện (ảnh cross-section W15: SA, SC nhuộm nâu).
 * `renderOrder` chỉ xếp TRONG một hàng đợi: cạnh khối chuẩn ở hàng đợi trong suốt
 * (`canonicalEdgeMaterial`) nên vẽ đè lên phần tô; nét liền ĐỤC (đoạn phụ, viền đa giác) vẫn
 * chạy trước toàn bộ hàng đợi trong suốt.
 */
export const THU_TU_TO_THIET_DIEN = 7;

/**
 * Độ đục phần TÔ của thiết diện khép kín (W15). Nhánh đa giác chung tô 0.16 — đồng phẳng
 * với miếng mặt cắt tím (0.20) và trước khối xám (0.22) thì vùng thiết diện hoà mất. Cổng
 * ảnh `SECTION_FILL_DISTINGUISHABLE` đo bật/tắt phần tô ở CÙNG khung hình theo ngưỡng
 * đăng ký trước (`ASSUMPTION_CERTIFICATE_AMENDMENT.md` §11); trượt ngưỡng thì chỉnh hằng
 * này, không chỉnh ngưỡng.
 */
export const DO_DUC_TO_THIET_DIEN = DO_DUC.section;

/* ══ NÉT LIỀN / NÉT KHUẤT THEO CAMERA ═══════════════════════════════════
 *
 * ─── VÌ SAO TRƯỚC ĐÂY KHÔNG CÓ CHE KHUẤT NÀO CẢ ────────────────────────
 *
 * **Mọi** khối trong renderer này khai `depthWrite: false` — khối đa diện,
 * khối cong, mặt, miếng mặt phẳng. Không ai ghi chiều sâu thì không gì che
 * được gì: một cạnh nằm sau quả cầu vẫn vẽ y như cạnh nằm trước nó. Đó không
 * phải "hidden-line làm chưa tốt", mà là **chưa từng có hidden-line**.
 *
 * ─── GIẢI PHÁP NHỎ NHẤT PHÙ HỢP RENDERER NÀY ───────────────────────────
 *
 * Hai mảnh, không mảnh nào cần tính hình học:
 *
 *   ① LỚP CHIỀU SÂU RIÊNG. Mỗi khối THẬT (đa diện, khối cong) kèm một bản
 *      sao vô hình chỉ ghi chiều sâu (`colorWrite:false, depthWrite:true`).
 *      Miếng mặt phẳng, nhãn và lưới **không** có bản sao ấy — chúng là vật
 *      minh hoạ, không được che gì.
 *   ② VẼ HAI LƯỢT cho mỗi đường: lượt thứ nhất `depthFunc: LessEqualDepth`
 *      (phần THẤY, nét liền), lượt thứ hai `GreaterDepth` + nét đứt (phần
 *      KHUẤT). GPU quyết định theo TỪNG ĐIỂM ẢNH, nên một cạnh tự chia thành
 *      nhiều đoạn thấy/khuất, và xoay camera thì phân loại đổi theo — không
 *      có cache nào để lỗi thời.
 *
 * Cách này rẻ hơn hẳn depth-pass đọc ngược hay phân đoạn trên CPU, và nó
 * KHÔNG sinh vật mới trong cảnh: bản sao chiều sâu vô hình, không bắt chuột,
 * không vào hộp bao, không vào `final_memory`. Nó là chi tiết TRÌNH BÀY.
 */

/** Thứ tự vẽ: khối tô bóng → lớp chiều sâu → phần tô thiết diện → đường → viền thiết diện. */
const THU_TU_CHIEU_SAU = 5;
const THU_TU_DUONG = 8;

/**
 * ĐỘ LỆCH CHIỀU SÂU của thiết diện — `units` thuần, KHÔNG có `factor`.
 *
 * ⚠️ `polygonOffsetFactor` co giãn theo ĐỘ DỐC của mặt so với hướng nhìn. Với
 * một vành nằm trong mặt cắt dốc — đúng ca `p3` và `p7` ở góc mặc định — độ
 * dốc lớn làm độ lệch bị khuếch đại tới mức CẢ vành thắng phép kiểm chiều sâu,
 * và thiết diện lại vẽ liền toàn bộ y như thời `depthTest: false`. Triệu chứng
 * đo được: `p7` 0 lần đổi nét ở góc mặc định, còn `p3` chỉ hiện nét đứt SAU
 * KHI XOAY — tức một lỗi phụ thuộc góc nhìn, thứ ảnh tĩnh một góc không bắt
 * được.
 *
 * `units` là hằng số theo đơn vị nhỏ nhất của bộ đệm chiều sâu: đủ để vành
 * không nhấp nháy khi nằm ĐÚNG trên mặt khối, và không đủ để nó nhảy ra trước
 * cả một khối.
 */
const LECH_THIET_DIEN = {
  polygonOffset: true, polygonOffsetFactor: 0, polygonOffsetUnits: -1,
} as const;

/** Chu kỳ nét đứt, theo tỉ lệ cảnh — đọc được ở mọi mức thu phóng. */
const NET_DUT_TI_LE = PHONG_CACH_SCENE3D.dash.relative;

/** Bản sao VÔ HÌNH chỉ ghi chiều sâu mặt SAU (ở hàng đợi đục, trước phần tô thiết diện ở thứ tự 7)
 *  để phần tô thiết diện nằm TRONG khối vượt qua phép kiểm `LessEqualDepth` ở chế độ thường mà vẫn bị
 *  khối khác nằm hẳn phía trước che đúng. */
function lopChieuSau(g: THREE.BufferGeometry): THREE.Mesh {
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
    colorWrite: false, depthWrite: true, depthTest: true,
    side: THREE.BackSide,
    transparent: false,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  }));
  m.renderOrder = THU_TU_CHIEU_SAU;
  m.userData.chieuSau = true;      // không bắt chuột, không vào hộp bao
  return m;
}

/** Bản sao VÔ HÌNH ghi chiều sâu mặt TRƯỚC ở thứ tự 7.5 (sau phần tô thiết diện ở 7, trước mọi đường ở 8..10)
 *  để các đường/nét nằm sau mặt trước của khối bị phân loại là khuất bởi phép kiểm chiều sâu GPU. */
function lopChieuSauMatTruoc(g: THREE.BufferGeometry): THREE.Mesh {
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
    colorWrite: false, depthWrite: false, depthTest: true,
    side: THREE.FrontSide,
    transparent: true, opacity: 0,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  }));
  m.renderOrder = THU_TU_TO_THIET_DIEN + 0.5;
  m.userData.chieuSauMatTruoc = true;
  m.userData.voHan = true;
  m.raycast = () => {};
  return m;
}

/** Vỏ khối SGK (`addPolyhedronShell` của HTML tham chiếu): hai lượt KHÔNG đèn — mặt SAU ở `shellBackRatio`×độ đục rồi
 *  mặt TRƯỚC ở độ đục đầy — để màu vỏ không đổi theo hướng đèn. Không ghi chiều sâu: che khuất vẫn do `lopChieuSau`.
 *  Trả mặt trước trước (vật đầu tiên là mặt "chính" mà các chỗ đọc vật liệu tìm), mặt sau thứ hai. */
function voKhoiHaiLuot(g: THREE.BufferGeometry, color: number, opacity: number): [THREE.Mesh, THREE.Mesh] {
  const tao = (side: THREE.Side, doDuc: number, thuTu: number) => {
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
      color, transparent: true, opacity: doDuc, side, forceSinglePass: true, depthWrite: false,
    }));
    m.renderOrder = thuTu;
    m.userData.voKhoi = true;
    m.userData.baseShellOpacity = doDuc;
    return m;
  };
  const sau = tao(THREE.BackSide, opacity * DO_DUC.shellBackRatio, -1);
  sau.userData.voKhoiMatSau = true;
  return [tao(THREE.FrontSide, opacity, 0), sau];
}

/**
 * Vỏ mặt cầu 3D hai lượt (`FrontSide` + `BackSide`) với suy hao quang học vỏ mỏng theo góc tiếp tuyến
 * và sắc độ khối cầu theo không gian camera — giữ đúng màu ngữ nghĩa `matphang.html`, không vẽ viền đen
 * nhân tạo (`sphere_silhouette`), không ghi chiều sâu để không che khuất điểm/đường/thiết diện bên trong.
 */
function taoVoCauBaChieuHaiLuot(
  g: THREE.BufferGeometry,
  color: number,
  opacity: number,
  thuTuTruoc: number,
  thuTuSau: number,
): [THREE.Mesh, THREE.Mesh] {
  const tao = (side: THREE.Side, doDuc: number, thuTu: number, laMatSau: boolean) => {
    const mat = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: doDuc,
      side,
      forceSinglePass: true,
      depthWrite: false,
      depthTest: false,
    });
    mat.customProgramCacheKey = () =>
      laMatSau ? "axo-sphere-airy-back-v2" : "axo-sphere-airy-front-v2";
    mat.onBeforeCompile = (shader) => {
      shader.vertexShader = shader.vertexShader
        .replace(
          "void main() {",
          "varying vec3 vSphereViewNormal;\nvarying vec3 vSphereViewDir;\nvoid main() {",
        )
        .replace(
          "#include <project_vertex>",
          "#include <project_vertex>\n\tvSphereViewNormal = normalize((modelViewMatrix * vec4(normal, 0.0)).xyz);\n\tvSphereViewDir = normalize(-mvPosition.xyz);",
        );
      const fragBlock = laMatSau
        ? `{
\t\tvec3 spN = normalize(vSphereViewNormal) * (gl_FrontFacing ? 1.0 : -1.0);
\t\tvec3 spV = normalize(vSphereViewDir);
\t\tfloat spMu = clamp(dot(spN, spV), 0.0, 1.0);
\t\tfloat spF = 1.0 - spMu;
\t\tdiffuseColor.a = clamp(diffuseColor.a * (0.58 + 0.34 * pow(spF, 2.1)), 0.0, 0.20);
\t}
\t#include <opaque_fragment>`
        : `{
\t\tvec3 spN = normalize(vSphereViewNormal) * (gl_FrontFacing ? 1.0 : -1.0);
\t\tvec3 spV = normalize(vSphereViewDir);
\t\tfloat spMu = clamp(dot(spN, spV), 0.0, 1.0);
\t\tfloat spF = 1.0 - spMu;
\t\tdiffuseColor.a = clamp(diffuseColor.a * (0.68 + 0.44 * pow(spF, 2.1)), 0.0, 0.28);
\t}
\t#include <opaque_fragment>`;
      shader.fragmentShader = shader.fragmentShader
        .replace(
          "void main() {",
          "varying vec3 vSphereViewNormal;\nvarying vec3 vSphereViewDir;\nvoid main() {",
        )
        .replace("#include <opaque_fragment>", fragBlock);
    };
    const m = new THREE.Mesh(g, mat);
    m.renderOrder = thuTu;
    m.userData.voKhoi = true;
    m.userData.baseShellOpacity = doDuc;
    return m;
  };
  const sau = tao(THREE.BackSide, opacity * DO_DUC.shellBackRatio, thuTuSau, true);
  sau.userData.voKhoiMatSau = true;
  sau.raycast = () => {};
  return [tao(THREE.FrontSide, opacity, thuTuTruoc, false), sau];
}

/**
 * Một đường → HAI đường: phần thấy nét liền, phần khuất nét đứt.
 *
 * `polygonOffset` đẩy nhẹ đường về phía camera để đường **nằm trên** mặt khối
 * (vành đáy, biên thiết diện) không nhấp nháy vì sai số chiều sâu.
 */
function duongHaiLuot(
  g: THREE.BufferGeometry, mau: number, chuKy: number, ten: string,
  duongThang = false,
): THREE.Group {
  const nhom = new THREE.Group();
  const chung = {
    color: mau, polygonOffset: true,
    polygonOffsetFactor: -2, polygonOffsetUnits: -2,
  } as const;
  const Lop = duongThang ? THREE.Line : THREE.LineSegments;

  const thay = new Lop(g, new THREE.LineBasicMaterial({
    ...chung, depthFunc: THREE.LessEqualDepth, depthWrite: false,
  }));
  thay.renderOrder = THU_TU_DUONG;
  thay.name = `${ten}:thay`;
  nhom.add(thay);

  const khuat = new Lop(g, new THREE.LineDashedMaterial({
    ...chung, depthFunc: THREE.GreaterDepth, depthWrite: false,
    dashSize: chuKy, gapSize: chuKy * PHONG_CACH_SCENE3D.dash.gapRatio, transparent: true, opacity: DO_DUC.hiddenEdge,
  }));
  (khuat as THREE.Line).computeLineDistances();
  khuat.renderOrder = THU_TU_DUONG;
  khuat.name = `${ten}:khuat`;
  nhom.add(khuat);
  return nhom;
}

/** Highlight chỉ đổi màu/độ dày; lớp vật liệu vẫn do hidden quyết.
 *
 *  ⚠️ CẢ HAI lớp tắt `depthTest` — phân loại CPU (thứ oracle đo) là thẩm quyền.
 *  Đoạn KHUẤT nằm sau lớp chiều sâu của chính khối: GPU kiểm lại là loại nó
 *  lần hai (w09: AB, AD phân loại đúng mà không có điểm ảnh nào). Đoạn THẤY
 *  giữa hai mặt trước thì mất một phần mẫu MSAA và nhạt đi (w10: cạnh SC). */
export function canonicalEdgeMaterial(
  hidden: boolean,
  highlighted: boolean,
  color: number = MAU.canh,
  dashSize = PHONG_CACH_SCENE3D.dash.fallback,
  highlightColor: number = MAU.highlight,
): THREE.LineBasicMaterial | THREE.LineDashedMaterial {
  const common = {
    color: highlighted ? highlightColor : hidden && color === MAU.canh ? MAU.hiddenEdge : color,
    linewidth: highlighted ? NET.selected : NET.edge,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
    // Hàng đợi trong suốt (opacity 1): `renderOrder` xếp nét SAU mặt tô, nếu
    // không mặt tô trong suốt vẽ đè lên nét và cạnh giữa hai mặt nhạt đi.
    transparent: true,
  } as const;
  return hidden
    ? new THREE.LineDashedMaterial({
        ...common, dashSize, gapSize: dashSize * PHONG_CACH_SCENE3D.dash.gapRatio, transparent: true, opacity: DO_DUC.hiddenEdge,
        depthTest: false, depthWrite: false,
      })
    : new THREE.LineBasicMaterial({ ...common, depthTest: false });
}

/** Khúc tô sáng trên một cạnh chuẩn (`edge_span` của đoạn con nằm trên cạnh) — tham số đo từ `edge.a`. */
export interface KhucToSang { t0: number; t1: number; mau: number }

/**
 * regular-square-pyramid-w04 — cắt các đoạn khuất/hiện của MỘT cạnh tại biên khúc tô sáng: phần trong khúc `sang`,
 * phần ngoài giữ như cũ. Không khúc ⇒ không phần nào `sang` (độ sáng cả cạnh do owner quyết như trước).
 */
export function chiaKhucToSang<S extends { t0: number; t1: number }>(
  spans: S[], khuc: { t0: number; t1: number } | undefined,
): (S & { sang: boolean })[] {
  if (!khuc) return spans.map((s) => ({ ...s, sang: false }));
  return spans.flatMap((s) => [
    { ...s, t1: Math.min(s.t1, khuc.t0), sang: false },
    { ...s, t0: Math.max(s.t0, khuc.t0), t1: Math.min(s.t1, khuc.t1), sang: true },
    { ...s, t0: Math.max(s.t0, khuc.t1), sang: false },
  ]).filter((s) => s.t1 > s.t0);
}

/**
 * Cạnh chuẩn được tô QUA vật khác: đoạn/đáy trùng cả cạnh ⇒ `ca` (cả cạnh); đoạn con trên cạnh (`edge_span`, W4) ⇒
 * `khuc` (chỉ khúc của nó). `vat` đã xếp theo độ mạnh — vật sau ghi đè vật trước.
 */
export function toSangCanhChuan(
  vat: SceneObject[], laNoiBat: (id: string) => boolean, mau: (id: string, edgeId?: string) => number,
): { ca: Map<string, number>; khuc: Map<string, KhucToSang> } {
  const ca = new Map<string, number>();
  const khuc = new Map<string, KhucToSang>();
  const canhKhoi = vat.filter((x) => x.type === "solid").flatMap((s) => canonicalEdgesOf(s));
  for (const o of vat.filter((x) => laNoiBat(x.id))) {
    if (o.edge_span) khuc.set(o.edge_span.edge_id, { t0: o.edge_span.t0, t1: o.edge_span.t1, mau: mau(o.id, o.edge_span.edge_id) });
    else if (o.boundary_edge_ids?.length) {
      for (const id of o.boundary_edge_ids) ca.set(id, mau(o.id, id));
    } else if (
      o.type === "segment3"
      && ((o.point_a && o.point_b) || (o.endpoints && o.endpoints.length >= 2))
      && canhKhoi.length > 0
    ) {
      const [ax, ay, az] = toVec3(o.point_a ?? o.endpoints![0]);
      const [bx, by, bz] = toVec3(o.point_b ?? o.endpoints![1]);
      for (const ce of canhKhoi) {
        const ex = ce.b.x - ce.a.x, ey = ce.b.y - ce.a.y, ez = ce.b.z - ce.a.z;
        const lenSq = ex * ex + ey * ey + ez * ez;
        if (lenSq <= 1e-12) continue;
        const ta = ((ax - ce.a.x) * ex + (ay - ce.a.y) * ey + (az - ce.a.z) * ez) / lenSq;
        const tb = ((bx - ce.a.x) * ex + (by - ce.a.y) * ey + (bz - ce.a.z) * ez) / lenSq;
        const da = Math.hypot(ce.a.x + ex * ta - ax, ce.a.y + ey * ta - ay, ce.a.z + ez * ta - az);
        const db = Math.hypot(ce.a.x + ex * tb - bx, ce.a.y + ey * tb - by, ce.a.z + ez * tb - bz);
        if (da <= 1e-4 && db <= 1e-4) {
          const t0 = Math.min(ta, tb);
          const t1 = Math.max(ta, tb);
          if (t0 >= -1e-4 && t1 <= 1 + 1e-4 && t1 - t0 > 1e-4) {
            if (t1 - t0 >= 0.999) {
              ca.set(ce.id, mau(o.id, ce.id));
            } else {
              khuc.set(ce.id, { t0: Math.max(0, t0), t1: Math.min(1, t1), mau: mau(o.id, ce.id) });
            }
          }
        }
      }
    } else if (o.type === "line3" && o.point && o.direction && canhKhoi.length > 0) {
      const [px, py, pz] = toVec3(o.point);
      const [dx, dy, dz] = toVec3(o.direction);
      const dn = Math.hypot(dx, dy, dz);
      if (dn > 1e-9) {
        const ux = dx / dn, uy = dy / dn, uz = dz / dn;
        const lechDuong = (v: THREE.Vector3) => {
          const vx = v.x - px, vy = v.y - py, vz = v.z - pz;
          const t = vx * ux + vy * uy + vz * uz;
          return Math.hypot(vx - t * ux, vy - t * uy, vz - t * uz);
        };
        for (const ce of canhKhoi) {
          if (lechDuong(ce.a) <= 1e-4 && lechDuong(ce.b) <= 1e-4) {
            ca.set(ce.id, mau(o.id, ce.id));
          }
        }
      }
    }
  }
  return { ca, khuc };
}

function createSpanPoolGeometry(): THREE.BufferGeometry {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(6), 3));
  geo.setAttribute("lineDistance", new THREE.Float32BufferAttribute(new Float32Array(2), 1));
  return geo;
}

function preallocateSpanGeoPool(owner: THREE.Object3D, count: number): THREE.BufferGeometry[] {
  const pool = (owner.userData.spanGeoPool as THREE.BufferGeometry[] | undefined) ?? [];
  while (pool.length < count) {
    pool.push(createSpanPoolGeometry());
  }
  owner.userData.spanGeoPool = pool;
  return pool;
}

function acquireSpanGeometry(
  owner: THREE.Object3D,
  slot: number,
  a: THREE.Vector3,
  b: THREE.Vector3,
  startDist = 0,
): THREE.BufferGeometry {
  const pool = preallocateSpanGeoPool(owner, slot + 1);
  const geo = pool[slot];
  const pos = geo.getAttribute("position") as THREE.BufferAttribute;
  const pa = pos.array as Float32Array;
  pa[0] = a.x; pa[1] = a.y; pa[2] = a.z;
  pa[3] = b.x; pa[4] = b.y; pa[5] = b.z;
  pos.needsUpdate = true;
  const dist = geo.getAttribute("lineDistance") as THREE.BufferAttribute;
  const da = dist.array as Float32Array;
  const segLen = Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z);
  da[0] = startDist;
  da[1] = startDist + segLen;
  dist.needsUpdate = true;
  geo.boundingSphere = null;
  geo.boundingBox = null;
  return geo;
}

const SHARED_WARM_SPAN_MAT = new THREE.LineDashedMaterial({
  colorWrite: false,
  depthWrite: false,
  depthTest: false,
  transparent: true,
  opacity: 0,
  dashSize: 0.1,
  gapSize: 0.1,
});

function warmSpanPools(
  goc: THREE.Object3D,
  scene3: THREE.Scene,
): THREE.Group | null {
  if (goc.userData.spanPoolsWarmed === true) return null;
  goc.userData.spanPoolsWarmed = true;
  if (!scene3.userData.warmHoldGroup) {
    const hold = new THREE.Group();
    const holdGeo = createSpanPoolGeometry();
    const solidHold = new THREE.Line(
      holdGeo,
      new THREE.LineBasicMaterial({ colorWrite: false, depthWrite: false, depthTest: false, transparent: true, opacity: 0 }),
    );
    const dashedHold = new THREE.Line(
      holdGeo,
      new THREE.LineDashedMaterial({
        colorWrite: false, depthWrite: false, depthTest: false, transparent: true, opacity: 0, dashSize: 0.1, gapSize: 0.1,
      }),
    );
    solidHold.frustumCulled = false;
    dashedHold.frustumCulled = false;
    solidHold.raycast = () => {};
    dashedHold.raycast = () => {};
    hold.add(solidHold, dashedHold, ...taoGiuAmNetDay());
    scene3.add(hold);
    scene3.userData.warmHoldGroup = hold;
  }
  const warmGroup = new THREE.Group();
  goc.traverse((node) => {
    const pool = node.userData?.spanGeoPool as THREE.BufferGeometry[] | undefined;
    if (!pool) return;
    for (const geo of pool) {
      const l = new THREE.Line(geo, SHARED_WARM_SPAN_MAT);
      l.frustumCulled = false;
      l.raycast = () => {};
      warmGroup.add(l);
    }
  });
  return warmGroup.children.length > 0 ? warmGroup : null;
}

function rebuildCanonicalEdgeOwner(
  owner: THREE.Group,
  edge: ReturnType<typeof canonicalEdgesOf>[number],
  spans: EdgeVisibilityAudit["edge_spans"],
): void {
  for (const child of [...owner.children]) {
    owner.remove(child);
    if (!child.userData?.fromSpanPool) (child as THREE.Line).geometry?.dispose();
    const material = (child as THREE.Line).material as THREE.Material | undefined;
    if (!material?.userData.spanPooled) material?.dispose();
  }
  const khuc = owner.userData.khuc as KhucToSang | undefined;
  const edgeLen = Math.hypot(edge.b.x - edge.a.x, edge.b.y - edge.a.y, edge.b.z - edge.a.z);
  const ownSpans = chiaKhucToSang(spans.filter((span) => span.edge_id === edge.id), khuc);
  ownSpans.forEach((span, idx) => {
    const a = edge.a.clone().lerp(edge.b, span.t0);
    const b = edge.a.clone().lerp(edge.b, span.t1);
    const startDist = edgeLen * span.t0;
    const geometry = acquireSpanGeometry(owner, idx, a, b, startDist);
    const isHidden = span.visibility === "HIDDEN";
    const highlighted = owner.userData.highlighted === true || span.sang;
    const highlightColor = span.sang ? khuc!.mau : owner.userData.highlightColor as number | undefined;
    const fade = span.sang ? 1 : (owner.userData.lamDiu as number | undefined) ?? 1;
    const material = spanMaterial(owner,
      [isHidden, highlighted, owner.userData.edgeColor, owner.userData.dashSize, highlightColor, fade].join("|"), () => {
        const m = canonicalEdgeMaterial(isHidden, highlighted, owner.userData.edgeColor as number,
          owner.userData.dashSize as number, highlightColor);
        if (fade !== 1) lamDiuVatLieu(m, fade);
        return m;
      });
    // Làm dịu (ngoài chuỗi nhân quả) phải sống qua lần dựng lại khi xoay — trừ KHÚC đang tô sáng (W4: chọn SM thì
    // khối ngoài chuỗi bị làm dịu, nhưng khúc S–M của nó là chính vật đang chọn).
    const line = new THREE.Line(geometry, material);
    line.userData.fromSpanPool = true;
    line.userData.hidden = isHidden;
    line.userData.dashDistanceOffset = startDist;
    line.userData.sang = span.sang;
    line.userData.logicalEdgeId = edge.id;
    if (owner.userData.interactionState) {
      line.userData.interactionState = owner.userData.interactionState;
    }
    line.renderOrder = THU_TU_DUONG;
    owner.add(line);
  });
}

interface NonCanonicalSegmentMeta {
  prefix: string;
  objectId: string;
  a: THREE.Vector3;
  b: THREE.Vector3;
  color: number;
  dashSize: number;
  highlighted: boolean;
  interactionState?: "neutral" | "hover" | "selected";
  yieldColinear: boolean;
  renderOrder: number;
  noRaycast?: boolean;
  forceDashed?: boolean;
}

interface NonCanonicalLoopMeta {
  objectId: string;
  pts: THREE.Vector3[];
  closed: boolean;
  color: number;
  dashSize: number;
  highlighted: boolean;
  interactionState?: "neutral" | "hover" | "selected";
  renderOrder: number;
  yieldColinear?: boolean;
  isPlaneBorder?: boolean;
  continuousPlaneBorder?: boolean;
}

interface CurvedRimLoopMeta {
  objectId: string;
  rimRole?: "section" | "base" | "reference" | "inscribed" | "circumscribed";
  highlighted?: boolean;
  interactionState?: "neutral" | "hover" | "selected";
  visibilityMode?: "all_dashed";
  selfOccludingSphere?: CurvedSolidVolumeMeta;
  trong: THREE.Vector3[];
  ngoai: THREE.Vector3[];
  midpoints: THREE.Vector3[];
  sample: (turn: number) => { inner: THREE.Vector3; outer: THREE.Vector3 };
  spanCapacity?: number;
  thayMesh: THREE.Mesh;
  khuatMesh: THREE.Mesh;
  thayNet: THREE.LineSegments;
  khuatNet: THREE.LineSegments;
}

/**
 * Khối cong vẫn hiện (đường bao theo camera) nhưng KHÔNG che vật khác — khối phụ cùng khung với khối chính. Trước đây
 * siêu dữ liệu bị xoá hẳn, nên đường bao cầu không bao giờ được đặt và một vòng đơn vị hiện ở gốc toạ độ.
 */
export function datKhoiCongKhongChe(obj: THREE.Object3D): void {
  if (!obj.userData.curvedSolidVolume) return;
  const meta = obj.userData.curvedSolidVolume as CurvedSolidVolumeMeta;
  obj.userData.curvedSilhouetteVolume = meta;
  delete obj.userData.curvedSolidVolume;
  obj.traverse((n) => {
    const rim = n.userData?.curvedRimLoop as CurvedRimLoopMeta | undefined;
    if (rim && n.name.startsWith("sphere_reference:") && rim.visibilityMode !== "all_dashed") {
      rim.selfOccludingSphere = meta;
    }
  });
}

/**
 * Một biên logic một chủ hình (OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT): khi cảnh đã có đường tròn backend trùng tâm,
 * bán kính và trục với một vành đáy mà khối cong tự vẽ (`objects`: do nơi gọi lọc — vật người dùng thấy, cùng phép dời), bỏ vành của khối — đường tròn backend hiện theo bước của chính
 * nó (#31) và một thiết diện đang chọn không bị vành xanh đậm của khối đè lên. So sánh số của dữ kiện backend, không suy.
 */
export function boVanhDayTrung(obj: THREE.Object3D, khoi: SceneObject, objects: readonly SceneObject[]): void {
  const tron = objects.filter((x) => x.id !== khoi.id && x.type === "circle3" && x.center && x.normal && x.radius_sq);
  if (!tron.length) return;
  const gan = (a: number, b: number) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));
  const vanh: THREE.Object3D[] = [];
  obj.traverse((n) => { if (n.userData.vanhDayCua) vanh.push(n); });
  for (const n of vanh) {
    type Ba = [number, number, number];
    const { center: c, axis, radius_sq } = n.userData.vanhDayCua as { center: Ba; axis: Ba; radius_sq: string };
    const d = new THREE.Vector3(...axis).normalize().toArray();
    const cungTruc = (e: number[]) => e.every((v, i) => gan(v, d[i])) || e.every((v, i) => gan(v, -d[i]));
    const trung = tron.some((x) => gan(toNumber(x.radius_sq!), toNumber(radius_sq))
      && toVec3(x.center!).every((v, i) => gan(v, c[i]))
      && cungTruc(new THREE.Vector3(...toVec3(x.normal!)).normalize().toArray()));
    if (trung) { n.removeFromParent(); disposeScene3DObject(n); }
  }
}

/**
 * Nét 1px dọc mép ngoài vành, dùng CHUNG vật liệu với dải. Dải nằm trong mặt phẳng miền nên khi nhìn xiên nó co dưới
 * một điểm ảnh và cung khuất biến mất (đo: elip p6, góc «quarter», 390px); nét như viền đa giác thì không co.
 */
function themNetVanh(nhom: THREE.Group, thay: THREE.Mesh, khuat: THREE.Mesh): Pick<CurvedRimLoopMeta, "thayNet" | "khuatNet"> {
  const net = (dai: THREE.Mesh) => {
    const l = new THREE.LineSegments(new THREE.BufferGeometry(), dai.material as THREE.Material);
    l.renderOrder = dai.renderOrder;
    l.raycast = () => {};
    nhom.add(l);
    return l;
  };
  return { thayNet: net(thay), khuatNet: net(khuat) };
}

function capNhatHinhHocVanhCong(
  rim: CurvedRimLoopMeta,
  spans: readonly { t0: number; t1: number; hidden: boolean }[],
  useCpuDepthOverride: boolean,
): void {
  const segCount = rim.midpoints.length;
  const dinhThay: number[] = [];
  const dinhDut: number[] = [];
  const netThay: number[] = [];
  const netDut: number[] = [];
  const dashCount = 44;
  const cycleLen = segCount / dashCount;
  const duty = 0.58;
  const pushArcChord = (u0: number, u1: number, dinhArr: number[], netArr: number[]) => {
    if (u1 - u0 <= 1e-6) return;
    const start = rim.sample(u0 / segCount);
    const end = rim.sample(u1 / segCount);
    const [a0, b0, a1, b1] = [start.inner, start.outer, end.inner, end.outer];
    dinhArr.push(
      a0.x, a0.y, a0.z, b0.x, b0.y, b0.z, a1.x, a1.y, a1.z,
      b0.x, b0.y, b0.z, b1.x, b1.y, b1.z, a1.x, a1.y, a1.z,
    );
    netArr.push(b0.x, b0.y, b0.z, b1.x, b1.y, b1.z);
  };
  const pushDashedArc = (t0: number, t1: number) => {
    const kMin = Math.floor(t0 / cycleLen);
    const kMax = Math.ceil(t1 / cycleLen);
    for (let k = kMin; k < kMax; k += 1) {
      const d0 = Math.max(t0, k * cycleLen);
      const d1 = Math.min(t1, (k + duty) * cycleLen);
      if (d1 - d0 <= 1e-5) continue;
      if (d1 - d0 > 0.9) {
        const dMid = (d0 + d1) * 0.5;
        pushArcChord(d0, dMid, dinhDut, netDut);
        pushArcChord(dMid, d1, dinhDut, netDut);
      } else {
        pushArcChord(d0, d1, dinhDut, netDut);
      }
    }
  };
  const pieces = spans.length ? spans : Array.from({ length: segCount }, (_, i) => ({ t0: i, t1: i + 1, hidden: false }));
  for (const span of pieces) {
    if (!useCpuDepthOverride) {
      pushArcChord(span.t0, span.t1, dinhThay, netThay);
      pushDashedArc(span.t0, span.t1);
    } else if (!span.hidden) {
      pushArcChord(span.t0, span.t1, dinhThay, netThay);
    } else {
      pushDashedArc(span.t0, span.t1);
    }
  }
  // Buffer cỡ TỐI ĐA (mọi đoạn) cấp một lần cho mỗi mesh, rồi ghi tại chỗ + `setDrawRange` — dựng
  // `BufferGeometry` mới mỗi lần đổi góc nhìn là một buffer GPU mới mỗi khung khi xoay (cổng
  // `scene3d-orbit-gate`, `capPhat = 0`, ca p6/p7 thiết diện elip).
  const setPos = (mesh: THREE.Mesh | THREE.LineSegments, arr: number[]) => {
    // Eight probe intervals/chord plus analytic tangent seeds; reserve independently of camera orientation.
    const cap = (rim.spanCapacity ?? segCount * 16) * (mesh instanceof THREE.LineSegments ? 6 : 18);
    let attr = mesh.geometry?.getAttribute?.("position") as THREE.BufferAttribute | undefined;
    if (!attr || attr.array.length !== cap) {
      const g = new THREE.BufferGeometry();
      attr = new THREE.BufferAttribute(new Float32Array(cap), 3);
      attr.setUsage(THREE.DynamicDrawUsage);
      g.setAttribute("position", attr);
      mesh.geometry?.dispose?.();
      mesh.geometry = g;
    }
    (attr.array as Float32Array).set(arr);
    attr.needsUpdate = true;
    mesh.geometry.setDrawRange(0, arr.length / 3);
    mesh.geometry.computeBoundingSphere();
    const mat = mesh.material as THREE.MeshBasicMaterial;
    mat.depthTest = !useCpuDepthOverride;
  };
  setPos(rim.thayMesh, dinhThay);
  setPos(rim.khuatMesh, dinhDut);
  setPos(rim.thayNet, netThay);
  setPos(rim.khuatNet, netDut);
}

function updateNonCanonicalVisibility(
  targetRoot: THREE.Object3D,
  camera: THREE.Camera,
  occluders: readonly WorldSolidOccluder[],
  worldSignature: string,
  curvedVolumes: readonly CurvedSolidVolumeMeta[],
): void {
  const worldCam = camera.position.clone();
  const prioritySegments: { id: string; a: THREE.Vector3; b: THREE.Vector3 }[] = [];
  targetRoot.traverse((node) => {
    const seg = node.userData?.nonCanonicalSegment as NonCanonicalSegmentMeta | undefined;
    if (seg && (node as THREE.Group).isGroup) {
      node.updateWorldMatrix(true, false);
      prioritySegments.push({
        id: seg.objectId,
        a: seg.a.clone().applyMatrix4(node.matrixWorld),
        b: seg.b.clone().applyMatrix4(node.matrixWorld),
      });
      return;
    }
    const loop = node.userData?.nonCanonicalLoop as NonCanonicalLoopMeta | undefined;
    if (loop && !loop.yieldColinear) {
      node.updateWorldMatrix(true, false);
      const edgeCount = loop.closed ? loop.pts.length : Math.max(0, loop.pts.length - 1);
      for (let i = 0; i < edgeCount; i += 1) {
        prioritySegments.push({
          id: `${loop.objectId}::border:${i}`,
          a: loop.pts[i].clone().applyMatrix4(node.matrixWorld),
          b: loop.pts[(i + 1) % loop.pts.length].clone().applyMatrix4(node.matrixWorld),
        });
      }
    }
  });
  targetRoot.traverse((node) => {
    const seg = node.userData?.nonCanonicalSegment as NonCanonicalSegmentMeta | undefined;
    if (seg && (node as THREE.Group).isGroup) {
      if (node.userData.nonCanonicalSig === worldSignature) return;
      if (occluders.length === 0 && curvedVolumes.length === 0) {
        if (seg.forceDashed) {
          for (const child of node.children) {
            if (child.name.endsWith(":khuat")) {
              child.visible = true;
              child.userData.hidden = false;
              child.userData.forceDashed = true;
            } else if (child.name.endsWith(":thay")) {
              child.visible = false;
            }
          }
          node.userData.nonCanonicalSig = worldSignature;
          return;
        }
        for (const child of node.children) {
          if (child.userData?.hidden === true || child.name.endsWith(":khuat")) child.visible = false;
          else if (child.name.endsWith(":thay")) child.visible = true;
        }
        node.userData.nonCanonicalSig = worldSignature;
        return;
      }
      node.updateWorldMatrix(true, false);
      const worldA = seg.a.clone().applyMatrix4(node.matrixWorld);
      const worldB = seg.b.clone().applyMatrix4(node.matrixWorld);
      const res = classifyWorldSegmentVisibility(worldA, worldB, worldCam, occluders, {
        edge_id: seg.objectId,
        curved_occluders: curvedVolumes,
        yield_colinear_canonical_edges: seg.yieldColinear,
      });
      const spanSig = `${res.spans.map((s) => `${s.visibility}:${s.t0}:${s.t1}`).join("|")}|${res.colinear_canonical_edge_ids.join(",")}`;
      // Cạnh chuẩn mà đoạn này nhường nét (trùng cạnh khối): độ thấy của đoạn khi ấy nằm ở các khúc của cạnh chuẩn.
      node.userData.colinearCanonicalIds = res.colinear_canonical_edge_ids;
      if (node.userData.nonCanonicalSpanSig === spanSig) {
        node.userData.nonCanonicalSig = worldSignature;
        return;
      }
      for (const child of [...node.children]) {
        if (child.userData?.nonCanonicalSpanLine
            || child.name.endsWith(":thay")
            || child.name.endsWith(":khuat")) {
          node.remove(child);
          if (!child.userData?.fromSpanPool) (child as THREE.Line).geometry?.dispose();
          const material = (child as THREE.Line).material as THREE.Material | undefined;
          if (!material?.userData.spanPooled) material?.dispose();
        }
      }
      const segLen = Math.hypot(seg.b.x - seg.a.x, seg.b.y - seg.a.y, seg.b.z - seg.a.z);
      res.spans.forEach((span, idx) => {
        const p0 = seg.a.clone().lerp(seg.b, span.t0);
        const p1 = seg.a.clone().lerp(seg.b, span.t1);
        const startDist = segLen * span.t0;
        const isHidden = span.visibility === "HIDDEN";
        const useDashed = Boolean(seg.forceDashed) || isHidden;
        const mat = spanMaterial(node, [useDashed, seg.highlighted, seg.color, seg.dashSize, node.userData.lamDiu].join("|"), () => {
          const m = canonicalEdgeMaterial(useDashed, seg.highlighted, seg.color, seg.dashSize, seg.color);
          if (node.userData.lamDiu) lamDiuVatLieu(m, node.userData.lamDiu as number);
          return m;
        });
        const line = new THREE.Line(acquireSpanGeometry(node, idx, p0, p1, startDist), mat);
        line.name = idx === 0 && !isHidden ? `${seg.prefix}:thay` : `${seg.prefix}:span:${idx}`;
        line.userData.fromSpanPool = true;
        line.userData.nonCanonicalSpanLine = true;
        if (seg.forceDashed) line.userData.forceDashed = true;
        line.userData.hidden = isHidden;
        line.userData.dashDistanceOffset = startDist;
        if (node.userData.semanticLineRole) {
          line.userData.semanticLineRole = node.userData.semanticLineRole;
        }
        if (seg.interactionState) {
          line.userData.interactionState = seg.interactionState;
        }
        line.renderOrder = isHidden ? Math.min(seg.renderOrder, THU_TU_DUONG - 0.5) : seg.renderOrder;
        if (seg.noRaycast) line.raycast = () => {};
        node.add(line);
      });
      if (seg.yieldColinear && res.colinear_canonical_edge_ids.length > 0 && !seg.noRaycast) {
        const proxy = new THREE.Line(
          acquireSpanGeometry(node, res.spans.length, seg.a, seg.b),
          spanMaterial(node, "proxy", () => new THREE.LineBasicMaterial({
            colorWrite: false, depthWrite: false, transparent: true, opacity: 0, linewidth: NET.pick,
          })),
        );
        proxy.name = `${seg.prefix}:proxy`;
        proxy.userData.fromSpanPool = true;
        proxy.userData.nonCanonicalSpanLine = true;
        node.add(proxy);
      }
      node.userData.nonCanonicalSpanSig = spanSig;
      node.userData.nonCanonicalSig = worldSignature;
      return;
    }

    const loop = node.userData?.nonCanonicalLoop as NonCanonicalLoopMeta | undefined;
    if (loop) {
      if (node.userData.nonCanonicalSig === worldSignature) return;
      if (occluders.length === 0 && curvedVolumes.length === 0 && !(loop.yieldColinear && prioritySegments.length > 0)) {
        for (const child of node.children) {
          if (child.userData?.hidden === true || child.name.endsWith(":khuat")) child.visible = false;
          else if (child.name.endsWith(":thay")) child.visible = true;
        }
        node.userData.nonCanonicalSig = worldSignature;
        return;
      }
      node.updateWorldMatrix(true, false);
      const edgeCount = loop.closed ? loop.pts.length : Math.max(0, loop.pts.length - 1);
      const edgeResults = [];
      for (let i = 0; i < edgeCount; i += 1) {
        const localA = loop.pts[i];
        const localB = loop.pts[(i + 1) % loop.pts.length];
        const worldA = localA.clone().applyMatrix4(node.matrixWorld);
        const worldB = localB.clone().applyMatrix4(node.matrixWorld);
        const res = classifyWorldSegmentVisibility(worldA, worldB, worldCam, occluders, {
          edge_id: `${loop.objectId}::border:${i}`,
          curved_occluders: curvedVolumes,
          yield_colinear_canonical_edges: Boolean(loop.yieldColinear),
          priority_segments: loop.yieldColinear ? prioritySegments : undefined,
        });
        edgeResults.push({ i, localA, localB, res });
      }
      const spanSig = edgeResults
        .map(({ i, res }) => `${i}:${res.spans.map((s) => `${s.visibility}:${s.t0}:${s.t1}`).join(",")}:${res.colinear_canonical_edge_ids.join(",")}`)
        .join("|");
      if (node.userData.nonCanonicalSpanSig === spanSig) {
        node.userData.nonCanonicalSig = worldSignature;
        return;
      }
      for (const child of [...node.children]) {
        if (child.userData?.nonCanonicalBorderLine) {
          node.remove(child);
          if (!child.userData?.fromSpanPool) (child as THREE.Line).geometry?.dispose();
          const material = (child as THREE.Line).material as THREE.Material | undefined;
          if (!material?.userData.spanPooled) material?.dispose();
        }
      }
      let slotIdx = 0;
      let perimeterOffset = 0;
      for (const { i, localA, localB, res } of edgeResults) {
        const edgeLen = Math.hypot(localB.x - localA.x, localB.y - localA.y, localB.z - localA.z);
        res.spans.forEach((span, idx) => {
          const p0 = localA.clone().lerp(localB, span.t0);
          const p1 = localA.clone().lerp(localB, span.t1);
          const startDist = perimeterOffset + edgeLen * span.t0;
          // Viền mặt phẳng đơn lẻ theo phân loại thấy/khuất; khi nhiều mặt phẳng cùng tồn tại thì giữ nét liền dịu để không nhầm với cạnh khuất.
          const isHidden = span.visibility === "HIDDEN";
          const continuousBorder = Boolean(loop.isPlaneBorder && loop.continuousPlaneBorder);
          const mat = spanMaterial(node,
            [isHidden, loop.highlighted, loop.color, loop.dashSize, loop.isPlaneBorder, continuousBorder, node.userData.lamDiu].join("|"), () => {
              const m = continuousBorder && isHidden
                ? new THREE.LineBasicMaterial({
                    color: loop.color,
                    linewidth: NET.plane,
                    polygonOffset: true,
                    polygonOffsetFactor: -2,
                    polygonOffsetUnits: -2,
                    transparent: true,
                    opacity: DO_DUC.hiddenPlaneEdge * 0.85,
                    depthTest: false,
                    depthWrite: false,
                  })
                : canonicalEdgeMaterial(isHidden, loop.highlighted, loop.color, loop.dashSize, loop.color);
              if (loop.isPlaneBorder) {
                m.linewidth = NET.plane;
                const doDuc = loop.highlighted
                  ? DO_DUC.selectedPlaneEdge
                  : loop.interactionState === "hover"
                    ? 0.90
                    : DO_DUC.planeEdge;
                m.opacity = isHidden
                  ? (continuousBorder ? DO_DUC.hiddenPlaneEdge * 0.85 : DO_DUC.hiddenPlaneEdge)
                  : doDuc;
              } else if (!isHidden) {
                m.linewidth = loop.highlighted ? NET.selected : NET.border;
              }
              if (node.userData.lamDiu) lamDiuVatLieu(m, node.userData.lamDiu as number);
              return m;
            });
          const line = new THREE.Line(acquireSpanGeometry(node, slotIdx++, p0, p1, startDist), mat);
          line.name = loop.isPlaneBorder ? `plane_border:${loop.objectId}:${i}:${idx}` : `section_border:${loop.objectId}:${i}:${idx}`;
          line.userData.fromSpanPool = true;
          line.userData.nonCanonicalBorderLine = true;
          line.userData.hidden = isHidden;
          line.userData.dashDistanceOffset = startDist;
          if (continuousBorder) {
            line.userData.continuousPlaneBorder = true;
          }
          if (node.userData.semanticLineRole) {
            line.userData.semanticLineRole = node.userData.semanticLineRole;
          }
          if (loop.interactionState) {
            line.userData.interactionState = loop.interactionState;
          }
          line.renderOrder = isHidden ? Math.min(loop.renderOrder, THU_TU_DUONG - 0.5) : loop.renderOrder;
          node.add(line);
        });
        perimeterOffset += edgeLen;
      }
      node.userData.nonCanonicalSpanSig = spanSig;
      node.userData.nonCanonicalSig = worldSignature;
    }
  });
}

export function updateCanonicalEdgeVisibility(
  root: THREE.Object3D,
  camera: THREE.Camera,
  renderSignature = "",
): EdgeVisibilityAudit & {
  highlighted_render_owner_ids: string[];
  recomputed_solid_count: number;
  recomputation_ms: number;
  edge_count: number;
  span_count: number;
} {
  const started = globalThis.performance?.now?.() ?? Date.now();
  const status = new Map<string, Set<"visible" | "hidden">>();
  const counts = new Map<string, number>();
  const highlighted = new Set<string>();
  const allSpans: EdgeVisibilityAudit["edge_spans"] = [];
  const occluders: WorldSolidOccluder[] = [];
  let triangleCount = 0;
  let sampleCount = 0;
  let recomputedSolidCount = 0;
  const khoa = (v: number) => (Math.abs(v) < 1e-12 ? 0 : Number(v.toPrecision(10)));
  const solidCandidates: { candidate: THREE.Object3D; source: SceneObject }[] = [];
  const curvedVolumes: CurvedSolidVolumeMeta[] = [];
  root.traverse((candidate) => {
    const source = candidate.userData?.solidSceneObject as SceneObject | undefined;
    if (source) {
      candidate.updateWorldMatrix(true, false);
      solidCandidates.push({ candidate, source });
      occluders.push({ solid: source, matrixWorld: candidate.matrixWorld.clone() });
      return;
    }
    const curvedMeta = candidate.userData?.curvedSolidVolume as CurvedSolidVolumeMeta | undefined;
    if (!curvedMeta && !candidate.userData?.curvedSilhouetteVolume) return;
    candidate.updateWorldMatrix(true, false);
    if (curvedMeta) curvedVolumes.push({ ...curvedMeta, worldToLocal: candidate.matrixWorld.clone().invert() });
    updateCurvedSolidSilhouette(candidate, camera);
  });
  for (const { candidate, source } of solidCandidates) {
    const localCamera = candidate.worldToLocal(camera.position.clone());
    const signature = [
      ...[
        localCamera.x, localCamera.y, localCamera.z,
        ...camera.matrixWorldInverse.elements,
        ...camera.projectionMatrix.elements,
      ].map(khoa),
      renderSignature,
    ].join("|");
    let audit = candidate.userData.edgeVisibilityAudit as EdgeVisibilityAudit | undefined;
    if (!audit || candidate.userData.edgeVisibilitySignature !== signature) {
      const viewport = /^(\d+)x(\d+)@(\d+(?:\.\d+)?)$/.exec(renderSignature);
      const distinctSolids = solidCandidates.filter(
        (item, idx, arr) => arr.findIndex((x) => x.source.id === item.source.id) === idx,
      );
      const invMat = candidate.matrixWorld.clone().invert();
      const toFrac = (n: number) => {
        const scaled = Math.round(n * 1000000);
        return scaled % 1000000 === 0 ? String(scaled / 1000000) : `${scaled}/1000000`;
      };
      const localOccluders: SceneObject[] = distinctSolids.length > 1
        ? distinctSolids.map(({ candidate: otherNode, source: otherSolid }) => {
            if (otherSolid.id === source.id) return source;
            const relMat = invMat.clone().multiply(otherNode.matrixWorld);
            const isIdentity = relMat.elements.every((val, i) => Math.abs(val - (i % 5 === 0 ? 1 : 0)) < 1e-7);
            if (isIdentity) return otherSolid;
            return {
              ...otherSolid,
              vertices: (otherSolid.vertices ?? []).map((pt) => {
                const v = new THREE.Vector3(...toVec3(pt)).applyMatrix4(relMat);
                return [toFrac(v.x), toFrac(v.y), toFrac(v.z)];
              }),
            };
          })
        : [source];
      audit = classifySolidEdgeVisibility(source, localCamera, {
        // Polyhedron edges follow the solids' faces only (base and Owner reference convention): a curved solid that
        // encloses an inscribed polyhedron must not dash all of its edges. Curved solids still dash free segments.
        occluders: localOccluders,
        projected_edge_pixels: viewport
          ? (edge) => {
              const a = candidate.localToWorld(edge.a.clone()).project(camera);
              const b = candidate.localToWorld(edge.b.clone()).project(camera);
              const width = Number(viewport[1]) * Number(viewport[3]);
              const height = Number(viewport[2]) * Number(viewport[3]);
              return Math.hypot((a.x - b.x) * width / 2, (a.y - b.y) * height / 2);
            }
          : undefined,
      });
      candidate.userData.edgeVisibilityAudit = audit;
      candidate.userData.edgeVisibilitySignature = signature;
      recomputedSolidCount += 1;
    }
    triangleCount += audit.triangle_count;
    sampleCount += audit.sample_count;
    allSpans.push(...audit.edge_spans);
    const visible = new Set(audit.visible_edge_ids);
    const hidden = new Set(audit.hidden_edge_ids);
    const mixed = new Set(audit.mixed_edge_ids);
    candidate.traverse((child) => {
      const id = child.userData?.visualOwnerId as string | undefined;
      const edge = child.userData?.canonicalEdge as ReturnType<typeof canonicalEdgesOf>[number] | undefined;
      if (!id || !edge || !(child as THREE.Group).isGroup) return;
      const signature = audit.edge_spans.filter((span) => span.edge_id === id)
        .map((span) => `${span.visibility}:${span.t0}:${span.t1}`).join("|");
      if (child.userData.spanSignature !== signature) {
        rebuildCanonicalEdgeOwner(child as THREE.Group, edge, audit.edge_spans);
        child.userData.spanSignature = signature;
      }
      const values = status.get(id) ?? new Set<"visible" | "hidden">();
      if (visible.has(id) || mixed.has(id)) values.add("visible");
      if (hidden.has(id) || mixed.has(id)) values.add("hidden");
      status.set(id, values);
      counts.set(id, (counts.get(id) ?? 0) + 1);
      if (child.userData.highlighted === true) highlighted.add(id);
    });
  }

  const occluderSignature = [...occluders.flatMap(o => o.matrixWorld?.elements ?? []),
    ...curvedVolumes.flatMap(o => o.worldToLocal?.elements ?? [])].map(khoa).join(",");
  const worldSignature = [
    ...[
      camera.position.x, camera.position.y, camera.position.z,
      ...camera.matrixWorldInverse.elements,
      ...camera.projectionMatrix.elements,
    ].map(khoa),
    renderSignature,
    occluderSignature,
  ].join("|");
  updateNonCanonicalVisibility(root, camera, occluders, worldSignature, curvedVolumes);
  {
    const worldCam = camera.position.clone();
    let hiddenAt: ((point: THREE.Vector3, curveNormal?: THREE.Vector3, checkHostBackface?: boolean) => boolean) | undefined;
    root.traverse((node) => {
      const rim = node.userData?.curvedRimLoop as CurvedRimLoopMeta | undefined;
      if (!rim) return;
      node.updateWorldMatrix(true, false);
      const rimSignature = `${worldSignature}|${node.matrixWorld.elements.map(khoa).join(",")}`;
      if (node.userData.curvedRimSig === rimSignature) return;
      const count = rim.midpoints.length;
      if (rim.visibilityMode === "all_dashed") {
        const flagSig = "all_dashed";
        if (node.userData.curvedRimFlagSig !== flagSig) {
          const allDashedSpans = Array.from({ length: count }, (_, i) => ({ t0: i, t1: i + 1, hidden: true }));
          capNhatHinhHocVanhCong(rim, allDashedSpans, true);
          node.userData.curvedRimFlagSig = flagSig;
        }
        node.userData.curvedRimSig = rimSignature;
        return;
      }
      if (curvedVolumes.length === 0 && occluders.length === 0 && !rim.selfOccludingSphere) {
        return;
      }
      let activeCurved = curvedVolumes;
      let tester: (point: THREE.Vector3, curveNormal?: THREE.Vector3, checkHostBackface?: boolean) => boolean;
      if (rim.selfOccludingSphere) {
        const hostNode = node.parent ?? node;
        hostNode.updateWorldMatrix(true, false);
        activeCurved = [
          ...curvedVolumes,
          { ...rim.selfOccludingSphere, worldToLocal: hostNode.matrixWorld.clone().invert() },
        ];
        tester = createWorldPointOcclusionTest(worldCam, occluders, activeCurved);
      } else {
        hiddenAt ??= createWorldPointOcclusionTest(worldCam, occluders, curvedVolumes);
        tester = hiddenAt;
      }
      rim.spanCapacity = Math.max(count * 16, count * 9 + 4 * activeCurved.length);
      const sampleWorld = (turn: number) => rim.sample(turn).outer.applyMatrix4(node.matrixWorld);
      const isCoplanarPolygonCircle = rim.rimRole === "inscribed" || rim.rimRole === "circumscribed";
      const curveNormal = isCoplanarPolygonCircle
        ? new THREE.Vector3(0, 0, 1).transformDirection(node.matrixWorld).normalize()
        : undefined;
      const checkHostBackface = rim.rimRole === "inscribed";
      const hidden = (t: number) => tester(sampleWorld(t / count), curveNormal, checkHostBackface);
      const tangencies = curvedSurfaceTangentTurns(sampleWorld, worldCam, activeCurved).map(t => t * count);
      const spans: { t0: number; t1: number; hidden: boolean }[] = [];
      // Probe the curve itself: chord interiors lie inside curved solids even on their visible side.
      // Angular probe spacing <= 2π/384; transition bracket refined to < 2π/(96*2^20).
      for (let i = 0; i < count; i++) {
        let start = i, state = hidden(i);
        const cuts = [i, i + 0.25, i + 0.5, i + 0.75, i + 1,
          ...tangencies.filter(t => t > i && t < i + 1)].sort((a, b) => a - b);
        // Midpoints between analytic tangencies catch a tiny visible interval even if its endpoints are tangencies.
        const probes = cuts.flatMap((t, j) => j ? [(cuts[j - 1] + t) / 2, t] : [t]);
        for (let j = 1; j < probes.length; j++) {
          const end = probes[j], next = hidden(end);
          if (next === state) continue;
          let lo = probes[j - 1], hi = end;
          for (let k = 0; k < 20; k++) {
            const mid = (lo + hi) / 2;
            if (hidden(mid) === state) lo = mid; else hi = mid;
          }
          const boundary = (lo + hi) / 2;
          spans.push({ t0: start, t1: boundary, hidden: state });
          start = boundary; state = next;
        }
        spans.push({ t0: start, t1: i + 1, hidden: state });
      }
      const flagSig = spans.map(s => `${s.t0.toFixed(8)},${s.t1.toFixed(8)},${+s.hidden}`).join("|");
      if (node.userData.curvedRimFlagSig !== flagSig) {
        capNhatHinhHocVanhCong(rim, spans, true);
        node.userData.curvedRimFlagSig = flagSig;
      }
      node.userData.curvedRimSig = rimSignature;
    });
  }

  const visible = [...status].filter(([, values]) => values.size === 1 && values.has("visible"))
    .map(([id]) => id).sort();
  const hidden = [...status].filter(([, values]) => values.size === 1 && values.has("hidden"))
    .map(([id]) => id).sort();
  root.userData.hiddenCanonicalEdgeIds = new Set(hidden);   // đọc bởi `datCoGocVuong` (chọn dấu đại diện không khuất)
  const mixed = [...status].filter(([, values]) => values.size > 1)
    .map(([id]) => id).sort();
  const duplicates = [...counts].filter(([, count]) => count > 1)
    .map(([id]) => id).sort();
  return {
    visible_edge_ids: visible,
    hidden_edge_ids: hidden,
    mixed_edge_ids: mixed,
    duplicate_visual_owner_ids: duplicates,
    edge_spans: allSpans,
    triangle_count: triangleCount,
    sample_count: sampleCount,
    highlighted_render_owner_ids: [...highlighted].sort(),
    recomputed_solid_count: recomputedSolidCount,
    recomputation_ms: (globalThis.performance?.now?.() ?? Date.now()) - started,
    edge_count: status.size,
    span_count: allSpans.length,
  };
}

/**
 * Bề dày nét của thiết diện, tính từ TỈ LỆ CẢNH.
 *
 * Không có nền hình học (ô soi dựng một vật lẻ) thì lùi về tỉ lệ của chính
 * vật ấy — nét vẫn cân đối, chỉ mất tương quan với phần còn lại của cảnh.
 */
function beDayNet(diemNen: Vec3[], coVat: number): number {
  const d = duongKinhCanh(diemNen);
  return (d > 0 ? d : Math.max(coVat, 1) * 2) * SECTION_STROKE_RATIO;
}

/** Khối chính + khoảng khung vừa của lần đặt khung gần nhất, để giới hạn zoom gần theo kịp hướng nhìn khi xoay. */
const _gioiHanGanTheoKhoi = new WeakMap<OrbitControls, { tam: TamXoayOnDinh; khoangKhung: number }>();

/** Cập nhật `minDistance` theo hướng nhìn hiện tại (gọi ở mỗi `change` của điều khiển); trả khoảng tựa hiện tại. */
export function capNhatGioiHanGan(cam: THREE.PerspectiveCamera, dieuKhien: OrbitControls): number | null {
  const g = _gioiHanGanTheoKhoi.get(dieuKhien);
  if (!g) return null;
  const t = dieuKhien.target;
  const huong: [number, number, number] = [cam.position.x - t.x, cam.position.y - t.y, cam.position.z - t.z];
  dieuKhien.minDistance = khoangGanToiThieu(g.tam, huong, g.khoangKhung);
  return khoangTuaTheoHuong(g.tam, huong);
}

/** Đặt camera về một khung nhìn — và HUỶ đà xoay còn lại của cú kéo trước.
 *  Damping giữ phần xoay chưa áp trong OrbitControls; chỉ đặt pose thì đà ấy
 *  đẩy camera đi tiếp, và "Xem lại toàn hình" không về trạng thái trung tính.
 *  Một lần `update()` với damping tắt tiêu hết đà (xoá delta), rồi mới đặt. */
export function datKhungNhin(
  cam: THREE.PerspectiveCamera,
  dieuKhien: OrbitControls,
  kn: KhungNhin,
  tuyChon?: { banKinhKhoi?: number; tam?: TamXoayOnDinh | null },
): void {
  const dist = Math.hypot(
    kn.viTri[0] - kn.nhinVao[0],
    kn.viTri[1] - kn.nhinVao[1],
    kn.viTri[2] - kn.nhinVao[2],
  );
  if (Number.isFinite(dist) && dist > 1e-4) {
    const rKhoi = tuyChon?.banKinhKhoi;
    const tam = tuyChon?.tam;
    if (tam) {
      _gioiHanGanTheoKhoi.set(dieuKhien, { tam, khoangKhung: dist });
    } else {
      _gioiHanGanTheoKhoi.delete(dieuKhien);
    }
    if (typeof rKhoi === "number" && Number.isFinite(rKhoi) && rKhoi > 1e-4) {
      dieuKhien.minDistance = tam
        ? khoangGanToiThieu(tam, [kn.viTri[0] - kn.nhinVao[0], kn.viTri[1] - kn.nhinVao[1], kn.viTri[2] - kn.nhinVao[2]], dist)
        : Math.max(0.5, Math.min(dist * 0.55, rKhoi * 1.08));
      dieuKhien.maxDistance = Math.max(dist * 2.8, rKhoi * 6, 12);
      cam.near = Math.max(0.02, Math.min(0.1, Math.min(dist, rKhoi) * 0.01));
      cam.far = Math.max(200, Math.max(dist, rKhoi) * 16);
    } else {
      dieuKhien.minDistance = Math.max(0.8, dist * 0.42);
      dieuKhien.maxDistance = Math.max(dist * 2.8, 12);
      cam.near = Math.max(0.02, Math.min(0.1, dist * 0.01));
      cam.far = Math.max(200, dist * 12);
    }
  }
  const damping = dieuKhien.enableDamping;
  dieuKhien.enableDamping = false;
  dieuKhien.update();
  cam.position.set(...kn.viTri);
  dieuKhien.target.set(...kn.nhinVao);
  dieuKhien.update();
  dieuKhien.enableDamping = damping;
  cam.updateProjectionMatrix();
}

/**
 * Chuyển danh sách `SceneObject` sang đầu vào số thuần cho `tinhTamXoayTuKhoi` để giữ
 * `scene3d-camera.ts` không phụ thuộc `scene3d-model.ts` hay `three`.
 */
export function tinhTamXoayOnDinh(
  objects: readonly SceneObject[],
  bienDoiDiem?: (p: Vec3, objectId: string) => Vec3,
): TamXoayOnDinh | null {
  const mapPt = (p: Vec3, id: string): Vec3 => (bienDoiDiem ? bienDoiDiem(p, id) : p);
  const dsKhoi: LoaiKhoiTamXoay[] = [];
  const diemDuPhong: Vec3[] = [];

  for (const o of objects) {
    if (o.type === "solid" && (o.vertices?.length ?? 0) > 0) {
      dsKhoi.push({
        loai: "solid",
        vertices: o.vertices!.map((v) => mapPt(toVec3(v), o.id)),
        faces: o.faces ?? [],
      });
    } else if (o.type === "curved_solid" && o.anchor && o.radius_sq) {
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
      const anchor = mapPt(toVec3(o.anchor), o.id);
      const h = o.curved_kind && o.curved_kind !== "ball" && o.height_sq
        ? Math.sqrt(Math.max(0, toNumber(o.height_sq)))
        : 0;
      const dinhRaw: Vec3 = o.apex_or_top
        ? toVec3(o.apex_or_top)
        : h > 0
          ? [toNumber(o.anchor[0]), toNumber(o.anchor[1]), toNumber(o.anchor[2]) + h]
          : toVec3(o.anchor);
      dsKhoi.push({
        loai: "curved_solid",
        curvedKind: o.curved_kind ?? "ball",
        anchor,
        radius: r,
        apexOrTop: mapPt(dinhRaw, o.id),
        pts: diemHuuHan([o]).map((p) => mapPt(p, o.id)),
      });
    }
    for (const p of diemHuuHan([o])) {
      diemDuPhong.push(mapPt(p, o.id));
    }
  }

  return tinhTamXoayTuKhoi(dsKhoi, diemDuPhong);
}

/**
 * Điểm thế giới mà khung nhìn phải ôm — đỉnh THẬT của những gì đang dựng.
 *
 * ⚠️ BỎ VẬT VÔ HẠN KHỎI PHÉP TÍNH KHUNG NHÌN. `setFromObject(goc)` ôm trọn mọi
 * thứ đang dựng — kể cả miếng mặt phẳng và đoạn đại diện của đường thẳng, hai
 * thứ có cỡ do CHÍNH tầng trình bày chọn. Để chúng vào thì quyết định trình
 * bày tự khuếch đại: miếng to ra ⇒ hộp bao to ra ⇒ camera lùi ⇒ hình thật bé
 * lại. ĐỈNH THẬT (toạ độ thế giới, đã tính tách khối), không phải góc hộp bao:
 * khung vừa theo HÌNH CHIẾU, và góc hộp bao chiếu ra ngoài hình.
 */
export function diemKhungNhin(goc: THREE.Object3D, daCoDiemCanh = false): [number, number, number][] {
  const diem: [number, number, number][] = [];
  const p = new THREE.Vector3();
  // Cờ nằm trên NHÓM (đường vô hạn là một nhóm hai nét): hỏi cả tổ tiên, không
  // chỉ chính nút — bỏ sót thì nét con kéo khung theo đoạn do renderer tự chọn
  // (w11: "Xem lại toàn hình" ở bước cuối bài thiết diện dời hẳn tâm nhìn).
  const boQua = (vat: THREE.Object3D) => {
    for (let x: THREE.Object3D | null = vat; x && x !== goc; x = x.parent) {
      if (x.userData?.voHan || x.userData?.chieuSau) return true;
      if (daCoDiemCanh && (x.userData?.curvedRimLoop || x.userData?.curvedSolidVolume)) return true;
    }
    return false;
  };
  goc.updateMatrixWorld(true);
  goc.traverse((vat) => {
    if (boQua(vat)) return;
    if (!(vat as THREE.Mesh).isMesh && !(vat as THREE.Line).isLine) return;
    // Hình cầu bắt chuột và chấm đỉnh (co giãn theo zoom) không phải hình; toạ
    // độ điểm đã vào khung qua `diemHuuHan`.
    if (vat.name === "pick-proxy" || vat.name.endsWith(":proxy") || vat.userData?.dauDinh) return;
    const pos = (vat as THREE.Mesh).geometry?.getAttribute?.("position");
    for (let i = 0; pos && i < pos.count; i++) {
      p.fromBufferAttribute(pos, i).applyMatrix4(vat.matrixWorld);
      diem.push([p.x, p.y, p.z]);
    }
  });
  return diem;
}

/**
 * Điểm khung nhìn ôm: hình đang dựng (`diemKhungNhin`) + toàn cảnh (`diemCanh`, đã xoay hiển thị). Hộp bao đầy đủ
 * chỉ là dự phòng cho cảnh CHỈ có mặt phẳng/đường — xét nó sau khi gộp toàn cảnh (regular-triangular-pyramid-w01:
 * ở bước 0 chỉ có điểm, vùng bấm lọt vào hai góc hộp bao ⇒ hình lệch 65–100 px, tâm quỹ đạo lệch khỏi hình).
 */
export function diemVuaKhung(goc: THREE.Object3D, diemCanh: Vec3[]): Vec3[] {
  const diem: Vec3[] = [...diemKhungNhin(goc, diemCanh.length > 0), ...diemCanh];
  if (diem.length === 0) {
    const hop = new THREE.Box3().setFromObject(goc);
    if (!hop.isEmpty()) diem.push([hop.min.x, hop.min.y, hop.min.z], [hop.max.x, hop.max.y, hop.max.z]);
  }
  return diem;
}

/**
 * Cỡ chấm đỉnh và vùng bấm theo ĐIỂM ẢNH CSS — gọi mỗi khung (w11, W10-H5).
 *
 * Lưới giữ bán kính gốc; ở đây chỉ co giãn cho hình chiếu bằng đúng token
 * `DAU_DINH_PX`, bất kể camera xa gần, hình to nhỏ hay DPR (tính theo px CSS).
 */
export function datCoDauDinh(
  goc: THREE.Object3D, cam: THREE.PerspectiveCamera, rongCss: number, caoCss: number, stepPulse = 0,
): void {
  const p = new THREE.Vector3();
  const s = new THREE.Vector3();
  const clampedPulse = Number.isFinite(stepPulse) ? Math.max(0, Math.min(1, stepPulse)) : 0;
  goc.updateMatrixWorld(true);
  goc.traverse((x) => {
    const loai = x.userData?.dauDinh ?? (x.userData?.vungBam ? "bam" : null);
    if (!loai) return;
    x.getWorldPosition(p).applyMatrix4(cam.matrixWorldInverse);
    const stepRole = loai === "thuong" && clampedPulse > 0.005
      ? (x.parent?.userData?.stepHighlightRole as "new" | "dep" | undefined)
      : undefined;
    const stepDotScale = stepRole === "new" ? 1 + 0.22 * clampedPulse : stepRole === "dep" ? 1 + 0.09 * clampedPulse : 1;
    const banKinhPx = loai === "bam" ? banKinhBamPx(rongCss) : (coDauDinhPx(loai === "chon", rongCss) / 2) * stepDotScale;
    const goc0 = ((x as THREE.Mesh).geometry as THREE.SphereGeometry).parameters.radius;
    x.parent?.getWorldScale(s);
    x.scale.setScalar((banKinhPx * donViMoiPx(-p.z, cam.fov, caoCss)) / (goc0 * (s.x || 1)));
  });
}

/**
 * Đoạn thẳng nào NHƯỜNG NÉT cho cạnh chuẩn của một khối đang dựng — một cạnh,
 * một nét. `dung` là các vật SẼ dựng ở bước này; `bienDoi(id)` là khoá vị trí
 * trình bày (tách khối dời khối đi thì cạnh ấy không còn trùng đoạn nữa).
 */
export function doanNhuongCanh(
  dung: SceneObject[], bienDoi: (id: string) => string,
): Set<string> {
  const chu = new Map<string, string>();
  const khoiDich = new Map<string, string>();
  for (const o of dung) {
    if (o.type !== "solid") continue;
    const kd = bienDoi(o.id);
    khoiDich.set(o.id, kd);
    for (const e of o.edge_ownership ?? []) chu.set(e.edge_id, kd);
  }
  const ra = new Set(dung.filter((o) => o.type === "segment3" && o.boundary_edge_ids?.length
    && o.boundary_edge_ids.every((id) => chu.get(id) === bienDoi(o.id))).map((o) => o.id));
  for (const o of dung) {
    if (
      o.type === "polygon3"
      && o.parent
      && (o.display_group ?? []).includes("face")
      && khoiDich.has(o.parent)
      && khoiDich.get(o.parent) === bienDoi(o.id)
    ) {
      ra.add(o.id);
    }
  }
  const canhMien: { a: Vec3; b: Vec3; dich: string }[] = [];
  for (const o of dung) {
    if ((o.type !== "section" && !(o.type === "polygon3" && vaiTroMien(o) === "section")) || o.closed === false) continue;
    const pts = (o.polygon ?? o.vertices ?? []).map(toVec3);
    if (pts.length < 3) continue;
    const dich = bienDoi(o.id);
    for (let i = 0; i < pts.length; i += 1) {
      canhMien.push({ a: pts[i], b: pts[(i + 1) % pts.length], dich });
    }
  }
  if (canhMien.length > 0) {
    const trenDoan = (p: Vec3, a: Vec3, b: Vec3) => {
      const abx = b[0] - a[0], aby = b[1] - a[1], abz = b[2] - a[2];
      const lenSq = abx * abx + aby * aby + abz * abz;
      if (lenSq < 1e-12) return false;
      const apx = p[0] - a[0], apy = p[1] - a[1], apz = p[2] - a[2];
      const t = (apx * abx + apy * aby + apz * abz) / lenSq;
      if (t < -1e-4 || t > 1 + 1e-4) return false;
      return Math.hypot(a[0] + abx * t - p[0], a[1] + aby * t - p[1], a[2] + abz * t - p[2]) <= 1e-4;
    };
    for (const o of dung) {
      if (ra.has(o.id)) continue;
      if (o.type === "polygon3" && vaiTroMien(o) !== "section" && o.closed !== false) {
        const pts = (o.polygon ?? o.vertices ?? []).map(toVec3);
        const dich = bienDoi(o.id);
        if (
          pts.length >= 3
          && pts.every((p, idx) => {
            const q = pts[(idx + 1) % pts.length];
            return canhMien.some((c) => c.dich === dich && trenDoan(p, c.a, c.b) && trenDoan(q, c.a, c.b));
          })
        ) {
          ra.add(o.id);
        }
        continue;
      }
      if (o.type !== "segment3" || o.perpendicular_witness || o.annotation?.witness) continue;
      const ptA = o.point_a ?? o.endpoints?.[0];
      const ptB = o.point_b ?? o.endpoints?.[1];
      if (!ptA || !ptB) continue;
      const a = toVec3(ptA), b = toVec3(ptB);
      const dich = bienDoi(o.id);
      if (canhMien.some((c) => c.dich === dich && trenDoan(a, c.a, c.b) && trenDoan(b, c.a, c.b))) {
        ra.add(o.id);
      }
    }
  }
  return ra;
}

/**
 * Quyền sở hữu biên của đa giác đáy (`BASE_REGION`) theo từng bước dựng:
 * khi khối `solid` chủ chưa xuất hiện ở bước hiện tại (vd Bước 1 dựng đáy `ABCD`, Bước 2 dựng `SA`)
 * hoặc khối đã tách rời khỏi mặt đáy, đa giác đáy tự giữ quyền vẽ các cạnh biên `#1E293B`;
 * ngay khi khối `solid` có mặt cùng phép dời và sở hữu đủ `boundary_edge_ids`, mặt đáy nhường biên sạch cho khối.
 */
export function resolveStepPolygonBoundaryOwnership(
  o: SceneObject,
  dung: readonly SceneObject[],
  bienDoi: (id: string) => string = () => "0,0,0",
): SceneObject {
  if (
    o.type !== "polygon3"
    || vaiTroMien(o) !== "base"
    || !(o.boundary_edge_ids && o.boundary_edge_ids.length > 0)
  ) {
    return o;
  }
  const chu = new Map<string, string>();
  for (const s of dung) {
    if (s.type !== "solid") continue;
    const kd = bienDoi(s.id);
    if (s.edge_ownership && s.edge_ownership.length > 0) {
      for (const e of s.edge_ownership) chu.set(e.edge_id, kd);
    } else {
      for (const ce of canonicalEdgesOf(s)) chu.set(ce.id, kd);
    }
  }
  const myKey = bienDoi(o.id);
  const allOwnedByActiveSolid = o.boundary_edge_ids.every((id) => chu.get(id) === myKey);
  return allOwnedByActiveSolid ? o : { ...o, boundary_edge_ids: [] };
}

/**
 * Thiết diện ở MỘT bước: chỉ các cạnh `geometry_progress` đã cho hiện, khép và tô theo
 * cờ CỦA BƯỚC ẤY — tua ngược về bước chưa tô là mất phần tô. `null` ⇔ chưa cạnh nào hiện.
 * Vật không phải thiết diện, hoặc không có tiến độ, giữ nguyên.
 */
export function vatThietDienTaiBuoc(o: SceneObject, progress?: GeometryProgress): SceneObject | null {
  if (o.type !== "section" || !progress || !o.polygon) return o;
  const count = progress.visible_edge_ids.length;
  if (count === 0) return null;
  return {
    ...o,
    polygon: progress.closed ? o.polygon : o.polygon.slice(0, count + 1),
    closed: progress.closed,
    fill_visible: progress.fill_visible,
  };
}

/** Móc đo `__geo3d_set_section_fill_visible`: bật/tắt ĐÚNG các vật `section_fill:<id>`. */
export function datHienToThietDien(goc: THREE.Object3D, on: boolean): string[] {
  const ten: string[] = [];
  goc.traverse((x) => {
    if (x.name.startsWith("section_fill:")) {
      x.visible = on;
      ten.push(x.name);
    }
  });
  return ten;
}

/**
 * Một đối tượng cảnh → một `Object3D`, hoặc `null` nếu không vẽ được.
 *
 * `readout` trả `null` **có chủ đích**: một đại lượng đo được không có hình
 * trong không gian. Nó vẫn phải hiện lên — nhưng ở bảng chữ bên cạnh, không
 * phải trong khung 3D. Vẽ bừa một nhãn lơ lửng là đặt một con số vào một chỗ
 * không có nghĩa hình học.
 */
export function buildObject3D(
  o: SceneObject,
  /** `true` = tô sáng theo bước; một tầng = chuỗi nhân quả quanh vật đang chọn. */
  noiBat: boolean | TangNhanManh | "hover",
  banKinhBam = banKinhBamDiem(KHOANG_CAM_MAC_DINH),
  /**
   * Điểm CÓ BIÊN của cả cảnh — chỉ mặt phẳng dùng tới, để cắt phần đáng vẽ ra
   * khỏi một mặt phẳng vô hạn. Mặc định rỗng ⇒ rơi về cỡ cố định, nên mọi nơi
   * gọi cũ (test, ô soi) giữ nguyên hành vi.
   */
  diemNen: Vec3[] = [],
  cameraPosition = new THREE.Vector3(8, 3, 6),
  /** Cạnh chuẩn được tô qua vật khác (đoạn/đáy trùng cạnh) → màu tô. */
  highlightedEdgeIds: ReadonlySet<string> | ReadonlyMap<string, number> = new Set(),
  /** W4: khúc tô sáng của đoạn con nằm trên cạnh chuẩn (`toSangCanhChuan().khuc`). */
  khucToSang: ReadonlyMap<string, KhucToSang> = new Map(),
  xray = false,
  vaiKhoi: VaiTroKhoi = "primary",
  coThietDienDong = true,
  sphereReference = true,
  auxiliaryExplanatorySurface = false,
  sceneContext?: Pick<Scene3D, "objects">,
  defaultEdgeColors: ReadonlyMap<string, number> = new Map(),
  hoveredEdgeIds: ReadonlySet<string> = new Set(),
  boundedPlanePolygon?: Vec3[],
  visibleStepObjects?: readonly SceneObject[],
): THREE.Object3D | null {
  // Bảo toàn màu ngữ nghĩa toán học khi hover, chọn đối tượng hoặc làm bối cảnh:
  // nhấn mạnh bằng độ dày nét, điều biến độ sáng cùng họ màu (|Δhue| < 1.5°) và giảm nhẹ độ đục cho bối cảnh.
  const boiCanh = noiBat === "boi_canh";
  if (boiCanh) noiBat = false;
  const interactionMode: "neutral" | "hover" | "selected" = noiBat === "hover"
    ? "hover"
    : noiBat
      ? "selected"
      : "neutral";
  const modState: InteractionVisualState = boiCanh ? "context" : interactionMode;
  const finishBuilt = (built: THREE.Object3D | null, name: string): THREE.Object3D | null => {
    if (!built) return null;
    v(built, name);
    built.userData.interactionState = interactionMode;
    if (boiCanh) lamDiu(built, 0.84);
    return built;
  };
  const nen = (macDinh: number) => macDinh;
  const net = (macDinh: number) => modulateSemanticColor(macDinh, modState);
  const mauKhoi = vaiKhoi === "secondary" ? MAU.secondaryMesh : MAU.mesh;
  const doDucKhoi = interactionMode === "selected"
    ? DO_DUC.selectedSolid
    : interactionMode === "hover"
      ? 0.15
      : vaiKhoi === "secondary"
        ? DO_DUC.secondarySolid
        : DO_DUC.solid;
  const vaiMien =
    o.type === "polygon3" && sceneContext && isPolyhedronOppositeTopBasePolygon(sceneContext, o)
      ? "base"
      : vaiTroMien(o);
  const laThietDien = vaiMien === "section";
  const netMien = (macDinh: number) => modulateSemanticColor(macDinh, modState);
  const mauToMien = laThietDien
    ? (auxiliaryExplanatorySurface ? MAU.line : MAU.polygon)
    : vaiMien === "base" ? MAU.mesh : MAU.surface;
  const mauVienMien = laThietDien
    ? (auxiliaryExplanatorySurface ? MAU.line : MAU.sectionOutline)
    : vaiMien === "base" ? MAU.canh : MAU.planeOutline;
  const doDucMien = laThietDien
    ? (auxiliaryExplanatorySurface
        ? (interactionMode === "selected" ? 0.28 : interactionMode === "hover" ? 0.22 : 0.18)
        : (interactionMode === "selected" ? DO_DUC.selectedSection : DO_DUC.section))
    : vaiMien === "base" ? (interactionMode === "selected" ? DO_DUC.selectedBase : DO_DUC.base)
    : (interactionMode === "selected" ? DO_DUC.selectedPlane : interactionMode === "hover" ? 0.10 : DO_DUC.plane);

  if (o.render === "point_marker" && o.xyz) {
    // HAI hình, một vật: chấm NHÌN THẤY giữ nguyên cỡ, cộng một hình cầu VÔ
    // HÌNH rộng hơn chỉ để bắt con trỏ. Phóng to chấm cho dễ bấm thì một điểm
    // hình học bắt đầu trông như quả cầu — đổi thứ học sinh NHÌN THẤY để
    // chuột dễ hơn là cái giá không được trả.
    //
    // `visible = false` KHÔNG dùng được: `Raycaster` bỏ qua vật vô hình. Nên
    // proxy phải "được vẽ" mà không để lại gì — `colorWrite: false` +
    // `depthWrite: false`.
    const nhom = new THREE.Group();
    const m = new THREE.MeshStandardMaterial({
      color: o.origin === "free" ? net(MAU.free) : net(MAU.derived),
    });
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(BAN_KINH_NHIN, 16, 12), m);
    // Cỡ THẬT theo px màn hình đặt mỗi khung (`datCoDauDinh`, w11).
    mesh.userData.dauDinh = noiBat === "dich" || interactionMode === "selected" ? "chon" : "thuong";
    nhom.add(mesh);
    const proxy = new THREE.Mesh(
      new THREE.SphereGeometry(banKinhBam, 8, 6),
      new THREE.MeshBasicMaterial({
        colorWrite: false, depthWrite: false, transparent: true, opacity: 0,
      }),
    );
    proxy.name = "pick-proxy";
    proxy.userData.vungBam = true;
    nhom.add(proxy);
    nhom.position.set(...toVec3(o.xyz));
    return finishBuilt(nhom, `point:${o.id}`);
  }

  if (o.render === "line" && o.point && o.direction) {
    // Kéo dài vector chỉ phương ĐÃ CHO ra hai phía. Không tính hướng — hướng
    // là dữ liệu từ kernel. Phần được vẽ ôm vùng hình (`doanDuongThang`), như
    // miếng mặt phẳng; không có điểm nền thì rơi về độ dài cố định.
    const rawDir = toVec3(o.direction);
    if (Math.hypot(...rawDir) <= 1e-9) return null;
    const p = new THREE.Vector3(...toVec3(o.point));
    const d = new THREE.Vector3(...rawDir).normalize();
    const resolvedSpan = sceneContext
      ? resolveLineDisplaySpan(sceneContext, o, sceneContext.objects, diemNen)
      : null;
    if (resolvedSpan?.mode === "no_intersection") return null;
    const doan = resolvedSpan ? resolvedSpan.endpoints : doanDuongThang(toVec3(o.point), rawDir, diemNen);
    const a = doan ? new THREE.Vector3(...doan[0]) : p.clone().addScaledVector(d, -LINE_DISPLAY_HALF_LENGTH);
    const b = doan ? new THREE.Vector3(...doan[1]) : p.clone().addScaledVector(d, LINE_DISPLAY_HALF_LENGTH);
    const laGiaoTuyen = isIntersectionLineOrSegment(o, sceneContext ?? undefined);
    const laDuongChinh = isPrimarySpatialLine(o);
    const mauDuong = laGiaoTuyen
      ? netMien(MAU.sectionOutline)
      : laDuongChinh
        ? net(MAU.circumscribedCircle)
        : net(MAU.line);
    const coNetDut = beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE;
    let coreA = a;
    let coreB = b;
    const extPairs: [THREE.Vector3, THREE.Vector3][] = [];
    if (resolvedSpan?.coreSegment) {
      let c0 = new THREE.Vector3(...resolvedSpan.coreSegment[0]);
      let c1 = new THREE.Vector3(...resolvedSpan.coreSegment[1]);
      const abx = b.x - a.x, aby = b.y - a.y, abz = b.z - a.z;
      const c01x = c1.x - c0.x, c01y = c1.y - c0.y, c01z = c1.z - c0.z;
      if (abx * c01x + aby * c01y + abz * c01z < 0) {
        const tmpC = c0;
        c0 = c1;
        c1 = tmpC;
      }
      if (Math.hypot(c1.x - c0.x, c1.y - c0.y, c1.z - c0.z) > 1e-4) {
        coreA = c0;
        coreB = c1;
        if (Math.hypot(c0.x - a.x, c0.y - a.y, c0.z - a.z) > 1e-4) extPairs.push([a, c0]);
        if (Math.hypot(b.x - c1.x, b.y - c1.y, b.z - c1.z) > 1e-4) extPairs.push([c1, b]);
      }
    }
    const g = new THREE.BufferGeometry().setFromPoints([coreA, coreB]);
    const duong = duongHaiLuot(g, mauDuong, coNetDut, `line:${o.id}`, true);
    duong.userData.voHan = true;
    const semLineRole = laGiaoTuyen
      ? "intersection_line"
      : laDuongChinh
        ? "target_line"
        : "auxiliary_line";
    duong.userData.semanticLineRole = semLineRole;
    for (const c of duong.children) {
      c.userData.semanticLineRole = semLineRole;
      c.userData.interactionState = interactionMode;
    }
    preallocateSpanGeoPool(duong, 6);
    duong.userData.nonCanonicalSegment = {
      prefix: `line:${o.id}`,
      objectId: o.id,
      a: coreA,
      b: coreB,
      color: mauDuong,
      dashSize: coNetDut,
      highlighted: Boolean(noiBat),
      interactionState: interactionMode,
      yieldColinear: true,
      renderOrder: laGiaoTuyen ? THU_TU_VE_THIET_DIEN : THU_TU_DUONG,
    } satisfies NonCanonicalSegmentMeta;
    extPairs.forEach(([ea, eb], extIdx) => {
      const extGeo = new THREE.BufferGeometry().setFromPoints([ea, eb]);
      const extGroup = duongHaiLuot(extGeo, mauDuong, coNetDut, `line_ext:${o.id}:${extIdx}`, true);
      extGroup.name = `line_ext:${o.id}:${extIdx}`;
      extGroup.userData.voHan = true;
      extGroup.userData.semanticLineRole = "line_extension";
      for (const c of extGroup.children) {
        c.userData.forceDashed = true;
        if (c.name.endsWith(":thay")) c.visible = false;
        else if (c.name.endsWith(":khuat")) {
          c.visible = true;
          c.userData.hidden = false;
        }
      }
      for (const c of extGroup.children) {
        c.userData.semanticLineRole = "line_extension";
        c.userData.interactionState = interactionMode;
        c.raycast = () => {};
      }
      preallocateSpanGeoPool(extGroup, 4);
      extGroup.userData.nonCanonicalSegment = {
        prefix: `line_ext:${o.id}:${extIdx}`,
        forceDashed: true,
        objectId: `${o.id}::ext:${extIdx}`,
        a: ea,
        b: eb,
        color: mauDuong,
        dashSize: coNetDut,
        highlighted: Boolean(noiBat),
        interactionState: interactionMode,
        yieldColinear: true,
        renderOrder: THU_TU_DUONG,
        noRaycast: true,
      } satisfies NonCanonicalSegmentMeta;
      lamDiu(extGroup, 0.72);
      duong.add(extGroup);
    });
    if (!noiBat && !laGiaoTuyen && !laDuongChinh) lamDiu(duong, HE_SO_DUONG_PHU);
    return finishBuilt(duong, `line:${o.id}`);
  }

  if (
    (o.render === "segment" || (o.type === "segment3" && o.render === "line" && (!o.point || !o.direction)))
    && ((o.point_a && o.point_b) || (o.endpoints && o.endpoints.length >= 2))
  ) {
    // Đoạn thẳng HỮU HẠN nối đúng hai đầu mút — không vô hạn, không kéo dài.
    const ptA = o.point_a ?? o.endpoints![0];
    const ptB = o.point_b ?? o.endpoints![1];
    const a = new THREE.Vector3(...toVec3(ptA));
    const b = new THREE.Vector3(...toVec3(ptB));
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const laGiaoTuyen = isIntersectionLineOrSegment(o, sceneContext ?? undefined);
    const laCanhBienKhoi = !laGiaoTuyen
      && !(o.perpendicular_witness || o.annotation?.witness)
      && !(o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
      && ((o.formation_roles ?? []).includes("CONSTRUCT_LATERAL_BOUNDARY") || Boolean(o.boundary_edge_ids?.length));
    const mauDoan = laGiaoTuyen
      ? netMien(MAU.sectionOutline)
      : laCanhBienKhoi
        ? net(MAU.canh)
        : net(MAU.line);
    const coNetDut = (beDayNet(diemNen, 1) / SECTION_STROKE_RATIO) * NET_DUT_TI_LE;
    // Nhường nét cho cạnh chuẩn của khối (`doanNhuongCanh`): chỉ còn vùng bấm.
    const duong: THREE.Object3D = o.display_role === "hit_proxy"
      ? v(new THREE.Line(g, new THREE.LineBasicMaterial({
          colorWrite: false, depthWrite: false, transparent: true, opacity: 0, linewidth: NET.pick,
        })), `segment:${o.id}:proxy`)
      : duongHaiLuot(
          g,
          mauDoan,
          coNetDut,
          `segment:${o.id}`,
          true,
        );
    duong.userData.voHan = false;
    if (o.display_role !== "hit_proxy") {
      const isWitnessSeg = !laGiaoTuyen && !laCanhBienKhoi && Boolean(o.perpendicular_witness || o.annotation?.witness);
      const isAuxSeg = !laGiaoTuyen
        && !isWitnessSeg
        && !(o.display_group ?? []).includes("target")
        && (o.formation_roles ?? []).includes("CONSTRUCT_AUXILIARY_GEOMETRY");
      const segRole = laGiaoTuyen
        ? "intersection_line"
        : isWitnessSeg
          ? "perpendicular_witness"
          : isAuxSeg
            ? "auxiliary_line"
            : undefined;
      if (segRole) {
        duong.userData.semanticLineRole = segRole;
      }
      for (const c of duong.children) {
        if (segRole) c.userData.semanticLineRole = segRole;
        c.userData.interactionState = interactionMode;
      }
      preallocateSpanGeoPool(duong, 6);
      duong.userData.nonCanonicalSegment = {
        prefix: `segment:${o.id}`,
        objectId: o.id,
        a,
        b,
        color: mauDoan,
        dashSize: coNetDut,
        highlighted: Boolean(noiBat),
        interactionState: interactionMode,
        yieldColinear: !laGiaoTuyen,
        renderOrder: laGiaoTuyen ? THU_TU_VE_THIET_DIEN : THU_TU_DUONG,
      } satisfies NonCanonicalSegmentMeta;
    }

    // Ký hiệu góc vuông (perpendicular marker) CHỈ khi vật mang chứng chỉ vuông góc tường minh từ backend
    // (`perpendicular_witness` hoặc `annotation.witness`) với hai phương u, v thực sự vuông góc.
    const chungChi = o.perpendicular_witness ?? o.annotation?.witness;
    if (chungChi?.foot && chungChi.marker?.u && chungChi.marker?.v
        && nhanChungDoanHopLe(chungChi, [a.x, a.y, a.z], [b.x, b.y, b.z])) {
      const footVec = toVec3(chungChi.foot);
      const segMid: [number, number, number] = [
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5,
        (a.z + b.z) * 0.5,
      ];
      const rawU = toVec3(chungChi.marker.u);
      const rawV0 = toVec3(chungChi.marker.v);
      const flipV1 =
        rawV0[0] * (segMid[0] - footVec[0])
          + rawV0[1] * (segMid[1] - footVec[1])
          + rawV0[2] * (segMid[2] - footVec[2])
        < -1e-9;
      const rawV: [number, number, number] = flipV1
        ? [-rawV0[0], -rawV0[1], -rawV0[2]]
        : rawV0;
      const [cx, cy, cz] = footVec;
      const doanCoTrongCanh = visibleStepObjects
        ? doanDaVe(visibleStepObjects)
        : (sceneContext ? doanDaVe(sceneContext.objects) : []);
      const uToId = chungChi.marker.u_to;
      const uToPool = visibleStepObjects ?? sceneContext?.objects;
      const uToPtObj = uToId && uToPool
        ? uToPool.find((cand) => cand.id === uToId && cand.type === "point3" && Boolean(cand.xyz))
        : undefined;
      const uToVecCandidate = uToPtObj?.xyz ? toVec3(uToPtObj.xyz) : null;
      const uToDiff: Vec3 | null = uToVecCandidate
        ? [uToVecCandidate[0] - cx, uToVecCandidate[1] - cy, uToVecCandidate[2] - cz]
        : null;
      const uToLen = uToDiff ? Math.hypot(uToDiff[0], uToDiff[1], uToDiff[2]) : 0;
      const rawVLen0 = Math.hypot(rawV[0], rawV[1], rawV[2]);
      const validUTo = Boolean(
        uToDiff
        && uToLen > 1e-6
        && rawVLen0 > 1e-6
        && Math.abs(uToDiff[0] * rawV[0] + uToDiff[1] * rawV[1] + uToDiff[2] * rawV[2]) <= 1e-4 * uToLen * rawVLen0,
      );
      const rawULenEarly = Math.hypot(rawU[0], rawU[1], rawU[2]);
      const allSceneSegsEarly = sceneContext ? doanDaVe(sceneContext.objects) : [];
      let futureArmAlongRawU: Vec3 | null = null;
      if (rawULenEarly > 1e-6) {
        for (const [p0, p1] of allSceneSegsEarly) {
          const d0x = p0[0] - cx, d0y = p0[1] - cy, d0z = p0[2] - cz;
          const d1x = p1[0] - cx, d1y = p1[1] - cy, d1z = p1[2] - cz;
          const l0 = Math.hypot(d0x, d0y, d0z);
          const l1 = Math.hypot(d1x, d1y, d1z);
          if (l0 <= 1e-6 && l1 > 1e-5) {
            if (Math.abs(d1x * rawU[0] + d1y * rawU[1] + d1z * rawU[2]) / (l1 * rawULenEarly) > 0.999) {
              futureArmAlongRawU = [d1x, d1y, d1z];
              break;
            }
          } else if (l1 <= 1e-6 && l0 > 1e-5) {
            if (Math.abs(d0x * rawU[0] + d0y * rawU[1] + d0z * rawU[2]) / (l0 * rawULenEarly) > 0.999) {
              futureArmAlongRawU = [d0x, d0y, d0z];
              break;
            }
          }
        }
      }
      const [ux, uy, uz] = validUTo && uToDiff
        ? uToDiff
        : futureArmAlongRawU
          ? futureArmAlongRawU
          : huongChanTheoDoanDaVe(footVec, rawU, rawV, diemNen, doanCoTrongCanh);
      const [vx, vy, vz] = rawV;
      const du = Math.hypot(ux, uy, uz);
      const dv = Math.hypot(vx, vy, vz);
      {
        const uUnit: Vec3 = [ux / du, uy / du, uz / du];
        const vUnit: Vec3 = [vx / dv, vy / dv, vz / dv];
        const coDoanTheoHuongU = doanCoTrongCanh.some(([p0, p1]) => {
          const d0x = p0[0] - cx, d0y = p0[1] - cy, d0z = p0[2] - cz;
          const d1x = p1[0] - cx, d1y = p1[1] - cy, d1z = p1[2] - cz;
          const l0 = Math.hypot(d0x, d0y, d0z);
          const l1 = Math.hypot(d1x, d1y, d1z);
          if (l0 <= 1e-6 && l1 > 1e-5) {
            return Math.abs(d1x * uUnit[0] + d1y * uUnit[1] + d1z * uUnit[2]) / l1 > 0.999;
          }
          if (l1 <= 1e-6 && l0 > 1e-5) {
            return Math.abs(d0x * uUnit[0] + d0y * uUnit[1] + d0z * uUnit[2]) / l0 > 0.999;
          }
          if (l0 > 1e-5 && l1 > 1e-5) {
            const cos01 = (d0x * d1x + d0y * d1y + d0z * d1z) / (l0 * l1);
            if (cos01 < -0.999) {
              return Math.abs(d0x * uUnit[0] + d0y * uUnit[1] + d0z * uUnit[2]) / l0 > 0.999;
            }
          }
          return false;
        });
        const closeU = Boolean(visibleStepObjects && doanCoTrongCanh.length > 0 && !coDoanTheoHuongU);
        const daiDoan = Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
        const s = Math.min(0.35, Math.max(0.12, 0.22 * daiDoan), PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * daiDoan);
        const hasGroundedSecondLeg = !visibleStepObjects || coDoanTheoHuongU || validUTo;
        const nhom = new THREE.Group();
        nhom.userData.voHan = false;
        nhom.add(duong);
        if (hasGroundedSecondLeg) {
          const lineMarker = dauGocVuong(
            [cx, cy, cz], uUnit, vUnit, s,
            PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * daiDoan, net(MAU.line), undefined, closeU,
          );
          (lineMarker.material as THREE.LineBasicMaterial).depthTest = false;
          lineMarker.renderOrder = 10;
          lineMarker.name = `perp_marker:${o.id}`;
          lineMarker.userData.perpMarker = true;
          const pw = o.perpendicular_witness;
          if (pw?.relation && pw.on) {
            (lineMarker.userData.gocVuongDonVi as GocVuongDonVi).nhomQuanHe = [pw.relation, pw.rule ?? "", pw.on].join("|");
          }
          if (pw?.from && pw.foot_id) (lineMarker.userData.gocVuongDonVi as GocVuongDonVi).dauMut = [pw.from, pw.foot_id];
          nhom.add(lineMarker);
        }
        if (validUTo && uToVecCandidate && !namTrenDoanDaVe(footVec, uToVecCandidate, doanCoTrongCanh)) {
          const witnessLeg = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([
              new THREE.Vector3(cx, cy, cz),
              new THREE.Vector3(uToVecCandidate[0], uToVecCandidate[1], uToVecCandidate[2]),
            ]),
            new THREE.LineDashedMaterial({
              color: net(MAU.line),
              dashSize: coNetDut,
              gapSize: coNetDut * PHONG_CACH_SCENE3D.dash.witnessGapRatio,
              depthTest: false,
              depthWrite: false,
              transparent: true,
              opacity: DO_DUC.witness,
            }),
          );
          witnessLeg.computeLineDistances();
          witnessLeg.name = `witness_leg:${o.id}`;
          witnessLeg.userData.witness_leg = true;
          witnessLeg.userData.semanticLineRole = "perpendicular_witness";
          witnessLeg.userData.interactionState = interactionMode;
          witnessLeg.renderOrder = 10;
          witnessLeg.raycast = () => {};
          nhom.add(witnessLeg);
        }
        const secondW = chungChi.second;
        if (
          secondW?.foot
          && secondW.marker?.u
          && secondW.marker?.v
          && nhanChungDoanHopLe(secondW, [a.x, a.y, a.z], [b.x, b.y, b.z])
        ) {
          const footVec2 = toVec3(secondW.foot);
          const rawU2 = toVec3(secondW.marker.u);
          const rawV20 = toVec3(secondW.marker.v);
          const flipV2 =
            rawV20[0] * (segMid[0] - footVec2[0])
              + rawV20[1] * (segMid[1] - footVec2[1])
              + rawV20[2] * (segMid[2] - footVec2[2])
            < -1e-9;
          const rawV2: [number, number, number] = flipV2
            ? [-rawV20[0], -rawV20[1], -rawV20[2]]
            : rawV20;
          const [cx2, cy2, cz2] = footVec2;
          const [ux2, uy2, uz2] = huongChanTheoDoanDaVe(footVec2, rawU2, rawV2, diemNen, doanCoTrongCanh);
          const [vx2, vy2, vz2] = rawV2;
          const du2 = Math.hypot(ux2, uy2, uz2);
          const dv2 = Math.hypot(vx2, vy2, vz2);
          if (du2 > 1e-9 && dv2 > 1e-9) {
            const lineMarker2 = dauGocVuong(
              [cx2, cy2, cz2], [ux2 / du2, uy2 / du2, uz2 / du2], [vx2 / dv2, vy2 / dv2, vz2 / dv2], s,
              PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * daiDoan, net(MAU.line),
            );
            (lineMarker2.material as THREE.LineBasicMaterial).depthTest = false;
            lineMarker2.renderOrder = 10;
            lineMarker2.name = `perp_marker_2:${o.id}`;
            lineMarker2.userData.perpMarker = true;
            nhom.add(lineMarker2);
          }
        }
        return finishBuilt(nhom, `segment:${o.id}`);
      }
    }

    return finishBuilt(duong, `segment:${o.id}`);
  }

  if (o.render === "surface" && o.point && o.normal) {
    const diemMp = toVec3(o.point);
    const phapTuyen = toVec3(o.normal);
    if (Math.hypot(...phapTuyen) <= 1e-9) return null;
    const daGiacNghienCuu =
      boundedPlanePolygon && boundedPlanePolygon.length >= 3
        ? boundedPlanePolygon
        : sceneContext && o.type === "plane3"
          ? computeBoundedStudiedPlanePolygon(sceneContext, o, sceneContext.objects)
          : [];
    const daGiac = daGiacNghienCuu.length >= 3 ? daGiacNghienCuu : daGiacMatPhang(diemMp, phapTuyen, diemNen);
    const daGiacMoRong = daGiacNghienCuu.length >= 3 ? null : moRongDaGiacMatPhang(diemMp, phapTuyen, diemNen, daGiac);
    const laChonTrucTiepMp = noiBat === true || noiBat === "dich";
    const planeStyle = sceneContext && o.type === "plane3"
      ? resolveStudiedPlaneVisualStyle(sceneContext, o, sceneContext.objects, laChonTrucTiepMp)
      : null;
    const planeOpacityFactor = planeStyle?.opacityScale ?? 1;
    const continuousPlaneBorder = Boolean(planeStyle?.continuousPlaneBorder);
    const mauMp = nen(planeStyle ? planeStyle.fillColor : MAU.surface);
    const mauVienMp = net(planeStyle ? planeStyle.borderColor : MAU.planeOutline);
    const laMatPhangDocLap = !coThietDienDong;
    const doDucTamMp = (laChonTrucTiepMp
      ? DO_DUC.selectedPlane
      : interactionMode === "hover"
        ? 0.105
        : laMatPhangDocLap
          ? DO_DUC.standalonePlane
          : DO_DUC.plane) * planeOpacityFactor;
    const doDucVienMp = (laChonTrucTiepMp
      ? DO_DUC.selectedPlaneEdge
      : interactionMode === "hover"
        ? 0.90
        : laMatPhangDocLap
          ? DO_DUC.standalonePlaneEdge
          : DO_DUC.planeEdge) * (laChonTrucTiepMp ? 1 : Math.min(1, planeOpacityFactor + 0.12));
    const coNetDut = (beDayNet(diemNen, 1) / SECTION_STROKE_RATIO) * NET_DUT_TI_LE;
    const ganVienMatPhang = (target: THREE.Mesh, daGiacVien: Vec3[]) => {
      const ptsVien = daGiacVien.map((p) => new THREE.Vector3(...p));
      const vongVien = [...ptsVien, ptsVien[0]];
      const vienBanDau = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(vongVien),
        new THREE.LineBasicMaterial({
          color: mauVienMp,
          linewidth: NET.plane,
          transparent: true,
          opacity: doDucVienMp,
          depthTest: false,
        }),
      );
      vienBanDau.userData.hidden = false;
      vienBanDau.userData.continuousPlaneBorder = continuousPlaneBorder;
      vienBanDau.userData.interactionState = interactionMode;
      vienBanDau.name = `plane_border:${o.id}`;
      vienBanDau.userData.nonCanonicalBorderLine = true;
      vienBanDau.renderOrder = THU_TU_DUONG;
      target.add(vienBanDau);
      if (
        planeStyle
        && !coThietDienDong
        && daGiacNghienCuu.length === 0
        && planeStyle.coexistingCount >= 2
        && daGiacVien.length >= 4
      ) {
        const cIdx = planeStyle.rank % daGiacVien.length;
        const cPt = daGiacVien[cIdx];
        const prevPt = daGiacVien[(cIdx + daGiacVien.length - 1) % daGiacVien.length];
        const nextPt = daGiacVien[(cIdx + 1) % daGiacVien.length];
        const e1x = prevPt[0] - cPt[0], e1y = prevPt[1] - cPt[1], e1z = prevPt[2] - cPt[2];
        const e2x = nextPt[0] - cPt[0], e2y = nextPt[1] - cPt[1], e2z = nextPt[2] - cPt[2];
        const len1 = Math.hypot(e1x, e1y, e1z);
        const len2 = Math.hypot(e2x, e2y, e2z);
        if (len1 > 1e-4 && len2 > 1e-4) {
          const arcR = Math.min(len1, len2) * 0.135;
          const p1x = cPt[0] + (arcR / len1) * e1x;
          const p1y = cPt[1] + (arcR / len1) * e1y;
          const p1z = cPt[2] + (arcR / len1) * e1z;
          const p2x = cPt[0] + (arcR / len2) * e2x;
          const p2y = cPt[1] + (arcR / len2) * e2y;
          const p2z = cPt[2] + (arcR / len2) * e2z;
          const pmx = cPt[0] + 0.72 * ((arcR / len1) * e1x + (arcR / len2) * e2x);
          const pmy = cPt[1] + 0.72 * ((arcR / len1) * e1y + (arcR / len2) * e2y);
          const pmz = cPt[2] + 0.72 * ((arcR / len1) * e1z + (arcR / len2) * e2z);
          const arcPts: THREE.Vector3[] = [];
          for (let s = 0; s <= 10; s += 1) {
            const t = s / 10;
            const u = 1 - t;
            arcPts.push(new THREE.Vector3(
              u * u * p1x + 2 * u * t * pmx + t * t * p2x,
              u * u * p1y + 2 * u * t * pmy + t * t * p2y,
              u * u * p1z + 2 * u * t * pmz + t * t * p2z,
            ));
          }
          const cornerArc = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints(arcPts),
            new THREE.LineBasicMaterial({
              color: mauVienMp,
              linewidth: NET.plane,
              transparent: true,
              opacity: doDucVienMp * 0.72,
              depthTest: true,
            }),
          );
          cornerArc.name = `plane_corner_arc:${o.id}`;
          cornerArc.userData.voHan = true;
          cornerArc.userData.interactionState = interactionMode;
          cornerArc.renderOrder = THU_TU_DUONG;
          cornerArc.raycast = () => {};
          target.add(cornerArc);
        }
      }
      preallocateSpanGeoPool(target, Math.max(8, daGiacVien.length * 4));
      target.userData.nonCanonicalLoop = {
        objectId: o.id,
        pts: ptsVien,
        closed: true,
        color: mauVienMp,
        dashSize: coNetDut,
        highlighted: laChonTrucTiepMp,
        interactionState: interactionMode,
        renderOrder: THU_TU_DUONG,
        yieldColinear: true,
        isPlaneBorder: true,
        continuousPlaneBorder,
      } satisfies NonCanonicalLoopMeta;
    };
    const attachPlanePerpWitness = (planeObj: THREE.Object3D, wrapRotatedMesh = false): THREE.Object3D => {
      if (!sceneContext || o.type !== "plane3") return planeObj;
      const mpW = resolvePlanePerpendicularLineWitness(sceneContext, o, visibleStepObjects);
      if (!mpW) return planeObj;
      const [fx, fy, fz] = mpW.foot;
      const mpStepSegs = doanDaVe(visibleStepObjects ?? sceneContext.objects);
      const mpAlignedU = huongChanTheoDoanDaVe(mpW.foot, mpW.uUnit, mpW.vUnit, diemNen, mpStepSegs);
      const mpULen = Math.hypot(mpAlignedU[0], mpAlignedU[1], mpAlignedU[2]);
      if (mpULen <= 1e-6) return planeObj;
      const mpGroundedU: Vec3 = [mpAlignedU[0] / mpULen, mpAlignedU[1] / mpULen, mpAlignedU[2] / mpULen];
      const hasGroundedPlaneArm = mpStepSegs.some(([p0, p1]) => {
        const d0x = p0[0] - fx, d0y = p0[1] - fy, d0z = p0[2] - fz;
        const d1x = p1[0] - fx, d1y = p1[1] - fy, d1z = p1[2] - fz;
        const l0 = Math.hypot(d0x, d0y, d0z);
        const l1 = Math.hypot(d1x, d1y, d1z);
        if (l0 <= 1e-6 && l1 > 1e-5) {
          return Math.abs(d1x * mpGroundedU[0] + d1y * mpGroundedU[1] + d1z * mpGroundedU[2]) / l1 > 0.999;
        }
        if (l1 <= 1e-6 && l0 > 1e-5) {
          return Math.abs(d0x * mpGroundedU[0] + d0y * mpGroundedU[1] + d0z * mpGroundedU[2]) / l0 > 0.999;
        }
        if (l0 > 1e-5 && l1 > 1e-5) {
          const cos01 = (d0x * d1x + d0y * d1y + d0z * d1z) / (l0 * l1);
          if (cos01 < -0.999) {
            return Math.abs(d0x * mpGroundedU[0] + d0y * mpGroundedU[1] + d0z * mpGroundedU[2]) / l0 > 0.999;
          }
        }
        return false;
      });
      if (!hasGroundedPlaneArm) return planeObj;
      const sMp = Math.min(0.35, Math.max(0.12, 0.22 * mpW.spanLen), PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * mpW.spanLen);
      const mpMarker = dauGocVuong(
        mpW.foot,
        mpGroundedU,
        mpW.vUnit,
        sMp,
        PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * mpW.spanLen,
        net(MAU.line),
      );
      (mpMarker.material as THREE.LineBasicMaterial).depthTest = false;
      mpMarker.renderOrder = 10;
      mpMarker.name = `perp_marker:${o.id}`;
      mpMarker.userData.perpMarker = true;
      if (wrapRotatedMesh) {
        const grp = new THREE.Group();
        grp.userData.voHan = true;
        grp.add(planeObj, mpMarker);
        return grp;
      }
      planeObj.add(mpMarker);
      return planeObj;
    };
    if (daGiac && daGiac.length >= 3) {
      const pos: number[] = [];
      for (const [a, b, c] of chiaTamGiac(daGiac)) {
        for (const j of [a, b, c]) pos.push(...daGiac[j]);
      }
      if (pos.length > 0) {
        const coMoRong = Boolean(daGiacMoRong && daGiacMoRong.length >= 3);
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        g.computeVertexNormals();
        const m = new THREE.MeshBasicMaterial({
          color: mauMp,
          transparent: true,
          opacity: coMoRong ? 0 : (laChonTrucTiepMp ? DO_DUC.selectedPlaneCore : (laMatPhangDocLap ? DO_DUC.standalonePlane : DO_DUC.planeCore) * planeOpacityFactor),
          forceSinglePass: true,
          colorWrite: !coMoRong,
          side: THREE.DoubleSide,
          depthWrite: false,
          depthTest: false,
        });
        const mesh = new THREE.Mesh(g, m);
        mesh.renderOrder = 1;
        mesh.userData.voHan = true;
        if (daGiacMoRong && daGiacMoRong.length >= 3) {
          const posMoRong: number[] = [];
          for (const [a, b, c] of chiaTamGiac(daGiacMoRong)) {
            for (const j of [a, b, c]) posMoRong.push(...daGiacMoRong[j]);
          }
          if (posMoRong.length > 0) {
            const gMoRong = new THREE.BufferGeometry();
            gMoRong.setAttribute("position", new THREE.Float32BufferAttribute(posMoRong, 3));
            gMoRong.computeVertexNormals();
            const mMoRong = new THREE.MeshBasicMaterial({
              color: mauMp,
              transparent: true,
              opacity: doDucTamMp,
              forceSinglePass: true,
              side: THREE.DoubleSide,
              depthWrite: false,
              depthTest: false,
            });
            const mienMoRong = new THREE.Mesh(gMoRong, mMoRong);
            mienMoRong.name = `plane_sheet:${o.id}`;
            mienMoRong.renderOrder = 1;
            mienMoRong.userData.voHan = true;
            ganVienMatPhang(mienMoRong, daGiacMoRong);
            mesh.add(mienMoRong);
          }
        } else {
          ganVienMatPhang(mesh, daGiac);
        }
        return finishBuilt(attachPlanePerpWitness(mesh), `plane:${o.id}`);
      }
    }
    if (daGiacMoRong && daGiacMoRong.length >= 3) {
      const posMoRong: number[] = [];
      for (const [a, b, c] of chiaTamGiac(daGiacMoRong)) {
        for (const j of [a, b, c]) posMoRong.push(...daGiacMoRong[j]);
      }
      if (posMoRong.length > 0) {
        const gMoRong = new THREE.BufferGeometry();
        gMoRong.setAttribute("position", new THREE.Float32BufferAttribute(posMoRong, 3));
        gMoRong.computeVertexNormals();
        const mMoRong = new THREE.MeshBasicMaterial({
          color: mauMp,
          transparent: true,
          opacity: doDucTamMp,
          forceSinglePass: true,
          side: THREE.DoubleSide,
          depthWrite: false,
          depthTest: false,
        });
        const mesh = new THREE.Mesh(gMoRong, mMoRong);
        mesh.renderOrder = 1;
        mesh.userData.voHan = true;
        ganVienMatPhang(mesh, daGiacMoRong);
        return finishBuilt(attachPlanePerpWitness(mesh), `plane:${o.id}`);
      }
    }
    const khung = khungMatPhang(diemMp, phapTuyen, diemNen);
    const canh = khung ? khung.canh : PLANE_DISPLAY_SIZE;
    const g = new THREE.PlaneGeometry(canh, canh);
    const m = new THREE.MeshBasicMaterial({
      color: mauMp,
      transparent: true,
      opacity: laChonTrucTiepMp ? DO_DUC.selectedPlane : DO_DUC.plane,
      forceSinglePass: true,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(g, m);
    const n = new THREE.Vector3(...phapTuyen).normalize();
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    mesh.position.set(...(khung ? khung.tam : diemMp));
    mesh.userData.voHan = true;
    return finishBuilt(attachPlanePerpWitness(mesh, true), `plane:${o.id}`);
  }

  if (o.render === "circle" && o.center && o.normal && o.radius_sq) {
    const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
    const rawNormal = toVec3(o.normal);
    if (!(r > 1e-6) || Math.hypot(...rawNormal) <= 1e-9) return null;
    const circleRole = classifyCircleSemanticRole(sceneContext ?? { objects: [o] }, o);
    const thamChieu = circleRole === "REFERENCE_EQUATOR" || circleRole === "REFERENCE_GREAT_CIRCLE";
    const duongTronDay = circleRole === "BOUNDARY_AND_INTERSECTION";
    const laNoiTiep = circleRole === "INSCRIBED_CIRCLE";
    const laNgoaiTiep = circleRole === "CIRCUMSCRIBED_CIRCLE";
    const refStrokeScale = typeof (o as SceneObject & { _refStrokeScale?: number })._refStrokeScale === "number"
      ? (o as SceneObject & { _refStrokeScale?: number })._refStrokeScale!
      : 0.27;
    const heSoDay = thamChieu
      ? refStrokeScale
      : duongTronDay
        ? (noiBat ? 1.12 : 1) * 0.36
        : laNoiTiep || laNgoaiTiep
          ? (noiBat ? 1.10 : 1) * 0.30
          : (noiBat ? 1.12 : 1) * 0.40;
    const day = beDayNet(diemNen, r) * heSoDay;
    const ngoaiR = r;
    const trongR = Math.max(0, r - day);
    const mauVanh: THREE.Color | number = thamChieu
      ? net(0x475569)
      : laNoiTiep
        ? net(MAU.inscribed)
        : laNgoaiTiep
          ? net(MAU.circumscribedCircle)
          : duongTronDay
            ? net(MAU.canh)
            : netMien(mauVienMien);
    const chungVanh = {
      color: mauVanh, side: THREE.DoubleSide,
      forceSinglePass: true,
      ...LECH_THIET_DIEN,
    } as const;
    const nhomVanh = new THREE.Group();
    const coTo = o.fill_visible !== false && (o.surface_role as string | undefined) !== "BOUNDARY_CURVE" && !thamChieu && !laNgoaiTiep;
    if (coTo) {
      const bkTo = Math.max(2e-5, ngoaiR);
      const mauToTron = laNoiTiep ? MAU.inscribed : duongTronDay ? MAU.mesh : mauToMien;
      const doDucTron = laNoiTiep
        ? (interactionMode === "selected" ? 0.14 : interactionMode === "hover" ? 0.10 : DO_DUC.inscribedCircleFill)
        : duongTronDay
          ? (interactionMode === "selected" ? DO_DUC.selectedBase : DO_DUC.base)
          : doDucMien;
      const laMienDayHoacNoiTiep = duongTronDay || laNoiTiep;
      const to = new THREE.Mesh(
        new THREE.RingGeometry(1e-5, bkTo, VONG_CHIA),
        new THREE.MeshBasicMaterial(
          duongTronDay
            ? {
                color: nen(mauToTron),
                transparent: true,
                opacity: doDucTron,
                forceSinglePass: true,
                side: THREE.DoubleSide,
                depthWrite: false,
              }
            : {
                color: nen(mauToTron),
                transparent: true,
                opacity: doDucTron,
                forceSinglePass: true,
                side: THREE.DoubleSide,
                depthWrite: false,
                depthTest: !xray,
                depthFunc: THREE.LessEqualDepth,
                ...LECH_THIET_DIEN,
              },
        ),
      );
      to.name = `${laMienDayHoacNoiTiep ? "polygon_fill" : "section_fill"}:${o.id}`;
      if (!duongTronDay) to.renderOrder = THU_TU_TO_THIET_DIEN;
      nhomVanh.add(to);
    }
    const soDoanVanh = 128;
    const trongPts: THREE.Vector3[] = [];
    const ngoaiPts: THREE.Vector3[] = [];
    const midpoints: THREE.Vector3[] = [];
    for (let i = 0; i <= soDoanVanh; i += 1) {
      const t = (i / soDoanVanh) * Math.PI * 2;
      const cs = Math.cos(t), sn = Math.sin(t);
      trongPts.push(new THREE.Vector3(trongR * cs, trongR * sn, 0));
      ngoaiPts.push(new THREE.Vector3(ngoaiR * cs, ngoaiR * sn, 0));
      if (i < soDoanVanh) {
        const tm = ((i + 0.5) / soDoanVanh) * Math.PI * 2;
        midpoints.push(new THREE.Vector3(ngoaiR * Math.cos(tm), ngoaiR * Math.sin(tm), 0));
      }
    }
    const thay = new THREE.Mesh(
      new THREE.BufferGeometry(),
      new THREE.MeshBasicMaterial({ ...chungVanh, depthFunc: THREE.LessEqualDepth, transparent: true }),
    );
    thay.renderOrder = THU_TU_VE_THIET_DIEN;
    const khuat = new THREE.Mesh(
      new THREE.BufferGeometry(),
      new THREE.MeshBasicMaterial({
        ...chungVanh, depthFunc: THREE.GreaterDepth, depthWrite: false,
        ...(thamChieu ? { color: net(MAU.hiddenEdge) } : {}),
        transparent: true, opacity: DO_DUC.hiddenRim,
      }),
    );
    khuat.renderOrder = THU_TU_VE_THIET_DIEN;
    nhomVanh.add(thay, khuat);
    if (!thamChieu) {
      const proxyRing = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(ngoaiPts),
        new THREE.LineBasicMaterial({ colorWrite: false, depthWrite: false, transparent: true, opacity: 0 }),
      );
      proxyRing.name = `circle:${o.id}:proxy`;
      nhomVanh.add(proxyRing);
    }
    const rimMeta: CurvedRimLoopMeta = {
      objectId: o.id,
      rimRole: thamChieu
        ? "reference"
        : laNoiTiep
          ? "inscribed"
          : laNgoaiTiep
            ? "circumscribed"
            : duongTronDay
              ? "base"
              : "section",
      highlighted: Boolean(noiBat),
      interactionState: interactionMode,
      trong: trongPts,
      ngoai: ngoaiPts,
      midpoints,
      sample: turn => {
        const angle = turn * 2 * Math.PI, cs = Math.cos(angle), sn = Math.sin(angle);
        return { inner: new THREE.Vector3(trongR * cs, trongR * sn, 0), outer: new THREE.Vector3(ngoaiR * cs, ngoaiR * sn, 0) };
      },
      thayMesh: thay,
      khuatMesh: khuat,
      ...themNetVanh(nhomVanh, thay, khuat),
    };
    capNhatHinhHocVanhCong(rimMeta, [], false);
    nhomVanh.userData.curvedRimLoop = rimMeta;
    nhomVanh.userData.circleSceneSpec = {
      id: o.id,
      center: toVec3(o.center),
      normal: rawNormal,
      radius: r,
      isResultSection: !thamChieu && !duongTronDay && !laNoiTiep && !laNgoaiTiep,
    };
    const n = new THREE.Vector3(...rawNormal).normalize();
    nhomVanh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    nhomVanh.position.set(...toVec3(o.center));
    return finishBuilt(nhomVanh, `circle:${o.id}`);
  }

  if (
    o.render === "ellipse" && o.center && o.normal &&
    o.major_dir && o.minor_dir && o.semi_major_sq && o.semi_minor_sq
  ) {
    const a = Math.sqrt(Math.max(0, toNumber(o.semi_major_sq)));
    const b = Math.sqrt(Math.max(0, toNumber(o.semi_minor_sq)));
    if (!(a > 1e-6) || !(b > 1e-6)) return null;
    const rawM = toVec3(o.major_dir);
    const rawMin = toVec3(o.minor_dir);
    if (Math.hypot(...rawM) <= 1e-9 || Math.hypot(...rawMin) <= 1e-9) return null;
    const M = new THREE.Vector3(...rawM).normalize();
    const m = new THREE.Vector3(...rawMin).normalize();
    const n = new THREE.Vector3().crossVectors(M, m).normalize();
    const duongTronDay = vaiMien === "base";
    const day = beDayNet(diemNen, Math.max(a, b)) * (noiBat ? 0.56 : 0.46);
    const soDoanVanh = 128;
    const trong: THREE.Vector3[] = [];
    const ngoai: THREE.Vector3[] = [];
    const midpoints: THREE.Vector3[] = [];
    for (let i = 0; i <= soDoanVanh; i += 1) {
      const t = (i / soDoanVanh) * Math.PI * 2;
      const P = new THREE.Vector3()
        .addScaledVector(M, a * Math.cos(t))
        .addScaledVector(m, b * Math.sin(t));
      const tt = new THREE.Vector3()
        .addScaledVector(M, -a * Math.sin(t))
        .addScaledVector(m, b * Math.cos(t))
        .normalize();
      const ra = new THREE.Vector3().crossVectors(tt, n).normalize()
        .multiplyScalar(day);
      const pTrong = P.clone().sub(ra);
      trong.push(pTrong);
      ngoai.push(P);
      if (i < soDoanVanh) {
        const tm = ((i + 0.5) / soDoanVanh) * Math.PI * 2;
        midpoints.push(
          new THREE.Vector3()
            .addScaledVector(M, a * Math.cos(tm))
            .addScaledVector(m, b * Math.sin(tm)),
        );
      }
    }
    const dinhTo: number[] = [];
    for (let i = 0; i < soDoanVanh; i += 1) {
      const [t0, t1] = [ngoai[i], ngoai[i + 1]];
      dinhTo.push(0, 0, 0, t0.x, t0.y, t0.z, t1.x, t1.y, t1.z);
    }
    const hh = (ds: number[]) => {
      const bg = new THREE.BufferGeometry();
      bg.setAttribute("position", new THREE.Float32BufferAttribute(ds, 3));
      return bg;
    };
    const chungVanh = {
      color: netMien(mauVienMien), side: THREE.DoubleSide,
      forceSinglePass: true,
      ...LECH_THIET_DIEN,
    } as const;
    const nhomVanh = new THREE.Group();
    if (o.fill_visible !== false) {
      const gTo = hh(dinhTo);
      gTo.computeVertexNormals();
      const to = new THREE.Mesh(
        gTo,
        new THREE.MeshBasicMaterial({
          color: nen(mauToMien),
          transparent: true,
          opacity: doDucMien,
          forceSinglePass: true,
          side: THREE.DoubleSide,
          depthWrite: false,
          depthTest: !xray,
          depthFunc: THREE.LessEqualDepth,
          ...LECH_THIET_DIEN,
        }),
      );
      to.name = `section_fill:${o.id}`;
      to.renderOrder = THU_TU_TO_THIET_DIEN;
      nhomVanh.add(to);
    }
    const thay = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({
      ...chungVanh, depthFunc: THREE.LessEqualDepth, transparent: true,
    }));
    thay.renderOrder = THU_TU_VE_THIET_DIEN;
    const khuat = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({
      ...chungVanh, depthFunc: THREE.GreaterDepth, depthWrite: false,
      transparent: true, opacity: DO_DUC.hiddenRim,
    }));
    khuat.renderOrder = THU_TU_VE_THIET_DIEN;
    nhomVanh.add(thay, khuat);
    const ellipseProxy = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(ngoai),
      new THREE.LineBasicMaterial({ colorWrite: false, depthWrite: false, transparent: true, opacity: 0 }),
    );
    ellipseProxy.name = `ellipse:${o.id}:proxy`;
    nhomVanh.add(ellipseProxy);
    const rimMeta: CurvedRimLoopMeta = {
      objectId: o.id,
      rimRole: duongTronDay ? "base" : "section",
      highlighted: Boolean(noiBat),
      interactionState: interactionMode,
      trong,
      ngoai,
      midpoints,
      sample: turn => {
        const angle = turn * 2 * Math.PI, cs = Math.cos(angle), sn = Math.sin(angle);
        const outer = M.clone().multiplyScalar(a * cs).addScaledVector(m, b * sn);
        const tangent = M.clone().multiplyScalar(-a * sn).addScaledVector(m, b * cs).normalize();
        return { outer, inner: outer.clone().sub(new THREE.Vector3().crossVectors(tangent, n).normalize().multiplyScalar(day)) };
      },
      thayMesh: thay,
      khuatMesh: khuat,
      ...themNetVanh(nhomVanh, thay, khuat),
    };
    capNhatHinhHocVanhCong(rimMeta, [], false);
    nhomVanh.userData.curvedRimLoop = rimMeta;
    nhomVanh.position.set(...toVec3(o.center));
    return finishBuilt(nhomVanh, `ellipse:${o.id}`);
  }

  if (o.render === "curved_solid" && o.anchor && (o.rim_point || o.radius_sq) && o.curved_kind) {
    const tamVec = toVec3(o.anchor);
    const tam = new THREE.Vector3(...tamVec);
    const rFromSq = Math.sqrt(Math.max(0, toNumber(o.radius_sq ?? "0")));
    const r = rFromSq > 1e-6
      ? rFromSq
      : o.rim_point
        ? Math.hypot(...toVec3(o.rim_point).map((val, idx) => val - tamVec[idx]))
        : 0;
    const h = Math.sqrt(Math.max(0, toNumber(o.height_sq ?? "0")));
    if (!(r > 1e-6)) return null;
    const dinh = o.apex_or_top
      ? new THREE.Vector3(...toVec3(o.apex_or_top))
      : o.curved_kind !== "ball" && h > 0
        ? new THREE.Vector3(tam.x, tam.y, tam.z + h)
      : null;
    if (o.curved_kind !== "ball" && (!dinh || !(h > 1e-6 || o.apex_or_top))) return null;
    const sphereRole = o.curved_kind === "ball"
      ? classifySphereSemanticRole(sceneContext ?? { objects: [o] }, o)
      : "STANDALONE_SPHERE";
    const laCauNoiTiep = sphereRole === "INSCRIBED_SPHERE";
    const laCauNgoaiTiep = sphereRole === "CIRCUMSCRIBED_SPHERE";
    const mauVoCong = laCauNoiTiep
      ? MAU.inscribed
      : laCauNgoaiTiep
        ? MAU.circumscribedSphere
        : nen(mauKhoi);
    const doDucVoCong = laCauNoiTiep
      ? (interactionMode === "selected" ? 0.22 : interactionMode === "hover" ? 0.19 : DO_DUC.inscribedSphereShell)
      : laCauNgoaiTiep
        ? (interactionMode === "selected" ? 0.14 : interactionMode === "hover" ? 0.11 : DO_DUC.circumscribedSphereShell)
        : doDucKhoi;
    const hThuc = dinh ? Math.hypot(dinh.x - tam.x, dinh.y - tam.y, dinh.z - tam.z) : h;
    const baseCapCircle = o.curved_kind === "cylinder" && dinh && sceneContext?.objects
      ? sceneContext.objects.find((cand) => {
          if (cand.type !== "circle3" || cand.surface_role !== "BASE_REGION" || !cand.center || !cand.normal) return false;

          const cc = toVec3(cand.center);
          return Math.hypot(cc[0] - tam.x, cc[1] - tam.y, cc[2] - tam.z) <= 1e-4
            || Math.hypot(cc[0] - dinh.x, cc[1] - dinh.y, cc[2] - dinh.z) <= 1e-4;
        })
      : undefined;
    const obliqueCap = o.curved_kind === "cylinder" && dinh && baseCapCircle?.normal
      ? resolveObliqueCylinderCapBasis(tam, dinh, new THREE.Vector3(...toVec3(baseCapCircle.normal)))
      : null;
    let g: THREE.BufferGeometry;
    const nhomCong = new THREE.Group();
    let meshChinh: THREE.Mesh;
    if (o.curved_kind === "ball") {
      g = new THREE.SphereGeometry(r, VONG_CHIA, Math.round(VONG_CHIA / 2));
      const [thuTuSau, thuTuTruoc] = laCauNoiTiep
        ? [-0.6, -0.4]
        : laCauNgoaiTiep
          ? [-1.5, 0.5]
          : [-1, 0];
      const [voTruoc, voSau] = taoVoCauBaChieuHaiLuot(g, mauVoCong, doDucVoCong, thuTuTruoc, thuTuSau);
      voTruoc.position.copy(tam);
      voSau.position.copy(tam);
      nhomCong.add(voTruoc, voSau);
      meshChinh = voTruoc;
    } else if (obliqueCap && dinh) {
      g = buildObliqueCylinderGeometry(tam, dinh, obliqueCap.u1, obliqueCap.u2, r, VONG_CHIA);
      const m = new THREE.MeshBasicMaterial({
        color: mauVoCong,
        transparent: true,
        opacity: doDucVoCong,
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(g, m);
      mesh.userData.voKhoi = true;
      mesh.userData.baseShellOpacity = doDucVoCong;
      mesh.userData.obliqueCylinder = true;
      nhomCong.add(mesh);
      meshChinh = mesh;
    } else {
      // Nón/trụ giữ nguyên vỏ MeshBasicMaterial một lượt + đường sinh bao động.
      g = o.curved_kind === "cylinder"
        ? new THREE.CylinderGeometry(r, r, hThuc, VONG_CHIA)
        : new THREE.ConeGeometry(r, hThuc, VONG_CHIA);
      const m = new THREE.MeshBasicMaterial({
        color: mauVoCong,
        transparent: true,
        opacity: doDucVoCong,
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(g, m);
      mesh.userData.voKhoi = true;
      mesh.userData.baseShellOpacity = doDucVoCong;
      if (dinh) {
        const truc = dinh.clone().sub(tam).normalize();
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), truc);
        mesh.position.copy(tam).addScaledVector(truc, hThuc / 2);
      } else {
        mesh.position.copy(tam);
      }
      nhomCong.add(mesh);
      meshChinh = mesh;
    }
    const sphereMeta: CurvedSolidVolumeMeta = {
      id: o.id,
      kind: o.curved_kind as "cylinder" | "cone" | "ball",
      anchor: tam.clone(),
      top: dinh ? dinh.clone() : null,
      radius: r,
      height: hThuc,
      ...(obliqueCap ? { capBasis: [obliqueCap.u1.clone(), obliqueCap.u2.clone()] } : {}),
    };
    if (laCauNoiTiep || laCauNgoaiTiep) {
      // Mặt cầu nội/ngoại tiếp không ghi chiều sâu và không che khuất cạnh của khối chủ trong cảnh.
      nhomCong.userData.curvedSilhouetteVolume = sphereMeta;
    } else {
      const bong = lopChieuSau(g);
      bong.quaternion.copy(meshChinh.quaternion);
      bong.position.copy(meshChinh.position);
      const bongTruoc = lopChieuSauMatTruoc(g);
      bongTruoc.quaternion.copy(meshChinh.quaternion);
      bongTruoc.position.copy(meshChinh.position);
      nhomCong.add(bong, bongTruoc);
      nhomCong.userData.curvedSolidVolume = sphereMeta;
    }
    if (o.curved_kind === "ball") {
      // Theo matphang.html: KHÔNG vẽ đường bao viền đậm giả (sphere_silhouette) quanh mặt cầu;
      // khối cầu đọc tự nhiên qua bề mặt bán trong suốt 3D và đường tròn xích đạo tham chiếu 3D (trước liền, sau đứt).
      const refPolicy = resolveSphereReferenceGreatCirclePolicy(
        sceneContext ?? { objects: [o] },
        o,
        {
          auxiliaryShown: Boolean((o as SceneObject & { _auxiliaryShown?: boolean })._auxiliaryShown),
          visibleObjects: visibleStepObjects ?? sceneContext?.objects,
        },
      );
      if (sphereReference && refPolicy.visible) {
        const refObjSpec: SceneObject & { _refStrokeScale?: number } = {
          ...o,
          type: "circle3",
          render: "circle",
          center: refPolicy.center,
          normal: refPolicy.normal,
          radius_sq: refPolicy.radiusSq,
          surface_role: "BASE_REGION",
          fill_visible: false,
          display_role: "presentation_reference",
          semantic_role: "REFERENCE_GREAT_CIRCLE",
          _refStrokeScale: refPolicy.strokeScale,
        };
        const reference = buildObject3D(refObjSpec, false, banKinhBam, diemNen, cameraPosition, undefined, undefined, false, "primary", coThietDienDong, false, false, sceneContext);
        if (reference) {
          reference.name = `sphere_reference:${o.id}`;
          reference.userData.interactionState = interactionMode;
          reference.userData.presentationReference = {
            role: "REFERENCE_GREAT_CIRCLE",
            source_object_id: o.id,
            authoritative: false,
          };
          reference.userData.referenceGreatCirclePolicy = refPolicy;
          const eqRim = reference.userData.curvedRimLoop as CurvedRimLoopMeta | undefined;
          if (eqRim) {
            eqRim.interactionState = interactionMode;
            if (laCauNoiTiep) {
              const eqColor = net(MAU.inscribed);
              eqRim.visibilityMode = "all_dashed";
              (eqRim.thayMesh.material as THREE.MeshBasicMaterial).color.setHex(eqColor);
              (eqRim.khuatMesh.material as THREE.MeshBasicMaterial).color.setHex(eqColor);
              (eqRim.khuatMesh.material as THREE.MeshBasicMaterial).opacity = refPolicy.hiddenOpacity;
              const allDashedSpans = Array.from({ length: eqRim.midpoints.length }, (_, i) => ({ t0: i, t1: i + 1, hidden: true }));
              capNhatHinhHocVanhCong(eqRim, allDashedSpans, true);
            } else if (laCauNgoaiTiep) {
              const eqColor = net(MAU.circumscribedSphere);
              eqRim.selfOccludingSphere = sphereMeta;
              (eqRim.thayMesh.material as THREE.MeshBasicMaterial).color.setHex(eqColor);
              (eqRim.thayMesh.material as THREE.MeshBasicMaterial).opacity = refPolicy.frontOpacity;
              (eqRim.khuatMesh.material as THREE.MeshBasicMaterial).color.setHex(eqColor);
              (eqRim.khuatMesh.material as THREE.MeshBasicMaterial).opacity = refPolicy.hiddenOpacity;
            } else {
              eqRim.selfOccludingSphere = sphereMeta;
              (eqRim.thayMesh.material as THREE.MeshBasicMaterial).color.setHex(net(0x475569));
              (eqRim.thayMesh.material as THREE.MeshBasicMaterial).opacity = refPolicy.frontOpacity;
              (eqRim.khuatMesh.material as THREE.MeshBasicMaterial).color.setHex(net(MAU.hiddenEdge));
              (eqRim.khuatMesh.material as THREE.MeshBasicMaterial).opacity = refPolicy.hiddenOpacity;
            }
          }
          reference.traverse(child => { child.raycast = () => {}; });
          nhomCong.add(reference);
        }
      }
    } else if (dinh) {
      const phanSo = (v: THREE.Vector3) => v.toArray().map((x) => `${Math.round(x * 1e6)}/1000000`) as [string, string, string];
      const truc = dinh.clone().sub(tam);
      const phapTuyenVanh = obliqueCap ? obliqueCap.normal : truc;
      const tamVanh: [[string, string, string], THREE.Vector3][] = [[o.anchor, tam]];
      if (o.curved_kind === "cylinder") tamVanh.push([o.apex_or_top ?? phanSo(dinh), dinh]);
      for (const [center, tamSo] of tamVanh) {
        const rim = buildObject3D({
          ...o,
          type: "circle3",
          render: "circle",
          center,
          normal: phanSo(phapTuyenVanh),
          surface_role: "BASE_REGION",
          semantic_role: "BOUNDARY_AND_INTERSECTION",
          formation_roles: [],
          fill_visible: false,
        }, noiBat, banKinhBam, diemNen, cameraPosition, undefined, undefined, xray, vaiKhoi, coThietDienDong, sphereReference, false, sceneContext);
        if (!rim) continue;
        rim.traverse((child) => { child.raycast = () => {}; });
        rim.userData.vanhDayCua = { center: tamSo.toArray(), axis: phapTuyenVanh.toArray(), radius_sq: o.radius_sq };
        nhomCong.add(rim);
      }
      const outline = new THREE.Group();
      outline.name = `curved_silhouette:${o.id}`;
      outline.visible = false; // until `updateCurvedSolidSilhouette` places it for a camera
      for (let i = 0; i < 2; i++) {
        const line = new THREE.Line(createSpanPoolGeometry(), new THREE.LineBasicMaterial({
          color: net(MAU.canh), transparent: true, opacity: 1, depthWrite: false,
        }));
        line.userData.interactionState = interactionMode;
        line.name = `curved_generator:${o.id}:${i}`;
        line.renderOrder = THU_TU_DUONG;
        line.raycast = () => {};
        outline.add(line);
      }
      nhomCong.add(outline);
    }
    return finishBuilt(nhomCong, `curved:${o.id}:${o.curved_kind}`);
  }

  if (o.render === "mesh" && o.vertices && o.faces) {
    const dinh = o.vertices.map(toVec3);
    const tamKhoi: Vec3 = dinh.length > 0
      ? [
          dinh.reduce((s, p) => s + p[0], 0) / dinh.length,
          dinh.reduce((s, p) => s + p[1], 0) / dinh.length,
          dinh.reduce((s, p) => s + p[2], 0) / dinh.length,
        ]
      : [0, 0, 0];
    const pos: number[] = [];
    for (const f of o.faces) {
      const mat = f.map((j) => dinh[j]);
      for (const [a, b, c] of chiaTamGiac(mat)) {
        const pA = mat[a], pB = mat[b], pC = mat[c];
        const ux = pB[0] - pA[0], uy = pB[1] - pA[1], uz = pB[2] - pA[2];
        const vx = pC[0] - pA[0], vy = pC[1] - pA[1], vz = pC[2] - pA[2];
        const nx = uy * vz - uz * vy;
        const ny = uz * vx - ux * vz;
        const nz = ux * vy - uy * vx;
        const ox = pA[0] - tamKhoi[0], oy = pA[1] - tamKhoi[1], oz = pA[2] - tamKhoi[2];
        const tri = nx * ox + ny * oy + nz * oz < 0 ? [a, c, b] : [a, b, c];
        for (const k of tri) pos.push(...mat[k]);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    const nhom = new THREE.Group();
    nhom.add(...voKhoiHaiLuot(g, nen(mauKhoi), doDucKhoi));
    nhom.add(lopChieuSau(g));
    const audit = classifySolidEdgeVisibility(o, cameraPosition);
    const dashSize = beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE;
    for (const edge of canonicalEdgesOf(o)) {
      const mauQua = highlightedEdgeIds instanceof Map ? highlightedEdgeIds.get(edge.id) : undefined;
      const edgeHighlighted = Boolean(noiBat) || highlightedEdgeIds.has(edge.id);
      const baseEdgeColor = defaultEdgeColors.get(edge.id) ?? MAU.canh;
      const isEdgeHovered = !edgeHighlighted && (interactionMode === "hover" || hoveredEdgeIds.has(edge.id));
      const edgeState: "neutral" | "hover" | "selected" = highlightedEdgeIds.has(edge.id) || Boolean(noiBat)
        ? "selected"
        : isEdgeHovered
          ? "hover"
          : "neutral";
      const owner = new THREE.Group();
      owner.name = `edge:${edge.id}`;
      owner.userData.visualOwnerId = edge.id;
      owner.userData.canonicalEdge = edge;
      owner.userData.highlighted = edgeHighlighted;
      owner.userData.interactionState = edgeState;
      owner.userData.edgeColor = isEdgeHovered ? modulateSemanticColor(baseEdgeColor, "hover") : baseEdgeColor;
      owner.userData.highlightColor = mauQua ?? modulateSemanticColor(baseEdgeColor, edgeState);
      owner.userData.dashSize = dashSize;
      owner.userData.khuc = khucToSang.get(edge.id);
      preallocateSpanGeoPool(owner, 6);
      rebuildCanonicalEdgeOwner(owner, edge, audit.edge_spans);
      owner.userData.spanSignature = audit.edge_spans.filter((span) => span.edge_id === edge.id)
        .map((span) => `${span.visibility}:${span.t0}:${span.t1}`).join("|");
      nhom.add(owner);
    }
    nhom.userData.solidSceneObject = o;
    return finishBuilt(nhom, `solid:${o.id}`);
  }

  if (o.type === "face" && o.polygon && o.polygon.length >= 3) {
    const pts = o.polygon.map(toVec3);
    const pos: number[] = [];
    for (const [a, b, c] of chiaTamGiac(pts)) {
      for (const j of [a, b, c]) pos.push(...pts[j]);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    const hitProxy = o.display_role === "hit_proxy" && !noiBat;
    return finishBuilt(new THREE.Mesh(g, new THREE.MeshBasicMaterial(hitProxy ? {
      colorWrite: false,
      depthWrite: false,
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
    } : {
      color: nen(mauKhoi),
      transparent: true,
      opacity: interactionMode === "selected" ? DO_DUC.selectedFace : DO_DUC.face,
      forceSinglePass: true,
      side: THREE.DoubleSide,
      depthWrite: false,
    })), `face:${o.id}`);
  }

  if (o.type === "edge" && o.polygon && o.polygon.length === 2) {
    const g = new THREE.BufferGeometry().setFromPoints(
      o.polygon.map((x) => new THREE.Vector3(...toVec3(x))));
    const hitProxy = o.display_role === "hit_proxy";
    const edgeLine = new THREE.Line(g, new THREE.LineBasicMaterial(hitProxy ? {
      colorWrite: false, depthWrite: false, transparent: true, opacity: 0,
      linewidth: NET.pick,
    } : {
      color: net(MAU.line), linewidth: NET.border,
    }));
    edgeLine.userData.interactionState = interactionMode;
    return finishBuilt(edgeLine, `edge:${o.id}`);
  }

  if (o.render === "polygon" && (o.polygon || o.vertices)) {
    const rawPts = (o.polygon ?? o.vertices ?? []).map(toVec3);
    if (rawPts.length < 2) return null;
    if (o.display_role === "hit_proxy" && !noiBat) {
      const nhomProxy = new THREE.Group();
      if (rawPts.length >= 3) {
        const posProxy: number[] = [];
        for (const [a, b, c] of chiaTamGiac(rawPts)) {
          for (const j of [a, b, c]) posProxy.push(...rawPts[j]);
        }
        const gProxy = new THREE.BufferGeometry();
        gProxy.setAttribute("position", new THREE.Float32BufferAttribute(posProxy, 3));
        nhomProxy.add(new THREE.Mesh(gProxy, new THREE.MeshBasicMaterial({
          colorWrite: false, depthWrite: false, transparent: true, opacity: 0, side: THREE.DoubleSide,
        })));
      }
      return finishBuilt(nhomProxy, `polygon:${o.id}`);
    }
    const pts = rawPts.map((p) => new THREE.Vector3(...p));
    const vong = o.closed === false ? pts : [...pts, pts[0]];
    const gLine = new THREE.BufferGeometry().setFromPoints(vong);
    const mauVien = netMien(mauVienMien);
    const coNetDut = (beDayNet(diemNen, 1) / SECTION_STROKE_RATIO) * NET_DUT_TI_LE;
    const thietDien = o.type === "section";
    const daGiacPhu = o.type === "polygon3" && laThietDien;
    const toXuyenKhoi = thietDien || daGiacPhu;
    const thuTuVien = toXuyenKhoi ? THU_TU_VE_THIET_DIEN : THU_TU_DUONG;
    const doDayVien = noiBat ? NET.selected : NET.border;
    const chungVien = {
      color: mauVien,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
    } as const;
    const line = new THREE.Line(gLine, new THREE.LineBasicMaterial({
      ...chungVien, linewidth: doDayVien, depthFunc: THREE.LessEqualDepth, depthWrite: false,
    }));
    line.name = `polygon_border:${o.id}:thay`;
    line.userData.nonCanonicalBorderLine = true;
    line.userData.interactionState = interactionMode;
    line.renderOrder = thuTuVien;
    const lineKhuat = new THREE.Line(gLine.clone(), new THREE.LineDashedMaterial({
      ...chungVien, linewidth: doDayVien, depthFunc: THREE.GreaterDepth, depthWrite: false,
      dashSize: coNetDut, gapSize: coNetDut * PHONG_CACH_SCENE3D.dash.gapRatio, transparent: true, opacity: DO_DUC.hiddenEdge,
    }));
    lineKhuat.computeLineDistances();
    lineKhuat.name = `polygon_border:${o.id}:khuat`;
    lineKhuat.userData.nonCanonicalBorderLine = true;
    lineKhuat.userData.hidden = true;
    lineKhuat.userData.interactionState = interactionMode;
    lineKhuat.renderOrder = thuTuVien;
    const ownsBoundary = !(
      o.surface_role === "BASE_REGION"
      && o.occludes_edges === false
      && (o.boundary_edge_ids?.length ?? 0) > 0
    );
    const nhom = new THREE.Group();
    if (auxiliaryExplanatorySurface) {
      nhom.userData.semanticLineRole = "auxiliary_line";
      line.userData.semanticLineRole = "auxiliary_line";
      lineKhuat.userData.semanticLineRole = "auxiliary_line";
    } else if (vaiMien === "base") {
      nhom.userData.semanticLineRole = "solid_edge";
      line.userData.semanticLineRole = "solid_edge";
      lineKhuat.userData.semanticLineRole = "solid_edge";
    }
    if (ownsBoundary) {
      nhom.add(line, lineKhuat);
      preallocateSpanGeoPool(nhom, Math.max(8, pts.length * 4));
      nhom.userData.nonCanonicalLoop = {
        objectId: o.id,
        pts,
        closed: o.closed !== false,
        color: mauVien,
        dashSize: coNetDut,
        highlighted: Boolean(noiBat),
        interactionState: interactionMode,
        renderOrder: thuTuVien,
        yieldColinear: !toXuyenKhoi,
      } satisfies NonCanonicalLoopMeta;
    }

    if (o.closed !== false && o.fill_visible !== false && rawPts.length >= 3) {
      const pos: number[] = [];
      for (const [a, b, c] of chiaTamGiac(rawPts)) {
        for (const j of [a, b, c]) pos.push(...rawPts[j]);
      }
      if (pos.length > 0) {
        const gMesh = new THREE.BufferGeometry();
        gMesh.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        gMesh.computeVertexNormals();
        const mesh = new THREE.Mesh(gMesh, new THREE.MeshBasicMaterial({
          color: nen(mauToMien),
          transparent: true,
          opacity: doDucMien,
          forceSinglePass: true,
          side: THREE.DoubleSide,
          depthWrite: false,
          ...(toXuyenKhoi ? { ...LECH_THIET_DIEN, depthTest: !xray } : {}),
        }));
        mesh.name = `${thietDien ? "section_fill" : "polygon_fill"}:${o.id}`;
        if (toXuyenKhoi) mesh.renderOrder = THU_TU_TO_THIET_DIEN;
        nhom.add(mesh);
      }
    }

    return finishBuilt(nhom, `polygon:${o.id}`);
  }

  return null; // `readout` và mọi loại chưa vẽ được
}

/**
 * Tên `Object3D` → **id ngữ nghĩa**, hoặc `null` nếu không phải vật của cảnh.
 *
 * Mỗi `Object3D` mang tên `"<render>:<id>"` (`point:M`, `solid:chop`). Hàm này
 * là chỗ DUY NHẤT quy ước ấy được đọc ngược — tách ra để chọn-bằng-chuột kiểm
 * được mà **không cần WebGL**: raycast trả về một `Object3D`, phần còn lại
 * chỉ là bóc chuỗi.
 *
 * `id` có thể chứa dấu `:`? Không: nó là tên biến của chương trình. Nhưng hàm
 * vẫn cắt ở dấu `:` ĐẦU TIÊN để một tên lạ không làm mất phần đuôi.
 */
export function semanticIdOf(name: string | undefined | null): string | null {
  if (!name) return null;
  const i = name.indexOf(":");
  return i > 0 && i < name.length - 1 ? name.slice(i + 1) : null;
}

/** Leo lên cha cho tới khi gặp một vật có id ngữ nghĩa. */
export function pickSemanticId(o: THREE.Object3D | null): string | null {
  for (let x: THREE.Object3D | null = o; x; x = x.parent) {
    const id = semanticIdOf(x.name);
    if (id) return id;
  }
  return null;
}

/** Hover is a draw-time material change; pooled materials retain their baseline for visibility updates. */
export function applyHoverFeedback(
  root: THREE.Object3D, hoveredId: string | null, edgeIds: ReadonlySet<string>,
): () => void {
  const undo: (() => void)[] = [];
  const touched = new Set<THREE.Material>();
  if (hoveredId) root.traverse((node) => {
    let matches = false;
    for (let p: THREE.Object3D | null = node; p && p !== root; p = p.parent) {
      if (p.userData.interactionState === "selected") return;
      const id = semanticIdOf(p.name);
      if (id === hoveredId || (id && edgeIds.has(id))) matches = true;
    }
    if (!matches) return;
    const previous = node.userData.interactionState;
    node.userData.interactionState = "hover";
    undo.push(() => {
      if (previous === undefined) delete node.userData.interactionState;
      else node.userData.interactionState = previous;
    });
    const raw = (node as THREE.Mesh).material;
    for (const mat of raw ? (Array.isArray(raw) ? raw : [raw]) : []) {
      if (touched.has(mat) || mat.colorWrite === false) continue;
      touched.add(mat);
      const colored = mat as THREE.MeshBasicMaterial;
      if (colored.color && (!(node as THREE.Mesh).isMesh || node.userData.dauDinh)) {
        const color = colored.color.getHex();
        colored.color.setHex(modulateSemanticColor(color, "hover"));
        undo.push(() => colored.color.setHex(color));
      }
      if (mat.transparent && mat.opacity > 0 && mat.opacity < 1) {
        const opacity = mat.opacity;
        mat.opacity = Math.min(0.95, opacity * 1.15);
        undo.push(() => { mat.opacity = opacity; });
      }
    }
  });
  return () => { for (let i = undo.length - 1; i >= 0; i--) undo[i]!(); };
}

/**
 * Trong danh sách va chạm (đã sắp theo KHOẢNG CÁCH), chọn vật CỤ THỂ NHẤT.
 *
 * ─── HAI LẦN SAI, HAI LÝ DO KHÁC NHAU ───────────────────────────────────
 *
 * ① Bản đầu lấy thẳng `ids[0]`. Mặt của khối nằm ĐÚNG trên bề mặt khối nên
 *    tia trúng cả hai, và học sinh bấm vào mặt SAB thì hệ trả về cả hình chóp.
 * ② Bản sửa lấy "vật con đầu tiên" — và thế là ĐIỂM không bao giờ chọn được:
 *    một đỉnh nằm trên mặt khối, tia trúng cả điểm (gần hơn) lẫn mặt, mà luật
 *    ấy nhảy qua điểm để lấy mặt. Demo tay đo được: 0/144 cú bấm trúng điểm.
 *
 * Luật đúng giữ NGUYÊN thứ tự khoảng cách và chỉ **hạ bệ đúng một thứ**: một
 * KHỐI bị bỏ qua khi chính mặt/cạnh của nó cũng nằm trong danh sách. Không có
 * vật con nào thì khối vẫn chọn được như thường.
 */
export function chonCuThe(
  ids: string[],
  loaiCua?: (id: string) => string | undefined,
): string | null {
  if (ids.length === 0) return null;
  const cha = new Set(
    ids.map((x) => parentSolidOf(x)).filter((x): x is string => !!x),
  );
  if (!loaiCua) return ids.find((x) => !cha.has(x)) ?? ids[0];
  // Xếp theo HẠNG CỤ THỂ, giữ thứ tự khoảng cách trong cùng hạng. Một vật
  // chỉ vào danh sách khi tia THẬT SỰ trúng vùng bấm của nó, nên "ưu tiên
  // điểm" không bao giờ cướp được một mặt ở xa con trỏ.
  let tot = ids[0];
  let hang = hangCuThe(loaiCua(ids[0]));
  for (const x of ids.slice(1)) {
    const h = hangCuThe(loaiCua(x));
    if (h < hang) { tot = x; hang = h; }
  }
  return tot;
}

/**
 * Đặt vị trí TRÌNH BÀY = **vị trí gốc của vật CỘNG khoảng dịch bung hình**.
 *
 * ─── LỖI ĐÃ QUAN SÁT, VÀ NÓ LÀ CỦA TÔI ──────────────────────────────────
 *
 * Bản trước viết `obj.position.set(bd.translate…)` — **GHI ĐÈ**, không cộng.
 * Với hầu hết đối tượng điều đó vô hại: đường, mặt, khối, đa giác đều nướng
 * toạ độ vào `BufferGeometry`, nên `position` của chúng vốn là gốc.
 *
 * Nhưng ĐIỂM thì không: `buildObject3D` đặt cả nhóm tại `o.xyz`. Ghi đè bằng
 * đồng nhất thức `(0,0,0)` kéo **mọi điểm về gốc toạ độ**. `plane3` cũng vậy
 * (`mesh.position.set(...o.point)`).
 *
 * Triệu chứng khớp chính xác với thứ demo tay đo được: `A(0,0,0)` bấm được —
 * vì nó vốn ở gốc — còn `B(2,0,0)`, `C(2,2,0)`, `D(0,2,0)`, `S(0,0,2)` thì
 * không, và 2907 lượt bấm nhắm cũng không cứu được, vì chúng KHÔNG NẰM Ở CHỖ
 * lẽ ra chúng phải nằm. Đó không phải chuyện đích bấm nhỏ.
 *
 * ⚠️ MỘT thẩm quyền đặt vị trí, áp cho CẢ NHÓM: chấm nhìn thấy và hình cầu
 * bắt con trỏ là hai con của cùng một nhóm, nên chúng không thể lệch nhau.
 */
export function datViTriTrinhBay(
  obj: THREE.Object3D,
  bd: { translate: [number, number, number] },
): void {
  obj.position.set(
    obj.position.x + bd.translate[0],
    obj.position.y + bd.translate[1],
    obj.position.z + bd.translate[2],
  );
}

export type WebglLifecyclePhase = "healthy" | "recovering" | "failed";

export interface SceneCameraPose {
  position: [number, number, number];
  target: [number, number, number];
}

interface Props {
  scene: Scene3D;
  step: number;
  /** Cách nhìn hiện tại. Vắng ⇒ hiện mọi thứ, không bung — hành vi cũ. */
  interaction?: InteractionState;
  /** Bấm vào một vật. Vắng ⇒ khung 3D chỉ để xem. */
  onSelect?: (id: string | null) => void;
  /**
   * Tăng giá trị này để yêu cầu ĐẶT LẠI KHUNG NHÌN cho vừa hình.
   *
   * Là một con số chứ không phải một hàm, vì nơi gọi (nút "Xem lại toàn hình")
   * nằm ở component cha còn camera thuộc renderer. Truyền hàm xuống sẽ buộc
   * cha giữ một ref vào ruột renderer — đúng kiểu đảo hướng phụ thuộc mà bản
   * đồ kiến trúc cấm.
   */
  fitToken?: number;
  /** Tăng giá trị này để phát lại quá trình hình thành mặt cầu ở bước đang mở. */
  replayNonce?: number;
  /** Trạng thái đang phát tự động của thanh điều khiển bước (dùng để dừng ổn định hoạt ảnh hình thành khi bấm Tạm dừng). */
  isPlaying?: boolean;
  /** W18 §16.5: chế độ nhãn số đo trên hình. Vắng ⇒ gọn (dữ kiện + lựa chọn). */
  annotationView?: AnnotationView;
  /** W2 · D: công tắc «Hình phụ» — vắng/false ⇒ hình phụ xong nhiệm vụ và mặt phẳng chỉ để đo ẩn (`scene3d-auxiliary`). */
  auxiliaryShown?: boolean;
  /** W2 · F: lưới nền mảnh, mặc định TẮT; ngoài nhóm gốc ⇒ không vào occlusion, raycast hay khung nhìn. */
  gridShown?: boolean;
  xray?: boolean;
  shellShown?: boolean;
  planeShown?: boolean;
  sectionShown?: boolean;
  axesShown?: boolean;
  shellOpacityPct?: number;
  planeOpacityPct?: number;
  rightAnglesShown?: boolean;
  dashedHiddenShown?: boolean;
  webglFallbackNode?: ReactNode;
  webglRecoveringNode?: ReactNode;
  onWebglFailure?: (failed: boolean) => void;
  onWebglLifecycleChange?: (state: {
    phase: WebglLifecyclePhase;
    attempt: number;
    maxAttempts: number;
  }) => void;
  initialCameraPose?: SceneCameraPose | null;
  onCameraPoseChange?: (pose: SceneCameraPose) => void;
}

/** §16.7 — cạnh góc vuông của ký hiệu tại chân, theo độ dài đoạn tới chân, có trần (đơn vị cảnh). */
const NHAN_CHUNG_GOC = { tiLe: 0.12, toiDa: 0.24 };

/** Màu nhân chứng theo VAI: nhãn khoảng cách đang xét mang xanh "đang xét" (W12); đoạn vuông góc của điểm hình chiếu
 *  luôn hiện nên là ĐƯỜNG PHỤ — cùng màu với các đường phụ khác, không giành nghĩa "đang xét" (review, 2026-10-11). */
export function mauNhanChung(vai: WitnessShown["vai"]): number {
  return vai === "hinh_chieu" ? MAU.line : MAU_VAI_TRO.dich;
}

interface GocVuongDonVi {
  foot: Vec3; u: Vec3; v: Vec3; s0: number; maxWorld: number; cornerOwner: THREE.Object3D;
  /** Một quan hệ backend (`relation|rule|on`, vd mọi cạnh bên ⊥ đáy): mặc định chỉ một dấu đại diện (`datCoGocVuong`). */
  nhomQuanHe?: string;
  /** Id thực thể hai đầu mút của đoạn mang chứng chỉ (`from`, `foot_id`) — để đọc độ thấy của cạnh khối trùng nó. */
  dauMut?: [string, string];
  companionRay?: THREE.Object3D;
  companionRayMeta?: {
    foot: Vec3;
    dir: Vec3;
    baseLen: number;
    minRatio: number;
    maxWorldLen: number;
  };
}

/** Ký hiệu góc vuông dạng ô vuông HAI đoạn (`addRightAngleMarker` của HTML tham chiếu): `foot + s0·u`,
 *  `foot + s0·(u+v)`, `foot + s0·v` ở toạ độ cảnh. `u`, `v` là hai phương ĐƠN VỊ backend đã chứng nhận vuông góc —
 *  không suy luận gì ở đây. `s0` là cỡ dựng; `datCoGocVuong` co/giãn quanh chân theo pixel, không vượt `maxWorld`
 *  (một phần đoạn liên quan) để dấu không lấn ra ngoài cạnh của nó. */
function dauGocVuong(
  foot: Vec3, u: Vec3, v: Vec3, s0: number, maxWorld: number, color: number, cornerOwner?: THREE.Object3D, _closeBaseU = false,
): THREE.Line {
  const p = (a: number, b: number) =>
    new THREE.Vector3(foot[0] + s0 * (a * u[0] + b * v[0]), foot[1] + s0 * (a * u[1] + b * v[1]),
      foot[2] + s0 * (a * u[2] + b * v[2]));
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([p(1, 0), p(1, 1), p(0, 1)]),
    new THREE.LineBasicMaterial({ color, linewidth: NET.perpendicular, transparent: true }),
  );
  const goc = p(1, 1);
  line.userData = { foot, corner: [goc.x, goc.y, goc.z] as Vec3 };
  line.userData.gocVuongDonVi = { foot, u, v, s0, maxWorld: Math.max(s0, maxWorld), cornerOwner: cornerOwner ?? line } satisfies GocVuongDonVi;
  return line;
}

/** Khoá trùng của một dấu ở toạ độ THẾ GIỚI (sau phép tách/cô lập của cha): chân + cặp phương không phân biệt dấu. */
function khoaGocVuong(d: GocVuongDonVi, cha: THREE.Matrix4): string {
  const chuan = (p: Vec3) => {
    const q = new THREE.Vector3(...p).transformDirection(cha).toArray();
    const k = q.find((x) => Math.abs(x) > 1e-6) ?? 1;
    return q.map((x) => (Math.sign(k) * x).toFixed(3)).join(",");
  };
  const chan = new THREE.Vector3(...d.foot).applyMatrix4(cha).toArray();
  return [chan.map((x) => x.toFixed(4)).join(","), ...[chuan(d.u), chuan(d.v)].sort()].join("|");
}

/**
 * Cỡ ký hiệu vuông góc theo MÀN HÌNH: cạnh dấu ≈ `rightAngle.perCanvasHeight` × chiều cao khung, kẹp
 * [`minPx`, `maxPx`] (16–22 px). Co/giãn quanh chân, nhưng cỡ world không vượt `maxWorld` (một phần đoạn liên quan).
 * Cỡ điểm ảnh tỉ lệ nghịch với ĐỘ SÂU view-space của chân — phép chiếu của camera, không phép hình học nào trên
 * cảnh. Có `tamNhin` (đích OrbitControls): chỉ tính lại khi độ sâu của TÂM NHÌN đổi (thu phóng, đặt khung) — lúc chỉ
 * XOAY, cỡ world giữ nguyên nên toạ độ dấu đứng yên và nét dày không cấp phát lại buffer GPU mỗi khung (cổng
 * `scene3d-orbit-gate`, `capPhat = 0`). Hai dấu cùng chân và cùng cặp phương (toạ độ thế giới) ⇒ giữ dấu ĐẬM nhất
 * (dấu đang nhấn / không bị làm dịu), ẩn các dấu lặp; dấu dưới một tổ tiên ẩn không tranh khoá. Trả số dấu đang hiện.
 */
/** Đại diện đang hiện của mỗi nhóm quan hệ (theo gốc cảnh) — chỉ để giữ ổn định giữa các khung. */
const _daiDienGocVuong = new WeakMap<THREE.Object3D, Map<string, string>>();
/** Độ "mở" tối thiểu (diện tích chiếu / diện tích không co) để dấu đại diện còn đọc được: 0.15 ≈ cos 81°. */
export const DO_MO_TOI_THIEU = 0.15;

export function datCoGocVuong(
  roots: readonly THREE.Object3D[],
  cam: THREE.Camera,
  hCss: number,
  tamNhin?: THREE.Vector3,
  hienGocVuong = true,
): number {
  if (!hienGocVuong) {
    for (const r of roots) {
      r.traverse((node) => {
        if (node.userData?.gocVuongDonVi) {
          node.visible = false;
          const comp = (node.userData.gocVuongDonVi as GocVuongDonVi).companionRay;
          if (comp) comp.visible = false;
        }
      });
    }
    return 0;
  }
  const pc = cam as THREE.PerspectiveCamera;
  if (!pc.isPerspectiveCamera || !(hCss > 0)) return 0;
  const cfg = PHONG_CACH_SCENE3D.rightAngle;
  const px = Math.min(cfg.maxPx, Math.max(cfg.minPx, cfg.perCanvasHeight * hCss));
  const f = hCss / (2 * Math.tan((pc.fov * Math.PI) / 360));
  pc.updateMatrixWorld();
  const chan = new THREE.Vector3();
  const doSauTam = tamNhin ? -chan.copy(tamNhin).applyMatrix4(pc.matrixWorldInverse).z : null;
  const DONG_NHAT_MT = new THREE.Matrix4();
  // Lượt 1: gom ứng viên (khoá thế giới, độ đậm, tổ tiên có hiện không).
  const ungVien: { node: THREE.Object3D; d: GocVuongDonVi; khoa: string; dam: number; toTienHien: boolean }[] = [];
  for (const r of roots) {
    r.updateMatrixWorld(true);
    r.traverse((node) => {
      const d = node.userData?.gocVuongDonVi as GocVuongDonVi | undefined;
      if (!d) return;
      let toTienHien = !node.userData?.retiredByStepPolicy;
      if (toTienHien) {
        for (let p = node.parent; p; p = p.parent) if (!p.visible) { toTienHien = false; break; }
      }
      const mat = (node as THREE.Line).material as THREE.Material | undefined;
      ungVien.push({ node, d, khoa: khoaGocVuong(d, node.parent?.matrixWorld ?? DONG_NHAT_MT),
        dam: mat?.opacity ?? 1, toTienHien });
    });
  }
  // Lượt 2: mỗi khoá giữ MỘT dấu — dấu đậm nhất trong số dấu có tổ tiên hiện (hoà ⇒ dấu gặp trước).
  const thang = new Map<string, (typeof ungVien)[number]>();
  for (const c of ungVien) {
    if (!c.toTienHien) continue;
    const cu = thang.get(c.khoa);
    if (!cu || c.dam > cu.dam) thang.set(c.khoa, c);
  }
  // Lượt 3 (Owner 2026-10-26: ít dấu hơn, không xoá quan hệ): các dấu của CÙNG một quan hệ backend (`nhomQuanHe`,
  // vd bốn cạnh bên ⊥ đáy) ⇒ mặc định một dấu. Dấu của đoạn đang nhấn (bước hiện tại / đang chọn) luôn hiện; không
  // đoạn nào nhấn ⇒ một đại diện dễ đọc nhất: ưu tiên đoạn không khuất hoàn toàn, rồi ô vuông 3D THẬT chiếu ra "mở"
  // nhất (diện tích chiếu / diện tích không co ≈ |cos| giữa mặt phẳng dấu và tia nhìn — không đổi hình dấu). GIỮ đại
  // diện cũ trừ khi ứng viên khác mở hơn rõ (25 %), để dấu không nhảy góc khi xoay.
  const laNhanManh = (n: THREE.Object3D) =>
    Boolean(n.parent?.children.some((x) => (x.userData?.nonCanonicalSegment as { highlighted?: boolean } | undefined)?.highlighted));
  // Cạnh chuẩn KHUẤT HẲN theo phân loại của chính lượt thấy/khuất (`updateCanonicalEdgeVisibility` ghi lên gốc) — đoạn
  // trùng cạnh khối nhường nét cho cạnh ấy (`colinearCanonicalIds`), nên độ thấy của nó là của cạnh chuẩn.
  const canhKhuat = new Set(roots.flatMap((r) => [...((r.userData.hiddenCanonicalEdgeIds as Set<string> | undefined) ?? [])]));
  const capDinhKhuat = [...canhKhuat].flatMap((id) => {
    const cap = id.split("::edge:")[1]?.split("-");
    return cap?.length === 2 ? [cap.slice().sort().join("|")] : [];
  });
  const khuatHet = (c: (typeof ungVien)[number]) => {
    const duong = c.node.parent?.children.find((x) => x.userData?.nonCanonicalSegment);
    const khuc = duong?.children.filter((x) => x.userData?.nonCanonicalSpanLine && !x.name.endsWith(":proxy")) ?? [];
    if (khuc.length > 0) return khuc.every((x) => x.userData.hidden === true);
    const trung = (duong?.userData.colinearCanonicalIds as string[] | undefined) ?? [];
    if (trung.length > 0) return trung.every((id) => canhKhuat.has(id));
    // Đoạn đã nhường hẳn nét cho cạnh khối (vùng bấm, không tự phân loại): đọc cạnh khối có CÙNG hai đầu mút (id thực
    // thể backend `from`/`foot_id` của chứng chỉ) trong phân loại của lượt thấy/khuất.
    const dau = c.d.dauMut;
    return dau !== undefined && capDinhKhuat.includes(dau.slice().sort().join("|"));
  };
  const wCss = hCss * (pc.aspect || 1);
  const doMo = (c: (typeof ungVien)[number]) => {
    const m = c.node.parent?.matrixWorld ?? DONG_NHAT_MT;
    const F = new THREE.Vector3(...c.d.foot).applyMatrix4(m);
    const sau = -F.clone().applyMatrix4(pc.matrixWorldInverse).z;
    if (!(sau > 0)) return 0;
    const eps = 1e-3 * sau;                         // probe ≪ depth: the perspective linearisation error stays ≈ 0.1 %
    const diem = [F, new THREE.Vector3(...c.d.u).transformDirection(m).multiplyScalar(eps).add(F),
      new THREE.Vector3(...c.d.v).transformDirection(m).multiplyScalar(eps).add(F)]
      .map((p) => { const q = p.project(pc); return [(q.x * wCss) / 2, (q.y * hCss) / 2]; });
    const dt = Math.abs((diem[1][0] - diem[0][0]) * (diem[2][1] - diem[0][1]) - (diem[1][1] - diem[0][1]) * (diem[2][0] - diem[0][0]));
    return dt / (f * 1e-3) ** 2;
  };
  const theoNhom = new Map<string, (typeof ungVien)[number][]>();
  for (const c of thang.values()) {
    const k = c.d.nhomQuanHe;
    if (k) theoNhom.set(k, [...(theoNhom.get(k) ?? []), c]);
  }
  // Chân đã mang một dấu RIÊNG (không thuộc nhóm, vd đoạn vuông góc chung chân A): đại diện của một nhóm tránh chỗ đó —
  // hai ô vuông ở một đỉnh đọc như rác, không như một quan hệ. Khoá chân = phần đầu của `khoa` (toạ độ thế giới).
  const chanRieng = new Set([...thang.values()].filter((c) => !c.d.nhomQuanHe).map((c) => c.khoa.split("|")[0]));
  const truoc = roots[0] ? (_daiDienGocVuong.get(roots[0]) ?? new Map<string, string>()) : new Map<string, string>();
  if (roots[0]) _daiDienGocVuong.set(roots[0], truoc);
  const anTheoNhom = new Set<(typeof ungVien)[number]>();
  for (const [k, ds] of theoNhom) {
    if (ds.length < 2) continue;
    const nhan = ds.filter((c) => laNhanManh(c.node));
    let giu: (typeof ungVien)[number][];
    if (nhan.length > 0) giu = nhan;
    else {
      const hang = new Map(ds.map((c) => [c, { thay: khuatHet(c) ? 0 : 1, rieng: chanRieng.has(c.khoa.split("|")[0]) ? 0 : 1,
        mo: doMo(c) }]));
      const hon = (a: (typeof ds)[number], b: (typeof ds)[number]) => {
        const x = hang.get(a)!, y = hang.get(b)!;
        return x.thay !== y.thay ? x.thay > y.thay : x.rieng !== y.rieng ? x.rieng > y.rieng : x.mo > y.mo;
      };
      const tot = ds.reduce((a, b) => (hon(b, a) ? b : a));
      const cu = ds.find((c) => c.node.uuid === truoc.get(k));
      const giuCu = cu !== undefined && hang.get(cu)!.thay === hang.get(tot)!.thay && hang.get(cu)!.rieng === hang.get(tot)!.rieng
        && hang.get(tot)!.mo <= hang.get(cu)!.mo * 1.25;
      const chon = giuCu ? cu! : tot;
      truoc.set(k, chon.node.uuid);
      // Ngay cả dấu dễ đọc nhất cũng gần như nằm dọc tia nhìn (mặt phẳng dấu lệch < ~9° so với tia) ⇒ ô vuông bẹp thành
      // một vạch, không còn đọc được là góc vuông: mặc định không vẽ (không bao giờ thay bằng góc vuông màn hình giả).
      giu = hang.get(chon)!.mo >= DO_MO_TOI_THIEU ? [chon] : [];
    }
    for (const c of ds) if (!giu.includes(c)) anTheoNhom.add(c);
  }
  const camWorldEl = pc.matrixWorld.elements;
  const camX = camWorldEl[12], camY = camWorldEl[13], camZ = camWorldEl[14];
  const uTmp = new THREE.Vector3();
  const vTmp = new THREE.Vector3();
  const DO_MO_SUY_BIEN = 0.035;
  let hien = 0;
  for (const c of ungVien) {
    const { node, d } = c;
    let isEdgeOnDegenerate = false;
    if (thang.get(c.khoa) === c && !anTheoNhom.has(c)) {
      const mParent = node.parent?.matrixWorld ?? DONG_NHAT_MT;
      const fWorld = chan.set(...d.foot).applyMatrix4(mParent);
      const rx = fWorld.x - camX, ry = fWorld.y - camY, rz = fWorld.z - camZ;
      const rayLen = Math.hypot(rx, ry, rz);
      uTmp.set(...d.u).transformDirection(mParent);
      vTmp.set(...d.v).transformDirection(mParent);
      const nx = uTmp.y * vTmp.z - uTmp.z * vTmp.y;
      const ny = uTmp.z * vTmp.x - uTmp.x * vTmp.z;
      const nz = uTmp.x * vTmp.y - uTmp.y * vTmp.x;
      const nLen = Math.hypot(nx, ny, nz);
      if (rayLen > 1e-6 && nLen > 1e-6) {
        isEdgeOnDegenerate = Math.abs(rx * nx + ry * ny + rz * nz) / (rayLen * nLen) < DO_MO_SUY_BIEN;
      }
    }
    node.visible = thang.get(c.khoa) === c && !anTheoNhom.has(c) && !isEdgeOnDegenerate;
    if (d.companionRay) d.companionRay.visible = node.visible;
    if (!node.visible) continue;
    hien += 1;
    // Chỉ XOAY (độ sâu tâm nhìn, cỡ khung và vị trí cha không đổi) ⇒ giữ cỡ world đã đặt: không ghi toạ độ mới.
    const e = node.parent?.matrixWorld.elements;
    const khoaCo = doSauTam === null ? null
      : `${doSauTam.toFixed(6)}|${hCss}|${e ? [e[12], e[13], e[14]].map((x) => x.toFixed(6)).join(",") : ""}`;
    if (khoaCo !== null && node.userData.khoaCoGocVuong === khoaCo) continue;
    node.userData.khoaCoGocVuong = khoaCo;
    const doSau = -chan.set(...d.foot).applyMatrix4(node.parent?.matrixWorld ?? DONG_NHAT_MT)
      .applyMatrix4(pc.matrixWorldInverse).z;
    const effectiveMaxWorld = d.companionRayMeta
      ? Math.min(d.maxWorld, d.companionRayMeta.maxWorldLen / d.companionRayMeta.minRatio)
      : d.maxWorld;
    const k = doSau > 0 ? Math.min(effectiveMaxWorld, (px * doSau) / f) / d.s0 : 1;
    node.scale.setScalar(k);
    node.position.set(d.foot[0] * (1 - k), d.foot[1] * (1 - k), d.foot[2] * (1 - k));
    node.updateMatrixWorld(true);
    const s = k * d.s0;
    if (d.companionRay && d.companionRayMeta) {
      const targetRayLen = Math.min(
        d.companionRayMeta.maxWorldLen,
        Math.max(d.companionRayMeta.baseLen, s * d.companionRayMeta.minRatio),
      );
      const rayLine = d.companionRay as THREE.Line;
      const posAttr = rayLine.geometry?.getAttribute("position") as THREE.BufferAttribute | undefined;
      if (posAttr && posAttr.count >= 2) {
        posAttr.setXYZ(
          1,
          d.companionRayMeta.foot[0] + targetRayLen * d.companionRayMeta.dir[0],
          d.companionRayMeta.foot[1] + targetRayLen * d.companionRayMeta.dir[1],
          d.companionRayMeta.foot[2] + targetRayLen * d.companionRayMeta.dir[2],
        );
        posAttr.needsUpdate = true;
        rayLine.computeLineDistances();
      }
    }
    d.cornerOwner.userData.corner = [d.foot[0] + (d.u[0] + d.v[0]) * s, d.foot[1] + (d.u[1] + d.v[1]) * s,
      d.foot[2] + (d.u[2] + d.v[2]) * s];
  }
  return hien;
}

/** Đoạn HỮU HẠN đã vẽ của cảnh (cạnh khối, cạnh đa giác, đoạn thẳng) — để đoạn chứng minh không vẽ chồng lên chúng. */
const _camLocalParallelTmp = new THREE.Vector3();
export function capNhatDauSongSong(root: THREE.Object3D, cam: THREE.Camera): void {
  cam.updateMatrixWorld();
  root.updateMatrixWorld(true);
  const el = cam.matrixWorld.elements;
  _camLocalParallelTmp.set(el[12], el[13], el[14]);
  root.worldToLocal(_camLocalParallelTmp);
  root.traverse((node) => {
    const meta = node.userData?.parallelChevron as
      | { center: Vec3; dirUnit: Vec3; scale: number }
      | undefined;
    if (!meta) return;
    const line = node as THREE.Line;
    const pos = line.geometry?.getAttribute("position") as THREE.BufferAttribute | undefined;
    if (!pos || pos.count < 3) return;
    const [mcx, mcy, mcz] = meta.center;
    const [tx, ty, tz] = meta.dirUnit;
    const sc = meta.scale;
    const rx = _camLocalParallelTmp.x - mcx;
    const ry = _camLocalParallelTmp.y - mcy;
    const rz = _camLocalParallelTmp.z - mcz;
    const rLen = Math.hypot(rx, ry, rz);
    let wx = ty * rz - tz * ry;
    let wy = tz * rx - tx * rz;
    let wz = tx * ry - ty * rx;
    let wLen = Math.hypot(wx, wy, wz);
    if (rLen > 1e-6 && wLen / rLen < 0.14) {
      line.visible = false;
      return;
    }
    line.visible = line.userData?.retiredByStepPolicy !== true;
    if (wLen <= 1e-5) {
      const fbRx = 0;
      const fbRy = Math.abs(tz) > 0.9 ? 1 : 0;
      const fbRz = Math.abs(tz) > 0.9 ? 0 : 1;
      wx = ty * fbRz - tz * fbRy;
      wy = tz * fbRx - tx * fbRz;
      wz = tx * fbRy - ty * fbRx;
      wLen = Math.hypot(wx, wy, wz);
    }
    if (wLen <= 1e-6) return;
    wx /= wLen;
    wy /= wLen;
    wz /= wLen;
    pos.setXYZ(
      0,
      mcx - 0.46 * sc * tx + 0.64 * sc * wx,
      mcy - 0.46 * sc * ty + 0.64 * sc * wy,
      mcz - 0.46 * sc * tz + 0.64 * sc * wz,
    );
    pos.setXYZ(1, mcx + 0.46 * sc * tx, mcy + 0.46 * sc * ty, mcz + 0.46 * sc * tz);
    pos.setXYZ(
      2,
      mcx - 0.46 * sc * tx - 0.64 * sc * wx,
      mcy - 0.46 * sc * ty - 0.64 * sc * wy,
      mcz - 0.46 * sc * tz - 0.64 * sc * wz,
    );
    pos.needsUpdate = true;
  });
}

export function doanDaVe(objects: readonly SceneObject[]): [Vec3, Vec3][] {
  return objects.flatMap((o): [Vec3, Vec3][] => {
    if (o.type === "segment3") {
      if (o.endpoints?.length === 2) return [[toVec3(o.endpoints[0]), toVec3(o.endpoints[1])]];
      if (o.point_a && o.point_b) return [[toVec3(o.point_a), toVec3(o.point_b)]];
    }
    if (o.type === "line3" && o.point && o.direction) {
      const p = toVec3(o.point);
      const d = toVec3(o.direction);
      const dn = Math.hypot(d[0], d[1], d[2]);
      if (dn > 1e-9) {
        const half = LINE_DISPLAY_HALF_LENGTH;
        return [[
          [p[0] - (d[0] / dn) * half, p[1] - (d[1] / dn) * half, p[2] - (d[2] / dn) * half],
          [p[0] + (d[0] / dn) * half, p[1] + (d[1] / dn) * half, p[2] + (d[2] / dn) * half],
        ]];
      }
    }
    const dinh = (o.vertices ?? o.polygon)?.map(toVec3);
    if (!dinh) return [];
    const vong = o.type === "solid"
      ? (o.faces ?? [])
      : (o.type === "polygon3" || (o.type === "section" && o.closed !== false))
        ? [dinh.map((_, i) => i)]
        : [];
    return vong.flatMap((f) => f.map((i, k): [Vec3, Vec3] => [dinh[i], dinh[f[(k + 1) % f.length]]]));
  });
}

function huongChanTheoDoanDaVe(
  foot: Vec3,
  rawU: Vec3,
  rawV: Vec3,
  diemNen: Vec3[],
  doanCo: readonly [Vec3, Vec3][],
): Vec3 {
  const lenU = Math.hypot(rawU[0], rawU[1], rawU[2]);
  const lenV = Math.hypot(rawV[0], rawV[1], rawV[2]);
  if (lenU > 1e-9 && lenV > 1e-9 && doanCo.length > 0) {
    const arms: Vec3[] = [];
    for (const [p0, p1] of doanCo) {
      const d0: Vec3 = [p0[0] - foot[0], p0[1] - foot[1], p0[2] - foot[2]];
      const d1: Vec3 = [p1[0] - foot[0], p1[1] - foot[1], p1[2] - foot[2]];
      const l0 = Math.hypot(d0[0], d0[1], d0[2]);
      const l1 = Math.hypot(d1[0], d1[1], d1[2]);
      if (l0 <= 1e-6 && l1 > 1e-5) {
        arms.push(d1);
      } else if (l1 <= 1e-6 && l0 > 1e-5) {
        arms.push(d0);
      } else if (l0 > 1e-5 && l1 > 1e-5) {
        const cos01 = (d0[0] * d1[0] + d0[1] * d1[1] + d0[2] * d1[2]) / (l0 * l1);
        if (cos01 < -0.9999) {
          arms.push(l0 >= l1 ? d0 : d1);
        }
      }
    }
    const matchingArm = arms.find((arm) => {
      const la = Math.hypot(arm[0], arm[1], arm[2]);
      return la > 1e-5 && (arm[0] * rawU[0] + arm[1] * rawU[1] + arm[2] * rawU[2]) / (la * lenU) > 0.9999;
    });
    if (matchingArm) return rawU;
    const rawUAlreadyOnDrawnSeg = arms.some((arm) => {
      const la = Math.hypot(arm[0], arm[1], arm[2]);
      return la > 1e-5 && Math.abs(arm[0] * rawU[0] + arm[1] * rawU[1] + arm[2] * rawU[2]) / (la * lenU) > 0.9999;
    });
    if (!rawUAlreadyOnDrawnSeg) {
      let bestArm: Vec3 | null = null;
      let bestLen = -1;
      for (const arm of arms) {
        const la = Math.hypot(arm[0], arm[1], arm[2]);
        if (la <= 1e-5) continue;
        const cosV = Math.abs(arm[0] * rawV[0] + arm[1] * rawV[1] + arm[2] * rawV[2]) / (la * lenV);
        if (cosV <= 1e-4 && la > bestLen) {
          bestLen = la;
          bestArm = arm;
        }
      }
      if (bestArm) return bestArm;
    }
  }
  return huongChanVuongGoc(foot, rawU, diemNen, rawV);
}

/** Nhân chứng một khoảng cách: đoạn nét đứt từ điểm tới CHÂN backend phát + ký hiệu vuông góc dựng từ
 *  hai phương backend phát (`u`, `v`) — chỉ đổi độ dài để có cỡ ký hiệu, không suy luận hình học nào.
 *  Có `uTo` (Owner 2026-10-26): cạnh trong vật nhận của dấu chĩa ĐÚNG tới điểm có tên ấy, và đoạn chứng minh
 *  chân → điểm được vẽ (trừ khi nó đã là một đoạn của hình) — dấu nằm giữa hai đường thật, không lơ lửng.
 *  Chân trùng một điểm có tên đang vẽ (`diemCoTen`, vd chân A của SA ⊥ (ABCD)) ⇒ không thêm chấm chân: chấm thứ hai
 *  chồng lên góc dấu và tô đỉnh đề cho bằng màu điểm dẫn xuất. */
export function vatNhanChung(
  w: WitnessShown,
  diemNen: Vec3[] = [],
  mau?: number,
  diu = false,
  doanCo: readonly [Vec3, Vec3][] = [],
  diemCoTen: readonly Vec3[] = [],
): THREE.Group {
  const g = new THREE.Group();
  const tu = new THREE.Vector3(...w.from);
  const chan = new THREE.Vector3(...w.foot);
  const v = new THREE.Vector3(...w.v);
  const uHuong: Vec3 = w.uTo
    ? [w.uTo[0] - w.foot[0], w.uTo[1] - w.foot[1], w.uTo[2] - w.foot[2]]
    : huongChanTheoDoanDaVe(w.foot, w.u, w.v, diemNen, doanCo);
  const dk = duongKinhCanh(diemNen);
  const s = dk > 0
    ? Math.min(v.length() * 0.18, Math.max(v.length() * NHAN_CHUNG_GOC.tiLe, dk * 0.032), dk * 0.042, NHAN_CHUNG_GOC.toiDa)
    : Math.min(v.length() * NHAN_CHUNG_GOC.tiLe, NHAN_CHUNG_GOC.toiDa);
  const chuKy = dk > 0 ? Math.max(0.045, Math.min(0.16, dk * 0.034), s * 1.05) : Math.max(0.12, s * 1.05);
  const uDon = new THREE.Vector3(...uHuong).normalize();
  const vDon = v.clone().normalize();
  const mauNet = mau ?? mauNhanChung(w.vai);
  const doan = new THREE.Line(new THREE.BufferGeometry().setFromPoints([chan, tu]),
    new THREE.LineDashedMaterial({ color: mauNet, dashSize: chuKy, gapSize: chuKy * PHONG_CACH_SCENE3D.dash.witnessGapRatio, depthTest: false, transparent: true, opacity: DO_DUC.witness }));
  doan.computeLineDistances();
  // Ký hiệu vuông góc dựng ở cỡ `s`; `datCoGocVuong` co/giãn về pixel và cập nhật `corner` của nhóm.
  const daiNhanChung = Math.hypot(tu.x - chan.x, tu.y - chan.y, tu.z - chan.z);
  const goc = dauGocVuong([chan.x, chan.y, chan.z], [uDon.x, uDon.y, uDon.z], [vDon.x, vDon.y, vDon.z], s,
    PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * daiNhanChung, mauNet, g);
  (goc.material as THREE.LineBasicMaterial).depthTest = false;
  (goc.material as THREE.LineBasicMaterial).opacity = DO_DUC.witness;
  const gocDinh = chan.clone().addScaledVector(uDon, s).addScaledVector(vDon, s);
  const mauChan = mau ?? (w.vai === "khoang_cach" ? mauNet : MAU.derived);
  const chamChan = new THREE.Mesh(
    new THREE.SphereGeometry(BAN_KINH_NHIN, 16, 12),
    new THREE.MeshBasicMaterial({ color: mauChan, depthTest: false, transparent: true, opacity: DO_DUC.foot }),
  );
  chamChan.position.copy(chan);
  chamChan.userData.dauDinh = "thuong";
  const canhPhu: THREE.Line[] = [];
  if (w.uTo && !namTrenDoanDaVe(w.foot, w.uTo, doanCo)) {
    const chanToi = new THREE.Line(new THREE.BufferGeometry().setFromPoints([chan, new THREE.Vector3(...w.uTo)]),
      (doan.material as THREE.LineDashedMaterial).clone());
    chanToi.computeLineDistances();
    chanToi.name = `witness_leg:${w.id}`;
    chanToi.userData.witness_leg = true;
    canhPhu.push(chanToi);
  }
  // Đoạn chân → điểm đã là một đoạn của hình (góc vuông BC ⊥ (SAB) đặt trên cạnh BC): không vẽ bản nét đứt thứ hai.
  const doanCanVe = w.khongVeDoan || namTrenDoanDaVe(w.from, w.foot, doanCo) ? [] : [doan];
  const chanLaDiemCoTen = diemCoTen.some((p) => Math.hypot(p[0] - w.foot[0], p[1] - w.foot[1], p[2] - w.foot[2]) < 1e-9);
  for (const x of [...doanCanVe, ...canhPhu, goc, ...(chanLaDiemCoTen ? [] : [chamChan])]) {
    x.renderOrder = x === chamChan ? 11 : 10;
    x.raycast = () => {};                 // trình bày thuần: không bao giờ bắt cú bấm chọn vật
    g.add(x);
  }
  g.userData = {
    nhanChung: w.id,
    from: w.from,
    foot: w.foot,
    corner: [gocDinh.x, gocDinh.y, gocDinh.z] as Vec3,
  };
  if (diu) lamDiu(g, HE_SO_LAM_DIU);
  return g;
}

/** Vùng một lớp phủ khác đang che khung (`data-che-khung`: nút nổi, ô soi, ngăn kéo) — nhãn
 *  số đo không được nằm dưới nó. Toạ độ px trong khung `goc`. */
function vungCheKhung(goc: DOMRect): LabelRect[] {
  return Array.from(
    document.querySelectorAll<HTMLElement>(
      "[data-che-khung], #playback-pa-box, #floating-toolbar-3d, #canvas-mobile-prob-badge, #btn-reopen-dock-capsule",
    ),
  ).flatMap((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 ? [{ x: r.left - goc.left, y: r.top - goc.top, w: r.width, h: r.height }] : [];
  });
}

/**
 * Lưới định hướng không gian sư phạm (`Lưới nền`): thưa (`8×8` ô), nhạt dần từ tâm ra biên theo 3 vành bán kính
 * để không tạo viền cứng cắt khung và không có hai trục đậm giả hệ trục toạ độ ở giữa đáy.
 * Khi cảnh có mặt phẳng toán học đang hiện/được chọn, `heSoDiu < 1` hạ thêm độ đậm để mặt phẳng bài toán luôn nổi bật hơn.
 */
export function dungLuoiNenSuPham(diem: Vec3[], heSoDiu = 1): THREE.Group {
  const nhom = new THREE.Group();
  nhom.name = "luoi_nen_su_pham";
  if (diem.length === 0) return nhom;
  const lo = [0, 1, 2].map((i) => Math.min(...diem.map((p) => p[i])));
  const hi = [0, 1, 2].map((i) => Math.max(...diem.map((p) => p[i])));
  const spanXY = Math.max(hi[0] - lo[0], hi[1] - lo[1], 1);
  const spanZ = Math.max(hi[2] - lo[2], spanXY, 1);
  const banKinh = spanXY * 0.92;
  const cx = (lo[0] + hi[0]) / 2;
  const cy = (lo[1] + hi[1]) / 2;
  const z0 = lo[2] - spanZ * 0.012;
  const soO = 8;
  const soKhuc = 16;
  const vanh0: number[] = [];
  const vanh1: number[] = [];
  const vanh2: number[] = [];
  const themDoan = (x0: number, y0: number, x1: number, y1: number) => {
    for (let s = 0; s < soKhuc; s++) {
      const t0 = s / soKhuc;
      const t1 = (s + 1) / soKhuc;
      const ax = x0 + (x1 - x0) * t0;
      const ay = y0 + (y1 - y0) * t0;
      const bx = x0 + (x1 - x0) * t1;
      const by = y0 + (y1 - y0) * t1;
      const mx = (ax + bx) / 2 - cx;
      const my = (ay + by) / 2 - cy;
      const r = Math.hypot(mx, my) / banKinh;
      if (r > 1.06) continue;
      const mang = r <= 0.52 ? vanh0 : r <= 0.82 ? vanh1 : vanh2;
      mang.push(ax, ay, z0, bx, by, z0);
    }
  };
  for (let i = 0; i <= soO; i++) {
    const u = -banKinh + (2 * banKinh * i) / soO;
    themDoan(cx - banKinh, cy + u, cx + banKinh, cy + u);
    themDoan(cx + u, cy - banKinh, cx + u, cy + banKinh);
  }
  const taoVanh = (ten: string, ds: number[], mau: number, doDucGoc: number) => {
    if (ds.length === 0) return;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(ds, 3));
    const m = new THREE.LineBasicMaterial({
      color: mau,
      transparent: true,
      opacity: Number((doDucGoc * heSoDiu).toFixed(4)),
      depthWrite: false,
    });
    const l = new THREE.LineSegments(g, m);
    l.name = ten;
    l.renderOrder = -2;
    l.raycast = () => {};
    nhom.add(l);
  };
  taoVanh("luoi:trong", vanh0, MAU.grid, DO_DUC.gridInner);
  taoVanh("luoi:giua", vanh1, MAU.grid, DO_DUC.gridMiddle);
  taoVanh("luoi:ngoai", vanh2, MAU.gridOuter, DO_DUC.gridOuter);
  nhom.userData = {
    divisions: soO,
    z0,
    heSoDiu,
  };
  return nhom;
}

/**
 * Đặt vị trí nhãn điểm hướng ra ngoài tâm hình chiếu, đồng thời tránh các cạnh đi qua đỉnh
 * và ký hiệu góc vuông tại chân đường cao (như đỉnh A trong family04_derived_sub_pyramid).
 */
const THUONG_GIU_HUONG = 10;

/**
 * Owner 2026-10-26 (P5): khi va chạm THẬT buộc nhãn đổi chỗ, nhãn TRƯỢT tới chỗ mới thay vì nhảy — mỗi khung đi
 * `k` phần quãng còn lại của ĐỘ LỆCH so với điểm neo (điểm neo vẫn bám đúng điểm 3D), khớp hẳn khi còn < 0.5 px.
 * Nhãn mới xuất hiện (chưa có lệch cũ) đặt thẳng vào chỗ.
 */
export function lamMuotLechNhan(
  truoc: { dx: number; dy: number } | undefined, dich: { dx: number; dy: number }, k = 0.5,
): { dx: number; dy: number } {
  if (!truoc || Math.hypot(dich.dx - truoc.dx, dich.dy - truoc.dy) < 0.5) return dich;
  return { dx: truoc.dx + (dich.dx - truoc.dx) * k, dy: truoc.dy + (dich.dy - truoc.dy) * k };
}

export function tinhViTriNhanDiem(
  diem: readonly { id: string; x: number; y: number; w: number; h: number }[],
  canh2d: readonly { ax: number; ay: number; bx: number; by: number }[],
  gocVuong: readonly { fx: number; fy: number; cx: number; cy: number; tx?: number; ty?: number }[],
  /** Hướng (rad, màn hình) đã chọn ở khung trước, theo id — được cập nhật tại chỗ. Owner 2026-10-26 (P5): ứng viên gần
   *  hướng cũ được cộng tối đa `THUONG_GIU_HUONG` điểm, đủ để hai phía tương đương không đổi qua lại giữa các khung khi
   *  xoay, quá nhỏ để thắng một va chạm thật (phạt tới ~77 điểm khi đè lên nét). */
  huongTruoc?: Map<string, number>,
): Map<string, { x: number; y: number; duoi: boolean }> {
  const ra = new Map<string, { x: number; y: number; duoi: boolean }>();
  if (diem.length === 0) return ra;
  const cx = diem.reduce((s, p) => s + p.x, 0) / diem.length;
  const cy = diem.reduce((s, p) => s + p.y, 0) / diem.length;

  const kcDiemDoan = (px: number, py: number, ax: number, ay: number, bx: number, by: number) => {
    const abx = bx - ax, aby = by - ay;
    const lenSq = abx * abx + aby * aby;
    if (lenSq < 1e-6) return Math.hypot(px - ax, py - ay);
    const t = Math.max(0, Math.min(1, ((px - ax) * abx + (py - ay) * aby) / lenSq));
    return Math.hypot(ax + abx * t - px, ay + aby * t - py);
  };

  const deltas = [0, -0.36, 0.36, -0.74, 0.74, -1.14, 1.14, -1.57, 1.57, -2.05, 2.05, Math.PI];

  for (const p of diem) {
    const cw = Math.max(14, p.w || 18);
    const ch = Math.max(14, p.h || 18);
    let rx = p.x - cx;
    let ry = p.y - cy;
    const rLen = Math.hypot(rx, ry);
    if (rLen < 1e-3) {
      rx = 0;
      ry = -1;
    } else {
      rx /= rLen;
      ry /= rLen;
    }
    for (const g of gocVuong) {
      if (Math.hypot(g.fx - p.x, g.fy - p.y) < 10) {
        const gx = g.cx - p.x;
        const gy = g.cy - p.y;
        const gLen = Math.hypot(gx, gy) || 1;
        rx -= (gx / gLen) * 1.45;
        ry -= (gy / gLen) * 1.45;
      }
    }
    const norm = Math.hypot(rx, ry) || 1;
    rx /= norm;
    ry /= norm;

    const theta0 = Math.atan2(ry, rx);
    const dist = Math.hypot(cw * 0.5, ch * 0.5) + 7.5;
    let bestLx = p.x - cw / 2;
    let bestLy = p.y - 1.4 * ch;
    let bestScore = -Infinity;
    let bestTheta = theta0;
    const cu = huongTruoc?.get(p.id);

    for (const dTheta of deltas) {
      const theta = theta0 + dTheta;
      const ux = Math.cos(theta);
      const uy = Math.sin(theta);
      const mx = p.x + ux * dist;
      const my = p.y + uy * dist;
      const lx = mx - cw / 2;
      const ly = my - ch / 2;

      let score = (ux * rx + uy * ry) * 16;
      if (cu !== undefined) {
        const lech = Math.abs(Math.atan2(Math.sin(theta - cu), Math.cos(theta - cu)));
        score += THUONG_GIU_HUONG * Math.max(0, 1 - lech / 0.6);
      }

      for (const s of canh2d) {
        const dSeg = kcDiemDoan(mx, my, s.ax, s.ay, s.bx, s.by);
        if (dSeg < 16) {
          score -= (16 - dSeg) * 4.8;
        }
      }

      for (const g of gocVuong) {
        const dCorner = Math.hypot(mx - g.cx, my - g.cy);
        const dMid = Math.hypot(mx - (g.fx + g.cx) * 0.5, my - (g.fy + g.cy) * 0.5);
        const dMin = Math.min(dCorner, dMid);
        if (dMin < 20) {
          score -= (20 - dMin) * 7.5;
        }
        if (Math.hypot(g.fx - p.x, g.fy - p.y) < 10) {
          const gx = g.cx - p.x;
          const gy = g.cy - p.y;
          const gLen = Math.hypot(gx, gy) || 1;
          score -= (ux * (gx / gLen) + uy * (gy / gLen)) * 22;
        }
      }

      for (const q of diem) {
        if (q.id === p.id) continue;
        const dq = Math.hypot(mx - q.x, my - q.y);
        if (dq < 24) {
          score -= (24 - dq) * 4.0;
        }
      }

      if (score > bestScore) {
        bestScore = score;
        bestLx = lx;
        bestLy = ly;
        bestTheta = theta;
      }
    }

    huongTruoc?.set(p.id, bestTheta);
    ra.set(p.id, { x: bestLx, y: bestLy, duoi: bestLy > p.y });
  }
  return ra;
}

export function dungTrucOxyzSuPham(diem: Vec3[]): THREE.Group {
  const nhom = new THREE.Group();
  nhom.name = "truc_oxyz_su_pham";
  const maxDim = diem.length > 0
    ? Math.max(
        2.0,
        ...[0, 1, 2].map((i) => Math.max(...diem.map((p) => Math.abs(p[i])))),
      )
    : 3;
  const arrowH = Math.max(0.18, maxDim * 0.052);
  const arrowR = arrowH * 0.36;
  const specs: { ten: string; nhan: string; axisIdx: 0 | 1 | 2; dir: [number, number, number]; mau: number }[] = [
    { ten: "truc:Ox", nhan: "x", axisIdx: 0, dir: [1, 0, 0], mau: 0x475569 },
    { ten: "truc:Oy", nhan: "y", axisIdx: 1, dir: [0, 1, 0], mau: 0x475569 },
    { ten: "truc:Oz", nhan: "z", axisIdx: 2, dir: [0, 0, 1], mau: 0x475569 },
  ];
  const taoNhanTruc = (chu: string): THREE.Sprite | null => {
    if (typeof document === "undefined") return null;
    const canvas = document.createElement("canvas");
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.font = "italic 600 34px Georgia, 'Times New Roman', serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 4;
    ctx.strokeStyle = "rgba(246, 245, 242, 0.92)";
    ctx.strokeText(chu, 32, 32);
    ctx.fillStyle = "#334155";
    ctx.fillText(chu, 32, 32);
    const tex = new THREE.CanvasTexture(canvas);
    const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false, depthWrite: false });
    const sp = new THREE.Sprite(mat);
    const sc = Math.max(0.34, maxDim * 0.105);
    sp.scale.set(sc, sc, 1);
    sp.raycast = () => {};
    return sp;
  };
  for (const sc of specs) {
    const axisMax = diem.length > 0
      ? Math.max(1.2, ...diem.map((p) => Math.abs(p[sc.axisIdx])))
      : 2.2;
    const span = Math.min(axisMax * 1.16 + 0.28, maxDim * 1.12);
    const innerSpan = Math.min(axisMax * 0.86, span * 0.72);
    const negSpan = Math.min(axisMax * 0.24, 0.65);
    const dirVec = new THREE.Vector3(sc.dir[0], sc.dir[1], sc.dir[2]);
    const innerEnd = dirVec.clone().multiplyScalar(innerSpan);
    const posEnd = dirVec.clone().multiplyScalar(span);
    const negEnd = dirVec.clone().multiplyScalar(-negSpan);

    const gInner = new THREE.BufferGeometry().setFromPoints([negEnd, innerEnd]);
    const lInner = new THREE.Line(
      gInner,
      new THREE.LineDashedMaterial({
        color: 0x64748b,
        dashSize: Math.max(0.08, maxDim * 0.032),
        gapSize: Math.max(0.07, maxDim * 0.026),
        transparent: true,
        opacity: 0.46,
        depthWrite: false,
      }),
    );
    lInner.computeLineDistances();
    lInner.name = `${sc.ten}:am`;
    lInner.renderOrder = -1;
    lInner.raycast = () => {};
    nhom.add(lInner);

    const gPos = new THREE.BufferGeometry().setFromPoints([innerEnd, posEnd]);
    const lPos = new THREE.Line(
      gPos,
      new THREE.LineBasicMaterial({ color: sc.mau, transparent: true, opacity: 0.84, depthWrite: false }),
    );
    lPos.name = `${sc.ten}:duong`;
    lPos.renderOrder = -1;
    lPos.raycast = () => {};
    nhom.add(lPos);

    const cone = new THREE.Mesh(
      new THREE.ConeGeometry(arrowR, arrowH, 12),
      new THREE.MeshBasicMaterial({ color: sc.mau, transparent: true, opacity: 0.86, depthWrite: false }),
    );
    cone.position.copy(posEnd);
    cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dirVec);
    cone.name = `${sc.ten}:mui`;
    cone.raycast = () => {};
    nhom.add(cone);

    const sp = taoNhanTruc(sc.nhan);
    if (sp) {
      sp.position.copy(posEnd).addScaledVector(dirVec, arrowH * 0.9 + Math.max(0.15, maxDim * 0.045));
      sp.name = `${sc.ten}:nhan`;
      nhom.add(sp);
    }
  }
  return nhom;
}

const MAX_WEBGL_AUTO_RESTORES = 2;
const WEBGL_RESTORE_TIMEOUT_MS = 4500;

function hopLeCameraPose(pose: SceneCameraPose | null | undefined): pose is SceneCameraPose {
  if (!pose) return false;
  const { position: p, target: t } = pose;
  if (
    !Array.isArray(p)
    || p.length !== 3
    || !Array.isArray(t)
    || t.length !== 3
    || p.some((n) => !Number.isFinite(n) || Math.abs(n) > 1e4)
    || t.some((n) => !Number.isFinite(n) || Math.abs(n) > 1e4)
  ) {
    return false;
  }
  const dist = Math.hypot(p[0] - t[0], p[1] - t[1], p[2] - t[2]);
  return Number.isFinite(dist) && dist > 1e-3 && dist <= 500;
}

export const SPHERE_FORMATION_DURATION_MS = 1350;

const COMPACT_MATH_ATOM_SRC = String.raw`(?<![\p{L}\p{N}²³])(?:(?:[A-Za-z][A-Za-z0-9′'_²³]*|√)\((?:[^()\n]|\([^()\n]*\))*\)|[A-Za-z][A-Za-z0-9′'_]*_[A-Za-z0-9′']+|S(?:xq|tp|td)|\((?:[^()\n]|\([^()\n]*\))+\)|(?:\d+(?:\.\d+)?|[√π])[A-Za-z0-9′'_√π^°²³]*|[a-z][√π][A-Za-z0-9′'_√π^°²³]*|[A-ZĐ][A-ZĐ0-9′'°²³]*|[a-z])(?![\p{L}\p{N}²³])`;
const COMPACT_MATH_SIDE_SRC = String.raw`${COMPACT_MATH_ATOM_SRC}(?:\s*(?:\/|\*|·|\^|\+|-)\s*${COMPACT_MATH_ATOM_SRC})*`;

export const COMPACT_MATH_TOKEN_RE = new RegExp(
  `(${COMPACT_MATH_SIDE_SRC}(?:\\s*(?:⊥|∥|∩|=|≤|≥|≠)\\s*${COMPACT_MATH_SIDE_SRC})+|(?<![\\p{L}\\p{N}²³])\\([A-ZĐ0-9′']+\\s*;\\s*[^()\\n]+\\)(?![\\p{L}\\p{N}²³]))`,
  "gu",
);

function renderMathSuperscripts(segment: string, keyPrefix: string): ReactNode {
  return segment.split(/(\^-?\d+)/).map((part, idx) =>
    /^\^-?\d+$/.test(part) ? <sup key={`${keyPrefix}-${idx}`}>{part.slice(1)}</sup> : part,
  );
}

export function MathDisplay({ text }: { text: string }) {
  return (
    <>
      {text.split(COMPACT_MATH_TOKEN_RE).map((chunk, i) =>
        i % 2 === 1 ? (
          <span key={i} className="math-nowrap">
            {renderMathSuperscripts(chunk, `m${i}`)}
          </span>
        ) : (
          renderMathSuperscripts(chunk, `t${i}`)
        ),
      )}
    </>
  );
}

export interface CanvasObstacleRect {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

function collectCanvasObstacleRects(container: HTMLElement, r: DOMRect): CanvasObstacleRect[] {
  const host = container.closest(".stage-3d, .geo3d-host") ?? container.parentElement ?? container;
  return Array.from(
    host.querySelectorAll<HTMLElement>(
      "[data-che-khung], #playback-pa-box, #floating-toolbar-3d, #canvas-mobile-prob-badge, #btn-reopen-dock-capsule",
    ),
  ).flatMap((el) => {
    const br = el.getBoundingClientRect();
    if (br.width <= 0 || br.height <= 0) return [];
    const st = typeof window !== "undefined" ? window.getComputedStyle(el) : null;
    if (st && (st.display === "none" || st.visibility === "hidden" || Number(st.opacity) <= 0.05)) return [];
    return [{
      left: br.left - r.left,
      top: br.top - r.top,
      right: br.right - r.left,
      bottom: br.bottom - r.top,
    }];
  });
}

export function computeClampedCanvasTooltipPosition(
  relX: number,
  relY: number,
  tipWidth: number,
  tipHeight: number,
  stageWidth: number,
  stageHeight: number,
  obstacles: readonly CanvasObstacleRect[] = [],
): { x: number; y: number } {
  const pad = 8;
  const tw = Math.min(Math.max(1, tipWidth), Math.max(1, stageWidth - 2 * pad));
  const th = Math.min(Math.max(1, tipHeight), Math.max(1, stageHeight - 2 * pad));

  let x = relX + 16;
  if (x + tw > stageWidth - pad) {
    x = relX - tw - 16;
  }
  x = Math.max(pad, Math.min(stageWidth - tw - pad, x));

  let y = relY - th - 16;
  if (y < pad) {
    y = relY + 18;
  }
  y = Math.max(pad, Math.min(stageHeight - th - pad, y));

  const sortedObstacles = [...obstacles].sort((a, b) => b.top - a.top);
  for (let pass = 0; pass < sortedObstacles.length; pass += 1) {
    let adjusted = false;
    for (const obs of sortedObstacles) {
      const overlapsX = x < obs.right + 4 && x + tw > obs.left - 4;
      const overlapsY = y < obs.bottom + 4 && y + th > obs.top - 4;
      if (!overlapsX || !overlapsY) continue;
      if (obs.top - th - 8 >= pad && Math.abs(y - (obs.top - th - 8)) > 0.5) {
        y = obs.top - th - 8;
        adjusted = true;
      } else if (obs.bottom + 8 + th <= stageHeight - pad && Math.abs(y - (obs.bottom + 8)) > 0.5) {
        y = obs.bottom + 8;
        adjusted = true;
      }
    }
    if (!adjusted) break;
  }
  y = Math.max(pad, Math.min(stageHeight - th - pad, y));
  return { x: Math.round(x), y: Math.round(y) };
}

export function Scene3DWorkspace({
  scene, step, interaction, onSelect, fitToken = 0, replayNonce = 0, isPlaying = false, annotationView = DEFAULT_ANNOTATION_VIEW,
  auxiliaryShown = false, gridShown = false, xray = false,
  shellShown = true, planeShown = true, sectionShown = true, axesShown = false,
  shellOpacityPct, planeOpacityPct,
  rightAnglesShown = true, dashedHiddenShown = true,
  webglFallbackNode, webglRecoveringNode, onWebglFailure, onWebglLifecycleChange,
  initialCameraPose, onCameraPoseChange,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<THREE.Group | null>(null);
  const veRef = useRef<(() => void) | null>(null);
  const commitRenderDirtyRef = useRef(false);
  const scheduleCommitRender = () => {
    commitRenderDirtyRef.current = true;
  };
  const rightAnglesShownRef = useRef(rightAnglesShown);
  rightAnglesShownRef.current = rightAnglesShown;
  const dashedHiddenShownRef = useRef(dashedHiddenShown);
  dashedHiddenShownRef.current = dashedHiddenShown;
  const xrayRef = useRef(xray);
  xrayRef.current = xray;
  const onCameraPoseChangeRef = useRef(onCameraPoseChange);
  onCameraPoseChangeRef.current = onCameraPoseChange;
  const pendingRestoredCameraRef = useRef<SceneCameraPose | null>(
    hopLeCameraPose(initialCameraPose) ? initialCameraPose : null,
  );
  const prevFitTokenRef = useRef(fitToken);
  //: Đặt lại khung nhìn cho vừa hình. Giữ trong ref vì nó do vòng dựng cảnh
  //: tạo ra (cần `cam`, `controls`) nhưng được gọi từ ngoài vòng ấy.
  const vuaKhungRef = useRef<(() => void) | null>(null);
  const sceneRef = useRef(scene);
  sceneRef.current = scene;
  //: Hướng nhãn điểm của khung trước (`tinhViTriNhanDiem`), để nhãn không nhảy qua lại khi xoay; xoá khi đổi cảnh.
  const huongNhanRef = useRef(new Map<string, number>());
  //: Độ lệch nhãn ĐANG vẽ so với điểm neo (`lamMuotLechNhan`): nhãn trượt thay vì nhảy; xoá khi đổi cảnh.
  const lechNhanRef = useRef(new Map<string, { dx: number; dy: number }>());
  useEffect(() => { huongNhanRef.current.clear(); lechNhanRef.current.clear(); }, [scene]);
  const vaiKhoiTheoId = useMemo(() => vaiTroKhoi(scene), [scene]);
  const [webglPhase, setWebglPhase] = useState<WebglLifecyclePhase>("healthy");
  const [webglEpoch, setWebglEpoch] = useState(0);
  const webglRestoreCountRef = useRef(0);
  const webglTerminalLatchedRef = useRef(false);
  const prevSceneForRecoveryRef = useRef(scene);
  const webglFailed = webglPhase === "failed";
  useEffect(() => {
    if (prevSceneForRecoveryRef.current === scene) return;
    prevSceneForRecoveryRef.current = scene;
    webglRestoreCountRef.current = 0;
    if (webglPhase !== "healthy" || webglTerminalLatchedRef.current) {
      webglTerminalLatchedRef.current = false;
      setWebglPhase("healthy");
      setWebglEpoch((n) => n + 1);
    }
  }, [scene, webglPhase]);
  useEffect(() => {
    onWebglFailure?.(webglFailed);
  }, [webglFailed, onWebglFailure]);
  useEffect(() => {
    onWebglLifecycleChange?.({
      phase: webglPhase,
      attempt: webglRestoreCountRef.current,
      maxAttempts: MAX_WEBGL_AUTO_RESTORES,
    });
  }, [webglPhase, onWebglLifecycleChange]);
  const [hoveredObject, setHoveredObject] = useState<string | null>(null);
  const hoverFeedbackRef = useRef<{ id: string | null; edges: ReadonlySet<string> }>({ id: null, edges: new Set() });
  const [touchTooltipId, setTouchTooltipId] = useState<string | null>(null);
  // Drag hides the tooltip while hover feedback stays independent of geometry lifetime.
  const [dangKeoCanvas, setDangKeoCanvas] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const lastTooltipRelPosRef = useRef<{ relX: number; relY: number } | null>(null);
  useEffect(() => {
    setHoveredObject(null);
    setTouchTooltipId(null);
  }, [scene, step]);
  /* regular-triangular-pyramid-w01 — XOAY HIỂN THỊ: đáy chóp nghiêng (§18.2) về nằm ngang. Đồng nhất thức cho mọi cảnh
     có đáy ngang (mọi họ trước), nên các họ ấy không đổi một điểm ảnh. Áp lên nhóm gốc + nhóm nhân chứng; vị trí THẾ GIỚI
     của nhãn/khung nhìn/lưới đi qua cùng phép quay (`xoay`). Toạ độ cảnh không đổi. */
  const qHienThi = useMemo(() => quayHienThi(scene.objects), [scene]);
  const qRef = useRef(qHienThi);
  qRef.current = qHienThi;
  // exact-dimensions: T khung (cột-chính 4×4) của cảnh có `chart_metric` — chỉ cho ảnh chụp camera của bộ đo.
  const tRef = useRef<number[] | null>(null);
  tRef.current = maTranKhung4(scene);
  const buoc = clampStep(scene, step);
  const tuongTac = interaction ?? TRANG_THAI_DAU;
  const tuongTacRef = useRef(tuongTac);
  tuongTacRef.current = tuongTac;
  const hasSelection = Boolean(tuongTac?.selected_id);
  const pedSteps = useMemo(() => pedagogicalStepList(scene), [scene]);
  const activePedStep = useMemo(
    () => pedSteps.find((p) => buoc >= p.startAnchor && buoc <= p.anchor),
    [pedSteps, buoc],
  );
  const stepHighlightTargets = useMemo(
    () => computeStepHighlightTargets(scene, buoc, activePedStep?.startAnchor),
    [scene, buoc, activePedStep?.startAnchor],
  );
  const tapChon = useMemo(
    () => new Set(hasSelection ? highlightSet(scene, tuongTac.selected_id!, true) : []),
    [scene, hasSelection, tuongTac?.selected_id],
  );
  const tapNoiBat = useMemo(
    () =>
      hasSelection
        ? tapChon
        : new Set([...stepHighlightTargets.newIds, ...geometryHighlightedAt(scene, buoc)]),
    [hasSelection, tapChon, stepHighlightTargets, scene, buoc],
  );
  const prevStepSceneRef = useRef<{ scene: Scene3D; buoc: number }>({ scene, buoc });
  const stepEntranceRef = useRef<{
    startMs: number;
    durationMs: number;
    reducedMotion: boolean;
    step: number;
    newIds: string[];
    depIds: string[];
  }>({
    startMs: 0,
    durationMs: 0,
    reducedMotion: false,
    step: buoc,
    newIds: [...stepHighlightTargets.newIds].sort(),
    depIds: [...stepHighlightTargets.depIds].sort(),
  });
  const sphereFormationSpecs = useMemo(() => {
    const isFirstPedStep = pedSteps.length > 0 ? activePedStep === pedSteps[0] : buoc === 0;
    if (!isFirstPedStep) return [];
    const presentIds = new Set(objectsAt(scene, buoc).map((o) => o.id));
    const byId = new Map(scene.objects.map((o) => [o.id, o]));
    const specs: {
      ballId: string;
      radiusSegId: string | null;
      origin: Vec3;
      refPtId: string | null;
      segKey: string | null;
    }[] = [];
    for (const o of scene.objects) {
      if (o.type !== "curved_solid" || o.curved_kind !== "ball" || !o.anchor || !presentIds.has(o.id)) continue;
      if (classifySphereSemanticRole(scene, o) !== "STANDALONE_SPHERE") continue;
      const radCandId = `${o.id}__radius`;
      const radSeg = presentIds.has(radCandId)
        ? byId.get(radCandId)
        : scene.objects.find((cand) => {
            if (cand.type !== "segment3" || !presentIds.has(cand.id)) return false;
            return classifyCurvedSegmentRole(scene, cand)?.kind === "radius";
          });
      const origin = toVec3(o.anchor);
      let refPtId: string | null = null;
      let segKey: string | null = null;
      if (radSeg) {
        const epIds = radSeg.endpoint_ids?.length ? radSeg.endpoint_ids : (radSeg.depends ?? []);
        if (epIds.length === 2 && epIds[0] && epIds[1]) {
          segKey = epIds[0] < epIds[1] ? `${epIds[0]}|${epIds[1]}` : `${epIds[1]}|${epIds[0]}`;
        }
        for (const epId of epIds) {
          const pt = byId.get(epId);
          if (!pt || pt.type !== "point3" || !pt.xyz) continue;
          const pv = toVec3(pt.xyz);
          if (Math.hypot(pv[0] - origin[0], pv[1] - origin[1], pv[2] - origin[2]) > 1e-4) {
            refPtId = pt.id;
            break;
          }
        }
      }
      specs.push({
        ballId: o.id,
        radiusSegId: radSeg?.id ?? null,
        origin,
        refPtId,
        segKey,
      });
    }
    return specs;
  }, [scene, buoc, pedSteps, activePedStep]);
  const initialReducedMotion =
    typeof window !== "undefined"
    && typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sphereFormationRef = useRef<{
    startMs: number;
    durationMs: number;
    reducedMotion: boolean;
    specs: {
      ballId: string;
      radiusSegId: string | null;
      origin: Vec3;
      refPtId: string | null;
      segKey: string | null;
    }[];
    overrideProgress: number | null;
  }>({
    startMs: typeof performance !== "undefined" ? performance.now() : Date.now(),
    durationMs: 0,
    reducedMotion: initialReducedMotion,
    specs: sphereFormationSpecs,
    overrideProgress: null,
  });
  sphereFormationRef.current.specs = sphereFormationSpecs;
  const prevReplayNonceRef = useRef(replayNonce);
  const prevIsPlayingRef = useRef(isPlaying);
  useEffect(() => {
    const wasPlaying = prevIsPlayingRef.current;
    prevIsPlayingRef.current = isPlaying;
    if (wasPlaying && !isPlaying && sphereFormationRef.current.durationMs > 0) {
      sphereFormationRef.current.durationMs = 0;
      scheduleCommitRender();
    }
  }, [isPlaying]);
  useEffect(() => {
    const prev = prevStepSceneRef.current;
    const replayRequested = prevReplayNonceRef.current !== replayNonce;
    prevReplayNonceRef.current = replayNonce;
    const reduced =
      typeof window !== "undefined"
      && typeof window.matchMedia === "function"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const newIdsSorted = [...stepHighlightTargets.newIds].sort();
    const depIdsSorted = [...stepHighlightTargets.depIds].sort();
    const now = typeof performance !== "undefined" ? performance.now() : Date.now();
    if (prev.scene !== scene) {
      prevStepSceneRef.current = { scene, buoc };
      stepEntranceRef.current = {
        startMs: 0,
        durationMs: 0,
        reducedMotion: reduced,
        step: buoc,
        newIds: newIdsSorted,
        depIds: depIdsSorted,
      };
      sphereFormationRef.current = {
        startMs: now,
        durationMs: !replayRequested || reduced || sphereFormationSpecs.length === 0 ? 0 : SPHERE_FORMATION_DURATION_MS,
        reducedMotion: reduced,
        specs: sphereFormationSpecs,
        overrideProgress: null,
      };
      scheduleCommitRender();
      return;
    }
    if (prev.buoc !== buoc || replayRequested) {
      prevStepSceneRef.current = { scene, buoc };
      huongNhanRef.current.clear();
      lechNhanRef.current.clear();
      stepEntranceRef.current = {
        startMs: now,
        durationMs: reduced || newIdsSorted.length === 0 ? 0 : 650,
        reducedMotion: reduced,
        step: buoc,
        newIds: newIdsSorted,
        depIds: depIdsSorted,
      };
      sphereFormationRef.current = {
        startMs: now,
        durationMs: (!isPlaying && !replayRequested) || reduced || sphereFormationSpecs.length === 0 ? 0 : SPHERE_FORMATION_DURATION_MS,
        reducedMotion: reduced,
        specs: sphereFormationSpecs,
        overrideProgress: null,
      };
      scheduleCommitRender();
    } else {
      stepEntranceRef.current.newIds = newIdsSorted;
      stepEntranceRef.current.depIds = depIdsSorted;
      stepEntranceRef.current.reducedMotion = reduced;
      sphereFormationRef.current.specs = sphereFormationSpecs;
      sphereFormationRef.current.reducedMotion = reduced;
    }
  }, [scene, buoc, replayNonce, isPlaying, stepHighlightTargets, sphereFormationSpecs]);
  // Chỉ khi NGƯỜI DÙNG chọn: phân tầng chuỗi nhân quả; null = trung tính.
  const tang = useMemo(
    () => (tuongTac.selected_id ? tangNhanManh(scene, tuongTac.selected_id) : null),
    [scene, tuongTac.selected_id],
  );
  const rawHiddenAux = useMemo(
    () => auxiliaryHiddenAt(scene, buoc, auxiliaryShown, tuongTac.selected_id ?? null),
    [scene, buoc, auxiliaryShown, tuongTac.selected_id],
  );
  const stepVisualRoles = useMemo(
    () =>
      resolveStepVisualRoles(scene, buoc, {
        auxiliaryShown,
        selectedId: tuongTac.selected_id,
      }),
    [scene, buoc, auxiliaryShown, tuongTac.selected_id],
  );
  const anPhu = useMemo(() => {
    if (rawHiddenAux.size === 0) return rawHiddenAux;
    const present = objectsAt(scene, buoc);
    const auxMap = auxiliaryObjects(scene);
    const byObjId = new Map(scene.objects.map((o) => [o.id, o]));
    const out = new Set(rawHiddenAux);
    for (const id of rawHiddenAux) {
      const obj = byObjId.get(id);
      if (!obj) continue;
      if (
        (obj.display_group ?? []).includes("sphere_foundation_ref")
        && (stepVisualRoles.get(id)?.visible ?? false)
      ) {
        out.delete(id);
        continue;
      }
      if (
        obj.type === "line3"
        && resolveLineDisplaySpan(scene, obj, present).mode === "extended_ray"
        && (stepVisualRoles.get(id)?.visible ?? true)
      ) {
        out.delete(id);
        continue;
      }
      const auxMeta = auxMap.get(id);
      if (
        (obj.type === "segment3" || obj.type === "line3")
        && auxMeta?.loai === "dung"
        && auxMeta.xongTai >= 0
        && (stepVisualRoles.get(id)?.visible ?? false)
      ) {
        const depEndpoints = [...(obj.endpoint_ids ?? []), ...(obj.depends ?? [])]
          .map((depId) => byObjId.get(depId))
          .filter((dep): dep is SceneObject => Boolean(dep && dep.type === "point3"));
        const usesHiddenPlaneAnchor = depEndpoints.some((pt) => laDiemPhuDungMatPhang(scene, pt, byObjId));
        if (!usesHiddenPlaneAnchor) {
          out.delete(id);
        }
      }
    }
    return out;
  }, [scene, buoc, rawHiddenAux, stepVisualRoles]);
  const quyetDinhMatPhang = useMemo(
    () =>
      new Map(
        scene.objects
          .filter((o) => o.type === "plane3")
          .map((o) => [
            o.id,
            resolvePlaneSectionVisibility(
              scene,
              o,
              buoc,
              auxiliaryShown,
              tuongTac.selected_id ?? null,
              activePedStep?.startAnchor,
            ),
          ]),
      ),
    [scene, buoc, auxiliaryShown, tuongTac.selected_id, activePedStep?.startAnchor],
  );
  // W17 · §15.4 / W18 · §16.5: nhãn số đo của bước — gọn mặc định, tập trung theo lựa chọn. Chủ thể
  // phải đang hiện — ẩn/cô lập theo cùng luật nhãn điểm. "Hiện tất cả" chỉ đổi danh sách này (và nhân
  // chứng của nó): hình, camera, bước, chuỗi nhân quả, nét đứt không đọc nó.
  const ungroundedPts = useMemo(() => ungroundedFreePointIdsAt(scene, buoc), [scene, buoc]);
  const tooltipTargetId = (dangKeoCanvas ? null : hoveredObject) ?? touchTooltipId;
  const tooltipInfo = useMemo(
    () => buildVerifiedObjectTooltip(scene, tooltipTargetId, buoc),
    [scene, tooltipTargetId, buoc],
  );
  useEffect(() => {
    const tip = tooltipRef.current;
    const container = containerRef.current;
    const rel = lastTooltipRelPosRef.current;
    if (!tip || !container || !rel || !tooltipInfo) return;
    const r = container.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return;
    const obstacles = collectCanvasObstacleRects(container, r);
    const tw = Math.max(190, tip.offsetWidth);
    const th = Math.max(54, tip.offsetHeight);
    const clamped = computeClampedCanvasTooltipPosition(rel.relX, rel.relY, tw, th, r.width, r.height, obstacles);
    tip.style.transform = `translate3d(${clamped.x}px,${clamped.y}px,0)`;
  }, [tooltipInfo, tooltipTargetId]);
  const coMatNhan = useMemo(
    () =>
      new Set(
        objectsAt(scene, buoc)
          .filter(
            (o) =>
              !anPhu.has(o.id)
              && !ungroundedPts.has(o.id)
              && (stepVisualRoles.get(o.id)?.visible ?? true),
          )
          .map((o) => o.id),
      ),
    [scene, buoc, anPhu, ungroundedPts, stepVisualRoles],
  );
  const nhanSoDo = useMemo(
    () => annotationsAt(scene, buoc, annotationView, tuongTac.selected_id ?? null)
      .filter((a) => a.subject_ids.every((id) => isVisible(tuongTac, id, coMatNhan))),
    [scene, buoc, annotationView, tuongTac, coMatNhan],
  );
  // Disclosure hides text and hit targets, while distance witnesses still use all certified entries.
  const nhanChu = useMemo(() => nhanSoDo.filter((a) => !annotationView.hiddenIds?.has(a.id)),
    [nhanSoDo, annotationView.hiddenIds]);
  const chonHienTai = useRef<string | null>(null);
  chonHienTai.current = tuongTac.selected_id ?? null;
  useEffect(() => {
    // Điểm neo THẾ GIỚI + độ dời trình bày của chủ thể (tách khối), đọc trong vòng vẽ qua ref.
    const m = new Map<string, THREE.Vector3>();
    for (const a of nhanChu) {
      const p = annotationAnchor(scene, a);
      if (!p) continue;
      const doi = a.subject_ids.map((id) => visualTransformOf(tuongTac, scene, id).translate);
      const tb = [0, 1, 2].map((i) => doi.reduce((s, t) => s + t[i], 0) / doi.length);
      m.set(a.id, new THREE.Vector3(p[0] + tb[0], p[1] + tb[1], p[2] + tb[2]));
    }
    viTriSoDo.current = m;
    scheduleCommitRender();
  }, [scene, nhanChu, tuongTac]);
  const chonRef = useRef(onSelect);
  chonRef.current = onSelect;
  // `id → type`, để luật chọn biết cái nào cụ thể hơn. `ref` vì vòng lặp
  // raycast sống trong một `useEffect` chạy MỘT LẦN.
  const loaiRef = useRef(new Map<string, string>());
  loaiRef.current = new Map(
    scene.objects.map((o) => [
      o.id,
      o.type === "polygon3" && o.parent && (o.display_group ?? []).includes("face") ? "face" : o.type,
    ]),
  );
  const nhanRef = useRef<HTMLDivElement>(null);
  //: `id → vị trí THẾ GIỚI` của nhãn. Ghi trong vòng dựng cảnh, đọc trong
  //: vòng vẽ — hai nhịp khác nhau nên phải đi qua `ref`, không qua state.
  const viTriNhan = useRef(new Map<string, THREE.Vector3>());
  const nhanMpRef = useRef<HTMLDivElement>(null);
  const viTriMatPhang = useRef(new Map<string, THREE.Vector3>());
  const gocMatPhangRef = useRef(new Map<string, THREE.Vector3[]>());
  //: W17 · nhãn SỐ ĐO: lớp DOM thứ hai, cùng vòng chiếu — đặt SAU nhãn điểm để tránh chúng.
  const soDoRef = useRef<HTMLDivElement>(null);
  const viTriSoDo = useRef(new Map<string, THREE.Vector3>());
  /** §16.7: nhóm nhân chứng — ngoài nhóm gốc, nên đổi bước/đổi lựa chọn không dựng lại nó và nó không
   *  dựng lại hình; chỉ đổi khi danh sách nhãn khoảng cách đang hiện đổi. */
  const nhanChungRef = useRef<THREE.Group | null>(null);
  /** W2 · F: nhóm lưới nền — ngoài nhóm gốc như nhân chứng: không dựng lại hình, không vào occlusion/raycast. */
  const luoiRef = useRef<THREE.Group | null>(null);
  const trucRef = useRef<THREE.Group | null>(null);

  // Dựng scene MỘT LẦN; đổi bước chỉ thay nội dung nhóm gốc.
  useEffect(() => {
    if (webglFailed || webglTerminalLatchedRef.current) return;
    const container = containerRef.current;
    if (!container) return;
    const acquired = acquireSceneWebGLRenderer();
    if (!acquired) {
      webglTerminalLatchedRef.current = true;
      setWebglPhase("failed");
      return;
    }
    const { renderer, pooled: isPooledRenderer } = acquired;
    let contextLostObserved = false;
    const scene3 = new THREE.Scene();
    const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
    /* ─── TRỤC LÊN LÀ Z, VÀ PHẢI ĐẶT TRƯỚC `OrbitControls` ─────────────────
     *
     * Toạ độ bài toán dùng **z làm chiều cao** (S(0;0;6), trục trụ O→K theo z),
     * còn mặc định của three.js là `up = (0,1,0)`. Để nguyên mặc định thì quỹ
     * đạo quay bám trục Y: hình vẫn xoay tự do và trục vẫn CỐ ĐỊNH tuyệt đối
     * (đo được ‖trục‖ = 1,000), nhưng nó xoay quanh một trục **không phải
     * chiều cao của bài** — nên người học không bao giờ nhìn được khối từ trên
     * xuống hay từ dưới lên. Đo trên ba ca: `cos` giữa hướng nhìn và trục z
     * chỉ chạy trong [−0,35; 0,00], không bao giờ tới gần ±1. Sau dòng này nó
     * chạm đúng ±1,000.
     *
     * ⚠️ **Thứ tự là toàn bộ vấn đề, không phải giá trị.** `OrbitControls`
     * chụp `camera.up` NGAY TRONG CONSTRUCTOR để dựng quaternion đưa trục ấy
     * về Y nội bộ. Đặt `cam.up` SAU khi tạo controls thì controls vẫn tin trục
     * quỹ đạo là Y trong khi camera dựng khung theo Z — hợp của hai phép quay
     * quanh hai trục không trùng nhau là một phép quay có **trục đổi theo từng
     * khung**. Đó chính là con bọ `56350f7`: đo được ‖trục‖ 0,59–0,66, và trên
     * màn hình nó đọc ra như hình bị lộn nhào.
     *
     * Nên dòng này phải đứng trước `new OrbitControls(...)` bên dưới. Khoá bởi
     * `scene3d-zup-lifecycle.test.tsx`, kiểm bằng HÀNH VI (dựng controls thật
     * rồi hỏi `getPolarAngle`) và bằng **AST** của chính tệp này, không bằng
     * phép tìm chuỗi.
     */
    cam.up.set(0, 0, 1);
    cam.position.set(8, 3, 6);
    scene3.add(new THREE.AmbientLight(MAU.light, PHONG_CACH_SCENE3D.light.ambient));
    const den = new THREE.DirectionalLight(MAU.light, PHONG_CACH_SCENE3D.light.directional);
    den.position.set(5, 10, 7);
    scene3.add(den);
    const goc = new THREE.Group();
    scene3.add(goc);
    rootRef.current = goc;
    const nhanChung = new THREE.Group();
    scene3.add(nhanChung);
    nhanChungRef.current = nhanChung;
    const luoi = new THREE.Group();
    scene3.add(luoi);
    luoiRef.current = luoi;
    const truc = new THREE.Group();
    scene3.add(truc);
    trucRef.current = truc;
    const netDay = new THREE.Group();
    netDay.name = "net_day_man_hinh";
    scene3.add(netDay);

    const dieuKhien = new OrbitControls(cam, renderer.domElement);
    dieuKhien.enableDamping = true;
    dieuKhien.dampingFactor = 0.08;
    dieuKhien.screenSpacePanning = true;
    dieuKhien.zoomSpeed = 0.85;
    dieuKhien.rotateSpeed = 0.85;
    dieuKhien.panSpeed = 0.75;
    dieuKhien.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };
    dieuKhien.minAzimuthAngle = -Infinity;
    dieuKhien.maxAzimuthAngle = Infinity;
    dieuKhien.minPolarAngle = 0.005;
    dieuKhien.maxPolarAngle = Math.PI - 0.005;
    container.appendChild(renderer.domElement);

    let song = true;
    let restoreTimeoutId: ReturnType<typeof setTimeout> | null = null;
    let awaitingContextRestore = false;
    let userAdjustedCamera = false;
    let dangDatKhungTuDong = false;
    let lechOngKinhNgang = 0;
    let lechOngKinhDoc = 0;
    let kcKhungChuan = 0;
    const armRestoreTimeout = () => {
      if (restoreTimeoutId !== null) {
        clearTimeout(restoreTimeoutId);
        restoreTimeoutId = null;
      }
      if (typeof document !== "undefined" && document.visibilityState === "hidden") {
        return;
      }
      restoreTimeoutId = setTimeout(() => {
        restoreTimeoutId = null;
        awaitingContextRestore = false;
        webglTerminalLatchedRef.current = true;
        setWebglPhase("failed");
      }, WEBGL_RESTORE_TIMEOUT_MS);
    };
    const xuLyDoiTrangThaiTab = () => {
      if (typeof document === "undefined") return;
      if (document.visibilityState === "hidden") {
        if (restoreTimeoutId !== null) {
          clearTimeout(restoreTimeoutId);
          restoreTimeoutId = null;
        }
      } else if (awaitingContextRestore && !webglTerminalLatchedRef.current) {
        armRestoreTimeout();
      }
    };
    const tinhZoomDashScale = (): number => {
      const kcHienTai = cam.position.clone().sub(dieuKhien.target).length();
      if (!(kcKhungChuan > 1e-4) || !(kcHienTai > 1e-4)) return 1;
      if (Math.abs(kcHienTai - kcKhungChuan) <= kcKhungChuan * 1e-3) return 1;
      return Math.max(0.55, Math.min(2.2, kcKhungChuan / kcHienTai));
    };
    const baoCaoCameraPose = () => {
      if (dangDatKhungTuDong || !onCameraPoseChangeRef.current) return;
      const pose: SceneCameraPose = {
        position: [cam.position.x, cam.position.y, cam.position.z],
        target: [dieuKhien.target.x, dieuKhien.target.y, dieuKhien.target.z],
      };
      if (hopLeCameraPose(pose)) {
        onCameraPoseChangeRef.current(pose);
      }
    };
    let controlsInteracting = false;
    let khoangTuaHienTai: number | null = null;
    let lastInteractionWakeMs = 0;
    let wakeRenderLoop = () => {};
    const danhDauNguoiDungChinhCam = () => {
      if (!dangDatKhungTuDong) userAdjustedCamera = true;
      controlsInteracting = true;
      lastInteractionWakeMs = typeof performance !== "undefined" ? performance.now() : Date.now();
      wakeRenderLoop();
    };
    const xuLyKetThucDieuKhien = () => {
      controlsInteracting = false;
      lastInteractionWakeMs = typeof performance !== "undefined" ? performance.now() : Date.now();
      if (!dangDatKhungTuDong) {
        userAdjustedCamera = true;
        baoCaoCameraPose();
      }
      wakeRenderLoop();
    };
    const xuLyDoiDieuKhien = () => {
      if (!dangDatKhungTuDong) {
        lastInteractionWakeMs = typeof performance !== "undefined" ? performance.now() : Date.now();
        wakeRenderLoop();
      }
    };
    const xuLyMatNguCanhWebgl = (ev: Event) => {
      ev.preventDefault();
      contextLostObserved = true;
      song = false;
      if (userAdjustedCamera) {
        const snapshotPose: SceneCameraPose = {
          position: [cam.position.x, cam.position.y, cam.position.z],
          target: [dieuKhien.target.x, dieuKhien.target.y, dieuKhien.target.z],
        };
        if (hopLeCameraPose(snapshotPose)) {
          pendingRestoredCameraRef.current = snapshotPose;
        }
      }
      for (const group of [goc, nhanChung, luoi, truc, netDay]) {
        disposeScene3DObject(group);
      }
      const isHidden = typeof document !== "undefined" && document.visibilityState === "hidden";
      if (
        webglTerminalLatchedRef.current
        || webglRestoreCountRef.current >= MAX_WEBGL_AUTO_RESTORES
        || (isHidden && webglRestoreCountRef.current > 0)
      ) {
        awaitingContextRestore = false;
        webglTerminalLatchedRef.current = true;
        setWebglPhase("failed");
        return;
      }
      awaitingContextRestore = true;
      setWebglPhase("recovering");
      armRestoreTimeout();
    };
    const xuLyKhoiPhucNguCanhWebgl = () => {
      awaitingContextRestore = false;
      if (restoreTimeoutId !== null) {
        clearTimeout(restoreTimeoutId);
        restoreTimeoutId = null;
      }
      if (webglTerminalLatchedRef.current || webglRestoreCountRef.current >= MAX_WEBGL_AUTO_RESTORES) {
        webglTerminalLatchedRef.current = true;
        setWebglPhase("failed");
        return;
      }
      webglRestoreCountRef.current += 1;
      setWebglPhase("healthy");
      setWebglEpoch((n) => n + 1);
    };
    renderer.domElement.addEventListener("wheel", xuLyDoiDieuKhien, { passive: true });
    // A label or annotation over the figure keeps its pointer events (selection, focus) but must not swallow the
    // wheel: forward it to the canvas so zooming works wherever the pointer rests on the figure.
    const chuyenWheelVeCanvas = (e: WheelEvent) => {
      if (e.target === renderer.domElement) return;
      e.preventDefault();
      renderer.domElement.dispatchEvent(new WheelEvent("wheel", e));
    };
    container.addEventListener("wheel", chuyenWheelVeCanvas, { passive: false });
    renderer.domElement.addEventListener("webglcontextlost", xuLyMatNguCanhWebgl, false);
    renderer.domElement.addEventListener("webglcontextrestored", xuLyKhoiPhucNguCanhWebgl, false);
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", xuLyDoiTrangThaiTab);
    }
    // Near zoom limit follows the real surface along the new view direction (clamped on the next controls update).
    const capNhatGioiHanTheoHuong = () => { khoangTuaHienTai = capNhatGioiHanGan(cam, dieuKhien); };
    dieuKhien.addEventListener("start", danhDauNguoiDungChinhCam);
    dieuKhien.addEventListener("change", capNhatGioiHanTheoHuong);
    dieuKhien.addEventListener("change", xuLyDoiDieuKhien);
    dieuKhien.addEventListener("end", xuLyKetThucDieuKhien);

    let lastSizedW = 0;
    let lastSizedH = 0;
    let lastSizedDpr = 0;
    const chinhCo = () => {
      const w = container.clientWidth || 640;
      const h = container.clientHeight || 420;
      const dpr = renderer.getPixelRatio();
      if (w !== lastSizedW || h !== lastSizedH || dpr !== lastSizedDpr) {
        renderer.setSize(w, h, false);
        lastSizedW = w;
        lastSizedH = h;
        lastSizedDpr = dpr;
      }
      cam.aspect = w / h;
      if (Math.abs(lechOngKinhNgang) > 1e-4 || Math.abs(lechOngKinhDoc) > 1e-4) {
        cam.setViewOffset(w, h, -lechOngKinhNgang * (w * 0.5), lechOngKinhDoc * (h * 0.5), w, h);
      } else {
        cam.clearViewOffset();
      }
      cam.updateProjectionMatrix();
    };
    const xuLyDoiCoKhung = () => {
      chinhCo();
      // Tuyệt đối không reset góc nhìn hay mức zoom của người học khi thu gọn/mở Study Dock, đóng/mở panel hoặc resize.
      veRef.current?.();
      chieuNhan();
    };
    chinhCo();
    window.addEventListener("resize", xuLyDoiCoKhung);
    // W4: khung đổi cỡ KHÔNG qua sự kiện cửa sổ ⇒ theo dõi khung chứa, bỏ qua callback khởi tạo trùng kích thước và giữ nguyên góc camera.
    const roKhung = typeof ResizeObserver !== "undefined"
      ? new ResizeObserver(() => {
          const w = container.clientWidth || 640;
          const h = container.clientHeight || 420;
          if (w === lastSizedW && h === lastSizedH) return;
          xuLyDoiCoKhung();
        })
      : null;
    roKhung?.observe(container);

    // ── CHỌN BẰNG CHUỘT ──────────────────────────────────────────────────
    //
    // `pointerup`, không `pointerdown`: OrbitControls dùng kéo-thả để xoay
    // cảnh, và bắt ở `down` thì mỗi lần xoay cũng là một lần chọn. Chỉ tính
    // là bấm khi con trỏ gần như không di chuyển giữa hai mốc.
    let batDau: [number, number] | null = null;
    const NGUONG_KEO = 4;
    const datViTriTooltip = (clientX: number, clientY: number) => {
      const tip = tooltipRef.current;
      if (!tip) return;
      const r = container.getBoundingClientRect();
      const relX = clientX - r.left;
      const relY = clientY - r.top;
      lastTooltipRelPosRef.current = { relX, relY };
      const obstacles = collectCanvasObstacleRects(container, r);
      const tw = Math.max(190, tip.offsetWidth);
      const th = Math.max(54, tip.offsetHeight);
      const clamped = computeClampedCanvasTooltipPosition(relX, relY, tw, th, r.width, r.height, obstacles);
      tip.style.transform = `translate3d(${clamped.x}px,${clamped.y}px,0)`;
    };
    const xuongTay = (e: PointerEvent) => {
      batDau = [e.clientX, e.clientY];
      setDangKeoCanvas(true);
      if (e.pointerType !== "touch") setTouchTooltipId(null);
      renderer.domElement.style.cursor = "";
    };
    const vatTaiConTro = (e: PointerEvent, chiThietDien = false) => {
      const r = renderer.domElement.getBoundingClientRect();
      const diem = new THREE.Vector2(
        ((e.clientX - r.left) / r.width) * 2 - 1,
        -((e.clientY - r.top) / r.height) * 2 + 1,
      );
      const tia = new THREE.Raycaster();
      const kc = cam.position.clone().sub(dieuKhien.target).length();
      tia.params.Line = { threshold: nguongBamCanh(kc) };
      tia.params.Points = { threshold: nguongBamCanh(kc) };
      tia.setFromCamera(diem, cam);
      const trung = tia.intersectObjects(goc.children, true);
      const ids = trung
        .filter((h) => !h.object.userData?.chieuSau)
        .map((h) => pickSemanticId(h.object))
        .filter((x): x is string => typeof x === "string" && x.length > 0);
      return chiThietDien ? ids.find((id) => {
        const object = sceneRef.current.objects.find((o) => o.id === id);
        return object && vaiTroMien(object) === "section";
      }) ?? null : chonCuThe(ids, (id) => loaiRef.current.get(id));
    };
    const nhacTay = (e: PointerEvent) => {
      const d0 = batDau;
      batDau = null;
      setDangKeoCanvas(false);
      if (!d0 || !chonRef.current) return;
      if (Math.hypot(e.clientX - d0[0], e.clientY - d0[1]) > NGUONG_KEO) {
        userAdjustedCamera = true;
        setTouchTooltipId(null);
        return;
      }
      const picked = vatTaiConTro(e);
      if (e.pointerType === "touch") {
        setTouchTooltipId(picked);
        if (picked) datViTriTooltip(e.clientX, e.clientY);
      } else {
        setTouchTooltipId(null);
      }
      chonRef.current(picked);
    };
    const roiConTro = () => {
      setHoveredObject(null);
      setDangKeoCanvas(false);
      setTouchTooltipId(null);
      renderer.domElement.style.cursor = "";
    };
    const diConTro = (e: PointerEvent) => {
      if (batDau && Math.hypot(e.clientX - batDau[0], e.clientY - batDau[1]) > NGUONG_KEO) {
        userAdjustedCamera = true;
      }
      if (e.pointerType === "touch" || e.buttons || batDau) return;
      const id = vatTaiConTro(e, false);
      if (id) datViTriTooltip(e.clientX, e.clientY);
      setHoveredObject((prev) => (prev === id ? prev : id));
      renderer.domElement.style.cursor = id ? "pointer" : "";
    };
    renderer.domElement.addEventListener("pointerdown", xuongTay);
    renderer.domElement.addEventListener("pointerup", nhacTay);
    renderer.domElement.addEventListener("pointermove", diConTro);
    renderer.domElement.addEventListener("pointerleave", roiConTro);

    // ── NHÃN ĐIỂM, CHIẾU RA MÀN HÌNH MỖI KHUNG ──────────────────────────
    //
    // Học sinh đọc hình bằng TÊN ĐIỂM: "AB", "SAB", "trung điểm M". Một khối
    // 3D không nhãn buộc họ tra sang bảng bên cạnh rồi quay lại — và chính chỗ
    // quay đi quay lại ấy là nơi hình mất nghĩa.
    //
    // Nhãn là DOM, không phải sprite: chữ nét thật, ăn theo token màu, đọc
    // được bởi trình đọc màn hình, và không tốn một texture nào. Cập nhật
    // bằng cách ghi thẳng `style` trong vòng vẽ — đi qua state React thì mỗi
    // khung là một lần dựng lại cây.
    //
    // `cam.project` ở đây là phép CHIẾU TRÌNH BÀY, không phải suy luận hình
    // học: đầu ra là vị trí điểm ảnh của một nhãn, không quay lại `GeometryState`.
    const chieuNhan = () => {
      const lop = nhanRef.current;
      if (!lop) return;
      const w = renderer.domElement.clientWidth || 1;
      const h = renderer.domElement.clientHeight || 1;
      // Chiếu trước, LỌC CHỒNG sau. Bản trước hiện mọi nhãn, và ảnh chụp thật
      // cho thấy bốn câu mô tả đè lên nhau ngay giữa hình. Lọc ở đây chứ
      // không ở lúc dựng cảnh, vì hai nhãn có chồng nhau hay không phụ thuộc
      // GÓC NHÌN — thứ chỉ biết được sau phép chiếu.
      const gocVuongNodes: THREE.Object3D[] = [...(nhanChungRef.current?.children ?? [])];
      goc.traverse((node) => {
        if (!node.visible || !node.userData?.perpMarker) return;
        let vis = true;
        for (let p: THREE.Object3D | null = node; p && p !== goc; p = p.parent) {
          if (!p.visible) { vis = false; break; }
        }
        if (vis) gocVuongNodes.push(node);
      });
      const gocVuongPts = gocVuongNodes.flatMap((child) => {
        const ud = child.userData as { foot?: Vec3; corner?: Vec3; from?: Vec3 } | undefined;
        if (!ud?.foot || !ud?.corner) return [];
        const f3 = new THREE.Vector3(...ud.foot).applyQuaternion(qRef.current).project(cam);
        const c3 = new THREE.Vector3(...ud.corner).applyQuaternion(qRef.current).project(cam);
        const t3 = ud.from ? new THREE.Vector3(...ud.from).applyQuaternion(qRef.current).project(cam) : null;
        if (!(f3.z < 1) || !(c3.z < 1)) return [];
        return [{
          fx: ((f3.x + 1) / 2) * w, fy: ((1 - f3.y) / 2) * h,
          cx: ((c3.x + 1) / 2) * w, cy: ((1 - c3.y) / 2) * h,
          ...(t3 && t3.z < 1 ? { tx: ((t3.x + 1) / 2) * w, ty: ((1 - t3.y) / 2) * h } : {}),
        }];
      });
      const canh2d: { ax: number; ay: number; bx: number; by: number }[] = [];
      const chieuDoan3 = (a3: THREE.Vector3, b3: THREE.Vector3, matW: THREE.Matrix4) => {
        const pa = a3.clone().applyMatrix4(matW).project(cam);
        const pb = b3.clone().applyMatrix4(matW).project(cam);
        if (pa.z < 1 && pb.z < 1) {
          canh2d.push({
            ax: ((pa.x + 1) / 2) * w,
            ay: ((1 - pa.y) / 2) * h,
            bx: ((pb.x + 1) / 2) * w,
            by: ((1 - pb.y) / 2) * h,
          });
        }
      };
      goc.updateMatrixWorld(true);
      goc.traverse((node) => {
        if (!node.visible) return;
        const ce = node.userData?.canonicalEdge as { a: THREE.Vector3; b: THREE.Vector3 } | undefined;
        if (ce) {
          chieuDoan3(ce.a, ce.b, node.matrixWorld);
          return;
        }
        const seg = node.userData?.nonCanonicalSegment as { a: THREE.Vector3; b: THREE.Vector3 } | undefined;
        if (seg) {
          chieuDoan3(seg.a, seg.b, node.matrixWorld);
          return;
        }
        const loop = node.userData?.nonCanonicalLoop as { pts: THREE.Vector3[]; closed: boolean; isPlaneBorder?: boolean } | undefined;
        if (loop && !loop.isPlaneBorder && loop.pts.length >= 2) {
          const n = loop.closed ? loop.pts.length : loop.pts.length - 1;
          for (let i = 0; i < n; i += 1) {
            chieuDoan3(loop.pts[i], loop.pts[(i + 1) % loop.pts.length], node.matrixWorld);
          }
          return;
        }
        if (
          (node as THREE.Line).isLine
          && (node.name.startsWith("witness_leg:") || node.name.startsWith("perp_plane_ray:"))
        ) {
          const posAttr = (node as THREE.Line).geometry?.getAttribute?.("position") as THREE.BufferAttribute | undefined;
          if (posAttr && posAttr.count >= 2) {
            chieuDoan3(
              new THREE.Vector3().fromBufferAttribute(posAttr, 0),
              new THREE.Vector3().fromBufferAttribute(posAttr, posAttr.count - 1),
              node.matrixWorld,
            );
          }
        }
      });

      const dat: { el: HTMLElement; id: string; x: number; y: number; lx: number; ly: number; duoi?: boolean; uuTien: number; w: number; h: number }[] = [];
      // Cỡ hộp nhãn cho phép lọc chồng: ĐỌC hết trước khi GHI style nào — đọc xen giữa các lần ghi ép trình duyệt
      // tính lại bố cục cho từng nhãn ở mỗi khung (transform/opacity không đổi offsetWidth/Height).
      const co = new Map((Array.from(lop.children) as HTMLElement[]).map((el) => [el, [el.offsetWidth, el.offsetHeight]]));
      const ungVienDiem2d: { el: HTMLElement; id: string; x: number; y: number; w: number; h: number; uuTien: number }[] = [];
      for (const el of Array.from(lop.children) as HTMLElement[]) {
        const id = el.dataset.id;
        const v = id ? viTriNhan.current.get(id) : undefined;
        if (!v || !id) { el.style.opacity = "0"; continue; }
        const p3 = v.clone().applyQuaternion(qRef.current).project(cam);
        // Sau lưng camera ⇒ giấu. Không có phép kiểm này thì nhãn của mặt
        // khuất lộn ngược lên trước hình.
        const hien = p3.z < 1 && p3.x > -1.1 && p3.x < 1.1 && p3.y > -1.1 && p3.y < 1.1;
        if (!hien) { el.style.opacity = "0"; continue; }
        const x = ((p3.x + 1) / 2) * w;
        const y = ((1 - p3.y) / 2) * h;
        const [cw, ch] = co.get(el)!;
        ungVienDiem2d.push({ el, id, x, y, w: cw, h: ch, uuTien: Number(el.dataset.uuTien ?? "1") });
      }
      const viTriToiUu = tinhViTriNhanDiem(ungVienDiem2d, canh2d, gocVuongPts, huongNhanRef.current);
      for (const u of ungVienDiem2d) {
        const dich = viTriToiUu.get(u.id) ?? { x: u.x - (u.w || 18) / 2, y: u.y - 1.4 * (u.h || 18), duoi: false };
        const lech = lamMuotLechNhan(lechNhanRef.current.get(u.id), { dx: dich.x - u.x, dy: dich.y - u.y });
        lechNhanRef.current.set(u.id, lech);
        const pos = { x: u.x + lech.dx, y: u.y + lech.dy, duoi: dich.duoi };
        u.el.style.transform = `translate(${Math.round(pos.x)}px,${Math.round(pos.y)}px)`;
        dat.push({
          el: u.el,
          id: u.id,
          x: u.x,
          y: u.y,
          lx: pos.x,
          ly: pos.y,
          duoi: pos.duoi,
          uuTien: u.uuTien,
          w: u.w,
          h: u.h,
        });
      }
      const giu = locNhanChongNhau(dat, w <= 480 ? 5 : undefined);
      for (const d of dat) d.el.style.opacity = giu.has(d.id) ? "1" : "0";

      // ── W17 · NHÃN SỐ ĐO — đặt sau nhãn điểm, tránh chúng và các lớp phủ che khung ─────
      // Luật hộp nhãn (§15.5) ở hàm thuần `placeAnnotationLabels`; đây chỉ đo cỡ chữ và chiếu.
      const lopSo = soDoRef.current;
      if (!lopSo) return;
      const hopDiem = dat.filter((d) => giu.has(d.id)).map((d) => ({
        id: d.id, x: d.lx,
        y: d.ly,
        w: d.el.offsetWidth, h: d.el.offsetHeight,
      }));
      const chamDiem: LabelRect[] = dat.filter((d) => giu.has(d.id)).map((d) => ({
        x: d.x - 7, y: d.y - 7, w: 14, h: 14,
      }));
      const gocVuongRects: LabelRect[] = gocVuongPts.flatMap((g) => {
        const ra: LabelRect[] = [
          { x: g.fx - 8, y: g.fy - 8, w: 16, h: 16 },
          { x: g.cx - 8, y: g.cy - 8, w: 16, h: 16 },
        ];
        if (g.tx !== undefined && g.ty !== undefined) {
          const dx = g.fx - g.tx, dy = g.fy - g.ty, d = Math.hypot(dx, dy);
          if (d > 24) {
            const mx = (g.fx + g.tx) / 2, my = (g.fy + g.ty) / 2;
            const ux = (dx / d) * 10, uy = (dy / d) * 10;
            ra.push({ x: mx + ux - 2, y: my + uy - 2, w: 4, h: 4 }, { x: mx - ux - 2, y: my - uy - 2, w: 4, h: 4 });
          }
        }
        return ra;
      });
      const capKhoaDoan = (a: string, b: string) => (a < b ? `${a}|${b}` : `${b}|${a}`);
      const hiddenCanonicalSet = (goc.userData.hiddenCanonicalEdgeIds as Set<string> | undefined) ?? new Set<string>();
      const hiddenSegCap = new Set<string>();
      for (const objItem of sceneRef.current.objects) {
        for (const eo of objItem.edge_ownership ?? []) {
          if (eo.endpoint_ids?.length === 2 && hiddenCanonicalSet.has(eo.edge_id)) {
            hiddenSegCap.add(capKhoaDoan(eo.endpoint_ids[0], eo.endpoint_ids[1]));
          }
        }
      }
      const objMapNow = new Map(sceneRef.current.objects.map((x) => [x.id, x]));
      goc.traverse((node) => {
        const segMeta = node.userData?.nonCanonicalSegment as { objectId?: string } | undefined;
        if (!segMeta?.objectId) return;
        const segObj = objMapNow.get(segMeta.objectId);
        const eps = segObj?.endpoint_ids?.length === 2
          ? segObj.endpoint_ids
          : segObj?.type === "segment3" && segObj.depends?.length === 2
            ? segObj.depends
            : null;
        if (!eps) return;
        const spanLines = node.children.filter(
          (ch) => ch.userData?.nonCanonicalSpanLine && !ch.name.endsWith(":proxy"),
        );
        if (spanLines.length > 0 && spanLines.every((ch) => ch.userData?.hidden === true)) {
          hiddenSegCap.add(capKhoaDoan(eps[0], eps[1]));
        }
      });
      const canDat: LabelToPlace[] = [];
      const theTheoId = new Map<string, HTMLElement>();
      const hiddenEdgeAnnIds: string[] = [];
      for (const el of Array.from(lopSo.children) as HTMLElement[]) {
        const id = el.dataset.annId;
        const segKey = el.dataset.annSegKey ?? "";
        const isHiddenEdge = Boolean(segKey && hiddenSegCap.has(segKey) && !xrayRef.current);
        if (isHiddenEdge) {
          hiddenEdgeAnnIds.push(id ?? "");
          if (!dashedHiddenShownRef.current) {
            el.style.opacity = "0";
            el.dataset.thieuCho = "hidden_edge";
            el.classList.toggle("la-net-khuat", false);
            el.style.pointerEvents = "none";
            el.tabIndex = -1;
            continue;
          }
        }
        el.classList.toggle("la-net-khuat", isHiddenEdge && dashedHiddenShownRef.current);
        const v = id ? viTriSoDo.current.get(id) : undefined;
        const p3 = v?.clone().applyQuaternion(qRef.current).project(cam);
        if (!id || !p3 || !(p3.z < 1)) { el.style.opacity = "0"; continue; }
        canDat.push({ id, ax: ((p3.x + 1) / 2) * w, ay: ((1 - p3.y) / 2) * h,
          w: el.offsetWidth, h: el.offsetHeight, priority: Number(el.dataset.uuTien ?? "1") });
        theTheoId.set(id, el);
      }
      const vungChe = vungCheKhung(renderer.domElement.getBoundingClientRect());
      const hopThietDien: LabelRect[] = [];
      const tmpSec = new THREE.Vector3();
      goc.traverse((node) => {
        if (!node.visible || !(node as THREE.Mesh).isMesh || !node.name.startsWith("section_fill:")) return;
        for (let p: THREE.Object3D | null = node; p; p = p.parent) {
          if (!p.visible) return;
          if (p === goc) break;
        }
        const posAttr = (node as THREE.Mesh).geometry?.getAttribute?.("position") as THREE.BufferAttribute | undefined;
        if (!posAttr || posAttr.count < 3) return;
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        for (let i = 0; i < posAttr.count; i += 1) {
          tmpSec.fromBufferAttribute(posAttr, i).applyMatrix4(node.matrixWorld).project(cam);
          if (!(tmpSec.z < 1)) continue;
          const sx = ((tmpSec.x + 1) / 2) * w;
          const sy = ((1 - tmpSec.y) / 2) * h;
          minX = Math.min(minX, sx);
          maxX = Math.max(maxX, sx);
          minY = Math.min(minY, sy);
          maxY = Math.max(maxY, sy);
        }
        if (maxX - minX > 12 && maxY - minY > 12) {
          hopThietDien.push({ x: minX + 4, y: minY + 4, w: maxX - minX - 8, h: maxY - minY - 8 });
        }
      });
      const ungVienSoDo = w <= 480 && canDat.length > 4
        ? [...canDat].sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id)).slice(0, 4)
        : canDat;
      const daDat = placeAnnotationLabels(
        ungVienSoDo,
        [...hopDiem, ...chamDiem, ...gocVuongRects, ...vungChe],
        { w, h },
        hopThietDien,
      );
      for (const c of ungVienSoDo) {
        if (!daDat.has(c.id)) {
          const r2 = placeAnnotationLabels([c], [...hopDiem, ...chamDiem, ...vungChe, ...daDat.values()], { w, h }, hopThietDien).get(c.id)
            ?? placeAnnotationLabels([c], [...hopDiem, ...vungChe, ...daDat.values()], { w, h }).get(c.id);
          if (r2) daDat.set(c.id, r2);
        }
      }
      const hopSo: { id: string; box: LabelRect; anchor: { x: number; y: number } }[] = [];
      for (const c of canDat) {
        const el = theTheoId.get(c.id)!;
        const r = daDat.get(c.id);
        el.style.opacity = r ? "1" : "0";
        // W2 · A: nhãn HỢP LỆ ở bước này nhưng thiếu chỗ — khác nhãn chưa hợp lệ (không có trong lớp này). Giá
        // trị vẫn ở ngăn «Đại lượng» và ô soi.
        el.dataset.thieuCho = r ? "" : "1";
        // Nhãn chưa đặt được thì không bắt chuột, không nhận Tab — giá trị vẫn ở ô soi và lời giải.
        el.style.pointerEvents = r ? "auto" : "none";
        el.tabIndex = r ? 0 : -1;
        if (!r) continue;
        el.style.transform = `translate(${r.x}px,${r.y}px)`;
        hopSo.push({ id: c.id, box: r, anchor: { x: c.ax, y: c.ay } });
      }
      // ── NHÃN KÝ HIỆU MẶT PHẲNG (`.geo3d-nhan-mp`) — đặt ở diềm mở rộng của mặt phẳng, tránh nhãn điểm & số đo ──
      const lopMp = nhanMpRef.current;
      const hopMatPhang: { id: string; box: LabelRect; anchor: { x: number; y: number } }[] = [];
      if (lopMp) {
        const canDatMp: LabelToPlace[] = [];
        const theMpTheoId = new Map<string, HTMLElement>();
        const kcDiemDoan2d = (px: number, py: number, ax: number, ay: number, bx: number, by: number): number => {
          const dx = bx - ax;
          const dy = by - ay;
          const lenSq = dx * dx + dy * dy;
          if (lenSq <= 1e-6) return Math.hypot(px - ax, py - ay);
          const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / lenSq));
          return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
        };
        for (const el of Array.from(lopMp.children) as HTMLElement[]) {
          const id = el.dataset.planeId;
          if (!id) {
            el.style.opacity = "0";
            continue;
          }
          const lw = el.offsetWidth || 44;
          const lh = el.offsetHeight || 20;
          const corners3 = gocMatPhangRef.current.get(id);
          let bestAnchor: { x: number; y: number } | null = null;
          if (corners3 && corners3.length >= 3) {
            const projCorners: { x: number; y: number }[] = [];
            for (const c3 of corners3) {
              const p = c3.clone().applyQuaternion(qRef.current).project(cam);
              if (p.z < 1 && p.x > -1.25 && p.x < 1.25 && p.y > -1.25 && p.y < 1.25) {
                projCorners.push({ x: ((p.x + 1) / 2) * w, y: ((1 - p.y) / 2) * h });
              }
            }
            if (projCorners.length >= 3) {
              const cx = projCorners.reduce((s, p) => s + p.x, 0) / projCorners.length;
              const cy = projCorners.reduce((s, p) => s + p.y, 0) / projCorners.length;
              const candidates: { x: number; y: number }[] = [];
              for (let k = 0; k < projCorners.length; k += 1) {
                const pa = projCorners[k];
                const pb = projCorners[(k + 1) % projCorners.length];
                candidates.push({ x: 0.85 * pa.x + 0.15 * cx, y: 0.85 * pa.y + 0.15 * cy });
                const mx = 0.5 * (pa.x + pb.x);
                const my = 0.5 * (pa.y + pb.y);
                candidates.push({ x: 0.86 * mx + 0.14 * cx, y: 0.86 * my + 0.14 * cy });
              }
              let bestScore = -Infinity;
              const padX = Math.max(24, lw * 0.65);
              const padY = Math.max(16, lh * 0.65);
              for (const cand of candidates) {
                if (cand.x < padX || cand.x > w - padX || cand.y < padY || cand.y > h - padY) continue;
                let minClear = 240;
                for (const hd of hopDiem) {
                  minClear = Math.min(minClear, Math.hypot(cand.x - (hd.x + hd.w * 0.5), cand.y - (hd.y + hd.h * 0.5)) - 14);
                }
                for (const cd of chamDiem) {
                  minClear = Math.min(minClear, Math.hypot(cand.x - (cd.x + cd.w * 0.5), cand.y - (cd.y + cd.h * 0.5)) - 10);
                }
                for (const seg2 of canh2d) {
                  minClear = Math.min(minClear, kcDiemDoan2d(cand.x, cand.y, seg2.ax, seg2.ay, seg2.bx, seg2.by));
                }
                for (const hs of hopSo) {
                  minClear = Math.min(minClear, Math.hypot(cand.x - hs.anchor.x, cand.y - hs.anchor.y) - 12);
                }
                for (const gr of gocVuongRects) {
                  minClear = Math.min(minClear, Math.hypot(cand.x - (gr.x + gr.w * 0.5), cand.y - (gr.y + gr.h * 0.5)) - 18);
                }
                for (const prevMp of canDatMp) {
                  minClear = Math.min(minClear, Math.hypot(cand.x - prevMp.ax, cand.y - prevMp.ay) * 0.82 - 18);
                }
                const score = minClear - 0.04 * (cand.y - cy);
                if (score > bestScore) {
                  bestScore = score;
                  bestAnchor = cand;
                }
              }
            }
          }
          if (!bestAnchor) {
            const v = viTriMatPhang.current.get(id);
            const p3 = v?.clone().applyQuaternion(qRef.current).project(cam);
            if (!p3 || !(p3.z < 1) || p3.x <= -1.08 || p3.x >= 1.08 || p3.y <= -1.08 || p3.y >= 1.08) {
              el.style.opacity = "0";
              continue;
            }
            bestAnchor = { x: ((p3.x + 1) / 2) * w, y: ((1 - p3.y) / 2) * h };
          }
          canDatMp.push({
            id,
            ax: bestAnchor.x,
            ay: bestAnchor.y,
            w: lw,
            h: lh,
            priority: Number(el.dataset.uuTien ?? "1"),
          });
          theMpTheoId.set(id, el);
        }
        const vatCanMp: LabelRect[] = [
          ...hopDiem,
          ...chamDiem,
          ...gocVuongRects,
          ...vungChe,
          ...hopSo.map((x) => x.box),
        ];
        const daDatMp = placeAnnotationLabels(canDatMp, [...vatCanMp, ...hopThietDien], { w, h });
        for (const c of canDatMp) {
          if (!daDatMp.has(c.id)) {
            const fallbackMp = placeAnnotationLabels([c], [...vatCanMp, ...daDatMp.values()], { w, h }).get(c.id);
            if (fallbackMp) daDatMp.set(c.id, fallbackMp);
          }
        }
        for (const c of canDatMp) {
          const el = theMpTheoId.get(c.id)!;
          const r = daDatMp.get(c.id);
          el.style.opacity = r ? "1" : "0";
          if (!r) continue;
          el.style.transform = `translate(${r.x}px,${r.y}px)`;
          hopMatPhang.push({ id: c.id, box: r, anchor: { x: c.ax, y: c.ay } });
        }
      }
      if (typeof window !== "undefined") {
        // Móc ĐO của bộ kiểm trình duyệt (§15.5): hộp nhãn số đo đang hiện + hộp nhãn điểm đang hiện.
        (window as any).__geo3d_annotation_boxes = hopSo;
        // W2 · A: nhãn hợp lệ ở bước này mà không đặt được vì thiếu chỗ.
        (window as any).__geo3d_annotation_unplaced = canDat.filter((c) => !daDat.has(c.id)).map((c) => c.id);
        (window as any).__geo3d_annotation_hidden_edge_ids = hiddenEdgeAnnIds.filter(Boolean);
        (window as any).__geo3d_point_label_boxes = hopDiem;
        (window as any).__geo3d_plane_label_boxes = hopMatPhang;
      }
    };

    const currentStepPulse = (): number => {
      const st = stepEntranceRef.current;
      if (st.durationMs <= 0) return 0;
      const now = typeof performance !== "undefined" ? performance.now() : Date.now();
      const elapsed = now - st.startMs;
      if (elapsed >= st.durationMs) return 0;
      const u = Math.max(0, Math.min(1, elapsed / st.durationMs));
      return (1 - u) * (1 - u);
    };

    const currentSphereFormationProgress = (): number => {
      const sf = sphereFormationRef.current;
      if (typeof sf.overrideProgress === "number" && Number.isFinite(sf.overrideProgress)) {
        return Math.max(0, Math.min(1, sf.overrideProgress));
      }
      if (sf.durationMs <= 0 || sf.specs.length === 0) return 1;
      const now = typeof performance !== "undefined" ? performance.now() : Date.now();
      const elapsed = now - sf.startMs;
      if (elapsed >= sf.durationMs) return 1;
      return Math.max(0, Math.min(1, elapsed / sf.durationMs));
    };

    const capNhatVongThamChieuVaHinhThanhMatCau = (
      rootGroup: THREE.Group,
      camera: THREE.PerspectiveCamera,
      wCss: number,
      hCss: number,
    ) => {
      rootGroup.updateMatrixWorld(true);
      const viewFromScene = new THREE.Matrix4()
        .multiplyMatrices(camera.matrixWorldInverse, rootGroup.matrixWorld)
        .elements;
      const projElements = camera.projectionMatrix.elements;
      const formProg = currentSphereFormationProgress();
      const showRadiusBeat = formProg >= 0.2;
      const uRadFadeRaw = Math.max(0, Math.min(1, (formProg - 0.2) / 0.3));
      const uRadFade = formProg >= 1 ? 1 : 1 - (1 - uRadFadeRaw) * (1 - uRadFadeRaw);
      const uShellRaw = Math.max(0, Math.min(1, (formProg - 0.54) / 0.46));
      const uShell = formProg >= 1 ? 1 : 1 - (1 - uShellRaw) * (1 - uShellRaw);

      for (const rootDom of [nhanRef.current, soDoRef.current]) {
        if (!rootDom) continue;
        for (const prevEl of rootDom.querySelectorAll<HTMLElement>('[data-sf-hidden="1"]')) {
          prevEl.style.visibility = "";
          delete prevEl.dataset.sfHidden;
        }
      }

      const sfSpecs = sphereFormationRef.current.specs;
      const formingBallIds = new Set(sfSpecs.map((s) => s.ballId));

      for (const spec of sfSpecs) {
        if (spec.radiusSegId) {
          const segNode = rootGroup.getObjectByName(`segment:${spec.radiusSegId}`);
          if (segNode) {
            if (!showRadiusBeat) {
              segNode.visible = false;
            } else {
              segNode.visible = true;
              segNode.scale.set(1, 1, 1);
              segNode.traverse((ch) => {
                const lineObj = ch as THREE.Line;
                const mat = lineObj.material as THREE.Material | undefined;
                if (!mat || !("opacity" in mat)) return;
                if (typeof lineObj.userData.steadyRadOpacity !== "number") {
                  lineObj.userData.steadyRadOpacity = (mat as THREE.LineBasicMaterial).opacity;
                }
                (mat as THREE.LineBasicMaterial).opacity =
                  (lineObj.userData.steadyRadOpacity as number) * (0.45 + 0.55 * uRadFade);
              });
            }
            segNode.updateMatrixWorld(true);
          }
        }
        if (spec.refPtId) {
          const ptNode =
            rootGroup.getObjectByName(`point:${spec.refPtId}`)
            ?? rootGroup.getObjectByName(`point_marker:${spec.refPtId}`);
          if (ptNode) {
            ptNode.visible = showRadiusBeat;
          }
          const lblEl = nhanRef.current?.querySelector<HTMLElement>(`[data-id="${spec.refPtId}"]`);
          if (lblEl && !showRadiusBeat) {
            lblEl.style.visibility = "hidden";
            lblEl.dataset.sfHidden = "1";
          }
        }
        if (spec.segKey && !showRadiusBeat && soDoRef.current) {
          for (const annEl of soDoRef.current.querySelectorAll<HTMLElement>(
            `[data-ann-seg-key="${spec.segKey}"]`,
          )) {
            annEl.style.visibility = "hidden";
            annEl.dataset.sfHidden = "1";
          }
        }
        const ballNode =
          rootGroup.getObjectByName(`curved:${spec.ballId}:ball`)
          ?? rootGroup.getObjectByName(`curved_solid:${spec.ballId}`);
        if (ballNode) {
          ballNode.traverse((child) => {
            const mesh = child as THREE.Mesh;
            if (!mesh.isMesh || !mesh.userData?.voKhoi) return;
            const mat = mesh.material as THREE.MeshBasicMaterial | undefined;
            if (!mat || mat.colorWrite === false) return;
            if (typeof mesh.userData.steadyShellOpacity !== "number") {
              mesh.userData.steadyShellOpacity = mat.opacity;
              mesh.userData.steadyShellVisible = mesh.visible;
            }
            const steadyVis = mesh.userData.steadyShellVisible !== false;
            const steadyOp = mesh.userData.steadyShellOpacity as number;
            if (!steadyVis || uShell <= 0.01) {
              mesh.visible = false;
            } else {
              mesh.visible = true;
              mat.opacity = uShell >= 0.999 ? steadyOp : Math.max(0.01, steadyOp * uShell);
            }
          });
        }
      }

      const activeSectionCircles: {
        id: string;
        center: Vec3;
        normal: Vec3;
        radius: number;
      }[] = [];
      for (const child of rootGroup.children) {
        if (!child.visible) continue;
        const spec = child.userData?.circleSceneSpec as
          | {
              id: string;
              center: Vec3;
              normal: Vec3;
              radius: number;
              circleRole: string;
              isResultSection: boolean;
            }
          | undefined;
        if (!spec || !spec.isResultSection) continue;
        activeSectionCircles.push({
          id: spec.id,
          center: [child.position.x, child.position.y, child.position.z],
          normal: spec.normal,
          radius: spec.radius,
        });
      }

      const refProjectionDiag: Record<string, { maxOverlap: number; opacityScale: number }> = {};
      rootGroup.traverse((node) => {
        if (!node.name.startsWith("sphere_reference:")) return;
        const eqRim = node.userData?.curvedRimLoop as CurvedRimLoopMeta | undefined;
        const refPol = node.userData?.referenceGreatCirclePolicy as
          | ReturnType<typeof resolveSphereReferenceGreatCirclePolicy>
          | undefined;
        if (!eqRim || !refPol) return;
        const thayMat = eqRim.thayMesh.material as THREE.MeshBasicMaterial | undefined;
        const khuatMat = eqRim.khuatMesh.material as THREE.MeshBasicMaterial | undefined;
        if (!thayMat || !khuatMat) return;
        if (typeof eqRim.thayMesh.userData.steadyRefOpacity !== "number") {
          eqRim.thayMesh.userData.steadyRefOpacity = thayMat.opacity;
        }
        if (typeof eqRim.khuatMesh.userData.steadyRefOpacity !== "number") {
          eqRim.khuatMesh.userData.steadyRefOpacity = khuatMat.opacity;
        }
        const steadyFront = eqRim.thayMesh.userData.steadyRefOpacity as number;
        const steadyHidden = eqRim.khuatMesh.userData.steadyRefOpacity as number;
        const ballId = node.name.slice("sphere_reference:".length);
        const parentPos = node.parent?.position;
        const refCenter: Vec3 = [
          toNumber(refPol.center[0]) + (parentPos?.x ?? 0),
          toNumber(refPol.center[1]) + (parentPos?.y ?? 0),
          toNumber(refPol.center[2]) + (parentPos?.z ?? 0),
        ];
        const refNormal = toVec3(refPol.normal);
        const refRadius = Math.sqrt(Math.max(0, toNumber(refPol.radiusSq)));
        let projScale = 1;
        if (refPol.suppressibleByProjection && refRadius > 1e-6 && activeSectionCircles.length > 0) {
          projScale = computeProjectedCircleOverlapFactor(
            refCenter,
            refNormal,
            refRadius,
            activeSectionCircles,
            {
              matrixWorldInverse: { elements: viewFromScene },
              projectionMatrix: { elements: projElements },
            },
            wCss,
            hCss,
          );
        }
        const prevSmoothed = node.userData.smoothedProjScale as number | undefined;
        const smoothedProjScale =
          typeof prevSmoothed === "number" && sphereFormationRef.current.overrideProgress === null
            ? prevSmoothed + 0.35 * (projScale - prevSmoothed)
            : projScale;
        node.userData.smoothedProjScale = smoothedProjScale;
        const maxOverlap = Number((1 - smoothedProjScale).toFixed(4));
        const shellScale = formingBallIds.has(ballId) ? uShell : 1;
        const effectiveScale = smoothedProjScale * shellScale;
        thayMat.opacity = effectiveScale <= 0.01 ? 0 : steadyFront * effectiveScale;
        khuatMat.opacity = effectiveScale <= 0.01 ? 0 : steadyHidden * effectiveScale;
        refProjectionDiag[ballId] = {
          maxOverlap,
          opacityScale: Number(effectiveScale.toFixed(4)),
        };
      });

      if (typeof window !== "undefined") {
        (window as any).__geo3d_sphere_formation_state = {
          progress: Number(formProg.toFixed(3)),
          uRad: Number((showRadiusBeat ? uRadFade : 0).toFixed(3)),
          showRefPt: showRadiusBeat,
          uShell: Number(uShell.toFixed(3)),
          ballIds: [...formingBallIds],
        };
        (window as any).__geo3d_sphere_ref_projection_state = refProjectionDiag;
      }
    };

    let rafId = 0;
    const isAnimationActive = (controlsChanged: boolean): boolean => {
      if (controlsChanged || controlsInteracting) return true;
      const nowMs = typeof performance !== "undefined" ? performance.now() : Date.now();
      if (nowMs - lastInteractionWakeMs < 260) return true;
      if (currentStepPulse() > 0) return true;
      const sf = sphereFormationRef.current;
      if (sf.overrideProgress === null && sf.durationMs > 0 && nowMs - sf.startMs < sf.durationMs + 40) {
        return true;
      }
      return false;
    };
    const renderSingleFrame = (updateControls: boolean): boolean => {
      let controlsMoved = false;
      if (updateControls) {
        const truocPos = cam.position.clone();
        const truocQuat = cam.quaternion.clone();
        controlsMoved = dieuKhien.update();
        if (!controlsMoved) {
          cam.position.copy(truocPos);
          cam.quaternion.copy(truocQuat);
        }
      }
      cam.updateMatrixWorld();
      const wCss = renderer.domElement.clientWidth || 1;
      const hCss = renderer.domElement.clientHeight || 1;
      const stepPulse = currentStepPulse();
      capNhatVongThamChieuVaHinhThanhMatCau(goc, cam, wCss, hCss);
      datCoDauDinh(goc, cam, wCss, hCss, stepPulse);
      datCoDauDinh(nhanChung, cam, wCss, hCss, stepPulse);
      const edgeAudit = updateCanonicalEdgeVisibility(
        goc,
        cam,
        `${renderer.domElement.clientWidth}x${renderer.domElement.clientHeight}`
          + `@${renderer.getPixelRatio()}`,
      );
      if (typeof window !== "undefined") {
        (window as any).__geo3d_step_highlight_state = {
          step: stepEntranceRef.current.step,
          newIds: stepEntranceRef.current.newIds,
          depIds: stepEntranceRef.current.depIds,
          pulse: Number(stepPulse.toFixed(3)),
          reducedMotion: stepEntranceRef.current.reducedMotion,
        };
        (window as any).__geo3d_visible_edge_ids = edgeAudit.visible_edge_ids;
        (window as any).__geo3d_hidden_edge_ids = edgeAudit.hidden_edge_ids;
        (window as any).__geo3d_mixed_edge_ids = edgeAudit.mixed_edge_ids;
        (window as any).__geo3d_duplicate_visual_owner_ids =
          edgeAudit.duplicate_visual_owner_ids;
        (window as any).__geo3d_edge_spans = edgeAudit.edge_spans;
        (window as any).__geo3d_camera_target = dieuKhien.target.toArray();
        const khungT = tRef.current;
        const coXoay = !qRef.current.equals(DONG_NHAT) || khungT !== null;
        const model = khungT ? new THREE.Matrix4().fromArray(khungT).premultiply(goc.matrixWorld) : goc.matrixWorld;
        (window as any).__geo3d_camera_snapshot = {
          position: cam.position.toArray(),
          near: cam.near, far: cam.far,
          min_distance: dieuKhien.minDistance, max_distance: dieuKhien.maxDistance,
          // Observability criterion (axo-end-to-end-authority-scene3d-usability): distance ≥ 2 × support of the main solid.
          support_along_view: khoangTuaHienTai ?? capNhatGioiHanGan(cam, dieuKhien),
          view_matrix_column_major: [...(coXoay
            ? new THREE.Matrix4().multiplyMatrices(cam.matrixWorldInverse, model)
            : cam.matrixWorldInverse).elements],
          ...(coXoay ? { model_matrix_column_major: [...model.elements] } : {}),
          projection_matrix_column_major: [...cam.projectionMatrix.elements],
          viewport_width: renderer.domElement.clientWidth,
          viewport_height: renderer.domElement.clientHeight,
          device_pixel_ratio: renderer.getPixelRatio(),
        };
        (window as any).__geo3d_highlighted_render_owner_ids =
          edgeAudit.highlighted_render_owner_ids;
        const dashSignature: Record<string, string[]> = {};
        goc.traverse((node) => {
          const ownerId = node.userData?.visualOwnerId as string | undefined;
          if (!ownerId || !(node as THREE.Group).isGroup) return;
          dashSignature[ownerId] = node.children.map((child) =>
            child.userData?.hidden === true ? "HIDDEN_DASHED" : "VISIBLE_SOLID");
        });
        (window as any).__geo3d_edge_dash_signature = dashSignature;
        const cham: { id: string | null; state: string; center: number[]; radius_world: number }[] = [];
        const tam = new THREE.Vector3();
        const ti = new THREE.Vector3();
        goc.traverse((node) => {
          if (!node.userData?.dauDinh) return;
          node.getWorldPosition(tam);
          if (coXoay) goc.worldToLocal(tam);
          if (khungT) tam.applyMatrix4(new THREE.Matrix4().fromArray(khungT).invert());
          node.getWorldScale(ti);
          cham.push({ id: pickSemanticId(node), state: node.userData.dauDinh, center: tam.toArray(),
            radius_world: ((node as THREE.Mesh).geometry as THREE.SphereGeometry).parameters.radius * ti.x });
        });
        (window as any).__geo3d_vertex_markers = cham;
        const perf = goc.userData.occlusionPerformance ?? {
          frame_count: 0, recompute_count: 0, recomputation_times_ms: [],
          edge_count: 0, triangle_count: 0, sample_count: 0, span_count: 0,
        };
        perf.frame_count += 1;
        perf.recompute_count += edgeAudit.recomputed_solid_count;
        if (edgeAudit.recomputed_solid_count > 0) {
          perf.recomputation_times_ms.push(edgeAudit.recomputation_ms);
        }
        perf.edge_count = edgeAudit.edge_count;
        perf.triangle_count = edgeAudit.triangle_count;
        perf.sample_count = edgeAudit.sample_count;
        perf.span_count = edgeAudit.span_count;
        goc.userData.occlusionPerformance = perf;
        (window as any).__geo3d_occlusion_performance = { ...perf };
        (window as any).__geo3d_reset_occlusion_performance = () => {
          goc.userData.occlusionPerformance = {
            frame_count: 0, recompute_count: 0, recomputation_times_ms: [],
            edge_count: 0, triangle_count: 0, sample_count: 0, span_count: 0,
          };
        };
      }
      const warmGroup = warmSpanPools(goc, scene3);
      if (warmGroup) scene3.add(warmGroup);
      datCoGocVuong([goc, nhanChung], cam, hCss, dieuKhien.target, rightAnglesShownRef.current);
      capNhatDauSongSong(goc, cam);
      const undoHover = applyHoverFeedback(goc, hoverFeedbackRef.current.id, hoverFeedbackRef.current.edges);
      const fatSummary = dongBoNetDayManHinh([goc, nhanChung], netDay, wCss, hCss, dashedHiddenShownRef.current, stepPulse, tinhZoomDashScale());
      if (typeof window !== "undefined") {
        (window as any).__geo3d_fat_line_summary = {
          totalLines: fatSummary.totalLines,
          maxSectionBorderWidth: fatSummary.maxSectionBorderWidth,
          maxVisibleEdgeWidth: fatSummary.maxVisibleEdgeWidth,
          minHiddenEdgeWidth: fatSummary.minHiddenEdgeWidth,
        };
      }
      const anTam = [...fatSummary.sourceLines, ...fatSummary.sourceRimObjects];
      for (const l of anTam) l.visible = false;
      renderer.render(scene3, cam);
      undoHover();
      for (const l of anTam) l.visible = true;
      if (warmGroup) scene3.remove(warmGroup);
      chieuNhan();
      return controlsMoved;
    };
    const vong = () => {
      rafId = 0;
      if (!song) return;
      const moved = renderSingleFrame(true);
      if (song && isAnimationActive(moved)) {
        // controls.update() may already have queued the next frame through its change event.
        wakeRenderLoop();
      } else if (song && userAdjustedCamera) {
        baoCaoCameraPose();
      }
    };
    wakeRenderLoop = () => {
      if (song && rafId === 0) {
        rafId = requestAnimationFrame(vong);
      }
    };
    veRef.current = () => {
      if (!song) return;
      const moved = renderSingleFrame(false);
      if (isAnimationActive(moved)) {
        wakeRenderLoop();
      }
    };
    (window as any).__geo3d_set_sphere_formation_progress = (p: number | null) => {
      sphereFormationRef.current.overrideProgress =
        typeof p === "number" && Number.isFinite(p) ? Math.max(0, Math.min(1, p)) : null;
      veRef.current?.();
      chieuNhan();
    };
    // Móc ĐO của cổng ảnh `SECTION_FILL_DISTINGUISHABLE` — chỉ harness gọi, người học không
    // thấy (mặc định bật). Tắt/bật phần tô rồi vẽ lại ĐÚNG khung hình này; trả tên các vật
    // đã chạm — rỗng thì không có gì để đo, cổng phải tự đỏ.
    (window as any).__geo3d_set_section_fill_visible = (on: boolean) => {
      const ten = datHienToThietDien(goc, on);
      const wCss = renderer.domElement.clientWidth || 1;
      const hCss = renderer.domElement.clientHeight || 1;
      datCoGocVuong([goc, nhanChung], cam, hCss, dieuKhien.target, rightAnglesShownRef.current);
      capNhatDauSongSong(goc, cam);
      const fatSummary = dongBoNetDayManHinh([goc, nhanChung], netDay, wCss, hCss, dashedHiddenShownRef.current, 0, tinhZoomDashScale());
      const anTam = [...fatSummary.sourceLines, ...fatSummary.sourceRimObjects];
      for (const l of anTam) l.visible = false;
      renderer.render(scene3, cam);
      for (const l of anTam) l.visible = true;
      return ten;
    };

    const tinhTuyChonKhung = (diem: Vec3[], huong: [number, number, number], w: number, _h: number) => {
      const tiLeCR = tiLeHinhChieu(diem, huong) ?? 1;
      const dsVat = sceneRef.current.objects;
      const coMatCat = dsVat.some(
        (o) => o.type === "plane3" || o.type === "section" || o.type === "circle3" || o.type === "ellipse3",
      );
      const cRect = container.getBoundingClientRect();
      const panelEl = typeof document !== "undefined" ? document.getElementById("geo3d-bang-phan-tich") : null;
      const pRect = panelEl?.getBoundingClientRect();
      const coPanelPhai = Boolean(
        pRect && pRect.width > 0 && cRect.width > 0 && pRect.left < cRect.right && pRect.left > cRect.left,
      );
      const laKhungHep = w <= 680;
      const padX = laKhungHep ? 14 : 24;
      const safeLeft = cRect.left + padX;
      const safeRight = coPanelPhai ? Math.max(cRect.left + w * 0.36, pRect!.left - 28) : cRect.right - padX;
      const safeWidthRatio = cRect.width > 0
        ? Math.max(0.32, Math.min(1, (safeRight - safeLeft) / Math.max(1, w)))
        : 1;
      const safeCenterX = (safeLeft + safeRight) / 2;
      const dichTamNgang = coPanelPhai && cRect.width > 0
        ? (safeCenterX - (cRect.left + w / 2)) / Math.max(1, w / 2)
        : 0;
      let tiLeDoc = 0.67;
      if (tiLeCR > 1.15) tiLeDoc = 0.64;
      if (coMatCat) tiLeDoc = Math.min(tiLeDoc, 0.65);
      if (w < 900) tiLeDoc = Math.min(tiLeDoc, laKhungHep ? 0.66 : 0.60);
      if (coPanelPhai) tiLeDoc = Math.min(tiLeDoc, 0.62);
      const paEl = typeof document !== "undefined" ? document.getElementById("playback-pa-box") : null;
      const tbEl = typeof document !== "undefined" ? document.getElementById("floating-toolbar-3d") : null;
      const coCapsuleDay = Boolean(
        (paEl && paEl.getBoundingClientRect().height > 0) || (tbEl && tbEl.getBoundingClientRect().height > 0),
      );
      if (coCapsuleDay && cRect.height > 0 && cRect.height < 680 && !laKhungHep) {
        tiLeDoc = Math.min(tiLeDoc, 0.61);
      }
      let dichTamDoc = coCapsuleDay ? (cRect.height > 0 && cRect.height < 680 ? 0.05 : 0.035) : 0.02;
      if (coCapsuleDay && cRect.width > 0 && cRect.height > 0) {
        const centerLeft = cRect.left + cRect.width * (laKhungHep ? 0.16 : 0.32);
        const centerRight = cRect.right - cRect.width * (laKhungHep ? 0.16 : 0.32);
        let capsuleCenterTop = cRect.bottom;
        for (const el of [paEl, tbEl]) {
          if (!el) continue;
          const r = el.getBoundingClientRect();
          if (r.width <= 0 || r.height <= 0) continue;
          if (r.right > centerLeft && r.left < centerRight && r.top > cRect.top + cRect.height * 0.42 && r.top < cRect.bottom) {
            capsuleCenterTop = Math.min(capsuleCenterTop, r.top);
          }
        }
        if (capsuleCenterTop < cRect.bottom - 8) {
          const safeTop = cRect.top + (laKhungHep ? 14 : 28);
          const safeBottom = Math.max(safeTop + (laKhungHep ? 110 : 100), capsuleCenterTop - (laKhungHep ? 14 : 22));
          const availRatio = (safeBottom - safeTop) / cRect.height;
          tiLeDoc = Math.min(tiLeDoc, Math.max(laKhungHep ? 0.50 : 0.38, availRatio * (laKhungHep ? 0.88 : 0.84)));
          const midY = cRect.top + cRect.height / 2;
          const safeMidY = (safeTop + safeBottom) / 2;
          dichTamDoc = Math.max(dichTamDoc, Math.min(0.32, (midY - safeMidY) / Math.max(1, cRect.height / 2)));
        }
      }
      const tiLeNgang = coPanelPhai
        ? Math.min(0.58, safeWidthRatio * 0.78)
        : Math.min(laKhungHep ? 0.80 : 0.74, safeWidthRatio * (laKhungHep ? 0.88 : 0.82));
      return {
        tiLeDoc,
        tiLeNgang,
        dichTamNgang,
        dichTamDoc,
      };
    };

    const tinhTamVaDiemCanh = () => {
      const tt = tuongTacRef.current;
      const dsTatCa = sceneRef.current.objects;
      const dsLoc = tt.isolated_ids.length > 0
        ? dsTatCa.filter((o) => tt.isolated_ids.includes(o.id))
        : dsTatCa;
      const dsNguon = dsLoc.length > 0 ? dsLoc : dsTatCa;
      const bienDoi = (p: Vec3, id: string): Vec3 => {
        const dich = visualTransformOf(tt, sceneRef.current, id).translate;
        return xoay([p[0] + dich[0], p[1] + dich[1], p[2] + dich[2]], qRef.current);
      };
      const byIdNguon = new Map(dsTatCa.map((x) => [x.id, x]));
      const infoTam = tinhTamXoayOnDinh(dsNguon, bienDoi);
      const diemNenNguon = diemHuuHan(dsNguon.filter((x) => !laDiemPhuDungMatPhang(sceneRef.current, x, byIdNguon)));
      const clampToSolidRadius = (ptWorld: Vec3): Vec3 => {
        if (!infoTam || !(infoTam.banKinhKhoi > 1e-5)) return ptWorld;
        const dx = ptWorld[0] - infoTam.tamXoay[0];
        const dy = ptWorld[1] - infoTam.tamXoay[1];
        const dz = ptWorld[2] - infoTam.tamXoay[2];
        const d = Math.hypot(dx, dy, dz);
        const maxR = infoTam.banKinhKhoi * 1.28;
        if (d <= maxR || d <= 1e-9) return ptWorld;
        const k = maxR / d;
        return [
          infoTam.tamXoay[0] + dx * k,
          infoTam.tamXoay[1] + dy * k,
          infoTam.tamXoay[2] + dz * k,
        ];
      };
      const diemCoBan: Vec3[] = [];
      for (const o of dsNguon) {
        if (laDiemPhuDungMatPhang(sceneRef.current, o, byIdNguon)) continue;
        for (const p of diemHuuHan([o])) diemCoBan.push(bienDoi(p, o.id));
        if (o.type === "line3" && o.point && o.direction) {
          const span = resolveLineDisplaySpan(sceneRef.current, o, dsNguon, diemNenNguon);
          if (span?.mode !== "no_intersection") {
            const endpoints = span
              ? span.endpoints
              : doanDuongThang(toVec3(o.point), toVec3(o.direction), diemNenNguon);
            if (endpoints) {
              diemCoBan.push(
                clampToSolidRadius(bienDoi(endpoints[0], o.id)),
                clampToSolidRadius(bienDoi(endpoints[1], o.id)),
              );
            }
          }
        }
      }
      const diem = tt.exploded_groups.length > 0
        ? diemVuaKhung(goc, diemCoBan)
        : diemCoBan.length > 0
          ? diemCoBan
          : diemVuaKhung(goc, []);
      return { dsNguon, infoTam, diem };
    };

    const vungAnToanTuTuyChon = (tc: {
      tiLeDoc: number;
      tiLeNgang: number;
      dichTamNgang: number;
      dichTamDoc: number;
    }): VungAnToanNdc => ({
      xMin: Math.max(-0.88, -tc.tiLeNgang),
      xMax: Math.min(0.88, tc.tiLeNgang),
      yMin: Math.max(-0.86, -tc.tiLeDoc),
      yMax: Math.min(0.86, tc.tiLeDoc),
    });

    const sanKhau = container.closest(".geo3d-san") ?? container.parentElement;
    let trangThaiPanelTruoc = Boolean(
      typeof document !== "undefined" && document.getElementById("geo3d-bang-phan-tich"),
    );
    const moPanel = typeof MutationObserver !== "undefined" && sanKhau
      ? new MutationObserver(() => {
          const hienTaiPanel = Boolean(document.getElementById("geo3d-bang-phan-tich"));
          if (hienTaiPanel !== trangThaiPanelTruoc) {
            trangThaiPanelTruoc = hienTaiPanel;
            chinhCo();
            veRef.current?.();
          }
        })
      : null;
    if (moPanel && sanKhau) {
      moPanel.observe(sanKhau, { childList: true, subtree: true });
    }

    // ── ĐẶT KHUNG NHÌN CHO VỪA HÌNH ────────────────────────────────────
    vuaKhungRef.current = () => {
      const savedPose = pendingRestoredCameraRef.current;
      userAdjustedCamera = false;
      const { dsNguon, infoTam, diem } = tinhTamVaDiemCanh();
      if (diem.length === 0) return;
      const ct = cauTrucSuPham(dsNguon, qRef.current);
      const huong = ct.canh.length > 0
        ? chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon)
        : ([8, 5, 6] as [number, number, number]);
      const w0 = container.clientWidth || 640;
      const h0 = container.clientHeight || 420;
      const tc = tinhTuyChonKhung(diem, huong, w0, h0);
      lechOngKinhNgang = tc.dichTamNgang;
      lechOngKinhDoc = tc.dichTamDoc;
      chinhCo();
      const w = renderer.domElement.clientWidth || 1;
      const h = renderer.domElement.clientHeight || 1;
      const kn = (infoTam
        ? khungNhinQuanhTam(diem, infoTam.tamXoay, cam.fov, w / h, huong, vungAnToanTuTuyChon(tc))
        : khungNhinSuPham(diem, [], [], cam.fov, w / h, huong, { ...tc, dichTamDoc: 0 }))
        ?? khungNhinVua(hopBaoCuaDiem(diem), cam.fov, w / h);
      if (!kn) return;
      dangDatKhungTuDong = true;
      try {
        datKhungNhin(cam, dieuKhien, kn, infoTam ? { banKinhKhoi: infoTam.banKinhKhoi, tam: infoTam } : undefined);
        // A recovered pose still needs the scene's fit-derived zoom and clipping bounds, not OrbitControls' 0..Infinity.
        if (savedPose && hopLeCameraPose(savedPose)) {
          pendingRestoredCameraRef.current = null;
          cam.position.set(...savedPose.position);
          dieuKhien.target.set(...savedPose.target);
          dieuKhien.update();
          userAdjustedCamera = true;
        }
        kcKhungChuan = cam.position.clone().sub(dieuKhien.target).length();
      } finally {
        dangDatKhungTuDong = false;
      }
      scheduleCommitRender();
    };

    scheduleCommitRender();

    return () => {
      if (userAdjustedCamera && !contextLostObserved) {
        baoCaoCameraPose();
      }
      song = false;
      awaitingContextRestore = false;
      if (rafId !== 0) {
        cancelAnimationFrame(rafId);
        rafId = 0;
      }
      if (restoreTimeoutId !== null) {
        clearTimeout(restoreTimeoutId);
        restoreTimeoutId = null;
      }
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", xuLyDoiTrangThaiTab);
      }
      renderer.domElement.removeEventListener("wheel", xuLyDoiDieuKhien);
      container.removeEventListener("wheel", chuyenWheelVeCanvas);
      renderer.domElement.removeEventListener("webglcontextlost", xuLyMatNguCanhWebgl);
      renderer.domElement.removeEventListener("webglcontextrestored", xuLyKhoiPhucNguCanhWebgl);
      dieuKhien.removeEventListener("start", danhDauNguoiDungChinhCam);
      dieuKhien.removeEventListener("change", xuLyDoiDieuKhien);
      dieuKhien.removeEventListener("change", capNhatGioiHanTheoHuong);
      dieuKhien.removeEventListener("end", xuLyKetThucDieuKhien);
      renderer.domElement.removeEventListener("pointerdown", xuongTay);
      renderer.domElement.removeEventListener("pointerup", nhacTay);
      renderer.domElement.removeEventListener("pointermove", diConTro);
      renderer.domElement.removeEventListener("pointerleave", roiConTro);
      window.removeEventListener("resize", xuLyDoiCoKhung);
      roKhung?.disconnect();
      moPanel?.disconnect();
      dieuKhien.dispose();
      const warmHold = scene3.userData.warmHoldGroup as THREE.Group | undefined;
      if (warmHold) disposeScene3DObject(warmHold);
      for (const group of [goc, nhanChung, luoi, truc, netDay]) disposeScene3DObject(group);
      trucRef.current = null;
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
      releaseSceneWebGLRenderer(renderer, isPooledRenderer, contextLostObserved);
      rootRef.current = null;
      nhanChungRef.current = null;
      luoiRef.current = null;
      veRef.current = null;
      vuaKhungRef.current = null;
      if (typeof window !== "undefined") {
        for (const k of [
          "__geo3d_set_section_fill_visible",
          "__geo3d_set_sphere_formation_progress",
          "__geo3d_sphere_formation_state",
          "__geo3d_sphere_ref_projection_state",
          "__geo3d_annotation_boxes",
          "__geo3d_annotation_unplaced",
          "__geo3d_annotation_hidden_edge_ids",
          "__geo3d_point_label_boxes",
          "__geo3d_plane_label_boxes",
          "__geo3d_step_highlight_state",
          "__geo3d_visible_edge_ids",
          "__geo3d_hidden_edge_ids",
          "__geo3d_mixed_edge_ids",
          "__geo3d_duplicate_visual_owner_ids",
          "__geo3d_edge_spans",
          "__geo3d_camera_target",
          "__geo3d_camera_snapshot",
          "__geo3d_highlighted_render_owner_ids",
          "__geo3d_edge_dash_signature",
          "__geo3d_vertex_markers",
          "__geo3d_occlusion_performance",
          "__geo3d_reset_occlusion_performance",
          "__geo3d_fat_line_summary",
          "__geo3d_witness_ids",
          "__geo3d_grid_visible",
          "__geo3d_grid_subordinated",
          "__geo3d_axes_visible",
          "__geo3d_rendered_object_ids",
          "__geo3d_geometry_build_count",
          "__geo3d_contract_reference_ids",
          "__geo3d_hovered_object_id",
          "__geo3d_hovered_section_id",
          "__geo3d_auxiliary_hidden_ids",
          "__geo3d_causal_tiers",
          "__geo3d_step_visual_roles",
          "__geo3d_shell_visible",
          "__geo3d_plane_visible",
          "__geo3d_section_visible",
          "__geo3d_shell_opacity_pct",
          "__geo3d_plane_opacity_pct",
          "__geo3d_right_angles_visible",
          "__geo3d_dashed_hidden_visible",
          "__geo3d_selected_id",
          "__geo3d_highlighted_ids",
          "__geo3d_selection_highlight_ids",
        ]) {
          delete (window as any)[k];
        }
      }
    };
  }, [webglEpoch, webglFailed]);

  // §16.7 — nhân chứng của các nhãn khoảng cách ĐANG HIỆN (chọn, hoặc "Hiện tất cả"): đoạn tới chân
  // + ký hiệu vuông góc. Không thêm bước dựng, không chạm nhóm gốc, nét đứt hay camera.
  useEffect(() => {
    const nhom = nhanChungRef.current;
    if (!nhom) return;
    for (const con of [...nhom.children]) {
      nhom.remove(con);
      disposeScene3DObject(con);
    }
    // Review I1: cộng đoạn vuông góc PHỤ của điểm hình chiếu đã có mặt ở bước này — cùng cách vẽ, chân do backend phát.
    const diemToanCanh = diemHuuHan(scene.objects);
    // Mặt phẳng "chỉ để đo" (`measurementOnlyPlanes`: mặt của chính khối, ẩn khỏi khung vì đã có trên hình) vẫn là chủ
    // thể HIỆN của nhân chứng: SA ⊥ (ABCD), BC ⊥ (SAB) đặt dấu trên mặt khối đang thấy. Ẩn/cô lập của người xem vẫn áp.
    const mpDo = measurementOnlyPlanes(scene);
    const coMatNhanChung = new Set([...coMatNhan,
      ...objectsAt(scene, buoc).filter((o) => mpDo.has(o.id)).map((o) => o.id)]);
    const hienNhanChung = new Set([...coMatNhanChung].filter((id) => isVisible(tuongTac, id, coMatNhanChung)));
    const tuSoDo = witnessesShown(scene, nhanSoDo);
    const daCoSoDo = new Set(tuSoDo.map((w) => w.id));
    const tuChieu = projectionWitnessesAt(scene, hienNhanChung, !tang ? buoc : undefined)
      .filter((w) => !daCoSoDo.has(w.id.slice("perpendicular:".length)));
    // Chế độ A không lộ đáp số: dấu vuông góc của một GÓC đo được CHÍNH LÀ đáp số (90°), nên ẩn cùng nhãn của nó.
    // Nhân chứng khoảng cách thì không — chân đường vuông góc là cách dựng, không phải con số.
    const laDapSoAn = (id: string) => annotationView.hiddenIds?.has(id) === true
      && scene.objects.some((o) => o.id === id && o.annotation?.kind === "angle");
    const ds = [...tuSoDo, ...tuChieu]
      .filter((w) => !laDapSoAn(w.vai === "hinh_chieu" ? w.id.slice("perpendicular:".length) : w.id));
    const doanCo = doanDaVe(scene.objects);
    const diemCoTen = objectsAt(scene, buoc).flatMap((o) => (o.type === "point3" && o.xyz ? [toVec3(o.xyz)] : []));
    for (const w of ds) {
      const chuId = w.vai === "hinh_chieu" ? w.id.slice("perpendicular:".length) : w.id;
      const ptWitness = w.vai === "hinh_chieu"
        ? scene.objects.find((x) => x.id === chuId)?.perpendicular_witness
        : undefined;
      const coveredByVisiblePerpSeg =
        w.vai === "hinh_chieu"
        && scene.objects.some((o) => {
          if (o.type !== "segment3" || !coMatNhan.has(o.id)) return false;
          const pw = o.perpendicular_witness ?? o.annotation?.witness;
          if (!pw) return false;
          const segRefs = o.endpoint_ids ?? o.depends ?? [];
          const matchesFoot = pw.foot_id === chuId || segRefs.includes(chuId);
          if (!matchesFoot) return false;
          if (ptWitness?.from) {
            const matchesFrom = pw.from === ptWitness.from || segRefs.includes(ptWitness.from);
            if (!matchesFrom) return false;
          }
          if (ptWitness?.on && pw.on && pw.on !== ptWitness.on) {
            return false;
          }
          return true;
        });
      if (coveredByVisiblePerpSeg) continue;
      if (w.vai === "khoang_cach") {
        const coveredByDistSeg = scene.objects.some((o) => {
          if (o.type !== "segment3" || !coMatNhan.has(o.id)) return false;
          const pw = o.perpendicular_witness ?? o.annotation?.witness;
          if (!pw) return false;
          const pa = o.point_a ?? o.endpoints?.[0];
          const pb = o.point_b ?? o.endpoints?.[1];
          if (!pa || !pb) return false;
          const va = toVec3(pa), vb = toVec3(pb);
          const dFromA = Math.hypot(va[0] - w.from[0], va[1] - w.from[1], va[2] - w.from[2]);
          const dFootB = Math.hypot(vb[0] - w.foot[0], vb[1] - w.foot[1], vb[2] - w.foot[2]);
          const dFromB = Math.hypot(vb[0] - w.from[0], vb[1] - w.from[1], vb[2] - w.from[2]);
          const dFootA = Math.hypot(va[0] - w.foot[0], va[1] - w.foot[1], va[2] - w.foot[2]);
          return (dFromA < 1e-4 && dFootB < 1e-4) || (dFromB < 1e-4 && dFootA < 1e-4);
        });
        if (coveredByDistSeg) continue;
      }
      const t = tang?.get(chuId);
      const dangDungDiem = !tang && tapNoiBat.has(chuId) && loaiRef.current.get(chuId) === "point3";
      const mauGocNhanChung = mauNhanChung(w.vai);
      const mau = (t && t !== "boi_canh") || dangDungDiem
        ? modulateSemanticColor(mauGocNhanChung, "selected")
        : undefined;
      const diu = Boolean(tang && !t);
      nhom.add(vatNhanChung(w, diemToanCanh, mau, diu, doanCo, diemCoTen));
    }
    if (typeof window !== "undefined") (window as any).__geo3d_witness_ids = ds.map((w) => w.id);
    scheduleCommitRender();
  }, [scene, buoc, nhanSoDo, coMatNhan, tuongTac, tang, tapNoiBat, annotationView.hiddenIds, webglEpoch]);

  const heSoDiuLuoi = useMemo(() => {
    const daTonTai = entitiesPresentAt(scene, buoc, objectsAt);
    const matPhangHien = scene.objects.filter(
      (o) =>
        planeShown
        && o.type === "plane3"
        && daTonTai.has(o.id)
        && isVisible(tuongTac, o.id, daTonTai)
        && !anPhu.has(o.id)
        && (quyetDinhMatPhang.get(o.id)?.visible ?? true),
    );
    if (matPhangHien.length === 0) return 1;
    const coMpNgang = matPhangHien.some((o) => {
      if (!o.normal) return false;
      const n = xoay(toVec3(o.normal), qHienThi);
      return Math.hypot(n[0], n[1]) <= 1e-4 * Math.abs(n[2]);
    });
    if (coMpNgang) return 0.38;
    const dangNhanMp = matPhangHien.some(
      (o) => tuongTac.selected_id === o.id || tapNoiBat.has(o.id) || (tang?.has(o.id) && tang.get(o.id) !== "boi_canh"),
    );
    return dangNhanMp ? 0.55 : 0.78;
  }, [scene, buoc, tuongTac, anPhu, quyetDinhMatPhang, qHienThi, tapNoiBat, tang, planeShown]);

  // W2 · F — LƯỚI NỀN tuỳ chọn: mảnh, nhạt, nằm dưới đáy hình (mặt z thấp nhất của cảnh), ô theo cỡ cảnh — không
  // số toạ độ, không đơn vị. Bật/tắt chỉ thêm/bớt nhóm này rồi vẽ lại một khung: camera, bước, lựa chọn không đổi.
  useEffect(() => {
    const nhom = luoiRef.current;
    if (!nhom) return;
    for (const con of [...nhom.children]) {
      nhom.remove(con);
      con.traverse((x) => {
        const l = x as THREE.LineSegments;
        l.geometry?.dispose?.();
        (l.material as THREE.Material | undefined)?.dispose?.();
      });
    }
    // Lưới nằm dưới hình NGƯỜI HỌC THẤY: lấy toạ độ sau phép xoay hiển thị (nhóm lưới không xoay).
    const diem = diemHuuHan(scene.objects).map((p) => xoay(p, qHienThi));
    if (gridShown && diem.length > 0) {
      nhom.add(dungLuoiNenSuPham(diem, heSoDiuLuoi));
    }
    if (typeof window !== "undefined") {
      (window as any).__geo3d_grid_visible = nhom.children.length > 0;
      (window as any).__geo3d_grid_subordinated = heSoDiuLuoi < 1;
    }
    scheduleCommitRender();
  }, [scene, gridShown, qHienThi, heSoDiuLuoi, webglEpoch]);

  useEffect(() => {
    const nhom = trucRef.current;
    if (!nhom) return;
    for (const con of [...nhom.children]) {
      nhom.remove(con);
      disposeScene3DObject(con);
    }
    const diem = diemHuuHan(scene.objects).map((p) => xoay(p, qHienThi));
    if (axesShown) {
      nhom.add(dungTrucOxyzSuPham(diem));
    }
    if (typeof window !== "undefined") {
      (window as any).__geo3d_axes_visible = nhom.children.length > 0;
    }
    scheduleCommitRender();
  }, [scene, axesShown, qHienThi, webglEpoch]);

  // §16.5 — nhãn số đo BẤM ĐƯỢC (chuột, Enter/Space): bấm là chọn đại lượng, bấm lại là bỏ chọn.
  // Listener gắn bằng lệnh (lớp này không dùng prop sự kiện trong JSX — khoá ở `scene3d.test.tsx`).
  useEffect(() => {
    const lop = soDoRef.current;
    if (!lop) return;
    const chonNhan = (e: Event) => {
      const id = (e.target as HTMLElement | null)?.closest<HTMLElement>("[data-ann-id]")?.dataset.annId;
      if (!id || !chonRef.current) return;
      if (e instanceof KeyboardEvent) {
        if (e.key !== "Enter" && e.key !== " ") return;
        e.preventDefault();
      }
      chonRef.current(chonHienTai.current === id ? null : id);
    };
    lop.addEventListener("click", chonNhan);
    lop.addEventListener("keydown", chonNhan);
    return () => {
      lop.removeEventListener("click", chonNhan);
      lop.removeEventListener("keydown", chonNhan);
    };
  }, [webglFailed]);

  // Đổi bước ⇒ dựng lại nội dung nhóm gốc. Rẻ vì cảnh nhỏ (≤ vài chục mesh).
  useEffect(() => {
    const goc = rootRef.current;
    if (!goc) return;
    goc.quaternion.copy(qHienThi);
    nhanChungRef.current?.quaternion.copy(qHienThi);
    goc.userData.spanPoolsWarmed = false;
    for (const con of [...goc.children]) {
      goc.remove(con);
      disposeScene3DObject(con);
    }
    viTriNhan.current.clear();
    viTriMatPhang.current.clear();
    gocMatPhangRef.current.clear();
    const noiBat = tapNoiBat;
    // MỘT thẩm quyền "vật nào đang có mặt", dùng chung với cây phân rã.
    //
    // Bản trước hỏi thẳng `objectsAt` ở đây còn cây hỏi `entitiesPresentAt`.
    // Hai phép khác nhau: mặt và cạnh KHÔNG có sự kiện timeline riêng, nên
    // `objectsAt` bỏ chúng ra — cây liệt kê được mặt mà khung nhìn không dựng
    // mặt nào, và raycast chỉ còn trúng khối. Demo tay bắt đúng chuyện đó.
    const daTonTai = entitiesPresentAt(scene, buoc, objectsAt);
    const hienTai = scene.objects.filter((o) => daTonTai.has(o.id));
    const progressById = new Map(
      (scene.formation?.steps[buoc]?.geometry_progress ?? [])
        .map((progress) => [progress.object_id, progress]),
    );
    // Cạnh chuẩn tô QUA vật khác (đoạn/đáy trùng cạnh) mang màu tầng của vật ấy;
    // hai vật cùng trỏ một cạnh thì tầng mạnh hơn thắng. Ngữ cảnh cấu trúc
    // không tô cạnh nào — nét của nó giữ mực trung tính (w11).
    const tangCua = (id: string) => tang?.get(id);
    const vatTheoId = new Map(scene.objects.map((x) => [x.id, x]));
    const mucMau = (id: string) => {
      const src = vatTheoId.get(id);
      return src
        ? classifySceneObjectSemantics(scene, src, buoc, id, null).strokeColor
        : modulateSemanticColor(MAU.canh, "selected");
    };
    const doManh = (id: string) => ["trung_gian", "du_kien_so", "dich"].indexOf(tangCua(id) ?? "");
    const seDung = hienTai.filter(
      (o) =>
        isVisible(tuongTac, o.id, daTonTai)
        && veTrenKhung(o)
        && !anPhu.has(o.id)
        && !ungroundedPts.has(o.id)
        && (stepVisualRoles.get(o.id)?.visible ?? true),
    );
    const laCanhNguNghiaMacDinh = (id: string) => {
      const src = vatTheoId.get(id);
      if (!src || (src.type !== "segment3" && src.type !== "line3")) return false;
      const roles = src.formation_roles ?? [];
      return (
        Boolean(src.perpendicular_witness || src.annotation?.witness)
        || roles.includes("CONSTRUCT_HEIGHT")
        || isIntersectionLineOrSegment(src, scene)
        || isPrimarySpatialLine(src, scene)
      );
    };
    const { ca: defaultEdgeColors, khuc: defaultKhuc } = toSangCanhChuan(
      seDung,
      laCanhNguNghiaMacDinh,
      (id) => {
        const src = vatTheoId.get(id);
        return src ? classifySceneObjectSemantics(scene, src, buoc).strokeColor : MAU.canh;
      },
    );
    const isActiveAuxCarrierOnSolidEdge = (id: string) => {
      if (hasSelection || !stepHighlightTargets.newIds.has(id)) return false;
      const src = vatTheoId.get(id);
      if (!src || src.type !== "line3") return false;
      const spanMode = resolveLineDisplaySpan(scene, src, seDung).mode;
      return spanMode === "clamped_segment" || spanMode === "extended_ray";
    };
    const { ca: canonicalHighlights, khuc: highlightKhuc } = toSangCanhChuan(
      [...hienTai].sort((a, b) => doManh(a.id) - doManh(b.id)),
      (id) => (hasSelection && tapChon.has(id) && tangCua(id) !== "boi_canh") || isActiveAuxCarrierOnSolidEdge(id),
      (id, edgeId) => {
        const baseEdgeHex = edgeId ? (defaultEdgeColors.get(edgeId) ?? defaultKhuc.get(edgeId)?.mau) : undefined;
        if (baseEdgeHex !== undefined) return modulateSemanticColor(baseEdgeHex, "selected");
        if (laCanhNguNghiaMacDinh(id)) return mucMau(id);
        return modulateSemanticColor(MAU.canh, "selected");
      },
    );
    const khucToSang = new Map<string, KhucToSang>([...defaultKhuc, ...highlightKhuc]);
    const buocTrungGian = !isLastGeometryStep(scene, buoc);
    if (!hasSelection && buocTrungGian) {
      for (const depId of stepHighlightTargets.depIds) {
        if (depId.includes("::edge:") && !canonicalHighlights.has(depId)) {
          const baseEdgeHex = defaultEdgeColors.get(depId) ?? MAU.canh;
          canonicalHighlights.set(depId, modulateSemanticColor(baseEdgeHex, "selected"));
        }
      }
    }
    // Quan sát cho bằng chứng playback: vật nào THỰC SỰ được dựng lên khung ở
    // bước này (thiết diện đang hình thành kèm số cạnh đã hiện).
    const daDung: string[] = [];
    /* Nền hình học để cắt mặt phẳng vô hạn: lấy từ vật ĐANG HIỆN, không từ cả
       cảnh. Bước 1 chưa có khối thì miếng mặt phẳng cũng chưa được phình ra
       ôm một khối chưa xuất hiện — mắt đọc đúng thứ tự dựng. */
    const diemNen = diemHuuHan(seDung);
    const coHinhCong = seDung.some((x) => x.render === "circle" || x.render === "ellipse" || x.render === "curved_solid");
    const idSeDung = new Set(seDung.map((o) => o.id));
    const khoaDich = (id: string) => visualTransformOf(tuongTac, scene, id).translate.join(",");
    const nhuong = doanNhuongCanh(seDung, khoaDich);
    const primaryWitnessFootIds = new Set<string>();
    if (!hasSelection) {
      for (const cand of seDung) {
        if (cand.type !== "segment3" && cand.type !== "line3") continue;
        if (stepVisualRoles.get(cand.id)?.role !== "PRIMARY") continue;
        if (!(cand.perpendicular_witness || cand.annotation?.witness)) continue;
        if (classifyCurvedSegmentRole(scene, cand)) continue;
        for (const depId of [...(cand.depends ?? []), ...(cand.endpoint_ids ?? [])]) {
          const depObj = vatTheoId.get(depId);
          if (depObj?.type === "point3" && depObj.origin === "derived") {
            primaryWitnessFootIds.add(depId);
          }
        }
      }
    }
    const dsKhoiId = seDung.filter((x) => x.type === "solid" || x.type === "curved_solid").map((x) => x.id);
    const canhKhoiDaDung: { a: THREE.Vector3; b: THREE.Vector3; dich: string }[] = [];
    const canhThietDienDaDung: { a: THREE.Vector3; b: THREE.Vector3; dich: string }[] = [];
    for (const secObj of seDung) {
      if (secObj.type !== "section" || secObj.closed === false) continue;
      const progSec = progressById.get(secObj.id);
      if (progSec && !progSec.closed) continue;
      const ptsSec = (secObj.polygon ?? secObj.vertices ?? []).map((p) => new THREE.Vector3(...toVec3(p)));
      if (ptsSec.length < 3) continue;
      const dichSec = khoaDich(secObj.id);
      for (let i = 0; i < ptsSec.length; i += 1) {
        canhThietDienDaDung.push({ a: ptsSec[i], b: ptsSec[(i + 1) % ptsSec.length], dich: dichSec });
      }
    }
    for (const o of seDung) {
      const qMp = o.type === "plane3" ? quyetDinhMatPhang.get(o.id) : undefined;
      if (qMp && !qMp.visible) continue;
      const progress = progressById.get(o.id);
      const progressCha = o.parent ? progressById.get(o.parent) : undefined;
      if (o.type === "face" && progressCha && (!progressCha.closed || !progressCha.fill_visible)) continue;
      if (o.type === "edge" && progressCha && !progressCha.visible_edge_ids.includes(o.id)) continue;
      if (o.type === "point3" && o.parent && o.id.includes("::vertex:")) {
        if (progressCha && !progressCha.closed && Number(o.id.split(":vertex:")[1]) > progressCha.visible_edge_ids.length) {
          continue;
        }
        if ((o.depends ?? []).some((d) => idSeDung.has(d)) && !(hasSelection && tapChon.has(o.id))) continue;
      }
      let renderObject = (nhuong.has(o.id) && !(hasSelection && tapChon.has(o.id))) ? { ...o, display_role: "hit_proxy" } as SceneObject : o;
      renderObject = resolveStepPolygonBoundaryOwnership(renderObject, seDung, khoaDich);
      if (o.type === "face" && o.parent && idSeDung.has(o.parent) && khoaDich(o.id) === khoaDich(o.parent)) {
        renderObject = { ...renderObject, display_role: "hit_proxy" };
      }
      if (o.type === "section" && progress && o.polygon) {
        const theoBuoc = vatThietDienTaiBuoc(o, progress);
        if (!theoBuoc) continue;
        renderObject = theoBuoc;
      }
      const sangBuoc = noiBat.has(o.id)
        || (o.type === "point3" && Boolean(o.parent && noiBat.has(o.parent) && progressCha && !progressCha.closed));
      const coThietDienDong = o.render === "surface" && tuongTac.selected_id !== o.id && seDung.some((x) =>
        (x.type === "section" || x.type === "circle3" || x.type === "ellipse3")
        && x.depends.includes(o.id)
        && x.closed !== false && (progressById.get(x.id)?.closed ?? true),
      );
      const daGiacNghienCuu = o.type === "plane3" ? computeBoundedStudiedPlanePolygon(scene, o, seDung) : [];
      const neoGonMp = o.type === "plane3" && daGiacNghienCuu.length < 3 ? compactPlaneAnchorPoints(scene, o, seDung) : [];
      const diemMp = o.render === "surface"
        ? (daGiacNghienCuu.length >= 3
            ? daGiacNghienCuu
            : neoGonMp.length >= 3
              ? neoGonMp
              : coHinhCong
                ? diemHuuHan(seDung.filter((x) => o.depends.includes(x.id) || (x.type === "section" && x.depends.includes(o.id))))
                : [
                    ...diemHuuHan(seDung.filter((x) => o.depends.includes(x.id) || x.type === "solid" || (x.type === "section" && x.depends.includes(o.id)))),
                    ...(o.type === "plane3" ? planeSolidEdgeIntersections(o, seDung) : []),
                  ])
        : [];
      const diemChoVat = o.render === "line"
        ? diemChoDuong(seDung, o.id)
        : o.render === "surface" && diemMp.length >= 3
          ? diemMp
          : diemNen;
      const roleEntry = stepVisualRoles.get(o.id);
      const isSpatialWitnessGoal =
        (o.type === "segment3" || o.type === "line3")
        && Boolean(o.perpendicular_witness || o.annotation?.witness)
        && !classifyCurvedSegmentRole(scene, o);
      const selectionEmphasis = tang
        ? tang.get(o.id) ?? false
        : (
            (roleEntry?.role === "PRIMARY"
              && (o.type === "point3"
                || isSpatialWitnessGoal
                || (buocTrungGian && (o.type === "segment3" || o.type === "line3"))))
            || (o.type === "point3" && primaryWitnessFootIds.has(o.id))
              ? "dich"
              : false
          );
      const auxSurface = isAuxiliaryExplanatoryPolygon(scene, o);
      const sphereRef =
        o.type === "curved_solid" && o.curved_kind === "ball"
          ? shouldShowSphereReferenceEquator(scene, o, auxiliaryShown, seDung)
          : dsKhoiId.length === 1;
      if (o.type === "curved_solid" && o.curved_kind === "ball") {
        // Cờ UI chỉ cho lần dựng này: gắn vào BẢN SAO, không ghi vào đối tượng Scene3D của envelope (đó là dữ liệu có
        // thẩm quyền, được băm làm định danh cảnh và được lưu vào lịch sử).
        renderObject = { ...renderObject, _auxiliaryShown: auxiliaryShown } as SceneObject;
      }
      const obj = buildObject3D(
        renderObject,
        selectionEmphasis,
        banKinhBamDiem(KHOANG_CAM_MAC_DINH),
        diemChoVat,
        undefined,
        canonicalHighlights,
        khucToSang,
        xray,
        vaiKhoiTheoId.get(o.id) ?? vaiKhoiTheoId.get(o.parent ?? "") ?? "primary",
        coThietDienDong,
        sphereRef,
        auxSurface,
        scene,
        defaultEdgeColors,
        undefined,
        daGiacNghienCuu,
        seDung,
      );
      if (!obj) continue;
      const stepRole: "new" | "dep" | undefined = stepHighlightTargets.newIds.has(o.id)
        ? "new"
        : stepHighlightTargets.depIds.has(o.id)
          ? "dep"
          : (o.type === "point3"
            && o.parent
            && stepHighlightTargets.newIds.has(o.parent)
            && Boolean(progressCha && !progressCha.closed))
            ? "new"
            : undefined;
      if (stepRole) {
        obj.userData.stepHighlightRole = stepRole;
      } else if (o.type === "solid" && (stepHighlightTargets.newIds.size > 0 || stepHighlightTargets.depIds.size > 0)) {
        const diemTrenCanh = (p: THREE.Vector3, a: THREE.Vector3, b: THREE.Vector3) => {
          const abx = b.x - a.x, aby = b.y - a.y, abz = b.z - a.z;
          const lenSq = abx * abx + aby * aby + abz * abz;
          if (lenSq < 1e-12) return false;
          const apx = p.x - a.x, apy = p.y - a.y, apz = p.z - a.z;
          const t = (apx * abx + apy * aby + apz * abz) / lenSq;
          if (t < -1e-4 || t > 1 + 1e-4) return false;
          return Math.hypot(a.x + abx * t - p.x, a.y + aby * t - p.y, a.z + abz * t - p.z) <= 1e-4;
        };
        const yieldedSpans = seDung.flatMap((seg) => {
          if (!nhuong.has(seg.id)) return [];
          const role = stepHighlightTargets.newIds.has(seg.id)
            ? "new"
            : stepHighlightTargets.depIds.has(seg.id)
              ? "dep"
              : undefined;
          if (!role) return [];
          const pa = seg.point_a ?? seg.endpoints?.[0];
          const pb = seg.point_b ?? seg.endpoints?.[1];
          if (!pa || !pb) return [];
          return [{ role, a: new THREE.Vector3(...toVec3(pa)), b: new THREE.Vector3(...toVec3(pb)) }];
        });
        obj.traverse((child) => {
          const edge = child.userData?.canonicalEdge as ReturnType<typeof canonicalEdgesOf>[number] | undefined;
          if (!edge || !(child as THREE.Group).isGroup) return;
          if (stepHighlightTargets.newIds.has(edge.id)) {
            child.userData.stepHighlightRole = "new";
            return;
          }
          if (stepHighlightTargets.depIds.has(edge.id)) {
            child.userData.stepHighlightRole = "dep";
            return;
          }
          for (const ys of yieldedSpans) {
            if (diemTrenCanh(ys.a, edge.a, edge.b) && diemTrenCanh(ys.b, edge.a, edge.b)) {
              child.userData.stepHighlightRole = ys.role;
              if (ys.role === "new") break;
            }
          }
        });
      }
      // All steps (the circle's own step decides, #31), but only circles the user has not hidden or isolated away and
      // drawn at the same display translation: otherwise the solid would lose a cap nobody draws.
      if (o.type === "curved_solid") boVanhDayTrung(obj, o, scene.objects.filter((x) => !tuongTac.hidden_ids.includes(x.id)
        && (!tuongTac.isolated_ids.length || tuongTac.isolated_ids.includes(x.id)) && khoaDich(x.id) === khoaDich(o.id)));
      const chiSoKhoi = dsKhoiId.indexOf(o.id);
      const dichVat = khoaDich(o.id);
      if (dsKhoiId.length > 1 && chiSoKhoi >= 0) {
        const laKhoiPhu = chiSoKhoi > 0;
        if (laKhoiPhu) {
          if (o.type === "curved_solid" && dichVat === khoaDich(dsKhoiId[0])) {
            datKhoiCongKhongChe(obj);
            for (const c of [...obj.children]) {
              if (c.userData?.chieuSau || c.userData?.chieuSauMatTruoc) obj.remove(c);
            }
          }
        }
        if (o.type === "solid") {
          const diemTrenDoan = (p: THREE.Vector3, a: THREE.Vector3, b: THREE.Vector3) => {
            const abx = b.x - a.x, aby = b.y - a.y, abz = b.z - a.z;
            const lenSq = abx * abx + aby * aby + abz * abz;
            if (lenSq < 1e-12) return false;
            const apx = p.x - a.x, apy = p.y - a.y, apz = p.z - a.z;
            const t = (apx * abx + apy * aby + apz * abz) / lenSq;
            if (t < -1e-4 || t > 1 + 1e-4) return false;
            return Math.hypot(a.x + abx * t - p.x, a.y + aby * t - p.y, a.z + abz * t - p.z) <= 1e-4;
          };
          if (laKhoiPhu && dichVat === khoaDich(dsKhoiId[0]) && !sangBuoc && (o.vertices?.length ?? 0) > 0) {
            const namTrongKhoiChinh = (o.vertices ?? []).every((vRaw) => {
              const vp = new THREE.Vector3(...toVec3(vRaw));
              return canhKhoiDaDung.some((c) => c.dich === dichVat && diemTrenDoan(vp, c.a, c.b));
            });
            if (namTrongKhoiChinh) {
              for (const c of [...obj.children]) {
                if (c.userData?.chieuSau) {
                  obj.remove(c);
                } else if ((c as THREE.Mesh).isMesh) {
                  const mat = (c as THREE.Mesh).material as THREE.MeshStandardMaterial;
                  mat.colorWrite = false;
                  mat.opacity = 0;
                }
              }
            }
          }
          obj.traverse((child) => {
            const edge = child.userData?.canonicalEdge as ReturnType<typeof canonicalEdgesOf>[number] | undefined;
            if (!edge || !(child as THREE.Group).isGroup) return;
            if (!laKhoiPhu) {
              canhKhoiDaDung.push({ a: edge.a.clone(), b: edge.b.clone(), dich: dichVat });
              return;
            }
            const trungCanhChinh = canhKhoiDaDung.some(
              (c) => c.dich === dichVat && diemTrenDoan(edge.a, c.a, c.b) && diemTrenDoan(edge.b, c.a, c.b),
            );
            const trungCanhThietDien = canhThietDienDaDung.some(
              (c) => c.dich === dichVat && diemTrenDoan(edge.a, c.a, c.b) && diemTrenDoan(edge.b, c.a, c.b),
            );
            if ((trungCanhChinh || trungCanhThietDien) && !child.userData.highlighted && !child.userData.khuc) {
              child.visible = false;
            }
          });
        }
      }
      if (tang && !tang.has(o.id)) {
        lamDiu(obj);   // ngoài chuỗi nhân quả
      } else if (
        !tang
        && o.type !== "plane3"
        && o.type !== "solid"
        && o.type !== "curved_solid"
        && roleEntry
        && roleEntry.opacityScale > 0
        && roleEntry.opacityScale < 1
      ) {
        lamDiu(obj, roleEntry.opacityScale);
      }
      if (!tang && roleEntry) {
        if (roleEntry.showPerpWitnessSymbol === false) {
          obj.traverse((child) => {
            if (
              child.name === `perp_marker:${o.id}`
              || child.name === `perp_marker_2:${o.id}`
              || child.name === `perp_plane_ray:${o.id}`
              || child.name === `witness_leg:${o.id}`
              || Boolean(child.userData?.witness_leg)
            ) {
              child.userData.retiredByStepPolicy = true;
              child.visible = false;
            }
          });
        } else if (
          typeof roleEntry.perpWitnessOpacityScale === "number"
          && roleEntry.perpWitnessOpacityScale > 0
          && roleEntry.perpWitnessOpacityScale < 1
        ) {
          obj.traverse((child) => {
            if (
              child.name === `perp_marker:${o.id}`
              || child.name === `perp_marker_2:${o.id}`
              || child.name === `perp_plane_ray:${o.id}`
              || child.name === `witness_leg:${o.id}`
              || Boolean(child.userData?.witness_leg)
            ) {
              lamDiu(child, roleEntry.perpWitnessOpacityScale);
            }
          });
        }
      }
      const hostSolidScale =
        !tang && o.type === "solid" && roleEntry?.reason === "host_solid_section_context"
          ? roleEntry.opacityScale
          : 1;
      if (
        (o.type === "solid" || o.type === "curved_solid")
        && (!shellShown || typeof shellOpacityPct === "number" || hostSolidScale !== 1)
      ) {
        obj.traverse((child) => {
          const mesh = child as THREE.Mesh;
          if (!mesh.isMesh || !mesh.userData?.voKhoi) return;
          const mat = mesh.material as THREE.MeshBasicMaterial | undefined;
          if (!mat || mat.colorWrite === false) return;
          if (!shellShown || shellOpacityPct === 0) {
            mesh.visible = false;
          } else {
            mesh.visible = true;
            const baseOp = typeof mesh.userData?.baseShellOpacity === "number" ? mesh.userData.baseShellOpacity : DO_DUC.solid;
            const pctScale = typeof shellOpacityPct === "number" ? shellOpacityPct / 12 : 1;
            mat.opacity = Math.max(0.01, Math.min(0.95, baseOp * pctScale * hostSolidScale));
          }
        });
      }
      if (o.type === "plane3") {
        const heSoMp = qMp?.opacityScale ?? 1;
        if (!planeShown || planeOpacityPct === 0 || heSoMp <= 0) {
          obj.visible = false;
        } else if (typeof planeOpacityPct === "number" || heSoMp !== 1) {
          const pctScale = typeof planeOpacityPct === "number" ? planeOpacityPct / 8 : 1;
          const borderScale = (0.45 + 0.55 * pctScale) * heSoMp;
          obj.traverse((child) => {
            if (child.userData?.nonCanonicalLoop?.isPlaneBorder) {
              child.userData.lamDiu = borderScale;
              child.userData.planeBorderWidthScale =
                qMp?.lifecycleStage === "attenuated_support" || qMp?.lifecycleStage === "consolidated_section_support"
                  ? 0.76
                  : 1;
            }
            const mesh = child as THREE.Mesh;
            if (mesh.isMesh) {
              const mat = mesh.material as THREE.MeshBasicMaterial | undefined;
              if (!mat || mat.colorWrite === false) return;
              if (typeof mesh.userData.basePlaneOpacity !== "number") {
                mesh.userData.basePlaneOpacity = mat.opacity;
              }
              mat.opacity = Math.max(0.01, Math.min(0.95, (mesh.userData.basePlaneOpacity as number) * pctScale * heSoMp));
              return;
            }
            const line = child as THREE.Line;
            if (line.isLine && (line.name.startsWith("plane_border:") || line.name.startsWith("plane_corner_arc:"))) {
              const lMat = line.material as THREE.LineBasicMaterial | undefined;
              if (lMat && typeof lMat.opacity === "number") {
                lMat.opacity = Math.max(0.05, Math.min(0.95, lMat.opacity * borderScale));
              }
            }
          });
        }
      }
      const laMatBienKhoiCha = Boolean(
        o.type === "polygon3" && o.parent && (o.display_group ?? []).includes("face") && idSeDung.has(o.parent),
      );
      const thuocThietDienCha = Boolean(
        o.parent && scene.objects.some((p) => p.id === o.parent && (p.type === "section" || vaiTroMien(p) === "section")),
      );
      const laMienThietDienKetQua =
        o.type === "circle3"
          ? classifyCircleSemanticRole(scene, o) === "RESULT_SECTION"
          : vaiTroMien(o) === "section" && !isAuxiliaryExplanatoryPolygon(scene, o);
      if (
        !sectionShown
        && !laMatBienKhoiCha
        && (o.type === "section" || laMienThietDienKetQua || thuocThietDienCha || isIntersectionLineOrSegment(o, scene))
      ) {
        obj.visible = false;
      }
      const bd = visualTransformOf(tuongTac, scene, o.id);
      datViTriTrinhBay(obj, bd);
      goc.add(obj);
      daDung.push(renderObject.polygon && o.type === "section"
        ? `${o.id}#${renderObject.polygon.length}${renderObject.closed ? "c" : ""}`
          + `${renderObject.fill_visible ? "f" : ""}` : o.id);
      // Chỉ ĐIỂM mang nhãn `.geo3d-label`. Mặt phẳng có ký hiệu (`notation`) do backend phát
      // được gắn nhãn `.geo3d-nhan-mp` riêng ở diềm mở rộng của tấm mặt phẳng.
      if (o.type === "point3" && o.xyz) {
        const [x, y, z] = toVec3(o.xyz);
        viTriNhan.current.set(o.id, new THREE.Vector3(
          x + bd.translate[0], y + bd.translate[1], z + bd.translate[2]));
      }
      const showMpLabel =
        o.type !== "plane3"
        || (qMp?.showPlaneLabel ?? true)
        || auxiliaryShown
        || tuongTac.selected_id === o.id;
      if (o.type === "plane3" && o.point && o.normal && kyHieu(o) !== null && showMpLabel) {
        let neo: Vec3 | null = null;
        if (daGiacNghienCuu.length >= 3) {
          gocMatPhangRef.current.set(
            o.id,
            daGiacNghienCuu.map((p) => new THREE.Vector3(p[0] + bd.translate[0], p[1] + bd.translate[1], p[2] + bd.translate[2])),
          );
          const m = daGiacNghienCuu.length;
          const tam: Vec3 = [
            daGiacNghienCuu.reduce((s, p) => s + p[0], 0) / m,
            daGiacNghienCuu.reduce((s, p) => s + p[1], 0) / m,
            daGiacNghienCuu.reduce((s, p) => s + p[2], 0) / m,
          ];
          const daDat: Vec3[] = [...viTriMatPhang.current.values()].map((v) => [
            v.x - bd.translate[0],
            v.y - bd.translate[1],
            v.z - bd.translate[2],
          ]);
          const tranh: Vec3[] = [...diemNen, ...daDat];
          const ungVien: Vec3[] = [];
          for (let i = 0; i < m; i += 1) {
            const a = daGiacNghienCuu[i];
            const b = daGiacNghienCuu[(i + 1) % m];
            ungVien.push([0.86 * a[0] + 0.14 * tam[0], 0.86 * a[1] + 0.14 * tam[1], 0.86 * a[2] + 0.14 * tam[2]]);
            const mid: Vec3 = [(a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5];
            ungVien.push([0.88 * mid[0] + 0.12 * tam[0], 0.88 * mid[1] + 0.12 * tam[1], 0.88 * mid[2] + 0.12 * tam[2]]);
          }
          let diemTot = -Infinity;
          for (const u of ungVien) {
            const kcMin = tranh.length > 0
              ? Math.min(...tranh.map((p) => Math.hypot(u[0] - p[0], u[1] - p[1], u[2] - p[2])))
              : 1;
            const diemSo = kcMin + 0.06 * (u[2] - tam[2]);
            if (diemSo > diemTot) {
              diemTot = diemSo;
              neo = u;
            }
          }
        } else {
          neo = diemNeoNhanMatPhang(toVec3(o.point), toVec3(o.normal), diemChoVat);
        }
        if (neo) {
          viTriMatPhang.current.set(o.id, new THREE.Vector3(
            neo[0] + bd.translate[0], neo[1] + bd.translate[1], neo[2] + bd.translate[2]));
        }
      }
    }
    for (const lnObj of seDung) {
      if (lnObj.type !== "line3" || !lnObj.point || !lnObj.direction) continue;
      const kh = kyHieu(lnObj);
      if (!kh || !/^(?:[a-z]|Δ|δ|d'|d₁|d₂|Δ')$/u.test(kh)) continue;
      const spLn = resolveLineDisplaySpan(scene, lnObj, seDung, diemNen);
      const segLn = spLn.coreSegment ?? spLn.endpoints;
      if (!segLn) continue;
      const [lp0, lp1] = segLn;
      const bdLn = visualTransformOf(tuongTac, scene, lnObj.id);
      viTriMatPhang.current.set(
        lnObj.id,
        new THREE.Vector3(
          0.12 * lp0[0] + 0.88 * lp1[0] + bdLn.translate[0],
          0.12 * lp0[1] + 0.88 * lp1[1] + bdLn.translate[1],
          0.12 * lp0[2] + 0.88 * lp1[2] + bdLn.translate[2],
        ),
      );
    }
    if (planeShown && planeOpacityPct !== 0) {
      const faceCarriers = resolveSolidFaceDuplicateCarrierPolygons(scene, buoc, tuongTac.selected_id);
      for (const fc of faceCarriers) {
        if (tuongTac.hidden_ids.includes(fc.planeId) || (tuongTac.isolated_ids.length > 0 && !tuongTac.isolated_ids.includes(fc.planeId))) continue;
        const ptsFc = fc.vertices.map(toVec3);
        if (ptsFc.length < 3) continue;
        const posFc: number[] = [];
        for (const [ia, ib, ic] of chiaTamGiac(ptsFc)) {
          for (const jk of [ia, ib, ic]) posFc.push(...ptsFc[jk]);
        }
        if (posFc.length === 0) continue;
        const gFc = new THREE.BufferGeometry();
        gFc.setAttribute("position", new THREE.Float32BufferAttribute(posFc, 3));
        gFc.computeVertexNormals();
        const pctScaleFc = typeof planeOpacityPct === "number" ? planeOpacityPct / 8 : 1;
        const tintHex = fc.rank % 2 === 0 ? MAU.line : 0x4f46e5;
        const baseOpFc = fc.isSelected ? 0.24 : 0.16;
        const meshFc = new THREE.Mesh(
          gFc,
          new THREE.MeshBasicMaterial({
            color: tintHex,
            transparent: true,
            opacity: Math.max(0.03, Math.min(0.65, baseOpFc * pctScaleFc)),
            forceSinglePass: true,
            side: THREE.DoubleSide,
            depthWrite: false,
            ...LECH_THIET_DIEN,
          }),
        );
        meshFc.name = `plane_face_carrier:${fc.planeId}`;
        meshFc.renderOrder = THU_TU_TO_THIET_DIEN - 1;
        meshFc.raycast = () => {};
        const bdFc = visualTransformOf(tuongTac, scene, fc.planeId);
        datViTriTrinhBay(meshFc, bdFc);
        goc.add(meshFc);
        if (!daDung.includes(fc.planeId)) daDung.push(fc.planeId);
      }
    }
    if (sectionShown) {
      const dkPar = duongKinhCanh(diemNen);
      const chevronScale = (dkPar > 0 ? dkPar : 4) * 0.019;
      const canonicalizeParallelDir = (rawDir: Vec3): Vec3 | null => {
        const dLen = Math.hypot(rawDir[0], rawDir[1], rawDir[2]);
        if (dLen <= 1e-6) return null;
        let tx = rawDir[0] / dLen, ty = rawDir[1] / dLen, tz = rawDir[2] / dLen;
        const flip =
          Math.abs(tx) > 1e-5
            ? tx < 0
            : Math.abs(ty) > 1e-5
              ? ty < 0
              : tz < 0;
        if (flip) {
          tx = -tx;
          ty = -ty;
          tz = -tz;
        }
        return [tx, ty, tz];
      };
      const appendChevronTicks = (
        outContours: { pts: [THREE.Vector3, THREE.Vector3, THREE.Vector3]; center: Vec3; dirUnit: Vec3; scale: number; isTarget: boolean }[],
        mid: Vec3,
        canonDir: Vec3,
        tickCount: 1 | 2 | 3,
        isTarget: boolean,
      ) => {
        const [tx, ty, tz] = canonDir;
        const useAltR = Math.abs(-0.58 * ty + 0.81 * tz) > 0.85;
        const rx = useAltR ? 0.81 : 0, ry = useAltR ? 0 : -0.58, rz = useAltR ? 0.58 : 0.81;
        let wx = ty * rz - tz * ry;
        let wy = tz * rx - tx * rz;
        let wz = tx * ry - ty * rx;
        const wLen = Math.hypot(wx, wy, wz);
        if (wLen <= 1e-6) return;
        wx /= wLen; wy /= wLen; wz /= wLen;
        const offsets =
          tickCount === 1
            ? [0]
            : tickCount === 2
              ? [-0.52 * chevronScale, 0.52 * chevronScale]
              : [-0.82 * chevronScale, 0, 0.82 * chevronScale];
        for (const off of offsets) {
          const mcx = mid[0] + off * tx, mcy = mid[1] + off * ty, mcz = mid[2] + off * tz;
          const tip = new THREE.Vector3(
            mcx + 0.46 * chevronScale * tx,
            mcy + 0.46 * chevronScale * ty,
            mcz + 0.46 * chevronScale * tz,
          );
          const w1 = new THREE.Vector3(
            mcx - 0.46 * chevronScale * tx + 0.64 * chevronScale * wx,
            mcy - 0.46 * chevronScale * ty + 0.64 * chevronScale * wy,
            mcz - 0.46 * chevronScale * tz + 0.64 * chevronScale * wz,
          );
          const w2 = new THREE.Vector3(
            mcx - 0.46 * chevronScale * tx - 0.64 * chevronScale * wx,
            mcy - 0.46 * chevronScale * ty - 0.64 * chevronScale * wy,
            mcz - 0.46 * chevronScale * tz - 0.64 * chevronScale * wz,
          );
          outContours.push({
            pts: [w1, tip, w2],
            center: [mcx, mcy, mcz],
            dirUnit: [tx, ty, tz],
            scale: chevronScale,
            isTarget,
          });
        }
      };
      const visibleNamedPts = seDung
        .filter((x) => x.type === "point3" && Boolean(x.xyz))
        .map((x) => toVec3(x.xyz!));
      const minClearanceAt = (cand: Vec3) =>
        visibleNamedPts.length > 0
          ? Math.min(...visibleNamedPts.map((pt) => Math.hypot(pt[0] - cand[0], pt[1] - cand[1], pt[2] - cand[2])))
          : Infinity;
      const pickClearSegmentPoint = (p0: Vec3, p1: Vec3): Vec3 => {
        const segLen = Math.hypot(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]);
        const minClearReq = Math.max(chevronScale * 5.5, segLen * 0.18);
        const rawMid: Vec3 = [(p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5];
        if (minClearanceAt(rawMid) >= minClearReq) return rawMid;
        let bestCand = rawMid;
        let bestClear = minClearanceAt(rawMid);
        for (const tCand of [0.22, 0.36, 0.64, 0.78]) {
          const uCand: Vec3 = [
            (1 - tCand) * p0[0] + tCand * p1[0],
            (1 - tCand) * p0[1] + tCand * p1[1],
            (1 - tCand) * p0[2] + tCand * p1[2],
          ];
          const cl = minClearanceAt(uCand);
          if (cl > bestClear) {
            bestClear = cl;
            bestCand = uCand;
          }
        }
        return bestCand;
      };
      const segKeyFromEndpoints = (p0: Vec3, p1: Vec3): string => {
        const fmt = (p: Vec3) => `${p[0].toFixed(4)},${p[1].toFixed(4)},${p[2].toFixed(4)}`;
        const k0 = fmt(p0), k1 = fmt(p1);
        return k0 < k1 ? `${k0}|${k1}` : `${k1}|${k0}`;
      };
      type PendingParallelEntry = {
        interId: string;
        canonDir: Vec3;
        primaryMid: Vec3;
        primaryKey: string;
        targets: { mid: Vec3; key: string }[];
      };
      const pendingParallels: PendingParallelEntry[] = [];
      for (const interCand of seDung) {
        if (!isIntersectionLineOrSegment(interCand, scene)) continue;
        if (stepVisualRoles.get(interCand.id)?.showParallelWitnessSymbol === false) continue;
        const semObj = resolveSemanticObjectContract(scene, interCand.id);
        const parRel = semObj?.verifiedRelations.find((r) => r.kind === "parallel" && r.canDisplaySymbol);
        if (!parRel || parRel.targetIds.length === 0) continue;
        let lineMid: Vec3 | null = null;
        let lineDir: Vec3 | null = null;
        let lineSegKey = interCand.id;
        if (interCand.type === "line3" && interCand.point && interCand.direction) {
          const sp = resolveLineDisplaySpan(scene, interCand, seDung, diemNen);
          const segPair = sp.coreSegment ?? sp.endpoints;
          if (segPair) {
            const [p0, p1] = segPair;
            lineMid = pickClearSegmentPoint(p0, p1);
            lineDir = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]];
            lineSegKey = segKeyFromEndpoints(p0, p1);
          }
        } else {
          const pa = interCand.point_a ?? interCand.endpoints?.[0];
          const pb = interCand.point_b ?? interCand.endpoints?.[1];
          if (pa && pb) {
            const p0 = toVec3(pa);
            const p1 = toVec3(pb);
            lineMid = pickClearSegmentPoint(p0, p1);
            lineDir = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]];
            lineSegKey = segKeyFromEndpoints(p0, p1);
          }
        }
        if (!lineMid || !lineDir) continue;
        const canonDir = canonicalizeParallelDir(lineDir);
        if (!canonDir) continue;
        const bdInter = visualTransformOf(tuongTac, scene, interCand.id);
        const primaryMid: Vec3 = [
          lineMid[0] + bdInter.translate[0],
          lineMid[1] + bdInter.translate[1],
          lineMid[2] + bdInter.translate[2],
        ];
        const targets: { mid: Vec3; key: string }[] = [];
        for (const tid of parRel.targetIds) {
          if (targets.length >= 2) break;
          if (tid.includes("::edge:")) {
            const [solId] = tid.split("::edge:");
            const solObj = seDung.find((s) => s.id === solId && s.type === "solid");
            if (!solObj) continue;
            const ce = canonicalEdgesOf(solObj).find((e) => e.id === tid);
            if (!ce) continue;
            const p0: Vec3 = [ce.a.x, ce.a.y, ce.a.z];
            const p1: Vec3 = [ce.b.x, ce.b.y, ce.b.z];
            const bdTp = visualTransformOf(tuongTac, scene, solId);
            const clearPt = pickClearSegmentPoint(p0, p1);
            targets.push({
              mid: [clearPt[0] + bdTp.translate[0], clearPt[1] + bdTp.translate[1], clearPt[2] + bdTp.translate[2]],
              key: segKeyFromEndpoints(p0, p1),
            });
          } else {
            const tObj = seDung.find((s) => s.id === tid);
            if (!tObj) continue;
            const pa = tObj.point_a ?? tObj.endpoints?.[0];
            const pb = tObj.point_b ?? tObj.endpoints?.[1];
            if (!pa || !pb) continue;
            const p0 = toVec3(pa), p1 = toVec3(pb);
            const bdTp = visualTransformOf(tuongTac, scene, tid);
            const clearPt = pickClearSegmentPoint(p0, p1);
            targets.push({
              mid: [clearPt[0] + bdTp.translate[0], clearPt[1] + bdTp.translate[1], clearPt[2] + bdTp.translate[2]],
              key: segKeyFromEndpoints(p0, p1),
            });
          }
        }
        if (targets.length === 0) continue;
        pendingParallels.push({
          interId: interCand.id,
          canonDir,
          primaryMid,
          primaryKey: lineSegKey,
          targets,
        });
      }
      const dirClasses: { dir: Vec3; stampedKeys: Set<string> }[] = [];
      const entryClassIndices: number[] = [];
      for (const entry of pendingParallels) {
        let foundIdx = -1;
        for (let ci = 0; ci < dirClasses.length; ci += 1) {
          const cd = dirClasses[ci]!.dir;
          const cr = Math.hypot(
            entry.canonDir[1] * cd[2] - entry.canonDir[2] * cd[1],
            entry.canonDir[2] * cd[0] - entry.canonDir[0] * cd[2],
            entry.canonDir[0] * cd[1] - entry.canonDir[1] * cd[0],
          );
          if (cr < 1e-4) {
            foundIdx = ci;
            break;
          }
        }
        if (foundIdx < 0) {
          foundIdx = dirClasses.length;
          dirClasses.push({ dir: entry.canonDir, stampedKeys: new Set<string>() });
        }
        entryClassIndices.push(foundIdx);
      }
      pendingParallels.forEach((entry, idx) => {
        const clsIdx = entryClassIndices[idx]!;
        const cls = dirClasses[clsIdx]!;
        const tickCount: 1 | 2 | 3 = dirClasses.length === 1 ? 2 : (Math.min(3, clsIdx + 1) as 1 | 2 | 3);
        const chevronContours: { pts: [THREE.Vector3, THREE.Vector3, THREE.Vector3]; center: Vec3; dirUnit: Vec3; scale: number; isTarget: boolean }[] = [];
        if (!cls.stampedKeys.has(entry.primaryKey)) {
          cls.stampedKeys.add(entry.primaryKey);
          appendChevronTicks(chevronContours, entry.primaryMid, cls.dir, tickCount, false);
        }
        for (const tp of entry.targets) {
          if (cls.stampedKeys.has(tp.key)) continue;
          cls.stampedKeys.add(tp.key);
          appendChevronTicks(chevronContours, tp.mid, cls.dir, tickCount, true);
        }
        if (chevronContours.length > 0) {
          const parGroup = new THREE.Group();
          parGroup.name = `parallel_tick:${entry.interId}`;
          parGroup.userData.voHan = true;
          chevronContours.forEach((cEntry, cIdx) => {
            const cLine = new THREE.Line(
              new THREE.BufferGeometry().setFromPoints(cEntry.pts),
              new THREE.LineBasicMaterial({
                color: cEntry.isTarget ? MAU.sectionOutline : 0x7c2d12,
                transparent: true,
                opacity: 0.94,
                depthTest: false,
                depthWrite: false,
              }),
            );
            cLine.name = `parallel_chevron:${entry.interId}:${cIdx}`;
            cLine.userData.semanticLineRole = "parallel_witness";
            cLine.userData.parallelChevron = {
              center: cEntry.center,
              dirUnit: cEntry.dirUnit,
              scale: cEntry.scale,
            };
            cLine.renderOrder = 10;
            cLine.raycast = () => {};
            parGroup.add(cLine);
          });
          goc.add(parGroup);
        }
      });
    }
    const nhomThamChieuHopDong = buildContractReferenceGroup(scene, seDung, buoc);
    if (nhomThamChieuHopDong) {
      goc.add(nhomThamChieuHopDong);
    }
    if (typeof window !== "undefined") {
      (window as any).__geo3d_rendered_object_ids = daDung;
      (window as any).__geo3d_contract_reference_ids = nhomThamChieuHopDong
        ? nhomThamChieuHopDong.children.map((c) => c.name)
        : [];
      (window as any).__geo3d_geometry_build_count = ((window as any).__geo3d_geometry_build_count ?? 0) + 1;
      (window as any).__geo3d_auxiliary_hidden_ids = [...anPhu].sort();
      (window as any).__geo3d_causal_tiers = tang ? Object.fromEntries(tang) : null;
      (window as any).__geo3d_step_visual_roles = Object.fromEntries(stepVisualRoles);
      (window as any).__geo3d_shell_visible = shellShown;
      (window as any).__geo3d_plane_visible = planeShown;
      (window as any).__geo3d_section_visible = sectionShown;
      (window as any).__geo3d_shell_opacity_pct = shellOpacityPct ?? 12;
      (window as any).__geo3d_plane_opacity_pct = planeOpacityPct ?? 8;
      (window as any).__geo3d_right_angles_visible = rightAnglesShown;
      (window as any).__geo3d_dashed_hidden_visible = dashedHiddenShown;
    }
    scheduleCommitRender();
  }, [scene, buoc, tuongTac, tapNoiBat, hasSelection, tapChon, stepHighlightTargets, tang, anPhu, ungroundedPts, quyetDinhMatPhang, stepVisualRoles, auxiliaryShown, xray, vaiKhoiTheoId, shellShown, planeShown, sectionShown, shellOpacityPct, planeOpacityPct, rightAnglesShown, dashedHiddenShown, webglEpoch]);

  useEffect(() => {
    const present = entitiesPresentAt(scene, buoc, objectsAt);
    const { ca } = toSangCanhChuan(scene.objects.filter(o => present.has(o.id)), id => id === hoveredObject, () => 0);
    hoverFeedbackRef.current = { id: hoveredObject, edges: new Set(ca.keys()) };
    if (typeof window !== "undefined") {
      (window as any).__geo3d_hovered_object_id = hoveredObject;
      (window as any).__geo3d_hovered_section_id = hoveredObject
        && scene.objects.some(o => o.id === hoveredObject && (o.type === "section" || vaiTroMien(o) === "section")) ? hoveredObject : null;
    }
    scheduleCommitRender();
  }, [hoveredObject, scene, buoc, webglEpoch]);

  // ── KHI NÀO ĐẶT LẠI KHUNG NHÌN ────────────────────────────────────────
  //
  // Cố ý **không** có `buoc` trong danh sách phụ thuộc. Đặt lại khung nhìn ở
  // mỗi bước sẽ biến việc tua bước thành việc đổi góc máy: người xem thấy hình
  // nhúc nhích và không phân biệt được đâu là vật mới dựng, đâu là camera vừa
  // dịch. Hai hình so sánh bước 5 với bước 12 chỉ có nghĩa khi khung nhìn đứng
  // yên giữa hai bước.
  //
  // Ba dịp được đặt lại, và cả ba đều là lúc TẬP VẬT ĐANG THẤY đổi hẳn:
  // nạp cảnh khác · người dùng bấm xem lại toàn hình (`fitToken`) · tách hoặc
  // ráp khối (`exploded_groups`).
  const daBung = tuongTac.exploded_groups.join("|");
  useEffect(() => {
    if (prevFitTokenRef.current !== fitToken) {
      prevFitTokenRef.current = fitToken;
      pendingRestoredCameraRef.current = null;
    }
    vuaKhungRef.current?.();
  }, [scene, fitToken, daBung, webglEpoch]);

  // Gộp mọi cập nhật đồ thị cảnh & khung nhìn trong cùng một commit React thành ĐÚNG MỘT lượt render WebGL đồng bộ.
  useEffect(() => {
    if (commitRenderDirtyRef.current) {
      commitRenderDirtyRef.current = false;
      veRef.current?.();
    }
  });

  const hien = objectsAt(scene, buoc);
  // Chỉ in nhãn cho vật CÓ ký hiệu do backend phát. Vật không có ký hiệu thì
  // khung không in gì cho nó — trước bản này phía đây tự rút một ký hiệu từ
  // `id`, nên `plane_MNP` hiện thành `MNP` và `V_AMNP` hiện nguyên si.
  const tapHienId = new Set(hien.map((x) => x.id));
  const ungVienNhan = hien.filter(
    (o) => o.type === "point3"
      && veTrenKhung(o)
      && kyHieu(o) !== null
      && !anPhu.has(o.id)
      && !ungroundedPts.has(o.id)
      && (stepVisualRoles.get(o.id)?.visible ?? true)
      && isVisible(tuongTac, o.id, tapHienId),
  );
  const chuNhanDiem = kyHieuDiem(ungVienNhan);
  // Kiểu nhãn SGK theo vai trò (HTML tham chiếu: main-vertex / section-vertex / aux-vertex) — chỉ trình bày.
  // Chỉ các vật CÓ MẶT ở bước đang xem (frame k ⇔ trace[k]): M chưa mang vai đỉnh thiết diện trước khi thiết diện dựng.
  const dinhThietDien = useMemo(
    () => (
      sectionShown
        ? diemTaiDinhThietDien({
            objects: objectsAt(scene, buoc).filter(
              (x) => !isAuxiliaryExplanatoryPolygon(scene, x) && !isPolyhedronOppositeTopBasePolygon(scene, x),
            ),
          })
        : new Set<string>()
    ),
    [scene, buoc, sectionShown],
  );
  const vaiNhan = (o: SceneObject) => dinhThietDien.has(o.id) ? " vai-thiet-dien"
    : o.origin === "derived" ? " vai-phu" : "";
  const nhanDiem = ungVienNhan.filter((o) => chuNhanDiem.has(o.id));
  const nhanMatPhang = hien.filter(
    (o) => (
      (planeShown && o.type === "plane3")
      || (o.type === "line3" && /^(?:[a-z]|Δ|δ|d'|d₁|d₂|Δ')$/u.test(kyHieu(o) ?? ""))
    )
      && veTrenKhung(o)
      && kyHieu(o) !== null
      && !anPhu.has(o.id)
      && (quyetDinhMatPhang.get(o.id)?.visible ?? true)
      && (o.type !== "plane3" || (quyetDinhMatPhang.get(o.id)?.showPlaneLabel ?? true) || auxiliaryShown || tuongTac.selected_id === o.id)
      && isVisible(tuongTac, o.id, tapHienId),
  );

  useEffect(() => {
    if (!webglFailed && !webglTerminalLatchedRef.current && typeof window !== "undefined") {
      (window as any).__geo3d_selected_id = tuongTac?.selected_id || null;
      (window as any).__geo3d_highlighted_ids = [...tapNoiBat].sort();
      (window as any).__geo3d_selection_highlight_ids = [...tapChon].sort();
    }
  }, [webglFailed, tuongTac?.selected_id, tapNoiBat, tapChon]);

  return (
    <div className="geo3d" data-webgl-phase={webglPhase}>
      {webglPhase === "failed" ? (
        webglFallbackNode ?? <p className="geo3d-fallback">{GEOMETRY_WEBGL_FALLBACK}</p>
      ) : (
        <>
          <div
            ref={containerRef}
            className="geo3d-canvas"
            style={webglPhase === "recovering" ? { visibility: "hidden", pointerEvents: "none" } : undefined}
          >
          {/* Lớp NHÃN nằm trên canvas và KHÔNG bắt chuột (`pointer-events`
              tắt trong CSS) — nếu bắt, một chữ "B" sẽ nuốt cú bấm vào chính
              điểm B nằm ngay dưới nó. */}
          <div ref={nhanRef} className="geo3d-labels" aria-hidden="true">
            {nhanDiem.map((o) => (
              <span
                key={o.id}
                data-id={o.id}
                className={`geo3d-label${vaiNhan(o)}${
                  tuongTac.selected_id === o.id
                  || (!hasSelection && !isLastGeometryStep(scene, buoc) && stepHighlightTargets.newIds.has(o.id))
                    ? " la-chon"
                    : tang && !tang.has(o.id)
                      ? " la-diu"
                      : ""
                }`}
                data-uu-tien={uuTienNhan(o, tuongTac.selected_id, stepVisualRoles.get(o.id)?.role)}
              >
                {chuNhanDiem.get(o.id) ?? kyHieu(o)}
              </span>
            ))}
          </div>
          <div ref={nhanMpRef} className="geo3d-plane-labels" aria-hidden="true">
            {nhanMatPhang.map((o) => {
              const t = tang?.get(o.id);
              const chon = tuongTac.selected_id === o.id || t === "dich";
              const qMpDec = quyetDinhMatPhang.get(o.id);
              const diu = (tang !== null && !tang.has(o.id)) || (!chon && qMpDec !== undefined && qMpDec.lifecycleStage !== "primary_focus");
              return (
                <span
                  key={o.id}
                  data-plane-id={o.id}
                  className={`geo3d-nhan-mp${chon ? " la-chon" : diu ? " la-diu" : ""}`}
                  data-uu-tien={uuTienNhan(o, tuongTac.selected_id, stepVisualRoles.get(o.id)?.role)}
                >
                  {kyHieu(o)}
                </span>
              );
            })}
          </div>
          <div
            ref={tooltipRef}
            className={`geo3d-math-tooltip${tooltipInfo ? " is-visible" : ""}`}
            role="status"
            aria-live="polite"
            data-tooltip-target={tooltipInfo ? (tooltipTargetId ?? "") : ""}
          >
            {tooltipInfo ? (
              <>
                <div className="geo3d-math-tooltip-head">
                  <span className="geo3d-math-tooltip-dot" style={{ backgroundColor: tooltipInfo.accentHex }} />
                  <strong className="geo3d-math-tooltip-title"><MathDisplay text={tooltipInfo.header} /></strong>
                </div>
                <div className="geo3d-math-tooltip-body"><MathDisplay text={tooltipInfo.body} /></div>
              </>
            ) : null}
          </div>
          {/* W17 · SỐ ĐO TRÊN HÌNH. W12 gỡ dải số nổi vì một con số không chủ thể đặt ở đâu cũng
              vô nghĩa. Nhãn ở đây khác ở đúng chỗ ấy: mỗi nhãn đứng cạnh CHỦ THỂ backend gắn
              (đoạn, miền, khối, điểm của cặp, nhân chứng), chỉ từ bước đại lượng khả dụng.
              W18 §16.5: mặc định chỉ dữ kiện; nhãn là NÚT (bấm/Enter/Space ⇒ chọn đại lượng, chi
              tiết mở ở ô soi), nên lớp này không còn giấu khỏi trình đọc màn hình. */}
          <div ref={soDoRef} className="geo3d-so-do-lop" aria-label="Số đo trên hình">
            {nhanChu.map((a) => {
              const diu = !a.related && tang !== null && !tang.has(a.id)
                && !a.subject_ids.some((id) => tang.has(id));
              return (
                <span
                  key={a.id}
                  role="button"
                  tabIndex={0}
                  aria-pressed={tuongTac.selected_id === a.id}
                  data-ann-id={a.id}
                  data-ann-seg-key={
                    a.anchor === "segment" && a.subject_ids.length === 2
                      ? (a.subject_ids[0] < a.subject_ids[1]
                          ? `${a.subject_ids[0]}|${a.subject_ids[1]}`
                          : `${a.subject_ids[1]}|${a.subject_ids[0]}`)
                      : ""
                  }
                  data-uu-tien={a.priority}
                  className={`geo3d-so-do${a.role === "result" ? " la-ket-qua" : ""}${
                    a.related ? " la-lien-quan" : diu ? " la-diu" : ""}`}
                >
                  {a.text}
                </span>
              );
            })}
          </div>
          </div>
          {webglPhase === "recovering" ? (
            <div className="geo3d-recovering-overlay">
              {webglRecoveringNode ?? (
                <p className="geo3d-fallback" role="status" aria-live="polite">
                  Đang khôi phục mô phỏng
                </p>
              )}
            </div>
          ) : null}
        </>
      )}
      {/* Mọi con số — dữ kiện, bước tính, kết quả — có đủ ở bảng lời giải dưới thanh bước
          (`scene3d-solution.tsx`); nhãn trên hình (W17) chỉ là lối tắt đọc cạnh chủ thể.

          Nội suy GỘP thành MỘT chuỗi: `{a}/{b}` làm SSR chèn marker
          `<!-- -->` vào giữa, nên chữ hiện ra đúng mà mọi phép kiểm chuỗi lại
          trượt — một lệch câm giữa thứ người đọc thấy và thứ test đọc. */}
      <p className="geo3d-progress geo3d-sr">
        {`Bước ${geometryStepOf(scene, buoc) + 1}/${geometryStepCount(scene)}`}
      </p>
      {/* W4: dòng lời kể nhìn thấy dưới thanh đã gỡ — đây là nơi trình đọc màn hình NGHE bước mới. */}
      <p className="geo3d-narration geo3d-sr" aria-live="polite">{geometryNarrationAt(scene, buoc)}</p>
    </div>
  );
}
