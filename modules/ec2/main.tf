resource "aws_instance" "web" {
  ami                         = var.ami_id
  instance_type               = "t2.micro"
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = true
  user_data                   = file("${path.module}/user_data.sh")

  tags = {
    Name        = "${var.project_name}-web-server"
    Environment = var.environment
  }
}

# Register instance with target group
resource "aws_lb_target_group_attachment" "web" {
  target_group_arn = var.target_group_arn
  target_id        = aws_instance.web.id
  port             = 80
}