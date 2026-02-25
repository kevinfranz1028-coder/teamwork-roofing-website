import { randomUUID } from 'crypto';
import chalk from 'chalk';
import { askClaudeJSON } from '../../integrations/claude-client.js';
import { DAILY_ENGINE_SYSTEM, OPTIONS_ENGINE_USER, formatBriefContext, type CreativeBrief } from './prompts.js';
import { buildCarousel } from '../03-content-builder/carousel-builder.js';
import { buildReel } from '../03-content-builder/reel-builder.js';
import { getDb, insertRow } from '../../database/db.js';
import { CONFIG } from '../../config/env.js';

interface ContentOption {
  title: string;
  content_type: 'carousel' | 'reel';
  content_pillar?: string;
  hook: string;
  value_proposition: string;
  emotional_trigger: string;
  send_trigger: string;
  send_probability: string;
  save_probability: string;
  caption_seo_keywords: string[];
  formatNotes: string;
}

interface OptionsResult {
  options: ContentOption[];
}

export interface GeneratedBatch {
  batchId: string;
  options: Array<{
    ideaId: number;
    scriptId: number;
    contentType: string;
    title: string;
    hook: string;
    sendTrigger: string;
    localPaths: string[];
    publicUrls: string[];
  }>;
}

/**
 * Generate 5 content options and script them (text-only, no rendering).
 * Rendering happens later when the user approves individual content.
 */
export async function generateContentOptions(): Promise<GeneratedBatch> {
  const niche = CONFIG.app.niche;
  if (!niche) throw new Error('Set NICHE in .env first');

  const batchId = randomUUID();
  const db = getDb();

  // Create batch record
  insertRow('content_option_batches', {
    id: batchId,
    status: 'generating',
    option_count: 5,
  });

  console.log(chalk.blue(`\n  Generating 5 content options (batch: ${batchId.slice(0, 8)})...`));

  // Load active creative brief
  const activeBrief = db.prepare(
    'SELECT * FROM creative_briefs WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1'
  ).get() as CreativeBrief | undefined;

  const briefContext = formatBriefContext(activeBrief ?? null);
  if (activeBrief) {
    console.log(chalk.gray(`  Using creative brief: "${activeBrief.title}"`));
  }

  // Load recent titles for deduplication (last 30 ideas)
  const recentIdeas = db.prepare(
    'SELECT title, content_pillar FROM content_ideas ORDER BY created_at DESC LIMIT 30'
  ).all() as { title: string; content_pillar: string | null }[];

  const recentTitles = recentIdeas.map(i => i.title);

  // Count pillar distribution from last 30 ideas
  const pillarCounts: Record<string, number> = {
    'diagnosis': 0, 'treatment': 0, 'prevention': 0, 'debunk': 0, 'trending-rescue': 0
  };
  for (const idea of recentIdeas) {
    if (idea.content_pillar && pillarCounts[idea.content_pillar] !== undefined) {
      pillarCounts[idea.content_pillar]++;
    }
  }

  console.log(chalk.gray(`  Dedup: ${recentTitles.length} recent titles loaded, pillar counts: ${JSON.stringify(pillarCounts)}`));

  // Step 1: Generate 5 ideas via Claude
  console.log(chalk.gray('  Step 1/2: Generating ideas via Claude...'));
  const userPrompt = briefContext
    ? OPTIONS_ENGINE_USER(niche, CONFIG.content.carouselSlideCount, recentTitles, pillarCounts) + briefContext
    : OPTIONS_ENGINE_USER(niche, CONFIG.content.carouselSlideCount, recentTitles, pillarCounts);

  const result = await askClaudeJSON<OptionsResult>({
    systemPrompt: DAILY_ENGINE_SYSTEM(niche, briefContext),
    userPrompt,
    maxTokens: 4096,
  });

  if (!result.options || result.options.length === 0) {
    throw new Error('Claude returned no options');
  }

  // Step 2: Insert all ideas, then script them in PARALLEL
  console.log(chalk.gray(`  Step 2/2: Scripting ${result.options.length} ideas in parallel...`));

  // Load brand system for builders
  const brand = db.prepare(
    'SELECT config_json FROM brand_system WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
  ).get() as { config_json: string } | undefined;
  const brandSystem = brand ? JSON.parse(brand.config_json) : {};

  // Insert all ideas into DB first (fast, synchronous)
  const ideaEntries = result.options.map((opt, i) => {
    console.log(chalk.gray(`    [${i + 1}/5] ${opt.content_type}: ${opt.title}`));
    const ideaId = insertRow('content_ideas', {
      title: opt.title,
      content_type: opt.content_type,
      hook: opt.hook,
      value_proposition: opt.value_proposition,
      emotional_trigger: opt.emotional_trigger,
      send_trigger: opt.send_trigger,
      send_probability: opt.send_probability,
      save_probability: opt.save_probability,
      caption_seo_keywords: JSON.stringify(opt.caption_seo_keywords),
      content_pillar: opt.content_pillar || null,
      status: 'scripted',
      batch_id: batchId,
    }) as number;
    return { opt, ideaId };
  });

  // Script all 5 ideas in parallel via Claude
  const scriptStartTime = Date.now();
  console.log(chalk.gray(`    Dispatching ${ideaEntries.length} script builds in parallel...`));
  await Promise.all(ideaEntries.map(async ({ opt, ideaId }) => {
    const builderIdea = {
      id: ideaId,
      title: opt.title,
      hook: opt.hook,
      formatNotes: opt.formatNotes || '',
      captionKeywords: opt.caption_seo_keywords || [],
    };
    try {
      if (opt.content_type === 'carousel') {
        await buildCarousel(builderIdea, brandSystem);
      } else {
        await buildReel(builderIdea, brandSystem);
      }
    } catch (err: any) {
      console.log(chalk.yellow(`    Script failed for "${opt.title}": ${err.message}`));
    }
  }));
  console.log(chalk.gray(`    All scripts built in ${((Date.now() - scriptStartTime) / 1000).toFixed(1)}s`));

  // Collect results
  const batchOptions: GeneratedBatch['options'] = [];
  for (const { opt, ideaId } of ideaEntries) {
    const script = db.prepare(
      'SELECT id FROM content_scripts WHERE idea_id = ? ORDER BY created_at DESC LIMIT 1'
    ).get(ideaId) as { id: number } | undefined;

    if (script) {
      batchOptions.push({
        ideaId,
        scriptId: script.id,
        contentType: opt.content_type,
        title: opt.title,
        hook: opt.hook,
        sendTrigger: opt.send_trigger,
        localPaths: [],
        publicUrls: [],
      });
    }
  }

  // Mark batch as ready (text-only — rendering happens on approval)
  db.prepare('UPDATE content_option_batches SET status = ? WHERE id = ?')
    .run('ready', batchId);

  console.log(chalk.green(`\n  Batch ${batchId.slice(0, 8)} ready with ${batchOptions.length} options`));

  return { batchId, options: batchOptions };
}

