"""
Scoped Key Collision Prevention Test

Tests that scoped idempotency keys prevent collisions on same template but different concrete paths.
This addresses the external code review recommendation for collision testing.
"""

from server.security.idempotency.scoped_key_helper import ScopedKeyHelper


def test_same_template_different_paths_no_collision():
    """Test that same template with different concrete paths generates different keys."""

    # Same template, different concrete paths
    path1 = "/api/users/123/posts/456"
    path2 = "/api/users/789/posts/012"

    # Both should extract to same template
    template1 = ScopedKeyHelper.extract_path_template(path1)
    template2 = ScopedKeyHelper.extract_path_template(path2)
    assert template1 == template2 == "/api/users/{id}/posts/{id}"

    # But generate different scoped keys due to different concrete paths
    key1 = ScopedKeyHelper.generate_scoped_key(
        method="POST",
        path=path1,
        subject_user_id="user123",
        organization_id="org1",
        idempotency_key="same_idem_key",
    )

    key2 = ScopedKeyHelper.generate_scoped_key(
        method="POST",
        path=path2,
        subject_user_id="user123",
        organization_id="org1",
        idempotency_key="same_idem_key",
    )

    # Keys should be different despite same template and idempotency key
    assert key1 != key2

    # Verify collision analysis detects no risk
    collision_info = ScopedKeyHelper.get_collision_info(key1, key2)
    assert collision_info["full_collision"] == False


def test_template_normalization_consistency():
    """Test that path template extraction is consistent across similar paths."""

    test_cases = [
        ("/api/users/123", "/api/users/{id}"),
        ("/api/users/123/posts/456", "/api/users/{id}/posts/{id}"),
        ("/api/orgs/abc-123/teams/def-456", "/api/orgs/{id}/teams/{id}"),
        ("/api/items/uuid-1234-5678", "/api/items/{id}"),
        ("/api/nested/abc123/def456/ghi789", "/api/nested/{id}/{id}/{id}"),
    ]

    for concrete_path, expected_template in test_cases:
        actual_template = ScopedKeyHelper.extract_path_template(concrete_path)
        assert (
            actual_template == expected_template
        ), f"Path {concrete_path} -> {actual_template}, expected {expected_template}"


def test_cross_user_same_template_collision_prevention():
    """Test that different users on same template don't collide."""

    template_path = "/api/users/123/posts"

    # Same template, same idempotency key, different users
    key_user1 = ScopedKeyHelper.generate_scoped_key(
        method="POST",
        path=template_path,
        subject_user_id="user_alice",
        organization_id="org1",
        idempotency_key="create_post_123",
    )

    key_user2 = ScopedKeyHelper.generate_scoped_key(
        method="POST",
        path=template_path,
        subject_user_id="user_bob",
        organization_id="org1",
        idempotency_key="create_post_123",
    )

    # Should generate different keys
    assert key_user1 != key_user2

    # Verify no collision risk
    collision_info = ScopedKeyHelper.get_collision_info(key_user1, key_user2)
    assert collision_info["full_collision"] == False


def test_cross_org_same_template_collision_prevention():
    """Test that different orgs on same template don't collide."""

    template_path = "/api/teams/456/members"

    # Same template, same user, same idempotency key, different orgs
    key_org1 = ScopedKeyHelper.generate_scoped_key(
        method="POST",
        path=template_path,
        subject_user_id="user_alice",
        organization_id="org_alpha",
        idempotency_key="add_member_789",
    )

    key_org2 = ScopedKeyHelper.generate_scoped_key(
        method="POST",
        path=template_path,
        subject_user_id="user_alice",
        organization_id="org_beta",
        idempotency_key="add_member_789",
    )

    # Should generate different keys
    assert key_org1 != key_org2

    # Verify no collision risk
    collision_info = ScopedKeyHelper.get_collision_info(key_org1, key_org2)
    assert collision_info["full_collision"] == False


def test_method_differentiation_same_template():
    """Test that different HTTP methods on same template don't collide."""

    template_path = "/api/posts/123"

    key_get = ScopedKeyHelper.generate_scoped_key(
        method="GET",
        path=template_path,
        subject_user_id="user1",
        organization_id="org1",
        idempotency_key="action_123",
    )

    key_post = ScopedKeyHelper.generate_scoped_key(
        method="POST",
        path=template_path,
        subject_user_id="user1",
        organization_id="org1",
        idempotency_key="action_123",
    )

    key_delete = ScopedKeyHelper.generate_scoped_key(
        method="DELETE",
        path=template_path,
        subject_user_id="user1",
        organization_id="org1",
        idempotency_key="action_123",
    )

    # All should be different
    assert len({key_get, key_post, key_delete}) == 3

    # Verify no collisions between any pair
    assert (
        ScopedKeyHelper.get_collision_info(key_get, key_post)["full_collision"] == False
    )
    assert (
        ScopedKeyHelper.get_collision_info(key_post, key_delete)["full_collision"]
        == False
    )
    assert (
        ScopedKeyHelper.get_collision_info(key_get, key_delete)["full_collision"]
        == False
    )


