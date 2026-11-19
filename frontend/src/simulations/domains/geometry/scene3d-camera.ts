/**
 * scene3d-camera.ts — KHUNG NHÌN, tính từ hộp bao của vật ĐANG THẤY.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Bản trước đặt camera bằng một hằng số (`position.set(6, 5, 8)`) cho mọi bài.
 * Với bài toạ độ nhỏ thì hình chiếm một góc khung; với bài toạ độ lớn thì hình
 * tràn ra ngoài. Ảnh chụp thật cho thấy cả hai kiểu hỏng.
 *
 * ⚠️ Đây là **phép tính trình bày**, không phải phép tính hình học: đầu vào là
 * các vị trí đã do nhân hình học sinh ra, đầu ra là vị trí camera tính bằng
 * đơn vị thế giới của renderer. Nó không quay lại `Scene3D`, không sinh vật
 * mới, và không đổi một toạ độ nào.
 *
 * ⚠️ **Không tự gọi khi đổi bước.** Khung nhìn phải đứng yên giữa bước k và
 * k+1, nếu không thì hoạt cảnh tua bước biến thành hoạt cảnh đổi góc máy, và
 * người xem không phân biệt được cái nào đang đổi. Chỉ gọi khi: nạp cảnh lần
 * đầu, người dùng bấm xem lại toàn hình, và khi tách/ráp khối làm kích thước
 * hình đổi hẳn.
 */

/** Hộp bao trục, đơn vị thế giới. */
export interface HopBao {
  min: [number, number, number];
  max: [number, number, number];
}

/** Kết quả đặt khung nhìn — vị trí camera và điểm nó nhìn vào. */
export interface KhungNhin {
  viTri: [number, number, number];
  nhinVao: [number, number, number];
}

/**
 * Hướng nhìn mặc định: [8, 3, 6] (phương vị ~20.6°, góc ngẩng ~35.1°).
 * Tránh hình chiếu suy biến dọc đường chéo đáy (45° ở hình vuông, 37°-53° ở hình chữ nhật),
 * giữ S, A, C không thẳng hàng/chồng lấn trên màn hình và bảo toàn độ sâu cho mọi họ bài.
 */
export const HUONG: readonly [number, number, number] = [8, 3, 6];

/** Phần khung mà hình nên chiếm. Chỉ thị đặt khoảng 55–80%; lấy giữa dải. */
const TI_LE_LAP_KHUNG = 0.68;

/** Khoảng cách tối thiểu, chặn ca hộp bao suy biến về một điểm. */
const KHOANG_TOI_THIEU = 2.5;

export function hopBaoCuaDiem(diem: [number, number, number][]): HopBao | null {
  if (diem.length === 0) return null;
  const min: [number, number, number] = [Infinity, Infinity, Infinity];
  const max: [number, number, number] = [-Infinity, -Infinity, -Infinity];
  for (const p of diem) {
    for (let i = 0; i < 3; i++) {
      if (!Number.isFinite(p[i])) return null;
      if (p[i] < min[i]) min[i] = p[i];
      if (p[i] > max[i]) max[i] = p[i];
    }
  }
  return { min, max };
}

/**
 * Đặt khung nhìn sao cho hộp bao lấp khoảng `TI_LE_LAP_KHUNG` chiều cao khung.
 *
 * `fovDo` là góc mở dọc của camera (độ); `tiLeKhung` là rộng/cao của khung vẽ.
 * Khi khung hẹp hơn cao, chiều RỘNG mới là chiều bị bó, nên khoảng cách phải
 * lấy theo cái lớn hơn trong hai ràng buộc — bỏ qua điều này thì ở khung dọc
 * hình bị cắt hai bên.
 *
 * Trả `null` khi đầu vào không dùng được, để nơi gọi giữ nguyên khung nhìn
 * hiện tại thay vì nhảy tới một chỗ vô nghĩa. **Không bao giờ trả `NaN`.**
 */
export function khungNhinVua(
  hop: HopBao | null,
  fovDo: number,
  tiLeKhung: number,
): KhungNhin | null {
  if (!hop) return null;
  if (!Number.isFinite(fovDo) || fovDo <= 0 || fovDo >= 180) return null;
  if (!Number.isFinite(tiLeKhung) || tiLeKhung <= 0) return null;

  const tam: [number, number, number] = [
    (hop.min[0] + hop.max[0]) / 2,
    (hop.min[1] + hop.max[1]) / 2,
    (hop.min[2] + hop.max[2]) / 2,
  ];
  const nuaCanh = [
    (hop.max[0] - hop.min[0]) / 2,
    (hop.max[1] - hop.min[1]) / 2,
    (hop.max[2] - hop.min[2]) / 2,
  ];
  const banKinh = Math.hypot(nuaCanh[0], nuaCanh[1], nuaCanh[2]);
  if (!Number.isFinite(banKinh)) return null;

  const fov = (fovDo * Math.PI) / 180;
  const canDoc = banKinh / Math.sin(fov / 2);
  // Góc mở NGANG suy từ góc dọc và tỉ lệ khung.
  const fovNgang = 2 * Math.atan(Math.tan(fov / 2) * tiLeKhung);
  const canNgang = banKinh / Math.sin(fovNgang / 2);
  const can = Math.max(canDoc, canNgang) / TI_LE_LAP_KHUNG;
  const khoang = Math.max(KHOANG_TOI_THIEU, can);
  if (!Number.isFinite(khoang)) return null;

  const dai = Math.hypot(HUONG[0], HUONG[1], HUONG[2]);
  return {
    viTri: [
      tam[0] + (HUONG[0] / dai) * khoang,
      tam[1] + (HUONG[1] / dai) * khoang,
      tam[2] + (HUONG[2] / dai) * khoang,
    ],
    nhinVao: tam,
  };
}

/* ─── GÓC NHÌN SƯ PHẠM (w10) ───────────────────────────────────────────────
 *
 * Một hướng cố định cho mọi cảnh nhìn dọc cạnh AB của hình chóp đáy chữ nhật:
 * đáy bị ép dẹt, đỉnh A lọt giữa hình, nhãn đè nhau (ảnh w09). Hướng nay CHỌN
 * theo số đo của chính cảnh — hình chiếu các đỉnh và cạnh — không theo tên bài
 * hay toạ độ riêng của họ nào. Z vẫn hướng lên; OrbitControls không đổi.
 */
export type Diem3 = [number, number, number];

/** Số đo của một hướng nhìn, chuẩn hoá theo bán kính R quanh trọng tâm. */
export interface ChatLuongGocNhin {
  /** Diện tích bao lồi của hình chiếu / R² — hình có "choán" mặt phẳng nhìn không. */
  dienTichBao: number;
  /** Khoảng cách nhỏ nhất giữa hai đỉnh chiếu / R — đỉnh (và nhãn) chồng nhau. */
  khoangDinhMin: number;
  /** Khoảng hở nhỏ nhất đỉnh ↔ cạnh không chứa nó / R — đỉnh nằm lên cạnh khác. */
  khoangDinhCanhMin: number;
  /** Dải độ sâu các đỉnh dọc hướng nhìn / R — hình có chiều sâu hay bẹt. */
  doSau: number;
  /** min |n·d| trên các mặt — mặt nào bị ép thành một đường thẳng. */
  matNghiengMin: number;
}

const tru = (a: Diem3, b: Diem3): Diem3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const tich = (a: Diem3, b: Diem3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cheo = (a: Diem3, b: Diem3): Diem3 =>
  [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const chuan = (a: Diem3): Diem3 => {
  const d = Math.hypot(...a) || 1;
  return [a[0] / d, a[1] / d, a[2] / d];
};

/** Hướng TỪ tâm TỚI camera, Z-up: phương vị quanh Z, góc ngẩng so với mặt Oxy. */
export function huongTuGoc(phuongViDo: number, caoDo: number): Diem3 {
  const a = (phuongViDo * Math.PI) / 180;
  const e = (caoDo * Math.PI) / 180;
  return [Math.cos(e) * Math.cos(a), Math.cos(e) * Math.sin(a), Math.sin(e)];
}

/** Hướng QUEN kiểu SGK mà `chonHuongNhin` kéo về: phương vị của `HUONG`, góc ngẩng 22.4° — góc "Góc SGK" của HTML
 *  tham chiếu (φ = 1.18 rad ⇒ 90° − 67.6°). Chỉ đổi lực kéo trong điểm chấm; ngưỡng vẫn đo theo `HUONG`. */
export const HUONG_SGK: Diem3 = huongTuGoc((Math.atan2(HUONG[1], HUONG[0]) * 180) / Math.PI, 22.4);

/** Trọng số kéo về `HUONG_SGK` trong điểm chấm (bản trước 0.85 — đo trên các cảnh B1/B2: quá yếu để đổi lựa chọn
 *  giữa các hướng ĐÃ đạt ngưỡng). Ngưỡng vẫn xét TRƯỚC, nên hướng suy biến không thắng nhờ lực kéo. */
const LUC_KEO_SGK = 2;

function chieu(diem: Diem3[], huong: Diem3) {
  const d = chuan(huong);
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  const tam = diem.reduce<Diem3>((s, p) => [s[0] + p[0] / diem.length, s[1] + p[1] / diem.length,
    s[2] + p[2] / diem.length], [0, 0, 0]);
  const R = Math.max(1e-9, ...diem.map((p) => Math.hypot(...tru(p, tam))));
  return { d, R, uv: diem.map((p) => [tich(tru(p, tam), phai) / R, tich(tru(p, tam), len) / R]),
    sau: diem.map((p) => tich(tru(p, tam), d) / R) };
}

function dienTichBaoLoi(uv: number[][]): number {
  const p = [...uv].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (p.length < 3) return 0;
  const cross = (o: number[], a: number[], b: number[]) =>
    (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const duoi: number[][] = [];
  const tren: number[][] = [];
  for (const q of p) {
    while (duoi.length >= 2 && cross(duoi.at(-2)!, duoi.at(-1)!, q) <= 0) duoi.pop();
    duoi.push(q);
  }
  for (const q of [...p].reverse()) {
    while (tren.length >= 2 && cross(tren.at(-2)!, tren.at(-1)!, q) <= 0) tren.pop();
    tren.push(q);
  }
  const bao = [...duoi.slice(0, -1), ...tren.slice(0, -1)];
  let s = 0;
  for (let i = 0; i < bao.length; i++) {
    const [a, b] = [bao[i], bao[(i + 1) % bao.length]];
    s += a[0] * b[1] - b[0] * a[1];
  }
  return Math.abs(s) / 2;
}

function khoangDiemDoan(p: number[], a: number[], b: number[]): number {
  const ab = [b[0] - a[0], b[1] - a[1]];
  const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1])
    / Math.max(1e-12, ab[0] ** 2 + ab[1] ** 2)));
  return Math.hypot(p[0] - a[0] - t * ab[0], p[1] - a[1] - t * ab[1]);
}

function khoangDiemDoan3(p: Diem3, a: Diem3, b: Diem3): number {
  const ab = tru(b, a);
  const t = Math.max(0, Math.min(1, tich(tru(p, a), ab) / Math.max(1e-12, tich(ab, ab))));
  return Math.hypot(...tru(p, [a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2]]));
}

