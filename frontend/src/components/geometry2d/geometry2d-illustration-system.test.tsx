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
  Cone2D,
  Cube2D,
  Cylinder2D,
  GEOMETRY_FAMILY_ICONS,
  GEOMETRY_TEMPLATES,
  GeometryFamilyIcon,
  PerpendicularMarker2D,
  Plane2D,
  Prism2D,
  Pyramid2D,
  SAMPLE_ILLUSTRATION_MAPPING,
  Section2D,
  Segment2D,
  Sphere2D,
  deriveIllustrationSpecFromScene3D,
  detectFamilyFromScene3D,
  normalizeGeometryFamily,
  resolveGeometryIllustration,
  resolveTemplateFromIllustrationSpec,
  verifyCatalogIllustrationConsistency,
  type GeometryFamilyId,
  type GeometryTemplateId,
} from "./index";

describe("Axo 2D Geometry Illustration System (Tier A Family Icons + Tier B Composable Templates + Safe Fallback)", () => {
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

  it("2. Composable 2D Components & Template Registry (Tier B): đủ 10 component thành phần và 22 template tổ hợp/cơ bản", () => {
    const compSvg = renderToString(
      <svg viewBox="0 0 180 110">
        <Pyramid2D />
        <Cube2D />
        <Prism2D />
        <Sphere2D center={[90, 55]} radius={34} />
        <Cylinder2D bottomCenter={[90, 82]} topCenter={[90, 26]} rx={34} ry={10} />
        <Cone2D apex={[90, 18]} baseCenter={[90, 82]} rx={40} ry={12} />
        <Plane2D points={[[40, 40], [140, 40], [130, 80], [30, 80]]} label="(P)" showLabel={true} />
        <Section2D points={[[50, 50], [120, 50], [110, 75], [45, 75]]} />
        <Segment2D from={[60, 20]} to={[60, 80]} role="target" />
        <PerpendicularMarker2D at={[60, 80]} alongA={[60, 20]} alongB={[100, 80]} />
      </svg>,
    );
    expect(compSvg).toContain('data-geo2d-comp="pyramid"');
    expect(compSvg).toContain('data-geo2d-comp="cube"');
    expect(compSvg).toContain('data-geo2d-comp="prism"');
    expect(compSvg).toContain('data-geo2d-comp="sphere"');
    expect(compSvg).toContain('data-geo2d-comp="cylinder"');
    expect(compSvg).toContain('data-geo2d-comp="cone"');
    expect(compSvg).toContain('data-geo2d-comp="plane"');
    expect(compSvg).toContain('data-geo2d-comp="section-polygon"');

    const templateIds = Object.keys(GEOMETRY_TEMPLATES) as GeometryTemplateId[];
    expect(templateIds).toEqual([
      "pyramid.section",
      "pyramid.diagonal-section",
      "pyramid.perpendicular",
      "pyramid.altitude-distance",
      "pyramid.volume-height",
      "pyramid.circumscribed-sphere",
      "sphere.plane-section",
      "sphere.basic-radius",
      "cylinder.perpendicular-section",
      "cylinder.oblique-axis",
      "cylinder.right-basic",
      "cone.axial-section",
      "cone.slant-generator",
      "cone.inscribed-cylinder",
      "cube.plane-section",
      "prism.plane-section",
      "pyramid.point-to-plane-distance",
      "pyramid.dihedral-angle",
      "pyramid.skew-lines-distance",
      "oxyz.line-plane-intersection",
      "sphere.tangent-plane",
      "cone.parallel-section",
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

    // Kiểm tra 2 template đa khối (hình chóp nội tiếp mặt cầu & hình nón nội tiếp hình trụ) dùng chung các component 2D
    const pyrSphereSvg = renderToString(
      <SamplePreview templateId="pyramid.circumscribed-sphere" forceGeneric={true} />,
    );
    expect(pyrSphereSvg).toContain('data-geo2d-comp="sphere"');
    expect(pyrSphereSvg).toContain('data-geo2d-comp="pyramid"');

    const coneCylSvg = renderToString(
      <SamplePreview templateId="cone.inscribed-cylinder" forceGeneric={true} />,
    );
    expect(coneCylSvg).toContain('data-geo2d-comp="cylinder"');
    expect(coneCylSvg).toContain('data-geo2d-comp="cone"');

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
      "chop-thiet-dien-ba-diem": 12,
      "lap-phuong-thiet-dien-bat-ky": 13,
      "khoang-cach-diem-mat-phang-nghieng": 10,
      "goc-nhi-dien-hai-mat-phang": 12,
      "khoang-cach-hai-duong-cheo-nhau": 13,
      "lang-tru-tam-giac-thiet-dien": 11,
      "mat-cau-cat-mat-phang": 10,
      "oxyz-giao-diem-duong-mat": 10,
      "mat-phang-tiep-xuc-mat-cau": 8,
      "hinh-non-cat-song-song-day": 13,
      "chop-mat-cau-ngoai-tiep": 17,
    };

    for (const entry of publicCatalog()) {
      expect(
        stepCountOfEnvelope(entry.envelope),
        `stepCount mismatch for ${entry.id}`,
      ).toBe(expectedSteps[entry.id]);
    }

    const homeHtml = renderToString(<HomeView />);
    expect(homeHtml).toContain('data-thumb-template="pyramid.section"');
    expect(homeHtml).toContain('data-thumb-template="sphere.plane-section"');
    expect(homeHtml).toContain('data-thumb-template="cube.plane-section"');
    expect(homeHtml).toContain('data-thumb-template="cone.parallel-section"');

    const libHtml = renderToString(<LibraryView />);
    expect(libHtml).toContain('data-family-icon="pyramid"');
    expect(libHtml).toContain('data-family-icon="sphere"');
    expect(libHtml).toContain('data-family-icon="cylinder"');
    expect(libHtml).toContain('data-family-icon="cone"');
  });

  it("7. IllustrationSpec & Hình tổ hợp (§4.4): hỗ trợ đa khối, fallback an toàn khi quan hệ chưa xác minh và không phụ thuộc thứ tự bài", () => {
    // 7a. Hình chóp nội tiếp mặt cầu qua IllustrationSpec
    const pyrSphereSpec = resolveTemplateFromIllustrationSpec({
      primaryShape: "pyramid",
      secondaryShapes: ["sphere"],
      relation: "circumscribed",
      emphasis: "composite",
    });
    expect(pyrSphereSpec.templateId).toBe("pyramid.circumscribed-sphere");
    expect(pyrSphereSpec.fallback).toBe(false);

    // 7b. Hình nón nội tiếp hình trụ qua IllustrationSpec
    const coneCylSpec = resolveTemplateFromIllustrationSpec({
      primaryShape: "cone",
      secondaryShapes: ["cylinder"],
      relation: "inscribed",
      emphasis: "composite",
    });
    expect(coneCylSpec.templateId).toBe("cone.inscribed-cylinder");
    expect(coneCylSpec.fallback).toBe(false);

    // 7c. Khi có hình tổ hợp nhưng chưa xác minh được quan hệ -> fallback về hình minh họa trung tính của hình chính
    const unknownComposite = resolveGeometryIllustration({
      spec: {
        primaryShape: "sphere",
        secondaryShapes: ["cylinder", "cone"],
        relation: "skew_tangent_unverified",
      },
    });
    expect(unknownComposite.mode).toBe("family-icon");
    expect(unknownComposite.family).toBe("sphere");
    expect(unknownComposite.templateId).toBeNull();
    expect(unknownComposite.fallback).toBe(true);

    // 7d. Khi không xác định được hình chính -> fallback về icon hình học trung tính
    const unknownPrimary = resolveGeometryIllustration({
      spec: {
        primaryShape: "unknown_shape" as never,
      },
    });
    expect(unknownPrimary.mode).toBe("fallback-neutral");
    expect(unknownPrimary.family).toBe("neutral");
    expect(unknownPrimary.fallback).toBe(true);

    // 7e. Suy dẫn trực tiếp từ Scene3D đa khối (chóp + cầu & nón + trụ)
    const compositePyramidSphereScene: Scene3D = {
      free_objects: ["chop_sabcd", "mat_cau_ngoai_tiep"],
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
            ["1", "1", "3"],
          ],
          faces: [
            [0, 1, 2, 3],
            [0, 1, 4],
            [1, 2, 4],
            [2, 3, 4],
            [3, 0, 4],
          ],
        },
        {
          id: "mat_cau_ngoai_tiep",
          type: "curved_solid",
          curved_kind: "ball",
          render: "mesh",
          origin: "derived",
          producer: "test",
          label: "Mặt cầu ngoại tiếp",
          depends: ["chop_sabcd"],
          anchor: ["1", "1", "1"],
        },
      ],
      events: [],
    };
    const derivedCompSpec = deriveIllustrationSpecFromScene3D(compositePyramidSphereScene);
    expect(derivedCompSpec?.primaryShape).toBe("pyramid");
    expect(derivedCompSpec?.secondaryShapes).toEqual(["sphere"]);
    expect(derivedCompSpec?.relation).toBe("circumscribed");

    const resolvedComp = resolveGeometryIllustration({
      scene3d: compositePyramidSphereScene,
    });
    expect(resolvedComp.templateId).toBe("pyramid.circumscribed-sphere");
    expect(resolvedComp.fallback).toBe(false);

    // 7f. Đảo ngược thứ tự hoặc chỉ lấy tập con của danh sách bài mẫu không làm sai kết quả chọn hình minh họa
    const reversedCatalog = [...publicCatalog()].reverse();
    for (const item of reversedCatalog) {
      const expected = SAMPLE_ILLUSTRATION_MAPPING[item.id];
      const res = resolveGeometryIllustration({
        scene3d: (item.envelope as { scene3d?: Scene3D }).scene3d,
      });
      expect(res.templateId).toBe(expected.templateId);
      expect(res.family).toBe(expected.family);
    }
  });
});
