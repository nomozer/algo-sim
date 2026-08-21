import { beforeAll, describe, expect, it } from "vitest";
import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { publicCatalog } from "../data/offline-catalog";
import type { SimulationModule } from "./types";
/* W7 — NGUỒN DUY NHẤT: bảng chế độ nay sống ở mã SẢN PHẨM. Giữ bản thứ hai ở
   đây thì mã sản phẩm và bảng đo sẽ trôi khỏi nhau, và triệu chứng của kiểu
   trôi ấy là "test xanh mà học sinh thấy khác". */
import { TRANSPORT_POLICY } from "./transport-policy";

/**
 * WAVE 6 — MÔ HÌNH LÀ CHÍNH, THỬ THÁCH LÀ PHỤ.
 *
 * ─── CÂU HỎI PHẢI TRẢ LỜI ─────────────────────────────────────────────────
 *
 * "AlgoSim là một PHÒNG THÍ NGHIỆM Tin học, hay là một bài kiểm tra có hình
 * minh hoạ ở trên?"
 *
 * Cách hỏi phải quét TOÀN danh mục chứ không xem vài ảnh chụp: mùi quiz không
 * nằm ở một trang xấu, nó nằm ở chỗ SỞ HỮU — một thanh dự đoán mở sẵn, một tấm
 * thẻ "Đúng/Sai" cao hơn cả cơ chế, hay một kết quả bị giấu tới khi bấm Play.
 * Sửa từng trang là vá triệu chứng; đo theo chủ sở hữu mới thấy bán kính.
 *
 * ─── BỐN TẦNG (§WAVE6) ────────────────────────────────────────────────────
 *
 *   1. MÔ HÌNH / CÔNG CỤ        — trọng lượng thị giác cao nhất
 *   2. TRẠNG THÁI NHÂN QUẢ      — gọn, một câu
 *   3. GIẢI THÍCH (tuỳ chọn)    — đóng mặc định
 *   4. THỬ THÁCH (tuỳ chọn)     — mở có chủ đích
 *
 * ─── BA BỀ MẶT KHÔNG ĐƯỢC LẪN ─────────────────────────────────────────────
 *
 *   KHÁM PHÁ  — MÔ TẢ cái vừa đổi và vì sao. Không phán đúng/sai.
 *   CAM KẾT   — học sinh quyết định BƯỚC TIẾP THEO của chính thuật toán
 *               (đổi chỗ / giữ nguyên / chọn nửa trái). Đây là CƠ CHẾ, không
 *               phải một lớp trắc nghiệm dán lên trên.
 *   THỬ THÁCH — dự đoán tuỳ chọn, mở có chủ đích, tính đúng sai do engine tất
 *               định sở hữu (`predict.check`), UI chỉ ĐỌC.
 *
 * ⚠️ Manifest này MÔ TẢ hiện thực, KHÔNG cấp chứng nhận. Nợ bằng chứng toàn
 * danh mục của Wave 4 (tương tác + phù hợp trải nghiệm, đo trong trình duyệt)
 * vẫn là `NO_EVIDENCE` và thuộc W12 — không dòng nào ở đây xoá được nó.
 */

type TransportNeed = "FULL_TRACE" | "OPTIONAL_TRACE" | "RESET_ONLY" | "UNCLASSIFIED";

interface Row {
  id: string;
  domain: string;
  interactionMode: string;
  /** Có công cụ/tham số học sinh đổi được không (dẫn từ hợp đồng module). */
  tool: boolean;
  trace: boolean;
  challenge: boolean;
  /** Thử thách có đóng mặc định không — đọc từ CHỦ SỞ HỮU state, không đoán. */
  challengeDefaultClosed: boolean;
  causalFeedback: boolean;
  transportNeed: TransportNeed;
  correctnessOwner: string;
  hasOfflineSample: boolean;
}

/**
 * NHU CẦU TRANSPORT — khai theo CƠ CHẾ, không theo "module có timeline không".
 *
 * Có timeline mà kết quả đọc được ngay (base_conversion sau W5) thì transport
 * là TUỲ CHỌN: nó giải thích quá trình, không phải đường duy nhất tới đáp án.
 * Ngược lại, đóng gói qua các tầng mạng thì TRÌNH TỰ CHÍNH LÀ bài học, nên
 * transport là bắt buộc.
 *
 * Đây là đầu vào cho W7 (W7 sở hữu bề rộng/bố cục), nên nó phải nói LÝ DO.
 */
