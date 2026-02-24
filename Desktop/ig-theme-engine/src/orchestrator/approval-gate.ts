import { getDb, insertRow } from '../database/db.js';
import { publishCarouselPost, publishReel, publishImagePost } from '../integrations/instagram-api.js';
import { addToQueue as bufferQueue } from '../integrations/buffer-api.js';
import { getRenderedAssets, renderScript } from '../rendering/asset-pipeline.js';
import { closeBrowser } from '../rendering/browser-pool.js';
import { scheduleNextSlot } from '../modules/06-growth-strategy/scheduler.js';
import { CONFIG } from '../config/env.js';

type PublishMethod = 'instagram_direct' | 'buffer' | 'manual';

interface PublishResult {
  success: boolean;
  platform: string;
  postId?: string;
  postUrl?: string;
  error?: string;
}

/**
 * Approve a content script and transition it through the pipeline
 */
export function approveContent(scriptId: number): void {
  const db = getDb();
  const script = db.prepare('SELECT * FROM content_scripts WHERE id = ?').get(scriptId) as any;
  if (!script) throw new Error(`Script ${scriptId} not found`);
  db.prepare('UPDATE content_ideas SET status = ? WHERE id = ?').run('approved', script.idea_id);
}

/**
 * Reject a content script
 */
export function rejectContent(scriptId: number): void {
  const db = getDb();
  const script = db.prepare('SELECT * FROM content_scripts WHERE id = ?').get(scriptId) as any;
  if (!script) throw new Error(`Script ${scriptId} not found`);
  db.prepare('UPDATE content_ideas SET status = ? WHERE id = ?').run('archived', script.idea_id);
}

/**
 * Approve content for rendering: sets status to 'approved', renders visuals,
 * then sets status to 'designed' once rendering is complete.
 */
export async function approveContentForRendering(scriptId: number): Promise<{
  success: boolean;
  localPaths: string[];
  publicUrls: string[];
  error?: string;
}> {
  const db = getDb();
  const script = db.prepare('SELECT * FROM content_scripts WHERE id = ?').get(scriptId) as any;
  if (!script) throw new Error(`Script ${scriptId} not found`);

  // Mark as approved (rendering in progress)
  db.prepare('UPDATE content_ideas SET status = ? WHERE id = ?').run('approved', script.idea_id);

  try {
    const rendered = await renderScript(scriptId);
    await closeBrowser();

    if (rendered) {
      // Mark as designed (visuals ready)
      db.prepare('UPDATE content_ideas SET status = ? WHERE id = ?').run('designed', script.idea_id);
      return { success: true, localPaths: rendered.localPaths, publicUrls: rendered.publicUrls };
    } else {
      // Rendering returned nothing — revert to scripted
      db.prepare('UPDATE content_ideas SET status = ? WHERE id = ?').run('scripted', script.idea_id);
      return { success: false, localPaths: [], publicUrls: [], error: 'Nothing to render for this script' };
    }
  } catch (err: any) {
    // On error, revert to scripted so user can retry
    db.prepare('UPDATE content_ideas SET status = ? WHERE id = ?').run('scripted', script.idea_id);
    return { success: false, localPaths: [], publicUrls: [], error: err.message };
  }
}

/**
 * Regenerate visuals for an already-rendered script.
 * Deletes existing rendered_assets, re-renders, and returns new paths/URLs.
 * Status stays 'designed' throughout — no status change needed.
 */
export async function regenerateVisuals(scriptId: number): Promise<{
  success: boolean;
  localPaths: string[];
  publicUrls: string[];
  error?: string;
}> {
  const db = getDb();
  const script = db.prepare('SELECT * FROM content_scripts WHERE id = ?').get(scriptId) as any;
  if (!script) throw new Error(`Script ${scriptId} not found`);

  try {
    // Delete existing rendered assets so renderScript generates fresh ones
    db.prepare('DELETE FROM rendered_assets WHERE script_id = ?').run(scriptId);

    const rendered = await renderScript(scriptId);
    await closeBrowser();

    if (rendered) {
      return { success: true, localPaths: rendered.localPaths, publicUrls: rendered.publicUrls };
    } else {
      return { success: false, localPaths: [], publicUrls: [], error: 'Nothing to render for this script' };
    }
  } catch (err: any) {
    return { success: false, localPaths: [], publicUrls: [], error: err.message };
  }
}

