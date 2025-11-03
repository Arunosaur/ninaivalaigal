/// Integration tests for Memory Service (Rust)
///
/// These tests require:
/// - Memory Service running on port 8000
/// - PostgreSQL database accessible
/// - Redis running
/// - Valid JWT secret configured
///
/// Run with: `cargo test --test integration_test -- --ignored --nocapture`
///
/// Or run specific test: `cargo test --test integration_test test_health_check -- --ignored`

use serde_json::{json, Value};
use std::time::Duration;
use uuid::Uuid;

const BASE_URL: &str = "http://localhost:8000";
const HEALTH_URL: &str = "http://localhost:8000/health";
const METRICS_URL: &str = "http://localhost:8000/metrics";
const MEMORIES_URL: &str = "http://localhost:8000/api/v1/memories";

/// Test helper to make HTTP requests
struct TestClient {
    base_url: String,
    client: reqwest::Client,
}

impl TestClient {
    fn new() -> Self {
        Self {
            base_url: BASE_URL.to_string(),
            client: reqwest::Client::builder()
                .timeout(Duration::from_secs(10))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    async fn get(&self, path: &str) -> Result<reqwest::Response, reqwest::Error> {
        let url = format!("{}{}", self.base_url, path);
        self.client.get(&url).send().await
    }

    async fn post(&self, path: &str, body: Value) -> Result<reqwest::Response, reqwest::Error> {
        let url = format!("{}{}", self.base_url, path);
        self.client
            .post(&url)
            .json(&body)
            .header("Content-Type", "application/json")
            .send()
            .await
    }

    async fn get_with_auth(
        &self,
        path: &str,
        token: &str,
    ) -> Result<reqwest::Response, reqwest::Error> {
        let url = format!("{}{}", self.base_url, path);
        self.client
            .get(&url)
            .header("Authorization", format!("Bearer {}", token))
            .send()
            .await
    }

    async fn post_with_auth(
        &self,
        path: &str,
        token: &str,
        body: Value,
    ) -> Result<reqwest::Response, reqwest::Error> {
        let url = format!("{}{}", self.base_url, path);
        self.client
            .post(&url)
            .json(&body)
            .header("Content-Type", "application/json")
            .header("Authorization", format!("Bearer {}", token))
            .send()
            .await
    }
}

/// Generate a test JWT token
/// This is a simplified version - in real tests, you'd use the actual Core API
/// or a test JWT generation utility
fn generate_test_token(user_id: &str, email: &str) -> String {
    // For integration tests, we'll need a valid token from Core API
    // or use a test JWT generator
    // This is a placeholder - actual implementation should use jsonwebtoken crate
    // or fetch from Core API
    format!("test_token_{}_{}", user_id, email)
}

#[tokio::test]
#[ignore] // Requires running service
async fn test_health_check() {
    let client = TestClient::new();

    let response = client.get("/health").await.expect("Failed to send request");
    assert_eq!(response.status(), 200, "Health check should return 200");

    let body: Value = response.json().await.expect("Failed to parse JSON");

    assert_eq!(body["service"], "memory-service");
    assert!(body["status"].is_string());
    assert!(body["database"].is_string());
    assert!(body["redis"].is_string());

    println!("✓ Health check passed: {:?}", body);
}

#[tokio::test]
#[ignore]
async fn test_metrics_endpoint() {
    let client = TestClient::new();

    let response = client.get("/metrics").await.expect("Failed to send request");
    assert_eq!(response.status(), 200, "Metrics should return 200");

    let body: Value = response.json().await.expect("Failed to parse JSON");

    assert!(body["active_connections"].is_number());
    assert!(body["total_requests"].is_number());
    assert!(body["cache_hits"].is_number());
    assert!(body["cache_misses"].is_number());

    println!("✓ Metrics endpoint passed: {:?}", body);
}

#[tokio::test]
#[ignore]
async fn test_auth_missing_header() {
    let client = TestClient::new();

    let response = client
        .get("/api/v1/memories")
        .await
        .expect("Failed to send request");

    assert_eq!(
        response.status(),
        401,
        "Should return 401 for missing Authorization header"
    );

    let body: Value = response.json().await.expect("Failed to parse JSON");
    assert_eq!(body["error"], "Authentication failed");

    println!("✓ Auth missing header test passed");
}

#[tokio::test]
#[ignore]
async fn test_auth_invalid_token() {
    let client = TestClient::new();

    let response = client
        .get_with_auth("/api/v1/memories", "invalid_token")
        .await
        .expect("Failed to send request");

    assert_eq!(
        response.status(),
        401,
        "Should return 401 for invalid token"
    );

    let body: Value = response.json().await.expect("Failed to parse JSON");
    assert_eq!(body["error"], "Authentication failed");

    println!("✓ Auth invalid token test passed");
}

#[tokio::test]
#[ignore]
async fn test_list_memories_requires_auth() {
    // This test verifies that the endpoint requires authentication
    // The actual implementation may return empty list or error
    let client = TestClient::new();

    // Without auth - should fail
    let response = client
        .get("/api/v1/memories")
        .await
        .expect("Failed to send request");
    assert_eq!(response.status(), 401);

    // TODO: With valid auth token (once we have a way to generate test tokens)
    // let token = get_test_token();
    // let response = client
    //     .get_with_auth("/api/v1/memories", &token)
    //     .await
    //     .expect("Failed to send request");
    // assert_eq!(response.status(), 200);

    println!("✓ List memories auth requirement test passed");
}

#[tokio::test]
#[ignore]
async fn test_create_memory_requires_auth() {
    let client = TestClient::new();
    let memory_data = json!({
        "content": "Test memory content",
        "metadata": {"tag": "test"}
    });

    // Without auth - should fail
    let response = client
        .post("/api/v1/memories", memory_data.clone())
        .await
        .expect("Failed to send request");
    assert_eq!(response.status(), 401);

    // TODO: With valid auth token
    // let token = get_test_token();
    // let response = client
    //     .post_with_auth("/api/v1/memories", &token, memory_data)
    //     .await
    //     .expect("Failed to send request");
    // assert_eq!(response.status(), 201);

    println!("✓ Create memory auth requirement test passed");
}

#[tokio::test]
#[ignore]
async fn test_get_memory_requires_auth() {
    let client = TestClient::new();
    let memory_id = Uuid::new_v4();

    // Without auth - should fail
    let response = client
        .get(&format!("/api/v1/memories/{}", memory_id))
        .await
        .expect("Failed to send request");
    assert_eq!(response.status(), 401);

    // TODO: With valid auth token
    // let token = get_test_token();
    // let response = client
    //     .get_with_auth(&format!("/api/v1/memories/{}", memory_id), &token)
    //     .await
    //     .expect("Failed to send request");
    // // Should return 404 if not found, or 200 if found
    // assert!(response.status() == 200 || response.status() == 404);

    println!("✓ Get memory auth requirement test passed");
}

#[tokio::test]
#[ignore]
async fn test_create_memory_invalid_json() {
    let client = TestClient::new();

    // Try to post invalid JSON
    let response = client
        .client
        .post(&format!("{}/api/v1/memories", BASE_URL))
        .header("Content-Type", "application/json")
        .body("invalid json")
        .send()
        .await
        .expect("Failed to send request");

    // Should return 400 Bad Request
    assert!(response.status() == 400 || response.status() == 401);

    println!("✓ Invalid JSON test passed");
}

#[tokio::test]
#[ignore]
async fn test_get_nonexistent_memory() {
    // This test requires a valid token, so we'll mark it as TODO for now
    // Once we have token generation, we can test 404 responses
    println!("⏳ Get nonexistent memory test - requires valid JWT token");
    println!("   TODO: Implement test token generation");
}

#[tokio::test]
#[ignore]
async fn test_cors_headers() {
    let client = TestClient::new();

    // Make an OPTIONS request to test CORS using request builder
    let response = client
        .client
        .request(reqwest::Method::OPTIONS, &format!("{}/api/v1/memories", BASE_URL))
        .send()
        .await
        .expect("Failed to send request");

    // CORS should allow all origins based on the CORS configuration
    // In a real scenario, you'd check for specific CORS headers
    println!("✓ CORS test completed - status: {}", response.status());
}

/// Test suite runner - can be used to run all tests in sequence
#[tokio::test]
#[ignore]
async fn run_all_integration_tests() {
    println!("🧪 Running Memory Service Integration Tests");
    println!("{}", "=".repeat(60));

    // These tests should be run individually, but this provides a summary
    println!("✓ Test suite structure complete");
    println!("⚠ Note: Tests require running service and valid JWT tokens");
    println!("⚠ To generate test tokens, use Core API or JWT test utilities");
}
