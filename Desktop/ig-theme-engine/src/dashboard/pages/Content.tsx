import React, { useEffect, useState } from 'react';

// ─── Types ──────────────────────────────────────────

interface OptionData {
  ideaId: number;
  scriptId: number;
  contentType: string;
  title: string;
  hook: string;
  sendTrigger: string;
  valueProp: string;
  emotionalTrigger: string;
  sendProbability: string;
  caption: string;
  hashtags: string[];
  dmTrigger: string;
  scriptJson: string;
  localPaths: string[];
  publicUrls: string[];
}

interface BatchData {
  batchId: string;
  status: string;
  selectedIdeaId: number | null;
  createdAt: string;
  options: OptionData[];
}

interface ScheduleItem {
  calendarId: number;
  scheduledDate: string;
  scheduledTime: string;
  contentType: string;
  status: string;
  scriptId: number;
  caption: string;
  hashtags: string[];
  scriptJson: string;
  dmTrigger: string;
  ideaId: number;
  title: string;
  hook: string;
  sendTrigger: string;
  sendProbability: string;
  localPaths: string[];
  publicUrls: string[];
}

interface QueueItem {
  id: number;
  idea_id: number;
  content_type: string;
  script_json: string;
  caption: string;
  hashtags: string;
  title: string;
  hook: string;
  idea_status: string;
  send_trigger: string;
  send_probability: string;
  dm_trigger_keyword: string;
  batch_id: string | null;
  local_paths: string[];
  public_urls: string[];
}

// ─── Helpers ────────────────────────────────────────

const typeColors: Record<string, string> = {
  carousel: 'bg-blue-600',
  reel: 'bg-pink-600',
  story: 'bg-orange-600',
  static: 'bg-green-600',
};

const probColors: Record<string, string> = {
  high: 'text-yellow-400',
  very_high: 'text-orange-400',
  extreme: 'text-red-400',
};

const toUrl = (p: string): string => {
  const assetsIdx = p.indexOf('data/assets/');
  if (assetsIdx !== -1) return '/' + p.slice(assetsIdx).replace('data/', '');
  return p;
};

const getAllSlides = (opt: { publicUrls: string[]; localPaths: string[] }): string[] => {
  const paths = opt.publicUrls && opt.publicUrls.length > 0 ? opt.publicUrls : opt.localPaths;
  if (!paths || paths.length === 0) return [];
  return paths.map(p => opt.publicUrls && opt.publicUrls.length > 0 ? p : toUrl(p));
};

const getThumbnail = (opt: { publicUrls: string[]; localPaths: string[] }): string | null => {
  const slides = getAllSlides(opt);
  return slides.length > 0 ? slides[0] : null;
};

function formatScheduleDate(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
}

// ─── Full-Screen Slide Preview Modal ────────────────

