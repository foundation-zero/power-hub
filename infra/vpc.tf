variable "project_id" {
  description = "project id"
}

variable "region" {
  description = "region"
}

variable "name" {
  description = "name"
}

variable "env" {
  description = "environment (staging for now)"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# VPC
resource "google_compute_network" "vpc" {
  name                    = "${var.name}-${var.env}-vpc"
  auto_create_subnetworks = "false"
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.name}-${var.env}-subnet"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.10.0.0/24"
}
