// Playwright ile kareleri çizip ffmpeg'e borular.
// Kullanım: node src/render.js <çıktı.mp4> [fps] [başlangıç] [bitiş]
//           node src/render.js --stills <klasör> t1,t2,...
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

(async () => {
  const root = path.resolve(__dirname, "..");
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on("pageerror", (e) => { console.error("Sayfa hatası:", e.message); process.exit(1); });
  await page.goto("file://" + path.join(root, "web", "index.html"));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => Promise.all([...document.fonts].map((f) => f.load())));
  const grab = (t) => page.evaluate((t) => { renderFrame(t); return document.getElementById("c").toDataURL("image/jpeg", 0.96).split(",")[1]; }, t);

  if (process.argv[2] === "--stills") {
    const dir = process.argv[3]; fs.mkdirSync(dir, { recursive: true });
    for (const t of process.argv[4].split(",").map(Number)) {
      // fizik için sıralı simülasyon renderFrame içinde yapılır
      const b64 = await page.evaluate((t) => { renderFrame(t); return document.getElementById("c").toDataURL("image/png").split(",")[1]; }, t);
      fs.writeFileSync(path.join(dir, `kare_${t.toFixed(2)}.png`), Buffer.from(b64, "base64"));
    }
    await browser.close(); return;
  }
  const out = process.argv[2], fps = +(process.argv[3] || 30);
  const total = await page.evaluate(() => TOTAL);
  const t0 = +(process.argv[4] || 0), t1 = +(process.argv[5] || total);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
  const n = Math.round((t1 - t0) * fps);
  for (let i = 0; i < n; i++) {
    const b64 = await grab(t0 + i / fps);
    if (!ff.stdin.write(Buffer.from(b64, "base64"))) await new Promise((r) => ff.stdin.once("drain", r));
    if (i % 60 === 0) process.stdout.write(`\r  kare ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on("close", r));
  process.stdout.write(`\r  kare ${n}/${n}\n`);
  await browser.close();
})();
