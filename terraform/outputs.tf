output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.applio.dns_name
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.applio.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.applio.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.applio.name
}
