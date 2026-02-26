import path from 'path';
import { mkdirSync, existsSync, readFileSync } from 'fs';
import { getBrowser } from './browser-pool.js';
import { hookSlideHtml, valueSlideHtml, ctaSlideHtml } from './templates.js';
import type { SlideContent, RenderConfig } from './types.js';
import { findAndDownloadPhoto } from '../integrations/pexels-api.js';
import { CONFIG } from '../config/env.js';

/**
 * Render carousel slides as 1080x1080 PNGs via Pexels stock photos + Puppeteer.
 */
export async function renderCarouselSlides(
  slides: SlideContent[],
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string[]> {
  const outputDir = path.join(CONFIG.paths.assets, `carousel-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  // ─── Step 1: Download Pexels stock photo backgrounds ───
  console.log('  Downloading Pexels stock photo backgrounds...');
  const bgPaths: (string | null)[] = [];
  for (let i = 0; i < slides.length; i++) {
    const slide = slides[i];
    const searchTerms = slide.pexelsSearch || (slide.designNotes ? [slide.designNotes] : []);
    console.log(`    bg ${i + 1}/${slides.length}...`);
    try {
      const result = await findAndDownloadPhoto(
        searchTerms,
        outputDir,
        `bg-${i}.png`,
        'square',
        scriptId,
        i
      );
      bgPaths.push(result.path);
    } catch (err: any) {
      console.log(`    bg ${i + 1} failed: ${err.message.slice(0, 80)}`);
      bgPaths.push(null);
    }
    // Rate limit: at least 1s between API calls
    if (i < slides.length - 1) {
      await new Promise(r => setTimeout(r, 1000));
    }
  }

  // ─── Step 2: Render slides with Puppeteer (text overlay on stock photo backgrounds) ───
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

  const rawSlides: any[] = Array.isArray(parsed) ? parsed
    : parsed.slides ? parsed.slides
    : parsed.carousel?.slides ? parsed.carousel.slides
    : [];

  return rawSlides.map((s: any, i: number) => ({
    slideNumber: s.slideNumber || i + 1,
    headline: s.headline || s.title || '',
    bodyText: s.bodyText || s.body || s.text || '',
    designNotes: s.designNotes || '',
    pexelsSearch: Array.isArray(s.pexelsSearch) ? s.pexelsSearch : undefined,
    type: i === 0 ? 'hook' as const
      : i === rawSlides.length - 1 ? 'cta' as const
      : 'value' as const,
  }));
}