/**
 * Publish approved content to Instagram
 * Requires image/video URLs to be set (user uploads assets first)
 */
export async function publishContent(
  scriptId: number,
  options: {
    method: PublishMethod;
    imageUrls?: string[];
    videoUrl?: string;
  }
): Promise<PublishResult> {
  const db = getDb();
  const script = db.prepare(`
    SELECT cs.*, ci.title, ci.content_type, ci.status as idea_status
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE cs.id = ?
  `).get(scriptId) as any;

  if (!script) return { success: false, platform: 'instagram', error: 'Script not found' };
  if (script.idea_status !== 'designed') {
    return { success: false, platform: 'instagram', error: 'Content must be rendered (designed) before publishing' };
  }

  const caption = script.caption || '';

  // Auto-retrieve rendered asset URLs if not explicitly provided
  if (!options.imageUrls?.length && !options.videoUrl) {
    const assets = getRenderedAssets(scriptId);
    if (assets && assets.publicUrls.length > 0) {
      if (assets.contentType === 'reel') {
        options.videoUrl = assets.publicUrls[0];
      } else {
        options.imageUrls = assets.publicUrls;
      }
    }
  }

  try {
    let result: PublishResult;

    if (options.method === 'instagram_direct') {
      if (script.content_type === 'carousel' && options.imageUrls?.length) {
        const published = await publishCarouselPost(options.imageUrls, caption);
        result = { success: true, platform: 'instagram', postId: published.id, postUrl: published.permalink };
      } else if (script.content_type === 'reel' && options.videoUrl) {
        const published = await publishReel(options.videoUrl, caption);
        result = { success: true, platform: 'instagram', postId: published.id, postUrl: published.permalink };
      } else if (options.imageUrls?.[0]) {
        const published = await publishImagePost(options.imageUrls[0], caption);
        result = { success: true, platform: 'instagram', postId: published.id, postUrl: published.permalink };
      } else {
        return { success: false, platform: 'instagram', error: 'No media URLs provided' };
      }
    } else if (options.method === 'buffer') {
      await bufferQueue({ text: caption, mediaUrls: options.imageUrls });
      result = { success: true, platform: 'buffer' };
    } else {
      // Manual — just mark as published in our system
      result = { success: true, platform: 'manual' };
    }

    // Record in published_content table
    if (result.success) {
      insertRow('published_content', {
        script_id: scriptId,
        platform: 'instagram',
        platform_post_id: result.postId || null,
        platform_post_url: result.postUrl || null,
      });

      // Update idea status
      db.prepare('UPDATE content_ideas SET status = ?, published_at = CURRENT_TIMESTAMP WHERE id = ?')
        .run('published', script.idea_id);
    }

    return result;
  } catch (error: any) {
    return { success: false, platform: 'instagram', error: error.message };
  }
}

/**
 * Approve content and auto-schedule it to the next available time slot.
 */
export function approveAndSchedule(scriptId: number): { calendarId: number; scheduledDate: string; scheduledTime: string; contentType: string } {
  const db = getDb();
  const script = db.prepare(`
    SELECT cs.*, ci.content_type, ci.status as idea_status
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE cs.id = ?
  `).get(scriptId) as any;
  if (!script) throw new Error(`Script ${scriptId} not found`);
  if (script.idea_status !== 'designed') throw new Error('Content must be rendered (designed) before scheduling');

  // Schedule to next available slot
  const slot = scheduleNextSlot(scriptId, script.content_type);
  return slot;
}

/**
 * Get all content awaiting approval
 */
export function getPendingApproval(): any[] {
  const db = getDb();
  return db.prepare(`
    SELECT cs.*, ci.title, ci.content_type, ci.hook, ci.send_trigger
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE ci.status = 'scripted'
    ORDER BY cs.created_at DESC
  `).all();
}

/**
 * Get all rendered content ready to publish
 */
export function getReadyToPublish(): any[] {
  const db = getDb();
  return db.prepare(`
    SELECT cs.*, ci.title, ci.content_type, ci.hook, ci.send_trigger
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE ci.status = 'designed'
    ORDER BY cs.created_at DESC
  `).all();
}
