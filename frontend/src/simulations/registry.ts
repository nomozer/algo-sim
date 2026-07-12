import type { Domain, InteractionMode, SimulationModule, VisualMode } from "./types";

/**
 * Simulation registry — thêm domain mới = đăng ký module mới,
 * KHÔNG sửa lõi hệ thống, không switch-case trung tâm.
 */

const registry = new Map<string, SimulationModule<unknown, unknown>>();

export function registerSimulation<C, S>(module: SimulationModule<C, S>): void {
  if (registry.has(module.id)) {
    throw new Error(`Simulation "${module.id}" đã được đăng ký trước đó.`);
  }
  if (!/^[a-z_]+\.[a-z0-9_]+$/.test(module.id)) {
    throw new Error(`Simulation id "${module.id}" phải có dạng "<domain>.<tên>".`);
  }
  registry.set(module.id, module as SimulationModule<unknown, unknown>);
}

export function getSimulation(id: string): SimulationModule<unknown, unknown> | undefined {
  return registry.get(id);
}

export interface SimulationMeta {
  id: string;
  domain: Domain;
  title: string;
  interactionMode: InteractionMode;
  supportedVisualModes: VisualMode[];
  hasTimeline: boolean;
}

/** Danh mục cho UI catalog và cho skill classify (backend giữ bản chiếu). */
export function listSimulations(): SimulationMeta[] {
  return [...registry.values()].map((m) => ({
    id: m.id,
    domain: m.domain,
    title: m.title,
    interactionMode: m.interactionMode,
    supportedVisualModes: m.supportedVisualModes,
    hasTimeline: Boolean(m.timeline),
  }));
}

/** Chỉ dùng trong test — dọn registry giữa các test case. */
export function clearRegistryForTest(): void {
  registry.clear();
}
