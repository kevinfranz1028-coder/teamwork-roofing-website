import type { VisualPlan, VisualBrief, GeneratedImage } from './types.js';
import { generateFlux2Pro } from './models/flux-2-pro.js';
import { generateGPTImage } from './models/gpt-image.js';
import { generateIdeogram } from './models/ideogram.js';
import { validateImage } from './quality-gate.js';
import { retryPlan } from './creative-director.js';
import { buildFinalPrompt, buildNegativePrompt } from './prompt-engineer.js';
import { generateBackground } from '../integrations/replicate-api.js';

const MAX_RETRIES = parseInt(process.env.QUALITY_GATE_MAX_RETRIES || '2');

/**
 * Generate an image using the model specified in the plan.
 * Runs quality gate and retries with refined prompts if needed.
 */
export async function generateImage(
  plan: VisualPlan,
  brief: VisualBrief,
  outputDir: string,
  filename: string
): Promise<GeneratedImage> {
  const qualityGateEnabled = process.env.QUALITY_GATE_ENABLED !== 'false';
  let currentPlan = plan;
  let retryCount = 0;
  let lastPath = '';

  console.log(`    [Image Router] Starting generation: model=${currentPlan.model}, qualityGate=${qualityGateEnabled}, maxRetries=${MAX_RETRIES}`);

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const finalPrompt = buildFinalPrompt(currentPlan, brief);
      const negativePrompt = buildNegativePrompt(currentPlan);
      const retryFilename = attempt > 0 ? filename.replace('.png', `-r${attempt}.png`) : filename;

      console.log(`    [Image Router] Attempt ${attempt + 1}/${MAX_RETRIES + 1} — model: ${currentPlan.model}, prompt: "${finalPrompt.slice(0, 80)}..."`);

      // Route to the correct model
      let imagePath: string;

      switch (currentPlan.model) {
        case 'gpt-image-1.5':
          imagePath = await generateGPTImage(finalPrompt, outputDir, retryFilename, currentPlan.aspectRatio);
          break;

        case 'ideogram-3':
          try {
            imagePath = await generateIdeogram(finalPrompt, outputDir, retryFilename, currentPlan.aspectRatio, negativePrompt);
          } catch (err: any) {
            console.log(`    Ideogram failed (${err.message?.slice(0, 60)}), falling back to FLUX 2 Pro`);
            imagePath = await generateFlux2Pro(finalPrompt, outputDir, retryFilename, currentPlan.aspectRatio);
          }
          break;

        case 'flux-2-pro':
        default:
          try {
            imagePath = await generateFlux2Pro(finalPrompt, outputDir, retryFilename, currentPlan.aspectRatio);
          } catch (err: any) {
            console.log(`    FLUX 2 Pro failed (${err.message?.slice(0, 60)}), falling back to legacy Flux Schnell`);
            imagePath = await generateBackground(brief.originalVisualDescription, outputDir, retryFilename, currentPlan.aspectRatio);
          }
          break;
      }

      lastPath = imagePath;

      // Quality Gate check (if enabled and not final attempt)
      if (qualityGateEnabled && attempt < MAX_RETRIES) {
        const report = await validateImage(imagePath, finalPrompt, currentPlan.model, brief.contentType, brief.segmentType);

        if (report.pass) {
          return { path: imagePath, model: currentPlan.model, prompt: finalPrompt, qualityScore: report.score, retryCount: attempt };
        }

        // Failed quality — get a refined plan from Creative Director
        console.log(`    Quality Gate failed (${report.score}/10), retrying...`);
        currentPlan = await retryPlan(brief, report.feedback || report.issues.join('; '));
        retryCount = attempt + 1;
      } else {
        // Quality gate disabled or final attempt — accept as-is
        return { path: imagePath, model: currentPlan.model, prompt: finalPrompt, retryCount: attempt };
      }
    } catch (err: any) {
      console.log(`    Image generation attempt ${attempt + 1} failed: ${err.message?.slice(0, 80)}`);
      if (attempt === MAX_RETRIES) {
        // Final fallback: use legacy Flux Schnell
        try {
          const fallbackPath = await generateBackground(brief.originalVisualDescription, outputDir, filename, currentPlan.aspectRatio);
          return { path: fallbackPath, model: 'flux-schnell-fallback', prompt: brief.originalVisualDescription, retryCount: attempt };
        } catch {
          throw new Error(`All image generation attempts failed for segment ${brief.segmentIndex}`);
        }
      }
    }
  }

  // Should not reach here, but safety return
  return { path: lastPath, model: currentPlan.model, prompt: currentPlan.prompt, retryCount };
}
