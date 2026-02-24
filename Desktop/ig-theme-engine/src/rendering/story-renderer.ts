import path from 'path';
import { mkdirSync, existsSync, readFileSync } from 'fs';
import { getBrowser } from './browser-pool.js';
import { storySlideHtml } from './templates.js';
import type { StorySlideContent, RenderConfig } from './types.js';
import type { VisualBrief } from '../visual-intelligence/types.js';
import { planVisualsBatch } from '../visual-intelligence/creative-director.js';
import { generateImage } from '../visual-intelligence/image-router.js';
import { getStyleAnchor } from '../visual-intelligence/knowledge/style-anchors.js';
import { CONFIG } from '../config/env.js';

/**
 * Render story slides as 1080x1920 PNGs via Visual Intelligence + Puppeteer.
 */
export async function renderStorySlides(
  slides: StorySlideContent[],
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string[]> {
  const outputDir = path.join(CONFIG.paths.assets, `story-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  // ─── Step 1: Creative Director plans visuals ───
  console.log('  Creative Director planning story visuals...');
  const anchor = getStyleAnchor();
  const briefs: VisualBrief[] = slides.map((slide, i) => ({
    contentType: 'story' as const,
    segmentType: i === 0 ? 'hook' : i === slides.length - 1 ? 'cta' : 'body',
    segmentIndex: i,
    totalSegments: slides.length,
    onScreenText: slide.text,
    originalVisualDescription: slide.designNotes || `professional ${CONFIG.app.niche} story visual, vertical 9:16`,
    brandContext: {
      niche: CONFIG.app.niche || 'Houseplant ICU',
      stylePrefix: anchor.imageStylePrefix,
      colorPalette: [renderConfig.brandColors.primary, renderConfig.brandColors.secondary, renderConfig.brandColors.accent],
      mood: i === 0 ? 'dramatic, scroll-stopping' : i === slides.length - 1 ? 'warm, inviting' : 'engaging, clear',
    },
  }));

  const plans = await planVisualsBatch(briefs);

  // ─── Step 2: Generate AI backgrounds ───
  console.log('  Generating AI story backgrounds...');
  const bgPaths: (string | null)[] = [];
  for (let i = 0; i < slides.length; i++) {
    console.log(`    bg ${i + 1}/${slides.length}...`);
    try {
      const plan = { ...plans[i], aspectRatio: '9:16' as const };
      const result = await generateImage(plan, briefs[i], outputDir, `bg-${i}.png`);
      bgPaths.push(result.path);
    } catch (err: any) {
      console.log(`    bg ${i + 1} failed: ${err.message.slice(0, 80)}`);
      bgPaths.push(null);
    }
    if (i < slides.length - 1) {
      await new Promise(r => setTimeout(r, 3000));
    }
  }

  // ─── Step 3: Render slides with Puppeteer ───
  const browser = await getBrowser();
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

  const paths: string[] = [];

  try {
    for (let i = 0; i < slides.length; i++) {
      const slide = slides[i];
      const bgUrl = bgPaths[i]
        ? `data:image/png;base64,${readFileSync(bgPaths[i]!).toString('base64')}`
        : undefined;
      const html = storySlideHtml(slide, renderConfig, bgUrl);
      await page.setContent(html, { waitUntil: 'domcontentloaded' });
      await page.evaluate(() => Promise.race([
        document.fonts.ready,
        new Promise(r => setTimeout(r, 3000)),
      ]));

      const outputPath = path.join(outputDir, `story-${String(slide.slideNumber).padStart(2, '0')}.png`);
      await page.screenshot({ path: outputPath, type: 'png' });
      paths.push(outputPath);
    }
  } finally {
    await page.close();
  }

  return paths;
}

/**
 * Parse a content_scripts row's story_sequence_json into StorySlideContent[].
 */
export function parseStoryScript(storyJson: string): StorySlideContent[] {
  const parsed = JSON.parse(storyJson);

  const rawSlides: any[] = Array.isArray(parsed) ? parsed
    : parsed.slides ? parsed.slides
    : parsed.storySequence?.slides ? parsed.storySequence.slides
    : [];

  return rawSlides.map((s: any, i: number) => ({
    slideNumber: s.slideNumber || i + 1,
    text: s.text || s.content || s.headline || '',
    interactiveElement: s.interactiveElement || s.interactive || 'none',
    interactiveData: s.interactiveData || s.data || undefined,
    designNotes: s.designNotes || '',
  }));
}
