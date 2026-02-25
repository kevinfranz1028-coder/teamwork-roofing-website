import express from 'express';
import cors from 'cors';
import path from 'path';
import archiver from 'archiver';
import { readdirSync, readFileSync, statSync, existsSync } from 'fs';
import { CONFIG } from './config/env.js';
import { getDb, getRows } from './database/db.js';
import { getState, runDailyPipeline } from './orchestrator/master.js';
import { approveContent, rejectContent, publishContent, getPendingApproval, getReadyToPublish, approveAndSchedule, approveContentForRendering, regenerateVisuals } from './orchestrator/approval-gate.js';
import { generateWeeklyScorecard, refreshAnalytics } from './orchestrator/analytics-loop.js';
import { scanTrends } from './modules/04-daily-output/trend-scanner.js';
import { generateDesignSystem, getDesignDirection } from './modules/05-design-system/design-manager.js';
import { generateContentCalendar, getUpcomingCalendar, getTodaysSchedule, getScheduledQueue, removeFromSchedule } from './modules/06-growth-strategy/scheduler.js';
import { generateEngagementProtocol } from './modules/06-growth-strategy/engagement-engine.js';
import { generateRevenueStrategy, getRevenueOverview } from './modules/07-monetization/revenue-tracker.js';
import { generateRoadmap, getCurrentPhase } from './modules/08-scaling/roadmap-engine.js';
import { createDMFlow, generateLeadMagnets, getActiveDMFlows, getEmailListStats } from './modules/09-dm-automation/dm-flows.js';
import { adaptForPlatform, getCrossPlatformLog, getDistributionStats } from './modules/10-cross-platform/distributor.js';
import { auditQueue } from './modules/00-originality/fingerprint-check.js';
import { renderScript, renderDailyPackage } from './rendering/asset-pipeline.js';
import { autoPublish, autoPublishScript } from './orchestrator/auto-publisher.js';
import { generateContentOptions, getLatestBatch } from './modules/04-daily-output/options-engine.js';
import { runMigrations } from './database/migrations.js';
import { checkAndRefreshToken, testMediaContainer } from './integrations/instagram-api.js';
import { syncFlowsToManyChat } from './integrations/manychat-api.js';
import {
  DEFAULT_CONTENT_BUILDER_SYSTEM,
  DEFAULT_CAROUSEL_DESIGN_INSTRUCTION,
  DEFAULT_REEL_VISUAL_INSTRUCTION,
} from './modules/03-content-builder/prompts.js';

runMigrations();

const app = express();
app.use(cors());
app.use(express.json());

// ─── Authentication Middleware ──────────────────────
app.use((req: express.Request, res: express.Response, next: express.NextFunction) => {
  // Only protect API routes
  if (!req.path.startsWith('/api/')) return next();
  // Allow webhook endpoints (they have their own auth)
  if (req.path.startsWith('/api/webhooks/')) return next();
  // No key configured = no auth required (backward compatible)
  if (!CONFIG.app.dashboardApiKey) return next();

  const apiKey = req.headers['x-api-key'] || req.query.apiKey;
  if (apiKey !== CONFIG.app.dashboardApiKey) {
    return res.status(401).json({ error: 'Unauthorized. Provide X-API-Key header.' });
  }
  next();
});

// ─── API Routes ─────────────────────────────────────

// Pipeline status
app.get('/api/status', (req, res) => {
  res.json(getState());
});

