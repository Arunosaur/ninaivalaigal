# Spec 010: Observability & Telemetry System

## Overview
Implement comprehensive observability and telemetry system with RED metrics, OpenTelemetry tracing, and intelligent sampling to provide operational visibility while controlling costs and performance impact.

## Objectives
- Implement RED metrics (Rate, Errors, Duration) for all endpoints
- Add OpenTelemetry distributed tracing with sampling
- Create alerting on permission denials and security events
- Build performance monitoring with RBAC context awareness
- Establish cost-effective telemetry with intelligent sampling
- Provide operational dashboards for system health

## Architecture

### Observability Components
```
server/observability/
├── __init__.py
├── metrics/
│   ├── __init__.py
│   ├── red_metrics.py       # Rate, Errors, Duration metrics
│   ├── rbac_metrics.py      # RBAC-specific metrics
│   └── custom_metrics.py    # Business logic metrics
├── tracing/
│   ├── __init__.py
│   ├── otel_config.py       # OpenTelemetry configuration
│   ├── sampling.py          # Intelligent sampling strategies
│   └── span_processors.py   # Custom span processing
├── alerting/
│   ├── __init__.py
│   ├── security_alerts.py   # Security event alerting
│   ├── performance_alerts.py # Performance threshold alerts
│   └── rbac_alerts.py       # RBAC denial alerts
└── dashboards/
    ├── __init__.py
    ├── grafana_config.py    # Grafana dashboard configs
    └── prometheus_config.py # Prometheus configuration
```

## Technical Specifications

### 1. RED Metrics Implementation

#### Core Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps
import time

class REDMetrics:
    """Rate, Errors, Duration metrics collector"""
    
    def __init__(self):
        # Rate metrics
        self.request_count = Counter(
            'ninaivalaigal_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status_code', 'user_role', 'organization']
        )
        
        # Error metrics
        self.error_count = Counter(
            'ninaivalaigal_errors_total',
            'Total number of errors',
            ['method', 'endpoint', 'error_type', 'user_role']
        )
        
        # Duration metrics
        self.request_duration = Histogram(
            'ninaivalaigal_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint', 'user_role'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # RBAC-specific metrics
        self.rbac_checks = Counter(
            'ninaivalaigal_rbac_checks_total',
            'Total RBAC permission checks',
            ['resource', 'action', 'decision', 'role', 'sensitivity_tier']
        )
        
        self.active_users = Gauge(
            'ninaivalaigal_active_users',
            'Number of active users',
            ['organization', 'role']
        )
        
        # Redaction metrics
        self.redaction_events = Counter(
            'ninaivalaigal_redactions_total',
            'Total redaction events',
            ['redaction_type', 'sensitivity_tier', 'pattern_matched']
        )

    def record_request(self, method: str, endpoint: str, status_code: int, 
                      duration: float, rbac_context: RBACContext = None):
        """Record request metrics with RBAC context"""
        labels = {
            'method': method,
            'endpoint': endpoint,
            'status_code': str(status_code),
            'user_role': rbac_context.user_role.value if rbac_context else 'anonymous',
            'organization': str(rbac_context.organization_id) if rbac_context else 'none'
        }
        
        self.request_count.labels(**labels).inc()
        self.request_duration.labels(
            method=method, 
            endpoint=endpoint, 
            user_role=labels['user_role']
        ).observe(duration)
        
        if status_code >= 400:
            self.error_count.labels(
                method=method,
                endpoint=endpoint,
                error_type=self._get_error_type(status_code),
                user_role=labels['user_role']
            ).inc()

def metrics_middleware():
    """FastAPI middleware for automatic metrics collection"""
    async def middleware(request: Request, call_next):
        start_time = time.time()
        
        # Extract RBAC context if available
        rbac_context = getattr(request.state, 'rbac_context', None)
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            red_metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration,
                rbac_context=rbac_context
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            red_metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration,
                rbac_context=rbac_context
            )
            raise
    
    return middleware
