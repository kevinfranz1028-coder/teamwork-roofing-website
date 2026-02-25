import type { VisualPlan, GeneratedVideo } from './types.js';
import { generateVideoFromImage } from './models/kling-video.js';
import { buildMotionPrompt } from './prompt-engineer.js';

/**
 * Generate a video clip from a still image.
 * Falls back gracefully to returning the still image path if video gen fails.
 */
export async function generateVideo(
  imagePath: string,
  plan: VisualPlan,
  outputDir: string,
  filename: string
): Promise<GeneratedVideo> {
  const falKey = process.env.FAL_API_KEY;

  if (!falKey) {
    console.log('    [Video Router] FAL_API_KEY not set — using still image (Ken Burns will be applied)');
    return { path: imagePath, model: 'still-fallback', durationSeconds: 0, fromImage: false };
  }

  console.log(`    [Video Router] FAL_API_KEY is set, calling Kling 2.6 Pro...`);

  try {
    const motionPrompt = plan.motionPrompt || buildMotionPrompt(plan, {
      contentType: 'reel',
      segmentType: 'body',
      segmentIndex: 0,
      totalSegments: 1,
      onScreenText: '',
      originalVisualDescription: plan.prompt,
      brandContext: { niche: '', stylePrefix: '', colorPalette: [], mood: '' },
    });

    const video = await generateVideoFromImage(
      imagePath,
      motionPrompt,
      outputDir,
      filename,
      5
    );

    return video;
  } catch (err: any) {
    console.log(`    [Video Router] Kling failed (${err.message?.slice(0, 80)}), using still image fallback`);
    return { path: imagePath, model: 'still-fallback', durationSeconds: 0, fromImage: false };
  }
}
