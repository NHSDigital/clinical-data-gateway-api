output "url" {
  description = "URL of the preview environment"
  value       = "https://${local.effective_host_name}"
}

# output "service_arn" {
#   description = "ARN of the ECS service for this preview environment"
#   value       = aws_ecs_service.branch.arn
# }

output "target_group_arn" {
  description = "ARN of the ALB target group for this preview environment"
  value       = aws_lb_target_group.branch.arn
}
