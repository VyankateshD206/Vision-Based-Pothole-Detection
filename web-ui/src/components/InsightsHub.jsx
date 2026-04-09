import { useMemo, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Expand,
  Filter,
  Sparkles,
  X,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const MODEL_COLORS = ['#f59e0b', '#fb923c', '#f97316', '#06b6d4', '#84cc16', '#a3a3a3'];
const SEVERITY_COLORS = {
  Shallow: '#facc15',
  Moderate: '#fb923c',
  Deep: '#f87171',
  Unknown: '#94a3b8',
};

function niceModelName(name) {
  if (!name) return 'Unknown';
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (s) => s.toUpperCase());
}

function MetricTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload;
  return (
    <div className="glass-card-bright px-4 py-3 shadow-xl max-w-[260px]">
      <p className="text-sm font-semibold text-white mb-1">{niceModelName(label)}</p>
      <p className="text-xs text-slate-300">
        Accuracy: <span className="text-amber-400 font-mono">{(row.accuracy ?? 0).toFixed(2)}%</span>
      </p>
      <p className="text-xs text-slate-400">
        Macro F1: <span className="text-cyan-300 font-mono">{(row.macroF1 ?? 0).toFixed(2)}%</span>
      </p>
    </div>
  );
}

function ScatterTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0].payload;
  return (
    <div className="glass-card-bright px-4 py-3 shadow-xl max-w-[280px]">
      <p className="text-sm font-semibold text-white">{p.imageName || 'Sample'}</p>
      <p className="text-xs text-slate-300 mt-1">
        Severity: <span style={{ color: SEVERITY_COLORS[p.severity] || SEVERITY_COLORS.Unknown }}>{p.severity}</span>
      </p>
      <p className="text-xs text-slate-400 mt-1 font-mono">X: {Number(p.x).toFixed(4)}</p>
      <p className="text-xs text-slate-400 font-mono">Y: {Number(p.y).toFixed(4)}</p>
    </div>
  );
}

