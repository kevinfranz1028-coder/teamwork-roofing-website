import React, { useEffect, useState } from 'react';

interface RevenueEntry {
  id: number;
  date: string;
  source: string;
  description: string;
  amount: number;
  currency: string;
}

export default function Revenue() {
  const [entries, setEntries] = useState<RevenueEntry[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ date: '', source: '', description: '', amount: '' });

  const fetchRevenue = async () => {
    try {
      const res = await fetch('/api/revenue');
      setEntries(await res.json());
    } catch {}
  };

  useEffect(() => {
    fetchRevenue();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/revenue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, amount: parseFloat(form.amount) }),
    });
    setForm({ date: '', source: '', description: '', amount: '' });
    setShowForm(false);
    fetchRevenue();
  };

  const totalRevenue = entries.reduce((sum, e) => sum + (e.amount || 0), 0);
  const thisMonth = entries
    .filter(e => e.date?.startsWith(new Date().toISOString().slice(0, 7)))
    .reduce((sum, e) => sum + (e.amount || 0), 0);

  const bySource = entries.reduce((acc, e) => {
    acc[e.source] = (acc[e.source] || 0) + (e.amount || 0);
    return acc;
  }, {} as Record<string, number>);

  const sourceColors: Record<string, string> = {
    affiliate: 'bg-blue-600',
    digital_product: 'bg-purple-600',
    shoutout: 'bg-pink-600',
    subscription: 'bg-green-600',
    sponsorship: 'bg-orange-600',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Revenue Tracker</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
        >
          {showForm ? 'Cancel' : '+ Log Revenue'}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Total Revenue</p>
          <p className="text-2xl font-bold mt-1 text-green-400">${totalRevenue.toFixed(2)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">This Month</p>
          <p className="text-2xl font-bold mt-1">${thisMonth.toFixed(2)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Entries</p>
          <p className="text-2xl font-bold mt-1">{entries.length}</p>
        </div>
      </div>

      {/* Revenue by Source */}
      {Object.keys(bySource).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Revenue by Source</h3>
          <div className="space-y-2">
            {Object.entries(bySource)
              .sort(([, a], [, b]) => b - a)
              .map(([source, amount]) => {
                const pct = totalRevenue > 0 ? (amount / totalRevenue) * 100 : 0;
                return (
                  <div key={source} className="flex items-center gap-3">
                    <span className="text-sm text-gray-300 w-32 capitalize">{source.replace('_', ' ')}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-4 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${sourceColors[source] || 'bg-gray-600'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-400 w-20 text-right">${amount.toFixed(2)}</span>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Add Revenue Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h3 className="text-lg font-semibold">Log Revenue Entry</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider">Date</label>
              <input
                type="date"
                value={form.date}
                onChange={e => setForm({ ...form, date: e.target.value })}
                required
                className="w-full mt-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider">Source</label>
              <select
                value={form.source}
                onChange={e => setForm({ ...form, source: e.target.value })}
                required
                className="w-full mt-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-purple-500"
              >
                <option value="">Select...</option>
                <option value="affiliate">Affiliate</option>
                <option value="digital_product">Digital Product</option>
                <option value="shoutout">Shoutout</option>
                <option value="subscription">Subscription</option>
                <option value="sponsorship">Sponsorship</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider">Amount ($)</label>
              <input
                type="number"
                step="0.01"
                value={form.amount}
                onChange={e => setForm({ ...form, amount: e.target.value })}
                required
                className="w-full mt-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider">Description</label>
              <input
                type="text"
                value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-green-700 hover:bg-green-600 rounded-lg text-sm font-medium transition-colors"
          >
            Save Entry
          </button>
        </form>
      )}

      {/* Revenue Log Table */}
      {entries.length > 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                <th className="text-left p-3">Date</th>
                <th className="text-left p-3">Source</th>
                <th className="text-left p-3">Description</th>
                <th className="text-right p-3">Amount</th>
              </tr>
            </thead>
            <tbody>
              {entries
                .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
                .map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="p-3">{entry.date}</td>
                    <td className="p-3">
                      <span className={`text-xs text-white px-2 py-0.5 rounded-full ${sourceColors[entry.source] || 'bg-gray-600'}`}>
                        {entry.source?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="p-3 text-gray-400">{entry.description || '—'}</td>
                    <td className="p-3 text-right text-green-400 font-medium">${(entry.amount || 0).toFixed(2)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">No revenue logged yet</p>
        </div>
      )}
    </div>
  );
}
