-- =============================================================================
-- Supabase Schema Setup for Weekly Reports Platform
-- =============================================================================
-- This script creates all necessary tables, indexes, and RLS policies
-- for the Weekly Reports platform. It is idempotent and safe to run multiple times.
--
-- Instructions:
-- 1. Open your Supabase project dashboard
-- 2. Go to SQL Editor
-- 3. Paste this entire script
-- 4. Run it
-- =============================================================================

-- =============================================================================
-- TABLES
-- =============================================================================

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
-- This is the main table that stores all Weekly Reports data
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

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Budget General indexes
CREATE INDEX IF NOT EXISTS idx_budget_general_base_week_metric ON budget_general(base_week, metric, kind);
CREATE INDEX IF NOT EXISTS idx_budget_general_base_week_month ON budget_general(base_week, month, kind);

-- Budget General Totals indexes
CREATE INDEX IF NOT EXISTS idx_budget_general_totals_base_week ON budget_general_totals(base_week, metric, scope, kind);

-- Budget Markets Detailed indexes
CREATE INDEX IF NOT EXISTS idx_budget_markets_detailed_base_week ON budget_markets_detailed(base_week, market, month, kind);
CREATE INDEX IF NOT EXISTS idx_budget_markets_detailed_market_metric ON budget_markets_detailed(base_week, market, metric, kind);

-- Budget Markets Totals indexes
CREATE INDEX IF NOT EXISTS idx_budget_markets_totals_base_week ON budget_markets_totals(base_week, market, metric, scope, kind);

-- Budget Files indexes
CREATE INDEX IF NOT EXISTS idx_budget_files_year ON budget_files(year);

-- Weekly Report Metrics indexes
CREATE INDEX IF NOT EXISTS idx_weekly_report_metrics_computed_at ON weekly_report_metrics(computed_at DESC);

-- Sync Runs indexes
CREATE INDEX IF NOT EXISTS idx_sync_runs_base_week ON sync_runs(base_week, finished_at DESC);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE weeks ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_general ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_general_totals ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_markets_detailed ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_markets_totals ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_report_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_runs ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- RLS POLICIES - READ ACCESS
-- =============================================================================
-- Allow anyone (authenticated and anonymous) to read from these tables

-- Weeks
DROP POLICY IF EXISTS "Allow read weeks" ON weeks;
CREATE POLICY "Allow read weeks" ON weeks FOR SELECT USING (true);

-- Budget General
DROP POLICY IF EXISTS "Allow read budget_general" ON budget_general;
CREATE POLICY "Allow read budget_general" ON budget_general FOR SELECT USING (true);

-- Budget General Totals
DROP POLICY IF EXISTS "Allow read budget_general_totals" ON budget_general_totals;
CREATE POLICY "Allow read budget_general_totals" ON budget_general_totals FOR SELECT USING (true);

-- Budget Markets Detailed
DROP POLICY IF EXISTS "Allow read budget_markets_detailed" ON budget_markets_detailed;
CREATE POLICY "Allow read budget_markets_detailed" ON budget_markets_detailed FOR SELECT USING (true);

-- Budget Markets Totals
DROP POLICY IF EXISTS "Allow read budget_markets_totals" ON budget_markets_totals;
CREATE POLICY "Allow read budget_markets_totals" ON budget_markets_totals FOR SELECT USING (true);

-- Budget Files
DROP POLICY IF EXISTS "Allow read budget_files" ON budget_files;
CREATE POLICY "Allow read budget_files" ON budget_files FOR SELECT USING (true);

-- Weekly Report Metrics
DROP POLICY IF EXISTS "Allow read weekly_report_metrics" ON weekly_report_metrics;
CREATE POLICY "Allow read weekly_report_metrics" ON weekly_report_metrics FOR SELECT USING (true);

-- Sync Runs
DROP POLICY IF EXISTS "Allow read sync_runs" ON sync_runs;
CREATE POLICY "Allow read sync_runs" ON sync_runs FOR SELECT USING (true);

-- =============================================================================
-- NOTES
-- =============================================================================
-- 
-- 1. Write access is controlled server-side via service role key
--    The backend uses the service role key which has bypass_rls=true
-- 
-- 2. All tables use Row Level Security (RLS) for data protection
-- 
-- 3. The weekly_report_metrics table stores all Weekly Reports data as JSONB:
--    - periods: Period calculations
--    - metrics: Table 1 metrics
--    - markets: Top markets data
--    - kpis: Online KPIs
--    - contribution: Contribution metrics
--    - gender_sales: Gender sales data
--    - men_category_sales: Men category sales
--    - women_category_sales: Women category sales
--    - category_sales: All category sales
--    - products_new: Top products for new customers
--    - products_gender: Top products by gender
--    - sessions_per_country: Sessions per country
--    - conversion_per_country: Conversion per country
--    - new_customers_per_country: New customers per country
--    - returning_customers_per_country: Returning customers per country
--    - aov_new_customers_per_country: AOV for new customers per country
--    - aov_returning_customers_per_country: AOV for returning customers per country
--    - marketing_spend_per_country: Marketing spend per country
--    - ncac_per_country: nCAC per country
--    - contribution_new_per_country: Contribution new per country
--    - contribution_new_total_per_country: Contribution new total per country
--    - contribution_returning_per_country: Contribution returning per country
--    - contribution_returning_total_per_country: Contribution returning total per country
--    - total_contribution_per_country: Total contribution per country
--
-- 4. Budget files are stored once per year and reused across all weeks
--
-- 5. File hashes in weekly_report_metrics allow cache invalidation
--    when source files change
--
-- =============================================================================
-- VERIFICATION QUERIES (Run these after setup to verify)
-- =============================================================================

-- Check all tables exist
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('weeks', 'budget_general', 'budget_general_totals', 
--                    'budget_markets_detailed', 'budget_markets_totals', 
--                    'budget_files', 'weekly_report_metrics', 'sync_runs')
-- ORDER BY table_name;

-- Check RLS is enabled
-- SELECT tablename, rowsecurity FROM pg_tables 
-- WHERE schemaname = 'public' 
-- AND tablename IN ('weeks', 'budget_general', 'budget_general_totals', 
--                   'budget_markets_detailed', 'budget_markets_totals', 
--                   'budget_files', 'weekly_report_metrics', 'sync_runs')
-- ORDER BY tablename;

-- Check indexes exist
-- SELECT indexname FROM pg_indexes 
-- WHERE schemaname = 'public' 
-- AND indexname LIKE 'idx_%'
-- ORDER BY indexname;





