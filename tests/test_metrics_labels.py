import pytest
from server.observability.metrics_labels import validate_metric_labels

def test_route_template_only():
    with pytest.raises(ValueError):
        validate_metric_labels({"route":"/memories/123"})
    validate_metric_labels({"route":"/memories/{id}"})

def test_reason_buckets():
    validate_metric_labels({"reason":"engine_error"})
    with pytest.raises(ValueError):
        validate_metric_labels({"reason":"some-dynamic-detail"})
