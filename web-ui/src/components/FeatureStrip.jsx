import {
  Maximize2, ArrowDown, TrendingUp, Activity, BarChart3, ArrowUpRight,
} from 'lucide-react';

const FEATURE_CARDS = [
  { key: 'pothole_area', label: 'Pothole Area', unit: 'px²', icon: Maximize2, format: (v) => v.toLocaleString() },
  { key: 'max_depth',    label: 'Max Depth',    unit: '',     icon: ArrowDown,    format: (v) => v.toFixed(4) },
  { key: 'mean_depth',   label: 'Mean Depth',   unit: '',     icon: TrendingUp,   format: (v) => v.toFixed(4) },
  { key: 'depth_std',    label: 'Depth Std',    unit: 'σ',    icon: Activity,     format: (v) => v.toFixed(4) },
  { key: 'depth_range',  label: 'Depth Range',  unit: '',     icon: BarChart3,    format: (v) => v.toFixed(4) },
  { key: 'p90_depth',    label: 'P90 Depth',    unit: '',     icon: ArrowUpRight, format: (v) => v.toFixed(4) },
];

function MiniGauge({ value, max = 1.0 }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full h-1 rounded-full bg-slate-700/50 mt-2">
      <div
        className="h-full rounded-full bg-gradient-to-r from-cyan-500/60 to-amber-500"
        style={{ width: `${pct}%`, transition: 'width 0.8s ease-out' }}
      />
    </div>
  );
}

export default function FeatureStrip({ features }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {FEATURE_CARDS.map(({ key, label, unit, icon: Icon, format }, i) => {
        const val = features[key] ?? 0;
        const gaugeMax = key === 'pothole_area' ? 50000 : 1.0;
        return (
          <div
            key={key}
            className="glass-card-bright p-4 fade-in-up"
            style={{ animationDelay: `${i * 0.08}s` }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon className="w-4 h-4 text-cyan-500/70" strokeWidth={1.5} />
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-medium">
                {label}
              </span>
            </div>
            <p className="text-xl font-bold text-white tracking-tight">
              {format(val)}
              {unit && <span className="text-xs text-slate-500 ml-1">{unit}</span>}
            </p>
            <MiniGauge value={val} max={gaugeMax} />
          </div>
        );
      })}
    </div>
  );
}
