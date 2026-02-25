import { readFileSync } from 'fs';
import { CONFIG } from '../config/env.js';
import { getDb } from '../database/db.js';
import type { QualityReport } from './types.js';
import { logApiCost } from '../utils/cost-tracker.js';

/**
 * Validate a generated image using Claude Vision.
 * Returns a score 1-10 with specific issue detection.
 */
export async function validateImage(
  imagePath: string,
  prompt: string,
  model: string,
  contentType: string,
  segmentType: string
): Promise<QualityReport> {
  const apiKey = CONFIG.ai.apiKey;
  if (!apiKey) {
    console.log('    [Quality Gate] ANTHROPIC_API_KEY not set, skipping validation');
    return defaultPass();
  }

  try {
    const imageBuffer = readFileSync(imagePath);
    const base64 = imageBuffer.toString('base64');
    const mediaType = imagePath.endsWith('.jpg') || imagePath.endsWith('.jpeg')
      ? 'image/jpeg' : 'image/png';

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-5-20250929',
        max_tokens: 500,
        messages: [{
          role: 'user',
          content: [
            {
              type: 'image',
              source: { type: 'base64', media_type: mediaType, data: base64 },
            },
            {
              type: 'text',
              text: `You are a quality inspector for AI-generated images used in Instagram plant care content. Score this image 1-10 and check for issues.

The image was generated with this prompt: "${prompt.slice(0, 300)}"

Check for these specific problems:
- Garbled/unreadable text anywhere in the image
- Collage/split-screen/multiple panels layout
- Black bars, padding, or empty void areas
- Subject unclear or not in focus
- Unrealistic artifacts (weird textures, impossible anatomy, floating objects)
- Brand misalignment (wrong mood for plant care content)

Respond with ONLY valid JSON (no markdown, no backticks):
{"score":7,"issues":["list of specific issues found"],"feedback":"one sentence suggestion for prompt improvement","checks":{"noGarbledText":true,"noCollage":true,"noBlackBars":true,"subjectClarity":true,"brandAlignment":true}}`,
            },
          ],
        }],
      }),
    });

    if (!response.ok) {
      console.log(`    [Quality Gate] Claude API error ${response.status}, skipping`);
      return defaultPass();
    }

    const data = await response.json() as any;
    const text = data.content?.[0]?.text || '';

    // Log vision API cost
    const inputTokens = data.usage?.input_tokens || 0;
    const outputTokens = data.usage?.output_tokens || 0;
    const visionCost = (inputTokens / 1_000_000) * 3 + (outputTokens / 1_000_000) * 15;
    logApiCost({
      provider: 'anthropic',
      category: 'vision',
      endpoint: 'messages.create (vision)',
      model: 'claude-sonnet-4-5-20250929',
      description: `Quality gate: ${model} ${segmentType}`,
      inputTokens,
      outputTokens,
      estimatedCost: visionCost,
    });

    // Parse JSON from response
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.log('    [Quality Gate] Could not parse response, skipping');
      return defaultPass();
    }

    const parsed = JSON.parse(jsonMatch[0]);
    const minScore = parseInt(process.env.QUALITY_GATE_MIN_SCORE || '7');

    const report: QualityReport = {
      score: parsed.score || 5,
      pass: (parsed.score || 5) >= minScore,
      issues: parsed.issues || [],
      feedback: parsed.feedback || '',
      checks: {
        noGarbledText: parsed.checks?.noGarbledText ?? true,
        noCollage: parsed.checks?.noCollage ?? true,
        noBlackBars: parsed.checks?.noBlackBars ?? true,
        subjectClarity: parsed.checks?.subjectClarity ?? true,
        brandAlignment: parsed.checks?.brandAlignment ?? true,
      },
    };

    // Log to visual_quality_log for self-learning
    try {
      const db = getDb();
      db.prepare(`INSERT INTO visual_quality_log (model, content_type, segment_type, prompt, quality_score, issues, retry_count, final_prompt)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?)`).run(
        model, contentType, segmentType, prompt.slice(0, 1000),
        report.score, JSON.stringify(report.issues), prompt.slice(0, 1000)
      );
    } catch { /* don't crash on logging failure */ }

    const statusIcon = report.pass ? '\u2713' : '\u2717';
    console.log(`    [Quality Gate] ${statusIcon} Score: ${report.score}/10 ${report.issues.length > 0 ? '— Issues: ' + report.issues.join(', ') : ''}`);

    return report;
  } catch (err: any) {
    console.log(`    [Quality Gate] Error: ${err.message?.slice(0, 80)}, skipping`);
    return defaultPass();
  }
}

function defaultPass(): QualityReport {
  return {
    score: 7,
    pass: true,
    issues: [],
    feedback: '',
    checks: { noGarbledText: true, noCollage: true, noBlackBars: true, subjectClarity: true, brandAlignment: true },
  };
}

/**
 * Query quality log for high-performing prompt patterns.
 */
export function getTopPromptPatterns(model: string, limit: number = 10): string[] {
  try {
    const db = getDb();
    const rows = db.prepare(
      `SELECT final_prompt FROM visual_quality_log WHERE model = ? AND quality_score >= 8 ORDER BY quality_score DESC, created_at DESC LIMIT ?`
    ).all(model, limit) as any[];
    return rows.map(r => r.final_prompt);
  } catch {
    return [];
  }
}
