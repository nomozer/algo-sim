import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * VỆ SINH UI — QUÉT MÃ NGUỒN, KHÔNG QUÉT HTML ĐÃ RENDER (M9-UX6).
 *
 * VÌ SAO ĐỔI CÁCH QUÉT: guard đầu tiên (M9-UX5) quét `renderToString(<App/>)` —
 * nhưng SSR chỉ đi qua **trạng thái đầu** (Home) nên nó KHÔNG bao giờ chạm tới
 * workspace. Hậu quả: emoji 🔮 trong `PredictionBar` và chuỗi `find_max` trong
 * `AnalysisCard` **lọt qua guard xanh lè**, rồi người dùng chụp màn hình gửi lại.
 *
 * Bài học: guard phải đặt ở chỗ KHÔNG phụ thuộc route nào được test đi qua.
 * Quét thẳng mã nguồn thì mọi component đều bị soi, kể cả component chưa có test.
 */

const SRC = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (/\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name)) out.push(full);
  }
  return out;
}

const FILES = walk(SRC).map((f) => ({ path: f, text: readFileSync(f, "utf-8") }));

/**
 * Bóc chú thích + import: các chú thích ở repo này CỐ Ý nhắc tên ký tự đã cấm để
 * ghi lại lịch sử ("thay ⏮ ◀ ▶"), quét cả chú thích thì test tự bắt chính nó.
 */
function code(text: string): string {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "")
    .replace(/^import .*$/gm, "");
}

describe("(M9-UX6) UI hygiene — quét MÃ NGUỒN, không phụ thuộc route nào được test", () => {
  /**
   * Emoji + ký tự hình khối làm icon. `◧` (U+25E7) từng thành Ô VUÔNG RỖNG trên
   * Windows; emoji thì mỗi OS vẽ một kiểu, không ăn theo màu chữ. Icon = SVG.
   */
  it("KHÔNG emoji / ký tự Unicode làm icon trong bất kỳ component nào", () => {
    const BANNED = ["◧", "◨", "▸", "◀", "▶", "⏮", "⏭", "⏸", "⟳", "↺", "✕", "✓", "✗", "＋", "⌁"];
    const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;

    const offenders: string[] = [];
    for (const f of FILES) {
      if (f.path.endsWith("icons.tsx")) continue; // nơi ĐỊNH NGHĨA icon
      const body = code(f.text);
      for (const ch of BANNED) {
        if (body.includes(ch)) offenders.push(`${f.path}: ký tự "${ch}"`);
      }
      const m = body.match(EMOJI);
      if (m) offenders.push(`${f.path}: emoji "${m[0]}"`);
    }
    expect(offenders, `dùng components/icons.tsx thay vì:\n${offenders.join("\n")}`).toEqual([]);
  });

  /**
   * Chuỗi định danh kĩ thuật (`simulation_id`, `algorithm_id`) là khoá định tuyến
   * NỘI BỘ. Đã lọt lên UI học sinh BA lần: InputPanel → HistoryView → AnalysisCard.
   * Ba lần đều vá một chỗ mà không vá chỗ kia. Nay chặn ở mã nguồn.
   */
  it("KHÔNG render simulation_id / algorithm_id ra UI học sinh", () => {
    const offenders: string[] = [];
    for (const f of FILES) {
      // renderer/registry/legacy ĐƯỢC PHÉP dùng id (chúng định tuyến, không hiển thị)
      if (!/[/\\]components[/\\]/.test(f.path)) continue;
      const body = code(f.text);
      // Dấu hiệu HIỂN THỊ: id nằm trong biểu thức JSX. Nhưng DÙNG id làm KHOÁ TRA
      // bảng tên tiếng Việt (`ALGORITHM_NAMES[analysis.algorithm_id]`) là hợp lệ —
      // thứ hiện ra màn hình là cái TÊN, không phải cái id.
      const rendersRawId = /\{[^}]*\.algorithm_id[^}]*\}/.test(body) &&
        !/_NAMES\[[^\]]*\.algorithm_id\]/.test(body);
      if (rendersRawId) {
        offenders.push(`${f.path}: render algorithm_id`);
      }
      if (/\{[^}]*\.simulationId[^}]*\}/.test(body) && !/previewKindOf|getSimulation/.test(body)) {
        offenders.push(`${f.path}: render simulationId`);
      }
      if (/\{[^}]*\.simId[^}]*\}/.test(body) && !/previewKindOf/.test(body)) {
        offenders.push(`${f.path}: render simId`);
      }
    }
    expect(offenders, `chuỗi kĩ thuật lọt lên UI:\n${offenders.join("\n")}`).toEqual([]);
  });
});

