terraform {
  required_version = ">= 1.4.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Typically you'll set a different key per branch in CI (e.g. dev/preview/<branch>.tfstate)
  backend "s3" {
    bucket = "cds-cdg-dev-tfstate-900119715266"
    key    = "dev/preview/branch_name.tfstate"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
}

data "aws_region" "current" {}

############################
# 1. Import core outputs
############################

data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = "cds-cdg-dev-tfstate-900119715266"
    key    = "dev/terraform.tfstate"
    region = "eu-west-2"
  }
}

locals {
  # Strip trailing dot if present
  base_domain = trimsuffix(var.base_domain, ".")

  # e.g. "feature-123.dev.endpoints.clinical-data-gateway.national.nhs.uk"
  effective_host_name = "${var.branch_name}.${local.base_domain}"

  branch_safe    = replace(replace(var.branch_name, "/", "-"), " ", "-")
  log_group_name = "/ecs/preview/${local.branch_safe}"

  # Default image tag to branch_name if not provided
  effective_image_tag = length(var.image_tag) > 0 ? var.image_tag : var.branch_name

  # Core outputs
  vpc_id             = data.terraform_remote_state.core.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.core.outputs.private_subnet_ids
  ecs_tasks_sg_id    = data.terraform_remote_state.core.outputs.ecs_tasks_sg_id
  alb_listener_arn   = data.terraform_remote_state.core.outputs.alb_listener_arn
  ecs_cluster_name   = data.terraform_remote_state.core.outputs.ecs_cluster_name
  ecr_repository_url = data.terraform_remote_state.core.outputs.ecr_repository_url
}

############################
# 2. Target group + ALB rule for this branch
############################

resource "aws_lb_target_group" "branch" {
  name        = trim(substr(replace(var.branch_name, ".", "-"), 0, 32), "-")
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = local.vpc_id

  #   health_check {
  #     path                = "/"
  #     matcher             = "200-399"
  #     interval            = 30
  #     timeout             = 5
  #     unhealthy_threshold = 2
  #     healthy_threshold   = 2
  #   }
}

resource "aws_lb_listener_rule" "branch" {
  listener_arn = local.alb_listener_arn
  priority     = var.alb_rule_priority

  condition {
    host_header {
      values = [local.effective_host_name]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.branch.arn
  }
}

############################
# 3. IAM roles for this preview service
############################

resource "aws_iam_role" "execution" {
  name = "ecs-preview-${var.branch_name}-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution_policy" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name = "ecs-preview-${var.branch_name}-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "task_exec_command" {
  name = "ecs-preview-${var.branch_name}-exec-command"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = [
        "ssmmessages:CreateControlChannel",
        "ssmmessages:CreateDataChannel",
        "ssmmessages:OpenControlChannel",
        "ssmmessages:OpenDataChannel",
        "logs:DescribeLogGroups",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      Resource = "*"
    }]
  })
}

resource "aws_cloudwatch_log_group" "branch" {
  name              = local.log_group_name
  retention_in_days = var.log_retention_days
}

############################
# 4. ECS task definition + service
############################

data "aws_ecs_cluster" "cluster" {
  cluster_name = local.ecs_cluster_name
}

resource "aws_ecs_task_definition" "branch" {
  family                   = "preview-${var.branch_name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory

  execution_role_arn = aws_iam_role.execution.arn
  task_role_arn      = aws_iam_role.task.arn

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

  container_definitions = jsonencode([
    {
      name  = "app"
      image = "${local.ecr_repository_url}:${local.effective_image_tag}"
      portMappings = [{
        containerPort = var.container_port
        protocol      = "tcp"
      }]
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group_name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = local.branch_safe
        }
      }
    }
  ])

  depends_on = [aws_cloudwatch_log_group.branch]
}

resource "aws_ecs_service" "branch" {
  name                   = "preview-${var.branch_name}"
  cluster                = data.aws_ecs_cluster.cluster.id
  task_definition        = aws_ecs_task_definition.branch.arn
  desired_count          = var.desired_count
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets         = local.private_subnet_ids
    security_groups = [local.ecs_tasks_sg_id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.branch.arn
    container_name   = "app"
    container_port   = var.container_port
  }

  lifecycle {
    ignore_changes = [task_definition]
  }

  depends_on = [aws_lb_listener_rule.branch]
}


