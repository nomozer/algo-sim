/**
 * XƯỞNG HÌNH 3D — canvas là màn hình, chữ là thứ gọi ra khi cần.
 *
 * ─── VÌ SAO THAY BỐ CỤC, KHÔNG PHẢI TRANG TRÍ LẠI ───────────────────────
 *
 * Bản trước đọc như một **trang báo cáo có khung 3D đính kèm**: tiêu đề, một
 * đoạn văn giải thích kiến trúc, rồi khung hình bị bóp còn hai phần ba vì một
 * bảng danh sách luôn mở nằm cạnh. Học sinh mở ra và đọc; thứ họ cần là **xoay
 * cái hình**.
 *
 * Nay khung 3D chiếm gần trọn chiều rộng. Mọi bảng — thành phần, đề bài, chi
 * tiết kỹ thuật — là **lớp phủ gọi theo nhu cầu**, nên mở một bảng không bóp
 * hình lại. Ô soi chỉ hiện khi có vật đang chọn, và nói bằng tiếng của học
 * sinh: *"Trung điểm của SA"*, không phải `point3 · construct_point.midpoint`.
 *
 * ─── HAI CHẾ ĐỘ, MỘT DỮ LIỆU ────────────────────────────────────────────
 *
 * `chiTiet` chỉ mở thêm những trường vốn đã có trong `Scene3D` — `producer`,
 * `depends`, `parent`, `source`. Không chế độ nào giấu dữ liệu khỏi model; nó
 * chỉ quyết định **ai được mời đọc**. Học sinh lớp 11 không cần biết chữ
 * `construct_point.midpoint` để hiểu M là trung điểm.
 *
 * ─── MỘT THẨM QUYỀN CHỌN ────────────────────────────────────────────────
 *
 * `InteractionState` sống ở ĐÂY và chỉ ở đây. Ngăn kéo, cây, khung nhìn, ô soi
 * đều đọc `selected_id` của nó và đều báo về cùng một hàm. Giữ thêm một bản
 * chọn riêng cho ngăn kéo là mời hai bản lệch nhau — và lúc ấy học sinh bấm
 * một mặt trong khung rồi thấy cây sáng ở chỗ khác.
 */
import { useEffect, useMemo, useState } from "react";
import {
  CHUA_THAY,
  apDungPhien,
  type ClassroomSession,
  type SeenMarks,
} from "../../../state/classroom-sync";
import type { Scene3D } from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import {
  coherentFormula,
  geometryAnchor,
  objectsAt,
  hienSo,
  quantityChoices,
} from "./scene3d-model";
import {
  type InteractionState,
  type TreeNode,
  clearIsolate,
  collapseAll,
  dependencyClosure,
  directDependencies,
  explode,
  groupKeysOf,
  hide,
  highlightSet,
  isolate,
  select,
  semanticTree,
  showAll,
  taoTrangThai,
  tangNhanManh,
  treeAt,
} from "./interaction-state";
import {
  entitiesPresentAt,
  isSubEntity,
  parentSolidOf,
  sectionDetails,
  sectionViewIds,
  withSubEntities,
} from "./scene3d-subentities";
import { Scene3DPlayer } from "./scene3d-playback";
import { auxiliaryObjects } from "./scene3d-auxiliary";
import { BangNoi, BangNoiHost, batTatBang } from "./scene3d-floating-panel";
import {
  type AnnotationView,
  DEFAULT_ANNOTATION_VIEW,
  hasHiddenByDefault,
  quantitySources,
} from "./scene3d-annotations";
import { MenuCongCu, hoTroToanManHinh } from "./scene3d-tool-menu";
import { IconBack, IconExperiment, IconReset } from "../../../components/icons";

const NHOM_BUNG = "face";

/** Chú giải màu — cùng lớp vai trò với khung 3D và bảng «Đại lượng» (`scene3d-roles.ts`); sống trong menu «Hiển
 *  thị» (W05 · E — trước là khối dưới thẻ lời giải đã gỡ). "Vừa dựng" dùng cùng màu với "Đang xét". */
const CHU_GIAI_VAI_TRO: { lop: string; chu: string }[] = [
  { lop: "la-chon", chu: "Đang xét" },
  { lop: "la-chon", chu: "Vừa dựng ở bước này" },
  { lop: "la-so-lieu", chu: "Dữ kiện số" },
  { lop: "la-trung-gian", chu: "Đại lượng trung gian" },
  { lop: "la-boi-canh", chu: "Hình liên quan" },
];

