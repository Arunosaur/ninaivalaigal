#!/usr/bin/env python3
"""
CI Self-Heal and Recovery Hooks
Automated recovery system for CI/CD pipeline failures
"""

import os
import sys
import time
import json
import subprocess
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path


class CIRecoverySystem:
    """CI/CD Self-Heal and Recovery System"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.config = self._load_config()
        self.recovery_attempts = 0
        self.max_attempts = int(os.getenv('MAX_RECOVERY_ATTEMPTS', '3'))
        self.backoff_multiplier = float(os.getenv('RECOVERY_BACKOFF_MULTIPLIER', '2.0'))
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('ci_recovery.log')
            ]
        )
        return logging.getLogger('CIRecovery')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load recovery configuration"""
        return {
            'postgres_main': {
                'host': 'localhost',
                'port': 5432,
                'database': 'foundation_test',
                'user': 'postgres',
                'password': os.getenv('POSTGRES_PASSWORD', 'foundation_test_password_123')
            },
            'redis_main': {
                'host': 'localhost',
                'port': 6379,
                'db': 15
            },
            'api_server': {
                'host': 'localhost',
                'port': 13370,
                'health_endpoint': '/health'
            }
        }
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            if service_name == 'postgres_main':
                return self._check_postgres_health(self.config['postgres_main'])
            elif service_name == 'redis_main':
                return self._check_redis_health(self.config['redis_main'])
            elif service_name == 'api_server':
                return self._check_api_health(self.config['api_server'])
            else:
                self.logger.error(f"Unknown service: {service_name}")
                return False
        except Exception as e:
            self.logger.error(f"Health check failed for {service_name}: {e}")
            return False
    
    def _check_postgres_health(self, config: Dict[str, Any]) -> bool:
        """Check PostgreSQL health"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                connect_timeout=10
            )
            cursor = conn.cursor()
            cursor.execute('SELECT 1;')
            cursor.fetchone()
            conn.close()
            return True
        except Exception as e:
            self.logger.debug(f"PostgreSQL health check failed: {e}")
            return False
    
    def _check_redis_health(self, config: Dict[str, Any]) -> bool:
        """Check Redis health"""
        try:
            import redis
            r = redis.Redis(
                host=config['host'],
                port=config['port'],
                db=config['db'],
                socket_connect_timeout=10
            )
            r.ping()
            return True
        except Exception as e:
            self.logger.debug(f"Redis health check failed: {e}")
            return False
    
    def _check_api_health(self, config: Dict[str, Any]) -> bool:
        """Check API server health"""
        try:
            url = f"http://{config['host']}:{config['port']}{config['health_endpoint']}"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"API health check failed: {e}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        self.logger.info(f"Attempting to restart {service_name}...")
        
        try:
            if service_name == 'postgres_main':
                return self._restart_postgres_main()
            elif service_name == 'redis_main':
                return self._restart_redis_main()
            elif service_name == 'api_server':
                return self._restart_api_server()
            else:
                self.logger.error(f"Unknown service for restart: {service_name}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to restart {service_name}: {e}")
            return False
    
    def _restart_postgres_main(self) -> bool:
        """Restart main PostgreSQL service"""
        commands = [
            "docker stop nv-db || true",
            "docker rm nv-db || true",
            f"docker run -d --name nv-db -p 5432:5432 "
            f"-e POSTGRES_PASSWORD={self.config['postgres_main']['password']} "
            f"-e POSTGRES_DB={self.config['postgres_main']['database']} "
            f"postgres:15"
        ]
        
        return self._execute_restart_commands(commands, 'postgres_main')
    
    def _restart_redis_main(self) -> bool:
        """Restart main Redis service"""
        commands = [
            "docker stop nv-redis || true",
            "docker rm nv-redis || true",
            "docker run -d --name nv-redis -p 6379:6379 redis:7-alpine"
        ]
        
        return self._execute_restart_commands(commands, 'redis_main')
    
    
    def _restart_api_server(self) -> bool:
        """Restart API server"""
        # For CI environment, we'll simulate API server restart
        # In production, this would restart the actual API server
        self.logger.info("API server restart simulated for CI environment")
        return True
    
    def _execute_restart_commands(self, commands: List[str], service_name: str) -> bool:
        """Execute restart commands with error handling"""
        for cmd in commands:
            self.logger.info(f"Executing: {cmd}")
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Command failed: {cmd}")
                    self.logger.error(f"Error output: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.logger.error(f"Command timed out: {cmd}")
                return False
            except Exception as e:
                self.logger.error(f"Command execution failed: {cmd}, error: {e}")
                return False
        
        # Wait for service to stabilize
        self.logger.info(f"Waiting for {service_name} to stabilize...")
        time.sleep(30)
        
        # Verify service is healthy after restart
        return self.check_service_health(service_name)
    
    def perform_recovery(self, failed_services: List[str]) -> Dict[str, bool]:
        """Perform recovery for failed services"""
        recovery_results = {}
        
        for service in failed_services:
            self.logger.info(f"Starting recovery for {service}")
            
            for attempt in range(1, self.max_attempts + 1):
                self.logger.info(f"Recovery attempt {attempt}/{self.max_attempts} for {service}")
                
                # Restart the service
                restart_success = self.restart_service(service)
                
                if restart_success:
                    # Verify health after restart
                    if self.check_service_health(service):
                        self.logger.info(f"Recovery successful for {service}")
                        recovery_results[service] = True
                        break
                    else:
                        self.logger.warning(f"Service {service} restarted but still unhealthy")
                
                if attempt < self.max_attempts:
                    backoff_time = int(30 * (self.backoff_multiplier ** (attempt - 1)))
                    self.logger.info(f"Waiting {backoff_time}s before next attempt...")
                    time.sleep(backoff_time)
            
            if service not in recovery_results:
                self.logger.error(f"Recovery failed for {service} after {self.max_attempts} attempts")
                recovery_results[service] = False
        
        return recovery_results
    
    def run_foundation_tests(self) -> bool:
        """Run Foundation tests to validate recovery"""
        self.logger.info("Running Foundation tests to validate recovery...")
        
        try:
            # Run a subset of critical Foundation tests
            cmd = [
                "python", "-m", "pytest",
                "tests/foundation/spec_007/",
                "tests/foundation/spec_012/",
                "-v", "--tb=short", "--maxfail=3"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info("Foundation tests passed - recovery validated")
                return True
            else:
                self.logger.error("Foundation tests failed after recovery")
                self.logger.error(f"Test output: {result.stdout}")
                self.logger.error(f"Test errors: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to run Foundation tests: {e}")
            return False
    
    def send_notification(self, message: str, success: bool = True):
        """Send notification about recovery status"""
        # Slack notification
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            try:
                color = "good" if success else "danger"
                emoji = "✅" if success else "❌"
                
                payload = {
                    "text": f"{emoji} CI Recovery System",
                    "attachments": [
                        {
                            "color": color,
                            "fields": [
                                {
                                    "title": "Recovery Status",
                                    "value": message,
                                    "short": False
                                },
                                {
                                    "title": "Timestamp",
                                    "value": datetime.now(timezone.utc).isoformat(),
                                    "short": True
                                }
                            ]
                        }
                    ]
                }
                
                response = requests.post(slack_webhook, json=payload, timeout=10)
                if response.status_code == 200:
                    self.logger.info("Slack notification sent successfully")
                else:
                    self.logger.error(f"Failed to send Slack notification: {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Failed to send Slack notification: {e}")
        
        # HealthChecks.io ping
        healthcheck_uuid = os.getenv('HEALTHCHECK_UUID')
        if healthcheck_uuid:
            try:
                endpoint = "https://hc-ping.com/" + healthcheck_uuid
                if success:
                    endpoint += "/recovery-success"
                else:
                    endpoint += "/fail"
                
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    self.logger.info("HealthChecks.io ping sent successfully")
                else:
                    self.logger.error(f"Failed to send HealthChecks.io ping: {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Failed to send HealthChecks.io ping: {e}")
    
    def generate_recovery_report(self, recovery_results: Dict[str, bool], 
                               foundation_tests_passed: bool) -> str:
        """Generate recovery report"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        report = f"""# CI Recovery Report

