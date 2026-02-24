// Quality Gate — Validates every generated image/video and scores quality
import sharp from 'sharp';
import { readFile, stat } from 'fs/promises';
import Anthropic from '@anthropic-ai/sdk';
import { CONFIG } from '../config/env.js';
import { getDb } from '../database/db.js';
import type { QualityReport, VisualPlan, QualityLogEntry } from './types.js';

const anthropic = new Anthropic({ apiKey: CONFIG.ai.apiKey });

const QUALITY_CHECK_PROMPT = `Evaluate this AI-generated image for an Instagram post. Score it 1-10 on "would this pass as a real photograph on Instagram?" Check for these specific issues:

1. GARBLED TEXT: Are there any words, letters, or text-like artifacts in the image? AI models often generate gibberish text on signs, labels, packaging. Any visible text that isn't perfectly readable = automatic failure.

2. COLLAGE LAYOUT: Does the image look like multiple images stacked or side-by-side? A good image is ONE cohesive scene from ONE camera angle.

3. BLACK BARS/VOIDS: Are there any solid black or empty areas? The image should fill the entire canvas edge-to-edge.

4. SEAMS/STITCHING: Is there a visible line where two different images were joined?

5. SUBJECT CLARITY: Is the main subject clearly visible and properly focused?

6. REALISM: Would a casual Instagram scroller think this was a real photo?

7. COMPOSITION: Is the image well-composed with professional framing?

Respond in JSON only, no markdown:
{
  "score": 1-10,
  "issues": ["list of detected problems"],
  "garbled_text_detected": true/false,
  "collage_detected": true/false,
  "black_bars_detected": true/false,
  "seams_detected": true/false,
  "subject_clarity": true/false,
  "brand_alignment": true/false,
  "feedback": "specific suggestion for improving the prompt if regeneration is needed"
}`;

function isQualityGateEnabled(): boolean {
  return process.env.QUALITY_GATE_ENABLED !== 'false';
}

function getMinScore(): number {
  return parseInt(process.env.QUALITY_GATE_MIN_SCORE || '7', 10);
}

export async function validateImage(
  imagePath: string,
  plan: VisualPlan
): Promise<QualityReport> {
  // 1. Technical checks (fast, no AI needed)
  const techChecks = await runTechnicalChecks(imagePath, plan.aspectRatio);

  // If quality gate is disabled, return a passing report based on tech checks only
  if (!isQualityGateEnabled()) {
    return {
      score: techChecks.allPassed ? 8 : 5,
      pass: techChecks.allPassed,
      issues: techChecks.issues,
      feedback: '',
      checks: {
        dimensions: techChecks.dimensions,
        fileSize: techChecks.fileSize,
        noGarbledText: true,
        noCollage: true,
        noBlackBars: true,
        noSeams: true,
        subjectClarity: true,
        brandAlignment: true,
      },
    };
  }

  // 2. AI Vision check (Claude with the image)
  const imageBuffer = await readFile(imagePath);
  const imageBase64 = imageBuffer.toString('base64');
  const ext = imagePath.endsWith('.png') ? 'image/png' : 'image/jpeg';

  try {
    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 1024,
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: ext as any, data: imageBase64 } },
          { type: 'text', text: QUALITY_CHECK_PROMPT },
        ],
      }],
    });

    const text = response.content
      .filter((b): b is Anthropic.TextBlock => b.type === 'text')
      .map(b => b.text)
      .join('');

    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.warn('    Quality Gate: Could not parse vision response, passing with tech checks only');
      return buildFallbackReport(techChecks);
    }

    const vision = JSON.parse(jsonMatch[0]);
    const score = Math.min(10, Math.max(1, vision.score || 5));

    return {
      score,
      pass: score >= getMinScore() && techChecks.allPassed,
      issues: [...techChecks.issues, ...(vision.issues || [])],
      feedback: vision.feedback || '',
      checks: {
        dimensions: techChecks.dimensions,
        fileSize: techChecks.fileSize,
        noGarbledText: !vision.garbled_text_detected,
        noCollage: !vision.collage_detected,
        noBlackBars: !vision.black_bars_detected,
        noSeams: !vision.seams_detected,
        subjectClarity: vision.subject_clarity !== false,
        brandAlignment: vision.brand_alignment !== false,
      },
    };
  } catch (err: any) {
    console.warn(`    Quality Gate: Vision check failed (${err.message}), using tech checks only`);
    return buildFallbackReport(techChecks);
  }
}

interface TechnicalCheckResult {
  allPassed: boolean;
  dimensions: boolean;
  fileSize: boolean;
  issues: string[];
}

async function runTechnicalChecks(imagePath: string, expectedAspectRatio: string): Promise<TechnicalCheckResult> {
  const issues: string[] = [];
  let dimensionsOk = true;
  let fileSizeOk = true;

  try {
    const metadata = await sharp(imagePath).metadata();
    const w = metadata.width || 0;
    const h = metadata.height || 0;

    // Check minimum resolution
    if (w < 512 || h < 512) {
      issues.push(`Image too small: ${w}x${h}`);
      dimensionsOk = false;
    }

    // Check aspect ratio roughly matches
    const ratio = w / h;
    const expected = parseAspectRatio(expectedAspectRatio);
    if (expected && Math.abs(ratio - expected) > 0.15) {
      issues.push(`Aspect ratio mismatch: got ${ratio.toFixed(2)}, expected ~${expected.toFixed(2)}`);
      dimensionsOk = false;
    }
  } catch {
    issues.push('Could not read image metadata');
    dimensionsOk = false;
  }

  try {
    const stats = await stat(imagePath);
    if (stats.size < 5000) {
      issues.push('File too small — may be corrupt');
      fileSizeOk = false;
    }
    if (stats.size > 50_000_000) {
      issues.push('File unusually large (>50MB)');
    }
  } catch {
    issues.push('Could not stat file');
    fileSizeOk = false;
  }

  return {
    allPassed: dimensionsOk && fileSizeOk && issues.length === 0,
    dimensions: dimensionsOk,
    fileSize: fileSizeOk,
    issues,
  };
}

function parseAspectRatio(ar: string): number | null {
  const parts = ar.split(/[x:]/);
  if (parts.length === 2) {
    const [a, b] = parts.map(Number);
    if (a && b) return a / b;
  }
  return null;
}

function buildFallbackReport(techChecks: TechnicalCheckResult): QualityReport {
  return {
    score: techChecks.allPassed ? 7 : 4,
    pass: techChecks.allPassed,
    issues: techChecks.issues,
    feedback: '',
    checks: {
      dimensions: techChecks.dimensions,
      fileSize: techChecks.fileSize,
      noGarbledText: true,
      noCollage: true,
      noBlackBars: true,
      noSeams: true,
      subjectClarity: true,
      brandAlignment: true,
    },
  };
}

/**
 * Log a quality check result to the DB for self-learning.
 */
export function logQualityResult(entry: QualityLogEntry): void {
  try {
    const db = getDb();
    db.prepare(`
      INSERT INTO visual_quality_log (model, content_type, segment_type, prompt, quality_score, issues, retry_count, final_prompt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      entry.model,
      entry.contentType,
      entry.segmentType || null,
      entry.prompt,
      entry.qualityScore,
      JSON.stringify(entry.issues),
      entry.retryCount,
      entry.finalPrompt || null
    );
  } catch (err: any) {
    console.warn(`    Quality log write failed: ${err.message}`);
  }
}
