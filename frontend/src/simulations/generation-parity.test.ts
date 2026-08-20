import { beforeAll, describe, expect, it } from "vitest";
import { mkdirSync, writeFileSync } from "node:fs";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { availableVisualModes, rendererFor } from "./renderer";
import { publicCatalog } from "../data/offline-catalog";
import { provenance } from "../../scripts/evidence.mjs";
import type { SimAction, SimulationModule } from "./types";

/**
 * WAVE 1 — MÔ PHỎNG MẪU VÀ MÔ PHỎNG DO AI SINH LÀ **CÙNG MỘT SẢN PHẨM**.
 *
 * ─── CÂU HỎI PHẢI TRẢ LỜI ─────────────────────────────────────────────────
 *
 * "Sửa một renderer bằng bài mẫu trong thư viện thì một mô phỏng AI vừa sinh có
 * được hưởng bản sửa đó không?"
 *
 * Nếu câu trả lời là "không chắc" thì mọi bản sửa giao diện đều chỉ là sửa
 * DEMO, và sản phẩm thật của học sinh (đề các em tự gõ) không được gì.
 *
 * ─── KIẾN TRÚC ĐANG CÓ (đã kiểm, không phải giả định) ─────────────────────
 *
 * `store.loadEnvelope` giải module bằng ĐÚNG `env.simulation_id`, và không một
 * file production nào rẽ nhánh theo nguồn của envelope. Bài kiểm này KHOÁ điều
 * đó lại, vì nó là thứ dễ mất nhất: chỉ cần một `if (sampleId)` là bài mẫu và
 * bài AI thành hai đường.
 *
 * ─── FIXTURE "AI" LÀ GÌ ───────────────────────────────────────────────────
 *
 * Repo KHÔNG lưu envelope AI thật (chúng nằm trong cache DB, bị gitignore), nên
 * fixture ở đây được dựng theo ĐÚNG hình dạng pipeline phát ra — bốn giá trị
 * `source` có thật trong `ai/pipeline.py` + `main.py`: `composed`,
 * `family_resolved`, `pattern_reuse`, `exact_cache`, kèm `cached` và tiêu đề do
 * AI tự viết. Đây là giới hạn đã biết và được khai: bài kiểm chứng minh **nguồn
 * không chọn đường đi**, nó không chứng minh chất lượng spec AI (việc đó thuộc
 * benchmark chương trình học).
 */

const PIPELINE_SOURCES = ["composed", "family_resolved", "pattern_reuse", "exact_cache"] as const;

/**
 * Bộ action thăm dò CỐ ĐỊNH.
 *
 * ⚠️ Cột "từ vựng action" trong ma trận là **CẬN DƯỚI**, không phải danh sách
 * đầy đủ: bộ này không mang hình dạng riêng của từng miền (vd `character_encoding`
 * cần `set_param name:"text"`, `boolean_dag` cần `toggle` theo id đầu vào thật),
 * nên vài target hiện 0 dù chúng thao tác được — phép đo trải nghiệm
 * (`experience-audit-w4b4a`) mới là nơi đếm đủ.
 *
 * Điều đó KHÔNG làm yếu khẳng định của Wave 1: parity so mẫu với AI bằng CÙNG
 * một bộ thăm dò, nên hai bên phải cho cùng kết quả dù bộ ấy hẹp.
 */
const PROBES: SimAction[] = [
  { type: "whatif_swap", i: 0, j: 1 },
  { type: "exit_branch" },
  { type: "toggle", target: "A" },
  { type: "toggle", target: "0" },
  { type: "toggle", target: "reset" },
  { type: "set_param", name: "variant", value: "dfs" },
  { type: "set_param", name: "targetBase", value: 8 },
  { type: "set_param", name: "fontSize", value: 32 },
  { type: "set_param", name: "sort.direction", value: "asc" },
  { type: "set_param", name: "condition.op", value: "<" },
  { type: "set_param", name: "selected", value: "heading" },
  /* W5 §5 — ba kênh màu phải nằm trong hợp đồng PRODUCTION, không phải state
     riêng của bài mẫu. Nếu ai đó dựng RGB bằng useState trong renderer thì mẫu
     đổi được còn spec AI sinh thì không, và parity ở đây sẽ đỏ. */
  { type: "set_param", name: "r", value: 255 },
  { type: "set_param", name: "g", value: 128 },
  { type: "set_param", name: "b", value: 0 },
  /* Ba tham số đổi cơ số + đầu vào mã hoá — cùng lý do. */
  { type: "set_param", name: "sourceBase", value: 2 },
  { type: "set_param", name: "targetBase", value: 16 },
  { type: "set_param", name: "text", value: "Tin" },
  { type: "move", target: "heading", x: 0, y: 1 },
  { type: "net_reset" },
];

