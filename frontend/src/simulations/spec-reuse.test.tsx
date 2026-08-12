import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { getSimulation, registerAllSimulations } from "./index";
import { rendererFor, availableVisualModes } from "./renderer";
import type { SimulationEnvelope } from "./types";

registerAllSimulations();

/**
 * W4B-2V §2/§17/§30 — HỢP ĐỒNG TÁI DỤNG SPEC.
 *
 * Luận điểm của đề tài là "LLM đọc đề, engine tất định diễn hoạt". Nó chỉ đứng
 * vững nếu **ngữ cảnh ngôn ngữ tự nhiên KHÔNG sinh ra mã UI mới**:
 *
 *   ngữ cảnh khác nhau + CÙNG cơ chế tính toán
 *     = cùng target · cùng engine · cùng chủ sở hữu biểu diễn
 *     ≠ dữ liệu, ≠ nhãn ngữ nghĩa.
 *
 * Nếu "tìm điểm 8,5 trong sổ điểm" và "tìm số báo danh 189 trong danh sách" cần
 * HAI renderer viết tay, thì hệ này không phải một hệ mô phỏng tái dụng được —
 * nó là một tập bài minh hoạt được đặt hàng riêng. Đó là ranh giới đáng test,
 * và trước wave này chưa test nào phát biểu nó.
 *
 * PHÉP SO LÀ SỞ HỮU, KHÔNG PHẢI PIXEL (§30). Test này KHÔNG so ảnh chụp: hai
 * ngữ cảnh PHẢI vẽ khác nhau (nhãn khác, số khác). Thứ phải giống là *ai sở hữu
 * cái gì*: cùng module, cùng component renderer, cùng hình dạng sự kiện engine.
 */

/** Dựng envelope cho cùng một target với ngữ cảnh khác nhau. */
function envelope(
  simulationId: string,
  algorithmId: string,
  summary: string,
  data: Record<string, unknown>,
): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: simulationId,
    domain: "algorithm",
    visual_mode: "2d",
    title: summary,
    description: null,
    notes: null,
    config: {
      problem: { summary, input: "i", output: "o" },
      algorithm_id: algorithmId,
      data,
      data_generated: false,
      notes: null,
    },
  } as SimulationEnvelope;
}

/** Chuỗi KIỂU sự kiện của toàn timeline — dấu vân tay của cơ chế, không của dữ liệu. */
function mechanismShape(simulationId: string, env: SimulationEnvelope): string[] {
  const mod = getSimulation(simulationId)!;
  const r = mod.validateConfig(env.config);
  if (!r.ok) throw new Error(`${simulationId}: ${r.error}`);
  const state = mod.init(r.config) as { trace: { steps: { events: { type: string }[] }[] } };
  return state.trace.steps.map((s) => s.events.map((e) => e.type).join("+"));
}

interface ReuseCase {
  simulationId: string;
  algorithmId: string;
  /** Hai ngữ cảnh KHÁC NHAU của cùng một cơ chế. */
  contexts: { summary: string; data: Record<string, unknown> }[];
}

