// Model capabilities, costs, and routing rules
import type { ModelCapabilities } from '../types.js';

export const MODEL_REGISTRY: Record<string, ModelCapabilities> = {
  'flux-2-pro': {
    name: 'FLUX 2 Pro',
    provider: 'Replicate',
    costPerImage: 0.03,
    speedSeconds: 6,
    strengths: [
      'Photorealistic nature/plant photography',
      'Atmospheric lighting and bokeh',
      'Macro close-ups with texture detail',
      'Single-subject compositions',
      'Consistent 9:16 and 1:1 aspect ratios',
    ],
    weaknesses: [
      'Text rendering improved but not reliable for body copy',
      'Can over-sharpen details',
      'Complex multi-element scenes sometimes merge objects',
    ],
    absoluteNever: [
      'Product packaging with brand names',
      'Readable text longer than 2 words',
      'Multi-panel or collage layouts',
      'UI mockups or interface elements',
      'Clock faces or digital displays',
    ],
    promptTips: [
      'Include lens focal length (85mm, 100mm macro, 35mm)',
      'Specify lighting direction explicitly',
      'Use "editorial" or "magazine" to boost polish',
      'Add film stock reference for color grading (Portra 400, Kodachrome)',
    ],
    aspectRatios: ['9:16', '1:1', '16:9', '4:5', '3:2'],
  },

  'gpt-image-1.5': {
    name: 'GPT Image 1.5',
    provider: 'OpenAI',
    costPerImage: 0.06,
    speedSeconds: 12,
    strengths: [
      'Best-in-class text rendering',
      'Highest prompt adherence',
      'Multi-element compositions with spatial relationships',
      'Product photography with readable packaging',
      'Infographic-style images',
    ],
    weaknesses: [
      'Slightly less cinematic than FLUX for pure photography',
      'Slower generation',
      'Higher cost per image',
    ],
    absoluteNever: [
      'Copyrighted brand logos',
    ],
    promptTips: [
      'Be extremely specific — this model follows long, detailed prompts well',
      'Specify exact text to render in quotes',
      'Describe spatial layout explicitly',
    ],
    aspectRatios: ['1024x1024', '1024x1792', '1792x1024'],
  },

  'ideogram-3': {
    name: 'Ideogram 3.0',
    provider: 'Ideogram',
    costPerImage: 0.05,
    speedSeconds: 10,
    strengths: [
      'Industry-leading typography rendering',
      'Poster and graphic design aesthetics',
      'Reliable multi-line text layout',
      'Style reference support',
    ],
    weaknesses: [
      'General photorealism behind FLUX and GPT Image',
      'Smaller community, less prompt documentation',
    ],
    absoluteNever: [],
    promptTips: [
      "Specify exact text in single quotes within prompt",
      'Describe font style: serif, sans-serif, handwritten',
      'Use "graphic design" or "poster layout" for designed compositions',
    ],
    aspectRatios: ['ASPECT_1_1', 'ASPECT_9_16', 'ASPECT_16_9', 'ASPECT_4_5'],
  },

  'kling-2.6-pro': {
    name: 'Kling 2.6 Pro (Image-to-Video)',
    provider: 'fal.ai',
    costPerSecond: 0.07,
    speedSeconds: 120,
    strengths: [
      'Cinematic image-to-video transformation',
      'Excellent physics simulation (leaves, water, light, insects)',
      'Natural camera motion (pan, tilt, parallax)',
      'Character/subject consistency from source image',
      '9:16 vertical video natively supported',
    ],
    weaknesses: [
      'Complex multi-character scenes can lose consistency after 5s',
      'Generation takes 1-3 minutes per clip',
    ],
    absoluteNever: [
      'Never enable native audio (we use OpenAI TTS separately)',
      'Never generate longer than 5s per segment (stitch instead)',
    ],
    promptTips: [
      'Describe the MOTION, not the scene (scene is in the source image)',
      'Use: "gentle breeze moves leaves", "camera slowly pushes in"',
      'Keep motion descriptions simple',
      'Add "smooth, cinematic, 24fps" for professional feel',
    ],
    aspectRatios: ['9:16', '16:9', '1:1'],
  },
};
