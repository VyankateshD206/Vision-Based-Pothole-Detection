import { useState } from 'react';
import { CLASSIFIERS, SEVERITY_COLORS } from '../mockData';

export default function ClassifierTable({ results }) {
  const [hoveredRow, setHoveredRow] = useState(null);

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-5 py-4 border-b border-white/5">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Classifier Breakdown
        </h3>
      </div>
      <div className="divide-y divide-white/[0.04]">
        {CLASSIFIERS.map((cls) => {
          const result = results[cls.id];
          if (!result) return null;
          const color = SEVERITY_COLORS[result.severity] || SEVERITY_COLORS['Moderate'];
          const isRule = cls.type === 'rule';

          return (
            <div
              key={cls.id}
              onMouseEnter={() => setHoveredRow(cls.id)}
              onMouseLeave={() => setHoveredRow(null)}
              className={`
                relative flex items-center px-5 py-3.5 transition-all duration-200
                ${hoveredRow === cls.id ? 'bg-white/[0.03]' : ''}
              `}
            >
              {/* Classifier name */}
              <div className="flex-1 min-w-0">
                <span
                  className={`text-sm font-medium ${
                    isRule ? 'font-mono text-cyan-400' : 'text-slate-200'
                  }`}
                >
                  {cls.name}
                </span>
                {isRule && (
                  <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-500 border border-cyan-500/20">
                    THRESHOLD
                  </span>
                )}
              </div>

              {/* Severity pill */}
              <div className="flex items-center gap-4 shrink-0">
                <span
                  className="px-3 py-1 rounded-full text-xs font-bold"
                  style={{
                    backgroundColor: `${color.bg}20`,
                    color: color.bg,
                    border: `1px solid ${color.bg}40`,
                  }}
                >
                  {result.severity}
                </span>

                {/* Confidence bar */}
                <div className="w-28 flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded-full bg-slate-700/60 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700 ease-out"
                      style={{
                        width: `${result.confidence * 100}%`,
                        background: `linear-gradient(to right, ${color.bg}99, ${color.bg})`,
                      }}
                    />
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono w-8 text-right">
                    {Math.round(result.confidence * 100)}%
                  </span>
                </div>
              </div>

              {/* Tooltip on hover */}
              {hoveredRow === cls.id && (
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 z-10
                  px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-600/50
                  text-[11px] text-slate-300 whitespace-nowrap shadow-xl
                  fade-in-up"
                  style={{ animationDuration: '0.2s' }}
                >
                  {isRule
                    ? 'Manual thresholds on max_depth & area'
                    : 'Pseudo-labels via KMeans clustering'}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
