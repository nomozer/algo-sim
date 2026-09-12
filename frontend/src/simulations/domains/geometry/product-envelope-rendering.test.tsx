import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { UnsupportedNotice } from "../../../components/SimulationWorkspace";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { registerSemanticDomain } from "../semantic";
import { clearRegistryForTest } from "../../registry";
import { useAppStore } from "../../../state/store";
import { __resetHistoryForTest } from "../../../state/history";
import type { SimulationEnvelope } from "../../types";
import { hienSo, hopLeScene3D, objectsAt, stepCount, type Scene3D } from "./scene3d-model";
import { entitiesPresentAt } from "./scene3d-subentities";

/**
 * PHẢN HỒI SẢN PHẨM CỦA LƯỢT ĐO CUỐI PHẢI DỰNG THÀNH MÔ PHỎNG.
 *
 * ─── VÌ SAO ĐỌC FIXTURE THẬT, KHÔNG DỰNG CẢNH TAY ────────────────────────
 *
 * `scene3d-page.test.tsx` dựng một cảnh hai vật để khoá HỢP ĐỒNG của biên
 * nhận — đúng việc của nó, và không thay được việc ở đây. Một cảnh viết tay
 * luôn vừa khít thứ phía TS đã biết cách đọc; nó không trả lời được câu duy
 * nhất wave này hỏi: **envelope mà backend THẬT SỰ phát ra cho chín bài của
 * lượt đo cuối có dựng được không.**
 *
 * Nên fixture ở đây là phản hồi sản phẩm dựng lại từ chương trình đã đóng băng
 * (`backend/scripts/build_product_ui_fixtures.py`, 0 lượt gọi model), và mỗi
 * fixture nối ngược về artifact lượt đo bằng SHA-256.
 *
 * ─── BA CỘT, KHÔNG GỘP ───────────────────────────────────────────────────
 *
 * Lượt đo cuối chấm `EXACT_ANSWER_MATCH` · `SCENE3D_PASS` · `SERVABLE` thành
 * ba cột độc lập vì chúng hỏng độc lập. Test ở đây giữ đúng cách chia ấy: một
 * cảnh đủ vật mà mất đáp số, và một đáp số đúng trên một cảnh rỗng, là hai
 * bệnh khác nhau.
 */

const THU_MUC = join(
  process.cwd(), "..", "docs", "evaluation", "geometry",
  "product-ui-result-rendering", "fixtures",
);

interface Fixture {
  case_id: string;
  positive_or_negative: "positive" | "negative";
  source_artifact_path: string;
  source_sha256: string;
  served_from_stage: "A" | "B";
  status: string;
  expected_exact_display: string[];
  expected_scene_object_count: number;
  expected_scene_kinds: string[];
  expected_trace_event_count: number;
  expected_failure_stage_or_code: Record<string, unknown> | null;
  problem_text: string;
  envelope: SimulationEnvelope & { scene3d?: unknown; learner_reason?: string };
}

const FIXTURES: Fixture[] = readdirSync(THU_MUC)
  .filter((f) => f.endsWith(".json"))
  .sort()
  .map((f) => JSON.parse(readFileSync(join(THU_MUC, f), "utf-8")) as Fixture);

const DUONG = FIXTURES.filter((f) => f.positive_or_negative === "positive");
const AM = FIXTURES.filter((f) => f.positive_or_negative === "negative");

const canhCua = (f: Fixture) => f.envelope.scene3d as Scene3D;

/* ⚠️ `registerAllSimulations()` KHÔNG dùng được ở đây: nó có cờ một-lần
   (`registered`), nên sau `clearRegistryForTest()` nó im lặng không đăng ký gì
   và mọi ca đổ vào nhánh *"Hệ thống chưa có mô phỏng"*. Gọi thẳng người sở hữu
   `generic.semantic_program`. */
beforeEach(() => {
  clearRegistryForTest();
  registerSemanticDomain();
  __resetHistoryForTest();
  useAppStore.getState().reset();
});

// ══ ⓪ BỘ FIXTURE ════════════════════════════════════════════════════════
describe("bộ fixture — nối được về lượt đo cuối", () => {
  it("đủ 9 ca: 7 dương + 2 âm", () => {
    expect(FIXTURES).toHaveLength(9);
    expect(DUONG).toHaveLength(7);
    expect(AM).toHaveLength(2);
  });

  it("mỗi fixture khai nguồn bằng đường dẫn artifact + SHA-256", () => {
    for (const f of FIXTURES) {
      expect(f.source_artifact_path).toMatch(
        /^docs\/evaluation\/geometry\/thesis-final-acceptance\//,
      );
      expect(f.source_sha256).toMatch(/^[0-9a-f]{64}$/);
    }
  });

  it("`p3` là ca DUY NHẤT phục vụ ở chặng B", () => {
    const b = DUONG.filter((f) => f.served_from_stage === "B").map((f) => f.case_id);
    expect(b).toEqual(["p3_mat_cau_va_thiet_dien_tron"]);
  });
});

