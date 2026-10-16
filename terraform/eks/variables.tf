variable "aws_region" {
  description = "AWS region for the EKS demo"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "Existing default VPC ID"
  type        = string
  default     = "vpc-0032c82860990c901"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "microservices-demo"
}

variable "admin_ip_cidr" {
  description = "Public IP allowed to access the Kubernetes API"
  type        = string
  default     = "122.183.57.36/32"

  validation {
    condition     = can(cidrhost(var.admin_ip_cidr, 0))
    error_message = "Provide a valid IPv4 CIDR, such as 203.0.113.10/32."
  }
}
