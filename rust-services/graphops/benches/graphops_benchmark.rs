// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

use std::env;

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use graphops_service::{CypherExecutor, DbPool};

fn benchmark_cypher_execution(c: &mut Criterion) {
    // Load .env file if present (silently ignore if missing)
    let _ = dotenvy::dotenv();

    let database_url = match env::var("DATABASE_URL") {
        Ok(url) => url,
        Err(_) => {
            eprintln!("DATABASE_URL not set – skipping benchmarks");
            return;
        }
    };

    let graph_name = env::var("GRAPHOPS_GRAPH").unwrap_or_else(|_| "graph".to_string());
    let pool = match DbPool::new(&database_url) {
        Ok(pool) => pool,
        Err(error) => {
            eprintln!("Invalid DATABASE_URL: {error}");
            return;
        }
    };

    // Use single-threaded runtime to reduce scheduling noise
    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("Tokio runtime");

    // Warmup phase: run queries 300 times to stabilize connection and caches
    runtime.block_on(async {
        let warmup_client = pool.get_client().await.expect("warmup client");
        let warmup_executor = CypherExecutor::new(&graph_name, warmup_client);
        for _ in 0..300 {
            let _ = warmup_executor
                .execute_query("MATCH (n) RETURN n LIMIT 1")
                .await;
        }
    });

    // PERFORMANCE FIX: Acquire connection ONCE per benchmark and reuse across iterations
    // This eliminates per-iteration connection overhead (was causing 8-9× slowdown)
    c.bench_function("cypher_simple_match", |b| {
        // Get a dedicated client for this benchmark's iterations
        let client = runtime.block_on(async { pool.get_client().await.expect("bench client") });
        let executor = CypherExecutor::new(&graph_name, client);

        b.to_async(&runtime).iter(|| async {
            let result = executor
                .execute_query("MATCH (n) RETURN n LIMIT 10")
                .await
                .expect("cypher query");
            black_box(result);
        });
    });

    c.bench_function("cypher_graph_traversal", |b| {
        // Get a dedicated client for this benchmark's iterations
        let client = runtime.block_on(async { pool.get_client().await.expect("bench client") });
        let executor = CypherExecutor::new(&graph_name, client);

        b.to_async(&runtime).iter(|| async {
            let result = executor
                .execute_query(
                    "MATCH (a)-[r*1..3]->(b) RETURN {start: a, hops: r, end: b} LIMIT 10",
                )
                .await
                .expect("cypher traversal");
            black_box(result);
        });
    });
}

criterion_group!(benches, benchmark_cypher_execution);
criterion_main!(benches);
