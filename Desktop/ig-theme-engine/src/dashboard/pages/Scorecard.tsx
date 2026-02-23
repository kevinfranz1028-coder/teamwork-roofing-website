import React, { useEffect, useState } from 'react';

interface ScorecardData {
  postsPublished: number;
  totalReach: number;
  totalSends: number;
  avgSendsPerReach: number;
  totalSaves: number;
  avgEngagementRate: number;
  revenue: number;
  status: 'green' | 'yellow' | 'red';
  kpis: Record<string, { value: number; green: number; yellow: number }>;
}

interface ScorecardHistory {
  id: number;
  week_start: string;
  posts_published: number;
  total_reach: number;
  total_sends: number;
  avg_sends_per_reach: number;
  revenue_total: number;
  status: string;
}

export default function Scorecard() {
  const [current, setCurrent] = useState<ScorecardData | null>(null);
  const [history, setHistory] = useState<ScorecardHistory[]>([]);

  useEffect(() => {
    fetch('/api/scorecard').then(r => r.json()).then(setCurrent).catch(() => {});
    fetch('/api/scorecard/history').then(r => r.json()).then(setHistory).catch(() => {});
  }, []);

  const statusConfig = {
    green: { bg: 'bg-green-900/30', border: 'border-green-700', text: 'text-green-400', label: 'GREEN' },
    yellow: { bg: 'bg-yellow-900/30', border: 'border-yellow-700', text: 'text-yellow-400', label: 'YELLOW' },
    red: { bg: 'bg-red-900/30', border: 'border-red-700', text: 'text-red-400', label: 'RED' },
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Weekly Scorecard</h2>

      {current ? (
        <>
          {/* Traffic Light Status */}
          <div className={`${statusConfig[current.status].bg} border ${statusConfig[current.status].border} rounded-xl p-6 text-center`}>
            <p className={`text-4xl font-bold ${statusConfig[current.status].text}`}>
              {statusConfig[current.status].label}
            </p>
            <p className="text-sm text-gray-400 mt-2">Overall weekly health</p>
          </div>

          {/* KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard
              label="Sends/Reach"
              value={`${((current.avgSendsPerReach || 0) * 100).toFixed(2)}%`}
              target={`Target: >${(current.kpis?.sendsPerReach?.green || 0.03) * 100}%`}
              status={getKPIStatus(current.avgSendsPerReach, current.kpis?.sendsPerReach)}
            />
            <KPICard
              label="Engagement Rate"
              value={`${((current.avgEngagementRate || 0) * 100).toFixed(2)}%`}
              target={`Target: >${(current.kpis?.engagementRate?.green || 0.05) * 100}%`}
              status={getKPIStatus(current.avgEngagementRate, current.kpis?.engagementRate)}
            />
            <KPICard
              label="Posts/Week"
              value={`${current.postsPublished || 0}`}
              target={`Target: >${current.kpis?.postsPerWeek?.green || 7}`}
              status={getKPIStatus(current.postsPublished, current.kpis?.postsPerWeek)}
            />
            <KPICard
              label="Revenue"
              value={`$${(current.revenue || 0).toFixed(2)}`}
              target={`Target: >$${current.kpis?.revenue?.green || 100}`}
              status={getKPIStatus(current.revenue, current.kpis?.revenue)}
            />
          </div>

          {/* Summary Row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-500 uppercase">Total Reach</p>
              <p className="text-xl font-bold mt-1">{(current.totalReach || 0).toLocaleString()}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-500 uppercase">Total Sends</p>
              <p className="text-xl font-bold mt-1 text-purple-400">{(current.totalSends || 0).toLocaleString()}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-500 uppercase">Total Saves</p>
              <p className="text-xl font-bold mt-1 text-blue-400">{(current.totalSaves || 0).toLocaleString()}</p>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">No scorecard data yet</p>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <h3 className="text-lg font-semibold p-4 border-b border-gray-800">History</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="text-left p-3">Week</th>
                <th className="text-center p-3">Status</th>
                <th className="text-right p-3">Posts</th>
                <th className="text-right p-3">Reach</th>
                <th className="text-right p-3">Sends</th>
                <th className="text-right p-3">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.id} className="border-b border-gray-800/50">
                  <td className="p-3">{row.week_start}</td>
                  <td className="p-3 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      row.status === 'green' ? 'bg-green-900 text-green-400' :
                      row.status === 'yellow' ? 'bg-yellow-900 text-yellow-400' :
                      'bg-red-900 text-red-400'
                    }`}>{row.status?.toUpperCase()}</span>
                  </td>
                  <td className="p-3 text-right">{row.posts_published}</td>
                  <td className="p-3 text-right">{(row.total_reach || 0).toLocaleString()}</td>
                  <td className="p-3 text-right">{(row.total_sends || 0).toLocaleString()}</td>
                  <td className="p-3 text-right">${(row.revenue_total || 0).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function getKPIStatus(value: number | undefined, thresholds?: { green: number; yellow: number }): 'green' | 'yellow' | 'red' {
  if (!thresholds || value === undefined) return 'red';
  if (value >= thresholds.green) return 'green';
  if (value >= thresholds.yellow) return 'yellow';
  return 'red';
}

function KPICard({ label, value, target, status }: { label: string; value: string; target: string; status: 'green' | 'yellow' | 'red' }) {
  const colors = {
    green: 'border-green-700 text-green-400',
    yellow: 'border-yellow-700 text-yellow-400',
    red: 'border-red-700 text-red-400',
  };
  return (
    <div className={`bg-gray-900 border ${colors[status].split(' ')[0]} rounded-xl p-4`}>
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${colors[status].split(' ')[1]}`}>{value}</p>
      <p className="text-xs text-gray-600 mt-1">{target}</p>
    </div>
  );
}
