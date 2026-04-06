import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ErrorBar, ReferenceLine,
} from 'recharts';
import { MODEL_ACCURACIES } from '../mockData';

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="glass-card-bright px-4 py-3 shadow-xl">
      <p className="text-sm font-semibold text-white mb-1">{d.name}</p>
      <p className="text-xs text-slate-400">
        Accuracy: <span className="text-amber-400 font-mono">{(d.accuracy * 100).toFixed(1)}%</span>
      </p>
      <p className="text-xs text-slate-500">
        95% CI: [{(d.ci_lower * 100).toFixed(1)}% – {(d.ci_upper * 100).toFixed(1)}%]
      </p>
    </div>
  );
};

const GRADIENT_COLORS = ['#d97706', '#ea580c', '#f59e0b', '#b45309'];

export default function AccuracyChart() {
  // Transform data so error bars work (recharts ErrorBar needs [low, high] delta)
  const data = MODEL_ACCURACIES.map(d => ({
    ...d,
    acc_pct: d.accuracy * 100,
    errorLow: (d.accuracy - d.ci_lower) * 100,
    errorHigh: (d.ci_upper - d.accuracy) * 100,
  }));

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
        Validation Accuracy with 95% CI
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 10, right: 20, bottom: 5, left: 0 }} barCategoryGap="25%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
            tickLine={false}
          />
          <YAxis
            domain={[60, 100]}
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <ReferenceLine y={90} stroke="rgba(245,158,11,0.2)" strokeDasharray="4 4" />
          <Bar dataKey="acc_pct" radius={[6, 6, 0, 0]} maxBarSize={52}>
            {data.map((_, i) => (
              <Cell key={i} fill={`url(#barGrad${i})`} />
            ))}
            <ErrorBar
              dataKey="errorHigh"
              direction="y"
              width={8}
              stroke="#f59e0b"
              strokeWidth={1.5}
            />
          </Bar>
          <defs>
            {data.map((_, i) => (
              <linearGradient key={i} id={`barGrad${i}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={GRADIENT_COLORS[i]} stopOpacity={0.9} />
                <stop offset="100%" stopColor={GRADIENT_COLORS[i]} stopOpacity={0.4} />
              </linearGradient>
            ))}
          </defs>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
