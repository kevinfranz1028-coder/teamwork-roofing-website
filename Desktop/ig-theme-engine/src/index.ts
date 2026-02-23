import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { analyzeNiches, selectNiche } from './modules/01-niche-selector/niche-analyzer.js';
import { generateOriginalityStrategy } from './modules/00-originality/originality-engine.js';
import { auditQueue } from './modules/00-originality/fingerprint-check.js';
import { generateViralBlueprint } from './modules/02-viral-blueprint/content-ideator.js';
import { generateContentCalendar, getUpcomingCalendar } from './modules/06-growth-strategy/scheduler.js';
import { generateEngagementProtocol } from './modules/06-growth-strategy/engagement-engine.js';
import { generateRevenueStrategy } from './modules/07-monetization/revenue-tracker.js';
import { generateRoadmap } from './modules/08-scaling/roadmap-engine.js';
import { createDMFlow, generateLeadMagnets } from './modules/09-dm-automation/dm-flows.js';
import { adaptForPlatform } from './modules/10-cross-platform/distributor.js';
import { generateDesignSystem } from './modules/05-design-system/design-manager.js';
import { runDailyPipeline, startScheduler, getState } from './orchestrator/master.js';
import { approveContent, rejectContent, publishContent } from './orchestrator/approval-gate.js';
import { refreshAnalytics, generateWeeklyScorecard } from './orchestrator/analytics-loop.js';
import { renderScript, renderDailyPackage } from './rendering/asset-pipeline.js';
import { autoPublish } from './orchestrator/auto-publisher.js';
import { scanTrends } from './modules/04-daily-output/trend-scanner.js';
import { runMigrations } from './database/migrations.js';
import { getDb, getRows } from './database/db.js';
import { CONFIG } from './config/env.js';

const program = new Command();

program
  .name('ig-engine')
  .description('Instagram Theme Page AI Engine')
  .version('1.0.0');

// ─── SETUP COMMANDS ─────────────────────────────────
program
  .command('niches')
  .description('Run Module 1: Analyze and rank 20 niches')
  .action(async () => {
    const spinner = ora('Analyzing 20 niches via Claude...').start();
    try {
      const result = await analyzeNiches();
      spinner.succeed('Niche analysis complete');

      console.log(chalk.cyan('\n═══ TOP 10 NICHES ═══\n'));
      result.niches.slice(0, 10).forEach((n, i) => {
        console.log(chalk.white(`${i + 1}. ${n.name} (${n.subNiche})`));
        console.log(chalk.gray(`   Score: ${n.compositeScore} | Send trigger: ${n.sendTrigger}`));
        console.log(chalk.gray(`   DM Share: ${n.scores.dmShareability} | Original: ${n.scores.originalContentViability} | SEO: ${n.scores.searchSeo}`));
        console.log();
      });

      console.log(chalk.yellow('Run `ig-engine select-niche <id>` to choose your niche.'));
    } catch (err: any) {
      spinner.fail(err.message);
    }
  });

program
  .command('select-niche <id>')
  .description('Select a niche by its database ID')
  .action((id: string) => {
    selectNiche(parseInt(id));
    const niche = getDb().prepare('SELECT * FROM niches WHERE id = ?').get(parseInt(id)) as any;
    console.log(chalk.green(`✓ Selected: ${niche.name} (${niche.sub_niche})`));
    console.log(chalk.yellow('Update your .env file: NICHE="' + niche.name + '"'));
  });