```

### 2. OpenTelemetry Tracing with Intelligent Sampling

#### Tracing Configuration
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

class IntelligentSampler:
    """Cost-effective sampling strategy for high-volume endpoints"""
    
    def __init__(self):
        self.endpoint_sample_rates = {
            '/health': 0.01,        # 1% sampling for health checks
            '/metrics': 0.01,       # 1% sampling for metrics
            '/memory': 0.1,         # 10% sampling for memory operations
            '/contexts': 0.2,       # 20% sampling for context operations
            '/auth/': 1.0,          # 100% sampling for auth (security critical)
            '/rbac/': 1.0,          # 100% sampling for RBAC (security critical)
            '/admin/': 1.0,         # 100% sampling for admin operations
        }
        
        self.error_boost_factor = 10.0  # Increase sampling for errors
        self.high_latency_threshold = 2.0  # Always sample requests > 2s
    
    def should_sample(self, span_context, trace_id, name, kind, attributes, links):
        """Intelligent sampling decision based on endpoint and context"""
        
        # Always sample errors and high-latency requests
        if attributes.get('http.status_code', 0) >= 400:
            return True
        
        if attributes.get('http.request.duration', 0) > self.high_latency_threshold:
            return True
        
        # Sample based on endpoint
        endpoint = attributes.get('http.route', attributes.get('http.target', ''))
        
        for pattern, rate in self.endpoint_sample_rates.items():
            if endpoint.startswith(pattern):
                return random.random() < rate
        
        # Default sampling rate
        return random.random() < 0.05  # 5% default

class ObservabilityConfig:
    """OpenTelemetry configuration with intelligent sampling"""
    
    def __init__(self):
        self.tracer_provider = TracerProvider(
            sampler=IntelligentSampler()
        )
        trace.set_tracer_provider(self.tracer_provider)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv('JAEGER_AGENT_HOST', 'localhost'),
            agent_port=int(os.getenv('JAEGER_AGENT_PORT', '6831')),
        )
        
        span_processor = BatchSpanProcessor(jaeger_exporter)
        self.tracer_provider.add_span_processor(span_processor)
        
    def instrument_app(self, app):
        """Instrument FastAPI application"""
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument()
        
        return app

# Enhanced tracing decorator
def trace_rbac_operation(operation_name: str):
    """Decorator to trace RBAC operations with context"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(f"rbac.{operation_name}") as span:
                # Add RBAC context to span
                if 'rbac_context' in kwargs:
                    rbac_context = kwargs['rbac_context']
                    span.set_attributes({
                        'rbac.user_id': rbac_context.user_id,
                        'rbac.user_role': rbac_context.user_role.value,
                        'rbac.organization_id': rbac_context.organization_id,
                        'rbac.scopes': ','.join(rbac_context.scopes.keys())
                    })
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute('rbac.decision', 'allowed')
                    return result
                except PermissionDenied as e:
                    span.set_attribute('rbac.decision', 'denied')
                    span.set_attribute('rbac.denial_reason', str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator
```

### 3. Security & RBAC Alerting

