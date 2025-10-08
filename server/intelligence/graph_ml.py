"""
Graph-Aware ML Engine
Graph Neural Networks for intelligent memory ranking and relationship prediction
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    EmbeddingUpdate,
    GraphContext,
    GraphMLMetrics,
    RelationshipPrediction,
    ScoredMemory,
    UserFeedback,
    WeightUpdate,
)

logger = logging.getLogger(__name__)


class GraphMLEngine:
    """
    Graph Neural Network engine for intelligent memory ranking and relationship prediction

    Features:
    - Graph-aware memory relevance scoring
    - Relationship prediction between memories
    - Adaptive learning from user feedback
    - Embedding optimization with graph features
    """

    def __init__(self, config: Dict):
        self.config = config
        self.model_cache = {}
        self.feature_weights = {
            "content_similarity": 0.25,
            "graph_centrality": 0.20,
            "temporal_relevance": 0.15,
            "user_context": 0.20,
            "collaboration_strength": 0.10,
            "feedback_score": 0.10,
        }
        self.metrics = GraphMLMetrics(
            model_accuracy=0.0,
            prediction_confidence=0.0,
            processing_latency_ms=0.0,
            memory_usage_mb=0.0,
            throughput_qps=0.0,
            error_rate=0.0,
            last_training=datetime.utcnow(),
            model_version="1.0.0",
        )

    async def predict_memory_relevance(
        self,
        query: str,
        context: GraphContext,
        candidate_memories: List[Dict],
        limit: int = 20,
    ) -> List[ScoredMemory]:
        """
        Predict memory relevance using graph-aware ML

        Args:
            query: User query or search term
            context: Graph context including user, team, and task information
            candidate_memories: List of candidate memories to score
            limit: Maximum number of scored memories to return

        Returns:
            List of memories with ML-generated relevance scores
        """
        start_time = datetime.utcnow()

        try:
            scored_memories = []

            for memory in candidate_memories:
                # Extract graph features for this memory
                graph_features = await self._extract_graph_features(memory, context)

                # Calculate content similarity
                content_score = await self._calculate_content_similarity(query, memory)

                # Calculate graph-based scores
                centrality_score = graph_features.get("centrality", 0.0)
                temporal_score = self._calculate_temporal_relevance(memory, context)
                context_score = await self._calculate_context_relevance(memory, context)
                collaboration_score = graph_features.get("collaboration_strength", 0.0)

                # Get historical feedback score
                feedback_score = await self._get_feedback_score(
                    memory["id"], context.user_id
                )

                # Combine scores using learned weights
                relevance_score = (
                    self.feature_weights["content_similarity"] * content_score
                    + self.feature_weights["graph_centrality"] * centrality_score
                    + self.feature_weights["temporal_relevance"] * temporal_score
                    + self.feature_weights["user_context"] * context_score
                    + self.feature_weights["collaboration_strength"]
                    * collaboration_score
                    + self.feature_weights["feedback_score"] * feedback_score
                )

                # Calculate confidence based on feature agreement
                confidence = self._calculate_prediction_confidence(
                    [
                        content_score,
                        centrality_score,
                        temporal_score,
                        context_score,
                        collaboration_score,
                        feedback_score,
                    ]
                )

                # Generate reasoning for transparency
                reasoning = self._generate_reasoning(
                    content_score,
                    centrality_score,
                    temporal_score,
                    context_score,
                    collaboration_score,
                    feedback_score,
                )

                # Get graph connections
                connections = await self._get_memory_connections(memory["id"], context)

                scored_memory = ScoredMemory(
                    memory_id=memory["id"],
                    content_preview=memory.get("content", "")[:200] + "...",
                    relevance_score=relevance_score,
                    confidence=confidence,
                    reasoning=reasoning,
                    graph_connections=connections,
                    temporal_relevance=temporal_score,
                    team_relevance=context_score,
                )

                scored_memories.append(scored_memory)

            # Sort by relevance score and return top results
            scored_memories.sort(key=lambda m: m.relevance_score, reverse=True)

            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_ml_metrics(len(scored_memories), processing_time)

            return scored_memories[:limit]

        except Exception as e:
            logger.error(f"Memory relevance prediction failed: {e}")
            self.metrics.error_rate += 1
            return []

    async def train_relationship_predictor(
        self, training_data: List[Dict], validation_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Train the relationship prediction model using graph data

        Args:
            training_data: Training examples with memory pairs and relationships
            validation_data: Optional validation data for model evaluation

        Returns:
            Training results and model performance metrics
        """
        try:
            logger.info("Starting relationship predictor training...")

            # Prepare training features
            features, labels = await self._prepare_training_data(training_data)

            # Train graph neural network model
            model_results = await self._train_gnn_model(features, labels)

            # Validate model if validation data provided
            if validation_data:
                val_features, val_labels = await self._prepare_training_data(
                    validation_data
                )
                validation_results = await self._validate_model(
                    val_features, val_labels
                )
                model_results.update(validation_results)

            # Update model cache and metrics
            self.model_cache["relationship_predictor"] = model_results["model"]
            self.metrics.model_accuracy = model_results.get("accuracy", 0.0)
            self.metrics.last_training = datetime.utcnow()
            self.metrics.model_version = f"1.0.{int(datetime.utcnow().timestamp())}"

            logger.info(
                f"Training completed. Accuracy: {self.metrics.model_accuracy:.3f}"
            )

            return model_results

        except Exception as e:
            logger.error(f"Relationship predictor training failed: {e}")
            return {"success": False, "error": str(e)}

    async def predict_relationships(
        self,
        memory_id: str,
        candidate_memories: List[str],
        context: GraphContext,
        threshold: float = 0.7,
    ) -> List[RelationshipPrediction]:
        """
        Predict relationships between memories using trained model

        Args:
            memory_id: Source memory ID
            candidate_memories: List of candidate memory IDs for relationships
            context: Graph context for prediction
            threshold: Minimum confidence threshold for predictions

        Returns:
            List of predicted relationships above threshold
        """
        try:
            if "relationship_predictor" not in self.model_cache:
                logger.warning("Relationship predictor not trained")
                return []

            predictions = []
            model = self.model_cache["relationship_predictor"]

            for candidate_id in candidate_memories:
                # Extract features for memory pair
                pair_features = await self._extract_pair_features(
                    memory_id, candidate_id, context
                )

                # Predict relationship using trained model
                prediction_result = await self._predict_with_model(model, pair_features)

                if prediction_result["confidence"] >= threshold:
                    # Generate supporting evidence
                    evidence = await self._generate_relationship_evidence(
                        memory_id, candidate_id, pair_features
                    )

                    # Find graph path between memories
                    graph_path = await self._find_graph_path(memory_id, candidate_id)

                    prediction = RelationshipPrediction(
                        memory_a=memory_id,
                        memory_b=candidate_id,
                        relationship_type=prediction_result["relationship_type"],
                        confidence=prediction_result["confidence"],
                        supporting_evidence=evidence,
                        graph_path=graph_path,
                    )

                    predictions.append(prediction)

            # Sort by confidence
            predictions.sort(key=lambda p: p.confidence, reverse=True)

            return predictions

        except Exception as e:
            logger.error(f"Relationship prediction failed: {e}")
            return []

    async def optimize_embeddings(
        self,
        memories: List[Dict],
        graph_data: Dict,
        optimization_target: str = "relevance",
    ) -> List[EmbeddingUpdate]:
        """
        Optimize memory embeddings using graph structure and relationships

        Args:
            memories: List of memories to optimize embeddings for
            graph_data: Graph structure and relationship data
            optimization_target: Target metric for optimization ('relevance', 'clustering', etc.)

        Returns:
            List of embedding updates with improvement scores
        """
        try:
            embedding_updates = []

            for memory in memories:
                # Get current embedding
                current_embedding = memory.get("embedding", [])
                if not current_embedding:
                    continue

                # Extract graph features for this memory
                graph_features = await self._extract_memory_graph_features(
                    memory, graph_data
                )

                # Optimize embedding using graph-enhanced approach
                enhanced_embedding = await self._enhance_embedding_with_graph(
                    current_embedding, graph_features, optimization_target
                )

                # Calculate improvement score
                improvement_score = await self._calculate_embedding_improvement(
                    current_embedding, enhanced_embedding, memory, graph_data
                )

                if improvement_score > 0.05:  # Only update if significant improvement
                    update = EmbeddingUpdate(
                        memory_id=memory["id"],
                        original_embedding=current_embedding,
                        enhanced_embedding=enhanced_embedding,
                        improvement_score=improvement_score,
                        graph_features=graph_features,
                    )

                    embedding_updates.append(update)

            logger.info(f"Generated {len(embedding_updates)} embedding updates")
            return embedding_updates

        except Exception as e:
            logger.error(f"Embedding optimization failed: {e}")
            return []

    async def adapt_ranking_weights(
        self, feedback_batch: List[UserFeedback], learning_rate: float = 0.01
    ) -> WeightUpdate:
        """
        Adapt ranking weights based on user feedback using online learning

        Args:
            feedback_batch: Batch of user feedback for learning
            learning_rate: Learning rate for weight updates

        Returns:
            Weight update with performance improvement metrics
        """
        try:
            # Analyze feedback patterns
            feedback_analysis = await self._analyze_feedback_patterns(feedback_batch)

            # Calculate weight gradients based on feedback
            weight_gradients = await self._calculate_weight_gradients(
                feedback_batch, feedback_analysis
            )

            # Update weights using gradient descent
            old_weights = self.feature_weights.copy()
            performance_before = await self._evaluate_current_performance(
                feedback_batch
            )

            for feature, gradient in weight_gradients.items():
                if feature in self.feature_weights:
                    self.feature_weights[feature] += learning_rate * gradient

            # Normalize weights to sum to 1.0
            total_weight = sum(self.feature_weights.values())
            if total_weight > 0:
                self.feature_weights = {
                    k: v / total_weight for k, v in self.feature_weights.items()
                }

            # Evaluate performance improvement
            performance_after = await self._evaluate_updated_performance(feedback_batch)
            performance_improvement = performance_after - performance_before

            # Revert if performance decreased significantly
            if performance_improvement < -0.05:
                self.feature_weights = old_weights
                performance_improvement = 0.0
                update_reason = "Reverted due to performance decrease"
            else:
                update_reason = (
                    f"Improved based on {len(feedback_batch)} feedback samples"
                )

            weight_update = WeightUpdate(
                feature_weights=self.feature_weights.copy(),
                confidence_threshold=self._calculate_confidence_threshold(
                    feedback_analysis
                ),
                learning_rate=learning_rate,
                update_reason=update_reason,
                performance_improvement=performance_improvement,
            )

            logger.info(
                f"Weight update: {update_reason}, improvement: {performance_improvement:.3f}"
            )

            return weight_update

        except Exception as e:
            logger.error(f"Weight adaptation failed: {e}")
            return WeightUpdate(
                feature_weights=self.feature_weights,
                confidence_threshold=0.5,
                learning_rate=learning_rate,
                update_reason=f"Failed: {str(e)}",
                performance_improvement=0.0,
            )

    async def _extract_graph_features(
        self, memory: Dict, context: GraphContext
    ) -> Dict[str, float]:
        """Extract graph-based features for a memory"""
        features = {}

        # Calculate centrality measures
        features["centrality"] = await self._calculate_memory_centrality(memory["id"])
        features["clustering_coefficient"] = (
            await self._calculate_clustering_coefficient(memory["id"])
        )

        # Calculate collaboration strength with user's team
        features["collaboration_strength"] = (
            await self._calculate_collaboration_strength(memory, context.team_context)
        )

        # Calculate graph-based similarity to recent memories
        features["graph_similarity"] = await self._calculate_graph_similarity(
            memory["id"], context.recent_memories
        )

        # Calculate expertise alignment
        features["expertise_alignment"] = await self._calculate_expertise_alignment(
            memory, context.expertise_areas
        )

        return features

    async def _calculate_content_similarity(self, query: str, memory: Dict) -> float:
        """Calculate content similarity between query and memory"""
        # This would use embeddings or TF-IDF for better similarity
        # For now, simple keyword matching
        query_words = set(query.lower().split())
        memory_content = memory.get("content", "") + " " + memory.get("title", "")
        memory_words = set(memory_content.lower().split())

        if not query_words or not memory_words:
            return 0.0

        intersection = len(query_words & memory_words)
        union = len(query_words | memory_words)

        return intersection / union if union > 0 else 0.0

    def _calculate_temporal_relevance(
        self, memory: Dict, context: GraphContext
    ) -> float:
        """Calculate temporal relevance based on memory age and access patterns"""
        created_at = memory.get("created_at")
        if not created_at:
            return 0.5

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        # Age-based decay
        age_days = (datetime.utcnow() - created_at).days
        age_score = max(0, 1 - (age_days / 365))  # Decay over 1 year

        # Recent access boost
        last_accessed = memory.get("last_accessed")
        access_score = 0.5  # Default
        if last_accessed:
            if isinstance(last_accessed, str):
                last_accessed = datetime.fromisoformat(
                    last_accessed.replace("Z", "+00:00")
                )
            days_since_access = (datetime.utcnow() - last_accessed).days
            access_score = max(0, 1 - (days_since_access / 30))  # Decay over 30 days

        return age_score * 0.6 + access_score * 0.4

    def _calculate_prediction_confidence(self, feature_scores: List[float]) -> float:
        """Calculate prediction confidence based on feature agreement"""
        if not feature_scores:
            return 0.0

        # Calculate variance - lower variance means higher confidence
        mean_score = sum(feature_scores) / len(feature_scores)
        variance = sum((score - mean_score) ** 2 for score in feature_scores) / len(
            feature_scores
        )

        # Convert variance to confidence (inverse relationship)
        confidence = max(0, 1 - (variance * 2))  # Scale variance to 0-1 range

        return confidence

    def _generate_reasoning(self, *scores) -> List[str]:
        """Generate human-readable reasoning for the relevance score"""
        reasoning = []

        (
            content_score,
            centrality_score,
            temporal_score,
            context_score,
            collab_score,
            feedback_score,
        ) = scores

        if content_score > 0.7:
            reasoning.append("High content similarity to query")
        elif content_score > 0.4:
            reasoning.append("Moderate content relevance")

        if centrality_score > 0.6:
            reasoning.append("Highly connected in knowledge graph")

        if temporal_score > 0.7:
            reasoning.append("Recently created or accessed")
        elif temporal_score < 0.3:
            reasoning.append("Older content, may need verification")

        if context_score > 0.6:
            reasoning.append("Strong alignment with team context")

        if collab_score > 0.5:
            reasoning.append("From collaborative team relationship")

        if feedback_score > 0.6:
            reasoning.append("Positive user feedback history")
        elif feedback_score < 0.3:
            reasoning.append("Limited positive feedback")

        return reasoning if reasoning else ["Standard relevance scoring applied"]

    def _update_ml_metrics(self, processed_count: int, processing_time: float):
        """Update ML performance metrics"""
        # Update processing latency (exponential moving average)
        alpha = 0.1
        self.metrics.processing_latency_ms = (
            alpha * processing_time + (1 - alpha) * self.metrics.processing_latency_ms
        )

        # Update throughput (queries per second)
        if processing_time > 0:
            current_qps = (
                processed_count / processing_time
            ) * 1000  # Convert ms to seconds
            self.metrics.throughput_qps = (
                alpha * current_qps + (1 - alpha) * self.metrics.throughput_qps
            )

    async def get_ml_metrics(self) -> GraphMLMetrics:
        """Get current ML performance metrics"""
        return self.metrics
