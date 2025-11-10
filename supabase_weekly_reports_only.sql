-- =============================================================================
-- Weekly Reports Tables - Supabase Setup
-- =============================================================================
-- This script creates ONLY the weekly_report_metrics table for Weekly Reports data.
-- Budget tables should already exist.
--
-- Instructions:
-- 1. Open your Supabase project dashboard
-- 2. Go to SQL Editor
-- 3. Paste this entire script
-- 4. Run it
-- =============================================================================

-- =============================================================================
-- WEEKLY REPORT METRICS TABLE
-- =============================================================================
-- This table stores all Weekly Reports data as JSONB for fast retrieval.
-- Contains all metrics from all Weekly Reports pages (Summary, Top Markets, 
-- Online KPIs, Contribution, Gender Sales, Category Sales, Products, etc.)

CREATE TABLE IF NOT EXISTS weekly_report_metrics (
    base_week TEXT PRIMARY KEY,
    metrics JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_hashes JSONB, -- Tracks which files were used: {"qlik": "md5...", "dema_spend": "md5..."}
    num_weeks INTEGER NOT NULL DEFAULT 8 -- Number of weeks analyzed
);

-- =============================================================================
-- INDEXES
-- =============================================================================
-- Index for fast lookups by computation time (useful for cache invalidation)

CREATE INDEX IF NOT EXISTS idx_weekly_report_metrics_computed_at 
ON weekly_report_metrics(computed_at DESC);

-- Index for JSONB queries (optional but can improve performance)
CREATE INDEX IF NOT EXISTS idx_weekly_report_metrics_gin 
ON weekly_report_metrics USING GIN (metrics);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS
ALTER TABLE weekly_report_metrics ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- RLS POLICIES - READ ACCESS
-- =============================================================================
-- Allow anyone (authenticated and anonymous) to read from this table

DROP POLICY IF EXISTS "Allow read weekly_report_metrics" ON weekly_report_metrics;
CREATE POLICY "Allow read weekly_report_metrics" 
ON weekly_report_metrics 
FOR SELECT 
USING (true);

-- =============================================================================
-- NOTES
-- =============================================================================
-- 
-- 1. The weekly_report_metrics table stores all Weekly Reports data as JSONB:
--    - periods: Period calculations
--    - metrics: Table 1 metrics (Summary page)
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
-- 2. Write access is controlled server-side via service role key
--    The backend uses the service role key which has bypass_rls=true
--
-- 3. File hashes allow cache invalidation when source files change
--
-- =============================================================================
-- VERIFICATION QUERIES (Run these after setup to verify)
-- =============================================================================

-- Check table exists
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name = 'weekly_report_metrics';

-- Check RLS is enabled
-- SELECT tablename, rowsecurity FROM pg_tables 
-- WHERE schemaname = 'public' 
-- AND tablename = 'weekly_report_metrics';

-- Check indexes exist
-- SELECT indexname FROM pg_indexes 
-- WHERE schemaname = 'public' 
-- AND indexname LIKE 'idx_weekly_report_metrics%'
-- ORDER BY indexname;

-- Check table structure
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_schema = 'public' 
-- AND table_name = 'weekly_report_metrics'
-- ORDER BY ordinal_position;

