import { fal } from '@fal-ai/client';
import { writeFile } from 'fs/promises';
import path from 'path';
import { existsSync, mkdirSync } from 'fs';
import { CONFIG } from '../config/env.js';
import { logApiCost } from '../utils/cost-tracker.js';

const VOICE_MAP: Record<string, string> = {
  alloy: 'Rachel',
  echo: 'Drew',
  fable: 'Rachel',
  onyx: 'Drew',
  nova: 'Rachel',
  shimmer: 'Rachel',
};

export async function generateSpeech(
  text: string,
  outputDir: string,
  filename: string = 'voiceover.mp3',
  voice: string = 'alloy'
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, filename);

  try {
    const falKey = CONFIG.fal.apiKey;
    if (!falKey) throw new Error('FAL_API_KEY not set');
    fal.config({ credentials: falKey });

    const elevenLabsVoice = VOICE_MAP[voice] || 'Rachel';
    console.log(`  TTS: Generating via ElevenLabs (${elevenLabsVoice}) on fal.ai...`);

    const result = await fal.subscribe('fal-ai/elevenlabs/tts/turbo-v2.5', {
      input: { text, voice: elevenLabsVoice },
    }) as any;

    const audioUrl = result?.data?.audio_url || result?.audio_url || result?.data?.audio?.url;
    if (!audioUrl) {
      console.error('  TTS: No audio URL in fal response, falling back to OpenAI...');
      return generateSpeechOpenAI(text, outputDir, filename, voice);
    }

    const response = await fetch(audioUrl);
    if (!response.ok) throw new Error(`Download failed: ${response.status}`);
    const buffer = Buffer.from(await response.arrayBuffer());
    await writeFile(outputPath, buffer);
    console.log(`  TTS: ElevenLabs audio saved (${(buffer.length / 1024).toFixed(0)}KB)`);

    const charCount = text.length;
    logApiCost({
      provider: 'fal',
      category: 'tts',
      endpoint: 'fal-ai/elevenlabs/tts/turbo-v2.5',
      model: 'elevenlabs-turbo-v2.5',
      description: `TTS: ${text.slice(0, 60)}`,
      estimatedCost: (charCount / 1000) * 0.030,
    });

    return outputPath;

  } catch (err: any) {
    console.error(`  TTS: ElevenLabs failed (${err.message}), falling back to OpenAI tts-1-hd...`);
    return generateSpeechOpenAI(text, outputDir, filename, voice);
  }
}

async function generateSpeechOpenAI(
  text: string, outputDir: string, filename: string, voice: string
): Promise<string> {
  const OpenAI = (await import('openai')).default;
  const openai = new OpenAI({ apiKey: CONFIG.openaiTts.apiKey });
  const outputPath = path.join(outputDir, filename);
  const mp3 = await openai.audio.speech.create({
    model: 'tts-1-hd',
    voice: (voice as any) || 'alloy',
    input: text,
  });
  const buffer = Buffer.from(await mp3.arrayBuffer());
  await writeFile(outputPath, buffer);
  console.log(`  TTS: OpenAI fallback saved (${(buffer.length / 1024).toFixed(0)}KB)`);

  const charCount = text.length;
  logApiCost({
    provider: 'openai',
    category: 'tts',
    endpoint: 'audio.speech.create',
    model: 'tts-1-hd',
    description: `TTS fallback: ${text.slice(0, 60)}`,
    estimatedCost: (charCount / 1000) * 0.030,
  });

  return outputPath;
}
