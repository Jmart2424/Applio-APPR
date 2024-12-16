variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "models_bucket" {
  description = "S3 bucket for storing RVC models"
  type        = string
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "applio"
}

variable "container_cpu" {
  description = "Container CPU units"
  type        = number
  default     = 4096
}

variable "container_memory" {
  description = "Container memory in MiB"
  type        = number
  default     = 16384
}

variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}