const TRANSPORT_REASON = TRANSPORT_POLICY;

let rows: Row[] = [];
let mods: SimulationModule<unknown, unknown>[] = [];

/**
 * ⚠️ KHÔNG CÓ MẶC ĐỊNH — và đó là cả điểm của hàm này.
 *
 * Bản đầu trả `FULL_TRACE` cho mọi module có `timeline`, và bảng đọc ra "18
 * target cần transport đầy đủ". Con số ấy GIẢ: nó chỉ là "18 module có
 * timeline" đổi tên, không phải một phán quyết về cơ chế nào cần trình tự.
 * Mặc định như thế biến bảng phân loại thành phép đếm thuộc tính kĩ thuật.
 *
 * Nên target chưa được người soát phân loại sẽ hiện `UNCLASSIFIED`, và test
 * dưới đòi con số đó bằng 0 — tức phải khai từng target kèm lý do CƠ CHẾ.
 */
function transportOf(m: SimulationModule<unknown, unknown>): TransportNeed {
  return TRANSPORT_REASON[m.id]?.[0] ?? "UNCLASSIFIED";
}

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();
  const samples = new Set(publicCatalog().map((s) => s.simId));
  mods = listSimulations().map((meta) => getSimulation(meta.id)!);
  rows = mods
    .map((m) => ({
      id: m.id,
      domain: m.domain,
      interactionMode: m.interactionMode,
      tool: Boolean(m.explore) || m.interactionMode !== "progressive",
      trace: Boolean(m.timeline),
      challenge: false, // W13 gỡ Thử thách
      /* Đọc từ chủ sở hữu THẬT: `loadEnvelope` đặt `challengeOpen: false` cho
         MỌI mô phỏng mới (W4B-2Z). Nên giá trị này giống nhau ở mọi dòng — và
         đó chính là điều đáng khoá: nó là thuộc tính của SHELL, không phải của
         từng module, nên không module nào tự mở được. */
      challengeDefaultClosed: true,
      causalFeedback: Boolean(m.narrate),
      transportNeed: transportOf(m),
      correctnessOwner: "—", // không còn bên chấm nào sau W13
      hasOfflineSample: samples.has(m.id),
    }))
    .sort((a, b) => a.id.localeCompare(b.id));
});

// ── 1. THỬ THÁCH LÀ PHỤ ──────────────────────────────────────────────────────

describe("W6 §3 — thử thách đóng mặc định, mô hình dùng được khi nó đóng", () => {
  /* it("KHÔNG mô phỏng nào tự mở thử thách khi vừa nạp…") ĐÃ XOÁ 2026-08-21 (Task 10b).
     Khai niem W13 da go: cong Thi nghiem dang PANEL / che do Thu thach / vung cam ket. */

  it("mọi target có thử thách đều CÓ mô hình dùng được khi thử thách đóng", () => {
    /* Nếu một target chỉ tương tác được qua ô dự đoán thì đóng thử thách lại là
       học sinh không còn gì để làm — đúng định nghĩa "quiz có hình minh hoạ". */
    const offenders = rows
      .filter((r) => r.challenge && !r.tool && !r.trace)
      .map((r) => r.id);
    expect(offenders, `target chỉ dùng được qua thử thách:\n${offenders.join("\n")}`)
      .toEqual([]);
  });

  /* it("tính đúng sai KHÔNG do UI thử thách sở hữu…") ĐÃ XOÁ 2026-08-21 (Task 10b).
     Khai niem W13 da go: cong Thi nghiem dang PANEL / che do Thu thach / vung cam ket. */
});

// ── 2. KẾT QUẢ HIỆN NGAY VỚI TARGET CÔNG CỤ (chính sách W5, nâng lên toàn cục) ──

