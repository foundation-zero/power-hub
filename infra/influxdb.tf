variable "influxdb_admin_password" {
  description = "influxdb admin password"
}

variable "influxdb_admin_token" {
  description = "influxdb admin token"
}

locals {
  influxdb_record_name      = "influxdb.${var.env}.${var.subdomain}"
  influxdb_hostname         = "influxdb.${var.env}.${var.subdomain}.${var.root_hostname}"
  influxdb_auth_secret_name = "influxdb-auth"
  influxdb_ssl_name         = "${var.name}-${var.env}-influxdb-ssl"
}

resource "kubernetes_secret" "influxdb_auth" {
  metadata {
    name = local.influxdb_auth_secret_name
  }

  data = {
    admin-password = var.influxdb_admin_password
    admin-token    = var.influxdb_admin_token
  }
}

resource "google_compute_global_address" "influxdb_ip" {
  name = "${var.name}-${var.env}-influxdb-address"
}

resource "kubernetes_manifest" "influxdb_ssl_secret" {
  manifest = {
    "apiVersion" = "networking.gke.io/v1"
    "kind"       = "ManagedCertificate"
    "metadata" = {
      "name"      = local.influxdb_ssl_name
      "namespace" = "default"
    }
    "spec" = {
      "domains" = [local.influxdb_hostname]
    }
  }
}

resource "helm_release" "influxdb" {
  name       = "influxdb"
  chart      = "influxdb2"
  repository = "https://helm.influxdata.com/"


  depends_on = [
    google_container_cluster.primary,
    kubernetes_secret.influxdb_auth,
    kubernetes_manifest.influxdb_ssl_secret
  ]

  values = [file("influxdb.values.yaml")]

  set {
    name  = "adminUser.existingSecret"
    value = local.influxdb_auth_secret_name
  }

  set {
    name  = "ingress.hostname"
    value = local.influxdb_hostname
  }

  set {
    name  = "ingress.annotations.networking\\.gke\\.io/managed-certificates"
    value = local.influxdb_ssl_name
  }

  set {
    name  = "ingress.annotations.kubernetes\\.io/ingress\\.global-static-ip-name"
    value = google_compute_global_address.influxdb_ip.name
  }

  set {
    name = "ingress.annotations.ingressClassName"
    value = "gce"
  }
}

resource "cloudflare_record" "influxdb_record" {
  zone_id = data.cloudflare_zone.zone.id
  name    = local.influxdb_record_name
  value   = google_compute_global_address.influxdb_ip.address
  type    = "A"
  comment = "managed by power hub terraform"
}