program
  .command('originality')
  .description('Run Module 0: Generate originality architecture for your niche')
  .action(async () => {
    if (!CONFIG.app.niche) {
      console.log(chalk.red('Set NICHE in .env first. Run `ig-engine niches` to explore options.'));
      return;
    }
    const spinner = ora('Designing originality architecture...').start();
    const strategy = await generateOriginalityStrategy(CONFIG.app.niche);
    spinner.succeed('Originality architecture generated');

    console.log(chalk.cyan('\n═══ ORIGINALITY STRATEGY ═══\n'));
    console.log(chalk.white(`Primary Method: ${strategy.primaryMethod}`));
    console.log(chalk.gray(strategy.description));
    console.log(chalk.yellow('\nRed Lines (NEVER do these):'));
    strategy.redLines.forEach(r => console.log(chalk.red(`  ✗ ${r}`)));
    console.log(chalk.green('\nTransformation Rules:'));
    strategy.transformationRules.forEach((r: any) => {
      const text = typeof r === 'string' ? r : r.rule || r.description || JSON.stringify(r);
      console.log(chalk.green(`  ✓ ${text}`));
    });
  });

program
  .command('design-system')
  .description('Run Module 5: Generate brand design system')
  .action(async () => {
    const spinner = ora('Generating design system...').start();
    const ds = await generateDesignSystem(CONFIG.app.niche);
    spinner.succeed('Design system generated');
    console.log(chalk.cyan('\n═══ DESIGN SYSTEM ═══\n'));
    console.log(chalk.white(`Aesthetic: ${ds.moodBoard.aesthetic}`));
    console.log(chalk.gray(`Primary: ${ds.colorPalette.primary} | Accent: ${ds.colorPalette.accent}`));
    console.log(chalk.gray(`Headline: ${ds.typography.headlineFont} | Body: ${ds.typography.bodyFont}`));
  });

// ─── DAILY OPERATIONS ───────────────────────────────
program
  .command('daily')
  .description('Run the daily content pipeline NOW (manual trigger)')
  .action(async () => {
    await runDailyPipeline();
  });

program
  .command('start')
  .description('Start the scheduled daily pipeline + dashboard')
  .action(() => {
    runMigrations();
    startScheduler();
    import('./server.js').then(({ startDashboard }) => {
      startDashboard();
    });
    console.log(chalk.green(`\nDashboard: http://localhost:${CONFIG.app.dashboardPort}`));
    console.log(chalk.blue('Press Ctrl+C to stop.\n'));
  });

program
  .command('status')
  .description('Show current pipeline status')
  .action(() => {
    const s = getState();
    console.log(chalk.cyan('\n═══ PIPELINE STATUS ═══'));
    console.log(`Phase: ${s.phase}`);
    console.log(`Last run: ${s.lastRun || 'Never'}`);
    if (s.errors.length) console.log(chalk.red(`Errors: ${s.errors.join(', ')}`));
  });

program
  .command('trends')
  .description('Scan for trending topics in your niche')
  .action(async () => {
    const spinner = ora('Scanning trends...').start();
    const trends = await scanTrends();
    spinner.succeed('Trend scan complete');
    if (trends.hasTrend) {
      trends.trends.forEach(t => {
        console.log(chalk.magenta(`\n⚡ ${t.topic} [${t.urgency}]`));
        console.log(chalk.gray(`   Angle: ${t.originalAngle}`));
        console.log(chalk.gray(`   Hook: ${t.hookIdea}`));
      });
    } else {
      console.log(chalk.gray('No actionable trends detected today.'));
    }
  });

// ─── CONTENT MANAGEMENT ─────────────────────────────
program
  .command('queue')
  .description('View content awaiting approval')
  .action(() => {
    const items = getRows('content_scripts', undefined, 20) as any[];
    const pending = items.filter((i: any) => {
      const idea = getDb().prepare('SELECT status FROM content_ideas WHERE id = ?').get(i.idea_id) as any;
      return idea?.status === 'scripted';
    });

    if (pending.length === 0) {
      console.log(chalk.gray('No content in queue. Run `ig-engine daily` to generate.'));
      return;
    }

    console.log(chalk.cyan(`\n═══ CONTENT QUEUE (${pending.length} items) ═══\n`));
    pending.forEach((item: any) => {
      const script = JSON.parse(item.script_json);
      console.log(chalk.white(`[${item.id}] ${item.content_type.toUpperCase()}: ${script.idea?.title || 'Untitled'}`));
      console.log(chalk.gray(`  Caption: ${(item.caption || '').slice(0, 80)}...`));
      console.log();
    });
  });

