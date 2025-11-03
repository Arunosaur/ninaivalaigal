/// Test helpers for integration tests
/// Provides utilities for generating test JWT tokens, setting up test data, etc.

use serde_json::Value;
use uuid::Uuid;

/// Helper to get a test JWT token from Core API
/// This requires Core API to be running and a test user to exist
pub async fn get_test_token_from_core_api() -> Result<String, Box<dyn std::error::Error>> {
    // TODO: Implement actual token fetch from Core API
    // For now, return an error indicating this needs to be implemented
    Err("Token generation from Core API not yet implemented".into())
}

/// Helper to create test memory data
pub fn create_test_memory_request(content: &str) -> Value {
    serde_json::json!({
        "content": content,
        "metadata": {
            "tag": "test",
            "test_id": Uuid::new_v4().to_string()
        }
    })
}

/// Helper to validate memory response structure
pub fn validate_memory_response(response: &Value) -> bool {
    response.get("id").is_some()
        && response.get("content").is_some()
        && response.get("created_at").is_some()
        && response.get("updated_at").is_some()
}

/// Helper to wait for service to be ready
pub async fn wait_for_service(base_url: &str, max_retries: u32) -> bool {
    let client = reqwest::Client::new();

    for i in 0..max_retries {
        match client.get(format!("{}/health", base_url)).send().await {
            Ok(resp) if resp.status() == 200 => return true,
            _ => {
                if i < max_retries - 1 {
                    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
                }
            }
        }
    }

    false
}
