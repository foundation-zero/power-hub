variable "openweather_api_key" {
  description = "Open Weather API Key"
}

variable "power_hub_api_token" {
  description = "API token"
}


locals {
  power_hub_api_record_name       = "api.${var.env}.${var.subdomain}"
  power_hub_api_hostname          = "api.${var.env}.${var.subdomain}.${var.root_hostname}"
  power_hub_api_ssl_name          = "${var.name}-${var.env}-ssl"
  openweather_api_key_secret_name = "openweather-key"
}

resource "google_compute_global_address" "power_hub_api_ip" {
  name = "${var.name}-${var.env}-api-address"
}

resource "kubernetes_manifest" "power_hub_api_ssl_secret" {
  manifest = {
    "apiVersion" = "networking.gke.io/v1"
    "kind"       = "ManagedCertificate"
    "metadata" = {
      "name"      = local.power_hub_api_ssl_name
      "namespace" = "default"
    }
    "spec" = {
      "domains" = [local.power_hub_api_hostname]
    }
  }
}

resource "kubernetes_secret" "openweather_api_key" {
  metadata {
    name = local.openweather_api_key_secret_name
  }

  data = {
    key = var.openweather_api_key
  }
}

resource "helm_release" "power_hub_api" {
  name  = "power-hub-api"
  chart = "./charts/python-app"

  values = [file("power_hub_api.values.yaml")]

  depends_on = [
    google_container_cluster.primary,
    kubernetes_manifest.power_hub_api_ssl_secret
  ]

  set {
    name  = "image.repository"
    value = "${local.power_hub_repo}/api"
  }

  set {
    name  = "image.tag"
    value = var.python_app_image_tag
  }

  set {
    name  = "ingress.hosts[0].host"
    value = local.power_hub_api_hostname
  }

  set {
    name  = "ingress.hosts[0].paths[0].path"
    value = "/"
  }

  set {
    name  = "ingress.hosts[0].paths[0].pathType"
    value = "Prefix"
  }

  set {
    name  = "ingress.annotations.networking\\.gke\\.io/managed-certificates"
    value = local.power_hub_api_ssl_name
  }

  set {
    name  = "ingress.annotations.kubernetes\\.io/ingress\\.global-static-ip-name"
    value = google_compute_global_address.power_hub_api_ip.name
  }

  set {
    name  = "ingress.annotations.ingressClassName"
    value = "gce"
  }

  set {
    name  = "container.env.API_TOKEN"
    value = var.power_hub_api_token
  }


  set {
    name  = "container.envFromSecrets.OPEN_WEATHER_API_KEY.secretName"
    value = kubernetes_secret.openweather_api_key.metadata.0.name
  }

  set {
    name  = "container.envFromSecrets.OPEN_WEATHER_API_KEY.secretKey"
    value = "key"
  }

  set {
    name  = "container.env.INFLUXDB_URL"
    value = "http://${kubernetes_service.influxdb_internal.metadata.0.name}:${kubernetes_service.influxdb_internal.spec.0.port.0.port}"
  }


  set {
    name  = "container.envFromSecrets.INFLUXDB_TOKEN.secretName"
    value = kubernetes_secret.influxdb_auth.metadata.0.name
  }

  set {
    name  = "container.envFromSecrets.INFLUXDB_TOKEN.secretKey"
    value = "admin-token"
  }

  set {
    name  = "container.env.INFLUXDB_ORGANISATION"
    value = var.influxdb_org
  }

  set {
    name  = "container.env.INFLUXDB_TELEGRAF_BUCKET"
    value = var.influxdb_bucket
  }
}

resource "cloudflare_record" "power_hub_api_record" {
  zone_id = data.cloudflare_zone.zone.id
  name    = local.power_hub_api_record_name
  value   = google_compute_global_address.power_hub_api_ip.address
  type    = "A"
  comment = "managed by power hub terraform"
}
