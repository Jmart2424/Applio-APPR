provider "aws" {
  region = "us-west-2"
}

# ECR Repository for Docker images
resource "aws_ecr_repository" "applio" {
  name = "applio-tts-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "applio" {
  name = "applio-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "applio" {
  family                   = "applio-task"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = 4096  # 4 vCPU
  memory                  = 16384 # 16GB RAM
  execution_role_arn      = aws_iam_role.ecs_execution_role.arn
  task_role_arn          = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "applio"
      image = "${aws_ecr_repository.applio.repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "CUDA_VISIBLE_DEVICES"
          value = "0"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/applio"
          "awslogs-region"        = "us-west-2"
          "awslogs-stream-prefix" = "applio"
        }
      }

      mountPoints = [
        {
          sourceVolume  = "models"
          containerPath = "/app/rvc/models"
          readOnly     = true
        },
        {
          sourceVolume  = "audio-cache"
          containerPath = "/app/assets/audios"
          readOnly     = false
        }
      ]
    }
  ])

  volume {
    name = "models"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.models.id
      root_directory = "/"
    }
  }

  volume {
    name = "audio-cache"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.audio_cache.id
      root_directory = "/"
    }
  }
}

# ECS Service
resource "aws_ecs_service" "applio" {
  name            = "applio-service"
  cluster         = aws_ecs_cluster.applio.id
  task_definition = aws_ecs_task_definition.applio.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.applio.arn
    container_name   = "applio"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }
}

# Auto Scaling
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.applio.name}/${aws_ecs_service.applio.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based Auto Scaling
resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

# Request Count-based Auto Scaling
resource "aws_appautoscaling_policy" "requests" {
  name               = "request-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
    }
    target_value = 1000.0  # Scale at ~1000 requests per target per minute
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}
