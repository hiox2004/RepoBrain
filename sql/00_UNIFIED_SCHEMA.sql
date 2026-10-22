-- sql/00_UNIFIED_SCHEMA.sql
-- RepoBrain V2 & ResearchBrain OS: Complete Unified PostgreSQL 16 Schema
-- Enforces: Layer 1 (AST), Layer 2 (Episodes), Layer 3 (ResearchBrain CRAG), Layer 4 (Templates)

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Guardrail #3: Sub-Token Identifier Normalizer
-- Splits camelCase, PascalCase, and snake_case while preserving original token
-- ============================================================================
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

-- ============================================================================
-- LAYER 1: Structural AST Memory (ast_parents & ast_children)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ast_parents (
  parent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  file_path TEXT NOT NULL UNIQUE,
  language TEXT NOT NULL CHECK (language IN ('python', 'typescript', 'javascript', 'rust', 'go')),
  imports_header TEXT NOT NULL DEFAULT '',
  enclosing_scope TEXT,
  git_blob_sha TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ast_children (
  child_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

CREATE INDEX IF NOT EXISTS idx_ast_children_file_path
  ON ast_children (file_path);

-- ============================================================================
-- LAYER 2: Episodic Diagnostic Memory (project_episodes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_episodes (
  episode_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- ============================================================================
-- LAYER 3: Conceptual ResearchBrain (tech_knowledge_chunks)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tech_knowledge_chunks (
  chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_doc TEXT NOT NULL,             -- e.g. 'rfcs/fastapi_di.md', 'adr/001_mcp.md'
  domain TEXT NOT NULL DEFAULT 'general', -- e.g. 'python', 'fastmcp', 'postgres'
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  external_url TEXT,
  embedding vector(768) NOT NULL,
  fts_tokens tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', normalize_code_identifiers(title)), 'A') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(content)), 'B')
  ) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tech_knowledge_embedding_hnsw
  ON tech_knowledge_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_tech_knowledge_fts_gin
  ON tech_knowledge_chunks USING gin (fts_tokens);

-- ============================================================================
-- LAYER 4: GitHub Template Stockroom (template_blueprints)
-- ============================================================================
CREATE TABLE IF NOT EXISTS template_blueprints (
  blueprint_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  repo_name TEXT NOT NULL,               -- e.g. 'tiangolo/full-stack-fastapi-template'
  file_path TEXT NOT NULL,               -- e.g. 'backend/app/api/deps.py'
  symbol_name TEXT NOT NULL,
  stack_domain TEXT NOT NULL,            -- e.g. 'fastapi', 'shadcn', 'fastmcp'
  description TEXT NOT NULL,
  code_snippet TEXT NOT NULL,
  start_line INT NOT NULL DEFAULT 1,
  end_line INT NOT NULL DEFAULT 1,
  embedding vector(768) NOT NULL,
  fts_tokens tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', normalize_code_identifiers(repo_name)), 'A') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(symbol_name)), 'A') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(description)), 'B') ||
    setweight(to_tsvector('simple', normalize_code_identifiers(code_snippet)), 'C')
  ) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_template_blueprints_embedding_hnsw
  ON template_blueprints USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_template_blueprints_fts_gin
  ON template_blueprints USING gin (fts_tokens);

-- ============================================================================
-- PARAMETERIZED TWO-STAGE HYBRID RRF QUERY TEMPLATE (Guardrail #4 & #5)
-- $1 = query_embedding::vector(768), $2 = raw_query_text::text, $3 = rrf_pool_size (25)
-- ============================================================================
-- Function: repobrain_search_codebase_rrf
CREATE OR REPLACE FUNCTION repobrain_search_codebase_rrf(
  p_embedding vector(768),
  p_query_text TEXT,
  p_limit INT DEFAULT 25
)
RETURNS TABLE (
  child_id UUID,
  parent_id UUID,
  file_path TEXT,
  language TEXT,
  symbol_name TEXT,
  node_kind TEXT,
  signature TEXT,
  docstring TEXT,
  body_code TEXT,
  start_line INT,
  end_line INT,
  git_blob_sha TEXT,
  imports_header TEXT,
  enclosing_scope TEXT,
  dense_rank BIGINT,
  sparse_rank BIGINT,
  rrf_score FLOAT8
)
LANGUAGE sql
AS $$
WITH lexical_query AS (
  SELECT to_tsquery(
    'simple',
    ARRAY_TO_STRING(
      ARRAY(
        SELECT DISTINCT token
        FROM REGEXP_SPLIT_TO_TABLE(
          TRIM(REGEXP_REPLACE(normalize_code_identifiers(p_query_text), '[^a-zA-Z0-9_]+', ' ', 'g')),
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
    c.child_id,
    c.parent_id,
    ROW_NUMBER() OVER (ORDER BY c.embedding <=> p_embedding) AS dense_rank
  FROM ast_children c
  ORDER BY c.embedding <=> p_embedding
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
  LIMIT p_limit
)
SELECT
  c.child_id,
  c.parent_id,
  p.file_path,
  p.language,
  c.symbol_name,
  c.node_kind,
  c.signature,
  c.docstring,
  c.body_code,
  c.start_line,
  c.end_line,
  p.git_blob_sha,
  p.imports_header,
  p.enclosing_scope,
  r.dense_rank,
  r.sparse_rank,
  r.rrf_score
FROM rrf_fused r
JOIN ast_children c ON r.child_id = c.child_id
JOIN ast_parents p ON r.parent_id = p.parent_id
ORDER BY r.rrf_score DESC;
$$;

