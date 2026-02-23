import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getDb, insertRow } from '../../database/db.js';
import { CROSS_PLATFORM_SYSTEM, adaptContentPrompt } from './prompts.js';

interface AdaptedContent {
  platform: string;
  adaptedFormat: string;
  title: string;
  hook: string;
  body: string;
  caption: string;
  hashtags: string[];
  keywords: string[];
  schedulingNote: string;
  adaptationNotes: string;
}

const SUPPORTED_PLATFORMS = ['tiktok', 'youtube_shorts', 'pinterest', 'twitter'] as const;
type Platform = (typeof SUPPORTED_PLATFORMS)[number];

export async function adaptForPlatform(
  scriptId: number,
  targetPlatform: Platform
): Promise<AdaptedContent> {
  const db = getDb();

  const script = db.prepare(`
    SELECT cs.*, ci.title
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE cs.id = ?
  `).get(scriptId) as any;

  if (!script) throw new Error(`Script ${scriptId} not found`);

  const originalScript = JSON.parse(script.script_json);

  const adapted = await askClaudeJSON<AdaptedContent>({
    systemPrompt: CROSS_PLATFORM_SYSTEM,
    userPrompt: adaptContentPrompt(originalScript, 'instagram', targetPlatform),
    maxTokens: 4096,
  });

  // Store in cross-platform log
  insertRow('cross_platform_log', {
    original_script_id: scriptId,
    platform: targetPlatform,
    adapted_script_json: JSON.stringify(adapted),
    published: 0,
  });

  return adapted;
}

export async function adaptForAllPlatforms(
  scriptId: number
): Promise<Record<string, AdaptedContent>> {
  const results: Record<string, AdaptedContent> = {};

  for (const platform of SUPPORTED_PLATFORMS) {
    results[platform] = await adaptForPlatform(scriptId, platform);
  }

  return results;
}

export function getCrossPlatformLog(scriptId?: number): any[] {
  const db = getDb();

  if (scriptId) {
    return db.prepare('SELECT * FROM cross_platform_log WHERE original_script_id = ?')
      .all(scriptId);
  }

  return db.prepare('SELECT * FROM cross_platform_log ORDER BY id DESC LIMIT 50').all();
}

export function markAsPublished(logId: number, postUrl: string): void {
  const db = getDb();
  db.prepare('UPDATE cross_platform_log SET published = 1, platform_post_url = ?, published_at = CURRENT_TIMESTAMP WHERE id = ?')
    .run(postUrl, logId);
}

export function getDistributionStats(): {
  totalAdapted: number;
  totalPublished: number;
  byPlatform: Record<string, { adapted: number; published: number }>;
} {
  const db = getDb();

  const stats = db.prepare(`
    SELECT platform, COUNT(*) as adapted, SUM(published) as published
    FROM cross_platform_log
    GROUP BY platform
  `).all() as any[];

  const byPlatform: Record<string, { adapted: number; published: number }> = {};
  let totalAdapted = 0;
  let totalPublished = 0;

  for (const s of stats) {
    byPlatform[s.platform] = { adapted: s.adapted, published: s.published || 0 };
    totalAdapted += s.adapted;
    totalPublished += s.published || 0;
  }

  return { totalAdapted, totalPublished, byPlatform };
}