// ══ ① BIÊN NHẬN — ADAPTER ĂN ĐÚNG ENVELOPE THẬT ═════════════════════════
describe("adapter nhận envelope thật", () => {
  it.each(DUONG.map((f) => [f.case_id, f] as const))(
    "%s — `loadEnvelope` dựng được `active`, không rơi vào lỗi",
    (_id, f) => {
      const store = useAppStore.getState();
      store.loadEnvelope(f.envelope);
      const s = useAppStore.getState();
      expect(s.analysisError).toBeNull();
      expect(s.active).not.toBeNull();
      expect(s.active!.moduleId).toBe("generic.semantic_program");
      expect(s.unsupported).toBeNull();
    },
  );

  it("envelope dương đều mang `scene3d` HỢP LỆ ở biên nhận", () => {
    for (const f of DUONG) expect(hopLeScene3D(canhCua(f))).toBe(true);
  });

  it("envelope dương khai `domain: geometry` — không còn nhãn «Tổng quát»", () => {
    for (const f of DUONG) {
      expect((f.envelope as { domain?: string }).domain).toBe("geometry");
      expect(f.envelope.simulation_id).toBe("generic.semantic_program");
    }
  });

  /* Envelope thật mang thêm khoá mà kiểu phía này không khai (`analysis`,
     `representation_plan`, `notes`…). Biên nhận phải BỎ QUA chúng, không được
     coi là hình dạng lạ — nếu không thì mọi lần backend thêm một trường là một
     lần sản phẩm ngừng dựng hình. */
  it("khoá optional lạ KHÔNG làm hỏng biên nhận", () => {
    const f = DUONG[0];
    const them = {
      ...f.envelope,
      scene3d: { ...canhCua(f), truong_chua_biet: 1 },
      truong_moi_cua_backend: { bat_ky: true },
    };
    expect(hopLeScene3D(them.scene3d)).toBe(true);
    useAppStore.getState().loadEnvelope(them as SimulationEnvelope);
    expect(useAppStore.getState().analysisError).toBeNull();
    expect(useAppStore.getState().active).not.toBeNull();
  });
});

// ══ ② ĐÁP SỐ — GIỮ NGUYÊN DẠNG CHÍNH XÁC ═══════════════════════════════
/*
 * ⚠️ VÌ SAO KHÔNG KHẲNG ĐỊNH TRÊN `renderToString(<SimulationWorkspace/>)`.
 *
 * Hai rào, cả hai là hợp đồng thật của sản phẩm chứ không phải hạn chế của
 * test, và bản đầu của khối này đã đâm vào cả hai:
 *
 *   ① SSR đọc ảnh chụp KHỞI TẠO của store (zustand v5 +
 *      `useSyncExternalStore`), nên `loadEnvelope` xong `renderToString` vẫn
 *      dựng ra `empty-state`. Trạng thái store kiểm ở §① và §⑥, không kiểm
 *      qua HTML.
 *   ② Số đo chỉ hiện ở BƯỚC ĐÃ ĐO nó (`soDo = objectsAt(scene, buoc)` lọc
 *      `readout`) — bước đầu là 0, nên đáp số **đúng ra** phải vắng mặt ở
 *      khung đầu tiên. Đó là mục tiêu sư phạm, không phải thiếu sót.
 *
 * Nên ở đây kiểm THẨM QUYỀN ĐỊNH DẠNG (`hienSo` trên `exact` của bước cuối),
 * còn "nó có lên màn hình thật không" là việc của lượt nghiệm thu trình duyệt
 * (`frontend/scripts/certify-product-ui-rendering.mjs`), nơi có WebGL và tua
 * được tới bước cuối.
 */
