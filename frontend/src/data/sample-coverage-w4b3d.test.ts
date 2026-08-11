import { beforeAll, describe, expect, it } from "vitest";
import descriptorsJson from "../simulations/capability-descriptors.json";
import { DOMAIN_LABEL, offlineCatalog, publicCatalog } from "./offline-catalog";
import { GROUP_ORDER } from "../components/LibraryView";
import { getSimulation, registerAllSimulations } from "../simulations";
import type { Domain } from "../simulations/types";

/**
 * W4B-3D — MỌI TARGET HỌC-SINH-TỚI-ĐƯỢC ĐỀU PHẢI CÓ MẪU CHẠY ĐƯỢC.
 *
 * ─── VÌ SAO ──────────────────────────────────────────────────────────────
 *
 * Trước wave này 14/23 target có mẫu offline. Chín target còn lại vẫn
 * `ai_reachable_public` — học sinh TỚI ĐƯỢC bằng đề bài — nhưng không lượt đo
 * trình duyệt nào từng chạm chúng, vì mọi script đo đều duyệt danh mục offline.
 * Engine/validator của chúng đã khoá kĩ; phần học sinh NHÌN THẤY thì chưa ai đo.
 * Một "điểm mù bằng chứng" không phải là "chưa hỗ trợ", nhưng cũng KHÔNG được
 * đếm như đã kiểm chứng.
 *
 * ─── BỐN TẬP KHÁC NHAU, ĐỪNG ĐÁNH ĐỒNG (§9) ──────────────────────────────
 *
 *   A registry target        — có trong `runtime_targets`
 *   B học-sinh-tới-được      — `ai_reachable_public`
 *   C nội bộ                 — A \\ B
 *   D có mẫu offline         — có entry trong `offlineCatalog()`
 *   E có mẫu CÔNG KHAI       — có entry trong `publicCatalog()` (Thư viện học sinh)
 *
 * D ≠ E là điểm mấu chốt: thêm mẫu để ĐO ĐƯỢC không có nghĩa là quảng bá bài đó
 * cho học sinh. `algorithm.scan` là bề mặt tổng quát bắt các đề ngoài tám bài
 * chuyên biệt — nó cần bằng chứng, nhưng đưa vào Thư viện thì trùng nghĩa với
 * chính tám bài ấy.
 */

const targets = (descriptorsJson as unknown as {
  runtime_targets: Record<string, { reachability: string[] }>;
}).runtime_targets;

beforeAll(() => registerAllSimulations());

const A = Object.keys(targets);
const B = A.filter((t) => targets[t].reachability.includes("ai_reachable_public"));
const C = A.filter((t) => !targets[t].reachability.includes("ai_reachable_public"));

describe("W4B-3D · phủ mẫu theo TỪNG TẬP, không gộp", () => {
  it("mọi target học-sinh-tới-được đều có ít nhất một mẫu offline chạy được", () => {
    const withSample = new Set(offlineCatalog().map((e) => e.simId));
    const missing = B.filter((t) => !withSample.has(t));
    expect(
      missing,
      "Target học sinh tới được nhưng KHÔNG mẫu nào ⇒ không đo được trong trình duyệt:\n" +
        missing.map((t) => `  - ${t}`).join("\n"),
    ).toEqual([]);
  });

  it("mọi mẫu offline đều qua `validateConfig` THẬT và `init` được", () => {
    /* Một mẫu không chạy được còn tệ hơn không có mẫu: mọi script đo sẽ lặng lẽ
       bỏ qua nó và bảng phủ vẫn đếm nó là "có". */
    for (const e of offlineCatalog()) {
      const mod = getSimulation(e.simId);
      expect(mod, `${e.id}: không có module ${e.simId}`).toBeDefined();
      const v = mod!.validateConfig(e.envelope.config);
      expect(v.ok, `${e.id} (${e.simId}): validator từ chối — ${v.ok ? "" : v.error}`).toBe(true);
      if (!v.ok) continue;
      expect(() => mod!.init(v.config), `${e.id}: init ném lỗi`).not.toThrow();
    }
  });

  it("D và E là HAI tập khác nhau — mẫu để đo ≠ bài quảng bá cho học sinh", () => {
    const offline = new Set(offlineCatalog().map((e) => e.simId));
    const publicIds = new Set(publicCatalog().map((e) => e.simId));
    for (const id of publicIds) {
      expect(offline.has(id), `${id}: công khai mà không có trong danh mục offline`).toBe(true);
    }
    /* Có ít nhất một mẫu CỐ Ý chỉ-nội-bộ. Nếu vế này rỗng thì hoặc sản phẩm đã
       quảng bá mọi thứ, hoặc ai đó vừa lặng lẽ nâng visibility để cho đẹp số. */
    const internalOnly = [...offline].filter((id) => !publicIds.has(id));
    expect(internalOnly.length, "không còn mẫu nội bộ nào — visibility có bị nâng để làm đẹp số?")
      .toBeGreaterThan(0);
  });

  it("Thư viện phủ MỌI miền — thiếu một miền là mất bài không báo", () => {
    /* `GROUP_ORDER` vừa là thứ tự VỪA là bộ lọc, nên bỏ quên một miền = mọi mẫu
       công khai của miền đó biến mất khỏi Thư viện mà không lỗi ở đâu. Đúng ca
       đã xảy ra với `tree` (W4B-3D). Khoá theo TẬP MIỀN, không theo số lượng —
       số lượng chỉ đỏ khi tình cờ có mẫu công khai của miền bị quên. */
    const missing = (Object.keys(DOMAIN_LABEL) as Domain[]).filter((d) => !GROUP_ORDER.includes(d));
    expect(missing, `Thư viện bỏ sót miền: ${missing.join(", ")}`).toEqual([]);
  });

  it("target NỘI BỘ không bị nâng visibility chỉ để đạt phần trăm", () => {
    /* Hiện C rỗng (mọi target đều học-sinh-tới-được). Khẳng định vẫn đứng đó để
       nếu sau này có target nội bộ, không ai nâng nó lên public cho đủ số. */
    const publicIds = new Set(publicCatalog().map((e) => e.simId));
    for (const t of C) {
      expect(publicIds.has(t), `${t} là target nội bộ nhưng đã nằm trong Thư viện học sinh`)
        .toBe(false);
    }
  });
});
