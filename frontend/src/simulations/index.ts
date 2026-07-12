import { registerAlgorithmDomain } from "./domains/algorithm";
import { registerBinaryDomain } from "./domains/binary";
import { registerGenericDomain } from "./domains/generic";
import { registerLogicDomain } from "./domains/logic";
import { registerNetworkDomain } from "./domains/network";

export * from "./types";
export { getSimulation, listSimulations, registerSimulation } from "./registry";
export { fromLegacyAnalysis, toSimulationId } from "./legacy";

let registered = false;

/**
 * Đăng ký toàn bộ domain vào registry (gọi một lần khi app khởi động).
 * Thêm domain mới = thêm một dòng ở đây — KHÔNG sửa lõi (M5 §1).
 */
export function registerAllSimulations(): void {
  if (registered) return;
  registered = true;
  registerAlgorithmDomain();
  registerLogicDomain();
  registerBinaryDomain();
  registerNetworkDomain();
  registerGenericDomain();
}
