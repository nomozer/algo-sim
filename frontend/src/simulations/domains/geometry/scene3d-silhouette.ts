/**
 * scene3d-silhouette.ts — ĐƯỜNG BAO của khối cong, phụ thuộc camera.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Khối đa diện có `EdgesGeometry`: cạnh của nó là cạnh THẬT, nằm sẵn trong
 * hình. Mặt trơn thì **không có cạnh nào** — `EdgesGeometry` của một hình trụ
 * chia lưới chỉ trả về hai vành (và cả những cạnh lưới giả nếu ngưỡng góc sai).
 * Đo trên sản phẩm thật: p4/p5 dựng ra một **vệt xám không có một nét nào** —
 * không vành, không đường sinh, không trục. So với mockup đã duyệt thì mất
 * toàn bộ thông tin hình dạng.
 *
 * Thứ làm nên hình dáng của mặt trơn là **đường bao** (silhouette): nơi mặt
 * tiếp tuyến chứa mắt nhìn. Nó ĐỔI KHI CAMERA ĐỔI, nên phải tính lại mỗi khung.
 *
 * ─── CHIA VIỆC: TĨNH vs THEO CAMERA ──────────────────────────────────────
 *
 * Không phải mọi nét của khối cong đều phụ thuộc camera:
 *
 *   • **Vành** (trên/dưới của trụ, đáy của nón) là đường tròn CỐ ĐỊNH trong
 *     không gian. Phần thấy/khuất của chúng đã có cơ chế hai lượt chiều sâu lo
 *     (`LessEqualDepth` / `GreaterDepth` trên lớp chiều sâu của khối) — đúng
 *     cùng lối với cạnh khối đa diện, và tự cập nhật khi xoay mà không tính gì.
 *   • **Đường sinh bao** (hai đường sinh của trụ/nón) và **đường bao mặt cầu**
 *     thì phụ thuộc camera thật ⇒ cập nhật mỗi khung.
 *
 * Nhờ chia như vậy, phần phải tính lại mỗi khung chỉ còn **hai đoạn thẳng**
 * (trụ/nón) hoặc **một đường tròn** (cầu) cho mỗi khối.
 *
 * ─── KHÔNG CẤP PHÁT TRONG VÒNG VẼ ────────────────────────────────────────
 *
 * Hình học và vật liệu dựng MỘT lần; `capNhat` chỉ ghi đè vào mảng đã có rồi
 * bật `needsUpdate`. Cổng tương tác đòi `capPhatBuffer = 0` khi kéo, nên gọi
 * `setPositions` lại mỗi khung (nó dựng `InstancedInterleavedBuffer` mới) là
 * vi phạm trực tiếp.
 */
import * as THREE from "three";
import { BE_DAY_PX, taoNet, taoVatLieuNet } from "./scene3d-wide-line";

/**
 * Số cung chia một vành/đường bao tròn.
 *
 * ⚠️ Mỗi vành đi HAI LƯỢT chiều sâu, và một hình trụ có HAI vành ⇒ số đoạn
 * thực tế gấp bốn con số này. Mỗi đoạn của nét rộng là một dải tam giác riêng,
 * nên đây là hằng số đắt nhất trong module. Lấy đúng `VONG_CHIA` của lưới mặt
 * (48): vành mịn hơn lưới thì cũng không đọc ra mịn hơn.
 */
const VONG_CHIA_BAO = 48;

export type LoaiKhoiCong = "ball" | "cylinder" | "cone";

export interface KhoiCongMoTa {
  kind: LoaiKhoiCong;
  /** Tâm đáy (trụ/nón) hoặc tâm cầu. */
  tam: THREE.Vector3;
  /** Tâm mặt trên (trụ) hoặc đỉnh (nón). `null` với mặt cầu. */
  dinh: THREE.Vector3 | null;
  r: number;
  h: number;
}

export interface MauBao {
  thay: number;
  khuat: number;
}

