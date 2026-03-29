-- schema.sql
-- Supabase schema for fashion trend prediction benchmark.
-- Idempotent: safe to run multiple times (CREATE TABLE IF NOT EXISTS).
-- Tested on PostgreSQL 15 (Supabase).

CREATE TABLE IF NOT EXISTS predictions (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    statement            text        NOT NULL,
    attribute            text        NOT NULL,
    category             text        NOT NULL,
    market               text        NOT NULL,
    source               text        NOT NULL,
    query_term           text,
    threshold_operator   text        NOT NULL,
    threshold_value      numeric     NOT NULL,
    threshold_unit       text        NOT NULL,
    deadline             date        NOT NULL,
    probability          numeric     NOT NULL CHECK (probability > 0 AND probability < 1),
    submitted_by         text        NOT NULL,
    submitted_at         timestamptz DEFAULT now(),
    seal_hash            text        UNIQUE NOT NULL,
    github_timestamp_url text,
    resolution_criteria  text        NOT NULL
);

CREATE TABLE IF NOT EXISTS resolutions (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id    uuid        REFERENCES predictions(id),
    outcome          boolean     NOT NULL,
    resolved_at      timestamptz DEFAULT now(),
    t1_value         numeric,
    t2_value         numeric,
    computed_metric  numeric,
    raw_data_snapshot jsonb,
    notes            text
);

CREATE TABLE IF NOT EXISTS scores (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id        uuid        REFERENCES predictions(id),
    brier_score          numeric,
    log_score            numeric,
    baseline_naive_brier numeric,
    brier_skill_score    numeric,
    scored_at            timestamptz DEFAULT now()
);
