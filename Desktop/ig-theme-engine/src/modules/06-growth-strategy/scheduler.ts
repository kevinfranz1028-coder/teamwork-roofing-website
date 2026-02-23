import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getDb, insertRow } from '../../database/db.js';
import { CONFIG } from '../../config/env.js';
import { GROWTH_STRATEGY_SYSTEM, contentCalendarPrompt } from './prompts.js';
import { format, addDays, startOfWeek } from 'date-fns';

interface CalendarDay {
  day: string;
  postType: string;
  pillar: string;
  ideaTitle: string;
  postingTime: string;
  storyCount: number;
  storyTheme: string;
  engagementFocus: string;
}

interface ContentCalendar {
  weeks: Array<{
    weekNumber: number;
    theme: string;
    days: CalendarDay[];
  }>;
  pillarRotation: string;
  restDayStrategy: string;
}

export async function generateContentCalendar(
  contentPillars: string[],
  postsPerWeek = 5
): Promise<ContentCalendar> {
  const niche = CONFIG.app.niche;

  const calendar = await askClaudeJSON<ContentCalendar>({
    systemPrompt: GROWTH_STRATEGY_SYSTEM,
    userPrompt: contentCalendarPrompt(niche, contentPillars, postsPerWeek),
    maxTokens: 6000,
  });

  // Store calendar entries in database
  const weekStart = startOfWeek(new Date(), { weekStartsOn: 1 });
  const dayMap: Record<string, number> = {
    Monday: 0, Tuesday: 1, Wednesday: 2, Thursday: 3,
    Friday: 4, Saturday: 5, Sunday: 6,
  };

  for (const week of calendar.weeks) {
    for (const day of week.days) {
      const dayOffset = (week.weekNumber - 1) * 7 + (dayMap[day.day] || 0);
      const date = format(addDays(weekStart, dayOffset), 'yyyy-MM-dd');

      if (day.postType !== 'rest') {
        insertRow('content_calendar', {
          scheduled_date: date,
          scheduled_time: day.postingTime,
          content_type: day.postType,
          content_pillar: day.pillar,
          status: 'planned',
          notes: JSON.stringify({
            ideaTitle: day.ideaTitle,
            storyCount: day.storyCount,
            storyTheme: day.storyTheme,
            engagementFocus: day.engagementFocus,
            weekTheme: week.theme,
          }),
        });
      }
    }
  }

  return calendar;
}

export function getUpcomingCalendar(days = 14): any[] {
  const db = getDb();
  return db.prepare(`
    SELECT * FROM content_calendar
    WHERE scheduled_date >= date('now')
    AND scheduled_date <= date('now', '+${days} days')
    ORDER BY scheduled_date, scheduled_time
  `).all();
}

export function getTodaysSchedule(): any[] {
  const db = getDb();
  return db.prepare(`
    SELECT * FROM content_calendar
    WHERE scheduled_date = date('now')
    ORDER BY scheduled_time
  `).all();
}

// ─── Schedule Management Functions ──────────────────

interface ScheduledSlot {
  calendarId: number;
  scheduledDate: string;
  scheduledTime: string;
  contentType: string;
}

/**
 * Find the next open time slot and schedule a script into it.
 * Prefers days that don't already have the same content_type (variety).
 * 30-day lookahead max.
 */
