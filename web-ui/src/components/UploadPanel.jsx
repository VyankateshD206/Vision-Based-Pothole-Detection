import { useState, useRef, useCallback } from 'react';
import { Upload, Radar, AlertTriangle } from 'lucide-react';
import { CLASSIFIERS } from '../mockData';

export default function UploadPanel({ onImageUpload, onRunAnalysis, isLoading }) {
  const [preview, setPreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [enabledClassifiers, setEnabledClassifiers] = useState(
    Object.fromEntries(CLASSIFIERS.map(c => [c.id, true]))
  );
  const fileInputRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      onImageUpload(e.target.result, file);
    };
    reader.readAsDataURL(file);
  }, [onImageUpload]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const loadDemo = useCallback(async () => {
    const url = '/sample_pothole.png';
    const res = await fetch(url);
    const blob = await res.blob();
    const file = new File([blob], 'sample_pothole.png', { type: blob.type });
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      onImageUpload(e.target.result, file);
    };
    reader.readAsDataURL(blob);
  }, [onImageUpload]);

  const toggleClassifier = (id) => {
    setEnabledClassifiers(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <section className="w-full max-w-5xl mx-auto mb-10">
      {/* Upload Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative glass-card cursor-pointer
          border-2 border-dashed transition-all duration-300 ease-out
          flex flex-col items-center justify-center
          min-h-[260px] p-8
          ${isDragging
            ? 'border-amber-500 bg-amber-500/[0.04] scale-[1.01]'
            : preview
              ? 'border-amber-500/30 hover:border-amber-500/60'
              : 'border-amber-500/40 hover:border-amber-500/70'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />

        {preview ? (
          <div className="flex flex-col items-center gap-4">
            <img
              src={preview}
              alt="Uploaded road"
              className="max-h-[180px] rounded-xl object-contain shadow-2xl"
            />
            <p className="text-slate-400 text-sm">
              Click or drag to replace image
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 text-center">
            {/* Road crack icon */}
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 flex items-center justify-center mb-1">
              <AlertTriangle className="w-8 h-8 text-amber-500" strokeWidth={1.5} />
            </div>
            <div>
              <p className="text-xl font-semibold text-slate-200">
                Drop a road image to analyze
              </p>
              <p className="text-sm text-slate-500 mt-1">
                PNG, JPG up to 20MB — or click to browse
              </p>
              <button
                onClick={(e) => { e.stopPropagation(); loadDemo(); }}
                className="mt-2 text-xs text-amber-500 hover:text-amber-400 underline underline-offset-2 transition-colors"
              >
                Try with sample pothole image →
              </button>
            </div>
          </div>
        )}

        {/* Drag shimmer overlay */}
        {isDragging && (
          <div className="absolute inset-0 rounded-2xl border-2 border-amber-500 animate-pulse pointer-events-none" />
        )}
      </div>

      {/* Classifier Toggles */}
      <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
        {CLASSIFIERS.map(cls => (
          <button
            key={cls.id}
            onClick={() => toggleClassifier(cls.id)}
            className={`
              px-4 py-1.5 rounded-full text-xs font-medium
              transition-all duration-200 border
              ${enabledClassifiers[cls.id]
                ? cls.type === 'rule'
                  ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-400'
                  : 'bg-amber-500/15 border-amber-500/40 text-amber-400'
                : 'bg-slate-800/50 border-slate-700 text-slate-500'
              }
            `}
          >
            {cls.name}
          </button>
        ))}
      </div>

      {/* Run Analysis Button */}
      <button
        onClick={onRunAnalysis}
        disabled={!preview || isLoading}
        className={`
          mt-5 w-full py-3.5 rounded-xl font-semibold text-base
          transition-all duration-300 flex items-center justify-center gap-2
          ${preview && !isLoading
            ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white hover:glow-amber hover:scale-[1.01] active:scale-[0.99] cursor-pointer'
            : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }
        `}
      >
        {isLoading ? (
          <>
            <Radar className="w-5 h-5 animate-spin" />
            Running YOLOv8 + Depth Estimation…
          </>
        ) : (
          <>
            <Upload className="w-5 h-5" />
            Run Analysis
          </>
        )}
      </button>
    </section>
  );
}
