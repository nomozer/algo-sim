/**
 * scene3d-zup-lifecycle.test.tsx — khoá VÒNG ĐỜI khởi tạo camera.
 *
 * ⚠️ Vì sao tệp này tồn tại. Bản vá Z-up là **đúng một dòng**, và cái sai không
 * nằm ở giá trị mà ở **thứ tự**: `OrbitControls` chụp `camera.up` ngay trong
 * hàm dựng để dựng `_quat` — phép quay đưa trục ấy về Y nội bộ. Đặt `cam.up`
 * SAU khi tạo controls thì controls vẫn quay vị trí quanh Y trong khi `lookAt`
 * dựng tư thế theo Z; hợp của hai phép quay quanh hai trục không trùng nhau là
 * một phép quay có **trục đổi theo từng khung**.
 *
 * Đó không phải suy đoán: `56350f7` đã ship đúng lỗi ấy, và đo được ‖trục quay
 * trung bình‖ = 0,60–0,66 (lộn nhào) so với 1,000 (bàn xoay). Toàn bộ suite
 * khi ấy vẫn xanh, build vẫn xanh, cổng trình duyệt vẫn PASS — vì không test
 * nào canh thứ tự khởi tạo. Bằng chứng:
 * `docs/SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_DIAGNOSIS.md` và
 * `docs/SCENE3D_ORBIT_GATE_AXIS_AUDIT.md`.
 *
 * ─── HAI TẦNG, CỐ Ý ───────────────────────────────────────────────────────
 *
 * ① **Hành vi**: dựng camera + controls thật ở CẢ HAI thứ tự rồi hỏi bằng API
 *    công khai (`getPolarAngle`) xem trục quỹ đạo nằm ở đâu. Đây là nơi chứng
 *    minh *vì sao* thứ tự quan trọng.
 * ② **Ràng buộc vào SẢN PHẨM**: đọc `scene3d-view.tsx` bằng **AST của
 *    TypeScript**, không bằng `indexOf`. Một phép so chuỗi sẽ xanh cả khi dòng
 *    ấy nằm trong chú thích hoặc trong một nhánh chết; AST trả về vị trí thật
 *    của lời gọi thật.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import * as ts from "typescript";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

/**
 * Phần tử giả tối thiểu cho hàm dựng `OrbitControls`.
 *
 * Suite chạy ở môi trường `node` (`vite.config.ts` không khai `environment`),
 * và kéo jsdom vào chỉ để có một `<div>` là đổi hạ tầng test của cả kho. Hàm
 * dựng chỉ cần `addEventListener` / `removeEventListener` / `getRootNode` /
 * `style`; nó không đọc kích thước nào.
 */
function phanTuGia(): HTMLElement {
  const el = {
    style: {} as Record<string, string>,
    addEventListener() { /* test này không phát sự kiện */ },
    removeEventListener() { /* như trên */ },
    getRootNode() { return el; },
    ownerDocument: { addEventListener() {}, removeEventListener() {} },
  };
  return el as unknown as HTMLElement;
}

/** Dựng camera + controls theo một thứ tự cho trước. */
function dung(up: [number, number, number], truocControls: boolean) {
  const cam = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 200);
  if (truocControls) cam.up.set(...up);
  cam.position.set(6, 5, 8);
  const dk = new OrbitControls(cam, phanTuGia());
  if (!truocControls) cam.up.set(...up);
  dk.enableDamping = true;
  return { cam, dk };
}

/**
 * Góc cực mà CONTROLS tự khai, sau khi đặt camera thẳng "trên" theo trục z.
 *
 * Đây là phép hỏi quyết định, và nó dùng **API công khai**: `getPolarAngle()`
 * đo từ trục quỹ đạo mà controls tin là trục lên. Đặt camera tại
 * `target + (0, 0, r)`:
 *   · trục quỹ đạo = Z ⇒ camera đang ở ĐỈNH quỹ đạo ⇒ cực ≈ 0;
 *   · trục quỹ đạo = Y ⇒ camera đang ở XÍCH ĐẠO ⇒ cực ≈ π/2.
 */
function cucKhiCameraOTrenZ(dk: OrbitControls, cam: THREE.PerspectiveCamera): number {
  dk.target.set(0, 0, 0);
  cam.position.set(0, 0, 10);
  dk.update();
  return dk.getPolarAngle();
}

