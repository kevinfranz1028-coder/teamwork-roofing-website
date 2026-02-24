import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import ffmpeg from 'fluent-ffmpeg';
import ffmpegInstaller from '@ffmpeg-installer/ffmpeg';
import sharp from 'sharp';
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

  // Step 1: Generate AI backgrounds (parallel), fallback to gradient if Replicate fails
  console.log('  Generating AI backgrounds...');
  let bgPaths: string[];
  try {
    bgPaths = await Promise.all(
      allSegments.map((seg, i) =>
        generateBackground(
          seg.visualDescription || `cinematic ${CONFIG.app.niche} visual, moody lighting, vertical 9:16`,
          outputDir,
          `bg-${i}.png`
        )
      )
    );
  } catch (err: any) {
    console.log(`  Replicate failed (${err.message}), using gradient backgrounds...`);
    bgPaths = await Promise.all(
      allSegments.map((_, i) => generateGradientBackground(outputDir, `bg-${i}.png`, renderConfig, i))
    );
  }

  // Step 2: Generate voiceover, fallback to silent audio if TTS fails
  const totalDuration = allSegments.reduce((sum, s) => sum + s.durationSeconds, 0);
  console.log('  Generating voiceover...');
  let voiceoverPath: string;
  try {
    const voiceoverText = script.voiceoverText
      || [script.hook, ...allSegments.map(s => s.text), script.cta].join('. ');
    voiceoverPath = await generateSpeech(voiceoverText, outputDir, 'voiceover.mp3');
  } catch (err: any) {
    console.log(`  TTS failed (${err.message}), generating silent audio...`);
    voiceoverPath = await generateSilentAudio(outputDir, allSegments);
  }

  // Pad voiceover with silence to match total video duration so -shortest doesn't truncate
  voiceoverPath = await padAudioToLength(voiceoverPath, totalDuration, outputDir);

  // Step 3: Render text overlays as transparent PNGs
  console.log('  Rendering text overlays...');
  const overlayPaths = await renderTextOverlays(allSegments, renderConfig, outputDir);

  // Step 4: Compose video with ffmpeg
  console.log('  Composing video...');
  const outputPath = path.join(outputDir, 'reel.mp4');
  await composeVideo(bgPaths, overlayPaths, allSegments, voiceoverPath, outputPath);

  return outputPath;
}

function generateSilentAudio(outputDir: string, segments: ReelSegment[]): Promise<string> {
  const totalDuration = segments.reduce((sum, s) => sum + s.durationSeconds, 0);
  const outputPath = path.join(outputDir, 'voiceover.mp3');
  return new Promise((resolve, reject) => {
    ffmpeg()
      .input('anullsrc=r=44100:cl=mono')
      .inputFormat('lavfi')
      .duration(totalDuration)
      .audioCodec('libmp3lame')
      .output(outputPath)
      .on('end', () => resolve(outputPath))
      .on('error', (err) => reject(new Error(`Silent audio generation failed: ${err.message}`)))
      .run();
  });
}

function padAudioToLength(audioPath: string, targetSeconds: number, outputDir: string): Promise<string> {
  const paddedPath = path.join(outputDir, 'voiceover-padded.mp3');
  return new Promise((resolve, reject) => {
    ffmpeg()
      .input(audioPath)
      .input('anullsrc=r=44100:cl=mono')
      .inputFormat('lavfi')
      .complexFilter(`[0:a][1:a]concat=n=2:v=0:a=1[out]`)
      .outputOptions(['-map', '[out]', '-t', `${targetSeconds}`])
      .audioCodec('libmp3lame')
      .output(paddedPath)
      .on('end', () => resolve(paddedPath))
      .on('error', (err) => reject(new Error(`Audio padding failed: ${err.message}`)))
      .run();
  });
}

async function generateGradientBackground(
  outputDir: string,
  filename: string,
  config: RenderConfig,
  index: number
): Promise<string> {
  const outputPath = path.join(outputDir, filename);
  // Rotate hue slightly per segment for visual variety
  const colors = [config.brandColors.primary, config.brandColors.accent, config.brandColors.secondary];
  const hex = colors[index % colors.length].replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  await sharp({
    create: { width: 1080, height: 1920, channels: 3, background: { r, g, b } },
  }).png().toFile(outputPath);

  return outputPath;
}

