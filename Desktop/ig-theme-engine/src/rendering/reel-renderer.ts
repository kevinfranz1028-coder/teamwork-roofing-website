import path from 'path';
import { mkdirSync, existsSync, copyFileSync, unlinkSync } from 'fs';
import { execSync } from 'child_process';
import ffmpeg from 'fluent-ffmpeg';
import ffmpegInstaller from '@ffmpeg-installer/ffmpeg';
import sharp from 'sharp';
import { getBrowser } from './browser-pool.js';
import { reelOverlayHtml } from './templates.js';
import { generateSpeech } from '../integrations/tts-api.js';
import { findAndDownloadVideoClip } from '../integrations/pexels-api.js';
import type { ReelScript, ReelSegment, ReelScriptV2, ReelSegmentV2, RenderConfig } from './types.js';
import { CONFIG } from '../config/env.js';

ffmpeg.setFfmpegPath(ffmpegInstaller.path);

// ─── Audio Utilities ───

function getMediaDuration(filePath: string): number {
  try {
    const result = execSync(
      `ffprobe -v quiet -print_format json -show_format "${filePath}"`,
      { encoding: 'utf-8' }
    );
    return parseFloat(JSON.parse(result).format?.duration || '0');
  } catch { return 0; }
}

function matchClipToAudioDuration(
  clipPath: string, audioDuration: number, outputPath: string
): string {
  const clipDuration = getMediaDuration(clipPath);
  if (clipDuration <= 0 || audioDuration <= 0) return clipPath;
  const diff = audioDuration - clipDuration;
  if (Math.abs(diff) < 0.1) return clipPath;

  if (diff > 0) {
    console.log(`    Extending clip by ${diff.toFixed(1)}s (freeze last frame)`);
    execSync(
      `ffmpeg -y -i "${clipPath}" -vf "tpad=stop_mode=clone:stop_duration=${diff.toFixed(2)}" -c:v libx264 -preset fast -crf 23 -an "${outputPath}"`,
      { stdio: 'pipe' }
    );
    return outputPath;
  } else {
    console.log(`    Trimming clip by ${Math.abs(diff).toFixed(1)}s`);
    execSync(
      `ffmpeg -y -i "${clipPath}" -t ${audioDuration.toFixed(2)} -c:v libx264 -preset fast -crf 23 -an "${outputPath}"`,
      { stdio: 'pipe' }
    );
    return outputPath;
  }
}

function generateSilentSegment(outputDir: string, filename: string, durationSeconds: number): Promise<string> {
  const outputPath = path.join(outputDir, filename);
  return new Promise((resolve, reject) => {
    ffmpeg()
      .input('anullsrc=r=44100:cl=mono')
      .inputFormat('lavfi')
      .duration(durationSeconds)
      .audioCodec('libmp3lame')
      .output(outputPath)
      .on('end', () => resolve(outputPath))
      .on('error', (err) => reject(new Error(`Silent audio generation failed: ${err.message}`)))
      .run();
  });
}

function concatenateAudio(audioPaths: string[], outputDir: string): Promise<string> {
  const outputPath = path.join(outputDir, 'voiceover.mp3');
  if (audioPaths.length === 1) {
    copyFileSync(audioPaths[0], outputPath);
    return Promise.resolve(outputPath);
  }
  return new Promise((resolve, reject) => {
    const inputLabels = audioPaths.map((_, i) => `[${i}:a]`).join('');
    const filter = `${inputLabels}concat=n=${audioPaths.length}:v=0:a=1[out]`;
    const cmd = ffmpeg();
    for (const p of audioPaths) {
      cmd.input(p);
    }
    cmd
      .complexFilter(filter)
      .outputOptions(['-map', '[out]'])
      .audioCodec('libmp3lame')
      .output(outputPath)
      .on('end', () => resolve(outputPath))
      .on('error', (err) => reject(new Error(`Audio concat failed: ${err.message}`)))
      .run();
  });
}

// ─── Color Fallback Clip ───

