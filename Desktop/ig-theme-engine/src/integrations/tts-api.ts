import OpenAI from 'openai';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
import { CONFIG } from '../config/env.js';

let client: OpenAI | null = null;

function getClient(): OpenAI {
  if (!client) {
    client = new OpenAI({ apiKey: CONFIG.openaiTts.apiKey });
  }
  return client;
}

/**
 * Generate speech audio from text via OpenAI TTS.
 * Returns the local file path of the MP3.
 */
export async function generateSpeech(
  text: string,
  outputDir: string,
  filename: string,
  voice: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer' = 'nova'
): Promise<string> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const openai = getClient();

  const response = await openai.audio.speech.create({
    model: 'tts-1',
    voice,
    input: text,
    response_format: 'mp3',
  });

  const outputPath = path.join(outputDir, filename);
  const buffer = Buffer.from(await response.arrayBuffer());
  await writeFile(outputPath, buffer);

  return outputPath;
}