describe("W6 §4 — chính sách hiện kết quả", () => {
  it("target CÔNG CỤ không được giấu kết quả sau thanh điều khiển", () => {
    /* Chính sách hình thành ở W5 cho ba target, nay khoá thành luật chung:
       transport TUỲ CHỌN hoặc KHÔNG CÓ ⇒ kết quả phải đọc được không cần tua.
       Bằng chứng trình duyệt: `measure-tool-first-w5.mjs`. */
    const toolTargets = rows.filter((r) =>
      r.transportNeed === "OPTIONAL_TRACE" || r.transportNeed === "RESET_ONLY");
    expect(toolTargets.length, "không target công cụ nào ⇒ luật rỗng")
      .toBeGreaterThanOrEqual(3);
    for (const r of toolTargets) {
      expect(r.tool, `${r.id} khai transport công cụ nhưng không có công cụ`).toBe(true);
    }
  });

  it("mọi target khai FULL_TRACE đều thật sự có dòng thời gian", () => {
    for (const r of rows.filter((x) => x.transportNeed === "FULL_TRACE")) {
      expect(r.trace, `${r.id} đòi transport đầy đủ mà không có timeline`).toBe(true);
    }
  });

  it("KHÔNG target nào còn chưa phân loại transport", () => {
    /* Chỗ này thay cho một giá trị mặc định. Mặc định "có timeline ⇒ cần
       transport đầy đủ" cho ra con số 18 nghe rất gọn nhưng không phải phán
       quyết nào cả — nó là phép đếm thuộc tính kĩ thuật đội lốt phân loại sư
       phạm. Đòi 0 chưa-phân-loại buộc mỗi target phải có người soát và một lý
       do đọc được. */
    const missing = rows.filter((r) => r.transportNeed === "UNCLASSIFIED").map((r) => r.id);
    expect(missing, `chưa khai nhu cầu transport (kèm lý do cơ chế):\n${missing.join("\n")}`)
      .toEqual([]);
  });

  it("mỗi ngoại lệ transport phải nêu LÝ DO CƠ CHẾ", () => {
    for (const [id, [, why]] of Object.entries(TRANSPORT_REASON)) {
      expect(rows.some((r) => r.id === id), `${id} không có trong danh mục`).toBe(true);
      expect(why.length, `${id}: lý do quá ngắn để kiểm chứng`).toBeGreaterThan(60);
      for (const lazy of ["renderer đang", "hiện tại đang", "theo lịch sử"]) {
        expect(why, `${id}: lý do né cơ chế`).not.toContain(lazy);
      }
    }
  });
});

// ── 3. PHẢN HỒI NHÂN QUẢ ≠ PHÁN QUYẾT ────────────────────────────────────────

