output "ecs_cluster_id" {
  value       = aws_ecs_cluster.fractal_cluster.id
  description = "The ID of the ECS cluster"
}
