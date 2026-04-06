import { Radar } from 'lucide-react';

export default function LoadingSkeleton() {
  return (
    <div className="w-full max-w-6xl mx-auto space-y-8 fade-in-up">
      {/* Loading indicator */}
      <div className="flex items-center justify-center gap-3 py-6">
        <Radar className="w-8 h-8 text-amber-500 animate-spin" />
        <span className="text-lg text-slate-300 font-medium">
          Running YOLOv8 + Depth Estimation…
        </span>
      </div>

      {/* Image trio skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {[0, 1, 2].map(i => (
          <div key={i} className="glass-card p-4" style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="shimmer rounded-xl h-48 mb-3" />
            <div className="shimmer rounded-lg h-4 w-3/4" />
          </div>
        ))}
      </div>

      {/* Severity badge skeleton */}
      <div className="flex justify-center">
        <div className="shimmer rounded-full w-36 h-36" />
      </div>

      {/* Table skeleton */}
      <div className="glass-card p-5 space-y-3">
        {[0, 1, 2, 3, 4].map(i => (
          <div key={i} className="shimmer rounded-lg h-10" style={{ animationDelay: `${i * 0.05}s` }} />
        ))}
      </div>
    </div>
  );
}