/** Đo một hướng nhìn. `canh`/`mat` là chỉ số vào `diem`. */
export function danhGiaGocNhin(
  diem: Diem3[], canh: [number, number][], mat: number[][], huong: Diem3,
): ChatLuongGocNhin {
  const { d, R, uv, sau } = chieu(diem, huong);
  let khoangDinhMin = Infinity;
  for (let i = 0; i < uv.length; i++) {
    for (let j = i + 1; j < uv.length; j++) {
      khoangDinhMin = Math.min(khoangDinhMin, Math.hypot(uv[i][0] - uv[j][0], uv[i][1] - uv[j][1]));
    }
  }
  let khoangDinhCanhMin = Infinity;
  for (let i = 0; i < uv.length; i++) {
    for (const [a, b] of canh) {
      if (a === i || b === i) continue;
      // Điểm NẰM TRÊN cạnh trong không gian (đỉnh thiết diện, trung điểm): hình
      // chiếu nào cũng đặt nó lên cạnh — đó là sự thật hình học, không phải chồng nhãn.
      if (khoangDiemDoan3(diem[i], diem[a], diem[b]) < 1e-6 * R) continue;
      khoangDinhCanhMin = Math.min(khoangDinhCanhMin, khoangDiemDoan(uv[i], uv[a], uv[b]));
    }
  }
  let matNghiengMin = Infinity;
  for (const f of mat) {
    if (f.length < 3) continue;
    const n = chuan(cheo(tru(diem[f[1]], diem[f[0]]), tru(diem[f[2]], diem[f[0]])));
    matNghiengMin = Math.min(matNghiengMin, Math.abs(tich(n, d)));
  }
  return {
    dienTichBao: dienTichBaoLoi(uv),
    khoangDinhMin: Number.isFinite(khoangDinhMin) ? khoangDinhMin : 0,
    khoangDinhCanhMin: Number.isFinite(khoangDinhCanhMin) ? khoangDinhCanhMin : 1,
    doSau: sau.length ? Math.max(...sau) - Math.min(...sau) : 0,
    matNghiengMin: Number.isFinite(matNghiengMin) ? matNghiengMin : 1,
  };
}

/* NGƯỠNG — hai loại, mỗi loại gắn với một tham chiếu nói rõ được:
 *
 *  · KHOẢNG HỞ (đỉnh↔đỉnh, đỉnh↔cạnh) gắn với khối lập phương đơn vị nhìn theo
 *    hướng mặc định cũ `HUONG` — hướng ấy được chọn có chủ đích để không đỉnh
 *    nào chồng đỉnh nào trên khối hộp, và các cảnh khối hộp của w09 đọc được ở
 *    đó. Đạt khi ≥ một nửa số đo tham chiếu.
 *  · DIỆN TÍCH BAO và ĐỘ SÂU gắn với hướng TỐT NHẤT của CHÍNH cảnh ấy: hình chóp
 *    cao gầy không bao giờ choán mặt phẳng nhìn như khối hộp, nên so với khối
 *    hộp là phạt hình dáng chứ không phạt góc nhìn. Đạt khi ≥ 60% / 50% cực đại.
 *  · Không mặt nào gần song song tia nhìn quá 6° (|n·d| ≥ sin 6°) — mặt ấy bị ép
 *    thành một đường thẳng, đúng kiểu "hình dẹt". */
const _LP: Diem3[] = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]];
const _LP_MAT = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]];
const _LP_CANH: [number, number][] = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4],
  [0, 4], [1, 5], [2, 6], [3, 7]];
export const GOC_NHIN_THAM_CHIEU = danhGiaGocNhin(_LP, _LP_CANH, _LP_MAT, [...HUONG]);
export const NGUONG_GOC_NHIN = {
  tiLeDienTichBao: 0.6,
  tiLeDoSau: 0.5,
  khoangDinhMin: 0.5 * GOC_NHIN_THAM_CHIEU.khoangDinhMin,
  khoangDinhCanhMin: 0.5 * GOC_NHIN_THAM_CHIEU.khoangDinhCanhMin,
  matNghiengMin: Math.sin((6 * Math.PI) / 180),
} as const;

/** Cực đại diện tích bao / độ sâu của cảnh trên lưới hướng — mẫu số của ngưỡng. */
export interface TranGocNhin { dienTichBao: number; doSau: number }

export interface TuyChonHuongNhin {
  /** Pháp tuyến đơn vị của các miền/mặt trọng tâm (thiết diện, tam giác qua trục, mặt phẳng nghiên cứu, tam giác nhân chứng vuông góc). */
  matTrongTam?: Diem3[];
  /** Cặp tâm hai đáy khối trụ `[tamDuoi, tamTren, banKinh]` để tránh góc nhìn làm hai đáy chồng lấn hoặc một đáy bị nhìn nghiêng bẹt. */
  capDayTru?: [Diem3, Diem3, number][];
  /** Các mặt nắp ngang của khối đa diện hai đáy (`[tamMat, phapTuyenDonVi]`, vd lăng trụ / hình hộp) để tránh góc nhìn phối cảnh làm mặt đáy trên bị bẹt thành đường thẳng. */
  matCap?: [Diem3, Diem3][];
  /** Cảnh có khối tròn xoay (nón/trụ) kết hợp mặt/tam giác trọng tâm — tránh hướng nhìn trùng khít đường sinh biên làm cạnh thiết diện đè lên đường bao khối. */
  coKhoiCong?: boolean;
  /** Mặt phẳng tiếp xúc mặt cầu: ưu tiên góc nhìn nghiêng tiếp tuyến để tiếp điểm nằm sát vành cầu và các điểm phụ trên mặt phẳng nằm ngoài đĩa cầu. */
  matTiepDienCau?: {
    tamCau: Diem3;
    banKinh: number;
    tiepDiem: Diem3;
    phapTuyen: Diem3;
    diemTrenMat: Diem3[];
  }[];
}

export function datNguong(q: ChatLuongGocNhin, tran: TranGocNhin): boolean {
  return q.dienTichBao >= NGUONG_GOC_NHIN.tiLeDienTichBao * tran.dienTichBao
    && q.doSau >= NGUONG_GOC_NHIN.tiLeDoSau * tran.doSau
    && q.khoangDinhMin >= NGUONG_GOC_NHIN.khoangDinhMin
    && q.khoangDinhCanhMin >= NGUONG_GOC_NHIN.khoangDinhCanhMin
    && q.matNghiengMin >= NGUONG_GOC_NHIN.matNghiengMin;
}

/** Lưới hướng: phương vị 10° × góc ngẩng 15°–40° (Z-up, như OrbitControls). */
function luoiHuong(): Diem3[] {
  const ra: Diem3[] = [];
  for (let cao = 15; cao <= 40; cao += 5) {
    for (let pv = 0; pv < 360; pv += 10) ra.push(huongTuGoc(pv, cao));
  }
  return ra;
}

/** Đo cả lưới một lần: số đo từng hướng + cực đại làm mẫu số ngưỡng. */
export function doLuoiGocNhin(diem: Diem3[], canh: [number, number][], mat: number[][]) {
  const cac = luoiHuong().map((huong) => ({ huong, q: danhGiaGocNhin(diem, canh, mat, huong) }));
  const tran: TranGocNhin = {
    dienTichBao: Math.max(0, ...cac.map((c) => c.q.dienTichBao)),
    doSau: Math.max(0, ...cac.map((c) => c.q.doSau)),
  };
  return { cac, tran };
}

function doMoMatTrongTam(
  huong: Diem3,
  matTrongTam: readonly Diem3[],
  coKhoiCong = false,
): { tb: number; minNghieng: number; coMatDung: boolean } {
  if (matTrongTam.length === 0) return { tb: 0, minNghieng: 1, coMatDung: false };
  const d = chuan(huong);
  let tong = 0;
  let minNghieng = Infinity;
  let coMatDung = false;
  let dem = 0;
  for (const rawN of matTrongTam) {
    const len = Math.hypot(...rawN);
    if (!(len > 1e-9)) continue;
    const n: Diem3 = [rawN[0] / len, rawN[1] / len, rawN[2] / len];
    const mo = Math.abs(tich(n, d));
    const kich = coKhoiCong && Math.abs(n[2]) < 0.35
      ? (mo <= 0.87 ? mo / 0.87 : Math.max(0.74, 1 - 0.95 * ((mo - 0.87) / 0.13)))
      : Math.min(mo, 0.94) / 0.94;
    tong += kich;
    dem += 1;
    if (Math.abs(n[2]) < 0.90) {
      coMatDung = true;
      minNghieng = Math.min(minNghieng, mo);
    }
  }
  return {
    tb: dem > 0 ? tong / dem : 0,
    minNghieng: Number.isFinite(minNghieng) ? minNghieng : 1,
    coMatDung,
  };
}

function uocLuongCameraPhoiCanh(diem: Diem3[], d: Diem3): Diem3 {
  if (diem.length >= 2) {
    const kn = khungNhinSuPham(diem, [], [], 40, 1.25, d, { tiLeDoc: 0.67 });
    if (kn) return kn.viTri;
  }
  return [d[0] * 10, d[1] * 10, d[2] * 10];
}

function kiemMoPhoiCanhNapDaDien(camEst: Diem3, matCap: readonly [Diem3, Diem3][]): boolean {
  for (const [tamMat, phap] of matCap) {
    const tia = chuan(tru(camEst, tamMat));
    if (Math.abs(tich(phap, tia)) < 0.22) return false;
  }
  return true;
}

function diemTachDayTru(
  huong: Diem3,
  camEst: Diem3,
  capDayTru: readonly [Diem3, Diem3, number][],
): { hopLe: boolean; thuong: number } {
  if (capDayTru.length === 0) return { hopLe: true, thuong: 0 };
  const d = chuan(huong);
  let hopLe = true;
  let tong = 0;
  for (const [c0, c1, r] of capDayTru) {
    const truc = tru(c1, c0);
    const h = Math.hypot(...truc);
    if (!(h > 1e-6)) continue;
    const doc = tich(truc, d);
    const hChieu = Math.sqrt(Math.max(0, h * h - doc * doc));
    const uRaw: Diem3 = [truc[0] / h, truc[1] / h, truc[2] / h];
    const u: Diem3 = uRaw[2] < 0 ? [-uRaw[0], -uRaw[1], -uRaw[2]] : uRaw;
    const moTruc = tich(u, d);
    const banTrucNho = Math.max(0, r) * Math.abs(tich(u, d));
    const moDay0 = tich(u, chuan(tru(camEst, c0)));
    const moDay1 = tich(u, chuan(tru(camEst, c1)));
    if (r > 1e-6 && (moTruc < 0.25 || moTruc > 0.56 || hChieu < 1.75 * banTrucNho || Math.min(moDay0, moDay1) < 0.22)) hopLe = false;
    tong += (r > 1e-6 ? Math.min(1, hChieu / (1.35 * r)) : Math.min(1, hChieu / h)) * Math.max(0, Math.min(1, Math.min(moDay0, moDay1) / 0.35));
  }
  return { hopLe, thuong: tong / capDayTru.length };
}

