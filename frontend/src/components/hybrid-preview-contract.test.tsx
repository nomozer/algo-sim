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
  geometryNarrationAt,
  geometryStepList,
  geometryTimeline,
  ghiChuGiaTriDung,
  hopLeScene3D,
  narrationAt,
  solutionAt,
  tapKetQuaCuoi,
  type Scene3D,
  type SceneObject,
} from "../simulations/domains/geometry/scene3d-model";
import {
  annotationsAt,
  DEFAULT_ANNOTATION_VIEW,
} from "../simulations/domains/geometry/scene3d-annotations";
import {
  cauQuanSat,
  docPhanHoiHybrid,
  giaTriDapSo,
  hybridTaiBuoc,
  hybridViewCua,
  KHOA_HYBRID_VIEW,
  type HybridPreviewView,
} from "../simulations/domains/geometry/hybrid-preview-adapter";
import {
  ChartMetricError,
  maTranKhung,
  veKhongGian,
} from "../simulations/domains/geometry/scene3d-chart";
import { Scene3DExplorer } from "../simulations/domains/geometry/Scene3DExplorer";
import { buildObject3D } from "../simulations/domains/geometry/scene3d-view";

const RUNS_DIR = join(__dirname, "..", "..", "..", "docs", "evaluation", "geometry", "runs");
const FIXTURES_DIR = join(RUNS_DIR, "claude-to-codex-takeover", "claude-resume", "fixtures-adapter-2-common-perpendicular");

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

