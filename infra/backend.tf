terraform {
 backend "gcs" {
   bucket  = "power-hub-bucket-tfstate"
   prefix  = "terraform/state"
 }
}