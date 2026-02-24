// Image Router — Routes image generation to the correct model based on VisualPlan
import type { VisualPlan, VisualBrief, GeneratedImage } from './types.js';
import { generateFlux2Pro } from './models/flux-2-pro.js';
import { generateGPTImage } from './models/gpt-image.js';
import { generateIdeogram } from './models/ideogram.js';
import { buildFinalPrompt } from './prompt-engineer.js';
import { validateImage, logQualityResult } from './quality-gate.js';
import { retryPlan } from './creative-director.js';
import chalk from 'chalk';

const MAX_RETRIES = parseInt(process.env.QUALITY_GATE_MAX_RETRIES || '2', 10);

/**
 * Generate an image using the model specified in the VisualPlan.
 * Runs Quality Gate validation and retries if needed.
 */
export async function generateImage(
  plan: VisualPlan,
  brief: VisualBrief,
  outputDir: string,
  filename: string
): Promise<GeneratedImage> {
  let currentPlan = plan;
  let retryCount = 0;
  let bestResult: GeneratedImage | null = null;
  let bestScore = 0;

  while (retryCount <= MAX_RETRIES) {
    const { prompt, negativePrompt } = buildFinalPrompt(currentPlan, brief);
    const outputPath = `${outputDir}/${retryCount > 0 ? `retry${retryCount}-${filename}` : filename}`;

    console.log(chalk.cyan(`    Image Router → ${currentPlan.model} (attempt ${retryCount + 1})`));

    try {
      // Route to the correct model
      switch (currentPlan.model) {
        case 'flux-2-pro':
          await generateFlux2Pro(prompt, negativePrompt, currentPlan.aspectRatio, outputPath);
          break;
        case 'gpt-image-1.5':
          await generateGPTImage(prompt, currentPlan.aspectRatio, outputPath);
          break;
        case 'ideogram-3':
          await generateIdeogram(prompt, currentPlan.aspectRatio, outputPath);
          break;
        default:
          await generateFlux2Pro(prompt, negativePrompt, currentPlan.aspectRatio, outputPath);
      }

      // Validate through Quality Gate
      const report = await validateImage(outputPath, currentPlan);
      console.log(chalk.cyan(`    Quality Gate: score ${report.score}/10 ${report.pass ? '(PASS)' : '(FAIL)'}`));

      const result: GeneratedImage = {
        path: outputPath,
        model: currentPlan.model,
        prompt,
        qualityReport: report,
        retryCount,
      };

      // Track best result across retries
      if (report.score > bestScore) {
        bestScore = report.score;
        bestResult = result;
      }

      // Log the quality result for self-learning
      logQualityResult({
        model: currentPlan.model,
        contentType: brief.contentType,
        segmentType: brief.segmentType,
        prompt,
        qualityScore: report.score,
        issues: report.issues,
        retryCount,
        finalPrompt: retryCount > 0 ? prompt : undefined,
      });

      if (report.pass) {
        return result;
      }

      // If quality failed, ask Creative Director for a revised plan
      if (retryCount < MAX_RETRIES) {
        console.log(chalk.yellow(`    Retrying with adjusted prompt (issues: ${report.issues.join(', ')})`));
        currentPlan = await retryPlan(currentPlan, report.feedback, brief);
      }

      retryCount++;
    } catch (err: any) {
      console.warn(chalk.red(`    Image generation failed: ${err.message}`));
      retryCount++;

      if (retryCount > MAX_RETRIES) {
        // Return best result if we have one, otherwise throw
        if (bestResult) return bestResult;
        throw err;
      }
    }
  }

  // Return best result from all attempts
  if (bestResult) return bestResult;
  throw new Error(`Image generation failed after ${MAX_RETRIES + 1} attempts`);
}
