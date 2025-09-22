terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ECS Cluster
resource "aws_ecs_cluster" "ninaivalaigal" {
  name = "ninaivalaigal-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "ninaivalaigal"
    Environment = var.environment
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "ninaivalaigal_api" {
  family                   = "ninaivalaigal-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn

  container_definitions = jsonencode([
    {
      name  = "ninaivalaigal-api"
      image = "ghcr.io/arunosaur/ninaivalaigal-api:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DATABASE_URL"
          value = var.database_url
        },
        {
          name  = "NINAIVALAIGAL_JWT_SECRET"
          value = var.jwt_secret
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ninaivalaigal.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name        = "ninaivalaigal-api"
    Environment = var.environment
  }
}

# ECS Service
resource "aws_ecs_service" "ninaivalaigal_api" {
  name            = "ninaivalaigal-api"
  cluster         = aws_ecs_cluster.ninaivalaigal.id
  task_definition = aws_ecs_task_definition.ninaivalaigal_api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ninaivalaigal.arn
    container_name   = "ninaivalaigal-api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.ninaivalaigal]

  tags = {
    Name        = "ninaivalaigal-api"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "ninaivalaigal" {
  name               = "ninaivalaigal-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids

  enable_deletion_protection = false

  tags = {
    Name        = "ninaivalaigal-alb"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "ninaivalaigal" {
  name        = "ninaivalaigal-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "ninaivalaigal-tg"
    Environment = var.environment
  }
}

resource "aws_lb_listener" "ninaivalaigal" {
  load_balancer_arn = aws_lb.ninaivalaigal.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ninaivalaigal.arn
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "ninaivalaigal-alb-sg"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ninaivalaigal-alb-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "ninaivalaigal-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ninaivalaigal-ecs-tasks-sg"
    Environment = var.environment
  }
}

# IAM Role for ECS Execution
resource "aws_iam_role" "ecs_execution_role" {
  name = "ninaivalaigal-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "ninaivalaigal-ecs-execution-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ninaivalaigal" {
  name              = "/ecs/ninaivalaigal-api"
  retention_in_days = 7

  tags = {
    Name        = "ninaivalaigal-logs"
    Environment = var.environment
  }
}