export interface DuongBao {
  nhom: THREE.Group;
  /**
   * Cập nhật phần phụ thuộc camera. `camTheGioi` là vị trí camera trong TOẠ ĐỘ
   * THẾ GIỚI; nhóm được đặt ở gốc nên không cần đổi hệ.
   */
  capNhat(camTheGioi: THREE.Vector3): void;
}

const _tamPhu = new THREE.Vector3();

/**
 * Cơ sở trực chuẩn có `u` làm trục thứ ba, ghi vào `e1`/`e2` có sẵn.
 *
 * Ghi vào chỗ cho trước chứ không trả về vectơ mới: hàm này chạy trong vòng vẽ
 * của đường bao mặt cầu, nơi mỗi lần cấp phát là rác sinh ra 60 lần mỗi giây.
 */
function coSoVao(u: THREE.Vector3, e1: THREE.Vector3, e2: THREE.Vector3): void {
  if (Math.abs(u.z) < 0.9) _tamPhu.set(0, 0, 1); else _tamPhu.set(1, 0, 0);
  e1.crossVectors(_tamPhu, u).normalize();
  e2.crossVectors(u, e1).normalize();
}

/** Một cơ sở trực chuẩn có `u` làm trục thứ ba. Dùng lúc DỰNG, không trong vòng vẽ. */
function coSo(u: THREE.Vector3): [THREE.Vector3, THREE.Vector3] {
  const e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  coSoVao(u, e1, e2);
  return [e1, e2];
}

/** Toạ độ phẳng của một đường tròn, dạng đường gấp khúc khép kín. */
function toaDoVanh(tam: THREE.Vector3, e1: THREE.Vector3, e2: THREE.Vector3,
  r: number): number[] {
  const ra: number[] = [];
  for (let i = 0; i <= VONG_CHIA_BAO; i++) {
    const t = (i / VONG_CHIA_BAO) * Math.PI * 2;
    ra.push(tam.x + r * (Math.cos(t) * e1.x + Math.sin(t) * e2.x),
      tam.y + r * (Math.cos(t) * e1.y + Math.sin(t) * e2.y),
      tam.z + r * (Math.cos(t) * e1.z + Math.sin(t) * e2.z));
  }
  return ra;
}

/** Đường tròn đi HAI LƯỢT chiều sâu — phần bị khối che đọc ra là khuất. */
function vanhHaiLuot(toaDo: number[], mau: MauBao, chuKy: number, ten: string): THREE.Group {
  const nhom = new THREE.Group();
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(toaDo, 3));
  const thay = taoNet(g, true, taoVatLieuNet({
    mau: mau.thay, beDayPx: BE_DAY_PX.canhThay, depthFunc: THREE.LessEqualDepth,
  }));
  thay.name = `${ten}:thay`;
  const khuat = taoNet(g, true, taoVatLieuNet({
    mau: mau.khuat, beDayPx: BE_DAY_PX.canhKhuat, dut: true, chuKy,
    depthFunc: THREE.GreaterDepth, depthWrite: false,
  }));
  khuat.name = `${ten}:khuat`;
  nhom.add(thay, khuat);
  return nhom;
}

/** Vật nét dựng sẵn `soDoan` đoạn, để `capNhat` ghi đè tại chỗ. */
function netDongDuoc(soDoan: number, mau: number, beDayPx: number, ten: string) {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position",
    new THREE.Float32BufferAttribute(new Float32Array(soDoan * 6), 3));
  const d = taoNet(g, false, taoVatLieuNet({
    mau, beDayPx, depthFunc: THREE.LessEqualDepth,
  }));
  d.name = ten;
  /* Toạ độ đổi mỗi khung ⇒ hộp bao dựng lúc tạo là vô nghĩa. Tắt cắt khung
   * thay vì tính lại hộp bao mỗi khung (tính lại là cấp phát). */
  d.frustumCulled = false;
  /* ⚠️ VÀ PHẢI ĐỨNG NGOÀI PHÉP KHỚP KHUNG.
   *
   * Lúc dựng, bộ đệm toàn số 0 ⇒ hộp bao của vật này ôm gốc toạ độ. Khớp
   * khung chạy NGAY SAU khi dựng cảnh, tức trước lần `capNhat` đầu tiên, nên
   * nó cộng thêm điểm (0,0,0) vào hộp bao rồi lùi camera ra — đo được: hình
   * trụ p4 tụt từ ~66 % khung xuống ~20 %. Kể cả sau khi có toạ độ thật thì
   * đường bao vẫn là hệ quả của vị trí camera, nên để nó tham gia quyết định
   * vị trí camera là một vòng lặp phản hồi. */
  d.userData.baoDong = true;
  return d;
}