async function generateColorFallbackClip(
  outputDir: string,
  filename: string,
  config: RenderConfig,
  index: number,
  durationSeconds: number
): Promise<string> {
  // Generate a still image with brand colors
  const imgPath = path.join(outputDir, `fallback-still-${index}.png`);
  const colors = [config.brandColors.primary, config.brandColors.accent, config.brandColors.secondary];
  const hex = colors[index % colors.length].replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  await sharp({
    create: { width: 1080, height: 1920, channels: 3, background: { r, g, b } },
  }).png().toFile(imgPath);

  // Convert still to video clip at the required duration
  const videoPath = path.join(outputDir, filename);
  const frames = Math.ceil(durationSeconds * 25);
  execSync(
    `ffmpeg -y -loop 1 -i "${imgPath}" -c:v libx264 -t ${durationSeconds.toFixed(2)} -pix_fmt yuv420p -vf "scale=1080:1920,fps=25" -preset fast "${videoPath}"`,
    { stdio: 'pipe' }
  );

  return videoPath;
}

// ─── Segment Builder (v2) ───

function buildSegmentListV2(script: ReelScriptV2): ReelSegmentV2[] {
  const segments: ReelSegmentV2[] = [];

  segments.push({
    onScreenText: script.hook.onScreenText,
    voiceover: script.hook.voiceover,
    pexelsSearch: script.hook.pexelsSearch || [],
    targetDuration: 3,
    segmentType: 'hook',
  });

  for (const seg of script.segments) {
    segments.push({
      onScreenText: seg.onScreenText,
      voiceover: seg.voiceover,
      pexelsSearch: seg.pexelsSearch || [],
      targetDuration: seg.targetDuration || 4,
      segmentType: 'body',
    });
  }

  segments.push({
    onScreenText: script.cta.onScreenText,
    voiceover: script.cta.voiceover,
    pexelsSearch: script.cta.pexelsSearch || [],
    targetDuration: 4,
    segmentType: 'cta',
  });

  return segments;
}

// ─── Text Overlay Rendering ───

async function renderTextOverlays(
  segments: ReelSegmentV2[],
  config: RenderConfig,
  outputDir: string
): Promise<string[]> {
  const browser = await getBrowser();
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

  const paths: string[] = [];

  try {
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      const html = reelOverlayHtml(seg.onScreenText, config, seg.segmentType, i, segments.length);
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

// ─── Video Composition ───

function composeVideoV2(
  clipPaths: string[],
  overlayPaths: string[],
  segments: ReelSegmentV2[],
  segmentAudioPaths: string[],
  voiceoverPath: string,
  outputPath: string,
  outputDir: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    const segmentCount = segments.length;

    // Match each clip's duration to its corresponding audio segment
    console.log('  Matching clip durations to audio segments...');
    const matchedClips: string[] = [];
    for (let i = 0; i < segmentCount; i++) {
      const clipPath = clipPaths[i];
      const audioPath = segmentAudioPaths[i];
      if (audioPath && existsSync(audioPath) && clipPath.endsWith('.mp4')) {
        const audioDur = getMediaDuration(audioPath);
        if (audioDur > 0) {
          segments[i] = { ...segments[i], actualDuration: audioDur };
          const matchedPath = path.join(outputDir, `clip-${i}-matched.mp4`);
          try {
            matchedClips.push(matchClipToAudioDuration(clipPath, audioDur, matchedPath));
          } catch (err: any) {
            console.log(`    Match failed for segment ${i}: ${err.message}, keeping original`);
            matchedClips.push(clipPath);
          }
        } else {
          matchedClips.push(clipPath);
        }
      } else {
        matchedClips.push(clipPath);
      }
    }

    let filterComplex = '';
    const inputs: string[] = [];

    // Add all video inputs (use matched clips)
    for (let i = 0; i < segmentCount; i++) {
      inputs.push(matchedClips[i]);
    }
    // Add all overlay inputs
    for (let i = 0; i < segmentCount; i++) {
      inputs.push(overlayPaths[i]);
    }
    // Add voiceover
    inputs.push(voiceoverPath);

    // Build filter graph
    for (let i = 0; i < segmentCount; i++) {
      const dur = segments[i].actualDuration || segments[i].targetDuration;
      // Stock video clips — scale, fps-normalize, and trim
      filterComplex += `[${i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25,trim=duration=${dur},setpts=PTS-STARTPTS[bg${i}];`;
    }

    // Scale overlays
    for (let i = 0; i < segmentCount; i++) {
      const overlayIdx = segmentCount + i;
      filterComplex += `[${overlayIdx}:v]scale=1080:1920[ov${i}];`;
    }

    // Overlay text on video backgrounds
    for (let i = 0; i < segmentCount; i++) {
      filterComplex += `[bg${i}][ov${i}]overlay=0:0:format=auto[seg${i}];`;
    }

    // Apply crossfade transitions (0.3s dissolve)
    if (segmentCount > 1) {
      let cumulativeDuration = segments[0].actualDuration || segments[0].targetDuration;
      let prevLabel = 'seg0';
      for (let i = 1; i < segmentCount; i++) {
        const fadeOffset = cumulativeDuration - 0.3;
        const outLabel = i === segmentCount - 1 ? 'outv' : `xf${i}`;
        filterComplex += `[${prevLabel}][seg${i}]xfade=transition=fade:duration=0.3:offset=${fadeOffset.toFixed(2)}[${outLabel}];`;
        cumulativeDuration += (segments[i].actualDuration || segments[i].targetDuration) - 0.3;
        prevLabel = outLabel;
      }
    } else {
      filterComplex += `[seg0]copy[outv];`;
    }

    // Remove trailing semicolon
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
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-r', '25',
        '-shortest',
      ])
      .output(outputPath)
      .on('end', () => resolve())
      .on('error', (err) => reject(new Error(`ffmpeg error: ${err.message}`)))
      .run();
  });
}

