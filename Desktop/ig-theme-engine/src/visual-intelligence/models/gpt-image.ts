import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { CONFIG } from '../../config/env.js';
import type { AspectRatio } from '../types.js';
import { logApiCost } from '../../utils/cost-tracker.js';

const SIZE_MAP: Record<AspectRatio, string> = {
  '1:1': '1024x1024',
  '9:16': '1024x1536',
  '16:9': '1536x1024',
};

export async function generateGPTImage(
  prompt: string,
  outputDir: string,
  filename: string,
  aspectRatio: AspectRatio = '9:16'
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const apiKey = CONFIG.openaiTts?.apiKey || process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error('OPENAI_API_KEY not set — cannot use GPT Image 1.5');

  console.log(`    [GPT Image 1.5] Generating image (${aspectRatio})...`);

  const response = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-image-1',
      prompt,
      n: 1,
      size: SIZE_MAP[aspectRatio] || '1024x1536',
      response_format: 'b64_json',
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`GPT Image API error ${response.status}: ${err.slice(0, 200)}`);
  }

  const data = await response.json() as any;
  const b64 = data.data?.[0]?.b64_json;

  if (!b64) throw new Error('GPT Image returned no image data');

  const outputPath = path.join(outputDir, filename);
  await writeFile(outputPath, Buffer.from(b64, 'base64'));

  console.log(`    [GPT Image 1.5] Saved: ${filename}`);

  logApiCost({
    provider: 'openai',
    category: 'image',
    endpoint: 'images/generations',
    model: 'gpt-image-1',
    description: `Image: ${prompt.slice(0, 60)}`,
    estimatedCost: 0.06,
  });

  return outputPath;
}
