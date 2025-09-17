import pytest

def test_roles_string_normalization_allows_list_semantics():
    # Upstream sends roles as comma-separated string; your normalizer should coerce to list safely.
    # Pseudo-interface: normalize_claims({"roles": "editor,admin"}) -> {"roles": ["editor","admin"]}
    from typing import List

    def normalize_roles(v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        if isinstance(v, list):
            return v
        return []

    assert normalize_roles("editor,admin") == ["editor","admin"]
    assert normalize_roles(["viewer"]) == ["viewer"]
