// Photography vocabulary library for prompt engineering

export const LENS_TYPES = {
  macro: '100mm f/2.8 macro lens, 1:1 reproduction ratio',
  portrait: '85mm f/1.4 lens, creamy bokeh',
  wide: '24mm f/2.8 lens, environmental context',
  standard: '50mm f/1.8 lens, natural perspective',
  telephoto: '200mm f/4 lens, compressed perspective, background blur',
} as const;

export const LIGHTING = {
  windowLight: 'soft diffused window light from the left, gentle shadows',
  goldenHour: 'warm golden hour backlight, rim lighting on subject edges',
  overcast: 'even overcast daylight, no harsh shadows, soft and flat',
  studioSoft: 'studio softbox lighting, clean white background, even illumination',
  dramatic: 'single strong sidelight, deep shadows, chiaroscuro',
  practicalLight: 'warm tungsten desk lamp, cozy indoor ambience',
} as const;

export const DEPTH_OF_FIELD = {
  shallow: 'f/2.8, shallow depth of field, background melts into soft bokeh',
  moderate: 'f/5.6, subject sharp with gently blurred background',
  deep: 'f/11, everything in sharp focus from foreground to background',
} as const;

export const COLOR_PALETTES = {
  plantCare: 'rich greens, warm earth browns, soft terracotta, natural tones',
  clinical: 'clean whites, cool greens, sterile blue-green, medical precision',
  warm: 'golden amber, warm browns, sunset oranges, honey tones',
  moody: 'deep shadows, muted greens, dark earth, low-key dramatic',
  fresh: 'bright greens, clean whites, morning dew, high-key airy',
} as const;

export const FILM_STOCKS = {
  portra400: 'Kodak Portra 400 color profile, warm skin tones, pastel highlights',
  ektar100: 'Kodak Ektar 100, punchy saturated colors, fine grain',
  fujiPro400H: 'Fuji Pro 400H, cooler tones, subtle pastels, soft greens',
} as const;

export const TEXTURES = {
  soil: 'wet soil granules, dark humus, visible organic matter',
  leaf: 'waxy leaf surface, visible venation patterns, translucent edges',
  bark: 'rough bark texture, deep fissures, lichen patches',
  root: 'tangled white root fibers, root ball structure, mycelium threads',
  water: 'water droplets on leaves, condensation beads, morning dew',
  ceramic: 'terracotta pot surface, matte glaze, mineral deposits',
  trichome: 'fuzzy leaf trichomes, silvery surface hairs, soft velvet texture',
} as const;

export type LensType = keyof typeof LENS_TYPES;
export type LightingType = keyof typeof LIGHTING;
export type DOFType = keyof typeof DEPTH_OF_FIELD;
export type PaletteType = keyof typeof COLOR_PALETTES;
export type FilmStockType = keyof typeof FILM_STOCKS;
