// Per-model DO and DON'T rules for prompt engineering

export const MODEL_RULES = {
  universal: {
    never: [
      'NEVER include text, words, numbers, or letters in image prompts',
      'NEVER ask for clocks, timers, watches, or time displays',
      'NEVER ask for product packaging with brand names or labels',
      'NEVER ask for collages, split screens, or multi-panel layouts',
      'NEVER ask for UI elements, buttons, or digital interfaces',
      'NEVER ask for multiple distinct scenes in one image',
      'NEVER use abstract concepts as visual descriptions',
      'ALL text content goes exclusively in the HTML overlay layer',
    ],
    always: [
      'ALWAYS describe ONE scene from ONE camera angle',
      'ALWAYS include lens focal length in the prompt',
      'ALWAYS include lighting direction and quality',
      'ALWAYS include depth of field specification',
      'ALWAYS include color palette description',
      'ALWAYS include a specific texture or material detail',
      'ALWAYS start with the image style prefix from AI Settings',
    ],
  },

  'flux-2-pro': {
    additional: [
      'Add "editorial quality, magazine photography" for polish boost',
      'Specify a film stock for consistent color grading',
      'Use "shot on Canon R5" or similar for camera realism cue',
      'For macro shots, add "1:1 reproduction, ring flash fill"',
      'Avoid overly complex scene descriptions (keep to 2-3 elements max)',
    ],
  },

  'gpt-image-1.5': {
    additional: [
      'Can handle longer, more detailed prompts (up to 4000 chars)',
      'Specify exact text to render in double quotes within prompt',
      'Describe spatial layout explicitly when multiple elements present',
      'Add "professional product photography, e-commerce quality" for products',
    ],
  },

  'ideogram-3': {
    additional: [
      "Put text to render in single quotes: 'Your Text Here'",
      'Describe the font style: "bold sans-serif", "elegant script", etc.',
      'Add "graphic design layout" or "poster design" for typography-first images',
    ],
  },
} as const;
