terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "default" {
  id = var.vpc_id
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

data "aws_subnet" "selected" {
  for_each = toset(data.aws_subnets.public.ids)
  id       = each.value
}

locals {
  # Pick one available subnet from each of two AZs.
  subnet_by_az = {
    for subnet in data.aws_subnet.selected :
    subnet.availability_zone => subnet.id
    if subnet.map_public_ip_on_launch
  }

  eks_subnet_ids = [
    for az in slice(sort(keys(local.subnet_by_az)), 0, 2) :
    local.subnet_by_az[az]
  ]
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = "1.37"

  vpc_id     = data.aws_vpc.default.id
  subnet_ids = local.eks_subnet_ids

  endpoint_public_access       = true
  endpoint_private_access      = true
  endpoint_public_access_cidrs = [var.admin_ip_cidr]

  cloudwatch_log_group_retention_in_days = 7

  enable_cluster_creator_admin_permissions = true

  addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni    = {}
  }

  eks_managed_node_groups = {
    demo = {
      instance_types = ["t3.small"]
      capacity_type  = "ON_DEMAND"
      min_size       = 1
      max_size       = 1
      desired_size   = 1
      subnet_ids     = local.eks_subnet_ids
    }

  }

  tags = {
    Project     = "k8s-microservices-platform"
    Environment = "demo"
    ManagedBy   = "Terraform"
  }
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "region" {
  value = var.aws_region
}
