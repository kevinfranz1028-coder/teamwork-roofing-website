import React, { useEffect, useState } from 'react';

interface Brief {
  id: number;
  title: string;
  notes: string | null;
  competitor_links: string | null;
  content_angles: string | null;
  mood_themes: string | null;
  visual_style: string | null;
  target_emotions: string | null;
  is_active: number;
  created_at: string;
  updated_at: string;
}

interface BriefForm {
  title: string;
  notes: string;
  competitor_links: string[];
  content_angles: string[];
  mood_themes: string;
  visual_style: string;
  target_emotions: string;
}

const emptyForm: BriefForm = {
  title: '',
  notes: '',
  competitor_links: [],
  content_angles: [],
  mood_themes: '',
  visual_style: '',
  target_emotions: '',
};

function parseBriefToForm(b: Brief): BriefForm {
  return {
    title: b.title,
    notes: b.notes || '',
    competitor_links: b.competitor_links ? JSON.parse(b.competitor_links) : [],
    content_angles: b.content_angles ? JSON.parse(b.content_angles) : [],
    mood_themes: b.mood_themes || '',
    visual_style: b.visual_style || '',
    target_emotions: b.target_emotions || '',
  };
}

export default function CreativeBrief() {
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [form, setForm] = useState<BriefForm>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [linkInput, setLinkInput] = useState('');
  const [angleInput, setAngleInput] = useState('');

  const loadBriefs = async () => {
    const res = await fetch('/api/briefs');
    const data = await res.json();
    setBriefs(data);
  };

  useEffect(() => { loadBriefs(); }, []);

  const activeBrief = briefs.find(b => b.is_active);
  const pastBriefs = briefs.filter(b => !b.is_active);

  const handleSave = async () => {
    setSaving(true);
    const payload = {
      ...form,
      competitor_links: form.competitor_links.length > 0 ? form.competitor_links : null,
      content_angles: form.content_angles.length > 0 ? form.content_angles : null,
    };

    if (editingId) {
      await fetch(`/api/briefs/${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } else {
      await fetch('/api/briefs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    }

    setShowForm(false);
    setEditingId(null);
    setForm({ ...emptyForm });
    setSaving(false);
    loadBriefs();
  };

  const handleActivate = async (id: number) => {
    await fetch(`/api/briefs/${id}/activate`, { method: 'POST' });
    loadBriefs();
  };

  const handleDelete = async (id: number) => {
    await fetch(`/api/briefs/${id}`, { method: 'DELETE' });
    loadBriefs();
  };

  const startEdit = (b: Brief) => {
    setForm(parseBriefToForm(b));
    setEditingId(b.id);
    setShowForm(true);
  };

  const startNew = () => {
    setForm({ ...emptyForm });
    setEditingId(null);
    setShowForm(true);
  };

  const addLink = () => {
    const trimmed = linkInput.trim();
    if (trimmed && !form.competitor_links.includes(trimmed)) {
      setForm({ ...form, competitor_links: [...form.competitor_links, trimmed] });
    }
    setLinkInput('');
  };

  const removeLink = (idx: number) => {
    setForm({ ...form, competitor_links: form.competitor_links.filter((_, i) => i !== idx) });
  };

  const addAngle = () => {
    const trimmed = angleInput.trim();
    if (trimmed && !form.content_angles.includes(trimmed)) {
      setForm({ ...form, content_angles: [...form.content_angles, trimmed] });
    }
    setAngleInput('');
  };

  const removeAngle = (idx: number) => {
    setForm({ ...form, content_angles: form.content_angles.filter((_, i) => i !== idx) });
  };

  const formatDate = (d: string) => new Date(d + 'Z').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

  // ─── Render ───────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Creative Brief</h2>
          <p className="text-gray-400 text-sm mt-1">
            Guide the AI with your creative vision — angles, mood, visual style, and inspiration
          </p>
        </div>
        {!showForm && (
          <button
            onClick={startNew}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors"
          >
            + New Brief
          </button>
        )}
      </div>

      {/* Active Brief Card */}
      {activeBrief && !showForm && (
        <div className="bg-gray-900 border border-green-700/50 rounded-xl p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold">{activeBrief.title}</h3>
              <span className="px-2 py-0.5 text-xs font-medium bg-green-600/20 text-green-400 rounded-full">
                Active
              </span>
            </div>
            <button
              onClick={() => startEdit(activeBrief)}
              className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Edit
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {activeBrief.notes && (
              <div className="md:col-span-2">
                <span className="text-gray-500 text-xs uppercase tracking-wide">Notes & Inspiration</span>
                <p className="text-gray-300 mt-1 whitespace-pre-wrap">{activeBrief.notes}</p>
              </div>
            )}
            {activeBrief.competitor_links && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Competitor Links</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {(JSON.parse(activeBrief.competitor_links) as string[]).map((link, i) => (
                    <a key={i} href={link} target="_blank" rel="noopener noreferrer"
                       className="text-purple-400 hover:text-purple-300 underline break-all text-xs">
                      {link.replace(/https?:\/\/(www\.)?instagram\.com\//, '@')}
                    </a>
                  ))}
                </div>
              </div>
            )}
            {activeBrief.content_angles && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Content Angles</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {(JSON.parse(activeBrief.content_angles) as string[]).map((a, i) => (
                    <span key={i} className="px-2 py-0.5 bg-gray-800 text-gray-300 rounded-full text-xs">{a}</span>
                  ))}
                </div>
              </div>
            )}
            {activeBrief.mood_themes && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Mood & Themes</span>
                <p className="text-gray-300 mt-1">{activeBrief.mood_themes}</p>
              </div>
            )}
            {activeBrief.visual_style && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Visual Style</span>
                <p className="text-gray-300 mt-1">{activeBrief.visual_style}</p>
              </div>
            )}
            {activeBrief.target_emotions && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Target Emotions</span>
                <p className="text-gray-300 mt-1">{activeBrief.target_emotions}</p>
              </div>
            )}
          </div>
          <p className="text-gray-600 text-xs mt-4">Created {formatDate(activeBrief.created_at)}</p>
        </div>
      )}

      {/* No Active Brief */}
      {!activeBrief && !showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-400">No active brief. Create one to guide your AI content generation.</p>
        </div>
      )}

      {/* Brief Editor Form */}
      {showForm && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
          <h3 className="text-lg font-semibold">
            {editingId ? 'Edit Brief' : 'New Creative Brief'}
          </h3>

          {/* Title */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Title</label>
            <input
              type="text"
              value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })}
              placeholder="February Week 4 Brief"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Notes / Inspiration</label>
            <textarea
              value={form.notes}
              onChange={e => setForm({ ...form, notes: e.target.value })}
              placeholder="Focus on spring prep content, new growth..."
              rows={4}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500 resize-y"
            />
          </div>

          {/* Competitor Links */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Competitor Links</label>
            <div className="flex gap-2">
              <input
                type="url"
                value={linkInput}
                onChange={e => setLinkInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addLink(); } }}
                placeholder="https://instagram.com/plantaccount"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              />
              <button onClick={addLink} className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
                Add
              </button>
            </div>
            {form.competitor_links.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {form.competitor_links.map((link, i) => (
                  <span key={i} className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-800 border border-gray-700 rounded-full text-xs">
                    <span className="text-purple-400 max-w-[200px] truncate">{link}</span>
                    <button onClick={() => removeLink(i)} className="text-gray-500 hover:text-red-400">&times;</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Content Angles */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Content Angles</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={angleInput}
                onChange={e => setAngleInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addAngle(); } }}
                placeholder="beginner mistakes, seasonal tips..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              />
              <button onClick={addAngle} className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
                Add
              </button>
            </div>
            {form.content_angles.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {form.content_angles.map((angle, i) => (
                  <span key={i} className="flex items-center gap-1.5 px-2.5 py-1 bg-purple-600/20 text-purple-300 rounded-full text-xs">
                    {angle}
                    <button onClick={() => removeAngle(i)} className="text-purple-400 hover:text-red-400">&times;</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Mood, Visual Style, Target Emotions — row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Mood & Themes</label>
              <input
                type="text"
                value={form.mood_themes}
                onChange={e => setForm({ ...form, mood_themes: e.target.value })}
                placeholder="hopeful, fresh start, spring energy"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Visual Style</label>
              <input
                type="text"
                value={form.visual_style}
                onChange={e => setForm({ ...form, visual_style: e.target.value })}
                placeholder="bright natural light, green palette, clean"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Target Emotions</label>
              <input
                type="text"
                value={form.target_emotions}
                onChange={e => setForm({ ...form, target_emotions: e.target.value })}
                placeholder="curiosity, confidence, FOMO"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleSave}
              disabled={!form.title.trim() || saving}
              className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
            >
              {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Create Brief'}
            </button>
            <button
              onClick={() => { setShowForm(false); setEditingId(null); setForm({ ...emptyForm }); }}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Brief History */}
      {pastBriefs.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-3">Past Briefs</h3>
          <div className="space-y-2">
            {pastBriefs.map(b => (
              <div key={b.id} className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 flex items-center justify-between">
                <div>
                  <span className="font-medium text-sm">{b.title}</span>
                  <span className="text-gray-500 text-xs ml-2">{formatDate(b.created_at)}</span>
                  {b.mood_themes && (
                    <span className="text-gray-500 text-xs ml-2">— {b.mood_themes}</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleActivate(b.id)}
                    className="px-3 py-1 text-xs bg-green-600/20 text-green-400 hover:bg-green-600/30 rounded-lg transition-colors"
                  >
                    Activate
                  </button>
                  <button
                    onClick={() => startEdit(b)}
                    className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(b.id)}
                    className="px-3 py-1 text-xs bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded-lg transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
