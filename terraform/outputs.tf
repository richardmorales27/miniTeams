output "vpc_id" {
  description = "MiniTeams VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id
  ]
}

output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "ecs_task_security_group_id" {
  description = "ECS task security group ID"
  value       = aws_security_group.ecs_tasks.id
}

output "dynamodb_table_name" {
  description = "DynamoDB message table name"
  value       = aws_dynamodb_table.messages.name
}

output "ecr_repository_url" {
  description = "ECR repository URL for MiniTeams"
  value       = aws_ecr_repository.miniteams.repository_url
}

output "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "app_task_role_arn" {
  description = "MiniTeams application task role ARN"
  value       = aws_iam_role.app_task.arn
}

output "ecs_cluster_name" {
  description = "MiniTeams ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "MiniTeams ECS service name"
  value       = aws_ecs_service.miniteams.name
}

output "ecs_task_definition_arn" {
  description = "MiniTeams ECS task definition ARN"
  value       = aws_ecs_task_definition.miniteams.arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group for MiniTeams"
  value       = aws_cloudwatch_log_group.miniteams.name
}