export type Model = "HighQuality" | "Fast";
export type OcrStrategy = "All" | "Auto" | "Off";
export type SegmentationStrategy = "LayoutAnalysis" | "Page";

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface OcrResult {
  text: string;
  confidence: number;
}

export interface Segment {
  segment_id: string;
  bbox: BoundingBox;
  content: string;
  html: string;
  image: string;
  markdown: string;
  ocr: OcrResult[];
  page_height: number;
  page_number: number;
  page_width: number;
  segment_type: string;
}

export interface Chunk {
  segments: Segment[];
  chunk_length: number;
}

export interface ExtractedField {
  name: string;
  field_type: string;
  value: any;
}

export interface ExtractedJson {
  title: string;
  schema_type: string;
  extracted_fields: ExtractedField[];
}

export interface OutputResponse {
  chunks: Chunk[];
  extracted_json?: ExtractedJson;
}

export interface TaskResponse {
  configuration: {
    model: Model;
    ocr_strategy: OcrStrategy;
    target_chunk_length: number;
  };
  created_at: string;
  expires_at?: string;
  file_name: string;
  finished_at?: string;
  input_file_url: string;
  message: string;
  output?: OutputResponse;
  page_count: number;
  status: "Starting" | "Processing" | "Succeeded" | "Failed" | "Cancelled";
  task_id: string;
  task_url: string;
}

export interface AggregateResults {
  totalTime: number;
  totalPages: number;
  pagesPerSecond: number;
}

export type WorkerResult = {
  totalPages: number;
  startTime: number;
  endTime: number;
  failureTypes: FailureTypes;
};

export type FailureTypes = {
  startTaskFailed: number;
  pollTaskFailed: number;
  taskStatusFailed: number;
};

export type ModelConfig = {
  model: Model;
  segmentationStrategy: SegmentationStrategy;
  ocrStrategy: OcrStrategy;
  percentage: number;
};