function diemTiepDienCau(
  huong: Diem3,
  matTiepDienCau: NonNullable<TuyChonHuongNhin["matTiepDienCau"]>,
): { hopLe: boolean; thuong: number } {
  if (matTiepDienCau.length === 0) return { hopLe: true, thuong: 0 };
  const d = chuan(huong);
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  let hopLe = Math.abs(d[0]) >= 0.30 && Math.abs(d[1]) >= 0.30;
  let tong = 0;
  for (const item of matTiepDienCau) {
    const R = Math.max(1e-6, item.banKinh);
    const u = chuan(item.phapTuyen);
    const ud = tich(u, d);
    const nd = Math.abs(ud);
    if (ud < 0.42 || ud > 0.58) {
      hopLe = false;
    }
    let diemItem =
      ud >= 0.42 && ud <= 0.58
        ? 1.4 - Math.abs(nd - 0.49) / 0.10
        : ud > 0.68 || ud < 0.18
          ? -2.2
          : -0.9;
    const dirs2d: [number, number][] = [];
    for (const pk of item.diemTrenMat) {
      const v = tru(pk, item.tamCau);
      const vd = tich(v, d);
      const r2 = Math.max(0, tich(v, v) - vd * vd);
      const rProj = Math.sqrt(r2);
      const tiLeR = rProj / R;
      if (tiLeR < 0.96) {
        hopLe = false;
      }
      const ap = tru(pk, item.tiepDiem);
      const apLen = Math.hypot(...ap);
      const dotCungPhia = apLen > 1e-6 ? (-ud * tich(ap, d)) / apLen : 0;
      const sx = tich(ap, phai);
      const sy = tich(ap, len);
      const sLen = Math.hypot(sx, sy);
      if (sLen > 1e-6) {
        dirs2d.push([sx / sLen, sy / sLen]);
      }
      if (tiLeR < 0.85) {
        diemItem -= 1.6;
      } else if (tiLeR >= 0.96) {
        diemItem += Math.min(1.1, (tiLeR - 0.94) * 2.2);
      }
      if (dotCungPhia >= 0) {
        diemItem += 0.45 * dotCungPhia;
      } else {
        diemItem += 0.25 * dotCungPhia;
      }
    }
    if (dirs2d.length >= 2) {
      const sinGoc = Math.abs(dirs2d[0][0] * dirs2d[1][1] - dirs2d[0][1] * dirs2d[1][0]);
      if (sinGoc < 0.65) {
        hopLe = false;
      }
      diemItem += 0.9 * sinGoc;
    }
    tong += diemItem;
  }
  return { hopLe, thuong: tong / matTiepDienCau.length };
}

/** Hướng nhìn tốt nhất trên lưới. Đạt ngưỡng trước; trong số đạt, cân diện
 *  tích, khoảng hở và độ sâu, trừ một chút cho việc xa hướng quen thuộc cũ để
 *  hình giữ tư thế sách giáo khoa. Không hướng nào đạt ⇒ hướng điểm cao nhất. */
export function chonHuongNhin(
  diem: Diem3[], canh: [number, number][], mat: number[][], tuyChon?: TuyChonHuongNhin,
): Diem3 {
  const quen = HUONG_SGK;
  const { cac, tran } = doLuoiGocNhin(diem, canh, mat);
  const matTrongTam = tuyChon?.matTrongTam ?? [];
  const capDayTru = tuyChon?.capDayTru ?? [];
  const matCap = tuyChon?.matCap ?? [];
  const coKhoiCong = Boolean(tuyChon?.coKhoiCong);
  const matTiepDienCau = tuyChon?.matTiepDienCau ?? [];
  const coTuyChon = matTrongTam.length > 0 || capDayTru.length > 0 || matCap.length > 0 || matTiepDienCau.length > 0;

  if (!coTuyChon) {
    let tot: { huong: Diem3; diem: number; dat: boolean } | null = null;
    for (const { huong, q } of cac) {
      const dat = datNguong(q, tran);
      const diemSo = q.dienTichBao / (tran.dienTichBao || 1) + 2 * Math.min(q.khoangDinhCanhMin, 0.2)
        + Math.min(q.khoangDinhMin, 0.38) + 0.5 * q.doSau / (tran.doSau || 1)
        - LUC_KEO_SGK * (1 - tich(huong, quen));
      if (!tot || (dat && !tot.dat) || (dat === tot.dat && diemSo > tot.diem)) {
        tot = { huong, diem: diemSo, dat };
      }
    }
    return tot ? tot.huong : quen;
  }

  const danhSach = cac.map(({ huong, q }) => {
    const d = chuan(huong);
    const camEst = uocLuongCameraPhoiCanh(diem, d);
    const mo = doMoMatTrongTam(huong, matTrongTam, coKhoiCong);
    const truInfo = diemTachDayTru(huong, camEst, capDayTru);
    const tiepDienInfo = diemTiepDienCau(huong, matTiepDienCau);
    const napMo = kiemMoPhoiCanhNapDaDien(camEst, matCap);
    const datKhongDetNap = truInfo.hopLe && napMo && tiepDienInfo.hopLe;
    const datCoBan = datNguong(q, tran) && datKhongDetNap;
    const datMo = (!mo.coMatDung || mo.minNghieng >= 0.55) && tiepDienInfo.hopLe;
    return { huong, q, mo, truInfo, tiepDienInfo, datKhongDetNap, datCoBan, datDayDu: datCoBan && datMo };
  });
  const coUngVienMo = danhSach.some((x) => x.datDayDu);
  const coUngVienCoBan = danhSach.some((x) => x.datCoBan);

  let tot: { huong: Diem3; diem: number; hang: number } | null = null;
  for (const item of danhSach) {
    const { huong, q, mo, truInfo, tiepDienInfo, datKhongDetNap, datCoBan, datDayDu } = item;
    const hang = coUngVienMo
      ? (datDayDu ? 3 : datCoBan ? 2 : datKhongDetNap ? 1 : 0)
      : coUngVienCoBan
        ? (datCoBan ? 2 : datKhongDetNap ? 1 : 0)
        : (datKhongDetNap ? 1 : 0);
    const lucKeo = mo.coMatDung || matTiepDienCau.length > 0 ? 0.55 : LUC_KEO_SGK;
    const diemSo = q.dienTichBao / (tran.dienTichBao || 1)
      + 2.2 * Math.min(q.khoangDinhCanhMin, 0.22)
      + Math.min(q.khoangDinhMin, 0.38)
      + 0.5 * q.doSau / (tran.doSau || 1)
      + (matTrongTam.length > 0 ? 2.6 * mo.tb : 0)
      + (capDayTru.length > 0 ? 0.45 * truInfo.thuong : 0)
      + (matTiepDienCau.length > 0 ? 2.4 * tiepDienInfo.thuong : 0)
      - lucKeo * (1 - tich(huong, quen));
    if (!tot || hang > tot.hang || (hang === tot.hang && diemSo > tot.diem)) {
      tot = { huong, diem: diemSo, hang };
    }
  }
  return tot ? tot.huong : quen;
}

/**
 * TỈ LỆ HÌNH CHIẾU cao/rộng của các điểm theo hướng `huong` (mobile-canvas-fit, D5) — cùng cơ sở phải/lên với
 * `khungNhinSuPham`. Phép chiếu song song: bỏ qua phối cảnh vài phần trăm, nằm trong lề của `TI_LE_LAP_KHUNG`.
 * `null` khi hình chiếu suy biến (ít hơn hai điểm, bề ngang 0).
 */
export function tiLeHinhChieu(diem: Diem3[], huong: Diem3): number | null {
  if (diem.length < 2) return null;
  const { uv } = chieu(diem, huong);
  const rong = Math.max(...uv.map((p) => p[0])) - Math.min(...uv.map((p) => p[0]));
  const cao = Math.max(...uv.map((p) => p[1])) - Math.min(...uv.map((p) => p[1]));
  return rong > 1e-9 && Number.isFinite(cao) ? cao / rong : null;
}

export interface TuyChonKhungNhinSuPham {
  /** Tỉ lệ lấp khung dọc mục tiêu (mặc định TI_LE_LAP_KHUNG = 0.78). */
  tiLeDoc?: number;
  /** Tỉ lệ lấp khung ngang mục tiêu (mặc định TI_LE_LAP_KHUNG = 0.78). */
  tiLeNgang?: number;
  /** Độ dịch tâm vùng an toàn theo phương ngang (tỉ lệ nửa chiều rộng khung, âm = dịch hình sang trái khi mở panel phải). */
  dichTamNgang?: number;
  /** Độ dịch tâm vùng an toàn theo phương dọc (tỉ lệ nửa chiều cao khung). */
  dichTamDoc?: number;
}

/** Khung nhìn: hướng sư phạm + khoảng cách vừa khít theo HÌNH CHIẾU THẬT của
 *  các điểm (không theo mặt cầu bao, vốn làm hình cao/hẹp chỉ choán một dải). */
export function khungNhinSuPham(
  diem: Diem3[], canh: [number, number][], mat: number[][], fovDo: number, tiLeKhung: number,
  huongCo?: Diem3,
  tuyChon?: TuyChonKhungNhinSuPham,
): KhungNhin | null {
  const hop = hopBaoCuaDiem(diem);
  const coBan = khungNhinVua(hop, fovDo, tiLeKhung);
  // Không có cạnh nào để đo (chỉ điểm, khối cong): giữ khung cũ đã được duyệt.
  if (!coBan || diem.length < 2 || (!huongCo && canh.length === 0)) return coBan;
  const d = chuan(huongCo ?? chonHuongNhin(diem, canh, mat));
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  const tanDoc = Math.tan((fovDo * Math.PI) / 360);
  const tanNgang = tanDoc * tiLeKhung;
  const tiLeDoc = Math.max(0.25, Math.min(0.9, tuyChon?.tiLeDoc ?? TI_LE_LAP_KHUNG));
  const tiLeNgang = Math.max(0.25, Math.min(0.9, tuyChon?.tiLeNgang ?? TI_LE_LAP_KHUNG));
  // Khoảng cách k nhỏ nhất để MỌI điểm lọt vào tiLeDoc/tiLeNgang của khung.
  const khoangVua = (tam: Diem3) => Math.max(KHOANG_TOI_THIEU, ...diem.map((p) => {
    const q = tru(p, tam);
    const s = tich(q, d);
    return Math.max(s + Math.abs(tich(q, phai)) / (tanNgang * tiLeNgang),
      s + Math.abs(tich(q, len)) / (tanDoc * tiLeDoc));
  }));
  // Rồi dời tâm nhìn về giữa hình chiếu thật: tâm hộp bao lệch khỏi tâm hình
  // chiếu, và phía lệch ấy phí mất một dải khung. Hai vòng là đủ hội tụ.
  let tam: Diem3 = [...coBan.nhinVao];
  for (let vong = 0; vong < 2; vong++) {
    const k = khoangVua(tam);
    const x = diem.map((p) => { const q = tru(p, tam); return tich(q, phai) / (k - tich(q, d)); });
    const y = diem.map((p) => { const q = tru(p, tam); return tich(q, len) / (k - tich(q, d)); });
    const [dx, dy] = [(Math.max(...x) + Math.min(...x)) / 2 * k, (Math.max(...y) + Math.min(...y)) / 2 * k];
    tam = [tam[0] + phai[0] * dx + len[0] * dy, tam[1] + phai[1] * dx + len[1] * dy,
      tam[2] + phai[2] * dx + len[2] * dy];
  }
  const k = khoangVua(tam);
  const dichNgang = (tuyChon?.dichTamNgang ?? 0) * tanNgang * k;
  const dichDoc = (tuyChon?.dichTamDoc ?? 0) * tanDoc * k;
  const tamCuoi: Diem3 = [
    tam[0] - phai[0] * dichNgang - len[0] * dichDoc,
    tam[1] - phai[1] * dichNgang - len[1] * dichDoc,
    tam[2] - phai[2] * dichNgang - len[2] * dichDoc,
  ];
  return { viTri: [tamCuoi[0] + d[0] * k, tamCuoi[1] + d[1] * k, tamCuoi[2] + d[2] * k], nhinVao: tamCuoi };
}

