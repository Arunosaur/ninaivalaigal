use prometheus::{Encoder, Opts, Registry, Counter, Histogram, TextEncoder};
use std::sync::Arc;

pub struct Metrics {
    pub requests_total: Counter,
    pub request_duration: Histogram,
    pub cache_hits: Counter,
    pub cache_misses: Counter,
    pub registry: Arc<Registry>,
}

impl Metrics {
    pub fn new() -> anyhow::Result<Self> {
        let registry = Arc::new(Registry::new());

        let requests_total = Counter::with_opts(
            Opts::new("memory_requests_total", "Total number of requests")
        )?;
        registry.register(Box::new(requests_total.clone()))?;

        let request_duration = Histogram::with_opts(
            prometheus::HistogramOpts::new(
                "memory_request_duration_seconds",
                "Request duration in seconds"
            )
        )?;
        registry.register(Box::new(request_duration.clone()))?;

        let cache_hits = Counter::with_opts(
            Opts::new("memory_cache_hits_total", "Total cache hits")
        )?;
        registry.register(Box::new(cache_hits.clone()))?;

        let cache_misses = Counter::with_opts(
            Opts::new("memory_cache_misses_total", "Total cache misses")
        )?;
        registry.register(Box::new(cache_misses.clone()))?;

        Ok(Self {
            requests_total,
            request_duration,
            cache_hits,
            cache_misses,
            registry,
        })
    }

    pub fn encode(&self) -> anyhow::Result<Vec<u8>> {
        let encoder = TextEncoder::new();
        let metric_families = self.registry.gather();
        let mut buffer = vec![];
        encoder.encode(&metric_families, &mut buffer)?;
        Ok(buffer)
    }
}

impl Default for Metrics {
    fn default() -> Self {
        Self::new().unwrap()
    }
}
