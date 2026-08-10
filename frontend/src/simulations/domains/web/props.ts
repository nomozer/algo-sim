/**
 * MIỀN GIÁ TRỊ — chỗ "bounded" trở thành thật. Mirror của
 * `backend/app/simulation/catalog.py::validate_web_style_config`; hai tầng cùng
 * luật, đúng khuôn validate hai tầng của mọi domain khác.
 */
export type WebProp =
  | "backgroundColor" | "color" | "fontSize" | "padding" | "borderRadius";

export const COLOR_CHOICES = [
  { value: "#ffffff", label: "Trắng" },
  { value: "#fde68a", label: "Vàng" },
  { value: "#fca5a5", label: "Đỏ nhạt" },
  { value: "#a7f3d0", label: "Xanh lá nhạt" },
  { value: "#bfdbfe", label: "Xanh dương nhạt" },
  { value: "#e9d5ff", label: "Tím nhạt" },
  { value: "#1f2937", label: "Xám đậm" },
] as const;

export const TEXT_COLOR_CHOICES = [
  { value: "#1f2937", label: "Đen" },
  { value: "#b91c1c", label: "Đỏ" },
  { value: "#1d4ed8", label: "Xanh dương" },
  { value: "#047857", label: "Xanh lá" },
  { value: "#ffffff", label: "Trắng" },
] as const;

export const NUMERIC_RANGE = {
  fontSize: { min: 12, max: 48, step: 2, unit: "px", label: "Cỡ chữ" },
  padding: { min: 0, max: 48, step: 4, unit: "px", label: "Đệm trong" },
  borderRadius: { min: 0, max: 40, step: 2, unit: "px", label: "Bo góc" },
} as const;

export const NUMERIC_PROPS = ["fontSize", "padding", "borderRadius"] as const;
