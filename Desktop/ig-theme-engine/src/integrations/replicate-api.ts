import Replicate from 'replicate';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { CONFIG } from '../config/env.js';
import { getActiveAISettings } from '../config/ai-settings.js';
import { withRetry, withFallback } from '../utils/retry.js';
import { getBrowser } from '../rendering/browser-pool.js';

let client: Replicate | null = null;

function getClient(): Replicate {
  if (!client) {
    client = new Replicate({ auth: CONFIG.replicate.apiToken });
  }
  return client;
}

/**
 * Generate an AI background image via Replicate Flux Schnell.
 * Falls back to a CSS gradient rendered by Puppeteer if Replicate fails.
 * Returns the local file path of the downloaded image.
 */
export async function generateBackground(
  prompt: string,
  outputDir: string,
  filename: string,
  aspectRatio: string = '9:16'
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  return withFallback(
    () => withRetry(() => generateBackgroundFromReplicate(prompt, outputDir, filename, aspectRatio), {
      maxAttempts: 2, delayMs: 3000, backoffMultiplier: 2
    }),
    () => generateGradientFallback(outputDir, filename, aspectRatio),
    'Background generation'
  );
}

async function generateBackgroundFromReplicate(
  prompt: string,
  outputDir: string,
  filename: string,
  aspectRatio: string
): Promise<string> {
  const replicate = getClient();

  // Enhance prompt with AI settings style prefix/suffix/negative
  let enhancedPrompt = prompt;
  const settings = getActiveAISettings();
  if (settings) {
    if (settings.image_style_prefix) {
      enhancedPrompt = `${settings.image_style_prefix}, ${enhancedPrompt}`;
    }
    if (settings.image_style_suffix) {
      enhancedPrompt = `${enhancedPrompt}, ${settings.image_style_suffix}`;
    }
    if (settings.image_negative_prompt) {
      enhancedPrompt = `${enhancedPrompt}. Do not include: ${settings.image_negative_prompt}`;
    }
  }

  const output = await replicate.run('black-forest-labs/flux-schnell', {
    input: {
      prompt: enhancedPrompt,
      num_outputs: 1,
      aspect_ratio: aspectRatio,
      output_format: 'png',
    },
  }) as any;

  // Output is an array of ReadableStream or URL strings
  const imageData = output[0];
  const outputPath = path.join(outputDir, filename);

  if (typeof imageData === 'string') {
    // It's a URL — download it
    const response = await fetch(imageData);
    const buffer = Buffer.from(await response.arrayBuffer());
    await writeFile(outputPath, buffer);
  } else if (imageData instanceof ReadableStream || (imageData && typeof imageData.read === 'function')) {
    // It's a stream
    const chunks: Uint8Array[] = [];
    const reader = (imageData as ReadableStream).getReader();
    let done = false;
    while (!done) {
      const result = await reader.read();
      done = result.done;
      if (result.value) chunks.push(result.value);
    }
    await writeFile(outputPath, Buffer.concat(chunks));
  } else {
    throw new Error('Unexpected Replicate output format');
  }

  return outputPath;
}

async function generateGradientFallback(
  outputDir: string,
  filename: string,
  aspectRatio: string
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
