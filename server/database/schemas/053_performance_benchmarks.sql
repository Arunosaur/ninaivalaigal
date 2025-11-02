-- SPDX-License-Identifier: Proprietary
-- Copyright (c) 2025 Medhasys LLC
--
-- Schema for Performance Benchmarking System (SPEC-069, US#409)
-- Note: Performance benchmarking enhancements are part of SPEC-069
-- Stores historical benchmark results for regression detection and trend analysis

-- Performance benchmark runs table
CREATE TABLE IF NOT EXISTS performance_benchmark_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type VARCHAR(50) NOT NULL, -- 'automated', 'manual', 'ci', 'scheduled'
    environment VARCHAR(50) NOT NULL, -- 'production', 'staging', 'development', 'ci'
    commit_sha VARCHAR(40), -- Git commit SHA for CI runs
    branch_name VARCHAR(100), -- Git branch name
    run_timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    metadata JSONB DEFAULT '{}', -- Additional run metadata (test config, system info, etc.)
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Index for querying recent runs by type/environment
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_type_env ON performance_benchmark_runs(run_type, environment, run_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_commit ON performance_benchmark_runs(commit_sha) WHERE commit_sha IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_timestamp ON performance_benchmark_runs(run_timestamp DESC);

-- Performance benchmark results table
CREATE TABLE IF NOT EXISTS performance_benchmark_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES performance_benchmark_runs(run_id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL, -- e.g., 'api_latency_p95_ms', 'cache_hit_rate', 'throughput_rps'
    metric_category VARCHAR(50) NOT NULL, -- 'api', 'database', 'cache', 'graph', 'system'
    metric_value DECIMAL(15, 4) NOT NULL,
    metric_unit VARCHAR(20), -- 'ms', 'rps', 'percent', 'mb', etc.
    target_value DECIMAL(15, 4), -- Target/threshold value for this metric
    status VARCHAR(20) DEFAULT 'good' CHECK (status IN ('good', 'warning', 'critical', 'regression')),
    tags JSONB DEFAULT '{}', -- Additional tags (endpoint, query_type, etc.)
    percentile_p50 DECIMAL(15, 4), -- 50th percentile (median)
    percentile_p95 DECIMAL(15, 4), -- 95th percentile
    percentile_p99 DECIMAL(15, 4), -- 99th percentile
    sample_count INTEGER DEFAULT 1, -- Number of samples for this metric
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_benchmark_results_run ON performance_benchmark_results(run_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_metric ON performance_benchmark_results(metric_name, metric_category);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_timestamp ON performance_benchmark_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_status ON performance_benchmark_results(status) WHERE status != 'good';

-- Performance benchmark comparisons table (regression tracking)
CREATE TABLE IF NOT EXISTS performance_benchmark_comparisons (
    comparison_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_run_id UUID NOT NULL REFERENCES performance_benchmark_runs(run_id) ON DELETE CASCADE,
    current_run_id UUID NOT NULL REFERENCES performance_benchmark_runs(run_id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    baseline_value DECIMAL(15, 4) NOT NULL,
    current_value DECIMAL(15, 4) NOT NULL,
    change_percent DECIMAL(8, 2) NOT NULL, -- Positive = improvement, Negative = regression
    change_absolute DECIMAL(15, 4) NOT NULL,
    regression_threshold DECIMAL(8, 2) DEFAULT -5.0, -- % change threshold for regression (default -5%)
    is_regression BOOLEAN DEFAULT FALSE,
    regression_severity VARCHAR(20) DEFAULT 'none' CHECK (regression_severity IN ('none', 'minor', 'major', 'critical')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(current_run_id, metric_name, metric_category)
);

-- Indexes for regression queries
CREATE INDEX IF NOT EXISTS idx_benchmark_comparisons_current ON performance_benchmark_comparisons(current_run_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_comparisons_regression ON performance_benchmark_comparisons(is_regression, regression_severity) WHERE is_regression = TRUE;
CREATE INDEX IF NOT EXISTS idx_benchmark_comparisons_metric ON performance_benchmark_comparisons(metric_name, metric_category);

-- Performance benchmark trends table (for historical analysis)
CREATE TABLE IF NOT EXISTS performance_benchmark_trends (
    trend_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    avg_value DECIMAL(15, 4) NOT NULL,
    min_value DECIMAL(15, 4),
    max_value DECIMAL(15, 4),
    median_value DECIMAL(15, 4),
    sample_count INTEGER NOT NULL,
    trend_direction VARCHAR(20) CHECK (trend_direction IN ('improving', 'stable', 'degrading')),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for trend analysis
CREATE INDEX IF NOT EXISTS idx_benchmark_trends_metric ON performance_benchmark_trends(metric_name, metric_category, environment);
CREATE INDEX IF NOT EXISTS idx_benchmark_trends_period ON performance_benchmark_trends(period_start, period_end);

-- Function to detect regressions automatically
CREATE OR REPLACE FUNCTION detect_benchmark_regression(
    p_current_run_id UUID,
    p_metric_name VARCHAR(100),
    p_metric_category VARCHAR(50),
    p_regression_threshold DECIMAL DEFAULT -5.0
) RETURNS BOOLEAN AS $$
DECLARE
    v_baseline_value DECIMAL(15, 4);
    v_current_value DECIMAL(15, 4);
    v_change_percent DECIMAL(8, 2);
    v_is_regression BOOLEAN := FALSE;
BEGIN
    -- Get current value
    SELECT metric_value INTO v_current_value
    FROM performance_benchmark_results
    WHERE run_id = p_current_run_id
      AND metric_name = p_metric_name
      AND metric_category = p_metric_category;

    IF v_current_value IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Get baseline value (most recent previous run in same environment)
    SELECT r.metric_value INTO v_baseline_value
    FROM performance_benchmark_results r
    JOIN performance_benchmark_runs runs ON r.run_id = runs.run_id
    WHERE r.metric_name = p_metric_name
      AND r.metric_category = p_metric_category
      AND runs.environment = (SELECT environment FROM performance_benchmark_runs WHERE run_id = p_current_run_id)
      AND runs.run_timestamp < (SELECT run_timestamp FROM performance_benchmark_runs WHERE run_id = p_current_run_id)
      AND runs.status = 'completed'
    ORDER BY runs.run_timestamp DESC
    LIMIT 1;

    IF v_baseline_value IS NULL OR v_baseline_value = 0 THEN
        RETURN FALSE;
    END IF;

    -- Calculate change percentage
    -- For metrics where lower is better (latency, time), positive change is regression
    -- For metrics where higher is better (throughput, hit_rate), negative change is regression
    v_change_percent := ((v_current_value - v_baseline_value) / v_baseline_value) * 100;

    -- Check if regression (threshold is negative, so change must be worse than threshold)
    IF v_change_percent < p_regression_threshold THEN
        v_is_regression := TRUE;
    END IF;

    RETURN v_is_regression;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE performance_benchmark_runs IS 'Stores benchmark run metadata and execution context';
COMMENT ON TABLE performance_benchmark_results IS 'Stores individual metric results for each benchmark run';
COMMENT ON TABLE performance_benchmark_comparisons IS 'Stores comparisons between benchmark runs for regression detection';
COMMENT ON TABLE performance_benchmark_trends IS 'Stores aggregated trend data for historical performance analysis';
COMMENT ON FUNCTION detect_benchmark_regression IS 'Automatically detects performance regressions by comparing current run to baseline';
