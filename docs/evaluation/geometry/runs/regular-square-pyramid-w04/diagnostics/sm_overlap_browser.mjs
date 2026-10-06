/**
 * regular-square-pyramid-w04 · yêu cầu 4 — quan sát THẬT trong trình duyệt ca SM (M trung điểm SA), 0 lượt gọi model.
 *
 * Mở fixture qua đúng biên mạng của sản phẩm (`openFixture`) trên `dist/` đã dựng, tới bước cuối, rồi ghi:
 *   - vật được dựng lên khung (`__geo3d_rendered_object_ids`), cạnh có hơn một visual owner
 *     (`__geo3d_duplicate_visual_owner_ids`), đoạn nào vẽ NÉT RIÊNG (`__geo3d_segment_strokes`, khi bản dựng có móc này);
 *   - ảnh khung cuối và ảnh cắt sát vùng cạnh SA; chọn SM qua ngăn «Thành phần» rồi chụp lại.
 *
 * usage (từ frontend/): node <this> --dist <dist dir> --fixture <json> --anh <thư mục ảnh> --ra <json kết quả>
 */
import { writeFileSync, mkdirSync, readFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]]);
  return a;
}, []));
const FE = resolve(process.cwd());
const { phucVu } = await import(pathToFileURL(join(FE, "scripts/scene3d-orbit-gate.mjs")).href);
const { capture, openFixture, trustedClick } = await import(pathToFileURL(join(FE, "scripts/compiler-scene-suite.mjs")).href);
const { pollUntil } = await import(pathToFileURL(join(FE, "scripts/compiler-scene-replay-lib.mjs")).href);

const ra = resolve(CO.ra);
if (existsSync(ra)) throw new Error(`refusing to overwrite ${ra}`);
const anh = resolve(CO.anh);
mkdirSync(anh, { recursive: true });
const fixture = JSON.parse(readFileSync(resolve(CO.fixture), "utf8"));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));

const { sv, cong } = await phucVu(resolve(CO.dist));
const { session: s } = await openFixture({ port: cong, viewport: { width: 1440, height: 900 }, fixture });
const out = { fixture: CO.fixture, dist: CO.dist, application_llm_calls: 0 };
try {
  await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
  // tới bước cuối bằng nút "Bước sau"
  for (let i = 0; i < 30; i += 1) {
    const tat = await j(s, "[...document.querySelectorAll('button')].find(b=>(b.textContent||'').includes('Bước sau'))?.disabled??true");
    if (tat) break;
    await trustedClick(s, "[...document.querySelectorAll('button')].find(b=>(b.textContent||'').includes('Bước sau'))");
    await sleep(250);
  }
  await sleep(900);
  const doc = async () => ({
    step: await j(s, "(document.querySelector('.geo3d-buoc-so')?.textContent||'').trim()"),
    rendered: await j(s, "(window.__geo3d_rendered_object_ids||[]).slice().sort()"),
    duplicate_visual_owner_ids: await j(s, "(window.__geo3d_duplicate_visual_owner_ids||[]).slice()"),
    segment_strokes: await j(s, "window.__geo3d_segment_strokes??null"),
    highlighted_render_owner_ids: await j(s, "(window.__geo3d_highlighted_render_owner_ids||[]).slice()"),
    selected: await j(s, "window.__geo3d_selected_id||null"),
  });
  out.neutral = await doc();
  out.neutral.image = await capture(s, join(anh, "sm_neutral.png"));
  // chọn SM qua «Thành phần» (cây): nút mang chữ "SM"
  await trustedClick(s, "[...document.querySelectorAll('.geo3d-thanh-nut .geo3d-chip')].find(b=>(b.textContent||'').includes('Thành phần'))");
  await sleep(500);
  const coSM = await j(s, "[...document.querySelectorAll('.geo3d-tree-item')].some(b=>/\\bSM\\b/.test(b.textContent||''))");
  if (coSM) {
    await trustedClick(s, "[...document.querySelectorAll('.geo3d-tree-item')].find(b=>/\\bSM\\b/.test(b.textContent||''))");
    await sleep(900);
  }
  out.sm_in_tree = coSM;
  out.selected_sm = await doc();
  out.selected_sm.image = await capture(s, join(anh, "sm_selected.png"));
} finally {
  await s.close();
  sv.close();
}
mkdirSync(dirname(ra), { recursive: true });
writeFileSync(ra, `${JSON.stringify(out, null, 2)}\n`);
console.log(JSON.stringify({ neutral: { ...out.neutral, image: undefined }, sm_in_tree: out.sm_in_tree,
  selected: out.selected_sm.selected }, null, 0));
