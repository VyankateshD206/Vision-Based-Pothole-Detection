import { SEVERITY_COLORS } from '../mockData';

export default function SeverityBadge({ severity, consensusCount, total }) {
  const color = SEVERITY_COLORS[severity] || SEVERITY_COLORS['Moderate'];
  const isDeep = severity === 'Deep';

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`
          w-36 h-36 rounded-full flex flex-col items-center justify-center
          border-4 transition-all duration-500
          ${isDeep ? 'glow-red-pulse' : ''}
        `}
        style={{
          borderColor: color.bg,
          boxShadow: isDeep ? undefined : `0 0 30px ${color.ring}, 0 0 80px ${color.ring}`,
          background: `radial-gradient(circle at center, ${color.bg}18, transparent 70%)`,
        }}
      >
        <span className="text-4xl mb-1">
          {severity === 'No Pothole' ? '🟢' : severity === 'Shallow' ? '🟡' : severity === 'Moderate' ? '🟠' : '🔴'}
        </span>
        <span className="text-lg font-bold text-white tracking-wide">{severity}</span>
      </div>
      <p className="text-sm text-slate-400">
        Detected by <span className="text-amber-400 font-semibold">{consensusCount}</span> of {total} classifiers
      </p>
    </div>
  );
}
