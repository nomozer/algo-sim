/// <reference types="vite/client" />
import type { BufferGeometryNode } from "@react-three/fiber";
import type { RoundedPlaneGeometry } from "maath/geometry";

declare global {
  namespace JSX {
    interface IntrinsicElements {
      roundedPlaneGeometry: BufferGeometryNode<
        RoundedPlaneGeometry,
        typeof RoundedPlaneGeometry
      >;
    }
  }
}
