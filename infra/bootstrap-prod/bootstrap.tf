variable "name" {
  description = "name"
}

variable "env" {
  description = "environment"
}

resource "google_kms_key_ring" "terraform_state" {
  name     = "${var.name}-${var.env}-bucket-tfstate-ring"
  location = var.region
}

resource "google_kms_crypto_key" "terraform_state_bucket" {
  name            = "${var.name}-${var.env}-state-bucket"
  key_ring        = google_kms_key_ring.terraform_state.id
  rotation_period = "86400s"

  lifecycle {
    prevent_destroy = false
  }
}

variable "project_id" {
  description = "project id"
}

variable "region" {
  description = "region"
}

resource "google_project_service" "composer_api" {
  project = var.project_id
  service = "composer.googleapis.com"
}

resource "google_project_service" "service_usage_api" {
  project = var.project_id
  service = "serviceusage.googleapis.com"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "project" {
}

resource "google_project_iam_member" "default" {
  project    = var.project_id
  role       = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member     = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
  depends_on = [google_project_service.composer_api]
}

resource "google_storage_bucket" "default" {
  name          = "${var.name}-${var.env}-bucket-tfstate"
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.terraform_state_bucket.id
  }
  depends_on = [
    google_project_iam_member.default,
    google_project_service.service_usage_api
  ]
}
