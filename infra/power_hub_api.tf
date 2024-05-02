variable "openweather_api_key" {
  description = "Open Weather API Key"
}


locals {
  power_hub_api_record_name      = "power-hub-api.${var.env}.${var.subdomain}"
  power_hub_api_hostname         = "power-hub-api.${var.env}.${var.subdomain}.${var.root_hostname}"
}

resource "google_compute_global_address" "power_hub_api_ip" {
  name = "${var.name}-${var.env}-power-hub-api-address"
}

resource "helm_release" "power_hub_api" {
  name       = "power-hub-api"
  chart      = "./charts/python-app"

  values = [file("power_hub_api.values.yaml")]

  depends_on = [ 
      kubernetes_secret.artifact_registry
   ]

  set {
    name  = "ingress.hostname"
    value = local.power_hub_api_hostname
  }

  set {
    name  = "ingress.annotations.kubernetes\\.io/ingress\\.global-static-ip-name"
    value = google_compute_global_address.power_hub_api_ip.name
  }

  set {
    name  = "ingress.annotations.ingressClassName"
    value = "gce"
  }

   # TODO create secret out of this?
  set {
    name  = "container.env.OPEN_WEATHER_API_KEY"
    value = var.openweather_api_key
  }

  set {
    name  = "container.env.INFLUXDB_URL"
    value = "http://${kubernetes_service.influxdb_internal.metadata.0.name}:${kubernetes_service.influxdb_internal.spec.0.port.0.port}"
  }

  set {
    name  = "container.env.INFLUXDB_TOKEN"
    value = var.influxdb_admin_token
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