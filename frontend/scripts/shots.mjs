import { chromium } from "playwright";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/screenshots");
const URL = "http://127.0.0.1:1420";

const setLook = (page, skin, palette) =>
  page.evaluate(([s, p]) => {
    document.documentElement.dataset.skin = s;
    document.documentElement.dataset.palette = p;
  }, [skin, palette]);

const nav = async (page, label, ms = 1600) => {
  await page.locator(`aside button:has-text("${label}")`).first().click();
  await page.waitForTimeout(ms);
};

const sections = [
  ["Seguridad", "02-security"], ["Procesos", "03-processes"], ["Memoria", "04-memory"],
  ["Red", "05-network"], ["Optimizar", "06-optimization"], ["Juegos", "07-gaming"],
  ["Privacidad", "08-privacy"], ["Endurecimiento", "09-hardening"], ["Auditoría", "10-audit"],
  ["Amenazas", "11-threat"], ["Ajustes", "12-settings"],
];

const run = async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1360, height: 900 }, deviceScaleFactor: 1 });
  await page.goto(URL, { waitUntil: "load" });
  await page.waitForTimeout(2500);

  // ── Empresarial (sober) · Nord ──────────────────────────────
  await setLook(page, "sober", "nord");
  await page.waitForTimeout(600);
  await page.locator('aside button:has-text("Inicio")').first().click();
  await page.waitForTimeout(12000); // let the security audit populate the score
  await page.screenshot({ path: `${OUT}/01-dashboard.png` });
  for (const [label, name] of sections) {
    await nav(page, label);
    await page.screenshot({ path: `${OUT}/${name}.png` });
  }

  // ── Palettes (Empresarial) on the dashboard ─────────────────
  await nav(page, "Inicio", 1200);
  for (const pal of ["mono", "forest", "gray", "transparent"]) {
    await setLook(page, "sober", pal);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${OUT}/palette-${pal}.png` });
  }

  // ── Gamer (Free) neon skin ──────────────────────────────────
  await setLook(page, "gamer", "nord");
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/gamer-dashboard.png` });
  await nav(page, "Optimizar");
  await page.screenshot({ path: `${OUT}/gamer-optimization.png` });

  // ── Command palette (Ctrl+K) ────────────────────────────────
  await setLook(page, "sober", "nord");
  await nav(page, "Inicio", 800);
  await page.keyboard.press("Control+K");
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${OUT}/command-palette.png` });

  await browser.close();
  console.log("screenshots done");
};

run().catch((e) => { console.error(e); process.exit(1); });
