/**
 * VỊ TRÍ ĐIỂM trong không gian THẾ GIỚI — A–I. **0 mạng, 0 LLM, 0 WebGL.**
 *
 * ─── LỖI ĐƯỢC ĐO, KHÔNG ĐƯỢC ĐOÁN ───────────────────────────────────────
 *
 * Demo tay: `A(0,0,0)` bấm được, còn `B(2,0,0)`, `C(2,2,0)`, `D(0,2,0)`,
 * `S(0,0,2)` thì không — kể cả sau 2907 lượt bấm NHẮM, tức đã loại khả năng
 * "lấy mẫu thưa". Triệu chứng ấy chỉ khớp một nguyên nhân: các điểm **không
 * nằm ở chỗ chúng phải nằm**, và điểm duy nhất đúng chỗ là điểm vốn ở gốc.
 *
 * `buildObject3D` đặt nhóm điểm tại `o.xyz`; vòng dựng cảnh rồi **ghi đè**
 * `position` bằng khoảng dịch bung hình. Với đường/mặt/khối thì vô hại (toạ
 * độ nướng trong `BufferGeometry`), với ĐIỂM thì kéo tất cả về gốc.
 *
 * File này đo bằng chính `THREE.Object3D` sau `updateMatrixWorld(true)` —
 * không đọc mã nguồn rồi tin. Ca chỉ dùng `A` là ca vô nghĩa: `A` ở gốc nên
 * nó xanh cả khi lỗi còn nguyên.
 */
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import type { ExactVec3, SceneObject } from "./scene3d-model";
import {
  BAN_KINH_NHIN,
  KHOANG_CAM_MAC_DINH,
  banKinhBamDiem,
} from "./pick-target";
import {
  buildObject3D,
  datViTriTrinhBay,
  pickSemanticId,
  semanticIdOf,
} from "./scene3d-view";

const BAN_KINH_BAM = banKinhBamDiem(KHOANG_CAM_MAC_DINH);
const DONG_NHAT = { translate: [0, 0, 0] as [number, number, number] };

/** Đúng năm đỉnh của bài demo thật. BỐN trong số đó KHÔNG ở gốc. */
const DIEM: Record<string, ExactVec3> = {
  A: ["0", "0", "0"],
  B: ["2", "0", "0"],
  C: ["2", "2", "0"],
  D: ["0", "2", "0"],
  S: ["0", "0", "2"],
};

function _diem(id: string): SceneObject {
  return {
    id, label: id, type: "point3", render: "point_marker",
    origin: "free", producer: null, depends: [], xyz: DIEM[id],
  };
}

/** Dựng một điểm rồi đặt vị trí trình bày — ĐÚNG đường vòng dựng cảnh đi. */
function dung(id: string, bd = DONG_NHAT): THREE.Object3D {
  const o = buildObject3D(_diem(id), false, BAN_KINH_BAM)!;
  datViTriTrinhBay(o, bd);
  o.updateMatrixWorld(true);
  return o;
}

const theGioi = (o: THREE.Object3D) => {
  const v = new THREE.Vector3();
  o.getWorldPosition(v);
  return [v.x, v.y, v.z];
};

const timProxy = (o: THREE.Object3D): THREE.Object3D => {
  let ra: THREE.Object3D | null = null;
  o.traverse((x) => { if (x.name === "pick-proxy") ra = x; });
  expect(ra, "không tìm thấy pick-proxy").not.toBeNull();
  return ra!;
};

const timChamNhin = (o: THREE.Object3D): THREE.Mesh => {
  let ra: THREE.Mesh | null = null;
  o.traverse((x) => {
    const m = x as THREE.Mesh;
    if (m.isMesh && x.name !== "pick-proxy") ra = m;
  });
  expect(ra, "không tìm thấy chấm nhìn thấy").not.toBeNull();
  return ra!;
};

// ══ A · VỊ TRÍ THẾ GIỚI ĐÚNG cho MỌI điểm, kể cả KHÔNG ở gốc ═════════════
describe("A · điểm nằm đúng chỗ của nó", () => {
  it.each(Object.keys(DIEM))("%s về đúng toạ độ đề cho", (id) => {
    const mong = DIEM[id].map(Number);
    const nhom = dung(id);
    expect(theGioi(nhom)).toEqual(mong);
    expect(theGioi(timChamNhin(nhom))).toEqual(mong);
    expect(theGioi(timProxy(nhom))).toEqual(mong);
  });

  it("D · BỐN điểm KHÔNG ở gốc không được co về gốc", () => {
    // Đây là ca bắt được lỗi. Một ca chỉ dùng `A` sẽ xanh cả khi lỗi còn
    // nguyên, vì `A` vốn ở `(0,0,0)`.
    for (const id of ["B", "C", "D", "S"]) {
      expect(theGioi(dung(id))).not.toEqual([0, 0, 0]);
    }
    expect(theGioi(dung("A"))).toEqual([0, 0, 0]);
  });

  it("năm điểm cho năm vị trí PHÂN BIỆT", () => {
    const v = Object.keys(DIEM).map((id) => theGioi(dung(id)).join(","));
    expect(new Set(v).size).toBe(5);
  });
});

