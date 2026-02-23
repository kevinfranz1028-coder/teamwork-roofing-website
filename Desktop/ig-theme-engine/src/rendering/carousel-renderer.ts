import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { getBrowser } from './browser-pool.js';
import { hookSlideHtml, valueSlideHtml, ctaSlideHtml } from './templates.js';
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

  const browser = await getBrowser();
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });

  const paths: string[] = [];

  try {
    for (const slide of slides) {
      let html: string;
      if (slide.type === 'hook') {
        html = hookSlideHtml(slide, renderConfig);
      } else if (slide.type === 'cta') {
        html = ctaSlideHtml(slide, renderConfig);
      } else {
        html = valueSlideHtml(slide, renderConfig);
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
