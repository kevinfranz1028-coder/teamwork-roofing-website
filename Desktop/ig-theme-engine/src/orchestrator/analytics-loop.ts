import axios from 'axios';
import { CONFIG } from '../config/env.js';
import { getDb } from '../database/db.js';

// Fetch insights from Instagram Graph API for a specific media item
async function fetchMediaInsights(mediaId: string): Promise<any> {
  const url = `https://graph.facebook.com/v19.0/${mediaId}/insights`;
  const metrics = 'impressions,reach,saved,shares,total_interactions,video_views';

  try {
    const response = await axios.get(url, {
      params: {
        metric: metrics,
        access_token: CONFIG.instagram.accessToken,
      }
    });
    return response.data.data;
  } catch (error: any) {
    console.error(`Failed to fetch insights for ${mediaId}:`, error.message);
    return null;
  }
}

// Update all published content with latest metrics
export async function refreshAnalytics(): Promise<void> {
  const db = getDb();
  const published = db.prepare(`
    SELECT * FROM published_content
    WHERE platform = 'instagram'
    AND platform_post_id IS NOT NULL
    AND published_at > datetime('now', '-30 days')
  `).all() as any[];

  for (const post of published) {
    const insights = await fetchMediaInsights(post.platform_post_id);
    if (!insights) continue;

    const metrics: Record<string, number> = {};
    for (const metric of insights) {
      metrics[metric.name] = metric.values?.[0]?.value || 0;
    }

    const reach = metrics.reach || 1;
    const sends = metrics.shares || 0;
    const likes = metrics.total_interactions || 0;

    db.prepare(`
      UPDATE published_content SET
        impressions = ?,
        reach = ?,
        saves = ?,
        sends = ?,
        sends_per_reach = ?,
        likes_per_reach = ?,
        engagement_rate = ?,
        last_analytics_update = CURRENT_TIMESTAMP
      WHERE id = ?
    `).run(
      metrics.impressions || 0,
      reach,
      metrics.saved || 0,
      sends,
      sends / reach,
      likes / reach,
      (sends + (metrics.saved || 0) + likes) / reach,
      post.id
    );
  }
}

// Generate weekly scorecard
export function generateWeeklyScorecard(): any {
  const db = getDb();

  const weekData = db.prepare(`
    SELECT
      COUNT(*) as posts_published,
      SUM(reach) as total_reach,
      SUM(sends) as total_sends,
      AVG(sends_per_reach) as avg_sends_per_reach,
      SUM(saves) as total_saves,
      AVG(engagement_rate) as avg_engagement_rate
    FROM published_content
    WHERE published_at > datetime('now', '-7 days')
  `).get() as any;

  const revenue = db.prepare(`
    SELECT SUM(amount) as total
    FROM revenue
    WHERE date > date('now', '-7 days')
  `).get() as any;

  // Traffic light scoring
  const status =
    (weekData.avg_sends_per_reach || 0) > 0.03 ? 'green' :
    (weekData.avg_sends_per_reach || 0) > 0.01 ? 'yellow' : 'red';

  const scorecard = {
    postsPublished: weekData.posts_published,
    totalReach: weekData.total_reach,
    totalSends: weekData.total_sends,
    avgSendsPerReach: weekData.avg_sends_per_reach,
    totalSaves: weekData.total_saves,
    avgEngagementRate: weekData.avg_engagement_rate,
    revenue: revenue?.total || 0,
    status,
    kpis: {
      sendsPerReach: { value: weekData.avg_sends_per_reach, green: 0.03, yellow: 0.01 },
      engagementRate: { value: weekData.avg_engagement_rate, green: 0.05, yellow: 0.02 },
      postsPerWeek: { value: weekData.posts_published, green: 7, yellow: 4 },
      revenue: { value: revenue?.total || 0, green: 100, yellow: 25 },
    }
  };

  // Insert scorecard into database
  db.prepare(`
    INSERT INTO weekly_scorecard (week_start, posts_published, total_reach, total_sends,
      avg_sends_per_reach, total_saves, revenue_total, scorecard_json, status)
    VALUES (date('now', '-7 days'), ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    scorecard.postsPublished,
    scorecard.totalReach,
    scorecard.totalSends,
    scorecard.avgSendsPerReach,
    scorecard.totalSaves,
    scorecard.revenue,
    JSON.stringify(scorecard),
    scorecard.status
  );

  return scorecard;
}
