// Visual Intelligence Layer — Core Types

export type ImageModel = 'flux-2-pro' | 'gpt-image-1.5' | 'ideogram-3';
export type VideoModel = 'kling-2.6-pro';

export interface VisualPlan {
  model: ImageModel;
  prompt: string;
  negativePrompt: string;
  aspectRatio: '9:16' | '1:1' | '16:9' | '4:5';
  generateVideo: boolean;
  videoPrompt?: string;
  videoDuration?: 5 | 10;
  rationale: string;
}

export interface VisualBrief {
  contentType: 'carousel' | 'reel' | 'story';
  segmentType: 'hook' | 'body' | 'cta';
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

export interface QualityReport {
  score: number;
  pass: boolean;
  issues: string[];
  feedback: string;
  checks: {
    dimensions: boolean;
    fileSize: boolean;
    noGarbledText: boolean;
    noCollage: boolean;
    noBlackBars: boolean;
    noSeams: boolean;
    subjectClarity: boolean;
    brandAlignment: boolean;
  };
}

export interface GeneratedImage {
  path: string;
  model: ImageModel;
  prompt: string;
  qualityReport?: QualityReport;
  retryCount: number;
}

export interface GeneratedVideo {
  path: string;
  model: VideoModel;
  sourceImagePath: string;
  motionPrompt: string;
  durationSeconds: number;
  qualityReport?: QualityReport;
}

export interface StyleAnchor {
  imageStylePrefix: string;
  imageStyleSuffix: string;
  imageNegativePrompt: string;
  videoMotionStyle: string;
  hookVisualStyle: string;
  bodyVisualStyle: string;
  ctaVisualStyle: string;
}

export interface QualityLogEntry {
  model: string;
  contentType: string;
  segmentType?: string;
  prompt: string;
  qualityScore: number;
  issues: string[];
  retryCount: number;
  finalPrompt?: string;
}

export interface ModelCapabilities {
  name: string;
  provider: string;
  costPerImage?: number;
  costPerSecond?: number;
  speedSeconds: number;
  strengths: string[];
  weaknesses: string[];
  absoluteNever: string[];
  promptTips: string[];
  aspectRatios: string[];
}
