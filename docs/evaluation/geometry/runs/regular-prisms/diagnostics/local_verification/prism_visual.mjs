// LOCAL visual check: replay real envelopes through the repository's own openFixture (compiler-scene-suite.mjs) on a
// `vite preview` of the built app, wait for the 3D canvas, screenshot. No frontend file changed; 0 model calls.
import { readFileSync } from "node:fs";
import { openFixture } from "file:///D:/Documents/projects/algo-sim/frontend/scripts/compiler-scene-suite.mjs";

const [port, dir, ...rows] = process.argv.slice(2);
const viewport = { id: "desktop", width: 1440, height: 900 };
for (const row of rows) {
  const fixture = JSON.parse(readFileSync(`${dir}/${row}.fixture.json`, "utf8"));
  const { session, analyzeCalls } = await openFixture({ port: Number(port), viewport, fixture });
  try {
    const t0 = Date.now();
    let canvas = false;
    while (Date.now() - t0 < 30_000 && !canvas) {
      canvas = await session.eval(`!!document.querySelector('.geo3d-canvas canvas')`);
      if (!canvas) await new Promise((r) => setTimeout(r, 250));
    }
    await new Promise((r) => setTimeout(r, 1500));
    for (let i = 0; i < 6; i++) {               // step the formation timeline to its last step ("Bước sau")
      await session.eval(`(()=>{const b=[...document.querySelectorAll("button")].find(x=>x.textContent.trim()==="Bước sau");if(b&&!b.disabled)b.click();})()`);
      await new Promise((r) => setTimeout(r, 700));
    }
    await new Promise((r) => setTimeout(r, 1500));
    const body = await session.eval(`document.body.innerText`);
    await session.screenshot(`${dir}/${row}.png`);
    console.log(JSON.stringify({ row, canvas, analyzeCalls: analyzeCalls(),
      step: (body.match(/Bước \d+\/\d+/) || [""])[0], bodyHasValue: body.includes(fixture.envelope.scene3d.objects.find((o) => o.id === "V").value), refusalShown: /không thể|từ chối/i.test(body) }));
  } finally {
    await session.close();
  }
}
