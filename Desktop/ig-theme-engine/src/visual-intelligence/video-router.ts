// Video Router — Routes video generation to Kling via fal.ai
import type { VisualPlan, GeneratedVideo } from './types.js';
import { generateVideoFromImage, generateVideoFromText } from './models/kling-video.js';
import { buildVideoPrompt } from './prompt-engineer.js';
import chalk from 'chalk';

/**
 * Generate a video clip from a still image using Kling 2.6 Pro.
 * Falls back to a still-image hold if video generation is disabled or fails.
 */
export async function generateVideo(
  sourceImagePath: string,
  plan: VisualPlan,
  outputDir: string,
  filename: string
): Promise<GeneratedVideo> {
  const outputPath = `${outputDir}/${filename}`;
  const motionPrompt = buildVideoPrompt(plan);
  const duration = plan.videoDuration || 5;

  // Check if video generation is enabled
  if (!plan.generateVideo || process.env.ENABLE_VIDEO_GENERATION === 'false') {
    console.log(chalk.dim('    Video generation disabled — using still image'));
    return {
      path: sourceImagePath,
      model: 'kling-2.6-pro',
      sourceImagePath,
      motionPrompt: '',
      durationSeconds: duration,
    };
  }

  // Check for FAL API key
  if (!process.env.FAL_API_KEY) {
    console.warn(chalk.yellow('    FAL_API_KEY not set — skipping video generation, using still'));
    return {
      path: sourceImagePath,
      model: 'kling-2.6-pro',
      sourceImagePath,
      motionPrompt: '',
      durationSeconds: duration,
    };
  }

  try {
    console.log(chalk.cyan(`    Video Router → Kling 2.6 Pro (${duration}s, i2v)`));
    const videoPath = await generateVideoFromImage(sourceImagePath, motionPrompt, duration as 5 | 10, outputPath);

    return {
      path: videoPath,
      model: 'kling-2.6-pro',
      sourceImagePath,
      motionPrompt,
      durationSeconds: duration,
    };
  } catch (err: any) {
    console.warn(chalk.yellow(`    Kling video failed: ${err.message} — falling back to still image`));
    return {
      path: sourceImagePath,
      model: 'kling-2.6-pro',
      sourceImagePath,
      motionPrompt,
      durationSeconds: duration,
    };
  }
}
