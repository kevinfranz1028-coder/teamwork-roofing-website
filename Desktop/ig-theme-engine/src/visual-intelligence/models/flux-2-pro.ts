import Replicate from 'replicate';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { CONFIG } from '../../config/env.js';
import type { AspectRatio } from '../types.js';
import { logApiCost } from '../../utils/cost-tracker.js';

let client: Replicate | null = null;

function getClient(): Replicate {
  if (!client) {
    client = new Replicate({ auth: CONFIG.replicate.apiToken });
  }
  return client;
}

export async function generateFlux2Pro(
  prompt: string,
  outputDir: string,
  filename: string,
  aspectRatio: AspectRatio = '9:16'
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const replicate = getClient();

  console.log(`    [FLUX 2 Pro] Generating image (${aspectRatio})...`);

  const output = await replicate.run('black-forest-labs/flux-2-pro', {
    input: {
      prompt,
      aspect_ratio: aspectRatio,
      output_format: 'png',
      prompt_upsampling: true,
      safety_tolerance: 5,
      guidance: 3.5,
    },
  }) as any;

  // Replicate SDK returns FileOutput (extends ReadableStream).
  // String(output) gives the download URL. output[0] is undefined.
  const imageUrl = String(output);
  const outputPath = path.join(outputDir, filename);

  if (!imageUrl || imageUrl === '[object Object]' || imageUrl === 'undefined') {
    throw new Error('FLUX 2 Pro returned no image URL');
  }

  console.log(`    [FLUX 2 Pro] Downloading from: ${imageUrl.slice(0, 80)}...`);
  const response = await fetch(imageUrl);
  if (!response.ok) throw new Error(`FLUX 2 Pro download failed: ${response.status}`);
  const buffer = Buffer.from(await response.arrayBuffer());
  await writeFile(outputPath, buffer);

  console.log(`    [FLUX 2 Pro] Saved: ${filename}`);

  logApiCost({
    provider: 'replicate',
    category: 'image',
    endpoint: 'black-forest-labs/flux-2-pro',
    model: 'flux-2-pro',
    description: `Image: ${prompt.slice(0, 60)}`,
    estimatedCost: 0.03,
  });

  return outputPath;
}