/** `type` → cách gọi của HỌC SINH. Bề mặt học sinh không nói tiếng máy. */
/* ─── HAI BẢNG ĐÃ GỠ, KHÔNG ĐỔI TÊN ─────────────────────────────────────
 *
 *   `VAI_TRO`      kiểu → chữ tiếng Việt  (`point3` → "Điểm")
 *   `TU_PHEP_DUNG` producer → cụm tiếng Việt (`construct_point.midpoint` →
 *                  "Trung điểm của")
 *
 * Cả hai lặp lại đúng việc `display_names.py` làm ở backend, tức **một thẩm
 * quyền đặt tên thứ hai** nằm sai tầng — đúng thứ G1 sinh ra để dẹp, và nó
 * sống sót qua G1 vì lúc ấy không ai soi tới dòng vai trò của ô soi.
 *
 * Cái giá không phải giả thuyết: thêm `plane_perpendicular_to_line` ở G4 thì
 * bảng frontend không có khoá, và ô soi lặng lẽ tụt xuống *"Mặt phẳng"* trong
 * khi backend đã có sẵn câu *"Mặt phẳng qua B và vuông góc với SC"*. Một bảng
 * phải nhớ cập nhật là một bảng sẽ quên.
 *
 * Nay dòng ấy đọc thẳng `o.role` — backend quyết, phía này chỉ bày ra.
 */

function NutCay({
  nut, chon, onChon, tapNguon, duong, moNhom, onDoiNhom,
}: {
  /** Nút của cây ĐÃ LỌC theo bước (`treeAt`) — vật chưa dựng không có mặt ở đây. */
  nut: TreeNode;
  chon: string | null;
  onChon: (id: string) => void;
  tapNguon?: ReadonlySet<string>;
  /** Đường tới nút cha (`/<id>/…`) — khoá nhóm, cùng quy ước `groupKeysOf`. */
  duong: string;
  moNhom: ReadonlySet<string>;
  onDoiNhom: (khoa: string, mo: boolean) => void;
}) {
  const khoa = `${duong}/${nut.id}`;
  const con = nut.children.map((c) => (
    <NutCay key={c.id} nut={c} chon={chon} onChon={onChon} tapNguon={tapNguon}
            duong={khoa} moNhom={moNhom} onDoiNhom={onDoiNhom} />
  ));
  if (nut.isCategory) {
    // W4 · yêu cầu 5: nhóm THU GỌN mặc định (cây là lối phụ — lối chính là bấm lên hình); `<details>` cho bàn phím
    // và trình đọc màn hình hành vi mở/đóng chuẩn. Trạng thái mở do xưởng giữ (gắn với bài), không do DOM.
    return (
      <li>
        <details className="geo3d-tree-cat" open={moNhom.has(khoa)}
                 onToggle={(e) => onDoiNhom(khoa, e.currentTarget.open)}>
          <summary className="geo3d-tree-catname">
            {nut.label} <span className="geo3d-tree-dem">{nut.children.length}</span>
          </summary>
          <ul>{con}</ul>
        </details>
      </li>
    );
  }
  const laChon = chon === nut.id;
  const laNguon = !laChon && !!tapNguon?.has(nut.id);
  const lop = `geo3d-tree-item${laChon ? " la-chon" : laNguon ? " la-nguon" : ""}`;
  return (
    <li>
      <button
        type="button"
        className={lop}
        data-tree-id={nut.id}
        onClick={() => onChon(nut.id)}
        aria-current={laChon ? "true" : undefined}
      >
        <span className="geo3d-tree-nhan">{nut.label}</span>
      </button>
      {nut.children.length > 0 && <ul>{con}</ul>}
    </li>
  );
}

/** Bảng thông tin mở từ hàng trên của xưởng (ô soi mở theo lựa chọn, «Các bước dựng» ở trình phát). */
type BangThongTin = "de" | "thanh-phan" | "dai-luong";
/** Nút đã mở bảng — nơi trả tiêu điểm khi đóng bằng Escape: «Đề bài» là nút riêng, hai bảng kia mở từ menu «Khám phá». */
const nutMoBang = (id: BangThongTin) =>
  typeof document === "undefined" ? null
    : document.querySelector<HTMLElement>(id === "de" ? '[data-mo-bang="de"]' : '[data-mo-nhom="kham-pha"]');

