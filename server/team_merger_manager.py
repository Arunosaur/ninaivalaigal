"""
Team Merger Management System for Ninaivalaigal
Handles team consolidation, splits, dissolution, and restructuring
"""

import json
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MergerType(Enum):
    CONSOLIDATION = "consolidation"
    SPLIT = "split"
    DISSOLUTION = "dissolution"
    RENAME = "rename"


class MergerStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationType(Enum):
    MOVE = "move"
    COPY = "copy"
    ARCHIVE = "archive"
    DELETE = "delete"


class TeamMergerManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def initiate_team_merger(self, org_id: str, merger_config: dict) -> int:
        """
        Initiate team merger process

        Args:
            org_id: Organization ID
            merger_config: Merger configuration dictionary

        Returns:
            merger_id: ID of created merger
        """
        # Validate merger configuration
        self._validate_merger_config(merger_config)

        merger = {
            "organization_id": org_id,
            "merger_type": merger_config["type"],
            "source_teams": json.dumps(merger_config["source_teams"]),
            "target_teams": json.dumps(merger_config["target_teams"]),
            "merger_date": datetime.now(),
            "initiated_by": merger_config["initiated_by"],
            "status": MergerStatus.PENDING.value,
            "memory_migration_policy": json.dumps(
                merger_config.get("memory_policy", {})
            ),
        }

        merger_id = self.db.create_team_merger(merger)

        # Log merger initiation
        self._log_merger_action(
            merger_id, "merger_initiated", merger_config["initiated_by"]
        )

        # Validate merger prerequisites
        self._validate_merger_prerequisites(merger_id, merger_config)

        logger.info(f"Team merger {merger_id} initiated for organization {org_id}")
        return merger_id

    def execute_team_consolidation(self, merger_id: int) -> dict:
        """
        Execute team consolidation merger

        Args:
            merger_id: ID of merger to execute

        Returns:
            Execution result dictionary
        """
        merger = self.db.get_team_merger(merger_id)

        if merger["merger_type"] != MergerType.CONSOLIDATION.value:
            raise ValueError("Invalid merger type for consolidation")

        # Update merger status
        self.db.update_merger_status(merger_id, MergerStatus.IN_PROGRESS.value)

        try:
            source_teams = json.loads(merger["source_teams"])
            target_teams = json.loads(merger["target_teams"])

            # Step 1: Create or get target team
            target_team = self._create_or_get_target_team(merger, target_teams[0])

            # Step 2: Migrate team members
            migrated_members = self._migrate_team_members(
                merger_id, source_teams, target_team["id"]
            )

            # Step 3: Migrate memories and contexts
            migrated_contexts = self._migrate_team_memories(
                merger_id, source_teams, target_team["id"]
            )

            # Step 4: Update access permissions
            self._update_access_permissions(merger_id, target_team["id"])

            # Step 5: Archive source teams
            self._archive_source_teams(merger_id, source_teams)

            # Complete merger
            self.db.update_merger_status(merger_id, MergerStatus.COMPLETED.value)

            result = {
                "status": "completed",
                "merger_id": merger_id,
                "target_team": target_team,
                "migrated_contexts": migrated_contexts,
                "migrated_members": migrated_members,
                "completion_date": datetime.now().isoformat(),
            }

            self._log_merger_action(
                merger_id, "consolidation_completed", merger["initiated_by"], result
            )
            logger.info(f"Team consolidation {merger_id} completed successfully")

            return result

        except Exception as e:
            self.db.update_merger_status(merger_id, MergerStatus.FAILED.value)
            self._log_merger_error(merger_id, str(e))
            logger.error(f"Team consolidation {merger_id} failed: {str(e)}")
            raise

    def execute_team_split(self, merger_id: int) -> dict:
        """
        Execute team split merger

        Args:
            merger_id: ID of merger to execute

        Returns:
            Execution result dictionary
        """
        merger = self.db.get_team_merger(merger_id)

        if merger["merger_type"] != MergerType.SPLIT.value:
            raise ValueError("Invalid merger type for split")

        self.db.update_merger_status(merger_id, MergerStatus.IN_PROGRESS.value)

        try:
            source_teams = json.loads(merger["source_teams"])
            target_teams = json.loads(merger["target_teams"])

            # Step 1: Create new target teams
            created_teams = self._create_target_teams(merger, target_teams)

            # Step 2: Distribute members based on specialization
            member_distribution = self._distribute_team_members(
                merger_id, source_teams[0], created_teams
            )

            # Step 3: Distribute memories based on relevance
            memory_distribution = self._distribute_team_memories(
                merger_id, source_teams[0], created_teams
            )

            # Step 4: Set up cross-team collaboration
            collaboration_setup = self._setup_cross_team_collaboration(
                merger_id, created_teams
            )

            # Step 5: Archive source team
            self._archive_source_teams(merger_id, source_teams)

            self.db.update_merger_status(merger_id, MergerStatus.COMPLETED.value)

            result = {
                "status": "completed",
                "merger_id": merger_id,
                "target_teams": created_teams,
                "member_distribution": member_distribution,
                "memory_distribution": memory_distribution,
                "collaboration_setup": collaboration_setup,
                "completion_date": datetime.now().isoformat(),
            }

            self._log_merger_action(
                merger_id, "split_completed", merger["initiated_by"], result
            )
            logger.info(f"Team split {merger_id} completed successfully")

            return result

        except Exception as e:
            self.db.update_merger_status(merger_id, MergerStatus.FAILED.value)
            self._log_merger_error(merger_id, str(e))
            logger.error(f"Team split {merger_id} failed: {str(e)}")
            raise

    def execute_team_dissolution(self, merger_id: int) -> dict:
        """
        Execute team dissolution

        Args:
            merger_id: ID of merger to execute

        Returns:
            Execution result dictionary
        """
        merger = self.db.get_team_merger(merger_id)

        if merger["merger_type"] != MergerType.DISSOLUTION.value:
            raise ValueError("Invalid merger type for dissolution")

        self.db.update_merger_status(merger_id, MergerStatus.IN_PROGRESS.value)

        try:
            source_teams = json.loads(merger["source_teams"])
            target_teams = json.loads(merger["target_teams"])

            # Step 1: Archive team memories
            archived_contexts = self._archive_team_memories(merger_id, source_teams)

            # Step 2: Redistribute members to target teams
            redistributed_members = self._redistribute_team_members(
                merger_id, source_teams, target_teams
            )

            # Step 3: Set up historical access
            historical_access = self._setup_historical_access(merger_id, source_teams)

            # Step 4: Schedule cleanup
            cleanup_schedule = self._schedule_team_cleanup(merger_id, source_teams)

            self.db.update_merger_status(merger_id, MergerStatus.COMPLETED.value)

            result = {
                "status": "completed",
                "merger_id": merger_id,
                "archived_contexts": archived_contexts,
                "redistributed_members": redistributed_members,
                "historical_access": historical_access,
                "cleanup_schedule": cleanup_schedule,
                "completion_date": datetime.now().isoformat(),
            }

            self._log_merger_action(
                merger_id, "dissolution_completed", merger["initiated_by"], result
            )
            logger.info(f"Team dissolution {merger_id} completed successfully")

            return result

        except Exception as e:
            self.db.update_merger_status(merger_id, MergerStatus.FAILED.value)
            self._log_merger_error(merger_id, str(e))
            logger.error(f"Team dissolution {merger_id} failed: {str(e)}")
            raise

    def rollback_merger(self, merger_id: int, rollback_reason: str) -> dict:
        """
        Rollback completed team merger

        Args:
            merger_id: ID of merger to rollback
            rollback_reason: Reason for rollback

        Returns:
            Rollback result dictionary
        """
        merger = self.db.get_team_merger(merger_id)

        if merger["status"] != MergerStatus.COMPLETED.value:
            raise ValueError("Can only rollback completed mergers")

        try:
            # Get merger audit trail for rollback
            audit_trail = self.db.get_merger_audit_trail(merger_id)

            # Restore team memberships
            restored_memberships = self._restore_team_memberships(
                merger_id, audit_trail
            )

            # Restore memory locations
            restored_memories = self._restore_memory_locations(merger_id, audit_trail)

            # Restore team structures
            restored_teams = self._restore_team_structures(merger_id, audit_trail)

            # Update merger status
            self.db.update_merger_status(merger_id, MergerStatus.ROLLED_BACK.value)

            result = {
                "status": "rolled_back",
                "merger_id": merger_id,
                "rollback_reason": rollback_reason,
                "restored_memberships": restored_memberships,
                "restored_memories": restored_memories,
                "restored_teams": restored_teams,
                "rollback_date": datetime.now().isoformat(),
            }

            self._log_merger_action(merger_id, "merger_rolled_back", "system", result)
            logger.info(f"Team merger {merger_id} rolled back successfully")

            return result

        except Exception as e:
            logger.error(f"Failed to rollback merger {merger_id}: {str(e)}")
            raise

    def _validate_merger_config(self, config: dict):
        """Validate merger configuration"""
        required_fields = ["type", "source_teams", "target_teams", "initiated_by"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        if config["type"] not in [t.value for t in MergerType]:
            raise ValueError(f"Invalid merger type: {config['type']}")

    def _validate_merger_prerequisites(self, merger_id: int, config: dict):
        """Validate merger prerequisites"""
        # Check user permissions
        if not self._has_merger_permission(config["initiated_by"]):
            raise PermissionError("Insufficient permissions for team merger")

        # Check team existence
        for team_id in config["source_teams"]:
            if not self.db.team_exists(team_id):
                raise ValueError(f"Source team does not exist: {team_id}")

    def _migrate_team_memories(
        self, merger_id: int, source_teams: list[str], target_team_id: str
    ) -> list[dict]:
        """Migrate memories from source teams to target team"""
        migrated_contexts = []

        for source_team_id in source_teams:
            contexts = self.db.get_team_contexts(source_team_id)

            for context in contexts:
                # Move context to target team
                self.db.update_context_team(context["id"], target_team_id)

                # Update context metadata
                self.db.update_context_metadata(
                    context["id"],
                    {
                        "original_team_id": source_team_id,
                        "team_merger_id": merger_id,
                        "migration_date": datetime.now().isoformat(),
                    },
                )

                # Log migration
                self.db.log_memory_migration(
                    merger_id, context["id"], target_team_id, MigrationType.MOVE.value
                )

                migrated_contexts.append(
                    {
                        "context_id": context["id"],
                        "context_name": context["name"],
                        "source_team": source_team_id,
                        "target_team": target_team_id,
                    }
                )

        return migrated_contexts

    def _distribute_team_memories(
        self, merger_id: int, source_team_id: str, target_teams: list[dict]
    ) -> dict:
        """Distribute memories among target teams based on relevance"""
        contexts = self.db.get_team_contexts(source_team_id)
        distribution = {team["id"]: [] for team in target_teams}

        for context in contexts:
            # Determine most relevant target team
            target_team = self._determine_context_relevance(context, target_teams)

            # Move context to target team
            self.db.update_context_team(context["id"], target_team["id"])

            # Set up cross-team access for related contexts
            related_teams = self._find_related_teams(context, target_teams)
            for related_team in related_teams:
                if related_team["id"] != target_team["id"]:
                    self.db.grant_cross_team_access(
                        context["id"], related_team["id"], "read"
                    )

            distribution[target_team["id"]].append(
                {
                    "context_id": context["id"],
                    "context_name": context["name"],
                    "relevance_score": self._calculate_relevance_score(
                        context, target_team
                    ),
                }
            )

        return distribution

    def _determine_context_relevance(
        self, context: dict, target_teams: list[dict]
    ) -> dict:
        """Determine which target team is most relevant for a context"""
        best_team = target_teams[0]
        best_score = 0

        for team in target_teams:
            score = self._calculate_relevance_score(context, team)
            if score > best_score:
                best_score = score
                best_team = team

        return best_team

    def _calculate_relevance_score(self, context: dict, team: dict) -> float:
        """Calculate relevance score between context and team"""
        # Simple keyword-based relevance scoring
        context_keywords = self._extract_keywords(
            context["name"] + " " + context.get("description", "")
        )
        team_keywords = self._extract_keywords(
            team["name"] + " " + team.get("description", "")
        )

        common_keywords = set(context_keywords) & set(team_keywords)

        if not context_keywords:
            return 0.0

        return len(common_keywords) / len(context_keywords)

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text"""
        # Simple keyword extraction (could be enhanced with NLP)
        import re

        words = re.findall(r"\w+", text.lower())
        # Filter out common words
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        return [word for word in words if word not in stop_words and len(word) > 2]

    def _log_merger_action(
        self, merger_id: int, action: str, user_id: str, details: dict = None
    ):
        """Log merger action to audit trail"""
        audit_entry = {
            "merger_id": merger_id,
            "action": action,
            "performed_by": user_id,
            "timestamp": datetime.now(),
            "details": json.dumps(details) if details else None,
        }

        self.db.log_merger_audit(audit_entry)

    def _log_merger_error(self, merger_id: int, error_message: str):
        """Log merger error"""
        self._log_merger_action(
            merger_id, "error_occurred", "system", {"error": error_message}
        )

    def _has_merger_permission(self, user_id: str) -> bool:
        """Check if user has permission to perform team mergers"""
        # Implementation depends on your permission system
        return self.db.user_has_permission(user_id, "team_management")

    # Additional helper methods would be implemented here...
    def _create_or_get_target_team(self, merger: dict, team_id: str) -> dict:
        """Create or get target team"""
        # Implementation for team creation/retrieval
        pass

    def _migrate_team_members(
        self, merger_id: int, source_teams: list[str], target_team_id: str
    ) -> list[dict]:
        """Migrate team members"""
        # Implementation for member migration
        pass

    def _update_access_permissions(self, merger_id: int, target_team_id: str):
        """Update access permissions after merger"""
        # Implementation for permission updates
        pass

    def _archive_source_teams(self, merger_id: int, source_teams: list[str]):
        """Archive source teams"""
        # Implementation for team archival
        pass


class MemoryMigrationPolicy:
    """Memory migration policies for different merger types"""

    @staticmethod
    def get_consolidation_policy() -> dict:
        return {
            "default_action": MigrationType.MOVE.value,
            "conflict_resolution": "merge",
            "access_inheritance": "union",
            "context_naming": "preserve_with_prefix",
        }

    @staticmethod
    def get_split_policy() -> dict:
        return {
            "distribution_strategy": "relevance_based",
            "cross_team_access": "selective",
            "shared_contexts": ["onboarding", "company-standards"],
            "specialization_mapping": {
                "frontend": ["ui", "react", "css", "design", "javascript"],
                "backend": ["api", "database", "server", "auth", "python"],
                "devops": [
                    "deployment",
                    "ci/cd",
                    "infrastructure",
                    "monitoring",
                    "docker",
                ],
            },
        }

    @staticmethod
    def get_dissolution_policy() -> dict:
        return {
            "member_redistribution": "manual",
            "memory_action": MigrationType.ARCHIVE.value,
            "access_preservation": "historical",
            "cleanup_schedule": "90_days",
        }

    @staticmethod
    def get_rename_policy() -> dict:
        return {
            "memory_action": "update_metadata",
            "preserve_history": True,
            "update_references": True,
        }
