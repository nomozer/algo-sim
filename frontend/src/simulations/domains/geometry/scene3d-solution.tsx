import { useId, useState } from "react";
import {
  geometryHighlightedAt,
  hienSo,
  solutionAt,
  type Scene3D,
  type SolutionItem,
} from "./scene3d-model";
import { tangNhanManh, type TangNhanManh } from "./interaction-state";

/**
 * LỚP LỜI GIẢI — bảng dưới thanh bước (W12, review NEEDS_CHANGES).
 *
 * Thanh bước nay chỉ đi qua bước DỰNG HÌNH; mọi con số — dữ kiện đề cho, các
 * bước tính (công thức, nguồn số), kết quả — dồn về MỘT bảng thứ cấp ở đây,
 * đồng bộ với bước dựng đang xem. Dải số đo nổi trên khung 3D đã gỡ: khung là
 * của hình, số là của chữ.
 *
 * Đáp số xuất hiện ĐÚNG MỘT lần — ở mục Kết quả, bấm được để xem chuỗi nhân
 * quả. Màu một dòng theo vai trò của nó trong chuỗi quanh vật đang chọn, cùng
 * token với khung 3D (`scene3d-roles.ts`), nên xanh/cam đậm/cam nhạt/xám mang
 * một nghĩa ở cả hai nơi.
 *
 * Khổ hẹp: Dữ kiện và Các bước tính gập được; Kết quả luôn hiện.
 */

/** Lớp CSS của một dòng theo tầng causal; ngoài chuỗi thì dịu. */
export function lopDongLoiGiai(
  id: string, tang: ReadonlyMap<string, TangNhanManh> | null,
): string {
  if (!tang) return "geo3d-lg-dong";
  const t = tang.get(id);
  const vai = t === "dich" ? " la-chon" : t === "du_kien_so" ? " la-so-lieu"
    : t === "trung_gian" ? " la-trung-gian" : t ? " la-boi-canh" : " la-diu";
  return `geo3d-lg-dong${vai}`;
}

const CHU_GIAI_VAI_TRO: { lop: string; chu: string }[] = [
  { lop: "la-chon", chu: "Đang xét" },
  { lop: "la-so-lieu", chu: "Dữ kiện số" },
  { lop: "la-trung-gian", chu: "Đại lượng trung gian" },
  { lop: "la-boi-canh", chu: "Hình liên quan" },
];

interface Props {
  scene: Scene3D;
  /** Khung đang hiện (sự kiện neo của một bước dựng). */
  step: number;
  selectedId?: string | null;
  onSelect?: (id: string | null) => void;
}

export function Scene3DSolution({ scene, step, selectedId = null, onSelect }: Props) {
  const [moRong, setMoRong] = useState(false);
  const idThan = useId();
  const lg = solutionAt(scene, step);
  if (lg.givens.length + lg.steps.length + lg.results.length === 0) return null;

  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const tang = selectedId ? tangNhanManh(scene, selectedId) : null;
  const kyHieu = (id: string) => {
    const o = theoId.get(id);
    return o?.reference || o?.notation || o?.label || "";
  };
  const vuaDung = !tang && geometryHighlightedAt(scene, step).length > 0;

  const dong = (x: SolutionItem, coTieuDe: boolean) => {
    const o = theoId.get(x.id)!;
    const ten = o.notation || o.label;
    return (
      <li key={x.id} className={lopDongLoiGiai(x.id, tang)} data-solution-id={x.id}
          data-moi={x.isNew ? "true" : undefined}>
        <button
          type="button"
          className="geo3d-lg-nut"
          onClick={() => onSelect?.(selectedId === x.id ? null : x.id)}
          aria-pressed={selectedId === x.id}
        >
          {coTieuDe && o.label !== ten && <span className="geo3d-lg-tieu-de">{o.label}</span>}
          <span className="geo3d-lg-so">
            {x.formula ?? `${ten} = ${hienSo(o.exact, o.value)}`}
          </span>
        </button>
        {x.basis.length > 0 && (
          <span className="geo3d-lg-dua-tren">
            {`Dựa trên: ${x.basis.map(kyHieu).filter(Boolean).join(", ")}`}
          </span>
        )}
      </li>
    );
  };

  return (
    <section className="geo3d-loi-giai" aria-label="Lời giải">
      {lg.results.length > 0 && (
        <div className="geo3d-lg-muc geo3d-lg-ket-qua">
          <h4 className="geo3d-lg-ten-muc">Kết quả</h4>
          <ul className="geo3d-lg-ds">{lg.results.map((x) => dong(x, true))}</ul>
        </div>
      )}
      <button
        type="button"
        className="geo3d-lg-gap"
        onClick={() => setMoRong((m) => !m)}
        aria-expanded={moRong}
        aria-controls={idThan}
      >
        {moRong ? "Ẩn dữ kiện và các bước tính" : "Xem dữ kiện và các bước tính"}
      </button>
      <div id={idThan} className={`geo3d-lg-than${moRong ? " la-mo" : ""}`}>
        {lg.givens.length > 0 && (
          <div className="geo3d-lg-muc">
            <h4 className="geo3d-lg-ten-muc">Dữ kiện</h4>
            <ul className="geo3d-lg-ds">{lg.givens.map((x) => dong(x, false))}</ul>
          </div>
        )}
        {lg.steps.length > 0 && (
          <div className="geo3d-lg-muc">
            <h4 className="geo3d-lg-ten-muc">Các bước tính</h4>
            <ul className="geo3d-lg-ds">{lg.steps.map((x) => dong(x, true))}</ul>
          </div>
        )}
      </div>
      {(tang || vuaDung) && (
        <ul className="geo3d-chu-giai" aria-label="Chú giải màu">
          {(tang ? CHU_GIAI_VAI_TRO : [{ lop: "la-chon", chu: "Vừa dựng ở bước này" }])
            .map((m) => (
              <li key={m.lop} className={`geo3d-chu-giai-muc ${m.lop}`}>{m.chu}</li>
            ))}
        </ul>
      )}
    </section>
  );
}
