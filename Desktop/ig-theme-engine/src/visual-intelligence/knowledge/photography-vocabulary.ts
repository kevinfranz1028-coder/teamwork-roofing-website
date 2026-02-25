export const LENS_TYPES = {
  macro: { name: '100mm f/2.8 Macro', use: 'extreme close-ups of leaves, insects, soil, water droplets' },
  portrait: { name: '85mm f/1.4', use: 'single plant portraits, soft background blur' },
  wide: { name: '24mm f/2.8', use: 'room scenes, plant collections, shelf displays' },
  standard: { name: '50mm f/1.8', use: 'natural perspective, general plant shots' },
  telephoto: { name: '200mm f/2.8', use: 'compressed backgrounds, dramatic isolation' },
};

export const LIGHTING_STYLES = {
  windowLight: 'soft diffused north-facing window light',
  goldenHour: 'warm golden hour directional light with long shadows',
  overcast: 'soft even overcast daylight, no harsh shadows',
  studioSoft: 'studio softbox key light with fill, clean white',
  dramatic: 'single hard directional light with deep shadows',
  backlit: 'strong backlight with rim glow on leaves, translucent foliage',
  practicalLight: 'warm tungsten lamp light, cozy indoor ambiance',
};

export const DEPTH_OF_FIELD = {
  ultraShallow: 'f/1.4 — razor thin focus plane, extreme bokeh',
  shallow: 'f/2.8 — subject sharp, background beautifully blurred',
  moderate: 'f/5.6 — subject and immediate area sharp, soft background',
  deep: 'f/11 — most of scene in focus, environmental context',
};

export const COLOR_PALETTES = {
  plantCare: 'rich greens, warm browns, soft terracotta, natural earth tones',
  clinical: 'clean whites, pale greens, minimal, medical precision',
  warm: 'golden ambers, warm greens, honey tones, sunset warmth',
  moody: 'deep shadows, muted greens, dark earth, dramatic contrast',
  fresh: 'bright greens, crisp whites, light blues, morning dew freshness',
};

export const FILM_STOCKS = {
  portra400: 'Kodak Portra 400 — warm skin tones, soft pastels, creamy highlights',
  ektar100: 'Kodak Ektar 100 — ultra saturated, punchy colors, fine grain',
  fujiPro400H: 'Fuji Pro 400H — cool greens, soft pastels, ethereal quality',
  velvia50: 'Fuji Velvia 50 — extreme saturation, vivid greens, slide film punch',
};
