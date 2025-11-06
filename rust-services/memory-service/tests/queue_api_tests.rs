//! Integration tests for Queue API
//! US#93/US#95: Memory Router Rationalization - SPEC-131

mod common;

use common::{create_test_token, TestClient};
use serde_json::json;

// Note: These tests require a running service with Redis
// Run with: cargo test --test queue_api_tests -- --nocapture
// Set TEST_JWT_TOKEN environment variable for authenticated tests

#[tokio::test]
#[ignore] // Requires running service
async fn test_queue_enqueue_task() {
    let config = common::TestConfig::default();

    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available");
    }

    let token = create_test_token();
    let client = TestClient::with_token(token);

    let request = json!({
        "task_type": "memory_processing",
        "parameters": {
            "memory_id": "123e4567-e89b-12d3-a456-426614174000",
            "text": "Test memory content",
            "metadata": {}
        }
    });

    let response = client
        .post("/queue/tasks", &request)
        .await
        .expect("request failed");

    assert!(response.status().is_success());

    let body: serde_json::Value = response.json().await.expect("failed to parse JSON");
    assert_eq!(body["status"], "enqueued");
    assert!(body.get("job_id").is_some());

    // Store job_id for status test
    let job_id = body["job_id"].as_str().unwrap();

    // Test getting job status
    let status_response = client
        .get(&format!("/queue/jobs/{}", job_id))
        .await
        .expect("status request failed");

    assert!(status_response.status().is_success());
    let status_body: serde_json::Value = status_response.json().await.expect("failed to parse status JSON");
    assert_eq!(status_body["id"], job_id);
}

#[tokio::test]
#[ignore]
async fn test_queue_stats() {
    let config = common::TestConfig::default();

    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available");
    }

    let token = create_test_token();
    let client = TestClient::with_token(token);

    let response = client
        .get("/queue/stats")
        .await
        .expect("request failed");

    assert!(response.status().is_success());

    let body: serde_json::Value = response.json().await.expect("failed to parse JSON");
    assert!(body.get("queues").is_some());
    assert!(body.get("total_jobs").is_some());
    assert_eq!(body["healthy"], true);
}

#[tokio::test]
#[ignore]
async fn test_queue_health() {
    let config = common::TestConfig::default();

    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available");
    }

    // Health endpoint doesn't require auth
    let client = TestClient::new(config);

    let response = client
        .get("/queue/health")
        .await
        .expect("request failed");

    assert!(response.status().is_success());

    let body: serde_json::Value = response.json().await.expect("failed to parse JSON");
    assert!(body.get("status").is_some());
    assert!(body.get("connected").is_some());
}

#[tokio::test]
#[ignore]
async fn test_queue_endpoints_require_auth() {
    let config = common::TestConfig::default();

    if !common::wait_for_service(&config.base_url, 10).await {
        panic!("Service not available");
    }

    // Test without token (except health which is public)
    let client = TestClient::new(config);

    let request = json!({
        "task_type": "test",
        "parameters": {}
    });

    let response = client
        .post("/queue/tasks", &request)
        .await
        .expect("request failed");

    // Should return 401 Unauthorized
    assert_eq!(response.status(), 401);
}
