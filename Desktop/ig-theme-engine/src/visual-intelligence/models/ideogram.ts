import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import type { AspectRatio } from '../types.js';
import { logApiCost } from '../../utils/cost-tracker.js';

const ASPECT_MAP: Record<AspectRatio, string> = {
  '1:1': 'ASPECT_1_1',
  '9:16': 'ASPECT_9_16',
  '16:9': 'ASPECT_16_9',
};

export async function generateIdeogram(
  prompt: string,
  outputDir: string,
  filename: string,
  aspectRatio: AspectRatio = '9:16',
  negativePrompt?: string
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const apiKey = process.env.IDEOGRAM_API_KEY;
  if (!apiKey) throw new Error('IDEOGRAM_API_KEY not set — cannot use Ideogram 3.0');

  console.log(`    [Ideogram 3.0] Generating image (${aspectRatio})...`);

  const body: any = {
    image_request: {
      prompt,
      model: 'V_3',
      aspect_ratio: ASPECT_MAP[aspectRatio] || 'ASPECT_9_16',
      magic_prompt_option: 'AUTO',
    },
  };

  if (negativePrompt) {
    body.image_request.negative_prompt = negativePrompt;
  }

  const response = await fetch('https://api.ideogram.ai/api/v1/ideogram-v3/generate', {
    method: 'POST',
    headers: {
      'Api-Key': apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Ideogram API error ${response.status}: ${err.slice(0, 200)}`);
  }

  const data = await response.json() as any;
  const imageUrl = data.data?.[0]?.url;

  if (!imageUrl) throw new Error('Ideogram returned no image URL');

  const imgResponse = await fetch(imageUrl);
  const buffer = Buffer.from(await imgResponse.arrayBuffer());

  const outputPath = path.join(outputDir, filename);
  await writeFile(outputPath, buffer);

  console.log(`    [Ideogram 3.0] Saved: ${filename}`);

  logApiCost({
    provider: 'ideogram',
    category: 'image',
    endpoint: 'ideogram-v3/generate',
    model: 'ideogram-3',
    description: `Image: ${prompt.slice(0, 60)}`,
    estimatedCost: 0.05,
  });

  return outputPath;
}
