resource "google_artifact_registry_repository" "power-hub" {
  location      = "europe-west1"
  repository_id = "power-hub"
  description   = "Power Hub Docker repository"
  format        = "DOCKER"
}