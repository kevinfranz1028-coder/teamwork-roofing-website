// Tested prompt structures per content type
// These are enhanced over time by the self-learning quality loop

export const PROMPT_TEMPLATES = {
  carousel: {
    hook: '{stylePrefix}, {visualDescription}, {hookStyle}, {lens}, {lighting}, {dof}, {colorPalette}, {filmStock}, {suffix}',
    body: '{stylePrefix}, {visualDescription}, {bodyStyle}, {lens}, {lighting}, {dof}, {colorPalette}, {filmStock}, {suffix}',
    cta: '{stylePrefix}, {visualDescription}, {ctaStyle}, {lens}, {lighting}, {dof}, {colorPalette}, {filmStock}, {suffix}',
  },
  reel: {
    hook: '{stylePrefix}, {visualDescription}, {hookStyle}, dramatic angle, {lens}, {lighting}, {dof}, {colorPalette}, {filmStock}, {suffix}',
    body: '{stylePrefix}, {visualDescription}, {bodyStyle}, {lens}, {lighting}, {dof}, {colorPalette}, {filmStock}, {suffix}',
    cta: '{stylePrefix}, {visualDescription}, {ctaStyle}, uplifting, {lens}, {lighting}, {dof}, {colorPalette}, {filmStock}, {suffix}',
  },
  story: {
    hook: '{stylePrefix}, {visualDescription}, vertical 9:16 composition, {hookStyle}, {lens}, {lighting}, {dof}, {colorPalette}, {suffix}',
    body: '{stylePrefix}, {visualDescription}, vertical 9:16 composition, {bodyStyle}, {lens}, {lighting}, {dof}, {colorPalette}, {suffix}',
    cta: '{stylePrefix}, {visualDescription}, vertical 9:16 composition, {ctaStyle}, {lens}, {lighting}, {dof}, {colorPalette}, {suffix}',
  },
} as const;

export const VIDEO_MOTION_TEMPLATES = {
  hook: 'dramatic slow reveal, camera slowly pushes in, shallow depth of field, {motionStyle}',
  body: 'gentle organic motion, {motionDescription}, {motionStyle}',
  cta: 'warm, inviting, slow dolly out, soft focus shift, {motionStyle}',
} as const;
