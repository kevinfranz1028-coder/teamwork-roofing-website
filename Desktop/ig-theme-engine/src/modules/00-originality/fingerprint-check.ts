import { getDb } from '../../database/db.js';
import { askClaudeJSON } from '../../integrations/claude-client.js';

interface FingerprintResult {
  isOriginal: boolean;
  overallScore: number; // 1-10 originality score
  flags: string[];      // any potential overlap warnings
  similarities: Array<{
    existingContentId: number;
    similarityType: string;
    overlapPercentage: number;
    description: string;
  }>;
  recommendations: string[];
}

/**
 * Check new content against existing published/scripted content
 * Uses text-based similarity (hook, caption, slide headlines)
 * and AI-assisted conceptual similarity detection
 */
export async function checkFingerprint(content: {
  title: string;
  hook: string;
  caption: string;
  contentType: string;
  slideHeadlines?: string[];
}): Promise<FingerprintResult> {
  const db = getDb();

  // Fetch recent content for comparison
  const recentScripts = db.prepare(`
    SELECT cs.id, cs.content_type, cs.script_json, cs.caption, ci.title, ci.hook
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE cs.created_at > datetime('now', '-90 days')
    ORDER BY cs.created_at DESC
    LIMIT 50
  `).all() as any[];

  if (recentScripts.length === 0) {
    return {
      isOriginal: true,
      overallScore: 10,
      flags: [],
      similarities: [],
      recommendations: ['First content piece — no existing content to compare against.'],
    };
  }

  // Build comparison context
  const existingContent = recentScripts.map(s => ({
    id: s.id,
    type: s.content_type,
    title: s.title,
    hook: s.hook,
    captionPreview: (s.caption || '').slice(0, 100),
  }));

  // Use Claude to detect conceptual similarity
  const result = await askClaudeJSON<FingerprintResult>({
    systemPrompt: `You are a content originality auditor for an Instagram theme page. Your job is to compare a NEW piece of content against EXISTING content from the same page to ensure no self-plagiarism, repetitive hooks, or recycled concepts.

SCORING:
- 9-10: Completely original concept, angle, and execution
- 7-8: Original concept but some overlap in framing or structure
- 5-6: Similar topic covered before but different angle
- 3-4: High overlap — same concept with minor variations
- 1-2: Near-duplicate — should not be published`,

    userPrompt: `Check this NEW content against our existing library:

NEW CONTENT:
- Title: "${content.title}"
- Hook: "${content.hook}"
- Type: ${content.contentType}
- Caption preview: "${content.caption.slice(0, 200)}"
${content.slideHeadlines ? `- Slide headlines: ${content.slideHeadlines.join(' | ')}` : ''}

EXISTING CONTENT LIBRARY (last 90 days):
${JSON.stringify(existingContent, null, 2)}

Return JSON with:
- isOriginal (boolean): true if score >= 7
- overallScore (1-10): originality rating
- flags (string[]): any warnings about overlap
- similarities (array): each with existingContentId, similarityType ("hook", "concept", "angle", "structure"), overlapPercentage (0-100), description
- recommendations (string[]): how to make it more original if score < 8`,
    maxTokens: 2048,
  });

  return result;
}

/**
 * Quick text-based similarity check (no API call)
 * Returns a 0-1 score where 0 = no similarity, 1 = identical
 */
export function quickTextSimilarity(text1: string, text2: string): number {
  const words1 = new Set(text1.toLowerCase().split(/\s+/).filter(w => w.length > 3));
  const words2 = new Set(text2.toLowerCase().split(/\s+/).filter(w => w.length > 3));

  if (words1.size === 0 || words2.size === 0) return 0;

  let overlap = 0;
  for (const word of words1) {
    if (words2.has(word)) overlap++;
  }

  return overlap / Math.max(words1.size, words2.size);
}

/**
 * Batch check: run fingerprint on all queued content
 */
export async function auditQueue(): Promise<Array<{ scriptId: number; result: FingerprintResult }>> {
  const db = getDb();
  const queued = db.prepare(`
    SELECT cs.id, cs.script_json, cs.caption, cs.content_type, ci.title, ci.hook
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE ci.status = 'scripted' AND cs.originality_verified = 0
  `).all() as any[];

  const results: Array<{ scriptId: number; result: FingerprintResult }> = [];

  for (const item of queued) {
    const script = JSON.parse(item.script_json);
    const slideHeadlines = script.slides?.map((s: any) => s.headline).filter(Boolean);

    const result = await checkFingerprint({
      title: item.title,
      hook: item.hook,
      caption: item.caption || '',
      contentType: item.content_type,
      slideHeadlines,
    });

    // Mark as verified in database
    db.prepare('UPDATE content_scripts SET originality_verified = 1 WHERE id = ?')
      .run(item.id);

    results.push({ scriptId: item.id, result });
  }

  return results;
}
