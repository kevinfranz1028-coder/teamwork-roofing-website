// Ideogram 3.0 via Ideogram REST API — Typography-first designs
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { withRetry } from '../../utils/retry.js';

function mapAspectRatio(ar: string): string {
  switch (ar) {
    case '1:1': return 'ASPECT_1_1';
    case '9:16': return 'ASPECT_9_16';
    case '16:9': return 'ASPECT_16_9';
    case '4:5': return 'ASPECT_4_5';
    default: return 'ASPECT_1_1';
  }
}

export async function generateIdeogram(
  prompt: string,
  aspectRatio: string,
  outputPath: string
): Promise<string> {
  const apiKey = process.env.IDEOGRAM_API_KEY;
  if (!apiKey) throw new Error('IDEOGRAM_API_KEY not set');

  const dir = path.dirname(outputPath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  return withRetry(async () => {
    const response = await fetch('https://api.ideogram.ai/generate', {
      method: 'POST',
      headers: {
        'Api-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_request: {
          prompt: prompt,
          aspect_ratio: mapAspectRatio(aspectRatio),
          model: 'V_3',
          style_type: 'REALISTIC',
        },
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Ideogram API error ${response.status}: ${errText}`);
    }

    const result = await response.json() as any;
    const imageUrl = result.data?.[0]?.url;

    if (!imageUrl) throw new Error('No image URL in Ideogram response');

    const imgRes = await fetch(imageUrl);
    const buffer = Buffer.from(await imgRes.arrayBuffer());
    await writeFile(outputPath, buffer);

    return outputPath;
  }, { maxAttempts: 2, delayMs: 5000, backoffMultiplier: 2 });
}
