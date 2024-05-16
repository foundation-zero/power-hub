terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.26.0"
    }
  }

  required_version = ">= 1.7.1"
}