/**
 * Get the latest batch with all option details for the dashboard.
 */
export function getLatestBatch(): any | null {
  const db = getDb();

  const batch = db.prepare(`
    SELECT * FROM content_option_batches
    WHERE status IN ('ready', 'selected')
    ORDER BY created_at DESC LIMIT 1
  `).get() as any;

  if (!batch) return null;

  const ideas = db.prepare(`
    SELECT ci.*, cs.id as script_id, cs.script_json, cs.caption, cs.hashtags,
           cs.dm_trigger_keyword, cs.content_type as script_type
    FROM content_ideas ci
    LEFT JOIN content_scripts cs ON cs.idea_id = ci.id
    WHERE ci.batch_id = ?
    ORDER BY ci.id ASC
  `).all(batch.id) as any[];

  const options = ideas.map((idea: any) => {
    // Get rendered assets
    let localPaths: string[] = [];
    let publicUrls: string[] = [];
    if (idea.script_id) {
      const assets = db.prepare(
        'SELECT * FROM rendered_assets WHERE script_id = ? ORDER BY rendered_at DESC LIMIT 1'
      ).get(idea.script_id) as any;
      if (assets) {
        localPaths = JSON.parse(assets.local_paths || '[]');
        publicUrls = JSON.parse(assets.public_urls || '[]');
      }
    }

    return {
      ideaId: idea.id,
      scriptId: idea.script_id,
      contentType: idea.content_type,
      title: idea.title,
      hook: idea.hook,
      sendTrigger: idea.send_trigger,
      valueProp: idea.value_proposition,
      emotionalTrigger: idea.emotional_trigger,
      sendProbability: idea.send_probability,
      caption: idea.caption,
      hashtags: idea.hashtags ? (() => { try { const h = JSON.parse(idea.hashtags); return Array.isArray(h) ? h : String(h).split(/\s+/); } catch { return String(idea.hashtags).split(/\s+/); } })() : [],
      dmTrigger: idea.dm_trigger_keyword,
      scriptJson: idea.script_json,
      localPaths,
      publicUrls,
      ideaStatus: idea.status,
    };
  });

  return {
    batchId: batch.id,
    status: batch.status,
    selectedIdeaId: batch.selected_idea_id,
    createdAt: batch.created_at,
    options,
  };
}
