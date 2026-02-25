import path from 'path';
import { mkdirSync, existsSync, copyFileSync } from 'fs';
import { execSync } from 'child_process';
import ffmpeg from 'fluent-ffmpeg';
import ffmpegInstaller from '@ffmpeg-installer/ffmpeg';
import sharp from 'sharp';
import { getBrowser } from './browser-pool.js';
import { reelOverlayHtml } from './templates.js';
import { generateSpeech } from '../integrations/tts-api.js';
import type { ReelScript, ReelSegment, RenderConfig } from './types.js';
import type { VisualBrief, VisualPlan } from '../visual-intelligence/types.js';
import { planVisualsBatch, retryPlan } from '../visual-intelligence/creative-director.js';
import { generateImage } from '../visual-intelligence/image-router.js';
import { generateVideo } from '../visual-intelligence/video-router.js';
import { getStyleAnchor } from '../visual-intelligence/knowledge/style-anchors.js';
import { CONFIG } from '../config/env.js';
import { getActiveAISettings } from '../config/ai-settings.js';

ffmpeg.setFfmpegPath(ffmpegInstaller.path);

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

/**
 * Render a reel as an MP4 video using the Visual Intelligence Layer:
 * 1. Creative Director plans visuals for ALL segments at once
 * 2. Generate per-segment TTS FIRST (audio drives timing)
 * 3. For each segment: generate still → quality gate → video → text overlay
 * 4. Compose video with crossfade transitions + audio
 */
