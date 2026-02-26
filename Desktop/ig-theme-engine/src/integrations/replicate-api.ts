// LEGACY: This file is no longer used in the active rendering pipeline.
// Reel and carousel rendering now uses Pexels stock video/photo via pexels-api.ts.
// Kept for reference and potential future AI image generation needs.
import { fal } from '@fal-ai/client';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { CONFIG } from '../config/env.js';
import { getActiveAISettings } from '../config/ai-settings.js';
import { withRetry, withFallback } from '../utils/retry.js';
import { getBrowser } from '../rendering/browser-pool.js';
import { logApiCost } from '../utils/cost-tracker.js';

export async function generateBackground(
  prompt: string,
  outputDir: string,
  filename: string,
  aspectRatio: string = '9:16'
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  return withFallback(
    () => withRetry(() => generateBackgroundFromFal(prompt, outputDir, filename, aspectRatio), {
      maxAttempts: 2, delayMs: 3000, backoffMultiplier: 2
    }),
    () => generateGradientFallback(outputDir, filename, aspectRatio),
    'Background generation'
  );
}

const FAL_MODELS = [
  { endpoint: 'fal-ai/flux/dev',     model: 'flux-dev',     cost: 0.025, label: 'FLUX dev' },
  { endpoint: 'fal-ai/flux/schnell', model: 'flux-schnell', cost: 0.003, label: 'FLUX schnell' },
  { endpoint: 'fal-ai/flux-1/dev',   model: 'flux-1-dev',   cost: 0.025, label: 'FLUX-1 dev' },
];

async function generateBackgroundFromFal(
  prompt: string, outputDir: string, filename: string, aspectRatio: string
): Promise<string> {
  const falKey = CONFIG.fal.apiKey;
  if (!falKey) throw new Error('FAL_API_KEY not set');
  fal.config({ credentials: falKey });

  let enhancedPrompt = prompt;
  const settings = getActiveAISettings();
  if (settings) {
    if (settings.image_style_prefix) enhancedPrompt = `${settings.image_style_prefix}, ${enhancedPrompt}`;
    if (settings.image_style_suffix) enhancedPrompt = `${enhancedPrompt}, ${settings.image_style_suffix}`;
    if (settings.image_negative_prompt) enhancedPrompt = `${enhancedPrompt}. Do not include: ${settings.image_negative_prompt}`;
  }

  const imageSize = aspectRatio === '1:1' ? { width: 1080, height: 1080 } : { width: 1080, height: 1920 };
  let lastError: Error | null = null;

  for (const m of FAL_MODELS) {
    try {
      console.log(`  Image: Generating via fal.ai ${m.label}...`);

      const result = await fal.subscribe(m.endpoint, {
        input: { prompt: enhancedPrompt, image_size: imageSize, num_images: 1 },
      }) as any;

      const imageUrl = result?.data?.images?.[0]?.url || result?.images?.[0]?.url || result?.data?.output?.[0];
      if (!imageUrl) throw new Error(`No image URL from ${m.label}`);

      const response = await fetch(imageUrl);
      if (!response.ok) throw new Error(`Image download failed: ${response.status}`);
      const buffer = Buffer.from(await response.arrayBuffer());
      const outputPath = path.join(outputDir, filename);
      await writeFile(outputPath, buffer);
      console.log(`  Image: ${m.label} saved (${(buffer.length / 1024).toFixed(0)}KB)`);

      logApiCost({
        provider: 'fal',
        category: 'image',
        endpoint: m.endpoint,
        model: m.model,
        description: `Background: ${prompt.slice(0, 60)}`,
        estimatedCost: m.cost,
      });

      return outputPath;
    } catch (err: any) {
      lastError = err;
      console.warn(`  Image: ${m.label} failed (${err.message}), trying next model...`);
    }
  }

  throw lastError || new Error('All fal.ai FLUX models failed');
}

async function generateGradientFallback(
  outputDir: string, filename: string, aspectRatio: string
): Promise<string> {
  const width = 1080;
  const height = aspectRatio === '1:1' ? 1080 : 1920;
  const html = `<!DOCTYPE html><html><body style="margin:0;width:${width}px;height:${height}px;background:linear-gradient(135deg, #1a5c2e 0%, #0d3318 50%, #1a472a 100%);"></body></html>`;
  const browser = await getBrowser();
  const page = await browser.newPage();
  await page.setViewport({ width, height });
  await page.setContent(html, { waitUntil: 'domcontentloaded' });
  const outputPath = path.join(outputDir, filename);
  await page.screenshot({ path: outputPath, type: 'png' });
  await page.close();
  return outputPath;
}