describe("W6 §5 — mô tả khác phán xét", () => {
  it("`narrate` KHÔNG được nói giọng chấm điểm", () => {
    /* §17 #4: phản hồi KHÁM PHÁ bị render thành phán quyết đúng/sai. `narrate`
       mô tả trạng thái ("9 > 8,5 → xét nửa trái"); nói "Đúng"/"Sai" ở đó là
       lấn sang bề mặt thử thách, và học sinh đang chỉ kéo thanh trượt thì
       không có gì để đúng hay sai cả. */
    const dir = new URL("./domains/", import.meta.url).pathname
      .replace(/^\/([A-Za-z]:)/, "$1");
    const files: string[] = [];
    const walk = (d: string) => {
      for (const e of readdirSync(d)) {
        const p = join(d, e);
        if (statSync(p).isDirectory()) walk(p);
        else if (/\.tsx?$/.test(p) && !/\.test\./.test(p)) files.push(p);
      }
    };
    walk(dir);
    const offenders: string[] = [];
    for (const f of files) {
      const body = readFileSync(f, "utf-8")
        .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
      const narrate = body.match(/narrate\s*:\s*\([\s\S]*?\n\s{4}\}/);
      if (!narrate) continue;
      for (const judgy of ["Đúng rồi", "Sai rồi", "Chưa đúng", "Chính xác"]) {
        if (narrate[0].includes(judgy)) offenders.push(`${f}: narrate nói "${judgy}"`);
      }
    }
    expect(offenders, `phản hồi khám phá đang phán đúng/sai:\n${offenders.join("\n")}`)
      .toEqual([]);
  });

  it("W12-A: TOÀN BỘ khối thử thách gọn, không chỉ băng phán quyết", () => {
    /* GUARD W6 ĐO SAI TẦNG, và một màn hình thật đã cho thấy điều đó.
       W6 chỉ đòi `.result-banner` có `fit-content`. Băng ấy gọn thật, nhưng
       CÁI HỘP CHỨA nó — câu hỏi, dãy lựa chọn, đệm — vẫn cao 111px trong khi cơ
       chế của `network.packet_routing` chỉ cao 180px (tỉ lệ 0,62). Mắt đọc ra
       "bài kiểm tra dán dưới hình minh hoạ".
       Nay `.predict-bar` là dải NGANG biết xuống dòng, nên câu hỏi · lựa chọn ·
       nút đóng nằm cùng một hàng khi còn chỗ. Đo lại: 61px, tỉ lệ 0,34. */
    const css = readFileSync(new URL("../styles/global.css", import.meta.url).pathname
      .replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");
    const NL = String.fromCharCode(10);
    const block = css.slice(css.indexOf(`${NL}.predict-bar {`));
    const decl = block.slice(0, block.indexOf(`${NL}}`));
    expect(decl.length, "không tìm thấy khối .predict-bar — mẫu hỏng, không phải đạt")
      .toBeGreaterThan(60);
    expect(decl, "khối thử thách phải là dải NGANG biết xuống dòng")
      .toMatch(/flex-wrap:\s*wrap/);
    expect(decl, "cột dọc ép nó thành nhiều hàng cứng")
      .not.toMatch(/flex-direction:\s*column/);
    /* Đệm phải lùi một bậc so với bản cũ (`--sp-md --sp-lg`). */
    expect(decl).toMatch(/padding:\s*var\(--sp-sm\)\s+var\(--sp-md\)/);
  });

  it("băng kết quả là DẢI GỌN, không phải tấm thẻ chiếm sân khấu", () => {
    /* §6/§17 #3. Đo ở CSS chứ không ở ảnh: `.result-banner` phải giữ
       `width: fit-content` — bỏ dòng đó là nó giãn hết bề ngang thẻ và trở
       thành thứ nặng nhất trên trang. */
    const css = readFileSync(new URL("../styles/global.css", import.meta.url).pathname
      .replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");
    const block = css.slice(css.indexOf("\n.result-banner {"));
    const decl = block.slice(0, block.indexOf("}"));
    expect(decl, "`.result-banner` phải ôm sát nội dung").toContain("width: fit-content");
    expect(decl, "băng kết quả không được là khối chiếm dòng").not.toMatch(/display:\s*block/);
  });
});

// ── 4. KHẢ NĂNG TIẾP CẬN CỦA LỐI VÀO/RA THỬ THÁCH (§16) ─────────────────────

/* describe "W6 §16 — thử thách vào được thì phải ra được" GỠ 2026-08-21
   (Task 10b): cả khối đọc `components/PredictionBar.tsx`, file W13 đã XOÁ, và
   kiểm ba tính chất của một cửa (đóng được / không chỉ dựa vào màu / trả tiêu
   điểm) mà cửa đó không còn tồn tại.

   Ba tính chất ấy vẫn đáng giữ cho MỌI cửa mới — chúng thuộc a11y chứ không
   thuộc Thử thách. `certify-a11y-w12.mjs` là chủ sở hữu hiện tại; nếu sau này
   route sinh ngữ nghĩa mở một chế độ có cửa, phải khoá lại ở đó. */

// ── 5. MANIFEST ──────────────────────────────────────────────────────────────

describe("W6 §20 — manifest trải nghiệm 23 target", () => {
  it("sinh manifest và giữ nguyên nợ bằng chứng W12", () => {
    expect(rows.length).toBeGreaterThanOrEqual(23);
    const counts = rows.reduce<Record<string, number>>((acc, r) => {
      acc[r.transportNeed] = (acc[r.transportNeed] ?? 0) + 1;
      return acc;
    }, {});
    try {
      const dir = new URL("../../../docs/evaluation/m20/", import.meta.url)
        .pathname.replace(/^\/([A-Za-z]:)/, "$1");
      mkdirSync(dir, { recursive: true });
      writeFileSync(join(dir, "experience-manifest.json"), JSON.stringify({
        generatedAt: new Date().toISOString(),
        note: "sinh từ registry qua vitest; MÔ TẢ hiện thực, KHÔNG cấp chứng nhận.",
        interactionCertification: "NO_EVIDENCE (toàn danh mục, đo trình duyệt — W12)",
        experienceSuitabilityCertification: "NO_EVIDENCE (W12)",
        transportCounts: counts,
        transportReasons: TRANSPORT_REASON,
        rows,
      }, null, 2), "utf-8");
    } catch { /* thư mục chỉ-đọc trong CI */ }
  });
});
