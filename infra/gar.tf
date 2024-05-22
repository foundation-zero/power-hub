resource "google_artifact_registry_repository" "power_hub" {
  location      = var.region
  repository_id = var.name
  description   = "Power Hub Docker repository"
  format        = "DOCKER"
}

locals {
  power_hub_repo = "${var.region}-docker.pkg.dev/${var.project_id}/${var.name}"
}
