// ─── Visual Intelligence Layer — Type Definitions ───

export type ImageModel = 'flux-2-pro' | 'gpt-image-1.5' | 'ideogram-3';
export type VideoModel = 'kling-2.5-turbo-pro';
export type SegmentType = 'hook' | 'body' | 'cta';
export type ContentType = 'carousel' | 'reel' | 'story';
export type AspectRatio = '9:16' | '1:1' | '16:9';

export interface VisualBrief {
  contentType: ContentType;
  segmentType: SegmentType;
  segmentIndex: number;
  totalSegments: number;
  onScreenText: string;
  voiceoverText?: string;
  originalVisualDescription: string;
  brandContext: {
    niche: string;
    stylePrefix: string;
    colorPalette: string[];
    mood: string;
  };
}

export interface VisualPlan {
  model: ImageModel;
  prompt: string;
  negativePrompt: string;
  aspectRatio: AspectRatio;
  generateVideo: boolean;
  motionPrompt?: string;
  motionStyle?: string;
  lens?: string;
  lighting?: string;
  depthOfField?: string;
  colorPalette?: string;
}

export interface GeneratedImage {
  path: string;
  model: string;
  prompt: string;
  qualityScore?: number;
  retryCount: number;
}

export interface GeneratedVideo {
  path: string;
  model: string;
  durationSeconds: number;
  fromImage: boolean;
}

export interface QualityReport {
  score: number;
  pass: boolean;
  issues: string[];
  feedback: string;
  checks: {
    noGarbledText: boolean;
    noCollage: boolean;
    noBlackBars: boolean;
    subjectClarity: boolean;
    brandAlignment: boolean;
  };
}

export interface StyleAnchor {
  imageStylePrefix: string;
  imageNegativePrompt: string;
  videoMotionStyle: string;
  hookVisualStyle: string;
  bodyVisualStyle: string;
  ctaVisualStyle: string;
  cameraBody: string;
  defaultLens: string;
  defaultLighting: string;
  defaultColorProfile: string;
}