function SlidePreview({
  slides,
  startIndex,
  title,
  caption,
  hashtags,
  onClose,
}: {
  slides: string[];
  startIndex: number;
  title: string;
  caption: string;
  hashtags: string[];
  onClose: () => void;
}) {
  const [current, setCurrent] = useState(startIndex);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight' && current < slides.length - 1) setCurrent(c => c + 1);
      if (e.key === 'ArrowLeft' && current > 0) setCurrent(c => c - 1);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [current, slides.length, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center"
      onClick={onClose}
    >
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl z-10 w-10 h-10 flex items-center justify-center"
      >
        X
      </button>

      <div className="absolute top-4 left-1/2 -translate-x-1/2 text-gray-400 text-sm">
        Slide {current + 1} of {slides.length}
      </div>

      <div
        className="flex-1 flex items-center justify-center w-full px-16 py-12"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={() => setCurrent(c => Math.max(0, c - 1))}
          disabled={current === 0}
          className={`shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-colors ${
            current === 0
              ? 'text-gray-700 cursor-not-allowed'
              : 'text-gray-300 hover:text-white hover:bg-white/10'
          }`}
        >
          &lt;
        </button>

        <div className="flex-1 flex items-center justify-center mx-4 max-h-[80vh]">
          <img
            src={slides[current]}
            alt={`${title} — Slide ${current + 1}`}
            className="max-h-[80vh] max-w-full object-contain rounded-lg shadow-2xl"
          />
        </div>

        <button
          onClick={() => setCurrent(c => Math.min(slides.length - 1, c + 1))}
          disabled={current === slides.length - 1}
          className={`shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-colors ${
            current === slides.length - 1
              ? 'text-gray-700 cursor-not-allowed'
              : 'text-gray-300 hover:text-white hover:bg-white/10'
          }`}
        >
          &gt;
        </button>
      </div>

      <div
        className="w-full px-8 pb-4 flex justify-center gap-2 overflow-x-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {slides.map((src, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            className={`shrink-0 w-14 h-14 rounded-md overflow-hidden border-2 transition-all ${
              i === current ? 'border-purple-500 scale-110' : 'border-transparent opacity-50 hover:opacity-80'
            }`}
          >
            <img src={src} alt={`Thumb ${i + 1}`} className="w-full h-full object-cover" />
          </button>
        ))}
      </div>

      <div
        className="w-full max-w-2xl px-8 pb-6"
        onClick={(e) => e.stopPropagation()}
      >
        <details className="text-sm">
          <summary className="text-gray-500 cursor-pointer hover:text-gray-300 text-xs">
            Show caption preview
          </summary>
          <div className="mt-2 bg-gray-900/80 rounded-lg p-4 space-y-2 max-h-40 overflow-y-auto">
            <p className="text-gray-300 text-xs whitespace-pre-wrap">{caption}</p>
            {hashtags && hashtags.length > 0 && (
              <p className="text-blue-400 text-xs">
                {hashtags.map(t => `#${t.replace('#', '')}`).join(' ')}
              </p>
            )}
          </div>
        </details>
      </div>
    </div>
  );
}

// ─── Section 1: Content Options ─────────────────────

