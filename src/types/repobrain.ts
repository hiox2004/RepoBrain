// src/types/repobrain.ts

export type NodeKind = 'callable' | 'method' | 'type_definition';

export interface ASTParentNode {
  parent_id: string;
  file_path: string;
  language: 'python' | 'typescript';
  imports_header: string;
  enclosing_scope: string | null;
  git_blob_sha: string;
}

export interface ASTChildNode {
  child_id: string;
  parent_id: string;
  file_path: string;
  node_kind: NodeKind;
  symbol_name: string;
  signature: string;
  docstring: string | null;
  body_code: string;
  start_line: number;
  end_line: number;
}

export interface EpisodicFixRecord {
  episode_id: string;
  error_signature: string;
  target_symbol: string;
  file_path: string;
  root_cause_summary: string;
  resolution_diff: string;
  created_at?: string;
}

export interface RetrievedCodeContext {
  file_path: string;
  language: 'python' | 'typescript';
  symbol_name: string;
  node_kind: NodeKind;
  start_line: number;
  end_line: number;
  git_blob_sha: string;
  dense_rank: number | null;
  sparse_rank: number | null;
  rrf_score: number;
  cross_encoder_score: number;
  imports_header: string;
  enclosing_scope: string | null;
  body_code: string;
  related_episodes: EpisodicFixRecord[];
}

export interface PatchAndTestResponse {
  task_id: string;
  iteration: number;
  patch_applied: boolean;
  static_check_passed: boolean;
  tests_passed: boolean;
  exit_code: number;
  rolled_back: boolean;
  filtered_traceback: string;
  reindexed_files: string[];
  recorded_episode_id: string | null;
}
