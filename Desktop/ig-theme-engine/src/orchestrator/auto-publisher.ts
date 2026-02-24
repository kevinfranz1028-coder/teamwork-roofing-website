import chalk from 'chalk';
import { getDb, insertRow } from '../database/db.js';
import { publishCarouselPost, publishReel } from '../integrations/instagram-api.js';
import { getRenderedAssets } from '../rendering/asset-pipeline.js';
import type { DailyRenderedPackage } from '../rendering/types.js';

interface AutoPublishResult {
  published: number;
  failed: number;
  results: {
    contentType: string;
    success: boolean;
    postId?: string;
    postUrl?: string;
    error?: string;
  }[];
}

/**
 * Auto-publish rendered assets to Instagram.
 * Publishes carousel, reel, and stories independently.
 * Failures in one type don't block others.
 */
export async function autoPublish(dailyPackage: DailyRenderedPackage): Promise<AutoPublishResult> {
  const result: AutoPublishResult = { published: 0, failed: 0, results: [] };
  const db = getDb();

  // Publish carousel
  if (dailyPackage.carousel && dailyPackage.carousel.publicUrls.length > 0) {
    try {
      console.log(chalk.gray('  Publishing carousel to Instagram...'));
      const script = db.prepare(`
        SELECT cs.caption FROM content_scripts cs WHERE cs.id = ?
      `).get(dailyPackage.carousel.scriptId) as any;

      const published = await publishCarouselPost(
        dailyPackage.carousel.publicUrls,
        script?.caption || ''
      );

      // Auto-approve and record
      autoApproveAndRecord(dailyPackage.carousel.scriptId, published.id, published.permalink);

      result.published++;
      result.results.push({
        contentType: 'carousel',
        success: true,
        postId: published.id,
        postUrl: published.permalink,
      });
      console.log(chalk.green(`  Carousel published: ${published.permalink || published.id}`));
    } catch (err: any) {
      result.failed++;
      result.results.push({ contentType: 'carousel', success: false, error: err.message });
      console.log(chalk.red(`  Carousel publish failed: ${err.message}`));
    }
  }

  // Publish reel
  if (dailyPackage.reel && dailyPackage.reel.publicUrls.length > 0) {
    try {
      console.log(chalk.gray('  Publishing reel to Instagram...'));
      const script = db.prepare(`
        SELECT cs.caption FROM content_scripts cs WHERE cs.id = ?
      `).get(dailyPackage.reel.scriptId) as any;

      const published = await publishReel(
        dailyPackage.reel.publicUrls[0],
        script?.caption || ''
      );

      autoApproveAndRecord(dailyPackage.reel.scriptId, published.id, published.permalink);

      result.published++;
      result.results.push({
        contentType: 'reel',
        success: true,
        postId: published.id,
        postUrl: published.permalink,
      });
      console.log(chalk.green(`  Reel published: ${published.permalink || published.id}`));
    } catch (err: any) {
      result.failed++;
      result.results.push({ contentType: 'reel', success: false, error: err.message });
      console.log(chalk.red(`  Reel publish failed: ${err.message}`));
    }
  }

  // Stories are published as individual image posts (Instagram Graph API doesn't support story publishing directly)
  // They're rendered and stored for manual story upload or Buffer integration
  if (dailyPackage.stories && dailyPackage.stories.publicUrls.length > 0) {
    console.log(chalk.yellow(`  Stories rendered (${dailyPackage.stories.publicUrls.length} slides) — stored for manual upload`));
    result.results.push({
      contentType: 'story',
      success: true,
    });
  }

  return result;
}

/**
 * Auto-publish a single script by its ID.
 * Looks up rendered assets from the DB.
 */
export async function autoPublishScript(scriptId: number): Promise<{ success: boolean; error?: string }> {
  const assets = getRenderedAssets(scriptId);
  if (!assets || assets.publicUrls.length === 0) {
    return { success: false, error: 'No rendered assets with public URLs found' };
  }

  const db = getDb();
  const script = db.prepare(`
    SELECT cs.*, ci.content_type
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE cs.id = ?
  `).get(scriptId) as any;

  if (!script) return { success: false, error: 'Script not found' };

  try {
    if (script.content_type === 'carousel') {
      const published = await publishCarouselPost(assets.publicUrls, script.caption || '');
      autoApproveAndRecord(scriptId, published.id, published.permalink);
      return { success: true };
    } else if (script.content_type === 'reel') {
      const published = await publishReel(assets.publicUrls[0], script.caption || '');
      autoApproveAndRecord(scriptId, published.id, published.permalink);
      return { success: true };
    }
    return { success: false, error: `Unsupported content type for auto-publish: ${script.content_type}` };
  } catch (err: any) {
    // Extract actual Instagram API error details from axios response
    const igError = err.response?.data?.error;
    const detail = igError
      ? `${igError.error_user_msg || igError.message} (code ${igError.code}${igError.error_subcode ? '/' + igError.error_subcode : ''})`
      : err.message;
    console.error(`autoPublishScript failed for script ${scriptId}:`, detail);
    return { success: false, error: detail };
  }
}

function autoApproveAndRecord(scriptId: number, postId: string, postUrl?: string) {
  const db = getDb();

  // Get idea_id
  const script = db.prepare('SELECT idea_id FROM content_scripts WHERE id = ?').get(scriptId) as any;
  if (script) {
    db.prepare('UPDATE content_ideas SET status = ?, published_at = CURRENT_TIMESTAMP WHERE id = ?')
      .run('published', script.idea_id);
  }

  // Record in published_content
  insertRow('published_content', {
    script_id: scriptId,
    platform: 'instagram',
    platform_post_id: postId,
    platform_post_url: postUrl || null,
  });
}
