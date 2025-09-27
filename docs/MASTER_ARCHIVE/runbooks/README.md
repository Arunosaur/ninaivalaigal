# 📖 Operational Runbooks

## 🎯 Runbook Overview

Operational procedures for monitoring, troubleshooting, and maintaining the ninaivalaigal platform in production.

## 🚨 Emergency Procedures

### System Down
1. **Check Health Endpoints**: `/health`, `/health/detailed`
2. **Verify Infrastructure**: Database, Redis, API containers
3. **Check Logs**: Application and container logs
4. **Escalate**: If not resolved in 15 minutes

### Performance Degradation
1. **Check Metrics**: Response times, error rates
2. **Redis Status**: Cache hit rates, memory usage
3. **Database**: Connection pool, query performance
4. **Scale**: Add resources if needed

## 📊 Monitoring Checklist

### Daily Checks
- [ ] All health endpoints responding
- [ ] Error rates < 1%
- [ ] Response times within SLO
- [ ] Redis cache hit rate > 90%
- [ ] Database connection pool healthy

### Weekly Checks
- [ ] Security scan results
- [ ] Backup verification
- [ ] Performance trend analysis
- [ ] Capacity planning review

## 🔧 Common Issues

### Database Connection Issues
```bash
# Check database status
./scripts/nv-db-status.sh

# Check connection pool
container exec nv-pgbouncer pgbouncer -v

# Reset connections
make db-reset-connections
```

### Redis Cache Issues
```bash
# Check Redis status
./scripts/nv-redis-status.sh

# Clear cache if needed
container exec nv-redis redis-cli FLUSHALL

# Monitor memory usage
container exec nv-redis redis-cli INFO memory
```

### API Performance Issues
```bash
# Check API health
curl http://localhost:8000/health/detailed

# View API logs
container logs nv-api --tail 100

# Restart API if needed
./scripts/nv-api-restart.sh
```

## 📈 Performance Monitoring

### Key Metrics
- **API Response Time**: P95 < 200ms
- **Memory Retrieval**: P95 < 1ms (Redis)
- **Database Queries**: P95 < 100ms
- **Error Rate**: < 1%
- **Uptime**: > 99.9%

### Alerting Thresholds
- **Critical**: P95 > 500ms, Error rate > 5%
- **Warning**: P95 > 300ms, Error rate > 2%
- **Info**: Cache hit rate < 85%

## 🔒 Security Monitoring

### Security Events to Monitor
- Failed authentication attempts
- Privilege escalation attempts
- Unusual access patterns
- Rate limit violations
- Security header violations

### Security Response
1. **Identify**: Log analysis and pattern recognition
2. **Contain**: Block suspicious IPs/users
3. **Investigate**: Full security audit
4. **Remediate**: Fix vulnerabilities
5. **Document**: Update security procedures

## 📚 Related Documentation

- [Security Overview](../security/README.md)
- [Performance Testing](../testing/performance.md)
- [Deployment Guides](../deployment/README.md)
- [Architecture Overview](../architecture/README.md)

---

**SLO**: 99.9% uptime | **Response**: 15min RTO | **Monitoring**: 24/7