#### Security Event Alerting
```python
class SecurityAlertManager:
    """Manage security-related alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            'failed_logins_per_minute': 10,
            'permission_denials_per_minute': 50,
            'high_entropy_detections_per_hour': 100,
            'cross_org_attempts_per_hour': 5,
            'admin_actions_per_hour': 20,
        }
        
        self.notification_channels = [
            SlackNotifier(webhook_url=os.getenv('SLACK_SECURITY_WEBHOOK')),
            EmailNotifier(smtp_config=get_smtp_config()),
            PagerDutyNotifier(api_key=os.getenv('PAGERDUTY_API_KEY'))
        ]
    
    async def check_security_thresholds(self):
        """Check security metrics against thresholds"""
        current_time = datetime.utcnow()
        
        # Check failed login attempts
        failed_logins = await self._count_failed_logins_last_minute()
        if failed_logins > self.alert_thresholds['failed_logins_per_minute']:
            await self._send_alert(
                severity='HIGH',
                title='High Failed Login Rate',
                message=f'{failed_logins} failed logins in the last minute',
                metrics={'failed_logins': failed_logins}
            )
        
        # Check permission denials
        permission_denials = await self._count_permission_denials_last_minute()
        if permission_denials > self.alert_thresholds['permission_denials_per_minute']:
            await self._send_alert(
                severity='MEDIUM',
                title='High Permission Denial Rate',
                message=f'{permission_denials} permission denials in the last minute',
                metrics={'permission_denials': permission_denials}
            )
        
        # Check cross-org access attempts
        cross_org_attempts = await self._count_cross_org_attempts_last_hour()
        if cross_org_attempts > self.alert_thresholds['cross_org_attempts_per_hour']:
            await self._send_alert(
                severity='CRITICAL',
                title='Cross-Organization Access Attempts',
                message=f'{cross_org_attempts} cross-org access attempts in the last hour',
                metrics={'cross_org_attempts': cross_org_attempts}
            )

class RBACMetricsCollector:
    """Collect RBAC-specific metrics for monitoring"""
    
    def record_permission_check(self, rbac_context: RBACContext, 
                               resource: Resource, action: Action,
                               decision: bool, sensitivity_tier: ContextSensitivity = None):
        """Record RBAC permission check metrics"""
        red_metrics.rbac_checks.labels(
            resource=resource.value,
            action=action.value,
            decision='allowed' if decision else 'denied',
            role=rbac_context.user_role.value,
            sensitivity_tier=sensitivity_tier.value if sensitivity_tier else 'none'
        ).inc()
        
        # Alert on permission denials
        if not decision:
            asyncio.create_task(self._handle_permission_denial(
                rbac_context, resource, action, sensitivity_tier
            ))
    
    async def _handle_permission_denial(self, rbac_context: RBACContext,
                                       resource: Resource, action: Action,
                                       sensitivity_tier: ContextSensitivity):
        """Handle permission denial for alerting"""
        # Check if this is part of a pattern
        recent_denials = await self._count_recent_denials(rbac_context.user_id)
        
        if recent_denials > 5:  # Threshold for suspicious activity
            await security_alert_manager.send_alert(
                severity='MEDIUM',
                title='Repeated Permission Denials',
                message=f'User {rbac_context.user_id} has {recent_denials} permission denials',
                context={
                    'user_id': rbac_context.user_id,
                    'resource': resource.value,
                    'action': action.value,
                    'sensitivity_tier': sensitivity_tier.value if sensitivity_tier else None
                }
            )
```

### 4. Performance Monitoring

#### Performance Metrics & Alerting
```python
class PerformanceMonitor:
    """Monitor system performance with RBAC context awareness"""
    
    def __init__(self):
        self.performance_thresholds = {
            'api_response_p95': 2.0,      # 95th percentile < 2s
            'api_response_p99': 5.0,      # 99th percentile < 5s
            'database_query_p95': 1.0,    # DB queries < 1s
            'memory_usage_percent': 80,    # Memory usage < 80%
            'cpu_usage_percent': 70,       # CPU usage < 70%
        }
        
        self.rbac_performance_metrics = Histogram(
            'ninaivalaigal_rbac_operation_duration_seconds',
            'RBAC operation duration',
            ['operation_type', 'role', 'resource_count'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
    
    async def monitor_rbac_performance(self):
        """Monitor RBAC operation performance"""
        # Check RBAC check latency
        rbac_p95 = await self._get_rbac_latency_percentile(95)
        if rbac_p95 > 0.1:  # RBAC checks should be < 100ms
            await self._send_performance_alert(
                'RBAC Check Latency High',
                f'RBAC P95 latency: {rbac_p95:.3f}s'
            )
        
        # Check permission cache hit rate
        cache_hit_rate = await self._get_permission_cache_hit_rate()
        if cache_hit_rate < 0.8:  # Should have >80% cache hit rate
            await self._send_performance_alert(
                'Low Permission Cache Hit Rate',
                f'Cache hit rate: {cache_hit_rate:.2%}'
            )

    def record_rbac_operation(self, operation_type: str, role: Role, 
                             resource_count: int, duration: float):
        """Record RBAC operation performance metrics"""
        self.rbac_performance_metrics.labels(
            operation_type=operation_type,
            role=role.value,
            resource_count=str(min(resource_count, 100))  # Cap for cardinality
        ).observe(duration)
```

### 5. Dashboard Configuration

