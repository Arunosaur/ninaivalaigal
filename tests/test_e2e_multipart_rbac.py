import pytest


@pytest.mark.parametrize(
    "role,expected",
    [
        ("viewer", 403),
        ("org_editor", 200),
    ],
)
def test_rbac_roles(client, make_jwt, role, expected):
    token = make_jwt(claims={"roles": [role]})
    resp = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", b"data")},
    )
    assert resp.status_code == expected