export function Scene3DExplorer({
  scene: sceneKhung, de, tieuDe, quayLai, phien, onFocus, daiLop,
}: {
  scene: Scene3D;
  /** Đề bài nguyên văn. Vắng ⇒ không dựng nút «Đề bài». */
  de?: string | null;
  /** W05 — tên bài (tiêu đề envelope) ở hàng trên. */
  tieuDe?: string | null;
  /** W05 — đường ra của chế độ tập trung: chữ là tên trang đích. Vỏ quyết đích, xưởng chỉ bày nút. */
  quayLai?: { nhan: string; onClick: () => void };
  /**
   * Trạng thái phiên lớp. `null`/vắng ⇒ xưởng chạy y như khi tự học.
   *
   * Là PROP, không phải `useClassroomStore` ở đây: miền hình học không được
   * biết tới tầng lớp học. Biết là nó chỉ chạy được trong đúng một ngữ cảnh,
   * và test SSR phải dựng cả store lên mới render nổi.
   */
  phien?: ClassroomSession | null;
  /**
   * Báo TIÊU ĐIỂM NGỮ NGHĨA ra ngoài — id vật đang chọn + hành động vừa làm.
   *
   * Đây KHÔNG phải bản sao của `InteractionState`: nó là bản TÓM TẮT
   * (`StudentObservation`) mà giáo viên đọc. `InteractionState` đầy đủ vẫn chỉ
   * sống ở component này.
   */
  onFocus?: (selectedId: string | null, action: string) => void;
  /** Dải phụ trong thanh trên — nơi vỏ cắm chỉ báo lớp / dock giáo viên. */
  daiLop?: React.ReactNode;
}) {
  // exact-dimensions: toạ độ KHUNG → không gian Euclid MỘT lần (đồng nhất ⇒ chính cảnh cũ) — `scene3d-chart`.
  const scene = useMemo(() => veKhongGian(sceneKhung), [sceneKhung]);
  // MẶT và CẠNH sinh MỘT LẦN cho mỗi cảnh. Bỏ bước này là bỏ luôn khả năng
  // bấm vào một mặt — cây mất hai hạng mục và raycast chỉ còn trúng khối.
  const day = useMemo(() => withSubEntities(scene), [scene]);
  const cay = useMemo(() => semanticTree(day), [day]);
  const [tt, setTt] = useState<InteractionState>(taoTrangThai);
  const [moc, setMoc] = useState<SeenMarks>(CHUA_THAY);
  const [baoDongBo, setBaoDongBo] = useState(false);
  /* W4 (H-W2-3): các BẢNG THÔNG TIN đang mở — mỗi bảng độc lập (mở cái này không đóng cái kia); chỉ giữ TÊN bảng,
     không giữ một bản chọn riêng. Vị trí và thứ tự lớp do `BangNoiHost` giữ. */
  const [moBang, setMoBang] = useState<ReadonlySet<BangThongTin>>(new Set());
  const doiBang = (id: BangThongTin) => setMoBang((s) => batTatBang(s, id));
  const dongBang = (id: BangThongTin) => setMoBang((s) => (s.has(id) ? batTatBang(s, id) : s));
  /* ROADMAP §0.1-3: danh sách «Các bước dựng» — SỞ THÍCH trình bày như `chiTiet`, không gắn với cảnh; đóng/mở
     không đụng `tt` (bước, lựa chọn, tô sáng causal). */
  const [moBuoc, setMoBuoc] = useState(false);
  const [chiTiet, setChiTiet] = useState(false);
  /* W18 · §16.5 (thay U-W17-1): hình mặc định GỌN — tên điểm và dữ kiện đề cho; đáp số và đại
     lượng trung gian hiện khi người học chọn chúng (nhãn, dòng lời giải, vật). "Hiện tất cả" là
     SỞ THÍCH người dùng như `chiTiet` (giữ qua các bài); công tắc chỉ có mặt khi có nhãn mặc định
     đang ẩn. §16.6: lời giải đầy đủ thu gọn mặc định; khi nó mở, ô soi không lặp công thức. */
  const [xem, setXem] = useState<AnnotationView>(DEFAULT_ANNOTATION_VIEW);
  const coAn = useMemo(() => hasHiddenByDefault(day), [day]);
  /* W05 · C3: toàn màn hình là thao tác RIÊNG (chế độ tập trung không cần nó); trạng thái đọc từ trình duyệt, vì
     người dùng còn thoát bằng Esc/F11. Vào/ra chỉ đổi cỡ khung — bước, lựa chọn, camera không đi qua đây. */
  const [toanManHinh, setToanManHinh] = useState(false);
  useEffect(() => {
    const doi = () => setToanManHinh(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", doi);
    return () => document.removeEventListener("fullscreenchange", doi);
  }, []);
  const doiToanManHinh = () => {
    void (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen())
      .catch(() => {});
  };
  /* W2 · D/F: «Hình phụ» (hiện đường/mặt phẳng phụ đã xong việc) và «Lưới» (lưới nền) — SỞ THÍCH trình bày như
     `xem`, mặc định TẮT, giữ qua các bài; bật/tắt không đụng `tt` (bước, lựa chọn) hay camera. */
  const [hinhPhu, setHinhPhu] = useState(false);
  const [luoi, setLuoi] = useState(false);
  const coHinhPhu = useMemo(() => auxiliaryObjects(day).size > 0, [day]);
  // «Tách khối» chỉ có nghĩa khi cảnh có mặt để tách (W05: không mặt ⇒ không dựng nút).
  const coMatBung = day.objects.some((o) => o.type === "face");
  //: Tăng để yêu cầu khung nhìn đặt lại cho vừa hình. Trạng thái TRÌNH BÀY
  //: thuần — không đi vào `InteractionState`, vì nó không mô tả cách nhìn mà
  //: mô tả một YÊU CẦU xảy ra một lần.
  const [fitToken, setFitToken] = useState(0);

  /* ── ĐỔI BÀI ⇒ TRẢ TRẠNG THÁI GẮN VỚI CẢNH VỀ ĐẦU ────────────────────
   *
   * `SimulationWorkspace` dựng `Scene3DExplorer` ở cùng một vị trí cho mọi
   * bài, nên React DÙNG LẠI component — state không tự mất. Đo được: mở một
   * bài 12 bước, tua tới bước 10, chọn một vật, tách khối, rồi mở một bài 6
   * bước thì màn hình hiện **"Bước 10/6"**, ô soi vẫn mở trên một vật mang
   * cùng tên nhưng là vật KHÁC, và hình mở ra đã ở trạng thái tách sẵn.
   *
   * Phân biệt hai loại state, và chỉ trả về đầu loại thứ nhất:
   *   GẮN VỚI CẢNH   `tt` (bước, chọn, ẩn, cô lập, tách) · ngăn kéo đang mở
   *   SỞ THÍCH NGƯỜI DÙNG   `chiTiet` — mức chi tiết muốn đọc, không thuộc
   *                          về bài nào, nên giữ nguyên qua các bài.
   *
   * Dùng `useEffect` chứ không `key` để remount: remount cũng xoá `moc` (dấu
   * đã xem của lớp học), vốn không gắn với cảnh và không nên mất. */
  /* W4 · yêu cầu 5: nhóm đang mở của cây «Thành phần» (khoá `groupKeysOf`) — GẮN VỚI BÀI: giữ qua đóng/mở bảng và
     qua các bước, về rỗng khi đổi bài. */
  const [moNhom, setMoNhom] = useState<ReadonlySet<string>>(new Set());
  const doiNhom = (khoa: string, mo: boolean) => setMoNhom((s) => {
    if (s.has(khoa) === mo) return s;
    const n = new Set(s);
    if (mo) n.add(khoa); else n.delete(khoa);
    return n;
  });

  useEffect(() => {
    setTt(taoTrangThai());
    setMoBang(new Set());
    setMoNhom(new Set());
  }, [scene]);

  // Khung đang hiện = neo của bước DỰNG chứa `current_step` (W12) — cùng phép
  // với trình phát, nên cây và khung nhìn không bao giờ chỉ về hai khung khác.
  const buocHien = geometryAnchor(day, tt.current_step);
  const coMat = useMemo(
    () => entitiesPresentAt(day, buocHien, objectsAt),
    [day, buocHien],
  );
  const cayBuoc = useMemo(() => treeAt(cay, coMat), [cay, coMat]);
  // Chọn trên hình (hay ở bảng khác) ⇒ nhóm chứa vật ấy mở, mục của nó hiện ra trong cây.
  useEffect(() => {
    const k = groupKeysOf(cayBuoc, tt.selected_id);
    if (k.length) setMoNhom((s) => (k.every((x) => s.has(x)) ? s : new Set([...s, ...k])));
  }, [cayBuoc, tt.selected_id]);
  /* Tra một id sang CÁCH GỌI NGẮN — dùng ở "Thuộc", ở chi tiết thiết diện,
   * tức những chỗ vật này bị nhắc TRONG câu của vật khác. `label` ở đó cho ra
   * câu lồng câu; `reference` do backend dựng riêng cho vai này. */
  const ten = useMemo(() => {
    const m = new Map(day.objects.map((o) => [
      o.id,
      o.reference?.trim() || o.display_label?.trim() || o.label?.trim() || "đối tượng hình học",
    ]));
    return (id: string) => m.get(id) ?? "đối tượng hình học";
  }, [day]);

  /* ── ÁP LỆNH GIÁO VIÊN ────────────────────────────────────────────────
   *
   * Khoá theo `cmdId`/`roundId`, KHÔNG theo `phien` (object mới mỗi nhịp hỏi
   * ⇒ effect chạy 1,5 giây một lần và học sinh bị kéo về liên tục — đúng lỗi
   * mà `cmd_id` sinh ra để chặn, và nó sẽ quay lại ở đây nếu khoá sai).
   *
   * Luật ở `apDungPhien` (hàm thuần, có test riêng); chỗ này chỉ nối dây. */
  const coTrongCanh = useMemo(() => {
    const co = new Set(day.objects.map((o) => o.id));
    return (id: string) => co.has(id);
  }, [day]);

  useEffect(() => {
    const kq = apDungPhien(tt, phien ?? null, moc, coTrongCanh);
    if (kq.seen !== moc) setMoc(kq.seen);
    if (!kq.applied) return;
    setTt(kq.next);
    if (kq.reason === "sync") {
      setBaoDongBo(true);
      const t = setTimeout(() => setBaoDongBo(false), 2600);
      return () => clearTimeout(t);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phien?.roundId, phien?.cmdId, phien?.syncCmdId, phien?.mode, coTrongCanh]);

  const dangChon = tt.selected_id
    ? day.objects.find((o) => o.id === tt.selected_id) ?? null
    : null;
  const chon = (id: string | null) => {
    setTt((s) => select(s, id));
    onFocus?.(id, "SELECT_ENTITY");
  };
  const ctThietDien = dangChon ? sectionDetails(day, dangChon.id) : null;
  const formula = dangChon ? coherentFormula(day, dangChon) : null;
  // Ô soi của một ĐẠI LƯỢNG: dữ kiện số trong chuỗi và đầu vào trực tiếp — backend phát, không tính.
  const nguon = dangChon ? quantitySources(day, dangChon.id) : null;
  // Vật đang chọn là một ĐẠI LƯỢNG (mang giá trị backend phát) — ô soi luôn hiện giá trị của nó.
  const laDaiLuong = dangChon?.value != null;
  // Đại lượng không có nguồn số (thể tích đo thẳng trên khối): vật hình học nó đo, từ `depends` của backend.
  const doTren = laDaiLuong && nguon && nguon.givens.length + nguon.inputs.length === 0
    ? (dangChon?.depends ?? []).filter((id) => day.objects.some((o) => o.id === id && o.value == null))
    : [];
  // `hienSo` đọc số CHÍNH XÁC (căn, π) — cùng cách hiện mà thẻ lời giải (đã gỡ ở W05) dùng; không `toNumber`.
  const giaTri = (id: string) => {
    const o = day.objects.find((x) => x.id === id);
    return o ? `${o.notation || ten(id)} = ${hienSo(o.exact, o.value)}` : ten(id);
  };
  /* W05 · E: một mục của bảng «Đại lượng» thay dòng của thẻ lời giải: nhãn backend (`label`) rồi `ký hiệu = giá
     trị`. Không dựng tên từ kiểu hay phép dựng — `display_names.py` là thẩm quyền đặt tên duy nhất. */
  const dongDaiLuong = (id: string) => {
    const o = day.objects.find((x) => x.id === id);
    if (!o) return ten(id);
    return (
      <>
        {o.label && o.label !== o.notation && <span className="geo3d-dai-luong-ten">{o.label}</span>}
        <span className="geo3d-dai-luong-so">{giaTri(id)}</span>
      </>
    );
  };
  const daBung = tt.exploded_groups.includes(NHOM_BUNG);
  // ROADMAP §0.1-2: mọi đại lượng đã có ở bước này — một lối chọn cho cả đáp số bị ẩn mặc định.
  const daiLuong = useMemo(() => quantityChoices(day, buocHien), [day, buocHien]);
  const coDaiLuong = daiLuong.results.length + daiLuong.steps.length + daiLuong.givens.length > 0;
  /* W05 · E: vai trò trong chuỗi nhân quả quanh vật đang chọn (W10) tô ở mục bảng «Đại lượng» — trước ở dòng thẻ
     lời giải đã gỡ. Không chọn gì ⇒ trung tính; ngoài chuỗi ⇒ dịu, không biến mất. */
  const tang = useMemo(() => (tt.selected_id ? tangNhanManh(day, tt.selected_id) : null), [day, tt.selected_id]);
  const lopDaiLuong = (id: string) => {
    if (!tang) return "";
    const t = tang.get(id);
    return t === "dich" ? " la-chon" : t === "du_kien_so" ? " la-so-lieu"
      : t === "trung_gian" ? " la-trung-gian" : t ? " la-boi-canh" : " la-diu";
  };
  const tapNguon = useMemo(() => {
    if (!tt.selected_id) return new Set<string>();
    return new Set(dependencyClosure(day, tt.selected_id));
  }, [day, tt.selected_id]);

  return (
    <BangNoiHost>
    <div className="geo3d-xuong">
      {/* ── HÀNG TRÊN (W05 · chế độ tập trung): đường ra · tên bài · công cụ đã NHÓM ─────────────────────────────
          Vỏ không dựng thanh trên toàn cục cho cảnh 3D, nên đường ra nằm ở đây. Thao tác chính có chữ («Đề bài»);
          công cụ cùng loại vào menu («Khám phá», «Hiển thị», «Thêm») — tính năng mới vào một nhóm, không thêm chip. */}
      <div className="geo3d-thanh">
        {quayLai && (
          <button type="button" className="geo3d-quay-lai" onClick={quayLai.onClick}
                  title={`Rời mô phỏng, về ${quayLai.nhan}`}>
            <IconBack size={16} /> {quayLai.nhan}
          </button>
        )}
        <h1 className="geo3d-ten-bai" title={tieuDe ?? undefined}>{tieuDe || "Hình dựng theo từng bước"}</h1>
        {/* Lời báo NGẮN, KHÔNG modal: giáo viên vừa gọi cả lớp về, học sinh
            cần biết vì sao màn hình mình vừa đổi — nhưng một hộp thoại chặn
            màn hình giữa tiết thì tệ hơn cả việc không báo. */}
        {baoDongBo && (
          <span className="geo3d-bao-dong-bo" role="status">
            Giáo viên đã đồng bộ lớp
          </span>
        )}
        {daiLop}
        <div className="geo3d-thanh-nut">
          {de && (
            <button
              type="button"
              className={`geo3d-menu-nut${moBang.has("de") ? " la-mo" : ""}`}
              onClick={() => doiBang("de")}
              aria-expanded={moBang.has("de")}
              aria-controls={moBang.has("de") ? "geo3d-bang-de" : undefined}
              data-mo-bang="de"
            >Đề bài</button>
          )}
          <MenuCongCu nhan="Khám phá" khoa="kham-pha" muc={[
            { nhan: "Thành phần", chon: moBang.has("thanh-phan"), onChon: () => doiBang("thanh-phan"),
              title: "Cây các thành phần đã dựng ở bước này" },
            ...(coDaiLuong ? [{ nhan: "Đại lượng", chon: moBang.has("dai-luong"), onChon: () => doiBang("dai-luong"),
              title: "Chọn một đại lượng để xem giá trị, công thức và dữ kiện nó dựa vào" }] : []),
          ]} />
          <MenuCongCu nhan="Hiển thị" khoa="hien-thi" muc={[
            ...(coAn ? [{ nhan: "Hiện tất cả số đo", chon: xem.showAll, giuMo: true,
              onChon: () => setXem((s) => ({ showAll: !s.showAll })),
              title: "Hiện mọi số đo và đáp số đã có ở bước này ngay cạnh vật chúng đo" }] : []),
            ...(coHinhPhu ? [{ nhan: "Hình phụ", chon: hinhPhu, giuMo: true, onChon: () => setHinhPhu((x) => !x),
              title: "Hiện các đường và mặt phẳng phụ đã dùng xong (vd đường chéo dựng tâm, mặt phẳng để đo)" }] : []),
            { nhan: "Lưới nền", chon: luoi, giuMo: true, onChon: () => setLuoi((x) => !x),
              title: "Lưới nền mảnh để dễ cảm nhận chiều sâu" },
          ]} chanMenu={(
            /* W05 · E: chú giải màu ở đây — trước là khối thường trực dưới thẻ lời giải (đã gỡ). */
            <div className="geo3d-chu-giai-hop">
              <p className="geo3d-chu-giai-ten">Chú giải màu</p>
              <ul className="geo3d-chu-giai" aria-label="Chú giải màu">
                {CHU_GIAI_VAI_TRO.map((m) => (
                  <li key={m.chu} className={`geo3d-chu-giai-muc ${m.lop}`}>{m.chu}</li>
                ))}
              </ul>
            </div>
          )} />
          <MenuCongCu nhan="Thêm" khoa="them" muc={[
            { nhan: "Cách máy dựng", chon: chiTiet, giuMo: true, onChon: () => setChiTiet((x) => !x),
              title: "Ô chi tiết nêu thêm vật mà mỗi đối tượng dựa vào và giả thiết đặt hình" },
            ...(hoTroToanManHinh(typeof document === "undefined" ? undefined : document)
              ? [{ nhan: toanManHinh ? "Thoát toàn màn hình" : "Toàn màn hình", onChon: doiToanManHinh }] : []),
          ]} />
        </div>
      </div>

      {/* ── SÂN KHẤU: khung 3D + lớp phủ ───────────────────────────────── */}
      <div className="geo3d-san">
        <Scene3DPlayer
          scene={day}
          interaction={tt}
          onInteraction={setTt}
          onSelect={chon}
          fitToken={fitToken}
          annotationView={xem}
          stepsOpen={moBuoc}
          onStepsOpenChange={setMoBuoc}
          auxiliaryShown={hinhPhu}
          gridShown={luoi}
        />

        {/* Nút nổi — góc trái, KHÔNG che hình vì hình luôn ở giữa khung. */}
        {/* `data-che-khung`: lớp phủ nằm TRÊN khung — nhãn số đo (W17) tránh chỗ nó che. */}
        <div className="geo3d-noi" role="group" aria-label="Thao tác xem" data-che-khung="">
          {/* W05: chỉ dựng khi cảnh có mặt để tách — một nút vô hiệu thường trực là công cụ giả. */}
          {coMatBung && (
            <button
              type="button"
              className="geo3d-noi-nut"
              onClick={() =>
                setTt((s) => (daBung ? collapseAll(s) : explode(s, NHOM_BUNG)))
              }
            >
              <IconExperiment /> {daBung ? "Ráp lại" : "Tách khối"}
            </button>
          )}
          <button
            type="button"
            className="geo3d-noi-nut"
            onClick={() => {
              setTt((s) => showAll(clearIsolate(select(s, null))));
              // "Xem lại toàn hình" phải trả lại CẢ khung nhìn, không chỉ tập
              // vật đang hiện. Bỏ vế này thì sau khi phóng to một góc, nút
              // hiện đủ vật nhưng camera vẫn kẹt ở góc cũ.
              setFitToken((n) => n + 1);
            }}
          >
            <IconReset /> Xem lại toàn hình
          </button>
        </div>

        {/* Ô SOI — chỉ khi có vật đang chọn. W4: bảng nổi như mọi bảng thông tin — chọn vật không dành cột, không
            co canvas, không đổi camera; đóng ô soi là bỏ chọn. Thiết diện gọi bằng CHU TRÌNH khi mọi đỉnh có tên
            ("Thiết diện MNPQ" là cách đề bài gọi nó); còn một đỉnh chưa tên thì giữ nhãn cũ. */}
        {dangChon && (
          <BangNoi
            panel="soi"
            className="geo3d-soi"
            tieuDe={ctThietDien?.cycleLabel ?? dangChon.label}
            tieuDeLop="geo3d-soi-ten"
            nhanDong="Bỏ chọn"
            onDong={() => chon(null)}
          >
           <div className="geo3d-soi-than">
            {dangChon.role && <p className="geo3d-soi-vai">{dangChon.role}</p>}

            {dangChon.parent && (
              <p className="geo3d-soi-thuoc">
                Thuộc {ten(dangChon.parent)}
              </p>
            )}

            {/* §16.6 → W05: ô soi là nơi DUY NHẤT mang công thức (thẻ lời giải dưới mô phỏng đã gỡ). Đại lượng
                không có công thức nhất quán (thể tích đo thẳng trên khối) vẫn mang GIÁ TRỊ — W05 để trống ô ấy. */}
            {formula && (
              <p className="geo3d-soi-cong-thuc" data-formula-entity={dangChon.id}>
                {formula.text}
              </p>
            )}
            {!formula && laDaiLuong && (
              <p className="geo3d-soi-cong-thuc" data-value-entity={dangChon.id}>
                {giaTri(dangChon.id)}
              </p>
            )}

            {nguon && nguon.givens.length + nguon.inputs.length + doTren.length > 0 && (
              <dl className="geo3d-soi-nguon">
                {nguon.givens.length > 0 && (
                  <>
                    <dt>Từ dữ kiện đề cho</dt>
                    <dd>{nguon.givens.map(giaTri).join(", ")}</dd>
                  </>
                )}
                {nguon.inputs.length > 0 && (
                  <>
                    <dt>Tính trực tiếp từ</dt>
                    <dd>{[...new Set(nguon.inputs.map(ten))].join(", ")}</dd>
                  </>
                )}
                {/* Không nguồn SỐ nào: đại lượng đo thẳng trên vật hình học — nói vật ấy (phụ thuộc backend phát),
                    không bịa công thức. */}
                {doTren.length > 0 && (
                  <>
                    <dt>Đo trên</dt>
                    <dd>{doTren.map(ten).join(", ")}</dd>
                  </>
                )}
              </dl>
            )}

            {/* THIẾT DIỆN — đáp án của cả một họ bài, nên nó được nói đủ:
                gọi tên bằng chu trình, đếm đỉnh, kể khối nào và mặt nào. Mọi
                dòng đọc từ `Scene3D`; không dòng nào tính hình học ở đây. */}
            {ctThietDien && (
              <dl className="geo3d-soi-thiet-dien">
                <dt>Số đỉnh</dt>
                <dd>{ctThietDien.vertexCount}</dd>
                <dt>Các đỉnh</dt>
                <dd>{ctThietDien.vertexNames.join(" – ")}</dd>
                {ctThietDien.solidId && (
                  <>
                    <dt>Cắt khối</dt>
                    <dd>{ten(ctThietDien.solidId)}</dd>
                  </>
                )}
                {ctThietDien.planeId && (
                  <>
                    <dt>Mặt phẳng cắt</dt>
                    <dd>{ten(ctThietDien.planeId)}</dd>
                  </>
                )}
              </dl>
            )}

            <div className="geo3d-soi-nut">
              {ctThietDien && (
                <button
                  type="button"
                  className="geo3d-noi-nut"
                  onClick={() =>
                    setTt((s) => isolate(s, sectionViewIds(day, dangChon.id)))
                  }
                >
                  Xem thiết diện
                </button>
              )}
              <button
                type="button"
                className="geo3d-noi-nut"
                onClick={() =>
                  setTt((s) => isolate(s, highlightSet(day, dangChon.id)))
                }
              >
                Chỉ xem phần này
              </button>
              {directDependencies(day, dangChon.id).length > 0 && (
                <button
                  type="button"
                  className="geo3d-noi-nut"
                  onClick={() =>
                    setTt((s) =>
                      isolate(s, [
                        dangChon.id,
                        ...dependencyClosure(day, dangChon.id),
                      ]),
                    )
                  }
                >
                  Xem cấu tạo
                </button>
              )}
              <button
                type="button"
                className="geo3d-noi-nut"
                onClick={() => setTt((s) => select(hide(s, dangChon.id), null))}
              >
                Ẩn
              </button>
            </div>

            {/* Chi tiết vẫn nói bằng nhãn do backend phát hành. Stable IDs,
                enum kiểu và tên primitive chỉ là dây nối máy, không phải nội
                dung dành cho người học. */}
            {chiTiet && (
              <dl className="geo3d-soi-ky-thuat">
                <dt>Dựa trên</dt>
                <dd>
                  {directDependencies(day, dangChon.id).map(ten).join(", ") || "—"}
                </dd>
                {dangChon.source?.assumption && (
                  <>
                    <dt>Giả thiết</dt>
                    <dd>{dangChon.source.assumption}</dd>
                  </>
                )}
              </dl>
            )}
           </div>
          </BangNoi>
        )}

        {/* BẢNG THÔNG TIN — Xem đề, Thành phần, Đại lượng: mỗi bảng một `BangNoi`, mở độc lập, nổi TRÊN khung (không
            bóp khung lại). W4 thay MỘT ngăn phủ mép phải (mở cái này đóng cái kia; trên mobile phủ lên hình). */}
        {moBang.has("de") && (
          <BangNoi panel="de" className="geo3d-ngan" tieuDe="Đề bài" onDong={() => dongBang("de")}
                   traTieuDiem={() => nutMoBang("de")}>
            <div className="geo3d-ngan-than"><p className="geo3d-de">{de}</p></div>
          </BangNoi>
        )}
        {moBang.has("thanh-phan") && (
          <BangNoi panel="thanh-phan" className="geo3d-ngan" tieuDe="Các thành phần của hình"
                   onDong={() => dongBang("thanh-phan")} traTieuDiem={() => nutMoBang("thanh-phan")}>
            <div className="geo3d-ngan-than">
              <ul className="geo3d-tree">
                {cayBuoc.map((n) => (
                  <NutCay key={n.id} nut={n} chon={tt.selected_id} onChon={chon} tapNguon={tapNguon}
                          duong="" moNhom={moNhom} onDoiNhom={doiNhom} />
                ))}
              </ul>
            </div>
          </BangNoi>
        )}
        {moBang.has("dai-luong") && (
          <BangNoi panel="dai-luong" className="geo3d-ngan" tieuDe="Các đại lượng"
                   onDong={() => dongBang("dai-luong")} traTieuDiem={() => nutMoBang("dai-luong")}>
            <div className="geo3d-ngan-than geo3d-dai-luong">
              {([["Kết quả", daiLuong.results], ["Đại lượng trung gian", daiLuong.steps],
                 ["Dữ kiện", daiLuong.givens]] as const).filter(([, ids]) => ids.length > 0).map(([muc, ids]) => (
                <section key={muc} aria-label={muc}>
                  <h5 className="geo3d-dai-luong-muc">{muc}</h5>
                  <ul className="geo3d-dai-luong-ds">
                    {ids.map((id) => (
                      <li key={id}>
                        {/* W4: chọn GIỮ bảng mở — ô soi mở thành bảng riêng, không chiếm chỗ bảng này. */}
                        <button
                          type="button"
                          className={`geo3d-tree-item${lopDaiLuong(id)}`}
                          aria-pressed={tt.selected_id === id}
                          data-quantity-id={id}
                          onClick={() => chon(id)}
                        >
                          {dongDaiLuong(id)}
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          </BangNoi>
        )}
      </div>
      {/* W4 · yêu cầu 4: dòng «Bước n/N — lời kể» dưới thanh ĐÃ GỠ. Số bước ở thanh điều khiển, mô tả đầy đủ ở bảng
          «Các bước dựng», trình đọc màn hình nghe lời kể qua vùng `aria-live` trong khung nhìn. */}
    </div>
    </BangNoiHost>
  );
}

/** Chỉ để test: id nào là thực thể con của khối nào. */
export const _phuTro = { isSubEntity, parentSolidOf };

