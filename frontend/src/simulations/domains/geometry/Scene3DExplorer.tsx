/**
 * KHỐI THĂM DÒ hình 3D — cây phân rã + khung nhìn + ô soi, một trạng thái.
 *
 * ─── MỘT THẨM QUYỀN CHỌN, KHÔNG HAI ─────────────────────────────────────
 *
 * `InteractionState` sống ở ĐÂY và chỉ ở đây. Cây và khung nhìn đều đọc
 * `selected_id` của nó, và cả hai đều báo về bằng cùng một hàm. Giữ thêm
 * `treeSelected`/`viewportSelected` là mời hai bản lệch nhau — và lúc ấy học
 * sinh bấm một mặt trong khung rồi thấy cây sáng ở chỗ khác.
 *
 * ─── ĐIỀU KHỐI NÀY KHÔNG LÀM ────────────────────────────────────────────
 *
 * Không gọi mạng, không gọi LLM, không sửa `Scene3D`. Mọi thao tác chỉ đổi
 * cách nhìn. Thực thể con (mặt, cạnh) do `withSubEntities` sinh ra một lần và
 * là **dữ liệu nhìn** — chúng không quay ngược về `GeometryState`.
 */
import { useMemo, useState } from "react";
import type { Scene3D } from "./scene3d-model";
import { objectsAt } from "./scene3d-model";
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
  reset,
  select,
  semanticTree,
  showAll,
  taoTrangThai,
} from "./interaction-state";
import {
  entitiesPresentAt,
  isSubEntity,
  parentSolidOf,
  withSubEntities,
} from "./scene3d-subentities";
import { Scene3DPlayer } from "./scene3d-playback";

const NHOM_BUNG = "face";

function NutCay({
  nut, chon, onChon, coMat,
}: {
  nut: TreeNode;
  chon: string | null;
  onChon: (id: string) => void;
  coMat: ReadonlySet<string>;
}) {
  const con = nut.children.map((c) => (
    <NutCay key={c.id} nut={c} chon={chon} onChon={onChon} coMat={coMat} />
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
        {nut.label}
        <span className="geo3d-tree-type">{nut.type}</span>
      </button>
      {nut.children.length > 0 && <ul>{con}</ul>}
    </li>
  );
}

export function Scene3DExplorer({ scene }: { scene: Scene3D }) {
  // Sinh MỘT LẦN cho mỗi cảnh: mặt và cạnh là hàm thuần của topology, nên tính
  // lại mỗi lần vẽ chỉ tốn công và làm id đổi tham chiếu vô cớ.
  const day = useMemo(() => withSubEntities(scene), [scene]);
  const cay = useMemo(() => semanticTree(day), [day]);
  const [tt, setTt] = useState<InteractionState>(taoTrangThai);

  // Phép quyết định "nút này bấm được chưa" nằm ở `entitiesPresentAt` — hàm
  // THUẦN, kiểm được không cần DOM. Component chỉ gọi nó.
  const coMat = useMemo(
    () => entitiesPresentAt(day, tt.current_step, objectsAt),
    [day, tt.current_step],
  );

  const dangChon = tt.selected_id
    ? day.objects.find((o) => o.id === tt.selected_id) ?? null
    : null;

  const chon = (id: string | null) => setTt((s) => select(s, id));

  return (
    <div className="geo3d-explorer">
      <div className="geo3d-explorer-main">
        <Scene3DPlayer
          scene={day}
          interaction={tt}
          onInteraction={setTt}
          onSelect={chon}
        />
      </div>

      <aside className="geo3d-panel" aria-label="Phân rã hình">
        <h4 className="geo3d-panel-title">Các thành phần của hình</h4>
        <ul className="geo3d-tree">
          {cay.map((n) => (
            <NutCay key={n.id} nut={n} chon={tt.selected_id} onChon={chon} coMat={coMat} />
          ))}
        </ul>

        {dangChon && (
          <div className="geo3d-inspect">
            <h4 className="geo3d-panel-title">{dangChon.label}</h4>
            <dl className="geo3d-inspect-list">
              <dt>Loại</dt>
              <dd>{dangChon.type}</dd>
              {dangChon.parent && (
                <>
                  <dt>Thuộc</dt>
                  <dd>{day.objects.find((o) => o.id === dangChon.parent)?.label
                       ?? dangChon.parent}</dd>
                </>
              )}
              <dt>Được tạo bởi</dt>
              <dd>{dangChon.producer ?? "dữ kiện đề cho"}</dd>
              <dt>Dựa trên</dt>
              <dd>
                {directDependencies(day, dangChon.id).length
                  ? directDependencies(day, dangChon.id).join(", ")
                  : "—"}
              </dd>
              {dangChon.source?.fact_id && (
                <>
                  <dt>Dữ kiện</dt>
                  <dd>{dangChon.source.fact_id}</dd>
                </>
              )}
              {dangChon.source?.assumption && (
                <>
                  <dt>Do người giải chọn</dt>
                  <dd>{dangChon.source.assumption}</dd>
                </>
              )}
            </dl>

            <div className="geo3d-actions" role="group" aria-label="Thao tác xem">
              <button
                type="button"
                className="geo3d-btn"
                onClick={() =>
                  setTt((s) => isolate(s, highlightSet(day, dangChon.id)))
                }
              >
                Chỉ xem phần này
              </button>
              <button
                type="button"
                className="geo3d-btn"
                onClick={() =>
                  setTt((s) =>
                    isolate(s, [dangChon.id, ...dependencyClosure(day, dangChon.id)]),
                  )
                }
              >
                Kèm mọi thứ nó dựa vào
              </button>
              <button
                type="button"
                className="geo3d-btn"
                onClick={() => setTt((s) => hide(s, dangChon.id))}
              >
                Ẩn
              </button>
            </div>
          </div>
        )}

        <div className="geo3d-actions" role="group" aria-label="Thao tác toàn cảnh">
          <button
            type="button"
            className="geo3d-btn"
            onClick={() =>
              setTt((s) =>
                s.exploded_groups.includes(NHOM_BUNG)
                  ? collapseAll(s)
                  : explode(s, NHOM_BUNG),
              )
            }
            disabled={!day.objects.some((o) => o.type === "face")}
          >
            {tt.exploded_groups.includes(NHOM_BUNG) ? "Ghép lại" : "Tách các mặt"}
          </button>
          <button
            type="button"
            className="geo3d-btn"
            onClick={() => setTt((s) => showAll(clearIsolate(s)))}
          >
            Hiện lại tất cả
          </button>
          <button
            type="button"
            className="geo3d-btn"
            onClick={() => setTt(reset)}
          >
            Về mặc định
          </button>
        </div>
      </aside>
    </div>
  );
}

/** Chỉ để test: id nào là thực thể con của khối nào. */
export const _phuTro = { isSubEntity, parentSolidOf };
