import type { ImageModel } from '../types.js';

export interface ModelCapability {
  id: ImageModel;
  name: string;
  strengths: string[];
  weaknesses: string[];
  bestFor: string[];
  costPerImage: number;
  avgGenerationSeconds: number;
  maxPromptLength: number;
  supportsNegativePrompt: boolean;
}

export const MODEL_REGISTRY: Record<ImageModel, ModelCapability> = {
  'flux-2-pro': {
    id: 'flux-2-pro',
    name: 'FLUX 2 Pro',
    strengths: ['photorealism', 'nature photography', 'macro detail', 'atmospheric lighting', 'film stock emulation'],
    weaknesses: ['text rendering (improved but imperfect)', 'specific product reproduction'],
    bestFor: ['plant close-ups', 'nature scenes', 'macro photography', 'atmospheric/mood shots', 'editorial content'],
    costPerImage: 0.03,
    avgGenerationSeconds: 6,
    maxPromptLength: 2000,
    supportsNegativePrompt: false,
  },
  'gpt-image-1.5': {
    id: 'gpt-image-1.5',
    name: 'GPT Image 1.5',
    strengths: ['text rendering', 'complex compositions', 'photorealism', 'instruction following', 'spatial layout'],
    weaknesses: ['slightly slower', 'higher cost', 'can over-process artistic intent'],
    bestFor: ['images requiring text', 'product photography', 'multi-element scenes', 'precise compositions'],
    costPerImage: 0.06,
    avgGenerationSeconds: 12,
    maxPromptLength: 4000,
    supportsNegativePrompt: false,
  },
  'ideogram-3': {
    id: 'ideogram-3',
    name: 'Ideogram 3.0',
    strengths: ['typography', 'text accuracy', 'graphic design', 'poster aesthetics'],
    weaknesses: ['less photorealistic', 'weaker at pure nature photography', 'stylized look'],
    bestFor: ['typography-heavy designs', 'social cards', 'quote graphics', 'branded content'],
    costPerImage: 0.05,
    avgGenerationSeconds: 10,
    maxPromptLength: 2000,
    supportsNegativePrompt: true,
  },
};

export function getModelCapability(model: ImageModel): ModelCapability {
  return MODEL_REGISTRY[model];
}
