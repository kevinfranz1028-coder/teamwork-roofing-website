// Kling 2.6 Pro via fal.ai — Image-to-Video generation
import * as fal from '@fal-ai/serverless-client';
import { writeFile, readFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';

let configured = false;

function ensureConfig() {
  if (!configured) {
    const apiKey = process.env.FAL_API_KEY;
    if (!apiKey) throw new Error('FAL_API_KEY not set');
    fal.config({ credentials: apiKey });
    configured = true;
  }
}

export async function generateVideoFromImage(
  imagePath: string,
  motionPrompt: string,
  duration: 5 | 10,
  outputPath: string
): Promise<string> {
  ensureConfig();

  const dir = path.dirname(outputPath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  // Upload source image to fal storage
  const imageBuffer = await readFile(imagePath);
  const imageBlob = new Blob([imageBuffer], { type: 'image/png' });
  const imageUrl = await fal.storage.upload(imageBlob);

  console.log(`    Kling: generating ${duration}s video from still...`);

  const result = await fal.subscribe('fal-ai/kling-video/v2.6/pro/image-to-video', {
    input: {
      prompt: motionPrompt,
      image_url: imageUrl,
      duration: String(duration),
      aspect_ratio: '9:16',
    },
    logs: true,
    onQueueUpdate: (update: any) => {
      if (update.status === 'IN_PROGRESS') {
        const msg = update.logs?.[update.logs.length - 1]?.message || 'processing...';
        console.log(`    Kling: ${msg}`);
      }
    },
  }) as any;

  // Download the generated video
  const videoUrl = result.data?.video?.url || result.video?.url;
  if (!videoUrl) throw new Error('No video URL in Kling response');

  const videoRes = await fetch(videoUrl);
  const videoBuffer = Buffer.from(await videoRes.arrayBuffer());
  await writeFile(outputPath, videoBuffer);

  console.log(`    Kling: video saved (${(videoBuffer.length / 1024 / 1024).toFixed(1)}MB)`);
  return outputPath;
}

export async function generateVideoFromText(
  textPrompt: string,
  duration: 5 | 10,
  outputPath: string
): Promise<string> {
  ensureConfig();

  const dir = path.dirname(outputPath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  console.log(`    Kling: generating ${duration}s video from text prompt...`);

  const result = await fal.subscribe('fal-ai/kling-video/v2.6/pro/text-to-video', {
    input: {
      prompt: textPrompt,
      duration: String(duration),
      aspect_ratio: '9:16',
    },
    logs: true,
    onQueueUpdate: (update: any) => {
      if (update.status === 'IN_PROGRESS') {
        const msg = update.logs?.[update.logs.length - 1]?.message || 'processing...';
        console.log(`    Kling: ${msg}`);
      }
    },
  }) as any;

  const videoUrl = result.data?.video?.url || result.video?.url;
  if (!videoUrl) throw new Error('No video URL in Kling t2v response');

  const videoRes = await fetch(videoUrl);
  const videoBuffer = Buffer.from(await videoRes.arrayBuffer());
  await writeFile(outputPath, videoBuffer);

  return outputPath;
}
