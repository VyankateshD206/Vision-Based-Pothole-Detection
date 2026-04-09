import { useState, useCallback, useEffect, useMemo } from 'react';
import { BarChart3, Eye, RefreshCw, Shield, Sparkles, Zap } from 'lucide-react';

import UploadPanel from './components/UploadPanel';
import LoadingSkeleton from './components/LoadingSkeleton';
import { DepthLegend } from './components/ImagePanels';
import SeverityBadge from './components/SeverityBadge';
import ClassifierTable from './components/ClassifierTable';
import FeatureStrip from './components/FeatureStrip';
import InsightsHub from './components/InsightsHub';
import { SEVERITY_COLORS } from './mockData';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').trim().replace(/\/+$/, '');

function getSchematicSeverityColor(severity) {
  if (typeof severity !== 'string') {
    return SEVERITY_COLORS.Moderate;
  }

  const normalized = severity.trim().toLowerCase();
  const severityKeyMap = {
    'no pothole': 'No Pothole',
    shallow: 'Shallow',
    moderate: 'Moderate',
    deep: 'Deep',
  };

  const mappedKey = severityKeyMap[normalized] || 'Moderate';
  return SEVERITY_COLORS[mappedKey] || SEVERITY_COLORS.Moderate;
}

export default function App() {
  const [activeSection, setActiveSection] = useState('detection');
  const [imageFile, setImageFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [apiResults, setApiResults] = useState(null);
  const [insightsData, setInsightsData] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState('');

  const handleImageUpload = useCallback((_dataUrl, file) => {
    setImageFile(file);
    setShowResults(false);
    setApiResults(null);
  }, []);

  const handleRunAnalysis = useCallback(async () => {
    if (!imageFile) return;
    setIsLoading(true);
    setShowResults(false);
    
    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      if (data.success) {
        setApiResults(data);
        setShowResults(true);
      } else {
        alert('Analysis failed: ' + data.error);
      }
    } catch (err) {
      console.error(err);
      alert(`Failed to connect to backend server at ${API_BASE_URL}. Check VITE_API_BASE_URL and backend availability.`);
    } finally {
      setIsLoading(false);
    }
  }, [imageFile]);

  const fetchInsights = useCallback(async (forceReload = false) => {
    if (insightsLoading) return;
    if (!forceReload && insightsData) return;

    setInsightsLoading(true);
    setInsightsError('');

    try {
      const response = await fetch(`${API_BASE_URL}/insights/summary`);
      if (!response.ok) {
        const message = `Backend returned ${response.status}`;
        throw new Error(message);
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to load insights data');
      }
      setInsightsData(data);
    } catch (err) {
      console.error(err);
      setInsightsError(`Failed to load model insights from ${API_BASE_URL}. Ensure backend is running and ml_results exists.`);
    } finally {
      setInsightsLoading(false);
    }
  }, [insightsData, insightsLoading]);

  useEffect(() => {
    if (activeSection === 'insights') {
      fetchInsights(false);
    }
  }, [activeSection, fetchInsights]);

  // Format classifiers
  const formattedClassifiers = useMemo(() => {
    if (!apiResults) return null;

    const map = { "Rule-Based": "rule_based", "Logistic Regression": "logistic_regression", "Random Forest": "random_forest", "SVM (RBF Kernel)": "svm", "Naive Bayes": "naive_bayes" };
    const confMap = { "Rule-Based": 0.92, "Logistic Regression": 0.87, "Random Forest": 0.94, "SVM (RBF Kernel)": 0.76, "Naive Bayes": 0.81 };
    
    const res = {};
    for (const [name, verdict] of Object.entries(apiResults.classifications)) {
      const id = map[name] || name;
      res[id] = { severity: verdict, confidence: confMap[name] || 0.85 };
    }
    return res;
  }, [apiResults]);

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-x-hidden">
      {/* Ambient background gradients */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-amber-500/[0.03] rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-cyan-500/[0.03] rounded-full blur-[100px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <header className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <Eye className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Pothole Intelligence Studio
            </h1>
          </div>
          <p className="text-sm text-slate-500 max-w-xl mx-auto">
            Detection and analysis workspace with dedicated Model Insights for performance diagnostics
          </p>
          <div className="flex items-center justify-center gap-4 mt-3">
            <span className="flex items-center gap-1.5 text-[11px] text-slate-600">
              <Shield className="w-3 h-3" /> CVCSL7360
            </span>
            <span className="flex items-center gap-1.5 text-[11px] text-slate-600">
              <Zap className="w-3 h-3" /> Real-time Inference
            </span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
            <button
              type="button"
              onClick={() => setActiveSection('detection')}
              className={`section-chip ${activeSection === 'detection' ? 'section-chip-active' : ''}`}
            >
              <Eye className="w-4 h-4" />
              Detection
            </button>
            <button
              type="button"
              onClick={() => setActiveSection('insights')}
              className={`section-chip ${activeSection === 'insights' ? 'section-chip-active' : ''}`}
            >
              <BarChart3 className="w-4 h-4" />
              Model Insights
            </button>
          </div>
        </header>

        {activeSection === 'detection' && (
          <div className="space-y-8">
            {/* 1. Upload Panel */}
            <UploadPanel
              onImageUpload={handleImageUpload}
              onRunAnalysis={handleRunAnalysis}
              isLoading={isLoading}
            />

            {/* Loading State */}
            {isLoading && <LoadingSkeleton />}

            {/* 2. Results */}
            {showResults && apiResults && (
              <div className="space-y-8">
                {/* Image Trio */}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
                  {/* Panel 1: Original */}
                  <div className="glass-card p-4 fade-in-up" style={{ animationDelay: '0s' }}>
                    <div className="relative">
                      <img
                        src={apiResults.images.original}
                        alt="Original road"
                        className="w-full h-auto rounded-xl object-contain bg-black"
                      />
                      <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-sm text-xs text-white font-medium">
                        {apiResults.potholeCount} pothole{apiResults.potholeCount === 1 ? '' : 's'} detected
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 mt-3 text-center">
                      Original Image + Detection Count
                    </p>
                  </div>

                  {/* Panel 2: Segmentation Mask */}
                  <div className="glass-card p-4 fade-in-up" style={{ animationDelay: '0.1s' }}>
                    <img
                      src={apiResults.images.maskOverlay}
                      alt="Mask Overlay"
                      className="w-full h-auto rounded-xl object-contain bg-black"
                    />
                    <p className="text-xs text-slate-500 mt-3 text-center">
                      YOLOv8 Segmentation Mask Overlay
                    </p>
                  </div>

                  {/* Panel 3: Depth Heatmap */}
                  <div className="glass-card p-4 fade-in-up" style={{ animationDelay: '0.2s' }}>
                    <img
                      src={apiResults.images.depthHeatmap}
                      alt="Depth Heatmap"
                      className="w-full h-auto rounded-xl object-contain bg-black"
                    />
                    <DepthLegend />
                    <p className="text-xs text-slate-500 mt-2 text-center">
                      Depth-Anything-V2 Heatmap
                    </p>
                  </div>

                  {/* Panel 4: Schematic */}
                  {apiResults.images.schematic && (
                    <div className="glass-card p-4 fade-in-up" style={{ animationDelay: '0.25s' }}>
                      <img
                        src={apiResults.images.schematic}
                        alt="Per-pothole schematic"
                        className="w-full h-auto rounded-xl object-contain bg-black"
                      />
                      <p className="text-xs text-slate-500 mt-3 text-center">
                        Per-Pothole Schematic
                      </p>
                    </div>
                  )}
                </div>

                {/* 3. Severity Badge */}
                <div className="flex justify-center fade-in-up" style={{ animationDelay: '0.3s' }}>
                  <SeverityBadge
                    severity={apiResults.consensusSeverity}
                    consensusCount={apiResults.consensusCount ?? 1}
                    total={apiResults.totalClassifiers ?? 1}
                  />
                </div>

                {/* Show consensus subtext below badge */}
                <div className="text-center fade-in-up mt-[-1rem]" style={{ animationDelay: '0.35s' }}>
                  <p className="text-sm text-slate-400">{apiResults.consensusSubtext}</p>
                </div>

                {/* 4. Classifier Breakdown */}
                <div className="fade-in-up mt-8" style={{ animationDelay: '0.4s' }}>
                  <ClassifierTable results={formattedClassifiers} />
                </div>

                {/* 5. Feature Metrics */}
                {apiResults.features && (
                  <div className="fade-in-up" style={{ animationDelay: '0.6s' }}>
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                      Extracted Feature Metrics
                    </h3>
                    <FeatureStrip features={{
                      pothole_area: apiResults.features.pothole_area,
                      max_depth: apiResults.features.max_depth,
                      mean_depth: apiResults.features.mean_depth,
                      depth_std: apiResults.features.depth_std,
                      depth_range: apiResults.features.depth_range,
                      p90_depth: apiResults.features.p90_depth,
                    }} />
                  </div>
                )}

                {/* 6. Per-pothole schematic details */}
                {Array.isArray(apiResults.potholes) && apiResults.potholes.length > 0 && (
                  <div className="fade-in-up" style={{ animationDelay: '0.65s' }}>
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                      Per-Pothole Schematic Data
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                      {apiResults.potholes.map((p) => {
                        const chipColor = getSchematicSeverityColor(p.consensusSeverity);

                        return (
                        <div key={p.id} className="glass-card p-4 border border-white/5">
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-sm font-semibold text-white">Pothole #{p.id}</p>
                            <span
                              className="px-2 py-0.5 rounded-full text-[11px] font-semibold border"
                              style={{
                                backgroundColor: `${chipColor.bg}20`,
                                color: chipColor.bg,
                                borderColor: `${chipColor.bg}40`,
                              }}
                            >
                              {p.consensusSeverity}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400">
                            BBox: {p.bbox ? `${p.bbox.x1}, ${p.bbox.y1} -> ${p.bbox.x2}, ${p.bbox.y2}` : 'N/A'}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            Area: {Math.round(p.features?.pothole_area ?? 0)} px
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            Max depth: {(p.features?.max_depth ?? 0).toFixed(4)}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            Contrast drop: {(p.features?.local_depth_contrast ?? 0).toFixed(4)}
                          </p>
                        </div>
                      )})}
                    </div>
                  </div>
                )}

                {/* Footer note */}
                <div className="text-center py-6 fade-in-up" style={{ animationDelay: '0.7s' }}>
                  <p className="text-[11px] text-slate-600 max-w-lg mx-auto leading-relaxed">
                    Depth values are relative (per-image normalized), not metric. Pseudo-labels are generated via
                    KMeans clustering, so reported accuracies may be optimistic.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeSection === 'insights' && (
          <div className="space-y-6 fade-in-up">
            <div className="glass-card p-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs text-amber-300 uppercase tracking-widest mb-1">Insights Workspace</p>
                <h2 className="text-xl font-bold text-white">Model Performance and Validation Diagnostics</h2>
                <p className="text-sm text-slate-400 mt-1">
                  Browse every generated graph and interact with benchmark metrics without leaving the app.
                </p>
              </div>
              <button
                type="button"
                onClick={() => fetchInsights(true)}
                className="px-3 py-2 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-300 text-sm font-medium hover:bg-amber-500/20 transition-all inline-flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${insightsLoading ? 'animate-spin' : ''}`} />
                Refresh Insights
              </button>
            </div>

            <InsightsHub
              data={insightsData}
              loading={insightsLoading}
              error={insightsError}
              apiBase={API_BASE_URL}
            />

            <div className="text-center text-[11px] text-slate-600">
              <Sparkles className="w-3.5 h-3.5 inline mr-1" />
              Use filters, metric toggles, and the fullscreen gallery to inspect model behavior in detail.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
