//! Integration test helper utilities
//! US#93/US#95: Memory Router Rationalization - SPEC-131

use serde_json::json;
use std::time::Duration;

/// Test configuration
pub struct TestConfig {
    pub base_url: String,
    pub jwt_token: Option<String>,
    pub timeout: Duration,
}

impl Default for TestConfig {
    fn default() -> Self {
        Self {
            base_url: std::env::var("TEST_API_BASE_URL")
                .unwrap_or_else(|_| "http://localhost:13393".to_string()),
            jwt_token: std::env::var("TEST_JWT_TOKEN").ok(),
            timeout: Duration::from_secs(30),
        }
    }
}

/// Test client for making API requests
pub struct TestClient {
    client: reqwest::Client,
    config: TestConfig,
}

impl TestClient {
    pub fn new(config: TestConfig) -> Self {
        let client = reqwest::Client::builder()
            .timeout(config.timeout)
            .build()
            .expect("failed to create HTTP client");

        Self { client, config }
    }

    pub fn with_token(token: String) -> Self {
        let mut config = TestConfig::default();
        config.jwt_token = Some(token);
        Self::new(config)
    }

    fn headers(&self) -> reqwest::header::HeaderMap {
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert(
            reqwest::header::CONTENT_TYPE,
            "application/json".parse().unwrap(),
        );

        if let Some(token) = &self.config.jwt_token {
            headers.insert(
                reqwest::header::AUTHORIZATION,
                format!("Bearer {}", token).parse().unwrap(),
            );
        }

        headers
    }

    pub async fn get(&self, path: &str) -> Result<reqwest::Response, reqwest::Error> {
        self.client
            .get(format!("{}{}", self.config.base_url, path))
            .headers(self.headers())
            .send()
            .await
    }

    pub async fn post(
        &self,
        path: &str,
        body: &serde_json::Value,
    ) -> Result<reqwest::Response, reqwest::Error> {
        self.client
            .post(format!("{}{}", self.config.base_url, path))
            .headers(self.headers())
            .json(body)
            .send()
            .await
    }

    pub async fn health_check(&self) -> Result<bool, reqwest::Error> {
        match self.get("/health").await {
            Ok(response) => Ok(response.status().is_success()),
            Err(e) => Err(e),
        }
    }
}

/// Create a test JWT token (mock implementation)
/// In real tests, this would generate a valid JWT token
pub fn create_test_token() -> String {
    // This is a placeholder - in real tests, use the actual JWT secret
    // to generate a valid token or use a test token from the auth system
    std::env::var("TEST_JWT_TOKEN").unwrap_or_else(|_| "test-token".to_string())
}

/// Wait for service to be healthy
pub async fn wait_for_service(base_url: &str, max_attempts: u32) -> bool {
    let client = reqwest::Client::new();
    for attempt in 1..=max_attempts {
        if let Ok(response) = client
            .get(format!("{}/health", base_url))
            .timeout(Duration::from_secs(2))
            .send()
            .await
        {
            if response.status().is_success() {
                return true;
            }
        }
        if attempt < max_attempts {
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    }
    false
}

/// Generate test injection context
pub fn test_injection_context() -> serde_json::Value {
    json!({
        "session_id": "test-session-123",
        "current_activity": "coding",
        "location_context": {},
        "temporal_context": {},
        "semantic_context": {
            "language": "rust",
            "topic": "testing"
        },
        "user_state": {},
        "environment": {}
    })
}

/// Generate test bulk injection items
pub fn test_bulk_items(count: usize) -> Vec<serde_json::Value> {
    (0..count)
        .map(|i| {
            json!({
                "content": format!("Test memory content {}", i),
                "metadata": {
                    "index": i,
                    "source": "test"
                }
            })
        })
        .collect()
}




