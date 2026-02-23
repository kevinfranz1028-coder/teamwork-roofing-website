import { randomUUID } from 'crypto';
import chalk from 'chalk';
import { askClaudeJSON } from '../../integrations/claude-client.js';
import { DAILY_ENGINE_SYSTEM, OPTIONS_ENGINE_USER, formatBriefContext, type CreativeBrief } from './prompts.js';
import { buildCarousel } from '../03-content-builder/carousel-builder.js';
import { buildReel } from '../03-content-builder/reel-builder.js';
import { renderScript } from '../../rendering/asset-pipeline.js';
import { closeBrowser } from '../../rendering/browser-pool.js';
import { getDb, insertRow } from '../../database/db.js';
import { CONFIG } from '../../config/env.js';

interface ContentOption {
  title: string;
  content_type: 'carousel' | 'reel';
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
 * Generate 5 content options, script them, render visual assets,
 * and return a batch ready for dashboard preview.
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

  // Step 1: Generate 5 ideas via Claude
  console.log(chalk.gray('  Step 1/3: Generating ideas via Claude...'));
  const userPrompt = briefContext
    ? OPTIONS_ENGINE_USER(niche, CONFIG.content.carouselSlideCount) + briefContext
    : OPTIONS_ENGINE_USER(niche, CONFIG.content.carouselSlideCount);

  const result = await askClaudeJSON<OptionsResult>({
    systemPrompt: DAILY_ENGINE_SYSTEM(niche, briefContext),
    userPrompt,
    maxTokens: 4096,
  });

  if (!result.options || result.options.length === 0) {
    throw new Error('Claude returned no options');
  }

  // Step 2: Insert ideas + script each one
  console.log(chalk.gray(`  Step 2/3: Scripting ${result.options.length} ideas...`));

  // Load brand system for builders
  const brand = db.prepare(
    'SELECT config_json FROM brand_system WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
  ).get() as { config_json: string } | undefined;
  const brandSystem = brand ? JSON.parse(brand.config_json) : {};

  const batchOptions: GeneratedBatch['options'] = [];

  for (let i = 0; i < result.options.length; i++) {
    const opt = result.options[i];
    console.log(chalk.gray(`    [${i + 1}/5] ${opt.content_type}: ${opt.title}`));

    // Insert idea into content_ideas
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
      status: 'scripted',
      batch_id: batchId,
    }) as number;

    // Build script via existing builders
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

    // Find the script that was just inserted
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

  // Step 3: Render each script via Puppeteer
  console.log(chalk.gray('  Step 3/3: Rendering visual assets...'));
  for (const option of batchOptions) {
    try {
      console.log(chalk.gray(`    Rendering ${option.contentType} (script #${option.scriptId})...`));
      const rendered = await renderScript(option.scriptId);
      if (rendered) {
        option.localPaths = rendered.localPaths;
        option.publicUrls = rendered.publicUrls;
      }
    } catch (err: any) {
      console.log(chalk.yellow(`    Render failed for script ${option.scriptId}: ${err.message}`));
    }
  }

  await closeBrowser();

  // Mark batch as ready
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
      hashtags: idea.hashtags ? JSON.parse(idea.hashtags) : [],
      dmTrigger: idea.dm_trigger_keyword,
      scriptJson: idea.script_json,
      localPaths,
      publicUrls,
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
