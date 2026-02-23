import React, { useEffect, useState } from 'react';

interface PublishedPost {
  id: number;
  script_id: number;
  platform: string;
  published_at: string;
  impressions: number;
  reach: number;
  likes: number;
  comments: number;
  saves: number;
  sends: number;
  sends_per_reach: number;
  engagement_rate: number;
  watch_time_seconds: number;
}

export default function Analytics() {
  const [posts, setPosts] = useState<PublishedPost[]>([]);

  useEffect(() => {
    fetch('/api/analytics')
      .then(res => res.json())
      .then(setPosts)
      .catch(() => {});
  }, []);

  const totalReach = posts.reduce((sum, p) => sum + (p.reach || 0), 0);
  const totalSends = posts.reduce((sum, p) => sum + (p.sends || 0), 0);
  const totalSaves = posts.reduce((sum, p) => sum + (p.saves || 0), 0);
  const avgEngagement = posts.length > 0
    ? posts.reduce((sum, p) => sum + (p.engagement_rate || 0), 0) / posts.length
    : 0;
  const avgSendsPerReach = posts.length > 0
    ? posts.reduce((sum, p) => sum + (p.sends_per_reach || 0), 0) / posts.length
    : 0;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Analytics Overview</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Total Reach</p>
          <p className="text-2xl font-bold mt-1">{totalReach.toLocaleString()}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Total Sends</p>
          <p className="text-2xl font-bold mt-1 text-purple-400">{totalSends.toLocaleString()}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Total Saves</p>
          <p className="text-2xl font-bold mt-1 text-blue-400">{totalSaves.toLocaleString()}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Avg Sends/Reach</p>
          <p className="text-2xl font-bold mt-1 text-green-400">{(avgSendsPerReach * 100).toFixed(2)}%</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Avg Engagement</p>
          <p className="text-2xl font-bold mt-1">{(avgEngagement * 100).toFixed(2)}%</p>
        </div>
      </div>

      {/* Posts Table */}
      {posts.length > 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                  <th className="text-left p-3">Date</th>
                  <th className="text-left p-3">Platform</th>
                  <th className="text-right p-3">Reach</th>
                  <th className="text-right p-3">Sends</th>
                  <th className="text-right p-3">Saves</th>
                  <th className="text-right p-3">Likes</th>
                  <th className="text-right p-3">Sends/Reach</th>
                  <th className="text-right p-3">Engagement</th>
                </tr>
              </thead>
              <tbody>
                {posts.map((post) => (
                  <tr key={post.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="p-3">{post.published_at ? new Date(post.published_at).toLocaleDateString() : '—'}</td>
                    <td className="p-3 capitalize">{post.platform}</td>
                    <td className="p-3 text-right">{(post.reach || 0).toLocaleString()}</td>
                    <td className="p-3 text-right text-purple-400 font-medium">{(post.sends || 0).toLocaleString()}</td>
                    <td className="p-3 text-right text-blue-400">{(post.saves || 0).toLocaleString()}</td>
                    <td className="p-3 text-right">{(post.likes || 0).toLocaleString()}</td>
                    <td className="p-3 text-right">
                      <span className={`${(post.sends_per_reach || 0) > 0.03 ? 'text-green-400' : (post.sends_per_reach || 0) > 0.01 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {((post.sends_per_reach || 0) * 100).toFixed(2)}%
                      </span>
                    </td>
                    <td className="p-3 text-right">{((post.engagement_rate || 0) * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">No published content yet</p>
          <p className="text-xs text-gray-600 mt-2">Analytics will appear here after content is published</p>
        </div>
      )}
    </div>
  );
}