describe("đáp số giữ nguyên dạng chính xác", () => {
  const soDoCuoi = (f: Fixture) =>
    objectsAt(canhCua(f), stepCount(canhCua(f)) - 1)
      .filter((o) => o.render === "readout");

  it.each(DUONG.map((f) => [f.case_id, f] as const))(
    "%s — `hienSo` dựng lại đúng từng ký tự đáp số của lượt đo",
    (_id, f) => {
      const hien = soDoCuoi(f).map((o) => hienSo(o.exact, o.value)).sort();
      expect(hien).toEqual(f.expected_exact_display);
    },
  );

  /* `value` (chuỗi backend dựng sẵn) và `hienSo(exact)` (dựng lại từ CẤU
     TRÚC) là hai đường định dạng ĐỘC LẬP. Chúng phải ra cùng một chuỗi — đó
     là cách duy nhất phát hiện khi một trong hai trôi. */
  it("hai đường định dạng độc lập cho CÙNG một chuỗi", () => {
    for (const f of DUONG) {
      for (const o of soDoCuoi(f)) {
        expect(hienSo(o.exact, "«không dựng lại được»"), `${f.case_id}/${o.id}`)
          .toBe(o.value);
      }
    }
  });

  /* ⚠️ ĐÍNH CHÍNH MỘT CON SỐ CỦA WAVE TRƯỚC — 11 → 12.
     `THESIS_FINAL_ACCEPTANCE_EXECUTION` và hai chương ghi *"11/11 đại lượng"*.
     Artifact nói **12** (p1 ba · p2 một · p3 hai · p4 hai · p5 hai · p6 một ·
     p7 một), và bộ đối chiếu `doi_chieu_ket_qua_cuoi.py` vốn đã chấm `12/12`
     mà không ai đối chiếu lại con số kể ra bằng chữ. Test này neo nó vào
     ARTIFACT để nó không trôi lần nữa. */
  it("12 đại lượng — khớp bản chấm đã đính chính của lượt đo", () => {
    const tat_ca = DUONG.flatMap((f) => f.expected_exact_display).sort();
    expect(tat_ca).toEqual([
      "100π", "120π", "144π", "25π√5", "2π√6", "360π",
      "3√6", "4500π", "65π", "72", "9", "96",
    ]);

    const sua = JSON.parse(readFileSync(join(
      process.cwd(), "..", "docs", "evaluation", "geometry",
      "thesis-final-acceptance", "thesis-final-20260908T160224Z",
      "SCORING_CORRECTION.json"), "utf-8"));
    const cuaArtifact = Object.values(
      sua.cases as Record<string, { quantities_SUA: Record<string, {
        expected_display: string; exact_answer_match: boolean }> }>,
    ).flatMap((c) => Object.values(c.quantities_SUA));
    expect(cuaArtifact).toHaveLength(12);
    expect(cuaArtifact.every((q) => q.exact_answer_match)).toBe(true);
    expect(cuaArtifact.map((q) => q.expected_display).sort()).toEqual(tat_ca);
  });

  /* Ba giá trị VÔ TỈ là chỗ một bản làm tròn sẽ lộ ra. Không đủ nếu chỉ kiểm
     "có chữ π": `78.5` cũng là một đáp số, chỉ là sai kiểu. */
  it.each([
    ["p1_chop_thiet_dien_khoang_cach", "3√6"],
    ["p6_thiet_dien_elip_cua_hinh_tru", "25π√5"],
    ["p7_thiet_dien_elip_cua_hinh_non", "2π√6"],
  ] as const)("%s — «%s» giữ căn và π, KHÔNG thành số gần đúng", (id, mong) => {
    const f = DUONG.find((x) => x.case_id === id)!;
    const hien = soDoCuoi(f).map((o) => hienSo(o.exact, o.value));
    expect(hien).toContain(mong);
    for (const s of hien) expect(s).not.toMatch(/\d\.\d/);
  });
});

// ══ ③ CẢNH 3D — ĐÚNG LOẠI, ĐÚNG SỐ LƯỢNG ═══════════════════════════════
describe("cảnh 3D mang đúng vật thể mà JSON khai", () => {
  it.each(DUONG.map((f) => [f.case_id, f] as const))(
    "%s — số vật và tập kiểu khớp fixture",
    (_id, f) => {
      const canh = canhCua(f);
      expect(canh.objects).toHaveLength(f.expected_scene_object_count);
      expect([...new Set(canh.objects.map((o) => o.type))].sort())
        .toEqual(f.expected_scene_kinds);
    },
  );

  it("bốn họ hình khó đều có vật thể ĐÚNG KIỂU trong cảnh", () => {
    const kieuCua = (id: string) =>
      canhCua(DUONG.find((f) => f.case_id === id)!).objects.map((o) => o.type);
    // đa diện lõm — vẫn là một `solid`, lõm không sinh kiểu riêng
    expect(kieuCua("p2_chop_day_ngu_giac_lom")).toContain("solid");
    // khối cong — cầu, trụ, nón dùng CHUNG một kiểu, hình nào là DỮ LIỆU
    for (const id of ["p3_mat_cau_va_thiet_dien_tron",
      "p4_hinh_tru_the_tich_va_xung_quanh",
      "p5_hinh_non_the_tich_va_xung_quanh"]) {
      expect(kieuCua(id)).toContain("curved_solid");
    }
    // thiết diện elip xiên — kiểu RIÊNG, không mượn đường tròn
    for (const id of ["p6_thiet_dien_elip_cua_hinh_tru",
      "p7_thiet_dien_elip_cua_hinh_non"]) {
      expect(kieuCua(id)).toContain("ellipse3");
      expect(kieuCua(id)).not.toContain("circle3");
    }
    // thiết diện tròn của mặt cầu — đường tròn thật, không phải elip
    expect(kieuCua("p3_mat_cau_va_thiet_dien_tron")).toContain("circle3");
  });

  it("mọi vật đều có nhãn đọc được — KHÔNG rơi về `id`", () => {
    for (const f of DUONG) {
      for (const o of canhCua(f).objects) {
        expect(o.label, `${f.case_id}/${o.id}`).toBeTruthy();
        expect(o.label, `${f.case_id}/${o.id}`).not.toBe(o.id);
      }
    }
  });
});

