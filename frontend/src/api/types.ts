export interface Prediction {
  class_index: number;
  class_name: string;
  probability: number;
}

export interface CropPrediction {
  plant: string;
  probability: number;
}

export interface ConditionPrediction {
  class_index: number;
  class_name: string;
  plant: string;
  condition: string;
  joint_probability: number;
  conditional_probability: number;
}

export interface TaxonomyHierarchy {
  method: "crop_first_rejection_v2";
  selected_crop: string;
  selected_class_name: string | null;
  crops: CropPrediction[];
  conditions: ConditionPrediction[];
  crop_confident: boolean;
  crop_margin: number;
  confidence_threshold: number;
  margin_threshold: number;
  decision_reason: string;
}

export interface DiseaseKnowledge {
  class_name: string;
  plant: string;
  condition: string;
  is_healthy: boolean;
  symptoms: string;
  educational_note: string;
}

export interface TimingBreakdown {
  preprocess_ms: number;
  prediction_ms: number;
  gradcam_ms: number;
  total_ms: number;
}

export interface GradCamPayload {
  target_class_index: number;
  target_class_name: string;
  heatmap_data_url: string;
  overlay_data_url: string;
}

export interface LesionColorShare {
  name: string;
  proportion: number;
}

export interface LesionRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  centroid_x: number;
  centroid_y: number;
  area_pixels: number;
  area_percent_of_leaf: number;
  circularity: number;
  aspect_ratio: number;
  shape: string;
  color: string;
}

export interface LesionAnalysis {
  method: "opencv_exg_hsv_components_v1";
  image_size: [number, number];
  leaf_area_pixels: number;
  leaf_coverage_percent: number;
  lesion_area_pixels: number;
  lesion_coverage_percent: number;
  lesion_count: number;
  median_lesion_area_percent: number;
  largest_lesion_area_percent: number;
  mean_circularity: number;
  dominant_colors: LesionColorShare[];
  distribution: string;
  regions: LesionRegion[];
  overlay_data_url: string;
}

export interface ClassificationResult {
  predictions: Prediction[];
  hierarchy: TaxonomyHierarchy;
  knowledge: DiseaseKnowledge | null;
  lesion_analysis: LesionAnalysis | null;
  model_name: string;
  checkpoint_path: string;
  checkpoint_id: string;
  image_size: number;
  input_size: [number, number];
  target_layer_name: string | null;
  timings: TimingBreakdown;
  warnings: string[];
  gradcam: GradCamPayload | null;
}

export interface QwenStatus {
  supported_platform: boolean;
  dependency_available: boolean;
  weights_cached: boolean;
  ready: boolean;
  model_id: string;
  detail: string;
}

export interface QwenAnswer {
  raw_answer: string | null;
  observations: string[];
  message: string;
  action: string;
  refused: boolean;
  reasons: string[];
  sources: string[];
  model_id: string;
  scope: string;
  evidence_boundary: string;
}

export type AdviceProviderId = "openai" | "anthropic" | "gemini";

export interface AdviceProviderStatus {
  provider: AdviceProviderId;
  display_name: string;
  configured: boolean;
  model_id: string;
  detail: string;
}

export interface AdviceProvidersResponse {
  providers: AdviceProviderStatus[];
}

export interface ManagementAdvice {
  provider: AdviceProviderId;
  model_id: string;
  message: string;
  action: string;
  refused: boolean;
  reasons: string[];
  sources: string[];
  scope: string;
  evidence_boundary: string;
}

export interface ClassifierStatus {
  ready: boolean;
  checkpoint: string;
  device: string;
  target_layer: string | null;
  detail: string;
}

export interface DemoHealth {
  status: "ok" | "degraded";
  classifier: ClassifierStatus;
  qwen: QwenStatus;
}

export interface ClassifyOptions {
  topK: number;
  includeGradcam: boolean;
  device?: "auto" | "cpu" | "cuda" | "mps";
  targetLayer?: string;
}

export type FeatureState<T> =
  | { status: "idle"; data: null; error: null }
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: string };
