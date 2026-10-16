const { chromium } = require('playwright');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const ctx = await b.newContext({ acceptDownloads: true, userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36' });
  const p = await ctx.newPage();
  let buf = null;
  p.on('response', async r => { try { if ((r.headers()['content-type']||'').includes('pdf')) buf = await r.body(); } catch {} });
  const dl = p.waitForEvent('download', { timeout: 30000 }).catch(() => null);
  try { await p.goto(url, { waitUntil: 'networkidle', timeout: 45000 }); } catch (e) {}
  const d = await Promise.race([dl, new Promise(r => setTimeout(() => r(null), 8000))]);
  if (d) await d.saveAs(out); else if (buf) require('fs').writeFileSync(out, buf);
  else { console.error('no pdf; title=' + await p.title().catch(()=>'')); process.exitCode = 1; }
  await b.close();
})();