function buildSegmentList(script: ReelScript): ReelSegment[] {
  const segments: ReelSegment[] = [];

  // Hook segment — use parsed duration from timestamp, fallback to 3s
  segments.push({
    text: script.hook,
    durationSeconds: script.hookDuration || 3,
    visualDescription: script.hookVisual || 'attention-grabbing dramatic visual',
    segmentType: 'hook',
  });

  // Body segments
  for (const seg of script.segments) {
    segments.push({ ...seg, segmentType: seg.segmentType || 'body' });
  }

  // CTA segment — use parsed duration from timestamp, fallback to 4s
  segments.push({
    text: script.cta,
    durationSeconds: script.ctaDuration || 4,
    visualDescription: script.ctaVisual || 'call to action motivational visual',
    segmentType: 'cta',
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
  // Count body segments for step indicators
  const bodySegments = segments.filter(s => s.segmentType === 'body');
  const totalBodySteps = bodySegments.length;
  let bodyIndex = 0;

  try {
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      const segType = seg.segmentType || 'body';
      let stepIdx: number | undefined;
      if (segType === 'body') {
        bodyIndex++;
        stepIdx = bodyIndex;
      }
      const html = reelOverlayHtml(seg.text, config, segType, stepIdx, totalBodySteps);
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
    // Scale backgrounds to 1080x1920, then use zoompan to generate video frames with Ken Burns effect
    for (let i = 0; i < segmentCount; i++) {
      const dur = segments[i].durationSeconds;
      const frames = dur * 25;
      filterComplex += `[${i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,zoompan=z='min(zoom+0.0005,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${frames}:s=1080x1920:fps=25,setpts=PTS-STARTPTS[bg${i}];`;
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

    // Apply crossfade transitions (0.3s dissolve) between segments
    if (segmentCount > 1) {
      let cumulativeDuration = segments[0].durationSeconds;
      let prevLabel = 'seg0';
      for (let i = 1; i < segmentCount; i++) {
        const fadeOffset = cumulativeDuration - 0.3;
        const outLabel = i === segmentCount - 1 ? 'outv' : `xf${i}`;
        filterComplex += `[${prevLabel}][seg${i}]xfade=transition=fade:duration=0.3:offset=${fadeOffset.toFixed(2)}[${outLabel}];`;
        cumulativeDuration += segments[i].durationSeconds - 0.3;
        prevLabel = outLabel;
      }
    } else {
      // Single segment, just rename
      filterComplex += `[seg0]copy[outv];`;
    }

    // Remove trailing semicolon — ffmpeg rejects it
    filterComplex = filterComplex.replace(/;$/, '');

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
 * Parse a timestamp range string into a duration in seconds.
 * Supports: "0:02-0:05" (mm:ss), "1.7-4s", "4-7s", "19-23s" (seconds).
 */
function parseDurationFromTimestamp(timestamp: string): number | null {
  // Format: "0:02-0:05" (mm:ss-mm:ss)
  const mmss = timestamp.match(/(\d+):(\d+)\s*-\s*(\d+):(\d+)/);
  if (mmss) {
    const start = parseInt(mmss[1]) * 60 + parseInt(mmss[2]);
    const end = parseInt(mmss[3]) * 60 + parseInt(mmss[4]);
    return end - start;
  }
  // Format: "1.7-4s", "4-7s", "19-23s", "0-1.7s" (seconds with optional 's' suffix)
  const secs = timestamp.match(/([\d.]+)\s*s?\s*-\s*([\d.]+)\s*s?/);
  if (secs) {
    const dur = parseFloat(secs[2]) - parseFloat(secs[1]);
    if (dur > 0) return dur;
  }
  return null;
}

/**
 * Parse a content_scripts row's script_json into a ReelScript.
 */
export function parseReelScript(scriptJson: string): ReelScript {
  const parsed = JSON.parse(scriptJson);

  const reel = parsed.reel || parsed;

  // Hook can be a string or object with onScreenText
  const hookRaw = reel.hook;
  const hook = typeof hookRaw === 'string' ? hookRaw : hookRaw?.onScreenText || hookRaw?.text || '';

  // CTA can be a string or object with onScreenText
  const ctaRaw = reel.cta;
  const cta = typeof ctaRaw === 'string' ? ctaRaw : ctaRaw?.onScreenText || ctaRaw?.text || '';

  // Parse hook/CTA durations from timestamps
  const hookDuration = (typeof hookRaw === 'object' && hookRaw?.timestamp)
    ? parseDurationFromTimestamp(hookRaw.timestamp) ?? 3
    : 3;
  const ctaDuration = (typeof ctaRaw === 'object' && ctaRaw?.timestamp)
    ? parseDurationFromTimestamp(ctaRaw.timestamp) ?? 4
    : 4;

  // Segments can use body[], segments[], or other shapes
  const rawSegments = reel.segments || reel.body || [];

  const segments = rawSegments.map((s: any) => {
    const text = s.text || s.onScreenText || s.line || '';
    let durationSeconds: number | null = null;

    // Use explicit duration fields first
    if (typeof s.durationSeconds === 'number') durationSeconds = s.durationSeconds;
    else if (typeof s.duration === 'number') durationSeconds = s.duration;

    // Parse duration from timestamp if not set explicitly
    if (durationSeconds === null && s.timestamp) {
      durationSeconds = parseDurationFromTimestamp(s.timestamp);
    }

    return {
      text,
      durationSeconds: durationSeconds && durationSeconds > 0 ? durationSeconds : 4,
      visualDescription: s.visualDescription || s.visual || '',
      segmentType: s.segmentType || 'body',
    };
  });

  // Build voiceover from all segment voiceover fields
  const voiceoverParts: string[] = [];
  if (hookRaw?.voiceover) voiceoverParts.push(hookRaw.voiceover);
  for (const s of rawSegments) {
    if (s.voiceover) voiceoverParts.push(s.voiceover);
  }
  if (ctaRaw?.voiceover) voiceoverParts.push(ctaRaw.voiceover);
  const voiceoverText = reel.voiceoverText || voiceoverParts.join('. ') || '';

  // Extract visual descriptions for hook and CTA
  const hookVisual = typeof hookRaw === 'object' ? (hookRaw?.visual || hookRaw?.visualDescription || '') : '';
  const ctaVisual = typeof ctaRaw === 'object' ? (ctaRaw?.visual || ctaRaw?.visualDescription || '') : '';

  return {
    hook,
    hookVisual,
    hookDuration,
    segments,
    cta,
    ctaVisual,
    ctaDuration,
    totalLength: reel.totalLength || 30,
    voiceoverText,
  };
}