// ══ ④ TUA BƯỚC — CẢNH ĐỔI THEO BƯỚC, BƯỚC CUỐI DỰNG ĐỦ ═════════════════
describe("tua bước dựng", () => {
  it.each(DUONG.map((f) => [f.case_id, f] as const))(
    "%s — số bước khớp fixture và tăng dần từ 0",
    (_id, f) => {
      const canh = canhCua(f);
      expect(stepCount(canh)).toBe(f.expected_trace_event_count);
      expect(canh.events.map((e) => e.step_index))
        .toEqual(canh.events.map((_e, i) => i));
    },
  );

  it("chọn từng bước làm tập vật thể ĐỔI, và không bao giờ giảm", () => {
    for (const f of DUONG) {
      const canh = canhCua(f);
      const n = stepCount(canh);
      const so = Array.from({ length: n }, (_x, k) => objectsAt(canh, k).length);
      for (let k = 1; k < n; k++) {
        expect(so[k], `${f.case_id} bước ${k}`).toBeGreaterThanOrEqual(so[k - 1]);
      }
      // ít nhất một bước phải THÊM vật — nếu không thì tua chẳng cho thấy gì
      expect(new Set(so).size, f.case_id).toBeGreaterThan(1);
    }
  });

  it("bước CUỐI dựng lại đủ mọi vật của cảnh", () => {
    for (const f of DUONG) {
      const canh = canhCua(f);
      const cuoi = objectsAt(canh, stepCount(canh) - 1).map((o) => o.id).sort();
      expect(cuoi, f.case_id).toEqual(canh.objects.map((o) => o.id).sort());
    }
  });

  it("đáp số CHỈ xuất hiện sau bước đo nó, không có sẵn từ bước 0", () => {
    for (const f of DUONG) {
      const canh = canhCua(f);
      const dauTien = objectsAt(canh, 0).filter((o) => o.render === "readout");
      expect(dauTien, f.case_id).toHaveLength(0);
    }
  });

  /* `entitiesPresentAt` là SIÊU TẬP của `objectsAt`: mặt và cạnh của khối
     không có sự kiện riêng trong timeline (chúng là topology, không phải một
     bước dựng) nên chúng hiện đúng lúc khối cha hiện. Kiểm quan hệ bao hàm —
     đòi bằng nhau là đòi sai hợp đồng. */
  it("`entitiesPresentAt` bao hàm `objectsAt` ở mọi bước, không bỏ sót vật nào", () => {
    for (const f of DUONG) {
      const canh = canhCua(f);
      for (let k = 0; k < stepCount(canh); k++) {
        const co = entitiesPresentAt(canh, k, objectsAt);
        for (const o of objectsAt(canh, k)) {
          expect(co.has(o.id), `${f.case_id} bước ${k} thiếu ${o.id}`).toBe(true);
        }
      }
    }
  });
});