describe("hành vi: trục quỹ đạo nằm ở đâu", () => {
  it("up = (0,0,1) ĐẶT TRƯỚC controls ⇒ trục quỹ đạo là Z", () => {
    const { cam, dk } = dung([0, 0, 1], true);
    /* Camera thẳng trên theo z ⇒ nó ở đỉnh quỹ đạo ⇒ góc cực ≈ 0. */
    expect(cucKhiCameraOTrenZ(dk, cam)).toBeLessThan(0.05);
  });

  it("NỀN ĐỎ ①: bỏ hẳn việc đặt up ⇒ trục quỹ đạo vẫn là Y", () => {
    /* Không gọi `cam.up.set` lần nào — đúng trạng thái `1a553b8`. */
    const cam = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 200);
    cam.position.set(6, 5, 8);
    const dk = new OrbitControls(cam, phanTuGia());
    /* Camera thẳng trên theo z mà controls tin trục lên là Y ⇒ nó nằm ở xích
       đạo của quỹ đạo ⇒ cực ≈ π/2, không phải 0. */
    expect(cucKhiCameraOTrenZ(dk, cam)).toBeGreaterThan(1.5);
  });

  it("NỀN ĐỎ ②: đặt up SAU controls ⇒ trục quỹ đạo vẫn là Y", () => {
    const { cam, dk } = dung([0, 0, 1], false);
    expect(cucKhiCameraOTrenZ(dk, cam)).toBeGreaterThan(1.5);
  });

  it("NỀN ĐỎ ③: up = (0,1,0) đặt đúng chỗ ⇒ trục quỹ đạo vẫn là Y", () => {
    const { cam, dk } = dung([0, 1, 0], true);
    expect(cucKhiCameraOTrenZ(dk, cam)).toBeGreaterThan(1.5);
  });

  it("`_quat` đưa ĐÚNG `cam.up` về trục y — bất biến bên trong, khớp phép đo trên", () => {
    const { cam, dk } = dung([0, 0, 1], true);
    const q = (dk as unknown as { _quat: THREE.Quaternion })._quat;
    const v = cam.up.clone().applyQuaternion(q);
    expect(v.x).toBeCloseTo(0, 6);
    expect(v.y).toBeCloseTo(1, 6);
    expect(v.z).toBeCloseTo(0, 6);
  });

  it("phương vị KHÔNG bị chặn — người học quay hết vòng được", () => {
    const { dk } = dung([0, 0, 1], true);
    expect(dk.minAzimuthAngle).toBe(-Infinity);
    expect(dk.maxAzimuthAngle).toBe(Infinity);
  });
});

/* ═══ TẦNG ②: ràng buộc vào SẢN PHẨM, đọc bằng AST ════════════════════════ */

const DUONG = join(import.meta.dirname, "scene3d-view.tsx");
const CAY = ts.createSourceFile(
  DUONG, readFileSync(DUONG, "utf-8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);

/** Mọi lời gọi `<gì đó>.up.set(...)` trong file, kèm vị trí thật. */
function loiGoiDatUp(): { viTri: number; doiSo: string[] }[] {
  const ra: { viTri: number; doiSo: string[] }[] = [];
  const di = (n: ts.Node) => {
    if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression)
      && n.expression.name.text === "set") {
      const muc = n.expression.expression;
      if (ts.isPropertyAccessExpression(muc) && muc.name.text === "up") {
        ra.push({ viTri: n.getStart(CAY), doiSo: n.arguments.map((a) => a.getText(CAY)) });
      }
    }
    ts.forEachChild(n, di);
  };
  di(CAY);
  return ra;
}

/** Mọi biểu thức `new OrbitControls(...)`, kèm vị trí thật. */
function loiTaoControls(): number[] {
  const ra: number[] = [];
  const di = (n: ts.Node) => {
    if (ts.isNewExpression(n) && ts.isIdentifier(n.expression)
      && n.expression.text === "OrbitControls") ra.push(n.getStart(CAY));
    ts.forEachChild(n, di);
  };
  di(CAY);
  return ra;
}

describe("sản phẩm: `scene3d-view.tsx` dựng camera đúng thứ tự", () => {
  it("đặt `up` ĐÚNG MỘT lần, với đúng (0, 0, 1)", () => {
    const ups = loiGoiDatUp();
    expect(ups.length, "phải có đúng một lời gọi `.up.set(...)`").toBe(1);
    expect(ups[0].doiSo).toEqual(["0", "0", "1"]);
  });

  it("lời gọi ấy đứng TRƯỚC mọi `new OrbitControls(...)`", () => {
    const ups = loiGoiDatUp();
    const controls = loiTaoControls();
    expect(controls.length, "phải có ít nhất một `new OrbitControls`")
      .toBeGreaterThan(0);
    for (const c of controls) {
      expect(ups[0].viTri,
        "`cam.up.set` phải đứng trước `new OrbitControls` — OrbitControls chụp "
        + "`camera.up` ngay trong hàm dựng").toBeLessThan(c);
    }
  });

  it("KHÔNG tạo lại controls ở chỗ nào khác — một lần duy nhất", () => {
    /* Tạo lại controls giữa lúc tương tác là một đường khác dẫn tới cùng lỗi:
       controls mới chụp lại `up` ở một thời điểm không kiểm soát được. */
    expect(loiTaoControls().length).toBe(1);
  });
});
