//! Performance benchmarks for Injection API
//! US#93/US#95: Memory Router Rationalization - SPEC-131
//!
//! Target: >1000 memories/sec bulk throughput
//!
//! Run with: cargo bench --bench injection_benchmark

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use serde_json::json;
use uuid::Uuid;

// Note: These are placeholder benchmarks
// Full benchmarks would require database and Redis connections
// and should be run against a live service instance

fn benchmark_bulk_injection_processing(c: &mut Criterion) {
    let mut group = c.benchmark_group("injection");

    // Simulate processing 100 items
    let items: Vec<_> = (0..100)
        .map(|i| {
            json!({
                "content": format!("Memory content {}", i),
                "metadata": {"index": i}
            })
        })
        .collect();

    group.bench_function("bulk_process_100_items", |b| {
        b.iter(|| {
            // Simulate processing
            let _result: Vec<_> = black_box(&items)
                .iter()
                .map(|item| {
                    // Simulate processing time
                    item.get("content").and_then(|v| v.as_str()).unwrap_or("").len()
                })
                .collect();
        });
    });

    group.bench_function("bulk_process_1000_items", |b| {
        let large_items: Vec<_> = (0..1000)
            .map(|i| {
                json!({
                    "content": format!("Memory content {}", i),
                    "metadata": {"index": i}
                })
            })
            .collect();

        b.iter(|| {
            let _result: Vec<_> = black_box(&large_items)
                .iter()
                .map(|item| {
                    item.get("content").and_then(|v| v.as_str()).unwrap_or("").len()
                })
                .collect();
        });
    });

    group.finish();
}

fn benchmark_relevance_scoring(c: &mut Criterion) {
    let mut group = c.benchmark_group("relevance");

    let content = "I'm coding in Rust for memory injection";
    let activity = "coding";

    group.bench_function("relevance_score_single", |b| {
        b.iter(|| {
            let score = if content.to_lowercase().contains(&activity.to_lowercase()) {
                0.8
            } else {
                0.5
            };
            black_box(score);
        });
    });

    group.bench_function("relevance_score_1000", |b| {
        let contents: Vec<_> = (0..1000)
            .map(|i| format!("Memory content {} with coding activity", i))
            .collect();

        b.iter(|| {
            let scores: Vec<_> = contents
                .iter()
                .map(|c| {
                    if c.to_lowercase().contains(&activity.to_lowercase()) {
                        0.8
                    } else {
                        0.5
                    }
                })
                .collect();
            black_box(scores);
        });
    });

    group.finish();
}

criterion_group!(benches, benchmark_bulk_injection_processing, benchmark_relevance_scoring);
criterion_main!(benches);




