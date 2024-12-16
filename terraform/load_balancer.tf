# Application Load Balancer
resource "aws_lb" "applio" {
  name               = "applio-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = [aws_subnet.public_1.id, aws_subnet.public_2.id]


  enable_deletion_protection = true

  tags = {
    Name = "applio-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "applio" {
  name        = "applio-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher            = "200"
    path               = "/health"
    port               = "traffic-port"
    protocol           = "HTTP"
    timeout            = 5
    unhealthy_threshold = 3
  }
}

# Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.applio.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.applio.arn
  }
}
