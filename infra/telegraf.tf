variable "influxdb_org" {
  description = "influxdb org"
}

variable "influxdb_bucket" {
  description = "influxdb bucket"
}

resource "helm_release" "telegraf" {
  name       = "telegraf"
  repository = "https://helm.influxdata.com/"
  chart      = "telegraf"
  values = [file("telegraf.values.yaml")]

  depends_on = [
    google_container_cluster.primary,
    helm_release.influxdb,
    helm_release.vernemq
  ]

  set {
    name  = "config.outputs[0].influxdb_v2.token"
    value = var.influxdb_admin_token
  }

  set {
    name  = "config.outputs[0].influxdb_v2.organization"
    value = var.influxdb_org
  }

  set {
    name  = "config.outputs[0].influxdb_v2.bucket"
    value = var.influxdb_bucket
  }
}