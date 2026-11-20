import { createRoot } from "react-dom/client";
import { useRoute, useLocation } from "wouter";
import "./styles.css";
import { Logo } from "@pmndrs/branding";
import { EnterPortalsRefApp } from "./EnterPortalsRefApp";

/*
Model JSX / transformed assets from https://github.com/pmndrs/examples/tree/main/examples/enter-portals
Author: Omar Faruq Tawsif (https://sketchfab.com/omarfaruqtawsif32)
License: CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/)
*/

function Root() {
  const [, params] = useRoute("/item/:id");
  const [, setLocation] = useLocation();
  return (
    <>
      <EnterPortalsRefApp />
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        <a
          href="https://pmnd.rs/"
          style={{
            position: "absolute",
            bottom: 40,
            left: 90,
            fontSize: "13px",
          }}
        >
          pmnd.rs
          <br />
          dev collective
        </a>
        <div
          style={{
            position: "absolute",
            bottom: 40,
            right: 40,
            fontSize: "13px",
          }}
        >
          15/06/2023
        </div>
        <Logo
          style={{ position: "absolute", bottom: 40, left: 40, width: 30 }}
        />
        <a
          style={{ position: "absolute", top: 40, left: 40, fontSize: "13px" }}
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setLocation("/");
          }}
        >
          {params ? "< back" : "double click to enter portal"}
        </a>
      </div>
    </>
  );
}

const rootEl = document.getElementById("root");
if (rootEl) {
  createRoot(rootEl).render(<Root />);
}
