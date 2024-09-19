resource "google_artifact_registry_repository" "power_hub" {
  location      = var.region
  repository_id = var.name
  description   = "Power Hub Docker repository"
  format        = "DOCKER"
}

locals {
  power_hub_repo = "${var.region}-docker.pkg.dev/${var.project_id}/${var.name}"
}

resource "google_service_account" "powerhub_gar_sa" {
  account_id   = "powerhub-gar-sa"
  display_name = "Powerhub GAR Service Account"
}

resource "google_project_iam_member" "powerhub_gar_role_member" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = google_service_account.powerhub_gar_sa.member
}

resource "google_service_account_key" "powerhub_gar_sa_key" {
  service_account_id = google_service_account.powerhub_gar_sa.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

resource "google_secret_manager_secret" "powerhub_gar_sa_secret" {
  secret_id = "powerhub-gar-secret"

  replication {
    auto {}
  }

  depends_on = ["google_project_iam_member.tofu_secret_manager_access"]
}

resource "google_secret_manager_secret_version" "powerhub_gar_sa_secret_version" {
  secret = google_secret_manager_secret.powerhub_gar_sa_secret.id
  secret_data = base64decode(google_service_account_key.powerhub_gar_sa_key.private_key)
}
