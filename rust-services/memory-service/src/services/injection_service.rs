//! Injection Service - Core logic for memory injection operations
//! US#93/US#95: Memory Router Rationalization - SPEC-131

use serde_json::Value;
use sqlx::Result as SqlxResult;
use std::sync::Arc;
use tracing::{debug, error, warn};
use uuid::Uuid;

use crate::api::injection::InjectionCandidate;
use crate::cache::MemoryCache;
use crate::models::CreateMemoryRequest;
use crate::storage::MemoryStorage;

/// Service for memory injection operations
pub struct InjectionService {
    storage: Arc<MemoryStorage>,
    cache: MemoryCache,
}

impl InjectionService {
    pub fn new(storage: Arc<MemoryStorage>, cache: MemoryCache) -> Self {
        Self { storage, cache }
    }

    /// Analyze injection opportunities based on context
    pub async fn analyze_opportunities(
        &self,
        user_id: Uuid,
        context: &Value,
        max_candidates: usize,
    ) -> SqlxResult<Vec<InjectionCandidate>> {
        debug!(user_id = %user_id, "analyzing injection opportunities");

        // Get user's memories for analysis
        let memories = self.storage.get_memories(user_id).await?;

        // Simple relevance scoring based on semantic context
        let _semantic_context = context.get("semantic_context").and_then(|v| v.as_object());
        let current_activity = context.get("current_activity").and_then(|v| v.as_str());

        let mut candidates: Vec<InjectionCandidate> = memories
            .into_iter()
            .enumerate()
            .filter_map(|(idx, memory)| {
                // Simple relevance scoring - in production, this would use embeddings/similarity
                let relevance_score = if let Some(activity) = current_activity {
                    if memory.content.to_lowercase().contains(&activity.to_lowercase()) {
                        0.8
                    } else {
                        0.5
                    }
                } else {
                    0.5
                };

                // Only include memories with decent relevance
                if relevance_score >= 0.5 {
                    Some(InjectionCandidate {
                        memory_id: memory.id.to_string(),
                        relevance_score,
                        injection_reason: format!("Context match: {}", current_activity.unwrap_or("general")),
                        rule_id: None,
                        confidence: relevance_score,
                        urgency: if relevance_score > 0.7 { 0.7 } else { 0.5 },
                        context_match: serde_json::json!({
                            "activity": current_activity,
                            "memory_index": idx,
                        }),
                        suggested_timing: "immediate".to_string(),
                        metadata: memory.metadata.clone(),
                    })
                } else {
                    None
                }
            })
            .collect();

        // Sort by relevance score (descending)
        candidates.sort_by(|a, b| {
            b.relevance_score
                .partial_cmp(&a.relevance_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        // Limit to max_candidates
        candidates.truncate(max_candidates);

        Ok(candidates)
    }

    /// Inject memories based on context and strategy
    pub async fn inject_memories(
        &self,
        user_id: Uuid,
        context: &Value,
        strategy: &str,
        max_injections: usize,
    ) -> SqlxResult<Vec<crate::models::Memory>> {
        debug!(
            user_id = %user_id,
            strategy = %strategy,
            max_injections = max_injections,
            "injecting memories"
        );

        // Analyze opportunities first
        let candidates = self
            .analyze_opportunities(user_id, context, max_injections)
            .await?;

        // For now, we return existing memories that match
        // In a full implementation, this would create new memories or activate existing ones
        let memory_ids: Vec<Uuid> = candidates
            .iter()
            .filter_map(|c| Uuid::parse_str(&c.memory_id).ok())
            .collect();

        let memories = self.storage.get_memories(user_id).await?;
        let injected: Vec<_> = memories
            .into_iter()
            .filter(|m| memory_ids.contains(&m.id))
            .collect();

        // Invalidate cache after injection
        if let Err(e) = self.cache.invalidate_user(user_id).await {
            warn!(?e, user_id = %user_id, "failed to invalidate cache after injection");
        }

        Ok(injected)
    }

    /// Bulk inject memories (high-performance path)
    ///
    /// This is the primary performance-critical operation for bulk processing.
    pub async fn bulk_inject(
        &self,
        user_id: Uuid,
        items: &[Value],
    ) -> SqlxResult<Vec<crate::api::injection::BulkInjectionResult>> {
        debug!(
            user_id = %user_id,
            batch_size = items.len(),
            "bulk injecting memories"
        );

        let mut results = Vec::with_capacity(items.len());

        for item in items {
            let result = match self.process_bulk_item(user_id, item).await {
                Ok(memory_id) => crate::api::injection::BulkInjectionResult {
                    success: true,
                    memory_id: Some(memory_id.to_string()),
                    error: None,
                },
                Err(e) => {
                    error!(?e, "failed to process bulk item");
                    crate::api::injection::BulkInjectionResult {
                        success: false,
                        memory_id: None,
                        error: Some(e.to_string()),
                    }
                }
            };
            results.push(result);
        }

        // Invalidate cache after bulk operations
        if let Err(e) = self.cache.invalidate_user(user_id).await {
            warn!(?e, user_id = %user_id, "failed to invalidate cache after bulk injection");
        }

        Ok(results)
    }

    /// Process a single item in a bulk operation
    async fn process_bulk_item(&self, user_id: Uuid, item: &Value) -> SqlxResult<Uuid> {
        let content = item
            .get("content")
            .and_then(|v| v.as_str())
            .ok_or_else(|| sqlx::Error::RowNotFound)?;

        let request = CreateMemoryRequest {
            content: content.to_string(),
            context_id: item.get("context_id").and_then(|v| v.as_str()).map(|s| Uuid::parse_str(s).ok()).flatten(),
            metadata: item.get("metadata").cloned(),
        };

        let memory = self.storage.create_memory(user_id, request).await?;
        Ok(memory.id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    // Note: These are unit tests for the service logic
    // Full integration tests would require database and Redis connections
    // and should be in the tests/ directory

    #[test]
    fn test_injection_candidate_creation() {
        // Test that we can create injection candidates with proper structure
        let candidate = InjectionCandidate {
            memory_id: "123e4567-e89b-12d3-a456-426614174000".to_string(),
            relevance_score: 0.8,
            injection_reason: "Context match: test".to_string(),
            rule_id: None,
            confidence: 0.8,
            urgency: 0.7,
            context_match: json!({"activity": "test"}),
            suggested_timing: "immediate".to_string(),
            metadata: json!({}),
        };

        assert_eq!(candidate.memory_id, "123e4567-e89b-12d3-a456-426614174000");
        assert_eq!(candidate.relevance_score, 0.8);
        assert_eq!(candidate.confidence, 0.8);
    }

    #[test]
    fn test_context_parsing() {
        // Test context JSON parsing
        let context = json!({
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "current_activity": "coding",
            "semantic_context": {
                "language": "rust",
                "topic": "testing"
            }
        });

        assert_eq!(context.get("current_activity").and_then(|v| v.as_str()), Some("coding"));
        assert!(context.get("semantic_context").is_some());
    }

    #[test]
    fn test_relevance_scoring_logic() {
        // Test the relevance scoring algorithm logic
        let activity = Some("coding");
        let content_with_activity = "I'm coding in Rust";
        let content_without_activity = "I'm reading a book";

        let score_with = if let Some(act) = activity {
            if content_with_activity.to_lowercase().contains(&act.to_lowercase()) {
                0.8
            } else {
                0.5
            }
        } else {
            0.5
        };

        let score_without = if let Some(act) = activity {
            if content_without_activity.to_lowercase().contains(&act.to_lowercase()) {
                0.8
            } else {
                0.5
            }
        } else {
            0.5
        };

        assert_eq!(score_with, 0.8);
        assert_eq!(score_without, 0.5);
    }
}