/** Mảng toạ độ thật bên trong một vật nét — ghi vào đây rồi bật `needsUpdate`. */
function mangToaDo(d: THREE.Object3D): { mang: Float32Array; bat(): void } | null {
  const g = (d as THREE.Mesh).geometry as THREE.BufferGeometry;
  const at = g.getAttribute("instanceStart") as THREE.InterleavedBufferAttribute | undefined;
  if (!at?.data) return null;
  const data = at.data;
  return {
    mang: data.array as Float32Array,
    bat: () => {
      data.needsUpdate = true;
      const e = g.getAttribute("instanceEnd") as THREE.InterleavedBufferAttribute;
      if (e?.data && e.data !== data) e.data.needsUpdate = true;
    },
  };
}

/**
 * Đường bao của một khối cong.
 *
 * Toán, cho từng loại — mọi thứ đều là dạng đóng, không dò số:
 *
 * **Trụ.** Mặt tiếp tuyến dọc đường sinh ở góc `θ` có pháp tuyến `n(θ)` và đi
 * qua `O + r·n(θ)`. Mắt nằm trong mặt ấy ⇔ `n(θ)·(C−O) = r`. Đặt
 * `a = (C−O)·e1`, `b = (C−O)·e2`, `R = hypot(a,b)`, `φ = atan2(b,a)`:
 *
 *     R·cos(θ − φ) = r   ⇒   θ = φ ± acos(r/R)      (có nghiệm khi R > r)
 *
 * **Nón.** Pháp tuyến mặt tiếp tuyến dọc đường sinh qua `P(θ)` là `h·n(θ) + r·u`.
 * Với `d = C − S`, `c = d·u`:
 *
 *     h·(a·cosθ + b·sinθ) + r·c = 0  ⇒  θ = φ ± acos(−r·c / (h·R))
 *
 * **Cầu.** Đường bao là đường tròn tiếp xúc của nón tiếp tuyến từ `C`: tâm
 * `Q + (r²/D²)·(C−Q)`, bán kính `r·√(1 − r²/D²)`, pháp tuyến `C−Q`, với
 * `D = |C−Q|`.
 */