/**
 * (SHELL-N) THUYẾT MINH LÀ KHE CỦA SHELL — khoá bằng quét MÃ NGUỒN.
 *
 * Vì sao cần răng: trước bản này "thuyết minh bước hiện tại" chỉ là QUY ƯỚC.
 * Hệ quả đã đo được (audit UI baseline): ba hiện thực song song cho cùng một vai
 * trò — `.narration-bar` ở 11 tệp, `.notes` ở `logic/dag-module.tsx`, và một bản
 * dựng riêng trong `database/table-module.tsx` — cộng thêm `tree-module.tsx` là
 * bốn. Không có gì bắt module thứ 23 phải thuyết minh, cũng không có gì bắt nó
 * đặt đúng chỗ. Nay chỉ `components/SimulationWorkspace.tsx` được dựng khe đó.
 */
describe("(SHELL-N) chỉ SHELL được dựng khe thuyết minh", () => {
  it("không module/renderer nào tự render .narration-bar", () => {
    const offenders = FILES.filter((f) => /[/\\]simulations[/\\]/.test(f.path))
      .filter((f) => /className=\{?[`"'][^`"']*narration-bar/.test(code(f.text)))
      .map((f) => f.path);
    expect(
      offenders,
      "thuyết minh phải đi qua `narrate()` + khe của SimulationWorkspace:\n" +
        offenders.join("\n"),
    ).toEqual([]);
  });

  it("SimulationWorkspace là nơi DUY NHẤT dựng khe đó", () => {
    const builders = FILES.filter((f) =>
      /className=\{?[`"'][^`"']*narration-bar/.test(code(f.text)),
    ).map((f) => f.path.replace(/\\/g, "/").split("/").pop());
    expect(builders).toEqual(["SimulationWorkspace.tsx"]);
  });
});

/**
 * AI KHÔNG CÓ CHỖ THƯỜNG TRỰC TRONG WORKSPACE — quét MÃ NGUỒN.
 *
 * Quyết định sản phẩm: AlgoSim là hệ mô phỏng tương tác CÓ AI hỗ trợ phân tích
 * đề, không phải chatbot. Trong workspace, narration + Observer phải tự đủ để
 * giải thích bước hiện tại; một nút gọi model ngay cạnh timeline vừa mở thêm
 * đường tiêu token lúc đang chạy, vừa giữ một góc màn hình thường trực cho AI.
 *
 * AI chỉ còn ở BỐN chỗ, tất cả thuộc giai đoạn HIỂU ĐỀ (Trang chủ / trạng thái
 * phân tích / tóm tắt đã hiểu / phản hồi thiếu dữ kiện). Danh sách ĐÓNG.
 *
 * Guard quét mã nguồn chứ không quét HTML: bài học M9-UX6 — SSR chỉ đi qua
 * trạng thái đầu nên không bao giờ chạm workspace, và đúng lớp lỗi đó đã để lọt
 * emoji + chuỗi kỹ thuật ra UI học sinh.
 */
describe("AI không có control learner-facing trong workspace", () => {
  const WORKSPACE_FILES = FILES.filter((f) =>
    /[/\\](SimulationWorkspace|SimulationInspector|SimulationControls)\.tsx$/
      .test(f.path),
  );

  it("có tìm đúng các tệp workspace (guard không rỗng vô nghĩa)", () => {
    expect(WORKSPACE_FILES.length).toBe(3);
  });

  it('không tệp workspace nào render "Hỏi AI" hay accordion AI', () => {
    const offenders: string[] = [];
    for (const f of WORKSPACE_FILES) {
      const body = code(f.text);
      for (const needle of ["Hỏi AI", "ai-toggle", "ai-section", "AIHelpPanel", "Trợ lý AI", "Giải thích bằng AI"]) {
        if (body.includes(needle)) offenders.push(`${f.path}: "${needle}"`);
      }
    }
    expect(
      offenders,
      `workspace phải tự giải thích bằng narration + Observer:\n${offenders.join("\n")}`,
    ).toEqual([]);
  });

  it("không component nào còn dựng mục AI thu gọn (đã gỡ khỏi panel Quan sát)", () => {
    const offenders = FILES.filter((f) => /className="ai-(toggle|section)"/.test(code(f.text)))
      .map((f) => f.path);
    expect(offenders, offenders.join("\n")).toEqual([]);
  });
});

/**
 * NGÔN NGỮ THIẾT KẾ (DESIGN.md) — hai luật "Don't" quan trọng nhất, khoá bằng code.
 *
 * Đã vi phạm: một bản thiết kế lấy TÍM (sticker palette) tô nút "Có" và nút
 * "Kiểm tra", tô nền thẻ dự đoán, viền trái tím — tức là biến màu TRANG TRÍ thành
 * ACCENT CẤU TRÚC THỨ HAI. DESIGN.md cấm cả hai điều đó.
 */
describe("(M9-UX6) DESIGN.md — sticker palette là TRANG TRÍ, không sơn hành động", () => {
  const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8").replace(
    /\/\*[\s\S]*?\*\//g,
    "",
  );

  /** Cắt CSS thành các rule { selector, body }. */
  const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map((m) => ({
    sel: m[1].trim(),
    body: m[2],
  }));

  it('KHÔNG có nút/CTA nào lấy màu sticker làm nền ("never paint an action")', () => {
    const offenders = rules
      .filter((r) => /\.btn-|composer-send|-toggle\b/.test(r.sel))
      .filter((r) => /background[^;]*var\(--accent-/.test(r.body))
      .map((r) => r.sel);
    expect(offenders, `nút sơn bằng màu trang trí: ${offenders.join(", ")}`).toEqual([]);
  });

  it("form field KHÔNG bo tròn viên thuốc (inputs stay tight at rounded-xs)", () => {
    const offenders = rules
      .filter((r) => /-filter|-search|text-input|composer-text/.test(r.sel))
      .filter((r) => /border-radius[^;]*(--rounded-full|9999px|1[6-9]px|[2-9]\dpx)/.test(r.body))
      .map((r) => r.sel);
    expect(offenders, `ô nhập bo tròn quá: ${offenders.join(", ")}`).toEqual([]);
  });

  it("nút primary khi disabled là XÁM TRUNG TÍNH, không phải xanh mờ", () => {
    const disabled = rules.find((r) => r.sel === ".btn-primary:disabled");
    expect(disabled, ".btn-primary:disabled chưa được khai — sẽ rơi vào opacity .4 toàn cục").toBeDefined();
    expect(disabled!.body).toMatch(/background:\s*var\(--canvas-soft\)/);
    expect(disabled!.body).toMatch(/opacity:\s*1/);
  });

  /* POLISH-3: nút bước hết đường đi là trạng thái BÌNH THƯỜNG, gặp liên tục —
     mờ 40% thì vừa khó đọc vừa trông như hỏng. Cùng luật với btn-primary. */
  it("nút bước khi disabled cũng xám trung tính, không mờ", () => {
    const disabled = rules.find((r) => r.sel === ".btn-icon:disabled");
    expect(disabled, ".btn-icon:disabled chưa được khai").toBeDefined();
    expect(disabled!.body).toMatch(/opacity:\s*1/);
  });
});

/**
 * PHÍM TẮT TOÀN CỤC KHÔNG ĐƯỢC CƯỚP PHÍM CỦA CONTROL ĐANG FOCUS.
 *
 * Đã cháy ở lượt nghiệm thu Chrome: bấm Space trên node đầu vào A/B/C của
 * boolean_dag vừa đổi giá trị đầu vào (đúng ý), VỪA bật "Tự chạy" (Space là
 * phím tắt play/pause toàn cục) — timeline chạy mất, và vì đang chạy nên node
 * bị khoá ngay sau đó, không bấm tiếp được. Một lần bấm, hai hành động.
 *
 * Guard này quét mã nguồn vì hành vi nằm ở listener trên `window`, không hiện
 * ra HTML nên SSR không thấy; kiểm tra động nằm ở `dag-acceptance.json`.
 */
describe("phím tắt toàn cục nhường control đang focus", () => {
  const controls = FILES.find((f) => /SimulationControls\.tsx$/.test(f.path))!;

  /* W1 MỞ RỘNG: guard cũ chỉ kể `[role="button"]` vì nó được viết cho đúng ca
     boolean_dag. Nút đáp án của PredictionBar là `<button>` THẬT nên lọt qua —
     đo trong Chrome thấy Space làm `playing = true` và câu trả lời mất trắng.
     Nay guard kể theo NĂNG LỰC "tự xử lý Enter/Space": control gốc lẫn control
     giả đều phải được nhường phím. */
  it("handler phím tắt bỏ qua sự kiện phát từ trong control tự xử lý phím", () => {
    const body = code(controls.text);
    const guard = /closest\??\.\(\s*'([^']+)'\s*\)/.exec(body)?.[1] ?? "";
    expect(guard).toContain('[role="button"]');
    // native <button> phải có tên riêng — đây là ca đã lọt ở W1
    expect(guard).toMatch(/(^|,\s*)button(\s*,|$)/);
  });

  it("vẫn giữ luật cũ: bỏ qua khi đang gõ trong ô nhập", () => {
    const body = code(controls.text);
    expect(body).toContain("HTMLTextAreaElement");
    expect(body).toContain("HTMLInputElement");
  });
});

/**
 * FIX-1 — THANH ĐIỀU KHIỂN PHẢI Ở TRONG MÀN HÌNH Ở MÀN HẸP.
 *
 * Đo được trước bản vá (768×900): khi ô dự đoán hiện ra, `bubble_sort` đẩy thanh
 * điều khiển xuống 99px DƯỚI nếp gấp và `protocol_encapsulation` 21px ở bước 5 —
 * click vào toạ độ nút KHÔNG ăn, cuộn xuống rồi click LẠI ăn. Đây là guard tĩnh
 * cho luật đó; bằng chứng động là ảnh + `narrow-controls-probe.json`.
 */
describe("(FIX-1) màn hẹp: thanh điều khiển dán đáy, drawer không đè lên", () => {
  const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");
  const narrow = /@media \(max-width: 1100px\) \{([\s\S]*?)\n\}/.exec(css)?.[1] ?? "";

  it("panel-controls là sticky bottom trong media query màn hẹp", () => {
    const rule = /\.panel-controls \{([^}]*)\}/.exec(narrow)?.[1] ?? "";
    expect(rule, ".panel-controls chưa được ghim ở màn hẹp").toMatch(/position:\s*sticky/);
    expect(rule).toMatch(/bottom:\s*0/);
  });

  it("z-index thanh điều khiển CAO HƠN drawer Giải thích", () => {
    const controlsZ = Number(/\.panel-controls \{[^}]*z-index:\s*(\d+)/.exec(narrow)?.[1] ?? 0);
    const drawerZ = Number(/\.panel-right \{[^}]*z-index:\s*(\d+)/.exec(narrow)?.[1] ?? 0);
    expect(controlsZ).toBeGreaterThan(drawerZ);
  });
});

/**
 * W4B-2B §7 — PANEL PHẢI TÊN LÀ "GIẢI THÍCH", KHÔNG PHẢI "QUAN SÁT".
 *
 * Vì sao quét MÃ NGUỒN chứ không quét HTML: panel phải chỉ tồn tại trong
 * workspace, mà SSR qua `App` không bao giờ tới workspace (anti-pattern #8/#13).
 * Một guard render-based ở đây sẽ xanh mà không soi gì cả.
 *
 * RANH GIỚI PHẢI GIỮ — hai chữ "Quan sát" KHÁC NGHĨA trong repo này:
 *
 *  1. tên panel phải (biến/mã giả/bit...) → nay là "Giải thích";
 *  2. chế độ xem của renderer generic, cặp [Quan sát][Chỉnh sửa]
 *     (`generic/ui.tsx`) → GIỮ NGUYÊN. Đổi nó thành "Giải thích" sẽ đẻ ra cặp
 *     vô nghĩa "Giải thích ↔ Chỉnh sửa" và phá `generic/mode-switch.test.tsx`.
 *
 * Vì vậy guard cấm nhãn ở MỌI component TRỪ đúng một file sở hữu nghĩa (2), và
 * khẳng định luôn rằng file đó vẫn còn nhãn — nếu không, allowlist đã thành xác
 * và guard sẽ âm thầm mất hiệu lực.
 */
describe("(W4B-2B §7) nhãn panel phải — đổi tên có ranh giới, không thay chuỗi mù", () => {
  /** Nơi DUY NHẤT "Quan sát" còn hợp lệ: chế độ xem của renderer generic. */
  const MODE_SWITCH_OWNER = join("simulations", "domains", "generic", "ui.tsx");

  /**
   * M18 — GUARD NÓI ĐÚNG THỨ NÓ CANH, THAY VÌ DÀI THÊM DANH SÁCH MIỄN TRỪ.
   *
   * Bản trước cấm chuỗi "Quan sát" ở MỌI component rồi miễn trừ một file. Cách
   * viết đó bắt nhầm ngay khi tầng lớp học ra đời: "Quan sát lớp" (giáo viên
   * xem trạng thái thực hành) chẳng liên quan gì tới panel bên phải, và nếu cứ
   * thêm ngoại lệ thì sau vài wave guard chỉ còn là một danh sách tên file.
   *
   * Bất biến THẬT là hẹp hơn nhiều: **file nào dựng panel bên phải thì không
   * được gọi nó là "Quan sát"**. Nên chỉ soi những file thật sự chạm panel đó.
   * Mọi chỗ khác dùng chữ "quan sát" theo nghĩa tiếng Việt bình thường là
   * chuyện của chúng.
   */
  const RIGHT_PANEL_MARKERS = ["panel-right", "rightOpen", "toggleRight", "SimulationInspector"];

  it("file nào dựng panel phải thì KHÔNG được gọi nó là Quan sát/QUAN SÁT", () => {
    const offenders: string[] = [];
    let inspected = 0;
    for (const f of FILES) {
      if (f.path.endsWith(MODE_SWITCH_OWNER)) continue;
      const body = code(f.text); // chú thích lịch sử được phép nhắc tên cũ
      if (!RIGHT_PANEL_MARKERS.some((m) => body.includes(m))) continue;
      inspected += 1;
      for (const needle of ["Quan sát", "QUAN SÁT"]) {
        if (body.includes(needle)) offenders.push(`${f.path}: nhãn "${needle}"`);
      }
    }
    /* Sàn chống guard-rỗng: nếu một ngày không file nào khớp dấu hiệu nữa thì
       guard đã ngừng soi gì cả mà vẫn xanh. */
    expect(inspected, "không file nào chạm panel phải — dấu hiệu đã lỗi thời?")
      .toBeGreaterThan(1);
    expect(
      offenders,
      `panel phải nay tên "Giải thích" (W4B-2B §7):\n${offenders.join("\n")}`,
    ).toEqual([]);
  });

  it("bảng quan sát lớp KHÔNG đụng panel phải — hai bề mặt khác nhau", () => {
    /* Đối chứng cho guard ngay trên: nếu `ObserveView` một ngày dựng panel bên
       phải thì nó rơi vào tầm soi và chữ "Quan sát lớp" của nó thành vi phạm.
       Bài này khoá ranh giới đó lại cho rõ. */
    const owner = FILES.find((f) => f.path.endsWith(join("components", "ObserveView.tsx")));
    expect(owner, "không tìm thấy ObserveView.tsx").toBeDefined();
    const body = code(owner!.text);
    expect(body).toContain("Quan sát lớp");
    for (const marker of RIGHT_PANEL_MARKERS) {
      expect(body, `ObserveView đụng vào panel phải qua "${marker}"`).not.toContain(marker);
    }
  });

  it("renderer generic KHÔNG còn bày cặp tab [Quan sát][Chỉnh sửa] cho học sinh", () => {
    /* W12 — ĐẢO CHIỀU CÓ CHỦ ĐÍCH. Bài này trước đây khoá SỰ TỒN TẠI của cặp
       tab; nay nó khoá SỰ VẮNG MẶT, vì cặp tab ấy sai bản chất sản phẩm:

         · chỗ học sinh thao tác thật lại mang nhãn "Quan sát" — đúng cái từ
           bảo các em chỉ được nhìn;
         · "Chỉnh sửa" TẮT tương tác học tập để bật công cụ sửa ĐẶC TẢ (thêm
           nút, nối, xoá) — việc soạn bài, không phải việc học.

       Năng lực sửa đặc tả KHÔNG bị gỡ (`editMode` vẫn còn, mặc định `false`),
       chỉ thôi có cửa trên bề mặt người học. Guard soi MÃ NGUỒN nên nó bắt được
       cả trường hợp ai đó dựng lại cặp nút bằng chuỗi khác cách viết. */
    /* ⚠️ Chủ sở hữu cũ (`domains/generic/ui.tsx`) đã gỡ cùng chín domain Tin
       học, nên phép dò không còn một tệp cụ thể để soi. Luật thì rộng hơn một
       tệp và vẫn đáng giữ: cặp tab ấy không được quay lại ở BẤT KỲ đâu trên bề
       mặt học sinh. Nên quét TOÀN BỘ `src` thay vì một chủ sở hữu — phạm vi
       rộng ra, không hẹp đi. */
    /* ⚠️ Phạm vi là RENDERER MÔ PHỎNG, không phải cả `src`. Bản quét-tất-cả bắt
       nhầm `ClassesView.tsx`: "Quan sát" ở đó là tên một tính năng LỚP HỌC
       (giáo viên theo dõi tiến độ), không phải nửa của cặp tab chế độ. Cùng
       một chuỗi, hai nghĩa — và một guard không phân biệt được thì nó đang
       cấm một từ, không phải cấm một hành vi. */
    const renderers = FILES.filter((f) => f.path.includes(join("simulations", "domains")));
    expect(renderers.length, "không tìm thấy renderer nào — phép dò hỏng?")
      .toBeGreaterThan(0);
    for (const f of renderers) {
      const body = code(f.text);
      expect(body, `${f.path}: cặp tab chế độ đã quay lại bề mặt học sinh`)
        .not.toMatch(/>\s*Chỉnh sửa\s*</);
      expect(body, `${f.path}: cặp tab chế độ đã quay lại bề mặt học sinh`)
        .not.toMatch(/>\s*Quan sát\s*</);
    }
  });

  it("panel phải tự xưng là GIẢI THÍCH ở đúng component sở hữu nó", () => {
    const inspector = FILES.find((f) => f.path.endsWith(join("components", "SimulationInspector.tsx")));
    expect(inspector).toBeDefined();
    expect(code(inspector!.text)).toContain("GIẢI THÍCH");
  });
});