**Timestamp**: {timestamp}
**Recovery System**: CI Self-Heal v1.0

## Recovery Results

| Service | Status | Result |
|---------|--------|--------|
"""
        
        for service, success in recovery_results.items():
            status = "✅ Success" if success else "❌ Failed"
            result = "Recovered" if success else "Manual intervention required"
            report += f"| {service} | {status} | {result} |\n"
        
        report += f"""
## Validation

- **Foundation Tests**: {'✅ Passed' if foundation_tests_passed else '❌ Failed'}

## Summary

- **Total Services**: {len(recovery_results)}
- **Successful Recoveries**: {sum(recovery_results.values())}
- **Failed Recoveries**: {len(recovery_results) - sum(recovery_results.values())}
- **Overall Success**: {'✅ Yes' if all(recovery_results.values()) and foundation_tests_passed else '❌ No'}

## Next Steps

"""
        
        if all(recovery_results.values()) and foundation_tests_passed:
            report += "- ✅ All services recovered successfully\n- ✅ Foundation tests validated recovery\n- 🎉 System is operational"
        else:
            report += "- ❌ Manual intervention required\n- 🔧 Check service logs for details\n- 📞 Contact system administrator"
        
        return report


def main():
    """Main recovery function"""
    recovery_system = CIRecoverySystem()
    
    # Check which services need recovery
    services_to_check = [
        'postgres_main',
        'redis_main', 
        'api_server'
    ]
    
    failed_services = []
    
    recovery_system.logger.info("Starting CI recovery system...")
    
    # Check service health
    for service in services_to_check:
        if not recovery_system.check_service_health(service):
            failed_services.append(service)
            recovery_system.logger.warning(f"Service {service} is unhealthy")
        else:
            recovery_system.logger.info(f"Service {service} is healthy")
    
    if not failed_services:
        recovery_system.logger.info("All services are healthy - no recovery needed")
        recovery_system.send_notification("All services healthy - no recovery needed", True)
        return 0
    
    # Perform recovery
    recovery_system.logger.info(f"Starting recovery for {len(failed_services)} services: {failed_services}")
    recovery_results = recovery_system.perform_recovery(failed_services)
    
    # Run Foundation tests to validate recovery
    foundation_tests_passed = recovery_system.run_foundation_tests()
    
    # Generate report
    report = recovery_system.generate_recovery_report(recovery_results, foundation_tests_passed)
    
    # Save report
    with open('ci_recovery_report.md', 'w') as f:
        f.write(report)
    
    recovery_system.logger.info("Recovery report generated: ci_recovery_report.md")
    
    # Send notification
    overall_success = all(recovery_results.values()) and foundation_tests_passed
    
    if overall_success:
        message = f"Recovery successful for all {len(failed_services)} services. Foundation tests passed."
        recovery_system.send_notification(message, True)
        recovery_system.logger.info("CI recovery completed successfully")
        return 0
    else:
        failed_count = len(recovery_results) - sum(recovery_results.values())
        message = f"Recovery failed for {failed_count} services. Manual intervention required."
        recovery_system.send_notification(message, False)
        recovery_system.logger.error("CI recovery failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
