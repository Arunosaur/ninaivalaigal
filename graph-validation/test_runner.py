import yaml
from validators import (
    edge_weight_validator,
    path_validator,
    recommendation_validator,
    similarity_validator,
)


def run_all_tests():
    config = yaml.safe_load(open("test_config.yaml"))

    print("Running Graph Intelligence Test Suite...")
    similarity_validator.run(config)
    path_validator.run(config)
    recommendation_validator.run(config)
    edge_weight_validator.run(config)
    print("✅ All tests complete.")


if __name__ == "__main__":
    run_all_tests()