/**
 * HƯỚNG LÊN TRÌNH BÀY (regular-triangular-pyramid-w01) — pháp tuyến đơn vị của ĐÁY chóp, quay về phía ĐỈNH; `null` khi
 * đáy đã nằm ngang (|n_z| ≈ 1 — mọi họ đo trước: hình không đổi một điểm ảnh) hoặc đáy suy biến.
 *
 * Vì sao: đáy tam giác đều cạnh căn chỉ có toạ độ ℚ³ trên mặt NGHIÊNG x+y+z=k (amendment §18.2), nên hình chóp đúng
 * toán nằm nghiêng so với trục lên z của camera. View XOAY HIỂN THỊ (float) nhóm hình để pháp tuyến này về +z — không
 * đổi một toạ độ nào của cảnh, không đổi camera (z-up khoá ở `scene3d-zup-lifecycle.test.tsx`). Phép tính trình bày như
 * mọi hướng nhìn của module này; đáy và đỉnh do backend chỉ (`scene3d-model.dayVaDinhChop`).
 */
/**
 * KHUNG của ký hiệu góc vuông tại chân đường cao (regular-triangular-pyramid-w01): `d` dọc đoạn chân → đỉnh, `e1` là
 * trục x chiếu lên mặt ⊥ d (rơi về trục y khi d gần trục x), `e2 = d × e1`. Đoạn THẲNG ĐỨNG (mọi họ trước) cho đúng
 * x̂, ŷ, ẑ — ký hiệu không đổi một điểm ảnh; đáy nghiêng thì ký hiệu nằm theo đáy thay vì theo trục toạ độ.
 * `null` khi hai đầu trùng nhau.
 */
export function khungGocVuong(chan: Diem3, dinh: Diem3): { e1: Diem3; d: Diem3; e2: Diem3 } | null {
  const v = tru(dinh, chan);
  if (!(Math.hypot(...v) > 0)) return null;
  const d = chuan(v);
  const truc: Diem3 = Math.abs(d[0]) > 0.9 ? [0, 1, 0] : [1, 0, 0];
  const k = tich(truc, d);
  const e1 = chuan([truc[0] - k * d[0], truc[1] - k * d[1], truc[2] - k * d[2]]);
  return { e1, d, e2: cheo(d, e1) };
}

export function huongLenHienThi(day: Diem3[], dinh: Diem3): Diem3 | null {
  if (day.length < 3) return null;
  const n = cheo(tru(day[1], day[0]), tru(day[2], day[0]));
  if (!(Math.hypot(...n) > 0)) return null;
  const len = chuan(tich(tru(dinh, day[0]), n) < 0 ? [-n[0], -n[1], -n[2]] : n);
  return Math.abs(len[2]) > 1 - 1e-9 ? null : len;
}

export interface TamXoayOnDinh {
  tamXoay: Diem3;
  banKinhKhoi: number;
  diemKhoiChinh: Diem3[];
  /** The main (outer) solids the centre was taken from; their real surfaces bound the near zoom limit. */
  khoiChinh?: readonly LoaiKhoiTamXoay[];
}

export type LoaiKhoiTamXoay =
  | { loai: "solid"; vertices: readonly Diem3[]; faces: readonly number[][] }
  | {
      loai: "curved_solid";
      curvedKind: string;
      anchor: Diem3;
      radius: number;
      apexOrTop: Diem3;
      pts: readonly Diem3[];
    };

export interface VungAnToanNdc {
  xMin?: number;
  xMax?: number;
  yMin?: number;
  yMax?: number;
}

function trongTamTheTichDaDien(verts: readonly Diem3[], faces: readonly number[][]): { tam: Diem3; vol: number } {
  const n = verts.length;
  if (n === 0) return { tam: [0, 0, 0], vol: 0 };
  const v0: Diem3 = [
    verts.reduce((s, p) => s + p[0], 0) / n,
    verts.reduce((s, p) => s + p[1], 0) / n,
    verts.reduce((s, p) => s + p[2], 0) / n,
  ];
  let tongVol6 = 0;
  const tichLuy: Diem3 = [0, 0, 0];
  let tongDienTich2 = 0;
  const tichLuyMat: Diem3 = [0, 0, 0];

  for (const f of faces) {
    if (f.length < 3) continue;
    const a = verts[f[0]];
    if (!a) continue;
    for (let i = 1; i < f.length - 1; i++) {
      const b = verts[f[i]];
      const c = verts[f[i + 1]];
      if (!b || !c) continue;
      const crMat = cheo(tru(b, a), tru(c, a));
      const dt2 = Math.hypot(...crMat);
      if (dt2 > 1e-12) {
        tongDienTich2 += dt2;
        tichLuyMat[0] += (dt2 * (a[0] + b[0] + c[0])) / 3;
        tichLuyMat[1] += (dt2 * (a[1] + b[1] + c[1])) / 3;
        tichLuyMat[2] += (dt2 * (a[2] + b[2] + c[2])) / 3;
      }
      const cr = cheo(tru(b, v0), tru(c, v0));
      const vol6 = Math.abs(tich(tru(a, v0), cr));
      if (vol6 > 1e-12) {
        tongVol6 += vol6;
        tichLuy[0] += vol6 * 0.25 * (v0[0] + a[0] + b[0] + c[0]);
        tichLuy[1] += vol6 * 0.25 * (v0[1] + a[1] + b[1] + c[1]);
        tichLuy[2] += vol6 * 0.25 * (v0[2] + a[2] + b[2] + c[2]);
      }
    }
  }
  if (tongVol6 > 1e-12) {
    return {
      tam: [tichLuy[0] / tongVol6, tichLuy[1] / tongVol6, tichLuy[2] / tongVol6],
      vol: tongVol6 / 6,
    };
  }
  if (tongDienTich2 > 1e-12) {
    return {
      tam: [tichLuyMat[0] / tongDienTich2, tichLuyMat[1] / tongDienTich2, tichLuyMat[2] / tongDienTich2],
      vol: 0,
    };
  }
  return { tam: v0, vol: 0 };
}

function hopBaoChuaHopBao(lon: HopBao, nho: HopBao, eps = 1e-4): boolean {
  return (
    lon.min[0] - eps <= nho.min[0] && nho.max[0] <= lon.max[0] + eps &&
    lon.min[1] - eps <= nho.min[1] && nho.max[1] <= lon.max[1] + eps &&
    lon.min[2] - eps <= nho.min[2] && nho.max[2] <= lon.max[2] + eps
  );
}

/**
 * Tính tâm xoay quỹ đạo ổn định (`OrbitControls.target`) từ dữ liệu số thuần của các khối hình học:
 * - Ưu tiên khối chính (`solid`, `curved_solid`), loại trừ khối con nằm trọn bên trong khối bao lớn hơn
 *   (ví dụ chóp con tỉ số thể tích, nón cụt phần trên, mặt cầu nội tiếp) để không kéo lệch trục đối xứng.
 * - Kết hợp cân bằng 50/50 giữa trọng tâm thể tích `G_vol` và tâm hộp bao khối chính `C_aabb`:
 *   giữ nguyên trục đối xứng trên chóp đều/lăng trụ/trụ/nón/cầu, đồng thời tách hẳn khỏi các điểm trung gian
 *   như `P, M, N` trên chóp cạnh bên vuông góc đáy (`S.ABCD`).
 * - Bất biến qua mọi bước dựng (chỉ đọc dữ liệu hình học hợp lệ, không làm lộ vật chưa xuất hiện trên canvas).
 * - Khi bài không có khối đặc, fallback về trung bình khử trùng + tâm hộp bao của các đối tượng hữu hạn
 *   (bỏ qua đường thẳng vô hạn và mặt phẳng mở rộng).
 */
