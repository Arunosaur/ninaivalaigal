"""
SPEC-044: Memory Drift & Diff Detection Engine

Provides comprehensive memory change tracking and drift detection:
- Content diff analysis and similarity scoring
- Memory versioning and snapshot comparison
- Semantic drift detection using embeddings
- Drift monitoring and alerting
- Change visualization and reporting

Key Features:
- Real-time drift detection
- Historical change tracking
- Semantic similarity analysis
- Automated drift alerts
- Integration with existing memory systems
"""

import difflib
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import structlog
from redis_client import get_redis_client

# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
# Note: Using basic similarity calculations to avoid external dependencies


logger = structlog.get_logger(__name__)


class DriftType(Enum):
    """Types of memory drift"""

    CONTENT = "content"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    METADATA = "metadata"


class DriftSeverity(Enum):
    """Drift severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemorySnapshot:
    """Memory snapshot for comparison"""

    memory_id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None
    content_hash: str
    created_at: datetime
    version: int


@dataclass
class DriftDetection:
    """Drift detection result"""

    memory_id: str
    drift_type: DriftType
    severity: DriftSeverity
    confidence: float
    old_snapshot: MemorySnapshot
    new_snapshot: MemorySnapshot
    changes: dict[str, Any]
    detected_at: datetime


@dataclass
class DriftReport:
    """Comprehensive drift report"""

    memory_id: str
    total_drifts: int
    drift_detections: list[DriftDetection]
    drift_timeline: list[dict[str, Any]]
    summary_stats: dict[str, Any]
    generated_at: datetime


class MemoryDriftEngine:
    """Core engine for memory drift and diff detection"""

    def __init__(self):
        self.redis_client = None
        self.snapshot_ttl = 86400 * 30  # 30 days
        self.drift_threshold = 0.3  # Similarity threshold for drift detection

        # Drift severity thresholds
        self.severity_thresholds = {
            DriftSeverity.LOW: 0.1,
            DriftSeverity.MEDIUM: 0.3,
            DriftSeverity.HIGH: 0.6,
            DriftSeverity.CRITICAL: 0.8,
        }

    async def initialize(self):
        """Initialize Redis connections"""
        try:
            self.redis_client = await get_redis_client()
            if self.redis_client:
                await self.redis_client.ping()
            logger.info("Memory drift engine initialized successfully")
        except Exception as e:
            logger.warning(
                "Failed to initialize memory drift engine Redis connection",
                error=str(e),
            )
            self.redis_client = None

    async def create_memory_snapshot(
        self,
        memory_id: str,
        content: str,
        metadata: dict[str, Any] = None,
        embedding: list[float] = None,
    ) -> MemorySnapshot:
        """Create a memory snapshot for drift tracking"""

        try:
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Get current version
            current_version = await self._get_next_version(memory_id)

            snapshot = MemorySnapshot(
                memory_id=memory_id,
                content=content,
                metadata=metadata or {},
                embedding=embedding,
                content_hash=content_hash,
                created_at=datetime.utcnow(),
                version=current_version,
            )

            # Store snapshot
            await self._store_snapshot(snapshot)

            logger.info(
                "Memory snapshot created",
                memory_id=memory_id,
                version=current_version,
                content_hash=content_hash[:8],
            )

            return snapshot

        except Exception as e:
            logger.error(
                "Failed to create memory snapshot", memory_id=memory_id, error=str(e)
            )
            raise

    async def detect_drift(
        self,
        memory_id: str,
        new_content: str,
        new_metadata: dict[str, Any] = None,
        new_embedding: list[float] = None,
    ) -> list[DriftDetection]:
        """Detect drift between current and previous memory states"""

        try:
            # Get latest snapshot
            latest_snapshot = await self._get_latest_snapshot(memory_id)
            if not latest_snapshot:
                logger.info(
                    "No previous snapshot found for drift detection",
                    memory_id=memory_id,
                )
                return []

            # Create new snapshot
            new_snapshot = await self.create_memory_snapshot(
                memory_id, new_content, new_metadata, new_embedding
            )

            detections = []

            # Content drift detection
            content_drift = await self._detect_content_drift(
                latest_snapshot, new_snapshot
            )
            if content_drift:
                detections.append(content_drift)

            # Semantic drift detection
            if latest_snapshot.embedding and new_embedding:
                semantic_drift = await self._detect_semantic_drift(
                    latest_snapshot, new_snapshot
                )
                if semantic_drift:
                    detections.append(semantic_drift)

            # Metadata drift detection
            metadata_drift = await self._detect_metadata_drift(
                latest_snapshot, new_snapshot
            )
            if metadata_drift:
                detections.append(metadata_drift)

            # Store drift detections
            for detection in detections:
                await self._store_drift_detection(detection)

            if detections:
                logger.info(
                    "Drift detected",
                    memory_id=memory_id,
                    drift_count=len(detections),
                    drift_types=[d.drift_type.value for d in detections],
                )

            return detections

        except Exception as e:
            logger.error("Failed to detect drift", memory_id=memory_id, error=str(e))
            return []

    async def get_drift_history(
        self, memory_id: str, limit: int = 50
    ) -> list[DriftDetection]:
        """Get drift detection history for a memory"""

        try:
            if not self.redis_client:
                return []

            # Get drift detection keys
            pattern = f"drift:detection:{memory_id}:*"
            keys = await self.redis_client.keys(pattern)

            detections = []
            for key in sorted(keys, reverse=True)[:limit]:
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        detection_data = json.loads(data)
                        detection = self._deserialize_drift_detection(detection_data)
                        detections.append(detection)
                except Exception as e:
                    logger.warning(
                        "Failed to deserialize drift detection", key=key, error=str(e)
                    )

            return detections

        except Exception as e:
            logger.error(
                "Failed to get drift history", memory_id=memory_id, error=str(e)
            )
            return []

    async def generate_drift_report(
        self, memory_id: str, days_back: int = 30
    ) -> DriftReport:
        """Generate comprehensive drift report"""

        try:
            # Get drift history
            drift_detections = await self.get_drift_history(memory_id, limit=1000)

            # Filter by time range
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            recent_drifts = [
                d for d in drift_detections if d.detected_at >= cutoff_date
            ]

            # Generate timeline
            timeline = []
            for drift in recent_drifts:
                timeline.append(
                    {
                        "timestamp": drift.detected_at.isoformat(),
                        "drift_type": drift.drift_type.value,
                        "severity": drift.severity.value,
                        "confidence": drift.confidence,
                    }
                )

            # Calculate summary stats
            summary_stats = {
                "total_drifts": len(recent_drifts),
                "drift_types": {},
                "severity_distribution": {},
                "average_confidence": 0.0,
                "most_recent_drift": None,
                "drift_frequency": 0.0,
            }

            if recent_drifts:
                # Drift type distribution
                for drift in recent_drifts:
                    drift_type = drift.drift_type.value
                    summary_stats["drift_types"][drift_type] = (
                        summary_stats["drift_types"].get(drift_type, 0) + 1
                    )

                # Severity distribution
                for drift in recent_drifts:
                    severity = drift.severity.value
                    summary_stats["severity_distribution"][severity] = (
                        summary_stats["severity_distribution"].get(severity, 0) + 1
                    )

                # Average confidence
                summary_stats["average_confidence"] = sum(
                    d.confidence for d in recent_drifts
                ) / len(recent_drifts)

                # Most recent drift
                summary_stats["most_recent_drift"] = recent_drifts[
                    0
                ].detected_at.isoformat()

                # Drift frequency (drifts per day)
                summary_stats["drift_frequency"] = len(recent_drifts) / days_back

            report = DriftReport(
                memory_id=memory_id,
                total_drifts=len(recent_drifts),
                drift_detections=recent_drifts[:10],  # Top 10 most recent
                drift_timeline=timeline,
                summary_stats=summary_stats,
                generated_at=datetime.utcnow(),
            )

            logger.info(
                "Drift report generated",
                memory_id=memory_id,
                total_drifts=len(recent_drifts),
                days_back=days_back,
            )

            return report

        except Exception as e:
            logger.error(
                "Failed to generate drift report", memory_id=memory_id, error=str(e)
            )
            raise

    async def _detect_content_drift(
        self, old_snapshot: MemorySnapshot, new_snapshot: MemorySnapshot
    ) -> DriftDetection | None:
        """Detect content-based drift"""

        try:
            # Skip if content is identical
            if old_snapshot.content_hash == new_snapshot.content_hash:
                return None

            # Calculate text similarity
            similarity = self._calculate_text_similarity(
                old_snapshot.content, new_snapshot.content
            )

            # Calculate drift confidence (inverse of similarity)
            confidence = 1.0 - similarity

            # Determine severity
            severity = self._calculate_severity(confidence)

            # Generate diff
            diff = list(
                difflib.unified_diff(
                    old_snapshot.content.splitlines(keepends=True),
                    new_snapshot.content.splitlines(keepends=True),
                    fromfile=f"version_{old_snapshot.version}",
                    tofile=f"version_{new_snapshot.version}",
                )
            )

            changes = {
                "similarity_score": similarity,
                "content_diff": diff[:100],  # Limit diff size
                "char_changes": abs(
                    len(new_snapshot.content) - len(old_snapshot.content)
                ),
                "line_changes": abs(
                    len(new_snapshot.content.splitlines())
                    - len(old_snapshot.content.splitlines())
                ),
            }

            return DriftDetection(
                memory_id=new_snapshot.memory_id,
                drift_type=DriftType.CONTENT,
                severity=severity,
                confidence=confidence,
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot,
                changes=changes,
                detected_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error("Failed to detect content drift", error=str(e))
            return None

    async def _detect_semantic_drift(
        self, old_snapshot: MemorySnapshot, new_snapshot: MemorySnapshot
    ) -> DriftDetection | None:
        """Detect semantic drift using embeddings"""

        try:
            if not old_snapshot.embedding or not new_snapshot.embedding:
                return None

            # Calculate basic dot product similarity (simplified cosine similarity)
            similarity = self._calculate_embedding_similarity(
                old_snapshot.embedding, new_snapshot.embedding
            )
            confidence = 1.0 - similarity

            # Only report if significant semantic drift
            if confidence < self.drift_threshold:
                return None

            severity = self._calculate_severity(confidence)

            changes = {
                "semantic_similarity": float(similarity),
                "embedding_distance": float(confidence),
                "drift_magnitude": "high"
                if confidence > 0.7
                else "medium"
                if confidence > 0.4
                else "low",
            }

            return DriftDetection(
                memory_id=new_snapshot.memory_id,
                drift_type=DriftType.SEMANTIC,
                severity=severity,
                confidence=confidence,
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot,
                changes=changes,
                detected_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error("Failed to detect semantic drift", error=str(e))
            return None

    async def _detect_metadata_drift(
        self, old_snapshot: MemorySnapshot, new_snapshot: MemorySnapshot
    ) -> DriftDetection | None:
        """Detect metadata changes"""

        try:
            old_meta = old_snapshot.metadata or {}
            new_meta = new_snapshot.metadata or {}

            # Find changes
            added_keys = set(new_meta.keys()) - set(old_meta.keys())
            removed_keys = set(old_meta.keys()) - set(new_meta.keys())
            modified_keys = set()

            for key in set(old_meta.keys()) & set(new_meta.keys()):
                if old_meta[key] != new_meta[key]:
                    modified_keys.add(key)

            # Calculate confidence based on number of changes
            total_changes = len(added_keys) + len(removed_keys) + len(modified_keys)
            if total_changes == 0:
                return None

            # Normalize confidence (more changes = higher confidence)
            max_keys = max(len(old_meta), len(new_meta), 1)
            confidence = min(total_changes / max_keys, 1.0)

            severity = self._calculate_severity(confidence)

            changes = {
                "added_keys": list(added_keys),
                "removed_keys": list(removed_keys),
                "modified_keys": list(modified_keys),
                "total_changes": total_changes,
            }

            return DriftDetection(
                memory_id=new_snapshot.memory_id,
                drift_type=DriftType.METADATA,
                severity=severity,
                confidence=confidence,
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot,
                changes=changes,
                detected_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error("Failed to detect metadata drift", error=str(e))
            return None

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using difflib"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def _calculate_embedding_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Calculate embedding similarity using basic dot product (simplified cosine similarity)"""
        try:
            if len(embedding1) != len(embedding2):
                return 0.0

            # Calculate dot product
            dot_product = sum(
                a * b for a, b in zip(embedding1, embedding2, strict=False)
            )

            # Calculate magnitudes
            magnitude1 = sum(a * a for a in embedding1) ** 0.5
            magnitude2 = sum(b * b for b in embedding2) ** 0.5

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            # Cosine similarity
            return dot_product / (magnitude1 * magnitude2)

        except Exception:
            return 0.0  # Default to no similarity on error

    def _calculate_severity(self, confidence: float) -> DriftSeverity:
        """Calculate drift severity based on confidence"""
        if confidence >= self.severity_thresholds[DriftSeverity.CRITICAL]:
            return DriftSeverity.CRITICAL
        elif confidence >= self.severity_thresholds[DriftSeverity.HIGH]:
            return DriftSeverity.HIGH
        elif confidence >= self.severity_thresholds[DriftSeverity.MEDIUM]:
            return DriftSeverity.MEDIUM
        else:
            return DriftSeverity.LOW

    async def _get_next_version(self, memory_id: str) -> int:
        """Get next version number for memory"""
        try:
            if not self.redis_client:
                return 1

            version_key = f"drift:version:{memory_id}"
            current_version = await self.redis_client.get(version_key)

            if current_version:
                next_version = int(current_version) + 1
            else:
                next_version = 1

            await self.redis_client.set(version_key, next_version)
            return next_version

        except Exception:
            return int(time.time())  # Fallback to timestamp

    async def _store_snapshot(self, snapshot: MemorySnapshot):
        """Store memory snapshot"""
        try:
            if not self.redis_client:
                return

            snapshot_key = f"drift:snapshot:{snapshot.memory_id}:{snapshot.version}"
            snapshot_data = {
                "memory_id": snapshot.memory_id,
                "content": snapshot.content,
                "metadata": snapshot.metadata,
                "embedding": snapshot.embedding,
                "content_hash": snapshot.content_hash,
                "created_at": snapshot.created_at.isoformat(),
                "version": snapshot.version,
            }

            await self.redis_client.setex(
                snapshot_key, self.snapshot_ttl, json.dumps(snapshot_data)
            )

            # Update latest snapshot pointer
            latest_key = f"drift:latest:{snapshot.memory_id}"
            await self.redis_client.setex(
                latest_key, self.snapshot_ttl, json.dumps(snapshot_data)
            )

        except Exception as e:
            logger.error("Failed to store snapshot", error=str(e))

    async def _get_latest_snapshot(self, memory_id: str) -> MemorySnapshot | None:
        """Get latest snapshot for memory"""
        try:
            if not self.redis_client:
                return None

            latest_key = f"drift:latest:{memory_id}"
            data = await self.redis_client.get(latest_key)

            if not data:
                return None

            snapshot_data = json.loads(data)
            return MemorySnapshot(
                memory_id=snapshot_data["memory_id"],
                content=snapshot_data["content"],
                metadata=snapshot_data["metadata"],
                embedding=snapshot_data["embedding"],
                content_hash=snapshot_data["content_hash"],
                created_at=datetime.fromisoformat(snapshot_data["created_at"]),
                version=snapshot_data["version"],
            )

        except Exception as e:
            logger.error("Failed to get latest snapshot", error=str(e))
            return None

    async def _store_drift_detection(self, detection: DriftDetection):
        """Store drift detection result"""
        try:
            if not self.redis_client:
                return

            detection_key = f"drift:detection:{detection.memory_id}:{int(detection.detected_at.timestamp())}"
            detection_data = {
                "memory_id": detection.memory_id,
                "drift_type": detection.drift_type.value,
                "severity": detection.severity.value,
                "confidence": detection.confidence,
                "changes": detection.changes,
                "detected_at": detection.detected_at.isoformat(),
                "old_version": detection.old_snapshot.version,
                "new_version": detection.new_snapshot.version,
            }

            await self.redis_client.setex(
                detection_key, self.snapshot_ttl, json.dumps(detection_data)
            )

        except Exception as e:
            logger.error("Failed to store drift detection", error=str(e))

    def _deserialize_drift_detection(self, data: dict[str, Any]) -> DriftDetection:
        """Deserialize drift detection from stored data"""
        # This would normally reconstruct the full DriftDetection object
        # For now, return a simplified version
        return DriftDetection(
            memory_id=data["memory_id"],
            drift_type=DriftType(data["drift_type"]),
            severity=DriftSeverity(data["severity"]),
            confidence=data["confidence"],
            old_snapshot=None,  # Would reconstruct if needed
            new_snapshot=None,  # Would reconstruct if needed
            changes=data["changes"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
        )


# Global drift engine instance
_drift_engine: MemoryDriftEngine | None = None


async def get_drift_engine() -> MemoryDriftEngine:
    """Get the global drift engine instance"""
    global _drift_engine
    if _drift_engine is None:
        _drift_engine = MemoryDriftEngine()
        await _drift_engine.initialize()
    return _drift_engine


def reset_drift_engine():
    """Reset the global drift engine instance (useful for testing)"""
    global _drift_engine
    _drift_engine = None
