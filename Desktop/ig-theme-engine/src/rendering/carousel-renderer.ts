import path from 'path';
import { mkdirSync, existsSync, readFileSync } from 'fs';
import { getBrowser } from './browser-pool.js';
import { hookSlideHtml, valueSlideHtml, ctaSlideHtml } from './templates.js';
import { generateBackground } from '../integrations/replicate-api.js';
import type { SlideContent, RenderConfig } from './types.js';
import { CONFIG } from '../config/env.js';

/**
 * Render carousel slides as 1080x1080 PNGs via Puppeteer.
 * Returns an array of local file paths.
 */
export async function renderCarouselSlides(
  slides: SlideContent[],
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string[]> {
  const outputDir = path.join(CONFIG.paths.assets, `carousel-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  // Generate AI background images sequentially, respecting rate limits
  console.log('  Generating AI carousel backgrounds...');
  const bgPaths: (string | null)[] = [];
  for (let i = 0; i < slides.length; i++) {
    const slide = slides[i];
    const prompt = slide.designNotes
      || `professional ${CONFIG.app.niche} visual, clean aesthetic, square format`;
    console.log(`    bg ${i + 1}/${slides.length}...`);
    const startTime = Date.now();
    try {
      bgPaths.push(await generateBackground(prompt, outputDir, `bg-${i}.png`, '1:1'));
    } catch (err: any) {
      console.log(`    bg ${i + 1} failed: ${err.message.slice(0, 80)}`);
      bgPaths.push(null);
    }
    // Ensure at least 10s between API calls (rate limit reset window)
    if (i < slides.length - 1) {
      const elapsed = Date.now() - startTime;
      const waitMs = Math.max(0, 10000 - elapsed);
      if (waitMs > 0) await new Promise(r => setTimeout(r, waitMs));
    }
  }

  const browser = await getBrowser();
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });

  const paths: string[] = [];

  try {
    for (let i = 0; i < slides.length; i++) {
      const slide = slides[i];
      const bgUrl = bgPaths[i]
        ? `data:image/png;base64,${readFileSync(bgPaths[i]!).toString('base64')}`
        : undefined;

      let html: string;
      if (slide.type === 'hook') {
        html = hookSlideHtml(slide, renderConfig, bgUrl);
      } else if (slide.type === 'cta') {
        html = ctaSlideHtml(slide, renderConfig, bgUrl);
      } else {
        html = valueSlideHtml(slide, renderConfig, bgUrl);
      }

      await page.setContent(html, { waitUntil: 'domcontentloaded' });
      // Allow fonts to load (with 3s timeout fallback)
      await page.evaluate(() => Promise.race([
        document.fonts.ready,
        new Promise(r => setTimeout(r, 3000)),
      ]));

      const outputPath = path.join(outputDir, `slide-${String(slide.slideNumber).padStart(2, '0')}.png`);
      await page.screenshot({ path: outputPath, type: 'png' });
      paths.push(outputPath);
    }
  } finally {
    await page.close();
  }

  return paths;
}

/**
 * Parse a content_scripts row's script_json into SlideContent[].
 */
export function parseCarouselScript(scriptJson: string): SlideContent[] {
  const parsed = JSON.parse(scriptJson);

  // Handle both flat array and nested { slides: [...] } shapes
  const rawSlides: any[] = Array.isArray(parsed) ? parsed
    : parsed.slides ? parsed.slides
    : parsed.carousel?.slides ? parsed.carousel.slides
    : [];

  return rawSlides.map((s: any, i: number) => ({
    slideNumber: s.slideNumber || i + 1,
    headline: s.headline || s.title || '',
    bodyText: s.bodyText || s.body || s.text || '',
    designNotes: s.designNotes || '',
    type: i === 0 ? 'hook' as const
      : i === rawSlides.length - 1 ? 'cta' as const
      : 'value' as const,
  }));
}