def test_high_collision_scenario_detection():
    """Test collision detection in high-risk scenarios."""

    # Generate many keys with similar patterns
    keys = []
    base_path = "/api/items/{id}/actions"

    for i in range(100):
        key = ScopedKeyHelper.generate_scoped_key(
            method="POST",
            path=f"/api/items/{i}/actions",
            subject_user_id=f"user_{i % 10}",  # Only 10 different users
            organization_id="shared_org",
            idempotency_key=f"action_{i % 5}",  # Only 5 different idempotency keys
        )
        keys.append(key)

    # Should still have no collisions due to path differences
    # Check a few random pairs for collision
    import random

    for _ in range(10):
        key1, key2 = random.sample(keys, 2)
        collision_info = ScopedKeyHelper.get_collision_info(key1, key2)
        assert collision_info["full_collision"] == False


def test_edge_case_path_templates():
    """Test edge cases in path template extraction."""

    edge_cases = [
        # Root paths
        ("/", "/"),
        ("/api", "/api"),
        # Single ID paths
        ("/123", "/{id}"),
        ("/api/123", "/api/{id}"),
        # UUID patterns
        ("/api/users/550e8400-e29b-41d4-a716-446655440000", "/api/users/{uuid}"),
        # Mixed patterns
        ("/api/v1/users/123/posts/abc-def", "/api/{id}/users/{id}/posts/{id}"),
        # Numeric-only segments
        ("/api/2023/01/15/reports/456", "/api/{id}/{id}/{id}/reports/{id}"),
    ]

    for concrete_path, expected in edge_cases:
        template = ScopedKeyHelper.extract_path_template(concrete_path)
        assert (
            template == expected
        ), f"Path {concrete_path} -> {template}, expected {expected}"


def test_collision_analysis_comprehensive():
    """Test comprehensive collision analysis functionality."""

    # Create a mix of keys with potential collision patterns
    keys = [
        # Same user, different paths
        ScopedKeyHelper.generate_scoped_key(
            "POST",
            "/api/users/1",
            subject_user_id="user1",
            organization_id="org1",
            idempotency_key="key1",
        ),
        ScopedKeyHelper.generate_scoped_key(
            "POST",
            "/api/users/2",
            subject_user_id="user1",
            organization_id="org1",
            idempotency_key="key1",
        ),
        # Different users, same path template
        ScopedKeyHelper.generate_scoped_key(
            "POST",
            "/api/posts/123",
            subject_user_id="user1",
            organization_id="org1",
            idempotency_key="key2",
        ),
        ScopedKeyHelper.generate_scoped_key(
            "POST",
            "/api/posts/456",
            subject_user_id="user2",
            organization_id="org1",
            idempotency_key="key2",
        ),
        # Cross-org scenarios
        ScopedKeyHelper.generate_scoped_key(
            "POST",
            "/api/teams/1",
            subject_user_id="user1",
            organization_id="org1",
            idempotency_key="key3",
        ),
        ScopedKeyHelper.generate_scoped_key(
            "POST",
            "/api/teams/1",
            subject_user_id="user1",
            organization_id="org2",
            idempotency_key="key3",
        ),
    ]

    # Should detect no collisions between any pairs
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            collision_info = ScopedKeyHelper.get_collision_info(keys[i], keys[j])
            assert collision_info["full_collision"] == False


if __name__ == "__main__":
    # Run collision prevention tests
    test_functions = [
        test_same_template_different_paths_no_collision,
        test_template_normalization_consistency,
        test_cross_user_same_template_collision_prevention,
        test_cross_org_same_template_collision_prevention,
        test_method_differentiation_same_template,
        test_high_collision_scenario_detection,
        test_edge_case_path_templates,
        test_collision_analysis_comprehensive,
    ]

    print("Running scoped key collision prevention tests...")

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            raise

    print(f"\nAll {len(test_functions)} collision prevention tests passed!")
    print(
        "Scoped idempotency keys successfully prevent collisions on same template with different paths."
    )