export function tinhTamXoayTuKhoi(
  dsKhoiDauVao: readonly LoaiKhoiTamXoay[],
  diemDuPhong: readonly Diem3[],
): TamXoayOnDinh | null {
  const dsKhoi: { pts: Diem3[]; hop: HopBao; tamVol: Diem3; vol: number; nguon: LoaiKhoiTamXoay }[] = [];

  for (const k of dsKhoiDauVao) {
    if (k.loai === "solid" && k.vertices.length > 0) {
      const verts: Diem3[] = k.vertices.map((v) => [v[0], v[1], v[2]]);
      const hop = hopBaoCuaDiem(verts);
      if (!hop) continue;
      const { tam, vol } = trongTamTheTichDaDien(verts, k.faces);
      dsKhoi.push({ pts: verts, hop, tamVol: tam, vol: Math.max(vol, 1e-6), nguon: k });
    } else if (k.loai === "curved_solid" && Number.isFinite(k.radius) && k.radius > 0) {
      const pts: Diem3[] = k.pts.map((p) => [p[0], p[1], p[2]]);
      const hop = hopBaoCuaDiem(pts);
      if (!hop) continue;
      const r = k.radius;
      const c = k.anchor;
      const dinh = k.apexOrTop;
      const chieuCao = Math.hypot(dinh[0] - c[0], dinh[1] - c[1], dinh[2] - c[2]);
      let tamVol: Diem3 = [c[0], c[1], c[2]];
      let vol = (4 / 3) * Math.PI * r * r * r;
      if (k.curvedKind === "cylinder") {
        tamVol = [(c[0] + dinh[0]) * 0.5, (c[1] + dinh[1]) * 0.5, (c[2] + dinh[2]) * 0.5];
        vol = Math.PI * r * r * Math.max(chieuCao, 1e-6);
      } else if (k.curvedKind === "cone") {
        tamVol = [
          0.75 * c[0] + 0.25 * dinh[0],
          0.75 * c[1] + 0.25 * dinh[1],
          0.75 * c[2] + 0.25 * dinh[2],
        ];
        vol = (1 / 3) * Math.PI * r * r * Math.max(chieuCao, 1e-6);
      }
      dsKhoi.push({ pts, hop, tamVol, vol: Math.max(vol, 1e-6), nguon: k });
    }
  }

  if (dsKhoi.length > 0) {
    const khoiNgoai = dsKhoi.filter(
      (nho, idx) =>
        !dsKhoi.some(
          (lon, jdx) =>
            jdx !== idx &&
            lon.vol > nho.vol * (1 + 1e-4) &&
            hopBaoChuaHopBao(lon.hop, nho.hop),
        ),
    );
    const chon = khoiNgoai.length > 0 ? khoiNgoai : dsKhoi;
    const diemKhoiChinh = chon.flatMap((k) => k.pts);
    const hopChung = hopBaoCuaDiem(diemKhoiChinh);
    if (hopChung) {
      const tongVol = chon.reduce((s, k) => s + k.vol, 0) || 1;
      const gVol: Diem3 = [
        chon.reduce((s, k) => s + k.vol * k.tamVol[0], 0) / tongVol,
        chon.reduce((s, k) => s + k.vol * k.tamVol[1], 0) / tongVol,
        chon.reduce((s, k) => s + k.vol * k.tamVol[2], 0) / tongVol,
      ];
      const cAabb: Diem3 = [
        (hopChung.min[0] + hopChung.max[0]) * 0.5,
        (hopChung.min[1] + hopChung.max[1]) * 0.5,
        (hopChung.min[2] + hopChung.max[2]) * 0.5,
      ];
      const tamXoay: Diem3 = [
        (gVol[0] + cAabb[0]) * 0.5,
        (gVol[1] + cAabb[1]) * 0.5,
        (gVol[2] + cAabb[2]) * 0.5,
      ];
      const banKinhKhoi = Math.max(
        0.25,
        ...diemKhoiChinh.map((p) => Math.hypot(p[0] - tamXoay[0], p[1] - tamXoay[1], p[2] - tamXoay[2])),
      );
      return { tamXoay, banKinhKhoi, diemKhoiChinh, khoiChinh: chon.map((k) => k.nguon) };
    }
  }

  // Chiến lược dự phòng cho bài không có solid: chỉ lấy đối tượng hữu hạn hợp lệ (bỏ line3 / plane3 vô hạn).
  const huuHan: Diem3[] = diemDuPhong.filter((pm) => pm.every(Number.isFinite)).map((pm) => [pm[0], pm[1], pm[2]]);
  const hopDuPhong = hopBaoCuaDiem(huuHan);
  if (!hopDuPhong) return null;
  const duyNhat: Diem3[] = [];
  for (const p of huuHan) {
    if (!duyNhat.some((q) => Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]) < 1e-6)) {
      duyNhat.push(p);
    }
  }
  const tb: Diem3 = [
    duyNhat.reduce((s, p) => s + p[0], 0) / duyNhat.length,
    duyNhat.reduce((s, p) => s + p[1], 0) / duyNhat.length,
    duyNhat.reduce((s, p) => s + p[2], 0) / duyNhat.length,
  ];
  const cAabb: Diem3 = [
    (hopDuPhong.min[0] + hopDuPhong.max[0]) * 0.5,
    (hopDuPhong.min[1] + hopDuPhong.max[1]) * 0.5,
    (hopDuPhong.min[2] + hopDuPhong.max[2]) * 0.5,
  ];
  const tamXoay: Diem3 = [
    (tb[0] + cAabb[0]) * 0.5,
    (tb[1] + cAabb[1]) * 0.5,
    (tb[2] + cAabb[2]) * 0.5,
  ];
  const banKinhKhoi = Math.max(
    0.25,
    ...duyNhat.map((p) => Math.hypot(p[0] - tamXoay[0], p[1] - tamXoay[1], p[2] - tamXoay[2])),
  );
  return { tamXoay, banKinhKhoi, diemKhoiChinh: duyNhat };
}

/**
 * Khoảng TỰA của khối chính theo hướng nhìn `huong` (từ tâm xoay về phía camera): max⟨p − tâm, u⟩ trên mặt THẬT của khối
 * — đỉnh đa diện; cầu c·u + r; trụ/nón: đĩa đáy/đỉnh c·u + r·√(1 − (n·u)²) (và đỉnh nón). Đây là chỗ mặt gần camera nhất
 * thực sự nằm; cầu bao chỉ là cận trên (với khối cong nó TRÙNG mặt, nên không dùng được để giữ khoảng cách).
 */
export function khoangTuaTheoHuong(info: TamXoayOnDinh, huong: Diem3): number {
  const len = Math.hypot(huong[0], huong[1], huong[2]);
  if (!(len > 0)) return info.banKinhKhoi;
  const u: Diem3 = [huong[0] / len, huong[1] / len, huong[2] / len];
  const t = info.tamXoay;
  const chieu = (p: readonly number[]) => (p[0] - t[0]) * u[0] + (p[1] - t[1]) * u[1] + (p[2] - t[2]) * u[2];
  let tua = Math.max(0, ...info.diemKhoiChinh.map(chieu));
  for (const k of info.khoiChinh ?? []) {
    if (k.loai === "solid") {
      for (const v of k.vertices) tua = Math.max(tua, chieu(v));
      continue;
    }
    const truc: Diem3 = [k.apexOrTop[0] - k.anchor[0], k.apexOrTop[1] - k.anchor[1], k.apexOrTop[2] - k.anchor[2]];
    const h = Math.hypot(...truc);
    if ((k.curvedKind === "cylinder" || k.curvedKind === "cone") && h > 0) {
      const nu = (truc[0] * u[0] + truc[1] * u[1] + truc[2] * u[2]) / h;
      const vanh = k.radius * Math.sqrt(Math.max(0, 1 - nu * nu));
      tua = Math.max(tua, chieu(k.anchor) + vanh, chieu(k.apexOrTop) + (k.curvedKind === "cylinder" ? vanh : 0));
    } else {
      tua = Math.max(tua, chieu(k.anchor) + k.radius);
    }
  }
  return tua;
}

/** Mặt gần nhất của khối chính không bao giờ quá NỬA đường từ camera tới tâm xoay. */
export const HE_SO_KHOANG_GAN_MAT = 2;

/**
 * Giới hạn zoom gần (`OrbitControls.minDistance`) theo hướng nhìn hiện tại. Giữ luật cũ (theo khung vừa và cầu bao) làm
 * sàn, nâng lên `HE_SO_KHOANG_GAN_MAT × khoảng tựa` để camera không áp sát mặt thật của khối (cầu/trụ/nón), và chặn trên ở
 * 0.8 khoảng khung vừa để luôn còn cận cảnh. Không đổi hình học — chỉ khoảng cách camera.
 */
export function khoangGanToiThieu(info: TamXoayOnDinh | null | undefined, huong: Diem3, khoangKhung: number): number {
  const r = info?.banKinhKhoi;
  if (!info || !(typeof r === "number" && Number.isFinite(r) && r > 1e-4)) return Math.max(0.8, khoangKhung * 0.42);
  const cu = Math.max(0.5, Math.min(khoangKhung * 0.55, r * 1.08));
  return Math.min(Math.max(cu, HE_SO_KHOANG_GAN_MAT * khoangTuaTheoHuong(info, huong)), Math.max(cu, khoangKhung * 0.8));
}

/**
 * Đặt vị trí camera dọc theo hướng nhìn đi qua ĐÚNG `tamXoay` cố định sao cho mọi điểm hữu hạn `diem`
 * đều nằm gọn trong vùng an toàn NDC `[xMin, xMax] × [yMin, yMax]`, tuyệt đối không dịch chuyển `nhinVao`
 * khỏi tâm xoay chuẩn của khối hình học chính.
 */
export function khungNhinQuanhTam(
  diem: readonly Diem3[],
  tamXoay: Diem3,
  fovDo: number,
  tiLeKhung: number,
  huongChon?: Diem3,
  vungAnToanNdc?: VungAnToanNdc,
): KhungNhin | null {
  if (
    diem.length === 0 ||
    !tamXoay.every(Number.isFinite) ||
    !Number.isFinite(fovDo) || fovDo <= 0 || fovDo >= 180 ||
    !Number.isFinite(tiLeKhung) || tiLeKhung <= 0
  ) {
    return null;
  }
  const d = chuan(
    huongChon && huongChon.every(Number.isFinite) && Math.hypot(...huongChon) > 1e-9
      ? huongChon
      : ([...HUONG] as Diem3),
  );
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  const tanDoc = Math.tan((fovDo * Math.PI) / 360);
  const tanNgang = tanDoc * tiLeKhung;
  if (!(tanDoc > 0) || !(tanNgang > 0)) return null;

  const xMin = Math.max(-0.92, Math.min(-0.15, vungAnToanNdc?.xMin ?? -TI_LE_LAP_KHUNG));
  const xMax = Math.min(0.92, Math.max(0.15, vungAnToanNdc?.xMax ?? TI_LE_LAP_KHUNG));
  const yMin = Math.max(-0.92, Math.min(-0.15, vungAnToanNdc?.yMin ?? -TI_LE_LAP_KHUNG));
  const yMax = Math.min(0.92, Math.max(0.15, vungAnToanNdc?.yMax ?? TI_LE_LAP_KHUNG));

  let k = KHOANG_TOI_THIEU;
  for (const p of diem) {
    if (!p.every(Number.isFinite)) continue;
    const q = tru(p, tamXoay);
    const s = tich(q, d);
    const rx = tich(q, phai);
    const ry = tich(q, len);
    const kx = rx >= 0 ? rx / (xMax * tanNgang) : (-rx) / (-xMin * tanNgang);
    const ky = ry >= 0 ? ry / (yMax * tanDoc) : (-ry) / (-yMin * tanDoc);
    k = Math.max(k, s + Math.max(0.25, kx, ky));
  }

  return {
    viTri: [tamXoay[0] + d[0] * k, tamXoay[1] + d[1] * k, tamXoay[2] + d[2] * k],
    nhinVao: [tamXoay[0], tamXoay[1], tamXoay[2]],
  };
}

export interface TuyChonCanDoiTam {
  tiLeNgang: number;
  tiLeDoc: number;
  dichTamNgang?: number;
  dichTamDoc?: number;
  bienDichTamToiDa?: { ngang?: number; doc?: number };
}

export interface KetQuaCanDoiTam {
  vungAnToanNdc: VungAnToanNdc;
  lechOngKinhNgang: number;
  lechOngKinhDoc: number;
}

/**
 * Cân đối vùng an toàn NDC và độ lệch tâm quang học (`setViewOffset`) quanh `tamXoay` cố định:
 * - Giữ nguyên tuyệt đối `controls.target === tamXoay` để xoay Orbit 90°/180°/360° quanh đúng tâm khối.
 * - Khi hình chiếu bất đối xứng quanh `tamXoay` (vd: đỉnh chóp S hoặc điểm trên mặt tiếp diện cao hơn phần đáy),
 *   phân bổ dải NDC `2 × tiLeDoc` / `2 × tiLeNgang` theo tỷ lệ nhô hai phía có chặn biên an toàn, đồng thời
 *   dịch nhẹ tâm quang học ngược dấu để hình vừa cân giữa vùng khả dụng vừa đạt kích thước mục tiêu (~55–65% cao, ≤70% rộng/cao).
 */
