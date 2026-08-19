import { chromium } from "playwright";
import * as fs from "fs";
import * as path from "path";

const ARTIFACT_DIR = "C:/Users/Bunny/.gemini/antigravity-ide/brain/1b410171-c038-4e7f-ae93-ef8434b82ce0";

const VIEWPORTS = [
  { name: "desktop_1920x1080", width: 1920, height: 1080 },
  { name: "laptop_1536x864", width: 1536, height: 864 },
  { name: "school_1366x768", width: 1366, height: 768 },
  { name: "tablet_768x900", width: 768, height: 900 },
];

const STACK_BRACKET_SPEC = {
  dsl_version: "1.0",
  title: "Kiểm tra chuỗi ngoặc hợp lệ bằng Ngăn xếp (Stack)",
  objects: [
    {
      id: "bracket_strip",
      type: "array_strip",
      label: "Chuỗi ngoặc đầu vào",
      items: ["{", "[", "(", ")", "]", "}"],
    },
    {
      id: "stack_view",
      type: "stack_view",
      label: "Ngăn xếp",
      items: ["{", "["],
      capacity: 6,
    },
    {
      id: "curr_char",
      type: "value_box",
      label: "Ký tự hiện tại",
      value: "(",
    },
    {
      id: "result_box",
      type: "value_box",
      label: "Kết quả",
      value: "HỢP LỆ",
    },
    {
      id: "ptr_i",
      type: "pointer",
      label: "i",
      target: "bracket_strip",
      target_index: 2,
    },
  ],
  rules: [],
  interactions: [],
  processes: [
    {
      type: "step_sequence",
      steps: [
        {
          action: "inspect",
          targets: ["bracket_strip"],
          pointer_id: "ptr_i",
          to_index: 0,
          narration: "Xét ký tự đầu tiên '{': Là dấu mở ngoặc, đẩy vào Ngăn xếp.",
        },
        {
          action: "push",
          targets: ["stack_view"],
          pointer_id: "ptr_i",
          to_index: 1,
          narration: "Xét ký tự tiếp theo '[': Là dấu mở ngoặc, tiếp tục đẩy vào Ngăn xếp.",
        },
        {
          action: "push",
          targets: ["stack_view"],
          pointer_id: "ptr_i",
          to_index: 2,
          narration: "Xét ký tự '(': Là dấu mở ngoặc, đẩy vào Ngăn xếp.",
        },
        {
          action: "pop",
          targets: ["stack_view"],
          pointer_id: "ptr_i",
          to_index: 3,
          narration: "Xét ký tự ')': Khớp với '(' ở đỉnh Stack! Pop '(' ra khỏi stack.",
        },
        {
          action: "complete",
          targets: ["result_box"],
          narration: "Duyệt hết chuỗi và Stack rỗng: Chuỗi ngoặc hoàn toàn HỢP LỆ!",
        },
      ],
    },
  ],
};

async function run() {
  console.log("Starting Real Browser Playwright Verification...");
  const browser = await chromium.launch({ headless: true });
  const report = {
    browser: "Chromium (Headless)",
    viewports: [],
    checks: {
      data_fidelity: false,
      single_heading: false,
      pointer_anchor: false,
      zero_disallowed_collisions: false,
      narration_parity: false,
    },
  };

  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await page.goto("http://localhost:3000", { waitUntil: "networkidle" });

    // Inject simulation envelope into store
    const envelope = {
      status: "ok",
      simulation_id: "generic.rule_scene",
      domain: "generic",
      visual_mode: "2d",
      title: STACK_BRACKET_SPEC.title,
      description: "Mô phỏng kiểm tra ngoặc",
      config: STACK_BRACKET_SPEC,
      notes: null,
    };

    const loadResult = await page.evaluate((env) => {
      const store = window.__ALGO_SIM_STORE__;
      if (!store) return { ok: false, error: "No __ALGO_SIM_STORE__ found" };
      store.getState().loadEnvelope(env);
      const state = store.getState();
      return {
        ok: true,
        view: state.view,
        active: !!state.active,
        analysisError: state.analysisError,
      };
    }, envelope);

    console.log(`[${vp.name}] Load result:`, loadResult);
    await page.waitForTimeout(1000);

    // Take screenshot
    const screenshotPath = path.join(ARTIFACT_DIR, `stack_bracket_render_${vp.name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Saved screenshot for ${vp.name} -> ${screenshotPath}`);

    // DOM & bounding client rect inspection
    const domInspection = await page.evaluate(() => {
      const texts = Array.from(document.querySelectorAll("text, span, strong, p, h1, h2, h3, div"))
        .map((el) => el.textContent?.trim() || "")
        .filter(Boolean);

      const svg = document.querySelector("svg.generic-canvas, svg[viewBox], svg");
      let svgRect = null;
      let elements = [];

      if (svg) {
        svgRect = svg.getBoundingClientRect();
        const nodes = svg.querySelectorAll("g, rect, text, path");
        nodes.forEach((node) => {
          const r = node.getBoundingClientRect();
          if (r.width > 0 && r.height > 0) {
            elements.push({
              tag: node.tagName,
              text: node.textContent?.trim(),
              left: r.left,
              top: r.top,
              right: r.right,
              bottom: r.bottom,
              width: r.width,
              height: r.height,
            });
          }
        });
      }

      return {
        allTexts: texts,
        svgRect: svgRect ? { width: svgRect.width, height: svgRect.height, top: svgRect.top, left: svgRect.left } : null,
        elementsCount: elements.length,
      };
    });

    report.viewports.push({
      viewport: vp.name,
      width: vp.width,
      height: vp.height,
      screenshot: screenshotPath,
      domInspection,
    });

    await page.close();
  }

  await browser.close();
  console.log("Real browser inspection finished successfully.");
  fs.writeFileSync(
    path.join(ARTIFACT_DIR, "real_browser_render_report.json"),
    JSON.stringify(report, null, 2),
    "utf-8"
  );
}

run().catch((err) => {
  console.error("Browser verification failed:", err);
  process.exit(1);
});