export function scheduleNextSlot(scriptId: number, contentType: string): ScheduledSlot {
  const db = getDb();
  const timeSlots = CONFIG.app.postingSchedule; // e.g. ['9:00', '12:00', '18:00']

  // Get all occupied future slots
  const occupied = db.prepare(`
    SELECT scheduled_date, scheduled_time, content_type
    FROM content_calendar
    WHERE scheduled_date >= date('now')
    AND status IN ('planned', 'approved', 'generated')
  `).all() as { scheduled_date: string; scheduled_time: string; content_type: string }[];

  const occupiedSet = new Set(occupied.map(o => `${o.scheduled_date}|${o.scheduled_time}`));
  const typesPerDay = new Map<string, Set<string>>();
  for (const o of occupied) {
    if (!typesPerDay.has(o.scheduled_date)) typesPerDay.set(o.scheduled_date, new Set());
    typesPerDay.get(o.scheduled_date)!.add(o.content_type);
  }

  // Iterate days starting today, 30-day lookahead
  const today = new Date();
  let bestSlot: { date: string; time: string; hasTypeConflict: boolean } | null = null;

  for (let dayOffset = 0; dayOffset < 30; dayOffset++) {
    const d = addDays(today, dayOffset);
    const dateStr = format(d, 'yyyy-MM-dd');
    const dayTypes = typesPerDay.get(dateStr);

    for (const time of timeSlots) {
      const key = `${dateStr}|${time}`;
      if (occupiedSet.has(key)) continue;

      const hasTypeConflict = dayTypes ? dayTypes.has(contentType) : false;

      // If we find a slot without type conflict, use it immediately
      if (!hasTypeConflict) {
        bestSlot = { date: dateStr, time, hasTypeConflict: false };
        break;
      }

      // Otherwise, remember the first available slot as fallback
      if (!bestSlot) {
        bestSlot = { date: dateStr, time, hasTypeConflict: true };
      }
    }

    if (bestSlot && !bestSlot.hasTypeConflict) break;
  }

  if (!bestSlot) {
    throw new Error('No available time slots in the next 30 days');
  }

  const calendarId = db.prepare(`
    INSERT INTO content_calendar (scheduled_date, scheduled_time, content_type, script_id, status)
    VALUES (?, ?, ?, ?, 'approved')
  `).run(bestSlot.date, bestSlot.time, contentType, scriptId).lastInsertRowid as number;

  return {
    calendarId,
    scheduledDate: bestSlot.date,
    scheduledTime: bestSlot.time,
    contentType,
  };
}

/**
 * Get all future scheduled items with full details for the dashboard.
 */
export function getScheduledQueue(): any[] {
  const db = getDb();
  return db.prepare(`
    SELECT
      cc.id as calendarId,
      cc.scheduled_date as scheduledDate,
      cc.scheduled_time as scheduledTime,
      cc.content_type as contentType,
      cc.status,
      cc.script_id as scriptId,
      cs.caption,
      cs.hashtags,
      cs.script_json as scriptJson,
      cs.dm_trigger_keyword as dmTrigger,
      ci.id as ideaId,
      ci.title,
      ci.hook,
      ci.send_trigger as sendTrigger,
      ci.send_probability as sendProbability,
      ra.local_paths as localPaths,
      ra.public_urls as publicUrls
    FROM content_calendar cc
    LEFT JOIN content_scripts cs ON cc.script_id = cs.id
    LEFT JOIN content_ideas ci ON cs.idea_id = ci.id
    LEFT JOIN rendered_assets ra ON ra.script_id = cs.id
    WHERE cc.scheduled_date >= date('now')
    AND cc.status IN ('approved', 'planned', 'generated')
    ORDER BY cc.scheduled_date ASC, cc.scheduled_time ASC
  `).all().map((row: any) => ({
    ...row,
    localPaths: row.localPaths ? JSON.parse(row.localPaths) : [],
    publicUrls: row.publicUrls ? JSON.parse(row.publicUrls) : [],
    hashtags: row.hashtags ? JSON.parse(row.hashtags) : [],
  }));
}

/**
 * Remove a scheduled item — set status to 'skipped' and revert idea to 'scripted'.
 */
export function removeFromSchedule(calendarId: number): void {
  const db = getDb();
  const entry = db.prepare('SELECT script_id FROM content_calendar WHERE id = ?').get(calendarId) as any;
  if (!entry) throw new Error(`Calendar entry ${calendarId} not found`);

  db.prepare('UPDATE content_calendar SET status = ? WHERE id = ?').run('skipped', calendarId);

  if (entry.script_id) {
    const script = db.prepare('SELECT idea_id FROM content_scripts WHERE id = ?').get(entry.script_id) as any;
    if (script) {
      db.prepare('UPDATE content_ideas SET status = ? WHERE id = ?').run('scripted', script.idea_id);
    }
  }
}
