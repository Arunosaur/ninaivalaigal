#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Integration tests to verify UUID types are used correctly in context API
#

import inspect
from uuid import UUID, uuid4

import pytest


def test_audit_logger_uuid_types():
    """Test that audit logger methods accept UUID types"""
    import inspect
    from uuid import UUID, uuid4

    from server.contexts.audit_logger import ContextSharingAuditLogger, SharingAction

    logger = ContextSharingAuditLogger(None)  # Pool not needed for type checking

    # Check method signatures
    log_share_sig = inspect.signature(logger.log_share)

    # Verify context_id and actor_user_id parameters are UUID
    context_id_param = log_share_sig.parameters["context_id"]
    actor_user_id_param = log_share_sig.parameters["actor_user_id"]

    assert context_id_param.annotation == UUID, "log_share.context_id should be UUID"
    assert actor_user_id_param.annotation == UUID, "log_share.actor_user_id should be UUID"


def test_context_ops_uuid_types():
    """Test that UnifiedContextOps methods accept UUID types"""
    import inspect
    from uuid import UUID

    from server.database.operations.context_ops_unified import UnifiedContextOps

    # Check get_context method signature
    ops = UnifiedContextOps(None)  # Pool not needed for type checking
    get_context_sig = inspect.signature(ops.get_context)

    # Verify parameters are UUID
    context_id_param = get_context_sig.parameters["context_id"]
    user_id_param = get_context_sig.parameters["user_id"]

    assert context_id_param.annotation == UUID, "get_context.context_id should be UUID"
    # user_id is Optional[UUID], so check the annotation
    assert user_id_param.annotation == type(None) or UUID in str(
        user_id_param.annotation
    ), "get_context.user_id should be Optional[UUID]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
