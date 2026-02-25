export const UNIVERSAL_NEVER = [
  'NEVER include text, words, letters, or numbers in the image',
  'NEVER include clocks, watches, timers, or time indicators',
  'NEVER include product labels, brand names, or logos',
  'NEVER create collages, split screens, or multiple panels',
  'NEVER include UI elements, buttons, or interface components',
  'NEVER include black bars, padding, or empty space',
  'NEVER include cartoon or illustration styles — photorealism only',
];

export const UNIVERSAL_ALWAYS = [
  'ALWAYS describe ONE single scene from ONE camera angle',
  'ALWAYS specify a lens focal length and aperture',
  'ALWAYS specify lighting direction and quality',
  'ALWAYS specify depth of field',
  'ALWAYS specify a color palette or film stock',
  'ALWAYS include at least one texture detail (leaf veins, soil grains, water droplets)',
];

export const MODEL_TIPS: Record<string, string[]> = {
  'flux-2-pro': [
    'Add "editorial quality, magazine photography" to boost realism',
    'Specify a film stock for color science (e.g., "Kodak Portra 400")',
    'Mention a camera model (e.g., "shot on Canon R5")',
    'Use prompt_upsampling for enhanced detail',
    'Excellent at nature, plants, macro detail, atmospheric lighting',
  ],
  'gpt-image-1.5': [
    'Can handle prompts up to 4000 characters — be detailed',
    'If text MUST appear, put it in exact quotes: \'the text "PLANT CARE"\' ',
    'Describe spatial layout precisely for complex scenes',
    'Best for: photorealism, text-in-image, multi-element compositions',
  ],
  'ideogram-3': [
    'Put desired text in single quotes in the prompt',
    'Describe font style explicitly (bold sans-serif, hand-lettered, etc.)',
    'Add "graphic design layout" for poster/card aesthetics',
    'Best for: typography, posters, social cards with text as the hero',
  ],
};
