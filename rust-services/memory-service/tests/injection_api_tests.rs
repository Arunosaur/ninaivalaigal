//! Integration tests for Injection API
//! US#93/US#95: Memory Router Rationalization - SPEC-131

mod common;

use common::{create_test_token, test_bulk_items, test_injection_context, TestClient};
use serde_json::json;

// Note: These tests require a running service with database and Redis
// Run with: cargo test --test injection_api_tests -- --nocapture
// Set TEST_JWT_TOKEN environment variable for authenticated tests

#[tokio::test]
#[ignore] // Requires running service
async fn test_injection_analyze_endpoint() {
    let config = common::TestConfig::default();

    // Wait for service to be ready
    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available at {}", config.base_url);
    }

    let token = create_test_token();
    let client = TestClient::with_token(token);

    let request = json!({
        "session_id": "test-session-123",
        "current_activity": "coding",
        "location_context": {},
        "temporal_context": {},
        "semantic_context": {
            "language": "rust",
            "topic": "testing"
        },
        "user_state": {},
        "environment": {},
        "max_candidates": 10
    });

    let response = client
        .post("/memory/injection/analyze", &request)
        .await
        .expect("request failed");

    assert!(response.status().is_success(), "Expected success, got: {}", response.status());

    let body: serde_json::Value = response.json().await.expect("failed to parse JSON");
    assert!(body.get("candidates").is_some());
    assert!(body.get("total_candidates").is_some());
    assert!(body.get("analysis_time_ms").is_some());
}

#[tokio::test]
#[ignore]
async fn test_injection_bulk_endpoint() {
    let config = common::TestConfig::default();

    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available");
    }

    let token = create_test_token();
    let client = TestClient::with_token(token);

    let items = test_bulk_items(10);
    let items_json = json!(items);

    let response = client
        .post("/memory/injection/bulk", &items_json)
        .await
        .expect("request failed");

    assert!(response.status().is_success());

    let body: serde_json::Value = response.json().await.expect("failed to parse JSON");
    assert_eq!(body["total_requested"], 10);
    assert!(body.get("success_count").is_some());
    assert!(body.get("execution_time_ms").is_some());
}

#[tokio::test]
#[ignore]
async fn test_injection_execute_endpoint() {
    let config = common::TestConfig::default();

    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available");
    }

    let token = create_test_token();
    let client = TestClient::with_token(token);

    let context = test_injection_context();
    let request = json!({
        "context": context,
        "strategy": "contextual",
        "max_injections": 5
    });

    let response = client
        .post("/memory/injection/execute", &request)
        .await
        .expect("request failed");

    assert!(response.status().is_success());

    let body: serde_json::Value = response.json().await.expect("failed to parse JSON");
    assert!(body.get("injected_memories").is_some());
    assert_eq!(body["strategy_used"], "contextual");
    assert!(body.get("execution_time_ms").is_some());
}

#[tokio::test]
#[ignore]
async fn test_injection_endpoints_require_auth() {
    let config = common::TestConfig::default();

    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available");
    }

    // Test without token
    let client = TestClient::new(config);

    let request = json!({
        "current_activity": "coding",
        "semantic_context": {}
    });

    let response = client
        .post("/memory/injection/analyze", &request)
        .await
        .expect("request failed");

    // Should return 401 Unauthorized
    assert_eq!(response.status(), 401);
}
