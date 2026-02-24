import cron from 'node-cron';
import { CONFIG } from '../config/env.js';
import { generateDailyPackage } from '../modules/04-daily-output/daily-engine.js';
import { renderDailyPackage } from '../rendering/asset-pipeline.js';
import { autoPublish } from './auto-publisher.js';
import { format } from 'date-fns';
import chalk from 'chalk';

interface PipelineState {
  phase: 'idle' | 'generating' | 'rendering' | 'awaiting_approval' | 'publishing' | 'analyzing';
  lastRun: string | null;
  todaysPackage: any | null;
  errors: string[];
}

let state: PipelineState = {
  phase: 'idle',
  lastRun: null,
  todaysPackage: null,
  errors: [],
};

export function getState(): PipelineState {
  return { ...state };
}

export async function runDailyPipeline(): Promise<void> {
  console.log(chalk.blue('\n═══════════════════════════════════════'));
  console.log(chalk.blue('  DAILY CONTENT PIPELINE — STARTING'));
  console.log(chalk.blue(`  ${format(new Date(), 'EEEE, MMMM d, yyyy — h:mm a')}`));
  console.log(chalk.blue('═══════════════════════════════════════\n'));

  state.phase = 'generating';
  state.errors = [];

  // Step 1: Generate daily content package — CRITICAL, abort if fails
  let dailyPackage: any;
  try {
    console.log(chalk.yellow('▶ Step 1: Generating daily content package via Claude...'));
    dailyPackage = await generateDailyPackage();
    state.todaysPackage = dailyPackage;
    console.log(chalk.green('✓ Daily package generated'));
  } catch (error: any) {
    state.phase = 'idle';
    state.errors.push(`Content generation failed: ${error.message}`);
    console.log(chalk.red(`\n✗ Pipeline aborted: content generation failed — ${error.message}`));
    return;
  }

  // Step 2: Log trend alert
  try {
    if (dailyPackage.trendAlert?.hasTrend) {
      console.log(chalk.magenta(`⚡ TREND ALERT: ${dailyPackage.trendAlert.topic}`));
      console.log(chalk.magenta(`   Angle: ${dailyPackage.trendAlert.originalAngle}`));
    }
  } catch { /* non-critical */ }

  // Step 3: Display content summary
  try {
    console.log(chalk.cyan('\n📋 TODAY\'S CONTENT PACKAGE:'));
    console.log(chalk.white(`   Carousel: "${dailyPackage.carousel?.idea?.title}"`));
    console.log(chalk.gray(`   → Send trigger: ${dailyPackage.carousel?.idea?.sendTrigger}`));
    console.log(chalk.white(`   Reel: "${dailyPackage.reel?.idea?.title}"`));
    console.log(chalk.gray(`   → Send trigger: ${dailyPackage.reel?.idea?.sendTrigger}`));
    console.log(chalk.white(`   Stories: ${dailyPackage.storySequence?.slides?.length || 0} slides`));
    console.log(chalk.gray(`   → DM trigger: "${dailyPackage.storySequence?.dmTriggerKeyword}"`));
  } catch { /* non-critical */ }

  // Step 4: Auto-render if enabled — NON-CRITICAL, continue without visuals
  let renderedPackage: any = null;
  if (CONFIG.pipeline.autoRender) {
    state.phase = 'rendering';
    try {
      console.log(chalk.yellow('\n▶ Step 4: Rendering visual assets...'));
      renderedPackage = await renderDailyPackage();
      console.log(chalk.green('✓ Visual assets rendered'));
    } catch (error: any) {
      state.errors.push(`Rendering failed (non-fatal): ${error.message}`);
      console.log(chalk.yellow(`\n⚠ Rendering failed (non-fatal): ${error.message}`));
      console.log(chalk.yellow('   Content queued without visuals.'));
    }
  }

  // Step 5: Auto-publish if enabled and rendering succeeded
  if (CONFIG.pipeline.autoPublish && renderedPackage) {
    state.phase = 'publishing';
    try {
      console.log(chalk.yellow('\n▶ Step 5: Auto-publishing to Instagram...'));
      const publishResult = await autoPublish(renderedPackage);
      console.log(chalk.green(`✓ Published ${publishResult.published} items (${publishResult.failed} failed)`));

      for (const r of publishResult.results) {
        if (r.success) {
          console.log(chalk.green(`   ${r.contentType}: ${r.postUrl || 'OK'}`));
        } else {
          console.log(chalk.red(`   ${r.contentType}: ${r.error}`));
        }
      }

      state.phase = 'idle';
      state.lastRun = new Date().toISOString();
      console.log(chalk.green('\n✓ Full pipeline complete — generated, rendered, published.\n'));
      return;
    } catch (error: any) {
      state.errors.push(`Publishing failed (non-fatal): ${error.message}`);
      console.log(chalk.yellow(`\n⚠ Publishing failed (non-fatal): ${error.message}`));
    }
  }

  // If not auto-publishing, move to approval gate
  state.phase = 'awaiting_approval';
  state.lastRun = new Date().toISOString();
  console.log(chalk.yellow('\n⏳ Content queued for approval.'));
  console.log(chalk.yellow('   Open dashboard at http://localhost:' + CONFIG.app.dashboardPort));
  console.log(chalk.yellow('   Or run: npx tsx src/index.ts approve\n'));
}

// Schedule the daily pipeline + weekly token health check
export function startScheduler(): void {
  const [hour, minute] = CONFIG.app.dailyTriggerTime.split(':');
  const cronExpr = `${minute} ${hour} * * *`;

  console.log(chalk.blue(`Scheduler started. Daily pipeline fires at ${CONFIG.app.dailyTriggerTime} ${CONFIG.app.timezone}`));

  // Daily content pipeline
  cron.schedule(cronExpr, () => {
    runDailyPipeline();
  }, { timezone: CONFIG.app.timezone });

  // Weekly token health check (every Monday at 9am)
  cron.schedule('0 9 * * 1', async () => {
    try {
      const { checkAndRefreshToken } = await import('../integrations/instagram-api.js');
      const result = await checkAndRefreshToken();
      if (result.refreshed) {
        console.log(chalk.green('Instagram token auto-refreshed successfully.'));
      } else if (result.daysLeft >= 0) {
        console.log(chalk.blue(`Instagram token healthy: ${result.daysLeft} days remaining.`));
      }
    } catch (err: any) {
      console.warn(chalk.yellow(`Token refresh check failed: ${err.message}`));
    }
  }, { timezone: CONFIG.app.timezone });
}
