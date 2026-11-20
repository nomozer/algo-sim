/// <reference types="vite/client" />
import type { BufferGeometryNode } from "@react-three/fiber";
import type { RoundedPlaneGeometry } from "maath/geometry";

declare module "@pmndrs/assets/fonts/inter_regular.woff" {
  const fontUrl: string;
  export default fontUrl;
}

declare module "@pmndrs/assets/fonts/inter_medium.woff" {
  const fontUrl: string;
  export default fontUrl;
}

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
