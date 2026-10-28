// Screenshot rendered slide HTML to PNG at exactly 1080x1350.
// Usage: node shoot.cjs <buildDir> <outDir> <name> [<name> ...]
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const [buildDir, outDir, ...names] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  for (const name of names) {
    await page.goto("file://" + path.resolve(buildDir, name + ".html"));
    await page.evaluate(() => document.fonts.ready);
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: path.resolve(outDir, name + ".png"), clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