program
  .command('approve <scriptId>')
  .description('Approve a content script for publishing')
  .action((scriptId: string) => {
    approveContent(parseInt(scriptId));
    console.log(chalk.green(`✓ Script ${scriptId} approved and ready to publish.`));
  });

program
  .command('reject <scriptId>')
  .description('Reject a content script')
  .action((scriptId: string) => {
    rejectContent(parseInt(scriptId));
    console.log(chalk.yellow(`✗ Script ${scriptId} rejected and archived.`));
  });

program
  .command('publish <scriptId>')
  .description('Publish approved content to Instagram')
  .option('--method <method>', 'Publishing method: instagram_direct, buffer, manual', 'manual')
  .option('--images <urls>', 'Comma-separated image URLs')
  .option('--video <url>', 'Video URL for reels')
  .action(async (scriptId: string, opts: any) => {
    const spinner = ora('Publishing content...').start();
    const result = await publishContent(parseInt(scriptId), {
      method: opts.method,
      imageUrls: opts.images?.split(','),
      videoUrl: opts.video,
    });
    if (result.success) {
      spinner.succeed(`Published to ${result.platform}${result.postUrl ? ` — ${result.postUrl}` : ''}`);
    } else {
      spinner.fail(`Publish failed: ${result.error}`);
    }
  });

// ─── RENDERING & AUTO-PUBLISH ──────────────────────────
program
  .command('render [scriptId]')
  .description('Render visual assets for a script (or all of today\'s content)')
  .action(async (scriptId?: string) => {
    if (scriptId) {
      const spinner = ora(`Rendering script ${scriptId}...`).start();
      const result = await renderScript(parseInt(scriptId));
      if (result) {
        spinner.succeed(`Rendered ${result.localPaths.length} files for ${result.contentType}`);
        result.localPaths.forEach(p => console.log(chalk.gray(`  ${p}`)));
        if (result.publicUrls.length) {
          console.log(chalk.cyan('\nPublic URLs:'));
          result.publicUrls.forEach(u => console.log(chalk.white(`  ${u}`)));
        }
      } else {
        spinner.fail('Nothing to render');
      }
    } else {
      const spinner = ora('Rendering all of today\'s content...').start();
      const pkg = await renderDailyPackage();
      const count = [pkg.carousel, pkg.stories, pkg.reel].filter(Boolean).length;
      spinner.succeed(`Rendered ${count} content types`);
      if (pkg.carousel) console.log(chalk.green(`  Carousel: ${pkg.carousel.localPaths.length} slides`));
      if (pkg.stories) console.log(chalk.green(`  Stories: ${pkg.stories.localPaths.length} slides`));
      if (pkg.reel) console.log(chalk.green(`  Reel: ${pkg.reel.localPaths[0]}`));
    }
  });

program
  .command('auto-publish')
  .description('Render + publish all of today\'s content to Instagram automatically')
  .action(async () => {
    const spinner = ora('Running full auto-publish pipeline...').start();
    spinner.text = 'Rendering assets...';
    const pkg = await renderDailyPackage();
    spinner.text = 'Publishing to Instagram...';
    const result = await autoPublish(pkg);
    if (result.published > 0) {
      spinner.succeed(`Published ${result.published} items to Instagram`);
    } else {
      spinner.warn('No items published');
    }
    for (const r of result.results) {
      if (r.success) {
        console.log(chalk.green(`  ${r.contentType}: ${r.postUrl || 'OK'}`));
      } else if (r.error) {
        console.log(chalk.red(`  ${r.contentType}: ${r.error}`));
      }
    }
  });

