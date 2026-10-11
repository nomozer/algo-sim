import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Scene3DWorkspace } from "../src/simulations/domains/geometry/scene3d-view";
import { TRANG_THAI_DAU } from "../src/simulations/domains/geometry/interaction-state";
import rows from "../../docs/evaluation/geometry/runs/geometry-library-expansion/offline-certification/scenes.json";
import "../src/styles/global.css";

function Harness() {
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [aux, setAux] = useState(false);
  const row = rows[index];
  (window as any).__expansion_scene = row.scene;
  return <main style={{ padding: 16, height: "100vh" }}>
    <h1>LOCAL / fake-provider / {row.id}</h1>
    <select aria-label="Scene" value={index} onChange={e => { setIndex(Number(e.target.value)); setSelected(null); }}>
      {rows.map((r, i) => <option key={r.id} value={i}>{r.id}</option>)}
    </select>
    <label><input type="checkbox" checked={aux} onChange={e => setAux(e.target.checked)} /> Hình phụ</label>
    <button onClick={() => setSelected(index % 4 === 0 ? "O" : "H")}>Chọn điểm dựng</button>
    <p>Không gọi API. Điểm mới có provenance/producer/dependencies; đây không phải pilot.</p>
    <div style={{ height: "75vh", minHeight: 440 }}>
      <Scene3DWorkspace scene={row.scene as any} step={9999} interaction={{ ...TRANG_THAI_DAU, selected_id: selected }} onSelect={setSelected} auxiliaryShown={aux} />
    </div>
  </main>;
}
createRoot(document.getElementById("root")!).render(<Harness />);
