// FLUX 2 Pro via Replicate API — Primary plant photography model
import Replicate from 'replicate';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { CONFIG } from '../../config/env.js';
import { withRetry } from '../../utils/retry.js';

let client: Replicate | null = null;

function getClient(): Replicate {
  if (!client) {
    client = new Replicate({ auth: CONFIG.replicate.apiToken });
  }
  return client;
}

export async function generateFlux2Pro(
  prompt: string,
  negativePrompt: string,
  aspectRatio: string,
  outputPath: string
): Promise<string> {
  const dir = path.dirname(outputPath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  return withRetry(async () => {
    const replicate = getClient();

    // FLUX 2 Pro does not support a negative_prompt parameter —
    // append "Do not include" clause to the prompt itself
    let fullPrompt = prompt;
    if (negativePrompt) {
      fullPrompt += `. Do not include: ${negativePrompt}`;
    }

    const output = await replicate.run('black-forest-labs/flux-2-pro', {
      input: {
        prompt: fullPrompt,
        aspect_ratio: aspectRatio,
        output_format: 'png',
        output_quality: 95,
        prompt_upsampling: true,
      },
    }) as any;

    const imageData = output[0] ?? output;

    if (typeof imageData === 'string') {
      const response = await fetch(imageData);
      const buffer = Buffer.from(await response.arrayBuffer());
      await writeFile(outputPath, buffer);
    } else if (imageData instanceof ReadableStream || (imageData && typeof imageData.read === 'function')) {
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
  }, { maxAttempts: 2, delayMs: 3000, backoffMultiplier: 2 });
}
