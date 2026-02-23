import Replicate from 'replicate';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { CONFIG } from '../config/env.js';

let client: Replicate | null = null;

function getClient(): Replicate {
  if (!client) {
    client = new Replicate({ auth: CONFIG.replicate.apiToken });
  }
  return client;
}

/**
 * Generate an AI background image via Replicate Flux Schnell.
 * Returns the local file path of the downloaded image.
 */
export async function generateBackground(
  prompt: string,
  outputDir: string,
  filename: string
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const replicate = getClient();

  const output = await replicate.run('black-forest-labs/flux-schnell', {
    input: {
      prompt,
      num_outputs: 1,
      aspect_ratio: '9:16',
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
