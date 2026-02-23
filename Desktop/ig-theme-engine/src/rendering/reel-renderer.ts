import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import ffmpeg from 'fluent-ffmpeg';
import ffmpegInstaller from '@ffmpeg-installer/ffmpeg';
import { getBrowser } from './browser-pool.js';
import { reelOverlayHtml } from './templates.js';
import { generateBackground } from '../integrations/replicate-api.js';
import { generateSpeech } from '../integrations/tts-api.js';
import type { ReelScript, ReelSegment, RenderConfig } from './types.js';
import { CONFIG } from '../config/env.js';

ffmpeg.setFfmpegPath(ffmpegInstaller.path);

/**
 * Render a reel as an MP4 video:
 * 1. Generate AI backgrounds per segment (Replicate Flux)
 * 2. Generate voiceover (OpenAI TTS)
 * 3. Render text overlays as transparent PNGs (Puppeteer)
 * 4. Compose everything with ffmpeg
 */
export async function renderReel(
  script: ReelScript,
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string> {
  const outputDir = path.join(CONFIG.paths.assets, `reel-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const allSegments = buildSegmentList(script);

  // Step 1: Generate AI backgrounds (parallel)
  console.log('  Generating AI backgrounds...');
  const bgPaths = await Promise.all(
    allSegments.map((seg, i) =>
      generateBackground(
        seg.visualDescription || `cinematic ${CONFIG.app.niche} visual, moody lighting, vertical 9:16`,
        outputDir,
        `bg-${i}.png`
      )
    )
  );

  // Step 2: Generate voiceover
  console.log('  Generating voiceover...');
  const voiceoverText = script.voiceoverText
    || [script.hook, ...allSegments.map(s => s.text), script.cta].join('. ');
  const voiceoverPath = await generateSpeech(voiceoverText, outputDir, 'voiceover.mp3');

  // Step 3: Render text overlays as transparent PNGs
  console.log('  Rendering text overlays...');
  const overlayPaths = await renderTextOverlays(allSegments, renderConfig, outputDir);

  // Step 4: Compose video with ffmpeg
  console.log('  Composing video...');
  const outputPath = path.join(outputDir, 'reel.mp4');
  await composeVideo(bgPaths, overlayPaths, allSegments, voiceoverPath, outputPath);

  return outputPath;
}

function buildSegmentList(script: ReelScript): ReelSegment[] {
  const segments: ReelSegment[] = [];

  // Hook segment
  segments.push({
    text: script.hook,
    durationSeconds: 3,
    visualDescription: 'attention-grabbing dramatic visual',
  });

  // Body segments
  for (const seg of script.segments) {
    segments.push(seg);
  }

  // CTA segment
  segments.push({
    text: script.cta,
    durationSeconds: 4,
    visualDescription: 'call to action motivational visual',
  });

  return segments;
}

async function renderTextOverlays(
  segments: ReelSegment[],
  config: RenderConfig,
  outputDir: string
): Promise<string[]> {
  const browser = await getBrowser();
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

  const paths: string[] = [];

  try {
    for (let i = 0; i < segments.length; i++) {
      const html = reelOverlayHtml(segments[i].text, config);
      await page.setContent(html, { waitUntil: 'domcontentloaded' });
      await page.evaluate(() => Promise.race([
        document.fonts.ready,
        new Promise(r => setTimeout(r, 3000)),
      ]));

      const outputPath = path.join(outputDir, `overlay-${i}.png`);
      await page.screenshot({ path: outputPath, type: 'png', omitBackground: true });
      paths.push(outputPath);
    }
  } finally {
    await page.close();
  }

  return paths;
}

function composeVideo(
  bgPaths: string[],
  overlayPaths: string[],
  segments: ReelSegment[],
  voiceoverPath: string,
  outputPath: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    // Build a complex filter to:
    // - Create video segments from still images with duration
    // - Overlay text on each segment
    // - Concatenate all segments
    // - Add audio

    const segmentCount = segments.length;
    let filterComplex = '';
    const inputs: string[] = [];

    // Add all background inputs
    for (let i = 0; i < segmentCount; i++) {
      inputs.push(bgPaths[i]);
    }
    // Add all overlay inputs
    for (let i = 0; i < segmentCount; i++) {
      inputs.push(overlayPaths[i]);
    }
    // Add voiceover
    inputs.push(voiceoverPath);

    // Build filter graph
    // Scale backgrounds to 1080x1920, set duration, create video from still
    for (let i = 0; i < segmentCount; i++) {
      const dur = segments[i].durationSeconds;
      filterComplex += `[${i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,loop=loop=${dur * 25}:size=1:start=0,fps=25,trim=duration=${dur},setpts=PTS-STARTPTS[bg${i}];`;
    }

    // Scale overlays
    for (let i = 0; i < segmentCount; i++) {
      const overlayIdx = segmentCount + i;
      filterComplex += `[${overlayIdx}:v]scale=1080:1920[ov${i}];`;
    }

    // Overlay text on backgrounds
    for (let i = 0; i < segmentCount; i++) {
      filterComplex += `[bg${i}][ov${i}]overlay=0:0:format=auto[seg${i}];`;
    }

    // Concatenate all segments
    const concatInputs = Array.from({ length: segmentCount }, (_, i) => `[seg${i}]`).join('');
    filterComplex += `${concatInputs}concat=n=${segmentCount}:v=1:a=0[outv]`;

    const audioIdx = inputs.length - 1;

    const cmd = ffmpeg();

    for (const input of inputs) {
      cmd.input(input);
    }

    cmd
      .complexFilter(filterComplex)
      .outputOptions([
        '-map', '[outv]',
        '-map', `${audioIdx}:a`,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-shortest',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
      ])
      .output(outputPath)
      .on('end', () => resolve())
      .on('error', (err) => reject(new Error(`ffmpeg error: ${err.message}`)))
      .run();
  });
}

/**
 * Parse a content_scripts row's script_json into a ReelScript.
 */
export function parseReelScript(scriptJson: string): ReelScript {
  const parsed = JSON.parse(scriptJson);

  const reel = parsed.reel || parsed;

  return {
    hook: reel.hook || reel.hookLine || '',
    segments: (reel.segments || reel.body || []).map((s: any) => ({
      text: s.text || s.line || '',
      durationSeconds: s.durationSeconds || s.duration || 4,
      visualDescription: s.visualDescription || s.visual || '',
    })),
    cta: reel.cta || reel.ctaLine || '',
    totalLength: reel.totalLength || 30,
    voiceoverText: reel.voiceoverText || '',
  };
}
