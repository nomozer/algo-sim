import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import { UnsupportedNotice, NHAN_LOAI_VAN_DE } from "./SimulationWorkspace";
import { useAppStore } from "../state/store";
import { registerAllSimulations } from "../simulations";
import {
  hopLeScene3D,
  nhanQuanSatCauHinh,
  type Scene3D,
  type SceneObject,
} from "../simulations/domains/geometry/scene3d-model";
import {
  ChartMetricError,
  maTranKhung,
  veKhongGian,
} from "../simulations/domains/geometry/scene3d-chart";
import { Scene3DExplorer } from "../simulations/domains/geometry/Scene3DExplorer";
import { buildObject3D } from "../simulations/domains/geometry/scene3d-view";

const FIXTURES_DIR = join(
  __dirname,
  "..",
  "..",
  "..",
  "docs",
  "evaluation",
  "geometry",
  "runs",
  "hybrid-preview-contract-hardening",
  "fixtures-adapter-2",
);

interface ManifestRow {
  id: string;
  kind: "served" | "refusal" | "gate";
  covers: string[];
  expected: {
    http_status: number;
    envelope_status?: string | null;
    reason_code?: string | null;
    failure_category?: string | null;
    refusal_cause?: "SOURCE" | "CONSTRUCTION" | "UNKNOWN" | null;
  };
  response_sha256: string;
  sha256: string;
  file: string;
}

interface Manifest {
  schema: string;
  count: number;
  fixtures: ManifestRow[];
}

const MANIFEST: Manifest = JSON.parse(
  readFileSync(join(FIXTURES_DIR, "manifest.json"), "utf8"),
);

function loadFixture(file: string): Record<string, any> {
  return JSON.parse(readFileSync(join(FIXTURES_DIR, file), "utf8"));
}

function canonicalJson(val: unknown): string {
  if (val === null || typeof val !== "object") return JSON.stringify(val);
  if (Array.isArray(val)) return `[${val.map(canonicalJson).join(",")}]`;
  const entries = Object.entries(val as Record<string, unknown>).sort(([a], [b]) =>
    a < b ? -1 : a > b ? 1 : 0,
  );
  return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${canonicalJson(v)}`).join(",")}}`;
}

const SERVED_ROWS = MANIFEST.fixtures.filter((f) => f.kind === "served");
const REFUSAL_ROWS = MANIFEST.fixtures.filter((f) => f.kind === "refusal");
const GATE_ROWS = MANIFEST.fixtures.filter((f) => f.kind === "gate");

const BAO_SUA_DE = [
  "Bổ sung dữ liệu còn thiếu vào đề",
  "diễn đạt lại",
  "kiểm tra lại đề",
  "đối chiếu lại các số liệu trong đề",
  "sửa đề",
  "nêu rõ hình",
];