export function duongBaoKhoiCong(
  mo: KhoiCongMoTa, mau: MauBao, chuKy: number, id: string,
): DuongBao | null {
  if (!(mo.r > 0)) return null;
  const nhom = new THREE.Group();

  if (mo.kind === "ball") {
    const bao = netDongDuoc(VONG_CHIA_BAO, mau.thay, BE_DAY_PX.canhThay,
      `bao:${id}:cau`);
    nhom.add(bao);
    const buf = mangToaDo(bao);
    /* Mọi vectơ tạm dựng MỘT lần ở đây. `capNhat` chạy mỗi khung, nên một
     * `new Vector3()` trong thân hàm là rác sinh ra 60 lần mỗi giây. */
    const dQ = new THREE.Vector3(), u = new THREE.Vector3();
    const e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
    const tamBao = new THREE.Vector3();
    return {
      nhom,
      capNhat(cam) {
        if (!buf) return;
        dQ.copy(cam).sub(mo.tam);
        const D = dQ.length();
        if (!(D > mo.r)) return;            // camera trong lòng cầu ⇒ không có bao
        u.copy(dQ).divideScalar(D);
        const k = (mo.r * mo.r) / (D * D);
        tamBao.copy(mo.tam).addScaledVector(dQ, k);
        const rb = mo.r * Math.sqrt(Math.max(0, 1 - k));
        coSoVao(u, e1, e2);
        for (let i = 0; i < VONG_CHIA_BAO; i++) {
          const t0 = (i / VONG_CHIA_BAO) * Math.PI * 2;
          const t1 = ((i + 1) / VONG_CHIA_BAO) * Math.PI * 2;
          const o = i * 6;
          buf.mang[o] = tamBao.x + rb * (Math.cos(t0) * e1.x + Math.sin(t0) * e2.x);
          buf.mang[o + 1] = tamBao.y + rb * (Math.cos(t0) * e1.y + Math.sin(t0) * e2.y);
          buf.mang[o + 2] = tamBao.z + rb * (Math.cos(t0) * e1.z + Math.sin(t0) * e2.z);
          buf.mang[o + 3] = tamBao.x + rb * (Math.cos(t1) * e1.x + Math.sin(t1) * e2.x);
          buf.mang[o + 4] = tamBao.y + rb * (Math.cos(t1) * e1.y + Math.sin(t1) * e2.y);
          buf.mang[o + 5] = tamBao.z + rb * (Math.cos(t1) * e1.z + Math.sin(t1) * e2.z);
        }
        buf.bat();
      },
    };
  }

  if (!mo.dinh || !(mo.h > 0)) return null;
  const u = mo.dinh.clone().sub(mo.tam).normalize();
  const [e1, e2] = coSo(u);

  // ── vành: hình học CỐ ĐỊNH, thấy/khuất do hai lượt chiều sâu lo ──
  nhom.add(vanhHaiLuot(toaDoVanh(mo.tam, e1, e2, mo.r), mau, chuKy, `vanh-day:${id}`));
  if (mo.kind === "cylinder") {
    nhom.add(vanhHaiLuot(toaDoVanh(mo.dinh, e1, e2, mo.r), mau, chuKy, `vanh-tren:${id}`));
  }

  // ── hai đường sinh bao: PHỤ THUỘC CAMERA ──
  const sinh = netDongDuoc(2, mau.thay, BE_DAY_PX.canhThay, `bao:${id}:${mo.kind}`);
  nhom.add(sinh);
  const buf = mangToaDo(sinh);
  const d = new THREE.Vector3();

  return {
    nhom,
    capNhat(cam) {
      if (!buf) return;
      const goc = mo.kind === "cone" ? mo.dinh! : mo.tam;
      d.copy(cam).sub(goc);
      const a = d.dot(e1), b = d.dot(e2);
      const R = Math.hypot(a, b);
      if (!(R > 1e-9)) return;
      const phi = Math.atan2(b, a);
      let cosA: number;
      if (mo.kind === "cylinder") {
        cosA = mo.r / R;
      } else {
        cosA = (-mo.r * d.dot(u)) / (mo.h * R);
      }
      if (!(cosA >= -1 && cosA <= 1)) {
        // Không có đường sinh bao (mắt ở trong khối, hoặc nhìn dọc trục).
        buf.mang.fill(0);
        buf.bat();
        return;
      }
      const alpha = Math.acos(cosA);
      for (let k = 0; k < 2; k++) {
        const t = phi + (k === 0 ? alpha : -alpha);
        const nx = Math.cos(t) * e1.x + Math.sin(t) * e2.x;
        const ny = Math.cos(t) * e1.y + Math.sin(t) * e2.y;
        const nz = Math.cos(t) * e1.z + Math.sin(t) * e2.z;
        const o = k * 6;
        buf.mang[o] = mo.tam.x + mo.r * nx;
        buf.mang[o + 1] = mo.tam.y + mo.r * ny;
        buf.mang[o + 2] = mo.tam.z + mo.r * nz;
        if (mo.kind === "cylinder") {
          buf.mang[o + 3] = mo.dinh!.x + mo.r * nx;
          buf.mang[o + 4] = mo.dinh!.y + mo.r * ny;
          buf.mang[o + 5] = mo.dinh!.z + mo.r * nz;
        } else {
          buf.mang[o + 3] = mo.dinh!.x;
          buf.mang[o + 4] = mo.dinh!.y;
          buf.mang[o + 5] = mo.dinh!.z;
        }
      }
      buf.bat();
    },
  };
}
