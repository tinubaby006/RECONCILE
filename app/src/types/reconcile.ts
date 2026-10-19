export type ColumnRole = 
  | 'match_key' 
  | 'entity' 
  | 'date' 
  | 'amount' 
  | 'compare' 
  | 'ignore';

export type RecordStatus = 
  | 'matched' 
  | 'discrepancy' 
  | 'needs_review' 
  | 'missing_in_b' 
  | 'missing_in_a' 
  | 'duplicate';

export interface ColumnMeta {
  name: string;
  inferred_type: 'string' | 'numeric' | 'date' | 'id';
  non_null_count: number;
  unique_count: number;
  sample_values: (string | number)[];
}

export interface DatasetMeta {
  file_path: string;
  file_name: string;
  file_type: 'csv' | 'xlsx' | 'json';
  total_rows: number;
  sheets: string[];
  active_sheet?: string | null;
  columns: ColumnMeta[];
  file_size?: string;
}

export interface ColumnMapping {
  col_a: string;
  col_b: string | null;
  role: ColumnRole;
  confidence: number;
  status: 'mapped' | 'unmapped' | 'ignored';
  sample_a?: string | null;
  sample_b?: string | null;
}

export interface FieldDifference {
  field: string;
  val_a: unknown;
  val_b: unknown;
  diff_type: 'amount_delta' | 'date_diff' | 'text_mismatch' | 'missing';
  delta?: number | null;
  description: string;
}

export interface CandidateMatch {
  candidate_id: string;
  record_b: Record<string, unknown>;
  score: number;
  source_b: string;
  entity_b?: string | null;
  amount_b?: number | null;
  date_b?: string | null;
  reason: string;
}

export interface ReconciliationRecord {
  id: string;
  status: RecordStatus;
  status_label: string;
  entity: string;
  reference: string;
  record_a?: Record<string, unknown> | null;
  record_b?: Record<string, unknown> | null;
  source_a?: string | null;
  source_b?: string | null;
  amount_a?: number | null;
  amount_b?: number | null;
  amount_diff?: number | null;
  date_a?: string | null;
  date_b?: string | null;
  differences: FieldDifference[];
  candidates: CandidateMatch[];
  confidence_score?: number | null;
  user_override?: 'confirmed' | 'unmatched' | 'switched_candidate' | null;
}

export interface ReconciliationSummary {
  total_a: number;
  total_b: number;
  total_records: number;
  matched_count: number;
  discrepancies_count: number;
  missing_in_b_count: number;
  missing_in_a_count: number;
  duplicates_count: number;
  needs_review_count: number;
  total_variance: number;
}

export type WorkflowStep = 'import' | 'mapping' | 'results' | 'detail';