/** Fixture TỔNG HỢP duy nhất của run hybrid-offline-readiness-finalization (provenance trong file). */
const SYNTHETIC_SOURCE = JSON.parse(readFileSync(join(RUNS_DIR,
  "hybrid-offline-readiness-finalization", "fixtures-synthetic", "synthetic-insufficient-specification-source.json"),
"utf8"));
const CHUNG_MINH = /đã\s*chứng\s*minh|được\s*chứng\s*minh|điều\s*phải\s*chứng\s*minh|đpcm|✓/i;
const clone = <T,>(x: T): T => JSON.parse(JSON.stringify(x));

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

  /* HFOI-F3 — ISSUE-ARCH-HYBRID-FRONTEND-OFFLINE-INTEGRATION: cảnh dựng ở a = 1 không được trình bày giá trị số như
     đáp số tổng quát. Kỳ vọng tay: H07 V = a³√3/3 (không phải √3/3), H01 V = a³ (không phải 1). */
  describe("HFOI-F3 — đáp số ký hiệu và tỉ lệ dựng", () => {
    it("12/12 served-* qua biên docPhanHoiHybrid; mọi đáp số nối đúng đại lượng kq_<id> của cảnh", () => {
      for (const row of SERVED_ROWS) {
        const fx = loadFixture(row.file);
        const r = docPhanHoiHybrid(fx.response);
        expect(r.ok, row.id).toBe(true);
        if (!r.ok) continue;
        const view = hybridViewCua(r.envelope)!;
        expect(view, row.id).not.toBeNull();
        expect(view.answers.map((a) => a.quantity_id).sort(), row.id).toEqual(
          Object.keys(fx.response.route_d.answers).map((k) => `kq_${k}`).sort());
      }
    });

    it("kỳ vọng tay: H07 đáp số a³√3/3, H01 a³ và a√3; cảnh không ký hiệu không có chú thích tỉ lệ", () => {
      const sym = (file: string) => {
        const r = docPhanHoiHybrid(loadFixture(file).response);
        return r.ok ? Object.fromEntries(hybridViewCua(r.envelope)!.answers.map((a) => [a.quantity_id, a.symbolic])) : null;
      };
      expect(sym("served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED.json")).toEqual({ kq_f8: "a³√3/3" });
      expect(sym("served-H01_CUBE.json")).toEqual({ kq_f3: "a³", kq_f4: "a√3" });
      expect(ghiChuGiaTriDung(loadFixture("served-pyramid-midpoint-area-AB.json").response.envelope.scene3d)).toBe("");
    });

    it("mọi chỗ hiện giá trị trên cảnh ký hiệu đều nói đó là giá trị của hình dựng (lời kể bước đo, nhãn số đo)", () => {
      for (const row of SERVED_ROWS) {
        const scene: Scene3D = loadFixture(row.file).response.envelope.scene3d;
        const chu = ghiChuGiaTriDung(scene);
        const buocDo = scene.events.filter((e) => e.action === "MEASURE").map((e) => e.step_index);
        for (const k of buocDo) {
          const nar = narrationAt(scene, k);
          if (scene.length_unit?.display_scale) expect(nar, `${row.id}@${k}`).toContain("trên hình dựng, a = 1 đơn vị dựng");
          else expect(nar, `${row.id}@${k}`).not.toContain("đơn vị dựng");
        }
        const cuoi = Math.max(...scene.events.map((e) => e.step_index));
        for (const a of annotationsAt(scene, cuoi, { ...DEFAULT_ANNOTATION_VIEW, showAll: true }, null)) {
          expect(a.text.endsWith(chu), `${row.id}:${a.id}`).toBe(true);
        }
      }
    });

    it("đáp số góc không lặp ký hiệu: H03 cos²(SA, (ABC)) = 1/4, không phải '= cos²=1/4' (review M1)", () => {
      const r = docPhanHoiHybrid(loadFixture("served-H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS.json").response);
      if (!r.ok) throw new Error(r.reason);
      const byId = Object.fromEntries(hybridViewCua(r.envelope)!.answers.map((a) => [a.quantity_id, giaTriDapSo(a)]));
      expect(byId).toEqual({ kq_f4: "a³√6/6", kq_f5: "1/4" });
    });

    it("biên vận chuyển từ chối: hệ số lệch đại lượng cảnh, đơn vị lệch, length_unit lệch, schema lạ, phản hồi cổng", () => {
      const goc = loadFixture("served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED.json").response;
      const lechHeSo = clone(goc); lechHeSo.route_d.answer_exact.f8.coef = "√3/2";
      const lechDonVi = clone(goc); lechDonVi.route_d.answer_exact.f8.unit = "b";
      const lechLU = clone(goc); lechLU.route_d.length_unit = null;
      const schema = clone(goc); schema.schema_version = "hybrid-route-d-preview/9";
      const tuMang = clone(goc); tuMang.envelope[KHOA_HYBRID_VIEW] = { adapter_version: "hybrid-preview-adapter/2" };
      for (const [ten, x] of Object.entries({ lechHeSo, lechDonVi, lechLU, schema, tuMang })) {
        expect(docPhanHoiHybrid(x).ok, ten).toBe(false);
      }
      for (const row of GATE_ROWS) expect(docPhanHoiHybrid(loadFixture(row.file).response).ok, row.id).toBe(false);
    });
  });

  /* HFOI-F4 — `route_d` nằm NGOÀI envelope; một biên vận chuyển đã kiểm, quan sát có tên loại quan hệ và bước neo. */
  describe("HFOI-F4 — biên route_d, quan hệ, neo timeline", () => {
    const H07 = "served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED.json";

    it("H07: một quan sát, tên loại quan hệ thật (perpendicular_line_plane), neo ở bước cuối; không hiện trước đó", () => {
      const r = docPhanHoiHybrid(loadFixture(H07).response);
      expect(r.ok).toBe(true);
      if (!r.ok) return;
      const scene = r.envelope.scene3d as Scene3D;
      const view = hybridViewCua(r.envelope) as HybridPreviewView;
      const cuoi = Math.max(...scene.events.map((e) => e.step_index));
      expect(view.observations).toEqual([{
        check_id: "f7", group: "goal", relation: "quan hệ vuông góc giữa đường thẳng và mặt phẳng",
        evidence_state: "TRUE_ON_CONFIGURATION", anchor_step: cuoi,
      }]);
      for (let k = 0; k < cuoi; k++) expect(hybridTaiBuoc(view, scene, k).observations, `bước ${k}`).toEqual([]);
      expect(hybridTaiBuoc(view, scene, cuoi).observations.length).toBe(1);
      // Đáp số V hiện từ bước ĐO của nó (kq_f8 ở bước cuối), không sớm hơn.
      expect(hybridTaiBuoc(view, scene, cuoi - 1).answers).toEqual([]);
      expect(hybridTaiBuoc(view, scene, cuoi).answers.map((a) => a.symbolic)).toEqual(["a³√3/3"]);
      const cau = cauQuanSat(view.observations[0]);
      expect(cau).toContain("trên hình đã dựng, điều này đúng");
      expect(cau).toContain("quan sát trên một hình, không phải chứng minh tổng quát");
      expect(cau).not.toMatch(CHUNG_MINH);
    });

    it("biên từ chối mọi quan sát tự xưng chứng minh hoặc trạng thái lạ (hợp đồng §3)", () => {
      const goc = loadFixture(H07).response;
      const dsLoi = [
        (x: any) => { x.route_d.planner.goal_checks.f7.can_present_as_proven = true; },
        (x: any) => { x.route_d.planner.goal_checks.f7.proof_status = "PROVEN"; },
        (x: any) => { delete x.route_d.planner.goal_checks.f7.can_present_as_proven; },
        (x: any) => { x.route_d.planner.goal_checks.f7.evidence_state = "PROVEN_TRUE"; },
        (x: any) => { x.route_d.runtime_identity.adapter_version = "hybrid-preview-adapter/1"; },
      ];
      dsLoi.forEach((hong, i) => { const x = clone(goc); hong(x); expect(docPhanHoiHybrid(x).ok, `lỗi ${i}`).toBe(false); });
    });

    it("qua store: envelope đã kiểm được nhận; view bị sửa (neo bước không tồn tại) bị validateEnvelope từ chối", () => {
      const r = docPhanHoiHybrid(loadFixture(H07).response);
      if (!r.ok) throw new Error(r.reason);
      useAppStore.getState().loadEnvelope(r.envelope as never);
      expect(useAppStore.getState().analysisError).toBeNull();
      expect(hybridViewCua(useAppStore.getState().active!.envelope)).not.toBeNull();

      // View tự đến (không qua biên vận chuyển) bị kiểm như lúc dựng: neo lạ, quan hệ chữ tự do, đại lượng trùng.
      const hongs = [
        (v: any) => { v.observations[0].anchor_step = 99; },
        (v: any) => { v.observations[0].anchor_step = 0; },
        (v: any) => { v.observations[0].anchor_step = "0"; },
        (v: any) => { v.observations[0].relation = "đã chứng minh xong"; },
        (v: any) => { v.answers.push({ ...v.answers[0] }); },
        (v: any) => { v.answers[0].unit = "b"; },
      ];
      hongs.forEach((hongView, i) => {
        useAppStore.getState().reset();
        const hong = clone(r.envelope) as any;
        hongView(hong[KHOA_HYBRID_VIEW]);
        useAppStore.getState().loadEnvelope(hong);
        expect(useAppStore.getState().active, `hỏng ${i}`).toBeNull();
        expect(useAppStore.getState().analysisError, `hỏng ${i}`).not.toBeNull();
      });
    });

    it("SSR ở bước đầu: không đáp số, không quan sát (không kết luận trước bước chống đỡ)", () => {
      const r = docPhanHoiHybrid(loadFixture(H07).response);
      if (!r.ok) throw new Error(r.reason);
      const html = renderToString(
        <Scene3DExplorer scene={r.envelope.scene3d as Scene3D} hybrid={hybridViewCua(r.envelope)} />,
      ).replace(/<!--.*?-->/g, "");
      expect(html).not.toContain("data-hybrid-answer");
      expect(html).not.toContain("data-route-d-observation");
      expect(html).not.toMatch(CHUNG_MINH);
    });

    it("wrapper hỏng có phần tử scene null bị từ chối thay vì ném lỗi", () => {
      const raw = clone(loadFixture(H07).response) as any;
      raw.envelope.scene3d.objects = [null];
      expect(() => docPhanHoiHybrid(raw)).not.toThrow();
      expect(docPhanHoiHybrid(raw).ok).toBe(false);
    });

    it("workspace không còn đọc route_d thô: chỉ view đã kiểm", () => {
      const src = readFileSync(join(__dirname, "SimulationWorkspace.tsx"), "utf8");
      expect(src).not.toMatch(/\.route_d\b|route_d\?:/);
      expect(src).toContain("hybridViewCua(active.envelope)");
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
        // HFOI-F5: 4/9 mã dừng TRƯỚC khi dựng — nhãn không được nói hệ đã chạy/dựng xong.
        expect(out, row.id).not.toMatch(/chạy được|đã dựng/i);
        expect(out, row.id).not.toContain("phản hồi cũ");
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
        // HFOI-F6: UNKNOWN ⇒ tiêu đề/nhãn đặt ở phía HỆ, không quy cho đề.
        expect(out, row.id).toContain("CHƯA XÁC ĐỊNH ĐỦ DỮ KIỆN");
        expect(out, row.id).toContain("hệ chưa xác định được đủ dữ kiện từ đề");
        expect(out, row.id).not.toContain("đề chưa đủ dữ kiện");
        expect(out, row.id).not.toContain("phản hồi cũ");
        expect(out, row.id).not.toContain("NGOÀI DANH MỤC MÔ PHỎNG");
        expect(out, row.id).not.toMatch(/dạng bài này hệ có mô phỏng/i);
        expect(BAO_SUA_DE.filter((c) => out.includes(c)), row.id).toEqual([]);
      }

      // Fixture TỔNG HỢP (khai trong file): chỉ đổi refusal_cause UNKNOWN → SOURCE của refusal-missing-dimension.
      expect(SYNTHETIC_SOURCE.SYNTHETIC).toBe(true);
      // Provenance names the bundle it was DERIVED from (superseded `hybrid-preview-contract-hardening/fixtures-adapter-2`,
      // kept unchanged); the envelope equality below ties it to the CURRENT bundle.
      const goc = JSON.parse(readFileSync(join(RUNS_DIR, "hybrid-preview-contract-hardening",
        "fixtures-adapter-2", "manifest.json"), "utf8")) as { fixtures: { id: string; response_sha256: string }[] };
      expect(SYNTHETIC_SOURCE.provenance.derived_from_response_sha256).toBe(
        goc.fixtures.find((f) => f.id === "refusal-missing-dimension")!.response_sha256);
      const sourceEnv = SYNTHETIC_SOURCE.response.envelope;
      expect({ ...sourceEnv, refusal_cause: "UNKNOWN" }).toEqual(
        loadFixture("refusal-missing-dimension.json").response.envelope);
      const sourceOut = renderToString(
        <UnsupportedNotice unsupported={sourceEnv} />,
      ).replace(/<!--.*?-->/g, "");
      expect(sourceOut).toContain("CHƯA ĐỦ DỮ KIỆN");
      expect(sourceOut).not.toContain("CHƯA XÁC ĐỊNH ĐỦ DỮ KIỆN");
      expect(sourceOut).toContain("đề chưa đủ dữ kiện");
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
          expect(tieuDe(out), row.id).toBe("CHƯA XÁC ĐỊNH ĐỦ DỮ KIỆN");
          expect(goiY(out), row.id).toBe(
            "Nếu đề thuộc dạng hệ dựng được và đã có đủ giả thiết, em có thể gửi lại để hệ phân tích lại.");
        }
        expect(out, row.id).not.toContain(env.reason_code);
      }
      // Mỗi reason_code của nhóm verification_gap đi cùng một nhánh — tiêu đề không phụ thuộc mã chi tiết.
      expect(maVG.size).toBe(9);
    });

    it("all 25 refusal fixtures keep technical codes out of the whole learner notice and preserve refusal_cause", () => {
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

  describe("SIMULATION-FIRST UX — không lộ đáp số cuối ở cả Path A và Path B, giữ nguyên đại lượng dựng hình & chứng chỉ", () => {
    it("tapKetQuaCuoi nhận diện đầy đủ kết quả cuối (cùng bí danh) trên 12/12 served-*, w11 và GEOMETRY_SAMPLES, nhưng giữ dữ kiện và trung gian", () => {
      for (const row of SERVED_ROWS) {
        const fx = loadFixture(row.file);
        const r = docPhanHoiHybrid(fx.response);
        if (!r.ok) throw new Error(r.reason);
        const scene = r.envelope.scene3d as Scene3D;
        const view = hybridViewCua(r.envelope)!;
        const an = tapKetQuaCuoi(scene, view);
        for (const a of view.answers) {
          expect(an.has(a.quantity_id), `${row.id}:${a.quantity_id}`).toBe(true);
        }
        // Dữ kiện đề cho (origin === "free") không bị coi là kết quả cuối.
        const givens = scene.objects.filter(
          (o) => o.type === "quantity" && o.origin === "free" && o.annotation?.role === "given",
        );
        for (const g of givens) {
          expect(an.has(g.id), `${row.id}:given:${g.id}`).toBe(false);
        }
        // Dữ liệu gốc trong model và view vẫn còn nguyên (P1 #8, #9).
        const cuoi = Math.max(0, scene.events.length - 1);
        expect(solutionAt(scene, cuoi).results.length).toBe(view.answers.length);
      }

      // Path A — bài mẫu offline GEOMETRY_SAMPLES: đại lượng đo không gõ loại (V = 16/3, d = 4) nằm trong tapKetQuaCuoi
      // và lời kể không rò "Gán V = 16/3." hay "Gán d = 4.".
      const samples = JSON.parse(
        readFileSync(join(__dirname, "..", "data", "geometry-samples.json"), "utf8"),
      ).samples as { id: string; envelope: { scene3d?: Scene3D } }[];
      const chop = samples.find((s) => s.id === "the-tich-chop")!.envelope.scene3d!;
      const anChop = tapKetQuaCuoi(chop);
      expect(anChop.has("V")).toBe(true);
      expect(anChop.has("d")).toBe(true);
      for (const e of chop.events) {
        expect(narrationAt(chop, e.step_index)).not.toMatch(/^Gán\s+/);
      }
      // What the learner reads per construction step (label + narration) never states a final value: a FINAL_RESULT
      // event only ever closes a step as its result, it never opens one (regenerated typed sample, run
      // `visual-hybrid-final-corrections`; the stale untyped sample made every event its own step).
      for (const g of geometryTimeline(chop)) {
        expect(g.construction.every((k) => chop.events[k]?.semantic_kind !== "FINAL_RESULT"), `step ${g.index}`).toBe(true);
        expect(geometryNarrationAt(chop, g.anchor), `step ${g.index}`).not.toContain("16/3");
      }
      expect(geometryStepList(chop).map((b) => b.label).join(" | ")).not.toContain("16/3");

      // Path A — cảnh có cả dữ kiện, trung gian và kết quả cuối (w11 rectangular_pyramid):
      const w11Pyr: Scene3D = JSON.parse(
        readFileSync(
          join(
            __dirname,
            "..",
            "..",
            "..",
            "docs",
            "evaluation",
            "geometry",
            "runs",
            "w11-pedagogical-polish",
            "inputs",
            "fixtures",
            "rectangular_pyramid_positive.json",
          ),
          "utf8",
        ),
      ).envelope.scene3d;
      const anW11 = tapKetQuaCuoi(w11Pyr);
      expect(anW11.has("the_tich_khoi_chop")).toBe(true);
      expect(anW11.has("v")).toBe(true);
      expect(anW11.has("AB_length")).toBe(false);
      expect(anW11.has("AD_length")).toBe(false);
      expect(anW11.has("SA_length")).toBe(false);
      expect(anW11.has("dien_tich_day_ABCD")).toBe(false);
    });

    it("Scene3DExplorer không dựng nút Xem/Ẩn đáp án hay thẻ Đáp số, lọc kết quả cuối khỏi Đại lượng và nhãn trên hình, và dựng hướng dẫn quan sát", () => {
      const exSrc = readFileSync(
        join(__dirname, "..", "simulations", "domains", "geometry", "Scene3DExplorer.tsx"),
        "utf8",
      );
      expect(exSrc).not.toContain("Xem đáp án");
      expect(exSrc).not.toContain("Ẩn đáp án");
      expect(exSrc).not.toContain("data-hybrid-answer");
      expect(exSrc).toContain("tapKetQuaCuoi(day, hybrid)");
      expect(exSrc).toContain("data-learner-guidance");

      for (const row of SERVED_ROWS) {
        const fx = loadFixture(row.file);
        const r = docPhanHoiHybrid(fx.response);
        if (!r.ok) throw new Error(r.reason);
        const scene = r.envelope.scene3d as Scene3D;
        const view = hybridViewCua(r.envelope)!;
        const html = renderToString(<Scene3DExplorer scene={scene} hybrid={view} />).replace(
          /<!--.*?-->/g,
          "",
        );
        expect(html, row.id).not.toContain("Xem đáp án");
        expect(html, row.id).not.toContain("Ẩn đáp án");
        expect(html, row.id).not.toContain("data-hybrid-answer");
        expect(html, row.id).toContain("data-learner-guidance");
        for (const a of view.answers) {
          expect(html, `${row.id}:${a.quantity_id}`).not.toContain(`data-ann-id="${a.quantity_id}"`);
        }
      }
    });
  });
});
