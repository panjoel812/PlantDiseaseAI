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
  method:
    | "crop_first_rejection_v2"
    | "independent_crop_then_disease_v3"
    | "local_catalog_then_disease_v4"
    | "external_species_then_disease_v4";
  selected_crop: string;
  selected_class_name: string | null;
  crops: CropPrediction[];
  conditions: ConditionPrediction[];
  crop_confident: boolean;
  crop_margin: number;
  confidence_threshold: number;
  margin_threshold: number;
  decision_reason: string;
  crop_source?:
    | "joint_disease_distribution"
    | "independent_mobilenet_v2_crop_checkpoint"
    | "local_leaf114_checkpoint"
    | "plantnet_api";
  disease_confident?: boolean;
  disease_confidence?: number;
  disease_margin?: number;
  disease_confidence_threshold?: number;
  disease_margin_threshold?: number;
  disease_decision_reason?: string;
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

export interface LesionFocusEvidence {
  method: "opencv_healthy_veto_roi_ensemble_v1";
  applied: boolean;
  selected_crop: string;
  reason: string;
  lesion_coverage_percent: number;
  healthy_coverage_threshold: number;
  lesion_count: number;
  roi_count: number;
  full_healthy_probability: number;
  focused_predictions: Prediction[];
  evidence_boundary: string;
}

export interface LeafShapeFeatures {
  area_pixels: number;
  coverage_percent: number;
  aspect_ratio: number;
  circularity: number;
  solidity: number;
  extent: number;
  border_touch_ratio: number;
  component_dominance: number;
}

export interface TargetPoint {
  x: number;
  y: number;
}

export interface LeafPurityEvidence {
  accepted: boolean;
  coverage_percent: number;
  border_touch_ratio: number;
  fragment_count: number;
  click_contained: boolean | null;
  probable_foreground_retention: number | null;
  principal_axis_aspect_ratio: number;
  axis_band_retention: number | null;
  coverage_range: [number, number];
  max_border_touch_ratio: number;
  min_probable_foreground_retention: number;
  min_axis_band_retention: number;
  reason: string;
}

export interface LeafIsolation {
  method: "opencv_target_leaf_v2";
  selection_mode: "automatic" | "click_grabcut";
  target_point: TargetPoint | null;
  purity: LeafPurityEvidence;
  accepted: boolean;
  reason: string;
  image_size: [number, number];
  bounding_box: [number, number, number, number] | null;
  shape: LeafShapeFeatures | null;
  cutout_data_url: string | null;
}

export interface LeafSelectionRequired {
  code: "leaf_selection_required";
  message: string;
  leaf_isolation: LeafIsolation;
}

export interface CornAbioticEvidence {
  method: "opencv_corn_midrib_stress_v1";
  status: "suspected_abiotic_nutrient_stress" | "unknown_visible_stress";
  suspected: boolean;
  abnormal_coverage_percent: number;
  central_axis_share: number;
  longitudinal_continuity: number;
  bilateral_similarity: number;
  off_axis_lesion_coverage_percent: number;
  abnormal_coverage_threshold: number;
  central_axis_share_threshold: number;
  longitudinal_continuity_threshold: number;
  bilateral_similarity_threshold: number;
  off_axis_lesion_coverage_threshold: number;
  reason: string;
  evidence_boundary: string;
  overlay_data_url: string;
}

export interface PlantNoveltyEvidence {
  method: "frozen_encoder_multi_prototype_cosine_v1";
  accepted: boolean;
  candidate_plant: string;
  classifier_agrees: boolean;
  similarity: number;
  margin: number;
  similarity_threshold: number;
  margin_threshold: number;
  alternatives: Array<{ plant: string; similarity: number }>;
  reason: string;
  evidence_boundary: string;
}

export interface PlantSpeciesPrediction {
  scientific_name: string;
  common_name: string | null;
  family: string | null;
  genus: string | null;
  score: number;
  routed_plant: string | null;
}

export interface PlantIdentityEvidence {
  provider: "plantnet";
  method: "plantnet_leaf_species_v2";
  model_version: string | null;
  remaining_requests: number | null;
  predictions: PlantSpeciesPrediction[];
  evidence_boundary: string;
}

export interface PlantIdentityStatus {
  provider: "plantnet";
  display_name: string;
  configured: boolean;
  scope: string;
  detail: string;
}

export interface ClassificationResult {
  predictions: Prediction[];
  hierarchy: TaxonomyHierarchy;
  knowledge: DiseaseKnowledge | null;
  leaf_isolation?: LeafIsolation | null;
  plant_novelty?: PlantNoveltyEvidence | null;
  plant_identity?: PlantIdentityEvidence | null;
  lesion_analysis: LesionAnalysis | null;
  lesion_focus?: LesionFocusEvidence | null;
  abiotic_evidence?: CornAbioticEvidence | null;
  model_name: string;
  checkpoint_path: string;
  checkpoint_id: string;
  image_size: number;
  input_size: [number, number];
  disease_input_method:
    | "original_image_v1"
    | "opencv_isolated_leaf_neutral_background_v1"
    | "opencv_isolated_leaf_plus_lesion_rois_v2";
  disease_input_size: [number, number] | null;
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
  crop_classifier?: {
    ready: boolean;
    checkpoint: string | null;
    detail: string;
  };
  openworld_gate?: {
    ready: boolean;
    index: string | null;
    detail: string;
  };
  plant_identity?: PlantIdentityStatus;
  qwen: QwenStatus;
}

export interface ClassifyOptions {
  topK: number;
  includeGradcam: boolean;
  device?: "auto" | "cpu" | "cuda" | "mps";
  targetLayer?: string;
  targetPoint?: TargetPoint;
}

export type FeatureState<T> =
  | { status: "idle"; data: null; error: null }
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: string };
