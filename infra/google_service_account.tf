resource "google_iam_workload_identity_pool" "power_hub_identity_pool" {
  workload_identity_pool_id 	= "power-hub"
  display_name            		= "Power Hub pool"
  description             		= "Power Hub pool"
  disabled                		= false
}   

resource "google_iam_workload_identity_pool_provider" "power_hub_pool_provider" {
  workload_identity_pool_id           	    = google_iam_workload_identity_pool.power_hub_identity_pool.workload_identity_pool_id
  workload_identity_pool_provider_id  	    = "power-hub-cloud-oidc-staging"
  display_name                        		= "power-hub-cloud-oidc-staging"
  description                       		= "Power Hub Provider"
  disabled                        			= false

  attribute_mapping                         = {
    "google.subject"        = "assertion.sub"
    "attribute.actor"       = "assertion.actor"
    "attribute.repository"  = "assertion.repository"
  }
  oidc {
    issuer_uri        = "https://token.actions.githubusercontent.com"
  }
}

data "google_project" "gcp_project" {}

resource "google_service_account" "service_account" {
  account_id   = "power-hub"
  display_name = "Power Hub"
}

variable "github_org" {
  default     = "foundation-zero"
  description = "Github Org"
}

variable "github_repo" {
  default     = "energy-box-control"
  description = "Github Repo"
}

resource "google_service_account_iam_binding" "power_hub_iam_binding" {
  service_account_id = google_service_account.service_account.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.power_hub_identity_pool.name}/attribute.repository/${var.github_org}/${var.github_repo}"
  ]
}

resource "google_project_iam_binding" "power_hub_gak_binding" {
  project = "${var.project_id}"
  role    = "roles/artifactregistry.writer"

  members = [
    "serviceAccount:${google_service_account.service_account.email}",
  ]
}