program
  .command('fingerprint')
  .description('Run originality check on all queued content')
  .action(async () => {
    const spinner = ora('Running originality audit...').start();
    const results = await auditQueue();
    spinner.succeed('Audit complete');
    results.forEach(r => {
      const color = r.result.overallScore >= 7 ? chalk.green : r.result.overallScore >= 5 ? chalk.yellow : chalk.red;
      console.log(color(`  [${r.scriptId}] Score: ${r.result.overallScore}/10 — ${r.result.isOriginal ? 'ORIGINAL' : 'NEEDS WORK'}`));
      r.result.flags.forEach(f => console.log(chalk.gray(`    ⚠ ${f}`)));
    });
  });

// ─── ANALYTICS ──────────────────────────────────────
program
  .command('analytics')
  .description('Refresh analytics from Instagram API')
  .action(async () => {
    const spinner = ora('Fetching latest analytics...').start();
    await refreshAnalytics();
    spinner.succeed('Analytics refreshed');
  });

program
  .command('scorecard')
  .description('Generate weekly scorecard')
  .action(() => {
    const sc = generateWeeklyScorecard();
    console.log(chalk.cyan('\n═══ WEEKLY SCORECARD ═══\n'));
    console.log(`Status: ${sc.status === 'green' ? chalk.green('GREEN') : sc.status === 'yellow' ? chalk.yellow('YELLOW') : chalk.red('RED')}`);
    console.log(`Posts: ${sc.postsPublished}`);
    console.log(`Total Reach: ${sc.totalReach?.toLocaleString()}`);
    console.log(`Total Sends: ${sc.totalSends?.toLocaleString()}`);
    console.log(`Avg Sends/Reach: ${((sc.avgSendsPerReach || 0) * 100).toFixed(2)}%`);
    console.log(`Revenue: $${(sc.revenue || 0).toFixed(2)}`);
  });

// ─── GROWTH & STRATEGY ──────────────────────────────
program
  .command('blueprint')
  .description('Run Module 2: Generate viral content blueprint')
  .action(async () => {
    const niche = getDb().prepare('SELECT * FROM niches WHERE selected = 1').get() as any;
    if (!niche) { console.log(chalk.red('Select a niche first.')); return; }
    const spinner = ora('Generating viral blueprint...').start();
    const bp = await generateViralBlueprint(niche.name, niche.sub_niche);
    spinner.succeed(`Generated ${bp.ideas.length} viral content ideas`);
    console.log(chalk.cyan(`\nPosting cadence: ${bp.postingCadence.postsPerWeek} posts/week`));
    bp.ideas.slice(0, 5).forEach((idea, i) => {
      console.log(chalk.white(`  ${i + 1}. [${idea.type}] ${idea.title}`));
      console.log(chalk.gray(`     Send: ${idea.sendTrigger}`));
    });
  });

program
  .command('calendar')
  .description('Run Module 6: Generate 4-week content calendar')
  .option('--pillars <pillars>', 'Comma-separated content pillars')
  .action(async (opts: any) => {
    const pillars = opts.pillars?.split(',') || ['education', 'diagnosis', 'transformation', 'community', 'promotion'];
    const spinner = ora('Generating content calendar...').start();
    const cal = await generateContentCalendar(pillars);
    spinner.succeed('4-week calendar generated');
    cal.weeks.forEach(w => {
      console.log(chalk.cyan(`\nWeek ${w.weekNumber}: ${w.theme}`));
      w.days.forEach(d => {
        if (d.postType !== 'rest') {
          console.log(chalk.white(`  ${d.day} ${d.postingTime} [${d.postType}] ${d.ideaTitle}`));
        }
      });
    });
  });

program
  .command('engagement')
  .description('Run Module 6: Generate engagement protocol')
  .action(async () => {
    const spinner = ora('Generating engagement protocol...').start();
    const protocol = await generateEngagementProtocol();
    spinner.succeed('Engagement protocol ready');
    console.log(chalk.cyan('\n═══ DAILY ENGAGEMENT ═══'));
    console.log(chalk.white('\nPre-post:'));
    protocol.prePostEngagement.actions.forEach(a => console.log(chalk.gray(`  • ${a}`)));
    console.log(chalk.white('\nPost-post (first hour):'));
    protocol.postPostEngagement.firstHour.forEach(a => console.log(chalk.gray(`  • ${a}`)));
  });

