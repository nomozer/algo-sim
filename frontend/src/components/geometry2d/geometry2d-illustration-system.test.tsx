import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../../data/geometry-samples";
import { publicCatalog } from "../../data/offline-catalog";
import type { Scene3D } from "../../simulations/domains/geometry/scene3d-model";
import { HomeView } from "../HomeView";
import { LibraryView } from "../LibraryView";
import { SamplePreview } from "../SamplePreview";
import { stepCountOfEnvelope } from "../SessionCard";
import {
  GEOMETRY_FAMILY_ICONS,
  GEOMETRY_TEMPLATES,
  GeometryFamilyIcon,
  SAMPLE_ILLUSTRATION_MAPPING,
  detectFamilyFromScene3D,
  normalizeGeometryFamily,
  resolveGeometryIllustration,
  verifyCatalogIllustrationConsistency,
  type GeometryFamilyId,
  type GeometryTemplateId,
} from "./index";

describe("Axo 2D Geometry Illustration System (Tier A Family Icons + Tier B Reusable Templates + Safe Fallback)", () => {
  it("1. Family Icon Registry (Tier A): đủ 4 họ hình học + neutral, chuẩn viewBox 24x24 và không chứa chữ/nhãn điểm", () => {
    const families: GeometryFamilyId[] = [
      "pyramid",
      "sphere",
      "cylinder",
      "cone",
      "neutral",
    ];
    for (const family of families) {
      expect(GEOMETRY_FAMILY_ICONS[family]).toBeDefined();
      const html = renderToString(<GeometryFamilyIcon family={family} size={20} />);
      expect(html).toContain('viewBox="0 0 24 24"');
      expect(html).toContain(`data-family-icon="${family}"`);
      expect(html).not.toContain("<text");
    }

    expect(normalizeGeometryFamily("Hình chóp")).toBe("pyramid");
    expect(normalizeGeometryFamily("Mặt cầu")).toBe("sphere");
    expect(normalizeGeometryFamily("Hình trụ")).toBe("cylinder");
    expect(normalizeGeometryFamily("Hình nón")).toBe("cone");
    expect(normalizeGeometryFamily("Chưa phân loại")).toBe("neutral");
    expect(normalizeGeometryFamily(null)).toBe("neutral");
  });

  it("2. Template Registry (Tier B): đủ 12 template dạng bài tái sử dụng và bảo toàn bất biến hình học phẳng", () => {
    const templateIds = Object.keys(GEOMETRY_TEMPLATES) as GeometryTemplateId[];
    expect(templateIds).toEqual([
      "pyramid.section",
      "pyramid.diagonal-section",
      "pyramid.perpendicular",
      "pyramid.altitude-distance",
      "pyramid.volume-height",
      "sphere.plane-section",
      "sphere.basic-radius",
      "cylinder.perpendicular-section",
      "cylinder.oblique-axis",
      "cylinder.right-basic",
      "cone.axial-section",
      "cone.slant-generator",
    ]);

    for (const id of templateIds) {
      const def = GEOMETRY_TEMPLATES[id];
      expect(def.id).toBe(id);
      expect(def.invariants.length).toBeGreaterThan(0);

      // Chế độ generic: render đầy đủ hình học, tuyệt đối không sinh thẻ <text> chưa xác minh
      const genericSvg = renderToString(
        <SamplePreview templateId={id} forceGeneric={true} />,
      );
      expect(genericSvg).toContain('viewBox="0 0 180 110"');
      expect(genericSvg).toContain(`data-thumb-template="${id}"`);
      expect(genericSvg).toContain('data-thumb-mode="generic"');
      expect(genericSvg).toContain('data-thumb-fallback="false"');
      expect(genericSvg, `template ${id} ở chế độ generic không được chứa nhãn <text>`).not.toContain("<text");
    }

    // Kiểm tra bất biến hình học của trục nghiêng cylinder.oblique-axis: OO' · OA = 0
    const O = [72, 75] as const;
    const OPrime = [108, 27] as const;
    const A = [92.8, 90.6] as const;
    const dotOblique =
      (OPrime[0] - O[0]) * (A[0] - O[0]) + (OPrime[1] - O[1]) * (A[1] - O[1]);
    expect(Math.abs(dotOblique)).toBeLessThan(1e-9);

    // Kiểm tra bất biến điểm H(89, 60) nằm chính xác trên cạnh bên SC từ S(66, 14) đến C(106, 94)
    const S = [66, 14] as const;
    const C = [106, 94] as const;
    const H = [89, 60] as const;
    const tx = (H[0] - S[0]) / (C[0] - S[0]);
    const ty = (H[1] - S[1]) / (C[1] - S[1]);
    expect(tx).toBeCloseTo(0.575, 6);
    expect(ty).toBeCloseTo(0.575, 6);
  });

  it("3. Mapping & Resolver cho toàn bộ 11 bài trong Thư viện: khớp chính xác họ hình + template + nhãn đã xác minh", () => {
    const report = verifyCatalogIllustrationConsistency();
    expect(report).toHaveLength(11);
    for (const row of report) {
      expect(
        row.matches,
        `Sample ${row.sampleId}: expected (${row.expectedFamily}, ${row.expectedTemplateId}) but got (${row.actualFamily}, ${row.actualTemplateId}, mode=${row.mode})`,
      ).toBe(true);
    }

    for (const [sampleId, expected] of Object.entries(SAMPLE_ILLUSTRATION_MAPPING)) {
      const html = renderToString(
        <SamplePreview sampleId={sampleId} category={expected.categoryVi} />,
      );
      expect(html).toContain(`data-thumb-id="${sampleId}"`);
      expect(html).toContain(`data-thumb-template="${expected.templateId}"`);
      expect(html).toContain(`data-thumb-family="${expected.family}"`);
      expect(html).toContain('data-thumb-mode="verified"');
      expect(html).toContain('data-thumb-fallback="false"');
      expect(html).toContain("<text");
    }
  });

  it("4. Dynamic Scene3D Resolution: tự động chọn đúng template và trích xuất nhãn cho đề toán mới không có sampleId", () => {
    for (const sample of GEOMETRY_SAMPLES) {
      const scene3d = (sample.envelope as { scene3d?: Scene3D }).scene3d!;
      const expected = SAMPLE_ILLUSTRATION_MAPPING[sample.id];
      expect(expected).toBeDefined();

      // Không truyền sampleId — chỉ truyền scene3d trực tiếp như một đề bài mới do AI/Backend trả về
      const resolved = resolveGeometryIllustration({
        sampleId: null,
        scene3d,
      });
      expect(resolved.mode).toBe("verified");
      expect(resolved.fallback).toBe(false);
      expect(resolved.family).toBe(expected.family);
      expect(resolved.templateId).toBe(expected.templateId);
    }
  });

  it("5. Safe Fallback Hierarchy (§6 & §7): tuyệt đối không vẽ nhãn M, N, P, Q, H, (α) khi chưa xác minh được bài toán", () => {
    // 5a. Khi chỉ biết chủ đề/họ hình học mà sampleId không khớp bài đã biết -> fallback về icon họ hình (Tier A)
    const familyCases: Array<{ category: string; expectedFamily: GeometryFamilyId }> = [
      { category: "Hình chóp", expectedFamily: "pyramid" },
      { category: "Mặt cầu", expectedFamily: "sphere" },
      { category: "Hình trụ", expectedFamily: "cylinder" },
      { category: "Hình nón", expectedFamily: "cone" },
    ];

    for (const { category, expectedFamily } of familyCases) {
      const resolved = resolveGeometryIllustration({
        sampleId: "de-toan-moi-chua-xac-minh",
        category,
      });
      expect(resolved.mode).toBe("family-icon");
      expect(resolved.family).toBe(expectedFamily);
      expect(resolved.templateId).toBeNull();
      expect(resolved.fallback).toBe(true);
      expect(resolved.labels).toBeUndefined();

      const svgHtml = renderToString(
        <SamplePreview sampleId="de-toan-moi-chua-xac-minh" category={category} />,
      );
      expect(svgHtml).toContain(`data-thumb-family="${expectedFamily}"`);
      expect(svgHtml).toContain('data-thumb-mode="family-icon"');
      expect(svgHtml).toContain('data-thumb-fallback="true"');
      expect(svgHtml).toContain(`data-family-glyph="${expectedFamily}"`);
      expect(svgHtml).not.toContain("<text");
    }

    // 5b. Khi không biết cả dạng bài lẫn họ hình học -> fallback trung tính (neutral)
    const neutralSvg = renderToString(
      <SamplePreview sampleId="khong-ro-de-toan" category="" />,
    );
    expect(neutralSvg).toContain('data-thumb-family="neutral"');
    expect(neutralSvg).toContain('data-thumb-mode="fallback-neutral"');
    expect(neutralSvg).toContain('data-thumb-fallback="true"');
    expect(neutralSvg).not.toContain("<text");

    // 5c. Khi Scene3D có khối hình chóp tối giản nhưng không thuộc dạng bài nào đã biết -> fallback về icon Hình chóp
    const minimalPyramidScene: Scene3D = {
      free_objects: ["chop_sabcd"],
      objects: [
        {
          id: "chop_sabcd",
          type: "solid",
          render: "mesh",
          origin: "free",
          producer: "test",
          label: "Khối chóp",
          depends: [],
          vertices: [
            ["0", "0", "0"],
            ["2", "0", "0"],
            ["2", "2", "0"],
            ["0", "2", "0"],
            ["0", "0", "3"],
          ],
          faces: [
            [0, 1, 2, 3],
            [0, 1, 4],
            [1, 2, 4],
            [2, 3, 4],
            [3, 0, 4],
          ],
        },
      ],
      events: [],
    };
    expect(detectFamilyFromScene3D(minimalPyramidScene)).toBe("pyramid");
    const minimalResolved = resolveGeometryIllustration({
      scene3d: minimalPyramidScene,
    });
    expect(minimalResolved.mode).toBe("family-icon");
    expect(minimalResolved.family).toBe("pyramid");
    expect(minimalResolved.fallback).toBe(true);
  });

  it("6. Bảo toàn số bước dựng 3D và tích hợp đồng bộ trên Trang chủ & Thư viện", () => {
    const expectedSteps: Record<string, number> = {
      "thiet-dien-chop": 10,
      "mat-cheo-sac": 6,
      "vuong-goc-chop": 5,
      "mp-vuong-goc-duong": 7,
      "the-tich-chop": 4,
      "cau-cat-mat-phang": 5,
      "cau-the-tich": 1,
      "tru-thiet-dien-tron": 6,
      "tru-truc-xien": 3,
      "non-thiet-dien-truc": 5,
      "non-duong-sinh": 4,
    };

    for (const entry of publicCatalog()) {
      expect(stepCountOfEnvelope(entry.envelope)).toBe(expectedSteps[entry.id]);
    }

    const homeHtml = renderToString(<HomeView />);
    expect(homeHtml).toContain('data-thumb-template="pyramid.section"');
    expect(homeHtml).toContain('data-thumb-template="sphere.plane-section"');
    expect(homeHtml).toContain('data-thumb-template="cylinder.perpendicular-section"');
    expect(homeHtml).toContain('data-thumb-template="cone.axial-section"');

    const libHtml = renderToString(<LibraryView />);
    expect(libHtml).toContain('data-family-icon="pyramid"');
    expect(libHtml).toContain('data-family-icon="sphere"');
    expect(libHtml).toContain('data-family-icon="cylinder"');
    expect(libHtml).toContain('data-family-icon="cone"');
  });
});