// ══ ⑤ CA ÂM — TỪ CHỐI AN TOÀN ══════════════════════════════════════════
describe("ca âm được trình bày an toàn", () => {
  it.each(AM.map((f) => [f.case_id, f] as const))(
    "%s — `status: unsupported`, KHÔNG có cảnh và KHÔNG có đáp số",
    (_id, f) => {
      expect(f.status).toBe("unsupported");
      expect(f.envelope.scene3d).toBeUndefined();
      expect(f.expected_exact_display).toEqual([]);
      expect(f.expected_scene_object_count).toBe(0);
    },
  );

  it.each(AM.map((f) => [f.case_id, f] as const))(
    "%s — thẻ từ chối nói ĐÚNG lớp nguyên nhân, bằng tiếng Việt",
    (_id, f) => {
      const u = f.envelope as unknown as Parameters<
        typeof UnsupportedNotice>[0]["unsupported"];
      expect((u as { failure_category?: string }).failure_category)
        .toBe("geometry_generation_failed");
      const html = renderToString(<UnsupportedNotice unsupported={u} />);
      /* (PRODUCT_RESPONSE_CONTRACT_ALIGNMENT) HAI CA ÂM, HAI NHÃN KHÁC NHAU.
         Bản trước đòi cùng một nhãn cho cả hai. Nhưng `n1` dừng ở lượt viết
         chương trình (thử lại còn cửa — "CHƯA" đúng) còn `n2` trượt cổng phủ
         (không phép dựng nào tạo ra vật ấy — "CHƯA" là một lời hứa hão). Một
         nhãn dùng chung buộc phải sai cho một trong hai ca. */
      const ngoaiBaoDong =
        (u as { error_code?: string }).error_code === "requested_operation_uncovered";
      expect(html).toContain(
        ngoaiBaoDong ? "NGOÀI PHẠM VI DỰNG HÌNH" : "CHƯA DỰNG ĐƯỢC MÔ PHỎNG");
      expect(html).toContain(f.envelope.learner_reason!);
      // Hai sự thật có cấu trúc phải LÊN MÀN HÌNH, không chỉ nằm trong JSON.
      expect(html).toContain("Dừng ở bước");
      expect(html).toContain("Loại vấn đề");
      expect(html).not.toContain("Không xác định được từ phản hồi cũ");
    },
  );

  /* ⚠️ LỖI ĐO ĐƯỢC Ở LƯỢT NGHIỆM THU TRÌNH DUYỆT (ảnh `n1`/`n2`).
     `geometry_generation_failed` gộp HAI tình huống ngược nhau:
       ① bài THUỘC bao đóng, mô hình viết hỏng ⇒ "thử diễn đạt lại" là đúng;
       ② bài NGOÀI bao đóng ⇒ câu ấy hứa một thứ sẽ không bao giờ tới.
     Cổng phủ đã phân biệt sẵn bằng `requested_operation_uncovered`; bề mặt học
     sinh thì chưa đọc nó. Đây đúng lớp lỗi kho đã sửa hai lần cho
     `out_of_scope` vs `not_simulation_suitable`. */
  it("bài NGOÀI bao đóng KHÔNG được hứa «dạng bài này hệ có mô phỏng»", () => {
    const n2 = AM.find((f) => f.case_id === "n2_khoi_ghep_bu_can_boolean")!;
    expect(n2.expected_failure_stage_or_code)
      .toMatchObject({ code: "requested_operation_uncovered" });
    const u = n2.envelope as unknown as Parameters<
      typeof UnsupportedNotice>[0]["unsupported"];
    const html = renderToString(<UnsupportedNotice unsupported={u} />);
    expect(html).not.toContain("Dạng bài này hệ có mô phỏng");
    expect(html).toContain("nằm ngoài các phép dựng");
  });

  /* Chiều ngược lại phải GIỮ ĐƯỢC LỜI KHUYÊN — nhưng ở dạng CÓ ĐIỀU KIỆN.
     `geometry_generation_failed` không kèm `error_code` (đúng ca `n1`) nghĩa là
     hệ bị chặn TRƯỚC cổng phủ, tức nó **không biết** dạng bài có nằm trong bao
     đóng không. Khẳng định "dạng bài này hệ có mô phỏng" ở đó là nói một điều
     mình không biết, về phía có lợi cho mình. Vẫn phải hữu ích, chỉ không được
     hứa — nếu không, bản vá này lặng lẽ biến thành "tắt hết lời khuyên". */
  it("không có `error_code` ⇒ lời khuyên CÓ ĐIỀU KIỆN, không phải lời hứa", () => {
    const html = renderToString(<UnsupportedNotice unsupported={{
      reason: "Chưa dựng được chương trình hình học cho đề này.",
      learner_reason: "…",
      failure_category: "geometry_generation_failed",
    }} />);
    expect(html).not.toContain("Dạng bài này hệ có mô phỏng");
    expect(html).toContain("Nếu đề thuộc dạng hệ dựng được");
    expect(html).toContain("gửi lại");        // vẫn còn đường đi tiếp
  });

  /* MỘT THẺ, MỘT GIỌNG. Không thẻ nào được vừa khẳng định hệ hỗ trợ dạng bài
     vừa nói yêu cầu nằm ngoài năng lực — đo được trên ảnh `n2` của lượt nghiệm
     thu trước. */
  it.each(AM.map((f) => [f.case_id, f] as const))(
    "%s — thẻ không vừa hứa hỗ trợ vừa nói ngoài năng lực",
    (_id, f) => {
      const u = f.envelope as unknown as Parameters<
        typeof UnsupportedNotice>[0]["unsupported"];
      const html = renderToString(<UnsupportedNotice unsupported={u} />);
      const hua = /Dạng bài này hệ có mô phỏng/.test(html);
      const gioiHan = /nằm ngoài các phép dựng|chưa có phép dựng/.test(html);
      expect(hua && gioiHan).toBe(false);
      expect(hua).toBe(false);
    },
  );

  /* Bất biến #10 của kho: định danh kỹ thuật KHÔNG được lọt lên bề mặt học
     sinh. Ca âm là chỗ dễ rò nhất vì thông điệp sinh ra từ chẩn đoán. */
  it("thẻ từ chối KHÔNG in mã lỗi, tên tầng hay JSON", () => {
    for (const f of AM) {
      const u = f.envelope as unknown as Parameters<
        typeof UnsupportedNotice>[0]["unsupported"];
      const html = renderToString(<UnsupportedNotice unsupported={u} />);
      for (const cam of ["geometry_generation_failed", "structural_coverage",
        "requested_operation_uncovered", "UNANCHORED_DERIVED_ASSUMPTION",
        "semantic_program", "error_code", "{\""]) {
        expect(html, `${f.case_id} rò «${cam}»`).not.toContain(cam);
      }
    }
  });

  /* Mã kỹ thuật vẫn phải TỒN TẠI trong dữ liệu để chẩn đoán được — nó chỉ
     không được bày cho học sinh. Hai câu khác nhau, và gộp lại thì hoặc là rò
     rỉ, hoặc là mất dấu vết. */
  it("mã kỹ thuật CÒN trong payload, chỉ không hiển thị", () => {
    const n2 = AM.find((f) => f.case_id === "n2_khoi_ghep_bu_can_boolean")!;
    expect(n2.expected_failure_stage_or_code).toMatchObject({
      stage: "structural_coverage",
      code: "requested_operation_uncovered",
    });
    /* `n1` bị chặn TRƯỚC khi có mã thẩm định nào — ghi `null` là ghi đúng thứ
       quan sát được. Đổi nó thành một mã cho đẹp là hồi tố sửa kỳ vọng. */
    const n1 = AM.find((f) => f.case_id === "n1_khoi_tron_xoay_tong_quat")!;
    expect(n1.expected_failure_stage_or_code).toMatchObject({
      stage: null, code: null, verdict: "UNRELATED_FAIL_CLOSED",
    });
  });
});