program
  .command('monetize')
  .description('Run Module 7: Generate monetization strategy')
  .option('--followers <count>', 'Current follower count', '0')
  .action(async (opts: any) => {
    const spinner = ora('Generating monetization strategy...').start();
    const strategy = await generateRevenueStrategy(parseInt(opts.followers));
    spinner.succeed('Strategy ready');
    console.log(chalk.cyan(`\nPhase: ${strategy.currentPhase}`));
    console.log(chalk.white('\nImmediate actions:'));
    strategy.immediateActions.forEach(a => console.log(chalk.green(`  → ${a.action} (${a.expectedRevenue})`)));
    console.log(chalk.white('\nRevenue streams:'));
    strategy.revenueStreams.forEach(s => console.log(chalk.gray(`  ${s.priority}. ${s.stream} — ${s.monthlyPotential}`)));
  });

program
  .command('roadmap')
  .description('Run Module 8: Generate scaling roadmap')
  .option('--followers <count>', 'Current follower count', '0')
  .action(async (opts: any) => {
    const spinner = ora('Generating scaling roadmap...').start();
    const roadmap = await generateRoadmap(parseInt(opts.followers));
    spinner.succeed('Roadmap ready');
    console.log(chalk.cyan(`\nCurrent phase: ${roadmap.currentPhase.name}`));
    console.log(chalk.white(`Next milestone: ${roadmap.nextMilestone.followers} followers (~${roadmap.nextMilestone.estimatedWeeks} weeks)`));
    console.log(chalk.white('\nTop growth levers:'));
    roadmap.growthLevers.slice(0, 5).forEach(l => console.log(chalk.green(`  ${l.priority}. ${l.lever} [${l.impact} impact]`)));
  });

program
  .command('dm-flow <keyword> <value>')
  .description('Run Module 9: Create a DM automation flow')
  .action(async (keyword: string, value: string) => {
    const spinner = ora(`Creating DM flow for "${keyword}"...`).start();
    const flow = await createDMFlow(keyword, value);
    spinner.succeed(`DM flow created: ${flow.flowName}`);
    console.log(chalk.cyan(`Steps: ${flow.steps.length} | Goal: ${flow.conversionGoal}`));
  });

program
  .command('lead-magnets')
  .description('Run Module 9: Generate lead magnet ideas')
  .action(async () => {
    const spinner = ora('Generating lead magnet ideas...').start();
    const result = await generateLeadMagnets();
    spinner.succeed('Lead magnets generated');
    result.leadMagnets.forEach((lm, i) => {
      console.log(chalk.white(`\n${i + 1}. ${lm.name} [${lm.type}]`));
      console.log(chalk.gray(`   DM keyword: "${lm.dmKeyword}" | Create in: ${lm.creationTime}`));
      console.log(chalk.gray(`   → Leads to: ${lm.paidProductBridge}`));
    });
  });

program
  .command('cross-platform <scriptId> <platform>')
  .description('Run Module 10: Adapt content for another platform (tiktok, youtube_shorts, pinterest, twitter)')
  .action(async (scriptId: string, platform: string) => {
    const spinner = ora(`Adapting for ${platform}...`).start();
    const adapted = await adaptForPlatform(parseInt(scriptId), platform as any);
    spinner.succeed(`Adapted for ${platform}`);
    console.log(chalk.cyan(`\nTitle: ${adapted.title}`));
    console.log(chalk.white(`Format: ${adapted.adaptedFormat}`));
    console.log(chalk.gray(`Hook: ${adapted.hook}`));
    console.log(chalk.gray(`Schedule: ${adapted.schedulingNote}`));
  });

program.parse();
