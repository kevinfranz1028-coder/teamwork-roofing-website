import React, { useEffect, useState, useRef } from 'react';
import { apiFetch } from '../utils/api.js';

interface CostSummary {
  total: number;
  calls: number;
  byProvider: { provider: string; total: number; calls: number }[];
  byCategory: { category: string; total: number; calls: number }[];
  periods: { today: number; week: number; month: number; all: number };
}

interface CostItem {
  id: number;
  endpoint: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  provider: string;
  category: string;
  model: string;
  description: string;
  idea_id: number | null;
  duration_ms: number | null;
  created_at: string;
}

interface BreakdownResponse {
  items: CostItem[];
  total: number;
  page: number;
  limit: number;
}

interface ProjectCost {
  projectKey: string;
  title: string;
  contentType: string;
  calls: number;
  totalCost: number;
  breakdown: { image: number; video: number; text: number; tts: number; vision: number };
  firstCost: string;
  lastCost: string;
}

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: 'bg-amber-600',
  openai: 'bg-emerald-600',
  replicate: 'bg-blue-600',
  fal: 'bg-purple-600',
  ideogram: 'bg-pink-600',
};

const CATEGORY_COLORS: Record<string, string> = {
  text: 'bg-blue-500',
  image: 'bg-green-500',
  video: 'bg-purple-500',
  tts: 'bg-orange-500',
  vision: 'bg-cyan-500',
};

const TYPE_BADGES: Record<string, string> = {
  carousel: 'bg-blue-900 text-blue-300',
  reel: 'bg-purple-900 text-purple-300',
  story: 'bg-pink-900 text-pink-300',
  mixed: 'bg-gray-700 text-gray-300',
  unknown: 'bg-gray-800 text-gray-500',
};

const POLL_INTERVAL = 15_000; // 15 seconds