// ══ ⑥ CÁCH LY TRẠNG THÁI ═══════════════════════════════════════════════
describe("chuyển ca không rò trạng thái", () => {
  it("ca ÂM sau ca DƯƠNG dọn sạch cảnh cũ", () => {
    const store = useAppStore.getState();
    store.loadEnvelope(DUONG[0].envelope);
    expect(useAppStore.getState().active).not.toBeNull();

    store.loadUnsupported(
      AM[0].envelope as unknown as Parameters<typeof store.loadUnsupported>[0]);
    const s = useAppStore.getState();
    expect(s.active).toBeNull();
    expect(s.unsupported).not.toBeNull();

    /* `active` rỗng ⇒ shell KHÔNG còn đường nào tới `Scene3DExplorer`: nhánh
       3D đọc `active.envelope.scene3d`, và nhánh `unsupported` trả về trước
       cả nó. Kiểm ở store vì SSR không phân biệt được (xem §②). */
    expect(s.active?.envelope).toBeUndefined();
  });

  it("bảy ca dương nối tiếp nhau — cảnh đang hoạt luôn là cảnh của ĐÚNG ca đó", () => {
    for (const f of DUONG) {
      useAppStore.getState().loadEnvelope(f.envelope);
      const dang = useAppStore.getState().active!.envelope as unknown as { scene3d: Scene3D };
      const soDo = objectsAt(dang.scene3d, stepCount(dang.scene3d) - 1)
        .filter((o) => o.render === "readout")
        .map((o) => o.value)
        .sort();
      expect(soDo, f.case_id).toEqual(f.expected_exact_display);
    }
  });

  it("ca dương sau ca âm dọn sạch thẻ từ chối", () => {
    const store = useAppStore.getState();
    store.loadUnsupported(
      AM[0].envelope as unknown as Parameters<typeof store.loadUnsupported>[0]);
    expect(useAppStore.getState().unsupported).not.toBeNull();

    store.loadEnvelope(DUONG[0].envelope);
    const s = useAppStore.getState();
    expect(s.unsupported).toBeNull();
    expect(s.active).not.toBeNull();
  });

  it("lịch sử ghi ĐỦ bảy ca dương, không nhân bản, không ghi ca âm", () => {
    const store = useAppStore.getState();
    for (const f of DUONG) store.loadEnvelope(f.envelope);
    store.loadUnsupported(
      AM[0].envelope as unknown as Parameters<typeof store.loadUnsupported>[0]);
    expect(useAppStore.getState().history).toHaveLength(DUONG.length);
  });
});

