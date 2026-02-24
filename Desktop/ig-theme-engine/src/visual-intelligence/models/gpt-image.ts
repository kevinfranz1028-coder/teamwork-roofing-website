// GPT Image 1.5 via OpenAI API — Text-heavy / complex compositions
import OpenAI from 'openai';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { withRetry } from '../../utils/retry.js';

let client: OpenAI | null = null;

function getClient(): OpenAI {
  if (!client) {
    client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  }
  return client;
}

function mapAspectToSize(aspectRatio: string): '1024x1024' | '1024x1792' | '1792x1024' {
  switch (aspectRatio) {
    case '9:16': return '1024x1792';
    case '16:9': return '1792x1024';
    case '1:1':
    default: return '1024x1024';
  }
}

export async function generateGPTImage(
  prompt: string,
  aspectRatio: string,
  outputPath: string,
  quality: 'low' | 'medium' | 'high' = 'high'
): Promise<string> {
  const dir = path.dirname(outputPath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  const size = mapAspectToSize(aspectRatio);

  return withRetry(async () => {
    const openai = getClient();

    const response = await openai.images.generate({
      model: 'gpt-image-1',
      prompt: prompt,
      n: 1,
      size: size,
      quality: quality,
    });

    const imageB64 = response.data?.[0]?.b64_json;
    const imageUrl = response.data?.[0]?.url;

    if (imageB64) {
      await writeFile(outputPath, Buffer.from(imageB64, 'base64'));
    } else if (imageUrl) {
      const res = await fetch(imageUrl);
      const buffer = Buffer.from(await res.arrayBuffer());
      await writeFile(outputPath, buffer);
    } else {
      throw new Error('No image data returned from OpenAI');
    }

    return outputPath;
  }, { maxAttempts: 2, delayMs: 5000, backoffMultiplier: 2 });
}