export function khungAnToanCanDoiTam(
  diem: readonly Diem3[],
  tamXoay: Diem3,
  fovDo: number,
  tiLeKhung: number,
  huongChon: Diem3 | undefined,
  tuyChon: TuyChonCanDoiTam,
): KetQuaCanDoiTam {
  const tiLeNgang = Math.max(0.20, Math.min(0.86, Number.isFinite(tuyChon.tiLeNgang) ? tuyChon.tiLeNgang : TI_LE_LAP_KHUNG));
  const tiLeDoc = Math.max(0.20, Math.min(0.84, Number.isFinite(tuyChon.tiLeDoc) ? tuyChon.tiLeDoc : TI_LE_LAP_KHUNG));
  const uiNgang = Number.isFinite(tuyChon.dichTamNgang) ? (tuyChon.dichTamNgang as number) : 0;
  const uiDoc = Number.isFinite(tuyChon.dichTamDoc) ? (tuyChon.dichTamDoc as number) : 0;
  const fallback = (): KetQuaCanDoiTam => ({
    vungAnToanNdc: {
      xMin: -tiLeNgang,
      xMax: tiLeNgang,
      yMin: -tiLeDoc,
      yMax: tiLeDoc,
    },
    lechOngKinhNgang: uiNgang,
    lechOngKinhDoc: uiDoc,
  });

  const diemHopLe = diem.filter((p) => p.every(Number.isFinite));
  if (
    diemHopLe.length === 0 ||
    !tamXoay.every(Number.isFinite) ||
    !Number.isFinite(fovDo) || fovDo <= 0 || fovDo >= 180 ||
    !Number.isFinite(tiLeKhung) || tiLeKhung <= 0
  ) {
    return fallback();
  }

  const d = chuan(
    huongChon && huongChon.every(Number.isFinite) && Math.hypot(...huongChon) > 1e-9
      ? huongChon
      : ([...HUONG] as Diem3),
  );
  const knSym = khungNhinQuanhTam(diemHopLe, tamXoay, fovDo, tiLeKhung, d, {
    xMin: -tiLeNgang,
    xMax: tiLeNgang,
    yMin: -tiLeDoc,
    yMax: tiLeDoc,
  });
  if (!knSym) return fallback();

  const kSym = Math.hypot(
    knSym.viTri[0] - tamXoay[0],
    knSym.viTri[1] - tamXoay[1],
    knSym.viTri[2] - tamXoay[2],
  );
  const tanDoc = Math.tan((fovDo * Math.PI) / 360);
  const tanNgang = tanDoc * tiLeKhung;
  if (!(kSym > 1e-6) || !(tanDoc > 0) || !(tanNgang > 0)) return fallback();

  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);

  let uxMin = 0;
  let uxMax = 0;
  let uyMin = 0;
  let uyMax = 0;
  for (const p of diemHopLe) {
    const q = tru(p, tamXoay);
    const depth = Math.max(0.25, kSym - tich(q, d));
    const ux = tich(q, phai) / (depth * tanNgang);
    const uy = tich(q, len) / (depth * tanDoc);
    if (ux < uxMin) uxMin = ux;
    if (ux > uxMax) uxMax = ux;
    if (uy < uyMin) uyMin = uy;
    if (uy > uyMax) uyMax = uy;
  }

  const maxAsymX = Math.max(0, Math.min(0.16, tuyChon.bienDichTamToiDa?.ngang ?? 0.08));
  const maxAsymY = Math.max(0, Math.min(0.18, tuyChon.bienDichTamToiDa?.doc ?? 0.10));
  const spanX = Math.max(1e-4, uxMax - uxMin);
  const spanY = Math.max(1e-4, uyMax - uyMin);
  const rawCx = 0.5 * (uxMax + uxMin) * Math.min(1.5, (2 * tiLeNgang) / spanX);
  const rawCy = 0.5 * (uyMax + uyMin) * Math.min(1.5, (2 * tiLeDoc) / spanY);
  const cX = Math.max(-maxAsymX, Math.min(maxAsymX, rawCx));
  const cY = Math.max(-maxAsymY, Math.min(maxAsymY, rawCy));

  return {
    vungAnToanNdc: {
      xMin: Math.max(-0.88, Math.min(-0.18, -tiLeNgang + cX)),
      xMax: Math.min(0.88, Math.max(0.18, tiLeNgang + cX)),
      yMin: Math.max(-0.86, Math.min(-0.18, -tiLeDoc + cY)),
      yMax: Math.min(0.86, Math.max(0.18, tiLeDoc + cY)),
    },
    lechOngKinhNgang: uiNgang - cX,
    lechOngKinhDoc: uiDoc - cY,
  };
}

// ─── ĐỊNH VỊ ĐỐI TƯỢNG THÔNG MINH (SMART OBJECT LOCATE — AXO V9.4.17) ─────────

export type LocateObjectKind =
  | "point"
  | "segment"
  | "plane"
  | "section"
  | "solid"
  | "curved_surface";

export interface OccluderTriangleMesh {
  objectId: string;
  vertices: readonly Diem3[];
  triangles: readonly [number, number, number][];
  isSolidFace?: boolean;
}

export interface OccluderSphereMesh {
  objectId: string;
  center: Diem3;
  radius: number;
}

export interface SmartLocateInput {
  objectId: string;
  objectKind: LocateObjectKind;
  objectPoints: readonly Diem3[];
  objectNormal?: Diem3 | null;
  contextPoints: readonly Diem3[];
  stableCenter?: TamXoayOnDinh | null;
  currentPosition: Diem3;
  currentTarget: Diem3;
  fovDeg: number;
  aspect: number;
  occluderMeshes?: readonly OccluderTriangleMesh[];
  occluderSpheres?: readonly OccluderSphereMesh[];
  objectCenter?: Diem3;
  isInteriorOrTangent?: boolean;
}

export type SmartLocateStatus =
  | "located"
  | "unchanged"
  | "fallback_unchanged";

export interface SmartLocateResult {
  status: SmartLocateStatus;
  position: Diem3;
  target: Diem3;
  viewDirection: Diem3;
  distance: number;
  targetNdc: [number, number];
  normalAlignment: number | null;
  segmentForeshorteningCos: number | null;
  occludedRatio: number;
  minMarginToHostMesh: number;
  reason: string;
  message?: string;
}

function add3(a: Diem3, b: Diem3): Diem3 {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}

function scale3(v: Diem3, s: number): Diem3 {
  return [v[0] * s, v[1] * s, v[2] * s];
}

function lerp3(a: Diem3, b: Diem3, t: number): Diem3 {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
}

function distPt(a: Diem3, b: Diem3): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}

function meanPt(pts: readonly Diem3[]): Diem3 | null {
  if (pts.length === 0) return null;
  let sx = 0, sy = 0, sz = 0, cnt = 0;
  for (const p of pts) {
    if (!p.every(Number.isFinite)) continue;
    sx += p[0]; sy += p[1]; sz += p[2]; cnt += 1;
  }
  return cnt > 0 ? [sx / cnt, sy / cnt, sz / cnt] : null;
}

function pointToTriangleDist(p: Diem3, a: Diem3, b: Diem3, c: Diem3): number {
  const ab = tru(b, a), ac = tru(c, a), ap = tru(p, a);
  const d1 = tich(ab, ap), d2 = tich(ac, ap);
  if (d1 <= 0 && d2 <= 0) return distPt(p, a);
  const bp = tru(p, b);
  const d3 = tich(ab, bp), d4 = tich(ac, bp);
  if (d3 >= 0 && d4 <= d3) return distPt(p, b);
  const vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) {
    const v = d1 / (d1 - d3);
    return distPt(p, add3(a, scale3(ab, v)));
  }
  const cp = tru(p, c);
  const d5 = tich(ab, cp), d6 = tich(ac, cp);
  if (d6 >= 0 && d5 <= d6) return distPt(p, c);
  const vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) {
    const w = d2 / (d2 - d6);
    return distPt(p, add3(a, scale3(ac, w)));
  }
  const va = d3 * d6 - d5 * d4;
  if (va <= 0 && (d4 - d3) >= 0 && (d5 - d6) >= 0) {
    const w = (d4 - d3) / ((d4 - d3) + (d5 - d6));
    return distPt(p, add3(b, scale3(tru(c, b), w)));
  }
  const denom = 1 / Math.max(1e-18, va + vb + vc);
  const v = vb * denom, w = vc * denom;
  const closest = add3(a, add3(scale3(ab, v), scale3(ac, w)));
  return distPt(p, closest);
}

function rayIntersectsTriangleParam(
  orig: Diem3,
  dir: Diem3,
  maxDist: number,
  a: Diem3,
  b: Diem3,
  c: Diem3,
): number | null {
  const e1 = tru(b, a), e2 = tru(c, a);
  const pvec = cheo(dir, e2);
  const det = tich(e1, pvec);
  if (Math.abs(det) < 1e-10) return null;
  const invDet = 1 / det;
  const tvec = tru(orig, a);
  const u = tich(tvec, pvec) * invDet;
  if (u < -1e-4 || u > 1 + 1e-4) return null;
  const qvec = cheo(tvec, e1);
  const v = tich(dir, qvec) * invDet;
  if (v < -1e-4 || u + v > 1 + 1e-4) return null;
  const t = tich(e2, qvec) * invDet;
  if (t <= 1e-5 * maxDist || t >= maxDist * (1 - 1.5e-3)) return null;
  return t;
}

function rayIntersectsSphereParam(
  orig: Diem3,
  dir: Diem3,
  maxDist: number,
  center: Diem3,
  radius: number,
): number | null {
  const oc = tru(orig, center);
  const b = tich(oc, dir);
  const c = tich(oc, oc) - radius * radius;
  const disc = b * b - c;
  if (disc <= 0) return null;
  const sqrtD = Math.sqrt(disc);
  const t1 = -b - sqrtD;
  if (t1 > 1e-5 * maxDist && t1 < maxDist * (1 - 1.5e-3)) return t1;
  const t2 = -b + sqrtD;
  if (t2 > 1e-5 * maxDist && t2 < maxDist * (1 - 1.5e-3)) return t2;
  return null;
}

function projectToNdc(
  pt: Diem3,
  camPos: Diem3,
  camTarget: Diem3,
  fovDeg: number,
  aspect: number,
): [number, number] | null {
  const fwd = tru(camPos, camTarget);
  const dist = Math.hypot(fwd[0], fwd[1], fwd[2]);
  if (!(dist > 1e-9)) return null;
  const d: Diem3 = [fwd[0] / dist, fwd[1] / dist, fwd[2] / dist];
  const phai = chuan(Math.abs(d[2]) > 0.999 ? cheo([0, 1, 0], d) : cheo([0, 0, 1], d));
  const len = cheo(d, phai);
  const rel = tru(pt, camTarget);
  const depth = dist - tich(rel, d);
  if (!(depth > 1e-6)) return null;
  const tanDoc = Math.tan((fovDeg * Math.PI) / 360);
  const tanNgang = tanDoc * aspect;
  if (!(tanDoc > 0) || !(tanNgang > 0)) return null;
  return [
    tich(rel, phai) / (depth * tanNgang),
    tich(rel, len) / (depth * tanDoc),
  ];
}

function computeOccludedRatioForView(
  camPos: Diem3,
  samplePts: readonly Diem3[],
  objectId: string,
  objectKind: LocateObjectKind,
  meshes: readonly OccluderTriangleMesh[],
  spheres: readonly OccluderSphereMesh[],
): number {
  if (samplePts.length === 0 || (meshes.length === 0 && spheres.length === 0)) return 0;
  let occluded = 0;
  for (const pt of samplePts) {
    const toPt = tru(pt, camPos);
    const rayLen = Math.hypot(toPt[0], toPt[1], toPt[2]);
    if (!(rayLen > 1e-9)) continue;
    const dir: Diem3 = [toPt[0] / rayLen, toPt[1] / rayLen, toPt[2] / rayLen];
    let hit = false;
    for (const sph of spheres) {
      if (sph.objectId === objectId && objectKind === "curved_surface") continue;
      if (rayIntersectsSphereParam(camPos, dir, rayLen, sph.center, sph.radius) !== null) {
        hit = true;
        break;
      }
    }
    if (!hit) {
      for (const m of meshes) {
        if (m.objectId === objectId && (objectKind === "solid" || objectKind === "section" || objectKind === "plane")) {
          continue;
        }
        for (const [ia, ib, ic] of m.triangles) {
          const va = m.vertices[ia], vb = m.vertices[ib], vc = m.vertices[ic];
          if (!va || !vb || !vc) continue;
          if (rayIntersectsTriangleParam(camPos, dir, rayLen, va, vb, vc) !== null) {
            hit = true;
            break;
          }
        }
        if (hit) break;
      }
    }
    if (hit) occluded += 1;
  }
  return occluded / samplePts.length;
}