// ══ ⑦ RAW JSON KHÔNG LÊN BỀ MẶT HỌC SINH ═══════════════════════════════
/* Khẳng định trên `Scene3DExplorer` chứ không trên `SimulationWorkspace`:
   component này nhận cảnh THẲNG qua prop nên nó dựng thật trong SSR, còn
   shell thì không (§②). Một khẳng định "không chứa JSON" trên một chuỗi HTML
   rỗng là một guard không bao giờ đỏ được. */
describe("raw JSON không nằm trên bề mặt học sinh", () => {
  it.each(DUONG.map((f) => [f.case_id, f] as const))(
    "%s — xưởng dựng thật, và KHÔNG in payload thô",
    (_id, f) => {
      const html = renderToString(<Scene3DExplorer scene={canhCua(f)} />);
      // rỗng-là-hỏng: không có mốc này thì mọi `not.toContain` dưới đây vô nghĩa
      expect(html).toContain("geo3d-canvas");
      for (const cam of ["\"simulation_id\"", "\"scene3d\"", "\"free_objects\"",
        "\"render\":", "generic.semantic_program", "semantic_program"]) {
        expect(html, `${f.case_id} rò «${cam}»`).not.toContain(cam);
      }
    },
  );
});

// ══ ⑧ PAYLOAD HỎNG — LỖI CÓ KIỂM SOÁT ═════════════════════════════════
describe("payload hỏng đi vào trạng thái lỗi có kiểm soát", () => {
  it("`simulation_id` không có trong registry ⇒ báo lỗi, KHÔNG ném", () => {
    const env = { ...DUONG[0].envelope, simulation_id: "khong.ton.tai" };
    expect(() => useAppStore.getState().loadEnvelope(env as SimulationEnvelope))
      .not.toThrow();
    const s = useAppStore.getState();
    expect(s.analysisError).toContain("khong.ton.tai");
    expect(s.active).toBeNull();
  });

  it("`config` hỏng ⇒ báo lỗi, KHÔNG dựng cảnh nửa vời", () => {
    const env = { ...DUONG[0].envelope, config: { frames: "không phải mảng" } };
    expect(() => useAppStore.getState().loadEnvelope(env as SimulationEnvelope))
      .not.toThrow();
    const s = useAppStore.getState();
    expect(s.active).toBeNull();
    expect(s.analysisError).toBeTruthy();
  });

  /* Cảnh HỎNG mà config vẫn hợp lệ: biên nhận fail-closed phải rơi về đường 2D
     cũ, KHÔNG dựng một khung 3D rỗng. Bày một khung rỗng là mời người học đi
     tìm thứ không có. `hopLeScene3D` là đúng chỗ shell hỏi câu ấy. */
  it.each([
    ["cảnh rỗng", { objects: [], events: [], free_objects: [] }],
    ["mất events", { objects: [{ id: "A" }], free_objects: [] }],
    ["events rỗng", { objects: [{ id: "A" }], events: [], free_objects: [] }],
    ["không phải object", "scene3d"],
  ])("`scene3d` hỏng (%s) ⇒ bài vẫn mở được, nhưng KHÔNG vào nhánh 3D", (_ten, xau) => {
    const env = { ...DUONG[0].envelope, scene3d: xau };
    useAppStore.getState().loadEnvelope(env as SimulationEnvelope);
    const s = useAppStore.getState();
    expect(s.active).not.toBeNull();
    expect(s.analysisError).toBeNull();
    expect(hopLeScene3D((s.active!.envelope as { scene3d?: unknown }).scene3d))
      .toBe(false);
  });
});


