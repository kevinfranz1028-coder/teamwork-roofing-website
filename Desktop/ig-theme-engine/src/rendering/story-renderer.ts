import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { getBrowser } from './browser-pool.js';
import { storySlideHtml } from './templates.js';
import type { StorySlideContent, RenderConfig } from './types.js';
import { CONFIG } from '../config/env.js';

/**
 * Render story slides as 1080x1920 PNGs via Puppeteer.
 * Returns an array of local file paths.
 */
export async function renderStorySlides(
  slides: StorySlideContent[],
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string[]> {
  const outputDir = path.join(CONFIG.paths.assets, `story-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const browser = await getBrowser();
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

  const paths: string[] = [];

  try {
    for (const slide of slides) {
      const html = storySlideHtml(slide, renderConfig);
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