describe("Hybrid Preview Contract v2 — 41 fixtures & F1–F6", () => {
  beforeEach(() => {
    registerAllSimulations();
    useAppStore.getState().reset();
  });

  it("manifest có đúng 41 fixture (12 served, 25 refusal, 4 gate) và toàn vẹn SHA-256", () => {
    expect(MANIFEST.schema).toBe("hybrid-preview-envelope-fixtures/1");
    expect(MANIFEST.count).toBe(41);
    expect(SERVED_ROWS.length).toBe(12);
    expect(REFUSAL_ROWS.length).toBe(25);
    expect(GATE_ROWS.length).toBe(4);

    for (const row of MANIFEST.fixtures) {
      const fx = loadFixture(row.file);
      const sha = createHash("sha256")
        .update(canonicalJson(fx.response), "utf8")
        .digest("hex");
      expect(sha, row.id).toBe(row.response_sha256);
    }
  });

  describe("Bước 0 — store.loadEnvelope nhận toàn bộ 12/12 fixture served-*", () => {
    it.each(SERVED_ROWS.map((r) => [r.id, r.file] as const))(
      "%s nạp qua store.loadEnvelope và mở Scene3D hợp lệ",
      (_id, file) => {
        const fx = loadFixture(file);
        const env = fx.response.envelope;
        expect(env.status).toBe("ok");
        expect(env.simulation_id).toBe("generic.semantic_program");
        expect(hopLeScene3D(env.scene3d)).toBe(true);

        useAppStore.getState().loadEnvelope(env);
        const st = useAppStore.getState();
        expect(st.analysisError).toBeNull();
        expect(st.unsupported).toBeNull();
        expect(st.active).not.toBeNull();
        expect(st.view).toBe("workspace");
      },
    );
  });

  describe("F1 — ISSUE-ARCH-SCENE3D-ALTITUDE-MARKER-UNCERTIFIED", () => {
    const gom = (g: THREE.Object3D): THREE.Object3D[] => {
      const ra: THREE.Object3D[] = [g];
      g.children.forEach((c) => ra.push(...gom(c)));
      return ra;
    };

    it("không vẽ perp_marker từ id chứa 'cao' hay label/role 'chiều cao' khi không có witness", () => {
      const doanTheoId: SceneObject = {
        id: "cao_do_thi",
        label: "Đoạn nối",
        type: "segment3",
        render: "segment",
        origin: "derived",
        producer: "construct_segment",
        depends: ["A", "B"],
        point_a: ["0", "0", "0"],
        point_b: ["1", "1", "1"],
        endpoint_ids: ["A", "B"],
      } as SceneObject;
      const doanTheoNhan: SceneObject = {
        id: "doan_1",
        label: "Chiều cao tương đối",
        role: "Chiều cao",
        type: "segment3",
        render: "segment",
        origin: "derived",
        producer: "construct_segment",
        depends: ["A", "S"],
        point_a: ["0", "0", "2"],
        point_b: ["0", "0", "0"],
        endpoint_ids: ["S", "A"],
      } as SceneObject;

      for (const d of [doanTheoId, doanTheoNhan]) {
        const con = gom(buildObject3D(d, false)!);
        expect(
          con.filter((c) => c.name.startsWith("perp_marker:")),
          d.id,
        ).toEqual([]);
      }
    });

    it("chỉ vẽ perp_marker khi có chứng chỉ vuông góc hợp lệ (u ⊥ v) tại đúng chân witness", () => {
      const doanCoChungChi: SceneObject = {
        id: "doan_vuong_goc",
        label: "Đoạn SH",
        type: "segment3",
        render: "segment",
        origin: "derived",
        producer: "construct_segment",
        depends: ["S", "H"],
        point_a: ["0", "0", "0"],
        point_b: ["0", "0", "3"],
        endpoint_ids: ["S", "H"],
        perpendicular_witness: {
          from: "S",
          foot: ["0", "0", "3"],
          on: "mp_tren",
          marker: { u: ["0", "1", "0"], v: ["0", "0", "-3"] },
        },
      } as SceneObject;

      const con = gom(buildObject3D(doanCoChungChi, false)!);
      const markers = con.filter((c) => c.name === "perp_marker:doan_vuong_goc");
      expect(markers.length).toBe(1);

      const doanSaiChungChi: SceneObject = {
        ...doanCoChungChi,
        id: "doan_lech",
        perpendicular_witness: {
          from: "S",
          foot: ["0", "0", "3"],
          on: "mp_tren",
          marker: { u: ["0", "1", "1"], v: ["0", "0", "-3"] },
        },
      } as SceneObject;
      const conLech = gom(buildObject3D(doanSaiChungChi, false)!);
      expect(conLech.filter((c) => c.name.startsWith("perp_marker:"))).toEqual([]);
    });
  });

  describe("F2 — ISSUE-ARCH-SCENE3D-CHART-METRIC-UNGUARDED", () => {
    const NON_SPD_MATRICES: [string[][], string][] = [
      [[["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]], "indefinite"],
      [[["1", "2", "0"], ["0", "1", "0"], ["0", "0", "1"]], "asymmetric"],
      [[["0", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]], "singular"],
      [[["1", "2", "0"], ["2", "1", "0"], ["0", "0", "1"]], "symmetric, det < 0"],
      [[["-1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]], "det > 0 but negative definite block"],
      [[["1", "0"], ["0", "1"]], "non-3x3"],
    ];

    it.each(NON_SPD_MATRICES)(
      "maTranKhung, veKhongGian và cổng shell hopLeScene3D từ chối metric không SPD (%s)",
      (badMetric, label) => {
        const fx = loadFixture("served-H01_CUBE.json");
        const badScene: Scene3D = {
          ...fx.response.envelope.scene3d,
          chart_metric: badMetric,
        };
        expect(() => maTranKhung(badScene), label).toThrow(ChartMetricError);
        expect(() => veKhongGian(badScene), label).toThrow(ChartMetricError);
        // `App.tsx` và `SimulationWorkspace.tsx` chỉ dựng xưởng 3D khi `hopLeScene3D` đúng ⇒ không toạ độ NaN nào lên màn.
        expect(hopLeScene3D(badScene), label).toBe(false);
      },
    );

    /* Store delegates envelope validation to the registered module; geometry stays outside the store. */
    it("store không import module miền nào (M2 #7)", () => {
      const storeSrc = readFileSync(join(__dirname, "..", "state", "store.ts"), "utf8");
      expect(storeSrc).not.toMatch(/from\s+["'][^"']*simulations\/domains\//);
      const code = storeSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/[^\n]*/g, "");
      expect(code).not.toMatch(/chart_metric|hopLeScene3D|hopLeChartMetric|scene3d-chart|["'][^"']*\/domains\//);
    });
  });

  describe("F3 — ISSUE-ARCH-HYBRID-ROUTE-D-NOT-WIRED (length_unit.display_scale)", () => {
    it("hiện scene3d.length_unit.display_scale khi có mặt và không đổi cảnh không có length_unit", () => {
      for (const row of SERVED_ROWS) {
        const fx = loadFixture(row.file);
        const scene: Scene3D = fx.response.envelope.scene3d;
        const html = renderToString(<Scene3DExplorer scene={scene} />).replace(
          /<!--.*?-->/g,
          "",
        );
        if (scene.length_unit?.display_scale) {
          expect(html, row.id).toContain(scene.length_unit.display_scale);
          expect(html, row.id).not.toContain("length_unit");
          expect(html, row.id).not.toContain("is_given");
        } else {
          expect(html, row.id).not.toContain("đơn vị dựng");
          expect(html, row.id).not.toContain("data-length-unit");
        }
      }
    });
  });

  describe("F4 — ISSUE-ARCH-HYBRID-ROUTE-D-NOT-WIRED (quan sát trên hình ≠ chứng minh)", () => {
    it("served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED hiện quan sát trên một hình, không gọi là đã chứng minh", () => {
      const fx = loadFixture("served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED.json");
      const html = renderToString(
        <Scene3DExplorer
          scene={fx.response.envelope.scene3d}
          routeD={fx.response.route_d}
        />,
      ).replace(/<!--.*?-->/g, "");

      expect(html).toContain("Trên hình đã dựng, điều này đúng");
      expect(html).toContain("quan sát trên một hình, không phải chứng minh tổng quát");
      expect(html).not.toMatch(/đã\s*chứng\s*minh|được\s*chứng\s*minh|điều\s*phải\s*chứng\s*minh|đpcm|✓/i);
      expect(html).not.toContain("TRUE_ON_CONFIGURATION");
      expect(html).not.toContain("UNVERIFIABLE");
    });

    it("nhanQuanSatCauHinh xử lý đủ 3 trạng thái và coi can_present_as_proven thiếu/lạ là false", () => {
      const t1 = nhanQuanSatCauHinh({
        evidence_state: "TRUE_ON_CONFIGURATION",
        proof_status: "UNVERIFIABLE",
        can_present_as_proven: false,
      });
      const t2 = nhanQuanSatCauHinh({
        evidence_state: "FALSE_ON_CONFIGURATION",
        proof_status: "UNVERIFIABLE",
      });
      const t3 = nhanQuanSatCauHinh({
        evidence_state: "UNVERIFIABLE",
      });

      expect(t1).toContain("Trên hình đã dựng, điều này đúng");
      expect(t2).toContain("Trên hình đã dựng, điều này không đúng");
      expect(t3).toContain("Chưa kiểm được trên hình đã dựng");
      for (const t of [t1, t2, t3]) {
        expect(t).toContain("quan sát trên một hình, không phải chứng minh tổng quát");
        expect(t).not.toMatch(/đã\s*chứng\s*minh|được\s*chứng\s*minh|điều\s*phải\s*chứng\s*minh|đpcm|✓/i);
        expect(t).not.toContain("đề sai");
      }
    });
  });

  describe("F5 & F6 — 25 fixture refusal-* và 4 fixture gate-*", () => {
    it("F5: mọi fixture verification_gap có tiêu đề/gợi ý riêng, không rơi về NGOÀI DANH MỤC và không hứa có mô phỏng", () => {
      const vgRows = REFUSAL_ROWS.filter(
        (r) => r.expected.failure_category === "verification_gap",
      );
      expect(vgRows.length).toBe(9);
      for (const row of vgRows) {
        const fx = loadFixture(row.file);
        const out = renderToString(
          <UnsupportedNotice unsupported={fx.response.envelope} />,
        ).replace(/<!--.*?-->/g, "");
        expect(out, row.id).toContain("CHƯA ĐỦ BẰNG CHỨNG KIỂM CHỨNG");
        expect(out, row.id).toContain(NHAN_LOAI_VAN_DE.verification_gap);
        expect(out, row.id).not.toContain("NGOÀI DANH MỤC MÔ PHỎNG");
        expect(out, row.id).not.toMatch(/dạng bài này hệ có mô phỏng/i);
        expect(BAO_SUA_DE.filter((c) => out.includes(c)), row.id).toEqual([]);
      }
    });

    it("F6: mọi fixture insufficient_specification với refusal_cause = UNKNOWN (hoặc vắng) không mời sửa đề và không hứa có mô phỏng; chỉ SOURCE mới mời bổ sung dữ liệu", () => {
      const isRows = REFUSAL_ROWS.filter(
        (r) => r.expected.failure_category === "insufficient_specification",
      );
      expect(isRows.length).toBe(3);
      for (const row of isRows) {
        const fx = loadFixture(row.file);
        const out = renderToString(
          <UnsupportedNotice unsupported={fx.response.envelope} />,
        ).replace(/<!--.*?-->/g, "");
        expect(out, row.id).toContain("CHƯA ĐỦ DỮ KIỆN");
        expect(out, row.id).not.toContain("NGOÀI DANH MỤC MÔ PHỎNG");
        expect(out, row.id).not.toMatch(/dạng bài này hệ có mô phỏng/i);
        expect(BAO_SUA_DE.filter((c) => out.includes(c)), row.id).toEqual([]);
      }

      const sourceEnv = {
        ...loadFixture("refusal-missing-dimension.json").response.envelope,
        refusal_cause: "SOURCE" as const,
      };
      const sourceOut = renderToString(
        <UnsupportedNotice unsupported={sourceEnv} />,
      ).replace(/<!--.*?-->/g, "");
      expect(sourceOut).toContain("Bổ sung dữ liệu còn thiếu vào đề rồi gửi lại");
      expect(sourceOut).toContain("dạng bài này hệ có mô phỏng");
    });

    /* Hai test trên dựng `UnsupportedNotice` thẳng từ fixture, bỏ qua store. Đường thật là
       `ProblemInput → store.loadUnsupported(result) → SimulationWorkspace` (shell trả về
       `<UnsupportedNotice unsupported={store.unsupported}/>`); SSR không đọc được store sau khi nạp
       (xem product-envelope-rendering.test.tsx §②), nên ở đây đọc lại `getState().unsupported` rồi dựng
       đúng phần tử shell dựng. F5 rẽ theo `failure_category`, KHÔNG theo `reason_code`. */
    it("F5/F6 qua store: loadUnsupported giữ nguyên trường có cấu trúc, tiêu đề/gợi ý theo failure_category + refusal_cause", () => {
      const tieuDe = (html: string) => html.match(/class="eyebrow">([^<]*)</)?.[1];
      const goiY = (html: string) => html.match(/class="notes">([^<]*)</)?.[1] ?? null;
      const maVG = new Set<string>();
      for (const row of REFUSAL_ROWS) {
        const env = loadFixture(row.file).response.envelope;
        if (!["verification_gap", "insufficient_specification"].includes(env.failure_category)) continue;
        useAppStore.getState().loadUnsupported(env);
        const u = useAppStore.getState().unsupported!;
        expect(u, row.id).toEqual(env);
        expect(useAppStore.getState().active, row.id).toBeNull();
        const out = renderToString(<UnsupportedNotice unsupported={u} />).replace(/<!--.*?-->/g, "");
        if (env.failure_category === "verification_gap") {
          maVG.add(env.reason_code);
          expect(tieuDe(out), row.id).toBe("CHƯA ĐỦ BẰNG CHỨNG KIỂM CHỨNG");
          expect(goiY(out), row.id).toBe(
            "Hệ chỉ hiển thị mô phỏng khi đối chiếu và kiểm chứng được đầy đủ từ dữ kiện đến kết quả.");
        } else {
          expect(env.refusal_cause, row.id).toBe("UNKNOWN");
          expect(tieuDe(out), row.id).toBe("CHƯA ĐỦ DỮ KIỆN");
          expect(goiY(out), row.id).toBe(
            "Nếu đề thuộc dạng hệ dựng được và đã có đủ giả thiết, em có thể gửi lại để hệ phân tích lại.");
        }
        expect(out, row.id).not.toContain(env.reason_code);
      }
      // Mỗi reason_code của nhóm verification_gap đi cùng một nhánh — tiêu đề không phụ thuộc mã chi tiết.
      expect(maVG.size).toBe(9);
    });

    it("toàn bộ 25 fixture refusal-* không lộ mã kỹ thuật và tuân thủ luật refusal_cause", () => {
      for (const row of REFUSAL_ROWS) {
        const fx = loadFixture(row.file);
        const env = fx.response.envelope;
        const out = renderToString(
          <UnsupportedNotice unsupported={env} />,
        ).replace(/<!--.*?-->/g, "");
        expect(out, row.id).toContain(env.learner_reason);
        expect(out, row.id).not.toContain(env.reason_code);
        expect(out, row.id).not.toContain(env.failure_category);
        expect(out, row.id).not.toContain("hybrid-route-d-preview");
        expect(out, row.id).not.toContain("OFFLINE_FIXTURE_ONLY");
        if (env.refusal_cause !== "SOURCE") {
          expect(BAO_SUA_DE.filter((c) => out.includes(c)), row.id).toEqual([]);
        }
      }
    });

    it("4 fixture gate-* là phản hồi cổng operator, không có envelope học sinh và frontend không gọi /api/preview/hybrid", () => {
      for (const row of GATE_ROWS) {
        const fx = loadFixture(row.file);
        expect(fx.response.envelope, row.id).toBeUndefined();
        expect([403, 404, 422, 503]).toContain(row.expected.http_status);
      }
      const clientSrc = readFileSync(
        join(__dirname, "..", "llm", "client.ts"),
        "utf8",
      );
      expect(clientSrc).not.toContain("/api/preview/hybrid");
      expect(clientSrc).not.toContain("ALGOSIM_HYBRID_PREVIEW");
      expect(clientSrc).not.toContain("X-Hybrid-Preview-Token");
    });
  });
});