function minClearanceToMeshes(
  camPos: Diem3,
  meshes: readonly OccluderTriangleMesh[],
  spheres: readonly OccluderSphereMesh[],
): number {
  let minDist = Infinity;
  for (const sph of spheres) {
    const d = distPt(camPos, sph.center) - sph.radius;
    if (d < minDist) minDist = d;
  }
  for (const m of meshes) {
    for (const [ia, ib, ic] of m.triangles) {
      const va = m.vertices[ia], vb = m.vertices[ib], vc = m.vertices[ic];
      if (!va || !vb || !vc) continue;
      const d = pointToTriangleDist(camPos, va, vb, vc);
      if (d < minDist) minDist = d;
    }
  }
  return minDist;
}

/**
 * Bộ giải vị trí camera sư phạm cho nút "Định vị":
 * - Bảo toàn ngữ cảnh khối chủ trong khung nhìn (không zoom mù vào 1 điểm cô lập).
 * - Mặt phẳng / thiết diện: tránh góc liếc cạnh (`|u · n̂| >= 0.42`).
 * - Đoạn thẳng / cạnh: tránh nhìn dọc trục (`|u · d̂| <= 0.82`).
 * - Điểm nằm trong / tiếp xúc khối: chọn hướng trong ~72 hướng ít bị che khuất nhất mà vẫn giữ camera ngoài vỏ khối.
 */
