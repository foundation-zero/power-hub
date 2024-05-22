variable "cloudflare_api_token" {
  description = "cloudflare access token"
}

variable "root_hostname" {
  description = "root hostname"
}

variable "subdomain" {
  description = "subdomain of root_hostname on which the infra is build"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

data "cloudflare_zone" "zone" {
  name = var.root_hostname
}
