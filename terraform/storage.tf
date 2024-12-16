# EFS File Systems
resource "aws_efs_file_system" "models" {
  creation_token = "applio-models"
  encrypted      = true

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = {
    Name = "applio-models"
  }
}

resource "aws_efs_file_system" "audio_cache" {
  creation_token = "applio-audio-cache"
  encrypted      = true

  lifecycle_policy {
    transition_to_ia = "AFTER_7_DAYS"
  }

  tags = {
    Name = "applio-audio-cache"
  }
}

# Mount Targets
resource "aws_efs_mount_target" "models_1" {
  file_system_id  = aws_efs_file_system.models.id
  subnet_id       = aws_subnet.private_1.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "models_2" {
  file_system_id  = aws_efs_file_system.models.id
  subnet_id       = aws_subnet.private_2.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "audio_cache_1" {
  file_system_id  = aws_efs_file_system.audio_cache.id
  subnet_id       = aws_subnet.private_1.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "audio_cache_2" {
  file_system_id  = aws_efs_file_system.audio_cache.id
  subnet_id       = aws_subnet.private_2.id
  security_groups = [aws_security_group.efs.id]
}
