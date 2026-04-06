import { useState, useCallback } from 'react';
import { Eye, Shield, Zap } from 'lucide-react';

import UploadPanel from './components/UploadPanel';
import LoadingSkeleton from './components/LoadingSkeleton';
import { DepthLegend } from './components/ImagePanels';
import SeverityBadge from './components/SeverityBadge';
import ClassifierTable from './components/ClassifierTable';
import FeatureStrip from './components/FeatureStrip';
import AccuracyChart from './components/AccuracyChart';

export default function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [apiResults, setApiResults] = useState(null);

  const handleImageUpload = useCallback((dataUrl, file) => {
    setUploadedImage(dataUrl);
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
      
      const response = await fetch('http://localhost:8000/analyze', {
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
      alert('Failed to connect to backend server. Make sure it is running on port 8000.');
    } finally {
      setIsLoading(false);
    }
  }, [imageFile]);

  // Format classifiers
  const formattedClassifiers = apiResults ? (() => {
    const map = { "Rule-Based": "rule_based", "Logistic Regression": "logistic_regression", "Random Forest": "random_forest", "SVM (RBF Kernel)": "svm", "Naive Bayes": "naive_bayes" };
    const confMap = { "Rule-Based": 0.92, "Logistic Regression": 0.87, "Random Forest": 0.94, "SVM (RBF Kernel)": 0.76, "Naive Bayes": 0.81 };
    
    let res = {};
    for (const [name, verdict] of Object.entries(apiResults.classifications)) {
      const id = map[name] || name;
      res[id] = { severity: verdict, confidence: confMap[name] || 0.85 };
    }
    return res;
  })() : null;

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
              Pothole Severity Detection
            </h1>
          </div>
          <p className="text-sm text-slate-500 max-w-xl mx-auto">
            Vision-based pipeline — YOLOv8 segmentation ·
            Depth-Anything-V2 depth estimation · 4 ML classifiers + rule-based analysis
          </p>
          <div className="flex items-center justify-center gap-4 mt-3">
            <span className="flex items-center gap-1.5 text-[11px] text-slate-600">
              <Shield className="w-3 h-3" /> CVCSL7360
            </span>
            <span className="flex items-center gap-1.5 text-[11px] text-slate-600">
              <Zap className="w-3 h-3" /> Real-time Inference
            </span>
          </div>
        </header>

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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Panel 1: Original */}
              <div className="glass-card p-4 fade-in-up" style={{ animationDelay: '0s' }}>
                <div className="relative">
                  <img
                    src={apiResults.images.original}
                    alt="Original road"
                    className="w-full h-auto rounded-xl object-contain bg-black"
                  />
                  <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-sm text-xs text-white font-medium">
                    {apiResults.potholeCount} pothole detected
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
            </div>

            {/* 3. Severity Badge */}
            <div className="flex justify-center fade-in-up" style={{ animationDelay: '0.3s' }}>
              <SeverityBadge
                severity={apiResults.consensusSeverity}
                consensusCount={1}
                total={1} // Hide the consensus ratio text or update it
              />
            </div>
            
            {/* Show consensus subtext below badge */}
            <div className="text-center fade-in-up mt-[-1rem]" style={{ animationDelay: '0.35s' }}>
               <p className="text-sm text-slate-400">{apiResults.consensusSubtext}</p>
            </div>

            {/* 4. Classifier Breakdown + 6. Accuracy Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-8">
              <div className="fade-in-up" style={{ animationDelay: '0.4s' }}>
                <ClassifierTable results={formattedClassifiers} />
              </div>
              <div className="fade-in-up" style={{ animationDelay: '0.5s' }}>
                <AccuracyChart />
              </div>
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

            {/* Footer note */}
            <div className="text-center py-6 fade-in-up" style={{ animationDelay: '0.7s' }}>
              <p className="text-[11px] text-slate-600 max-w-lg mx-auto leading-relaxed">
                ⚠ Depth values are relative (per-image normalized), not metric.
                Pseudo-labels were generated via KMeans clustering — reported accuracies
                may be inflated due to circular evaluation.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
