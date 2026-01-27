output "url" {
  description = "URL of the preview environment"
  value       = "https://${local.effective_host_name}"
}

output "target_group_arn" {
  description = "ARN of the ALB target group for this preview environment"
  value       = aws_lb_target_group.branch.arn
}

output "ecs_service_name" {
  description = "Name of the ECS service for this preview environment"
  value       = aws_ecs_service.branch.name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster for this preview environment"
  value       = local.ecs_cluster_name
}
