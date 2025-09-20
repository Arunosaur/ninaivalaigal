output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.ninaivalaigal.dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.ninaivalaigal.zone_id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.ninaivalaigal.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.ninaivalaigal_api.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.ninaivalaigal.name
}
