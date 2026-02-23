import express from 'express';
import cors from 'cors';
import path from 'path';
import { CONFIG } from './config/env.js';
import { getDb, getRows } from './database/db.js';
import { getState, runDailyPipeline } from './orchestrator/master.js';
import { approveContent, rejectContent, publishContent, getPendingApproval, getReadyToPublish, approveAndSchedule } from './orchestrator/approval-gate.js';
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

runMigrations();

const app = express();
app.use(cors());
app.use(express.json());

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
    WHERE ci.status IN ('scripted', 'approved')
    ORDER BY cs.created_at DESC
    LIMIT 50
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
    approveContent(parseInt(req.params.id));
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

app.get('/api/email-list', (_req, res) => {
  res.json(getEmailListStats());
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
    // Approve first
    approveContent(scriptId);
    // Publish directly to Instagram
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
  });
}

// Allow direct execution
if (process.argv[1]?.includes('server')) {
  startDashboard();
}
