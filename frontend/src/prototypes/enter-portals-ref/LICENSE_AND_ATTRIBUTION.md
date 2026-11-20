# Gate 1 Reference Reconstruction — License & Attribution Notice

This directory (`frontend/src/prototypes/enter-portals-ref/`) is an **isolated Gate 1 reference reconstruction** of the upstream `enter-portals` example from `pmndrs/examples` for fidelity comparison only. It is NOT integrated into Axo production routes or bundles.

## 1. Upstream Code License (MIT)

Source repository: `https://github.com/pmndrs/examples/tree/main/examples/enter-portals`
Author (example metadata `pmndrs.json`): Paul Henschel (`publishedAt: 2023-06-14`)

```text
MIT License

Copyright (c) 2024 Poimandres

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 2. 3D Model Assets (`CC-BY-4.0`)

Credited in upstream `examples/enter-portals/src/index.tsx`:
- Author: **Omar Faruq Tawsif** (`https://sketchfab.com/omarfaruqtawsif32`)
- License: **CC-BY-4.0** (`http://creativecommons.org/licenses/by/4.0/`)

Asset verification from binary GLB JSON headers:
1. `assets/pickles_3d_version_of_hyuna_lees_illustration-transformed.glb` (`153,628 B`):
   - Title: `"Pickles" 3d version of Hyuna Lee's illustration`
   - Embedded GLB `asset.extras`: `Omar Faruq Tawsif`, `CC-BY-4.0`, Sketchfab URL verified.
2. `assets/still_life_based_on_heathers_artwork-transformed.glb` (`363,456 B`):
   - Title: `Still life, Based on Heather's artwork`
   - Embedded GLB `asset.extras`: `Omar Faruq Tawsif`, `CC-BY-4.0`, Sketchfab URL verified.
3. `assets/fiesta_tea-transformed.glb` (`2,284,160 B`):
   - Credited in upstream `src/index.tsx` to Omar Faruq Tawsif (`CC-BY-4.0`).
   - Audit note: embedded `asset.extras` metadata was stripped when upstream ran `gltf-transform`. Retained strictly for Gate 1 reference verification; will NOT be carried into Gate 2 Axo integration.

## 3. Font & Decoder Assets

- **Inter font (`@pmndrs/assets/fonts/inter_regular.woff`, `inter_medium.woff` & `rsms.me/inter/inter.css`):** SIL Open Font License 1.1.
- **Draco glTF Decoder (`public/draco/*`):** Apache-2.0, copied locally from installed `three/examples/jsm/libs/draco/gltf/`.
