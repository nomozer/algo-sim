/**
 * MỘT THẨM QUYỀN ĐẶT TÊN, VÀ NÓ Ở BACKEND.
 *
 * ─── ĐIỀU GUARD NÀY CANH ──────────────────────────────────────────────────
 *
 * `display_names.py` sở hữu câu hỏi *"vật này gọi là gì trước mặt học sinh"*.
 * Frontend được **bày ra**, không được **dịch**: nó chọn giữa `label`,
 * `notation`, `reference`, `role`; nó cắt chữ, xếp chỗ, ẩn hiện. Nó không
 * biến `construct_point.midpoint` thành *"Trung điểm"*.
 *
 * ─── VÌ SAO CẦN MỘT GUARD, KHÔNG PHẢI MỘT LỜI DẶN ────────────────────────
 *
 * Bảng thứ hai ấy **đã từng tồn tại** ở `Scene3DExplorer.TU_PHEP_DUNG`, sống
 * sót qua cả wave G1 (wave dựng thẩm quyền tên ở backend), và chỉ lộ ra ở G4:
 * thêm `plane_perpendicular_to_line` thì bảng frontend không có khoá, và ô soi
 * lặng lẽ tụt xuống *"Mặt phẳng"* trong khi backend đã có sẵn câu đầy đủ. Một
 * bảng phải nhớ cập nhật là một bảng sẽ quên.
 *
 * ─── GUARD KHOÁ BẤT BIẾN, KHÔNG KHOÁ TÊN BIẾN ────────────────────────────
 *
 * Đổi tên `TU_PHEP_DUNG` thành `NHAN_PHEP_DUNG` không được phép đi lọt. Nên
 * guard tìm theo **dấu vết của việc dịch**: một chuỗi định danh máy
 * (`construct_*`, `measure.*`, `intersect_*`, tên `MemoryType`) nằm cạnh chữ
 * tiếng Việt trong cùng một mã nguồn không-phải-chú-thích.
 *
 * ⚠️ Guard **không** cấm chữ tiếng Việt trong frontend. *"Ẩn"*, *"Xem cấu
 * tạo"*, *"Loại"*, *"Phép dựng"*, *"Dựa trên"* là từ vựng giao diện và phải
 * được giữ — chúng gọi tên **thao tác của người dùng**, không gọi tên **khái
 * niệm hình học**.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const GOC = new URL("../../..", import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1");

function moiTepNguon(thuMuc: string): string[] {
  const ra: string[] = [];
  for (const ten of readdirSync(thuMuc)) {
    const p = join(thuMuc, ten);
    if (statSync(p).isDirectory()) {
      ra.push(...moiTepNguon(p));
    } else if (/\.tsx?$/.test(ten) && !/\.test\.tsx?$/.test(ten)) {
      ra.push(p);
    }
  }
  return ra;
}

/** Bỏ chú thích: lời kể *vì sao* được phép nhắc tên định danh máy. */
function chiMa(van: string): string {
  return van.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

/** Định danh do BACKEND phát — tên phép dựng, phép đo, kiểu ngữ nghĩa. */
const DINH_DANH_MAY = [
  "construct_point", "construct_line", "construct_plane", "construct_polygon",
  "construct_solid", "construct_section",
  "intersect_line_plane", "intersect_plane_plane", "intersect_line_line",
  "project_onto", "vector_from_points", "divide_segment", "translate",
  "plane_perpendicular_to_line",
  "measure.distance", "measure.volume", "measure.angle_cos",
];

/** Chữ có dấu tiếng Việt — dấu hiệu một cụm dành cho NGƯỜI ĐỌC. */
const CO_DAU = /[àáảãạăâèéẻẽẹêìíỉĩịòóỏõọôơùúủũụưỳýỷỹỵđ]/i;

const TEP = moiTepNguon(join(GOC, "simulations", "domains", "geometry"))
  .concat(moiTepNguon(join(GOC, "components")));

describe("(G1/G4) frontend KHÔNG dịch ngữ nghĩa hình học sang tiếng Việt", () => {
  it("tìm được tệp để soi — guard không rỗng vô nghĩa", () => {
    expect(TEP.length).toBeGreaterThan(10);
  });

  it("không tệp nào ánh xạ định danh máy sang cụm tiếng Việt", () => {
    const pham: string[] = [];
    for (const p of TEP) {
      const ma = chiMa(readFileSync(p, "utf8"));
      for (const dong of ma.split("\n")) {
        if (!DINH_DANH_MAY.some((d) => dong.includes(d))) continue;
        // Dòng có định danh máy. Nó chỉ phạm luật khi TRÊN CÙNG DÒNG có một
        // chuỗi tiếng Việt có dấu — tức đang đặt hai thứ cạnh nhau để dịch.
        const chuoi = dong.match(/"[^"]*"|'[^']*'|`[^`]*`/g) ?? [];
        if (chuoi.some((c) => CO_DAU.test(c))) {
          pham.push(`${p.split(/[\\/]/).slice(-2).join("/")}: ${dong.trim().slice(0, 90)}`);
        }
      }
    }
    expect(pham, "frontend đang dịch định danh máy sang tiếng người học "
      + "— việc ấy thuộc `display_names.py`:\n" + pham.join("\n")).toEqual([]);
  });

  it("không tệp nào đọc `producer` để quyết chữ hiển thị", () => {
    const pham: string[] = [];
    for (const p of TEP) {
      const ma = chiMa(readFileSync(p, "utf8"));
      // `producer` được phép HIỆN RA (chế độ chi tiết cho giáo viên) và được
      // phép đi qua như dữ liệu. Nó KHÔNG được làm khoá tra bảng, cũng không
      // được đem so với một hằng chuỗi để rẽ nhánh.
      if (/\[[^\]]*\bproducer\b[^\]]*\]\s*(\?\?|\|\||;|\))/.test(ma)
          || /\bproducer\b\s*===\s*["'`]/.test(ma)) {
        pham.push(p.split(/[\\/]/).slice(-2).join("/"));
      }
    }
    expect(pham, "`producer` đang được dùng để tra bảng hoặc rẽ nhánh hiển thị")
      .toEqual([]);
  });

  it("từ vựng GIAO DIỆN vẫn được giữ — guard không phải bộ lọc chính tả", () => {
    /* Đối chứng: nếu guard trên cấm mọi chữ tiếng Việt thì nó vô dụng, và ca
     * này sẽ đỏ trước. Những cụm dưới đây gọi tên THAO TÁC của người dùng, và
     * chúng phải sống. */
    const tatCa = TEP.map((p) => readFileSync(p, "utf8")).join("\n");
    for (const cum of ["Dựa trên", "Xem cấu tạo", "Thành phần", "Bước sau"]) {
      expect(tatCa).toContain(cum);
    }
  });
});