function ContentOptionsSection({
  onScheduled,
}: {
  onScheduled: () => void;
}) {
  const [batch, setBatch] = useState<BatchData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [scheduling, setScheduling] = useState<number | null>(null);
  const [scheduledInfo, setScheduledInfo] = useState<Record<number, { date: string; time: string }>>({});
  const [preview, setPreview] = useState<{ opt: OptionData; startIndex: number } | null>(null);

  const fetchLatest = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/options/latest');
      const data = await res.json();
      if (data && data.batchId) {
        setBatch(data);
      } else {
        setBatch(null);
      }
    } catch {
      // Server not running
    }
    setLoading(false);
  };

  useEffect(() => { fetchLatest(); }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setScheduledInfo({});
    try {
      await fetch('/api/options/generate', { method: 'POST' });
      await fetchLatest();
    } catch (err) {
      console.error('Generate failed:', err);
    }
    setGenerating(false);
  };

  const handleApproveSchedule = async (scriptId: number) => {
    setScheduling(scriptId);
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-and-schedule`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setScheduledInfo(prev => ({
          ...prev,
          [scriptId]: { date: data.scheduledDate, time: data.scheduledTime },
        }));
        onScheduled();
      }
    } catch (err) {
      console.error('Schedule failed:', err);
    }
    setScheduling(null);
  };

  return (
    <div className="space-y-4">
      {preview && (
        <SlidePreview
          slides={getAllSlides(preview.opt)}
          startIndex={preview.startIndex}
          title={preview.opt.title}
          caption={preview.opt.caption || ''}
          hashtags={preview.opt.hashtags || []}
          onClose={() => setPreview(null)}
        />
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Content Options</h2>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            generating
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-500 text-white'
          }`}
        >
          {generating ? (
            <span className="flex items-center gap-2">
              <span className="inline-block w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
              Generating 5 Options...
            </span>
          ) : (
            'Generate New Options'
          )}
        </button>
      </div>

      {loading && !generating && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      )}

      {!loading && !batch && !generating && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">No content options generated yet</p>
          <p className="text-xs text-gray-600 mt-2">
            Click "Generate New Options" to create 5 visual post options to choose from
          </p>
        </div>
      )}

      {batch && (
        <>
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <span>Batch: {batch.batchId.slice(0, 8)}</span>
            <span>|</span>
            <span>{batch.options.length} options</span>
            <span>|</span>
            <span className={batch.status === 'ready' ? 'text-green-400' : 'text-yellow-400'}>
              {batch.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {batch.options.map((opt, idx) => {
              const thumb = getThumbnail(opt);
              const slides = getAllSlides(opt);
              const isExpanded = expanded === opt.ideaId;
              const isScheduled = !!scheduledInfo[opt.scriptId];
              let script: any = {};
              try { script = JSON.parse(opt.scriptJson || '{}'); } catch {}

              return (
                <div
                  key={opt.ideaId}
                  className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${
                    isScheduled
                      ? 'border-green-500 ring-1 ring-green-500'
                      : 'border-gray-800 hover:border-gray-700'
                  }`}
                >
                  {/* Thumbnail */}
                  <div
                    className="relative aspect-square bg-gray-800 cursor-pointer group"
                    onClick={() => slides.length > 0 && setPreview({ opt, startIndex: 0 })}
                  >
                    {thumb ? (
                      <>
                        <img src={thumb} alt={opt.title} className="w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                          <span className="text-white text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 px-4 py-2 rounded-lg">
                            Preview All {slides.length} Slides
                          </span>
                        </div>
                      </>
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-600">
                        <span className="text-4xl">
                          {opt.contentType === 'carousel' ? '[ ]' : '|>'}
                        </span>
                      </div>
                    )}
                    <span className={`absolute top-2 left-2 text-xs text-white px-2 py-0.5 rounded-full ${typeColors[opt.contentType] || 'bg-gray-600'}`}>
                      {opt.contentType}
                    </span>
                    {slides.length > 1 && (
                      <span className="absolute bottom-2 right-2 text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                        {slides.length} slides
                      </span>
                    )}
                    <span className="absolute top-2 right-2 text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                      #{idx + 1}
                    </span>
                  </div>

                  {/* Info */}
                  <div className="p-4 space-y-2">
                    <h3 className="font-medium text-sm leading-tight">{opt.title}</h3>
                    <p className="text-xs text-gray-400 line-clamp-2">{opt.hook}</p>

                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-gray-500">Send:</span>
                      <span className={probColors[opt.sendProbability] || 'text-gray-400'}>
                        {opt.sendProbability?.replace('_', ' ')}
                      </span>
                    </div>

                    {opt.sendTrigger && (
                      <p className="text-xs text-purple-300 italic">"{opt.sendTrigger}"</p>
                    )}

                    {/* Action buttons */}
                    <div className="pt-2 flex gap-2">
                      <button
                        onClick={() => slides.length > 0 && setPreview({ opt, startIndex: 0 })}
                        className="flex-1 px-3 py-1.5 bg-purple-900/40 hover:bg-purple-800/60 border border-purple-700 text-purple-300 text-xs rounded-lg transition-colors"
                      >
                        Preview Full Post
                      </button>
                      <button
                        onClick={() => setExpanded(isExpanded ? null : opt.ideaId)}
                        className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-xs rounded-lg transition-colors"
                      >
                        {isExpanded ? 'Less' : 'Info'}
                      </button>
                    </div>

                    {isScheduled ? (
                      <div className="w-full px-3 py-2 text-xs rounded-lg bg-green-900/40 border border-green-700 text-green-300 text-center font-medium">
                        Scheduled: {scheduledInfo[opt.scriptId].date} at {scheduledInfo[opt.scriptId].time}
                      </div>
                    ) : (
                      <button
                        onClick={() => handleApproveSchedule(opt.scriptId)}
                        disabled={scheduling === opt.scriptId}
                        className={`w-full px-3 py-2 text-xs rounded-lg transition-colors font-medium ${
                          scheduling === opt.scriptId
                            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                            : 'bg-green-700 hover:bg-green-600 text-white'
                        }`}
                      >
                        {scheduling === opt.scriptId ? 'Scheduling...' : 'Approve & Schedule'}
                      </button>
                    )}
                  </div>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div className="border-t border-gray-800 p-4 space-y-4">
                      {slides.length > 1 && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                            All Slides — click any to preview full-size
                          </p>
                          <div className="grid grid-cols-5 gap-1.5">
                            {slides.map((src, i) => (
                              <button
                                key={i}
                                onClick={() => setPreview({ opt, startIndex: i })}
                                className="relative aspect-square rounded-md overflow-hidden border border-gray-700 hover:border-purple-500 transition-colors group"
                              >
                                <img src={src} alt={`Slide ${i + 1}`} className="w-full h-full object-cover" />
                                <span className="absolute bottom-0 inset-x-0 bg-black/60 text-[10px] text-gray-300 text-center py-0.5">
                                  {i + 1}
                                </span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {opt.caption && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Caption</p>
                          <p className="text-xs text-gray-300 whitespace-pre-wrap">{opt.caption}</p>
                        </div>
                      )}

                      {script?.hook && opt.contentType === 'reel' && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Reel Script</p>
                          <div className="bg-gray-800 rounded-lg p-3 space-y-2">
                            <div>
                              <span className="text-xs text-pink-400">HOOK (0-1.7s):</span>
                              <p className="text-xs mt-0.5">{script.hook.onScreenText}</p>
                            </div>
                            {script.body?.map((seg: any, i: number) => (
                              <div key={i}>
                                <span className="text-xs text-gray-500">{seg.timestamp}s:</span>
                                <p className="text-xs mt-0.5">{seg.onScreenText}</p>
                              </div>
                            ))}
                            {script.cta && (
                              <div>
                                <span className="text-xs text-green-400">CTA:</span>
                                <p className="text-xs mt-0.5">{script.cta.onScreenText}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {opt.hashtags && opt.hashtags.length > 0 && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Hashtags</p>
                          <div className="flex flex-wrap gap-1">
                            {opt.hashtags.map((tag: string, i: number) => (
                              <span key={i} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                                #{tag.replace('#', '')}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {opt.dmTrigger && (
                        <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-3">
                          <p className="text-xs text-purple-400">
                            DM Trigger: "{opt.dmTrigger}"
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Section 2: Upcoming Schedule ───────────────────

function UpcomingScheduleSection({
  schedule,
  onRefresh,
}: {
  schedule: ScheduleItem[];
  onRefresh: () => void;
}) {
  const [publishing, setPublishing] = useState<number | null>(null);
  const [removing, setRemoving] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const handlePublishNow = async (calendarId: number) => {
    setPublishing(calendarId);
    try {
      await fetch(`/api/schedule/${calendarId}/publish-now`, { method: 'POST' });
      onRefresh();
    } catch (err) {
      console.error('Publish failed:', err);
    }
    setPublishing(null);
  };

  const handleRemove = async (calendarId: number) => {
    setRemoving(calendarId);
    try {
      await fetch(`/api/schedule/${calendarId}/remove`, { method: 'POST' });
      onRefresh();
    } catch (err) {
      console.error('Remove failed:', err);
    }
    setRemoving(null);
  };

  // Group by date
  const grouped = schedule.reduce<Record<string, ScheduleItem[]>>((acc, item) => {
    const key = item.scheduledDate;
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});

  const sortedDates = Object.keys(grouped).sort();

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Upcoming Schedule</h2>

      {sortedDates.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
          <p className="text-gray-500">No content scheduled yet</p>
          <p className="text-xs text-gray-600 mt-1">Approve content above to auto-schedule it</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedDates.map(date => (
            <div key={date}>
              <h3 className="text-sm font-semibold text-gray-400 mb-2">
                {formatScheduleDate(date)}
              </h3>
              <div className="space-y-2">
                {grouped[date].map(item => {
                  const slides = getAllSlides(item);
                  const thumb = slides.length > 0 ? slides[0] : null;
                  const isExpanded = expandedId === item.calendarId;

                  return (
                    <div key={item.calendarId} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                      <div
                        className="p-3 flex items-center gap-3 cursor-pointer hover:bg-gray-800/50 transition-colors"
                        onClick={() => setExpandedId(isExpanded ? null : item.calendarId)}
                      >
                        {/* Thumbnail */}
                        {thumb && (
                          <img
                            src={thumb}
                            alt={item.title}
                            className="w-12 h-12 rounded-lg object-cover shrink-0"
                          />
                        )}

                        {/* Time badge */}
                        <span className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded-md font-mono shrink-0">
                          {item.scheduledTime}
                        </span>

                        {/* Type badge */}
                        <span className={`text-xs text-white px-2 py-0.5 rounded-full shrink-0 ${typeColors[item.contentType] || 'bg-gray-600'}`}>
                          {item.contentType}
                        </span>

                        {/* Title */}
                        <span className="text-sm font-medium flex-1 truncate">
                          {item.title || 'Untitled'}
                        </span>

                        {/* Actions */}
                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={(e) => { e.stopPropagation(); handlePublishNow(item.calendarId); }}
                            disabled={publishing === item.calendarId}
                            className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                              publishing === item.calendarId
                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'bg-green-700 hover:bg-green-600 text-white'
                            }`}
                          >
                            {publishing === item.calendarId ? 'Publishing...' : 'Publish Now'}
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleRemove(item.calendarId); }}
                            disabled={removing === item.calendarId}
                            className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                              removing === item.calendarId
                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'bg-red-900 hover:bg-red-800 text-red-200'
                            }`}
                          >
                            {removing === item.calendarId ? 'Removing...' : 'Remove'}
                          </button>
                          <span className="text-gray-500 text-sm">{isExpanded ? '\u25B2' : '\u25BC'}</span>
                        </div>
                      </div>

                      {/* Expanded details */}
                      {isExpanded && (
                        <div className="border-t border-gray-800 p-4 space-y-3">
                          {item.caption && (
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Caption</p>
                              <p className="text-xs text-gray-300 whitespace-pre-wrap">{item.caption}</p>
                            </div>
                          )}
                          {item.hashtags && item.hashtags.length > 0 && (
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Hashtags</p>
                              <div className="flex flex-wrap gap-1">
                                {item.hashtags.map((tag: string, i: number) => (
                                  <span key={i} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                                    #{tag.replace('#', '')}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {slides.length > 1 && (
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Slides</p>
                              <div className="flex gap-1.5 overflow-x-auto">
                                {slides.map((src, i) => (
                                  <img
                                    key={i}
                                    src={src}
                                    alt={`Slide ${i + 1}`}
                                    className="w-16 h-16 rounded-md object-cover shrink-0 border border-gray-700"
                                  />
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Section 3: Ready Content (previously in Queue) ─

function ReadyContentSection({
  onScheduled,
}: {
  onScheduled: () => void;
}) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [scheduling, setScheduling] = useState<number | null>(null);
  const [scheduledInfo, setScheduledInfo] = useState<Record<number, { date: string; time: string }>>({});
  const [preview, setPreview] = useState<{ item: QueueItem; startIndex: number } | null>(null);

  const fetchQueue = async () => {
    try {
      const res = await fetch('/api/queue');
      setItems(await res.json());
    } catch {
      // Server not running
    }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleApproveSchedule = async (scriptId: number) => {
    setScheduling(scriptId);
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-and-schedule`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setScheduledInfo(prev => ({
          ...prev,
          [scriptId]: { date: data.scheduledDate, time: data.scheduledTime },
        }));
        onScheduled();
        fetchQueue();
      }
    } catch (err) {
      console.error('Schedule failed:', err);
    }
    setScheduling(null);
  };

  const handleReject = async (id: number) => {
    await fetch(`/api/queue/${id}/reject`, { method: 'POST' });
    fetchQueue();
  };

  const getItemSlides = (item: QueueItem): string[] => {
    const paths = item.public_urls && item.public_urls.length > 0 ? item.public_urls : item.local_paths;
    if (!paths || paths.length === 0) return [];
    return paths.map(p => item.public_urls && item.public_urls.length > 0 ? p : toUrl(p));
  };

  if (items.length === 0) return null;

  return (
    <div className="space-y-4">
      {preview && (
        <SlidePreview
          slides={getItemSlides(preview.item)}
          startIndex={preview.startIndex}
          title={preview.item.title}
          caption={preview.item.caption || ''}
          hashtags={preview.item.hashtags ? (typeof preview.item.hashtags === 'string' ? JSON.parse(preview.item.hashtags) : preview.item.hashtags) : []}
          onClose={() => setPreview(null)}
        />
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Ready Content</h2>
        <span className="text-sm text-gray-500">{items.length} items</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item) => {
          const slides = getItemSlides(item);
          const thumb = slides.length > 0 ? slides[0] : null;
          const isExpanded = expanded === item.id;
          const isScheduled = !!scheduledInfo[item.id];
          const isApproved = item.idea_status === 'approved';
          let script: any = {};
          try { script = JSON.parse(item.script_json || '{}'); } catch {}
          let hashtags: string[] = [];
          try { hashtags = item.hashtags ? (typeof item.hashtags === 'string' ? JSON.parse(item.hashtags) : item.hashtags) : []; } catch {}

          return (
            <div
              key={item.id}
              className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${
                isScheduled
                  ? 'border-green-500 ring-1 ring-green-500'
                  : isApproved
                    ? 'border-blue-500/50'
                    : 'border-gray-800 hover:border-gray-700'
              }`}
            >
              {/* Thumbnail */}
              <div
                className="relative aspect-square bg-gray-800 cursor-pointer group"
                onClick={() => slides.length > 0 && setPreview({ item, startIndex: 0 })}
              >
                {thumb ? (
                  <>
                    <img src={thumb} alt={item.title} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                      <span className="text-white text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 px-4 py-2 rounded-lg">
                        Preview {slides.length > 1 ? `All ${slides.length} Slides` : 'Post'}
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-600">
                    <span className="text-4xl">
                      {item.content_type === 'carousel' ? '[ ]' : item.content_type === 'reel' ? '|>' : '#'}
                    </span>
                  </div>
                )}
                <span className={`absolute top-2 left-2 text-xs text-white px-2 py-0.5 rounded-full ${typeColors[item.content_type] || 'bg-gray-600'}`}>
                  {item.content_type}
                </span>
                {slides.length > 1 && (
                  <span className="absolute bottom-2 right-2 text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                    {slides.length} slides
                  </span>
                )}
                {isApproved && (
                  <span className="absolute top-2 right-2 text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">
                    approved
                  </span>
                )}
              </div>

              {/* Info */}
              <div className="p-4 space-y-2">
                <h3 className="font-medium text-sm leading-tight">{item.title || 'Untitled'}</h3>
                {item.hook && <p className="text-xs text-gray-400 line-clamp-2">{item.hook}</p>}

                {item.send_probability && (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-gray-500">Send:</span>
                    <span className={probColors[item.send_probability] || 'text-gray-400'}>
                      {item.send_probability?.replace('_', ' ')}
                    </span>
                  </div>
                )}

                {item.send_trigger && (
                  <p className="text-xs text-purple-300 italic">"{item.send_trigger}"</p>
                )}

                {/* Action buttons */}
                <div className="pt-2 flex gap-2">
                  {slides.length > 0 && (
                    <button
                      onClick={() => setPreview({ item, startIndex: 0 })}
                      className="flex-1 px-3 py-1.5 bg-purple-900/40 hover:bg-purple-800/60 border border-purple-700 text-purple-300 text-xs rounded-lg transition-colors"
                    >
                      Preview Full Post
                    </button>
                  )}
                  <button
                    onClick={() => setExpanded(isExpanded ? null : item.id)}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-xs rounded-lg transition-colors"
                  >
                    {isExpanded ? 'Less' : 'Info'}
                  </button>
                </div>

                {isScheduled ? (
                  <div className="w-full px-3 py-2 text-xs rounded-lg bg-green-900/40 border border-green-700 text-green-300 text-center font-medium">
                    Scheduled: {scheduledInfo[item.id].date} at {scheduledInfo[item.id].time}
                  </div>
                ) : item.idea_status === 'scripted' ? (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApproveSchedule(item.id)}
                      disabled={scheduling === item.id}
                      className={`flex-1 px-3 py-2 text-xs rounded-lg transition-colors font-medium ${
                        scheduling === item.id
                          ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                          : 'bg-green-700 hover:bg-green-600 text-white'
                      }`}
                    >
                      {scheduling === item.id ? 'Scheduling...' : 'Approve & Schedule'}
                    </button>
                    <button
                      onClick={() => handleReject(item.id)}
                      className="px-3 py-2 bg-red-900 hover:bg-red-800 text-red-200 text-xs rounded-lg transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                ) : (
                  <div className="w-full px-3 py-2 text-xs rounded-lg bg-blue-900/30 border border-blue-700 text-blue-300 text-center font-medium">
                    Approved — schedule above or publish from queue
                  </div>
                )}
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="border-t border-gray-800 p-4 space-y-4">
                  {slides.length > 1 && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                        All Slides — click any to preview full-size
                      </p>
                      <div className="grid grid-cols-5 gap-1.5">
                        {slides.map((src, i) => (
                          <button
                            key={i}
                            onClick={() => setPreview({ item, startIndex: i })}
                            className="relative aspect-square rounded-md overflow-hidden border border-gray-700 hover:border-purple-500 transition-colors"
                          >
                            <img src={src} alt={`Slide ${i + 1}`} className="w-full h-full object-cover" />
                            <span className="absolute bottom-0 inset-x-0 bg-black/60 text-[10px] text-gray-300 text-center py-0.5">
                              {i + 1}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {item.caption && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Caption</p>
                      <p className="text-xs text-gray-300 whitespace-pre-wrap">{item.caption}</p>
                    </div>
                  )}

                  {script?.hook && item.content_type === 'reel' && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Reel Script</p>
                      <div className="bg-gray-800 rounded-lg p-3 space-y-2">
                        <div>
                          <span className="text-xs text-pink-400">HOOK (0-1.7s):</span>
                          <p className="text-xs mt-0.5">{script.hook.onScreenText}</p>
                        </div>
                        {script.body?.map((seg: any, i: number) => (
                          <div key={i}>
                            <span className="text-xs text-gray-500">{seg.timestamp}s:</span>
                            <p className="text-xs mt-0.5">{seg.onScreenText}</p>
                          </div>
                        ))}
                        {script.cta && (
                          <div>
                            <span className="text-xs text-green-400">CTA:</span>
                            <p className="text-xs mt-0.5">{script.cta.onScreenText}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {hashtags.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Hashtags</p>
                      <div className="flex flex-wrap gap-1">
                        {hashtags.map((tag: string, i: number) => (
                          <span key={i} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                            #{tag.replace('#', '')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {item.dm_trigger_keyword && (
                    <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-3">
                      <p className="text-xs text-purple-400">
                        DM Trigger: "{item.dm_trigger_keyword}"
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main Content Page ──────────────────────────────

export default function Content() {
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);

  const fetchSchedule = async () => {
    try {
      const res = await fetch('/api/schedule');
      setSchedule(await res.json());
    } catch {
      // Server not running
    }
  };

  useEffect(() => { fetchSchedule(); }, []);

  return (
    <div className="space-y-10">
      <ContentOptionsSection onScheduled={fetchSchedule} />

      <div className="border-t border-gray-800" />

      <UpcomingScheduleSection schedule={schedule} onRefresh={fetchSchedule} />

      <div className="border-t border-gray-800" />

      <ReadyContentSection onScheduled={fetchSchedule} />
    </div>
  );
}