#### Grafana Dashboard Config
```python
GRAFANA_DASHBOARDS = {
    "ninaivalaigal_overview": {
        "title": "Ninaivalaigal System Overview",
        "panels": [
            {
                "title": "Request Rate",
                "type": "graph",
                "targets": [
                    "rate(ninaivalaigal_requests_total[5m])"
                ]
            },
            {
                "title": "Error Rate",
                "type": "graph", 
                "targets": [
                    "rate(ninaivalaigal_errors_total[5m])"
                ]
            },
            {
                "title": "Response Time P95",
                "type": "graph",
                "targets": [
                    "histogram_quantile(0.95, rate(ninaivalaigal_request_duration_seconds_bucket[5m]))"
                ]
            },
            {
                "title": "RBAC Permission Denials",
                "type": "graph",
                "targets": [
                    "rate(ninaivalaigal_rbac_checks_total{decision=\"denied\"}[5m])"
                ]
            }
        ]
    },
    
    "rbac_security_dashboard": {
        "title": "RBAC & Security Monitoring",
        "panels": [
            {
                "title": "Permission Checks by Role",
                "type": "graph",
                "targets": [
                    "sum by (role) (rate(ninaivalaigal_rbac_checks_total[5m]))"
                ]
            },
            {
                "title": "Redaction Events",
                "type": "graph",
                "targets": [
                    "rate(ninaivalaigal_redactions_total[5m])"
                ]
            },
            {
                "title": "Failed Authentication Attempts",
                "type": "stat",
                "targets": [
                    "increase(ninaivalaigal_errors_total{error_type=\"authentication\"}[1h])"
                ]
            }
        ]
    }
}
```

## Database Schema Changes

### Observability Tables
```sql
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE alert_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    context JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_alert_events_timestamp ON alert_events(timestamp);
CREATE INDEX idx_alert_events_severity ON alert_events(severity);
```

## Implementation Plan

### Phase 1: Core Metrics & Tracing (Week 5)
1. Implement RED metrics collection
2. Configure OpenTelemetry with intelligent sampling
3. Add metrics middleware to FastAPI
4. Create basic Prometheus/Grafana setup
5. Test metrics collection and export

### Phase 2: Alerting & Dashboards (Week 6)
1. Implement security alert manager
2. Add RBAC-specific metrics and alerts
3. Create Grafana dashboards
4. Configure notification channels
5. Test alerting workflows

## Configuration

### Environment Variables
```bash
# Observability Configuration
OBSERVABILITY_ENABLED=true
METRICS_PORT=9090
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831

# Sampling Configuration
TRACING_SAMPLE_RATE=0.05
HIGH_VOLUME_SAMPLE_RATE=0.01
ERROR_SAMPLE_BOOST=10.0

# Alerting Configuration
SLACK_SECURITY_WEBHOOK=https://hooks.slack.com/...
PAGERDUTY_API_KEY=your_pagerduty_key
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587

# Performance Thresholds
API_RESPONSE_P95_THRESHOLD=2.0
RBAC_CHECK_LATENCY_THRESHOLD=0.1
PERMISSION_CACHE_HIT_RATE_THRESHOLD=0.8
```

## Testing Strategy

### Metrics Testing
```python
class TestObservabilityMetrics:
    def test_red_metrics_collection(self):
        """Test RED metrics are properly collected"""
        
    def test_rbac_metrics_recording(self):
        """Test RBAC-specific metrics"""
        
    def test_intelligent_sampling(self):
        """Test sampling strategy works correctly"""
        
    def test_alert_threshold_triggers(self):
        """Test alert thresholds trigger correctly"""
```

## Success Criteria

### Operational Requirements
- [ ] RED metrics collected for all endpoints with <1% performance impact
- [ ] OpenTelemetry tracing with intelligent sampling reduces costs by 90%
- [ ] Security alerts trigger within 60 seconds of threshold breach
- [ ] RBAC performance monitoring shows <100ms P95 latency
- [ ] Grafana dashboards provide real-time system visibility

### Cost Control Requirements
- [ ] Telemetry costs stay under $100/month for 10K daily active users
- [ ] Intelligent sampling maintains security visibility while reducing volume
- [ ] Metric cardinality stays under 10K unique series
- [ ] Alert noise reduced to <5 false positives per day
- [ ] Storage costs for metrics/traces stay under 1GB/day

This observability system provides comprehensive visibility into system health, security, and performance while maintaining cost-effectiveness through intelligent sampling and focused alerting.