/* ══ TÊN HIỂN THỊ — BACKEND SỞ HỮU, FRONTEND CHỈ BÀY ═══════════════════════
   (DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH)

   `ellipse3` vào `MemoryType` từ 2026-09-07 nhưng ba bảng ở `display_names`
   không đi theo, nên `p6`/`p7` giao ra `Diện tích «đối tượng»`. Bản vá nằm
   TRỌN ở backend; phần của frontend là **không làm mất tên và không tự đặt
   tên**. Ba test dưới đây khoá đúng ranh giới ấy. */
describe("tên đại lượng do backend cấp, frontend không tự suy", () => {
  const soDoCuoi = (f: Fixture) =>
    objectsAt(canhCua(f), stepCount(canhCua(f)) - 1)
      .filter((o) => o.render === "readout");

  it("KHÔNG đại lượng nào của 7 ca dương còn nhãn chỗ-trống", () => {
    const xau: string[] = [];
    for (const f of DUONG) {
      for (const o of soDoCuoi(f)) {
        const nhan = String(o.label ?? "");
        for (const p of ["«đối tượng»", "Đối tượng", "undefined", "null"]) {
          if (nhan.includes(p)) xau.push(`${f.case_id}: ${nhan}`);
        }
        if (!nhan.trim()) xau.push(`${f.case_id}: nhãn RỖNG`);
      }
    }
    expect(xau, xau.join(" | ")).toEqual([]);
  });

  it("hai ca elip nói đúng chữ «elip», và giá trị KHÔNG đổi", () => {
    for (const id of ["p6_thiet_dien_elip_cua_hinh_tru",
                      "p7_thiet_dien_elip_cua_hinh_non"]) {
      const f = DUONG.find((x) => x.case_id === id)!;
      const so = soDoCuoi(f);
      expect(so.length, id).toBe(1);
      expect(String(so[0].label).toLowerCase(), id).toContain("elip");
      // Giá trị đi kèm phải y nguyên — tên đổi KHÔNG được chạm số.
      expect([hienSo(so[0].exact, so[0].value)]).toEqual(f.expected_exact_display);
    }
  });

  it("nhãn lạ đi qua tầng dữ liệu NGUYÊN SI — frontend không dựng lại tên", () => {
    /* Nhãn do backend sở hữu: frontend không sửa, không dịch, không đoán.
       ⚠️ KHÔNG khẳng định qua SSR: ô đọc số chỉ hiện ở BƯỚC ĐÃ ĐO nó, còn
       `renderToString` dựng bước đầu (§② ở đầu tệp) — một `toContain` trên
       chuỗi ấy sẽ đỏ vì lý do không liên quan. "Nó có lên màn hình thật không"
       là việc của `certify-product-ui-rendering.mjs`. */
    const f = DUONG.find((x) => x.case_id === "p6_thiet_dien_elip_cua_hinh_tru")!;
    const canh = JSON.parse(JSON.stringify(canhCua(f))) as Scene3D;
    const la = "MỘT NHÃN CHƯA TỪNG CÓ 12345";
    for (const o of canh.objects as { render?: string; label?: string }[]) {
      if (o.render === "readout") o.label = la;
    }
    const so = objectsAt(canh, stepCount(canh) - 1)
      .filter((x) => x.render === "readout");
    expect(so.length).toBeGreaterThan(0);
    for (const o of so) expect(o.label).toBe(la);
  });

  it("tầng vẽ RENDER thẳng `label`, không dựng tên từ `type`/`producer`", () => {
    /* Guard KIẾN TRÚC — quét mã nguồn. Không có nó, một bản vá "tiện tay" dựng
       nhãn ở frontend sẽ xanh hết và đẻ ra thẩm quyền đặt tên THỨ HAI, đúng
       thứ `display_names.py` tồn tại để là duy nhất. */
    const src = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf-8");
    const i = src.indexOf("geo3d-readout");
    expect(i, "không tìm thấy khối ô đọc số").toBeGreaterThan(0);
    const oDoc = src.slice(i, i + 700);
    /* ⚠️ Khẳng định TRONG khối ô đọc số, không phải trên cả tệp. Bản đầu hỏi
       `src.toContain("{o.label}")` — và `{o.label}` còn xuất hiện ở chỗ vẽ
       nhãn điểm, nên phép tiêm *"bỏ nhãn ô đọc số"* KHÔNG bị bắt. Đúng lớp
       lỗi mà phép tiêm sinh ra để tìm. */
    expect(oDoc, "ô đọc số không render thẳng `label` của backend")
      .toContain("{o.label}");
    for (const cam of ["o.type", "o.producer", "MO_TA_KIEU", "DANH_TU"]) {
      expect(oDoc, `ô đọc số suy nhãn từ ${cam}`).not.toContain(cam);
    }
  });
});
