import chalk from 'chalk';
import { getDb, insertRow } from '../database/db.js';
import { CONFIG } from '../config/env.js';
import { renderCarouselSlides, parseCarouselScript } from './carousel-renderer.js';
import { renderStorySlides, parseStoryScript } from './story-renderer.js';
import { renderReel, parseReelScript } from './reel-renderer.js';
import { uploadImages, uploadVideo } from '../integrations/cloudinary-api.js';
import { closeBrowser } from './browser-pool.js';
import type { RenderConfig, RenderedAssets, DailyRenderedPackage } from './types.js';

/**
 * Get the active render config from the brand_system table,
 * falling back to sensible defaults.
 */
export function getRenderConfig(): RenderConfig {
  const db = getDb();
  const brand = db.prepare(
    'SELECT config_json FROM brand_system WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1'
  ).get() as { config_json: string } | undefined;

  if (brand) {
    try {
      const cfg = JSON.parse(brand.config_json);
      return {
        brandColors: {
          primary: cfg.colorPalette?.primary || '#1B5E20',
          secondary: cfg.colorPalette?.secondary || '#2E7D32',
          accent: cfg.colorPalette?.accent || '#66BB6A',
          background: cfg.colorPalette?.background || '#0D1B0F',
          text: cfg.colorPalette?.text || '#FFFFFF',
        },
        fonts: {
          headline: cfg.typography?.headlineFont || 'Inter',
          body: cfg.typography?.bodyFont || 'Inter',
        },
        handle: '@theplanticu',
      };
    } catch { /* fall through to defaults */ }
  }

  return {
    brandColors: {
      primary: '#1B5E20',
      secondary: '#2E7D32',
      accent: '#66BB6A',
      background: '#0D1B0F',
      text: '#FFFFFF',
    },
    fonts: { headline: 'Inter', body: 'Inter' },
    handle: '@theplanticu',
  };
}

/**
 * Render all assets for a single content script.
 * Returns the rendered asset paths and (if Cloudinary configured) public URLs.
 */
export async function renderScript(scriptId: number): Promise<RenderedAssets | null> {
  const db = getDb();
  const script = db.prepare(`
    SELECT cs.*, ci.content_type
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE cs.id = ?
  `).get(scriptId) as any;

  if (!script) {
    console.log(chalk.red(`Script ${scriptId} not found`));
    return null;
  }

  const config = getRenderConfig();

  try {
    let localPaths: string[] = [];

    if (script.content_type === 'carousel' && script.script_json) {
      const slides = parseCarouselScript(script.script_json);
      localPaths = await renderCarouselSlides(slides, config, scriptId);
    } else if (script.content_type === 'story' && script.story_sequence_json) {
      const slides = parseStoryScript(script.story_sequence_json);
      localPaths = await renderStorySlides(slides, config, scriptId);
    } else if (script.content_type === 'reel' && script.script_json) {
      if (!CONFIG.pipeline.renderReels) {
        console.log(chalk.yellow('  Reel rendering disabled (RENDER_REELS=false)'));
        return null;
      }
      const reelScript = parseReelScript(script.script_json);
      const reelPath = await renderReel(reelScript, config, scriptId);
      localPaths = [reelPath];
    } else {
      console.log(chalk.yellow(`  No renderable content for script ${scriptId} (${script.content_type})`));
      return null;
    }

    // Upload to Cloudinary if configured
    let publicUrls: string[] = [];
    if (CONFIG.cloudinary.cloudName && CONFIG.cloudinary.apiKey) {
      console.log(chalk.gray('  Uploading to Cloudinary...'));
      if (script.content_type === 'reel') {
        const url = await uploadVideo(localPaths[0]);
        publicUrls = [url];
      } else {
        publicUrls = await uploadImages(localPaths);
      }
    }

    // Store in database
    const assetData = {
      script_id: scriptId,
      content_type: script.content_type,
      local_paths: JSON.stringify(localPaths),
      public_urls: JSON.stringify(publicUrls),
      rendered_at: new Date().toISOString(),
    };
    insertRow('rendered_assets', assetData);

    return {
      scriptId,
      contentType: script.content_type,
      localPaths,
      publicUrls,
    };
  } catch (err: any) {
    console.log(chalk.red(`  Render failed for script ${scriptId}: ${err.message}`));
    return null;
  }
}

/**
 * Render all assets for today's daily package (all scripted content).
 * Each content type renders independently — failures are isolated.
 */
export async function renderDailyPackage(): Promise<DailyRenderedPackage> {
  const db = getDb();
  const today = new Date().toISOString().slice(0, 10);

  console.log(chalk.blue('\n  Rendering daily assets...'));

  // Find today's scripts (most recent scripted/approved content)
  const scripts = db.prepare(`
    SELECT cs.id, ci.content_type
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE ci.status IN ('scripted', 'approved')
    AND date(cs.created_at) = date('now')
    ORDER BY cs.created_at DESC
  `).all() as any[];

  const result: DailyRenderedPackage = { date: today };

  for (const script of scripts) {
    try {
      console.log(chalk.gray(`  Rendering ${script.content_type} (script #${script.id})...`));
      const rendered = await renderScript(script.id);
      if (!rendered) continue;

      if (script.content_type === 'carousel') result.carousel = rendered;
      else if (script.content_type === 'story') result.stories = rendered;
      else if (script.content_type === 'reel') result.reel = rendered;
    } catch (err: any) {
      console.log(chalk.red(`  Failed to render ${script.content_type}: ${err.message}`));
    }
  }

  // Clean up browser
  await closeBrowser();

  const rendered = [result.carousel, result.stories, result.reel].filter(Boolean).length;
  console.log(chalk.green(`  Rendered ${rendered}/3 content types`));

  return result;
}

/**
 * Get rendered asset URLs for a script from the database.
 */
export function getRenderedAssets(scriptId: number): RenderedAssets | null {
  const db = getDb();
  const row = db.prepare(
    'SELECT * FROM rendered_assets WHERE script_id = ? ORDER BY rendered_at DESC LIMIT 1'
  ).get(scriptId) as any;

  if (!row) return null;

  return {
    scriptId: row.script_id,
    contentType: row.content_type,
    localPaths: JSON.parse(row.local_paths || '[]'),
    publicUrls: JSON.parse(row.public_urls || '[]'),
  };
}