export async function renderReel(
  script: ReelScript,
  renderConfig: RenderConfig,
  scriptId: number
): Promise<string> {
  const outputDir = path.join(CONFIG.paths.assets, `reel-${scriptId}`);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const allSegments = buildSegmentList(script);

  // ─── Step 1: Creative Director plans visuals ───
  console.log('  Creative Director planning visuals...');
  const briefs = buildVisualBriefs(allSegments, script, renderConfig);
  const plans = await planVisualsBatch(briefs);
  console.log(`  Creative Director planned ${plans.length} segments`);

  // ─── Step 2: Generate per-segment TTS (audio drives timing) ───
  console.log('  Generating per-segment voiceover...');
  const segmentAudioPaths: string[] = [];
  for (let i = 0; i < allSegments.length; i++) {
    const seg = allSegments[i];
    const voText = seg.voiceoverText || seg.text;
    const audioFile = `vo-${i}.mp3`;
    try {
      const audioPath = await generateSpeech(voText, outputDir, audioFile);
      segmentAudioPaths.push(audioPath);
      const audioDur = getMediaDuration(audioPath);
      if (audioDur > 0) {
        allSegments[i] = { ...seg, durationSeconds: audioDur + 0.3 };
      }
      console.log(`    Segment ${i} (${seg.segmentType}): ${audioDur.toFixed(1)}s audio → ${allSegments[i].durationSeconds.toFixed(1)}s visual`);
    } catch (err: any) {
      console.log(`    TTS failed for segment ${i}: ${err.message}, using ${seg.durationSeconds}s silence`);
      const silentPath = await generateSilentSegment(outputDir, audioFile, seg.durationSeconds);
      segmentAudioPaths.push(silentPath);
    }
  }

  // ─── Step 3: Generate visuals (PARALLEL) ───
  const aiSettings = getActiveAISettings() as any;
  const isVideoEnabled = (aiSettings?.enable_video_generation ?? (process.env.ENABLE_VIDEO_GENERATION !== 'false'))
    && !!process.env.FAL_API_KEY;
  console.log(`  Video generation: ${isVideoEnabled ? 'ENABLED' : 'DISABLED'} (FAL_API_KEY: ${process.env.FAL_API_KEY ? 'set' : 'NOT SET'})`);

  // Apply generateVideo overrides before parallel dispatch
  for (let i = 0; i < allSegments.length; i++) {
    const plan = plans[i];
    if (isVideoEnabled && !plan.generateVideo) {
      console.log(`  Segment ${i} — Creative Director set generateVideo=false, overriding to true for reel`);
      plan.generateVideo = true;
    }
    console.log(`  Segment ${i} — model: ${plan.model}, generateVideo: ${plan.generateVideo}, prompt: "${plan.prompt?.slice(0, 80)}..."`);
  }

  // 3a. Generate ALL still images in parallel
  console.log(`  Generating ${allSegments.length} stills in parallel...`);
  const imageStartTime = Date.now();
  const images = await Promise.all(
    plans.map((plan, i) => {
      console.log(`  Segment ${i} — dispatching still image generation...`);
      return generateImage(plan, briefs[i], outputDir, `still-${i}.png`);
    })
  );
  console.log(`  All ${images.length} stills generated in ${((Date.now() - imageStartTime) / 1000).toFixed(1)}s`);

  // 3b. Generate ALL video clips in parallel (if enabled)
  let videoClipPaths: string[];
  if (isVideoEnabled) {
    console.log(`  Generating ${allSegments.length} Kling video clips in parallel...`);
    const videoStartTime = Date.now();
    const videos = await Promise.all(
      images.map((image, i) => {
        if (plans[i].generateVideo) {
          console.log(`  Segment ${i} — dispatching Kling video generation...`);
          return generateVideo(image.path, plans[i], outputDir, `clip-${i}.mp4`);
        }
        return Promise.resolve({ path: image.path, model: 'still-fallback' as const, durationSeconds: 0, fromImage: false });
      })
    );
    videoClipPaths = videos.map((v, i) => {
      if (v.model === 'still-fallback') {
        console.log(`  Segment ${i} — using still image (video skipped or fell back)`);
      } else {
        console.log(`  Segment ${i} — Kling video generated: ${v.model}, ${v.durationSeconds}s`);
      }
      return v.path;
    });
    console.log(`  All ${videos.length} video clips generated in ${((Date.now() - videoStartTime) / 1000).toFixed(1)}s`);
  } else {
    console.log(`  Video disabled — using still images for all segments`);
    videoClipPaths = images.map(img => img.path);
  }

  // ─── Step 4: Render text overlays ───
  console.log('  Rendering text overlays...');
  const overlayPaths = await renderTextOverlays(allSegments, renderConfig, outputDir);

  // ─── Step 5: Stitch audio ───
  console.log('  Stitching audio...');
  const voiceoverPath = await concatenateAudio(segmentAudioPaths, outputDir);

  // ─── Step 6: Compose final video ───
  console.log('  Composing video...');
  const totalDur = allSegments.reduce((s, seg) => s + seg.durationSeconds, 0);
  console.log(`  Total reel: ${totalDur.toFixed(1)}s across ${allSegments.length} segments`);
  const outputPath = path.join(outputDir, 'reel.mp4');
  await composeVideo(videoClipPaths, overlayPaths, allSegments, segmentAudioPaths, voiceoverPath, outputPath, outputDir, isVideoEnabled);

  return outputPath;
}

// ─── Visual Brief Builder ───

function buildVisualBriefs(
  segments: ReelSegment[],
  script: ReelScript,
  config: RenderConfig
): VisualBrief[] {
  const anchor = getStyleAnchor();
  const sceneStr = script.sceneSetup
    ? `Scene context: ${script.sceneSetup.plant} in ${script.sceneSetup.pot}, ${script.sceneSetup.setting}, ${script.sceneSetup.lighting}, showing ${script.sceneSetup.condition}. `
    : '';

  if (sceneStr) {
    console.log(`  Visual briefs anchored to scene: plant=${script.sceneSetup!.plant}, setting=${script.sceneSetup!.setting}`);
  }

  return segments.map((seg, i) => ({
    contentType: 'reel' as const,
    segmentType: seg.segmentType || 'body',
    segmentIndex: i,
    totalSegments: segments.length,
    onScreenText: seg.text,
    voiceoverText: seg.voiceoverText || seg.text,
    originalVisualDescription: sceneStr + (seg.visualDescription || `professional ${CONFIG.app.niche} visual`),
    brandContext: {
      niche: CONFIG.app.niche || 'Houseplant ICU',
      stylePrefix: anchor.imageStylePrefix,
      colorPalette: [config.brandColors.primary, config.brandColors.secondary, config.brandColors.accent],
      mood: seg.segmentType === 'hook' ? 'dramatic' : seg.segmentType === 'cta' ? 'warm, inviting' : 'informative',
    },
  }));
}

