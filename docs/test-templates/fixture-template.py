# Fixture Template

import pytest

@pytest.fixture
def example_fixture():
    """Example test fixture."""
    # Setup: Create and return a resource
    print("\nSetting up the fixture...")
    yield "example_resource"
    # Teardown: Clean up the resource
    print("\nTearing down the fixture...")

def test_using_fixture(example_fixture):
    """Example test that uses the fixture."""
    print(f"\nTest is using the fixture: {example_fixture}")
    assert example_fixture == "example_resource"
