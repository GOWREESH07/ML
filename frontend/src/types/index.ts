export interface TumorInfo {
  name: string;
  description: string;
  general_symptom_patterns: string[];
  associated_conditions: string[];
  general_lifestyle_notes: string[];
  disclaimer: string;
}

export interface PredictionResult {
  predicted_class: "glioma" | "meningioma" | "notumor" | "pituitary" | string;
  confidence: number;
  uncertainty: number;
  severity_bucket: "low" | "medium" | "high";
  foreground_ratio: number;
  heatmap_base64: string;
  info: TumorInfo;
  disclaimer: string;
  low_confidence_flag: boolean;
  class_probabilities: Record<string, number>;
  class_uncertainties: Record<string, number>;
}

export interface BackendHealth {
  status: string;
  model_loaded: boolean;
  classes: string[];
  uncertainty_threshold: number;
}
