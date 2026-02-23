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

  try {
    // Step 1: Generate daily content package
    console.log(chalk.yellow('▶ Step 1: Generating daily content package via Claude...'));
    const dailyPackage = await generateDailyPackage();
    state.todaysPackage = dailyPackage;
    console.log(chalk.green('✓ Daily package generated'));

    // Step 2: Log trend alert
    if (dailyPackage.trendAlert.hasTrend) {
      console.log(chalk.magenta(`⚡ TREND ALERT: ${dailyPackage.trendAlert.topic}`));
      console.log(chalk.magenta(`   Angle: ${dailyPackage.trendAlert.originalAngle}`));
    }

    // Step 3: Display content summary
    console.log(chalk.cyan('\n📋 TODAY\'S CONTENT PACKAGE:'));
    console.log(chalk.white(`   Carousel: "${dailyPackage.carousel.idea.title}"`));
    console.log(chalk.gray(`   → Send trigger: ${dailyPackage.carousel.idea.sendTrigger}`));
    console.log(chalk.white(`   Reel: "${dailyPackage.reel.idea.title}"`));
    console.log(chalk.gray(`   → Send trigger: ${dailyPackage.reel.idea.sendTrigger}`));
    console.log(chalk.white(`   Stories: ${dailyPackage.storySequence.slides.length} slides`));
    console.log(chalk.gray(`   → DM trigger: "${dailyPackage.storySequence.dmTriggerKeyword}"`));

    // Step 4: Auto-render if enabled
    if (CONFIG.pipeline.autoRender) {
      state.phase = 'rendering';
      console.log(chalk.yellow('\n▶ Step 4: Rendering visual assets...'));
      const renderedPackage = await renderDailyPackage();
      console.log(chalk.green('✓ Visual assets rendered'));

      // Step 5: Auto-publish if enabled
      if (CONFIG.pipeline.autoPublish) {
        state.phase = 'publishing';
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
      }
    }

    // If not auto-publishing, move to approval gate
    state.phase = 'awaiting_approval';
    console.log(chalk.yellow('\n⏳ Content queued for approval.'));
    console.log(chalk.yellow('   Open dashboard at http://localhost:' + CONFIG.app.dashboardPort));
    console.log(chalk.yellow('   Or run: npx tsx src/index.ts approve\n'));

    state.lastRun = new Date().toISOString();

  } catch (error: any) {
    state.phase = 'idle';
    state.errors.push(error.message);
    console.log(chalk.red(`\n✗ Pipeline error: ${error.message}`));
  }
}

// Schedule the daily pipeline
export function startScheduler(): void {
  const [hour, minute] = CONFIG.app.dailyTriggerTime.split(':');
  const cronExpr = `${minute} ${hour} * * *`;

  console.log(chalk.blue(`Scheduler started. Daily pipeline fires at ${CONFIG.app.dailyTriggerTime} ${CONFIG.app.timezone}`));

  cron.schedule(cronExpr, () => {
    runDailyPipeline();
  }, { timezone: CONFIG.app.timezone });
}
