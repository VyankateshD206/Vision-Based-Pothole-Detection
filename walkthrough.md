# Pothole Severity Detection — Web UI Walkthrough

## What Was Built
A production-grade, dark-themed React dashboard for the Vision-Based Pothole Severity Detection system. All data is mocked/static — no backend required.

**Tech stack:** Vite + React + Tailwind CSS v4 + Recharts + Lucide Icons

**Location:** `web-ui/` within the project root

## UI Flow

### 1. Hero / Upload Panel
Dark glassmorphism upload zone with amber dashed border, classifier pill toggles, and gradient CTA button.

![Initial upload state](C:/Users/honpa/.gemini/antigravity/brain/887236c1-f71f-48da-a8dc-a0b6bd29fcd6/header_and_upload_panel_1775407540645.png)

---

### 2. Image Trio (after analysis)
Three-column grid: Original (with detection count badge), YOLOv8 mask overlay (orange-red with bounding box), and Depth-Anything-V2 heatmap (inferno colormap with legend).

![Results image trio](C:/Users/honpa/.gemini/antigravity/brain/887236c1-f71f-48da-a8dc-a0b6bd29fcd6/image_trio_section_1775407554406.png)

---

### 3. Severity Badge + Classifier Breakdown + Accuracy Chart
- **Severity Badge:** Pulsing red glow for "Deep" verdict, consensus count
- **Classifier Table:** Rule-Based (cyan/monospace) vs ML models with confidence bars + hover tooltips
- **Bar Chart:** Recharts gradient bars with 95% CI error bars

![Severity and classifiers](C:/Users/honpa/.gemini/antigravity/brain/887236c1-f71f-48da-a8dc-a0b6bd29fcd6/severity_and_classifiers_1775407566578.png)

---

### 4. Feature Metrics Strip + Footer
Six metric cards (Pothole Area, Max/Mean Depth, Std, Range, P90) with icons and mini gauge bars. Footer disclaimer about relative depth and pseudo-labels.

![Feature metrics](C:/Users/honpa/.gemini/antigravity/brain/887236c1-f71f-48da-a8dc-a0b6bd29fcd6/feature_metrics_bottom_1775407577223.png)

---

## Demo Recording

![Full flow recording](C:/Users/honpa/.gemini/antigravity/brain/887236c1-f71f-48da-a8dc-a0b6bd29fcd6/dashboard_screenshots_1775407517921.webp)

## Files Created

| File | Purpose |
|------|---------|
| `web-ui/vite.config.js` | Vite + Tailwind CSS v4 plugin config |
| `web-ui/index.html` | HTML shell with Inter font, SEO meta |
| `web-ui/src/index.css` | Tailwind theme, glass effects, animations |
| `web-ui/src/mockData.js` | All mock data, severity colors, accuracies |
| `web-ui/src/App.jsx` | Main layout wiring all sections |
| `web-ui/src/components/UploadPanel.jsx` | Drag-and-drop upload + classifier toggles |
| `web-ui/src/components/LoadingSkeleton.jsx` | Shimmer loading state |
| `web-ui/src/components/ImagePanels.jsx` | Canvas-based mask overlay + depth heatmap |
| `web-ui/src/components/SeverityBadge.jsx` | Animated severity verdict badge |
| `web-ui/src/components/ClassifierTable.jsx` | Classifier breakdown with confidence bars |
| `web-ui/src/components/FeatureStrip.jsx` | 6 feature metric cards with gauges |
| `web-ui/src/components/AccuracyChart.jsx` | Recharts accuracy bar chart with CI |

## Running

```bash
cd web-ui
npm run dev
# → http://localhost:5173/
```
