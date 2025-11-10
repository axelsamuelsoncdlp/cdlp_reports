-- Supabase schema for weekly report read-optimized data

-- Weeks tracking
CREATE TABLE IF NOT EXISTS weeks (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Budget General (detailed month-by-month)
CREATE TABLE IF NOT EXISTS budget_general (
    base_week TEXT NOT NULL,
    metric TEXT NOT NULL,
    customer TEXT NOT NULL DEFAULT '',
    month TEXT NOT NULL,
    value NUMERIC NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('budget', 'actuals')),
    PRIMARY KEY (base_week, metric, customer, month, kind)
);

-- Budget General Totals (Total and YTD)
CREATE TABLE IF NOT EXISTS budget_general_totals (
    base_week TEXT NOT NULL,
    metric TEXT NOT NULL,
    customer TEXT NOT NULL DEFAULT '',
    scope TEXT NOT NULL CHECK (scope IN ('TOTAL', 'YTD')),
    value NUMERIC NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('budget', 'actuals')),
    PRIMARY KEY (base_week, metric, customer, scope, kind)
);

-- Budget Markets Detailed (per market and month)
CREATE TABLE IF NOT EXISTS budget_markets_detailed (
    base_week TEXT NOT NULL,
    market TEXT NOT NULL,
    metric TEXT NOT NULL,
    month TEXT NOT NULL,
    value NUMERIC NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('budget', 'actuals')),
    PRIMARY KEY (base_week, market, metric, month, kind)
);

-- Budget Markets Totals (Total and YTD per market)
CREATE TABLE IF NOT EXISTS budget_markets_totals (
    base_week TEXT NOT NULL,
    market TEXT NOT NULL,
    metric TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('TOTAL', 'YTD')),
    value NUMERIC NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('budget', 'actuals')),
    PRIMARY KEY (base_week, market, metric, scope, kind)
);

-- Budget files storage (persisted across weeks, reused by year)
CREATE TABLE IF NOT EXISTS budget_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year INTEGER NOT NULL,
    week TEXT, -- ISO week when uploaded (for tracking, but file is reused by year)
    filename TEXT NOT NULL,
    content TEXT NOT NULL, -- CSV content as text
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(year) -- Only one budget file per year
);

-- Weekly Report Metrics (all computed metrics cached as JSONB)
CREATE TABLE IF NOT EXISTS weekly_report_metrics (
    base_week TEXT PRIMARY KEY,
    metrics JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_hashes JSONB, -- Tracks which files were used: {"qlik": "md5...", "dema_spend": "md5..."}
    num_weeks INTEGER NOT NULL DEFAULT 8 -- Number of weeks analyzed
);

-- Sync runs tracking
CREATE TABLE IF NOT EXISTS sync_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    base_week TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    details JSONB
);

-- Indexes for fast reads
CREATE INDEX IF NOT EXISTS idx_budget_general_base_week_metric ON budget_general(base_week, metric, kind);
CREATE INDEX IF NOT EXISTS idx_budget_general_base_week_month ON budget_general(base_week, month, kind);
CREATE INDEX IF NOT EXISTS idx_budget_general_totals_base_week ON budget_general_totals(base_week, metric, scope, kind);
CREATE INDEX IF NOT EXISTS idx_budget_markets_detailed_base_week ON budget_markets_detailed(base_week, market, month, kind);
CREATE INDEX IF NOT EXISTS idx_budget_markets_detailed_market_metric ON budget_markets_detailed(base_week, market, metric, kind);
CREATE INDEX IF NOT EXISTS idx_budget_markets_totals_base_week ON budget_markets_totals(base_week, market, metric, scope, kind);
CREATE INDEX IF NOT EXISTS idx_budget_files_year ON budget_files(year);
CREATE INDEX IF NOT EXISTS idx_weekly_report_metrics_computed_at ON weekly_report_metrics(computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_runs_base_week ON sync_runs(base_week, finished_at DESC);

-- Enable Row Level Security
ALTER TABLE weeks ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_general ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_general_totals ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_markets_detailed ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_markets_totals ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_report_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_runs ENABLE ROW LEVEL SECURITY;

-- Policies: allow read to authenticated and anon users
-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Allow read weeks" ON weeks;
CREATE POLICY "Allow read weeks" ON weeks FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read budget_general" ON budget_general;
CREATE POLICY "Allow read budget_general" ON budget_general FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read budget_general_totals" ON budget_general_totals;
CREATE POLICY "Allow read budget_general_totals" ON budget_general_totals FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read budget_markets_detailed" ON budget_markets_detailed;
CREATE POLICY "Allow read budget_markets_detailed" ON budget_markets_detailed FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read budget_markets_totals" ON budget_markets_totals;
CREATE POLICY "Allow read budget_markets_totals" ON budget_markets_totals FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read budget_files" ON budget_files;
CREATE POLICY "Allow read budget_files" ON budget_files FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read weekly_report_metrics" ON weekly_report_metrics;
CREATE POLICY "Allow read weekly_report_metrics" ON weekly_report_metrics FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read sync_runs" ON sync_runs;
CREATE POLICY "Allow read sync_runs" ON sync_runs FOR SELECT USING (true);

-- Policies: write only via service role (enforced server-side)
-- Service role has bypass_rls=true, so no write policy needed