export function computeSmartLocateCamera(input: SmartLocateInput): SmartLocateResult {
  const {
    objectId,
    objectKind,
    objectPoints,
    objectNormal,
    contextPoints,
    stableCenter,
    currentPosition,
    currentTarget,
    fovDeg,
    aspect,
    occluderMeshes = [],
    occluderSpheres = [],
    objectCenter: explicitCenter,
    isInteriorOrTangent = false,
  } = input;

  const fallback = (reason: string, message: string): SmartLocateResult => {
    const curDir = tru(currentPosition, currentTarget);
    const curLen = Math.hypot(curDir[0], curDir[1], curDir[2]);
    const uCur: Diem3 = curLen > 1e-9 ? [curDir[0] / curLen, curDir[1] / curLen, curDir[2] / curLen] : chuan([...HUONG_SGK]);
    return {
      status: "fallback_unchanged",
      position: [...currentPosition],
      target: [...currentTarget],
      viewDirection: uCur,
      distance: curLen,
      targetNdc: [0, 0],
      normalAlignment: null,
      segmentForeshorteningCos: null,
      occludedRatio: 0,
      minMarginToHostMesh: minClearanceToMeshes(currentPosition, occluderMeshes, occluderSpheres),
      reason,
      message,
    };
  };

  const validObjPts = objectPoints.filter((p) => p.every(Number.isFinite));
  const validCtxPts = contextPoints.filter((p) => p.every(Number.isFinite));
  const objCenter =
    explicitCenter && explicitCenter.every(Number.isFinite)
      ? explicitCenter
      : meanPt(validObjPts);

  if (
    !objCenter
    || validObjPts.length === 0
    || !currentPosition.every(Number.isFinite)
    || !currentTarget.every(Number.isFinite)
    || !Number.isFinite(fovDeg) || fovDeg <= 0 || fovDeg >= 180
    || !Number.isFinite(aspect) || aspect <= 0
  ) {
    return fallback("missing_or_non_finite_coordinates", "Đối tượng chưa có tọa độ hữu hạn để định vị.");
  }

  const allScenePts = validCtxPts.length > 0 ? [...validCtxPts, ...validObjPts] : [...validObjPts];
  const hostBox = hopBaoCuaDiem([...allScenePts]);
  const hostDiam = hostBox
    ? Math.hypot(
        hostBox.max[0] - hostBox.min[0],
        hostBox.max[1] - hostBox.min[1],
        hostBox.max[2] - hostBox.min[2],
      )
    : 1;
  const sceneScale = Math.max(hostDiam, 1e-4);
  const hostCenter: Diem3 =
    stableCenter && stableCenter.tamXoay.every(Number.isFinite)
      ? stableCenter.tamXoay
      : (meanPt(validCtxPts) ?? objCenter);

  const nHat: Diem3 | null =
    objectNormal && objectNormal.every(Number.isFinite) && Math.hypot(...objectNormal) > 1e-9
      ? chuan(objectNormal)
      : null;

  let segDir: Diem3 | null = null;
  if (objectKind === "segment" && validObjPts.length >= 2) {
    const d = tru(validObjPts[1], validObjPts[0]);
    if (Math.hypot(...d) > 1e-9) segDir = chuan(d);
  }

  const objDistFromHost = distPt(objCenter, hostCenter);
  const hasHostSpan = validCtxPts.length >= 4 && objDistFromHost > 0.15 * sceneScale;
  const contextBlend =
    objectKind === "solid" || objectKind === "curved_surface"
      ? 1.0
      : objectKind === "point"
        ? (hasHostSpan ? 0.45 : 0.34)
        : objectKind === "segment"
          ? (hasHostSpan ? 0.48 : 0.28)
          : (hasHostSpan ? 0.32 : 0.26);
  const desiredTarget = lerp3(objCenter, hostCenter, validCtxPts.length > 0 ? contextBlend : 0);

  const curOffset = tru(currentPosition, currentTarget);
  const curDist = Math.hypot(curOffset[0], curOffset[1], curOffset[2]);
  const uCur: Diem3 =
    curDist > 1e-9
      ? [curOffset[0] / curDist, curOffset[1] / curDist, curOffset[2] / curDist]
      : chuan([...HUONG_SGK]);

  // Chuẩn bị lưới điểm kiểm chứng che khuất & căn khung
  const samplePtsForOcclusion: Diem3[] = validObjPts.length <= 6
    ? [...validObjPts, ...(validObjPts.length > 1 ? [objCenter] : [])]
    : [objCenter, validObjPts[0], validObjPts[Math.floor(validObjPts.length / 3)], validObjPts[Math.floor((2 * validObjPts.length) / 3)]];

  const hostFaceNormals: Diem3[] = [];
  for (const m of occluderMeshes) {
    if (!m.isSolidFace) continue;
    for (const [ia, ib, ic] of m.triangles) {
      const va = m.vertices[ia], vb = m.vertices[ib], vc = m.vertices[ic];
      if (!va || !vb || !vc) continue;
      const n = cheo(tru(vb, va), tru(vc, va));
      const nLen = Math.hypot(n[0], n[1], n[2]);
      if (!(nLen > 1e-9)) continue;
      const nu: Diem3 = [n[0] / nLen, n[1] / nLen, n[2] / nLen];
      if (!hostFaceNormals.some((e) => Math.abs(tich(e, nu)) > 0.995)) {
        hostFaceNormals.push(nu);
      }
    }
  }

  const framingPts = validCtxPts.length > 0 ? allScenePts : validObjPts;
  const safeNdc =
    objectKind === "solid" || objectKind === "curved_surface"
      ? { xMin: -0.78, xMax: 0.78, yMin: -0.78, yMax: 0.78 }
      : { xMin: -0.84, xMax: 0.84, yMin: -0.82, yMax: 0.82 };

  const computeDistanceAndClearance = (dirUnit: Diem3, camTarget: Diem3): { pos: Diem3; dist: number; margin: number } | null => {
    const knObj = khungNhinQuanhTam(validObjPts, objCenter, fovDeg, aspect, dirUnit, {
      xMin: -0.58,
      xMax: 0.58,
      yMin: -0.58,
      yMax: 0.58,
    });
    const knCtx = khungNhinQuanhTam(framingPts, camTarget, fovDeg, aspect, dirUnit, safeNdc);
    const baseDist = knCtx ? Math.max(0.2 * sceneScale, distPt(knCtx.viTri, camTarget)) : Math.max(1.5 * sceneScale, curDist);
    const objOnlyDist = knObj ? distPt(knObj.viTri, objCenter) * 1.15 : 0;
    const ctxFloorMult = validCtxPts.length > 0 ? (objectKind === "point" ? 1.02 : 1.06) : 0.94;
    let dist =
      objectKind === "point"
        ? Math.max(baseDist * ctxFloorMult, 0.75 * sceneScale)
        : Math.max(baseDist * ctxFloorMult, objOnlyDist, 0.5 * sceneScale);

    const floorSupport = stableCenter ? Math.max(0.2 * sceneScale, khoangTuaTheoHuong(stableCenter, dirUnit) * 1.35) : 0.2 * sceneScale;
    dist = Math.max(dist, floorSupport);

    // Bảo đảm vị trí camera không cắt xuyên vào vỏ khối / mặt cầu
    for (let step = 0; step < 5; step += 1) {
      const candidatePos = add3(camTarget, scale3(dirUnit, dist));
      const margin = minClearanceToMeshes(candidatePos, occluderMeshes, occluderSpheres);
      const minSafe = 0.08 * sceneScale;
      if (!Number.isFinite(margin) || margin >= minSafe) {
        return { pos: candidatePos, dist, margin };
      }
      dist += Math.max(minSafe - margin + 0.05 * sceneScale, 0.12 * sceneScale);
    }
    const finalPos = add3(camTarget, scale3(dirUnit, dist));
    return { pos: finalPos, dist, margin: minClearanceToMeshes(finalPos, occluderMeshes, occluderSpheres) };
  };

  // Kiểm tra góc nhìn hiện tại đã tối ưu chưa (unchanged)
  const curTargetNdc = projectToNdc(objCenter, currentPosition, currentTarget, fovDeg, aspect);
  const curObjNdcs = validObjPts.map((p) => projectToNdc(p, currentPosition, currentTarget, fovDeg, aspect));
  const curNormalAlign = nHat ? Math.abs(tich(uCur, nHat)) : null;
  const curSegCos = segDir ? Math.abs(tich(uCur, segDir)) : null;
  const curOcc = computeOccludedRatioForView(currentPosition, samplePtsForOcclusion, objectId, objectKind, occluderMeshes, occluderSpheres);
  const curMargin = minClearanceToMeshes(currentPosition, occluderMeshes, occluderSpheres);
  const refFramed = computeDistanceAndClearance(uCur, desiredTarget);
  const allObjInViewport =
    curTargetNdc !== null
    && Math.abs(curTargetNdc[0]) <= 0.58
    && Math.abs(curTargetNdc[1]) <= 0.58
    && curObjNdcs.every((ndc) => ndc !== null && Math.abs(ndc[0]) <= 0.78 && Math.abs(ndc[1]) <= 0.78);
  const curPoseOptimal =
    allObjInViewport
    && distPt(currentTarget, desiredTarget) <= 0.22 * sceneScale
    && (curNormalAlign === null || curNormalAlign >= 0.48)
    && (curSegCos === null || curSegCos <= 0.76)
    && curOcc === 0
    && (!Number.isFinite(curMargin) || curMargin >= 0.08 * sceneScale)
    && refFramed !== null
    && curDist >= refFramed.dist * 0.80
    && curDist <= refFramed.dist * 1.24;

  if (curPoseOptimal) {
    return {
      status: "unchanged",
      position: [...currentPosition],
      target: [...currentTarget],
      viewDirection: uCur,
      distance: curDist,
      targetNdc: curTargetNdc!,
      normalAlignment: curNormalAlign,
      segmentForeshorteningCos: curSegCos,
      occludedRatio: curOcc,
      minMarginToHostMesh: curMargin,
      reason: "current_view_already_optimal",
    };
  }

  // Sinh tối thiểu 72 hướng nhìn ứng viên xác định tính (camera-relative + cầu + hướng ưu tiên theo mặt/cạnh)
  const candidates: Diem3[] = [uCur, chuan([...HUONG_SGK])];
  const baseAz = Math.atan2(uCur[1], uCur[0]);
  const azCount = 12;
  const elevDegs = [16, 28, 42, 58, -14, -30];
  for (const elDeg of elevDegs) {
    const el = (elDeg * Math.PI) / 180;
    const cosEl = Math.cos(el);
    const sinEl = Math.sin(el);
    for (let ai = 0; ai < azCount; ai += 1) {
      const az = baseAz + (2 * Math.PI * ai) / azCount;
      candidates.push([cosEl * Math.cos(az), cosEl * Math.sin(az), sinEl]);
    }
  }
  if (nHat) {
    const seed: Diem3 = Math.abs(nHat[2]) < 0.85 ? [0, 0, 1] : [1, 0, 0];
    const t1 = chuan(cheo(nHat, seed));
    const t2 = chuan(cheo(nHat, t1));
    for (const sign of [1, -1]) {
      for (const tilt of [0.55, 0.75, 0.90]) {
        const perp = Math.sqrt(1 - tilt * tilt);
        for (let k = 0; k < 4; k += 1) {
          const th = (Math.PI * k) / 2;
          candidates.push(chuan([
            sign * tilt * nHat[0] + perp * (Math.cos(th) * t1[0] + Math.sin(th) * t2[0]),
            sign * tilt * nHat[1] + perp * (Math.cos(th) * t1[1] + Math.sin(th) * t2[1]),
            sign * tilt * nHat[2] + perp * (Math.cos(th) * t1[2] + Math.sin(th) * t2[2]),
          ]));
        }
      }
    }
  }
  if (segDir) {
    const seed: Diem3 = Math.abs(segDir[2]) < 0.85 ? [0, 0, 1] : [1, 0, 0];
    const p1 = chuan(cheo(segDir, seed));
    const p2 = chuan(cheo(segDir, p1));
    for (let k = 0; k < 8; k += 1) {
      const th = (2 * Math.PI * k) / 8;
      candidates.push(chuan([
        0.92 * (Math.cos(th) * p1[0] + Math.sin(th) * p2[0]) + 0.38 * uCur[0],
        0.92 * (Math.cos(th) * p1[1] + Math.sin(th) * p2[1]) + 0.38 * uCur[1],
        0.92 * (Math.cos(th) * p1[2] + Math.sin(th) * p2[2]) + 0.38 * uCur[2],
      ]));
    }
  }

  let bestScore = Infinity;
  let bestResult: SmartLocateResult | null = null;
  let uCurCandidateScore: number | null = null;

  for (let candIdx = 0; candIdx < candidates.length; candIdx += 1) {
    const rawDir = candidates[candIdx]!;
    if (!rawDir.every(Number.isFinite) || Math.hypot(...rawDir) <= 1e-9) continue;
    const u = chuan(rawDir);
    const framed = computeDistanceAndClearance(u, desiredTarget);
    if (!framed) continue;

    const targetNdc = projectToNdc(objCenter, framed.pos, desiredTarget, fovDeg, aspect);
    if (!targetNdc || Math.abs(targetNdc[0]) > 0.88 || Math.abs(targetNdc[1]) > 0.88) continue;

    const normAlign = nHat ? Math.abs(tich(u, nHat)) : null;
    const segCos = segDir ? Math.abs(tich(u, segDir)) : null;
    const occRatio = computeOccludedRatioForView(framed.pos, samplePtsForOcclusion, objectId, objectKind, occluderMeshes, occluderSpheres);

    let penalty = 0;
    // 1. Che khuất ưu tiên tuyệt đối (đặc biệt với điểm nằm trong khối / tiếp xúc)
    penalty += occRatio * (isInteriorOrTangent ? 220 : 140);
    // 2. Mặt phẳng & thiết diện: cấm nhìn liếc cạnh (|u · n̂| < 0.42) + ưu tiên diện tích hình chiếu đa giác 2D
    if (normAlign !== null) {
      if (normAlign < 0.42) penalty += 160 + (0.42 - normAlign) * 200;
      else if (normAlign < 0.52) penalty += (0.52 - normAlign) * 18;
      // Thích góc nhìn nghiêng sư phạm (0.55..0.88) hơn nhìn thẳng đứng quá dẹt
      if (normAlign > 0.94) penalty += (normAlign - 0.94) * 12;
    }
    if ((objectKind === "section" || objectKind === "plane") && validObjPts.length >= 3) {
      const poly2d: [number, number][] = [];
      let clippedPolyPts = 0;
      for (const p of validObjPts) {
        const ndc = projectToNdc(p, framed.pos, desiredTarget, fovDeg, aspect);
        if (!ndc) {
          clippedPolyPts += 1;
        } else {
          if (Math.abs(ndc[0]) > 0.92 || Math.abs(ndc[1]) > 0.92) clippedPolyPts += 1;
          poly2d.push(ndc);
        }
      }
      penalty += clippedPolyPts * 22;
      if (poly2d.length >= 3) {
        let twiceArea = 0;
        for (let i = 0; i < poly2d.length; i += 1) {
          const a = poly2d[i]!;
          const b = poly2d[(i + 1) % poly2d.length]!;
          twiceArea += a[0] * b[1] - b[0] * a[1];
        }
        const polyAreaNdc = 0.5 * Math.abs(twiceArea);
        if (polyAreaNdc < 0.015) penalty += 35;
        else penalty -= Math.min(polyAreaNdc * 18, 8);
      }
    }
    // 3. Đoạn thẳng: tránh nhìn dọc theo cạnh (|u · d̂| > 0.82)
    if (segCos !== null) {
      if (segCos > 0.82) penalty += 150 + (segCos - 0.82) * 200;
      else penalty += segCos * segCos * 12;
    }
    // 4. Bảo toàn bối cảnh khối chủ & tránh cắt viền khung nhìn / nhìn lướt sát mặt bên của khối
    if (validCtxPts.length > 0) {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      let ctxClipped = 0;
      for (const p of validCtxPts) {
        const ndc = projectToNdc(p, framed.pos, desiredTarget, fovDeg, aspect);
        if (!ndc || Math.abs(ndc[0]) > 0.90 || Math.abs(ndc[1]) > 0.90) {
          ctxClipped += 1;
        }
        if (ndc) {
          if (ndc[0] < minX) minX = ndc[0];
          if (ndc[0] > maxX) maxX = ndc[0];
          if (ndc[1] < minY) minY = ndc[1];
          if (ndc[1] > maxY) maxY = ndc[1];
        }
      }
      penalty += ctxClipped * 18;
      if (validCtxPts.length >= 4 && Number.isFinite(minX)) {
        const spanX = Math.min(2, Math.max(0, maxX - minX));
        const spanY = Math.min(2, Math.max(0, maxY - minY));
        penalty -= Math.min(spanX * spanY * 8, 6);
      }
    }
    for (const fn of hostFaceNormals) {
      const fCos = Math.abs(tich(u, fn));
      if (fCos < 0.14) penalty += (0.14 - fCos) * 25;
    }
    // 5. Tránh lật ngược chiều đứng (nhìn từ dưới lên sâu quá -0.15)
    if (u[2] < 0.08) penalty += 35 + (0.08 - u[2]) * 60;
    else if (u[2] > 0.90) penalty += (u[2] - 0.90) * 25;
    // 6. Giữ tâm đối tượng tương đối trung tâm trong khung nhìn & chuyển động mượt từ góc nhìn hiện tại
    penalty += (Math.abs(targetNdc[0]) + Math.abs(targetNdc[1])) * 6;
    if (Math.abs(targetNdc[0]) > 0.56 || Math.abs(targetNdc[1]) > 0.56) {
      penalty += 14;
    }
    const rotCos = Math.max(-1, Math.min(1, tich(u, uCur)));
    penalty += (1 - rotCos) * 4.5;
    // 7. Rất nhẹ ưu tiên hướng 3/4 chuẩn SGK nếu nhiều hướng ngang điểm
    const sgkCos = tich(u, chuan([...HUONG_SGK]));
    penalty += (1 - sgkCos) * 0.4;
    if (candIdx === 0) uCurCandidateScore = penalty;

    if (penalty < bestScore) {
      bestScore = penalty;
      bestResult = {
        status: "located",
        position: framed.pos,
        target: desiredTarget,
        viewDirection: u,
        distance: framed.dist,
        targetNdc,
        normalAlignment: normAlign,
        segmentForeshorteningCos: segCos,
        occludedRatio: occRatio,
        minMarginToHostMesh: framed.margin,
        reason: `smart_locate_${objectKind}`,
      };
    }
  }

  const allObjUnclipped =
    curTargetNdc !== null
    && Math.abs(curTargetNdc[0]) <= 0.88
    && Math.abs(curTargetNdc[1]) <= 0.88
    && curObjNdcs.every((ndc) => ndc !== null && Math.abs(ndc[0]) <= 0.92 && Math.abs(ndc[1]) <= 0.92);
  if (
    bestResult
    && allObjUnclipped
    && distPt(currentTarget, desiredTarget) <= 0.22 * sceneScale
    && (curNormalAlign === null || curNormalAlign >= 0.42)
    && (curSegCos === null || curSegCos <= 0.82)
    && curOcc <= bestResult.occludedRatio + 1e-6
    && (!Number.isFinite(curMargin) || curMargin >= 0.08 * sceneScale)
    && refFramed !== null
    && curDist >= refFramed.dist * 0.80
    && curDist <= refFramed.dist * 1.24
    && uCurCandidateScore !== null
    && uCurCandidateScore <= bestScore + 5.0
  ) {
    return {
      status: "unchanged",
      position: [...currentPosition],
      target: [...currentTarget],
      viewDirection: uCur,
      distance: curDist,
      targetNdc: curTargetNdc!,
      normalAlignment: curNormalAlign,
      segmentForeshorteningCos: curSegCos,
      occludedRatio: curOcc,
      minMarginToHostMesh: curMargin,
      reason: "current_view_already_optimal",
    };
  }

  return bestResult ?? fallback("no_valid_locate_candidate", "Không tìm thấy hướng nhìn hợp lệ cho đối tượng.");
}

