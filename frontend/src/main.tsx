import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AppRoot } from "./App";
import { registerAllSimulations } from "./simulations";
import { useAppStore } from "./state/store";
import "./styles/global.css";

registerAllSimulations();

if (typeof window !== "undefined") {
  (window as any).__ALGO_SIM_STORE__ = useAppStore;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* `AppRoot` = `App` bọc trong lưới chặn NGOÀI. Điểm vào dựng nó, không
        dựng `App` trần: bọc ở đây mới phủ được cả vỏ (thanh trên, cột trái,
        `AuthGate`) — bọc bên trong `App` thì chính chỗ vỡ nằm ngoài lưới. */}
    <AppRoot />
  </StrictMode>,
);