/** Action nào ĐỔI được state — chữ ký từ vựng tương tác của một target. */
function actionVocabulary(mod: SimulationModule, state: unknown): string[] {
  const out: string[] = [];
  for (const a of PROBES) {
    try {
      if (mod.apply(state, a) !== state) out.push(JSON.stringify(a));
    } catch { /* fail-closed = không nhận */ }
  }
  return out;
}

interface Row {
  target: string;
  domain: string;
  sampleId: string;
  validator: string;
  moduleId: string;
  renderer2d: string;
  visualModes: string;
  interactionMode: string;
  hasTimeline: boolean;
  hasExplore: boolean;
  actionVocabulary: string[];
  aiSourcesChecked: number;
  parity: "OK" | "LỆCH";
}

const rows: Row[] = [];

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();
});

describe("WAVE 1 · bài mẫu và bài AI giải ra CÙNG một module/renderer", () => {
  it("mọi target công khai: nguồn envelope KHÔNG đổi module, renderer hay từ vựng action", () => {
    const seen = new Set<string>();
    for (const entry of publicCatalog()) {
      if (seen.has(entry.simId)) continue;
      seen.add(entry.simId);

      const mod = getSimulation(entry.simId) as SimulationModule | undefined;
      expect(mod, `${entry.simId}: registry không có module`).toBeDefined();
      if (!mod) continue;

      const sampleEnv = entry.envelope as unknown as Record<string, unknown>;
      const baseline = mod.validateConfig(sampleEnv.config);
      expect(baseline.ok, `${entry.simId}: mẫu công khai không qua validateConfig`).toBe(true);
      if (!baseline.ok) continue;

      const sampleState = mod.init(baseline.config);
      const sampleVocab = actionVocabulary(mod, sampleState);
      const sampleRenderer = rendererFor(mod, "2d");

      let parity: Row["parity"] = "OK";
      for (const source of PIPELINE_SOURCES) {
        /* Envelope hình dạng PIPELINE: cùng target + cùng config đã validate,
           nhưng tiêu đề/mô tả do AI viết và mang cờ nguồn. */
        const aiEnv = {
          status: "ok",
          simulation_id: entry.simId,
          domain: sampleEnv.domain,
          visual_mode: sampleEnv.visual_mode,
          title: "Đề do học sinh tự gõ (bản AI sinh)",
          description: "mô tả do mô hình viết",
          config: sampleEnv.config,
          notes: null,
          source,
          cached: source === "exact_cache",
        };

        const aiMod = getSimulation(String(aiEnv.simulation_id));
        expect(aiMod, `${entry.simId}/${source}: không giải được module`).toBe(mod);

        const aiValid = mod.validateConfig(aiEnv.config);
        expect(aiValid.ok, `${entry.simId}/${source}: config không qua validate`).toBe(true);
        if (!aiValid.ok) { parity = "LỆCH"; continue; }
        expect(aiValid.config, `${entry.simId}/${source}: config chuẩn hoá lệch`)
          .toEqual(baseline.config);

        expect(rendererFor(mod, "2d"), `${entry.simId}/${source}: renderer khác`)
          .toBe(sampleRenderer);
        expect(availableVisualModes(mod), `${entry.simId}/${source}: mode khác`)
          .toEqual(availableVisualModes(mod));

        const aiVocab = actionVocabulary(mod, mod.init(aiValid.config));
        expect(aiVocab, `${entry.simId}/${source}: từ vựng action khác`).toEqual(sampleVocab);
      }

      rows.push({
        target: entry.simId,
        domain: mod.domain,
        sampleId: entry.id,
        validator: `${entry.simId}::validateConfig`,
        moduleId: mod.id,
        renderer2d: (sampleRenderer as { name?: string })?.name ?? "(ẩn danh)",
        visualModes: availableVisualModes(mod).join("/"),
        interactionMode: mod.interactionMode,
        hasTimeline: !!mod.timeline,
        hasExplore: !!mod.explore,
        actionVocabulary: sampleVocab,
        aiSourcesChecked: PIPELINE_SOURCES.length,
        parity,
      });
    }

    expect(rows.length, "không target công khai nào được kiểm").toBeGreaterThan(10);
    expect(rows.filter((r) => r.parity !== "OK").map((r) => r.target)).toEqual([]);
  });

  it("KHÔNG file production nào rẽ nhánh theo NGUỒN của envelope", () => {
    /* Đây là vế 5 của Wave 1: "source = sample/library/AI không chọn một đường
       UI riêng". Quét mã nguồn vì đây là luật KIẾN TRÚC — một nhánh như thế có
       thể thêm vào bất cứ lúc nào và không test hành vi nào bắt được ngay. */
    const SRC = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
    const files: string[] = [];
    (function walk(dir: string) {
      for (const name of readdirSync(dir)) {
        const full = join(dir, name);
        if (statSync(full).isDirectory()) walk(full);
        else if (/\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name)) files.push(full);
      }
    })(SRC);

    const offenders: string[] = [];
    for (const f of files) {
      const body = readFileSync(f, "utf-8")
        .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
      /* `envelope.source` / `env.source` / `.cached` dùng để RẼ NHÁNH. Domain
         `network` có `config.source` (nút nguồn của tuyến) — khác hẳn, nên chỉ
         bắt khi nó đi cùng `envelope`/`env`. */
      if (/\b(envelope|env)\s*\.\s*source\b/.test(body)) offenders.push(`${f}: đọc envelope.source`);
      if (/\b(envelope|env)\s*\.\s*cached\b/.test(body)) offenders.push(`${f}: đọc envelope.cached`);
      if (/if\s*\([^)]*\bsampleId\b[^)]*\)/.test(body)) offenders.push(`${f}: rẽ nhánh theo sampleId`);
    }
    expect(offenders, `nguồn spec KHÔNG được chọn đường đi:\n${offenders.join("\n")}`).toEqual([]);
  });

  it("ma trận hợp đồng SINH RA cho mọi target công khai", () => {
    expect(rows.length).toBeGreaterThan(10);
    try {
      const dir = new URL("../../../docs/evaluation/m20/", import.meta.url)
        .pathname.replace(/^\/([A-Za-z]:)/, "$1");
      mkdirSync(dir, { recursive: true });
      /* W12 §8 — XUẤT XỨ, VÀ DANH TÍNH, KHÔNG CHỈ MỘT CON SỐ.
         Bản trước chỉ có `generatedAt` nên artifact này nằm ngoài mọi cổng
         provenance — và một báo cáo đã mang theo hai con số
         `PRIMARY_CAPABILITY_PARITY_CERTIFIED = 10/23` /
         `UNVERIFIED = 13/23` mà KHÔNG file nào trong kho sinh ra. Cách chữa
         không phải dựng lại 23 fixture để cứu con số, mà là nói rõ cổng NÀY
         chứng minh trục nào, trên những target NÀO. */
      writeFileSync(join(dir, "generation-parity.json"),
        JSON.stringify({ ...provenance("generation-parity.test", { targets: rows.length }),
          axis: "GENERATION_PARITY — nguồn spec (mẫu vs AI) KHÔNG chọn đường đi",
          notThisAxis: "KHÔNG phải PRIMARY_CAPABILITY_PARITY: cổng này không xếp hạng " +
                "năng lực từng target, nên đừng đọc nó thành 'x/23 target đã chứng nhận'.",
          certifiedTargets: rows.map((r) => r.target).sort(),
          certifiedCount: rows.length,
          pipelineSources: PIPELINE_SOURCES, rows }, null, 2), "utf-8");
    } catch { /* thư mục chỉ-đọc trong CI — bảng vẫn kiểm được */ }
  });
});
