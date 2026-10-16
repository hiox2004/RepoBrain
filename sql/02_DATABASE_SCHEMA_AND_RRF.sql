-- sql/02_DATABASE_SCHEMA_AND_RRF.sql
-- Production PostgreSQL schema, split-token identifier normalizer, and Two-Stage Hybrid RRF (k=60) query

CREATE EXTENSION IF NOT EXISTS vector;

-- Guardrail #3: Immutable identifier splitter for camelCase, PascalCase, and snake_case
CREATE OR REPLACE FUNCTION normalize_code_identifiers(input_text TEXT)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE PARALLEL SAFE
AS $$
SELECT COALESCE(
  input_text || ' ' ||
  LOWER(
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        REGEXP_REPLACE(COALESCE(input_text, ''), '([A-Z]+)([A-Z][a-z])', '\1 \2', 'g'),
        '([a-z0-9])([A-Z])', '\1 \2', 'g'
      ),
      '[_./:-]+', ' ', 'g'
    )
  ),
  ''
);
$$;

-- Layer 1: AST Parent Nodes (Structural Context Wrapper)
CREATE TABLE IF NOT EXISTS ast_parents (
  parent_id UUID PRIMARY KEY,
  file_path TEXT NOT NULL UNIQUE,
  language TEXT NOT NULL CHECK (language IN ('python', 'typescript')),
  imports_header TEXT NOT NULL DEFAULT '',
  enclosing_scope TEXT,
  git_blob_sha TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Layer 1: AST Child Nodes (Indexed Search Units)
CREATE TABLE IF NOT EXISTS ast_children (
  child_id UUID PRIMARY KEY,
  parent_id UUID NOT NULL REFERENCES ast_parents(parent_id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  node_kind TEXT NOT NULL CHECK (node_kind IN ('callable', 'method', 'type_definition')),
  symbol_name TEXT NOT NULL,
  signature TEXT NOT NULL,
  docstring TEXT,
  body_code TEXT NOT NULL,
  start_line INT NOT NULL CHECK (start_line >= 1),
  end_line INT NOT NULL CHECK (end_line >= start_line),
  embedding vector(768) NOT NULL,
  fts_tokens tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', normalize_code_identifiers(symbol_name)), 'A') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(signature)), 'B') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(COALESCE(docstring, ''))), 'C') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(body_code)), 'D')
  ) STORED
);

CREATE INDEX IF NOT EXISTS idx_ast_children_embedding_hnsw
  ON ast_children USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_ast_children_fts_gin
  ON ast_children USING gin (fts_tokens);

CREATE INDEX IF NOT EXISTS idx_ast_children_parent_id
  ON ast_children (parent_id);

-- Layer 2: Episodic Self-Correcting Diagnostic Memory
CREATE TABLE IF NOT EXISTS project_episodes (
  episode_id UUID PRIMARY KEY,
  error_signature TEXT NOT NULL,
  target_symbol TEXT NOT NULL,
  file_path TEXT NOT NULL,
  root_cause_summary TEXT NOT NULL,
  resolution_diff TEXT NOT NULL,
  embedding vector(768) NOT NULL,
  fts_tokens tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', normalize_code_identifiers(target_symbol)), 'A') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(error_signature)), 'B') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(root_cause_summary)), 'C')
  ) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_episodes_embedding_hnsw
  ON project_episodes USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_project_episodes_fts_gin
  ON project_episodes USING gin (fts_tokens);

-- Parameterized Hybrid RRF Query (Guardrails #4 & #5)
-- $1 = query_embedding::vector(768), $2 = raw_query_text::text, $3 = rrf_pool_size (default 25)
/*
WITH lexical_query AS (
  SELECT to_tsquery(
    'simple',
    ARRAY_TO_STRING(
      ARRAY(
        SELECT DISTINCT token
        FROM REGEXP_SPLIT_TO_TABLE(
          TRIM(REGEXP_REPLACE(normalize_code_identifiers($2), '[^a-zA-Z0-9_]+', ' ', 'g')),
          '\s+'
        ) AS token
        WHERE LENGTH(token) > 1
      ),
      ' | '
    )
  ) AS ts_q
),
dense_candidates AS (
  SELECT
    child_id,
    parent_id,
    ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector(768)) AS dense_rank
  FROM ast_children
  ORDER BY embedding <=> $1::vector(768)
  LIMIT 40
),
sparse_candidates AS (
  SELECT
    c.child_id,
    c.parent_id,
    ROW_NUMBER() OVER (
      ORDER BY ts_rank_cd(c.fts_tokens, lq.ts_q, 32) DESC
    ) AS sparse_rank
  FROM ast_children c
  CROSS JOIN lexical_query lq
  WHERE lq.ts_q IS NOT NULL
    AND c.fts_tokens @@ lq.ts_q
  ORDER BY sparse_rank
  LIMIT 40
),
rrf_fused AS (
  SELECT
    COALESCE(d.child_id, s.child_id) AS child_id,
    COALESCE(d.parent_id, s.parent_id) AS parent_id,
    d.dense_rank,
    s.sparse_rank,
    (COALESCE(1.0 / (60 + d.dense_rank), 0.0) +
     COALESCE(1.0 / (60 + s.sparse_rank), 0.0))::float8 AS rrf_score
  FROM dense_candidates d
  FULL OUTER JOIN sparse_candidates s ON d.child_id = s.child_id
  ORDER BY rrf_score DESC
  LIMIT $3
)
SELECT
  c.child_id,
  c.symbol_name,
  c.node_kind,
  c.signature,
  c.docstring,
  c.body_code,
  c.start_line,
  c.end_line,
  p.file_path,
  p.language,
  p.imports_header,
  p.enclosing_scope,
  p.git_blob_sha,
  r.dense_rank,
  r.sparse_rank,
  r.rrf_score
FROM rrf_fused r
JOIN ast_children c ON r.child_id = c.child_id
JOIN ast_parents p ON r.parent_id = p.parent_id
ORDER BY r.rrf_score DESC;
*/
