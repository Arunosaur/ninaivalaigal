# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Type Definitions for Event Bus
SPEC-100: Event-Driven Architecture
"""

from enum import Enum


class EventType(str, Enum):
    """Standard event types across all services"""

    # User Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

    # Team Events
    TEAM_CREATED = "team.created"
    TEAM_UPDATED = "team.updated"
    TEAM_DELETED = "team.deleted"
    TEAM_MEMBER_ADDED = "team.member_added"
    TEAM_MEMBER_REMOVED = "team.member_removed"

    # Organization Events
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_DELETED = "organization.deleted"

    # Memory Events
    MEMORY_CREATED = "memory.created"
    MEMORY_UPDATED = "memory.updated"
    MEMORY_DELETED = "memory.deleted"
    MEMORY_RECALLED = "memory.recalled"
    MEMORY_FEEDBACK = "memory.feedback"

    # Subscription/Business Events
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    USAGE_RECORDED = "usage.recorded"
    INVOICE_GENERATED = "invoice.generated"
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"

    # System Events
    SYSTEM_HEALTH_CHECK = "system.health_check"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"


class StreamTopic(str, Enum):
    """Redis Streams topics for event routing"""

    USERS = "ninaivalaigal:events:users"
    TEAMS = "ninaivalaigal:events:teams"
    ORGANIZATIONS = "ninaivalaigal:events:organizations"
    MEMORIES = "ninaivalaigal:events:memories"
    SUBSCRIPTIONS = "ninaivalaigal:events:subscriptions"
    SYSTEM = "ninaivalaigal:events:system"


# Event type to topic routing
EVENT_TO_TOPIC = {
    # User events
    EventType.USER_CREATED: StreamTopic.USERS,
    EventType.USER_UPDATED: StreamTopic.USERS,
    EventType.USER_DELETED: StreamTopic.USERS,
    EventType.USER_LOGIN: StreamTopic.USERS,
    EventType.USER_LOGOUT: StreamTopic.USERS,
    # Team events
    EventType.TEAM_CREATED: StreamTopic.TEAMS,
    EventType.TEAM_UPDATED: StreamTopic.TEAMS,
    EventType.TEAM_DELETED: StreamTopic.TEAMS,
    EventType.TEAM_MEMBER_ADDED: StreamTopic.TEAMS,
    EventType.TEAM_MEMBER_REMOVED: StreamTopic.TEAMS,
    # Organization events
    EventType.ORGANIZATION_CREATED: StreamTopic.ORGANIZATIONS,
    EventType.ORGANIZATION_UPDATED: StreamTopic.ORGANIZATIONS,
    EventType.ORGANIZATION_DELETED: StreamTopic.ORGANIZATIONS,
    # Memory events
    EventType.MEMORY_CREATED: StreamTopic.MEMORIES,
    EventType.MEMORY_UPDATED: StreamTopic.MEMORIES,
    EventType.MEMORY_DELETED: StreamTopic.MEMORIES,
    EventType.MEMORY_RECALLED: StreamTopic.MEMORIES,
    EventType.MEMORY_FEEDBACK: StreamTopic.MEMORIES,
    # Subscription/Business events
    EventType.SUBSCRIPTION_CREATED: StreamTopic.SUBSCRIPTIONS,
    EventType.SUBSCRIPTION_UPDATED: StreamTopic.SUBSCRIPTIONS,
    EventType.SUBSCRIPTION_CANCELLED: StreamTopic.SUBSCRIPTIONS,
    EventType.USAGE_RECORDED: StreamTopic.SUBSCRIPTIONS,
    EventType.INVOICE_GENERATED: StreamTopic.SUBSCRIPTIONS,
    EventType.PAYMENT_RECEIVED: StreamTopic.SUBSCRIPTIONS,
    EventType.PAYMENT_FAILED: StreamTopic.SUBSCRIPTIONS,
    # System events
    EventType.SYSTEM_HEALTH_CHECK: StreamTopic.SYSTEM,
    EventType.SYSTEM_ERROR: StreamTopic.SYSTEM,
    EventType.SYSTEM_WARNING: StreamTopic.SYSTEM,
}