// Trigger daily pipeline manually
app.post('/api/pipeline/run', async (req, res) => {
  try {
    await runDailyPipeline();
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Content Queue ──────────────────────────────────
app.get('/api/queue', (req, res) => {
  const db = getDb();
  const scripts = db.prepare(`
    SELECT cs.id, cs.idea_id, cs.content_type, cs.script_json, cs.caption,
           cs.hashtags, cs.dm_trigger_keyword, cs.created_at,
           ci.title, ci.status as idea_status, ci.send_trigger,
           ci.hook, ci.send_probability, ci.batch_id,
           ra.local_paths, ra.public_urls
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    LEFT JOIN rendered_assets ra ON ra.script_id = cs.id
    WHERE ci.status IN ('scripted', 'approved', 'designed', 'published')
    ORDER BY cs.created_at DESC
    LIMIT 100
  `).all().map((row: any) => ({
    ...row,
    local_paths: row.local_paths ? JSON.parse(row.local_paths) : [],
    public_urls: row.public_urls ? JSON.parse(row.public_urls) : [],
  }));
  res.json(scripts);
});

app.get('/api/queue/pending', (_req, res) => {
  res.json(getPendingApproval());
});

app.get('/api/queue/ready', (_req, res) => {
  res.json(getReadyToPublish());
});

app.post('/api/queue/:id/approve', (req, res) => {
  try {
    const scriptId = parseInt(req.params.id);
    approveContent(scriptId);

    // Auto-create DM flow if content has a DM trigger keyword
    const db = getDb();
    const script = db.prepare('SELECT dm_trigger_keyword, story_sequence_json FROM content_scripts WHERE id = ?').get(scriptId) as any;
    if (script?.dm_trigger_keyword) {
      const existing = db.prepare('SELECT id FROM dm_flows WHERE trigger_keyword = ?').get(script.dm_trigger_keyword);
      if (!existing) {
        const storySequence = JSON.parse(script.story_sequence_json || '{}');
        db.prepare(
          'INSERT INTO dm_flows (trigger_keyword, flow_name, flow_steps_json, is_active) VALUES (?, ?, ?, 1)'
        ).run(
          script.dm_trigger_keyword,
          `Auto: ${script.dm_trigger_keyword}`,
          JSON.stringify([{ type: 'text', text: storySequence.dmTriggerValue || "Thanks for your interest! Here's your resource." }])
        );
      }
    }

    res.json({ success: true });
  } catch (err: any) {
    res.status(400).json({ error: err.message });
  }
});

app.post('/api/queue/:id/reject', (req, res) => {
  try {
    rejectContent(parseInt(req.params.id));
    res.json({ success: true });
  } catch (err: any) {
    res.status(400).json({ error: err.message });
  }
});

app.post('/api/queue/:id/approve-content', async (req, res) => {
  try {
    const result = await approveContentForRendering(parseInt(req.params.id));
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post('/api/queue/:id/regenerate', async (req, res) => {
  try {
    const result = await regenerateVisuals(parseInt(req.params.id));
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ─── Publishing ─────────────────────────────────────
app.post('/api/queue/:id/publish', async (req, res) => {
  try {
    const { method, imageUrls, videoUrl } = req.body;
    const result = await publishContent(parseInt(req.params.id), {
      method: method || 'manual',
      imageUrls,
      videoUrl,
    });
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Instagram Token Management ────────────────────
app.get('/api/instagram/token-health', async (_req, res) => {
  try {
    const result = await checkAndRefreshToken();
    res.json({ success: true, daysLeft: result.daysLeft, refreshed: result.refreshed });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post('/api/instagram/refresh-token', async (_req, res) => {
  try {
    const result = await checkAndRefreshToken();
    res.json({ success: true, ...result });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post('/api/instagram/test-container', async (req, res) => {
  try {
    const { imageUrl } = req.body;
    if (!imageUrl) return res.status(400).json({ error: 'imageUrl required' });
    const result = await testMediaContainer(imageUrl);
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ─── Analytics ──────────────────────────────────────
app.get('/api/analytics', (req, res) => {
  const db = getDb();
  const recent = db.prepare(`
    SELECT * FROM published_content
    WHERE published_at > datetime('now', '-30 days')
    ORDER BY sends_per_reach DESC
  `).all();
  res.json(recent);
});

app.post('/api/analytics/refresh', async (_req, res) => {
  try {
    await refreshAnalytics();
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/scorecard', (req, res) => {
  const scorecard = generateWeeklyScorecard();
  res.json(scorecard);
});

app.get('/api/scorecard/history', (req, res) => {
  const history = getRows('weekly_scorecard');
  res.json(history);
});

// ─── Revenue ────────────────────────────────────────
app.get('/api/revenue', (req, res) => {
  const revenue = getRows('revenue');
  res.json(revenue);
});

app.get('/api/revenue/overview', (_req, res) => {
  res.json(getRevenueOverview());
});

app.post('/api/revenue', (req, res) => {
  const db = getDb();
  const { date, source, description, amount } = req.body;
  const id = db.prepare(
    'INSERT INTO revenue (date, source, description, amount) VALUES (?, ?, ?, ?)'
  ).run(date, source, description, amount).lastInsertRowid;
  res.json({ id });
});

app.post('/api/revenue/strategy', async (req, res) => {
  try {
    const { followers } = req.body;
    const strategy = await generateRevenueStrategy(followers || 0);
    res.json(strategy);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Niches ─────────────────────────────────────────
app.get('/api/niches', (req, res) => {
  const niches = getRows('niches');
  res.json(niches);
});

// ─── Trends ─────────────────────────────────────────
app.get('/api/trends', async (_req, res) => {
  try {
    const trends = await scanTrends();
    res.json(trends);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Design System ──────────────────────────────────
app.get('/api/design', (_req, res) => {
  try {
    const direction = getDesignDirection();
    res.json(direction);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/design/generate', async (_req, res) => {
  try {
    const ds = await generateDesignSystem(CONFIG.app.niche);
    res.json(ds);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Content Calendar ───────────────────────────────
app.get('/api/calendar', (_req, res) => {
  res.json(getUpcomingCalendar());
});

app.get('/api/calendar/today', (_req, res) => {
  res.json(getTodaysSchedule());
});

app.post('/api/calendar/generate', async (req, res) => {
  try {
    const { pillars } = req.body;
    const cal = await generateContentCalendar(pillars || ['education', 'diagnosis', 'transformation', 'community', 'promotion']);
    res.json(cal);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Engagement ─────────────────────────────────────
app.post('/api/engagement/protocol', async (_req, res) => {
  try {
    const protocol = await generateEngagementProtocol();
    res.json(protocol);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Scaling Roadmap ────────────────────────────────
app.get('/api/roadmap/phase', (req, res) => {
  const followers = parseInt(req.query.followers as string) || 0;
  res.json(getCurrentPhase(followers));
});

app.post('/api/roadmap/generate', async (req, res) => {
  try {
    const { followers } = req.body;
    const roadmap = await generateRoadmap(followers || 0);
    res.json(roadmap);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── DM Flows ───────────────────────────────────────
app.get('/api/dm-flows', (_req, res) => {
  res.json(getActiveDMFlows());
});

app.post('/api/dm-flows', async (req, res) => {
  try {
    const { keyword, value } = req.body;
    const flow = await createDMFlow(keyword, value);
    res.json(flow);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/dm-flows/lead-magnets', async (_req, res) => {
  try {
    const magnets = await generateLeadMagnets();
    res.json(magnets);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/dm-flows/sync', async (_req, res) => {
  try {
    const result = await syncFlowsToManyChat();
    res.json({ success: true, ...result });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/email-list', (_req, res) => {
  res.json(getEmailListStats());
});

app.get('/api/email-list/stats', (_req, res) => {
  const db = getDb();
  const total = db.prepare('SELECT COUNT(*) as count FROM email_list WHERE is_active = 1').get() as any;
  const bySource = db.prepare('SELECT source, COUNT(*) as count FROM email_list GROUP BY source').all();
  const byLeadMagnet = db.prepare('SELECT lead_magnet, COUNT(*) as count FROM email_list GROUP BY lead_magnet').all();
  const recent = db.prepare('SELECT * FROM email_list ORDER BY subscribed_at DESC LIMIT 20').all();

  res.json({
    totalActive: total.count,
    bySource,
    byLeadMagnet,
    recentSubscribers: recent,
  });
});

// Webhook endpoint for DM automation tools to send captured emails
app.post('/api/webhooks/email-capture', (req, res) => {
  const { email, source, lead_magnet, trigger_keyword } = req.body;

  if (!email || !email.includes('@')) {
    return res.status(400).json({ error: 'Valid email required' });
  }

  const db = getDb();

  try {
    db.prepare(
      'INSERT OR IGNORE INTO email_list (email, source, lead_magnet) VALUES (?, ?, ?)'
    ).run(email, source || 'dm_trigger', lead_magnet || trigger_keyword || 'unknown');

    // Update DM flow conversion count
    if (trigger_keyword) {
      db.prepare(
        'UPDATE dm_flows SET conversions = conversions + 1 WHERE trigger_keyword = ?'
      ).run(trigger_keyword);
    }

    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Cross-Platform ─────────────────────────────────
app.get('/api/cross-platform', (_req, res) => {
  res.json(getCrossPlatformLog());
});

app.get('/api/cross-platform/stats', (_req, res) => {
  res.json(getDistributionStats());
});

app.post('/api/cross-platform/adapt', async (req, res) => {
  try {
    const { scriptId, platform } = req.body;
    const adapted = await adaptForPlatform(scriptId, platform);
    res.json(adapted);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Schedule (unified content page) ───────────────
app.get('/api/schedule', (_req, res) => {
  res.json(getScheduledQueue());
});

app.post('/api/queue/:id/approve-and-post', async (req, res) => {
  try {
    const scriptId = parseInt(req.params.id);
    // Content must be rendered (designed) before posting
    const result = await autoPublishScript(scriptId);
    if (result.success) {
      res.json({ success: true });
    } else {
      res.status(500).json({ success: false, error: result.error });
    }
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post('/api/queue/:id/approve-and-schedule', (req, res) => {
  try {
    const slot = approveAndSchedule(parseInt(req.params.id));
    res.json({ success: true, ...slot });
  } catch (err: any) {
    res.status(400).json({ error: err.message });
  }
});

app.post('/api/schedule/:calendarId/remove', (req, res) => {
  try {
    removeFromSchedule(parseInt(req.params.calendarId));
    res.json({ success: true });
  } catch (err: any) {
    res.status(400).json({ error: err.message });
  }
});

app.post('/api/schedule/:calendarId/publish-now', async (req, res) => {
  try {
    const db = getDb();
    const entry = db.prepare('SELECT script_id FROM content_calendar WHERE id = ?')
      .get(parseInt(req.params.calendarId)) as any;
    if (!entry || !entry.script_id) {
      return res.status(404).json({ error: 'Calendar entry not found' });
    }
    const result = await publishContent(entry.script_id, { method: 'manual' });
    if (result.success) {
      db.prepare('UPDATE content_calendar SET status = ? WHERE id = ?')
        .run('published', parseInt(req.params.calendarId));
    }
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Rendering & Auto-Publish ──────────────────────
app.post('/api/render/:id', async (req, res) => {
  try {
    const result = await renderScript(parseInt(req.params.id));
    if (result) {
      res.json(result);
    } else {
      res.status(404).json({ error: 'Nothing to render for this script' });
    }
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/pipeline/auto-run', async (_req, res) => {
  try {
    const rendered = await renderDailyPackage();
    const published = await autoPublish(rendered);
    res.json({ rendered, published });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Originality / Fingerprint ──────────────────────
app.post('/api/fingerprint/audit', async (_req, res) => {
  try {
    const results = await auditQueue();
    res.json(results);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Creative Briefs ────────────────────────────────
app.get('/api/briefs', (_req, res) => {
  const db = getDb();
  const briefs = db.prepare('SELECT * FROM creative_briefs ORDER BY created_at DESC').all();
  res.json(briefs);
});

app.get('/api/briefs/active', (_req, res) => {
  const db = getDb();
  const brief = db.prepare(
    'SELECT * FROM creative_briefs WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1'
  ).get();
  res.json(brief || null);
});

app.post('/api/briefs', (req, res) => {
  const db = getDb();
  const { title, notes, competitor_links, content_angles, mood_themes, visual_style, target_emotions } = req.body;
  // Deactivate all existing briefs
  db.prepare('UPDATE creative_briefs SET is_active = 0').run();
  const id = db.prepare(`
    INSERT INTO creative_briefs (title, notes, competitor_links, content_angles, mood_themes, visual_style, target_emotions, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
  `).run(
    title, notes || null,
    competitor_links ? JSON.stringify(competitor_links) : null,
    content_angles ? JSON.stringify(content_angles) : null,
    mood_themes || null, visual_style || null, target_emotions || null
  ).lastInsertRowid;
  const brief = db.prepare('SELECT * FROM creative_briefs WHERE id = ?').get(id);
  res.json(brief);
});

app.put('/api/briefs/:id', (req, res) => {
  const db = getDb();
  const { title, notes, competitor_links, content_angles, mood_themes, visual_style, target_emotions } = req.body;
  db.prepare(`
    UPDATE creative_briefs
    SET title = ?, notes = ?, competitor_links = ?, content_angles = ?, mood_themes = ?, visual_style = ?, target_emotions = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
  `).run(
    title, notes || null,
    competitor_links ? JSON.stringify(competitor_links) : null,
    content_angles ? JSON.stringify(content_angles) : null,
    mood_themes || null, visual_style || null, target_emotions || null,
    parseInt(req.params.id)
  );
  const brief = db.prepare('SELECT * FROM creative_briefs WHERE id = ?').get(parseInt(req.params.id));
  res.json(brief);
});

app.post('/api/briefs/:id/activate', (req, res) => {
  const db = getDb();
  db.prepare('UPDATE creative_briefs SET is_active = 0').run();
  db.prepare('UPDATE creative_briefs SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
    .run(parseInt(req.params.id));
  const brief = db.prepare('SELECT * FROM creative_briefs WHERE id = ?').get(parseInt(req.params.id));
  res.json(brief);
});

app.delete('/api/briefs/:id', (req, res) => {
  const db = getDb();
  db.prepare('DELETE FROM creative_briefs WHERE id = ?').run(parseInt(req.params.id));
  res.json({ success: true });
});

// ─── AI Settings ───────────────────────────────────
app.get('/api/ai-settings', (_req, res) => {
  const db = getDb();
  const settings = db.prepare('SELECT * FROM ai_settings ORDER BY created_at DESC').all();
  res.json(settings);
});

app.get('/api/ai-settings/active', (_req, res) => {
  const db = getDb();
  const setting = db.prepare(
    'SELECT * FROM ai_settings WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1'
  ).get();
  res.json(setting || null);
});

app.get('/api/ai-settings/defaults', (_req, res) => {
  res.json({
    content_builder_system: DEFAULT_CONTENT_BUILDER_SYSTEM,
    carousel_design_instruction: DEFAULT_CAROUSEL_DESIGN_INSTRUCTION,
    reel_visual_instruction: DEFAULT_REEL_VISUAL_INSTRUCTION,
    temperature: 0.7,
  });
});

app.post('/api/ai-settings', (req, res) => {
  const db = getDb();
  const b = req.body;
  // Deactivate all existing
  db.prepare('UPDATE ai_settings SET is_active = 0').run();
  const id = db.prepare(`
    INSERT INTO ai_settings (name, content_builder_system, carousel_design_instruction, reel_visual_instruction,
      image_style_prefix, image_style_suffix, image_negative_prompt, temperature, is_active,
      default_image_model, default_video_model, enable_video_generation, video_motion_style,
      quality_gate_enabled, quality_gate_min_score,
      hook_visual_style, body_visual_style, cta_visual_style,
      camera_body, default_lens, default_lighting, default_color_profile)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    b.name,
    b.content_builder_system || null,
    b.carousel_design_instruction || null,
    b.reel_visual_instruction || null,
    b.image_style_prefix || null,
    b.image_style_suffix || null,
    b.image_negative_prompt || null,
    b.temperature ?? 0.7,
    b.default_image_model || 'flux-2-pro',
    b.default_video_model || 'kling-2.5-turbo-pro',
    b.enable_video_generation ?? true ? 1 : 0,
    b.video_motion_style || null,
    b.quality_gate_enabled ?? true ? 1 : 0,
    b.quality_gate_min_score ?? 7,
    b.hook_visual_style || null,
    b.body_visual_style || null,
    b.cta_visual_style || null,
    b.camera_body || null,
    b.default_lens || null,
    b.default_lighting || null,
    b.default_color_profile || null,
  ).lastInsertRowid;
  const setting = db.prepare('SELECT * FROM ai_settings WHERE id = ?').get(id);
  res.json(setting);
});

app.put('/api/ai-settings/:id', (req, res) => {
  const db = getDb();
  const b = req.body;
  db.prepare(`
    UPDATE ai_settings
    SET name = ?, content_builder_system = ?, carousel_design_instruction = ?, reel_visual_instruction = ?,
        image_style_prefix = ?, image_style_suffix = ?, image_negative_prompt = ?, temperature = ?,
        default_image_model = ?, default_video_model = ?, enable_video_generation = ?, video_motion_style = ?,
        quality_gate_enabled = ?, quality_gate_min_score = ?,
        hook_visual_style = ?, body_visual_style = ?, cta_visual_style = ?,
        camera_body = ?, default_lens = ?, default_lighting = ?, default_color_profile = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
  `).run(
    b.name,
    b.content_builder_system || null,
    b.carousel_design_instruction || null,
    b.reel_visual_instruction || null,
    b.image_style_prefix || null,
    b.image_style_suffix || null,
    b.image_negative_prompt || null,
    b.temperature ?? 0.7,
    b.default_image_model || 'flux-2-pro',
    b.default_video_model || 'kling-2.5-turbo-pro',
    b.enable_video_generation ?? true ? 1 : 0,
    b.video_motion_style || null,
    b.quality_gate_enabled ?? true ? 1 : 0,
    b.quality_gate_min_score ?? 7,
    b.hook_visual_style || null,
    b.body_visual_style || null,
    b.cta_visual_style || null,
    b.camera_body || null,
    b.default_lens || null,
    b.default_lighting || null,
    b.default_color_profile || null,
    parseInt(req.params.id),
  );
  const setting = db.prepare('SELECT * FROM ai_settings WHERE id = ?').get(parseInt(req.params.id));
  res.json(setting);
});

app.post('/api/ai-settings/:id/activate', (req, res) => {
  const db = getDb();
  db.prepare('UPDATE ai_settings SET is_active = 0').run();
  db.prepare('UPDATE ai_settings SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
    .run(parseInt(req.params.id));
  const setting = db.prepare('SELECT * FROM ai_settings WHERE id = ?').get(parseInt(req.params.id));
  res.json(setting);
});

app.delete('/api/ai-settings/:id', (req, res) => {
  const db = getDb();
  db.prepare('DELETE FROM ai_settings WHERE id = ?').run(parseInt(req.params.id));
  res.json({ success: true });
});

// ─── Content Options ────────────────────────────────
app.post('/api/options/generate', async (_req, res) => {
  try {
    const batch = await generateContentOptions();
    res.json(batch);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/options/latest', (_req, res) => {
  const batch = getLatestBatch();
  res.json(batch || {});
});

// ─── Build Doc Auto-Discovery ──────────────────────
app.get('/api/build-doc', (_req, res) => {
  const db = getDb();

  // 1. Discover database tables + columns
  const tableNames = db.prepare(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '\\_%' ESCAPE '\\' AND name NOT LIKE 'sqlite_%' ORDER BY name"
  ).all() as { name: string }[];
  const tables = tableNames.map((t) => {
    const columns = db.prepare(`PRAGMA table_info('${t.name}')`).all() as {
      name: string; type: string; notnull: number; dflt_value: string | null; pk: number;
    }[];
    const rowCount = (db.prepare(`SELECT COUNT(*) as count FROM "${t.name}"`).get() as any).count;
    return { name: t.name, columns, rowCount };
  });

  // 2. Discover API routes from Express
  const routes: { method: string; path: string }[] = [];
  try {
    const router = (app as any)._router || (app as any).router;
    if (router?.stack) {
      router.stack.forEach((layer: any) => {
        if (layer.route) {
          Object.keys(layer.route.methods).forEach((method: string) => {
            routes.push({ method: method.toUpperCase(), path: layer.route.path });
          });
        } else if (layer.name === 'router' && layer.handle?.stack) {
          layer.handle.stack.forEach((subLayer: any) => {
            if (subLayer.route) {
              Object.keys(subLayer.route.methods).forEach((method: string) => {
                routes.push({ method: method.toUpperCase(), path: subLayer.route.path });
              });
            }
          });
        }
      });
    }
  } catch {
    // Express 5 may not expose routes the same way — skip route discovery
  }

  // 3. Discover migrations
  const migrations = db.prepare('SELECT version, name, applied_at FROM _migrations ORDER BY version').all();

  // 4. Scan source file tree
  const srcRoot = path.resolve('src');
  function scanDir(dir: string, prefix = ''): { path: string; type: 'file' | 'dir' }[] {
    if (!existsSync(dir)) return [];
    const results: { path: string; type: 'file' | 'dir' }[] = [];
    try {
      const entries = readdirSync(dir);
      for (const entry of entries) {
        if (entry.startsWith('.') || entry === 'node_modules') continue;
        const fullPath = path.join(dir, entry);
        const relativePath = prefix ? `${prefix}/${entry}` : entry;
        const stat = statSync(fullPath);
        if (stat.isDirectory()) {
          results.push({ path: relativePath, type: 'dir' });
          results.push(...scanDir(fullPath, relativePath));
        } else {
          results.push({ path: relativePath, type: 'file' });
        }
      }
    } catch {}
    return results;
  }
  const sourceFiles = scanDir(srcRoot);

  // 5. Categorized source structure
  const categorize = (prefix: string) =>
    sourceFiles.filter(f => f.path.startsWith(prefix) && f.type === 'file').map(f => f.path);
  const sourceTree = {
    config: categorize('config/'),
    database: categorize('database/'),
    integrations: categorize('integrations/'),
    orchestrator: categorize('orchestrator/'),
    rendering: categorize('rendering/'),
    utils: categorize('utils/'),
    dashboard: categorize('dashboard/'),
    modules: (() => {
      const modDirs = sourceFiles
        .filter(f => f.path.startsWith('modules/') && f.type === 'dir' && f.path.split('/').length === 2)
        .map(f => f.path);
      return modDirs.map(dir => ({
        dir: dir.replace('modules/', ''),
        files: sourceFiles
          .filter(f => f.path.startsWith(dir + '/') && f.type === 'file')
          .map(f => f.path.replace(dir + '/', '')),
      }));
    })(),
    entryPoints: sourceFiles.filter(f => f.type === 'file' && !f.path.includes('/')).map(f => f.path),
  };

  // 6. Active config (redacted)
  const configSummary = {
    niche: CONFIG.app.niche,
    dashboardPort: CONFIG.app.dashboardPort,
    model: CONFIG.ai.model,
    carouselSlideCount: CONFIG.content.carouselSlideCount,
    hasInstagramToken: !!CONFIG.instagram.accessToken,
    hasReplicateToken: !!CONFIG.replicate.apiToken,
    hasCloudinary: !!CONFIG.cloudinary.cloudName,
    hasOpenAI: !!(CONFIG as any).openai?.apiKey,
    hasBuffer: !!(CONFIG as any).buffer?.accessToken,
  };

  // 7. Read actual source code of all files
  const sourceContents: Record<string, string> = {};
  for (const file of sourceFiles) {
    if (file.type !== 'file') continue;
    try {
      const fullPath = path.join(srcRoot, file.path);
      sourceContents[file.path] = readFileSync(fullPath, 'utf-8');
    } catch {}
  }

  res.json({
    generatedAt: new Date().toISOString(),
    tables,
    routes,
    migrations,
    sourceTree,
    configSummary,
    sourceContents,
  });
});

// ─── Download Rendered Assets ─────────────────────
app.get('/api/download/:scriptId', (req, res) => {
  const db = getDb();
  const scriptId = parseInt(req.params.scriptId);
  const script = db.prepare(`
    SELECT cs.id, ci.content_type, ci.title
    FROM content_scripts cs
    JOIN content_ideas ci ON cs.idea_id = ci.id
    WHERE cs.id = ?
  `).get(scriptId) as any;

  if (!script) return res.status(404).json({ error: 'Script not found' });

  const asset = db.prepare(
    'SELECT local_paths, content_type FROM rendered_assets WHERE script_id = ? ORDER BY rendered_at DESC LIMIT 1'
  ).get(scriptId) as any;

  if (!asset) return res.status(404).json({ error: 'No rendered assets found' });

  const localPaths: string[] = JSON.parse(asset.local_paths || '[]');
  if (localPaths.length === 0) return res.status(404).json({ error: 'No files to download' });

  // Sanitize title for filename
  const safeTitle = (script.title || `content-${scriptId}`)
    .replace(/[^a-zA-Z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .toLowerCase()
    .slice(0, 60);

  if (asset.content_type === 'reel') {
    // Single MP4 file
    const reelPath = localPaths.find((p: string) => p.endsWith('.mp4')) || localPaths[0];
    const filename = `${safeTitle}.mp4`;
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Type', 'video/mp4');
    res.sendFile(path.resolve(reelPath));
  } else {
    // For carousels/stories with multiple images, send as zip
    const filename = `${safeTitle}-slides.zip`;
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Type', 'application/zip');
    const archive = archiver('zip', { zlib: { level: 5 } });
    archive.pipe(res);
    localPaths.forEach((filePath: string, i: number) => {
      const ext = path.extname(filePath);
      archive.file(path.resolve(filePath), { name: `slide-${i + 1}${ext}` });
    });
    archive.finalize();
  }
});

// ─── API Costs ─────────────────────────────────────
app.get('/api/costs/summary', (req, res) => {
  const db = getDb();
  const period = (req.query.period as string) || 'all';

  let dateFilter = '';
  if (period === 'today') dateFilter = "AND created_at >= date('now')";
  else if (period === '7d') dateFilter = "AND created_at >= date('now', '-7 days')";
  else if (period === '30d') dateFilter = "AND created_at >= date('now', '-30 days')";

  const totalRow = db.prepare(`SELECT COALESCE(SUM(estimated_cost), 0) as total, COUNT(*) as calls FROM api_costs WHERE 1=1 ${dateFilter}`).get() as any;

  const byProvider = db.prepare(`SELECT provider, COALESCE(SUM(estimated_cost), 0) as total, COUNT(*) as calls FROM api_costs WHERE 1=1 ${dateFilter} GROUP BY provider ORDER BY total DESC`).all();

  const byCategory = db.prepare(`SELECT category, COALESCE(SUM(estimated_cost), 0) as total, COUNT(*) as calls FROM api_costs WHERE 1=1 ${dateFilter} GROUP BY category ORDER BY total DESC`).all();

  const periods = {
    today: (db.prepare("SELECT COALESCE(SUM(estimated_cost), 0) as total FROM api_costs WHERE created_at >= date('now')").get() as any).total,
    week: (db.prepare("SELECT COALESCE(SUM(estimated_cost), 0) as total FROM api_costs WHERE created_at >= date('now', '-7 days')").get() as any).total,
    month: (db.prepare("SELECT COALESCE(SUM(estimated_cost), 0) as total FROM api_costs WHERE created_at >= date('now', '-30 days')").get() as any).total,
    all: (db.prepare("SELECT COALESCE(SUM(estimated_cost), 0) as total FROM api_costs").get() as any).total,
  };

  res.json({ total: totalRow.total, calls: totalRow.calls, byProvider, byCategory, periods });
});

app.get('/api/costs/breakdown', (req, res) => {
  const db = getDb();
  const page = parseInt(req.query.page as string) || 1;
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
  const offset = (page - 1) * limit;
  const provider = req.query.provider as string;
  const category = req.query.category as string;

  let where = 'WHERE 1=1';
  const params: any[] = [];
  if (provider) { where += ' AND provider = ?'; params.push(provider); }
  if (category) { where += ' AND category = ?'; params.push(category); }

  const totalRow = db.prepare(`SELECT COUNT(*) as count FROM api_costs ${where}`).get(...params) as any;
  const rows = db.prepare(`SELECT * FROM api_costs ${where} ORDER BY created_at DESC LIMIT ? OFFSET ?`).all(...params, limit, offset);

  res.json({ items: rows, total: totalRow.count, page, limit });
});

app.get('/api/costs/by-project', (req, res) => {
  const db = getDb();

  // Use project_label if set, otherwise fall back to idea_id
  const rows = db.prepare(`
    SELECT
      COALESCE(project_label, CAST(idea_id AS TEXT), 'unassigned') as project_key,
      COUNT(*) as calls,
      ROUND(COALESCE(SUM(estimated_cost), 0), 4) as total_cost,
      ROUND(COALESCE(SUM(CASE WHEN category = 'image' THEN estimated_cost ELSE 0 END), 0), 4) as image_cost,
      ROUND(COALESCE(SUM(CASE WHEN category = 'video' THEN estimated_cost ELSE 0 END), 0), 4) as video_cost,
      ROUND(COALESCE(SUM(CASE WHEN category = 'text' THEN estimated_cost ELSE 0 END), 0), 4) as text_cost,
      ROUND(COALESCE(SUM(CASE WHEN category = 'tts' THEN estimated_cost ELSE 0 END), 0), 4) as tts_cost,
      ROUND(COALESCE(SUM(CASE WHEN category = 'vision' THEN estimated_cost ELSE 0 END), 0), 4) as vision_cost,
      MIN(created_at) as first_cost,
      MAX(created_at) as last_cost
    FROM api_costs
    GROUP BY project_key
    ORDER BY total_cost DESC
  `).all() as any[];

  const projects = rows.map((row: any) => {
    let title = row.project_key;
    let contentType = 'unknown';

    // Try to match project_key to content_ideas
    const ideaId = parseInt(row.project_key);
    if (!isNaN(ideaId)) {
      const idea = db.prepare('SELECT title, content_type FROM content_ideas WHERE id = ?').get(ideaId) as any;
      if (idea) {
        title = idea.title;
        contentType = idea.content_type;
      }
    }

    // Infer type from label pattern
    if (row.project_key === 'reel-batch') {
      title = 'Reel Rendering (images, video, TTS)';
      contentType = 'reel';
    } else if (row.project_key === 'carousel-batch') {
      title = 'Carousel Rendering (background images)';
      contentType = 'carousel';
    } else if (row.project_key === 'quality-gate') {
      title = 'Quality Gate (vision checks)';
      contentType = 'mixed';
    } else if (row.project_key === 'idea-generation') {
      title = 'Content Idea Generation';
      contentType = 'mixed';
    } else if (row.project_key.startsWith('carousel-')) {
      contentType = 'carousel';
      if (title === row.project_key) title = `Carousel #${row.project_key.replace('carousel-', '')}`;
    } else if (row.project_key.startsWith('reel-')) {
      contentType = 'reel';
      if (title === row.project_key) title = `Reel #${row.project_key.replace('reel-', '')}`;
    } else if (row.project_key === 'unassigned') {
      title = 'Shared / Unassigned';
      contentType = 'mixed';
    }

    return {
      projectKey: row.project_key,
      title,
      contentType,
      calls: row.calls,
      totalCost: row.total_cost,
      breakdown: {
        image: row.image_cost,
        video: row.video_cost,
        text: row.text_cost,
        tts: row.tts_cost,
        vision: row.vision_cost,
      },
      firstCost: row.first_cost,
      lastCost: row.last_cost,
    };
  });

  res.json(projects);
});

app.get('/api/costs/balances', (_req, res) => {
  res.json({
    anthropic: { status: 'check_dashboard', url: 'https://console.anthropic.com/settings/billing' },
    openai: { status: 'check_dashboard', url: 'https://platform.openai.com/usage' },
    replicate: { status: 'check_dashboard', url: 'https://replicate.com/account/billing' },
    fal: { status: 'check_dashboard', url: 'https://fal.ai/dashboard/billing' },
    ideogram: { status: 'check_dashboard', url: 'https://ideogram.ai/manage' },
  });
});

// ─── Serve Rendered Assets ─────────────────────────
app.use('/assets', express.static(path.resolve('data/assets')));

// ─── Serve Dashboard Static Files ───────────────────
const dashboardPath = path.resolve('dist/dashboard');
app.use(express.static(dashboardPath));
app.get('/{*splat}', (req, res) => {
  if (!req.path.startsWith('/api')) {
    res.sendFile(path.join(dashboardPath, 'index.html'));
  }
});

// ─── Start server ───────────────────────────────────
export function startDashboard() {
  app.listen(CONFIG.app.dashboardPort, () => {
    console.log(`Dashboard API running on http://localhost:${CONFIG.app.dashboardPort}`);

    // Check Instagram token health on startup (non-blocking)
    if (CONFIG.instagram.accessToken) {
      checkAndRefreshToken()
        .then(result => {
          if (result.daysLeft >= 0) {
            if (result.daysLeft < 7) {
              console.warn(`WARNING: Instagram token expires in ${result.daysLeft} days!${result.refreshed ? ' (auto-refreshed)' : ' Run refresh-token to renew.'}`);
            } else {
              console.log(`Instagram token valid for ${result.daysLeft} more days.`);
            }
          }
        })
        .catch(() => {
          console.warn('Could not verify Instagram token health.');
        });
    }
  });
}

// Allow direct execution
if (process.argv[1]?.includes('server')) {
  startDashboard();
}