// ─── Segment Builder ───

function buildSegmentList(script: ReelScript): ReelSegment[] {
  const segments: ReelSegment[] = [];

  segments.push({
    text: script.hook,
    voiceoverText: script.hookVoiceover || script.hook,
    durationSeconds: script.hookDuration || 3,
    visualDescription: script.hookVisual || 'attention-grabbing dramatic visual',
    segmentType: 'hook',
  });

  for (const seg of script.segments) {
    segments.push({ ...seg, segmentType: seg.segmentType || 'body' });
  }

  segments.push({
    text: script.cta,
    voiceoverText: script.ctaVoiceover || script.cta,
    durationSeconds: script.ctaDuration || 4,
    visualDescription: script.ctaVisual || 'call to action motivational visual',
    segmentType: 'cta',
  });

  return segments;
}

// ─── Audio Helpers ───

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

// ─── Text Overlay Rendering ───

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
      const seg = segments[i];
      const segType = seg.segmentType || 'body';
      const html = reelOverlayHtml(seg.text, config, segType, i, segments.length);
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

function composeVideo(
  clipPaths: string[],
  overlayPaths: string[],
  segments: ReelSegment[],
  segmentAudioPaths: string[],
  voiceoverPath: string,
  outputPath: string,
  outputDir: string,
  hasVideoClips: boolean
): Promise<void> {
  return new Promise((resolve, reject) => {
    const segmentCount = segments.length;

    // ─── Match each clip's duration to its corresponding audio segment ───
    console.log('  Matching clip durations to audio segments...');
    const matchedClips: string[] = [];
    for (let i = 0; i < segmentCount; i++) {
      const clipPath = clipPaths[i];
      const audioPath = segmentAudioPaths[i];
      if (audioPath && existsSync(audioPath) && clipPath.endsWith('.mp4')) {
        const audioDur = getMediaDuration(audioPath);
        if (audioDur > 0) {
          // Update segment duration to exact audio duration for accurate filter graph timing
          segments[i] = { ...segments[i], durationSeconds: audioDur };
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

    // Add all video/image inputs (use matched clips)
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
      const dur = segments[i].durationSeconds;
      const frames = dur * 25;
      const clipIsVideo = hasVideoClips && matchedClips[i].endsWith('.mp4');

      if (clipIsVideo) {
        // Video clip — already duration-matched; scale, fps-normalize, and trim as safety net
        filterComplex += `[${i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25,trim=duration=${dur},setpts=PTS-STARTPTS[bg${i}];`;
      } else {
        // Still image — use zoompan (Ken Burns) to generate video frames
        filterComplex += `[${i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,zoompan=z='min(zoom+0.0005,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${frames}:s=1080x1920:fps=25,setpts=PTS-STARTPTS[bg${i}];`;
      }
    }

    // Scale overlays
    for (let i = 0; i < segmentCount; i++) {
      const overlayIdx = segmentCount + i;
      filterComplex += `[${overlayIdx}:v]scale=1080:1920[ov${i}];`;
    }

    // Overlay text on video/backgrounds
    for (let i = 0; i < segmentCount; i++) {
      filterComplex += `[bg${i}][ov${i}]overlay=0:0:format=auto[seg${i}];`;
    }

    // Apply crossfade transitions (0.3s dissolve)
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

// ─── Gradient Fallback ───

async function generateGradientBackground(
  outputDir: string,
  filename: string,
  config: RenderConfig,
  index: number
): Promise<string> {
  const outputPath = path.join(outputDir, filename);
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

// ─── Timestamp Parsing ───

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
 * Parse a content_scripts row's script_json into a ReelScript.
 */
export function parseReelScript(scriptJson: string): ReelScript {
  const parsed = JSON.parse(scriptJson);
  const reel = parsed.reelScript || parsed.reel || parsed;

  if ((reel.body || reel.segments || []).length === 0) {
    console.warn('  WARNING: No body segments found in reel script! Check script JSON wrapper key. Tried: parsed.reelScript, parsed.reel, parsed');
  }

  const hookRaw = reel.hook;
  const hook = typeof hookRaw === 'string' ? hookRaw : hookRaw?.onScreenText || hookRaw?.text || '';
  const ctaRaw = reel.cta;
  const cta = typeof ctaRaw === 'string' ? ctaRaw : ctaRaw?.onScreenText || ctaRaw?.text || '';

  const hookDuration = (typeof hookRaw === 'object' && hookRaw?.timestamp)
    ? parseDurationFromTimestamp(hookRaw.timestamp) ?? 3 : 3;
  const ctaDuration = (typeof ctaRaw === 'object' && ctaRaw?.timestamp)
    ? parseDurationFromTimestamp(ctaRaw.timestamp) ?? 4 : 4;

  const rawSegments = reel.segments || reel.body || [];

  const extractVO = (obj: any): string => {
    const raw = obj?.voiceover || obj?.voiceoverScript || obj?.audio || '';
    return raw.replace(/^[^:]*:\s*['"]?/, '').replace(/['"]?\s*$/, '');
  };

  const segments = rawSegments.map((s: any) => {
    const text = s.text || s.onScreenText || s.line || '';
    let durationSeconds: number | null = null;
    if (typeof s.durationSeconds === 'number') durationSeconds = s.durationSeconds;
    else if (typeof s.duration === 'number') durationSeconds = s.duration;
    if (durationSeconds === null && s.timestamp) {
      durationSeconds = parseDurationFromTimestamp(s.timestamp);
    }
    const voiceoverText = extractVO(s) || text;

    return {
      text,
      voiceoverText,
      durationSeconds: durationSeconds && durationSeconds > 0 ? durationSeconds : 4,
      visualDescription: s.visualDescription || s.visual || '',
      segmentType: s.segmentType || 'body',
    };
  });

  const hookVoiceover = (typeof hookRaw === 'object') ? (extractVO(hookRaw) || hook) : hook;
  const ctaVoiceover = (typeof ctaRaw === 'object') ? (extractVO(ctaRaw) || cta) : cta;
  const voiceoverParts = [hookVoiceover, ...segments.map((s: any) => s.voiceoverText || s.text), ctaVoiceover];
  const voiceoverText = reel.voiceoverText || voiceoverParts.join('. ') || '';

  const hookVisual = typeof hookRaw === 'object' ? (hookRaw?.visual || hookRaw?.visualDescription || '') : '';
  const ctaVisual = typeof ctaRaw === 'object' ? (ctaRaw?.visual || ctaRaw?.visualDescription || '') : '';

  // Extract sceneSetup for visual consistency
  const sceneSetup = reel.sceneSetup || null;
  if (sceneSetup) {
    console.log(`  sceneSetup: plant=${sceneSetup.plant}, setting=${sceneSetup.setting}`);
  } else {
    console.warn('  ⚠️ No sceneSetup found in reel script — visual continuity will be degraded');
  }

  console.log(`  Parsed reel: hook="${hook.substring(0, 40)}...", ${segments.length} body segments, cta="${cta.substring(0, 40)}..."`);
  if (segments.length === 0) {
    console.warn('  ⚠️ Zero body segments parsed from reel script!');
  }

  return {
    hook,
    hookVisual,
    hookDuration,
    hookVoiceover,
    segments,
    cta,
    ctaVisual,
    ctaDuration,
    ctaVoiceover,
    totalLength: reel.totalLength || 30,
    voiceoverText,
    sceneSetup,
  };
}
