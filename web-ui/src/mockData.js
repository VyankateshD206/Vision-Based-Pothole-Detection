// Mock data for the pothole detection UI demo

export const SEVERITY_COLORS = {
  'No Pothole': { bg: '#22c55e', text: '#166534', ring: 'rgba(34,197,94,0.4)' },
  'Shallow':    { bg: '#eab308', text: '#854d0e', ring: 'rgba(234,179,8,0.4)' },
  'Moderate':   { bg: '#ea580c', text: '#9a3412', ring: 'rgba(234,88,12,0.4)' },
  'Deep':       { bg: '#ef4444', text: '#991b1b', ring: 'rgba(239,68,68,0.5)' },
};

export const CLASSIFIERS = [
  { id: 'rule_based', name: 'Rule-Based', type: 'rule' },
  { id: 'logistic_regression', name: 'Logistic Regression', type: 'ml' },
  { id: 'random_forest', name: 'Random Forest', type: 'ml' },
  { id: 'svm', name: 'SVM (RBF Kernel)', type: 'ml' },
  { id: 'naive_bayes', name: 'Naive Bayes', type: 'ml' },
];

export const MOCK_RESULTS = {
  classifiers: {
    rule_based:           { severity: 'Deep',     confidence: 0.92 },
    logistic_regression:  { severity: 'Deep',     confidence: 0.87 },
    random_forest:        { severity: 'Deep',     confidence: 0.94 },
    svm:                  { severity: 'Moderate', confidence: 0.76 },
    naive_bayes:          { severity: 'Deep',     confidence: 0.81 },
  },
  features: {
    pothole_area: 12847,
    max_depth: 0.9412,
    mean_depth: 0.6234,
    depth_std: 0.1876,
    depth_range: 0.7123,
    p90_depth: 0.8891,
    height: 187,
    width: 214,
    box_area: 40018,
    nonpothole_area: 27171,
    min_depth: 0.2289,
  },
  potholeCount: 1,
  maskAreaPercent: 8.4,
  consensus: 'Deep',
  consensusCount: 4,
  totalClassifiers: 5,
};

export const MODEL_ACCURACIES = [
  { name: 'Logistic Reg.', accuracy: 0.87, ci_lower: 0.83, ci_upper: 0.91 },
  { name: 'Random Forest', accuracy: 0.91, ci_lower: 0.87, ci_upper: 0.95 },
  { name: 'SVM',           accuracy: 0.89, ci_lower: 0.85, ci_upper: 0.93 },
  { name: 'Naive Bayes',   accuracy: 0.78, ci_lower: 0.72, ci_upper: 0.84 },
];
