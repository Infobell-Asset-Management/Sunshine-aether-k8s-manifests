from prometheus_client import CollectorRegistry, Counter


metrics_registry = CollectorRegistry()

# Example metric to ensure registry is non-empty and visible
requests_total = Counter(
    "processor_requests_total",
    "Total HTTP requests processed",
    registry=metrics_registry,
)