// ─── Main Render Function (v2) ───

/**
 * Render a reel using Pexels stock video clips:
 * 1. Generate per-segment TTS (audio drives timing)
 * 2. Search & download Pexels video clips per segment
 * 3. Trim clips to match audio duration
 * 4. Puppeteer text overlays
 * 5. ffmpeg crossfade composition + audio
 */
export async function renderReelV2(
  script: ReelScriptV2,
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string> {
  const outputDir = path.join(CONFIG.paths.assets, `reel-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const allSegments = buildSegmentListV2(script);

  // ─── Step 1: Generate per-segment TTS (audio drives timing) ───
  console.log('  Generating per-segment voiceover...');
  const segmentAudioPaths: string[] = [];
  for (let i = 0; i < allSegments.length; i++) {
    const seg = allSegments[i];
    const voText = seg.voiceover || seg.onScreenText;
    const audioFile = `vo-${i}.mp3`;
    try {
      const audioPath = await generateSpeech(voText, outputDir, audioFile);
      segmentAudioPaths.push(audioPath);
      const audioDur = getMediaDuration(audioPath);
      if (audioDur > 0) {
        allSegments[i] = { ...seg, actualDuration: audioDur + 0.3 };
      }
      console.log(`    Segment ${i} (${seg.segmentType}): ${audioDur.toFixed(1)}s audio → ${(allSegments[i].actualDuration || seg.targetDuration).toFixed(1)}s visual`);
    } catch (err: any) {
      console.log(`    TTS failed for segment ${i}: ${err.message}, using ${seg.targetDuration}s silence`);
      const silentPath = await generateSilentSegment(outputDir, audioFile, seg.targetDuration);
      segmentAudioPaths.push(silentPath);
    }
  }

  // ─── Step 2: Search & download Pexels video clips ───
  console.log('  Downloading Pexels stock video clips...');
  const clipPaths: string[] = [];
  for (let i = 0; i < allSegments.length; i++) {
    const seg = allSegments[i];
    const clipDuration = seg.actualDuration || seg.targetDuration;
    const clipFile = `clip-${i}.mp4`;

    try {
      const result = await findAndDownloadVideoClip(
        seg.pexelsSearch,
        outputDir,
        clipFile,
        Math.max(2, clipDuration - 2),   // minDuration: allow slightly shorter clips
        clipDuration + 10,                 // maxDuration: allow longer clips (we'll trim)
        scriptId,
        i
      );
      clipPaths.push(result.path);
    } catch (err: any) {
      console.warn(`    Pexels clip ${i} failed: ${err.message}, generating color fallback`);
      const fallbackPath = await generateColorFallbackClip(outputDir, clipFile, renderConfig, i, clipDuration);
      clipPaths.push(fallbackPath);
    }
  }

  // ─── Step 3: Render text overlays ───
  console.log('  Rendering text overlays...');
  const overlayPaths = await renderTextOverlays(allSegments, renderConfig, outputDir);

  // ─── Step 4: Stitch audio ───
  console.log('  Stitching audio...');
  const voiceoverPath = await concatenateAudio(segmentAudioPaths, outputDir);

  // ─── Step 5: Compose final video ───
  console.log('  Composing video...');
  const totalDur = allSegments.reduce((s, seg) => s + (seg.actualDuration || seg.targetDuration), 0);
  console.log(`  Total reel: ${totalDur.toFixed(1)}s across ${allSegments.length} segments`);
  const outputPath = path.join(outputDir, 'reel.mp4');
  await composeVideoV2(clipPaths, overlayPaths, allSegments, segmentAudioPaths, voiceoverPath, outputPath, outputDir);

  return outputPath;
}

// ─── Script Parser (v2 with v1 backward compat) ───

function parseDurationFromTimestamp(timestamp: string | number): number | null {
  if (typeof timestamp === 'number') return timestamp > 0 ? timestamp : null;
  if (typeof timestamp !== 'string') return null;
  const mmss = timestamp.match(/(\d+):(\d+)\s*-\s*(\d+):(\d+)/);
  if (mmss) {
    const start = parseInt(mmss[1]) * 60 + parseInt(mmss[2]);
    const end = parseInt(mmss[3]) * 60 + parseInt(mmss[4]);
    return end - start;
  }
  const secs = timestamp.match(/([\d.]+)\s*s?\s*-\s*([\d.]+)\s*s?/);
  if (secs) {
    const dur = parseFloat(secs[2]) - parseFloat(secs[1]);
    if (dur > 0) return dur;
  }
  return null;
}

/**
 * Parse a content_scripts row's script_json into a ReelScriptV2.
 * Handles both v2 format (with reelFormat + pexelsSearch) and
 * backward-compatible v1 format (with sceneSetup + visualDescription).
 */
export function parseReelScriptV2(scriptJson: string): ReelScriptV2 {
  const parsed = JSON.parse(scriptJson);
  const reel = parsed.reelScript || parsed.reel || parsed;

  // Detect v2 format: has reelFormat field
  if (reel.reelFormat) {
    return parseV2Native(reel);
  }

  // Fall back to v1 conversion
  return convertV1ToV2(reel);
}

function parseV2Native(reel: any): ReelScriptV2 {
  const hookRaw = reel.hook || {};
  const ctaRaw = reel.cta || {};

  const segments = (reel.segments || reel.body || []).map((s: any) => ({
    onScreenText: s.onScreenText || s.text || '',
    voiceover: s.voiceover || s.voiceoverScript || s.text || '',
    pexelsSearch: Array.isArray(s.pexelsSearch) ? s.pexelsSearch : [],
    targetDuration: s.targetDuration || s.durationSeconds || 4,
    segmentType: 'body' as const,
  }));

  const caption = reel.caption || {};

  return {
    reelFormat: reel.reelFormat || 'deep_dive',
    hook: {
      onScreenText: typeof hookRaw === 'string' ? hookRaw : (hookRaw.onScreenText || hookRaw.text || ''),
      voiceover: typeof hookRaw === 'string' ? hookRaw : (hookRaw.voiceover || hookRaw.voiceoverScript || hookRaw.onScreenText || ''),
      pexelsSearch: Array.isArray(hookRaw.pexelsSearch) ? hookRaw.pexelsSearch : [],
    },
    segments,
    cta: {
      onScreenText: typeof ctaRaw === 'string' ? ctaRaw : (ctaRaw.onScreenText || ctaRaw.text || ''),
      voiceover: typeof ctaRaw === 'string' ? ctaRaw : (ctaRaw.voiceover || ctaRaw.voiceoverScript || ctaRaw.onScreenText || ''),
      pexelsSearch: Array.isArray(ctaRaw.pexelsSearch) ? ctaRaw.pexelsSearch : [],
    },
    caption: {
      hookLine: caption.hookLine || '',
      body: caption.body || '',
      cta: caption.cta || '',
      seoKeywords: Array.isArray(caption.seoKeywords) ? caption.seoKeywords : [],
      hashtags: Array.isArray(caption.hashtags) ? caption.hashtags : [],
    },
    dmTrigger: reel.dmTrigger || '',
    totalLength: reel.totalLength || 28,
    audioMood: reel.audioMood,
    voiceoverText: reel.voiceoverText,
  };
}

/**
 * Convert a v1 ReelScript (with visualDescription / sceneSetup) into a v2 format.
 * Uses the visualDescription as a Pexels search term fallback.
 */
function convertV1ToV2(reel: any): ReelScriptV2 {
  const hookRaw = reel.hook;
  const hook = typeof hookRaw === 'string' ? hookRaw : hookRaw?.onScreenText || hookRaw?.text || '';
  const ctaRaw = reel.cta;
  const cta = typeof ctaRaw === 'string' ? ctaRaw : ctaRaw?.onScreenText || ctaRaw?.text || '';

  const extractVO = (obj: any): string => {
    const raw = obj?.voiceover || obj?.voiceoverScript || obj?.audio || '';
    return raw.replace(/^[^:]*:\s*['"]?/, '').replace(/['"]?\s*$/, '');
  };

  const hookVoiceover = (typeof hookRaw === 'object') ? (extractVO(hookRaw) || hook) : hook;
  const ctaVoiceover = (typeof ctaRaw === 'object') ? (extractVO(ctaRaw) || cta) : cta;

  const hookVisual = typeof hookRaw === 'object' ? (hookRaw?.visual || hookRaw?.visualDescription || '') : '';
  const ctaVisual = typeof ctaRaw === 'object' ? (ctaRaw?.visual || ctaRaw?.visualDescription || '') : '';

  // Extract plant name from sceneSetup for better Pexels searches
  const plantName = reel.sceneSetup?.plant || '';
  const plantSearch = plantName ? [plantName, 'houseplant'] : ['houseplant close up'];

  const rawSegments = reel.segments || reel.body || [];

  const segments = rawSegments.map((s: any) => {
    const text = s.text || s.onScreenText || s.line || '';
    let durationSeconds: number | null = null;
    if (typeof s.durationSeconds === 'number') durationSeconds = s.durationSeconds;
    else if (typeof s.duration === 'number') durationSeconds = s.duration;
    if (durationSeconds === null && s.timestamp) {
      durationSeconds = parseDurationFromTimestamp(s.timestamp);
    }

    return {
      onScreenText: text,
      voiceover: extractVO(s) || text,
      pexelsSearch: s.visualDescription ? [s.visualDescription, ...plantSearch] : plantSearch,
      targetDuration: durationSeconds && durationSeconds > 0 ? durationSeconds : 4,
      segmentType: 'body' as const,
    };
  });

  const caption = reel.caption || {};

  console.log(`  Converted v1 reel to v2: hook="${hook.substring(0, 40)}...", ${segments.length} body segments`);

  return {
    reelFormat: 'deep_dive',
    hook: {
      onScreenText: hook,
      voiceover: hookVoiceover,
      pexelsSearch: hookVisual ? [hookVisual, ...plantSearch] : plantSearch,
    },
    segments,
    cta: {
      onScreenText: cta,
      voiceover: ctaVoiceover,
      pexelsSearch: ctaVisual ? [ctaVisual, ...plantSearch] : plantSearch,
    },
    caption: {
      hookLine: caption.hookLine || '',
      body: caption.body || '',
      cta: caption.cta || '',
      seoKeywords: Array.isArray(caption.seoKeywords) ? caption.seoKeywords : [],
      hashtags: Array.isArray(caption.hashtags) ? caption.hashtags : [],
    },
    dmTrigger: reel.dmTrigger || '',
    totalLength: reel.totalLength || 30,
    audioMood: reel.audioMood,
    voiceoverText: reel.voiceoverText,
  };
}