// ══ B · CHẤM NHÌN và PROXY luôn TRÙNG NHAU ═══════════════════════════════
describe("B–C · chấm nhìn thấy và đích bấm không bao giờ lệch nhau", () => {
  it.each(Object.keys(DIEM))("%s · hai vật cùng vị trí thế giới", (id) => {
    const nhom = dung(id);
    expect(theGioi(timChamNhin(nhom))).toEqual(theGioi(timProxy(nhom)));
  });

  it("C · nằm trong một NHÓM đã biến đổi thì vẫn trùng nhau", () => {
    const cha = new THREE.Group();
    cha.position.set(1.5, -2, 0.25);
    cha.rotation.set(0.3, 0.7, -0.2);
    cha.scale.setScalar(1.4);
    for (const id of Object.keys(DIEM)) cha.add(buildObject3D(_diem(id), false, BAN_KINH_BAM)!);
    cha.updateMatrixWorld(true);
    for (const con of cha.children) {
      expect(theGioi(timChamNhin(con))).toEqual(theGioi(timProxy(con)));
    }
  });

  it("bung hình dịch CẢ HAI cùng một khoảng", () => {
    const bd = { translate: [0.3, -0.4, 0.5] as [number, number, number] };
    for (const id of Object.keys(DIEM)) {
      const nhom = dung(id, bd);
      expect(theGioi(timChamNhin(nhom))).toEqual(theGioi(timProxy(nhom)));
      // …và cộng vào vị trí gốc, KHÔNG thay nó.
      expect(theGioi(nhom)).toEqual(
        DIEM[id].map((x, i) => Number(x) + bd.translate[i]),
      );
    }
  });
});

// ══ E–F · DANH TÍNH ══════════════════════════════════════════════════════
describe("E–F · proxy mang đúng danh tính, không đẻ danh tính mới", () => {
  it.each(Object.keys(DIEM))("%s · bấm trúng proxy trả về đúng id", (id) => {
    expect(pickSemanticId(timProxy(dung(id)))).toBe(id);
  });

  it("proxy KHÔNG có id ngữ nghĩa của riêng nó", () => {
    // Nếu có, nó sẽ lọt vào cây phân rã như một thực thể mới.
    expect(semanticIdOf("pick-proxy")).toBeNull();
  });

  it("F · điểm này không cướp danh tính của điểm kia", () => {
    const ids = Object.keys(DIEM).map((id) => pickSemanticId(timProxy(dung(id))));
    expect(ids).toEqual(Object.keys(DIEM));
  });
});

// ══ G–H · KHÔNG tăng kích thước, cả nhìn lẫn bấm ════════════════════════
describe("G–H · bản sửa này KHÔNG được đụng tới kích thước", () => {
  it("G · cỡ NHÌN vẫn 0.09", () => {
    expect(BAN_KINH_NHIN).toBe(0.09);
    const g = timChamNhin(dung("B")).geometry as THREE.SphereGeometry;
    expect(g.parameters.radius).toBe(0.09);
  });

  it("H · bán kính BẤM giữ nguyên giá trị của wave trước", () => {
    const g = (timProxy(dung("B")) as THREE.Mesh).geometry as THREE.SphereGeometry;
    expect(g.parameters.radius).toBeCloseTo(BAN_KINH_BAM, 12);
    expect(BAN_KINH_BAM).toBeCloseTo(0.228, 3);
  });
});

// ══ I · KHÔNG chạm dữ liệu hình học ═════════════════════════════════════
describe("I · dựng và đặt vị trí không đổi một con số nào của cảnh", () => {
  it("`SceneObject` nguyên vẹn sau khi dựng và bung", () => {
    for (const id of Object.keys(DIEM)) {
      const o = _diem(id);
      const truoc = JSON.parse(JSON.stringify(o)) as SceneObject;
      const obj = buildObject3D(o, false, BAN_KINH_BAM)!;
      datViTriTrinhBay(obj, { translate: [9, 9, 9] });
      obj.updateMatrixWorld(true);
      expect(o).toEqual(truoc);
    }
  });
});
