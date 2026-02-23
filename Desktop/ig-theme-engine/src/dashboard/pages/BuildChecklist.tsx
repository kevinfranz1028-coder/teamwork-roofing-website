import React from 'react';

interface ChecklistItem {
  label: string;
  status: 'done' | 'partial' | 'missing';
  notes?: string;
}

interface ChecklistSection {
  title: string;
  completion: number;
  items: ChecklistItem[];
}

const checklist: ChecklistSection[] = [
  {
    title: 'Phase 1: Project Scaffold & Core Infrastructure',
    completion: 100,
    items: [
      { label: 'Initialize project (npm, TypeScript, tsconfig)', status: 'done' },
      { label: 'Install all dependencies', status: 'done' },
      { label: 'Create full directory structure (src/, data/)', status: 'done' },
      { label: '.env template with all config vars', status: 'done' },
      { label: 'src/config/env.ts — Environment config loader', status: 'done' },
      { label: 'src/config/niche.ts — Active niche configuration', status: 'done' },
      { label: 'src/config/brand.ts — Brand system (colors, fonts, voice)', status: 'done' },
      { label: 'package.json scripts (dev, start, niches, daily, etc.)', status: 'done' },
    ],
  },
  {
    title: 'Phase 2: Database Layer',
    completion: 100,
    items: [
      { label: 'src/database/schema.ts — All 11 tables defined', status: 'done' },
      { label: 'src/database/db.ts — Connection, insertRow, getRows helpers', status: 'done' },
      { label: 'src/database/migrations.ts — Schema migrations', status: 'done' },
      { label: 'Database tested and initializing correctly', status: 'done' },
    ],
  },
  {
    title: 'Phase 3: Claude AI Client',
    completion: 100,
    items: [
      { label: 'src/integrations/claude-client.ts — askClaude()', status: 'done' },
      { label: 'askClaudeJSON() with structured output', status: 'done' },
      { label: 'JSON repair for truncated responses', status: 'done' },
      { label: 'Cost estimation per request', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 0 — Originality Architecture',
    completion: 100,
    items: [
      { label: 'src/modules/00-originality/originality-engine.ts', status: 'done' },
      { label: 'src/modules/00-originality/fingerprint-check.ts', status: 'done', notes: 'AI-powered similarity detection + queue audit' },
    ],
  },
  {
    title: 'Phase 4: Module 1 — Niche Selector',
    completion: 100,
    items: [
      { label: 'src/modules/01-niche-selector/niche-analyzer.ts', status: 'done' },
      { label: 'src/modules/01-niche-selector/prompts.ts', status: 'done' },
      { label: 'Analyzes 20 niches with composite scoring', status: 'done' },
      { label: 'Stores results in database + select niche', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 2 — Viral Content Blueprint',
    completion: 100,
    items: [
      { label: 'src/modules/02-viral-blueprint/content-ideator.ts', status: 'done' },
      { label: 'src/modules/02-viral-blueprint/prompts.ts', status: 'done' },
      { label: '15 viral ideas (8 carousel + 7 reel) generation', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 3 — Faceless Content Builder',
    completion: 100,
    items: [
      { label: 'src/modules/03-content-builder/carousel-builder.ts', status: 'done' },
      { label: 'src/modules/03-content-builder/reel-builder.ts', status: 'done' },
      { label: 'src/modules/03-content-builder/story-builder.ts', status: 'done' },
      { label: 'src/modules/03-content-builder/prompts.ts', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 4 — Daily Output Engine',
    completion: 100,
    items: [
      { label: 'src/modules/04-daily-output/daily-engine.ts', status: 'done' },
      { label: 'src/modules/04-daily-output/trend-scanner.ts', status: 'done', notes: 'Seasonal/cultural context-aware trend detection' },
      { label: 'src/modules/04-daily-output/prompts.ts', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 5 — Design System',
    completion: 100,
    items: [
      { label: 'src/modules/05-design-system/design-manager.ts', status: 'done', notes: 'AI-generated brand design system' },
      { label: 'src/modules/05-design-system/template-generator.ts', status: 'done', notes: 'Carousel template generation' },
      { label: 'src/modules/05-design-system/prompts.ts', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 6 — Growth & Posting Strategy',
    completion: 100,
    items: [
      { label: 'src/modules/06-growth-strategy/scheduler.ts', status: 'done', notes: '4-week content calendar generation' },
      { label: 'src/modules/06-growth-strategy/engagement-engine.ts', status: 'done', notes: 'Engagement protocol + smart comment replies' },
      { label: 'src/modules/06-growth-strategy/prompts.ts', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 7 — Monetization',
    completion: 100,
    items: [
      { label: 'src/modules/07-monetization/revenue-tracker.ts', status: 'done', notes: 'AI strategy + DB revenue overview' },
      { label: 'src/modules/07-monetization/prompts.ts', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 8 — Scaling Roadmap',
    completion: 100,
    items: [
      { label: 'src/modules/08-scaling/roadmap-engine.ts', status: 'done', notes: 'Phase detection + growth levers' },
      { label: 'src/modules/08-scaling/prompts.ts', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 9 — DM Automation & Funnel',
    completion: 100,
    items: [
      { label: 'src/modules/09-dm-automation/dm-flows.ts', status: 'done', notes: 'DM flow builder + lead magnets + email list' },
      { label: 'src/modules/09-dm-automation/prompts.ts', status: 'done' },
      { label: 'ManyChat integration', status: 'partial', notes: 'DM flows designed for ManyChat — requires ManyChat account to connect' },
      { label: 'Email list management', status: 'done' },
    ],
  },
  {
    title: 'Phase 4: Module 10 — Cross-Platform Distribution',
    completion: 100,
    items: [
      { label: 'src/modules/10-cross-platform/distributor.ts', status: 'done', notes: 'TikTok, YouTube Shorts, Pinterest, Twitter adaptation' },
      { label: 'src/modules/10-cross-platform/prompts.ts', status: 'done' },
    ],
  },
  {
    title: 'Phase 5: Master Orchestrator',
    completion: 100,
    items: [
      { label: 'src/orchestrator/master.ts — Daily pipeline + cron', status: 'done' },
      { label: 'src/orchestrator/approval-gate.ts — Approve → Publish pipeline', status: 'done', notes: 'Supports instagram_direct, buffer, and manual publishing' },
      { label: 'Pipeline state management (idle → generating → approval → publishing)', status: 'done' },
    ],
  },
  {
    title: 'Phase 6: Analytics Loop',
    completion: 100,
    items: [
      { label: 'src/orchestrator/analytics-loop.ts — refreshAnalytics()', status: 'done' },
      { label: 'Instagram Graph API insights fetching', status: 'done', notes: 'Requires valid IG credentials to function' },
      { label: 'generateWeeklyScorecard() with traffic-light KPIs', status: 'done' },
      { label: 'Performance feedback into content generation', status: 'done' },
    ],
  },
  {
    title: 'Phase 7: CLI Interface',
    completion: 100,
    items: [
      { label: 'niches / select-niche commands', status: 'done' },
      { label: 'originality command', status: 'done' },
      { label: 'design-system command', status: 'done' },
      { label: 'daily / start / status commands', status: 'done' },
      { label: 'trends command', status: 'done' },
      { label: 'queue / approve / reject commands', status: 'done' },
      { label: 'publish command (--method, --images, --video)', status: 'done' },
      { label: 'fingerprint (originality audit) command', status: 'done' },
      { label: 'analytics / scorecard commands', status: 'done' },
      { label: 'blueprint / calendar / engagement commands', status: 'done' },
      { label: 'monetize / roadmap commands', status: 'done' },
      { label: 'dm-flow / lead-magnets commands', status: 'done' },
      { label: 'cross-platform command', status: 'done' },
    ],
  },
  {
    title: 'Phase 8: Dashboard (React Web UI)',
    completion: 90,
    items: [
      { label: 'Pipeline Status page', status: 'done' },
      { label: 'Content Queue page (approve/reject with preview)', status: 'done' },
      { label: 'Analytics Overview page', status: 'done' },
      { label: 'Weekly Scorecard page (traffic-light KPIs)', status: 'done' },
      { label: 'Revenue Tracker page (log + chart)', status: 'done' },
      { label: 'Build Checklist page', status: 'done' },
      { label: 'Dashboard API routes for all modules', status: 'done', notes: 'Publish, calendar, DM flows, cross-platform, trends, design, engagement, roadmap' },
    ],
  },
  {
    title: 'Integrations',
    completion: 100,
    items: [
      { label: 'src/integrations/claude-client.ts — Claude API', status: 'done' },
      { label: 'src/integrations/instagram-api.ts — Instagram Graph API posting', status: 'done', notes: 'Full IG posting: images, carousels, reels + insights' },
      { label: 'src/integrations/buffer-api.ts — Buffer scheduling/publishing', status: 'done', notes: 'Queue management, scheduled posting, analytics' },
      { label: 'src/integrations/canva-api.ts — Canva design generation', status: 'done', notes: 'Optional Canva Connect API + local design spec fallback' },
    ],
  },
  {
    title: 'Utilities',
    completion: 100,
    items: [
      { label: 'src/utils/logger.ts — Centralized logging (console + file)', status: 'done' },
      { label: 'src/utils/image-utils.ts — Image processing (sharp)', status: 'done', notes: 'Resize, backgrounds, text overlay, optimize' },
      { label: 'src/utils/text-utils.ts — Text helpers', status: 'done', notes: 'Captions, hashtags, slugify, health check' },
    ],
  },
];

const statusIcon = (status: string) => {
  switch (status) {
    case 'done': return <span className="text-green-400 font-bold">DONE</span>;
    case 'partial': return <span className="text-yellow-400 font-bold">PARTIAL</span>;
    case 'missing': return <span className="text-red-400 font-bold">MISSING</span>;
    default: return null;
  }
};

const completionColor = (pct: number) => {
  if (pct >= 80) return 'bg-green-500';
  if (pct >= 40) return 'bg-yellow-500';
  return 'bg-red-500';
};

export default function BuildChecklist() {
  const totalItems = checklist.reduce((sum, s) => sum + s.items.length, 0);
  const doneItems = checklist.reduce((sum, s) => sum + s.items.filter(i => i.status === 'done').length, 0);
  const partialItems = checklist.reduce((sum, s) => sum + s.items.filter(i => i.status === 'partial').length, 0);
  const missingItems = checklist.reduce((sum, s) => sum + s.items.filter(i => i.status === 'missing').length, 0);
  const overallPct = Math.round((doneItems / totalItems) * 100);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Build Checklist</h2>
      <p className="text-sm text-gray-400">Tracking progress against the original ig-engine-build-guide.md</p>

      {/* Overall Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <p className="text-xs text-gray-500 uppercase">Overall</p>
          <p className="text-3xl font-bold mt-1">{overallPct}%</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <p className="text-xs text-gray-500 uppercase">Total Items</p>
          <p className="text-3xl font-bold mt-1">{totalItems}</p>
        </div>
        <div className="bg-gray-900 border border-green-800 rounded-xl p-4 text-center">
          <p className="text-xs text-green-500 uppercase">Done</p>
          <p className="text-3xl font-bold mt-1 text-green-400">{doneItems}</p>
        </div>
        <div className="bg-gray-900 border border-yellow-800 rounded-xl p-4 text-center">
          <p className="text-xs text-yellow-500 uppercase">Partial</p>
          <p className="text-3xl font-bold mt-1 text-yellow-400">{partialItems}</p>
        </div>
        <div className="bg-gray-900 border border-red-800 rounded-xl p-4 text-center">
          <p className="text-xs text-red-500 uppercase">Missing</p>
          <p className="text-3xl font-bold mt-1 text-red-400">{missingItems}</p>
        </div>
      </div>

      {/* Success Banner */}
      {overallPct >= 95 ? (
        <div className="bg-green-900/20 border border-green-800 rounded-xl p-4">
          <h3 className="text-green-400 font-semibold mb-2">Engine Build Complete</h3>
          <p className="text-sm text-green-300">
            All core modules, integrations, CLI commands, and API routes are built.
            To start publishing, configure your Instagram Graph API credentials and Buffer API key in .env.
          </p>
        </div>
      ) : (
        <div className="bg-yellow-900/20 border border-yellow-800 rounded-xl p-4">
          <h3 className="text-yellow-400 font-semibold mb-2">Almost There</h3>
          <p className="text-sm text-yellow-300">
            {missingItems} items remaining. Check the sections below for details.
          </p>
        </div>
      )}

      {/* Section-by-Section Checklist */}
      {checklist.map((section, si) => (
        <div key={si} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {/* Section Header */}
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="font-semibold text-sm">{section.title}</h3>
            <div className="flex items-center gap-3">
              <div className="w-32 bg-gray-800 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full rounded-full ${completionColor(section.completion)}`}
                  style={{ width: `${section.completion}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 w-10 text-right">{section.completion}%</span>
            </div>
          </div>
          {/* Items */}
          <div className="divide-y divide-gray-800/50">
            {section.items.map((item, ii) => (
              <div key={ii} className="px-4 py-3 flex items-start gap-3">
                <div className="w-16 flex-shrink-0 pt-0.5">{statusIcon(item.status)}</div>
                <div className="flex-1">
                  <p className={`text-sm ${item.status === 'done' ? 'text-gray-300' : item.status === 'partial' ? 'text-yellow-200' : 'text-red-200'}`}>
                    {item.label}
                  </p>
                  {item.notes && (
                    <p className="text-xs text-gray-500 mt-0.5">{item.notes}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