export default function InsightsHub({ data, loading, error, apiBase }) {
  const [metricMode, setMetricMode] = useState('accuracy');
  const [galleryCategory, setGalleryCategory] = useState('All');
  const [gallerySearch, setGallerySearch] = useState('');
  const [activeGraphIndex, setActiveGraphIndex] = useState(null);
  const [xFeature, setXFeature] = useState('max_depth');
  const [yFeature, setYFeature] = useState('pothole_area');
  const [severityFilter, setSeverityFilter] = useState('All');

  const metrics = data?.metrics ?? [];
  const ablation = data?.ablation ?? [];
  const featureColumns = data?.featureColumns ?? [];
  const featureRows = data?.featureRows ?? [];
  const graphs = data?.graphs ?? [];

  const metricRows = useMemo(() => {
    const rows = metrics.map((m) => ({
      model: m.model,
      accuracy: Number((m.accuracy ?? 0) * 100),
      macroF1: Number(((m.macroF1 ?? 0) * 100)),
    }));
    const key = metricMode === 'macroF1' ? 'macroF1' : 'accuracy';
    return rows.sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0));
  }, [metrics, metricMode]);

  const ablationRows = useMemo(() => {
    return ablation.map((row) => ({
      subset: row.subset,
      valAccuracy: Number((row.valAccuracy ?? 0) * 100),
      macroF1: Number((row.macroF1 ?? 0) * 100),
      numFeatures: row.numFeatures,
    }));
  }, [ablation]);

  const severityOptions = useMemo(() => {
    const uniques = new Set(featureRows.map((r) => r.severity || 'Unknown'));
    return ['All', ...Array.from(uniques)];
  }, [featureRows]);

  const featureRowsFiltered = useMemo(() => {
    return featureRows
      .filter((row) => severityFilter === 'All' || row.severity === severityFilter)
      .slice(0, 1000)
      .map((row) => ({
        imageName: row.imageName,
        severity: row.severity || 'Unknown',
        x: Number(row[xFeature] ?? 0),
        y: Number(row[yFeature] ?? 0),
      }));
  }, [featureRows, severityFilter, xFeature, yFeature]);

  const groupedScatter = useMemo(() => {
    const map = {};
    for (const row of featureRowsFiltered) {
      const key = row.severity || 'Unknown';
      if (!map[key]) map[key] = [];
      map[key].push(row);
    }
    return map;
  }, [featureRowsFiltered]);

  const galleryCategories = useMemo(() => {
    const categories = Array.from(new Set(graphs.map((g) => g.category || 'Other')));
    return ['All', ...categories];
  }, [graphs]);

  const galleryItems = useMemo(() => {
    const query = gallerySearch.trim().toLowerCase();
    return graphs.filter((graph) => {
      const catMatch = galleryCategory === 'All' || graph.category === galleryCategory;
      const searchMatch = query.length === 0 || graph.title.toLowerCase().includes(query);
      return catMatch && searchMatch;
    });
  }, [graphs, galleryCategory, gallerySearch]);

  const activeGraph = activeGraphIndex === null ? null : galleryItems[activeGraphIndex] ?? null;

  const hasFeatures = featureColumns.length > 0 && featureRows.length > 0;

  if (loading) {
    return (
      <section className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-amber-400 animate-pulse" />
          <h2 className="text-lg font-semibold text-white">Loading Model Insights...</h2>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="shimmer rounded-xl h-36" />
          <div className="shimmer rounded-xl h-36" />
          <div className="shimmer rounded-xl h-36" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="glass-card p-6 border border-red-500/30">
        <h2 className="text-lg font-semibold text-white mb-2">Model Insights Unavailable</h2>
        <p className="text-sm text-red-300">{error}</p>
        <p className="text-xs text-slate-400 mt-2">
          Start backend API and ensure ml_results files exist.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-5">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Models Benchmarked</p>
          <p className="text-3xl font-bold text-white mt-2">{metrics.length}</p>
          <p className="text-xs text-slate-500 mt-1">Loaded from classification reports</p>
        </div>
        <div className="glass-card p-5">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Graphs Available</p>
          <p className="text-3xl font-bold text-white mt-2">{graphs.length}</p>
          <p className="text-xs text-slate-500 mt-1">Interactive gallery below</p>
        </div>
        <div className="glass-card p-5">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Top Model</p>
          <p className="text-xl font-bold text-white mt-2">
            {metricRows[0] ? niceModelName(metricRows[0].model) : 'N/A'}
          </p>
          <p className="text-xs text-amber-300 mt-1">
            {(metricRows[0]?.accuracy ?? 0).toFixed(2)}% accuracy
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
              Model Performance Explorer
            </h3>
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={() => setMetricMode('accuracy')}
                className={`px-3 py-1 rounded-full border ${metricMode === 'accuracy' ? 'border-amber-500/40 text-amber-300 bg-amber-500/10' : 'border-slate-700 text-slate-400'}`}
              >
                Accuracy
              </button>
              <button
                onClick={() => setMetricMode('macroF1')}
                className={`px-3 py-1 rounded-full border ${metricMode === 'macroF1' ? 'border-cyan-500/40 text-cyan-300 bg-cyan-500/10' : 'border-slate-700 text-slate-400'}`}
              >
                Macro F1
              </button>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={metricRows} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis
                dataKey="model"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => niceModelName(v).slice(0, 14)}
                angle={-15}
                textAnchor="end"
                height={52}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip content={<MetricTooltip />} />
              <Bar dataKey={metricMode} radius={[7, 7, 0, 0]} maxBarSize={55}>
                {metricRows.map((_, idx) => (
                  <Cell key={idx} fill={MODEL_COLORS[idx % MODEL_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
              Ablation Study
            </h3>
            <span className="text-xs text-slate-500">Accuracy vs Macro-F1</span>
          </div>

          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={ablationRows} margin={{ top: 8, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis
                dataKey="subset"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip />
              <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 12 }} />
              <Bar dataKey="valAccuracy" name="Val Accuracy" fill="#f59e0b" radius={[6, 6, 0, 0]} />
              <Bar dataKey="macroF1" name="Macro F1" fill="#06b6d4" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Interactive Feature Explorer
          </h3>
          <div className="flex flex-wrap gap-2 text-xs">
            <select
              value={xFeature}
              onChange={(e) => setXFeature(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200"
              disabled={!hasFeatures}
            >
              {(featureColumns.length ? featureColumns : ['max_depth']).map((feature) => (
                <option key={feature} value={feature}>{feature}</option>
              ))}
            </select>
            <select
              value={yFeature}
              onChange={(e) => setYFeature(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200"
              disabled={!hasFeatures}
            >
              {(featureColumns.length ? featureColumns : ['pothole_area']).map((feature) => (
                <option key={feature} value={feature}>{feature}</option>
              ))}
            </select>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200"
              disabled={!hasFeatures}
            >
              {severityOptions.map((severity) => (
                <option key={severity} value={severity}>{severity}</option>
              ))}
            </select>
          </div>
        </div>

        {hasFeatures ? (
          <>
            <ResponsiveContainer width="100%" height={330}>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 24, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="x"
                  name={xFeature}
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  label={{ value: xFeature, fill: '#64748b', fontSize: 11, position: 'insideBottom', offset: -10 }}
                />
                <YAxis
                  dataKey="y"
                  name={yFeature}
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  label={{ value: yFeature, fill: '#64748b', fontSize: 11, angle: -90, position: 'insideLeft' }}
                />
                <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: '4 4' }} />
                <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 12 }} />
                {Object.entries(groupedScatter).map(([severity, points]) => (
                  <Scatter
                    key={severity}
                    name={severity}
                    data={points}
                    fill={SEVERITY_COLORS[severity] || SEVERITY_COLORS.Unknown}
                    line={false}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
            <p className="text-xs text-slate-500 mt-2">
              Showing {featureRowsFiltered.length} samples for {xFeature} vs {yFeature}.
            </p>
          </>
        ) : (
          <p className="text-sm text-slate-400">Feature CSV files were not found in ml_results.</p>
        )}
      </div>

      <div className="glass-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Graph Gallery ({galleryItems.length} / {graphs.length})
          </h3>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <div className="flex items-center gap-1 text-slate-500 px-2">
              <Filter className="w-3.5 h-3.5" />
              Filter
            </div>
            {galleryCategories.map((category) => (
              <button
                key={category}
                onClick={() => {
                  setGalleryCategory(category);
                  setActiveGraphIndex(null);
                }}
                className={`px-3 py-1 rounded-full border ${galleryCategory === category ? 'border-amber-500/40 text-amber-300 bg-amber-500/10' : 'border-slate-700 text-slate-400'}`}
              >
                {category}
              </button>
            ))}
            <input
              value={gallerySearch}
              onChange={(e) => setGallerySearch(e.target.value)}
              placeholder="Search graph"
              className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200 placeholder:text-slate-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {galleryItems.map((graph, idx) => (
            <button
              key={graph.file}
              type="button"
              onClick={() => setActiveGraphIndex(idx)}
              className="group text-left glass-card-bright p-3 border border-white/5 hover:border-amber-500/40 transition-all duration-200"
            >
              <div className="relative overflow-hidden rounded-lg bg-black">
                <img
                  src={`${apiBase}${graph.url}`}
                  alt={graph.title}
                  className="w-full h-44 object-cover group-hover:scale-[1.02] transition-transform duration-300"
                  loading="lazy"
                />
                <span className="absolute top-2 left-2 text-[10px] px-2 py-1 rounded bg-black/70 text-amber-300 border border-amber-500/30">
                  {graph.category}
                </span>
                <span className="absolute top-2 right-2 p-1 rounded bg-black/65 text-slate-200 border border-white/10">
                  <Expand className="w-3.5 h-3.5" />
                </span>
              </div>
              <p className="text-sm text-slate-200 mt-2 min-h-[2.5rem]">{graph.title}</p>
            </button>
          ))}
        </div>

        {galleryItems.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">No graphs match your current filters.</p>
        )}
      </div>

      {activeGraph && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative w-full max-w-6xl glass-card p-4 border border-white/10">
            <button
              onClick={() => setActiveGraphIndex(null)}
              className="absolute top-3 right-3 p-2 rounded-lg bg-slate-900/90 border border-white/10 text-slate-200 hover:text-white"
              aria-label="Close graph modal"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center justify-between gap-2 mb-3 pr-12">
              <div>
                <p className="text-xs text-amber-300">{activeGraph.category}</p>
                <h4 className="text-lg font-semibold text-white">{activeGraph.title}</h4>
              </div>
              <div className="text-xs text-slate-400">{activeGraphIndex + 1} / {galleryItems.length}</div>
            </div>

            <div className="relative rounded-xl overflow-hidden bg-black">
              <img
                src={`${apiBase}${activeGraph.url}`}
                alt={activeGraph.title}
                className="w-full max-h-[70vh] object-contain"
              />
            </div>

            <div className="flex items-center justify-between mt-4">
              <button
                onClick={() => setActiveGraphIndex((prev) => (prev === null ? 0 : (prev - 1 + galleryItems.length) % galleryItems.length))}
                className="px-3 py-2 rounded-lg border border-white/15 text-slate-200 hover:border-amber-500/40"
              >
                <span className="flex items-center gap-1"><ChevronLeft className="w-4 h-4" /> Previous</span>
              </button>
              <button
                onClick={() => setActiveGraphIndex((prev) => (prev === null ? 0 : (prev + 1) % galleryItems.length))}
                className="px-3 py-2 rounded-lg border border-white/15 text-slate-200 hover:border-amber-500/40"
              >
                <span className="flex items-center gap-1">Next <ChevronRight className="w-4 h-4" /></span>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="text-center py-4">
        <p className="text-[11px] text-slate-500 max-w-2xl mx-auto leading-relaxed">
          Insights are loaded from ml_results artifacts. These metrics are dependent on pseudo-label quality and dataset distribution.
        </p>
      </div>
    </section>
  );
}