export default function APICosts() {
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [breakdown, setBreakdown] = useState<BreakdownResponse | null>(null);
  const [projects, setProjects] = useState<ProjectCost[]>([]);
  const [filterProvider, setFilterProvider] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'projects' | 'log'>('overview');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchSummary = async () => {
    try {
      const res = await apiFetch('/api/costs/summary');
      setSummary(await res.json());
    } catch {}
  };

  const fetchBreakdown = async () => {
    try {
      const params = new URLSearchParams({ page: String(page), limit: '50' });
      if (filterProvider) params.set('provider', filterProvider);
      if (filterCategory) params.set('category', filterCategory);
      const res = await apiFetch(`/api/costs/breakdown?${params}`);
      setBreakdown(await res.json());
    } catch {}
  };

  const fetchProjects = async () => {
    try {
      const res = await apiFetch('/api/costs/by-project');
      setProjects(await res.json());
    } catch {}
  };

  const fetchAll = async () => {
    await Promise.all([fetchSummary(), fetchBreakdown(), fetchProjects()]);
    setLastUpdated(new Date());
  };

  // Initial load
  useEffect(() => {
    setLoading(true);
    fetchAll().finally(() => setLoading(false));
  }, []);

  // Auto-refresh polling
  useEffect(() => {
    pollRef.current = setInterval(fetchAll, POLL_INTERVAL);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [page, filterProvider, filterCategory]);

  // Refetch breakdown on filter/page change
  useEffect(() => {
    fetchBreakdown();
  }, [page, filterProvider, filterCategory]);

  const fmt = (n: number) => `$${n.toFixed(4)}`;
  const fmtUsd = (n: number) => `$${n.toFixed(2)}`;

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-500">Loading cost data...</p>
      </div>
    );
  }

  const periods = summary?.periods || { today: 0, week: 0, month: 0, all: 0 };
  const maxProviderSpend = Math.max(...(summary?.byProvider?.map(p => p.total) || [0]), 0.001);
  const maxCategorySpend = Math.max(...(summary?.byCategory?.map(c => c.total) || [0]), 0.001);
  const totalPages = breakdown ? Math.ceil(breakdown.total / breakdown.limit) : 1;
  const maxProjectCost = Math.max(...projects.map(p => p.totalCost), 0.001);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">API Costs</h2>
        <span className="text-xs text-gray-600">
          Auto-updates every 15s — last: {lastUpdated.toLocaleTimeString()}
        </span>
      </div>

      {/* Period Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Today</p>
          <p className="text-2xl font-bold mt-1 text-green-400">{fmtUsd(periods.today)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">This Week</p>
          <p className="text-2xl font-bold mt-1">{fmtUsd(periods.week)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">This Month</p>
          <p className="text-2xl font-bold mt-1">{fmtUsd(periods.month)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">All Time</p>
          <p className="text-2xl font-bold mt-1 text-amber-400">{fmtUsd(periods.all)}</p>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1">
        {(['overview', 'projects', 'log'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-colors ${
              activeTab === tab
                ? 'bg-gray-700 text-white'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab === 'overview' ? 'Overview' : tab === 'projects' ? 'By Project' : 'Cost Log'}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ── */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* By Provider */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Spend by Provider</h3>
            {(summary?.byProvider?.length ?? 0) > 0 ? (
              <div className="space-y-2">
                {summary!.byProvider.map(p => (
                  <div key={p.provider} className="flex items-center gap-3">
                    <span className="text-sm text-gray-300 w-24 capitalize">{p.provider || 'unknown'}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-4 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${PROVIDER_COLORS[p.provider] || 'bg-gray-600'}`}
                        style={{ width: `${(p.total / maxProviderSpend) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-400 w-20 text-right">{fmtUsd(p.total)}</span>
                    <span className="text-xs text-gray-600 w-16 text-right">{p.calls} calls</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">No costs recorded yet</p>
            )}
          </div>

          {/* By Category */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Spend by Category</h3>
            {(summary?.byCategory?.length ?? 0) > 0 ? (
              <div className="space-y-2">
                {summary!.byCategory.map(c => (
                  <div key={c.category} className="flex items-center gap-3">
                    <span className="text-sm text-gray-300 w-24 capitalize">{c.category || 'unknown'}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-4 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${CATEGORY_COLORS[c.category] || 'bg-gray-600'}`}
                        style={{ width: `${(c.total / maxCategorySpend) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-400 w-20 text-right">{fmtUsd(c.total)}</span>
                    <span className="text-xs text-gray-600 w-16 text-right">{c.calls} calls</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">No costs recorded yet</p>
            )}
          </div>
        </div>
      )}

      {/* ── PROJECTS TAB ── */}
      {activeTab === 'projects' && (
        <div className="space-y-3">
          {projects.length > 0 ? (
            projects.map(proj => (
              <div key={proj.projectKey} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${TYPE_BADGES[proj.contentType] || TYPE_BADGES.unknown}`}>
                      {proj.contentType}
                    </span>
                    <h4 className="text-sm font-medium text-gray-200 truncate">{proj.title}</h4>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <span className="text-xs text-gray-600">{proj.calls} calls</span>
                    <span className="text-lg font-bold text-green-400">{fmtUsd(proj.totalCost)}</span>
                  </div>
                </div>

                {/* Cost bar */}
                <div className="bg-gray-800 rounded-full h-3 overflow-hidden mb-2">
                  <div className="h-full rounded-full bg-green-600" style={{ width: `${(proj.totalCost / maxProjectCost) * 100}%` }} />
                </div>

                {/* Category mini-breakdown */}
                <div className="flex gap-4 text-xs text-gray-500">
                  {proj.breakdown.image > 0 && (
                    <span><span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-1" />Image {fmtUsd(proj.breakdown.image)}</span>
                  )}
                  {proj.breakdown.video > 0 && (
                    <span><span className="inline-block w-2 h-2 rounded-full bg-purple-500 mr-1" />Video {fmtUsd(proj.breakdown.video)}</span>
                  )}
                  {proj.breakdown.text > 0 && (
                    <span><span className="inline-block w-2 h-2 rounded-full bg-blue-500 mr-1" />Text {fmtUsd(proj.breakdown.text)}</span>
                  )}
                  {proj.breakdown.tts > 0 && (
                    <span><span className="inline-block w-2 h-2 rounded-full bg-orange-500 mr-1" />TTS {fmtUsd(proj.breakdown.tts)}</span>
                  )}
                  {proj.breakdown.vision > 0 && (
                    <span><span className="inline-block w-2 h-2 rounded-full bg-cyan-500 mr-1" />Vision {fmtUsd(proj.breakdown.vision)}</span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
              <p className="text-gray-500">No project costs recorded yet.</p>
            </div>
          )}
        </div>
      )}

      {/* ── COST LOG TAB ── */}
      {activeTab === 'log' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-gray-800 flex items-center gap-3 flex-wrap">
            <h3 className="text-sm font-medium text-gray-400 mr-auto">Cost Log</h3>
            <select
              value={filterProvider}
              onChange={e => { setFilterProvider(e.target.value); setPage(1); }}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500"
            >
              <option value="">All Providers</option>
              <option value="anthropic">Anthropic</option>
              <option value="openai">OpenAI</option>
              <option value="replicate">Replicate</option>
              <option value="fal">fal.ai</option>
              <option value="ideogram">Ideogram</option>
            </select>
            <select
              value={filterCategory}
              onChange={e => { setFilterCategory(e.target.value); setPage(1); }}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500"
            >
              <option value="">All Categories</option>
              <option value="text">Text</option>
              <option value="image">Image</option>
              <option value="video">Video</option>
              <option value="tts">TTS</option>
              <option value="vision">Vision</option>
            </select>
          </div>

          {(breakdown?.items?.length ?? 0) > 0 ? (
            <>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                    <th className="text-left p-3">Time</th>
                    <th className="text-left p-3">Provider</th>
                    <th className="text-left p-3">Model</th>
                    <th className="text-left p-3">Description</th>
                    <th className="text-right p-3">Tokens</th>
                    <th className="text-right p-3">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {breakdown!.items.map(item => (
                    <tr key={item.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                      <td className="p-3 text-gray-400 whitespace-nowrap">
                        {new Date(item.created_at + 'Z').toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                        })}
                      </td>
                      <td className="p-3">
                        <span className={`text-xs text-white px-2 py-0.5 rounded-full ${PROVIDER_COLORS[item.provider] || 'bg-gray-600'}`}>
                          {item.provider}
                        </span>
                      </td>
                      <td className="p-3 text-gray-300 text-xs">{item.model || '\u2014'}</td>
                      <td className="p-3 text-gray-400 max-w-xs truncate">{item.description || item.endpoint}</td>
                      <td className="p-3 text-right text-gray-500 text-xs whitespace-nowrap">
                        {item.input_tokens || item.output_tokens
                          ? `${(item.input_tokens || 0).toLocaleString()} / ${(item.output_tokens || 0).toLocaleString()}`
                          : '\u2014'}
                      </td>
                      <td className="p-3 text-right text-green-400 font-medium whitespace-nowrap">{fmt(item.estimated_cost)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between p-3 border-t border-gray-800">
                  <span className="text-xs text-gray-500">{breakdown!.total} total entries</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page <= 1}
                      className="px-3 py-1 text-xs bg-gray-800 rounded disabled:opacity-40 hover:bg-gray-700 transition-colors"
                    >
                      Prev
                    </button>
                    <span className="text-xs text-gray-400 py-1">Page {page} / {totalPages}</span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page >= totalPages}
                      className="px-3 py-1 text-xs bg-gray-800 rounded disabled:opacity-40 hover:bg-gray-700 transition-colors"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No API costs recorded yet. Costs will appear here after generating content.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
