import path from 'path';
import { mkdirSync, existsSync, readFileSync } from 'fs';
import { getBrowser } from './browser-pool.js';
import { hookSlideHtml, valueSlideHtml, ctaSlideHtml } from './templates.js';
import type { SlideContent, RenderConfig } from './types.js';
import type { VisualBrief } from '../visual-intelligence/types.js';
import { planVisualsBatch } from '../visual-intelligence/creative-director.js';
import { generateImage } from '../visual-intelligence/image-router.js';
import { getStyleAnchor } from '../visual-intelligence/knowledge/style-anchors.js';
import { CONFIG } from '../config/env.js';

/**
 * Render carousel slides as 1080x1080 PNGs via Visual Intelligence + Puppeteer.
 */
export async function renderCarouselSlides(
  slides: SlideContent[],
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string[]> {
  const outputDir = path.join(CONFIG.paths.assets, `carousel-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  // ─── Step 1: Creative Director plans visuals for all slides at once ───
  console.log('  Creative Director planning carousel visuals...');
  const anchor = getStyleAnchor();
  const briefs: VisualBrief[] = slides.map((slide, i) => ({
    contentType: 'carousel' as const,
    segmentType: slide.type === 'hook' ? 'hook' : slide.type === 'cta' ? 'cta' : 'body',
    segmentIndex: i,
    totalSegments: slides.length,
    onScreenText: `${slide.headline}\n${slide.bodyText}`,
    originalVisualDescription: slide.designNotes || `professional ${CONFIG.app.niche} visual, clean aesthetic`,
    brandContext: {
      niche: CONFIG.app.niche || 'Houseplant ICU',
      stylePrefix: anchor.imageStylePrefix,
      colorPalette: [renderConfig.brandColors.primary, renderConfig.brandColors.secondary, renderConfig.brandColors.accent],
      mood: slide.type === 'hook' ? 'dramatic, scroll-stopping' : slide.type === 'cta' ? 'warm, inviting' : 'informative, clear',
    },
  }));

  const plans = await planVisualsBatch(briefs);

  // ─── Step 2: Generate AI backgrounds via Image Router (with Quality Gate) ───
  console.log('  Generating AI carousel backgrounds...');
  const bgPaths: (string | null)[] = [];
  for (let i = 0; i < slides.length; i++) {
    console.log(`    bg ${i + 1}/${slides.length}...`);
    try {
      // Override aspect ratio to 1:1 for carousel
      const plan = { ...plans[i], aspectRatio: '1:1' as const };
      const result = await generateImage(plan, briefs[i], outputDir, `bg-${i}.png`);
      bgPaths.push(result.path);
    } catch (err: any) {
      console.log(`    bg ${i + 1} failed: ${err.message.slice(0, 80)}`);
      bgPaths.push(null);
    }
    // Rate limit: at least 3s between API calls
    if (i < slides.length - 1) {
      await new Promise(r => setTimeout(r, 3000));
    }
  }

  // ─── Step 3: Render slides with Puppeteer (text overlay on AI backgrounds) ───
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
    type: i === 0 ? 'hook' as const
      : i === rawSlides.length - 1 ? 'cta' as const
      : 'value' as const,
  }));
}
