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
import { narrationAt, objectsAt, stepCount } from "./scene3d-model";
import {
  type InteractionState,
  type TreeNode,
  clearIsolate,
  collapseAll,
  dependencyClosure,
  directDependencies,
  explode,
  hide,
  highlightSet,
  isolate,
  select,
  semanticTree,
  showAll,
  taoTrangThai,
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
import {
  IconClose,
  IconExperiment,
  IconInfo,
  IconPanel,
  IconReset,
} from "../../../components/icons";

const NHOM_BUNG = "face";

/** `type` → cách gọi của HỌC SINH. Bề mặt học sinh không nói tiếng máy. */
const VAI_TRO: Record<string, string> = {
  point3: "Điểm",
  edge: "Cạnh",
  face: "Mặt",
  line3: "Đường thẳng",
  plane3: "Mặt phẳng",
  polygon3: "Đa giác",
  section: "Thiết diện",
  solid: "Khối",
  quantity: "Số đo",
};

/** Câu một dòng nói vật này LÀ GÌ, dẫn từ `producer` — không lộ tên hàm. */
const TU_PHEP_DUNG: Record<string, string> = {
  "construct_point.midpoint": "Trung điểm của",
  "construct_point.divide_segment": "Điểm chia đoạn",
  "construct_point.intersect_line_plane": "Giao điểm của",
  "construct_point.intersect_plane_plane": "Giao tuyến của",
  "construct_point.intersect_line_line": "Giao điểm của",
  "construct_point.project_onto": "Hình chiếu của",
  construct_line: "Đường thẳng qua",
  construct_plane: "Mặt phẳng qua",
  construct_polygon: "Đa giác",
  construct_solid: "Khối dựng từ",
  construct_section: "Thiết diện của",
  "measure.volume": "Thể tích của",
  "measure.distance": "Khoảng cách",
  "measure.angle_cos_sq": "Góc giữa",
};

function moTaNgan(o: {
  type: string; producer: string | null; depends: string[];
}, ten: (id: string) => string): string {
  if (o.producer === null) return "Điểm đề cho";
  const dau = TU_PHEP_DUNG[o.producer];
  const nguon = o.depends.map(ten).join(", ");
  if (!dau) return VAI_TRO[o.type] ?? "Đối tượng";
  return nguon ? `${dau} ${nguon}` : dau;
}

function NutCay({
  nut, chon, onChon, coMat, chiTiet,
}: {
  nut: TreeNode;
  chon: string | null;
  onChon: (id: string) => void;
  coMat: ReadonlySet<string>;
  chiTiet: boolean;
}) {
  const con = nut.children.map((c) => (
    <NutCay key={c.id} nut={c} chon={chon} onChon={onChon} coMat={coMat}
            chiTiet={chiTiet} />
  ));
  if (nut.isCategory) {
    return (
      <li className="geo3d-tree-cat">
        <span className="geo3d-tree-catname">{nut.label}</span>
        <ul>{con}</ul>
      </li>
    );
  }
  // Vật CHƯA DỰNG TỚI ở bước hiện tại vẫn nằm trong cây nhưng mờ và không bấm
  // được: giấu hẳn thì cây nhảy chỗ mỗi bước, còn cho bấm thì học sinh chọn
  // được một vật chưa tồn tại — hai kiểu nói dối khác nhau về cùng một thứ.
  const chuaCo = !coMat.has(nut.id);
  return (
    <li>
      <button
        type="button"
        className={`geo3d-tree-item${chon === nut.id ? " la-chon" : ""}`}
        onClick={() => onChon(nut.id)}
        disabled={chuaCo}
        aria-current={chon === nut.id ? "true" : undefined}
      >
        <span className="geo3d-tree-nhan">{nut.label}</span>
        {chiTiet && <span className="geo3d-tree-type">{nut.type}</span>}
      </button>
      {nut.children.length > 0 && <ul>{con}</ul>}
    </li>
  );
}

export function Scene3DExplorer({
  scene, de, onMoMenu, phien, onFocus, daiLop,
}: {
  scene: Scene3D;
  /** Đề bài nguyên văn. Vắng ⇒ không dựng nút «Xem đề». */
  de?: string | null;
  /**
   * Mở điều hướng ứng dụng. Vắng ⇒ KHÔNG dựng chip «Menu».
   *
   * Là CALLBACK chứ không phải `useAppStore` ở đây: miền hình học không được
   * biết tới vỏ ứng dụng. Biết là nó chỉ chạy được trong đúng một vỏ, và test
   * SSR của nó phải dựng cả store lên mới render nổi.
   */
  onMoMenu?: () => void;
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
  // MẶT và CẠNH sinh MỘT LẦN cho mỗi cảnh. Bỏ bước này là bỏ luôn khả năng
  // bấm vào một mặt — cây mất hai hạng mục và raycast chỉ còn trúng khối.
  const day = useMemo(() => withSubEntities(scene), [scene]);
  const cay = useMemo(() => semanticTree(day), [day]);
  const [tt, setTt] = useState<InteractionState>(taoTrangThai);
  const [moc, setMoc] = useState<SeenMarks>(CHUA_THAY);
  const [baoDongBo, setBaoDongBo] = useState(false);
  const [ngan, setNgan] = useState<"thanh-phan" | "de" | null>(null);
  const [chiTiet, setChiTiet] = useState(false);
  //: Tăng để yêu cầu khung nhìn đặt lại cho vừa hình. Trạng thái TRÌNH BÀY
  //: thuần — không đi vào `InteractionState`, vì nó không mô tả cách nhìn mà
  //: mô tả một YÊU CẦU xảy ra một lần.
  const [fitToken, setFitToken] = useState(0);

  const coMat = useMemo(
    () => entitiesPresentAt(day, tt.current_step, objectsAt),
    [day, tt.current_step],
  );
  const ten = useMemo(() => {
    const m = new Map(day.objects.map((o) => [o.id, o.label]));
    return (id: string) => m.get(id) ?? id;
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
  const coMatBung = day.objects.some((o) => o.type === "face");
  const daBung = tt.exploded_groups.includes(NHOM_BUNG);

  return (
    <div className="geo3d-xuong">
      {/* ── THANH TRÊN: mảnh, chỉ những gì cần gọi ra ───────────────────── */}
      <div className="geo3d-thanh">
        {/* Đường RA của xưởng. Cột điều hướng thường trực đã tắt ở đây
            (`app-root.is-canvas-first`), nên nếu không có chip này thì học
            sinh vào xưởng là kẹt lại. */}
        {onMoMenu && (
          <button type="button" className="geo3d-chip" onClick={onMoMenu}
            aria-label="Mở điều hướng">
            <IconPanel side="left" /> Menu
          </button>
        )}
        <span className="geo3d-ten-bai">Hình dựng theo từng bước</span>
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
              className={`geo3d-chip${ngan === "de" ? " la-mo" : ""}`}
              onClick={() => setNgan((x) => (x === "de" ? null : "de"))}
              aria-expanded={ngan === "de"}
            >
              Xem đề
            </button>
          )}
          <button
            type="button"
            className={`geo3d-chip${ngan === "thanh-phan" ? " la-mo" : ""}`}
            onClick={() =>
              setNgan((x) => (x === "thanh-phan" ? null : "thanh-phan"))
            }
            aria-expanded={ngan === "thanh-phan"}
          >
            <IconPanel side="right" /> Thành phần
          </button>
          <button
            type="button"
            className={`geo3d-chip${chiTiet ? " la-mo" : ""}`}
            onClick={() => setChiTiet((x) => !x)}
            aria-pressed={chiTiet}
            title="Hiện cách máy dựng từng đối tượng"
          >
            <IconInfo /> Chi tiết
          </button>
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
        />

        {/* Nút nổi — góc trái, KHÔNG che hình vì hình luôn ở giữa khung. */}
        <div className="geo3d-noi" role="group" aria-label="Thao tác xem">
          <button
            type="button"
            className="geo3d-noi-nut"
            onClick={() =>
              setTt((s) => (daBung ? collapseAll(s) : explode(s, NHOM_BUNG)))
            }
            disabled={!coMatBung}
          >
            <IconExperiment /> {daBung ? "Ráp lại" : "Tách khối"}
          </button>
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

        {/* Ô SOI — chỉ khi có vật đang chọn. */}
        {dangChon && (
          <aside className="geo3d-soi" aria-label="Thông tin đối tượng">
            <div className="geo3d-soi-dau">
              <div>
                {/* Thiết diện gọi bằng CHU TRÌNH khi mọi đỉnh có tên —
                    "Thiết diện MNPQ" là cách đề bài gọi nó. Còn một đỉnh
                    chưa tên thì giữ nhãn cũ, không ghép nửa tên nửa số. */}
                <p className="geo3d-soi-ten">
                  {ctThietDien?.cycleLabel ?? dangChon.label}
                </p>
                <p className="geo3d-soi-vai">
                  {moTaNgan(dangChon, ten)}
                </p>
              </div>
              <button
                type="button"
                className="geo3d-soi-dong"
                onClick={() => chon(null)}
                aria-label="Bỏ chọn"
              >
                <IconClose />
              </button>
            </div>

            {dangChon.parent && (
              <p className="geo3d-soi-thuoc">
                Thuộc {ten(dangChon.parent)}
              </p>
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

            {/* CHI TIẾT KỸ THUẬT — cùng dữ liệu, chỉ đổi người được mời đọc. */}
            {chiTiet && (
              <dl className="geo3d-soi-ky-thuat">
                <dt>Loại</dt>
                <dd>{dangChon.type}</dd>
                <dt>Phép dựng</dt>
                <dd>{dangChon.producer ?? "dữ kiện đề cho"}</dd>
                <dt>Dựa trên</dt>
                <dd>{directDependencies(day, dangChon.id).join(", ") || "—"}</dd>
                {dangChon.source?.fact_id && (
                  <>
                    <dt>Dữ kiện</dt>
                    <dd>{dangChon.source.fact_id}</dd>
                  </>
                )}
                {dangChon.source?.assumption && (
                  <>
                    <dt>Giả thiết</dt>
                    <dd>{dangChon.source.assumption}</dd>
                  </>
                )}
              </dl>
            )}
          </aside>
        )}

        {/* NGĂN KÉO — phủ lên khung, KHÔNG bóp khung lại. */}
        {ngan && (
          <aside
            className="geo3d-ngan"
            aria-label={ngan === "de" ? "Đề bài" : "Các thành phần của hình"}
          >
            <div className="geo3d-ngan-dau">
              <h4 className="geo3d-ngan-tieu">
                {ngan === "de" ? "Đề bài" : "Các thành phần của hình"}
              </h4>
              <button
                type="button"
                className="geo3d-soi-dong"
                onClick={() => setNgan(null)}
                aria-label="Đóng"
              >
                <IconClose />
              </button>
            </div>
            {ngan === "de" ? (
              <p className="geo3d-de">{de}</p>
            ) : (
              <ul className="geo3d-tree">
                {cay.map((n) => (
                  <NutCay key={n.id} nut={n} chon={tt.selected_id}
                          onChon={chon} coMat={coMat} chiTiet={chiTiet} />
                ))}
              </ul>
            )}
          </aside>
        )}
      </div>

      {/* ── ĐÁY: một dòng nói bước này đang làm gì ─────────────────────── */}
      <p className="geo3d-buoc">
        <span className="geo3d-buoc-so">
          {`Bước ${tt.current_step + 1}/${stepCount(day)}`}
        </span>
        <span className="geo3d-buoc-loi">{narrationAt(day, tt.current_step)}</span>
      </p>
    </div>
  );
}

/** Chỉ để test: id nào là thực thể con của khối nào. */
export const _phuTro = { isSubEntity, parentSolidOf };

/** Chỉ để test: câu mô tả một dòng cho ô soi. */
export const _moTaNgan = moTaNgan;

/** Chỉ để test: bảng cách gọi của học sinh. */
export const _VAI_TRO = VAI_TRO;
