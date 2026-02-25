import { writeFile } from 'fs/promises';
import { readFileSync, mkdirSync, existsSync } from 'fs';
import path from 'path';
import type { GeneratedVideo } from '../types.js';
import { logApiCost } from '../../utils/cost-tracker.js';

export async function generateVideoFromImage(
  imagePath: string,
  motionPrompt: string,
  outputDir: string,
  filename: string,
  durationSeconds: number = 5
): Promise<GeneratedVideo> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const apiKey = process.env.FAL_API_KEY;
  if (!apiKey) throw new Error('FAL_API_KEY not set — cannot use Kling video');

  // Dynamic import for fal client
  const { fal } = await import('@fal-ai/client');
  fal.config({ credentials: apiKey });

  console.log(`    [Kling 2.6 Pro] Generating ${durationSeconds}s video from still...`);

  // Read image as data URI
  const imageBuffer = readFileSync(imagePath);
  const base64 = imageBuffer.toString('base64');
  const ext = path.extname(imagePath).replace('.', '') || 'png';
  const dataUri = `data:image/${ext};base64,${base64}`;

  // Upload image to fal storage
  const imageUrl = await fal.storage.upload(new Blob([imageBuffer], { type: `image/${ext}` }));

  const result = await fal.subscribe('fal-ai/kling-video/v2.5-turbo/pro/image-to-video', {
    input: {
      prompt: motionPrompt,
      image_url: imageUrl,
      duration: durationSeconds <= 5 ? '5' : '10',
      aspect_ratio: '9:16',
    } as any,
    logs: true,
    onQueueUpdate: (update: any) => {
      if (update.status === 'IN_PROGRESS') {
        const msgs = update.logs?.map((l: any) => l.message).filter(Boolean) || [];
        if (msgs.length > 0) console.log(`      Kling: ${msgs[msgs.length - 1]}`);
      }
    },
  }) as any;

  const videoUrl = result.data?.video?.url || result.video?.url;
  if (!videoUrl) throw new Error('Kling returned no video URL');

  const videoResponse = await fetch(videoUrl);
  const videoBuffer = Buffer.from(await videoResponse.arrayBuffer());

  const outputPath = path.join(outputDir, filename);
  await writeFile(outputPath, videoBuffer);

  console.log(`    [Kling 2.6 Pro] Saved: ${filename} (${durationSeconds}s)`);

  logApiCost({
    provider: 'fal',
    category: 'video',
    endpoint: 'fal-ai/kling-video/v2.5-turbo/pro/image-to-video',
    model: 'kling-2.5-turbo-pro',
    description: `Video: ${motionPrompt.slice(0, 60)}`,
    estimatedCost: durationSeconds <= 5 ? 0.35 : 0.70,
    durationMs: durationSeconds * 1000,
  });

  return {
    path: outputPath,
    model: 'kling-2.6-pro',
    durationSeconds,
    fromImage: true,
  };
}