const CASES: ReuseCase[] = [
  {
    simulationId: "algorithm.binary_search",
    algorithmId: "binary_search",
    contexts: [
      {
        summary: "Tìm điểm 8,5 trong sổ điểm đã sắp thứ tự tăng dần",
        data: { array: [4, 5.5, 6, 6.5, 7, 8, 8.5, 9, 9.5, 10], target: 8.5 },
      },
      {
        summary: "Tìm số báo danh 189 trong danh sách đã sắp thứ tự tăng dần",
        data: { array: [101, 118, 133, 147, 162, 175, 189, 204, 218, 230], target: 189 },
      },
    ],
  },
  {
    simulationId: "algorithm.count_if",
    algorithmId: "count_if",
    contexts: [
      {
        summary: "Đếm số học sinh đạt điểm trung bình môn từ 8,0 trở lên",
        data: { array: [8.2, 6.5, 9.1, 7.8, 8, 5.9], condition: { op: ">=", value: 8 } },
      },
      {
        /* Phần tử THOẢ phải nằm ở CÙNG VỊ TRÍ với ngữ cảnh trên (0, 2, 4). Bản
           fixture đầu xếp chúng ở 1, 3, 5 và test đỏ ngay — đúng ý đồ: nếu vị
           trí lệch thì hai lượt đi hai đường thực thi khác nhau và phép so
           "cùng cơ chế" mất nghĩa. Test bắt được fixture sai của chính nó. */
        summary: "Đếm số ngày có nhiệt độ từ 35 độ trở lên trong tuần",
        data: { array: [36, 31, 38, 33, 37, 34], condition: { op: ">=", value: 35 } },
      },
    ],
  },
  {
    simulationId: "algorithm.find_max",
    algorithmId: "find_max",
    contexts: [
      {
        summary: "Tìm học sinh có điểm kiểm tra cao nhất trong tổ",
        data: { array: [7.5, 9, 6.5, 8], labels: ["An", "Bình", "Chi", "Dũng"] },
      },
      {
        summary: "Tìm ngày có lượng mưa lớn nhất trong tuần",
        data: { array: [12, 40, 8, 25], labels: ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5"] },
      },
    ],
  },
];

describe("W4B-2V §30 · cùng cơ chế + ngữ cảnh khác ⇒ cùng chủ sở hữu, khác dữ liệu", () => {
  it("mỗi ngữ cảnh đều validate được — không ngữ cảnh nào cần schema riêng", () => {
    for (const c of CASES) {
      const mod = getSimulation(c.simulationId);
      expect(mod, `${c.simulationId} chưa đăng ký`).toBeTruthy();
      for (const ctx of c.contexts) {
        const r = mod!.validateConfig(envelope(c.simulationId, c.algorithmId, ctx.summary, ctx.data).config);
        expect(r.ok, `${c.simulationId} / "${ctx.summary}": ${r.ok ? "" : r.error}`).toBe(true);
      }
    }
  });

  it("hai ngữ cảnh dùng ĐÚNG MỘT module và ĐÚNG MỘT component renderer", () => {
    for (const c of CASES) {
      const mod = getSimulation(c.simulationId)!;
      /* Đây là mấu chốt: renderer được tra qua `rendererFor(module, mode)` —
         dẫn xuất từ HỢP ĐỒNG MODULE, không phải từ tiêu đề/ngữ cảnh. Nên hai đề
         khác nhau nhận về CÙNG một tham chiếu component. Nếu một ngày có ai đó
         phân nhánh renderer theo nội dung đề, đẳng thức tham chiếu này vỡ. */
      const a = rendererFor(mod, "2d");
      const b = rendererFor(mod, "2d");
      expect(a, `${c.simulationId}: không có renderer 2D`).toBeTruthy();
      expect(a).toBe(b);
      expect(availableVisualModes(mod).length).toBeGreaterThan(0);
    }
  });

  it("cơ chế GIỮ NGUYÊN qua ngữ cảnh: cùng chuỗi kiểu sự kiện", () => {
    for (const c of CASES) {
      const shapes = c.contexts.map((ctx) =>
        mechanismShape(c.simulationId, envelope(c.simulationId, c.algorithmId, ctx.summary, ctx.data)));
      /* Dữ liệu được chọn để hai ngữ cảnh đi CÙNG một đường thực thi (cùng độ
         dài dãy, đích ở cùng vị trí, cùng số phần tử thoả điều kiện). Nhờ vậy
         chuỗi kiểu sự kiện phải trùng khít — nếu lệch thì hoặc engine đang nhìn
         vào ngữ cảnh, hoặc fixture đã trôi khỏi ý định của nó. */
      expect(shapes[0], `${c.simulationId}: cơ chế đổi theo ngữ cảnh`).toEqual(shapes[1]);
      expect(shapes[0].length, `${c.simulationId}: timeline rỗng`).toBeGreaterThan(1);
    }
  });

  it("DỮ LIỆU và NHÃN thì phải khác — nếu không, test trên vô nghĩa", () => {
    for (const c of CASES) {
      const [x, y] = c.contexts;
      expect(JSON.stringify(x.data), `${c.simulationId}: hai ngữ cảnh trùng dữ liệu`)
        .not.toBe(JSON.stringify(y.data));
      expect(x.summary).not.toBe(y.summary);
    }
  });

  it("ngữ cảnh CHẢY RA màn hình qua nhãn của spec, không qua mã renderer", () => {
    /* find_max cấp `labels` nên sân khấu phải nói được tên học sinh ở ngữ cảnh
       này và tên thứ trong tuần ở ngữ cảnh kia — CÙNG một component. Đây là vế
       "ngữ cảnh đổi NHÃN ngữ nghĩa" của §17. */
    const c = CASES[2];
    const mod = getSimulation(c.simulationId)!;
    for (const ctx of c.contexts) {
      const env = envelope(c.simulationId, c.algorithmId, ctx.summary, ctx.data);
      const r = mod.validateConfig(env.config);
      if (!r.ok) throw new Error(r.error);
      const state = mod.init(r.config);
      const Workspace = rendererFor(mod, "2d")!;
      const html = renderToString(
        <Workspace config={r.config} state={state} busy={false} dispatch={() => {}} />,
      );
      for (const label of ctx.data.labels as string[]) {
        expect(html, `${ctx.summary}: mất nhãn "${label}"`).toContain(label);
      }
    }
  });
});

/* ── KHÔNG CÓ ĐƯỜNG NÀO CHO LLM SINH UI (§18) ─────────────────────────────── */

describe("W4B-2V §18 · ngữ cảnh không được biến thành mã trình bày", () => {
  it("không renderer nào phân nhánh theo NỘI DUNG đề bài", async () => {
    const { readFileSync, readdirSync, statSync } = await import("node:fs");
    const { join } = await import("node:path");
    /* W4B-3A — QUÉT CẢ SHELL, KHÔNG CHỈ RENDERER MIỀN.
       Bản trước chỉ đi `domains/`, nên một nhánh theo nội dung đề bài đặt trong
       `components/SimulationWorkspace.tsx` (nơi QUYẾT ĐỊNH bày lối vào nào) đi
       lọt trọn vẹn — tiêm lỗi chứng minh được. Shell là chỗ dễ cám dỗ nhất để
       "chỉ rẽ một nhánh nhỏ theo đề bài", nên nó phải nằm trong tầm quét. */
    const roots = ["./domains/", "../components/"].map((r) =>
      new URL(r, import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"),
    );

    const walk = (dir: string, out: string[] = []): string[] => {
      for (const n of readdirSync(dir)) {
        const full = join(dir, n);
        if (statSync(full).isDirectory()) walk(full, out);
        else if (/\.tsx?$/.test(n) && !/\.test\./.test(n)) out.push(full);
      }
      return out;
    };

    /* Bóc chú thích trước khi quét: repo CỐ Ý nhắc thứ đã cấm trong chú thích để
       ghi lại vì sao cấm (cùng khuôn `code()` ở experiment-gate-w4b2b.test.ts). */
    const strip = (t: string) =>
      t.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

    const PATTERNS = [
      /* W4B-3A: `\.` cũ bỏ lọt OPTIONAL CHAINING. Tiêm lỗi
         `config?.problem?.summary?.includes("mạng")` đi lọt trọn vẹn phép dò
      'if ((config.notes ?? "").includes("khoá")) return null;',
         này — guard quét cả kho mã mà trả 0 vì regex hụt, không vì mã sạch.
         Bait bên dưới nay có cả dạng `?.`. */
      /* Đối số phải là HẰNG CHUỖI. Điều §18 cấm là rẽ nhánh theo NỘI DUNG ĐỀ
         BÀI viết cứng trong mã ("nếu đề nhắc 'học sinh' thì vẽ kiểu khác").
         So `title` với một BIẾN thì là chuyện khác hẳn — `LibraryView` lọc danh
         mục theo ô tìm kiếm học sinh gõ, và đó là một tính năng, không phải một
         nhánh trình bày. Guard kêu oan là guard sẽ bị tắt. */
      /* W4B-4C: `notes`/`description` cũng là CHỮ TỰ DO từ đề bài. Tiêm lỗi
         `config.notes.includes("khoá")` để quyết định CÓ CHO TƯƠNG TÁC hay không
         đi lọt trọn vẹn bản chỉ canh summary|title — cùng một lỗi, khác tên trường. */
      /\b(summary|title|notes|description)\b[^\n;]{0,80}\??\.(includes|startsWith|match|test)\s*\(\s*["'`]/g,
      /\balgorithm_id\s*===\s*["']/g,
      /\bsimulation_id\s*===\s*["']/g,
    ];

    /* PHÉP DÒ PHẢI THẬT SỰ DÒ (ARCHITECTURE_MAP §8 #14). Một guard quét cả kho
       mã và trả 0 trông y hệt một guard có regex hỏng. Nên trước khi tin số 0,
       bắt nó nhận diện ba mẫu vi phạm tổng hợp. */
    const BAIT = [
      'if (config.problem.summary.includes("học sinh")) return <StudentBars />;',
      'if (config.algorithm_id === "binary_search") return <SpecialPage />;',
      'if (env.simulation_id === "tree.traversal") { }',
      // W4B-3A — dạng optional chaining, chính là mẫu đã đi lọt bản trước.
      'if (config?.problem?.summary?.includes("mạng")) return null;',
    ];
    for (const bait of BAIT) {
      const hit = PATTERNS.some((re) => { re.lastIndex = 0; return re.test(bait); });
      expect(hit, `phép dò không bắt được mẫu vi phạm: ${bait}`).toBe(true);
    }

    /* MỒI ÂM — thứ phép dò KHÔNG được bắt. Không có vế này thì cách siết dễ
       nhất luôn là siết đến mức bắt cả việc hợp lệ, rồi guard bị tắt. */
    const CLEAN = [
      'e.title.toLowerCase().includes(q)',            // lọc danh mục theo ô tìm kiếm
      'DOMAIN_LABEL[e.domain].toLowerCase().includes(q)',
    ];
    for (const ok of CLEAN) {
      const hit = PATTERNS.some((re) => { re.lastIndex = 0; return re.test(ok); });
      expect(hit, `phép dò kêu oan trên mã hợp lệ: ${ok}`).toBe(false);
    }

    const offenders: string[] = [];
    for (const f of roots.flatMap((r) => walk(r))) {
      const src = strip(readFileSync(f, "utf-8"));
      /* Đọc `problem.summary` / `title` rồi RẼ NHÁNH theo nội dung của nó là
         đúng thứ §17 gọi là "mã hoá ngữ cảnh thành logic renderer". Đọc để
         HIỂN THỊ thì không sao — nên chỉ bắt các phép so khớp nội dung. */
      for (const re of PATTERNS) {
        re.lastIndex = 0;
        for (const m of src.matchAll(re)) {
          offenders.push(`${f.split(/[\\/]/).slice(-2).join("/")}: ${m[0].trim()}`);
        }
      }
    }
    expect(
      offenders,
      "Renderer đang quyết định theo NGỮ CẢNH/ĐỊNH DANH thay vì theo capability:\n" +
        offenders.join("\n"),
    ).toEqual([]);
  });
});
