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
